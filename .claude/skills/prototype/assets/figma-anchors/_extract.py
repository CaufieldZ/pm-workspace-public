"""把 Figma --nodes JSON 抽成扁平 spec — name / type / size / fill / text / font。

用法：python3 _extract.py htx-bottom-nav.json > htx-bottom-nav.spec.txt
"""
import json
import sys
from pathlib import Path


def rgb_to_hex(c):
    if not c:
        return ""
    r = int(c.get("r", 0) * 255)
    g = int(c.get("g", 0) * 255)
    b = int(c.get("b", 0) * 255)
    a = c.get("a", 1.0)
    if a < 1.0:
        return f"rgba({r},{g},{b},{a:.2f})"
    return f"#{r:02X}{g:02X}{b:02X}"


def fmt_fill(fills):
    if not fills:
        return ""
    out = []
    for f in fills:
        if not f.get("visible", True):
            continue
        if f.get("type") == "SOLID":
            out.append(rgb_to_hex(f.get("color")))
        elif f.get("type", "").startswith("GRADIENT"):
            stops = f.get("gradientStops", [])
            colors = [rgb_to_hex(s.get("color")) for s in stops]
            out.append(f"{f['type']}({' → '.join(colors)})")
    return " / ".join(out)


def walk(node, depth=0, parent_name=""):
    if not isinstance(node, dict):
        return
    name = node.get("name", "?")
    typ = node.get("type", "?")
    visible = node.get("visible", True)

    # 跳过隐藏节点（减噪）
    if not visible:
        return

    bbox = node.get("absoluteBoundingBox") or {}
    w = bbox.get("width")
    h = bbox.get("height")
    size = f"{w:.0f}×{h:.0f}" if w and h else ""

    radius = node.get("cornerRadius")
    radius_str = f" r={radius}" if radius else ""

    fill = fmt_fill(node.get("fills", []))
    fill_str = f" fill={fill}" if fill else ""

    stroke = fmt_fill(node.get("strokes", []))
    stroke_w = node.get("strokeWeight", 0) or 0
    stroke_str = f" stroke={stroke}/{stroke_w}px" if stroke and stroke_w else ""

    extra = ""
    if typ == "TEXT":
        chars = node.get("characters", "")
        style = node.get("style", {})
        font = style.get("fontFamily", "")
        weight = style.get("fontWeight", "")
        size_pt = style.get("fontSize", "")
        lh = style.get("lineHeightPx", "")
        extra = f' "{chars}" {font} {weight} {size_pt}px/lh{lh}px'

    indent = "  " * depth
    print(f"{indent}[{typ}] {name} {size}{radius_str}{fill_str}{stroke_str}{extra}")

    for child in node.get("children", []) or []:
        walk(child, depth + 1, name)


def main():
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    for node_id, payload in data.items():
        doc = payload.get("document") or payload
        print(f"=== {node_id} {doc.get('name','')} ===")
        walk(doc)


if __name__ == "__main__":
    main()
