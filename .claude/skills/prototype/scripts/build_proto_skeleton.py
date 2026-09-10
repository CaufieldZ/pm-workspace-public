#!/usr/bin/env python3
"""
可交互原型单步生成器（build 模式）
输入：项目信息 + View/页面结构 + page_fns 内容字典 + crud_js → 直接输出完整 HTML

约定：
  - page_fns 字典 key = (view_id, page_id)，value = callable() → html_str
  - 抽屉/模态/footer 可选 key: (view_id, 'drawer') / (view_id, 'modal') / (view_id, 'footer')
  - crud_js 直接作为字符串拼入 <script>
  - 生成即完整，可幂等重跑

用法（唯一 · 强制 src/scenes 分场景拆分，不分简单 / 大产物）：
    projects/{项目名}/scripts/
      build_proto_v1.py       # orchestrator，import src.scenes/ 各文件收 page_fns + 调 generate
      src/
        config.py             # project / views 数据
        scenes/
          __init__.py
          {view_id}_{page_id}.py  # 一文件一页面 ≤300 行，callable() → html_str

    禁把 page_fns 内联在 orchestrator 单文件里（post-prototype-split-check hook 拦截）。
    拆分结构见 .claude/runbooks/html-build-split.md §二。

导入方式：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/prototype/scripts'))
    from build_proto_skeleton import generate
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_builder import read_asset, render_head, write_html

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# 深色端（对客 App / Web 前台）该启用的组件层。未启用只 warn 不拦——存量项目
# 自带整套 crud.py CSS，强行拼入会改变已交付产物。
_DARK_DEVICES = ('phone', 'web-front')


def _css_packs(project: dict, views: list) -> str:
    """按 project['css_packs'] 拼组件层 CSS（拼在 prototype.css 之后、extra_css 之前）。"""
    packs = project.get('css_packs') or []
    if not packs and any(v.get('device') in _DARK_DEVICES for v in views):
        print('⚠️  深色端未启用组件层：project["css_packs"] = ["crypto-dark"] '
              '可直接用 cx- 组件，不必自写卡片 / 标签 / Tab / 浮层 CSS')
    return ''.join('\n' + read_asset(_ASSETS_DIR, f'{p}.css') for p in packs)


def _js_packs(project: dict) -> str:
    """组件层配套 JS（同名 .js，没有就跳过）。骨架的 switchTab 绑 .p-tab，形状与
    cx- 组件对不上，交互函数随包走。"""
    out = []
    for p in project.get('css_packs') or []:
        path = os.path.join(_ASSETS_DIR, f'{p}.js')
        if os.path.exists(path):
            out.append('\n' + read_asset(_ASSETS_DIR, f'{p}.js'))
    return ''.join(out)


def generate(project: dict, views: list, page_fns: dict, crud_js: str, output_path: str):
    """
    单步生成完整可交互原型 HTML，无 FILL marker。

    Args:
        project: {"name": str, "version": str}
        views: [{
            "id": str,           # e.g. "user-view"
            "name": str,         # Tab 显示名
            "icon": str,         # Tab icon emoji
            "theme": str,        # "dark" | "light"
            "device": str,       # "phone" | "web-front" | 省略（legacy web 全宽）
            "pages": [{"id": str, "name": str}, ...],
            # web-front device only (optional):
            "nav_items": [str, ...],
            # light theme only:
            "sidebar": [{"icon": str, "name": str}, ...],
        }, ...]
        page_fns: dict[tuple, callable]
            主页面 key: (view_id, page_id)            → callable() → html_str
            抽屉   key: (view_id, 'drawer')  → callable() → html_str（可选，省略则空白占位）
            模态   key: (view_id, 'modal')   → callable() → html_str（可选，light 主题）
            footer key: (view_id, 'footer')  → callable() → html_str（可选，web-front 主题，省略用默认）
        crud_js: str  # 直接插入 <script> 末尾的 JS 字符串（CRUD 操作函数等）
        output_path: 输出文件路径
    """
    _assemble(project, views, page_fns, crud_js, output_path, with_gnav=True)


def generate_single(project: dict, view: dict, page_fns: dict, crud_js: str, output_path: str):
    """单端单文件原型：一个 view = 一个独立 HTML，无 gnav 顶栏。

    多端项目（app / web / 后台）每端各调一次，产 N 个独立文件。每文件只含单端
    的纯粹导航范式，page id 不跨端、JS 全局 scope 天然不撞。

    Args 同 generate()，但 view 为单个 view dict（非 list）。page_fns 只需含该
    view 的 key。保留单个 .gnav-view-section.gnav-active 壳（不出顶栏 tab），让截图
    脚本与 goPage/openDrawer 的 || document fallback 零改动工作。
    """
    _assemble(project, [view], page_fns, crud_js, output_path, with_gnav=False)


def _assemble(project, views, page_fns, crud_js, output_path, with_gnav):
    missing = []
    for view in views:
        for page in view.get('pages', []):
            key = (view['id'], page['id'])
            if key not in page_fns:
                missing.append(f'({view["id"]}, {page["id"]})')
    if missing:
        raise KeyError(f'page_fns 缺少以下 key: {missing}')

    css = read_asset(_ASSETS_DIR, 'prototype.css') + _css_packs(project, views)
    js = read_asset(_ASSETS_DIR, 'prototype.js') + _js_packs(project)

    # 检测是否有任何 page_fns 返回 anno dict
    has_anno = False
    for fn in page_fns.values():
        if callable(fn):
            try:
                r = fn()
                if isinstance(r, dict) and 'anno' in r and r['anno']:
                    has_anno = True
                    break
            except Exception:
                pass

    parts = []
    parts.append(_head(project, css + (_ANNO_CSS if has_anno else '')))
    if with_gnav:
        parts.append(_gnav(project, views))
        parts.append('<div class="gnav-view-wrap">\n')
    else:
        parts.append('<div class="gnav-view-wrap" style="padding-top:0;">\n')

    for i, view in enumerate(views):
        parts.append(_view(project, view, i == 0, page_fns))

    parts.append('</div><!-- gnav-view-wrap -->\n')
    parts.append(_script(js, crud_js, has_anno=has_anno))
    parts.append('</body>\n</html>\n')

    html = '\n'.join(parts)
    write_html(output_path, html)

    print(f'✅ 可交互原型已生成: {output_path}')
    _print_summary(views)
    _warn_unreachable(html)


# ── 内部函数 ──────────────────────────────────────────────────────────


def _warn_unreachable(html):
    """生成即提示「点不到的页面 / 跳转死链」，别等评审现场才发现。"""
    from lib.proto_reachability import check_page_reachability

    reach = check_page_reachability(html)
    if reach.unreachable:
        print(f'   ⚠️  以下页面无入口，顺着 goPage 点不到: {" ".join(reach.unreachable)}')
        print('      → 从已可达页面加入口（Tab 栏 / 按钮 / 卡片 onclick）')
    if reach.dead_static:
        print(f'   ⚠️  goPage 指向本端不存在的页面（点了黑屏）: {" ".join(reach.dead_static)}')

def _head(project, css):
    title = f'{project["name"]} · 可交互原型 {project.get("version", "v1.0")}'
    return render_head(title, css)


def _gnav(project, views):
    tabs = []
    for i, v in enumerate(views):
        cls = ' on' if i == 0 else ''
        tabs.append(f'    <div class="gnav-tab{cls}" onclick="switchGlobalView({i})"><span class="gnav-ic">{v["icon"]}</span> {v["name"]}</div>')
    tabs_html = '\n'.join(tabs)
    return f'''<div class="gnav">
  <div class="gnav-logo">{project.get('logo_html', '<span>🔥</span>')} {project["name"]}</div>
  <div class="gnav-sep"></div>
  <div class="gnav-tabs">
{tabs_html}
  </div>
  <div class="gnav-right">
    <span class="gnav-ver">{project.get("version", "v1.0")}</span>
  </div>
</div>
'''


def _view(project, view, is_first, page_fns):
    if not view.get('pages'):
        raise ValueError(
            f"view {view.get('id')!r} 无 pages，无法渲染导航（nav logo / 面包屑硬取 pages[0]）——"
            f"先给该 view 补 pages 再生成"
        )
    active = ' gnav-active' if is_first else ''
    if view.get('theme') == 'light':
        return _light_view(project, view, active, page_fns)
    else:
        return _dark_view(project, view, active, page_fns)


def _dark_view(project, view, active, page_fns):
    pages_html = _build_pages_html(view, page_fns)
    device = view.get('device')

    if device == 'web-front':
        return _dark_web_front(project, view, active, pages_html, page_fns)

    drawer_content = page_fns.get((view['id'], 'drawer'), lambda: '')()

    if device == 'phone':
        return f'''
<div class="gnav-view-section{active}" id="{view["id"]}" style="background:#181A20;color:#EAECEF;min-height:calc(100vh - 52px);display:flex;justify-content:center;padding:0;">
<div class="app-mock">
  <div class="ph-status"><span>9:41</span><span>{project.get('status_html', '⚡📶')}</span></div>
  <div class="p-nav">
    <div class="p-nav-logo" onclick="goPage('{view["pages"][0]["id"]}')">{project.get('logo_html', '<span>🔥</span>')}<b>{view.get("nav_name", view["name"])}</b></div>
    <div class="p-nav-right">
      <button class="p-btn-out">{project.get('nav_right_html', '💰')} 资产</button>
    </div>
  </div>
{pages_html}

  <!-- 抽屉（底部上推，app-mock 内部绝对定位） -->
  <div class="p-overlay" id="drawerOverlay-{view["id"]}" onclick="closeDrawer()"></div>
  <div class="p-drawer" id="drawerPanel-{view["id"]}">
    <div class="p-drawer-bar"><h3>交易</h3><span class="dx" onclick="closeDrawer()">✕</span></div>
    <div class="p-drawer-body" style="padding:16px;">
{drawer_content}
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
    <div class="p-nav-logo" onclick="goPage('{view['pages'][0]['id']}')">{project.get('logo_html', '<span>🔥</span>')}<b>{view.get('nav_name', view['name'])}</b></div>
    <div class="p-nav-right">
      <button class="p-btn-out">{project.get('nav_right_html', '💰')} 资产</button>
      <button class="p-btn-blue">登录 / 注册</button>
    </div>
  </div>
{pages_html}

  <!-- 抽屉（右侧滑入，Web 全宽模式） -->
  <div class="p-overlay" id="drawerOverlay-{view["id"]}" onclick="closeDrawer()"></div>
  <div class="p-drawer" id="drawerPanel-{view["id"]}">
    <div class="p-drawer-bar"><h3>详情</h3><span class="dx" onclick="closeDrawer()">✕</span></div>
    <div class="p-drawer-body" style="padding:16px 20px;">
{drawer_content}
    </div>
  </div>
</div>
'''


def _dark_web_front(project, view, active, pages_html, page_fns):
    nav_items = view.get('nav_items', ['买币', '行情', '交易', '合约', '赚币'])
    nav_items_html = '\n    '.join(
        f'<div class="p-nav-item">{item} ▾</div>' for item in nav_items
    )
    footer_name = view.get('nav_name', view['name'])
    drawer_content = page_fns.get((view['id'], 'drawer'), lambda: '')()

    # footer 可由调用方提供，否则用默认三列结构
    default_footer = (
        '<div>\n'
        '        <h4>关于</h4>\n'
        '        <a>公司介绍</a><a>新闻中心</a><a>联系我们</a>\n'
        '      </div>\n'
        '      <div>\n'
        '        <h4>服务</h4>\n'
        '        <a>帮助中心</a><a>API 文档</a><a>费率说明</a>\n'
        '      </div>\n'
        '      <div>\n'
        '        <h4>合规</h4>\n'
        '        <a>服务条款</a><a>隐私政策</a><a>风险提示</a>\n'
        '      </div>'
    )
    footer_content = page_fns.get((view['id'], 'footer'), lambda: default_footer)()

    return f'''
<div class="gnav-view-section{active}" id="{view["id"]}">
<div class="web-front">
  <!-- 顶 nav（复用 .p-nav / .p-nav-item / .p-btn-blue）-->
  <div class="p-nav">
    <div class="p-nav-logo" onclick="goPage('{view["pages"][0]["id"]}')">{project.get('logo_html', '<span>🔥</span>')}<b>{view.get("nav_name", view["name"])}</b></div>
    {nav_items_html}
    <div class="p-nav-right">
      <button class="p-btn-out">{project.get('nav_right_html', '💰')} 资产</button>
      <button class="p-btn-blue">登录 / 注册</button>
    </div>
  </div>
{pages_html}

  <!-- footer（三列 + legal） -->
  <div class="wf-footer">
    <div class="wf-footer-cols">
{footer_content}
    </div>
    <div class="wf-footer-legal">
      <span>© 2026 {footer_name}. All rights reserved.</span>
      <span>Ver {view.get("version", "原型")}</span>
    </div>
  </div>

  <!-- 抽屉（右侧滑入，对客 web 模式） -->
  <div class="p-overlay" id="drawerOverlay-{view["id"]}" onclick="closeDrawer()"></div>
  <div class="p-drawer" id="drawerPanel-{view["id"]}">
    <div class="p-drawer-bar"><h3>详情</h3><span class="dx" onclick="closeDrawer()">✕</span></div>
    <div class="p-drawer-body" style="padding:16px 20px;">
{drawer_content}
    </div>
  </div>
</div><!-- .web-front -->
</div>
'''


def _light_view(project, view, active, page_fns):
    sidebar_items = []
    for i, item in enumerate(view.get('sidebar', [])):
        cls = ' on' if i == 0 else ''
        sidebar_items.append(f'    <div class="sb-item{cls}" onclick="swPage(this,{i})">{item["icon"]} {item["name"]}</div>')
    sidebar_html = '\n'.join(sidebar_items)

    pages = []
    for i, page in enumerate(view.get('pages', [])):
        hide = '' if i == 0 else ' hide'
        content = page_fns[(view['id'], page['id'])]()
        pages.append(f'''
    <!-- ═══════════════════════════════════════ -->
    <div class="ct page{hide}" id="page{i}">
{content}
    </div>''')
    pages_html = '\n'.join(pages)

    modal_content = page_fns.get(
        (view['id'], 'modal'),
        lambda: '      <p style="color:#848E9C;text-align:center;padding:40px 0;">弹窗内容</p>'
    )()

    return f'''
<div class="gnav-view-section{active}" id="{view["id"]}" style="background:#F5F6FA;color:#1D2129;">
<div class="layout">
  <div class="sb">
    <div class="sb-logo">{project.get('logo_html', '<span style="font-size:18px">🔥</span>')} {project.get('admin_name', '管理后台')}</div>
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
{modal_content}
    </div>
    <div class="modal-ft">
      <button class="b b-ghost" onclick="this.closest('.modal-bg').classList.remove('show')">取消</button>
      <button class="b b-blue" onclick="saveItem()">保存</button>
    </div>
  </div>
</div>
</div>
'''


def _build_pages_html(view, page_fns):
    """渲染所有页面 HTML，同时收集 anno 数据供骨架 JS 使用。"""
    pages = []
    for i, page in enumerate(view.get('pages', [])):
        show = ' show' if i == 0 else ''
        raw = page_fns[(view['id'], page['id'])]()
        # page_fns 支持两种返回格式：
        #   纯 str  → 直接作为页面内容，无 anno
        #   dict    → {'page': str, 'anno': [...]}
        if isinstance(raw, dict):
            content = raw.get('page', '')
            anno    = raw.get('anno', [])
        else:
            content = raw
            anno    = []
        # anno 数组序列化为 data-anno JSON 属性，骨架 JS 从此读取
        # 双引号属性 + html.escape（json 只转义 " 不转义 ' ，单引号属性遇文案撇号 Don't 即断链）
        import html as _html
        import json as _json
        anno_attr = f' data-anno="{_html.escape(_json.dumps(anno, ensure_ascii=False))}"' if anno else ''
        pages.append(f'''
<!-- ═══════════════════════════════════════ -->
<div class="p-page{show}" id="page-{view["id"]}-{page["id"]}" data-page="{page["id"]}"{anno_attr}>
{content}
</div>''')
    return '\n'.join(pages)


# ── Anno 骨架 CSS / JS（骨架内联，不依赖外部文件）────────────────────────

_ANNO_CSS = """
/* ═══ Proto Anno：Edge-Pin + Popover ═══
   Pin 挂在渲染壳上/下边缘，折线沿纵向导出，不占左右空间。
   Phone（375×812）/ Web-front 通用同一套机制。
════════════════════════════════════════ */
.proto-anno-pin{position:absolute;width:26px;height:26px;border-radius:50%;
  cursor:pointer;transform:translate(-50%,-50%);z-index:200;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:900;color:#fff;
  border:2.5px solid rgba(255,255,255,.9);
  transition:transform .18s ease,opacity .22s ease,box-shadow .18s ease;
  animation:_annoPinIn .2s ease}
@keyframes _annoPinIn{from{opacity:0;transform:translate(-50%,-50%) scale(.6)}
  to{opacity:1;transform:translate(-50%,-50%) scale(1)}}
.proto-anno-pin:hover{transform:translate(-50%,-50%) scale(1.22)!important}
.proto-anno-svg{position:absolute;top:0;left:0;overflow:visible;
  pointer-events:none;z-index:190}
.proto-anno-pop{position:absolute;z-index:300;background:#fff;border-radius:13px;
  padding:13px 15px 14px;width:252px;
  box-shadow:0 10px 40px rgba(0,0,0,.18),0 2px 8px rgba(0,0,0,.08);
  animation:_annoPopIn .15s ease;pointer-events:auto}
@keyframes _annoPopIn{from{opacity:0;transform:scale(.93)}to{opacity:1;transform:none}}
.proto-anno-pop-hd{display:flex;align-items:flex-start;gap:8px;margin-bottom:7px}
.proto-anno-pop-badge{width:22px;height:22px;border-radius:50%;font-size:11px;
  font-weight:900;color:#fff;display:flex;align-items:center;
  justify-content:center;flex-shrink:0;margin-top:1px}
.proto-anno-pop-title{font-size:13px;font-weight:700;color:#1C2030;line-height:1.3;flex:1}
.proto-anno-ptag{display:inline-block;font-size:9px;font-weight:700;padding:1px 6px;
  border-radius:8px;margin-left:4px;vertical-align:2px}
.proto-anno-pop-body{font-size:12px;color:#606C7A;line-height:1.68}
.proto-anno-pop-nav{display:flex;justify-content:space-between;align-items:center;
  margin-top:10px;padding-top:9px;border-top:1px solid #F0F2F5}
.proto-anno-pop-count{font-size:11px;color:#8B95A3}
.proto-anno-pop-btns{display:flex;gap:4px}
.proto-anno-pop-btn{width:26px;height:26px;border-radius:6px;background:#F3F4F6;
  border:none;cursor:pointer;font-size:13px;display:flex;align-items:center;
  justify-content:center;color:#606C7A}
.proto-anno-pop-btn:hover{background:#E5E7EB}
.proto-anno-pop-btn:disabled{opacity:.3;cursor:default}
.proto-anno-caret{position:absolute;width:12px;height:7px;overflow:hidden}
.proto-anno-caret::after{content:'';position:absolute;width:10px;height:10px;
  background:#fff;box-shadow:-1px -1px 4px rgba(0,0,0,.06);transform:rotate(45deg)}
.proto-anno-caret.down{bottom:-7px}
.proto-anno-caret.down::after{top:-5px;left:1px}
.proto-anno-caret.up{top:-7px}
.proto-anno-caret.up::after{bottom:-5px;left:1px;box-shadow:1px 1px 4px rgba(0,0,0,.06)}
/* debug grid（anno_debug:true 时显示）*/
.proto-anno-debug{position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;
  z-index:500;background-image:
    linear-gradient(rgba(0,127,255,.1) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,127,255,.1) 1px,transparent 1px);
  background-size:50px 50px}
.proto-anno-debug-label{position:absolute;font-size:9px;font-family:ui-monospace,monospace;
  color:rgba(0,127,255,.7);pointer-events:none;z-index:501;background:rgba(255,255,255,.8);
  padding:1px 3px;border-radius:2px}
"""

_ANNO_JS = r"""
/* ═══ Proto Anno Engine ═══════════════════════════════════════════════ */
(function(){
var PC={p0:'#2D81FF',p1:'#0ECB81',p2:'#d97706'};
var PL={p0:'P0',p1:'P1',p2:'P2'};
var PIN_R=13,PIN_OFF=9,MIN_GAP=34;
var _open=null;  // {wrap,page,n}

/* ── goPage 拦截：切页时重渲染 Pin ── */
var _origGoPage = typeof goPage === 'function' ? goPage : null;
window.goPage = function(name){
  if(_origGoPage) _origGoPage(name);
  // 延迟一帧等 DOM .show 切换完成
  setTimeout(function(){ _annoRefresh(); }, 30);
};

function _annoRefresh(){
  // 找当前 show 的 p-page，取 data-anno
  var pages = document.querySelectorAll('.p-page.show, .p-page[class*="show"]');
  pages.forEach(function(pg){
    _renderAnno(pg);
  });
}

function _renderAnno(pageEl){
  var raw = pageEl.getAttribute('data-anno');
  if(!raw) return;
  var items; try{ items=JSON.parse(raw); }catch(e){ return; }
  if(!items||!items.length) return;

  // wrap = 最近 ancestor .app-mock / .web-front / .gnav-view-section
  var wrap = pageEl.closest('.app-mock') || pageEl.closest('.web-front') || pageEl;
  var fw = wrap.offsetWidth  || 375;
  var fh = wrap.offsetHeight || 812;

  // clean previous
  wrap.querySelectorAll('.proto-anno-pin,.proto-anno-svg').forEach(function(e){ e.remove(); });

  var layout = _computeLayout(items, fw, fh);

  // SVG connector layer
  var svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.classList.add('proto-anno-svg');
  svg.setAttribute('width', fw); svg.setAttribute('height', fh);
  wrap.appendChild(svg);
  _drawLines(svg, items, layout, fw, fh, null);

  // pins
  items.forEach(function(a){
    var l=layout[a.n]; if(!l) return;
    var pin=document.createElement('div');
    pin.className='proto-anno-pin';
    pin.id='_apin_'+wrap.id+'_'+a.n;
    pin.textContent=a.n;
    pin.style.left=l.px+'px'; pin.style.top=l.py+'px';
    pin.style.background=PC[a.p]||'#2D81FF';
    pin.style.boxShadow='0 0 0 3px '+(PC[a.p]||'#2D81FF')+'44,0 4px 12px rgba(0,0,0,.22)';
    pin.addEventListener('click',function(e){
      e.stopPropagation();
      _doPin(wrap, items, layout, a.n, fw, fh);
    });
    wrap.appendChild(pin);
  });

  // debug grid
  if(wrap.dataset.annoDebug==='true'){
    var dbg=document.createElement('div'); dbg.className='proto-anno-debug';
    wrap.appendChild(dbg);
    for(var dx=0;dx<fw;dx+=50) for(var dy=0;dy<fh;dy+=50){
      var lbl=document.createElement('div'); lbl.className='proto-anno-debug-label';
      lbl.textContent=dx+','+dy; lbl.style.left=dx+'px'; lbl.style.top=dy+'px';
      wrap.appendChild(lbl);
    }
  }
}

function _computeLayout(items, fw, fh){
  var top=items.filter(function(a){ return a.ty<fh/2; }).sort(function(a,b){ return a.tx-b.tx; });
  var bot=items.filter(function(a){ return a.ty>=fh/2; }).sort(function(a,b){ return a.tx-b.tx; });
  function spread(grp){
    var xs=grp.map(function(a){ return a.tx; });
    for(var p=0;p<60;p++) for(var i=1;i<xs.length;i++)
      if(xs[i]-xs[i-1]<MIN_GAP){ var m=(xs[i]+xs[i-1])/2; xs[i-1]=m-MIN_GAP/2; xs[i]=m+MIN_GAP/2; }
    return xs.map(function(x){ return Math.max(PIN_R+4,Math.min(fw-PIN_R-4,x)); });
  }
  var tx=spread(top), bx=spread(bot), r={};
  top.forEach(function(a,i){ r[a.n]={px:tx[i],py:-(PIN_R+PIN_OFF),edge:'top'}; });
  bot.forEach(function(a,i){ r[a.n]={px:bx[i],py:fh+PIN_R+PIN_OFF,edge:'bot'}; });
  return r;
}

function _drawLines(svg, items, layout, fw, fh, hiN){
  svg.innerHTML='';
  items.forEach(function(a){
    var l=layout[a.n]; if(!l) return;
    var color=PC[a.p]||'#2D81FF';
    var isH=(hiN===a.n);
    var opa=hiN===null?0.28:(isH?1:0.05);
    var sw=isH?2.5:1.5;
    var edgeY=l.edge==='top'?0:fh;
    var pts=[a.tx+','+a.ty, a.tx+','+edgeY, l.px+','+edgeY, l.px+','+l.py].join(' ');
    var pl=document.createElementNS('http://www.w3.org/2000/svg','polyline');
    pl.setAttribute('points',pts); pl.setAttribute('fill','none');
    pl.setAttribute('stroke',color); pl.setAttribute('stroke-width',sw);
    pl.setAttribute('opacity',opa); pl.setAttribute('stroke-linecap','round');
    pl.setAttribute('stroke-linejoin','round');
    if(!isH) pl.setAttribute('stroke-dasharray','4,3');
    svg.appendChild(pl);
    if(isH){
      var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
      c.setAttribute('cx',a.tx); c.setAttribute('cy',a.ty); c.setAttribute('r','5');
      c.setAttribute('fill',color); svg.appendChild(c);
    }
  });
}

function _doPin(wrap, items, layout, n, fw, fh){
  if(_open && _open.n===n && _open.wrap===wrap){ _closeAll(); return; }
  _closeAll(true);
  _open={wrap:wrap,n:n};
  var a=items.find(function(i){ return i.n===n; }); if(!a) return;
  var l=layout[n]; if(!l) return;
  var idx=items.findIndex(function(i){ return i.n===n; });
  var color=PC[a.p]||'#2D81FF';
  // popover
  var pop=document.createElement('div');
  pop.className='proto-anno-pop'; pop.id='_apop_'+wrap.id+'_'+n;
  pop.innerHTML=
    '<div class="proto-anno-pop-hd">'+
      '<div class="proto-anno-pop-badge" style="background:'+color+'">'+n+'</div>'+
      '<span class="proto-anno-pop-title">'+a.title+
        '<span class="proto-anno-ptag" style="background:'+color+'22;color:'+color+'">'+
        (PL[a.p]||a.p)+'</span></span></div>'+
    '<div class="proto-anno-pop-body">'+a.text+'</div>'+
    (items.length>1?
      '<div class="proto-anno-pop-nav">'+
        '<span class="proto-anno-pop-count">'+(idx+1)+' / '+items.length+'</span>'+
        '<div class="proto-anno-pop-btns">'+
          '<button class="proto-anno-pop-btn" onclick="_annoNav('+(-1)+')"'+(idx===0?' disabled':'')+'">‹</button>'+
          '<button class="proto-anno-pop-btn" onclick="_annoNav(1)"'+(idx===items.length-1?' disabled':'')+'>›</button>'+
        '</div></div>'
    :'');
  pop.style.cssText='position:absolute;left:-9999px;top:-9999px;width:252px;visibility:hidden';
  wrap.appendChild(pop);
  var popH=pop.offsetHeight||90; var popW=252; var gap=10;
  var left=Math.max(-10,Math.min(l.px-popW/2,fw-popW+10));
  var top=l.edge==='top'? l.py-PIN_R-gap-popH : l.py+PIN_R+gap;
  pop.style.left=left+'px'; pop.style.top=top+'px'; pop.style.visibility='';
  var caret=document.createElement('div');
  caret.className='proto-anno-caret '+(l.edge==='top'?'down':'up');
  caret.style.left=Math.max(8,Math.min(l.px-left-6,popW-20))+'px';
  pop.appendChild(caret);
  // dim pins
  items.forEach(function(item){
    var el=document.getElementById('_apin_'+wrap.id+'_'+item.n);
    if(el) el.style.opacity=(item.n===n?'1':'0.2');
  });
  var svg=wrap.querySelector('.proto-anno-svg');
  if(svg){ var lyt=wrap._annoLayout; if(lyt) _drawLines(svg,items,lyt,fw,fh,n); }
}

window._annoNav=function(dir){
  if(!_open) return;
  var wrap=_open.wrap; var curN=_open.n;
  var pg=wrap.querySelector('.p-page.show')||wrap.querySelector('.p-page');
  if(!pg) return;
  var raw=pg.getAttribute('data-anno'); if(!raw) return;
  var items; try{ items=JSON.parse(raw); }catch(e){ return; }
  var idx=items.findIndex(function(i){ return i.n===curN; });
  var next=items[idx+dir]; if(!next) return;
  var l=wrap._annoLayout; var fw=wrap.offsetWidth||375; var fh=wrap.offsetHeight||812;
  _doPin(wrap,items,l,next.n,fw,fh);
};

function _closeAll(silent){
  if(!_open){ if(!silent) return; }
  document.querySelectorAll('.proto-anno-pop').forEach(function(p){ p.remove(); });
  if(_open){
    var wrap=_open.wrap;
    wrap.querySelectorAll('.proto-anno-pin').forEach(function(el){ el.style.opacity='1'; });
    var svg=wrap.querySelector('.proto-anno-svg');
    if(svg){
      var pg=wrap.querySelector('.p-page.show')||wrap.querySelector('.p-page');
      if(pg){
        var raw=pg.getAttribute('data-anno');
        var items; try{ items=JSON.parse(raw||'[]'); }catch(e){ items=[]; }
        var lyt=wrap._annoLayout||{};
        var fw=wrap.offsetWidth||375; var fh=wrap.offsetHeight||812;
        _drawLines(svg,items,lyt,fw,fh,null);
      }
    }
  }
  _open=null;
}

document.addEventListener('click',function(e){
  if(!e.target.closest('.proto-anno-pin')&&!e.target.closest('.proto-anno-pop')) _closeAll();
});
window.addEventListener('keydown',function(e){
  if(e.key==='Escape') _closeAll();
  if(e.key==='ArrowRight') window._annoNav(1);
  if(e.key==='ArrowLeft') window._annoNav(-1);
});

// 初始化：保存 layout + 渲染首页 anno
window.addEventListener('load', function(){
  document.querySelectorAll('.app-mock,.web-front').forEach(function(wrap){
    var pg=wrap.querySelector('.p-page.show');
    if(!pg) return;
    var raw=pg.getAttribute('data-anno'); if(!raw) return;
    var items; try{ items=JSON.parse(raw); }catch(e){ return; }
    if(!items||!items.length) return;
    var fw=wrap.offsetWidth||375; var fh=wrap.offsetHeight||812;
    var lyt=_computeLayout(items,fw,fh);
    wrap._annoLayout=lyt;
    _renderAnno(pg);
    // 保存 layout 供 _doPin 复用
    wrap.querySelectorAll('.proto-anno-pin').forEach(function(){});
    // patch: 在 _renderAnno 内执行后存 layout 到 wrap
    wrap._annoLayout=lyt;
  });
});
// 重新计算 layout 并存入 wrap（_renderAnno 调用完后）
var _origRender=_renderAnno;
_renderAnno=function(pageEl){
  _origRender(pageEl);
  var wrap=pageEl.closest('.app-mock')||pageEl.closest('.web-front')||pageEl;
  var raw=pageEl.getAttribute('data-anno'); if(!raw) return;
  var items; try{ items=JSON.parse(raw); }catch(e){ return; }
  var fw=wrap.offsetWidth||375; var fh=wrap.offsetHeight||812;
  wrap._annoLayout=_computeLayout(items,fw,fh);
};
})();
"""


def _script(js, crud_js, has_anno=False):
    crud_section = f'\n{crud_js}' if crud_js and crud_js.strip() else ''
    anno_section = f'\n{_ANNO_JS}' if has_anno else ''
    return f'''
<script>
{js}{crud_section}{anno_section}
</script>
'''


def _print_summary(views):
    total_pages = sum(len(v.get('pages', [])) for v in views)
    print(f'   {len(views)} 个 View, {total_pages} 个页面')
    device_labels = {'phone': '对客 App', 'web-front': '对客 web'}
    for v in views:
        pages = v.get('pages', [])
        ids = ', '.join(p['id'] for p in pages) if pages else '(无页面)'
        if v.get('theme') == 'light':
            label = '内部后台'
        else:
            label = device_labels.get(v.get('device'), '对客 web（legacy 全宽）')
        print(f'   {v["name"]}（{label}）: {ids}')


# ══════════════════════════════════════════════════════════════════════════
# 第二范式：单 phone + scene chips（V8 标杆类）
# 适用：纯 App 端、多场景 ≥ 5 个、所有场景在同一台手机内切换显示
# 与 generate() 区别：无 gnav / 无多 View / 无设备壳切换，外层只有一个 .phone
# ══════════════════════════════════════════════════════════════════════════

def generate_chips_phone(
    project: dict,
    nav_groups: list,
    scene_fns: dict,
    output_path: str,
    extra_css: str = '',
    extra_js: str = '',
    footnote: str = '',
):
    """
    单 phone + scene chips 范式生成器。

    Args:
        project: {"name": str, "version": str, "subtitle": str}
        nav_groups: [[(sid, label), ...], ...]  顶部 chips 分组，组间用 .sep 分隔
        scene_fns: {sid: callable() → html_str}
                   每个 fn 返回 `<div class="scr [on]" id="s-{sid}">...</div>` 整块
                   第一个 sid（nav_groups[0][0][0]）默认带 .on
        output_path: 输出文件路径
        extra_css: 项目自定义 CSS（拼在框架基础 CSS 之后；项目可覆盖 token）
        extra_js: 项目自定义 JS（拼在框架基础 JS 之后；含场景内交互函数）
        footnote: phone 下方提示文字（多行 HTML，可含 <br/>）

    Returns: 无（写文件 + stdout 摘要）
    """
    missing = [g[0] for grp in nav_groups for g in grp if g[0] not in scene_fns]
    if missing:
        raise KeyError(f'scene_fns 缺少以下 sid: {missing}')

    first_sid = nav_groups[0][0][0]
    first_label = nav_groups[0][0][1]

    scenes_html = '\n'.join(scene_fns[sid]() for grp in nav_groups for sid, _ in grp)

    parts = []
    parts.append(_chips_head(project, extra_css))
    parts.append(_chips_body_open(project))
    parts.append(_chips_nav(nav_groups, first_sid))
    parts.append(f'\n<div class="phone" id="phone">\n{scenes_html}\n<div class="toast" id="toastBox"></div>\n</div>\n')
    parts.append(f'\n<div class="cur-scene" id="curScene">{first_label}</div>\n')
    if footnote:
        parts.append(f'\n<div class="chips-footnote" style="margin-top:12px;font-size:10px;color:#64748b;text-align:center;max-width:380px;line-height:1.6;">{footnote}</div>\n')
    parts.append(_chips_script(extra_js))
    parts.append('</body>\n</html>\n')

    write_html(output_path, ''.join(parts))

    total = sum(len(g) for g in nav_groups)
    print(f'✅ 可交互原型已生成（chips-phone 范式）: {output_path}')
    print(f'   {total} 个 scene 分 {len(nav_groups)} 组')


# chips 范式基础 CSS（框架 token + 单 phone 壳 + chips 导航 + cur-scene 标签）
# 业务样式由项目通过 extra_css 追加
_CHIPS_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
:root{
  --bg:#0B0E11; --bg2:#1B1D22; --bg3:#2B2F36;
  --accent:#2979FF; --green:#0ECB81; --red:#F6465D; --gold:#FCD535;
  --text:#EAECEF; --text2:#848E9C; --text3:#5E6673; --border:#2B2F36;
  --dark:#0B0E11; --dark2:#161A1E; --dark3:#2B3139; --dark-text:#EAECEF; --dark-text2:#848E9C; --dark-text3:#5E6673; --blue:#2979FF;
}
*{margin:0;padding:0;box-sizing:border-box;}
body.chips-phone-paradigm{font-family:'Noto Sans SC',-apple-system,sans-serif;background:#101114;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px 16px 60px;}
.hd{text-align:center;margin-bottom:14px;}
.hd h1{font-size:17px;font-weight:900;color:#e2e8f0;letter-spacing:-.3px;}
.hd .sub{font-size:11px;color:#64748b;margin-top:3px;}
.nav{display:flex;flex-wrap:wrap;gap:3px;justify-content:center;max-width:480px;margin-bottom:14px;}
.nav button{font-family:inherit;font-size:9.5px;font-weight:700;padding:4px 7px;border-radius:4px;border:1px solid #334155;background:#1e293b;color:#94a3b8;cursor:pointer;transition:.12s;}
.nav button:hover{border-color:var(--accent);color:var(--accent);}
.nav button.on{background:var(--accent);border-color:var(--accent);color:#fff;}
.nav .sep{width:1px;background:#334155;margin:0 2px;}
.phone{width:375px;height:812px;background:var(--bg);border-radius:44px;border:3px solid #222;overflow:hidden;position:relative;box-shadow:0 0 0 1px #111,0 24px 80px rgba(0,0,0,.5);flex-shrink:0;}
.phone::before{content:'';position:absolute;top:8px;left:50%;transform:translateX(-50%);width:120px;height:32px;background:#000;border-radius:18px;z-index:80;pointer-events:none;}
.scr{position:absolute;top:0;left:0;right:0;bottom:0;display:none;flex-direction:column;}
.scr.on{display:flex;}
.slbl{display:none;}
.cur-scene{margin-top:14px;background:var(--accent);color:#fff;font-size:11px;font-weight:700;padding:5px 14px;border-radius:12px;letter-spacing:.3px;text-align:center;}
.phone *::-webkit-scrollbar{display:none;width:0;height:0;}
.phone *{scrollbar-width:none;-ms-overflow-style:none;}
.nav::-webkit-scrollbar{display:none;}
.toast{position:absolute;left:50%;top:38%;transform:translateX(-50%);background:rgba(0,0,0,.85);color:var(--text);padding:10px 18px;border-radius:8px;font-size:12px;z-index:90;border:1px solid var(--border);max-width:280px;text-align:center;line-height:1.6;opacity:0;transition:opacity .25s;pointer-events:none;}
.toast.show{opacity:1;}
"""

# chips 范式基础 JS（chip 切换 + cur-scene 标签 + toast 工具）
_CHIPS_BASE_JS = r"""
function go(id){
  document.querySelectorAll('.scr').forEach(function(s){s.classList.remove('on');});
  var t = document.getElementById('s-'+id);
  if (t) t.classList.add('on');
  document.querySelectorAll('.nav button').forEach(function(b){
    b.classList.toggle('on', b.dataset.s === id);
  });
  var labelEl = document.getElementById('curScene');
  var btn = document.querySelector('.nav button[data-s="'+id+'"]');
  if (labelEl && btn) labelEl.textContent = btn.textContent;
  if (t){ var bd = t.querySelector('.body'); if (bd) bd.scrollTop = 0; }
}
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('.nav button').forEach(function(b){
    b.addEventListener('click', function(){ if (b.dataset.s) go(b.dataset.s); });
  });
});
function _toast(msg){
  var box = document.getElementById('toastBox');
  if (!box) return;
  box.textContent = msg;
  box.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(function(){ box.classList.remove('show'); }, 2000);
}
"""


def _chips_head(project, extra_css):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{project["name"]} · 可交互原型 {project.get("version", "v1.0")}</title>
<style>
{_CHIPS_BASE_CSS}
{extra_css}
</style>
</head>
<body class="chips-phone-paradigm">
'''


def _chips_body_open(project):
    subtitle = project.get('subtitle', '')
    sub_html = f'<div class="sub">{subtitle}</div>' if subtitle else ''
    return f'''
<div class="hd">
  <h1>{project["name"]} · 可交互原型 {project.get("version", "v1.0")}</h1>
  {sub_html}
</div>
'''


def _chips_nav(nav_groups, first_sid):
    parts = ['<div class="nav" id="nav">']
    for i, grp in enumerate(nav_groups):
        if i > 0:
            parts.append('  <div class="sep"></div>')
        for sid, label in grp:
            cls = ' class="on"' if sid == first_sid else ''
            parts.append(f'  <button data-s="{sid}"{cls}>{label}</button>')
    parts.append('</div>')
    return '\n'.join(parts) + '\n'


def _chips_script(extra_js):
    extra = f'\n{extra_js}' if extra_js and extra_js.strip() else ''
    return f'''
<script>
{_CHIPS_BASE_JS}{extra}
</script>
'''


# ══════════════════════════════════════════════════════════════════════════
# 示例（python3 build_proto_skeleton.py 直接运行生成 demo HTML）
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    project = {"name": "示例产品", "version": "v1.0", "css_packs": ["crypto-dark"]}
    views = [
        {
            "id": "app-view",
            "name": "对客 App",
            "icon": "📱",
            "theme": "dark",
            "device": "phone",
            "pages": [
                {"id": "app-main", "name": "首页"},
                {"id": "app-detail", "name": "详情"},
            ],
        },
        {
            "id": "web-view",
            "name": "对客 web",
            "icon": "🖥",
            "theme": "dark",
            "device": "web-front",
            "nav_name": "示例产品",
            "pages": [
                {"id": "web-main", "name": "首页"},
                {"id": "web-detail", "name": "详情"},
            ],
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
            ],
        },
    ]

    def _placeholder(label, goto=None):
        # 每个页面都得有入口，否则评审点不到（_warn_unreachable 会报）
        link = (
            f'<div style="margin-top:14px;color:#007FFF;cursor:pointer;font-size:13px;" '
            f'onclick="goPage(\'{goto}\')">进入详情 →</div>'
        ) if goto else ''
        return (
            f'<div style="height:300px;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;color:#848E9C;font-size:14px;">{label}{link}</div>'
        )

    page_fns = {
        ('app-view',  'app-main'):   lambda: _placeholder('App 首页', 'app-detail'),
        ('app-view',  'app-detail'): lambda: _placeholder('App 详情'),
        ('web-view',  'web-main'):   lambda: _placeholder('Web 首页', 'web-detail'),
        ('web-view',  'web-detail'): lambda: _placeholder('Web 详情'),
        ('mgt-view',  'mgt-list'):   lambda: _placeholder('列表管理'),
        ('mgt-view',  'mgt-data'):   lambda: _placeholder('数据看板'),
    }

    crud_js = '// CRUD helpers placeholder\nfunction saveItem() { console.log("saved"); }'

    _HERE = os.path.dirname(os.path.abspath(__file__))
    OUTPUT = os.path.join(_HERE, 'build-proto-demo.html')
    generate(project, views, page_fns, crud_js, OUTPUT)
