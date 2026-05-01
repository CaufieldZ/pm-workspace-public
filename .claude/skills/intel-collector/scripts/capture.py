#!/usr/bin/env python3
"""竞品 APP 截图自动采集 — 录屏 + 抽帧模式，绕过 APP 截屏检测弹窗。

原理：iOS APP 通过 UIApplicationUserDidTakeScreenshotNotification 检测截屏并弹窗，
但屏幕录制（screencapture -v）不触发该通知。录全屏视频后 ffmpeg 裁剪+抽帧+去重。

用法:
  python3 capture.py --output-dir /tmp/captures-20260415/
  python3 capture.py --output-dir /tmp/captures/ --duration 30

输出: JSON 到 stdout，格式 {"captures": [{path, timestamp}], "total": N}

依赖: ffmpeg, sips (macOS 内置)
"""
import argparse, json, os, struct, subprocess, sys, time


def find_iphone_mirror_window():
    """获取 iPhone 镜像窗口的 bounds 和所在屏幕的 scale factor。

    Returns: (x, y, width, height, scale) 或 None。坐标为逻辑像素。
    """
    swift_code = r"""
import Cocoa
let opts = CGWindowListOption(arrayLiteral: .optionOnScreenOnly)
if let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] {
    for w in list {
        let owner = w["kCGWindowOwnerName"] as? String ?? ""
        if owner.contains("iPhone") && (owner.contains("镜像") || owner.contains("Mirror")) {
            if let bounds = w["kCGWindowBounds"] as? [String: Any],
               let x = bounds["X"] as? Int,
               let y = bounds["Y"] as? Int,
               let bw = bounds["Width"] as? Int,
               let bh = bounds["Height"] as? Int {
                let center = NSPoint(x: CGFloat(x) + CGFloat(bw)/2, y: CGFloat(y) + CGFloat(bh)/2)
                var scale = 2
                for screen in NSScreen.screens {
                    if NSPointInRect(center, screen.frame) {
                        scale = Int(screen.backingScaleFactor)
                        break
                    }
                }
                print("\(x),\(y),\(bw),\(bh),\(scale)")
            }
            break
        }
    }
}
"""
    result = subprocess.run(
        ["swift", "-e", swift_code],
        capture_output=True, text=True, timeout=10
    )
    parts = result.stdout.strip().split(",")
    if len(parts) != 5 or not all(p.lstrip("-").isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def get_pixels(path):
    """缩小到 32x32 BMP 提取像素字节，用于帧间对比。"""
    tmp_bmp = path + ".thumb.bmp"
    try:
        subprocess.run(
            ["sips", "-z", "32", "32", "-s", "format", "bmp", path, "--out", tmp_bmp],
            capture_output=True, timeout=5
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if not os.path.exists(tmp_bmp):
        return None
    data = open(tmp_bmp, "rb").read()
    os.remove(tmp_bmp)
    offset = struct.unpack_from("<I", data, 10)[0]
    return data[offset:]


def pixel_diff_pct(pixels_a, pixels_b):
    """计算两帧像素差异百分比。"""
    if pixels_a is None or pixels_b is None:
        return 100.0
    if len(pixels_a) != len(pixels_b):
        return 100.0
    diff = sum(1 for a, b in zip(pixels_a, pixels_b) if a != b)
    return diff / len(pixels_a) * 100


# 阈值：<10% 视为同一画面（H.264 解码噪声约 1-3%，滚动中差异 >50%）
DIFF_THRESHOLD = 10.0
# 连续 N 帧静止视为用户停下来了
STABLE_COUNT = 2


def extract_stable_frames(video_path, crop_rect, output_dir, fps=2):
    """从视频中抽帧、裁剪、去重，只保留用户停下来时的画面。

    Args:
        video_path: 录屏视频路径
        crop_rect: ffmpeg crop 参数 "w:h:x:y"（像素坐标）
        output_dir: 输出目录
        fps: 抽帧频率

    Returns:
        list of {"path": str, "timestamp": str}
    """
    tmp_dir = os.path.join(output_dir, "_frames")
    os.makedirs(tmp_dir, exist_ok=True)

    # ffmpeg 抽帧 + 裁剪
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps},crop={crop_rect}",
        os.path.join(tmp_dir, "frame_%04d.png"),
        "-y", "-loglevel", "error"
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)

    # 列出所有帧
    frame_files = sorted([
        os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)
        if f.startswith("frame_") and f.endswith(".png")
    ])

    if not frame_files:
        return []

    # 静止帧检测 + 去重
    captures = []
    seq = 0
    prev_pixels = None
    stable_counter = 0
    changed = False
    saved_pixels = None

    for frame_path in frame_files:
        curr_pixels = get_pixels(frame_path)
        diff = pixel_diff_pct(prev_pixels, curr_pixels)

        if diff > DIFF_THRESHOLD:
            # 画面变了（翻页/滚动中）
            stable_counter = 0
            changed = True
            prev_pixels = curr_pixels
        else:
            # 画面没变
            prev_pixels = curr_pixels
            if changed:
                stable_counter += 1
                if stable_counter >= STABLE_COUNT:
                    # 用户停下来了，检查是否和上次保存的重复
                    dup = pixel_diff_pct(saved_pixels, curr_pixels) < DIFF_THRESHOLD
                    if not dup:
                        seq += 1
                        save_path = os.path.join(output_dir, f"{seq:03d}.png")
                        os.rename(frame_path, save_path)
                        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                        captures.append({"path": save_path, "timestamp": ts})
                        saved_pixels = curr_pixels
                        print(f"  📷 #{seq} 有效截图", file=sys.stderr)
                    changed = False
                    stable_counter = 0

    # 如果最后几帧是静止的但没达到 STABLE_COUNT，也保留最后一帧
    if changed and stable_counter > 0:
        last_frame = frame_files[-1]
        if os.path.exists(last_frame):
            dup = pixel_diff_pct(saved_pixels, get_pixels(last_frame)) < DIFF_THRESHOLD
            if not dup:
                seq += 1
                save_path = os.path.join(output_dir, f"{seq:03d}.png")
                os.rename(last_frame, save_path)
                ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                captures.append({"path": save_path, "timestamp": ts})
                print(f"  📷 #{seq} 有效截图（末帧）", file=sys.stderr)

    # 清理临时帧目录
    for f in os.listdir(tmp_dir):
        fpath = os.path.join(tmp_dir, f)
        if os.path.isfile(fpath):
            os.remove(fpath)
    os.rmdir(tmp_dir)

    return captures


def main():
    parser = argparse.ArgumentParser(
        description="竞品 APP 截图采集（录屏模式，绕过截屏检测）"
    )
    parser.add_argument("--output-dir", required=True, help="截图保存目录")
    parser.add_argument("--duration", type=int, default=60, help="录制时长(秒)，默认 60")
    parser.add_argument("--fps", type=int, default=2, help="抽帧频率，默认 2fps")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 1. 找 iPhone 镜像窗口
    result = find_iphone_mirror_window()
    if result is None:
        print("❌ 未找到 iPhone 镜像窗口，请确认已打开", file=sys.stderr)
        sys.exit(1)

    x, y, w, h, scale = result
    crop_rect = f"{w * scale}:{h * scale}:{x * scale}:{y * scale}"

    print(f"✅ 找到 iPhone 镜像窗口 ({w}x{h}，scale={scale}x)", file=sys.stderr)
    print(f"📹 开始录制 {args.duration} 秒，请翻阅竞品页面。", file=sys.stderr)
    print(f"   录制期间请勿移动 iPhone 镜像窗口。", file=sys.stderr)

    # 2. 全屏录制（不触发 iOS 截屏通知）
    video_path = os.path.join(args.output_dir, "_recording.mov")
    try:
        subprocess.run(
            ["screencapture", "-v", "-V", str(args.duration), video_path],
            timeout=args.duration + 10
        )
    except subprocess.TimeoutExpired:
        pass

    if not os.path.exists(video_path):
        print("❌ 录制失败", file=sys.stderr)
        sys.exit(1)

    print(f"📼 录制完成，正在提取有效帧...", file=sys.stderr)

    # 3. 抽帧 + 裁剪 + 去重
    captures = extract_stable_frames(video_path, crop_rect, args.output_dir, args.fps)

    # 4. 清理视频文件
    os.remove(video_path)

    print(f"✅ 完成，共 {len(captures)} 张有效截图", file=sys.stderr)

    # 输出 JSON
    result = {"captures": captures, "total": len(captures)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
