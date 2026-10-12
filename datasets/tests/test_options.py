# -*- coding: utf-8 -*-
"""Option order: legacy equals the old loader exactly; balanced is even, deterministic and v1 only; reversal.

    python -m unittest discover -s datasets/tests
"""
import collections
import csv
import importlib.util
import json
import pathlib
import tempfile
import unittest

import _paths
from datasets import loader, options

GOLDEN = list(csv.DictReader(open(loader.MANIFESTS / "legacy_option_order.csv", encoding="utf-8", newline="")))
PASSAGES = _paths.OLD_WIKI_QA / "data" / "passages.json"


class LegacyTests(unittest.TestCase):
    def test_legacy_order_equals_the_golden_data_of_the_old_loader(self):
        """Protects the legacy answer keys: for all 1495 choice questions of legacy the permutation of the options and the position of
        the right answer are the ones the old wikiqa.dataset.load_cases produced (golden data made once from it)."""
        n = 0
        for g in GOLDEN:
            if g["kind"] != "choice":
                continue
            order = options.legacy_order(g["id"], int(g["n_options"]))
            self.assertEqual("-".join(map(str, order)), g["order"], g["id"])
            self.assertEqual(options.expected_of(order), int(g["expected"]), g["id"])
            n += 1
        self.assertEqual(n, 1099 + 247 + 149)

    def test_loader_legacy_cases_equal_the_golden_data(self):
        """Protects the whole legacy case built by the new loader: kind, expected and option order of every non-text case
        (text-only questions need the local Wikipedia passages: next test)."""
        gold = {g["id"]: g for g in GOLDEN}
        rows = {r["id"]: r for r in loader.load_rows("legacy")}
        cases = loader.load_cases("legacy", files=("synthetic.jsonl", "reasoning.jsonl"))
        self.assertEqual(len(cases), 607)
        for c in cases:
            g = gold[c["id"]]
            self.assertEqual((c["version"], c["key"]), ("legacy", ("legacy", c["id"])))
            self.assertEqual(str(c["expected"]), g["expected"], c["id"])
            if c["kind"] == "choice":
                r = rows[c["id"]]
                en = [r["en"]["correct"]] + list(r["en"]["wrong"])
                self.assertEqual("-".join(str(en.index(o[0])) for o in c["en"]["options"]), g["order"], c["id"])

    @unittest.skipUnless((_paths.OLD_WIKI_QA / "wikiqa" / "dataset.py").exists() and PASSAGES.exists(),
                         "old wiki_qa tree / local passages not available")
    def test_all_legacy_cases_equal_the_original_load_cases(self):
        """Direct comparison with the original implementation (only when the old tree exists): all 1962 cases, both languages,
        options, state, expected, kind, tags, difficulty."""
        spec = importlib.util.spec_from_file_location("old_dataset", _paths.OLD_WIKI_QA / "wikiqa" / "dataset.py")
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        total = 0
        for f in loader.LEGACY_FILES:
            a = old.load_cases(_paths.OLD_WIKI_QA, files=(f,))
            b = loader.load_cases("legacy", files=(f,), passages_path=PASSAGES)
            self.assertEqual(len(a), len(b))
            for x, y in zip(a, b):
                self.assertEqual(x["id"], y["id"])
                for k in ("kind", "modality", "tags", "difficulty", "expected"):
                    self.assertEqual(x[k], y[k], (x["id"], k))
                for lang in ("en", "ja"):
                    self.assertEqual(x.get(lang), y.get(lang), (x["id"], lang))
                total += 1
        self.assertEqual(total, 1962)

    def test_legacy_is_deterministic(self):
        """The same id always gives the same order (no hidden state, no dependence on the machine)."""
        self.assertEqual(options.legacy_order("img-0016", 4), options.legacy_order("img-0016", 4))
        self.assertEqual(options.legacy_order("img-0016", 4), [0, 3, 2, 1])      # value fixed by the old loader (golden csv)


class BalancedTests(unittest.TestCase):
    def test_balanced_never_applies_to_legacy(self):
        """legacy results were measured with the legacy order: asking for balanced on legacy must fail, loudly (and v1 never legacy)."""
        with self.assertRaises(ValueError):
            options.order_for("balanced", "legacy", "img-0001", 4, position=0)
        with self.assertRaises(ValueError):
            options.order_for("legacy", "v1", "photo-0001", 4)
        with self.assertRaises(ValueError):
            loader.load_cases("legacy", mode="balanced")

    def test_positions_are_even_per_group_and_option_count(self):
        """Within each (group, n) bucket every position of the right answer occurs floor or ceil of count/n times, whatever the
        number of options (2..12) and the input order."""
        items = []
        for g, n, cnt in (("photo", 4, 1099), ("biz", 4, 208), ("biz", 3, 39), ("rsn", 4, 113), ("rsn", 3, 36), ("txt", 4, 40),
                          ("photo", 2, 7), ("photo", 8, 21), ("biz", 10, 13), ("rsn", 12, 5)):
            items += [(("v1", "%s-%d-%04d" % (g, n, i)), g, n) for i in range(cnt)]
        pos = options.assign_positions(items)
        buckets = collections.defaultdict(list)
        for key, g, n in items:
            buckets[(g, n)].append(pos[key])
        for (g, n), ps in buckets.items():
            counts = [ps.count(p) for p in range(n)]
            self.assertLessEqual(max(counts) - min(counts), 1, (g, n, counts))
        self.assertEqual(pos, options.assign_positions(list(reversed(items))))

    def test_every_option_count_maps_the_correct_answer(self):
        """2..12 options: the order is a permutation, the right answer (item 0) is at the assigned position, and the shuffle is
        the same on every call."""
        for n in range(2, 13):
            for p in range(n):
                o = options.balanced_order("photo-0001", n, p)
                self.assertEqual(sorted(o), list(range(n)))
                self.assertEqual(options.expected_of(o), p)
                self.assertEqual(o, options.balanced_order("photo-0001", n, p))

    def test_special_options_stay_at_the_end_and_are_not_shuffled(self):
        """'None of the above' / cannot be determined (en/ja): pinned to the tail in their original order; the free options are
        balanced among the remaining positions; a right answer that is itself special keeps the tail."""
        self.assertTrue(options.is_special("None of the above"))
        self.assertTrue(options.is_special("該当なし"))
        self.assertTrue(options.is_special("判断できない"))
        self.assertFalse(options.is_special("Nonetheless"))
        en = ["cat", "dog", "fox", "None of the above"]
        ja = ["猫", "犬", "キツネ", "該当なし"]
        pin = options.pinned_indices(en, ja)
        self.assertEqual(pin, [3])
        for p in range(3):
            o = options.balanced_order("x", 4, p, pin)
            self.assertEqual(o[-1], 3)
            self.assertEqual(options.expected_of(o), p)
        o = options.balanced_order("x", 4, 0, [0, 3])         # two specials, the right answer being one of them
        self.assertEqual(o[-2:], [0, 3])
        with self.assertRaises(ValueError):
            options.balanced_order("x", 4, 3, pin)             # position outside the free positions

    def test_balanced_loader_on_synthetic_v1_rows(self):
        """The v1 loader path (positions per group and option count, pinned specials, key = (version, id)) on rows written to
        a temporary v1 directory."""
        rows = []
        for i in range(40):
            rows.append(dict(id="biz-%04d" % i, group="biz", modality="image", kind="choice", tags=[], difficulty="easy",
                             langs=["en", "ja"], local_images=["x.png"],
                             en=dict(instr="Q?", correct="a", wrong=["b", "c", "None of the above"]),
                             ja=dict(instr="Q？", correct="あ", wrong=["い", "う", "該当なし"])))
        with tempfile.TemporaryDirectory() as t:
            q = pathlib.Path(t)
            (q / "v1").mkdir()
            (q / "v1" / "x.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
            cases = loader.load_cases("v1", qdir=q)
        counts = [sum(1 for c in cases if c["expected"] == p) for p in range(3)]       # 40 questions over 3 free positions
        self.assertEqual((sum(counts), max(counts) - min(counts) <= 1), (40, True), counts)
        for c in cases:
            self.assertEqual(c["en"]["options"][3][0], "None of the above")
            self.assertEqual(c["ja"]["options"][3][0], "該当なし")
            self.assertEqual(c["en"]["options"][c["expected"]][0], "a")
            self.assertEqual(c["ja"]["options"][c["expected"]][0], "あ")
            self.assertEqual(c["key"], ("v1", c["id"]))


class ReverseTests(unittest.TestCase):
    def test_reversal_maps_the_expected_position(self):
        """REV: the right answer of the reversed question is at n-1-expected, for every option count."""
        for n in range(2, 13):
            for e in range(n):
                opts = list(range(n))
                self.assertEqual(options.reverse_options(opts)[options.reversed_expected(e, n)], opts[e])


if __name__ == "__main__":
    unittest.main()
