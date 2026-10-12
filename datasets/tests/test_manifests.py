# -*- coding: utf-8 -*-
"""Frozen legacy, classification and id map: every legacy id exactly once, groups add up, no Wikipedia text in the repository."""
import ast
import collections
import hashlib
import json
import unittest

import _paths
from datasets import loader, taxonomy

M = loader.MANIFESTS


class FrozenV1Tests(unittest.TestCase):
    def test_frozen_files_are_unchanged(self):
        """legacy stays legacy: the sha256 of each frozen file equals the value recorded when it was frozen (manifests/legacy_freeze.json)."""
        info = json.loads((M / "legacy_freeze.json").read_text(encoding="utf-8"))
        for name, d in info["files"].items():
            p = loader.QDIR / "legacy" / name
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), d["frozen_sha256"], name)
            self.assertEqual(len(loader.read_jsonl(p)), d["rows"], name)

    def test_legacy_has_1962_questions_in_three_files(self):
        """1355 (1268 pictures + 87 text-only) + 382 + 225 = 1962, ids unique."""
        rows = loader.load_rows("legacy")
        self.assertEqual(len(rows), 1962)
        self.assertEqual(len({r["id"] for r in rows}), 1962)
        self.assertEqual(collections.Counter(r["id"].split("-")[0] for r in rows), {"img": 1268, "txt": 87, "syn": 382, "rsn": 225})

    def test_no_wikipedia_text_in_the_question_files(self):
        """The repository must not carry Wikipedia text: no `evidence` strings in the frozen rows (only their sha256) and none
        in the items_text_*.py sources; a text-only question holds the article title and revision id, not the passage."""
        for p in (loader.QDIR / "legacy").glob("*.jsonl"):
            for r in loader.read_jsonl(p):
                self.assertNotIn("evidence", r, r["id"])
                self.assertNotIn("passage", r)
                if r["modality"] == "text":
                    self.assertEqual(set(r["article"]["en"]), {"title", "revid"})
                    self.assertTrue(all(len(h) == 64 for h in r["evidence_sha256"]["en"]))
        for p in loader.QDIR.glob("items_text_*.py"):
            src = p.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("tchoice", "tnoul"):
                    idx = (7, 8) if node.func.id == "tchoice" else (4, 5)
                    for i in idx:
                        self.assertEqual(ast.literal_eval(node.args[i]), [], (p.name, node.lineno))

    def test_no_pictures_or_secrets_are_committed(self):
        """No image files and no .env anywhere under datasets/ (pictures and keys are never in the repository)."""
        bad = [p for p in loader.ROOT.joinpath("datasets").rglob("*")
               if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp") or p.name == ".env"]
        self.assertEqual(bad, [])


class IdMapTests(unittest.TestCase):
    def setUp(self):
        self.idmap = loader.idmap_legacy_v1()
        self.legacy = loader.load_rows("legacy")

    def test_every_legacy_id_appears_exactly_once(self):
        """The id map is a bijection on the legacy ids: each of the 1962 ids once, no id missing, none invented; v1 ids unique."""
        ids = [m["legacy_id"] for m in self.idmap]
        self.assertEqual(sorted(ids), sorted(r["id"] for r in self.legacy))
        self.assertEqual(len(set(ids)), 1962)
        self.assertEqual(len({m["v1_id"] for m in self.idmap}), 1962)

    def test_new_groups_have_the_planned_sizes(self):
        """photo 797 + 471 = 1268, biz 382 - 94 = 288, rsn 225 + 94 = 319, txt 87; v1 id prefix = group."""
        c = collections.Counter(m["group_v1"] for m in self.idmap)
        self.assertEqual(c, {"photo": 1268, "biz": 288, "rsn": 319, "txt": 87})
        for m in self.idmap:
            self.assertEqual(m["v1_id"].split("-")[0], m["group_v1"])
        old = collections.Counter(m["group_legacy"] for m in self.idmap)
        self.assertEqual(old, {"wikipedia": 797, "expansion": 471, "synthetic": 382, "reasoning": 225, "text": 87})
        moved = [m for m in self.idmap if m["group_legacy"] == "synthetic" and m["group_v1"] == "rsn"]
        self.assertEqual(len(moved), 94)

    def test_id_map_matches_the_classification_rules(self):
        """The csv equals what taxonomy.py derives from the frozen rows (so the table cannot drift from the rules)."""
        by = {m["legacy_id"]: m for m in self.idmap}
        for r in self.legacy:
            self.assertEqual((by[r["id"]]["group_legacy"], by[r["id"]]["group_v1"]), (taxonomy.old_group(r), taxonomy.new_group(r)))

    def test_id_map_has_status_and_review_columns(self):
        """v1 is the polished legacy: each row carries status (kept / rewritten / dropped / pending), review_state, change_note."""
        self.assertEqual(list(self.idmap[0]), ["legacy_id", "v1_id", "group_legacy", "group_v1", "status", "review_state", "change_note"])
        self.assertLessEqual({m["status"] for m in self.idmap}, {"kept", "rewritten", "dropped", "pending"})

    def test_legacy_to_v1_and_back_use_versioned_keys(self):
        """The loader maps ('legacy', id) <-> ('v1', id); both directions are inverse."""
        f, b = loader.legacy_to_v1(), loader.v1_to_legacy()
        self.assertEqual(len(f), 1962)
        for k, v in f.items():
            self.assertEqual((k[0], v[0]), ("legacy", "v1"))
            self.assertEqual(b[v], k)


class ClassificationTests(unittest.TestCase):
    def test_classification_csv_covers_every_legacy_question_with_known_values(self):
        """questions_legacy.csv has one row per legacy question with source / image_type / skill / answer / difficulty / lang filled."""
        cls = loader.classification("legacy")
        self.assertEqual(len(cls), 1962)
        for k, r in cls.items():
            for col in ("source", "image_type", "skill", "answer", "difficulty", "lang", "group"):
                self.assertTrue(r[col], (k, col))
            self.assertIn(r["source"], {"commons-article", "commons-category", "rendered", "none"})
            self.assertIn(r["answer_kind"], {"choice", "yesno", "score"})
            self.assertIn(r["difficulty"], {"easy", "medium", "hard"})
            self.assertEqual(r["lang"], "both")

    def test_classification_csv_equals_the_rules(self):
        """The committed csv is exactly what taxonomy.classify() gives today (rerun tools/make_manifests.py after a rule change)."""
        cls = loader.classification("legacy")
        for r in loader.load_rows("legacy"):
            want = taxonomy.classify(r)
            got = cls[("legacy", r["id"])]
            for k, v in want.items():
                self.assertEqual(str(v), got[k], (r["id"], k))

    def test_answer_axis_counts(self):
        """Answer forms of legacy: choice 4 = 1416, choice 3 = 78, choice 2 = 1, score 5 = 49, yes/no = 418."""
        c = collections.Counter(r["answer"] for r in loader.classification("legacy").values())
        self.assertEqual(c, {"choice:4": 1416, "choice:3": 78, "choice:2": 1, "score:5": 49, "yesno": 418})


if __name__ == "__main__":
    unittest.main()
