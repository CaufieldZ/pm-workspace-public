"""误杀回归集：正常产物 / 合法 PM 术语不该被 strict 拦。

check_plain_language 是 regex gate，跑在 PRD/IMAP/周报产物上，读者是 leader/业务。
最大风险不是漏判，是误杀——把正常 PRD 腔、官方公告风、技术状态描述、
以及「梳理 / 链路 / 沉淀 / 对齐 / 触达 / 闭环 / 落地 / 打通」这类合法 PM 术语拦下来。

这组语料是扩词库的护栏：每加一类 warn 词，跑这个测试确认正常产物仍 0 strict。
素材改写自 shuorenhua repo references/boundary-cases.md，落到 Felix 产物域。
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
    # 合法 PM 术语（repo 想杀、Felix 语境合法）
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

