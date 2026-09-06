"""compress_image.py 纯函数测试。"""
import pytest


# ── needs_compress ────────────────────────────────────────────────────────

def test_needs_compress_oversized_dim():
    from compress_image import needs_compress
    assert needs_compress(2500, 1000, 100) is True


def test_needs_compress_oversized_file():
    from compress_image import needs_compress
    assert needs_compress(1000, 800, 6 * 1024 * 1024) is True


def test_needs_compress_ok():
    from compress_image import needs_compress
    assert needs_compress(1800, 900, 4 * 1024 * 1024) is False


# ── compress_image ────────────────────────────────────────────────────────

@pytest.fixture
def oversized_png(tmp_path):
    """造 3000×2000 PNG 落 tmp_path。"""
    from PIL import Image
    img = Image.new("RGB", (3000, 2000), color=(100, 150, 200))
    p = tmp_path / "big.png"
    img.save(p, "PNG")
    return p


def test_compress_resizes_dim(oversized_png):
    from compress_image import compress_image
    out = compress_image(oversized_png, max_dim=1800)
    from PIL import Image
    w, h = Image.open(out).size
    assert max(w, h) <= 1800


def test_compress_output_named_with_suffix(oversized_png):
    from compress_image import compress_image
    out = compress_image(oversized_png)
    assert out.stem.endswith("-compressed")


def test_compress_inplace(oversized_png):
    from compress_image import compress_image
    out = compress_image(oversized_png, inplace=True)
    assert out == oversized_png


def test_compress_already_ok(tmp_path):
    """已满足限制的图不应改变尺寸。"""
    from PIL import Image
    from compress_image import compress_image
    img = Image.new("RGB", (800, 600), color=(50, 50, 50))
    p = tmp_path / "small.png"
    img.save(p, "PNG")
    out = compress_image(p, max_dim=1800)
    w, h = Image.open(out).size
    assert (w, h) == (800, 600)
