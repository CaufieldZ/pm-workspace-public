"""video_gen.py 纯函数回归。

不碰网络：只测校验 / 拼装 / base 归一化与限值判定（媒体 URL 的公网校验按字面量 IP
断言，域名场景 monkeypatch 掉 `_resolve_host_ips`，不真解析）。
重点守四件容易静默回潮的事——① base 里的 /v1 必须被剥掉（video 走 /v2，
从 IMAGE_BASE_URL 抄来的 /v1 会打到不存在的地址）；② ratio 三种模式的
必填 / 忽略 / 可选规则别混；③ -p 归档路径的拼接规则；④ 媒体 URL 的 SSRF 兜底
（非 http(s) / 带凭证 / 内网 / 回环 / 云元数据地址不许透传给端点）。
"""

import ipaddress
import json
import pathlib

import pytest

import video_gen as vg

# ── base 归一化（/v1 必须剥掉）────────────────────────────────────────────


def test_normalize_base_strips_v1():
    assert vg.normalize_base("https://api.example/v1") == "https://api.example"
    assert vg.normalize_base("https://api.example/v1/") == "https://api.example"


def test_normalize_base_keeps_domain_and_custom_path():
    assert vg.normalize_base("https://api.example") == "https://api.example"
    assert vg.normalize_base("https://a.example/api") == "https://a.example/api"  # 自定义路径别动
    assert vg.normalize_base("  https://a.example  ") == "https://a.example"
    assert vg.normalize_base("") == ""


def test_parse_base_candidates_dedupes_after_normalize():
    """域名形态和 /v1 形态是同一个端点——归一化后再去重，免得对同一台机器探测两次。"""
    assert vg.parse_base_candidates("https://a.example, https://a.example/v1 ,,https://b.example/v1/") \
        == ["https://a.example", "https://b.example"]


def test_parse_base_candidates_empty():
    assert vg.parse_base_candidates("") == []
    assert vg.parse_base_candidates(None) == []
    assert vg.parse_base_candidates(" , , ") == []


# ── 端点路由（VIDEO_BASE_URLS 多候选择快）────────────────────────────────
# 探测本身走网络不单测；这里守的是「选谁」与「什么时候不探测」。


def test_pick_fastest_prefers_min_ok():
    assert vg.pick_fastest([("a", 900.0), ("b", 480.0), ("c", None)]) == "b"


def test_pick_fastest_all_fail_falls_back_first():
    assert vg.pick_fastest([("a", None), ("b", None)]) == "a"


def test_pick_fastest_empty():
    assert vg.pick_fastest([]) is None


def test_route_base_single_candidate_skips_probe(monkeypatch):
    """单端点不探测——否则每次出片都白等一个 RTT。"""
    def boom(*args, **kwargs):
        raise AssertionError("单候选不该探测")

    monkeypatch.setattr(vg, "probe_base", boom)
    assert vg.route_base(["https://only.example"]) == "https://only.example"


def test_route_base_picks_fastest(monkeypatch):
    monkeypatch.setattr(vg, "probe_base",
                        lambda base, timeout=None: {"https://slow.example": 900.0,
                                                    "https://fast.example": 12.0}[base])
    assert vg.route_base(["https://slow.example", "https://fast.example"]) == "https://fast.example"


def test_route_base_all_probes_fail_uses_first(monkeypatch):
    monkeypatch.setattr(vg, "probe_base", lambda base, timeout=None: None)
    assert vg.route_base(["https://a.example", "https://b.example"]) == "https://a.example"


# ── 模型档位校验 ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("model,resolution,ok", [
    ("MiniMax-H3", "768P", True),
    ("MiniMax-H3", "2K", True),
    ("MiniMax-H3", "480P", False),
    ("MiniMax-H3-Max", "480P", True),
    ("MiniMax-H3-Max", "768P", True),
    ("MiniMax-H3-Max", "2K", False),
])
def test_resolution_problem(model, resolution, ok):
    assert (vg.resolution_problem(model, resolution) is None) is ok


@pytest.mark.parametrize("model,duration,ok", [
    ("MiniMax-H3", 4, True), ("MiniMax-H3", 15, True),
    ("MiniMax-H3", 3, False), ("MiniMax-H3", 16, False),
    ("MiniMax-H3-Max", 5, True), ("MiniMax-H3-Max", 4, False),
])
def test_duration_problem(model, duration, ok):
    assert (vg.duration_problem(model, duration) is None) is ok


# ── 输入模式与互斥 ────────────────────────────────────────────────────────


def test_input_mode_detection():
    assert vg.input_mode(None, None, None, None, None) == "t2v"
    assert vg.input_mode("a.png", None, None, None, None) == "i2v"
    assert vg.input_mode(None, "b.png", None, None, None) == "i2v"
    assert vg.input_mode(None, None, [], ["r.mp4"], None) == "r2va"
    assert vg.input_mode(None, None, None, None, ["v.mp3"]) == "r2va"


def test_mix_problem_rejects_frames_plus_refs():
    assert vg.mix_problem("a.png", None, ["r.png"], None, None) is not None
    assert vg.mix_problem(None, "b.png", None, ["r.mp4"], None) is not None


def test_mix_problem_accepts_pure_inputs():
    assert vg.mix_problem("a.png", "b.png", None, None, None) is None
    assert vg.mix_problem(None, None, ["r.png"], ["r.mp4"], ["a.mp3"]) is None
    assert vg.mix_problem(None, None, None, None, None) is None


# ── ratio 三态规则 ────────────────────────────────────────────────────────


def test_effective_ratio_t2v_defaults_to_16_9():
    ratio, notes, err = vg.effective_ratio("t2v", None)
    assert (ratio, err) == (vg.T2V_DEFAULT_RATIO, None)
    assert notes  # 默认值要讲一声，别让人以为服务端自适应了


def test_effective_ratio_t2v_rejects_adaptive():
    ratio, _, err = vg.effective_ratio("t2v", "adaptive")
    assert ratio is None and err is not None


def test_effective_ratio_t2v_passthrough():
    assert vg.effective_ratio("t2v", "9:16") == ("9:16", [], None)


def test_effective_ratio_i2v_always_omits():
    assert vg.effective_ratio("i2v", None) == (None, [], None)
    assert vg.effective_ratio("i2v", "adaptive") == (None, [], None)
    ratio, notes, err = vg.effective_ratio("i2v", "16:9")
    assert (ratio, err) == (None, None)
    assert notes  # 显式传了要提示「会被忽略」


def test_effective_ratio_r2va_optional():
    assert vg.effective_ratio("r2va", None) == (None, [], None)
    assert vg.effective_ratio("r2va", "1:1") == ("1:1", [], None)


# ── 提示词限长 ────────────────────────────────────────────────────────────


def test_prompt_problem_boundaries():
    assert vg.prompt_problem("一只柴犬奔跑") is None
    assert vg.prompt_problem("x" * vg.MAX_PROMPT_CHARS) is None
    assert vg.prompt_problem("x" * (vg.MAX_PROMPT_CHARS + 1)) is not None
    assert vg.prompt_problem("") is not None
    assert vg.prompt_problem("   ") is not None


# ── 本地媒体 -> data URI ──────────────────────────────────────────────────


def test_prepare_media_local_file_becomes_data_uri(tmp_path):
    p = tmp_path / "f.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    items, problems = vg.prepare_media([str(p)], "image")
    assert problems == []
    (url, encoded), = items
    assert url.startswith("data:image/png;base64,")
    assert encoded == len(url)


def test_prepare_media_http_url_passthrough(monkeypatch):
    # 域名不真解析（测试不碰网络）：假装 cdn.example 解析到一个公网 IP
    monkeypatch.setattr(vg, "_resolve_host_ips", lambda host: [ipaddress.ip_address("93.184.216.34")])
    items, problems = vg.prepare_media(["https://cdn.example/a.png"], "image")
    assert problems == []
    assert items == [("https://cdn.example/a.png", 0)]


@pytest.mark.parametrize("url, keyword", [
    ("http://127.0.0.1/a.png", "不可访问"),                       # 回环
    ("http://169.254.169.254/latest/meta-data/a.png", "不可访问"),  # 云元数据
    ("http://10.0.0.5/a.png", "不可访问"),                         # 内网
    ("ftp://cdn.example/a.png", "http(s)"),                       # 协议
    ("http://user:pw@cdn.example/a.png", "账号密码"),              # URL 内嵌凭证
])
def test_prepare_media_rejects_ssrf_urls(url, keyword):
    """媒体 URL 是用户 / 模型输入，非公网地址不能透传给端点（SSRF 兜底）。"""
    items, problems = vg.prepare_media([url], "image")
    assert items == []
    assert any(keyword in p for p in problems)


def test_prepare_media_rejects_unresolvable_host(monkeypatch):
    monkeypatch.setattr(vg, "_resolve_host_ips", lambda host: [])
    items, problems = vg.prepare_media(["https://no-such-host.invalid/a.png"], "image")
    assert items == []
    assert any("解析不了" in p for p in problems)


def test_url_problem_download_allows_private_but_blocks_local_only():
    """下载地址由端点下发：内网 CDN 放行，回环 / 链路本地仍拦。"""
    assert vg.url_problem("http://10.0.0.5/x.mp4", "下载地址", allow_private=True) is None
    assert vg.url_problem("http://127.0.0.1/x.mp4", "下载地址", allow_private=True)
    assert vg.url_problem("http://169.254.169.254/x.mp4", "下载地址", allow_private=True)
    assert vg.url_problem("ftp://cdn.example/x.mp4", "下载地址", allow_private=True)


def test_prepare_media_reports_missing_and_bad_ext(tmp_path):
    _, problems = vg.prepare_media([str(tmp_path / "nope.png")], "image")
    assert any("不存在" in p for p in problems)
    bad = tmp_path / "clip.txt"
    bad.write_bytes(b"x")
    _, problems = vg.prepare_media([str(bad)], "video")
    assert any("格式" in p for p in problems)


def test_prepare_media_kind_matters(tmp_path):
    """图片格式喂给视频口要拦——不是所有「文件」都能当参考视频。"""
    p = tmp_path / "img.png"
    p.write_bytes(b"x")
    _, problems = vg.prepare_media([str(p)], "video")
    assert any("格式" in p for p in problems)


def test_prepare_media_size_limit(tmp_path, monkeypatch):
    p = tmp_path / "big.wav"
    p.write_bytes(b"x" * 20)
    monkeypatch.setitem(vg.MEDIA_KINDS["audio"], "limit_bytes", 10)
    _, problems = vg.prepare_media([str(p)], "audio")
    assert any("超过单文件上限" in p for p in problems)


def test_prepare_media_collects_all_problems_at_once(tmp_path):
    missing = tmp_path / "nope.png"
    ok = tmp_path / "ok.jpg"
    ok.write_bytes(b"x")
    items, problems = vg.prepare_media([str(missing), str(ok)], "image")
    assert len(problems) == 1 and len(items) == 1


def test_body_cap_problem():
    # 60MB 是自留余量（官方限 64MB）——恰好压线不算超，超出才算
    assert vg.body_cap_problem(vg.MAX_ENCODED_MEDIA_BYTES) is None
    assert vg.body_cap_problem(vg.MAX_ENCODED_MEDIA_BYTES + 1) is not None
    assert "URL" in vg.body_cap_problem(vg.MAX_ENCODED_MEDIA_BYTES * 2)


# ── 请求拼装 ──────────────────────────────────────────────────────────────


def test_build_content_order_and_roles():
    content = vg.build_content(
        "提示词",
        first=("https://a/first.png", 0),
        last=("https://a/last.png", 0),
        images=[("https://a/r1.png", 0), ("https://a/r2.png", 0)],
        videos=[("https://a/v.mp4", 0)],
        audios=["https://a/a.mp3"],  # 裸字符串也吃
    )
    assert [c["type"] for c in content] == ["text", "image_url", "image_url", "image_url",
                                            "image_url", "video_url", "audio_url"]
    assert content[0] == {"type": "text", "text": "提示词"}
    assert content[1]["role"] == "first_frame"
    assert content[2]["role"] == "last_frame"
    assert content[3]["image_url"]["url"] == "https://a/r1.png" and content[3]["role"] == "reference_image"
    assert content[5]["video_url"]["url"] == "https://a/v.mp4" and content[5]["role"] == "reference_video"
    assert content[6]["audio_url"]["url"] == "https://a/a.mp3" and content[6]["role"] == "reference_audio"


def test_build_content_minimal_t2v():
    assert vg.build_content("只有文字") == [{"type": "text", "text": "只有文字"}]


def test_build_request_omits_optional_fields():
    body = vg.build_request("MiniMax-H3", [{"type": "text", "text": "p"}], "768P", 5)
    assert body == {"model": "MiniMax-H3", "content": [{"type": "text", "text": "p"}],
                    "resolution": "768P", "duration": 5}


def test_build_request_carries_optional_fields():
    body = vg.build_request("MiniMax-H3-Max", [{"type": "text", "text": "p"}], "480P", 6,
                            ratio="9:16", prompt_expand="quality", aigc_watermark=True)
    assert body["ratio"] == "9:16"
    assert body["extra"] == {"prompt_expansion_mode": "quality"}
    assert body["aigc_watermark"] is True


# ── 提示词体检：官方 h3-prompt-writing 规则的机械判定 ─────────────────────
# 规则原文见 .claude/skills/视频提示词/references/；这份测试守两件事——
# ① 官方格式的好提示词一条不报（提示疲劳比漏报更糟）；② 各条官方禁区能命中。

GOOD_T2V = (
    "integrated_multimodal_description: [Shot 1] Live-action, cinematic, a medium-wide shot "
    "frames a lone figure in a dark trench coat at the edge of a rooftop, overlooking the "
    "neon skyline. The camera holds a static shot as mist drifts between the towers.\n\n"
    "overall_soundscape: Steady rain taps on metal vents while distant traffic hums below.\n\n"
    "non_diegetic_music: A slow synth pad with sparse piano notes, fading out at the end."
)

GOOD_I2V = (
    "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) "
    "is fully referenced.\n\n"
    "integrated_multimodal_description: [Shot 1] Live-action, cinematic, the young woman shown "
    "in <Picture 1> remains beside the rain-covered window. The camera trucks right with small "
    "amplitude at slow speed as she lifts her gaze toward the passing lights.\n\n"
    "overall_soundscape: Train wheels produce a steady metallic rhythm beneath a low hum.\n\n"
    "non_diegetic_music: Sustained cello notes at a slow tempo, gradually decreasing in volume."
)


def test_prompt_notes_quiet_on_official_format():
    """官方三段结构 + 运镜 + 音效写全的提示词一条都不报。"""
    assert vg.prompt_notes(GOOD_T2V, "t2v") == []


def test_prompt_notes_quiet_on_official_i2v():
    assert vg.prompt_notes(GOOD_I2V, "i2v") == []


def test_prompt_notes_flags_thin_prompt():
    assert any("信息量偏少" in n for n in vg.prompt_notes("一只柴犬在草地上跑", "t2v"))


def test_prompt_notes_flags_missing_camera_motion():
    notes = vg.prompt_notes(
        "雨后城市的夜晚，霓虹灯在湿漉漉的街道上投下长长的倒影，行人撑着伞匆匆走过，远处楼群灯火通明", "t2v")
    assert any("镜头运动" in n for n in notes)


def test_prompt_notes_motion_rule_quiet_when_static_declared():
    """固定机位也是运镜的一种——明写 Static Shot 就不该报。"""
    prompt = ("integrated_multimodal_description: [Shot 1] A static shot holds on the skyline while "
              "rain falls.\n\noverall_soundscape: Rain falls steadily.\n\nnon_diegetic_music: N/A")
    assert not any("镜头运动" in n for n in vg.prompt_notes(prompt, "t2v"))


TWO_SHOTS_NO_SIZE = (
    "integrated_multimodal_description: [Shot 1] A lone figure walks along a pier under neon light. "
    "The camera tracks alongside at slow speed. [Shot 2] At 00:03.000, the figure stops and turns "
    "toward the camera.\n\n"
    "overall_soundscape: Waves lap against the pilings.\n\nnon_diegetic_music: N/A"
)


def test_prompt_notes_flags_multi_shot_without_shot_size():
    """运镜 ≠ 景别：分镜给了运镜也仍要逐镜给景别。"""
    assert any("景别" in n for n in vg.prompt_notes(TWO_SHOTS_NO_SIZE, "t2v"))


def test_prompt_notes_shot_size_rule_quiet_when_framing_given():
    prompt = TWO_SHOTS_NO_SIZE.replace("A lone figure walks", "A wide shot frames a lone figure who walks")
    assert not any("景别" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_shot_size_rule_quiet_on_single_shot():
    """单镜头提示词不查景别——官方基础示例本身常不写。"""
    single = ("integrated_multimodal_description: [Shot 1] A lone figure walks along a pier under "
              "neon light while the camera tracks alongside at slow speed.\n\n"
              "overall_soundscape: Waves lap against the pilings.\n\nnon_diegetic_music: N/A")
    assert not any("景别" in n for n in vg.prompt_notes(single, "t2v"))


def test_prompt_notes_shot_count_dedupes_repeated_shot_ids():
    """官方 i2v 对齐指令会再引用一次 [Shot 1]，裸计数会把同一镜头数成两个、误报景别。"""
    assert vg.prompt_notes(GOOD_I2V, "i2v") == []


NO_LIGHT = (
    "integrated_multimodal_description: [Shot 1] A wide shot frames a chef plating a dish on a steel "
    "counter as the camera pushes in with small amplitude at slow speed.\n\n"
    "overall_soundscape: Pans clatter faintly in the next room.\n\nnon_diegetic_music: N/A"
)


def test_prompt_notes_flags_missing_lighting():
    assert any("没写光线" in n for n in vg.prompt_notes(NO_LIGHT, "t2v"))


def test_prompt_notes_lighting_rule_quiet_when_light_described():
    prompt = NO_LIGHT.replace("on a steel counter", "on a steel counter under warm overhead lighting")
    assert not any("没写光线" in n for n in vg.prompt_notes(prompt, "t2v"))


FOUR_SHOTS = (
    "integrated_multimodal_description: [Shot 1] A wide shot frames a city street at dusk. "
    "[Shot 2] At 00:01.000, a close-up of a hand pushing a door. "
    "[Shot 3] At 00:02.000, a medium shot of the room inside. "
    "[Shot 4] At 00:03.000, a wide shot of the balcony.\n\n"
    "overall_soundscape: Traffic hums below.\n\nnon_diegetic_music: N/A"
)


def test_prompt_notes_flags_dense_cut_pace():
    assert any("闪切" in n for n in vg.prompt_notes(FOUR_SHOTS, "t2v", duration=5))


def test_prompt_notes_pace_rule_quiet_when_duration_fits():
    assert not any("闪切" in n for n in vg.prompt_notes(FOUR_SHOTS, "t2v", duration=15))


def test_prompt_notes_pace_rule_quiet_without_duration():
    """没给 --duration 就无从算剪辑率，不猜。"""
    assert not any("闪切" in n for n in vg.prompt_notes(FOUR_SHOTS, "t2v"))


def test_prompt_notes_flags_unstructured_long_prompt():
    long_cn = "一座霓虹城市的天台，主角背对镜头俯瞰夜景，" * 8
    notes = vg.prompt_notes(long_cn, "t2v")
    assert any("官方结构" in n for n in notes)


def test_prompt_notes_structure_rule_quiet_when_shots_used():
    """已经用 [Shot N] 分镜的提示词不再劝结构。"""
    prompt = ("[Shot 1] " + "A rooftop overlooks the city. " * 10
              + "\n\noverall_soundscape: Wind blows across the roof.\n\nnon_diegetic_music: N/A")
    assert not any("官方结构" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_flags_i2v_without_alignment():
    notes = vg.prompt_notes("让她转头看向镜头，保持人物与场景不变", "i2v")
    assert any("对齐指令" in n for n in notes)
    # t2v 不查这条（模式门控）
    assert not any("对齐指令" in n for n in vg.prompt_notes("一只柴犬在草地上奔跑，镜头跟随", "t2v"))


def test_prompt_notes_i2v_alignment_quiet_when_present():
    assert not any("对齐指令" in n for n in vg.prompt_notes(GOOD_I2V, "i2v"))


def test_prompt_notes_flags_first_shot_timestamp():
    prompt = "integrated_multimodal_description: [Shot 1] At 00:00.000, the camera opens on a street."
    assert any("首个镜头" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_first_shot_timestamp_quiet_on_later_shots():
    prompt = "integrated_multimodal_description: [Shot 1] The street is empty. [Shot 2] At 00:03.000, the camera cuts to a window."
    assert not any("首个镜头" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_flags_missing_audio():
    notes = vg.prompt_notes("integrated_multimodal_description: [Shot 1] A static shot of a rooftop at night.",
                            "t2v")
    assert any("声音" in n for n in notes)


def test_prompt_notes_audio_rule_quiet_when_sound_mentioned():
    assert not any("声音" in n for n in vg.prompt_notes("夜晚的街道，雨声淅沥，镜头缓缓推进", "t2v"))


def test_prompt_notes_flags_dialogue_without_d_tag():
    notes = vg.prompt_notes("女孩转头对他说：我们该走了。无人机镜头缓缓拉远。", "t2v")
    assert any("<d>" in n for n in notes)


def test_prompt_notes_dialogue_quiet_with_d_tag():
    prompt = ('integrated_multimodal_description: [Shot 1] A static shot. The woman (S1) says: '
              '<d>[Chinese] 我们该走了。</d>\n\noverall_soundscape: Wind hums.\n\nnon_diegetic_music: N/A')
    assert not any("<d>" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_flags_music_mood_words():
    prompt = ("integrated_multimodal_description: [Shot 1] A static shot of rain.\n\n"
              "overall_soundscape: Rain falls.\n\n"
              "non_diegetic_music: An epic, emotional orchestral score.")
    assert any("抽象情绪词" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_music_mood_quiet_on_instrumentation():
    """cinematic 在 description 里是官方合法写法（官方示例自带），只有 music 段才禁。"""
    prompt = ("integrated_multimodal_description: [Shot 1] Cinematic, a static shot of rain.\n\n"
              "overall_soundscape: Rain falls.\n\n"
              "non_diegetic_music: A slow solo-piano score with sustained low strings.")
    assert not any("抽象情绪词" in n for n in vg.prompt_notes(prompt, "t2v"))


def test_prompt_notes_flags_r2va_without_labels():
    notes = vg.prompt_notes("让参考图里的角色照着参考视频的动作挥手，音色用参考音频", "r2va")
    assert any("标签" in n for n in notes)


def test_prompt_notes_r2va_quiet_with_labels():
    prompt = ("subject_definitions:\n<Subject 1> is the woman in <Picture 1>.\n"
              "detailed_description:\n[Shot 1] A static shot of <Subject 1> waving.")
    assert not any("标签" in n for n in vg.prompt_notes(prompt, "r2va"))


def test_prompt_notes_flags_long_chinese_brief():
    long_cn = "一位义体改造的雇佣兵站在天台边缘俯瞰城市，" * 8
    assert any("英文" in n for n in vg.prompt_notes(long_cn, "t2v"))
    assert not any("英文" in n for n in vg.prompt_notes("一只柴犬奔跑，镜头跟随", "t2v"))


def test_prompt_notes_flags_overlong_timecode():
    prompt = "integrated_multimodal_description: [Shot 1] A street. [Shot 2] At 00:20.000, the camera cuts to a window."
    assert any("时长" in n for n in vg.prompt_notes(prompt, "t2v", duration=5))
    assert not any("时长" in n for n in vg.prompt_notes(prompt, "t2v", duration=25))


def test_timecode_seconds_parses_mm_ss_and_ms():
    assert vg.timecode_seconds("At 00:03.500, cut") == [3.5]
    assert vg.timecode_seconds("At 01:05, cut") == [65.0]
    assert vg.timecode_seconds("no timecode here") == []


# ── 重试判定（官方：transient rate-limit / server failures 退避重试）──────


@pytest.mark.parametrize("status,expect", [
    (429, True), (500, True), (502, True), (503, True),
    (400, False), (401, False), (402, False), (404, False), (422, False), (200, False),
])
def test_should_retry_by_status(status, expect):
    assert vg.should_retry(status, "") is expect


def test_retry_delay_prefers_retry_after_header():
    assert vg.retry_delay(1, {"Retry-After": "7"}) == 7.0
    assert vg.retry_delay(3, {"Retry-After": "600"}) == 60.0


def test_retry_delay_backs_off_within_cap():
    assert 0.8 <= vg.retry_delay(1) <= 1.2
    assert 1.6 <= vg.retry_delay(2) <= 2.4
    assert vg.retry_delay(99) <= 60.0  # 抖动不得顶穿上限


# ── 错误信息解析（网关与官方都是 OaiError 形状）────────────────────────


def _oai(status, message, etype="bad_request_error"):
    return json.dumps({"type": "error",
                       "error": {"type": etype, "message": message, "http_code": str(status)},
                       "request_id": "req_1"}, ensure_ascii=False)


def test_http_error_message_hints_key_on_401():
    msg = vg.http_error_message(401, _oai(401, "login fail (1004)", "authorized_error"))
    assert "VIDEO_API_KEY" in msg and "login fail" in msg


def test_http_error_message_special_cases():
    assert "余额" in vg.http_error_message(402, _oai(402, "insufficient balance (1008)"))
    assert "涉敏" in vg.http_error_message(422, _oai(422, "video description contains sensitive content (1026)",
                                                   "unprocessable_entity_error"))
    assert "临时故障" in vg.http_error_message(503, _oai(503, "internal error (1000)", "server_error"))


def test_http_error_message_plain_passthrough():
    msg = vg.http_error_message(400, _oai(400, "prompt is required"))
    assert "prompt is required" in msg and "HTTP 400" in msg
    assert "HTTP 400" in vg.http_error_message(400, "<html>not json</html>")


# ── usage 与输出路径 ──────────────────────────────────────────────────────


def test_usage_note_renders_seconds():
    line = vg.usage_note({"usage": {"total_seconds": 5, "input_seconds": 0,
                                    "output_seconds": 5, "input_image_count": 2}})
    assert "生成 5s" in line and "参考图 2 张" in line
    # input_seconds 为 0 不渲染（t2v 就是 0，报出来是噪音）
    assert "输入" not in line


def test_usage_note_absent_returns_none():
    assert vg.usage_note({}) is None
    assert vg.usage_note({"usage": {}}) is None


def test_out_path_arg_forces_mp4():
    assert vg.out_path_arg("a.mp4") == (pathlib.Path("a.mp4"), None)
    path, note = vg.out_path_arg("a.mov")
    assert path == pathlib.Path("a.mp4") and note
    path, note = vg.out_path_arg("bare")
    assert path == pathlib.Path("bare.mp4") and note


def test_out_path_arg_default_is_timestamped_mp4():
    path, note = vg.out_path_arg(None)
    assert path.suffix == ".mp4" and note is None and path.name.startswith("video_")


def test_out_path_arg_with_project_dir_joins_relative():
    """-p 给了时相对 --out 拼到项目 assets 目录；绝对路径不被改写。"""
    pd = pathlib.Path("projects/x/deliverables/assets")
    path, note = vg.out_path_arg("a.mov", pd)
    assert path == pd / "a.mp4" and note
    assert vg.out_path_arg("/abs/a.mp4", pd) == (pathlib.Path("/abs/a.mp4"), None)


def test_out_path_arg_default_into_project_dir():
    pd = pathlib.Path("projects/x/deliverables/assets")
    path, note = vg.out_path_arg(None, pd)
    assert path.parent == pd and path.name.startswith("video_") and note is None
