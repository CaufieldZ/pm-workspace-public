#!/usr/bin/env python3
"""
交互大图单步生成器（build 模式）
输入：项目信息 + PART/Scene 结构 + scene_fns 内容字典 → 直接输出完整 HTML

约定：
  - scene_fns 字典 key = scene id，value = callable() → html_str | {'flow':.., 'anno':..}
    · 返回 str = 仅手机流(无注解，多数 scene)
    · 返回 dict = {'flow': 手机流 HTML, 'anno': ann-card HTML}；ann-card 下沉到 .flow 下方
      .scene-anno 区(竖向自然滚动可达，不再钉横向流最右端），徽章 hover 联动由内置 JS 承载
  - 生成即完整，可幂等重跑，改内容只改 scene_fns 对应函数

用法（唯一 · 强制 src/scenes 分场景拆分，不分简单 / 大产物）：
    projects/{项目}/scripts/
      build_imap_v{N}.py     # orchestrator，import src/scenes/ 各文件收 scene_fns + 调 generate
      src/
        config.py            # project / legends / parts
        scenes/
          a.py / b.py / ...  # 一文件一主场景 ≤300 行，def scene_{id}() → html_str
                             # 跨端表 → cross_data_flow.py
    post-imap-split-check hook 在 imap-*.html 产出时校验，找不到 src/scenes/*.py 即 FAIL。
    详见 .claude/skills/interaction-map/SKILL.md §硬规则 11 + .claude/runbooks/html-build-split.md §二

导入方式（在 orchestrator build_imap_v{N}.py 开头）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/scripts'))
    sys.path.insert(0, os.path.dirname(__file__))  # 让 src 包可 import
    from build_imap_skeleton import generate
    from src.config import project, legends, parts
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _validators import validate_part_stories, validate_part_stories_from_scene_list
from lib.html_builder import read_asset, render_head, write_html

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def generate(
    project: dict,
    legends: list,
    parts: list,
    scene_fns: dict,
    output_path: str,
    scene_list_path: str = None,
):
    """
    单步生成完整交互大图 HTML，无 FILL marker。

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
            "story": str,       # 一句话用户故事陈述（≤ 30 字），或 "—" 跳过
            "scenes": [{"id": str, "name": str, "trigger": str, "device": str}, ...],
            # scene.device: "phone" | "web"（仅影响调用者知晓，build 模式由 scene_fns 控制壳类型）
            # custom theme only:
            "bg": str, "color": str, "num_bg": str,
            # optional:
            "cross_table": bool  # True → 调用 scene_fns["cross-data-flow"]()
        }, ...]
        scene_fns: dict[str, callable]
            key 格式: "scene-{id.lower()}" 或 "cross-data-flow"
            value: callable() → html_str | {'flow':.., 'anno':..}
                - str: 仅 .flow 手机流内容
                - dict: {'flow': 手机流 HTML, 'anno': ann-card HTML}
                  ann-card 渲染到 .flow 下方 .scene-anno 区(下沉，可竖向滚到)
        output_path: 输出文件路径
        scene_list_path: 可选；不传则从 output_path 反推 projects/.../scene-list.md
    """
    if scene_list_path is None:
        import re
        m = re.search(r'projects/([^/]+(?:/[^/]+)?)/deliverables/', output_path)
        if m:
            candidate = os.path.join(_ROOT, 'projects', m.group(1), 'scene-list.md')
            if os.path.exists(candidate):
                scene_list_path = candidate

    if scene_list_path:
        validate_part_stories_from_scene_list(parts, scene_list_path)
    else:
        validate_part_stories(parts)

    missing = []
    for part in parts:
        for scene in part.get('scenes', []):
            sid = f'scene-{scene["id"].lower()}'
            if sid not in scene_fns:
                missing.append(sid)
        if part.get('cross_table') and 'cross-data-flow' not in scene_fns:
            missing.append('cross-data-flow')
    if missing:
        raise KeyError(f'scene_fns 缺少以下 key: {missing}')

    css = read_asset(_ASSETS_DIR, 'interaction-map.css')
    js = read_asset(_ASSETS_DIR, 'interaction-map.js')

    html_parts = []
    html_parts.append(_head(project, css))
    html_parts.append(_progress_bar())
    html_parts.append(_side_nav(parts))
    html_parts.append(_header(project, legends))
    html_parts.append('<div class="cv">\n')

    for part in parts:
        html_parts.append(_part_divider(part))
        for scene in part.get('scenes', []):
            html_parts.append(_scene_section(scene, scene_fns))
        if part.get('cross_table'):
            html_parts.append(_cross_table_section(scene_fns))

    html_parts.append('</div><!-- .cv -->\n')
    html_parts.append(_script(js))
    html_parts.append('</body>\n</html>\n')

    write_html(output_path, '\n'.join(html_parts))

    print(f'✅ 交互大图已生成: {output_path}')
    _print_summary(parts)


# ── 内部函数 ──────────────────────────────────────────────────────────

def _head(project, css):
    title = f'{project["name"]} · {project.get("subtitle", "交互大图")}'
    return render_head(title, css)


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


def _story_html(story):
    if not story or story == '—':
        return ''
    return f'<div class="part-story" style="font-size:14px;opacity:.7;margin-bottom:6px;font-weight:400;line-height:1.5;">{story}</div>\n    '


def _part_divider(part):
    theme = part.get('theme', 'viewer')
    story = _story_html(part.get('story', ''))

    if theme == 'custom':
        bg = part.get('bg', 'linear-gradient(135deg,#0B0E11,#161b22)')
        color = part.get('color', '#EAECEF')
        num_bg = part.get('num_bg', 'rgba(255,255,255,.08)')
        return f'''
<!-- ████████████████████████████████████████████████████████████████████████ -->
<div class="gd fade-section" id="{part["id"]}" style="background:{bg};color:{color};">
  <span class="gd-num" style="background:{num_bg};">{part["num"]}</span>
  <div>
    {story}<h2>{part["name"]}</h2>
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
    {story}<h2>{part["name"]}</h2>
    <div class="gd-desc">{part.get("desc", "")}</div>
  </div>
</div>
'''


def _scene_section(scene, scene_fns):
    sid = f'scene-{scene["id"].lower()}'
    result = scene_fns[sid]()
    if isinstance(result, dict):
        flow_html = result.get('flow', '')
        anno_html = result.get('anno', '')
    else:
        flow_html = result
        anno_html = ''
    anno_block = f'  <div class="scene-anno">\n{anno_html}\n  </div>\n' if anno_html.strip() else ''
    return f'''
<!-- ═══════════════════════════════════════ -->
<div class="fade-section" id="{sid}">
  <div class="st">
    <h2>{scene["id"]} · {scene["name"]}</h2>
    <span class="note">{scene.get("trigger", "")}</span>
  </div>
  <div class="flow">
{flow_html}
  </div>
{anno_block}</div>
'''


def _cross_table_section(scene_fns):
    content = scene_fns['cross-data-flow']()
    return f'''
<!-- ═══════════════════════════════════════ -->
<div class="fade-section" id="cross-data-flow">
  <div class="st">
    <h2>跨端数据流</h2>
    <span class="note">前后台联动链路</span>
  </div>
{content}
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
    print(f'   {len(parts)} 个 PART, {total_scenes} 个 Scene, {cross} 个跨端表')
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
        extra = ' + 跨端表' if part.get('cross_table') else ''
        print(f'   {part["num"]}: {ids}{extra}')


# ══════════════════════════════════════════════════════════════════════════
# 示例（python3 build_imap_skeleton.py 直接运行生成 demo HTML）
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
        {"color": "purple", "label": "Web 端"},
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
            "story": "用户从 Feed 发现活动，点击进入参与流程",
            "scenes": [
                {"id": "A", "name": "首页", "trigger": "启动 App", "device": "phone"},
                {"id": "A-1", "name": "Web 交易页", "trigger": "浏览器访问", "device": "web"},
            ],
        },
        {
            "id": "part1",
            "num": "PART 1",
            "name": "🖥 管理台",
            "desc": "CMS 后台",
            "theme": "admin",
            "dot_color": "purple",
            "story": "运营配置活动规则，发布后即时生效",
            "scenes": [
                {"id": "M-1", "name": "配置管理", "trigger": "运营登录", "device": "web"},
            ],
        },
        {
            "id": "part2",
            "num": "PART 2",
            "name": "🔄 跨端数据流",
            "desc": "前后台联动",
            "theme": "cross-end",
            "dot_color": "green",
            "story": "—",
            "scenes": [],
            "cross_table": True,
        },
    ]

    def _scene_a():
        # dict 返回：手机流 + 下沉 ann-card，演示 anno-n ↔ ann-num hover 联动
        flow = (
            '<div class="flow-col">'
            '<span class="phone-label">A · 首页</span>'
            '<div class="phone" style="height:600px;background:#181A20;position:relative;display:flex;'
            'align-items:center;justify-content:center;color:#848E9C;font-size:14px;">Scene A 内容'
            '<div class="anno amber" style="top:48px;left:16px;right:16px;height:64px;">'
            '<div class="anno-n amber">1</div></div>'
            '</div>'
            '<div class="flow-note">示例 Scene A — 启动 App 后的首屏</div>'
            '</div>'
        )
        anno = (
            '<div class="ann-card">'
            '<div class="card-title">📋 首页说明 <span class="ann-tag p0">P0</span></div>'
            '<div class="ann-item"><div class="ann-num amber">1</div>'
            '<div class="ann-text"><b>顶部活动入口</b><br>启动即展示当前活动，点击进入参与流程</div></div>'
            '</div>'
        )
        return {'flow': flow, 'anno': anno}

    def _scene_a1():
        return (
            '<div class="flow-col">'
            '<span class="phone-label">A-1 · Web 交易页</span>'
            '<div class="web" style="height:400px;background:#0B0E11;display:flex;align-items:center;'
            'justify-content:center;color:#848E9C;font-size:14px;">Scene A-1 内容</div>'
            '<div class="flow-note">示例 Scene A-1 — 浏览器直访</div>'
            '</div>'
        )

    def _scene_m1():
        return (
            '<div class="flow-col">'
            '<span class="phone-label">M-1 · 配置管理</span>'
            '<div class="web" style="height:400px;background:#F5F6FA;display:flex;align-items:center;'
            'justify-content:center;color:#333;font-size:14px;">Scene M-1 内容</div>'
            '<div class="flow-note">示例 Scene M-1 — 运营后台配置页</div>'
            '</div>'
        )

    def _cross():
        return (
            '<table style="width:100%;border-collapse:collapse;font-size:13px;color:var(--text);">'
            '<tr><th style="padding:8px 12px;background:var(--bg2);text-align:left;font-weight:700;">数据项</th>'
            '<th style="padding:8px 12px;background:var(--bg2);text-align:left;font-weight:700;">App</th>'
            '<th style="padding:8px 12px;background:var(--bg2);text-align:left;font-weight:700;">Web</th>'
            '<th style="padding:8px 12px;background:var(--bg2);text-align:left;font-weight:700;">CMS</th></tr>'
            '<tr><td style="padding:8px 12px;border-bottom:1px solid var(--border);">示例字段</td>'
            '<td style="padding:8px 12px;border-bottom:1px solid var(--border);">只读展示</td>'
            '<td style="padding:8px 12px;border-bottom:1px solid var(--border);">只读展示</td>'
            '<td style="padding:8px 12px;border-bottom:1px solid var(--border);">可配置</td></tr>'
            '</table>'
        )

    scene_fns = {
        'scene-a':         _scene_a,
        'scene-a-1':       _scene_a1,
        'scene-m-1':       _scene_m1,
        'cross-data-flow': _cross,
    }

    _HERE = os.path.dirname(os.path.abspath(__file__))
    OUTPUT = os.path.join(_HERE, 'build-imap-demo.html')
    generate(project, legends, parts, scene_fns, OUTPUT)
