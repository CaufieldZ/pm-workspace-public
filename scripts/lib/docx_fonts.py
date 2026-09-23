"""docx 东亚语言/字体规范化：生成器建完文档顺手调一次。

为什么需要：python-docx 自带默认模板里，文档主题语言写的是日语——settings.xml 的
`themeFontLang w:eastAsia="ja-JP"`，主题里 Jpan 映射到 ＭＳ ゴシック；pandoc 的 reference
模板也可能带同款来历。这个标记不清掉，WPS 会把中文按日文字体渲染（Word 宽容，所以不易察觉）。

调用方：
- `.claude/skills/ppt/scripts/gen-notes-docx.py` — new_document() 建文档
- `.claude/skills/user-manual/scripts/build_manual.py` — normalize_docx() 收尾校

API（全部幂等）：
- new_document(lang='zh-CN')                        → python-docx Document，主题语言已归正
- ensure_ea_language(doc, lang='zh-CN')             → 就地改内存里的 settings / styles
- normalize_docx(path, lang='zh-CN', ea_font=None)  → 给已落盘的 docx 打补丁（pandoc 产出用）
- inspect_docx(path)                                → 读现状（校验 / 自检用）
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

DEFAULT_LANG = "zh-CN"
_EA_FONT_FALLBACK = "Microsoft YaHei"

_THEME_LANG_RE = re.compile(r'(<w:themeFontLang\b[^>]*?w:eastAsia=")([^"]*)(")')
_DOCDEFAULTS_LANG_RE = re.compile(r'(<w:docDefaults>.*?<w:lang\b[^>]*?w:eastAsia=")([^"]*)(")', re.S)
_EA_RE = re.compile(r'<a:ea typeface="[^"]*"/>')
_HANS_RE = re.compile(r'<a:font script="Hans" typeface="[^"]*"/>')


def inspect_docx(path: str | Path) -> dict[str, object]:
    """读一份 docx 的主题语言与东亚字体配置（不改文件）。"""
    with zipfile.ZipFile(path) as z:
        settings = z.read("word/settings.xml").decode("utf-8")
        styles = z.read("word/styles.xml").decode("utf-8")
        theme = z.read("word/theme/theme1.xml").decode("utf-8")
    m = _THEME_LANG_RE.search(settings)
    d = _DOCDEFAULTS_LANG_RE.search(styles)
    ea = _EA_RE.search(theme)
    hans = _HANS_RE.search(theme)
    return {
        "theme_lang": m.group(2) if m else "",
        "docdefaults_lang": d.group(2) if d else "",
        "theme_ea": ea.group(0) if ea else "",
        "theme_hans": hans.group(0) if hans else "",
        "has_japanese_lang": 'w:eastAsia="ja-JP"' in settings or 'w:eastAsia="ja-JP"' in styles,
    }


def normalize_docx(path: str | Path, lang: str = DEFAULT_LANG,
                   ea_font: str | None = None) -> dict[str, object]:
    """把已落盘 docx 的东亚语言归正（可选：把主题东亚字体与简体中文脚本指向 ea_font）。

    幂等：已是目标状态时原样返回；改完做末态校验，校验不过不写盘。
    """
    p = Path(path)
    with zipfile.ZipFile(p) as z:
        parts = {i.filename: z.read(i.filename) for i in z.infolist()}
        infos = {i.filename: i for i in z.infolist()}

    before = inspect_docx(p)
    changed: list[str] = []

    def _sub(part: str, rx: re.Pattern[str], new: str, tag: str, current: str | None = None) -> None:
        """按当前值决定要不要改（幂等：值已对就不算改动）。"""
        text = parts[part].decode("utf-8")
        if not rx.search(text):
            return
        if current is not None and current in text:
            return
        updated, n = rx.subn(new, text)
        if n:
            parts[part] = updated.encode("utf-8")
            changed.append(tag)

    _sub("word/settings.xml", _THEME_LANG_RE, r"\g<1>" + lang + r"\g<3>", "themeFontLang",
         current=f'w:eastAsia="{lang}"')
    _sub("word/styles.xml", _DOCDEFAULTS_LANG_RE, r"\g<1>" + lang + r"\g<3>", "docDefaults.lang",
         current=f'w:eastAsia="{lang}"')
    if ea_font:
        _sub("word/theme/theme1.xml", _EA_RE, f'<a:ea typeface="{ea_font}"/>', "theme.ea",
             current=f'<a:ea typeface="{ea_font}"/>')
        _sub("word/theme/theme1.xml", _HANS_RE,
             f'<a:font script="Hans" typeface="{ea_font}"/>', "theme.hans",
             current=f'<a:font script="Hans" typeface="{ea_font}"/>')

    # 末态校验（幂等判据看结果，不看 pattern 是否命中）
    settings = parts["word/settings.xml"].decode("utf-8")
    styles = parts["word/styles.xml"].decode("utf-8")
    if f'w:eastAsia="{lang}"' not in settings and _THEME_LANG_RE.search(settings):
        raise ValueError(f"{p.name}: themeFontLang 未归正到 {lang}，不写盘")
    if f'w:eastAsia="{lang}"' not in styles and _DOCDEFAULTS_LANG_RE.search(styles):
        raise ValueError(f"{p.name}: docDefaults 语言未归正到 {lang}，不写盘")

    if changed:
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as out:
            for name, data in parts.items():
                out.writestr(infos[name], data)
    after = inspect_docx(p)
    return {"changed": bool(changed), "parts": changed, "before": before, "after": after}


def ensure_ea_language(doc: object, lang: str = DEFAULT_LANG) -> None:
    """就地改内存里 python-docx Document 的主题语言（settings + docDefaults）。"""
    from docx.oxml.ns import qn

    settings = doc.settings.element  # type: ignore[attr-defined]
    el = settings.find(qn("w:themeFontLang"))
    if el is None:
        el = settings.makeelement(qn("w:themeFontLang"), {})
        settings.insert(0, el)
    el.set(qn("w:val"), "en-US")
    el.set(qn("w:eastAsia"), lang)

    styles = doc.styles.element  # type: ignore[attr-defined]
    dd = styles.find(qn("w:docDefaults"))
    if dd is not None:
        lang_el = dd.find(".//" + qn("w:lang"))
        if lang_el is not None:
            lang_el.set(qn("w:eastAsia"), lang)


def new_document(lang: str = DEFAULT_LANG) -> object:
    """建 python-docx Document（主题语言已归正，绕开默认模板的日语标记）。"""
    from docx import Document

    doc = Document()
    ensure_ea_language(doc, lang)
    return doc
