"""projects/ 下项目目录解析 —— 产品线级 / campaign 嵌套级的统一口径。

项目目录有两种形态：产品线根（`projects/community`）与 campaign 嵌套（`projects/growth/queen`），
`-p <项目名>` 两种都要认，且重名时要报错而不是静默取第一个。

调用方：
- scripts/fetch_figma.py（`-p` → `inputs/figma/`）
- scripts/image_gen.py（`-p` → `deliverables/assets/`）
- scripts/video_gen.py（`-p` → `deliverables/assets/`）
"""

from pathlib import Path


def resolve_project_dir(root: Path, name: str) -> Path:
    """项目名 -> 项目目录。找不到 / 重名抛 ValueError（怎么报由调用方定）。"""
    cands = sorted((root / "projects").glob(f"*/{name}"))
    direct = root / "projects" / name
    if direct.is_dir():
        cands.append(direct)
    if len(cands) == 1:
        return cands[0]
    if not cands:
        raise ValueError(
            f"-p {name} 找不到对应项目目录（全清单：find projects -mindepth 2 -maxdepth 2 -type d）"
        )
    raise ValueError(f"-p {name} 匹配多个：{[str(c) for c in cands]}")


def resolve_project_assets(root: Path, name: str) -> Path:
    """项目名 -> projects/<项目>/deliverables/assets。找不到 / 重名抛 ValueError。"""
    return resolve_project_dir(root, name) / "deliverables" / "assets"
