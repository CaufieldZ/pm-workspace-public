"""
裁剪音视频（不重编码，秒级精度）。

用法：
  python3 scripts/av_trim.py video.mp4 --start 00:00:10 --end 00:01:30
  python3 scripts/av_trim.py audio.m4a --start 30 --duration 60
  python3 scripts/av_trim.py video.mp4 --start 10 --end 90 -o clip.mp4

时间格式：秒（30）或 H:M:S（00:00:30）。
默认 -c copy（不转码、瞬间完成、可能在非关键帧切口处掉首帧）。
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="ffmpeg 音视频裁剪")
    parser.add_argument("input", type=Path)
    parser.add_argument("--start", required=True, help="起点（秒或 H:M:S）")
    end = parser.add_mutually_exclusive_group(required=True)
    end.add_argument("--end",      help="终点（秒或 H:M:S）")
    end.add_argument("--duration", help="持续时长（秒或 H:M:S）")
    parser.add_argument("-o", "--output", type=Path, help="输出，默认 {原名}_trimmed.{ext}")
    parser.add_argument("--reencode", action="store_true",
                        help="重编码（精确切口但慢；H.264+AAC）")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"找不到：{args.input}")
        sys.exit(1)

    out = args.output or args.input.with_name(f"{args.input.stem}_trimmed{args.input.suffix}")

    cmd = ["ffmpeg", "-y", "-ss", args.start, "-i", str(args.input)]
    if args.end:
        cmd += ["-to", args.end]
    else:
        cmd += ["-t", args.duration]

    if args.reencode:
        cmd += ["-c:v", "libx264", "-c:a", "aac", "-preset", "medium"]
    else:
        cmd += ["-c", "copy"]
    cmd += [str(out)]

    print("→", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.exit(rc)
    print(f"\n→ {out}  ({out.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
