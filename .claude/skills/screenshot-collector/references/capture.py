#!/usr/bin/env python3
# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
# pm-ws-canary-236a5364
"""竞品 APP 截图自动采集 — 监控 iPhone 镜像窗口，检测页面变化自动截图。

用法:
  python3 capture.py --output-dir /tmp/captures-20260411/

输出: JSON 到 stdout，格式 {"captures": [{path, timestamp}], "total": N}
"""
import argparse, hashlib, json, os, subprocess, sys, time


def find_iphone_mirror_window():
    """通过 Swift + CGWindowListCopyWindowInfo 获取 iPhone 镜像窗口 ID。"""
    swift_code = r"""
import Cocoa
let opts = CGWindowListOption(arrayLiteral: .optionOnScreenOnly)
if let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] {
    for w in list {
        let owner = w["kCGWindowOwnerName"] as? String ?? ""
        if owner.contains("iPhone") && (owner.contains("镜像") || owner.contains("Mirror")) {
            let wid = w["kCGWindowNumber"] as? Int ?? 0
            print(wid)
            break
        }
    }
}
"""
    result = subprocess.run(
        ["swift", "-e", swift_code],
        capture_output=True, text=True, timeout=10
    )
    wid = result.stdout.strip()
    if not wid or not wid.isdigit():
        print("❌ 未找到 iPhone 镜像窗口，请确认已打开", file=sys.stderr)
        sys.exit(1)
    return int(wid)


def capture_frame(window_id, output_path):
    """用 screencapture 截取指定窗口。"""
    try:
        subprocess.run(
            ["screencapture", "-x", "-l", str(window_id), output_path],
            capture_output=True, timeout=5
        )
        return os.path.exists(output_path)
    except (subprocess.TimeoutExpired, OSError):
        return False


def get_pixels(path):
    """提取图片原始像素数据（缩小到 32x32 BMP 后取像素字节）。"""
    import struct
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


# iPhone 镜像视频流帧间噪声约 0~5%，翻页面差异 50%+
DIFF_THRESHOLD = 15.0


def main():
    parser = argparse.ArgumentParser(description="iPhone 镜像竞品截图采集")
    parser.add_argument("--output-dir", required=True, help="截图保存目录")
    parser.add_argument("--interval", type=float, default=0.5, help="轮询间隔(秒)")
    parser.add_argument("--stable-count", type=int, default=3, help="连续 N 帧不变视为稳定")
    parser.add_argument("--duration", type=int, default=0, help="采集时长(秒)，0=无限制(Ctrl+C停)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 找窗口
    wid = find_iphone_mirror_window()
    print(f"✅ 找到 iPhone 镜像窗口 (ID={wid})", file=sys.stderr)
    dur_msg = f"（{args.duration}秒后自动结束）" if args.duration > 0 else "Ctrl+C 结束"
    print(f"📸 开始监控，翻页面就行。{dur_msg}", file=sys.stderr)
    start_time = time.time()

    captures = []
    seq = 0
    prev_pixels = None
    stable_counter = 0
    changed = False
    saved_pixels = None  # 上一次保存时的像素，避免重复保存相同页面
    tmp_frame = os.path.join(args.output_dir, "_current_frame.png")

    try:
        while True:
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"\n⏱ 已达 {args.duration} 秒，自动结束", file=sys.stderr)
                break
            # 截当前帧
            if not capture_frame(wid, tmp_frame):
                time.sleep(args.interval)
                continue

            curr_pixels = get_pixels(tmp_frame)
            diff = pixel_diff_pct(prev_pixels, curr_pixels)

            if diff > DIFF_THRESHOLD:
                # 画面真的变了
                stable_counter = 0
                changed = True
                prev_pixels = curr_pixels
            else:
                # 画面没变（或只有噪声）
                prev_pixels = curr_pixels
                if changed:
                    stable_counter += 1
                    if stable_counter >= args.stable_count:
                        # 稳定了，检查是否和上次保存的重复
                        dup = pixel_diff_pct(saved_pixels, curr_pixels) < DIFF_THRESHOLD
                        if not dup:
                            seq += 1
                            save_path = os.path.join(args.output_dir, f"{seq:03d}.png")
                            capture_frame(wid, save_path)
                            ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                            captures.append({"path": save_path, "timestamp": ts})
                            saved_pixels = curr_pixels
                            print(f"  📷 #{seq} 已截图 ({ts})", file=sys.stderr)
                        changed = False
                        stable_counter = 0

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n⏹ 结束采集，共 {len(captures)} 张", file=sys.stderr)

    # 清理临时帧
    if os.path.exists(tmp_frame):
        os.remove(tmp_frame)

    # 输出 JSON 到 stdout
    result = {"captures": captures, "total": len(captures)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
