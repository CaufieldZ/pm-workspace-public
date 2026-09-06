#!/usr/bin/env python3
"""user-manual skill — 源 md → docx（pandoc + reference.docx + callout.lua）+ 图片清单。

唯一 docx 生成入口。源 md 本身即帮助中心可发布版（相对图链接），不另生成第二份正文。

用法:
  python3 build_manual.py <source.md>                       # 缺图 FAIL
  python3 build_manual.py <source.md> --allow-placeholder   # 缺图降级 warning（占位优先）
  python3 build_manual.py <source.md> --promo               # 营销稿：docx 可选产出，缺图常态放行（设计侧后补）
  python3 build_manual.py <source.md> --docx-out <path>     # 自定 docx 落点（默认同名 .docx）

产物:
  <source>.docx             ← pandoc 转出，截图内嵌
  <dir>/images-manifest.txt ← 引用的本地图清单（帮助中心上传替换链接用）
"""
import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
REFERENCE_DOCX = ASSETS / "user-manual-reference.docx"
CALLOUT_LUA = ASSETS / "callout.lua"

# markdown 图片：![alt](url "title")，抓 url
IMG_RE = re.compile(r"!\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")

# 加粗独占行（封面标题）：**标题**
BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*$")
COVER_FONT = "Microsoft YaHei"      # 中文（eastAsia）
COVER_FONT_LATIN = "Arial"          # 西文 / 数字（ascii/hAnsi），避免回退衬线体


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _cover_para(text: str, *, size: int, color: str, bold: bool, before: int = 0, after: int = 0) -> str:
    """居中封面段落 openxml。size/before/after 单位为半点/twips（Word 原生单位）。"""
    b = "<w:b/><w:bCs/>" if bold else ""
    return (
        "<w:p><w:pPr>"
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="240" w:lineRule="auto"/>'
        '<w:jc w:val="center"/>'
        f'<w:rPr><w:rFonts w:ascii="{COVER_FONT_LATIN}" w:eastAsia="{COVER_FONT}" w:hAnsi="{COVER_FONT_LATIN}"/>'
        f'{b}<w:color w:val="{color}"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="{COVER_FONT_LATIN}" w:eastAsia="{COVER_FONT}" w:hAnsi="{COVER_FONT_LATIN}"/>'
        f'{b}<w:color w:val="{color}"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
        f'<w:t xml:space="preserve">{_xml_escape(text)}</w:t></w:r></w:p>'
    )


_HEADER_SHADE = '<w:shd w:val="clear" w:color="auto" w:fill="EEF3FE"/>'


def _normalize_table(tbl_xml: str) -> str:
    """把 pandoc 表格改造成稳定组合（对齐可正常渲染的参考 docx）：
    - tblStyle 用 TableGrid（reference.docx 已美化为浅灰细线）
    - 去单元格 Compact pStyle（缺失样式会让 LibreOffice/WPS 内容溢出格外）
    - tblW pct→auto、去 tblLayout fixed、表格居中
    - 首行单元格注入浅蓝底纹 + 深色字
    """
    # tblStyle → TableGrid（pandoc 默认写 Table）
    tbl_xml = re.sub(r'<w:tblStyle w:val="[^"]*"\s*/>',
                     '<w:tblStyle w:val="TableGrid"/>', tbl_xml)
    # 宽度与布局
    tbl_xml = re.sub(r'<w:tblW w:type="pct" w:w="\d+"\s*/>',
                     '<w:tblW w:type="auto" w:w="0"/>', tbl_xml)
    tbl_xml = re.sub(r'<w:tblLayout w:type="fixed"\s*/>', "", tbl_xml)
    # 表格整体居中（tblPr 内补 jc）
    if "<w:jc " not in tbl_xml.split("</w:tblPr>")[0]:
        tbl_xml = tbl_xml.replace("</w:tblPr>", '<w:jc w:val="center"/></w:tblPr>', 1)
    # 单元格段落强制套 Compact（否则回退 Normal 的大行距，表格行高松散）。
    # 仅处理表格内 <w:tc> 里的段落 pPr。
    def _compact_cell(m):
        tc = m.group(0)
        tc = re.sub(r"<w:pPr>(?!\s*<w:pStyle)", '<w:pPr><w:pStyle w:val="Compact"/>', tc)
        tc = tc.replace("<w:pPr />", '<w:pPr><w:pStyle w:val="Compact"/></w:pPr>')
        tc = tc.replace("<w:pPr/>", '<w:pPr><w:pStyle w:val="Compact"/></w:pPr>')
        return tc
    tbl_xml = re.sub(r"<w:tc>.*?</w:tc>", _compact_cell, tbl_xml, flags=re.S)

    # 首行底纹 + 深色字
    tr_m = re.search(r"<w:tr\b.*?</w:tr>", tbl_xml, re.S)
    if tr_m:
        tr = tr_m.group(0)

        def fix_tc(m):
            tc = m.group(0)
            if "<w:tcPr />" in tc or "<w:tcPr/>" in tc:
                tc = re.sub(r"<w:tcPr ?/>", f"<w:tcPr>{_HEADER_SHADE}</w:tcPr>", tc)
            elif "<w:tcPr>" in tc:
                tc = tc.replace("<w:tcPr>", f"<w:tcPr>{_HEADER_SHADE}", 1)
            else:
                tc = tc.replace("<w:tc>", f"<w:tc><w:tcPr>{_HEADER_SHADE}</w:tcPr>", 1)
            tc = re.sub(r"(<w:rPr>)(?!.*<w:color)", r'\g<1><w:color w:val="1A3A6B"/>', tc)
            return tc

        new_tr = re.sub(r"<w:tc>.*?</w:tc>", fix_tc, tr, flags=re.S)
        tbl_xml = tbl_xml.replace(tr, new_tr, 1)
    return tbl_xml


def enable_table_header_shading(docx_path: Path) -> None:
    """pandoc 表格后处理：套 TableGrid + 去 Compact + 修宽 + 首行底纹（三端稳定 + 美观）。"""
    tmp = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}
    doc = data["word/document.xml"].decode("utf-8")
    doc = re.sub(r"<w:tbl>.*?</w:tbl>", lambda m: _normalize_table(m.group(0)), doc, flags=re.S)
    data["word/document.xml"] = doc.encode("utf-8")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, data[n])
    tmp.replace(docx_path)


def build_cover(md_text: str) -> str:
    """手册模式：把首个 H1 之前的加粗标题 + 副标重排成 docx 封面页（居中 openxml + 分页），
    md 源不动，仅改写喂给 pandoc 的文本。提取不到标题则原样返回。"""
    lines = md_text.split("\n")
    h1_idx = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if h1_idx is None:
        return md_text
    preamble, body = lines[:h1_idx], lines[h1_idx:]

    title = None
    title_line_idx = None
    for i, line in enumerate(preamble):
        m = BOLD_ONLY_RE.match(line.strip())
        if m:
            title, title_line_idx = m.group(1).strip(), i
            break
    if title is None:
        return md_text

    subtitle = next((line.strip() for line in preamble[title_line_idx + 1:] if line.strip()), None)

    xml = _cover_para(title, size=56, color="1A1A1A", bold=True, before=3200, after=200)
    if subtitle:
        xml += _cover_para(subtitle, size=26, color="808080", bold=False, after=0)
    xml += '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    cover = ["```{=openxml}", xml, "```", ""]
    return "\n".join(cover + body)


def find_pandoc() -> str:
    p = shutil.which("pandoc")
    if p:
        return p
    fallback = Path.home() / ".local" / "bin" / "pandoc"
    if fallback.exists():
        return str(fallback)
    sys.exit("❌ 找不到 pandoc。装：brew install pandoc 或确认 ~/.local/bin/pandoc 存在。")


def extract_images(md_text: str) -> list:
    out = []
    for m in IMG_RE.finditer(md_text):
        url = m.group(1).strip().strip("<>")
        if url.startswith(("http://", "https://", "data:")):
            continue
        out.append(url)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="源手册 md 路径")
    ap.add_argument("--allow-placeholder", action="store_true",
                    help="缺图降级为 warning（占位优先阶段用）")
    ap.add_argument("--promo", action="store_true",
                    help="营销稿模式：docx 为可选产出，缺图为常态（设计侧后补），不 FAIL")
    ap.add_argument("--docx-out", help="docx 落点，默认同名 .docx")
    args = ap.parse_args()
    # 营销稿缺图是常态（营销图设计侧后补），复用占位降级逻辑放行
    allow_missing = args.allow_placeholder or args.promo

    src = Path(args.source).resolve()
    if not src.exists():
        sys.exit(f"❌ 源 md 不存在: {src}")
    src_dir = src.parent
    md_text = src.read_text(encoding="utf-8")

    # 1. 校验本地图片引用
    imgs = extract_images(md_text)
    missing = [u for u in imgs if not (src_dir / u).exists()]
    if missing:
        head = "⚠️ 缺图（占位）" if allow_missing else "❌ 缺图"
        print(f"{head}：{len(missing)} 张引用的本地图不存在：", file=sys.stderr)
        for u in missing:
            print(f"   - {u}", file=sys.stderr)
        if not allow_missing:
            print("   → 放图进 images/ 后重跑，或临时加 --allow-placeholder", file=sys.stderr)
            sys.exit(1)

    # 2. pandoc 转 docx（手册模式生成封面页，源 md 不动，写临时文件喂 pandoc）
    docx_out = Path(args.docx_out).resolve() if args.docx_out else src.with_suffix(".docx")
    pandoc_src = src
    tmp_src = None
    if not args.promo:
        cover_text = build_cover(md_text)
        if cover_text != md_text:
            tmp_src = src_dir / f".{src.stem}.cover.md"
            tmp_src.write_text(cover_text, encoding="utf-8")
            pandoc_src = tmp_src
    cmd = [
        find_pandoc(), str(pandoc_src), "-o", str(docx_out),
        "--reference-doc", str(REFERENCE_DOCX),
        "--lua-filter", str(CALLOUT_LUA),
        "--resource-path", str(src_dir),
        "-f", "markdown", "-t", "docx",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if tmp_src is not None:
        tmp_src.unlink(missing_ok=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(f"❌ pandoc 转换失败（exit {r.returncode}）")

    # 2b. 开启表头行样式（浅蓝底加粗）
    enable_table_header_shading(docx_out)

    # 3. 图片清单
    manifest = src_dir / "images-manifest.txt"
    lines = ["# 本手册引用的截图清单（帮助中心发布时逐张上传、替换为 CMS 返回 URL）", ""]
    lines += [f"{'[缺]' if u in missing else '[有]'} {u}" for u in imgs] or ["（无图片引用）"]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ docx: {docx_out}")
    print(f"✅ 图片清单: {manifest}（共 {len(imgs)} 张，缺 {len(missing)}）")
    if missing and args.allow_placeholder:
        print("⚠️ 仍有占位缺图，正式交付前补齐并去掉 --allow-placeholder 重跑")
    elif missing and args.promo:
        print("⚠️ 营销稿缺图（设计侧后补），docx 已按现有图生成")
    try:
        from lib.skill_log import emit as _sl
        _sl("user-manual", True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
