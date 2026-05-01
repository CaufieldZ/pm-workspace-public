#!/usr/bin/env python3
"""HTML 骨架生成共享工具。

提供 CSS @import 展开、skill 资源文件读取、HTML 文件写出等通用函数，
消除 gen_imap_skeleton / gen_proto_skeleton / gen_flow_base 之间的重复代码。
"""
import json
import os
import re
from pathlib import Path

CSS_IMPORT_RE = re.compile(r"@import\s+url\(['\"]([^'\"]+)['\"]\);?")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

_WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def expand_css_imports(css_text: str, base_dir: str | Path, _seen: set | None = None) -> str:
    """递归展开 CSS 中的 @import url('...') 相对引用。

    inline 进 HTML <style> 后相对路径会失效，必须在读取时就替换成被引文件内容。
    """
    if _seen is None:
        _seen = set()
    stripped = CSS_COMMENT_RE.sub("", css_text)
    base_dir = Path(base_dir)

    def resolve(m):
        rel = m.group(1)
        if rel.startswith(('http://', 'https://')):
            return m.group(0)
        target = (base_dir / rel).resolve()
        key = str(target)
        if key in _seen:
            return ""
        _seen.add(key)
        inner = target.read_text(encoding='utf-8')
        return expand_css_imports(inner, target.parent, _seen)

    return CSS_IMPORT_RE.sub(resolve, stripped)


def get_author() -> str:
    """从 .claude/skills/_shared/workspace.json 读取 author 字段。"""
    cfg = _WORKSPACE_ROOT / ".claude" / "skills" / "_shared" / "workspace.json"
    try:
        return json.loads(cfg.read_text(encoding='utf-8')).get("author", "")
    except Exception:
        return ""


def read_skill_file(skill_name: str, filename: str) -> str:
    """读取 .claude/skills/{skill_name}/references/{filename}。"""
    path = _WORKSPACE_ROOT / ".claude" / "skills" / skill_name / "references" / filename
    return path.read_text(encoding='utf-8')


def write_html(output_path: str, html_content: str) -> None:
    """创建目录（如不存在）并写入 UTF-8 HTML。"""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
