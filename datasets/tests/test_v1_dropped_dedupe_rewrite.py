# -*- coding: utf-8 -*-
"""v1 follow-up: (1) the loader skips dropped v1 questions (and never touches legacy), (2) the cross-batch duplicate finder, (3) the
one-picture rebuild of the 12 two-picture questions (the right answer is derived from the scene and must match the picture)."""
import copy
import json
import pathlib
import tempfile
import unittest

import _paths  # noqa: F401  (puts the repository root first on sys.path)
from datasets import loader
from datasets.synthetic import gen_v1_rewrite as rw
from datasets.tools import dedupe_v1, v1_io


def row(i, instr="Q", correct="ok", wrong=("a", "b", "c"), state="reviewed", group="photo", img=None):
    return dict(id="%s-%04d" % (group, i), group=group, modality="image", kind="choice", tags=[], difficulty="easy",
                local_images=[img or "data/x%d.jpg" % i], langs=["en", "ja"],
                en=dict(instr=instr, correct=correct, wrong=list(wrong)),
                ja=dict(instr="問", correct="正", wrong=["誤1", "誤2", "誤3"][:len(wrong)]),
                review=dict(state=state, history=[]))


class DroppedAreSkippedTests(unittest.TestCase):
    """Dropped v1 questions (review.state == dropped, or id map status dropped) are not evaluated; legacy is never filtered."""

    def _load(self, rows, idmap=None, **kw):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            (root / "q" / "v1").mkdir(parents=True)
            text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
            (root / "q" / "v1" / "photo.jsonl").write_text(text, encoding="utf-8")
            if idmap is not None:
                (root / "m").mkdir()
                v1_io.write_csv(root / "m" / "idmap_legacy_v1.csv", v1_io.IDMAP_COLS, idmap)
            return loader.load_cases("v1", files=("photo.jsonl",), qdir=root / "q", passages_path=root / "p.json",
                                     manifests=(root / "m") if idmap is not None else None, **kw)

    def test_review_state_dropped_is_skipped(self):
        rows = [row(1), row(2, state="dropped"), row(3, state="changed")]
        self.assertEqual([c["id"] for c in self._load(rows)], ["photo-0001", "photo-0003"])
        self.assertEqual(len(self._load(rows, include_dropped=True)), 3)

    def test_idmap_status_dropped_is_skipped(self):
        rows = [row(1), row(2)]
        im = [dict(legacy_id="img-1", v1_id="photo-0001", status="kept"), dict(legacy_id="img-2", v1_id="photo-0002", status="dropped")]
        self.assertEqual([c["id"] for c in self._load(rows, im)], ["photo-0001"])

    def test_positions_are_balanced_over_the_kept_questions(self):
        """A dropped question does not take part in the balanced assignment: 4 kept 4-option questions use each position once."""
        rows = [row(i) for i in range(1, 5)] + [row(i, state="dropped") for i in range(5, 12)]
        self.assertEqual(sorted(c["expected"] for c in self._load(rows)), [0, 1, 2, 3])

    def test_real_v1_default_excludes_every_dropped_row(self):
        if not (loader.QDIR / "v1").exists():
            self.skipTest("v1 not written")
        allr = loader.load_rows("v1", include_dropped=True)
        kept = loader.load_rows("v1")
        dropped = {r["id"] for r in allr if r["review"]["state"] == "dropped"} | loader.dropped_ids()
        self.assertEqual({r["id"] for r in kept}, {r["id"] for r in allr} - dropped)
        self.assertEqual(len(loader.load_v1_cases(["photo", "biz", "rsn"])), len([r for r in kept if r["group"] != "txt"]))
        with self.assertRaises(ValueError):
            loader.load_v1_cases(["nope"])

    def test_legacy_is_not_filtered(self):
        self.assertEqual(len(loader.load_rows("legacy")), 1962)


class DedupeTests(unittest.TestCase):
    """Same picture bytes AND same question AND same right answer = duplicate (later id dropped); a shared picture with another
    question is not."""

    @staticmethod
    def sig(mapping):
        return lambda r: mapping.get(r["id"])

    def test_exact_duplicate_later_id_is_the_duplicate(self):
        a, b = row(1), row(2)
        pairs = dedupe_v1.find_duplicates([b, a], self.sig({"photo-0001": ("h",), "photo-0002": ("h",)}))
        self.assertEqual(pairs, [("photo-0001", "photo-0002", "exact")])

    def test_only_the_wrong_set_differs(self):
        a, b = row(1), row(2, wrong=("a", "b", "z"))
        pairs = dedupe_v1.find_duplicates([a, b], self.sig({"photo-0001": ("h",), "photo-0002": ("h",)}))
        self.assertEqual(pairs, [("photo-0001", "photo-0002", "wrong-set-differs")])

    def test_same_picture_different_question_or_answer_is_not_a_duplicate(self):
        a, b, c = row(1), row(2, instr="Another question"), row(3, correct="other")
        s = self.sig({r["id"]: ("h",) for r in (a, b, c)})
        self.assertEqual(dedupe_v1.find_duplicates([a, b, c], s), [])

    def test_different_picture_or_dropped_or_missing_picture_is_ignored(self):
        a, b, c = row(1), row(2), row(3, state="dropped")
        s = self.sig({"photo-0001": ("h",), "photo-0002": ("g",), "photo-0003": ("h",)})
        self.assertEqual(dedupe_v1.find_duplicates([a, b, c], s), [])
        self.assertEqual(dedupe_v1.find_duplicates([a, b], self.sig({"photo-0001": ("h",)})), [])

    def test_yesno_truth_matters(self):
        def yn(i, truth):
            r = row(i)
            r.update(kind="noul", answer=truth)
            r["en"] = dict(instr="There is a cat")
            r["ja"] = dict(instr="猫がいる")
            return r
        s = self.sig({"photo-0001": ("h",), "photo-0002": ("h",), "photo-0003": ("h",)})
        self.assertEqual(dedupe_v1.find_duplicates([yn(1, True), yn(2, False), yn(3, True)], s),
                         [("photo-0001", "photo-0003", "exact")])

    def test_apply_is_idempotent_and_records_history_and_idmap(self):
        by = {"photo": [row(1), row(2)]}
        im = [dict(legacy_id="a", v1_id="photo-0001", status="kept"), dict(legacy_id="b", v1_id="photo-0002", status="kept")]
        pairs = [("photo-0001", "photo-0002", "exact")]
        self.assertEqual(dedupe_v1.apply_pairs(by, im, pairs, "2026-10-11"), 1)
        once = copy.deepcopy((by, im))
        self.assertEqual(dedupe_v1.apply_pairs(by, im, pairs, "2026-10-11"), 0)
        self.assertEqual((by, im), once)
        r2 = by["photo"][1]
        self.assertEqual(r2["review"]["state"], "dropped")
        self.assertEqual(r2["review"]["history"], [{"date": "2026-10-11", "what": "drop", "why": "duplicate of photo-0001 (cross-batch)"}])
        self.assertEqual(im[1]["status"], "dropped")
        self.assertEqual(by["photo"][0]["review"]["state"], "reviewed")           # the earlier one stays

    def test_picture_signature_is_the_file_hash(self):
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            (d / "x1.jpg").write_bytes(b"same")
            (d / "x2.jpg").write_bytes(b"same")
            (d / "x3.jpg").write_bytes(b"other")

            def sig(i):
                return dedupe_v1.image_signature(row(i, img="data/x%d.jpg" % i), [d])
            self.assertEqual(sig(1), sig(2))
            self.assertNotEqual(sig(1), sig(3))
            self.assertIsNone(sig(9))

    def test_real_v1_has_no_remaining_duplicate_and_the_recorded_ones_are_dropped(self):
        by = v1_io.load_v1()
        dirs = [p for p in dedupe_v1.DEFAULT_PX224 if p.exists()]
        if len(dirs) < 2:
            self.skipTest("224 px pictures not on this machine")
        rows = {r["id"]: r for r in v1_io.all_rows(by)}
        for kept, dup, _, _ in dedupe_v1.recorded_pairs(by):
            self.assertEqual(rows[dup]["review"]["state"], "dropped")
            self.assertNotEqual(rows[kept]["review"]["state"], "dropped")
        self.assertEqual(dedupe_v1.find_duplicates(list(rows.values()), lambda r: dedupe_v1.image_signature(r, dirs)), [])


class RewriteTests(unittest.TestCase):
    """The 12 rebuilt questions: the right answer comes from the scene specification and the picture shows exactly that scene."""

    def test_before_after_picture_matches_its_spec_and_the_answer(self):
        for qid in rw.BA_IDS:
            spec = rw.before_after_spec(qid)
            read = rw.read_before_after(rw.draw_before_after(spec))
            self.assertEqual(read["before"], spec["before"], qid)
            self.assertEqual(read["after"], spec["after"], qid)
            gone = [x for x in read["before"] if x not in read["after"]]
            self.assertEqual(gone, [rw.answer_before_after(spec)], qid)
            self.assertEqual(len(set(spec["before"])), 4)

    def test_bar_pair_picture_shows_the_values_and_the_answer(self):
        sides = []
        for qid in rw.BAR_IDS:
            spec = rw.bar_pair_spec(qid)
            ymax = max(spec["left"] + spec["right"])
            read = rw.read_bar_pair(rw.draw_bar_pair(spec), ymax)
            self.assertEqual(read, spec, qid)                      # bar heights on the common scale give the printed values back
            side = rw.answer_bars(spec)
            self.assertEqual(side, "left" if sum(read["left"]) > sum(read["right"]) else "right")
            self.assertGreaterEqual(abs(sum(spec["left"]) - sum(spec["right"])), 6)
            sides.append(side)
        self.assertEqual(sides.count("left"), 4)                   # legacy had 6 of 8 "first"; now 4 / 4

    def test_the_specs_are_the_legacy_values(self):
        """Totals the reviewer recorded for the legacy two-picture items, and the right answers of the legacy before-after rows."""
        want = {"rsn-0188": (56, 36), "rsn-0189": (35, 51), "rsn-0190": (55, 45), "rsn-0191": (41, 27), "rsn-0192": (73, 45)}
        for qid, tot in want.items():
            s = rw.bar_pair_spec(qid)
            self.assertEqual(sorted((sum(s["left"]), sum(s["right"]))), sorted(tot), qid)
        legacy = {r["id"]: r for r in loader.load_rows("legacy")}
        for qid in rw.BA_IDS:
            self.assertEqual(rw.shape_name_en(rw.answer_before_after(rw.before_after_spec(qid))), legacy[qid]["en"]["correct"], qid)

    def test_rows_are_one_picture_with_matching_answer_en_and_ja(self):
        if not (loader.QDIR / "v1").exists():
            self.skipTest("v1 not written")
        rows = {r["id"]: r for r in v1_io.load_v1()["rsn"]}
        for qid in rw.BA_IDS + rw.BAR_IDS:
            new, spec, img, _ = rw.rebuild_row(rows[qid], "2026-10-11")
            self.assertEqual(len(new["local_images"]), 1)
            self.assertEqual(len(new["en"]["wrong"]), len(new["ja"]["wrong"]))
            self.assertNotIn("state", new["en"])
            self.assertEqual(rows[qid], dict(new, review=rows[qid]["review"]), qid)        # the file holds the rebuilt row
            if qid in rw.BAR_IDS:
                side = rw.answer_bars(spec)
                self.assertEqual((new["en"]["correct"], new["ja"]["correct"]), (side, {"left": "左", "right": "右"}[side]))
            else:
                gone = rw.answer_before_after(spec)
                self.assertEqual((new["en"]["correct"], new["ja"]["correct"]), (rw.shape_name_en(gone), rw._ja_shape(gone)))
                self.assertNotIn(new["en"]["correct"], new["en"]["wrong"])

    def test_apply_is_idempotent(self):
        by = v1_io.load_v1()
        im = v1_io.load_idmap()
        with tempfile.TemporaryDirectory() as t:
            rw.apply_rewrite(by, im, "2026-10-11", pathlib.Path(t))
            once = copy.deepcopy((by, im))
            rw.apply_rewrite(by, im, "2026-10-11", pathlib.Path(t))
            self.assertEqual((by, im), once)
            self.assertTrue((pathlib.Path(t) / "px224" / "rsn-0188.png").exists())
        st = {m["v1_id"]: m["status"] for m in im}
        self.assertTrue(all(st[i] == "rewritten" for i in rw.BA_IDS + rw.BAR_IDS))
        self.assertTrue(all(len(r["local_images"]) <= 1 for r in by["rsn"] if r["id"] in rw.BA_IDS + rw.BAR_IDS))


if __name__ == "__main__":
    unittest.main()
