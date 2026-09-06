#!/usr/bin/env python3
"""架构图集单步生成器（build 模式）

输入：项目信息 + Tab 列表 + tab_fns 内容字典（+ extra_css/extra_js）→ 直接输出完整 HTML

约定：
  - tab_fns 字典 key = tab id（与 nav 列表 id 对齐），value = callable() → html_str
  - 每个 tab fn 返回 `.pw` 容器内部内容（含 `.pg` 包裹），框架负责套 `<div class="pw a" id="t{id}">`
  - extra_css/extra_js 拼在 framework css/js 之后（项目可覆盖 token 或加 class）
  - 生成即完整，可幂等重跑

用法（简单产物，≤8 个 Tab）：
    复制本脚本到 projects/{项目}/scripts/build_arch_v1.py
    填 project / nav / tab_fns / OUTPUT → python3 build_arch_v1.py

用法（大产物，>8 个 Tab 或 > 1500 行）：
    scripts/build_arch_v{N}.py        # orchestrator
    scripts/arch_v{N}/
      tabs/tab_{id}.py                # 一文件一 Tab，callable() → html_str
      __init__.py
      [styles.py / js_helpers.py]     # 业务样式 / 业务 JS（可选）

导入方式：
    import sys, os
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/architecture-diagrams/scripts'))
    from build_arch_skeleton import generate
"""
import html
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))

from lib.html_builder import read_asset, render_head, write_html

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def generate(
    project: dict,
    nav: list,
    tab_fns: dict,
    output_path: str,
    extra_css: str = '',
    extra_js: str = '',
):
    """单步生成完整架构图集 HTML。

    Args:
        project: {"name": str, "subtitle": str (可选)}
        nav: [(tab_id, label), ...]  顶部 tab 顺序；第一个默认 active
        tab_fns: {tab_id: callable() → html_str}
                 每个 fn 返回 `.pw` 内部完整内容（建议套 `<div class="pg">...</div>`）
        output_path: 输出文件路径
        extra_css: 项目自定义 CSS（拼在 framework 之后）
        extra_js: 项目自定义 JS（拼在 framework 之后）
    """
    missing = [tid for tid, _ in nav if tid not in tab_fns]
    if missing:
        raise KeyError(f'tab_fns 缺少以下 tab id: {missing}')

    css = read_asset(_ASSETS_DIR, 'css-template.css')
    js = read_asset(_ASSETS_DIR, 'js-template.js')

    parts = []
    parts.append(_head(project, css, extra_css))
    parts.append(_tab_bar(nav))
    for i, (tid, _) in enumerate(nav):
        is_first = i == 0
        active = ' a' if is_first else ''
        body = tab_fns[tid]()
        parts.append(f'<div class="pw{active}" id="t{tid}">{body}</div>\n')
    parts.append(_script(js, extra_js))
    parts.append('</body>\n</html>\n')

    write_html(output_path, ''.join(parts))
    print(f'✅ 架构图集已生成: {output_path}')
    print(f'   {len(nav)} 个 Tab')


def _head(project, css, extra_css):
    subtitle = project.get('subtitle', '')
    # project 侧数据不转义会破坏 HTML（项目名/副标题含 " & < 时）
    sub_meta = f'<meta name="description" content="{html.escape(subtitle, quote=True)}">' if subtitle else ''
    title = html.escape(f'{project["name"]} · 架构图集')
    return render_head(title, css, extra_css=extra_css, extra_meta=sub_meta)


def _tab_bar(nav):
    items = []
    for i, (_, label) in enumerate(nav):
        cls = ' a' if i == 0 else ''
        items.append(
            f'  <div class="t{cls}" onclick="sw({i})"><span class="i">{i}</span>{html.escape(label)}</div>'
        )
    return '<div class="tb">\n' + '\n'.join(items) + '\n</div>\n'


def _script(js, extra_js):
    extra = f'\n{extra_js}' if extra_js and extra_js.strip() else ''
    return f'\n<script>\n{js}{extra}\n</script>\n'


# ══════════════════════════════════════════════════════════════════════
# Demo（python3 build_arch_skeleton.py 直接生成示例 HTML）
# ══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    project = {"name": "示例方案", "subtitle": "Architecture Demo"}
    nav = [
        ('0', '一页全景'),
        ('1', '账户结构'),
        ('2', '资金流'),
    ]

    def _pg(title, body):
        return (
            f'<div class="pg">\n'
            f'<h1>{title}</h1>\n'
            f'<div class="sub">DEMO</div>\n'
            f'<div class="rl"></div>\n'
            f'{body}\n'
            f'</div>\n'
        )

    tab_fns = {
        '0': lambda: _pg(
            '一页全景',
            '<div class="co co-b"><strong>总体目标</strong>方案 demo</div>'
            '<div class="fx mt"><div class="cd"><div class="st">入口</div></div>'
            '<div class="cd"><div class="st">中台</div></div>'
            '<div class="cd"><div class="st">出口</div></div></div>',
        ),
        '1': lambda: _pg(
            '账户结构',
            '<table><thead><tr><th>账户</th><th>用途</th></tr></thead>'
            '<tbody><tr><td>主账户</td><td>持仓</td></tr>'
            '<tr><td>子账户</td><td>对冲</td></tr></tbody></table>',
        ),
        '2': lambda: _pg(
            '资金流',
            '<div class="co co-g"><strong>结论</strong>跨方异步结算</div>',
        ),
    }

    _HERE = os.path.dirname(os.path.abspath(__file__))
    OUTPUT = os.path.join(_HERE, 'archive', 'build-arch-demo.html')
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    generate(project, nav, tab_fns, OUTPUT)
    try:
        from lib.skill_log import emit as _sl
        _sl("architecture-diagrams", True)
    except Exception:
        pass
