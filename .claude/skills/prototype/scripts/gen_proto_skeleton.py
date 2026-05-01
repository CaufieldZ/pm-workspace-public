#!/usr/bin/env python3
"""
可交互原型骨架生成器
输入：项目信息 + View/页面结构 → 输出：骨架 HTML（CSS + JS + 全局导航 + 页面占位）

用法：
    1. 复制本脚本到 projects/{项目名}/scripts/gen_proto_v1.py
    2. 修改底部的 project / views 数据
    3. python3 gen_proto_v1.py
    4. 骨架文件生成到 deliverables/，用户确认后进入 Step B（fill 脚本填充页面）

导入方式（在项目脚本开头）：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/scripts'))
    from gen_proto_skeleton import generate_skeleton
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_builder import expand_css_imports, write_html

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def generate_skeleton(project: dict, views: list, output_path: str):
    """
    生成原型骨架 HTML 文件。

    Args:
        project: {"name": str, "version": str}
        views: [{
            "id": str,           # e.g. "user-view"
            "name": str,         # Tab 显示名
            "icon": str,         # Tab icon emoji
            "theme": str,        # "dark" | "light"
            "pages": [{"id": str, "name": str}, ...],
            # light theme only:
            "sidebar": [{"icon": str, "name": str}, ...],
        }, ...]
        output_path: 输出文件路径
    """
    css = _read_file('prototype.css')
    js = _read_file('prototype.js')

    parts = []
    parts.append(_head(project, css))
    parts.append(_gnav(project, views))
    parts.append('<div class="gnav-view-wrap">\n')

    for i, view in enumerate(views):
        parts.append(_view(view, i == 0))

    parts.append('</div><!-- gnav-view-wrap -->\n')
    parts.append(_script(js))
    parts.append('</body>\n</html>\n')

    write_html(output_path, '\n'.join(parts))

    print(f'✅ 原型骨架已生成: {output_path}')
    _print_summary(views)


def _read_file(filename):
    path = os.path.join(_ASSETS_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if filename.endswith('.css'):
        content = expand_css_imports(content, _ASSETS_DIR)
    return content


def _head(project, css):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project["name"]} · 可交互原型 {project.get("version", "v1.0")}</title>
<style>
{css}
</style>
</head>
<body>
'''


def _gnav(project, views):
    tabs = []
    for i, v in enumerate(views):
        cls = ' on' if i == 0 else ''
        tabs.append(f'    <div class="gnav-tab{cls}" onclick="switchGlobalView({i})"><span class="gnav-ic">{v["icon"]}</span> {v["name"]}</div>')
    tabs_html = '\n'.join(tabs)
    return f'''<div class="gnav">
  <div class="gnav-logo"><span>🔥</span> {project["name"]}</div>
  <div class="gnav-sep"></div>
  <div class="gnav-tabs">
{tabs_html}
  </div>
  <div class="gnav-right">
    <span class="gnav-ver">{project.get("version", "v1.0")}</span>
  </div>
</div>
'''


def _view(view, is_first):
    active = ' gnav-active' if is_first else ''
    if view.get('theme') == 'light':
        return _light_view(view, active)
    else:
        return _dark_view(view, active)


def _dark_view(view, active):
    pages = []
    for i, page in enumerate(view.get('pages', [])):
        show = ' show' if i == 0 else ''
        pages.append(f'''
<!-- ═══════════════════════════════════════ -->
<div class="p-page{show}" id="page-{page["id"]}">
  <!-- FILL_START:page-{page["id"]} -->
  <!-- FILL_END:page-{page["id"]} -->
</div>''')
    pages_html = '\n'.join(pages)

    is_phone = view.get('device') == 'phone'

    if is_phone:
        return f'''
<div class="gnav-view-section{active}" id="{view["id"]}" style="background:#181A20;color:#EAECEF;min-height:calc(100vh - 52px);display:flex;justify-content:center;padding:0;">
<div class="app-mock">
  <div class="ph-status"><span>9:41</span><span>⚡📶</span></div>
  <div class="p-nav">
    <div class="p-nav-logo" onclick="goPage('{view["pages"][0]["id"]}')"><span>🔥</span><b>{view.get("nav_name", view["name"])}</b></div>
    <div class="p-nav-right">
      <button class="p-btn-out">💰 资产</button>
    </div>
  </div>
{pages_html}

  <!-- 抽屉（底部上推，app-mock 内部绝对定位） -->
  <div class="p-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
  <div class="p-drawer" id="drawerPanel">
    <div class="p-drawer-bar"><h3>交易</h3><span class="dx" onclick="closeDrawer()">✕</span></div>
    <div class="p-drawer-body" style="padding:16px;">
      <!-- FILL_START:drawer-{view["id"]} -->
      <!-- FILL_END:drawer-{view["id"]} -->
    </div>
  </div>
  <div class="home-ind"></div>
</div>
</div>
'''
    else:
        return f'''
<div class="gnav-view-section{active}" id="{view["id"]}" style="background:#181A20;color:#EAECEF;min-height:calc(100vh - 52px);">
  <div class="p-nav">
    <div class="p-nav-logo" onclick="goPage('{view["pages"][0]["id"]}')"><span>🔥</span><b>{view.get("nav_name", view["name"])}</b></div>
    <div class="p-nav-right">
      <button class="p-btn-out">💰 资产</button>
      <button class="p-btn-blue">登录 / 注册</button>
    </div>
  </div>
{pages_html}

  <!-- 抽屉（右侧滑入，Web 全宽模式） -->
  <div class="p-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
  <div class="p-drawer" id="drawerPanel">
    <div class="p-drawer-bar"><h3>详情</h3><span class="dx" onclick="closeDrawer()">✕</span></div>
    <div class="p-drawer-body" style="padding:16px 20px;">
      <!-- FILL_START:drawer-{view["id"]} -->
      <!-- FILL_END:drawer-{view["id"]} -->
    </div>
  </div>
</div>
'''


def _light_view(view, active):
    sidebar_items = []
    for i, item in enumerate(view.get('sidebar', [])):
        cls = ' on' if i == 0 else ''
        sidebar_items.append(f'    <div class="sb-item{cls}" onclick="swPage(this,{i})">{item["icon"]} {item["name"]}</div>')
    sidebar_html = '\n'.join(sidebar_items)

    pages = []
    for i, page in enumerate(view.get('pages', [])):
        hide = '' if i == 0 else ' hide'
        pages.append(f'''
    <!-- ═══════════════════════════════════════ -->
    <div class="ct page{hide}" id="page{i}">
      <!-- FILL_START:page-{page["id"]} -->
      <!-- FILL_END:page-{page["id"]} -->
    </div>''')
    pages_html = '\n'.join(pages)

    return f'''
<div class="gnav-view-section{active}" id="{view["id"]}" style="background:#F5F6FA;color:#1D2129;">
<div class="layout">
  <div class="sb">
    <div class="sb-logo"><span style="font-size:18px">🔥</span> 管理后台</div>
    <div class="sb-grp">{view.get("sidebar_group", "功能管理")}</div>
{sidebar_html}
  </div>
  <div class="mn">
    <div class="tb">
      <div class="bc">🏠 首页 / <b id="bcText">{view["pages"][0]["name"]}</b></div>
      <div style="font-size:12px;color:var(--text2);display:flex;align-items:center;gap:10px;">
        <span style="background:var(--green-l);color:#2E7D32;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">测试环境</span>
        <span>👤 运营</span>
      </div>
    </div>
{pages_html}
  </div>
</div>

<!-- 弹窗 -->
<div class="modal-bg" id="editModal">
  <div class="modal">
    <div class="modal-hd"><span id="modalTitle">编辑</span><span class="close" onclick="this.closest('.modal-bg').classList.remove('show')">✕</span></div>
    <div class="modal-bd">
      <!-- FILL_START:modal-{view["id"]} -->
      <p style="color:#848E9C;text-align:center;padding:40px 0;">弹窗内容待填充</p>
      <!-- FILL_END:modal-{view["id"]} -->
    </div>
    <div class="modal-ft">
      <button class="b b-ghost" onclick="this.closest('.modal-bg').classList.remove('show')">取消</button>
      <button class="b b-blue" onclick="saveItem()">保存</button>
    </div>
  </div>
</div>
</div>
'''


def _script(js):
    return f'''
<script>
{js}

// FILL_START:crud
// FILL_END:crud
</script>
'''


def _print_summary(views):
    total_pages = sum(len(v.get('pages', [])) for v in views)
    print(f'   {len(views)} 个 View, {total_pages} 个页面占位')
    for v in views:
        pages = v.get('pages', [])
        ids = ', '.join(p['id'] for p in pages) if pages else '(无页面)'
        theme = '深色' if v.get('theme') != 'light' else '浅色'
        print(f'   {v["name"]}（{theme}）: {ids}')


# ══════════════════════════════════════════════════════════════════════════
# 示例数据
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    project = {"name": "示例产品", "version": "v1.0"}
    views = [
        {
            "id": "user-view",
            "name": "用户端",
            "icon": "📱",
            "theme": "dark",
            "pages": [
                {"id": "main", "name": "首页"},
                {"id": "detail", "name": "详情"},
            ]
        },
        {
            "id": "mgt-view",
            "name": "管理台",
            "icon": "⚙️",
            "theme": "light",
            "sidebar_group": "功能管理",
            "sidebar": [
                {"icon": "📋", "name": "列表管理"},
                {"icon": "📊", "name": "数据看板"},
            ],
            "pages": [
                {"id": "mgt-list", "name": "列表管理"},
                {"id": "mgt-data", "name": "数据看板"},
            ]
        },
    ]
    generate_skeleton(project, views, "proto-demo.html")
