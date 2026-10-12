# -*- coding: utf-8 -*-
"""The v1 seed (make_v1_seed.py): before any review, v1 says exactly what legacy said.

Guards: (1) every v1 row equals its legacy row in content (options, answers, tags, difficulty, pictures); (2) the option order the
models SAW (legacy order made from the legacy id) and the right answer's position still match the golden data of legacy; (3) the id map and
the classification table are used as they are; (4) the build is deterministic and the committed v1 files still equal it for every
question not reviewed yet; (5) no Wikipedia text in the rows.
"""
import unittest

import _paths  # noqa: F401
from datasets import loader, options
from datasets.tools import make_v1_seed, v1_io


class SeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = make_v1_seed.build()
        cls.rows = v1_io.all_rows(cls.built)
        cls.legacy = {r["id"]: r for r in loader.load_rows("legacy")}

    def test_counts_and_ids(self):
        """1962 rows: photo 1268 / biz 288 / rsn 319 / txt 87, unique v1 ids, id prefix = group, legacy ids each once."""
        self.assertEqual({g: len(r) for g, r in self.built.items()}, {"photo": 1268, "biz": 288, "rsn": 319, "txt": 87})
        self.assertEqual(len({r["id"] for r in self.rows}), 1962)
        self.assertEqual(sorted(r["legacy_id"] for r in self.rows), sorted(self.legacy))
        self.assertTrue(all(r["id"].split("-")[0] == r["group"] for r in self.rows))

    def test_content_equals_legacy(self):
        """Every field of the legacy row (except id and the old `source` label) is unchanged; the unreviewed review block is added."""
        for r in self.rows:
            legacy = self.legacy[r["legacy_id"]]
            for k, v in legacy.items():
                if k in ("id", "source", "version"):
                    continue
                self.assertEqual(r[k], v, (r["id"], k))
            self.assertEqual(r["review"], {"state": "unreviewed", "history": []})
            self.assertEqual(r["lang"], "both")

    def test_answer_key_keeps_the_legacy_meaning(self):
        """`answer` of yes/no and score rows is still the right VALUE (the loader reads it); the axis is `answer_format`."""
        for r in self.rows:
            self.assertEqual(r.get("answer"), self.legacy[r["legacy_id"]].get("answer"))
            self.assertEqual(r["answer_format"], v1_io.answer_format(r)[0])

    def test_option_order_and_expected_equal_the_legacy_golden_data(self):
        """The order made from the legacy id equals manifests/legacy_option_order.csv, so what a reviewer sees is what the models saw."""
        gold = {g["id"]: g for g in loader._read_csv(loader.MANIFESTS / "legacy_option_order.csv")}
        n = 0
        for r in self.rows:
            if r["kind"] != "choice":
                continue
            order = options.legacy_order(r["legacy_id"], 1 + len(r["en"]["wrong"]))
            g = gold[r["legacy_id"]]
            self.assertEqual("-".join(map(str, order)), g["order"], r["id"])
            self.assertEqual(options.expected_of(order), int(g["expected"]), r["id"])
            n += 1
        self.assertEqual(n, 1495)

    def test_classification_comes_from_the_manifest(self):
        cls = {c["id"]: c for c in loader._read_csv(loader.MANIFESTS / "questions_legacy.csv")}
        for r in self.rows:
            c = cls[r["legacy_id"]]
            self.assertEqual((r["source"], r["image_type"], r["skill"], r["answer_format"]),
                             (c["source"], c["image_type"], c["skill"], c["answer"]))

    def test_no_passage_text(self):
        """Text-only rows keep evidence_sha256 only; the passages are never in the rows."""
        for r in self.built["txt"]:
            self.assertNotIn("evidence", r)
            self.assertIn("evidence_sha256", r)

    def test_build_is_deterministic(self):
        self.assertEqual(make_v1_seed.build(), self.built)

    def test_committed_files_equal_the_seed_for_unreviewed_rows(self):
        """A row that nobody reviewed is still the seed row (reviewed rows are allowed to differ)."""
        committed = v1_io.load_v1()
        if not committed:
            self.skipTest("v1 files not written")
        seed = {r["id"]: r for r in self.rows}
        for r in v1_io.all_rows(committed):
            if r["review"]["state"] == "unreviewed":
                self.assertEqual(r, seed[r["id"]], r["id"])
        self.assertEqual(sum(len(v) for v in committed.values()), 1962)

    def test_loader_reads_v1(self):
        """The loader accepts the v1 files (balanced order, yes/no and score values intact)."""
        if not (loader.QDIR / "v1").exists():
            self.skipTest("v1 files not written")
        cases = loader.load_cases("v1", files=("photo.jsonl", "biz.jsonl", "rsn.jsonl"), include_dropped=True)
        self.assertEqual(len(cases), 1875)                               # the files keep every question; the default skips dropped ones
        by = {c["id"]: c for c in cases}
        self.assertIsInstance(by["biz-0015"]["expected"], bool)          # yes/no keeps its truth value
        self.assertEqual(by["biz-0077"]["expected"], 0)                  # score keeps its level index


if __name__ == "__main__":
    unittest.main()
