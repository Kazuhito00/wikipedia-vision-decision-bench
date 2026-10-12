# -*- coding: utf-8 -*-
"""apply_review.py: validation of the reviewers' lines and the effect on v1 rows / id map.

Guards: bad lines are rejected (unknown id, schema violations, right answer among the wrong ones, duplicates, en/ja count mismatch,
a fix that does not fit the question kind, two-picture question kept as it is, id outside its batch, id twice); a valid fix changes the
row, recomputes answer_format and writes a history entry; the verdicts set review.state and the id-map status as documented; applying
the same output twice gives byte-identical files (idempotent).
"""
import copy
import pathlib
import tempfile
import unittest

import _paths  # noqa: F401
from datasets.tools import apply_review as ar
from datasets.tools import v1_io


def row(i="photo-0001", kind="choice", group="photo", images=1, **kw):
    r = dict(id=i, legacy_id="img-0001", group=group, source="commons-article", image_type="photo-animal", skill="recognition",
             lang="both", modality="image", kind=kind, tags=["classify"], difficulty="easy", langs=["en", "ja"],
             local_images=["data/images/x%d.jpg" % k for k in range(images)], review={"state": "unreviewed", "history": []})
    if kind == "choice":
        r.update(en=dict(instr="Which animal?", correct="sheep", wrong=["goat", "pig", "rabbit"]),
                 ja=dict(instr="どの動物？", correct="羊", wrong=["ヤギ", "豚", "ウサギ"]), answer_format="choice:4")
    elif kind == "noul":
        r.update(en=dict(instr="It is a sheep"), ja=dict(instr="羊である"), answer=True, answer_format="yesno")
    else:
        r.update(en=dict(instr="How full?", levels=["low", "mid", "high"]), ja=dict(instr="どのくらい？", levels=["低", "中", "高"]),
                 answer=1, answer_format="score:3")
    r.update(kw)
    return r


def line(i="photo-0001", verdict="ok", **kw):
    d = dict(id=i, verdict=verdict, issues=[], reason="because")
    d.update(kw)
    d["_file"], d["_line"] = "batch_photo_01.jsonl", 1
    return d


def errors(e, r):
    return ar.validate_entry(e, r)


class ValidationTests(unittest.TestCase):
    def test_ok_line_is_valid(self):
        self.assertEqual(errors(line(reason=""), row()), [])

    def test_unknown_id_and_verdict(self):
        self.assertTrue(errors(line("photo-9999"), None))
        self.assertTrue(errors(line(verdict="maybe"), row()))

    def test_reason_required_unless_ok(self):
        self.assertTrue(errors(line(verdict="drop", reason=""), row()))
        self.assertEqual(errors(line(verdict="drop"), row()), [])

    def test_fix_only_with_verdict_fix_and_not_empty(self):
        self.assertTrue(errors(line(fix={"difficulty": "hard"}), row()))                  # ok + fix
        self.assertTrue(errors(line(verdict="fix", fix={}), row()))
        self.assertTrue(errors(line(verdict="fix"), row()))

    def test_unknown_key_wrong_type_wrong_value(self):
        for fx in ({"colour": "x"}, {"instr_en": 5}, {"difficulty": "tough"}, {"image_type": "none"}, {"skill": "magic"},
                   {"answer": "sixteen"}, {"wrong_en": "goat"}):
            self.assertTrue(errors(line(verdict="fix", fix=fx), row()), fx)

    def test_right_answer_must_not_be_among_the_wrong_ones(self):
        self.assertTrue(errors(line(verdict="fix", fix={"wrong_en": ["Sheep ", "pig", "rabbit"]}), row()))     # case/space-insensitive

    def test_duplicates_empty_and_count_mismatch(self):
        self.assertTrue(errors(line(verdict="fix", fix={"wrong_en": ["goat", "goat", "pig"]}), row()))
        self.assertTrue(errors(line(verdict="fix", fix={"wrong_en": ["goat", "", "pig"]}), row()))
        self.assertTrue(errors(line(verdict="fix", fix={"wrong_en": ["goat", "pig"]}), row()))                  # ja still has 3
        self.assertEqual(errors(line(verdict="fix", fix={"wrong_en": ["goat", "pig"], "wrong_ja": ["ヤギ", "豚"]}), row()), [])

    def test_kind_specific_keys(self):
        self.assertTrue(errors(line(verdict="fix", fix={"truth": False}), row()))
        self.assertTrue(errors(line(verdict="fix", fix={"correct_en": "x"}), row(kind="noul")))
        self.assertEqual(errors(line(verdict="fix", fix={"truth": False}), row(kind="noul")), [])
        self.assertTrue(errors(line(verdict="fix", fix={"score": 3}), row(kind="score")))                      # out of range
        self.assertTrue(errors(line(verdict="fix", fix={"levels_en": ["a", "b"]}), row(kind="score")))         # count mismatch
        self.assertEqual(errors(line(verdict="fix", fix={"score": 2}), row(kind="score")), [])

    def test_two_picture_question_cannot_be_ok_or_fix(self):
        r = row(images=2)
        self.assertTrue(errors(line(), r))
        self.assertTrue(errors(line(verdict="fix", fix={"difficulty": "hard"}), r))
        self.assertEqual(errors(line(verdict="rewrite_1image"), r), [])
        self.assertEqual(errors(line(verdict="drop"), r), [])

    def test_text_group_keeps_its_classification(self):
        r = row("txt-0001", group="txt", image_type="none", skill="text-comprehension")
        self.assertTrue(errors(line("txt-0001", "fix", fix={"image_type": "chart"}), r))
        self.assertEqual(errors(line("txt-0001", "fix", fix={"difficulty": "hard"}), r), [])

    def test_batch_membership_and_duplicates(self):
        rows = {"photo-0001": row(), "photo-0002": row("photo-0002")}
        self.assertEqual(ar.validate([line()], rows, {"batch_photo_01": {"photo-0001"}}), [])
        self.assertTrue(ar.validate([line("photo-0002")], rows, {"batch_photo_01": {"photo-0001"}}))          # not in the batch
        self.assertTrue(ar.validate([line(), line()], rows, {}))                                                # twice


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.by = {"photo": [row("photo-0001"), row("photo-0002", kind="noul"), row("photo-0003"), row("photo-0004", images=2)]}
        self.idmap = [dict(legacy_id="img-%d" % i, v1_id="photo-%04d" % i, group_legacy="wikipedia", group_v1="photo", status="kept",
                           review_state="unreviewed", change_note="") for i in (1, 2, 3, 4)]
        self.idmap[3]["status"] = "pending"
        self.entries = [
            line("photo-0001", "fix", fix={"wrong_en": ["goat", "pig", "rabbit", "cow"], "wrong_ja": ["ヤギ", "豚", "ウサギ", "牛"],
                                           "answer": "choice:9"}, issues=["weak distractor"], reason="add a 5th option"),
            line("photo-0002", "ok"), line("photo-0003", "drop", reason="not decided by the picture"),
            line("photo-0004", "rewrite_1image", reason="use the left picture only")]

    def run_apply(self, by=None, idmap=None):
        by = by if by is not None else self.by
        idmap = idmap if idmap is not None else self.idmap
        return ar.apply_entries(by, idmap, copy.deepcopy(self.entries), "2026-10-11")

    def test_effects(self):
        S = self.run_apply()
        r1, r2, r3, r4 = self.by["photo"]
        self.assertEqual(r1["review"]["state"], "changed")
        self.assertEqual(r1["en"]["wrong"], ["goat", "pig", "rabbit", "cow"])
        self.assertEqual(r1["answer_format"], "choice:5")                         # recomputed, not the reviewer's choice:9
        self.assertTrue(any("choice:9" in w for w in S["warnings"]))
        self.assertEqual(r1["review"]["history"][0]["date"], "2026-10-11")
        self.assertEqual(r1["review"]["history"][0]["why"], "add a 5th option")
        self.assertIn("wrong_en", r1["review"]["history"][0]["what"])
        self.assertEqual([r["review"]["state"] for r in (r2, r3, r4)], ["reviewed", "dropped", "reviewed"])
        self.assertEqual([m["status"] for m in self.idmap], ["rewritten", "kept", "dropped", "pending"])
        self.assertEqual([m["review_state"] for m in self.idmap], ["reviewed"] * 4)
        self.assertTrue(self.idmap[3]["change_note"].startswith("rewrite_1image"))
        self.assertEqual((S["verdicts"]["fix"], S["verdicts"]["drop"], S["changed_rows"]), (1, 1, 1))

    def test_idempotent_in_memory(self):
        self.run_apply()
        snap = copy.deepcopy((self.by, self.idmap))
        self.run_apply()
        self.assertEqual((self.by, self.idmap), snap)
        self.run_apply()
        self.assertEqual((self.by, self.idmap), snap)

    def test_idempotent_through_files(self):
        """Write, apply, write, apply again: the files are byte-identical."""
        with tempfile.TemporaryDirectory() as t:
            d = pathlib.Path(t)
            self.run_apply()
            v1_io.save_v1(self.by, d)
            v1_io.save_idmap(self.idmap, d)
            first = (d / "photo.jsonl").read_bytes(), (d / "idmap_legacy_v1.csv").read_bytes()
            by2 = v1_io.load_v1(d)
            map2 = v1_io.load_idmap(d)
            self.run_apply(by2, map2)
            v1_io.save_v1(by2, d)
            v1_io.save_idmap(map2, d)
            self.assertEqual(first, ((d / "photo.jsonl").read_bytes(), (d / "idmap_legacy_v1.csv").read_bytes()))

    def test_state_does_not_go_backwards(self):
        self.run_apply()
        ar.apply_entries(self.by, self.idmap, [line("photo-0003", "ok")], "2026-10-12")
        self.assertEqual(self.by["photo"][2]["review"]["state"], "dropped")

    def test_noop_fix_does_not_mark_changed(self):
        e = line("photo-0003", "fix", fix={"difficulty": "easy"})              # same as now
        S = ar.apply_entries(self.by, self.idmap, [e], "2026-10-11")
        self.assertEqual(self.by["photo"][2]["review"]["state"], "reviewed")
        self.assertEqual(S["noop"], ["photo-0003"])

    def test_classification_table_rows(self):
        rows = v1_io.classification_rows(self.by["photo"][:3])
        self.assertEqual([r["answer"] for r in rows], ["choice:4", "yesno", "choice:4"])
        self.assertEqual(rows[1]["answer_n"], "")

    def test_report_lists_the_fixes(self):
        S = self.run_apply()
        md = ar.report(S, 4, 4, 0, False)
        self.assertIn("photo-0001", md)
        self.assertIn("dry run", md)
        self.assertIn("wrong_en", md)


if __name__ == "__main__":
    unittest.main()
