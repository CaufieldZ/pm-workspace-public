"""check_bullet_density 单测。

锁住「非豁免章内单行句号 ≥3 = 挤话」规则 + 误报边界：
  命中  — 正文段落 / bullet 单行 ≥3 个中文句号
  干净  — ≤2 句号 / 分号串子项 / 单句 bullet
  跳过  — >/表格/代码块/:::/frontmatter/空行/纯图片
  无章节豁免 — 决策 / 埋点 / 变更章也配写好看，句号≥3 / 分号串照样报（block 一视同仁；
              章节豁免只在 md_scan WARN 层给「长句可以长」这一维）
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
