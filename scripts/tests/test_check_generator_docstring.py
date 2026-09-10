"""check_generator_docstring 纯函数测试。

锁：退化 docstring（只回显文件名 / 空）被拦；有「怎么跑/产物/改哪/路径」线索的放行。
"""
import pytest
from check_generator_docstring import check_header, extract_header


@pytest.mark.parametrize("name,header", [
    # 只回显文件名 + 标题，无定位线索
    ("gen_ppt_x_v1.py", "gen_ppt_x_v1.py — 10x 风控 PPT 生成脚本"),
    ("gen_ppt_y_v1.js", "gen_ppt_y_v1.js — 方案全景 · 领导版"),
    ("gen_deck_z.py", ""),  # 空
])
def test_degenerate_flagged(name, header):
    assert check_header(name, header), f"{name} 应被拦"


@pytest.mark.parametrize("name,header", [
    # 有「改哪重生」
    ("build_proto_v5.py", "活动中心原型。改场景只改 proto_v5/scenes/*.py，重跑本脚本即可。"),
    # 有输入/产物路径锚点
    ("gen_deck_a.js", "竞品 deck。内容源：projects/x/deliverables/report.md；类名源：.claude/skills/ppt/assets/deck-template.html"),
    # 有运行命令
    ("gen_arch_b.py", "架构图集。用法：python3 gen_arch_b.py，产物落 deliverables/arch-b.drawio"),
])
def test_adequate_clean(name, header):
    assert check_header(name, header) == [], f"{name} 应放行"


def test_extract_py_docstring():
    text = '#!/usr/bin/env python3\n"""做什么。\n\n用法：python3 x.py\n"""\nimport os\n'
    h = extract_header(text, ".py")
    assert "用法" in h and "python3 x.py" in h


def test_extract_py_hash_comments():
    text = "#!/usr/bin/env python3\n# 生成脚本\n# 产物落 deliverables/\nimport os\n"
    h = extract_header(text, ".py")
    assert "产物落 deliverables/" in h


def test_extract_js_block():
    text = "#!/usr/bin/env node\n/**\n * deck 生成\n * 产物：ppt-x.html\n */\nconst fs=require('fs')\n"
    h = extract_header(text, ".js")
    assert "产物：ppt-x.html" in h


def test_extract_js_line_comments():
    text = "// gen deck\n// 跑：node gen.js\nconst x=1\n"
    h = extract_header(text, ".js")
    assert "跑：node gen.js" in h
