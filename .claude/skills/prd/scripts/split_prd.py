#!/usr/bin/env python3
"""把 single 模式 PRD 拆成 split 结构（一次性迁移工具）。

用法：
    python3 split_prd.py <prd.md>               # 原地迁移，原 md 备份到 .bak
    python3 split_prd.py <prd.md> --dry-run     # 只打印计划不改动

触发时机：
- single PRD 膨胀到 > 1500 行
- 场景数 > 10 导致 check_prd_md.sh 提醒 split
- PM 主动要求拆分

行为：
1. 找主 md 里第 5/6/7 章下的每个 `### N.x 编号 · 白话名` 场景块
2. 每个场景块内容抽出来写独立文件 → `{stem}-scenes/{view}-{id}-{name}.md`
3. 子文件内部 heading 降级为 `##`（去掉外层 h3 的一级）
4. 截图路径 `./assets/` 改为 `../assets/`（子文件视角）
5. 主 md 的场景块替换为引用链接行
6. 备份原 md 为 `{stem}.md.bak`

不处理的边界：
- 嵌套子场景（### 5.1 内部又有 #### 5.1.1）—— 按规范本就禁止，有就报错停
- 场景编号不规范（不是 X-N 格式）—— 报错
- 5/6/7 章下有非场景内容（如章头 narrative 段落）—— 保留在主 md，置于 heading 和第一个场景之间
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from core.md_renderer import stamp_skel_version

# 章节标题：兼容 12 章模板（# 5. xxx）+ docx 转 md 形态（# **5. xxx**）
# 场景章节范围扩展为 4-7，涵盖：
#   - 12 章模板 §5 前台 / §6 后台 / §7 跨端
#   - 多 view 业务 §4 前置流程章（如直播开播链路）
_CHAPTER_HEAD_RE = re.compile(r"^#\s+\*{0,2}([4-7])\.\s+(.+?)\*{0,2}\s*$")

# 场景标题：兼容 ### / ## 两种层级；兼容粗体 **包裹**；兼容 `Scene ` 前缀；
# 编号支持单字母（如 B 系列 5.6 Scene B · 连麦全流程）+ 字母数字混合（A-1 / B-2 / D-2a）
_SCENE_HEAD_RE = re.compile(
    r"^##+\s+\*{0,2}(\d+\.\d+)\s+(?:Scene\s+)?([A-Z][-\w]*)\s*·\s*(.+?)\*{0,2}\s*$"
)


# 章节 → view 前缀映射。
# 12 章模板默认（5/6/7 → front/back/cross）；§4 兜底用 ch4（多 view 业务通过 --view-map 覆盖）
_DEFAULT_VIEW_PREFIX = {4: "ch4", 5: "front", 6: "back", 7: "cross"}


def _view_prefix(chapter: int, view_map: dict[int, str]) -> str:
    return view_map.get(chapter, f"ch{chapter}")


_PHASE_TAG_RE = re.compile(r"\s*\*{0,2}[（(](?:Phase\s*\d+|变更|新增|后续迭代)[^）)]*[）)]\*{0,2}\s*$")


def _clean_display_name(name: str) -> str:
    """主 md 引用文本里的白话名清理：剥 ** 粗体闭合，保留 （Phase X 等）追溯标记。

    - `连麦全流程（B-1 ~ B-4b）**（Phase 2 · 连麦）` → `连麦全流程（B-1 ~ B-4b）（Phase 2 · 连麦）`
    - 普通名（无 Phase 标记）原样返回
    """
    return re.sub(r"\*+", "", name).strip()


def _safe_filename(name: str) -> str:
    r"""场景白话名 → 文件名 safe 部分。

    步骤：
    1. 剥离末尾追溯标记（Phase X · 连麦 / 变更 / 新增 / 后续迭代等）
    2. 剥离全部 （...） / (...) 括号 + 内容（修饰词 / 复合编号 / 备注，避免文件名臃肿）
       例：「连麦全流程（B-1 ~ B-4b）」→「连麦全流程」
       例：「主播认证（一次性）」→「主播认证」
       例：「半屏合约交易组件接入（合约组实现）」→「半屏合约交易组件接入」
    3. 替换 / \ : * ? < > | + 等不安全 / 易转义字符为 -
    4. 折叠连续多个 - 为单个
    """
    name = _PHASE_TAG_RE.sub("", name)
    name = re.sub(r"\s*[（(][^）)]*[）)]\s*", "", name)
    name = re.sub(r"[\s/\\:*?<>|+]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def _demote_heading(line: str) -> str:
    """### → ## / #### → ### （子文件里降一级）"""
    if line.startswith("### "):
        return "##" + line[3:]
    if line.startswith("#### "):
        return "###" + line[4:]
    return line


def _rewrite_asset_path(line: str) -> str:
    """./assets/x.png → ../assets/x.png（子文件视角）"""
    return re.sub(r"\]\(\./assets/", "](../assets/", line)


def split_prd(
    prd_path: Path,
    dry_run: bool = False,
    view_map: dict[int, str] | None = None,
) -> tuple[int, list[str]]:
    """返回 (场景数, 生成的子文件名列表)。

    view_map: 章节号 → view 前缀映射；不传走 _DEFAULT_VIEW_PREFIX
    （12 章模板：5=front / 6=back / 7=cross；多 view 业务可传 {4: 'pre', 5: 'audience', ...}）
    """
    effective_view_map = dict(_DEFAULT_VIEW_PREFIX)
    if view_map:
        effective_view_map.update(view_map)
    if not prd_path.exists():
        raise SystemExit(f"PRD 不存在：{prd_path}")

    stem = prd_path.stem
    scenes_dir = prd_path.parent / f"{stem}-scenes"
    if scenes_dir.exists() and not dry_run:
        raise SystemExit(
            f"目录已存在，不覆盖：{scenes_dir}\n"
            f"先检查是否已 split，或手动清理后重试"
        )

    main_lines = prd_path.read_text(encoding="utf-8").splitlines()

    # 扫描 5/6/7 章的场景块
    scene_blocks: list[dict] = []  # [{chapter, section, id, name, lines: [str], start, end}]
    current_chapter: int = 0
    current_scene: dict | None = None
    for i, line in enumerate(main_lines):
        m_chapter = _CHAPTER_HEAD_RE.match(line)
        if m_chapter:
            current_chapter = int(m_chapter.group(1))
            if current_scene is not None:
                current_scene["end"] = i
                scene_blocks.append(current_scene)
                current_scene = None
            continue

        if current_chapter in (4, 5, 6, 7):
            m_scene = _SCENE_HEAD_RE.match(line)
            if m_scene:
                if current_scene is not None:
                    current_scene["end"] = i
                    scene_blocks.append(current_scene)
                current_scene = {
                    "chapter": current_chapter,
                    "section": m_scene.group(1),
                    "id": m_scene.group(2),
                    "name": m_scene.group(3),
                    "start": i,
                    "end": -1,
                }
                continue

            # 下一个 # 级 heading（非 5/6/7 章）关闭当前 scene
            if line.startswith("# ") and not m_chapter:
                if current_scene is not None:
                    current_scene["end"] = i
                    scene_blocks.append(current_scene)
                    current_scene = None

    # 文件末尾关闭最后一个 scene
    if current_scene is not None:
        current_scene["end"] = len(main_lines)
        scene_blocks.append(current_scene)

    if not scene_blocks:
        print("⚠ 未找到任何 ### N.x 场景（5/6/7 章），无需 split", file=sys.stderr)
        return 0, []

    # 检查禁嵌套（###N.x 里不能有 ####N.x.y）
    for blk in scene_blocks:
        blk_lines = main_lines[blk["start"] : blk["end"]]
        for line in blk_lines[1:]:  # 跳过自己的 heading
            if re.match(r"^####\s+\d+\.\d+\.\d+", line):
                raise SystemExit(
                    f"❌ 场景 {blk['section']} 含嵌套子场景（违反扁平规则）：{line.strip()}\n"
                    f"   先把嵌套拆成并列 N.x / N.y，再跑 split_prd"
                )

    if dry_run:
        print(f"📋 计划：{len(scene_blocks)} 个场景 → {scenes_dir.name}/")
        for blk in scene_blocks:
            view = _view_prefix(blk["chapter"], effective_view_map)
            fn = f"{view}-{blk['id']}-{_safe_filename(blk['name'])}.md"
            print(f"  - {blk['section']}  {blk['id']} · {blk['name']}  →  {fn}")
        return len(scene_blocks), [blk["id"] for blk in scene_blocks]

    # 创建 scenes 目录 + 写子文件
    scenes_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    for blk in scene_blocks:
        view = _view_prefix(blk["chapter"], effective_view_map)
        fn = f"{view}-{blk['id']}-{_safe_filename(blk['name'])}.md"
        scene_file = scenes_dir / fn
        block_lines = main_lines[blk["start"] : blk["end"]]
        processed = [
            _rewrite_asset_path(_demote_heading(ln)) for ln in block_lines
        ]
        scene_file.write_text(
            stamp_skel_version("\n".join(processed).rstrip() + "\n"), encoding="utf-8"
        )
        generated.append(fn)
        blk["filename"] = fn

    # 重写主 md：场景块替换为引用链接
    out_lines: list[str] = []
    i = 0
    scene_idx = 0
    while i < len(main_lines):
        # 检查当前行是否是某个场景块的起始
        is_scene_start = (
            scene_idx < len(scene_blocks)
            and i == scene_blocks[scene_idx]["start"]
        )
        if is_scene_start:
            blk = scene_blocks[scene_idx]
            display_name = _clean_display_name(blk["name"])
            out_lines.append(
                f"- [{blk['section']} {blk['id']} · {display_name}]"
                f"({scenes_dir.name}/{blk['filename']})"
            )
            # 若最后一个场景紧贴下一章 heading，补一个空行避免列表与 heading 紧贴
            next_idx = scene_idx + 1
            is_last_in_chapter = (
                next_idx >= len(scene_blocks)
                or scene_blocks[next_idx]["chapter"] != blk["chapter"]
            )
            if is_last_in_chapter and blk["end"] < len(main_lines):
                next_line = main_lines[blk["end"]]
                if next_line.strip() and not next_line.startswith(("# ", "##")):
                    out_lines.append("")
                elif next_line.startswith("# "):
                    out_lines.append("")
            i = blk["end"]
            scene_idx += 1
            continue
        out_lines.append(main_lines[i])
        i += 1

    # 备份原 md
    bak_path = prd_path.with_suffix(prd_path.suffix + ".bak")
    shutil.copy2(prd_path, bak_path)

    prd_path.write_text(stamp_skel_version("\n".join(out_lines).rstrip() + "\n"), encoding="utf-8")

    print(f"✓ 拆出 {len(scene_blocks)} 个子场景文件到 {scenes_dir}")
    print(f"✓ 主 md 已更新（原文件备份为 {bak_path.name}）")
    return len(scene_blocks), generated


def main() -> int:
    ap = argparse.ArgumentParser(description="把 single 模式 PRD 拆成 split 结构")
    ap.add_argument("prd", help="主 PRD md 路径")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划不改动")
    ap.add_argument(
        "--view-map",
        default=None,
        help=(
            "章节号 → view 前缀映射，多 view 业务用。"
            "格式：'4=pre,5=audience,6=broadcaster,7=cms'。"
            "默认走 12 章模板：5=front / 6=back / 7=cross / 4=ch4"
        ),
    )
    args = ap.parse_args()

    view_map: dict[int, str] | None = None
    if args.view_map:
        try:
            view_map = {
                int(k.strip()): v.strip()
                for kv in args.view_map.split(",")
                for k, v in [kv.split("=", 1)]
            }
        except (ValueError, IndexError) as e:
            raise SystemExit(
                f"❌ --view-map 格式错误：{e}\n"
                f"   预期：'4=pre,5=audience,6=broadcaster,7=cms'"
            ) from e

    prd_path = Path(args.prd).resolve()
    n, _ = split_prd(prd_path, dry_run=args.dry_run, view_map=view_map)
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
