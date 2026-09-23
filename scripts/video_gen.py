#!/usr/bin/env python3
"""video_gen.py — MiniMax H3 出视频：文生 / 图生（首尾帧）/ 参考生成，建任务轮询下载。

用法:
  python3 scripts/video_gen.py "提示词"                                  # 文生视频：H3-Max 极速 · 768P · 5s · 16:9
  python3 scripts/video_gen.py "镜头缓推，女孩回头微笑" --resolution 2K --duration 10
  python3 scripts/video_gen.py "让她转头看向镜头" --first-frame in.png    # 图生视频（首帧驱动）
  python3 scripts/video_gen.py "由白昼渐变到黑夜" --first-frame a.png --last-frame b.png
  python3 scripts/video_gen.py "角色照参考视频的动作说这句台词，音色参考音频1" \\
      --ref-video ref.mp4 --ref-audio voice.mp3                         # 多模态参考生视频
  python3 scripts/video_gen.py "提示词" --model h3 --resolution 2K       # H3 质量档：2K、4–15 秒
  python3 scripts/video_gen.py --prompt-file shot.txt                    # 从文件读长提示词（官方三段结构）
  python3 scripts/video_gen.py --task-id 424010985738629 --out keep.mp4  # 只续查已建任务并下载
  python3 scripts/video_gen.py "提示词" -p <项目>                        # 产物落 projects/<项目>/deliverables/assets/

端点:
  建任务  POST {BASE}/v2/video_generation            -> {"task_id": ...}
  查任务  GET  {BASE}/v2/query/video_generation/{id}  -> {"task": {status, content.url, usage, ...}}
  异步任务：建完轮询到终态再下载；2K 档常要几分钟，Ctrl+C 中断后拿 --task-id 续查，不重复计费

Key 与域名: 环境变量 VIDEO_API_KEY / VIDEO_BASE_URL(S)——脚本自动读工区根 .env（环境变量优先）。
  脚本内没有默认端点：两个变量都必给（域名不入 git）。
  video 走 /v2 路径，base 只写域名——不带 /v1；带了会被自动剥掉（从 IMAGE_BASE_URL 抄来的
  /v1 是最常见错法，不剥会拼出 /v1/v2/... 打到不存在的地址）。VIDEO_BASE_URLS 给多个端点时
  并发测握手选最快（行为同 image_gen.py）。

模型:
  max（默认）= MiniMax-H3-Max：极速生成，480P / 768P（不支持 2K），5–15 秒（不支持 4 秒），
              独享 --prompt-expand 提示词扩写档（disabled / balanced / quality，默认 balanced）
  h3         = MiniMax-H3：768P / 2K，4–15 秒——要 2K、4 秒时用它

ratio:
  文生视频必填且不能 adaptive，没给时默认 16:9
  图生视频恒 adaptive（比例由输入图决定，显式传会被忽略——脚本直接不传并提示）
  参考生视频可选，默认 adaptive

本地媒体: 自动转 base64 data URI 塞进请求体；官方请求体总限 64MB 且 base64 放大约 33%，
  大文件（长参考视频 / 多图）直接给 http(s) 公网 URL 更稳（网关可能另有更小的体量上限）。
  媒体 URL 只收公网 http(s)：非 http(s) 协议、带账号密码、解析到内网 / 回环 / 链路本地 /
  保留段（含 169.254.169.254 云元数据地址）的一律拒收，不发给端点（SSRF 兜底）。
  首帧 / 尾帧 / 参考图：jpg jpeg png webp heic heif，单张 ≤30MB（参考图 ≤9 张）
  参考视频：mp4 mov，单个 ≤50MB，≤3 段，单段 2–15s
  参考音频：wav mp3，单个 ≤15MB，≤3 段，单段 2–15s
  首尾帧（first_frame / last_frame）与参考类（reference_*）互斥，混用会被脚本拦下

提示词: ≤7000 字符，任何场景必填；正文英文写，对白 / 歌词 / 画内文字保留原文；多行结构用
  --prompt-file 从文件读（- 走 stdin）。要点（官方 h3-prompt-writing 规范）：
  - 三段结构：integrated_multimodal_description（沿时间线的画面 + 动作 + 分镜 [Shot N]）/
    overall_soundscape（1–4 句环境音，整片静音才写 N/A）/ non_diegetic_music（配乐只写配器 /
    速度 / 节奏 / 动态，禁 epic / 大气这类抽象情绪词；无配乐写 N/A）。
  - 分镜：[Shot 1] 不加时间戳（官方明文）；切镜写作 [Shot 2] At 00:03.500, ...，时间严格递增、
    落在时长内；只换景别 / 角度用运镜，不切镜。
  - 运镜写进句子里当动作（The camera pushes in with small amplitude at slow speed ...），不是句尾
    贴标签；类型 Zoom In / Push In / Pan / Truck / Tilt / Pedestal / Arc Shot / Tracking Shot /
    Static Shot / Shake / POV / Roll。
  - 工艺水位（运镜之外的三件）：**景别**逐镜给（close-up / medium shot / wide shot；运镜 ≠ 景别）；
    **光线**给方向与质感（backlit rim light / soft overcast / neon glow），不给就是一套平光；
    **剪辑率**按时长配镜头数，平均每镜短于 1.5s 是闪切。三项体检会查。
  - 对白：说话人给稳定 ID (S1)，对白原文逐字进 <d>[语言] ...</d>，say / shout 这类动词与身份
    描述放 <d> 外；跨切镜 <scenetrans>，被片尾截断 <cutoff>。
  - 图生 / 首尾帧 / 尾帧：第一行是固定句式的对齐指令（<Picture 1> 锚 0.00 秒，尾帧锚 S.SS 秒）。
  - 全参考（--ref-image / --ref-video / --ref-audio）：六段固定顺序 subject_definitions / summary /
    retention_analysis / detailed_description / overall_soundscape / non_diegetic_music；素材标
    <Subject N> / <Picture N> / <Video N> / <Audio N> 并在正文引用。
  - 禁写「禁止出现 X」清单（官方无负面提示词机制）；不写声音字段模型会自行编造。
  完整规则、运镜词表与官方示例见 references/h3-prompt-writing/（base-en.txt 基础模式 /
  ref-en.txt 全参考模式 / notes.md 工区实战笔记）。
  脚本落盘前跑一遍提示词体检，命中官方规则的问题只提示、不改写提示词。

退出码: 0 = 成功下载；2 = 参数 / 校验不过、任务失败、查询超时；130 = 轮询中被 Ctrl+C（--task-id 可续查）。

前置:
  工区 .env 的 VIDEO_API_KEY / VIDEO_BASE_URL(S)（--help 本身不需要）；依赖 requests。
"""
# route-log: scripts/lib/route_log.py
import sys as _s, pathlib as _pl
_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("video_gen"))

import argparse
import base64
import ipaddress
import json
import os
import pathlib
import random
import re
import socket
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests
from lib.env_refs import apply_env_file  # noqa: E402
from lib.projects import resolve_project_assets  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]

MODEL_ALIASES = {"h3": "MiniMax-H3", "max": "MiniMax-H3-Max"}
MODEL_SPECS = {
    "MiniMax-H3": {"resolutions": ("768P", "2K"), "duration": (4, 15)},
    "MiniMax-H3-Max": {"resolutions": ("480P", "768P"), "duration": (5, 15)},
}
RESOLUTION_CHOICES = ("480P", "768P", "2K")
RATIO_CHOICES = ("adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16")
T2V_DEFAULT_RATIO = "16:9"

MEDIA_KINDS = {
    "image": {"exts": {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                       ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif"},
              "limit_bytes": 30 * 1024 * 1024},
    "video": {"exts": {".mp4": "video/mp4", ".mov": "video/quicktime"},
              "limit_bytes": 50 * 1024 * 1024},
    "audio": {"exts": {".wav": "audio/wav", ".mp3": "audio/mpeg"},
              "limit_bytes": 15 * 1024 * 1024},
}
MAX_REF_IMAGES = 9
MAX_REF_VIDEOS = 3
MAX_REF_AUDIOS = 3
# 官方请求体总限 64MB；本地媒体按 base64 编码后长度合计封顶，留 4MB 给 JSON 骨架
MAX_ENCODED_MEDIA_BYTES = 60 * 1024 * 1024

MAX_PROMPT_CHARS = 7000

# 提示词体检阈值（折算字数：汉字按 2 计，口径同 image_gen.py）
PROMPT_SHORT_UNITS = 50         # 低于此值写不下主体 / 动作 / 运镜 / 氛围
PROMPT_STRUCT_HINT_UNITS = 150  # 长于此值仍无官方结构标记 → 建议按三段组织
PROMPT_EN_HINT_UNITS = 100      # 中文简报超过此长度 → 提示官方以英文写正文
MIN_SECONDS_PER_SHOT = 1.5      # 平均每镜头短于此值基本是闪切，观众读不到画面信息
SHOT_SIZE_HINT_SHOTS = 2        # 达到此镜头数才算一份分镜，才查景别（单镜头不查）
PACE_HINT_SHOTS = 3             # 低于此镜头数不谈剪辑率（2 镜头短片是正常写法）

CREATE_TIMEOUT = 60      # 建任务本身很快，60s 已算宽裕
POLL_TIMEOUT = 30        # 单次查询超时
DOWNLOAD_TIMEOUT = 300   # 2K 成片几十 MB，慢 CDN 也要下得完
PROBE_TIMEOUT = 5.0      # 多端点路由的握手探测超时（秒）

DEFAULT_POLL_INTERVAL = 10.0
DEFAULT_WAIT_TIMEOUT = 900.0   # 2K 5s 片实测档要数分钟，15 分钟兜底
POLL_MAX_MISSES = 6            # 连续查询失败容忍次数——网络抖动不该杀掉等了几分钟的任务

RETRY_MAX_DEFAULT = 2
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 60.0

TERMINAL_OK = "succeeded"
TERMINAL_BAD = ("failed", "cancelled")

_URL_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.IGNORECASE)


def _resolve_host_ips(host):
    """主机名 -> 解析出的全部 IP（IP 字面量直接返回自身）；解析不了返回 []。"""
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, OSError):
        return []
    return list({ipaddress.ip_address(info[4][0]) for info in infos})


def _local_only(ip):
    """回环 / 链路本地 / 未指定 / 组播——任何部署下都不该被访问。"""
    return ip.is_loopback or ip.is_link_local or ip.is_unspecified or ip.is_multicast


def url_problem(url, what="URL", allow_private=False):
    """SSRF 兜底：地址只放行公网 http(s)。

    拒非 http(s) 协议与带账号密码的 URL，再解析主机名查全部 IP：allow_private=False
    （用户 / 模型给的媒体 URL）拒一切非公网地址（内网 / 回环 / 链路本地 / 保留段，含
    169.254.169.254 云元数据）；allow_private=True（端点下发的下载地址）只拒回环 /
    链路本地 / 未指定 / 组播——产物落在内网 CDN 是合法部署。返回人话错误，合规 None。
    端点地址（VIDEO_BASE_URL）不经此检查——那是使用方自己配置的网关。
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return f"{what} 只认 http(s) 地址（收到 {parts.scheme or '无协议'}）：{url}"
    if parts.username or parts.password:
        return f"{what} 不能带账号密码：{url}"
    host = parts.hostname
    if not host:
        return f"{what} 缺主机名：{url}"
    ips = _resolve_host_ips(host)
    if not ips:
        return f"{what} 域名解析不了：{host}"
    blocked = [ip for ip in ips if _local_only(ip) or (not allow_private and not ip.is_global)]
    if blocked:
        hint = "" if allow_private else "—— 媒体请用公网 http(s) 地址或改用本地文件"
        return f"{what} 指向不可访问地址（{' / '.join(map(str, blocked))}），已拒绝：{url}{hint}"
    return None


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def normalize_base(base):
    """去尾斜杠；路径恰为 /v1 的剥掉——video 走 /v2 路径，从 IMAGE_BASE_URL 抄来的 /v1
    会拼出 /v1/v2/video_generation 打到不存在的地址。其他自定义路径原样保留。"""
    base = (base or "").strip().rstrip("/")
    parts = urllib.parse.urlsplit(base)
    if parts.path == "/v1":
        base = parts._replace(path="").geturl()
    return base


def parse_base_candidates(spec):
    """'url1, url2,,url1' -> 归一化后去空、去重、保序的候选端点；空 / None -> []。"""
    seen = []
    for part in (spec or "").split(","):
        url = normalize_base(part)
        if url and url not in seen:
            seen.append(url)
    return seen


def probe_base(base, timeout=PROBE_TIMEOUT):
    """GET 查询端点测握手；有响应（任意状态码）算通，返回毫秒；失败返回 None。"""
    t0 = time.time()
    try:
        requests.get(f"{base}/v2/query/video_generation/probe", timeout=timeout)
    except requests.RequestException:
        return None
    return (time.time() - t0) * 1000


def pick_fastest(results):
    """[(base, ms|None)] -> 握手成功且最短者；全失败取首个；空表 -> None。"""
    ok = [(b, ms) for b, ms in results if ms is not None]
    if ok:
        return min(ok, key=lambda item: item[1])[0]
    return results[0][0] if results else None


def route_base(candidates):
    """并发探测候选端点选最快者；单候选不探测。结果与各候选用时打 stderr 提示。"""
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    with ThreadPoolExecutor(max_workers=len(candidates)) as pool:
        results = list(pool.map(lambda b: (b, probe_base(b)), candidates))
    chosen = pick_fastest(results)
    detail = "；".join(f"{b} {'失败' if ms is None else f'{ms:.0f}ms'}" for b, ms in results)
    print(f"提示：端点路由 → {chosen}（{detail}）", file=sys.stderr)
    return chosen


def load_conf():
    """读 VIDEO_API_KEY / VIDEO_BASE_URL(S)：apply_env_file 灌入工区根 .env 后取环境变量。

    VIDEO_BASE_URLS 为可选的多端点清单（逗号分隔）：设了就探测选最快者；未设用单一 VIDEO_BASE_URL。
    脚本内没有默认端点——两个变量都必给。
    """
    apply_env_file(ROOT / ".env")
    key = (os.environ.get("VIDEO_API_KEY") or "").strip()
    candidates = parse_base_candidates(os.environ.get("VIDEO_BASE_URLS")) \
        or parse_base_candidates(os.environ.get("VIDEO_BASE_URL") or "")
    missing = []
    if not key:
        missing.append("VIDEO_API_KEY")
    if not candidates:
        missing.append("VIDEO_BASE_URL（或 VIDEO_BASE_URLS）")
    if missing:
        fail(f"{' / '.join(missing)} 未设置（放工区根目录 .env，或导出同名环境变量）")
    return key, route_base(candidates)


# ── 前置校验（官方限值；坏参数在花钱之前拦下）────────────────────────────
def resolution_problem(model, resolution):
    allowed = MODEL_SPECS[model]["resolutions"]
    if resolution not in allowed:
        return f"{model} 只支持 {' / '.join(allowed)}，收到 {resolution}"
    return None


def duration_problem(model, duration):
    lo, hi = MODEL_SPECS[model]["duration"]
    if not lo <= duration <= hi:
        return f"{model} 时长须 {lo}–{hi} 秒，收到 {duration}"
    return None


def input_mode(first_frame, last_frame, ref_images, ref_videos, ref_audios):
    """-> 't2v' / 'i2v' / 'r2va'（决定 ratio 规则与 content 组合）。"""
    if first_frame or last_frame:
        return "i2v"
    if ref_images or ref_videos or ref_audios:
        return "r2va"
    return "t2v"


def mix_problem(first_frame, last_frame, ref_images, ref_videos, ref_audios):
    """官方：图生视频（首尾帧）与多模态参考生视频（reference_*）互斥，不可混用。"""
    has_frame = bool(first_frame or last_frame)
    has_ref = bool(ref_images or ref_videos or ref_audios)
    if has_frame and has_ref:
        return "首尾帧（--first-frame / --last-frame）与参考类（--ref-image / --ref-video / --ref-audio）互斥，不可混用"
    return None


def effective_ratio(mode, requested):
    """-> (发送值或 None（不发送）, 提示列表, 错误或 None)。

    t2v 必填非 adaptive（没给默认 16:9）；i2v 恒 adaptive（显式传会被忽略，脚本不传并提示）；
    r2va 可选，默认 adaptive。
    """
    if mode == "t2v":
        if requested is None:
            return T2V_DEFAULT_RATIO, [f"文生视频必须指定比例，默认按 {T2V_DEFAULT_RATIO} 出（要改用 --ratio）"], None
        if requested == "adaptive":
            return None, [], "文生视频的 --ratio 不能是 adaptive——比例须显式指定"
        return requested, [], None
    if mode == "i2v":
        if requested in (None, "adaptive"):
            return None, [], None
        return None, [f"图生视频比例由输入图决定，--ratio {requested} 会被忽略（按 adaptive 处理）"], None
    # r2va
    if requested is None:
        return None, [], None
    return requested, [], None


def prompt_problem(prompt):
    if not prompt or not prompt.strip():
        return "提示词必填（所有场景都要有非空 text）"
    if len(prompt) > MAX_PROMPT_CHARS:
        return f"提示词 {len(prompt)} 字符超过官方上限 {MAX_PROMPT_CHARS}"
    return None


def prepare_media(specs, kind):
    """把输入规格变成可发 URL：公网 http(s) 原样、本地文件转 base64 data URI。

    返回 (items, problems)：items 是 [(url, 编码后字节数)]（URL 输入计 0）；
    problems 是人话错误列表——出错的那条不进 items，其余照常处理，一次把问题报全。
    URL 输入过 url_problem 的 SSRF 兜底（非公网地址拒收，不发给端点）。
    """
    spec = MEDIA_KINDS[kind]
    items, problems = [], []
    for s in specs or []:
        if _URL_RE.match(s):
            if problem := url_problem(s, f"{kind} 媒体 URL"):
                problems.append(problem)
                continue
            items.append((s, 0))
            continue
        path = pathlib.Path(s)
        if not path.is_file():
            problems.append(f"输入不存在：{s}")
            continue
        mime = spec["exts"].get(path.suffix.lower())
        if mime is None:
            problems.append(f"{path.name} 不是 {kind} 支持的格式（{' '.join(sorted(spec['exts']))}）")
            continue
        raw = path.read_bytes()
        if len(raw) > spec["limit_bytes"]:
            problems.append(f"{path.name} {len(raw) / 1024 / 1024:.1f}MB 超过单文件上限 "
                            f"{spec['limit_bytes'] // 1024 // 1024}MB")
            continue
        uri = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
        items.append((uri, len(uri)))
    return items, problems


def body_cap_problem(encoded_total):
    if encoded_total > MAX_ENCODED_MEDIA_BYTES:
        return (f"本地媒体 base64 后共 {encoded_total / 1024 / 1024:.1f}MB，逼近请求体上限 64MB"
                "——大文件改传 http(s) 公网 URL")
    return None


# ── 提示词体检（官方 h3-prompt-writing 指南里能机械判定的那几条；只提示，不改写）──
# 规则来源：MiniMax 官方仓库 skills/h3-prompt-writing 的 references/base-en.txt 与 ref-en.txt
# （本地留档 references/h3-prompt-writing/；改规则前先对一遍原文）。
# 判不准的一律不报——提示疲劳比漏报更糟（image_gen.prompt_notes 的教训）。
_CJK = re.compile(r"[一-鿿]")
STRUCT_FIELD = re.compile(r"integrated_multimodal_description|detailed_description|subject_definitions",
                          re.IGNORECASE)
SHOT_MARK = re.compile(r"\[Shot\s*(\d+)\]", re.IGNORECASE)
SHOT1_TS = re.compile(r"\[Shot\s*1\][^\[]*?At\s+\d{1,2}:\d{2}", re.IGNORECASE)
_TIMECODE = re.compile(r"At\s+(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?", re.IGNORECASE)
CAMERA_MOTION = re.compile(
    r"静态|固定机位|镜头不动|推进|拉远|拉出|推近|左摇|右摇|摇镜|平移|跟随|环绕|升降|变焦|晃动"
    r"|\bzoom|\bpush(?:es)? in|\bpull(?:s)? out|\bpans?\b|\btrucks?\b|\btilts?\b|\bpedestals?\b"
    r"|\barc shots?\b|\btracking shots?\b|\bstatic shots?\b|\bshakes?\b|\bPOV\b"
    r"|\broll(?:s)? (?:clockwise|counterclockwise)\b|\bholds? steady\b|\bremains? still\b|\bkeeps? still\b",
    re.IGNORECASE)
# 景别与运镜是两件事：CAMERA_MOTION 查镜头怎么动，SHOT_SIZE 查画面框多大。分镜缺景别，
# 模型逐镜自行取景，成片景别节奏是乱的
SHOT_SIZE = re.compile(
    r"特写|近景|中景|远景|全景|全身|半身|景别|过肩|大特写"
    r"|\bclose-?ups?\b|\bextreme close-?ups?\b|\bmedium(?:[- ](?:wide|close|long))?[- ]shots?\b"
    r"|\bwide shots?\b|\bfull shots?\b|\bestablishing shots?\b|\blong shots?\b"
    r"|\bover-the-shoulder\b|\bcowboy shots?\b|\btwo[- ]shots?\b",
    re.IGNORECASE)
LIGHTING = re.compile(
    r"光线|光照|打光|逆光|顺光|侧光|顶光|柔光|硬光|晨光|暮色|夕照|霓虹|反光|阴影|投影|月光|烛光"
    r"|\blight(?:ing|s|ed)?\b|\blit\b|\bbacklit\b|\bdaylight\b|\bsunlight\b|\bmoonlight\b|\bneon\b"
    r"|\bglow(?:ing)?\b|\bshadows?\b|\bgolden hour\b|\bdusk\b|\bdawn\b|\bovercast\b|\bsilhouette\b"
    r"|\bsunrise\b|\bsunset\b|\bcandlelit\b|\bfluorescent\b|\bspotlight\b",
    re.IGNORECASE)
SOUND_TERM = re.compile(r"声音|音效|音乐|配乐|环境音|静音|无声|喧嚣|雨声|风声"
                        r"|\bsounds?\b|\bmusic\b|\baudio\b|\bsoundscape\b|\bscore\b|\bambien",
                        re.IGNORECASE)
DIALOGUE_TERM = re.compile(r"台词|对白|独白|念白|说：|说道|喊道|唱|旁白"
                           r"|\bsays?\b|\bshouts?\b|\bwhispers?\b|\bsings?\b|\bvoiceover\b",
                           re.IGNORECASE)
MUSIC_MOOD = re.compile(r"\bepic\b|\bemotional\b|\bdramatic\b|\bcinematic\b|\batmospheric\b|\bbeautiful\b"
                        r"|大气|史诗|感人|激昂|紧张|震撼|氛围感|唯美", re.IGNORECASE)
REF_LABEL = re.compile(r"<(?:Subject|Picture|Video|Audio)\s*\d+>", re.IGNORECASE)
ALIGN_ANCHOR = re.compile(r"Picture\s*1|aligns with", re.IGNORECASE)


def cjk_ratio(text):
    """汉字占全文比例——判断提示词是不是中文主导。"""
    if not text:
        return 0.0
    return len(_CJK.findall(text)) / len(text)


def effective_length(text):
    """信息量折算字数：汉字按 2 计——同样字数中文承载的信息比英文多，拿字符数直接比会误判。"""
    if not text:
        return 0
    cjk = len(_CJK.findall(text))
    return cjk * 2 + (len(text) - cjk)


def timecode_seconds(text):
    """抽提示词里所有切镜时间戳（At MM:SS.mmm）-> 秒数列表。"""
    return [int(m) * 60 + int(s) + (int(ms.ljust(3, "0")) / 1000 if ms else 0.0)
            for m, s, ms in _TIMECODE.findall(text)]


def prompt_notes(prompt, mode, duration=None):
    """提示词体检：返回中文提示列表（可能为空）。只提示，不改写提示词。

    规则对准官方 h3-prompt-writing 指南；每条提示给出「缺什么 + 官方要什么 + 去哪看」。
    """
    notes = []
    text = prompt.strip()
    units = effective_length(text)
    short = units < PROMPT_SHORT_UNITS
    # 按去重后的编号数镜头：对齐指令会再引用一次 [Shot 1]（官方 i2v 句式），裸计数会把同一镜头数成两个
    shots = len(set(SHOT_MARK.findall(text)))

    if short:
        notes.append(
            f"提示词信息量偏少（折算 {units:.0f} 字）：短视频也要写清 主体 + 动作 + 镜头运动 + 光线氛围，"
            "官方结构与示例见 references/h3-prompt-writing/")
    elif not CAMERA_MOTION.search(text):
        notes.append(
            "没看到镜头运动的描述：视频与图片的核心差别就是运动——补一句运镜"
            "（Push In / Pan / Tracking Shot…），确实要固定机位就明写 Static Shot")

    # 运镜 ≠ 景别：上一条查镜头怎么动，这条查画面框多大。单镜头提示词不查（官方示例本身常不写），
    # 到了分镜（≥2 镜头）不给景别，模型会逐镜自行取景，成片的景别节奏是乱的
    if shots >= SHOT_SIZE_HINT_SHOTS and not SHOT_SIZE.search(text):
        notes.append(
            f"{shots} 个镜头但一个景别都没给：分镜要逐镜写清框多大"
            "（extreme close-up / close-up / medium shot / wide shot / establishing shot），"
            "否则模型自行取景，景别节奏失控")

    # 只对文生视频报：图生 / 参考生的光线由输入图带入（官方首尾帧示例正文就不写光线，
    # 只写「framing established by Picture 1」），对这两种模式要求补写是假阳
    if mode == "t2v" and not short and not LIGHTING.search(text):
        notes.append(
            "没写光线：光是影视画面的根本，不给模型会默认一套平光。补光源方向与质感"
            "（backlit rim light / soft overcast diffusion / neon glow / golden hour），"
            "夜戏与室内戏尤其要写")

    if not short and units >= PROMPT_STRUCT_HINT_UNITS \
            and not STRUCT_FIELD.search(text) and not SHOT_MARK.search(text):
        notes.append(
            "提示词较长但没按官方结构组织：建议拆成 integrated_multimodal_description / "
            "overall_soundscape / non_diegetic_music 三段（写法与示例见 references/h3-prompt-writing/）")

    if mode == "i2v" and not ALIGN_ANCHOR.search(text):
        notes.append(
            "图生视频没写对齐指令：官方要求第一行写明 <Picture 1> 与 0.00 秒（尾帧为 S.SS 秒 + [Shot N]）"
            "的对齐关系，句式固定（见 references/h3-prompt-writing/base-en.txt 第 2.1 节）")

    if SHOT1_TS.search(text):
        notes.append(
            "首个镜头带了时间戳：[Shot 1] 不加时间戳是官方明文要求，时间戳只从 [Shot 2] 起的切镜开始")

    if not re.search(r"overall_soundscape|non_diegetic_music", text, re.IGNORECASE) and not SOUND_TERM.search(text):
        notes.append(
            "没写任何声音信息：官方说音频是常见失败点，不指定声音模型会自行编造。补 overall_soundscape"
            "（1–4 句环境音）与 non_diegetic_music（配乐；无配乐写 N/A，整片静音 soundscape 才写 N/A）")

    if DIALOGUE_TERM.search(text) and "<d>" not in text:
        notes.append(
            "出现了对白 / 台词但没有 <d> 标签：对白原文放进 <d>[语言] ...</d> 逐字保留，"
            "说话人给 (S1) 这类稳定 ID（格式见 references/h3-prompt-writing/）")

    if m := re.search(r"non_diegetic_music\s*:(.*)$", text, re.IGNORECASE | re.DOTALL):
        if MUSIC_MOOD.search(m.group(1)):
            notes.append(
                "non_diegetic_music 里用了抽象情绪词：官方只认配器 / 速度 / 节奏 / 动态变化，"
                "epic、cinematic、大气这类会被要求改写")

    if mode == "r2va" and not REF_LABEL.search(text):
        notes.append(
            "参考生成没给素材标签：官方全参考六段式要求把参考素材标成 <Subject N> / <Picture N> / "
            "<Video N> / <Audio N> 并在正文引用（references/h3-prompt-writing/ref-en.txt）")

    if cjk_ratio(text) > 0.3 and units >= PROMPT_EN_HINT_UNITS:
        notes.append(
            "长中文简报：官方指南以英文写正文与运镜，对白 / 画内文字保留原文——"
            "英文核心指令更稳（官方示例全英文）")

    if duration:
        secs = timecode_seconds(text)
        if secs and max(secs) >= duration:
            notes.append(
                f"描述里的切镜时间到 {max(secs):.1f}s，已达到或超过 --duration {duration}s——"
                "官方要求时间线与视频时长一致，改时长或改描述")

        # 剪辑率：镜头数除进时长，平均每镜头太短就是闪切，观众读不到画面信息
        if shots >= PACE_HINT_SHOTS and duration / shots < MIN_SECONDS_PER_SHOT:
            notes.append(
                f"{duration}s 里塞了 {shots} 个镜头（平均每镜 {duration / shots:.1f}s）："
                f"短于 {MIN_SECONDS_PER_SHOT}s 基本是闪切，画面信息来不及读——并镜头或加时长")

    return notes


# ── 请求拼装 ─────────────────────────────────────────────────────────────
def build_content(prompt, first=None, last=None, images=(), videos=(), audios=()):
    """拼 content 数组：text 首位，其后首帧 / 尾帧 / 参考图 / 参考视频 / 参考音频。

    媒体参数吃 (url, encoded) 元组或裸 URL 字符串都行。
    """
    def _url(item):
        return item if isinstance(item, str) else item[0]

    content = [{"type": "text", "text": prompt}]
    if first:
        content.append({"type": "image_url", "image_url": {"url": _url(first)}, "role": "first_frame"})
    if last:
        content.append({"type": "image_url", "image_url": {"url": _url(last)}, "role": "last_frame"})
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": _url(img)}, "role": "reference_image"})
    for vid in videos:
        content.append({"type": "video_url", "video_url": {"url": _url(vid)}, "role": "reference_video"})
    for aud in audios:
        content.append({"type": "audio_url", "audio_url": {"url": _url(aud)}, "role": "reference_audio"})
    return content


def build_request(model, content, resolution, duration, ratio=None,
                  prompt_expand=None, aigc_watermark=False):
    body = {"model": model, "content": content, "resolution": resolution, "duration": duration}
    if ratio is not None:
        body["ratio"] = ratio
    if prompt_expand:
        body["extra"] = {"prompt_expansion_mode": prompt_expand}
    if aigc_watermark:
        body["aigc_watermark"] = True
    return body


# ── HTTP 与重试 ──────────────────────────────────────────────────────────
def body_json(text):
    """响应体 -> dict；非 JSON（网关 / CDN 错误页）返回 None。"""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def http_error_message(status, body_text):
    """HTTP 非 200 -> 可读原因；网关与官方都是 OaiError 形状（error.message）。"""
    data = body_json(body_text)
    err = data.get("error") if data else None
    message = err.get("message") if isinstance(err, dict) else None
    message = message or (body_text[:300] if body_text.strip() else "（空响应体）")
    if status == 401:
        return f"HTTP 401: {message}——检查 VIDEO_API_KEY 是否有效"
    if status == 402:
        return f"HTTP 402: {message}——账户余额不足"
    if status == 422:
        return f"HTTP 422: {message}——内容涉敏，改提示词 / 参考素材后重试，原样重试无效"
    if status == 429 or status >= 500:
        return f"HTTP {status}: {message}（服务端临时故障，可稍后重试）"
    return f"HTTP {status}: {message}"


def should_retry(status, body_text):
    """限流（429）与服务端故障（5xx）才重试；参数错 / 涉敏 / 令牌问题重试无效。"""
    return status == 429 or status >= 500


def retry_delay(attempt, headers=None):
    """第 attempt 次重试前等几秒（attempt 从 1 起）：Retry-After 优先，否则指数退避 + ±20% 抖动。"""
    retry_after = (headers or {}).get("Retry-After")
    if retry_after:
        try:
            return round(max(0.0, min(float(retry_after), RETRY_MAX_DELAY)), 2)
        except (TypeError, ValueError):
            pass
    delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
    # 抖动后再封一次顶，否则 60s × 1.2 会顶穿上限
    return round(min(delay * random.uniform(0.8, 1.2), RETRY_MAX_DELAY), 2)


def request_with_retry(url, headers, json_body, retries=RETRY_MAX_DEFAULT):
    """POST 建任务；限流 / 服务端故障 / 断流按退避重试，其余原样返回给调用方报错。"""
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.post(url, headers=headers, json=json_body, timeout=CREATE_TIMEOUT)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as exc:
            if attempt > retries:
                raise
            delay = retry_delay(attempt)
            print(f"提示：连接中断（{type(exc).__name__}），{delay}s 后重试（第 {attempt}/{retries} 次）",
                  file=sys.stderr)
            time.sleep(delay)
            continue
        if resp.status_code == 200 or attempt > retries or not should_retry(resp.status_code, resp.text):
            return resp
        delay = retry_delay(attempt, resp.headers)
        print(f"提示：HTTP {resp.status_code}，{delay}s 后重试（第 {attempt}/{retries} 次）", file=sys.stderr)
        time.sleep(delay)


# ── 轮询与下载 ───────────────────────────────────────────────────────────
class PollTimeout(Exception):
    """等任务超时 / 连续查询失败——任务不一定死，可拿 task_id 续查。"""

    def __init__(self, task_id, reason):
        self.task_id, self.reason = task_id, reason
        super().__init__(f"{reason}（task_id={task_id}）")


class TaskFailed(Exception):
    """任务到 failed / cancelled 终态；task 字段是服务端返回的任务对象。"""

    def __init__(self, task):
        self.task = task
        super().__init__(json.dumps(task, ensure_ascii=False)[:300])


def poll_task(base, headers, task_id, interval=DEFAULT_POLL_INTERVAL, wait=DEFAULT_WAIT_TIMEOUT,
              misses_allowed=POLL_MAX_MISSES):
    """轮询到 succeeded 返回 task dict；failed / cancelled 抛 TaskFailed，撑不下去抛 PollTimeout。

    状态变化即时回报，长跑每 60s 一次心跳；网络抖动 / 429 / 5xx 容忍连续 misses_allowed 次，
    401 / 403 这类硬错误立即退出。
    """
    start = time.time()
    deadline = start + wait
    last_status, last_beat, misses = None, start, 0
    while True:
        now = time.time()
        if now > deadline:
            raise PollTimeout(task_id, f"等待超过 {wait:.0f}s")
        try:
            resp = requests.get(f"{base}/v2/query/video_generation/{task_id}",
                                headers=headers, timeout=POLL_TIMEOUT)
            if resp.status_code == 200:
                task = (body_json(resp.text) or {}).get("task") or {}
                status = task.get("status") or "unknown"
                if status != last_status:
                    print(f"状态：{status}（已等 {now - start:.0f}s）", file=sys.stderr)
                    last_status, last_beat = status, now
                elif now - last_beat >= 60:
                    print(f"仍在 {status}（已等 {now - start:.0f}s）", file=sys.stderr)
                    last_beat = now
                if status == TERMINAL_OK:
                    return task
                if status in TERMINAL_BAD:
                    raise TaskFailed(task)
                misses = 0
            elif resp.status_code in (401, 403):
                fail(http_error_message(resp.status_code, resp.text))
            else:  # 429 / 5xx / 偶发网关错误——下一轮再查
                misses += 1
        except requests.RequestException:
            misses += 1
        if misses >= misses_allowed:
            raise PollTimeout(task_id, f"连续 {misses_allowed} 次查询失败")
        time.sleep(interval)


def download_video(url, out_path):
    """流式下载到 <out>.part 再原子改名——半截文件不会被当成品。返回字节数。

    下载地址由已配置的端点下发，只拦回环 / 链路本地这类绝不该访问的地址（放行内网 CDN）。
    """
    if problem := url_problem(url, "下载地址", allow_private=True):
        fail(problem)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    part = out_path.with_name(out_path.name + ".part")
    with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as resp:
        resp.raise_for_status()
        with open(part, "wb") as fh:
            for chunk in resp.iter_content(1024 * 1024):
                if chunk:
                    fh.write(chunk)
    os.replace(part, out_path)
    return out_path.stat().st_size


def usage_note(task):
    """task.usage -> 一行用量（计费按秒）；没有返回 None。"""
    usage = task.get("usage")
    if not isinstance(usage, dict):
        return None
    total = usage.get("total_seconds")
    if total is None:
        return None
    parts = [f"生成 {total}s"]
    if usage.get("input_seconds"):
        parts.append(f"输入 {usage['input_seconds']}s")
    if usage.get("input_image_count"):
        parts.append(f"参考图 {usage['input_image_count']} 张")
    return "用量：" + " / ".join(parts)


def out_path_arg(spec, project_dir=None):
    """--out 归一：产物固定 mp4 容器，没后缀补 .mp4、别的后缀换成 .mp4。

    给了 -p 时：相对 --out 拼到项目 assets 目录下，没给 --out 则默认名落该目录。
    返回 (path, 提示)。
    """
    if not spec:
        name = time.strftime("video_%Y%m%d_%H%M%S.mp4")
        return (project_dir / name if project_dir else pathlib.Path(name)), None
    path = pathlib.Path(spec)
    if project_dir and not path.is_absolute():
        path = project_dir / path
    if path.suffix.lower() == ".mp4":
        return path, None
    return path.with_suffix(".mp4"), "输出后缀改为 .mp4（MiniMax 产物是 mp4 容器）"


def read_prompt_file(spec):
    """读提示词文件（'-' 表示 stdin）；文件缺失 / 为空都给出人话错误。"""
    if spec == "-":
        text = sys.stdin.read()
    else:
        path = pathlib.Path(spec)
        if not path.is_file():
            fail(f"提示词文件不存在：{spec}")
        text = path.read_text(encoding="utf-8", errors="replace")
    text = text.strip()
    if not text:
        fail("提示词文件是空的")
    return text


def finalize(task, out_path, t0, model=""):
    """拿到 succeeded 的 task 后：下载、落盘、回显用量与地址。"""
    url = (task.get("content") or {}).get("url")
    if not url:
        fail(f"任务成功但响应里没有视频 URL: {json.dumps(task, ensure_ascii=False)[:400]}")
    nbytes = download_video(url, out_path)
    print(f"{out_path}  ({nbytes / 1024 / 1024:.1f} MB)")
    if line := usage_note(task):
        print(f"提示：{line}", file=sys.stderr)
    meta = " / ".join(str(task[k]) for k in ("resolution", "ratio", "duration") if task.get(k))
    if meta:
        print(f"提示：{meta}", file=sys.stderr)
    print(f"视频地址：{url}")
    tail = f"（{model}）" if model else ""
    print(f"完成，总用时 {time.time() - t0:.0f}s{tail}")


def main():
    # description 吃整篇 docstring：示例 / 模型差异 / ratio 规则 / 媒体限制都随 --help 可达
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("prompt", nargs="?", help="提示词（≤7000 字符）；长结构用 --prompt-file；--task-id 模式下不要给")
    ap.add_argument("--prompt-file", metavar="FILE", dest="prompt_file",
                    help="从文件读提示词（多行官方三段结构命令行传不动；- 表示 stdin）")
    ap.add_argument("--task-id", dest="task_id", help="只续查已建任务并下载（建任务后回显 task_id）")
    ap.add_argument("--first-frame", metavar="IMG|URL", help="首帧图（本地路径或 http(s) URL）")
    ap.add_argument("--last-frame", metavar="IMG|URL", help="尾帧图；可单独用，也可与 --first-frame 成对")
    ap.add_argument("--ref-image", action="append", metavar="IMG|URL",
                    help="参考图（可重复，≤9 张；角色派给提示词里的序号）")
    ap.add_argument("--ref-video", action="append", metavar="VID|URL",
                    help="参考视频（可重复，≤3 段，单段 2–15s）")
    ap.add_argument("--ref-audio", action="append", metavar="AUD|URL",
                    help="参考音频（可重复，≤3 段，单段 2–15s；定音色 / 口型）")
    ap.add_argument("--model", help="max（默认，极速）/ h3（支持 2K 与 4 秒）/ 完整模型名")
    ap.add_argument("--resolution", choices=RESOLUTION_CHOICES, default="768P",
                    help="分辨率（默认 768P；2K 仅 H3）")
    ap.add_argument("--duration", type=int, default=5, help="时长秒（默认 5；H3 4–15，Max 5–15）")
    ap.add_argument("--ratio", choices=RATIO_CHOICES,
                    help="宽高比；文生视频必填（默认 16:9，不能 adaptive），图生视频恒 adaptive")
    ap.add_argument("--prompt-expand", choices=("disabled", "balanced", "quality"), dest="prompt_expand",
                    help="提示词扩写档，仅 MiniMax-H3-Max（默认 balanced）")
    ap.add_argument("--aigc-watermark", action="store_true", dest="aigc_watermark",
                    help="生成视频里加 AIGC 标识水印（默认不加）")
    ap.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, metavar="SEC",
                    help=f"轮询间隔秒（默认 {DEFAULT_POLL_INTERVAL:g}，下限 1）")
    ap.add_argument("--timeout", type=float, default=DEFAULT_WAIT_TIMEOUT, metavar="SEC",
                    help=f"等任务总超时秒（默认 {DEFAULT_WAIT_TIMEOUT:g}；超时任务不一定死，可 --task-id 续查）")
    ap.add_argument("--retries", type=int, default=RETRY_MAX_DEFAULT, metavar="N",
                    help=f"建任务请求的限流 / 故障重试次数（默认 {RETRY_MAX_DEFAULT}）")
    ap.add_argument("--out", help="输出路径，默认 video_<时间戳>.mp4（产物固定 mp4 容器）")
    ap.add_argument("-p", "--project", metavar="项目",
                    help="归档到 projects/<项目>/deliverables/assets/（相对 --out 拼在该目录下）")
    args = ap.parse_args()

    if args.task_id and (args.prompt or args.prompt_file):
        ap.error("给了 --task-id 就只续查下载，不要再给提示词")
    if not args.task_id and not args.prompt and not args.prompt_file:
        ap.error("缺少提示词（或用 --prompt-file 从文件读；--task-id 续查已建任务）")
    if args.prompt and args.prompt_file:
        ap.error("提示词位置参数与 --prompt-file 只能给一个")
    prompt = None
    if not args.task_id:
        prompt = args.prompt or read_prompt_file(args.prompt_file)

    key, base = load_conf()
    headers = {"Authorization": f"Bearer {key}"}
    project_dir = None
    if args.project:
        try:
            project_dir = resolve_project_assets(ROOT, args.project)
        except ValueError as exc:
            fail(str(exc))
    out_path, out_note = out_path_arg(args.out, project_dir)
    if out_note:
        print(f"提示：{out_note}", file=sys.stderr)

    if args.task_id:
        t0 = time.time()
        try:
            task = poll_task(base, headers, args.task_id, max(args.poll_interval, 1.0), args.timeout)
        except PollTimeout as exc:
            fail(f"{exc.reason}——任务不一定失败，稍后续查："
                 f"python3 scripts/video_gen.py --task-id {exc.task_id} --out {out_path}")
        except TaskFailed as exc:
            fail(f"任务失败：{json.dumps(exc.task, ensure_ascii=False)[:500]}")
        finalize(task, out_path, t0)
        return

    model = MODEL_ALIASES.get(args.model, args.model) if args.model else "MiniMax-H3-Max"
    if model not in MODEL_SPECS:
        fail(f"不认识的模型 {model}（可用：{' / '.join(MODEL_SPECS)}）")

    mode = input_mode(args.first_frame, args.last_frame, args.ref_image, args.ref_video, args.ref_audio)
    ratio, ratio_notes, ratio_err = effective_ratio(mode, args.ratio)

    problems = []
    for err in (prompt_problem(prompt),
                mix_problem(args.first_frame, args.last_frame, args.ref_image, args.ref_video, args.ref_audio),
                resolution_problem(model, args.resolution),
                duration_problem(model, args.duration),
                ratio_err):
        if err:
            problems.append(err)
    if args.prompt_expand and model != "MiniMax-H3-Max":
        problems.append("--prompt-expand 是 MiniMax-H3-Max 专属选项")
    if len(args.ref_image or []) > MAX_REF_IMAGES:
        problems.append(f"参考图 {len(args.ref_image)} 张超过官方上限 {MAX_REF_IMAGES} 张")
    if len(args.ref_video or []) > MAX_REF_VIDEOS:
        problems.append(f"参考视频 {len(args.ref_video)} 段超过官方上限 {MAX_REF_VIDEOS} 段")
    if len(args.ref_audio or []) > MAX_REF_AUDIOS:
        problems.append(f"参考音频 {len(args.ref_audio)} 段超过官方上限 {MAX_REF_AUDIOS} 段")

    first = last = None
    if args.first_frame:
        items, ps = prepare_media([args.first_frame], "image")
        first = items[0] if items else None
        problems += ps
    if args.last_frame:
        items, ps = prepare_media([args.last_frame], "image")
        last = items[0] if items else None
        problems += ps
    images, ps = prepare_media(args.ref_image, "image")
    problems += ps
    videos, ps = prepare_media(args.ref_video, "video")
    problems += ps
    audios, ps = prepare_media(args.ref_audio, "audio")
    problems += ps

    encoded_total = sum(n for _, n in ([first] if first else []) + ([last] if last else [])
                        + images + videos + audios)
    if err := body_cap_problem(encoded_total):
        problems.append(err)
    if problems:
        fail("；".join(problems))

    for note in ratio_notes:
        print(f"提示：{note}", file=sys.stderr)
    for note in prompt_notes(prompt, mode, duration=args.duration):
        print(f"提示：{note}", file=sys.stderr)

    content = build_content(prompt, first, last, images, videos, audios)
    body = build_request(model, content, args.resolution, args.duration, ratio=ratio,
                         prompt_expand=args.prompt_expand, aigc_watermark=args.aigc_watermark)

    if model == "MiniMax-H3" and args.resolution == "2K":
        print("提示：2K 档生成常要几分钟，期间无输出属正常（Ctrl+C 后可 --task-id 续查）", file=sys.stderr)

    t0 = time.time()
    try:
        resp = request_with_retry(f"{base}/v2/video_generation", headers, body, retries=args.retries)
    except requests.RequestException as exc:
        fail(f"建任务请求失败（已重试 {args.retries} 次）：{type(exc).__name__} {exc}")

    if resp.status_code != 200:
        data = body_json(resp.text) or {}
        request_id = resp.headers.get("x-request-id") or data.get("request_id")
        tail = f"（request_id: {request_id}）" if request_id else ""
        fail(f"{http_error_message(resp.status_code, resp.text)}{tail}")
    task_id = (body_json(resp.text) or {}).get("task_id")
    if not task_id:
        fail(f"建任务响应里没有 task_id: {resp.text[:300]}")
    print(f"任务已创建 task_id={task_id}（中断后续查：python3 scripts/video_gen.py "
          f"--task-id {task_id} --out {out_path}）")

    try:
        task = poll_task(base, headers, task_id, max(args.poll_interval, 1.0), args.timeout)
    except PollTimeout as exc:
        fail(f"{exc.reason}——任务不一定失败，稍后续查："
             f"python3 scripts/video_gen.py --task-id {task_id} --out {out_path}")
    except TaskFailed as exc:
        fail(f"任务失败：{json.dumps(exc.task, ensure_ascii=False)[:500]}")
    except KeyboardInterrupt:
        print(f"\n已中断——任务还在跑，稍后续查：python3 scripts/video_gen.py "
              f"--task-id {task_id} --out {out_path}", file=sys.stderr)
        sys.exit(130)
    try:
        finalize(task, out_path, t0, model)
    except KeyboardInterrupt:
        print(f"\n下载中断——重跑续传：python3 scripts/video_gen.py "
              f"--task-id {task_id} --out {out_path}", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
