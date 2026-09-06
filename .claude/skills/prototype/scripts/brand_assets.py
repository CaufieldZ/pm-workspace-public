"""品牌素材工具：把项目品牌 Logo 注入 generate_single 的 project dict。

用法（orchestrator 里）：

    from brand_assets import brand_logo_html
    project = {
        'name': 'Demo 直播',
        'version': '2.3',
        'logo_html': brand_logo_html(size=22),   # 注入后骨架自动替换 🔥
    }

公开函数：

    brand_logo_html(size=22, color_left='#EAECEF', color_right='#007FFF') → str
        返回 双火焰 SVG 字符串，可直接赋给 project['logo_html']。
        size 按高度缩放（原始比例 29:44 宽:高），宽度自动按比例收窄。
        color_left：左焰颜色，深色导航默认 #EAECEF（近白）。
        color_right：右焰颜色，默认 品牌蓝 #007FFF。

    brand_logo_html_mono(size=22, color='#EAECEF') → str
        单色版，左右焰同色，用于浅色背景或不需要双色区分的场合。

SVG path data 从 Figma 官方文件导出（fetch_figma.py --format svg），
原始尺寸 29×44（宽×高），viewBox 保留原始比例。
"""

# 双火焰路径（Figma 节点 2523:28950，原始 29×44）
_LEFT = (
    'M18.9168 13.4978C19.0476 7.02217 15.3807 1.37942 13.4709 0.0232385'
    'C13.4622 0.0145171 13.2921 -0.0770567 13.3052 0.175864'
    'C13.3052 0.180225 13.3008 0.180223 13.3008 0.184584'
    'C13.1046 12.4164 6.81716 15.7131 3.4031 20.1959'
    'C-4.18371 30.1644 2.14735 41.5372 10.3489 43.6913'
    'C10.4885 43.7262 10.8678 43.8396 11.5873 43.9879'
    'C11.9622 44.0664 12.0712 43.748 11.7965 43.2727'
    'C10.8155 41.5677 9.0714 38.6896 8.72694 34.9917'
    'C7.9421 26.4055 18.7642 21.0331 18.9168 13.4978Z'
)
_RIGHT = (
    'M23.0499 17.6413C22.9845 17.5934 22.8929 17.5977 22.8842 17.6806'
    'C22.7098 19.2373 21.1009 22.4643 18.9818 25.4819'
    'C11.8485 35.6554 15.4413 40.269 18.2318 43.4698'
    'C18.7464 44.0628 19.0036 43.932 19.2739 43.509'
    'C19.5268 43.1078 19.9105 42.5976 21.5587 41.8171'
    'C21.8159 41.695 28.0424 38.3896 28.7182 30.863'
    'C29.3679 23.5762 24.6981 18.9757 23.0499 17.6413Z'
)


def brand_logo_html(
    size: int = 22,
    color_left: str = '#EAECEF',
    color_right: str = '#007FFF',
) -> str:
    """双火焰 SVG，赋给 project['logo_html']。"""
    w = round(size * 29 / 44, 1)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{size}" '
        f'viewBox="0 0 29 44" fill="none" aria-label="brand" '
        f'style="display:inline-block;vertical-align:middle;flex-shrink:0;margin-right:4px">'
        f'<path d="{_LEFT}" fill="{color_left}"/>'
        f'<path d="{_RIGHT}" fill="{color_right}"/>'
        f'</svg>'
    )


def brand_logo_html_mono(size: int = 22, color: str = '#EAECEF') -> str:
    """双火焰单色版，左右焰同色。"""
    return brand_logo_html(size=size, color_left=color, color_right=color)


if __name__ == '__main__':
    """自检：输出示例 HTML 供肉眼验证。"""
    import xml.etree.ElementTree as ET

    for fn, args in [
        (brand_logo_html, {}),
        (brand_logo_html, {'size': 16, 'color_right': '#4DA6FF'}),
        (brand_logo_html_mono, {'color': '#FFFFFF'}),
    ]:
        svg = fn(**args)
        ET.fromstring(svg)   # 语法校验
        print('✅', svg[:80], '...')
    print('brand_assets 自检通过')
