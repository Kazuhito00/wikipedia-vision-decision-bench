# -*- coding: utf-8 -*-
"""v1 files, classification table and image list: groups add up, the tables equal the rows, no Wikipedia text, no pictures."""
import collections
import json
import unittest

import _paths  # noqa: F401  (puts the repository root on sys.path)
from datasets import loader
from datasets.fetch.commons import OK_LICENSE
from datasets.tools import v1_io

M = loader.MANIFESTS


class V1FileTests(unittest.TestCase):
    def test_no_wikipedia_text_in_the_question_files(self):
        """The repository must not carry Wikipedia text: a text-only question that has an article holds the article title and
        revision id (and the sha256 of its evidence), not the passage."""
        for r in loader.load_rows("v1", include_dropped=True):
            self.assertNotIn("evidence", r, r["id"])
            self.assertNotIn("passage", r)
            if r["modality"] == "text" and "article" in r:
                self.assertEqual(set(r["article"]["en"]), {"title", "revid"})
                self.assertTrue(all(len(h) == 64 for h in r["evidence_sha256"]["en"]))

    def test_no_pictures_or_secrets_are_committed(self):
        """No image files and no .env anywhere under datasets/ (pictures and keys are never in the repository)."""
        bad = [p for p in loader.ROOT.joinpath("datasets").rglob("*")
               if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp") or p.name == ".env"]
        self.assertEqual(bad, [])

    def test_rows_carry_no_trace_of_an_older_dataset(self):
        """A v1 row has no legacy_id, and every row has a review block."""
        for r in loader.load_rows("v1", include_dropped=True):
            self.assertNotIn("legacy_id", r, r["id"])
            self.assertIn(r["review"]["state"], v1_io.REVIEW_STATES, r["id"])

    def test_dropped_questions_are_the_ones_the_review_dropped(self):
        allr = loader.load_rows("v1", include_dropped=True)
        kept = loader.load_rows("v1")
        self.assertEqual({r["id"] for r in allr} - {r["id"] for r in kept}, {r["id"] for r in allr if loader.is_dropped(r)})


class ClassificationTests(unittest.TestCase):
    def test_classification_tables_equal_the_rows(self):
        """questions_v1.csv + questions_v1_new_<tag>.csv hold one row per question with the values the rows give (so the tables
        cannot drift from the question files)."""
        cls = loader.classification()
        rows = loader.load_rows("v1", include_dropped=True)
        self.assertEqual(len(cls), len(rows))
        for want in v1_io.classification_rows(rows):
            got = cls[("v1", want["id"])]
            for k in v1_io.Q2_COLS:
                self.assertEqual(str(want[k]), got[k], (want["id"], k))

    def test_classification_values_are_known(self):
        for k, r in loader.classification().items():
            for col in ("source", "image_type", "skill", "answer", "difficulty", "lang", "group"):
                self.assertTrue(r[col], (k, col))
            self.assertIn(r["answer_kind"], {"choice", "yesno", "score"})
            self.assertIn(r["difficulty"], {"easy", "medium", "hard"})

    def test_answer_axis_counts(self):
        """Answer forms of the evaluated questions: choice 2091 / yes-no 537 / score 140."""
        rows = loader.load_rows("v1")
        c = collections.Counter(v1_io.answer_format(r)[1] for r in rows)
        self.assertEqual(c, {"choice": 2091, "yesno": 537, "score": 140})


class ImageListTests(unittest.TestCase):
    def test_every_picture_not_drawn_for_v1_is_in_the_image_list(self):
        """manifests/images_v1.json lists the Commons and earlier drawn pictures with sha256 and licence; Commons pictures are
        CC0 / public domain only; pictures under generated/ are described by build_v1."""
        m = json.loads((M / "images_v1.json").read_text(encoding="utf-8"))
        listed = {e["file"]: e for e in m["images"] + m["rendered"]}
        self.assertEqual((len(m["images"]), len(m["rendered"])), (1021, 477))
        for e in m["images"]:
            self.assertRegex(e["license"], OK_LICENSE, e["file"])
        for r in loader.load_rows("v1"):
            for p in r.get("local_images", []):
                if not p.startswith("generated/"):
                    self.assertIn(p.rsplit("/", 1)[-1], listed, r["id"])


if __name__ == "__main__":
    unittest.main()
