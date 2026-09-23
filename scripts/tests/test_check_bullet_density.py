"""check_bullet_density 单测。

锁住四条挤话判据 + 误报边界：
  命中  — bullet 单行 ≥3 句号 / 单行 ≥2 分号 / 单句 ≥100 字 / 段落碎句（≥3 句且句长中位 <9）
  干净  — ≤2 句号 / 分号串子项 / 单句 bullet / 三句完整短句 / 引号内的长文案
  跳过  — >/表格/代码块/:::/frontmatter/空行/纯图片
  章节豁免 — 只给「长句」这一维：决策 / 变更 / 埋点章的论证句可以长；
            句号 / 分号 / 碎句一视同仁（哪章都该拆）
  逃生口 — <!-- lint-skip:density --> 行级跳过
"""
import check_bullet_density as c


def _lines(text):
    """返回命中行号列表。"""
    return [ln for ln, _kind, _cnt, _exc in c.check_text(text)]


# ── 真阳性 ────────────────────────────────────────────
def test_paragraph_3_periods_hits():
    """正文段落 3 个句号 = 多件事挤一团，报。"""
    assert 1 in _lines("第一句。第二句。第三句。")


def test_bullet_4_periods_hits_kind():
    """bullet 4 句报，kind=bullet。"""
    hits = c.check_text("- 一。二。三。四。")
    assert hits and hits[0][1] == "bullet"


# ── 真阴性 ────────────────────────────────────────────
def test_2_periods_clean():
    """2 个句号不报。"""
    assert _lines("第一句。第二句。") == []


def test_one_semicolon_clean():
    """单个分号（1 个子项分隔）不报——阈值是 ≥2。"""
    assert _lines("显示逻辑：A；B。") == []


def test_two_semicolons_hits():
    """单行 ≥2 分号 → 报（该拆嵌套 bullet），kind 带「分号」。"""
    hits = c.check_text("显示逻辑：默认自动通过；运营可人工通过 / 驳回；通过前校验冲突")
    assert hits and "分号" in hits[0][1]


def test_two_semicolons_halfwidth_hits():
    """半角分号同样计数。"""
    hits = c.check_text("data: a; b; c")
    assert hits and "分号" in hits[0][1]


def test_semicolon_in_table_row_exempt():
    """表格行内分号是 md_to_confluence 切 bullet 的约定分隔符，豁免。"""
    assert _lines("| 规则 | A；B；C；D |") == []


def test_single_sentence_bullet_clean():
    """一条 bullet 一句，不报。"""
    assert _lines("- 只有一句话。") == []


def test_promo_prefix_exempt(tmp_path):
    """营销稿（promo-）整类豁免：营销散文连贯成段，check_file 直接返回空。"""
    runon = "第一句。第二句。第三句。第四句。"
    # 普通文件名照报
    normal = tmp_path / "prd-x.md"
    normal.write_text(runon, encoding="utf-8")
    assert c.check_file(normal), "非 promo 文件应正常检测"
    # promo- 前缀豁免
    promo = tmp_path / "promo-x.md"
    promo.write_text(runon, encoding="utf-8")
    assert c.check_file(promo) == [], "promo- 营销稿应整类豁免"


# ── 行级跳过 ──────────────────────────────────────────
def test_blockquote_skipped():
    """> 场景业务故事导语 3 句不报（PRD 允许 >）。"""
    assert _lines("> 用户刷 Feed。被勾住。点进主页。") == []


def test_table_row_skipped():
    """表格行 3 句不报。"""
    assert _lines("| 一。二。三。 | 四 |") == []


def test_code_block_skipped():
    """代码块内 3 句不报。"""
    assert _lines("```\n一。二。三。\n```") == []


def test_container_marker_skipped():
    """::: 容器标记行不报。"""
    assert _lines(":::一。二。三。") == []


def test_frontmatter_skipped():
    """YAML frontmatter 内 3 句不报。"""
    assert _lines("---\ntitle: 一。二。三。\n---\n正文。") == []


def test_image_only_line_skipped():
    """纯图片行不报。"""
    assert _lines("![一。二。三。](a.png)") == []


# ── 无章节豁免：决策 / 埋点 / 变更章句号串、分号串照样 block ──────────
def test_decision_chapter_period_runon_hits():
    """§6 决策章内 3 句焊一行 = 挤话，拆成标签 bullet 更好读——照样报。"""
    assert 2 in _lines("# 6. 决策记录（WHY）\n取舍：选 A。因为 X。所以 Y。")


def test_decision_chapter_narrative_pair_clean():
    """决策章 2 句号（论点。论据。）不到阈值，天然过——不因章节而豁免，因句号 <3。"""
    assert _lines("# 6. 决策记录（WHY）\n取舍：选 A。因为成本更低。") == []


def test_tracking_chapter_semicolon_runon_hits():
    """§7 埋点章分号串列举照样报（哪章都该拆嵌套 bullet）。"""
    hits = c.check_text("# 7. 埋点与看板\n事件：曝光；点击；转化")
    assert hits and "分号" in hits[0][1]


def test_changelog_chapter_period_runon_hits():
    """变更记录章 3 句焊一行照样报（append-only 不等于随便挤）。"""
    assert 2 in _lines("# 15. 变更记录\nv3.2 上线。合并 A。砍 B。")


def test_scene_chapter_hits():
    """§2 场景章内 3 句报。"""
    text = "# 2. 本轮需求\n业务故事：用户发帖。挂卡片。双端发布。"
    assert 2 in _lines(text)


# ── 逃生口 ────────────────────────────────────────────
def test_lint_skip_marker():
    """行尾 <!-- lint-skip:density --> 跳过该行。"""
    assert _lines("归因口径：A。B。C。 <!-- lint-skip:density -->") == []


# ── 回归 fixture：livestream-2.1.2 L8 文件头背景段 ────
def test_regression_background_paragraph():
    """锁住原型 case：文件头背景段 4 句挤话。"""
    text = ("**背景**：2.1.1 上线后的补丁包。开播表单缺校验。"
            "推流方式仍加白锁死。直播结束后假重开。")
    assert _lines(text) == [1]


def test_enumeration_field_not_false_positive():
    """枚举字段（顿号分隔多项，句号 / 分号少）绝不误报——标定发现的最大误伤点。"""
    # 顿号 6 段但仅 0 句号 0 分号，合法枚举
    assert _lines("- 选手列表（序号、姓名、赛事阶段、直播票数、评审团票数、总票数）") == []
    assert _lines("- 投票组件：免费票余额展示、Platform C 现货余额、投票弹窗、消耗提示") == []


# ── 新增判据：碎句 / 长句 / 行首编号 / 引号 ────────────────
def test_three_complete_short_sentences_clean():
    """三句完整的短句不是挤话——段落不再数句号，句长够就不是碎句。"""
    assert _lines("目前这条漏斗没有看板。运营每天只能手工拉数。我们想做一张看板。") == []


def test_paragraph_and_bullet_long_sentence_hit():
    """单句 ≥100 字的段落与 bullet 都报，kind 带「长句」。"""
    long_sent = "甲" * c.LONG_SENTENCE_CHARS
    for text in (f"{long_sent}。", f"- {long_sent}。"):
        hits = c.check_text(text)
        assert hits and "长句" in hits[0][1], (text, hits)


def test_long_sentence_exempt_in_decision_chapter():
    """决策 / 变更 / 埋点章的论证句可以长——长句这一维免查，同句在正文照报。"""
    long_sent = "甲" * c.LONG_SENTENCE_CHARS
    assert _lines(f"# 6. 决策记录（WHY）\n取舍：{long_sent}。") == []
    assert _lines(f"# 2. 本轮需求\n{long_sent}。") == [2]


def test_quoted_long_text_not_counted_as_long_sentence():
    """引号里是引用来的整块文案，内部长度不算进本文的句长。"""
    assert _lines(f"- 提示用户「{'甲' * 300}」，点确认继续。") == []


def test_quoted_text_does_not_fake_a_fragment():
    """引号内长文案不能把该句压短、把中位数拖低——否则正常三段式手册语被误判碎句。"""
    assert _lines(
        "提交后页面提示「我们将在 1-2 个工作日内审核完毕」。审核有结果会用 App 推送通知你："
        "通过后身份直接变成主播，可以去主播中心创建直播；没通过会写明原因。"
    ) == []


def test_leading_list_number_not_counted_in_sentence_len():
    """行首 `1. ` 是列表标记不计句长——99 字放行、100 字才拦，差的就是那三个字符。"""
    body = "甲" * (c.LONG_SENTENCE_CHARS - 1)
    assert _lines(f"1. {body}。") == []
    assert _lines(f"1. {body}甲。") != []


# ── diff-based（only_line_texts：只报本次新增行，存量不报） ──────────
def test_diff_only_reports_added_lines():
    """only_line_texts 非空时，只报文本命中该集合的行，存量分号串行不报。"""
    text = ("- 存量：A；B；C\n"     # 存量分号串，不在 added 集
            "- 新增：X；Y；Z")      # 本次新增，在 added 集
    added = {"- 新增：X；Y；Z"}
    lines = [ln for ln, _k, _c, _e in c.check_text(text, only_line_texts=added)]
    assert lines == [2]


def test_diff_empty_added_reports_nothing():
    """added 集为空（本次无新增内容行）→ 零命中，纯存量编辑不卡。"""
    text = "- 存量：A；B；C"
    assert c.check_text(text, only_line_texts=set()) == []
