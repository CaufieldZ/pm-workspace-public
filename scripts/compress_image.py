#!/usr/bin/env python3
"""图片压缩 · 满足 Bedrock 多图 2000px / 5MB 限制，供多模态 Read 前预处理。

Bedrock 硬限制（any-image 和 many-image 两条均需满足）：
  - 任意维度 ≤ 2000px
  - 单文件 ≤ 5 MB（5 242 880 bytes）

用法（单张）：
    python3 scripts/compress_image.py path/to/img.png
用法（多张）：
    python3 scripts/compress_image.py a.png b.jpg c.png
用法（管道引用压缩后路径）：
    python3 scripts/compress_image.py img.png --print-path

退出码：
    0 — 全部处理完成（含「无需压缩」）
    2 — 任意一张图处理失败（PIL 读取失败 / 文件不存在，仅 --strict 时生效）
"""
from __future__ import annotations

import io
import sys
from pathlib import Path


# ── 压缩限制默认值 ────────────────────────────────────────────────────────

MAX_DIM_DEFAULT = 1800          # 留 200px 余量低于 Bedrock 2000px 硬限
MAX_MB_DEFAULT = 4.5            # 留余量低于 Bedrock 5MB 硬限
MAX_BYTES_DEFAULT = int(MAX_MB_DEFAULT * 1024 * 1024)
QUALITY_DEFAULT = 85


# ── 纯逻辑函数（可被 pytest import 直接测）────────────────────────────────

def needs_compress(width: int, height: int, file_size: int,
                   max_dim: int = MAX_DIM_DEFAULT,
                   max_bytes: int = MAX_BYTES_DEFAULT) -> bool:
    """判断图片是否超出 Bedrock 限制。"""
    return max(width, height) > max_dim or file_size > max_bytes


def compress_image(
    src: Path,
    max_dim: int = MAX_DIM_DEFAULT,
    max_bytes: int = MAX_BYTES_DEFAULT,
    quality: int = QUALITY_DEFAULT,
    inplace: bool = False,
) -> Path:
    """压缩单张图片，返回输出路径。

    - 长边 > max_dim 时等比缩小到 max_dim
    - PNG 先尝试 optimize 保存；仍超 max_bytes 则转 JPEG 降质
    - JPEG 按 quality 初始保存，超限每次降 10 直到 ≤ max_bytes
    - inplace=False 时输出同目录 ``{stem}-compressed{suffix}``（不覆盖原图）
    """
    from PIL import Image

    img = Image.open(src)
    w, h = img.size

    # 1. 等比缩小长边
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # 2. 决定输出格式
    suffix = src.suffix.lower()
    out_fmt = "JPEG" if suffix in {".jpg", ".jpeg"} else "PNG"
    if out_fmt == "JPEG" and img.mode in {"RGBA", "LA", "P"}:
        img = img.convert("RGB")

    # 3. 决定输出路径
    if inplace:
        out_path = src
    else:
        stem = src.stem
        if not stem.endswith("-compressed"):
            out_path = src.with_name(f"{stem}-compressed{src.suffix}")
        else:
            out_path = src

    # 4. 保存
    if out_fmt == "PNG":
        img.save(out_path, "PNG", optimize=True)
        if out_path.stat().st_size > max_bytes:
            # PNG 超限 → 转 JPEG
            jpg_path = out_path.with_suffix(".jpg")
            img_rgb = img.convert("RGB") if img.mode != "RGB" else img
            _save_jpeg_budget(img_rgb, jpg_path, quality, max_bytes)
            if out_path != src:
                out_path.unlink(missing_ok=True)
            out_path = jpg_path
    else:
        _save_jpeg_budget(img, out_path, quality, max_bytes)

    return out_path


def _save_jpeg_budget(img, out_path: Path, quality: int, max_bytes: int) -> None:
    """降质循环：从 quality 开始，每次 -10，直到文件 ≤ max_bytes。"""
    q = quality
    while q >= 30:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q)
        data = buf.getvalue()
        if len(data) <= max_bytes:
            out_path.write_bytes(data)
            return
        q -= 10
    # 最低质量兜底
    img.save(out_path, "JPEG", quality=30)


# ── CLI 入口 ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="图片压缩：满足 Bedrock 多图 2000px / 5MB 限制",
    )
    ap.add_argument("images", nargs="+", help="待压缩图片路径（支持多张）")
    ap.add_argument("--max-dim", type=int, default=MAX_DIM_DEFAULT,
                    help=f"最大像素边长（默认 {MAX_DIM_DEFAULT}）")
    ap.add_argument("--max-mb", type=float, default=MAX_MB_DEFAULT,
                    help=f"最大文件大小 MB（默认 {MAX_MB_DEFAULT}）")
    ap.add_argument("--quality", type=int, default=QUALITY_DEFAULT,
                    help=f"JPEG 初始质量（默认 {QUALITY_DEFAULT}）")
    ap.add_argument("--inplace", action="store_true",
                    help="原地覆盖原图（不可逆）")
    ap.add_argument("--print-path", action="store_true",
                    help="只输出压缩后路径（供脚本管道引用）")
    ap.add_argument("--strict", action="store_true",
                    help="任意图处理失败时 exit 2（hook 模式）")
    args = ap.parse_args()

    max_bytes = int(args.max_mb * 1024 * 1024)
    errors: list[str] = []

    for img_str in args.images:
        src = Path(img_str).expanduser().resolve()
        if not src.exists():
            msg = f"找不到文件：{src}"
            print(f"⚠  {msg}", file=sys.stderr)
            errors.append(msg)
            continue

        try:
            from PIL import Image as _Img
            pil_img = _Img.open(src)
            w, h = pil_img.size
        except Exception as e:
            msg = f"无法读取图片 {src.name}：{e}"
            print(f"⚠  {msg}", file=sys.stderr)
            errors.append(msg)
            continue

        before_size = src.stat().st_size

        if not needs_compress(w, h, before_size, args.max_dim, max_bytes):
            if args.print_path:
                print(src)
            else:
                print(f"✓  {src.name}  ({w}×{h}, {before_size // 1024} KB) 已满足限制，无需压缩")
            continue

        try:
            out = compress_image(src, args.max_dim, max_bytes, args.quality, args.inplace)
        except Exception as e:
            msg = f"压缩失败 {src.name}：{e}"
            print(f"⚠  {msg}", file=sys.stderr)
            errors.append(msg)
            continue

        after_size = out.stat().st_size
        from PIL import Image as _Img2
        ow, oh = _Img2.open(out).size

        if args.print_path:
            print(out)
        else:
            print(
                f"✓  {src.name} → {out.name}\n"
                f"   尺寸 {w}×{h} → {ow}×{oh}  |  "
                f"{before_size // 1024} KB → {after_size // 1024} KB"
            )

    return 2 if (args.strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main())
