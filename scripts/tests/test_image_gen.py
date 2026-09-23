"""image_gen.py 纯函数测试（无网络：只测解析 / 校验 / 拼装 / 落盘与后处理）。"""
import base64
import pathlib

import pytest


# ── parse_size ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("spec,expected", [
    ("1024x1024", (1024, 1024)),
    ("1536x1024", (1536, 1024)),
    (" 512x512 ", (512, 512)),
    ("AUTO", None),
    ("auto", None),
    (None, None),
    ("", None),
])
def test_parse_size_ok(spec, expected):
    from image_gen import parse_size
    assert parse_size(spec) == expected


@pytest.mark.parametrize("spec", ["1024", "1024x", "x1024", "1024x1024x1024", "宽x高"])
def test_parse_size_malformed(spec):
    from image_gen import parse_size
    with pytest.raises(ValueError):
        parse_size(spec)


# ── size_error ────────────────────────────────────────────────────────────

def test_size_error_accepts_square():
    from image_gen import size_error
    assert size_error(1024, 1024) is None


def test_size_error_accepts_max_ratio_boundary():
    """3:1 是允许的（规则是「不超过」），3072x1024 恰好 3.0。"""
    from image_gen import size_error
    assert size_error(3072, 1024) is None


def test_size_error_rejects_over_max_edge():
    from image_gen import size_error
    assert "最长边" in size_error(3856, 1024)


def test_size_error_rejects_non_multiple_of_16():
    from image_gen import size_error
    assert "16 的倍数" in size_error(1023, 1024)


def test_size_error_rejects_ratio_over_3():
    from image_gen import size_error
    assert "长短边比" in size_error(3840, 1024)


def test_size_error_rejects_too_few_pixels():
    from image_gen import size_error
    assert "总像素" in size_error(512, 512)


def test_size_error_rejects_too_many_pixels():
    """3840x3840 各单项都合法，只有总像素越界。"""
    from image_gen import size_error
    assert "总像素" in size_error(3840, 3840)


@pytest.mark.parametrize("w,h", [(0, 1024), (1024, 0), (-16, 1024)])
def test_size_error_rejects_non_positive(w, h):
    from image_gen import size_error
    assert "正整数" in size_error(w, h)


# ── size_notes（实验档提示，不拦）─────────────────────────────────────────

@pytest.mark.parametrize("w,h,expect_note", [
    (2560, 1440, False),   # 官方实验档分界线，恰好不超
    (2048, 2048, True),    # 边都没超 2560，但像素量超了
    (3072, 1024, False),   # 3:1 长条，像素量更小
    (3840, 2160, True),    # 4K
])
def test_size_notes_experimental_tier(w, h, expect_note):
    from image_gen import size_notes
    notes = size_notes(w, h)
    assert bool(notes) is expect_note
    if notes:
        assert "实验档" in notes[0]


# ── background_error / compression_error ──────────────────────────────────

@pytest.mark.parametrize("bg,fmt,expect", [
    ("transparent", "jpeg", "png / webp"),
    ("transparent", None, None),      # 未指定即服务端默认 png
    ("transparent", "webp", None),
    ("opaque", "jpeg", None),
    (None, "jpeg", None),
])
def test_background_error(bg, fmt, expect):
    from image_gen import background_error
    got = background_error(bg, fmt)
    assert (expect in got) if expect else got is None


@pytest.mark.parametrize("value,fmt,expect", [
    (None, None, None),
    (-1, "jpeg", "0–100"),
    (101, "jpeg", "0–100"),
    (80, "png", "jpeg / webp"),
    (80, None, "jpeg / webp"),        # 不给格式即默认 png，压缩率无效
    (80, "webp", None),
    (0, "jpeg", None),
    (100, "jpeg", None),
])
def test_compression_error(value, fmt, expect):
    from image_gen import compression_error
    got = compression_error(value, fmt)
    assert (expect in got) if expect else got is None


# ── keep_alpha_effective ──────────────────────────────────────────────────

@pytest.mark.parametrize("bg,flag,want_alpha,want_note", [
    ("transparent", False, True, True),    # 透明背景自动保留，否则白花钱
    ("transparent", True, True, False),    # 显式传了就不重复提示
    ("opaque", False, False, False),
    (None, False, False, False),
])
def test_keep_alpha_effective(bg, flag, want_alpha, want_note):
    from image_gen import keep_alpha_effective
    effective, note = keep_alpha_effective(bg, flag)
    assert effective is want_alpha
    assert (note is not None) is want_note


# ── mask_problems ─────────────────────────────────────────────────────────

def test_mask_problems_accepts_matching_rgba():
    from image_gen import mask_problems
    assert mask_problems((64, 48), (64, 48), "RGBA") == []


def test_mask_problems_rejects_size_mismatch():
    from image_gen import mask_problems
    got = mask_problems((64, 48), (32, 48), "RGBA")
    assert len(got) == 1 and "尺寸" in got[0]


def test_mask_problems_rejects_missing_alpha():
    from image_gen import mask_problems
    got = mask_problems((64, 48), (64, 48), "RGB")
    assert len(got) == 1 and "alpha" in got[0]


def test_mask_problems_reports_both():
    from image_gen import mask_problems
    assert len(mask_problems((64, 48), (32, 32), "L")) == 2


# ── upload_mime ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,expect", [
    ("a.png", "image/png"),
    ("a.PNG", "image/png"),
    ("a.jpg", "image/jpeg"),
    ("a.jpeg", "image/jpeg"),
    ("a.webp", "image/webp"),
    ("a.bmp", "image/png"),   # 不认的后缀退回 png，由服务端最终裁决
])
def test_upload_mime(name, expect):
    from image_gen import upload_mime
    assert upload_mime(pathlib.Path(name)) == expect


# ── body_json / http_error_message ────────────────────────────────────────

@pytest.mark.parametrize("text,expect_none", [
    ('{"data": []}', False),
    ("[1, 2]", True),
    ('"just a string"', True),
    ("<html>502 Bad Gateway</html>", True),
    ("", True),
])
def test_body_json(text, expect_none):
    from image_gen import body_json
    assert (body_json(text) is None) is expect_none


def test_http_error_message_moderation_blocked():
    from image_gen import http_error_message
    body = ('{"error": {"type": "image_generation_user_error", "code": "moderation_blocked",'
            ' "moderation_details": {"moderation_stage": "input", "categories": ["harassment"]}}}')
    msg = http_error_message(400, body)
    assert "输入侧" in msg and "harassment" in msg and "原样重试无效" in msg


def test_http_error_message_user_error():
    from image_gen import http_error_message
    body = '{"error": {"type": "image_generation_user_error", "code": "invalid_size", "message": "bad size"}}'
    msg = http_error_message(400, body)
    assert "bad size" in msg and "用户可修正" in msg


def test_http_error_message_retryable():
    from image_gen import http_error_message
    assert "可稍后重试" in http_error_message(429, '{"error": {"message": "slow down"}}')
    assert "可稍后重试" in http_error_message(503, "upstream unavailable")


def test_http_error_message_non_json_falls_back_to_raw():
    from image_gen import http_error_message
    msg = http_error_message(400, "<html>gateway error</html>")
    assert "400" in msg and "gateway error" in msg


# ── select_model ──────────────────────────────────────────────────────────

def test_select_model_default():
    from image_gen import select_model, MODEL_DEFAULT
    assert select_model() == MODEL_DEFAULT


def test_select_model_simple_flag():
    from image_gen import select_model, MODEL_SIMPLE
    assert select_model(simple=True) == MODEL_SIMPLE


@pytest.mark.parametrize("alias", ["flare", "sunburst"])
def test_select_model_expands_alias(alias):
    from image_gen import select_model, MODEL_ALIASES
    assert select_model(alias) == MODEL_ALIASES[alias]


def test_select_model_explicit_name_passes_through():
    from image_gen import select_model
    assert select_model("some-other-endpoint-model") == "some-other-endpoint-model"


def test_select_model_explicit_beats_simple_flag():
    from image_gen import select_model
    assert select_model("sunburst", simple=True) == "gpt-image-2.5-sunburst"


# ── build_payload ─────────────────────────────────────────────────────────

def test_build_payload_drops_nones():
    from image_gen import build_payload
    payload = build_payload("m", "p")
    assert payload == {"model": "m", "prompt": "p"}


def test_build_payload_maps_keys():
    from image_gen import build_payload
    payload = build_payload("m", "p", size="1024x1024", quality="high",
                            output_format="jpeg", compression=80, background="opaque")
    assert payload["size"] == "1024x1024"
    assert payload["output_compression"] == 80
    assert payload["output_format"] == "jpeg"
    assert payload["background"] == "opaque"


def test_build_payload_moderation_only_when_set():
    from image_gen import build_payload
    assert "moderation" not in build_payload("m", "p")
    assert build_payload("m", "p", moderation="low")["moderation"] == "low"


# ── out_paths ─────────────────────────────────────────────────────────────

def test_out_paths_single():
    from image_gen import out_paths
    assert out_paths(pathlib.Path("a/logo.png"), 1) == [pathlib.Path("a/logo.png")]


def test_out_paths_multi_numbers_from_one():
    from image_gen import out_paths
    got = out_paths(pathlib.Path("a/logo.png"), 3)
    assert [p.name for p in got] == ["logo-1.png", "logo-2.png", "logo-3.png"]
    assert all(p.parent.name == "a" for p in got)


# ── decode_b64 ────────────────────────────────────────────────────────────

def test_decode_b64_roundtrip():
    from image_gen import decode_b64
    raw = b"\x89PNG\r\n\x1a\n fake"
    assert decode_b64({"b64_json": base64.b64encode(raw).decode()}) == raw


def test_decode_b64_absent_returns_none():
    from image_gen import decode_b64
    assert decode_b64({"url": "https://example.invalid/x.png"}) is None
    assert decode_b64({}) is None


# ── resolve_project_assets ────────────────────────────────────────────────

def _mk_project(root, *parts):
    d = root.joinpath("projects", *parts, "deliverables", "assets")
    d.mkdir(parents=True)
    return d


def test_resolve_project_assets_line_level(tmp_path):
    from image_gen import resolve_project_assets
    expected = _mk_project(tmp_path, "community")
    assert resolve_project_assets(tmp_path, "community") == expected


def test_resolve_project_assets_nested_campaign(tmp_path):
    from image_gen import resolve_project_assets
    expected = _mk_project(tmp_path, "growth", "queen")
    assert resolve_project_assets(tmp_path, "queen") == expected


def test_resolve_project_assets_missing(tmp_path):
    from image_gen import resolve_project_assets
    (tmp_path / "projects").mkdir()
    with pytest.raises(ValueError, match="找不到"):
        resolve_project_assets(tmp_path, "nope")


def test_resolve_project_assets_ambiguous(tmp_path):
    from image_gen import resolve_project_assets
    _mk_project(tmp_path, "queen")
    _mk_project(tmp_path, "growth", "queen")
    with pytest.raises(ValueError, match="匹配多个"):
        resolve_project_assets(tmp_path, "queen")


# ── build_out_path ────────────────────────────────────────────────────────

STAMP = "20260101_000000"


def test_build_out_path_defaults_to_cwd_timestamp():
    from image_gen import build_out_path
    assert build_out_path(None, None, "png", STAMP) == pathlib.Path(f"image_{STAMP}.png")


def test_build_out_path_defaults_into_project_dir(tmp_path):
    from image_gen import build_out_path
    assert build_out_path(None, tmp_path, "webp", STAMP) == tmp_path / f"image_{STAMP}.webp"


def test_build_out_path_absolute_wins_over_project(tmp_path):
    from image_gen import build_out_path
    wanted = tmp_path / "elsewhere" / "x.png"
    assert build_out_path(str(wanted), tmp_path / "assets", "png", STAMP) == wanted


def test_build_out_path_relative_joins_project_dir(tmp_path):
    from image_gen import build_out_path
    assert build_out_path("logo.png", tmp_path / "assets", "png", STAMP) == tmp_path / "assets" / "logo.png"


def test_build_out_path_relative_without_project_stays_cwd():
    from image_gen import build_out_path
    assert build_out_path("logo.png", None, "png", STAMP) == pathlib.Path("logo.png")


def test_build_out_path_fills_missing_suffix():
    from image_gen import build_out_path
    assert build_out_path("logo", None, "jpg", STAMP) == pathlib.Path("logo.jpg")


# ── save_image（b64 落盘，不做网络）────────────────────────────────────────

def test_save_image_writes_b64_and_makes_parent(tmp_path):
    from image_gen import save_image
    raw = b"\x89PNG\r\n\x1a\n payload"
    target = tmp_path / "deep" / "a.png"
    nbytes = save_image({"b64_json": base64.b64encode(raw).decode()}, target)
    assert target.read_bytes() == raw
    assert nbytes == len(raw)


def test_save_image_without_b64_raises(tmp_path):
    from image_gen import save_image
    with pytest.raises(ValueError, match="b64_json"):
        save_image({"url": "https://example.invalid/x.png"}, tmp_path / "a.png")


# ── postprocess（PIL 造图走 tmp_path）─────────────────────────────────────

def _make_png(path, size=(64, 48), mode="RGBA", color=(255, 0, 0, 0)):
    from PIL import Image
    Image.new(mode, size, color).save(path)
    return path


def test_postprocess_composites_transparent_to_white(tmp_path):
    from PIL import Image
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", color=(255, 0, 0, 0))  # 全透明
    notes = postprocess(p)
    assert Image.open(p).mode == "RGB"
    assert Image.open(p).getpixel((0, 0)) == (255, 255, 255)
    assert any("透明像素" in n for n in notes)


def test_postprocess_keep_alpha_preserves_channel(tmp_path):
    from PIL import Image
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", color=(255, 0, 0, 0))
    notes = postprocess(p, keep_alpha=True)
    assert Image.open(p).mode == "RGBA"
    assert notes == []


def test_postprocess_opaque_rgba_becomes_rgb_without_note(tmp_path):
    from PIL import Image
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", color=(255, 0, 0, 255))
    notes = postprocess(p)
    assert Image.open(p).mode == "RGB"
    assert not any("透明像素" in n for n in notes)


def test_postprocess_resizes_and_notes_canvas_change(tmp_path):
    from PIL import Image
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", size=(64, 48), mode="RGB", color=(1, 2, 3))
    notes = postprocess(p, want_size=(128, 128))
    assert Image.open(p).size == (128, 128)
    assert any("模型改了画布" in n for n in notes)


def test_postprocess_no_resize_when_size_matches(tmp_path):
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", size=(64, 48), mode="RGB", color=(1, 2, 3))
    assert postprocess(p, want_size=(64, 48)) == []


def test_postprocess_jpeg_drops_alpha(tmp_path):
    """服务端可能把带透明通道的 PNG 字节写到 .jpg 路径上——后处理须按后缀丢 alpha。"""
    from io import BytesIO
    from PIL import Image
    from image_gen import postprocess
    buf = BytesIO()
    Image.new("RGBA", (64, 48), (255, 0, 0, 0)).save(buf, "PNG")
    p = tmp_path / "t.jpg"
    p.write_bytes(buf.getvalue())
    postprocess(p, keep_alpha=True)
    assert Image.open(p).mode == "RGB"


# ── composite_masked（蒙版回贴：α=0 处逐像素等于原图）─────────────────────

REF_RGB = (10, 20, 30)
GEN_RGB = (200, 100, 50)


def _mk_mask(path, size=(64, 48), edit_box=(0, 0, 32, 48)):
    """edit_box（默认左半）alpha=0 = 编辑区；其余 alpha=255 = 要逐像素保留。

    官方 mask 语义：**透明处才是要改的区域**。
    """
    from PIL import Image
    mask = Image.new("RGBA", size, (0, 0, 0, 255))
    mask.paste((0, 0, 0, 0), edit_box)
    mask.save(path)
    return path


def test_composite_masked_restores_untouched_region(tmp_path):
    from PIL import Image
    from image_gen import composite_masked

    ref = tmp_path / "ref.png"
    gen = tmp_path / "gen.png"
    Image.new("RGB", (64, 48), REF_RGB).save(ref)
    Image.new("RGB", (64, 48), GEN_RGB).save(gen)
    mask = _mk_mask(tmp_path / "mask.png")

    notes = composite_masked(gen, ref, mask)

    out = Image.open(gen).convert("RGB")
    assert out.getpixel((5, 5)) == GEN_RGB      # α=0：编辑区用生成结果
    assert out.getpixel((40, 5)) == REF_RGB     # α=255：逐像素等于原图
    assert any("回贴" in n for n in notes)


def test_composite_masked_normalizes_size(tmp_path):
    """模型改了画布时先归一尺寸再回贴。"""
    from PIL import Image
    from image_gen import composite_masked

    ref = tmp_path / "ref.png"
    gen = tmp_path / "gen.png"
    Image.new("RGB", (64, 48), REF_RGB).save(ref)
    Image.new("RGB", (32, 24), GEN_RGB).save(gen)
    mask = _mk_mask(tmp_path / "mask.png")

    composite_masked(gen, ref, mask)

    out = Image.open(gen).convert("RGB")
    assert out.size == (64, 48)
    assert out.getpixel((5, 5)) == GEN_RGB
    assert out.getpixel((40, 5)) == REF_RGB


# ── postprocess 不重写（重存会让 jpeg / webp 二次有损）────────────────────

def _noisy_rgb(size=(64, 48)):
    from PIL import Image
    im = Image.new("RGB", size)
    im.putdata([((x * 7) % 256, (y * 13) % 256, ((x ^ y) * 3) % 256)
                for y in range(size[1]) for x in range(size[0])])
    return im


def test_postprocess_leaves_untouched_jpeg_byte_identical(tmp_path):
    """不需要改动时不许碰文件——重存等于把服务端的画质再降一档。"""
    from image_gen import postprocess
    p = tmp_path / "t.jpg"
    _noisy_rgb().save(p, quality=95)
    before = p.read_bytes()
    assert postprocess(p, want_size=(64, 48)) == []
    assert p.read_bytes() == before


def test_postprocess_leaves_untouched_png_byte_identical(tmp_path):
    from image_gen import postprocess
    p = _make_png(tmp_path / "t.png", mode="RGB", color=(1, 2, 3))
    before = p.read_bytes()
    assert postprocess(p) == []
    assert p.read_bytes() == before


def test_postprocess_is_idempotent_on_jpeg(tmp_path):
    """跑两次结果一致——不幂等就说明还在重编码。"""
    from image_gen import postprocess
    p = tmp_path / "t.jpg"
    _noisy_rgb().save(p, quality=95)
    postprocess(p, want_size=(64, 48))
    once = p.read_bytes()
    postprocess(p, want_size=(64, 48))
    assert p.read_bytes() == once


def test_postprocess_still_rewrites_when_canvas_changes(tmp_path):
    from PIL import Image
    from image_gen import postprocess
    p = tmp_path / "t.jpg"
    _noisy_rgb().save(p, quality=95)
    postprocess(p, want_size=(32, 24))
    assert Image.open(p).size == (32, 24)


# ── prompt_notes（提示词体检：只提示，不改写提示词）──────────────────────

WELL_FORMED = (
    "Create a photorealistic candid photograph of a barista pulling a shot, "
    "shot like a 35mm film photograph, medium close-up at eye level, "
    "soft window daylight, shallow depth of field, natural color balance.\n"
    "Constraints: no extra text, no watermarks."
)


def test_prompt_notes_flags_thin_prompt():
    from image_gen import prompt_notes
    assert any("信息量偏少" in n for n in prompt_notes("一只柴犬"))


def test_prompt_notes_thin_prompt_rule_skips_edits():
    """官方改图示例本身就短（Make it look like a winter evening with snowfall.），不该按生成的标准要求。"""
    from image_gen import prompt_notes
    notes = prompt_notes("把背景换成雪夜，下着小雪", editing=True)
    assert not any("信息量偏少" in n for n in notes)


def test_prompt_notes_detailed_chinese_brief_is_not_thin():
    """中文信息密度高，29 字的信息图简报已经写全主体 / 用途 / 元素，不该报信息量不足。"""
    from image_gen import prompt_notes
    notes = prompt_notes("一张讲咖啡机工作原理的信息图，含图例与脚注，白底，扁平风格", quality="high")
    assert not any("信息量偏少" in n for n in notes)


def test_effective_length_weights_cjk_double():
    from image_gen import effective_length
    assert effective_length("") == 0
    assert effective_length("abcd") == 4
    assert effective_length("柴犬") == 4
    assert effective_length("a犬") == 3


def test_prompt_notes_quiet_on_well_formed_prompt():
    """官方结构写全的提示词一条都不报——体检规则宁漏勿扰。"""
    from image_gen import prompt_notes
    assert prompt_notes(WELL_FORMED) == []


def test_prompt_notes_flags_photoreal_intent_without_declaration():
    from image_gen import prompt_notes
    notes = prompt_notes("一张写实的城市夜景长曝光摄影，宽幅构图，霓虹与雨水的反光铺满街面，气氛压抑")
    assert any("photorealistic" in n for n in notes)


def test_prompt_notes_accepts_declared_photoreal():
    from image_gen import prompt_notes
    notes = prompt_notes("A photorealistic wide city night scene, long exposure, "
                         "neon reflections on wet asphalt, muted color balance")
    assert not any("photorealistic" in n for n in notes)


def test_prompt_notes_flags_photo_scene_without_lighting():
    from image_gen import prompt_notes
    notes = prompt_notes("A photorealistic product photograph of a ceramic mug on a linen cloth, "
                         "centered composition, muted earth tones, shallow depth of field")
    assert any("光线" in n for n in notes)


def test_prompt_notes_lighting_rule_quiet_when_light_described():
    from image_gen import prompt_notes
    notes = prompt_notes("A photorealistic product photograph of a ceramic mug on a linen cloth, "
                         "lit by soft window daylight from the left, centered composition")
    assert not any("光线" in n for n in notes)


def test_prompt_notes_lighting_rule_skips_flat_graphic_work():
    """平面版式 / 图标 / 信息图本就没有光线可言——只对摄影 / 场景类报，否则误杀设计稿。"""
    from image_gen import prompt_notes
    notes = prompt_notes('Ad poster with the tagline "Yours to Create." rendered exactly once, '
                         'centered, bold sans-serif, no extra text, clean modern layout.')
    assert not any("光线" in n for n in notes)


def test_prompt_notes_flags_person_without_shot_size():
    from image_gen import prompt_notes
    notes = prompt_notes("一张写实照片：一位女性咖啡师在吧台后拉花，暖色调，soft window daylight，"
                         "背景虚化，photorealistic")
    assert any("景别" in n for n in notes)


def test_prompt_notes_shot_size_rule_quiet_when_framing_given():
    from image_gen import prompt_notes
    notes = prompt_notes("一张写实照片：一位女性咖啡师在吧台后拉花，中景平视，暖色调，"
                         "soft window daylight，photorealistic")
    assert not any("景别" in n for n in notes)


def test_prompt_notes_craft_rules_skip_edits():
    """改图的光线与取景由输入图决定，要求补写是噪音。"""
    from image_gen import prompt_notes
    notes = prompt_notes("把这张人物写实照片的背景换成雪夜，保留人物身份与版面不变", editing=True)
    assert not any("光线" in n or "景别" in n for n in notes)


def test_prompt_notes_flags_quoted_text_without_count_and_guard():
    from image_gen import prompt_notes
    notes = prompt_notes("海报中间放一行大字 “Yours to Create.”，干净构图，面向青年街头品牌，版式现代")
    assert any("exactly once" in n for n in notes)


def test_prompt_notes_quoted_text_with_count_and_guard_is_quiet():
    from image_gen import prompt_notes
    prompt = ('Ad poster with the tagline "Yours to Create." rendered exactly once, '
              'centered, bold sans-serif, no extra text, no watermarks, clean modern layout.')
    assert prompt_notes(prompt) == []


def test_prompt_notes_flags_transparent_background_absent_from_prompt():
    from image_gen import prompt_notes
    notes = prompt_notes("A minimal flat icon of a coffee cup, clean silhouette, centered",
                         background="transparent")
    assert any("透明背景" in n for n in notes)


def test_prompt_notes_transparent_stated_in_prompt_is_quiet():
    from image_gen import prompt_notes
    prompt = ("Extract the product and isolate it on a fully transparent background, "
              "crisp silhouette, no backdrop, no checkerboard, no shadow")
    assert not any("透明背景" in n for n in prompt_notes(prompt, background="transparent"))


def test_prompt_notes_flags_multi_reference_without_roles():
    from image_gen import prompt_notes
    assert any("参考图" in n for n in prompt_notes("把这几个物件合成一个礼盒", ref_count=3))
    assert not any("参考图" in n for n in prompt_notes("把这几个物件合成一个礼盒", ref_count=1))


def test_prompt_notes_flags_edit_without_preserve_list():
    from image_gen import prompt_notes
    assert any("保留" in n for n in prompt_notes("把背景换成夜景", editing=True))


def test_prompt_notes_edit_with_preserve_list_is_quiet():
    from image_gen import prompt_notes
    notes = prompt_notes("只把背景换成夜景，保持人物身份、姿势、光照与构图不变", editing=True)
    assert not any("保留" in n for n in notes)


def test_prompt_notes_flags_removal_constraint_on_edit():
    from image_gen import prompt_notes
    notes = prompt_notes("把画面里的批注去掉，其余部分保持原样不动", editing=True)
    assert any("否定" in n for n in notes)


def test_prompt_notes_exclusions_are_fine_for_generation():
    """生成时排除项是官方推荐的正当写法（其示例自己就写 Avoid clip art, stock photography）。"""
    from image_gen import prompt_notes
    prompt = ('Create one pitch-deck slide titled "Market Opportunity", clean white background, '
              'modern sans-serif typography, crisp minimal layout, polished spacing.\n'
              'Avoid clip art, stock photography, gradients, shadows, decorative elements.')
    assert not any("否定" in n for n in prompt_notes(prompt, quality="high"))


def test_text_once_pattern_ignores_at_once():
    """'at once' 不是出现次数声明。"""
    from image_gen import prompt_notes
    notes = prompt_notes('海报中间放大字 "Hi"，所有元素一次性排布完成，干净背景与克制配色，版式现代简洁大气')
    assert any("exactly once" in n for n in notes)


def test_prompt_notes_dense_text_low_quality_vs_high_quality():
    from image_gen import prompt_notes
    dense = "一张信息图，白底，含图例与脚注，配色克制"
    assert any("medium" in n for n in prompt_notes(dense, quality="low"))
    assert not any("medium 以上质量档" in n for n in prompt_notes(dense, quality="high"))


def test_prompt_notes_dense_text_quiet_on_single_tagline():
    """单行标语不算密排——low 档也渲染得动，不该报。"""
    from image_gen import prompt_notes
    prompt = ('Create a bold poster with a single short slogan rendered exactly once, '
              'no extra text, no watermarks, high contrast layout')
    assert not any("medium" in n for n in prompt_notes(prompt, quality="low"))


def test_prompt_notes_flags_long_chinese_brief_only():
    """只有超过复杂度阈值的中文简报才提示——短中文提示词别烦人。"""
    from image_gen import PROMPT_EN_HINT_CHARS, prompt_notes
    long_cn = "为社区排行榜上线做一张宣发主视觉，" + "包含榜单卡片、用户头像、渐变背景与光效，" * 6
    assert len(long_cn) >= PROMPT_EN_HINT_CHARS
    assert any("英文核心指令" in n for n in prompt_notes(long_cn))
    assert not any("英文核心指令" in n for n in prompt_notes("一只戴圆框眼镜的柴犬，扁平插画风"))


# ── 提示词 / 上传 / n 的前置校验 ──────────────────────────────────────────

def test_cjk_ratio_bounds():
    from image_gen import cjk_ratio
    assert cjk_ratio("") == 0.0
    assert cjk_ratio("hello world") == 0.0
    assert cjk_ratio("柴犬") == 1.0
    assert 0.0 < cjk_ratio("flat icon of 柴犬") < 1.0


def test_prompt_length_error_boundary():
    from image_gen import MAX_PROMPT_CHARS, prompt_length_error
    assert prompt_length_error("x" * MAX_PROMPT_CHARS) is None
    assert "32000" in prompt_length_error("x" * (MAX_PROMPT_CHARS + 1))


def test_ref_count_error_boundary():
    from image_gen import MAX_REF_IMAGES, ref_count_error
    assert ref_count_error(MAX_REF_IMAGES) is None
    assert "16" in ref_count_error(MAX_REF_IMAGES + 1)


def test_upload_size_error_boundary(tmp_path):
    from image_gen import MAX_UPLOAD_BYTES, upload_size_error
    assert upload_size_error(tmp_path / "a.png", MAX_UPLOAD_BYTES - 1) is None
    assert "50MB" in upload_size_error(tmp_path / "a.png", MAX_UPLOAD_BYTES)


def test_upload_problems_reports_missing_files(tmp_path):
    from image_gen import upload_problems
    real = tmp_path / "ok.png"
    real.write_bytes(b"\0")
    assert upload_problems([]) == []
    assert upload_problems([real]) == []
    assert any("不存在" in p for p in upload_problems([tmp_path / "nope.png"]))


def test_n_error_boundary():
    from image_gen import MAX_N, n_error
    assert n_error(1) is None
    assert n_error(MAX_N) is None
    assert "至少" in n_error(0)
    assert "10" in n_error(MAX_N + 1)


# ── 重试判定 ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("status,expect", [
    (429, True), (500, True), (502, True), (503, True), (504, True),
    (400, False), (401, False), (403, False), (404, False), (200, False),
])
def test_should_retry_by_status(status, expect):
    from image_gen import should_retry
    assert should_retry(status, "") is expect


def test_should_retry_skips_moderation_and_user_errors():
    from image_gen import should_retry
    blocked = '{"error": {"code": "moderation_blocked", "type": "image_generation_user_error"}}'
    user_err = '{"error": {"type": "image_generation_user_error", "code": "invalid_prompt"}}'
    assert should_retry(429, blocked) is False
    assert should_retry(500, user_err) is False


def test_retry_delay_prefers_retry_after_header():
    from image_gen import retry_delay
    assert retry_delay(1, {"Retry-After": "7"}) == 7.0
    assert retry_delay(3, {"Retry-After": "600"}) == 60.0   # 封顶


def test_retry_delay_backs_off_exponentially_with_jitter():
    from image_gen import retry_delay
    assert 0.8 <= retry_delay(1) <= 1.2
    assert 1.6 <= retry_delay(2) <= 2.4
    assert retry_delay(99) <= 60.0


# ── usage_note ────────────────────────────────────────────────────────────

def test_usage_note_renders_tokens_and_cost():
    from image_gen import usage_note
    line = usage_note({"usage": {"input_tokens": 40, "output_tokens": 391}})
    assert "391" in line and "40" in line
    assert "$0.0117" in line


def test_usage_note_absent_returns_none():
    from image_gen import usage_note
    assert usage_note({}) is None
    assert usage_note({"usage": {}}) is None


# ── build_payload 的 n ────────────────────────────────────────────────────

def test_build_payload_sends_n_only_when_counting_multiple():
    from image_gen import build_payload
    assert "n" not in build_payload("m", "p", count=None)
    assert build_payload("m", "p", count=4)["n"] == 4


# ── 端点路由纯函数（load_conf 的候选解析与选优；probe_base 走网络不单测）──────

def test_parse_base_candidates_dedupe_and_order():
    from image_gen import parse_base_candidates
    assert parse_base_candidates("https://a.example/v1, https://b.example/v1 ,https://a.example/v1") \
        == ["https://a.example/v1", "https://b.example/v1"]


def test_parse_base_candidates_trims_slash_and_empties():
    from image_gen import parse_base_candidates
    assert parse_base_candidates(" https://a.example/v1/ ,, ,https://b.example/v1/") \
        == ["https://a.example/v1", "https://b.example/v1"]


def test_parse_base_candidates_empty():
    from image_gen import parse_base_candidates
    assert parse_base_candidates("") == []
    assert parse_base_candidates(None) == []


def test_pick_fastest_prefers_min_ok():
    from image_gen import pick_fastest
    assert pick_fastest([("a", 900), ("b", 480), ("c", None)]) == "b"


def test_pick_fastest_all_fail_falls_back_first():
    from image_gen import pick_fastest
    assert pick_fastest([("a", None), ("b", None)]) == "a"


def test_pick_fastest_empty():
    from image_gen import pick_fastest
    assert pick_fastest([]) is None
