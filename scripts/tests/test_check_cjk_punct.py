"""check_cjk_punct 新增规则单测：

锁住 chinese-copywriting-guidelines 补强的四条：
  strict — CJK 后半角 ! ?；全角数字 / 字母；水平分割线 ---
  warn   — 数字与单位间漏空格；专有名词大小写
并锁住对应的免误报边界（版本号 / 度数百分号 / markdown 图片 / 已正确大小写 /
  frontmatter / setext 下划线 / 表格分隔行）。
"""
import check_cjk_punct as c


def _levels(text, full=False):
    """返回 {level: [reason, ...]}，便于按级别断言。"""
    out = {}
    for _, level, reason, _ in c.check_text(text, full=full):
        out.setdefault(level, []).append(reason)
    return out


# ── strict：CJK 后半角 ! ? ────────────────────────────────
def test_halfwidth_bang_after_cjk_is_strict():
    assert "strict" in _levels("你知道嘛? 真的!")


def test_halfwidth_bang_english_tail_not_flagged():
    """英文整句结尾的 !? 不由本规则报（前导非 CJK）。"""
    assert "strict" not in _levels("Stay hungry, stay foolish!")


def test_markdown_image_bang_not_flagged():
    """行内 ![alt](url) 与引用式 ![alt][id] 的 `!` 不算 CJK 后半角。"""
    assert "strict" not in _levels("看图 ![截图](shot.png) 没问题")
    assert "strict" not in _levels("实现共赢![][image1]")


# ── strict：全角数字 / 字母 ───────────────────────────────
def test_fullwidth_digit_letter_is_strict():
    assert "strict" in _levels("全角数字１０００ 和字母ＡＢＣ")


# ── warn：数字与单位间空格 ────────────────────────────────
def test_unit_spacing_is_warn():
    lv = _levels("硬盘 20TB，带宽 10Gbps")
    assert "warn" in lv and any("单位" in r for r in lv["warn"])


def test_version_and_percent_not_unit_warn():
    """L3 / Q3 / 3.2 / 5G / 233° / 15% 不是单位漏空格。"""
    for s in ("版本 L3 和 Q3", "占比 3.2 倍", "5G 网络", "温度 233° 占比 15%"):
        lv = _levels(s)
        assert not any("单位" in r for r in lv.get("warn", [])), s


# ── warn：专有名词大小写 ──────────────────────────────────
def test_proper_noun_wrong_case_is_warn():
    lv = _levels("这是 github 不是 GitHub")
    assert any("GitHub" in r for r in lv.get("warn", []))


def test_proper_noun_correct_case_not_flagged():
    assert not any("专有名词" in r for r in _levels("适配 iOS 用 JavaScript 写").get("warn", []))


# ── fixer：strict 级可自动修复，修后复检干净 ──────────────
def test_fix_line_converts_bang_and_fullwidth():
    fixed = c.fix_line("你知道嘛? 真的! 全角１２３ＡＢ")
    assert "？" in fixed and "！" in fixed
    assert "123AB" in fixed
    assert not any(lv == "strict" for _, lv, _, _ in c.check_text(fixed))


def test_fix_line_keeps_version_tokens():
    """L3 / 3.2 不含全角、无 CJK 后半角，fixer 不应改动。"""
    assert c.fix_line("版本 L3 升到 3.2") == "版本 L3 升到 3.2"


# ── strict：水平分割线 ---（传 Confluence 渲染崩）──────────
def test_hr_strict():
    """前后空行的 --- 是水平分割线，必报。"""
    lv = _levels("段落一\n\n---\n\n段落二")
    assert "strict" in lv
    assert any("水平分割线" in r for r in lv["strict"])


def test_hr_indent_and_longer_dash():
    """≤3 空格缩进 / 4+ 减号仍是 HR。"""
    assert "strict" in _levels("段落\n\n   ---\n\n下文")
    assert "strict" in _levels("段落\n\n----\n\n下文")


# ── 放过：frontmatter / setext / 表格 ─────────────────────
def test_frontmatter_boundary_not_flagged():
    """文件首行 --- 开闸 / 再遇 --- 关闸，均不报。"""
    assert "strict" not in _levels("---\ntitle: test\n---\n\n正文 here")


def test_setext_underline_not_flagged():
    """--- 紧跟文本行下 = Setext h2 下划线，不报。"""
    assert "strict" not in _levels("标题文本\n---\n\n下文 here")


def test_table_separator_not_flagged():
    """表格分隔行 | --- | 含 |，不匹配纯 ---，不报。"""
    assert "strict" not in _levels("| col a | col b |\n| --- | --- |\n| 1 | 2 |")


# ── fixer：HR → 空行（setext / frontmatter 不动）─────────
def test_fix_hr_to_blank_line(tmp_path):
    f = tmp_path / "t.md"
    f.write_text("段落一\n\n---\n\n段落二\n", encoding="utf-8")
    assert c.fix_file(f) == 1
    assert "---" not in f.read_text(encoding="utf-8")


def test_fix_keeps_setext_and_frontmatter(tmp_path):
    src = "---\ntitle: test\n---\n\n标题\n---\n"
    f = tmp_path / "t.md"
    f.write_text(src, encoding="utf-8")
    assert c.fix_file(f) == 0
    assert f.read_text(encoding="utf-8") == src


# ── 空格自动插入（fix_line(punct=False, spaces=True)）──────────
def _sp(text):
    return c.fix_line(text, punct=False, spaces=True)


import pytest  # noqa: E402


@pytest.mark.parametrize("src", ["D值 < 0", "R公式建立在", "C模式机制", "A档方案"])
def test_space_single_letter_protected(src):
    """单个拉丁字母紧贴中文视为型号/变量名，不插空格。"""
    assert _sp(src) == src


@pytest.mark.parametrize("src,exp", [
    ("用GitHub世界", "用 GitHub 世界"),
    ("用OBS推流", "用 OBS 推流"),
    ("走TRTC房间", "走 TRTC 房间"),
])
def test_space_multiletter_word_inserted(src, exp):
    """≥2 连续拉丁字母的英文词两侧插空格。"""
    assert _sp(src) == exp


@pytest.mark.parametrize("src,exp", [
    ("第3章内容", "第 3 章内容"),
    ("30分钟内", "30 分钟内"),
    ("花了5000元", "花了 5000 元"),
])
def test_space_chinese_number_boundary(src, exp):
    assert _sp(src) == exp


def test_space_degree_percent_exception():
    """度数 ° / 百分号 % 后接中文不插空格（规范例外）。"""
    assert _sp("旋转90°角度") == "旋转 90°角度"      # 90 前插、° 后不插
    assert _sp("占比15%的用户") == "占比 15%的用户"   # 15 前插、% 后不插


@pytest.mark.parametrize("src,exp", [
    ("上传20TB文件", "上传 20 TB 文件"),
    ("延迟低于600ms那档", "延迟低于 600 ms 那档"),
])
def test_space_number_unit(src, exp):
    assert _sp(src) == exp


@pytest.mark.parametrize("src", ["597万用户", "月活2.4万", "10亿市值", "5千用户"])
def test_space_numeral_multiplier_protected(src):
    """中文数量级字（万/亿/千/百）是数字构成部分，不插空格。"""
    # 数字前若有中文仍会插（月活 2.4万），但数量级字前不插
    out = _sp(src)
    assert "万" not in out or " 万" not in out
    assert "亿" not in out or " 亿" not in out
    assert "千" not in out or " 千" not in out


@pytest.mark.parametrize("token", ["5G", "L3", "Q3", "H5"])
def test_space_version_token_not_broken(token):
    """5G / L3 / Q3 / H5 这类标识/版本内部不被拆（字母数字连写不插空格）。
    token 与相邻中文之间按 pangu 加空格属正确，但 token 内部完整。"""
    out = _sp(f"看{token}方案")
    assert token in out                     # 标识符内部完整
    assert f"{token[0]} {token[1]}" not in out  # 内部未被拆


def test_space_protected_spans():
    """代码块行内代码 / URL / markdown 链接内不插空格。"""
    assert _sp("`code里的abc`") == "`code里的abc`"
    assert _sp("看 https://a.com/中文abc 结束") == "看 https://a.com/中文abc 结束"
    assert _sp("[链接text](http://x.com/中文abc)") == "[链接text](http://x.com/中文abc)"


@pytest.mark.parametrize("src", [
    "用GitHub世界第3章上传20TB", "597万用户D值分析", "走TRTC房间30分钟",
])
def test_space_idempotent(src):
    once = _sp(src)
    assert _sp(once) == once


def test_fix_spaces_file_only_spaces_no_punct(tmp_path):
    """fix_file(punct=False, spaces=True) 只补空格，不动半角标点 / HR。"""
    src = "用GitHub世界,还有---分割\n"
    f = tmp_path / "t.md"
    f.write_text(src, encoding="utf-8")
    c.fix_file(f, punct=False, spaces=True)
    out = f.read_text(encoding="utf-8")
    assert "用 GitHub 世界" in out
    assert "," in out          # 半角逗号未被改全角（punct 关）
    assert "---" in out        # HR 未被删（punct 关）


def test_fix_file_default_still_strict_only(tmp_path):
    """默认 fix_file（punct=True, spaces=False）行为不变：改标点不补空格。"""
    src = "你知道嘛? 用GitHub世界\n"
    f = tmp_path / "t.md"
    f.write_text(src, encoding="utf-8")
    c.fix_file(f)
    out = f.read_text(encoding="utf-8")
    assert "？" in out              # 标点修了
    assert "用GitHub世界" in out    # 空格没补（默认档不碰空格）


def test_fix_line_image_link_not_duplicated():
    """图片行 --fix 不复制链接（嵌套 span 曾把 ![X](Y) 写成 ![X](Y)[X](Y)）。"""
    img = "![社区核心指标趋势](community-trends-0821.png)"
    out = c.fix_line(img)
    assert out == img  # 保护段内原样
    assert c.fix_line(out) == out  # 幂等


def test_fix_file_image_line_untouched(tmp_path):
    """整文件 --fix 跑完图片行保持单链接（gen_weekly_all 后处理链路回归）。"""
    f = tmp_path / "t.md"
    f.write_text("## 趋势图\n\n![直播核心指标趋势](live-trends-0821.png)\n", encoding="utf-8")
    c.fix_file(f)
    out = f.read_text(encoding="utf-8")
    assert out.count("live-trends-0821.png") == 1
