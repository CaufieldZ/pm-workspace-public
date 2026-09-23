"""migrate_scene_blocks 单测：平铺 → 组头式迁移的安全性。

锁住四类判据（形态取自真实存量产物标定）：
  形态  — 三种平铺分隔符（冒号 / 间隔号 / 无分隔符直跟 ul）都能转，正文一字不动
  分组  — 连续同标签并成一个组头；非连续同标签各自成组、不改文本顺序
  拒绝  — 顶层项混入非三段式标签 / 标签平衡存疑 → 整块跳过，不部分转换
  安全  — 文本等价门 + 字符数不变量在转换期把关；dry-run 不落盘，--apply 落 .bak
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "prd" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import migrate_scene_blocks as m  # noqa: E402


def block(*items, indent="      "):
    return indent + "<ol>\n" + "".join(items) + "\n" + indent + "</ol>\n"


def li(text):
    return "        <li>%s</li>\n" % text


def _run(text):
    """跑一遍迁移，返回 (新文本, 转换块数, 跳过清单, 是否有硬错误)。"""
    out, n_conv, skipped, hard = m.migrate_text(text)
    return out, n_conv, skipped, bool(hard)


# ── 形态：三种平铺分隔符 ────────────────────────────────
def test_colon_separator_converted():
    """`显示逻辑：文本` → 组头 + 子项，冒号被组头吸收。"""
    out, n, _skipped, hard = _run(block(li("显示逻辑：何时显示"), li("交互：点这里跳那里")))
    assert not hard and n == 1          # n = 转换块数
    assert "<li><strong>显示逻辑</strong>" in out
    assert "<li>何时显示</li>" in out
    assert "：" not in out.split("<strong>")[1].split("</strong>")[0]


def test_middot_separator_converted():
    """`交互 · 规则句` 同样转（间隔号被组头吸收，规则句下沉）。"""
    out, n, _skipped, hard = _run(block(li("交互 · 点按钮弹窗")))
    assert not hard and n == 1
    assert "<li><strong>交互</strong>" in out
    assert "点按钮弹窗" in out
    assert " · " not in out


def test_bare_label_with_nested_ul_converted():
    """标签后直跟嵌套 ul（无分隔符）→ 纯加粗，零字符丢弃。"""
    text = block("        <li>显示要素\n          <ul>\n            <li>标题</li>\n          </ul>\n        </li>\n")
    out, n, _skipped, hard = _run(text)
    assert not hard and n == 1
    assert "<li><strong>显示要素</strong>" in out and "<li>标题</li>" in out


def test_container_becomes_ul():
    """外层 <ol> 换成 <ul>（组头不该是编号项）。"""
    out, *_ = _run(block(li("显示逻辑：x")))
    assert "<ol>" not in out and out.lstrip().startswith("<ul>")


# ── 分组 ────────────────────────────────────────────────
def test_consecutive_same_label_merged():
    """连续同标签并成一个组头，子项按原顺序排。"""
    out, n, _skipped, hard = _run(block(li("显示逻辑：先讲 A"), li("显示逻辑：再讲 B")))
    assert not hard and n == 1
    assert out.count("<li><strong>显示逻辑</strong>") == 1
    assert out.index("<li>先讲 A</li>") < out.index("<li>再讲 B</li>")


def test_non_consecutive_same_label_kept_in_order():
    """非连续同标签各自成组，不重排文本。"""
    out, _n, _skipped, hard = _run(block(li("显示逻辑：A"), li("交互：B"), li("显示逻辑：C")))
    assert not hard
    assert out.count("<li><strong>显示逻辑</strong>") == 2
    assert out.index("<li>A</li>") < out.index("<li>B</li>") < out.index("<li>C</li>")


# ── 拒绝：整块跳过，不部分转换 ──────────────────────────
def test_mixed_label_block_skipped_whole():
    """顶层混入非三段式标签 → 整块跳过（交人工），一个字符都不动。"""
    text = block(li("显示逻辑：A"), li("主播收回：B"))
    out, n, skipped, hard = _run(text)
    assert n == 0 and not hard and len(skipped) == 1
    assert out == text


def test_plain_ordered_list_untouched():
    """无标签的普通编号列表静默不动（不是场景块，也不该被报为跳过）。"""
    text = block(li("第一步"), li("第二步"))
    out, n, skipped, hard = _run(text)
    assert (n, len(skipped), hard) == (0, 0, False)
    assert out == text


def test_unbalanced_block_reports_hard_failure():
    """嵌套 ul 未闭合 → 解析失败进硬错误清单（不写盘）。"""
    text = "      <ol>\n        <li>显示逻辑：\n          <ul>\n            <li>x</li>\n      </ol>\n"
    _out, n, _skipped, hard = _run(text)
    assert n == 0 and hard


# ── 安全：等价门与落盘 ──────────────────────────────────
def test_norm_strips_labels_suffix_and_whitespace():
    """比对基准：剥标签词、括注、分隔符与空白，只剩规则正文。"""
    assert m.norm("<li><strong>显示逻辑</strong><ul><li>甲</li></ul>") == "甲"
    assert m.norm("<li>显示逻辑（灰度）：甲</li>") == "甲"
    assert m.norm("<li>交互 · 甲</li>") == "甲"


def test_equivalence_gate_blocks_write(tmp_path, monkeypatch):
    """等价门不过 → 进硬错误、不写盘（构造一个正文会被改动的块）。"""
    f = tmp_path / "prd.md"
    src = block(li("显示逻辑：x"))
    f.write_text(src, encoding="utf-8")
    monkeypatch.setattr(m, "convert_block", lambda b, i: ("<ul>改坏了的正文</ul>", 1, 1))
    _n, hard = m.run_file(f, apply_=True, quiet=True)
    assert hard and f.read_text(encoding="utf-8") == src


def test_dry_run_does_not_write(tmp_path):
    """dry-run 只报数，文件不动、不落备份。"""
    f = tmp_path / "prd.md"
    src = block(li("显示逻辑：x"))
    f.write_text(src, encoding="utf-8")
    m.run_file(f, apply_=False, quiet=True)
    assert f.read_text(encoding="utf-8") == src
    assert not (tmp_path / "prd.md.bak").exists()


def test_apply_writes_and_backs_up(tmp_path):
    """--apply 落盘并留 .bak，备份等于原文。"""
    f = tmp_path / "prd.md"
    src = block(li("显示逻辑：x"))
    f.write_text(src, encoding="utf-8")
    m.run_file(f, apply_=True, quiet=True)
    assert f.read_text(encoding="utf-8") != src
    assert (tmp_path / "prd.md.bak").read_text(encoding="utf-8") == src


def test_idempotent_on_grouped_doc():
    """已组头的文档再跑 → 无可转块（幂等，不会二次套娃）。"""
    grouped = ("      <ul>\n        <li><strong>显示逻辑</strong>\n"
               "          <ul>\n            <li>x</li>\n          </ul>\n        </li>\n      </ul>\n")
    out, n, _skipped, hard = _run(grouped)
    assert (n, hard) == (0, False) and out == grouped


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
