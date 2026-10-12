# -*- coding: utf-8 -*-
"""export_review_batches.py: batching, the old-result statistics and the question records.

Guards: batches are consecutive and nearly equal; priority flags (all_wrong / majority_wrong / no_results) are computed from the
answered slots only; a choice question is shown in the order the models saw (legacy order of the legacy id) with the right index;
a text-only question needs its passage; picture paths are absolute and must exist. The full export over the real data is run
only when the old logs, the passages and the 224 px pictures are on this machine (otherwise skipped).
"""
import json
import pathlib
import tempfile
import unittest

import _paths
from datasets import options
from datasets.tools import export_review_batches as ex
from datasets.tools import v1_io


def choice_row(i="photo-0001", legacy="img-0016"):
    return dict(id=i, legacy_id=legacy, group="photo", kind="choice", modality="image", difficulty="easy", tags=["animal"], source="x",
                image_type="photo-animal", skill="recognition", answer_format="choice:4", langs=["en", "ja"],
                local_images=["data/images/abc.jpg"], review={"state": "unreviewed", "history": []},
                en=dict(instr="Q", correct="sheep", wrong=["goat", "pig", "rabbit"]),
                ja=dict(instr="問", correct="羊", wrong=["ヤギ", "豚", "ウサギ"]))


class UnitTests(unittest.TestCase):
    def test_chunks(self):
        parts = ex.chunks(list(range(1268)), 21)
        self.assertEqual(sum(map(len, parts)), 1268)
        self.assertLessEqual(max(map(len, parts)) - min(map(len, parts)), 1)
        self.assertEqual([x for p in parts for x in p], list(range(1268)))

    def test_priority_flags(self):
        res = {(m, l, "q1"): False for m in ex.MODELS for l in ("en", "ja")}
        self.assertEqual(ex.stats_for("q1", res, "photo")["priority"], "all_wrong")
        res = {(m, l, "q1"): (m != "qev") for m in ex.MODELS for l in ("en", "ja")}
        res[("openjev", "en", "q1")] = False
        self.assertEqual(ex.stats_for("q1", res, "photo")["priority"], "normal")
        res = {(m, l, "q1"): (l == "en") for m in ex.MODELS for l in ("en", "ja")}
        s = ex.stats_for("q1", res, "photo")
        self.assertEqual((s["priority"], s["wrong_ja"], s["answered"]), ("majority_wrong", 10, 20))
        self.assertEqual(ex.stats_for("q1", {}, "photo")["priority"], "no_results")
        self.assertEqual(ex.stats_for("q1", {("openjev", "en", "q1"): False}, "txt")["priority"], "no_results")

    def test_choice_record_uses_the_legacy_order_of_the_legacy_id(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            (d / "abc.jpg").write_bytes(b"x")
            rec = ex.question_record(choice_row(), {}, {}, [d], d, d / "extra")
        order = options.legacy_order("img-0016", 4)
        items = ["sheep", "goat", "pig", "rabbit"]
        self.assertEqual(rec["en"]["options_as_shown"], [items[i] for i in order])
        self.assertEqual(rec["en"]["options_as_shown"][rec["en"]["expected_index"]], "sheep")
        self.assertEqual(rec["ja"]["options_as_shown"][rec["ja"]["expected_index"]], "羊")
        self.assertEqual(rec["images"], [str(d / "abc.jpg")])
        self.assertTrue(pathlib.Path(rec["images"][0]).is_absolute())

    def test_text_question_needs_its_passage(self):
        r = choice_row("txt-0001", "txt-0001")
        r.update(modality="text", group="txt", local_images=[], article={"en": {"title": "T", "revid": 1}, "ja": {"title": "題", "revid": 2}})
        r.pop("images", None)
        rec = ex.question_record(r, {}, {"en:1": {"text": "body"}, "ja:2": {"text": "本文"}}, [], pathlib.Path("."), pathlib.Path("."))
        self.assertEqual((rec["en"]["state"], rec["ja"]["state"], rec["images"]), ("body", "本文", []))
        with self.assertRaises(FileNotFoundError):
            ex.question_record(r, {}, {}, [], pathlib.Path("."), pathlib.Path("."))


class FullExportTests(unittest.TestCase):
    def test_real_export(self):
        """33 batches, 1962 unique ids, every picture path exists (needs the local data; skipped otherwise)."""
        logs, passages = _paths.OLD_EVAL_COMMON, _paths.OLD_WIKI_QA / "data" / "passages.json"
        px = [p for p in (_paths.ROOT / "work" / "px224", _paths.OLD_WIKI_QA / "work" / "px224", _paths.ROOT / "work" / "generated" / "px224") if p.exists()]
        if not (logs / "results_w").exists() or not passages.exists() or not px or not v1_io.v1_files()[0].exists():
            self.skipTest("old logs / passages / 224 px pictures / v1 files not on this machine")
        with tempfile.TemporaryDirectory() as t:
            out = pathlib.Path(t)
            index = ex.export(out, logs, passages, px, _paths.OLD_WIKI_QA)
            self.assertEqual({g: sum(1 for b in index if b["group"] == g) for g in v1_io.GROUPS}, ex.BATCH_COUNT)
            ids, n_img = [], 0
            for b in index:
                batch = json.loads((out / (b["batch"] + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(batch["n_questions"], len(batch["questions"]))
                self.assertLessEqual(len(batch["questions"]), 64)
                for q in batch["questions"]:
                    ids.append(q["id"])
                    self.assertEqual(bool(q["images"]), q["group"] != "txt")
                    for p in q["images"]:
                        n_img += 1
                        self.assertTrue(pathlib.Path(p).is_absolute() and pathlib.Path(p).exists(), p)
            self.assertEqual(len(ids), 1962)
            self.assertEqual(len(set(ids)), 1962)
            # one picture per question, except the 13 legacy two-picture ones: 12 of them were rebuilt as one picture (gen_v1_rewrite.py)
            self.assertEqual(n_img, sum(len(r.get("local_images", [])) for r in v1_io.all_rows(v1_io.load_v1())))


if __name__ == "__main__":
    unittest.main()
