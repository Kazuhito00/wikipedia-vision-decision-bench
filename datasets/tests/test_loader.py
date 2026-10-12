# -*- coding: utf-8 -*-
"""Loader: answer mapping in both languages, single-language questions, text-only state, (version, id) keys, one picture per
question, Japanese review list. Ported from the old wiki_qa/tests/test_dataset.py and extended for v1.
"""
import json
import pathlib
import tempfile
import unittest

import _paths
from datasets import loader
from datasets.tools import list_ja_for_review

IMG = dict(id="img-9001", modality="image", kind="choice", tags=[], difficulty="easy", local_images=["data/images/x.jpg"],
           langs=["en", "ja"],
           en=dict(instr="Which animal?", correct="cat", wrong=["dog", "fox", "horse"]),
           ja=dict(instr="どの動物？", correct="猫", wrong=["犬", "キツネ", "馬"]))


def load(rows, passages=None, version="legacy"):
    """Write rows into a temporary tree and load them through the real loader."""
    with tempfile.TemporaryDirectory() as t:
        q = pathlib.Path(t) / "q"
        (q / version).mkdir(parents=True)
        name = "linked.jsonl" if version == "legacy" else "x.jsonl"
        (q / version / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        p = pathlib.Path(t) / "passages.json"
        p.write_text(json.dumps(passages or {}, ensure_ascii=False), encoding="utf-8")
        return loader.load_cases(version, files=(name,), qdir=q, passages_path=p)


def make_choice(n_wrong, i=0, group="photo"):
    return dict(IMG, id="%s-%04d" % (group, i), group=group,
                en=dict(instr="Q", correct="ok", wrong=["w%d" % k for k in range(n_wrong)]),
                ja=dict(instr="問", correct="正", wrong=["誤%d" % k for k in range(n_wrong)]))


class AnswerMappingTests(unittest.TestCase):
    def test_expected_points_at_the_correct_option_in_both_languages(self):
        """After the shuffle `expected` still names the right option in English and in Japanese (legacy, legacy order)."""
        c = load([IMG])[0]
        self.assertEqual(c["en"]["options"][c["expected"]][0], "cat")
        self.assertEqual(c["ja"]["options"][c["expected"]][0], "猫")
        self.assertEqual(len(c["en"]["options"]), 4)

    def test_legacy_shuffle_is_deterministic_and_spreads_positions(self):
        """The same id gives the same order; over 400 questions every position of the right answer is roughly uniform."""
        self.assertEqual(load([IMG])[0]["expected"], load([IMG])[0]["expected"])
        pos = [c["expected"] for c in load([dict(IMG, id="img-%04d" % i) for i in range(400)])]
        counts = [pos.count(i) for i in range(4)]
        self.assertTrue(all(70 <= n <= 130 for n in counts), counts)

    def test_option_counts_2_to_12_map_the_correct_answer_in_v1(self):
        """v1 (balanced): for every option count the right answer is where `expected` says, in both languages, and each position
        is used by about the same number of questions."""
        for n_opts in range(2, 13):
            rows = [make_choice(n_opts - 1, i) for i in range(n_opts * 5)]
            cases = load(rows, version="v1")
            counts = [sum(1 for c in cases if c["expected"] == p) for p in range(n_opts)]
            self.assertEqual(counts, [5] * n_opts, n_opts)
            for c in cases:
                self.assertEqual(len(c["en"]["options"]), n_opts)
                self.assertEqual(c["en"]["options"][c["expected"]][0], "ok")
                self.assertEqual(c["ja"]["options"][c["expected"]][0], "正")

    def test_yesno_and_score_expected(self):
        """yes/no keeps a bool, score keeps the level index, and neither has shuffled options."""
        yn = dict(IMG, id="img-9100", kind="noul", answer=False, en=dict(instr="s"), ja=dict(instr="文"))
        sc = dict(IMG, id="img-9101", kind="score", answer=2, en=dict(instr="q", levels=list("abcde")), ja=dict(instr="問", levels=list("あいうえお")))
        a, b = load([yn, sc])
        self.assertIs(a["expected"], False)
        self.assertIsNone(a["en"]["options"])
        self.assertEqual((b["expected"], b["ja"]["options"]), (2, list("あいうえお")))


class LanguageAndStateTests(unittest.TestCase):
    def test_single_language_item_has_only_that_language(self):
        """A question that exists in one language only appears only in that language."""
        row = dict(IMG, langs=["ja"])
        del row["en"]
        c = load([row])[0]
        self.assertIn("ja", c)
        self.assertNotIn("en", c)

    def test_text_item_state_is_the_passage_of_its_language(self):
        """A text-only question's state is the lead passage of the article in that language (pinned by revision id)."""
        row = dict(id="txt-9001", modality="text", kind="noul", tags=[], difficulty="easy", langs=["en", "ja"], answer=True,
                   article=dict(en=dict(title="X", revid=1), ja=dict(title="Y", revid=2)),
                   en=dict(instr="X is a thing."), ja=dict(instr="Xは物である。"))
        c = load([row], {"en:1": dict(text="EN passage"), "ja:2": dict(text="JA passage")})[0]
        self.assertEqual((c["en"]["state"], c["ja"]["state"]), ("EN passage", "JA passage"))
        self.assertIs(c["expected"], True)
        with self.assertRaises(FileNotFoundError):                    # no passage -> a clear error, not a silent empty state
            load([row], {})


class VersionKeyTests(unittest.TestCase):
    """(dataset_version, id) is the key of everything: legacy and v1 reuse some id spellings for different questions."""

    def test_the_same_spelling_is_a_different_key_in_legacy_and_v1(self):
        """rsn-0226 exists only in v1 (the 94 reasoning-tagged synthetic questions follow the 225 old ones); rsn-0001 and
        txt-0001 exist in both versions, as different keys. Looking up by id alone would mix up results."""
        legacy = {("legacy", r["id"]) for r in loader.load_rows("legacy")}
        v1 = set(loader.v1_to_legacy())
        self.assertNotIn(("legacy", "rsn-0226"), legacy)
        self.assertIn(("v1", "rsn-0226"), v1)
        self.assertIn(("legacy", "rsn-0001"), legacy)
        self.assertIn(("v1", "rsn-0001"), v1)
        self.assertNotEqual(("legacy", "rsn-0001"), ("v1", "rsn-0001"))
        self.assertNotIn(("legacy", "photo-0001"), legacy)
        with self.assertRaises(ValueError):
            loader.case_key("v3", "x")

    def test_legacy_ids_keep_their_original_spelling(self):
        """legacy is read with its original ids (img-, syn-, rsn-, txt-); v1 ids use the group names."""
        pre = {r["id"].split("-")[0] for r in loader.load_rows("legacy")}
        self.assertEqual(pre, {"img", "syn", "rsn", "txt"})
        self.assertTrue(all(k[0] == "v1" and k[1].split("-")[0] in {"photo", "biz", "rsn", "txt"} for k in loader.v1_to_legacy()))


class OnePictureTests(unittest.TestCase):
    def test_legacy_has_exactly_the_13_known_two_picture_questions(self):
        """legacy is frozen with its 13 two-picture reasoning questions (ids are listed in the id map as 'pending'); no other legacy
        question has more than one picture."""
        two = [r["id"] for r in loader.load_rows("legacy") if len(r.get("images", [])) > 1]
        self.assertEqual(len(two), 13)
        # a two-picture question is "pending" (waits for a one-picture rewrite), "rewritten" (rebuilt as one picture) or "dropped"
        status = {m["legacy_id"]: m["status"] for m in loader.idmap_legacy_v1()}
        self.assertTrue(all(status[i] in ("pending", "rewritten", "dropped") for i in two))

    def test_v1_questions_have_at_most_one_picture(self):
        """v1 rule: one picture per question (no leftover two-picture question). Skipped until v1 questions exist."""
        if not (loader.QDIR / "v1").exists():
            self.skipTest("v1 questions not written yet")
        # the 13 seed rows that were two-picture questions: rebuilt as one picture (12) or dropped; a "pending" one may still wait
        waiting = {m["v1_id"] for m in loader.idmap_legacy_v1() if m["status"] == "pending"}
        for r in loader.load_rows("v1", include_dropped=True):
            if r["id"] in waiting or r.get("review", {}).get("state") == "dropped":
                continue
            self.assertLessEqual(len(r.get("images", [])), 1, r["id"])
            self.assertLessEqual(len(r.get("local_images", [])), 1, r["id"])


class JapaneseReviewListTests(unittest.TestCase):
    def test_review_list_is_produced_for_every_japanese_question(self):
        """The reading aid for 'is this Japanese a machine translation?' lists every question that has a Japanese side
        (id, English and Japanese side by side). It does not judge anything."""
        rows = list_ja_for_review.rows_for_review("legacy")
        self.assertEqual(len(rows), 1962)
        self.assertTrue(all(r[3] and r[4] for r in rows))


if __name__ == "__main__":
    unittest.main()
