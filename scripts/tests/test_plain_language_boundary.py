"""误杀回归集：正常产物 / 合法 PM 术语不该被 strict 拦。

check_plain_language 是 regex gate，跑在 PRD/IMAP/周报产物上，读者是 leader/业务。
最大风险不是漏判，是误杀——把正常 PRD 腔、官方公告风、技术状态描述、
以及「梳理 / 链路 / 沉淀 / 对齐 / 触达 / 闭环 / 落地 / 打通」这类合法 PM 术语拦下来。

这组语料是扩词库的护栏：每加一类 warn 词，跑这个测试确认正常产物仍 0 strict。
素材改写自 shuorenhua repo references/boundary-cases.md，落到 维护者 产物域。
"""
import check_plain_language as cpl


def _strict_hits(text: str) -> list:
    """按普通 .md 产物的 strict 口径扫描（STRICT_PATTERNS + 场景编号裸引用）。"""
    lines = text.splitlines()
    patterns = list(cpl.STRICT_PATTERNS) + [cpl.SCENE_ANCHOR_PATTERN]
    return cpl._scan_lines(lines, patterns)


# 正常产物 / 合法术语 —— 每条都必须 0 strict
MUST_NOT_BLOCK = [
    # 正常 PRD 腔（产品语体，不该大手术）
    "用户首次进入工作台且无历史项目时，页面展示空状态卡片，引导创建第一个项目。"
    "创建成功后，卡片立即消失，后续不再展示。",
    # 官方公告风（本就是目标语域）
    "为保障系统稳定，今晚 23:00 至 23:30 对支付服务做例行维护。"
    "维护期间部分用户可能短时下单失败，完成后自动恢复，无需额外操作。",
    # 技术状态描述（专业信息要保留）
    "本次排查已定位到缓存层。昨天补齐了主链路日志，今天继续核对两个异常分支，"
    "确认是不是同一类失效路径。",
    # 合法 PM 术语（repo 想杀、维护者 语境合法）
    "先梳理社区需求，理清用户从进入到首单的链路，把过往运营经验沉淀成手册。",
    "三方口径对齐后，内容触达率作为本期核心指标。",
    "活动闭环跑通，方案落地到直播间，把社区和增长两条线打通。",
    # 工区 IDENTITY 术语：真相源
    "baseline 是该产品线当前态的唯一真相源，迭代写 delta。",
    # 业务列表序号「决策 1：」不是内部决策锚点（冒号边界豁免）
    "决策 1：先上线社区版，二期再做直播打通。",
    # 表格行里的场景编号是合法锚点
    "| A-1 | 下注弹层 | 主流程 |",
    # 标题里「编号 · 白话名」是认可形态
    "### 2.1 A-4 · 推荐卡露出",
]


def test_normal_deliverables_zero_strict():
    failures = []
    for text in MUST_NOT_BLOCK:
        hits = _strict_hits(text)
        if hits:
            failures.append((text[:40], hits))
    assert not failures, f"正常产物被误杀：{failures}"


def test_pm_jargon_not_blocked():
    """逐条 PM 术语单独验，定位回归更细。"""
    for term_sentence in [
        "梳理需求",
        "用户链路清晰",
        "经验沉淀成文档",
        "口径对齐",
        "内容触达用户",
        "闭环跑通",
        "方案落地",
        "两条线打通",
    ]:
        assert not _strict_hits(term_sentence), f"PM 术语被误杀：{term_sentence}"


def _warn_hits(text: str) -> list:
    return cpl._scan_lines(text.splitlines(), cpl.WARN_PATTERNS)


# 新增 AI 味词组：必须 warn 命中，且不得进 strict（warn 不阻断）
NEW_WARN_SAMPLES = [
    "综上所述，本期社区数据整体向好。",
    "研究表明用户更偏好短视频。",
    "数据显示留存有所回落。",
    "这是一篇保姆级运营攻略。",
    "划重点：先跑通主流程。",
]


def test_new_warn_words_fire():
    for text in NEW_WARN_SAMPLES:
        assert _warn_hits(text), f"新 AI 味词组未命中 warn：{text}"


def test_new_warn_words_not_strict():
    for text in NEW_WARN_SAMPLES:
        assert not _strict_hits(text), f"warn 词误升 strict（会阻断产物）：{text}"


# ── 营销稿（promo-）语境分流 ─────────────────────────────────
# 同一个「全新升级」：默认语境 strict 拦，营销语境降 warn。
# 但版本号 / 内部锚点跨语境硬伤照拦 strict。

def _check(tmp_path, name: str, text: str):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return cpl.check_file(p)


def test_promo_ai_slop_downgraded_to_warn(tmp_path):
    strict, warn = _check(tmp_path, "promo-x.md", "社区「交易卡片」全新升级，焕新体验。")
    assert not strict, f"营销词不该 strict 拦：{strict}"
    assert warn, "营销词应落 warn 软提醒"


def test_default_ai_slop_still_strict(tmp_path):
    strict, _ = _check(tmp_path, "user-manual-x.md", "本功能全新升级，焕新体验。")
    assert strict, "默认语境营销词应 strict 拦（零回归）"


def test_promo_version_number_blocked(tmp_path):
    strict, _ = _check(tmp_path, "promo-x.md", "社区 3.2 上线，欢迎体验。")
    cats = {h[1] for h in strict}
    assert "内部版本号外泄" in cats, f"营销稿版本号应 strict 拦：{strict}"


def test_promo_internal_anchor_still_blocked(tmp_path):
    strict, _ = _check(tmp_path, "promo-x.md", "详见 baseline.md 的说明。")
    assert strict, "内部锚点跨语境照拦，营销稿不豁免"


def test_promo_real_numbers_not_blocked(tmp_path):
    strict, _ = _check(
        tmp_path, "promo-x.md",
        "收益率 +12.34%，开仓价 67,388，涨幅达到 3.2 倍。",
    )
    assert not strict, f"营销稿真实数字不该被当版本号：{strict}"



# ── --added-only：只拦新增行（存量违规不拦）────────────────────
def test_parse_added_multi_line_hunk():
    assert cpl._parse_added("@@ -1,3 +1,5 @@\n+新行\n") == {1, 2, 3, 4, 5}


def test_parse_added_single_line_hunk_omits_count():
    """`@@ -5 +7 @@` 省略计数 = 1 行，别当成 0 行漏掉。"""
    assert cpl._parse_added("@@ -5 +7 @@\n+x\n") == {7}


def test_parse_added_new_file_hunk():
    assert cpl._parse_added("@@ -0,0 +1,4 @@\n+a\n+b\n") == {1, 2, 3, 4}


def test_parse_added_no_hunk():
    assert cpl._parse_added("diff --git a/x b/x\n") == set()


def test_added_lines_untracked_file_returns_none(tmp_path):
    """非仓库内的文件拿不到 diff → None（不限制），不能返回空集把门变成静默放行。"""
    f = tmp_path / "x.md"
    f.write_text("D-1 裸编号\n", encoding="utf-8")
    assert cpl._added_lines(f) is None


def test_check_file_added_only_filters_legacy(tmp_path, monkeypatch):
    """added_only=True 时，只保留新增行上的命中。"""
    f = tmp_path / "x.md"
    f.write_text("D-1 旧账\nD-2 旧账\nD-3 新账\n", encoding="utf-8")
    monkeypatch.setattr(cpl, "_added_lines", lambda p: {3})
    strict, _ = cpl.check_file(f, added_only=True)
    assert [h[0] for h in strict] == [3], f"应只剩新增行上的命中：{strict}"


def test_check_file_added_only_none_means_full_scan(tmp_path, monkeypatch):
    """_added_lines 返回 None（未跟踪 / 非仓库）→ 全量扫，不放行。"""
    f = tmp_path / "x.md"
    f.write_text("D-1 旧账\nD-2 旧账\n", encoding="utf-8")
    monkeypatch.setattr(cpl, "_added_lines", lambda p: None)
    strict, _ = cpl.check_file(f, added_only=True)
    assert len(strict) == 2, f"None 应回落到全量：{strict}"
