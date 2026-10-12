# -*- coding: utf-8 -*-
"""Offline tests of check / fetch / refresh (the Commons API is replaced by a fake: no network, no WIKIQA_CONTACT needed).

    uv run python -m unittest discover -s datasets/fetch/tests -t .

Each test says in its docstring what it protects.
"""
import hashlib
import io
import json
import os
import pathlib
import tempfile
import unittest
import zipfile

from datasets.fetch import commons, fetch_images, http
from datasets.fetch import inspect_images as I


def imageinfo(sha1="aaa", lic="Public domain", author="Ann", desc="a picture", thumb="http://t/x.jpg", ts=None):
    ii = {"sha1": sha1, "size": 1, "width": 10, "height": 10, "mime": "image/jpeg", "descriptionurl": "https://commons.example/File:X",
          "thumburl": thumb,
          "extmetadata": {"LicenseShortName": {"value": lic}, "Artist": {"value": '<a href="u">%s</a>' % author},
                          "ImageDescription": {"value": desc}}}
    if ts:
        ii["timestamp"] = ts
    return ii


class FakeCommons:
    """Answers imageinfo queries from a dict title -> imageinfo | None (missing) | ("redirect", new title, imageinfo)."""

    def __init__(self, files):
        self.files, self.calls = files, []

    def __call__(self, base, params, use_cache=True, post=False):
        titles = params["titles"].split("|")
        self.calls.append(dict(n=len(titles), use_cache=use_cache, post=post, iiurlwidth=params.get("iiurlwidth")))
        pages, redirects = {}, []
        for i, t in enumerate(titles):
            v = self.files[t]
            if v is None:
                pages[str(-i - 1)] = {"title": t, "missing": ""}
            elif isinstance(v, tuple):
                redirects.append({"from": t, "to": v[1]})
                pages[str(i + 1)] = {"title": v[1], "imageinfo": [v[2]]}
            else:
                pages[str(i + 1)] = {"title": t, "imageinfo": [v]}
        return {"query": {"redirects": redirects, "pages": pages}}


def manifest_entry(n, **kw):
    ii = commons.describe(imageinfo(**kw))
    return dict(file="f%d.jpg" % n, title="File:T%d.jpg" % n, source="commons", license=ii["license"], author=ii["author"],
                source_url=ii["source_url"], sha1=ii["sha1"], timestamp=None, description_sha256=ii["description_sha256"],
                sha256_original=None, sha256_224=None, question_ids=["q%d" % n])


class Check(unittest.TestCase):
    def test_batches_of_50_metadata_only(self):
        """check asks for 50 titles per request, never uses the cache (it must see the CURRENT state) and downloads nothing."""
        files = {"File:T%d.jpg" % n: imageinfo() for n in range(120)}
        api = FakeCommons(files)
        got = commons.image_info(list(files), api=api, use_cache=False)
        self.assertEqual([c["n"] for c in api.calls], [50, 50, 20])
        self.assertTrue(all(not c["use_cache"] for c in api.calls))
        self.assertEqual(len(got), 120)

    def test_each_state(self):
        """The five states of the policy are told apart, with the right question lists."""
        m = {"manifest_version": "legacy", "images": [manifest_entry(i) for i in range(6)]}
        files = {
            "File:T0.jpg": imageinfo(),                                         # ok
            "File:T1.jpg": None,                                                # broken: gone
            "File:T2.jpg": ("redirect", "File:New.jpg", imageinfo()),           # broken: renamed
            "File:T3.jpg": imageinfo(sha1="bbb"),                               # replaced
            "File:T4.jpg": imageinfo(lic="CC BY-SA 4.0"),                       # license changed
            "File:T5.jpg": imageinfo(author="Bob", desc="another text"),        # author / description changed
        }
        res = I.check(m, api=FakeCommons(files))
        states = {it["file"]: it["state"] for it in res["items"]}
        self.assertEqual(res["counts"]["ok"], 1)
        self.assertEqual(states, {"f1.jpg": "broken", "f2.jpg": "broken", "f3.jpg": "replaced", "f4.jpg": "license", "f5.jpg": "meta"})
        self.assertEqual(res["invalid_questions"], ["q1", "q2", "q4"])           # picture gone or no longer CC0 / PD
        self.assertEqual(res["affected_questions"], ["q3"])                      # evaluated on the old picture

    def test_sha1_alone_when_timestamp_unknown(self):
        """legacy has no timestamps: an image whose sha1 is unchanged is 正常 even though Commons now reports a timestamp."""
        e = manifest_entry(0)
        state, _, _ = I.classify(e, commons.image_info(["File:T0.jpg"], api=FakeCommons({"File:T0.jpg": imageinfo(ts="2026-01-01T00:00:00Z")}))["File:T0.jpg"])
        self.assertEqual(state, "ok")
        e["timestamp"] = "2025-01-01T00:00:00Z"
        state, diffs, _ = I.classify(e, commons.image_info(["File:T0.jpg"], api=FakeCommons({"File:T0.jpg": imageinfo(ts="2026-01-01T00:00:00Z")}))["File:T0.jpg"])
        self.assertEqual(state, "replaced")
        self.assertTrue(any(d.startswith("timestamp") for d in diffs))

    def test_license_regex(self):
        """Only CC0 / public domain pass the license test."""
        for ok in ("CC0", "Public domain", "Public Domain", "PD-old", "cc-zero"):
            self.assertTrue(commons.OK_LICENSE.match(ok), ok)
        for bad in ("CC BY-SA 4.0", "CC BY 2.0", "GFDL", "Attribution", ""):
            self.assertFalse(commons.OK_LICENSE.match(bad), bad)

    def test_contact_is_required(self):
        """Nothing goes to Wikimedia without WIKIQA_CONTACT (User-Agent policy)."""
        old = os.environ.pop("WIKIQA_CONTACT", None)
        try:
            with self.assertRaises(SystemExit):
                http.user_agent()
            os.environ["WIKIQA_CONTACT"] = "someone@example.org"
            self.assertIn("someone@example.org", http.user_agent())
        finally:
            os.environ.pop("WIKIQA_CONTACT", None)
            if old is not None:
                os.environ["WIKIQA_CONTACT"] = old


class Refresh(unittest.TestCase):
    def setUp(self):
        self.m = {"manifest_version": "legacy", "images": [manifest_entry(i) for i in range(4)]}
        files = {"File:T0.jpg": imageinfo(author="Bob"), "File:T1.jpg": imageinfo(lic="CC BY 2.0"), "File:T2.jpg": None,
                 "File:T3.jpg": imageinfo(sha1="ccc")}
        self.res = I.check(self.m, api=FakeCommons(files))

    def test_plan_does_not_touch_the_manifest(self):
        """refresh's plan is only a list: the manifest object is unchanged until apply_plan, and replaced pictures need --accept-replaced."""
        before = json.dumps(self.m, sort_keys=True)
        plan = I.plan_refresh(self.m, self.res)
        self.assertEqual(json.dumps(self.m, sort_keys=True), before)
        self.assertEqual({p["action"] for p in plan}, {"update", "exclude"})            # T3 (replaced) is not in the plan
        self.assertEqual(len(I.plan_refresh(self.m, self.res, accept_replaced=True)), 4)

    def test_apply_updates_author_and_excludes(self):
        """apply_plan writes the new author, marks the license-changed and the broken picture as excluded, and logs the refresh."""
        I.apply_plan(self.m, I.plan_refresh(self.m, self.res), self.res["checked_at"])
        im = {e["file"]: e for e in self.m["images"]}
        self.assertEqual(im["f0.jpg"]["author"], "Bob")
        self.assertIn("ライセンス変更", im["f1.jpg"]["excluded"])
        self.assertIn("リンク切れ", im["f2.jpg"]["excluded"])
        self.assertNotIn("excluded", im["f3.jpg"])
        self.assertEqual(self.m["refresh_log"][0]["changes"], 3)

    def test_check_file_roundtrip(self):
        """A check is written under results/checks/ with its date, counts per state and the disabled questions."""
        with tempfile.TemporaryDirectory() as d:
            p = I.write_check(self.res, pathlib.Path(d))
            back = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(back["counts"]["broken"], 1)
            self.assertEqual(back["invalid_questions"], ["q1", "q2"])
            self.assertEqual(I.latest_check(pathlib.Path(d)), p)


def jpeg(color, size=(300, 200)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "JPEG")
    return buf.getvalue()


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Fetch(unittest.TestCase):
    def test_fetch_states_and_224(self):
        """fetch tells a matching original, a re-rendered thumbnail (sha1 same) and a replaced file (sha1 changed) apart, and shrinks to 224 px."""
        good, rerender, replaced = jpeg("red"), jpeg("green"), jpeg("blue")
        entries = []
        for n, data in enumerate((good, jpeg("white"), jpeg("black"))):
            e = manifest_entry(n)
            e["sha256_original"] = sha(data)
            e["sha256_224"] = sha(fetch_images.shrink(data, 224))
            entries.append(e)
        m = {"manifest_version": "legacy", "source_width_px": 640, "input_px": 224, "images": entries}
        files = {"File:T0.jpg": imageinfo(thumb="http://t/0"), "File:T1.jpg": imageinfo(thumb="http://t/1"),
                 "File:T2.jpg": imageinfo(sha1="zzz", thumb="http://t/2")}
        served = {"http://t/0": good, "http://t/1": rerender, "http://t/2": replaced}
        api = FakeCommons(files)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            rep = fetch_images.fetch_commons(m, api=api, download=lambda url, **k: served[url], images_dir=d / "img", px_dir=d / "px")
            self.assertEqual(api.calls[0]["iiurlwidth"], 640)
            self.assertEqual(rep["original"], dict(match=1, thumbnail_rerendered=1, replaced=1, missing=0, cached=0))
            self.assertEqual(rep["px224"]["match"], 1)
            self.assertTrue((d / "px" / "f0.jpg").exists())
            self.assertFalse((d / "img" / "f2.jpg").exists())                  # the replaced file is not kept as if it were the old one
            from PIL import Image
            with Image.open(d / "px" / "f0.jpg") as im:
                self.assertLessEqual(max(im.size), 224)

    def test_release_zip_is_verified(self):
        """Release zips are checked member by member against the manifest: a wrong sha256 or an unknown file is refused."""
        a, b = jpeg("red"), jpeg("blue")
        m = {"images": [dict(manifest_entry(0), sha256_224=sha(a)), dict(manifest_entry(1), sha256_224=sha(b))], "rendered": []}
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            with zipfile.ZipFile(d / "images-224px.zip", "w") as z:
                z.writestr("ATTRIBUTION.md", "x")
                z.writestr("f0.jpg", a)
                z.writestr("f1.jpg", jpeg("black"))                              # wrong content
                z.writestr("zzz.jpg", a)                                         # not in the manifest
            rep = fetch_images.fetch_release(m, d, images_dir=d / "img", px_dir=d / "px")["images-224px.zip"]
            self.assertEqual((rep["ok"], rep["wrong_sha256"], rep["unknown"]), (1, ["f1.jpg"], ["zzz.jpg"]))
            self.assertTrue((d / "px" / "f0.jpg").exists() and not (d / "px" / "f1.jpg").exists())


if __name__ == "__main__":
    unittest.main()
