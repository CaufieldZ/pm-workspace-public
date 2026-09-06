"""按 domain 加载技术词表，命中即视为「描述当前态」违规。

调用方：
- scripts/check_static_chapter.py（真相源静态章 lint）
- scripts/lib/business_voice.py（PRD / IMAP / proto 共享）

加载策略：
- domain 默认推断：读 baseline / scene-list.md 关键字
- 显式传 domains 参数覆盖
- 未传 domain → 默认 ['infra']（最通用的基础设施词）
"""
from __future__ import annotations

import re
from pathlib import Path

_DIR = Path(__file__).parent
_CACHE: dict[str, list[str]] = {}

# 项目关键字 → domain 映射
# 激活策略：至少命中 2 个关键字（且非"K 线/合约"这种业务串话词），避免一词激活
_DOMAIN_KEYWORDS = {
    'livestream': ('直播', '弹幕', '礼物', '连麦', '主播中心', 'TRTC', 'OBS', '推流', '拉流'),
    'social': ('社区', 'Feed', '推荐位', '关注', '动态', '牛人榜', '排行榜', '帖子', '社区基座'),
    'trading': ('交易引擎', '合约下单', '撮合', 'K 线', '订单簿', '资金费率', 'Premium'),
    'web-frontend': ('Web 前台', 'PC 前台', 'H5 页面', 'React', 'Vue'),
}
_DOMAIN_MIN_HITS = 2  # 最少命中数


def _load_domain(domain: str) -> list[str]:
    """加载单 domain 词表，缓存。"""
    if domain in _CACHE:
        return _CACHE[domain]
    path = _DIR / f'{domain}.txt'
    if not path.exists():
        _CACHE[domain] = []
        return []
    words: list[str] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        words.append(line)
    _CACHE[domain] = words
    return words


def infer_domains(text: str) -> list[str]:
    """从真相源文本推断 domain 列表，infra 始终包含。

    激活策略：domain 需在文本中命中 ≥ _DOMAIN_MIN_HITS 个关键字才算激活，
    避免单一业务串话词（如"主播提到 K 线"）误激活 livestream + trading。
    """
    domains = ['infra']
    for dom, kws in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in text)
        if hits >= _DOMAIN_MIN_HITS:
            domains.append(dom)
    return domains


def load_jargon(domains: list[str] | None = None,
                context_text: str | None = None) -> list[re.Pattern]:
    """返回 compile 好的 regex 列表，命中即认为违规。

    优先级：显式 domains > 从 context_text 推断 > infra 兜底。
    """
    if domains is None:
        if context_text is not None:
            domains = infer_domains(context_text)
        else:
            domains = ['infra']
    seen: set[str] = set()
    words: list[str] = []
    for d in domains:
        for w in _load_domain(d):
            if w not in seen:
                seen.add(w)
                words.append(w)
    # \b 词边界，部分词如 K8s / NextJS 含数字大写混排，re.escape 保守处理
    pats: list[re.Pattern] = []
    for w in words:
        # 含空格 / 特殊符号 → 直接字面量匹配（前后非字母数字边界）
        if ' ' in w or any(c in w for c in '.+-'):
            pats.append(re.compile(rf'(?<![A-Za-z0-9]){re.escape(w)}(?![A-Za-z0-9])'))
        else:
            # 标识符词：词边界 + 大小写敏感
            pats.append(re.compile(rf'\b{re.escape(w)}\b'))
    return pats


def scan_jargon(text: str, patterns: list[re.Pattern]) -> list[str]:
    """扫描文本，返回命中的词列表。"""
    hits: list[str] = []
    for p in patterns:
        for m in p.finditer(text):
            hits.append(m.group(0))
    return hits
