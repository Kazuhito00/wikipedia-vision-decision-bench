# -*- coding: utf-8 -*-
"""Option order: balanced is even and deterministic; reversal.

    python -m unittest discover -s datasets/tests
"""
import collections
import json
import pathlib
import tempfile
import unittest

import _paths  # noqa: F401  (puts the repository root on sys.path)
from datasets import loader, options


class BalancedTests(unittest.TestCase):
    def test_unknown_version_or_mode_raises(self):
        """Only the balanced order of version v1 exists: anything else must fail, loudly."""
        with self.assertRaises(ValueError):
            options.order_for("balanced", "v0", "photo-0001", 4, position=0)
        with self.assertRaises(ValueError):
            options.order_for("shuffle", "v1", "photo-0001", 4)
        with self.assertRaises(ValueError):
            loader.load_cases("v0")

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
