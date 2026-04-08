#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
# pm-ws-canary-236a5364
"""
交互大图骨架生成器
输入：项目信息 + PART/Scene 结构 → 输出：骨架 HTML（CSS + JS + 侧导航 + PART + Scene 占位）

用法：
    1. 复制本脚本到 projects/{项目名}/scripts/gen_imap_v1.py
    2. 修改底部的 project / legends / parts / OUTPUT 数据
    3. python3 gen_imap_v1.py
    4. 骨架文件生成到 deliverables/，用户确认后进入 Step B（fill 脚本填充 Scene）

导入方式（在项目脚本开头）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/references'))
    from gen_imap_skeleton import generate_skeleton
"""
import os

# 资源文件目录：始终指向本文件所在的 references/ 目录
_REFS_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_skeleton(project: dict, legends: list, parts: list, output_path: str):
    """
    生成骨架 HTML 文件。

    Args:
        project: {"name": str, "subtitle": str, "nav_desc": str}
        legends: [{"color": str, "label": str}, ...]
        parts: [{
            "id": str,          # e.g. "part0"
            "num": str,         # e.g. "PART 0"
            "name": str,        # e.g. "🚀 用户端核心交互"
            "desc": str,        # 模块描述
            "theme": str,       # "frontend" | "admin" | "cross-end" | "custom"
            "dot_color": str,   # 侧导航圆点颜色变量名
            "scenes": [{"id": str, "name": str, "trigger": str, "device": str}, ...],
            # scene.device: "phone" | "web"（默认 "phone"）— 决定 fill 生成的设备壳类型
            # custom theme only:
            "bg": str,          # CSS background value
            "color": str,       # CSS color value
            "num_bg": str,      # .gd-num background
            # optional:
            "cross_table": bool # True → 插入跨端数据流表格占位
        }, ...]
        output_path: 输出文件路径
    """
    css = _read_file('interaction-map.css')
    js = _read_file('interaction-map.js')

    html_parts = []
    html_parts.append(_head(project, css))
    html_parts.append(_progress_bar())
    html_parts.append(_side_nav(parts))
    html_parts.append(_header(project, legends))
    html_parts.append('<div class="cv">\n')

    for part in parts:
        html_parts.append(_part_divider(part))
        for scene in part.get('scenes', []):
            html_parts.append(_scene_placeholder(scene))
        if part.get('cross_table'):
            html_parts.append(_cross_table_placeholder())

    html_parts.append('</div><!-- .cv -->\n')
    html_parts.append(_script(js))
    html_parts.append('</body>\n</html>\n')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))

    print(f'✅ 骨架已生成: {output_path}')
    _print_summary(parts)


# ── 内部函数 ──────────────────────────────────────────────────────────

def _read_file(filename):
    path = os.path.join(_REFS_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _head(project, css):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project["name"]} · {project.get("subtitle", "交互大图")}</title>
<style>
{css}
</style>
</head>
<body>
'''


def _progress_bar():
    return '<div class="progress-bar" id="progressBar"></div>\n'


def _side_nav(parts):
    lines = ['<nav class="side-nav" id="sideNav">']
    for part in parts:
        dot = part.get('dot_color', 'blue')
        lines.append(f'  <a href="#{part["id"]}"><div class="dot" style="background:var(--{dot});"></div>{part["num"]} {part["name"]}</a>')
        for scene in part.get('scenes', []):
            sid = f'scene-{scene["id"].lower()}'
            lines.append(f'  <a href="#{sid}"><div class="dot" style="background:var(--{dot});"></div>{scene["id"]} {scene["name"]}</a>')
    lines.append('</nav>\n')
    return '\n'.join(lines)


def _header(project, legends):
    legend_items = []
    for lg in legends:
        legend_items.append(f'    <span class="item"><span class="line" style="border-color:var(--{lg["color"]});"></span>{lg["label"]}</span>')
    legend_items.append('    <span style="margin-left:6px;" class="tag new">NEW</span>')
    legend_items.append('    <span class="tag chg">改动</span>')
    legends_html = '\n'.join(legend_items)

    return f'''<header class="hd">
  <div>
    <h1>{project["name"]} · {project.get("subtitle", "交互大图")}</h1>
    <div class="sub">{project.get("nav_desc", "")}</div>
  </div>
  <div class="lg">
{legends_html}
  </div>
</header>
'''


THEME_MAP = {
    'frontend': 'gd viewer',
    'admin': 'gd host',
    'cross-end': 'gd cross',
}

def _part_divider(part):
    theme = part.get('theme', 'viewer')

    if theme == 'custom':
        bg = part.get('bg', 'linear-gradient(135deg,#0B0E11,#161b22)')
        color = part.get('color', '#EAECEF')
        num_bg = part.get('num_bg', 'rgba(255,255,255,.08)')
        return f'''
<!-- ████████████████████████████████████████████████████████████████████████ -->
<div class="gd fade-section" id="{part["id"]}" style="background:{bg};color:{color};">
  <span class="gd-num" style="background:{num_bg};">{part["num"]}</span>
  <div>
    <h2>{part["name"]}</h2>
    <div class="gd-desc">{part.get("desc", "")}</div>
  </div>
</div>
'''
    else:
        cls = THEME_MAP.get(theme, 'gd viewer')
        return f'''
<!-- ████████████████████████████████████████████████████████████████████████ -->
<div class="{cls} fade-section" id="{part["id"]}">
  <span class="gd-num">{part["num"]}</span>
  <div>
    <h2>{part["name"]}</h2>
    <div class="gd-desc">{part.get("desc", "")}</div>
  </div>
</div>
'''


def _scene_placeholder(scene):
    sid = f'scene-{scene["id"].lower()}'
    return f'''
<!-- ═══════════════════════════════════════ -->
<div class="fade-section" id="{sid}">
  <div class="st">
    <h2>{scene["id"]} · {scene["name"]}</h2>
    <span class="note">{scene.get("trigger", "")}</span>
  </div>
  <div class="flow">
    <!-- FILL_START:{sid} -->
    <!-- FILL_END:{sid} -->
  </div>
</div>
'''


def _cross_table_placeholder():
    return '''
<!-- ═══════════════════════════════════════ -->
<div class="fade-section" id="cross-data-flow">
  <div class="st">
    <h2>跨端数据流</h2>
    <span class="note">前后台联动链路</span>
  </div>
  <!-- FILL_START:cross-data-flow -->
  <!-- FILL_END:cross-data-flow -->
</div>
'''


def _script(js):
    return f'''
<script>
{js}
</script>
'''


def _print_summary(parts):
    total_scenes = sum(len(p.get('scenes', [])) for p in parts)
    cross = sum(1 for p in parts if p.get('cross_table'))
    print(f'   {len(parts)} 个 PART, {total_scenes} 个 Scene 占位, {cross} 个跨端表占位')
    for part in parts:
        scenes = part.get('scenes', [])
        if scenes:
            items = []
            for s in scenes:
                dev = s.get('device', 'phone')
                icon = '📱' if dev == 'phone' else '🖥'
                items.append(f'{s["id"]}{icon}')
            ids = ', '.join(items)
        else:
            ids = '(无 Scene)'
        extra = ' + 跨端表占位' if part.get('cross_table') else ''
        print(f'   {part["num"]}: {ids}{extra}')


# ══════════════════════════════════════════════════════════════════════════
# 以下为示例数据，复制到项目脚本后修改
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    project = {
        "name": "示例项目",
        "subtitle": "交互大图 v1.0",
        "nav_desc": "用户端 → 管理台 → 跨端 ｜ 分组阅读",
    }

    legends = [
        {"color": "blue",   "label": "布局"},
        {"color": "green",  "label": "新增"},
        {"color": "red",    "label": "策略"},
        {"color": "purple", "label": "Web端"},
        {"color": "amber",  "label": "流程"},
    ]

    parts = [
        {
            "id": "part0",
            "num": "PART 0",
            "name": "🚀 用户端",
            "desc": "App 端核心交互",
            "theme": "frontend",
            "dot_color": "amber",
            "scenes": [
                {"id": "A", "name": "首页", "trigger": "启动 App", "device": "phone"},
                {"id": "A-1", "name": "Web 交易页", "trigger": "浏览器访问", "device": "web"},
            ]
        },
        {
            "id": "part1",
            "num": "PART 1",
            "name": "🖥 管理台",
            "desc": "CMS 后台",
            "theme": "admin",
            "dot_color": "purple",
            "scenes": [
                {"id": "M-1", "name": "配置管理", "trigger": "运营登录", "device": "web"},
            ]
        },
        {
            "id": "part2",
            "num": "PART 2",
            "name": "🔄 跨端数据流",
            "desc": "前后台联动",
            "theme": "cross-end",
            "dot_color": "green",
            "scenes": [],
            "cross_table": True,
        },
    ]

    OUTPUT = "skeleton-demo.html"
    generate_skeleton(project, legends, parts, OUTPUT)
