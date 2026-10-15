# -*- coding: utf-8 -*-
"""Jev API adapter: the request shapes, the picture size rule, the answer reading, and that the key never leaves the process.
Nothing here touches the network (urlopen is replaced)."""
import base64
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapters import typesafe_jev as J  # noqa: E402

OPTS = [("cat", "cat"), ("dog", "dog"), ("fox", "fox")]


class SizeTests(unittest.TestCase):
    def test_fit_size_meets_the_api_limits(self):
        """Every picture size the bench has (224 px longest side, any aspect) maps to a size the API accepts."""
        for w, h in [(224, 224), (224, 168), (168, 224), (224, 126), (224, 30), (30, 224), (640, 480), (1568, 256), (300, 2000)]:
            nw, nh = J.fit_size(w, h)
            self.assertTrue(J.MIN_SIDE <= nw <= J.MAX_SIDE and J.MIN_SIDE <= nh <= J.MAX_SIDE, (w, h, nw, nh))
            self.assertTrue(J.MIN_PIXELS <= nw * nh <= J.MAX_PIXELS, (w, h, nw, nh))

    def test_encode_image_returns_a_png_of_that_size(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x.png"
            Image.new("RGB", (224, 168), (10, 20, 30)).save(p)
            im = Image.open(io.BytesIO(base64.b64decode(J.encode_image(str(p)))))
            self.assertEqual(im.format, "PNG")
            self.assertEqual(im.size, J.fit_size(224, 168))


class RequestTests(unittest.TestCase):
    def test_text_only_state_is_a_plain_string(self):
        b = J.build_request("jev-preview", "Some state", [], "noul", "Is it?", None)
        self.assertEqual(b["state"], "Some state")
        self.assertNotIn("assets", b)
        self.assertEqual(b["questions"], {"q": {"instructions": "Is it?", "type": "noul"}})

    def test_picture_becomes_an_asset_the_state_refers_to(self):
        b = J.build_request("jev-preview", "ctx", ["QUJD"], "choice", "Which?", OPTS)
        (ref, asset), = b["assets"].items()
        self.assertEqual(asset, {"type": "image", "format": "png", "data_base64": "QUJD"})
        self.assertEqual(b["state"], {"image": ref, "context": "ctx"})
        self.assertEqual(b["questions"]["q"]["criteria"], {"cat": None, "dog": None, "fox": None})
        self.assertEqual(J.build_request("m", "", ["QUJD"], "noul", "q", None)["state"].keys(), {"image"})

    def test_score_levels_and_bad_input(self):
        q = J.build_request("m", "s", [], "score", "How?", ["low", "mid", "high"])["questions"]["q"]
        self.assertEqual((q["type"], q["criteria"]), ("score", ["low", "mid", "high"]))
        with self.assertRaises(ValueError):
            J.build_request("m", "s", [], "choice", "q", [("a", "a"), ("a", "b")])
        with self.assertRaises(ValueError):
            J.build_request("m", "s", [], "box", "q", None)


class AnswerTests(unittest.TestCase):
    def test_read_answer(self):
        self.assertIs(J.read_answer("noul", None, {"q": {"noul": 0.7}}), True)
        self.assertIs(J.read_answer("noul", None, {"q": {"noul": 0.5}}), False)
        self.assertEqual(J.read_answer("choice", OPTS, {"q": {"choice": "fox"}}), 2)
        self.assertEqual(J.read_answer("score", ["a", "b", "c"], {"q": {"probabilities": {"0": 0.1, "1": 0.2, "2": 0.7}}}), 2)


class AskTests(unittest.TestCase):
    def test_ask_sends_the_key_and_the_images_header_and_never_echoes_the_key(self):
        class Resp:
            def __init__(self, data): self._d = data
            def read(self): return self._d
            def __enter__(self): return self
            def __exit__(self, *a): return False

        seen = {}

        def fake_urlopen(req, timeout=0):
            seen["headers"] = {k.lower(): v for k, v in req.header_items()}
            seen["body"] = json.loads(req.data)
            return Resp(json.dumps({"model": "jev-preview", "answers": {"q": {"type": "choice", "choice": "dog"}},
                                    "usage": {"input_tokens": 12, "output_tokens": 1}}).encode())

        from PIL import Image
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "KEY-123456"}), \
                mock.patch("urllib.request.urlopen", fake_urlopen):
            p = pathlib.Path(d) / "x.png"
            Image.new("RGB", (224, 224)).save(p)
            ask = J.build()
            self.assertEqual(ask.info["model_name"], "jev-preview")
            self.assertEqual(ask("state", [str(p)], "choice", "Which?", OPTS), 1)
            self.assertEqual(seen["headers"]["authorization"], "Bearer KEY-123456")
            self.assertEqual(seen["headers"]["typesafe-danger-zone-images"], "true")
            self.assertEqual(ask.info["usage"]["input_tokens"], 12)
            self.assertNotIn("KEY-123456", json.dumps(ask.info))

    def test_missing_key_stops_with_a_clear_message(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TYPESAFE_API_KEY", None)
            with self.assertRaises(SystemExit):
                J.build()


if __name__ == "__main__":
    unittest.main()
