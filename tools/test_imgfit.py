# -*- coding: utf-8 -*-
"""The 320 px input condition: letterbox geometry, the file encoding, and that the runner's cache holds the same bytes as the Release zip."""
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402

from datasets import imgfit  # noqa: E402
from runner import run as runner_run  # noqa: E402


class LetterboxTests(unittest.TestCase):
    def test_always_a_square_of_px(self):
        for w, h in [(640, 480), (480, 640), (640, 640), (100, 30), (30, 100), (1, 1), (320, 320), (4000, 100)]:
            self.assertEqual(imgfit.letterbox(Image.new("RGB", (w, h), (1, 2, 3))).size, (320, 320), (w, h))

    def test_centred_on_grey_and_aspect_kept(self):
        im = imgfit.letterbox(Image.new("RGB", (640, 320), (255, 0, 0)))       # 2:1 -> 320 x 160 in the middle
        self.assertEqual(im.getpixel((160, 160)), (255, 0, 0))
        self.assertEqual(im.getpixel((160, 10)), imgfit.PAD)
        self.assertEqual(im.getpixel((160, 310)), imgfit.PAD)
        self.assertEqual(im.getpixel((5, 160)), (255, 0, 0))

    def test_encode_format_by_name(self):
        src = Image.new("RGB", (200, 100), (10, 20, 30))
        self.assertEqual(Image.open(io.BytesIO(imgfit.encode(src, "a.jpg"))).format, "JPEG")
        self.assertEqual(Image.open(io.BytesIO(imgfit.encode(src, "a.png"))).format, "PNG")
        self.assertEqual(imgfit.encode(src, "a.jpg"), imgfit.encode(src, "a.jpg"))     # deterministic


class RunnerCacheTests(unittest.TestCase):
    def test_runner_cache_equals_encode_and_a_320_square_is_kept_as_is(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            src = d / "o.jpg"
            Image.new("RGB", (640, 480), (200, 100, 50)).save(src, quality=90)
            small = d / "small"
            small.mkdir()
            (out,) = runner_run.prepare_images({"images": [str(src)]}, small, 320, "letterbox")
            self.assertEqual(pathlib.Path(out).read_bytes(), imgfit.encode(Image.open(src), "o.jpg"))
            # what Colab does: the Release picture is already 320 x 320 -> copied byte for byte
            rel = d / "r.jpg"
            rel.write_bytes(pathlib.Path(out).read_bytes())
            small2 = d / "small2"
            small2.mkdir()
            (out2,) = runner_run.prepare_images({"images": [str(rel)]}, small2, 320, "letterbox")
            self.assertEqual(pathlib.Path(out2).read_bytes(), rel.read_bytes())


if __name__ == "__main__":
    unittest.main()
