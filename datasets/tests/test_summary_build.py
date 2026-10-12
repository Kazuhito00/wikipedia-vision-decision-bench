# -*- coding: utf-8 -*-
"""build_dataset_summary.py: the statistics add up, every question appears once, the --public page has no pictures / cards,
and no Wikipedia passage reaches any page. DOM-free: the numbers are computed in Python; the embedded script gets `node --check`."""
import collections
import json
import pathlib
import re
import shutil
import subprocess
import unittest

import _paths
from datasets.tools import build_dataset_summary as B
from datasets.tools import v1_io

ROWS = v1_io.all_rows(v1_io.load_v1()) if v1_io.V1DIR.exists() else []
IDMAP = v1_io.load_idmap() if ROWS else []


def build(public):
    pics = {r["id"]: ["dataset_summary_files/img/%s" % pathlib.Path(p).name for p in r.get("local_images", [])] for r in ROWS}
    return B.build_data(ROWS, IDMAP, B.read_review_out(B.REVIEW_OUT), {}, pics, public=public)


@unittest.skipUnless(ROWS, "v1 questions not present")
class SummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full, cls.pub = build(False), build(True)

    def test_every_question_once(self):
        ids = [r["id"] for r in self.full["records"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {r["id"] for r in ROWS})

    def test_stats_sum_to_total(self):
        for scope, n in (("all", len(ROWS)), ("active", sum(1 for r in ROWS if r["review"]["state"] != "dropped"))):
            S = self.full["stats"][scope]
            self.assertEqual(S["total"], n)
            for k, items in S["dims"].items():
                self.assertEqual(sum(c for _, c in items), n, k)
            for k, cr in S["cross"].items():
                self.assertEqual(sum(map(sum, cr["cells"])), n, k)
            yn = sum(1 for r in ROWS if r["kind"] == "noul" and (scope == "all" or r["review"]["state"] != "dropped"))
            self.assertEqual(sum(S["yesno"]["total"]), yn)
            for mode in ("legacy", "balanced"):
                self.assertEqual(sum(sum(p["counts"]) for p in S["pos"][mode]),
                                 sum(1 for r in ROWS if r["kind"] == "choice" and (scope == "all" or r["review"]["state"] != "dropped")))
            for m in S["models"]:
                self.assertEqual(m["total"][0], sum(v[0] for v in m["cells"].values()))

    def test_idmap_totals(self):
        I = self.full["idmap_stats"]
        self.assertEqual(I["total"], len(IDMAP))
        self.assertEqual(sum(r["legacy"] for r in I["rows"]), len(IDMAP))

    def test_public_has_no_pictures_or_cards(self):
        html = B.render(self.pub)
        self.assertNotIn("records", self.pub)
        for bad in (B.FILES_DIR, ".jpg", ".png", "img/"):
            self.assertNotIn(bad, html)
        q = ROWS[0]["en"]["instr"]
        self.assertNotIn(q, html)

    def test_no_passage_text(self):
        html = B.render(self.full)
        p = next((q for q in (B.ROOT / "work" / "passages.json", B.JEV / "wiki_qa" / "data" / "passages.json") if q.exists()), None)
        if p is None:
            self.skipTest("passages.json absent")
        for v in list(json.loads(p.read_text(encoding="utf-8")).values())[:300]:
            self.assertNotIn(v["text"][:60], html)
        for r in self.full["records"]:
            if r["g"] == "txt":
                self.assertEqual(set(r["txt"]), {"en", "ja"})
                self.assertNotIn("s", r["en"])

    def test_script_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node absent")
        for data in (self.full, self.pub):
            js = pathlib.Path(_paths.ROOT / "work" / "_summary_check.js")
            js.parent.mkdir(exist_ok=True)
            js.write_text(B.extract_script(B.render(data)), encoding="utf-8")
            r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_issue_tag(self):
        self.assertEqual(B.issue_tag("Duplicate (photo-0012)"), "duplicate")
        self.assertEqual(B.issue_tag("needs_new_image_type: astro"), "needs_new_image_type")


if __name__ == "__main__":
    unittest.main()
