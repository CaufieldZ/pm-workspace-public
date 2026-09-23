#!/usr/bin/env python3
"""出图 / 改图（OpenAI Images API 兼容端点）—— 生成配图 / 封面 / 宣发图 / 示意图。

用法：
    python3 scripts/image_gen.py "一只戴圆框眼镜的柴犬，扁平插画风"
    python3 scripts/image_gen.py "一个咖啡杯图标" --simple
    python3 scripts/image_gen.py "改成夜景霓虹风" --edit <图>
    python3 scripts/image_gen.py "把这几个物件合成一个礼盒" --ref <图1> --ref <图2>
    python3 scripts/image_gen.py "logo 草稿" -n 3 --size 1024x1024 --quality high --out <路径>.png
    python3 scripts/image_gen.py "宣发配图" -p <项目>

端点：文生图 POST {BASE}/images/generations（JSON）；改图 / 参考图生图 POST {BASE}/images/edits（multipart）。
模型：默认 sunburst（质量优先基座）；--simple 或 --model flare 走 flare 小模型（速度优先，质量≈GPT Image 2）。
模型名是端点侧别名，可被 --model 直接写完整名覆盖。

坑：判断 AI 能不能画准海报文字别拿「文字处数」当门槛先验否决——$0.05 / 50 秒的成本下，
跑一次验证比先验判断便宜得多，真正决定成败的是提示词口气（人对着成品描述 vs 编号规格书）。

尺寸：推荐 1024x1024 / 1536x1024 / 1024x1536，也常用 2048x2048 / 2048x1152 / 3840x2160 / 2160x3840；
自定 <宽>x<高> 须宽高均为 16 的倍数、长短边比 1:3–3:1、单边 ≤3840、总像素 655,360–8,294,400。
超过 2560x1440（3,686,400 像素）属官方实验档，脚本给提示但不拦。
质量：low / medium / high / xhigh / max / auto（xhigh / max 是 2.5 档；草稿用 low，成品再往上试）。

落点：--out <路径> 指定；-p <项目> 落 projects/<项目>/deliverables/assets/；
都不给则落当前目录 image_<时间戳>.<ext>。两者同时给时相对 --out 拼在项目 assets/ 下。

提示词要点（官方 GPT Image 2.5 prompting guide）：
  - 本脚本落盘前跑一遍提示词体检，把可机械判定的问题打成「提示：」——**只提示，不改写提示词**。
    判不准的项不报（省得提示疲劳）；命中项自行决定改不改。
  - 生成：先说清用途 + 主体 + 构图 / 比例 + 风格 + 约束，再写可见细节（材质 / 光线 / 颜色 / 媒介）；
    复杂需求按「场景 / 主体 / 细节 / 约束」分段写。要照片感显式写 photorealistic；宽幅 / 夜景 / 霓虹
    这类场景写尺度与氛围，别只堆情绪词。人物写清景别、视线、与物体的交互（如「全身入镜，脚在画面里」）。
    单画面独立元素别超过 5 个（多了模型会自行删减）；复杂简报用英文写核心指令更稳（实测口径）。
  - 工艺水位：摄影 / 场景类必给光线（方向 + 质感），有人物必给景别 + 视角——这两项是成品图与通用
    AI 图的分界，体检对生成类提示词检查；平面版式 / 图标 / 信息图不查（本就无光线与景别可言）。
  - 图生图：提示词里按序号给每张参考图派角色（主体 / 风格 / 服装 / 背景），说明元素怎么组合、往哪搬、
    哪些必须不变（如「把图 2 的狗放进图 1 的场景，光照与构图沿用图 1」）。
  - 画面文字：要出现的原文用引号原样写进去 + 说明出现几次（exactly once）+ 位置与字体 + 加「no extra text」，
    出图后逐字核对；小字 / 密排文字用 medium 以上档。图里的数字与标签必须人工核对（模型会编数据）。
    文案越短越准，正文放图外，图内只留关键信息。
  - 改图：写「只改 X」+ 逐条列出要保留的（身份 / 几何 / 版面 / 光照 / 文字）+ 排除项（多余文字 / logo / 水印）。
    官方把 exclusions 列为正当写法，但工区实测显式否定不可靠（要求删批注没删、场景号残留）——
    关键区域别只靠提示词。
  - 局部改走 --mask（默认按蒙版回贴未改区域）；逐轮微调一次只改一件事，把上一轮输出当下一轮 --edit 输入，
    并复述要保留的约束。
  - 透明素材：prompt 里要求「isolate on a fully transparent background，no backdrop / no checkerboard」，
    并配 --background transparent；回图后确认真有 alpha 通道（画出来的棋盘格不算透明）。
  - 多张变体用 -n 一次请求出（官方给 logo 变体的推荐做法）：先 low 档多出几张挑，选中再 high 档重出。

服务端已知行为：
  - 响应固定返回 b64_json，本脚本自动解码落盘；response_format 会被拒（unknown_parameter），不要传
  - 多张走服务端 n（一次请求出 N 张变体，上限 10）；每张单独计费
  - 响应带 usage（输入 / 输出 token）与 x-request-id，脚本回显 token 用量与成本估算；
    排障拿 x-request-id 找服务商
  - 限流 429 与服务端 5xx 按指数退避自动重试（--retries 调，默认 2 次）；
    审核拦截与用户可修正错误不重试（重试无效）
  - 改图对输入图恒为高保真（官方：gpt-image-2 起不接受 input_fidelity，传了报 400）
  - 端点未开流式（stream / partial_images 会被 400 拒），脚本不暴露该参数
  - 改图可能换掉画布尺寸，脚本按 --size 缩放归一
  - 可能返回带透明通道的 PNG，默认合成白底（--keep-alpha 保留；--background transparent 自动保留）
  - 透明背景须配 png / webp 输出；output_compression 仅在 jpeg / webp 下有效
  - 后处理不需要改动时不重写文件——重存会让 jpeg / webp 二次有损编码
  - --mask 是提示性引导（官方：prompt-based，不保证贴合形状）；脚本默认按蒙版把未改区域回贴原图
  - 审核拦截返回 image_generation_user_error / moderation_blocked，脚本读出阶段与类别名，原样重试无效

上传边界：--edit / --ref 会把参考图**原图字节**发给所选端点（IMAGE_BASE_URL 或 IMAGE_BASE_URLS 路由结果）；文生图只发出提示词。
参考图含内部产品或未公开界面时先确认该端点可用——这是数据出域判断，不是脚本能兜的。

前置校验（真花钱之前拦下）：提示词 ≤32000 字符；参考图 ≤16 张、单张 <50MB；mask 与参考图同格式同尺寸且带 alpha；
-n 1–10、--size 合法、透明背景配 png / webp、压缩率仅 jpeg / webp。

前置：.env 里 IMAGE_API_KEY / IMAGE_BASE_URL（或同名环境变量）；可选 IMAGE_BASE_URLS（逗号分隔多端点，
启动时并发测速选最快者——大陆/出差跨网络与单端点故障兜底；候选全不通时用首个，请求阶段报真实错误）；
Python requests + Pillow。
--help 本身不需要以上任何一项。

退出码：0 成功；1 失败（缺凭证 / 参数非法 / HTTP 错 / 响应无图），原因写 stderr。
"""
from __future__ import annotations

# route-log: 调用埋点（scripts/lib/route_log.py）
import pathlib as _pl
import sys as _s

_r = next((p for p in _pl.Path(__file__).resolve().parents if (p / ".claude").is_dir()), None)
_r and (_s.path.insert(0, str(_r / "scripts")), __import__("lib.route_log", fromlist=["emit"]).emit("image_gen"))

import argparse
import base64
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from lib.env_refs import apply_env_file  # noqa: E402
from lib.projects import resolve_project_assets  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

MODEL_DEFAULT = "gpt-image-2.5-sunburst"   # 质量优先基座
MODEL_SIMPLE = "gpt-image-2.5-flare"        # 速度优先小模型（质量≈GPT Image 2）
MODEL_ALIASES = {"sunburst": MODEL_DEFAULT, "flare": MODEL_SIMPLE}

QUALITY_CHOICES = ("low", "medium", "high", "xhigh", "max", "auto")
BACKGROUND_CHOICES = ("transparent", "opaque", "auto")
MODERATION_CHOICES = ("low", "auto")

# 服务端尺寸约束（本脚本前置校验，坏参数在真花钱之前拦下）
MAX_EDGE = 3840
EDGE_MULTIPLE = 16
MAX_RATIO = 3.0
MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
EXPERIMENTAL_PIXELS = 2560 * 1440  # 官方：超过 2560x1440 属实验档

REQUEST_TIMEOUT = 300  # 官方标注复杂提示词最长可等 2 分钟
PROBE_TIMEOUT = 5.0    # 多端点路由的探测超时（秒）；候选不通时最坏多等这么久
REWRITE_QUALITY = 95   # 后处理非改不可时的 jpeg / webp 重编码档，别落到 Pillow 默认的 75

# 官方接口限值（本脚本前置拦下，坏请求在真花钱之前挡掉）
MAX_PROMPT_CHARS = 32_000          # prompt maxLength 32000
MAX_REF_IMAGES = 16                # GPT image 模型最多 16 张输入图
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 待编辑图与 mask 须 < 50MB
MAX_N = 10                         # n 上限 10

# 重试：只重试限流 / 服务端故障（官方：transient rate-limit and server failures with backoff）
RETRY_MAX_DEFAULT = 2
RETRY_BASE_DELAY = 1.0
RETRY_MAX_DELAY = 60.0

# 提示词体检阈值
PROMPT_SHORT_UNITS = 40     # 折算字数低于此值，写不下用途 / 构图 / 约束（改图不查，官方改图示例本身就很短）
PROMPT_EN_HINT_CHARS = 120  # 复杂简报（超过此长度）才提示英文核心指令更稳


# ── 纯函数（解析 / 校验 / 拼装，pytest 直测，无网络）────────────────────────
def parse_size(spec):
    """'1024x1024' -> (1024, 1024)；'auto' / None / 空 -> None；格式错抛 ValueError。"""
    if not spec or spec.strip().lower() == "auto":
        return None
    parts = spec.strip().lower().split("x")
    if len(parts) != 2 or not all(p.strip().isdigit() for p in parts):
        raise ValueError(f"尺寸格式应为 <宽>x<高> 或 auto，收到 {spec!r}")
    return int(parts[0]), int(parts[1])


def size_error(width, height):
    """校验尺寸是否落在服务端允许区间。合法返回 None，否则返回中文原因。"""
    if width <= 0 or height <= 0:
        return f"宽高须为正整数，收到 {width}x{height}"
    if max(width, height) > MAX_EDGE:
        return f"最长边 {max(width, height)} 超过 {MAX_EDGE}"
    if width % EDGE_MULTIPLE or height % EDGE_MULTIPLE:
        return f"宽高须均为 {EDGE_MULTIPLE} 的倍数，收到 {width}x{height}"
    ratio = max(width, height) / min(width, height)
    if ratio > MAX_RATIO:
        return f"长短边比 {ratio:.2f}:1 超过 {MAX_RATIO:g}:1"
    pixels = width * height
    if not MIN_PIXELS <= pixels <= MAX_PIXELS:
        return f"总像素 {pixels:,} 不在 {MIN_PIXELS:,}–{MAX_PIXELS:,} 区间"
    return None


def size_notes(width, height):
    """尺寸提示（不拦）：超过 2560x1440 属官方实验档。返回提示列表。"""
    if width * height > EXPERIMENTAL_PIXELS:
        return [f"{width}x{height} 超过 2560x1440，官方标注为实验档（效果与耗时可能不稳）"]
    return []


def select_model(model=None, simple=False):
    """解析模型名：显式 --model 优先，其次 --simple 的速度档，最后默认质量档；别名展开为完整名。"""
    name = model or (MODEL_SIMPLE if simple else MODEL_DEFAULT)
    return MODEL_ALIASES.get(name, name)


def background_error(background, output_format):
    """透明背景须配 png / webp（output_format 未指定时服务端默认 png）。合法返回 None。"""
    if background == "transparent" and output_format not in (None, "png", "webp"):
        return f"透明背景须配 png / webp 输出，当前 {output_format}——加 --output-format png 或 webp"
    return None


def compression_error(compression, output_format):
    """output_compression 仅 jpeg / webp 有效，取值 0–100。合法返回 None。"""
    if compression is None:
        return None
    if not 0 <= compression <= 100:
        return f"压缩率须在 0–100，收到 {compression}"
    if output_format not in ("jpeg", "webp"):
        current = output_format or "png（默认）"
        return f"压缩率仅 jpeg / webp 有效，当前输出 {current}——加 --output-format jpeg 或 webp"
    return None


def keep_alpha_effective(background, keep_alpha):
    """透明背景默认保留 alpha——否则后处理会把透明合成白底，白花钱。返回 (是否保留, 提示语)。"""
    if background == "transparent" and not keep_alpha:
        return True, "已按透明背景保留 alpha（无需再传 --keep-alpha）"
    return keep_alpha, None


def mask_problems(ref_size, mask_size, mask_mode, ref_format=None, mask_format=None):
    """mask 前置校验（官方要求：与参考图同格式、同尺寸、须带 alpha）。合法返回 []。"""
    problems = []
    if ref_format and mask_format and ref_format != mask_format:
        problems.append(f"mask 格式 {mask_format} 与参考图 {ref_format} 不一致（官方要求同格式）")
    if ref_size != mask_size:
        problems.append(f"mask 尺寸 {mask_size[0]}x{mask_size[1]} 与参考图 {ref_size[0]}x{ref_size[1]} 不一致")
    if "A" not in mask_mode:
        problems.append(f"mask 没有 alpha 通道（当前 {mask_mode}）——透明处才是要改的区域")
    return problems


def upload_mime(path):
    """按后缀给上传 mime——服务端按格式校验，别把 jpg / webp 一律写成 png。"""
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")


def body_json(text):
    """响应体 -> dict；非 JSON（网关 / CDN 错误页）返回 None。"""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def http_error_message(status, body_text):
    """HTTP 非 200 -> 中文原因：优先读 error.code / message / moderation_details。"""
    data = body_json(body_text)
    err = data.get("error") if data else None
    if not isinstance(err, dict):
        tail = "（服务端临时故障，可稍后重试）" if status == 429 or status >= 500 else ""
        return f"HTTP {status}{tail}: {body_text[:300]}"
    code = err.get("code") or ""
    message = err.get("message") or json.dumps(err, ensure_ascii=False)[:300]
    if code == "moderation_blocked":
        details = err.get("moderation_details") or {}
        stage = {"input": "输入侧（提示词 / 参考图）", "output": "输出侧（生成的图）"}.get(
            details.get("moderation_stage"), "来源不明")
        categories = "、".join(details.get("categories") or []) or "未给出"
        return (f"HTTP {status}: 内容审核拦截（{stage}；类别：{categories}）"
                "——改提示词或参考图后重试，原样重试无效")
    if err.get("type") == "image_generation_user_error":
        return f"HTTP {status}: {message}（用户可修正错误，改提示词 / 参考图后重试）"
    if status == 429 or status >= 500:
        return f"HTTP {status}: {message}（服务端临时故障，可稍后重试）"
    return f"HTTP {status}: {message}" + (f"（{code}）" if code else "")


def build_payload(model, prompt, size=None, quality=None, output_format=None,
                  compression=None, background=None, moderation=None, count=None):
    """拼请求体：None 一律丢弃（服务端不认空值）。count>1 时下发 n（一次请求出多张）。"""
    payload = {"model": model, "prompt": prompt}
    for key, value in (
        ("size", size),
        ("quality", quality),
        ("output_format", output_format),
        ("output_compression", compression),
        ("background", background),
        ("moderation", moderation),
        ("n", count),
    ):
        if value is not None:
            payload[key] = value
    return payload


def out_paths(base_path, total):
    """n>1 时输出 name-1.ext / name-2.ext …；n=1 即原路径。"""
    if total == 1:
        return [base_path]
    return [base_path.with_name(f"{base_path.stem}-{i}{base_path.suffix}") for i in range(1, total + 1)]


def build_out_path(out, project_dir, ext, stamp):
    """定基础输出路径（n>1 时再由 out_paths 派生子名）。

    out 给了：绝对路径原样用；相对路径在 project_dir 给了时拼到其下；无后缀补 .ext。
    out 没给：project_dir 给了落该目录，否则落 cwd，文件名统一 image_<stamp>.<ext>。
    """
    if out:
        path = Path(out)
        if project_dir and not path.is_absolute():
            path = project_dir / path
        return path if path.suffix else path.with_suffix("." + ext)
    name = f"image_{stamp}.{ext}"
    return (project_dir / name) if project_dir else Path(name)


def decode_b64(item):
    """响应条目 -> 图片字节；无 b64_json 返回 None。"""
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    return None


# ── 提示词体检（官方 prompting guide 里能机械判定的那几条；只提示，不改写提示词）──
# 规则来源：developers.openai.com/api/docs/guides/image-prompting（GPT Image 2.5 prompting guide）
# 的 8 条技法；带「工区实测」的条目来自 .claude/decisions/implemented/2026-09-10-image-gen-route.md。
_PHOTO_INTENT = re.compile(r"写实|真实感|照片|摄影|实拍|photoreal|photograph|realistic|hyperreal", re.I)
_PHOTO_DECLARED = re.compile(r"photorealistic|real photograph|photographic|真实照片|实拍照片|照片级真实", re.I)
_QUOTED = re.compile(r"[\"“”'‘’「」『』]")
_TEXT_ONCE = re.compile(r"exactly once|only once|(?<!at )\bonce\b|出现一次|只出现一次|仅出现一次|一次且仅|只出现.{0,4}次",
                        re.I)
_TEXT_GUARD = re.compile(
    r"no extra text|no additional text|no other text|no watermark|无多余文字|不要多余文字|不加多余文字|无额外文字|无水印", re.I)
_KEEP = re.compile(r"保留|保持不变|维持不变|维持原样|不变|preserve|keep|unchanged|maintain|retain", re.I)
_NEGATION = re.compile(r"不要|别出现|去掉|移除|抹掉|剔除|删掉|不留|不出现|禁止"
                       r"|\bremove\b|\bwithout\b|\bdelete\b|\berase\b|\bdon't\b", re.I)
# 只收「密集 / 小字」信号：单行标语、标题这类大字 low 档也渲染得动，不该报
_DENSE_TEXT = re.compile(
    r"小字|密排|多行|表格|图例|脚注|图注|标注|字号"
    r"|\blabel|\blegend|\bfootnote|\bcaption|\btypography|\bfont\b|\bfonts\b", re.I)
_TRANSPARENT = re.compile(r"透明|transparent", re.I)
# 工艺维度：光线与景别是成品图与通用 AI 图的分界，但只在判得准的场景报——
# 平面版式 / 图标 / 信息图本就没有光线与景别可言，所以两条都由 _PHOTO_INTENT 与 _PERSON 门控
_LIGHTING = re.compile(
    r"光线|光照|打光|逆光|顺光|侧光|顶光|柔光|硬光|晨光|暮色|夕照|霓虹|反光|曝光|阴影|投影|光斑|光晕"
    r"|\blight(?:ing|s)?\b|\blit\b|\bbacklit\b|\bdaylight\b|\bsunlight\b|\bmoonlight\b|\bneon\b"
    r"|\bglow(?:ing)?\b|\bshadows?\b|\bgolden hour\b|\bdusk\b|\bdawn\b|\bovercast\b|\bsilhouette\b",
    re.I)
_PERSON = re.compile(
    r"人物|人像|男[孩人性子]|女[孩人性子]|小孩|儿童|老人|模特|主播|肖像|面孔"
    r"|\bperson\b|\bpeople\b|\bman\b|\bwoman\b|\bgirl\b|\bboy\b|\bmodel\b|\bportrait\b"
    r"|\bbarista\b|\bfigure\b|\bcharacter\b", re.I)
_SHOT_SIZE = re.compile(
    r"特写|近景|中景|远景|全景|全身|半身|景别|俯拍|仰拍|平视|正面|侧面|背影"
    r"|\bclose-?up\b|\bmedium shot\b|\bwide shot\b|\bfull[- ]body\b|\bhalf[- ]body\b|\bportrait\b"
    r"|\beye level\b|\blow angle\b|\bhigh angle\b|\bover[- ]the[- ]shoulder\b|\bheadshot\b",
    re.I)
_CJK = re.compile(r"[一-鿿]")
_HIGH_QUALITY = ("medium", "high", "xhigh", "max")


def cjk_ratio(text):
    """中日韩汉字占全文比例——判断提示词是不是中文主导。"""
    if not text:
        return 0.0
    return len(_CJK.findall(text)) / len(text)


def effective_length(text):
    """信息量折算字数：汉字按 2 计——同样字数中文承载的信息比英文多，拿字符数直接比会误判。"""
    if not text:
        return 0
    cjk = len(_CJK.findall(text))
    return cjk * 2 + (len(text) - cjk)


def prompt_notes(prompt, editing=False, ref_count=1, background=None, quality=None):
    """提示词体检：返回中文提示列表（可能为空）。只提示，不改写提示词。

    体检项全部对应官方 prompting guide 的技法，或工区已实测的失败模式；
    判不准的一律不报，避免提示疲劳。
    """
    notes = []
    text = prompt.strip()

    # 官方认可短提示词（「Short prompts… can all express the same intent」），改图示例如「Make it look like
    # a winter evening with snowfall.」本身就短——这条只对生成、且只对信息量确实不够的提示词报
    units = effective_length(text)
    if not editing and units < PROMPT_SHORT_UNITS:
        notes.append(
            f"提示词信息量偏少（折算 {units:.0f} 字）：官方第一条技法是先点明主体与用途"
            "（产品图 / 广告 / 示意图？），再补构图 / 比例 / 风格 / 约束")

    if _PHOTO_INTENT.search(text) and not _PHOTO_DECLARED.search(text):
        notes.append(
            "要照片感但没显式写 photorealistic / real photograph——官方要求这类目标显式声明，"
            "只写「写实 / 真实感」不够")

    # 工艺项只对生成报：改图的光线与取景由输入图决定，要求补写是噪音
    if not editing and (_PHOTO_INTENT.search(text) or _PHOTO_DECLARED.search(text)) \
            and not _LIGHTING.search(text):
        notes.append(
            "摄影 / 场景类画面没写光线：官方公式要求主体与构图之后补可见细节（材质 / 光线 / 颜色 / 媒介）。"
            "光线是成品图与通用 AI 图的分界——写清方向与质感（soft window daylight / 逆光轮廓光 / 阴天散射）")

    if not editing and _PERSON.search(text) and not _SHOT_SIZE.search(text):
        notes.append(
            "画面里有人物但没给景别与视角：官方要求人物写清景别、视线、与物体的交互"
            "（如 medium close-up at eye level、「全身入镜，脚在画面里」）——不给模型会自行取景")

    if _QUOTED.search(text) and not (_TEXT_ONCE.search(text) and _TEXT_GUARD.search(text)):
        notes.append(
            "画面文字：原文用引号写出后，还要说明出现几次（如 exactly once / 只出现一次）"
            "并加 no extra text，否则可能多印或漏印；出图后逐字核对")

    if background == "transparent" and not _TRANSPARENT.search(text):
        notes.append(
            "已设 --background transparent，但提示词没写透明背景——官方要求两处都给："
            "提示词写 isolate on a fully transparent background, no backdrop / no checkerboard")

    if ref_count >= 2:
        notes.append(
            f"{ref_count} 张参考图：提示词里按序号给每张派角色（主体 / 风格 / 服装 / 背景），"
            "说明元素怎么组合、哪张优先——官方技法「assign roles to references」")

    if editing and not _KEEP.search(text):
        notes.append(
            "改图但没写要保留什么：官方要求「只改 X」+ 逐条列出保留项"
            "（身份 / 几何 / 版面 / 光照 / 文字 / 排除项）")

    # 只对改图报：生成时「no extra text / avoid clip art」这类排除项是官方推荐的正当写法；
    # 工区实测翻车的是改图里「把 X 去掉」——要删的东西就在输入图上，模型没删
    if editing and _NEGATION.search(text):
        notes.append(
            "改图里含「去掉 / remove」类删除约束：工区实测显式否定不可靠"
            "（要求删批注没删、内部场景号残留）。要删干净的区域走 --mask 局部改 + 自动回贴，别只靠提示词")

    if _DENSE_TEXT.search(text) and quality not in _HIGH_QUALITY:
        notes.append(
            f"画面含文字 / 标注 / 图例：官方建议小字、密排信息用 medium 以上质量档"
            f"（当前 {quality or 'auto'}）")

    if len(text) >= PROMPT_EN_HINT_CHARS and cjk_ratio(text) > 0.3:
        notes.append(
            "复杂简报用中文写：多份实测显示英文核心指令更稳（官方 guide 全英文示例）。"
            "要图里出现中文时，把中文原文用引号原样写进提示词即可")

    return notes


# ── 请求前校验（官方限值；坏参数在真花钱之前拦下）────────────────────────
def prompt_length_error(prompt):
    """官方 prompt 限长 32000 字符。合法返回 None。"""
    if len(prompt) > MAX_PROMPT_CHARS:
        return f"提示词 {len(prompt)} 字符超过官方上限 {MAX_PROMPT_CHARS}"
    return None


def ref_count_error(count):
    """官方：GPT image 模型最多 16 张输入图。合法返回 None。"""
    if count > MAX_REF_IMAGES:
        return f"参考图 {count} 张超过官方上限 {MAX_REF_IMAGES} 张"
    return None


def upload_size_error(path, size_bytes):
    """官方：待编辑图与 mask 须 < 50MB。合法返回 None。"""
    if size_bytes >= MAX_UPLOAD_BYTES:
        return f"{Path(path).name} {size_bytes / 1024 / 1024:.1f}MB 达到或超过官方上限 50MB"
    return None


def n_error(n):
    """官方 n 取值 1–10。合法返回 None。"""
    if n < 1:
        return f"-n 至少为 1，收到 {n}"
    if n > MAX_N:
        return f"-n {n} 超过官方上限 {MAX_N}"
    return None


# ── 重试判定（官方：transient rate-limit / server failures 退避重试）──────
def should_retry(status, body_text):
    """限流（429）与服务端故障（5xx）才重试；审核拦截 / 用户可修正错误重试无效。"""
    if not (status == 429 or status >= 500):
        return False
    data = body_json(body_text)
    err = data.get("error") if data else None
    if isinstance(err, dict) and (err.get("code") == "moderation_blocked"
                                  or err.get("type") == "image_generation_user_error"):
        return False
    return True


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


def usage_note(data):
    """响应 usage -> 一行 token 用量与成本估算；没有 usage 返回 None。"""
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    out_tokens, in_tokens = usage.get("output_tokens"), usage.get("input_tokens")
    if out_tokens is None and in_tokens is None:
        return None
    parts = []
    if in_tokens is not None:
        parts.append(f"输入 {in_tokens} token")
    if out_tokens is not None:
        parts.append(f"输出 {out_tokens} token")
    line = "用量：" + " / ".join(parts)
    if out_tokens is not None:
        line += f"（按官方 $30/1M 输出 token 估 ≈ ${out_tokens * 30 / 1_000_000:.4f}）"
    return line


# ── I/O ───────────────────────────────────────────────────────────────────
def parse_base_candidates(spec):
    """'url1, url2,,url1' -> 去重保序、去尾斜杠的候选端点列表；空 / None -> []。"""
    seen = []
    for part in (spec or "").split(","):
        url = part.strip().rstrip("/")
        if url and url not in seen:
            seen.append(url)
    return seen


def probe_base(base, timeout=PROBE_TIMEOUT):
    """GET {base}/images/generations 测握手；有响应（任意状态码）算通，返回毫秒；失败返回 None。"""
    t0 = time.time()
    try:
        requests.get(f"{base}/images/generations", timeout=timeout)
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
    """读 IMAGE_API_KEY / IMAGE_BASE_URL(S)（环境变量优先，其次仓库根 .env）；缺则退出。

    IMAGE_BASE_URLS 为可选的多端点清单（逗号分隔）：设了就探测选最快者；未设用单一 IMAGE_BASE_URL。
    """
    apply_env_file(ROOT / ".env")
    key = os.environ.get("IMAGE_API_KEY")
    candidates = parse_base_candidates(os.environ.get("IMAGE_BASE_URLS"))
    if not candidates:
        base = (os.environ.get("IMAGE_BASE_URL") or "").rstrip("/")
        candidates = [base] if base else []
    missing = []
    if not key:
        missing.append("IMAGE_API_KEY")
    if not candidates:
        missing.append("IMAGE_BASE_URL（或 IMAGE_BASE_URLS）")
    if missing:
        sys.exit(f"错误：{' / '.join(missing)} 未设置（放仓库根 .env，或导出同名环境变量）")
    return key, route_base(candidates)


def request_with_retry(url, headers, json_body=None, files_factory=None, retries=RETRY_MAX_DEFAULT):
    """POST images 端点；限流 / 服务端故障按退避重试，其余原样返回给调用方报错。

    files_factory 每轮重开文件句柄——上一轮的已经被关掉了，复用会读空。
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            if files_factory is not None:
                files, handles = files_factory()
                try:
                    resp = requests.post(url, headers=headers, data=json_body,
                                         files=files, timeout=REQUEST_TIMEOUT)
                finally:
                    for handle in handles:
                        handle.close()
            else:
                resp = requests.post(url, headers=headers, json=json_body, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            if attempt > retries:
                raise
            delay = retry_delay(attempt)
            print(f"提示：请求失败（{type(exc).__name__}），{delay}s 后重试（第 {attempt}/{retries} 次）",
                  file=sys.stderr)
            time.sleep(delay)
            continue
        if resp.status_code == 200 or attempt > retries or not should_retry(resp.status_code, resp.text):
            return resp
        delay = retry_delay(attempt, resp.headers)
        print(f"提示：HTTP {resp.status_code}，{delay}s 后重试（第 {attempt}/{retries} 次）", file=sys.stderr)
        time.sleep(delay)


def save_image(item, out_path):
    """按响应条目落盘。返回字节数。"""
    raw = decode_b64(item)
    if raw is None:
        raise ValueError(f"响应里没有 b64_json：{json.dumps(item, ensure_ascii=False)[:300]}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return len(raw)


def postprocess(out_path, want_size=None, keep_alpha=False):
    """规范化输出：透明像素合成白底、尺寸归一（edits 会把画布改成别的大小）。返回提示列表。

    不需要改动时**不重写文件**——重存会让 jpeg / webp 二次有损编码（服务端已按
    output_compression 编好，Pillow 默认档再存一遍等于白掉一档画质）。
    """
    from PIL import Image

    im = Image.open(out_path)
    notes = []
    touched = False
    if im.mode == "P":
        im = im.convert("RGBA")
        touched = True
    if im.mode in ("RGBA", "LA"):
        alpha = im.convert("RGBA").getchannel("A")
        data = alpha.get_flattened_data() if hasattr(alpha, "get_flattened_data") else alpha.getdata()
        if keep_alpha:
            pass
        elif min(data) < 255:
            rgba = im.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.getchannel("A"))
            im = bg
            touched = True
            notes.append("含透明像素，已合成白底（要保留加 --keep-alpha）")
        else:
            im = im.convert("RGB")
            touched = True
    elif im.mode != "RGB":
        im = im.convert("RGB")
        touched = True
    if im.mode == "RGBA" and out_path.suffix.lower() in (".jpg", ".jpeg"):
        im = im.convert("RGB")
        touched = True
    if want_size and im.size != want_size:
        notes.append(f"模型改了画布 {im.size[0]}x{im.size[1]} → {want_size[0]}x{want_size[1]}")
        im = im.resize(want_size, Image.LANCZOS)
        touched = True
    if touched:
        # 非改不可时才重编码：jpeg / webp 用高保真档，别落到 Pillow 默认的 75
        lossy = out_path.suffix.lower() in (".jpg", ".jpeg", ".webp")
        im.save(out_path, **({"quality": REWRITE_QUALITY} if lossy else {}))
    return notes


def upload_problems(paths):
    """--edit / --mask 上传前校验：文件存在且 < 50MB。合法返回 []。"""
    problems = []
    for p in paths:
        path = Path(p)
        if not path.is_file():
            problems.append(f"参考图不存在：{p}")
            continue
        err = upload_size_error(path, path.stat().st_size)
        if err:
            problems.append(err)
    return problems


def mask_problem_text(image_path, mask_path):
    """读图做 mask 前置校验。合法返回 None，否则返回中文原因。"""
    from PIL import Image

    try:
        with Image.open(image_path) as ref, Image.open(mask_path) as mask:
            problems = mask_problems(ref.size, mask.size, mask.mode, ref.format, mask.format)
    except (OSError, ValueError) as exc:  # 读不了图 / 不是图片（UnidentifiedImageError 属 OSError）
        return f"读图失败（{Path(mask_path).name}）：{exc}"
    return "；".join(problems) if problems else None


def composite_masked(result_path, image_path, mask_path, want_size=None):
    """按 mask alpha 把原图回贴进生成图：**透明处（α=0）是编辑区**，用生成图；
    不透明处（α=255）要逐像素保留，回贴原图。

    官方对「某区域必须逐像素不变」给的做法就是合成回原图，别只靠提示词。返回提示列表。
    """
    from PIL import Image

    gen = Image.open(result_path).convert("RGBA")
    ref = Image.open(image_path).convert("RGBA")
    mask = Image.open(mask_path).convert("RGBA").getchannel("A")
    target = want_size or ref.size
    if gen.size != target:
        gen = gen.resize(target, Image.LANCZOS)
    if ref.size != target:
        ref = ref.resize(target, Image.LANCZOS)
    if mask.size != target:
        mask = mask.resize(target, Image.LANCZOS)
    composed = Image.composite(ref, gen, mask)  # mask 不透明 -> 原图；透明 -> 生成图
    if result_path.suffix.lower() in (".jpg", ".jpeg"):
        composed = composed.convert("RGB")
    composed.save(result_path)
    return ["已按蒙版把未改区域回贴原图（α=0 处与原件逐像素一致；要关加 --no-mask-composite）"]


# ── CLI ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("prompt", help="提示词；改图时写清楚保留什么、改什么")
    ap.add_argument("--edit", "--ref", action="append", metavar="IMG",
                    help="参考图路径（走 /images/edits），可重复、最多 16 张：既用于改图，"
                         "也用于「拿几张参考图生成新画面」；多图要在提示词里按序号讲明每张图的角色")
    ap.add_argument("--mask", metavar="PNG",
                    help="局部修改的 PNG 蒙版（透明处为重点修改区），须与第一张参考图同尺寸且带 alpha；"
                         "默认按蒙版把未改区域回贴原图")
    ap.add_argument("--no-mask-composite", action="store_true", dest="no_mask_composite",
                    help="关掉蒙版回贴（默认把未改区域按原图逐像素贴回）")
    ap.add_argument("--model", help="sunburst（质量优先，默认）/ flare（速度优先）/ 完整模型名")
    ap.add_argument("--simple", action="store_true",
                    help="走 flare 小模型：速度优先、质量≈GPT Image 2（图标 / 单主体 / 快稿）")
    ap.add_argument("--size", help="auto 或 <宽>x<高>，推荐 1024x1024 / 1536x1024 / 1024x1536（默认服务端自选）")
    ap.add_argument("--quality", choices=QUALITY_CHOICES,
                    help="质量档（默认服务端自选；草稿用 low，成品再往上试，xhigh / max 仅 2.5 模型）")
    ap.add_argument("--output-format", choices=["png", "jpeg", "webp"], dest="output_format",
                    help="输出格式（默认 png；jpeg 更快）")
    ap.add_argument("--compression", type=int, metavar="0-100", help="有损压缩率，仅 jpeg / webp 有效")
    ap.add_argument("--moderation", choices=MODERATION_CHOICES, help="内容审核档（默认服务端 auto）")
    ap.add_argument("--background", choices=BACKGROUND_CHOICES,
                    help="背景（默认服务端 auto；transparent 须配 png / webp）")
    ap.add_argument("--keep-alpha", action="store_true", dest="keep_alpha",
                    help="保留透明通道（默认含透明像素时合成白底；--background transparent 自动保留）")
    ap.add_argument("-n", type=int, default=1,
                    help=f"张数 1–{MAX_N}，一次请求出 N 张变体（默认 1）")
    ap.add_argument("--retries", type=int, default=RETRY_MAX_DEFAULT, metavar="N",
                    help=f"限流 / 服务端故障的重试次数（默认 {RETRY_MAX_DEFAULT}；审核拦截不重试）")
    ap.add_argument("--out", help="输出路径；不给则落当前目录 image_<时间戳>.<ext>")
    ap.add_argument("-p", "--project", metavar="项目",
                    help="归档到 projects/<项目>/deliverables/assets/（相对 --out 拼在该目录下）")
    args = ap.parse_args()

    try:
        want_size = parse_size(args.size)
        project_assets = resolve_project_assets(ROOT, args.project) if args.project else None
    except ValueError as exc:
        sys.exit(f"错误：{exc}")

    problems = []
    if args.mask and not args.edit:
        problems.append("--mask 只在改图 / 参考图生图（--edit / --ref）下有效")
    if want_size:
        err = size_error(*want_size)
        if err:
            problems.append(f"--size {args.size} 不合法：{err}")
    for err in (background_error(args.background, args.output_format),
                compression_error(args.compression, args.output_format),
                prompt_length_error(args.prompt),
                n_error(args.n),
                ref_count_error(len(args.edit or []))):
        if err:
            problems.append(err)
    if args.edit:
        problems += upload_problems(args.edit)
    if problems:
        sys.exit("错误：" + "；".join(problems))

    for note in (size_notes(*want_size) if want_size else []):
        print(f"提示：{note}", file=sys.stderr)

    if args.mask:
        mask_err = mask_problem_text(args.edit[0], args.mask)
        if mask_err:
            sys.exit(f"错误：{mask_err}")

    keep_alpha, alpha_note = keep_alpha_effective(args.background, args.keep_alpha)
    if alpha_note:
        print(f"提示：{alpha_note}", file=sys.stderr)

    # 提示词体检——只提示，不改写提示词
    for note in prompt_notes(args.prompt, editing=bool(args.edit), ref_count=len(args.edit or []),
                             background=args.background, quality=args.quality):
        print(f"提示：{note}", file=sys.stderr)

    key, base = load_conf()
    ext = "jpg" if args.output_format == "jpeg" else (args.output_format or "png")
    base_path = build_out_path(args.out, project_assets, ext, time.strftime("%Y%m%d_%H%M%S"))

    model = select_model(args.model, args.simple)
    payload = build_payload(
        model, args.prompt,
        size=args.size, quality=args.quality, output_format=args.output_format,
        compression=args.compression, background=args.background,
        moderation=args.moderation,
        count=args.n if args.n > 1 else None,
    )

    headers = {"Authorization": f"Bearer {key}", "Accept": "*/*"}
    n = args.n
    print("提示：单张出图官方标注最长可等 2 分钟（复杂提示词更久），期间无输出属正常", file=sys.stderr)
    targets = out_paths(base_path, n)
    endpoint = "edits" if args.edit else "generations"
    url = f"{base}/images/{endpoint}"
    t0 = time.time()

    if args.edit:
        field = "image" if len(args.edit) == 1 else "image[]"

        def files_factory():
            """每轮重开文件句柄——重试时上一轮的已经关了，复用会读空。"""
            files, handles = [], []
            try:
                for p in list(args.edit) + ([args.mask] if args.mask else []):
                    handle = open(p, "rb")
                    handles.append(handle)
                    name = "mask" if p == args.mask else field
                    files.append((name, (Path(p).name, handle, upload_mime(Path(p)))))
            except OSError:
                for handle in handles:
                    handle.close()
                raise
            return files, handles

        try:
            resp = request_with_retry(url, headers, json_body=payload,
                                      files_factory=files_factory, retries=args.retries)
        except requests.RequestException as exc:  # 先于 OSError：RequestException 是 OSError 子类
            sys.exit(f"错误：请求失败（{type(exc).__name__}）{exc}")
        except OSError as exc:
            sys.exit(f"错误：读参考图失败 {exc}")
    else:
        try:
            resp = request_with_retry(url, headers, json_body=payload, retries=args.retries)
        except requests.RequestException as exc:
            sys.exit(f"错误：请求失败（{type(exc).__name__}）{exc}")

    if resp.status_code != 200:
        request_id = resp.headers.get("x-request-id")
        tail = f"（x-request-id: {request_id}）" if request_id else ""
        sys.exit(f"错误：{http_error_message(resp.status_code, resp.text)}{tail}")
    data = body_json(resp.text)
    if data is None:
        sys.exit(f"错误：响应不是 JSON（HTTP {resp.status_code}）：{resp.text[:200]}")
    items = data.get("data") or []
    if not items:
        sys.exit(f"错误：响应里没有图片数据: {json.dumps(data, ensure_ascii=False)[:300]}")

    for i, (target, item) in enumerate(zip(targets, items, strict=False), 1):
        prefix = f"[{i}/{n}] " if n > 1 else ""
        try:
            nbytes = save_image(item, target)
        except ValueError as exc:
            sys.exit(f"{prefix}错误：{exc}")
        notes = postprocess(target, want_size, keep_alpha)
        if args.mask and not args.no_mask_composite:
            notes += composite_masked(target, Path(args.edit[0]), Path(args.mask), want_size)
        print(f"{prefix}{target}  ({nbytes / 1024:.0f} KB)")
        for note in notes:
            print(f"{prefix}  · {note}")

    if len(items) != n:
        print(f"提示：请求 {n} 张，服务端返回 {len(items)} 张", file=sys.stderr)
    if usage_line := usage_note(data):
        print(f"提示：{usage_line}", file=sys.stderr)
    print(f"完成，用时 {time.time() - t0:.1f}s（{endpoint} / {model}）")


if __name__ == "__main__":
    main()
