"""lint 命中明细导出 JSON（供 post-checks 取命中词做词表防腐化埋点）。

格式：{"gate": <gate>, "hits": [{"lineno", "category", "matched"}, ...]}
json_out == '-' 走 stdout；<path> 写文件；None / 空跳过。

调用方：check_plain_language.py（gate=plain-language）/ check_static_chapter.py（gate=context-static-lint）
"""
import json
import sys
from pathlib import Path


def emit(json_out, gate, hits):
    """hits: 可迭代的 (lineno, category, matched) 三元组。"""
    if not json_out:
        return
    payload = {
        "gate": gate,
        "hits": [{"lineno": ln, "category": cat, "matched": m} for ln, cat, m in hits],
    }
    blob = json.dumps(payload, ensure_ascii=False)
    if json_out == "-":
        print(blob)
    else:
        try:
            p = Path(json_out)
            p.parent.mkdir(parents=True, exist_ok=True)  # 目录不存在是最常见失败因
            p.write_text(blob, encoding="utf-8")
        except OSError as e:
            sys.stderr.write(f"[json_out] 写 {json_out} 失败：{e}\n")  # 不静默吞
