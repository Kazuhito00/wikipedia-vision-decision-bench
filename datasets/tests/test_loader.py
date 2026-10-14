# -*- coding: utf-8 -*-
"""Loader: answer mapping in both languages, single-language questions, text-only state, (version, id) keys, one picture per
question.
"""
import json
import pathlib
import tempfile
import unittest

import _paths  # noqa: F401  (puts the repository root on sys.path)
from datasets import loader

IMG = dict(id="photo-9001", modality="image", kind="choice", tags=[], difficulty="easy", local_images=["data/images/x.jpg"],
           langs=["en", "ja"],
           en=dict(instr="Which animal?", correct="cat", wrong=["dog", "fox", "horse"]),
           ja=dict(instr="どの動物？", correct="猫", wrong=["犬", "キツネ", "馬"]))


def load(rows, passages=None):
    """Write rows into a temporary tree and load them through the real loader."""
    with tempfile.TemporaryDirectory() as t:
        q = pathlib.Path(t) / "q"
        (q / "v1").mkdir(parents=True)
        name = "x.jsonl"
        (q / "v1" / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        p = pathlib.Path(t) / "passages.json"
        p.write_text(json.dumps(passages or {}, ensure_ascii=False), encoding="utf-8")
        return loader.load_cases("v1", files=(name,), qdir=q, passages_path=p)


def make_choice(n_wrong, i=0, group="photo"):
    return dict(IMG, id="%s-%04d" % (group, i), group=group,
                en=dict(instr="Q", correct="ok", wrong=["w%d" % k for k in range(n_wrong)]),
                ja=dict(instr="問", correct="正", wrong=["誤%d" % k for k in range(n_wrong)]))


class AnswerMappingTests(unittest.TestCase):
    def test_expected_points_at_the_correct_option_in_both_languages(self):
        """After the shuffle `expected` still names the right option in English and in Japanese."""
        c = load([IMG])[0]
        self.assertEqual(c["en"]["options"][c["expected"]][0], "cat")
        self.assertEqual(c["ja"]["options"][c["expected"]][0], "猫")
        self.assertEqual(len(c["en"]["options"]), 4)

    def test_the_order_is_deterministic(self):
        """The same id gives the same order on every load."""
        self.assertEqual(load([IMG])[0]["expected"], load([IMG])[0]["expected"])
        self.assertEqual(load([IMG])[0]["en"]["options"], load([IMG])[0]["en"]["options"])

    def test_option_counts_2_to_12_map_the_correct_answer(self):
        """Balanced order: for every option count the right answer is where `expected` says, in both languages, and each position
        is used by about the same number of questions."""
        for n_opts in range(2, 13):
            rows = [make_choice(n_opts - 1, i) for i in range(n_opts * 5)]
            cases = load(rows)
            counts = [sum(1 for c in cases if c["expected"] == p) for p in range(n_opts)]
            self.assertEqual(counts, [5] * n_opts, n_opts)
            for c in cases:
                self.assertEqual(len(c["en"]["options"]), n_opts)
                self.assertEqual(c["en"]["options"][c["expected"]][0], "ok")
                self.assertEqual(c["ja"]["options"][c["expected"]][0], "正")

    def test_yesno_and_score_expected(self):
        """yes/no keeps a bool, score keeps the level index, and neither has shuffled options."""
        yn = dict(IMG, id="photo-9100", kind="noul", answer=False, en=dict(instr="s"), ja=dict(instr="文"))
        sc = dict(IMG, id="photo-9101", kind="score", answer=2, en=dict(instr="q", levels=list("abcde")), ja=dict(instr="問", levels=list("あいうえお")))
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
    def test_keys_carry_the_version(self):
        """(dataset_version, id) is the key of everything; an unknown version is an error."""
        self.assertEqual(loader.case_key("v1", "photo-0001"), ("v1", "photo-0001"))
        with self.assertRaises(ValueError):
            loader.case_key("v3", "x")
        c = load([IMG])[0]
        self.assertEqual((c["version"], c["key"]), ("v1", ("v1", "photo-9001")))

    def test_v1_ids_use_the_group_names(self):
        ids = [r["id"] for r in loader.load_rows("v1")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.split("-")[0] in {"photo", "biz", "rsn", "txt"} for i in ids))


class OnePictureTests(unittest.TestCase):
    def test_v1_questions_have_at_most_one_picture(self):
        """v1 rule: one picture per question."""
        for r in loader.load_rows("v1"):
            self.assertLessEqual(len(r.get("images", [])), 1, r["id"])
            self.assertLessEqual(len(r.get("local_images", [])), 1, r["id"])


class V1CountTests(unittest.TestCase):
    def test_v1_has_2768_evaluated_questions(self):
        """2768 evaluated questions (135 dropped rows stay in the files, but are skipped); the groups add up."""
        rows = loader.load_rows("v1")
        self.assertEqual(len(rows), 2768)
        self.assertEqual(len(loader.load_rows("v1", include_dropped=True)), 2768 + 135)
        counts = {g: sum(1 for r in rows if r["group"] == g) for g in loader.V1_GROUPS}
        self.assertEqual(counts, {"photo": 1476, "biz": 646, "rsn": 460, "txt": 186})
        self.assertEqual(len(loader.load_v1_cases(strict_passages=False)), 2768)


if __name__ == "__main__":
    unittest.main()
