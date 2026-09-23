"""
图片无损放大（Real-ESRGAN x4 超分，纯本地 onnxruntime CPU 推理）。

用法：
  python3 scripts/upscale.py photo.jpg                        # 4x 超分，输出 photo_x4.png
  python3 scripts/upscale.py photo.jpg --scale 2              # 4x 后缩回 2x（边缘更干净）
  python3 scripts/upscale.py photo.jpg --tile 512             # 大图分块块大小（默认 384）
  python3 scripts/upscale.py *.jpg                            # 批量

模型：scripts/models/Real-ESRGAN-x4.onnx（~67MB，gitignore 不进仓库）。
缺失时自动从 HuggingFace 下载；代理由 lib/proxy.py 运行时判定，无需手动 export。
CPU 推理速度参考：384 tile 每块约 10s，1200×800 全图约 2-3 分钟。
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

MODEL_PATH = Path(__file__).parent / "models" / "Real-ESRGAN-x4.onnx"
MODEL_URL = "https://huggingface.co/SceneWorks/real-esrgan-onnx/resolve/main/real_esrgan_x4.onnx"


def _apply_proxy() -> str | None:
    """发外网请求前把代理判定写进 os.environ（判定源 = lib/proxy.py，工区唯一）。

    urllib 只认环境变量里的 HTTP_PROXY / HTTPS_PROXY，不会自己判定；判定不到
    （境外 / 代理未启动）时判定源会清掉残留变量，让这里走直连。
    """
    scripts_dir = str(Path(__file__).resolve().parent)   # 本文件就在 <root>/scripts 下
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)                  # 被 import（而非直接跑）时也找得到 lib
    try:
        from lib.proxy import apply_env
    except Exception:
        return None
    return apply_env()


def _ensure_model() -> None:
    if MODEL_PATH.exists():
        return
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"模型缺失，下载中（~67MB）→ {MODEL_PATH}")
    _apply_proxy()
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except Exception as e:
        MODEL_PATH.unlink(missing_ok=True)
        raise SystemExit(
            f"下载失败：{e}\n"
            "确认本机代理已启动，再看判定结论：python3 scripts/lib/proxy.py --describe"
        ) from e
    print("下载完成")


def _ramp(n: int, fade: int) -> np.ndarray:
    """1D 线性渐变权重：边缘 overlap 区从 0 渐到 1，用于分块无缝拼接。"""
    w = np.ones(n, dtype=np.float32)
    fade = min(fade, n // 2)
    if fade > 0:
        w[:fade] = np.linspace(0, 1, fade, dtype=np.float32)
        w[-fade:] = np.linspace(1, 0, fade, dtype=np.float32)
    return w


def _tiled_run(sess, img: np.ndarray, tile: int, overlap: int) -> np.ndarray:
    """分块推理 + 渐变权重混合，避免大图爆内存和拼接缝。img: HxWx3 float32 0-1。"""
    h, w = img.shape[:2]
    out = np.zeros((h * 4, w * 4, 3), dtype=np.float32)
    weight = np.zeros((h * 4, w * 4), dtype=np.float32)

    wy = _ramp(h * 4, overlap * 4)
    wx = _ramp(w * 4, overlap * 4)
    step = tile - overlap
    starts = [(y, x) for y in range(0, max(h - overlap, 1), step)
              for x in range(0, max(w - overlap, 1), step)]
    total = len(starts)

    for i, (y, x) in enumerate(starts, 1):
        y2, x2 = min(y + tile, h), min(x + tile, w)
        patch = img[y:y2, x:x2].transpose(2, 0, 1)[None]  # 1x3xh'xw'
        t0 = time.time()
        r = sess.run(None, {"input": patch})[0][0].transpose(1, 2, 0)  # 4h'x4w'x3
        Y, X = y * 4, x * 4
        out[Y:Y + r.shape[0], X:X + r.shape[1]] += r * (wy[Y:Y + r.shape[0], None] * wx[None, X:X + r.shape[1]])[:, :, None]
        weight[Y:Y + r.shape[0], X:X + r.shape[1]] += wy[Y:Y + r.shape[0], None] * wx[None, X:X + r.shape[1]]
        print(f"\r  分块 {i}/{total}（{time.time() - t0:.0f}s/块）", end="", flush=True)
    print("\r" + " " * 30 + "\r", end="")
    return np.clip(out / np.maximum(weight, 1e-6)[..., None], 0, 1)


def upscale_one(src: Path, args) -> Path:
    img = Image.open(src)
    if img.mode != "RGB":
        if img.mode in ("RGBA", "LA", "P"):
            print(f"  ⚠ 透明底会被平铺成白底再超分")
        img = img.convert("RGB")

    arr = np.asarray(img, dtype=np.float32) / 255.0
    import onnxruntime as ort
    sess = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])

    if arr.shape[0] <= args.tile and arr.shape[1] <= args.tile:
        result = sess.run(None, {"input": arr.transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
        result = np.clip(result, 0, 1)
    else:
        result = _tiled_run(sess, arr, args.tile, args.overlap)

    out_img = Image.fromarray((result * 255).round().astype(np.uint8))
    if args.scale != 4:
        out_img = out_img.resize((img.width * args.scale, img.height * args.scale), Image.LANCZOS)

    dst = src.parent / f"{src.stem}_x{args.scale}{'.jpg' if args.jpg else '.png'}"
    out_img.save(dst, **({"quality": 92} if args.jpg else {"optimize": True}))
    print(f"  {src.name} {img.width}x{img.height} → {out_img.width}x{out_img.height} → {dst.name}")
    return dst


def main() -> None:
    ap = argparse.ArgumentParser(description="图片无损放大（Real-ESRGAN x4，本地 CPU 推理）")
    ap.add_argument("inputs", nargs="+", type=Path, help="图片路径，支持多张")
    ap.add_argument("--scale", type=int, default=4, choices=(1, 2, 4), help="放大倍数（默认 4；1=仅修复画质）")
    ap.add_argument("--tile", type=int, default=384, help="分块边长（默认 384；小图自动整图推理）")
    ap.add_argument("--overlap", type=int, default=32, help="分块重叠像素（默认 32）")
    ap.add_argument("--jpg", action="store_true", help="输出 jpg（默认 png 无损）")
    args = ap.parse_args()

    _ensure_model()
    for src in args.inputs:
        if not src.exists():
            raise SystemExit(f"找不到文件：{src}")
        upscale_one(src, args)


if __name__ == "__main__":
    sys.exit(main())
