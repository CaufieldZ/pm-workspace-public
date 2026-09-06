"""scene_match 回归：场景编号严格匹配 + 父子覆盖 + 单字符锚点形态。

防回归：旧 `grep -qi` 忽略大小写单字符匹配，让 `A` 在 class="add" / <a> 里假阳
（commit 历史多次因单字母 ID 误判）。新规则要求锚点形态。
"""
import pytest
from lib.scene_match import (
    extract_scene_ids,
    find_missing_ids,
    id_covered_in_text,
    scene_code_report,
)


class TestMultiCharID:
    """多字符 / 带 `-` 的 ID：严格词边界（前非字母数字 / 后非字母数字-）。"""

    @pytest.mark.parametrize("sid,text", [
        ("B-1a", "正文里 scene-B-1a 出现"),
        ("B-1", 'id="scene-B-1"'),
        ("A-4", "引用 A-4 场景"),
        ("M-2", ">M-2<"),
    ])
    def test_covered(self, sid, text):
        assert id_covered_in_text(sid, text) is True

    @pytest.mark.parametrize("sid,text", [
        ("B-1", "scene-B-10"),     # 不吞 B-10
        ("B-1", "scene-B-1a"),     # 不吞 B-1a
        ("B-1", "XB-1"),           # 前缀字母吞噬
        ("A-4", "A-40"),           # 不吞 A-40
        ("A-4", "XA-4"),           # 前缀字母
    ])
    def test_not_covered(self, sid, text):
        assert id_covered_in_text(sid, text) is False


class TestSingleCharID:
    """单字符 ID（A/B/M）：必须命中 9 种锚点形态之一，裸文本不假阳。"""

    @pytest.mark.parametrize("text", [
        "A-1 子场景",            # 父子覆盖 A-N
        ">A<",                   # 文本节点
        "A · 社区签到",          # 锚点 · 业务名
        'phone-label">A',        # IMAP phone-label
        "gd-num\">A",            # PART 编号容器
        'id="scene-A"',          # scene id
        "PART A",                # PART A
    ])
    def test_anchor_forms_covered(self, text):
        assert id_covered_in_text("A", text) is True

    @pytest.mark.parametrize("text", [
        'class="add"',           # 历史假阳：add 含小写 a，大写 A 不命中
        "address book",          # 小写 a 不算
        "普通正文里提到 A 和 B",  # 裸文本无锚点形态
        "<a>链接</a>",           # 标签名不是锚点形态
    ])
    def test_no_false_positive(self, text):
        assert id_covered_in_text("A", text) is False


def test_empty_and_lowercase_sid():
    assert id_covered_in_text("", "anything") is False
    # 小写 / 非单字符大写但无连字符的非 [A-Z] 单字符
    assert id_covered_in_text("a", "a-1") is False


def test_find_missing_ids():
    text = "覆盖了 A-1 和 B-2a"
    assert find_missing_ids(["A-1", "B-2a", "C-1"], text) == ["C-1"]


def test_scene_code_report():
    # 引用越界 = FAIL 级；未覆盖 = warn 级（delta 只覆盖本轮场景）
    text = "phone-label\">B-1 · 直播间\n引用 X-9 场景"
    undefined, missing = scene_code_report(["A-1", "B-1", "B-2"], text)
    assert undefined == ["X-9"]
    assert missing == ["A-1", "B-2"]


def test_scene_code_report_all_covered():
    text = "B-1 · 直播间 B-2 · 榜单"
    undefined, missing = scene_code_report(["B-1", "B-2"], text)
    assert undefined == []
    assert missing == []


def test_extract_scene_ids(tmp_path):
    content = """| 编号 | 场景 |
|------|------|
| A | 主流程 |
| A-1 | 登录 |
| B-1a/b/c | 子流程 |
| View | 视图（噪音过滤） |
| P0 | 占位（噪音） |
"""
    f = tmp_path / "scene-list.md"
    f.write_text(content, encoding="utf-8")
    ids = extract_scene_ids(f)
    # B-1a/b/c 斜杠展开为 3 条；View / P0 是噪音过滤
    assert ids == ["A", "A-1", "B-1a", "B-1b", "B-1c"]


def test_extract_scene_ids_missing_file(tmp_path):
    # 文件不存在返回空，不抛异常
    assert extract_scene_ids(tmp_path / "nope.md") == []


def test_extract_scene_ids_keeps_row_with_dashes_in_desc(tmp_path):
    # 回归：说明列含 '---' 的真实场景行不能被当分隔行误删（'---' in line 过宽）
    content = """| 编号 | 场景 | 说明 |
|------|------|------|
| A-1 | 正常 | 无 |
| B-2 | 转账 | 用户 A --- B 转账链路 |
"""
    f = tmp_path / "scene-list.md"
    f.write_text(content, encoding="utf-8")
    ids = extract_scene_ids(f)
    assert ids == ["A-1", "B-2"]  # B-2 保留，分隔行（第 2 行）仍跳过
