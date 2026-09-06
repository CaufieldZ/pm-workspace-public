#!/usr/bin/env python3
"""HTML 骨架生成共享工具。

提供 CSS @import 展开、skill 资源文件读取、HTML 文件写出等通用函数，
被 build_imap_skeleton / build_proto_skeleton / gen_flow_base 共用。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CSS_IMPORT_RE = re.compile(r"@import\s+url\(['\"]([^'\"]+)['\"]\);?")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

_WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def expand_css_imports(css_text: str, base_dir: str | Path, _seen: set | None = None) -> str:
    """递归展开 CSS 中的 @import url('...') 相对引用。

    inline 进 HTML <style> 后相对路径会失效，必须在读取时就替换成被引文件内容。

    副作用：会顺手剥离 CSS 注释 /* ... */（防止注释里的 @import 被误展开）。
    所以经过此函数后 <style> 块里不会再有 CSS 注释——不影响浏览器渲染，但
    如需保留版本/作者信息请放在 <!-- HTML 注释 --> 而非 CSS /* 注释 */。
    远程 @import（http/https）保留不展开，由浏览器加载。
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
        if not target.exists():
            raise FileNotFoundError(
                f"CSS @import 目标不存在：{rel!r}（在 {base_dir} 下解析为 {target}）—— "
                f"检查引用它的 CSS 里的 @import 路径"
            )
        inner = target.read_text(encoding='utf-8')
        return expand_css_imports(inner, target.parent, _seen)

    return CSS_IMPORT_RE.sub(resolve, stripped)


def get_author() -> str:
    """从 .claude/skills/_shared/workspace.json 读取 author 字段。"""
    cfg = _WORKSPACE_ROOT / ".claude" / "skills" / "_shared" / "workspace.json"
    try:
        return json.loads(cfg.read_text(encoding='utf-8')).get("author", "")
    except (json.JSONDecodeError, OSError):
        return ""


def get_skel_version() -> str:
    """读 workspace.json 的 skel_version（如 'v1'）。缺失/异常返回 ''。

    供 HTML 产物注入 <meta name="x-pm-skel-version">，drift checker 据此判旧产物该刷新。
    """
    cfg = _WORKSPACE_ROOT / ".claude" / "skills" / "_shared" / "workspace.json"
    try:
        return json.loads(cfg.read_text(encoding='utf-8')).get("skel_version", "")
    except (json.JSONDecodeError, OSError):
        return ""


def read_skill_file(skill_name: str, filename: str) -> str:
    """读取 .claude/skills/{skill_name}/references/{filename}。"""
    path = _WORKSPACE_ROOT / ".claude" / "skills" / skill_name / "references" / filename
    return path.read_text(encoding='utf-8')


def read_asset(assets_dir: str | Path, filename: str) -> str:
    """读取 skill 的 assets/{filename}；CSS 自动展开 @import 相对引用。

    被 build_imap_skeleton / build_proto_skeleton / build_arch_skeleton 共用。
    """
    path = Path(assets_dir) / filename
    content = path.read_text(encoding='utf-8')
    if filename.endswith('.css'):
        content = expand_css_imports(content, assets_dir)
    return content


def _provenance_comment() -> str:
    """从入口脚本（sys.argv[0]）推产物来源，生成 HTML 顶部指路注释。

    换 session 后模型读 HTML 首屏即知「改哪个脚本 + 怎么重生」，不必靠 deliverable-source-gate
    事后拦（那只在尝试 Write/Edit 时才触发、且靠文件名启发式匹配，会漏）。
    入口非项目/skill 生成脚本（解释器交互 / pytest / 无 argv）返回空串，不乱标。
    """
    entry = sys.argv[0] if sys.argv else ""
    if not entry:
        return ""
    name = Path(entry).name
    if "pytest" in name or name.startswith("python") or not (name.endswith(".py") or name.endswith(".js")):
        return ""
    try:
        src = str(Path(entry).resolve().relative_to(_WORKSPACE_ROOT))
    except (ValueError, OSError):
        src = name
    runner = "node" if name.endswith(".js") else "python3"
    return (f"<!-- ⚠ 生成产物，勿直接改此 HTML。源脚本：{src} —— "
            f"改源后跑 `{runner} {src}` 重生（直接改会被下次重生覆盖）-->\n")


def render_head(title: str, css: str, extra_css: str = '', extra_meta: str = '') -> str:
    """生成统一的 HTML <head> + <body> 开启块。

    Args:
        title: <title> 内容（调用方自行拼接产物名 / 项目名 / 版本号）
        css: 主 CSS 字符串（已通过 read_asset 展开 @import）
        extra_css: 项目自定义 CSS（拼在主 CSS 之后；空字符串自动跳过）
        extra_meta: 额外的 <meta> 标签（如 description），换行附加在 viewport 之后
    """
    skel = get_skel_version()
    skel_meta = f'\n<meta name="x-pm-skel-version" content="{skel}">' if skel else ''
    meta_block = f'\n{extra_meta}' if extra_meta and extra_meta.strip() else ''
    extra_block = f'\n{extra_css}' if extra_css and extra_css.strip() else ''
    prov = _provenance_comment()
    return f'''<!DOCTYPE html>
{prov}<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">{skel_meta}{meta_block}
<title>{title}</title>
<style>
{css}{extra_block}
</style>
</head>
<body>
'''


def write_html(output_path: str, html_content: str) -> None:
    """创建目录（如不存在）并写入 UTF-8 HTML。"""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
