"""章节 / §小节锚点正则的单一真相源。

banned_terms.py（禁词 / 内部锚点）与 business_voice.py（业务话语层 PATTERN）
两个检测器都要匹配「第 N 章/节/条」「§X.Y」这类内部锚点，过去各自 re.compile
一份，已出现漂移。收口到此处共享，消费方按需 import。

「章节」有两个变体，差异是**有意保留**的，不要合并：
  - CHAPTER_RE_WITH_JIE（含「节」）：内部锚点泄漏检测用（banned_terms / plain-language）。
    「第 3 节」也算内部锚点外泄，要拦。
  - CHAPTER_REF_RE（不含「节」）：业务话语层跨产物章节引用检测用（business_voice，
    服务 static-chapter / imap / proto）。该层「第 N 节」形态另由 business_voice 的
    SECTION_NUM_INLINE_RE（匹配 `6.2 节`）覆盖，故此处不含「节」。
"""
import re

# 含「节」——内部锚点泄漏检测
CHAPTER_RE_WITH_JIE = re.compile(r"第\s*\d+\s*[章节条]")

# 不含「节」——业务话语层章节引用检测
CHAPTER_REF_RE = re.compile(r"第\s*\d+\s*(?:章|条)")

# §X.Y 西文小节号（两个消费方完全等价）
SECTION_ANCHOR_RE = re.compile(r"§\s*\d+(?:\.\d+)?")
