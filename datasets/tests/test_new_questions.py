# -*- coding: utf-8 -*-
"""New v1 questions: the common receiving end (id ranges, validator, loader, balanced options, runner checks, review round trip).

Guards: the id-range table is consistent; the validator accepts the documented sample rows and rejects each kind of mistake with a
specific message; new rows load like base rows and never move a base answer position; options work for 2..16 options and 3/7/10 score
levels; the runner's limit check and dry run cover every v1 question; a full round trip (write -> validate -> manifests -> load ->
balanced -> review batch -> apply -> summary) works on a temporary directory and touches nothing else. Real data is never written.
"""
import collections
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

import _paths
import _newq_samples as S
from datasets import loader, newq, options
from datasets.tools import apply_review as ar
from datasets.tools import build_dataset_summary as B
from datasets.tools import export_review_batches as ex
from datasets.tools import v1_io
from datasets.tools import validate_new as V
from runner import cases as rc

REAL = v1_io.V1DIR
NOTES = _paths.ROOT / "datasets" / "NOTES.md"


def tmp_v1(base=True):
    """A temporary v1 question directory (a copy of the base files when ``base``) plus its manifests directory and image root."""
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "q" / "v1").mkdir(parents=True)
    (d / "m").mkdir()
    (d / "img" / "generated").mkdir(parents=True)
    if base:
        for g in v1_io.GROUPS:
            shutil.copyfile(REAL / ("%s.jsonl" % g), d / "q" / "v1" / ("%s.jsonl" % g))
        shutil.copyfile(v1_io.MANIFESTS / "idmap_legacy_v1.csv", d / "m" / "idmap_legacy_v1.csv")
        shutil.copyfile(v1_io.MANIFESTS / "questions_v1.csv", d / "m" / "questions_v1.csv")
    return d


def png(path: pathlib.Path, size=(224, 224), color=None):
    """A tiny picture; the colour comes from the file name unless given (so two rows never share the same picture bytes by accident)."""
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(path.name.encode()).digest()
    Image.new("RGB", size, color or (h[0], h[1], h[2])).save(path)


def tag_of(row) -> str:
    return next(t for t in newq.RANGES if newq.in_reserved_range(t, row["id"]))


def write_new(d: pathlib.Path, tag: str, rows: list):
    v1_io.write_jsonl(d / "q" / "v1" / newq.new_filename(tag), rows)


def check(d, tags=None, pictures=True):
    return V.validate(d / "q" / "v1", tags, [d / "img"], check_images=pictures)


def sample_dir(parent_picture=False):
    """Temp dir with the five sample rows written to their tags and the pictures of the rendered samples (``parent_picture``: also the
    picture the photo variant reuses from photo-0001)."""
    d = tmp_v1()
    if parent_picture:
        png(d / "img" / S.PARENT_PICTURE)
    by = collections.defaultdict(list)
    for r in S.sample_rows():
        by[tag_of(r)].append(r)
        for p in r["local_images"]:
            if p.startswith("generated/"):
                png(d / "img" / p)
    for t, rows in by.items():
        write_new(d, t, rows)
    return d


class TableTests(unittest.TestCase):
    def test_range_table_is_consistent(self):
        """No two reservations overlap, all lie in 1000..9999 (0001..0999 stays the legacy-derived band), spare ranges included."""
        self.assertEqual(newq.check_table(), [])
        self.assertEqual(newq.tag_of_filename("new_photo_variants.jsonl"), "photo_variants")
        self.assertIsNone(newq.tag_of_filename("photo.jsonl"))
        self.assertTrue(newq.in_reserved_range("rendered", "rsn-1199"))
        self.assertFalse(newq.in_reserved_range("rendered", "rsn-1200"))
        self.assertFalse(newq.in_reserved_range("rendered", "photo-1001"))

    def test_reserved_ids_do_not_collide_with_the_existing_v1_ids(self):
        ids = {r["id"] for r in v1_io.all_rows(v1_io.load_v1(REAL))}
        for tag, rg in newq.RANGES.items():
            for g, (lo, hi) in rg.items():
                self.assertFalse({newq.format_id(g, n) for n in range(lo, hi + 1)} & ids, (tag, g))


class ManyOptionsTests(unittest.TestCase):
    def test_balanced_positions_for_2_to_16_options(self):
        """Every option count 2..16: the right answer's positions differ by at most one, the order is a permutation with the right answer
        where assigned, the same on every call; a special option stays at the tail (also with 10+ options)."""
        for n in range(2, 17):
            keys = [(("v1", "biz-%04d" % i), "biz", n) for i in range(3 * n + 1)]
            pos = options.assign_positions([(k, b, f) for k, b, f in keys])
            counts = collections.Counter(pos.values())
            self.assertLessEqual(max(counts.values()) - min(counts.get(p, 0) for p in range(n)), 1, n)
            self.assertEqual(pos, options.assign_positions(list(reversed(keys))))
            for (_, qid), p in ((k[0], pos[k[0]]) for k in keys[:5]):
                o = options.balanced_order(qid, n, p)
                self.assertEqual((sorted(o), options.expected_of(o)), (list(range(n)), p))
                self.assertEqual(o, options.balanced_order(qid, n, p))
            if n >= 3:                                              # the last option is special
                pin = [n - 1]
                o = options.balanced_order("biz-0001", n, 0, pin)
                self.assertEqual((o[-1], sorted(o)), (n - 1, list(range(n))))

    def test_special_options_at_the_tail_in_a_12_option_question(self):
        en = ["a%d" % i for i in range(11)] + ["None of the above"]
        ja = ["あ%d" % i for i in range(11)] + ["上記のいずれでもない"]
        pin = options.pinned_indices(en, ja)
        self.assertEqual(pin, [11])
        orders = options.v1_orders([dict(id="rsn-1001", group="rsn", kind="choice", langs=["en", "ja"],
                                         en=dict(correct=en[0], wrong=en[1:]), ja=dict(correct=ja[0], wrong=ja[1:]))])
        self.assertEqual(orders["rsn-1001"][-1], 11)
        self.assertEqual(sorted(orders["rsn-1001"]), list(range(12)))

    def test_new_japanese_wordings_of_none_of_the_above_are_special(self):
        for t in ("上記のいずれでもない", "上記以外", "この中にはない", "いずれも当てはまらない", "どれも当てはまらない", "該当なし", "判断できない"):
            self.assertTrue(options.is_special(t), t)
        self.assertFalse(options.is_special("上記の図"))
        self.assertTrue(options.is_special("None of the listed"))

    def test_correct_answer_that_is_special_does_not_use_a_slot(self):
        """Rows whose right answer is 'none of the above' sit at the tail and are left out of the balancing, so the others stay even."""
        rows = []
        for i in range(40):
            special = i % 4 == 0
            rows.append(dict(id="biz-%04d" % (1001 + i), group="biz", kind="choice", langs=["en", "ja"],
                             en=dict(correct="None of the above" if special else "a", wrong=["b", "c", "a" if special else "None of the above"]),
                             ja=dict(correct="該当なし" if special else "あ", wrong=["い", "う", "あ" if special else "該当なし"])))
        orders = options.v1_orders(rows)
        free = [options.expected_of(orders[r["id"]]) for r in rows if r["en"]["correct"] == "a"]
        counts = [free.count(p) for p in range(3)]
        self.assertEqual((sum(counts), max(counts) - min(counts) <= 1), (30, True), counts)
        for r in rows:
            if r["en"]["correct"] != "a":
                self.assertEqual(options.expected_of(orders[r["id"]]), 3)

    def test_new_rows_never_move_a_base_row_and_keep_the_union_even(self):
        base = [(("v1", "photo-%04d" % (100 * n + i)), "photo", n) for n in (2, 4, 8, 12) for i in range(n * 5 + 3 + n)]
        new = [(("v1", "photo-%04d" % (2001 + i)), "photo", n) for i, n in enumerate([2, 4, 4, 8, 8, 8, 12] * 6)]
        self.assertEqual(len({k for k, _, _ in base + new}), len(base + new))
        alone = options.assign_positions(base)
        both = options.assign_positions_with_base(base, new)
        for k, _, _ in base:
            self.assertEqual(alone[k], both[k])
        self.assertEqual(both, options.assign_positions_with_base(list(reversed(base)), list(reversed(new))))
        for n in (2, 4, 8, 12):
            counts = [sum(1 for k, _, f in base + new if f == n and both[k] == p) for p in range(n)]
            self.assertLessEqual(max(counts) - min(counts), 1, (n, counts))

    def test_score_levels_3_7_10(self):
        """Levels are ordinal and never reordered; suggest_score_answers spreads the right level evenly for 3 / 5 / 7 / 10 levels."""
        for n in (3, 5, 7, 10):
            ids = ["rsn-%04d" % (1001 + i) for i in range(4 * n + 3)]
            s1 = options.suggest_score_answers(ids, n)
            self.assertEqual(s1, options.suggest_score_answers(list(reversed(ids)), n))
            counts = [list(s1.values()).count(p) for p in range(n)]
            self.assertLessEqual(max(counts) - min(counts), 1, (n, counts))
            self.assertTrue(all(0 <= v < n for v in s1.values()))

    def test_option_labels(self):
        labs = options.option_labels(16)
        self.assertEqual((labs[0], labs[9], labs[15], len(set(labs))), ("A", "J", "P", 16))


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tmp_v1()
        for name in ("biz-1001", "rsn-1001", "biz-2001"):
            png(cls.d / "img" / "generated" / (name + ".png"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, ignore_errors=True)

    def errs(self, row, tag=None, pictures=True):
        write_new(self.d, tag or tag_of(row), [row])
        rep = check(self.d, pictures=pictures)
        (self.d / "q" / "v1" / newq.new_filename(tag or tag_of(row))).unlink()
        return rep.errors

    def assertRejected(self, row, needle, **kw):
        errs = self.errs(row, **kw)
        self.assertTrue(any(needle in e for e in errs), (needle, errs))

    def test_the_samples_are_valid(self):
        d = sample_dir()
        try:
            rep = check(d)
            self.assertEqual(rep.errors, [])
            self.assertEqual(sum(rep.counts.values()), 5)
            self.assertTrue(any("not on this machine" in w for w in rep.warnings))      # the reused parent picture is not in the temp root
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_notes_print_exactly_the_samples(self):
        text = NOTES.read_text(encoding="utf-8")
        m = re.search(r"<!-- samples:begin -->\s*```[a-z]*\n(.*?)```\s*<!-- samples:end -->", text, re.S)
        self.assertIsNotNone(m, "NOTES.md must hold the sample rows between the samples:begin / samples:end markers")
        self.assertEqual(m.group(1).strip().splitlines(), S.sample_lines())

    def test_id_rules(self):
        r = S.rendered_yesno()
        r["id"] = "biz-1400"
        self.assertRejected(r, "outside the range reserved for tag", tag="rendered")
        r = S.rendered_yesno()
        r["id"] = "rsn-1001"
        self.assertRejected(r, "id prefix 'rsn' does not match group 'biz'")
        r = S.rendered_yesno()
        r["id"] = "biz-0001"
        self.assertRejected(r, "duplicate id", tag="rendered")
        r["id"] = "biz-1-2"
        self.assertRejected(r, "is not <group>-NNNN", tag="rendered")
        self.assertRejected(S.rendered_yesno(), "not registered in datasets/newq.py", tag="my_new_tag")

    def test_new_row_fields(self):
        for key, val, needle in (("legacy_id", "syn-0001", "legacy_id must be null"), ("origin", "v1-old", "origin must be"),
                                 ("derived_from", "photo-9999", "not a known v1 id"), ("difficulty", "trivial", "difficulty must be"),
                                 ("skill", "japanese", "skill 'japanese' not allowed"), ("image_type", "poster", "image_type 'poster' not allowed"),
                                 ("answer_format", "choice:3", "answer_format"), ("lang", "fr", "lang must be")):
            r = S.rendered_yesno()
            r[key] = val
            self.assertRejected(r, needle, tag="rendered")
        r = S.rendered_yesno()
        del r["review"]
        self.assertRejected(r, "missing keys", tag="rendered")

    def test_choice_rules(self):
        r = S.photo_choice()
        r["en"]["wrong"][0] = "sheep"
        self.assertRejected(r, "duplicate options")
        r = S.photo_choice()
        r["ja"]["wrong"] = r["ja"]["wrong"][:-1]
        self.assertRejected(r, "differ in the number of options")
        r = S.photo_choice()
        r["en"]["wrong"] = ["w%d" % i for i in range(16)]
        r["ja"]["wrong"] = ["誤%d" % i for i in range(16)]
        r["answer_format"] = "choice:17"
        self.assertRejected(r, "17 options")
        r = S.photo_choice()
        r["en"]["wrong"] = ["w%d" % i for i in range(15)]
        r["ja"]["wrong"] = ["誤%d" % i for i in range(15)]
        r["answer_format"] = "choice:16"
        self.assertEqual(self.errs(r), [])                                     # 16 options (QEV's limit) is fine
        r = S.photo_choice()
        r["en"]["wrong"], r["ja"]["wrong"], r["answer_format"] = [], [], "choice:1"
        self.assertRejected(r, "1 options")
        r = S.photo_choice()
        r["ja"]["wrong"][-1] = "牛乳"                                          # "None of the above" in en, not special in ja
        self.assertRejected(r, "must be special in both languages")

    def test_yesno_and_score_rules(self):
        r = S.rendered_yesno()
        r["answer"] = "yes"
        self.assertRejected(r, "answer true / false", tag="rendered")
        r = S.rendered_score()
        r["answer"] = 7
        self.assertRejected(r, "level index")
        r = S.rendered_score()
        r["en"]["levels"] = ["l%d" % i for i in range(11)]
        r["ja"]["levels"] = ["段%d" % i for i in range(11)]
        r["answer_format"] = "score:11"
        self.assertRejected(r, "11 levels")
        r = S.rendered_score()
        r["ja"]["levels"] = r["ja"]["levels"][:-1]
        self.assertRejected(r, "differ in the number of levels")
        for n in (3, 7, 10):                                                    # the supported grades are accepted
            r = S.rendered_score()
            r["en"]["levels"] = ["l%d" % i for i in range(n)]
            r["ja"]["levels"] = ["段%d" % i for i in range(n)]
            r["answer_format"], r["answer"] = "score:%d" % n, n - 1
            self.assertEqual(self.errs(r), [], n)

    def test_language_rules(self):
        r = S.japanese_only()
        r["lang"] = "both"
        self.assertRejected(r, "does not match lang")
        r = S.japanese_only()
        r["ja"]["instr"] = "Which sign is this?"
        self.assertRejected(r, "no Japanese characters")
        r = S.japanese_only()
        r["lang"], r["langs"] = "both", ["en", "ja"]
        r["en"] = {"instr": "Which sign?", "correct": "stop", "wrong": ["slow", "no entry", "no parking", "None of the above"]}
        self.assertRejected(r, "tag ja_specific is for lang", tag="ja_specific")
        r = S.japanese_only()
        r["id"], r["local_images"] = "biz-2002", ["generated/biz-2002.png"]
        png(self.d / "img" / "generated" / "biz-2002.png")
        self.assertEqual(self.errs(r, tag="ja_specific"), [])
        e = S.japanese_only()                                                   # an English-only row is allowed
        e.update(id="biz-1002", lang="en", langs=["en"], local_images=["generated/biz-1001.png"])
        e["en"] = {"instr": "Which sign?", "correct": "stop", "wrong": ["slow", "no entry", "no parking", "None of the above"]}
        del e["ja"]
        e["local_images"] = ["generated/biz-1002.png"]
        png(self.d / "img" / "generated" / "biz-1002.png")
        self.assertEqual(self.errs(e, tag="rendered"), [])

    def test_picture_rules(self):
        r = S.rendered_yesno()
        r["local_images"] = []
        self.assertRejected(r, "exactly one picture", tag="rendered")
        r["local_images"] = ["generated/biz-1001.png", "generated/biz-1002.png"]
        self.assertRejected(r, "exactly one picture", tag="rendered")
        r["local_images"] = ["data/images/other.jpg"]
        self.assertRejected(r, "use generated/biz-1001", tag="rendered")
        r["local_images"] = ["/abs/biz-1001.png"]
        self.assertRejected(r, "must be relative", tag="rendered")
        r["local_images"] = ["generated/biz-1001.png"]
        self.assertEqual(self.errs(r, tag="rendered"), [])
        r = S.rendered_yesno()
        r["id"], r["local_images"] = "biz-1003", ["generated/biz-1003.png"]
        self.assertRejected(r, "not found under", tag="rendered")
        self.assertEqual(self.errs(r, tag="rendered", pictures=False), [])
        (self.d / "img" / "generated" / "biz-1004.png").write_bytes(b"not a picture")
        r["id"], r["local_images"] = "biz-1004", ["generated/biz-1004.png"]
        self.assertRejected(r, "cannot be opened as an image", tag="rendered")
        r = S.rendered_yesno()
        r["id"], r["derived_from"], r["local_images"] = "biz-1005", "biz-0015", ["data/synthetic/syn-0015.png"]    # a variant may reuse its parent's picture
        self.assertEqual(self.errs(r, tag="rendered"), [])
        r["derived_from"] = None
        self.assertRejected(r, "use generated/biz-1005", tag="rendered")
        r = S.photo_choice()
        r["local_images"] = ["generated/photo-2001.png"]
        self.assertRejected(r, "not found under")                               # a flipped picture is a new file, must exist
        r = S.photo_choice()
        r["images"] = []
        self.assertRejected(r, 'needs images = ["File:..."]')

    def test_commons_new_needs_a_free_licence(self):
        r = S.photo_choice()
        r.update(id="photo-3001", source="commons-new", derived_from=None, local_images=["generated/photo-3001.png"],
                 images=["File:Some sign.jpg"])
        png(self.d / "img" / "generated" / "photo-3001.png")
        self.assertRejected(r, "needs credit", tag="ja_specific")
        r["credit"] = {"license": "CC BY-SA 4.0", "author": "X", "url": "https://commons.wikimedia.org/wiki/File:Some_sign.jpg"}
        self.assertRejected(r, "only CC0 / public domain", tag="ja_specific")
        r["credit"]["license"] = "CC0"
        r["ja"], r["lang"], r["langs"] = r.pop("ja"), "ja", ["ja"]
        del r["en"]
        self.assertEqual(self.errs(r, tag="ja_specific"), [])

    def test_no_wikipedia_text(self):
        r = S.text_control()
        r["en"]["state"] = "x" * 700
        self.assertRejected(r, "a string of 700 characters")
        r = S.text_control()
        r["evidence"] = ["a sentence"]
        self.assertRejected(r, "'evidence' is not allowed")
        r = S.text_control()
        r["en"]["passage"] = "..."
        self.assertRejected(r, "'passage' is not allowed")
        r = S.text_control()
        r["derived_from"] = None
        self.assertRejected(r, "is a control and needs derived_from")
        r = S.text_control()
        del r["ja"]["state"]
        self.assertRejected(r, "needs an authored state")
        r = S.text_control()
        r["derived_from"] = "txt-0001"
        self.assertRejected(r, "is not an image question")
        art = S.text_control()
        for l in ("en", "ja"):
            del art[l]["state"]
        art["derived_from"], art["id"] = None, "txt-2001"
        art["article"] = {"en": {"title": "Japan", "revid": 1378660280}, "ja": {"title": "日本", "revid": 111284890}}
        self.assertEqual(self.errs(art, tag="txt_forms"), [])                  # a reference to the revision only
        art["en"]["state"] = "Japan is an island country."
        self.assertRejected(art, "a passage-based row has no state", tag="txt_forms")
        del art["en"]["state"]
        art["article"]["en"]["revid"] = "latest"
        self.assertRejected(art, "article must be", tag="txt_forms")
        t = S.text_control()
        t["local_images"] = ["generated/txt-1001.png"]
        self.assertRejected(t, "a text-only row has no picture")

    def test_file_spread_warnings(self):
        d = tmp_v1()
        try:
            rows = []
            for i in range(30):
                r = S.rendered_yesno()
                r["id"], r["local_images"], r["answer"] = "biz-%04d" % (1001 + i), ["generated/biz-%04d.png" % (1001 + i)], True
                rows.append(r)
                png(d / "img" / r["local_images"][0])
            write_new(d, "rendered", rows)
            rep = check(d)
            self.assertEqual(rep.errors, [])
            self.assertTrue(any("yes/no answers are 30 true" in w for w in rep.warnings), rep.warnings)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_no_new_files_is_fine(self):
        d = tmp_v1()
        try:
            rep = check(d)
            self.assertEqual((rep.errors, rep.counts), ([], {}))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class LoaderNewTests(unittest.TestCase):
    def test_new_rows_load_like_base_rows_and_move_nothing(self):
        d = sample_dir()
        base = tmp_v1()
        try:
            q, m = d / "q", d / "m"
            with_new = loader.load_v1_cases(qdir=q, manifests=m, images_root=d / "img", strict_passages=False)
            without = loader.load_v1_cases(qdir=base / "q", manifests=base / "m", images_root=d / "img", strict_passages=False)
            self.assertEqual(len(with_new), len(without) + 5)
            old = {c["id"]: c for c in without}
            for c in with_new:
                if c["id"] in old:                                   # no base answer position, option order or state changed
                    self.assertEqual((c["expected"], c.get("en", {}).get("options")), (old[c["id"]]["expected"], old[c["id"]].get("en", {}).get("options")), c["id"])
            new = {c["id"]: c for c in with_new if c["id"] not in old}
            self.assertEqual(set(new), {"photo-2001", "biz-1001", "rsn-1001", "biz-2001", "txt-1001"})
            c = new["photo-2001"]
            self.assertEqual(len(c["en"]["options"]), 6)
            self.assertEqual(c["en"]["options"][5][0], "None of the above")            # special: at the tail
            self.assertEqual(c["ja"]["options"][5][0], "該当なし")
            self.assertEqual(c["en"]["options"][c["expected"]][0], "sheep")
            self.assertEqual(c["ja"]["options"][c["expected"]][0], "羊")
            self.assertEqual(c["key"], ("v1", "photo-2001"))
            self.assertEqual((new["rsn-1001"]["expected"], len(new["rsn-1001"]["en"]["options"])), (3, 7))
            self.assertEqual(new["biz-1001"]["expected"], True)
            ja = new["biz-2001"]
            self.assertNotIn("en", ja)                                                   # a Japanese-only question has no en side
            self.assertEqual(ja["ja"]["options"][4][0], "該当なし")
            t = new["txt-1001"]
            self.assertEqual((t["modality"], t["images"], t["en"]["state"]), ("text", [], "No picture is attached to this question."))
            only = loader.load_v1_cases(qdir=q, manifests=m, only_new=True)
            self.assertEqual({c["id"] for c in only}, set(new))
            sub = {c["id"]: c["expected"] for c in loader.load_v1_cases(["photo"], qdir=q, manifests=m)}
            self.assertEqual(sub["photo-2001"], new["photo-2001"]["expected"])           # a subset never changes a position
            self.assertEqual(loader.load_v1_cases(qdir=q, manifests=m, include_new=False, strict_passages=False)[0]["id"], without[0]["id"])
        finally:
            shutil.rmtree(d, ignore_errors=True)
            shutil.rmtree(base, ignore_errors=True)

    def test_dropped_new_rows_are_skipped_and_do_not_count(self):
        d = sample_dir()
        try:
            rows = v1_io.read_jsonl(d / "q" / "v1" / "new_photo_variants.jsonl")
            rows[0]["review"]["state"] = "dropped"
            write_new(d, "photo_variants", rows)
            ids = {c["id"] for c in loader.load_v1_cases(qdir=d / "q", manifests=d / "m", strict_passages=False)}
            self.assertNotIn("photo-2001", ids)
            ids = {c["id"] for c in loader.load_v1_cases(qdir=d / "q", manifests=d / "m", include_dropped=True, strict_passages=False)}
            self.assertIn("photo-2001", ids)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_real_data_is_unchanged_by_the_new_machinery(self):
        """Without any new file the v1 cases are the base ones: 1841 questions, no id from a reserved range, no new idmap rows."""
        if newq.new_files(REAL):
            self.skipTest("real new_*.jsonl files exist: the follower agents have started")
        cs = loader.load_v1_cases(strict_passages=False)
        self.assertEqual(len(cs), 1841)
        self.assertEqual(loader.idmap_v1_new(), [])
        self.assertEqual(len(loader.legacy_to_v1()), 1962)


class RunnerTests(unittest.TestCase):
    def test_v1_sets_and_version_mismatches(self):
        self.assertEqual(rc.v1_set("photo"), (("photo",), False))
        self.assertEqual(rc.v1_set("new"), (("photo", "biz", "rsn", "txt"), True))
        with self.assertRaises(ValueError):
            rc.load_cases("commons", version="v1")
        with self.assertRaises(ValueError):
            rc.load_cases("photo", version="legacy")
        with self.assertRaises(ValueError):
            rc.v1_set("nonsense")

    def test_every_v1_question_can_be_asked_and_is_within_every_model_limit(self):
        """Dummy ask over ALL v1 questions (en and ja): choice option counts, score levels, picture counts, expected positions and the
        yes/no form are all handled, and no question exceeds an adapter limit (option / level / picture counts)."""
        cs = rc.load_cases("all", version="v1", strict_passages=False)
        self.assertEqual({c["version"] for c in cs}, {"v1"})
        self.assertEqual(len({c["id"] for c in cs}), len(cs))
        r = rc.dry_run(cs)
        self.assertEqual(r["problems"], [])
        self.assertEqual(r["asked"], sum(("en" in c) + ("ja" in c) for c in cs))
        res = rc.check_all_limits(cs)
        self.assertTrue(res)
        for model, problems in res.items():
            self.assertEqual(problems, [] if problems is not None else None, model)

    def test_limit_check_flags_what_exceeds(self):
        mk = lambda kind, n, imgs=1: dict(id="x", kind=kind, images=["a.png"] * imgs, expected=0,
                                          en=dict(state="s", instr="q", options=[("o%d" % i, "o%d" % i) if kind == "choice" else "l%d" % i for i in range(n)]))
        qev = dict(max_images=1, max_choice_options=16, max_score_levels=16, min_options=2)
        one = dict(max_images=None, max_choice_options=255, max_score_levels=10)
        self.assertEqual(rc.check_limits([mk("choice", 16)], qev), [])
        self.assertEqual(len(rc.check_limits([mk("choice", 17)], qev)), 1)
        self.assertEqual(len(rc.check_limits([mk("choice", 1)], qev)), 1)
        self.assertEqual(len(rc.check_limits([mk("score", 11)], one)), 1)
        self.assertEqual(rc.check_limits([mk("score", 10)], one), [])
        self.assertEqual(len(rc.check_limits([mk("choice", 4, imgs=2)], qev)), 1)

    def test_dry_run_catches_a_bad_ask_and_bad_cases(self):
        c = dict(id="x", kind="choice", images=[], expected=5,
                 en=dict(state="s", instr="q", options=[("a", "a"), ("b", "b")]))
        r = rc.dry_run([c])
        self.assertTrue(any("expected 5 outside" in p for p in r["problems"]))
        r = rc.dry_run([dict(c, expected=0)], ask=lambda *a: "NA")
        self.assertTrue(any("not a valid answer" in p for p in r["problems"]))
        r = rc.dry_run([dict(c, expected=0)], ask=lambda *a: True)
        self.assertTrue(any("not a valid answer" in p for p in r["problems"]))

    def test_many_option_new_rows_through_the_runner_path(self):
        """A 16-option question and 3/7/10-level scores written as new rows reach the runner as cases and pass the dry run."""
        d = tmp_v1()
        try:
            rows = []
            for i, n in enumerate((16, 10, 12)):
                r = S.photo_choice()
                r.update(id="photo-%04d" % (2010 + i), derived_from=None, source="rendered", images=None)
                del r["images"]
                r.update(source="rendered", local_images=["generated/photo-%04d.png" % (2010 + i)])
                r["en"] = {"instr": "Which?", "correct": "c0", "wrong": ["c%d" % k for k in range(1, n)]}
                r["ja"] = {"instr": "どれですか？", "correct": "選0", "wrong": ["選%d" % k for k in range(1, n)]}
                r["answer_format"] = "choice:%d" % n
                rows.append(r)
                png(d / "img" / r["local_images"][0])
            for i, n in enumerate((3, 7, 10)):
                r = S.rendered_score()
                r.update(id="rsn-%04d" % (1010 + i), local_images=["generated/rsn-%04d.png" % (1010 + i)], answer_format="score:%d" % n, answer=n - 1)
                r["en"]["levels"] = ["lv%d" % k for k in range(n)]
                r["ja"]["levels"] = ["段階%d" % k for k in range(n)]
                rows.append(r)
                png(d / "img" / r["local_images"][0])
            by = collections.defaultdict(list)
            for r in rows:
                by["photo_variants" if r["group"] == "photo" else "rendered"].append(r)
            for t, rs in by.items():
                write_new(d, t, rs)
            self.assertEqual(check(d).errors, [])
            cs = loader.load_v1_cases(qdir=d / "q", manifests=d / "m", images_root=d / "img", only_new=True)
            self.assertEqual(sorted(len(c["en"]["options"]) for c in cs), [3, 7, 10, 10, 12, 16])
            self.assertEqual(rc.dry_run(cs, check_images=True)["problems"], [])
            self.assertEqual(rc.check_limits(cs, dict(max_images=1, max_choice_options=16, max_score_levels=16, min_options=2)), [])
            self.assertEqual(rc.check_limits(cs, dict(max_score_levels=10)), [])
        finally:
            shutil.rmtree(d, ignore_errors=True)


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


class RoundTripTests(unittest.TestCase):
    """load -> validate -> balanced -> review batch -> apply -> summary on a temporary directory (the base files must stay as they are)."""

    def test_full_round_trip(self):
        d = tmp_v1()
        try:
            rows = []
            for i in range(130):                                                  # 130 rows -> 3 batches of about 60
                r = S.rendered_yesno() if i % 2 else S.rendered_score()
                grp, num = ("biz", 1001 + i) if i % 2 else ("rsn", 1001 + i)
                r.update(id="%s-%04d" % (grp, num), local_images=["generated/%s-%04d.png" % (grp, num)])
                rows.append(r)
                png(d / "img" / r["local_images"][0])
            write_new(d, "rendered", rows)
            q, m = d / "q" / "v1", d / "m"
            base_hash = {p.name: sha(p) for p in q.glob("*.jsonl") if not newq.tag_of_filename(p.name)}
            map_hash = (sha(m / "idmap_legacy_v1.csv"), sha(m / "questions_v1.csv"))
            # validate + manifests
            rep = V.validate(q, None, [d / "img"])
            self.assertEqual(rep.errors, [])
            self.assertEqual(V.main(["--v1dir", str(q), "--images-root", str(d / "img"), "--write-manifests", "--manifests", str(m)]), 2)
            self.assertFalse(list(m.glob("idmap_v1_new_*")))                       # no tag: nothing is written
            self.assertEqual(V.main(["--v1dir", str(q), "--images-root", str(d / "img"), "--write-manifests", "--tag", "rendered",
                                     "--manifests", str(m)]), 0)
            im = v1_io.read_csv(m / "idmap_v1_new_rendered.csv")
            self.assertEqual((len(im), im[0]["legacy_id"], im[0]["status"], im[0]["group_legacy"]), (130, "", "new", "new"))
            self.assertEqual(len(v1_io.read_csv(m / "questions_v1_new_rendered.csv")), 130)
            self.assertEqual(len(loader.classification("v1", m)), 1962 + 130)
            self.assertEqual(len(loader.legacy_to_v1(m)), 1962)
            # review batches
            out = d / "review"
            index = ex.export_new(out, q, [], [d / "img"], None, manifests=m)
            self.assertEqual([b["batch"] for b in index], ["new_rendered_01", "new_rendered_02", "new_rendered_03"])
            self.assertEqual([b["n"] for b in index], [44, 43, 43])
            self.assertEqual([p.name for p in out.glob("index_new*.json")], ["index_new_rendered.json"])
            batch = json.loads((out / "new_rendered_01.json").read_text(encoding="utf-8"))
            q0 = batch["questions"][0]
            self.assertEqual((q0["new"], q0["legacy_id"], len(q0["images"])), (True, None, 1))
            self.assertTrue(pathlib.Path(q0["images"][0]).is_file())
            last = json.loads((out / "new_rendered_03.json").read_text(encoding="utf-8"))["questions"]
            sc = next(x for x in last if x["kind"] == "score")                # sorted by id: the biz rows come before the rsn rows
            self.assertEqual((sc["en"]["levels"], sc["en"]["expected_index"]), (rows[0]["en"]["levels"], 3))
            first = batch["questions"][1]["id"]
            # verdicts: ok for all but one fix and one drop
            ids = [x["id"] for b in index for x in json.loads((out / (b["batch"] + ".json")).read_text(encoding="utf-8"))["questions"]]
            for b in index:
                ids_b = [x["id"] for x in json.loads((out / (b["batch"] + ".json")).read_text(encoding="utf-8"))["questions"]]
                lines = [dict(id=i, verdict="ok", issues=[]) for i in ids_b]
                if b["batch"] == "new_rendered_01":
                    lines[0] = dict(id=ids_b[0], verdict="drop", issues=["unclear"], reason="the picture does not decide it")
                    lines[1] = dict(id=ids_b[1], verdict="fix", issues=[], fix={"difficulty": "hard"}, reason="harder than it looks")
                v1_io.write_jsonl(out / "out" / (b["batch"] + ".jsonl"), lines)
            code, text = ar.process(out, q, m, "2026-10-12", apply=False)
            self.assertEqual(code, 0, text)
            self.assertEqual(sha(q / "new_rendered.jsonl"), sha(q / "new_rendered.jsonl"))
            self.assertEqual(v1_io.read_jsonl(q / "new_rendered.jsonl")[0]["review"]["state"], "unreviewed")      # dry run writes nothing
            code, text = ar.process(out, q, m, "2026-10-12", apply=True)
            self.assertEqual(code, 0, text)
            after = v1_io.read_jsonl(q / "new_rendered.jsonl")
            st = collections.Counter(r["review"]["state"] for r in after)
            self.assertEqual(st, {"reviewed": 128, "dropped": 1, "changed": 1})
            self.assertEqual(next(r for r in after if r["id"] == first)["difficulty"], "hard")
            self.assertEqual({p.name: sha(p) for p in q.glob("*.jsonl") if not newq.tag_of_filename(p.name)}, base_hash)   # the base is untouched
            self.assertEqual((sha(m / "idmap_legacy_v1.csv"), sha(m / "questions_v1.csv")), map_hash)
            im = {r["v1_id"]: r for r in v1_io.read_csv(m / "idmap_v1_new_rendered.csv")}
            self.assertEqual(sorted(collections.Counter(r["status"] for r in im.values()).items()), [("dropped", 1), ("new", 129)])
            self.assertEqual(len(loader.dropped_ids(m) & set(im)), 1)
            # idempotent
            h1 = (sha(q / "new_rendered.jsonl"), sha(m / "idmap_v1_new_rendered.csv"))
            self.assertEqual(ar.process(out, q, m, "2026-10-12", apply=True)[0], 0)
            self.assertEqual((sha(q / "new_rendered.jsonl"), sha(m / "idmap_v1_new_rendered.csv")), h1)
            # the loader skips the dropped one
            cs = loader.load_v1_cases(qdir=d / "q", manifests=m, only_new=True, images_root=d / "img")
            self.assertEqual(len(cs), 129)
            # only the named tag's verdict files are read when --tag is given (the base verdicts in out/ are not touched)
            v1_io.write_jsonl(out / "out" / "batch_photo_01.jsonl", [dict(id="photo-0001", verdict="drop", issues=[], reason="x")])
            code, text = ar.process(out, q, m, "2026-10-12", apply=True, tags=["rendered"])
            self.assertEqual(code, 0, text)
            self.assertEqual({p.name: sha(p) for p in q.glob("*.jsonl") if not newq.tag_of_filename(p.name)}, base_hash)
            (out / "out" / "batch_photo_01.jsonl").unlink()
            # a verdict for an id outside its batch is refused
            v1_io.write_jsonl(out / "out" / "new_rendered_03.jsonl", [dict(id=ids[0], verdict="ok", issues=[])])
            self.assertEqual(ar.process(out, q, m, "2026-10-12")[0], 2)
            # summary
            allrows = v1_io.load_v1_all(q)
            data = B.build_data(allrows, v1_io.load_idmap(m), {}, {}, {}, idmap_new=v1_io.load_new_idmap(m))
            self.assertEqual(data["stats"]["all"]["total"], 1962 + 130)
            self.assertEqual(data["stats"]["active"]["total"], 1841 + 129)
            self.assertEqual(sum(r["new"] for r in data["idmap_stats"]["rows"]), 129)
            self.assertEqual(data["idmap_stats"]["total"], 1962)
            self.assertEqual(data["idmap_stats"]["dropped_mismatch"], [])
            self.assertEqual(sum(s for _, s in data["stats"]["active"]["score_levels"]), 41 + 65)
            for mode in ("legacy", "balanced"):
                self.assertEqual(sum(sum(p["counts"]) for p in data["stats"]["active"]["pos"][mode]) > 0, True)
            B.render(data)
            node = shutil.which("node")
            if node:
                js = d / "check.js"
                js.write_text(B.extract_script(B.render(data)), encoding="utf-8")
                self.assertEqual(subprocess.run([node, "--check", str(js)], capture_output=True, text=True).returncode, 0)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_apply_writes_only_the_touched_tag(self):
        """Two writers, two files: a verdict on one tag's rows never rewrites the other tag's file or the base."""
        d = sample_dir()
        try:
            q, m = d / "q" / "v1", d / "m"
            others = {p.name: sha(p) for p in q.glob("*.jsonl") if p.name != "new_ja_specific.jsonl"}
            out = d / "review"
            ex.export_new(out, q, [], [d / "img"], None, tags=["ja_specific"], manifests=m)
            v1_io.write_jsonl(out / "out" / "new_ja_specific_01.jsonl", [dict(id="biz-2001", verdict="ok", issues=[])])
            self.assertEqual(ar.process(out, q, m, "2026-10-12", apply=True)[0], 0)
            self.assertEqual({p.name: sha(p) for p in q.glob("*.jsonl") if p.name != "new_ja_specific.jsonl"}, others)
            self.assertEqual(v1_io.read_jsonl(q / "new_ja_specific.jsonl")[0]["review"]["state"], "reviewed")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_review_batch_of_a_control_and_a_ja_only_question(self):
        d = sample_dir(parent_picture=True)
        try:
            out = d / "review"
            index = ex.export_new(out, d / "q" / "v1", [], [d / "img"], None, manifests=d / "m")
            by = {i["tag"]: i for i in index}
            self.assertEqual(set(by), {"photo_variants", "rendered", "ja_specific", "txt_controls"})
            ja = json.loads((out / "new_ja_specific_01.json").read_text(encoding="utf-8"))["questions"][0]
            self.assertNotIn("en", ja)
            self.assertEqual(ja["ja"]["option_labels"], ["A", "B", "C", "D", "E"])
            self.assertEqual(ja["ja"]["options_as_shown"][-1], "該当なし")
            ctl = json.loads((out / "new_txt_controls_01.json").read_text(encoding="utf-8"))["questions"][0]
            self.assertEqual((ctl["images"], ctl["en"]["state"], ctl["derived_from"]), ([], "No picture is attached to this question.", "biz-0015"))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class DuplicateTests(unittest.TestCase):
    def test_duplicates_among_new_rows_and_against_the_base(self):
        """Same picture + wording + right answer + answer_format is a duplicate (other wrong options do not make it different); a variant
        that changes the option count, the kind, the wording, the picture or the answer is not."""
        d = tmp_v1()
        try:
            parent = next(r for r in v1_io.load_v1(REAL)["photo"] if r["id"] == "photo-0001")
            same_count = S.photo_choice()
            same_count.update(id="photo-2001", answer_format="choice:4")
            same_count["en"]["wrong"] = ["goat", "pig", "rabbit"]
            same_count["ja"]["wrong"] = ["ヤギ", "豚", "ウサギ"]
            self.assertEqual((same_count["en"]["correct"], parent["en"]["correct"]), ("sheep", "sheep"))
            four_other = dict(S.photo_choice(), id="photo-2002", answer_format="choice:4")
            four_other["en"] = dict(four_other["en"], wrong=["horse", "cow", "dog"])
            four_other["ja"] = dict(four_other["ja"], wrong=["馬", "牛", "犬"])
            ok6 = S.photo_choice()
            ok6.update(id="photo-2003")                                    # 6 options: another answer_format -> a real variant
            yn = S.photo_choice()
            yn.update(id="photo-2004", kind="noul", answer_format="yesno", answer=True)
            yn["en"], yn["ja"] = {"instr": "It is a sheep"}, {"instr": "羊である"}
            write_new(d, "photo_variants", [same_count, four_other, ok6, yn])
            errs = check(d).errors
            dup = [e for e in errs if "duplicate of" in e]
            self.assertEqual(len(dup), 2, errs)                               # photo-2001 and photo-2002 repeat photo-0001 (same count)
            self.assertTrue(all("duplicate of photo-0001" in e for e in dup), dup)
            self.assertFalse(any("photo-2003" in e or "photo-2004" in e for e in errs), errs)
            # between two new rows the later id is the duplicate
            a, b = S.rendered_yesno(), S.rendered_yesno()
            b["id"], b["local_images"] = "biz-1002", ["generated/biz-1002.png"]
            png(d / "img" / "generated" / "biz-1001.png")
            (d / "img" / "generated" / "biz-1002.png").write_bytes((d / "img" / "generated" / "biz-1001.png").read_bytes())   # same picture
            write_new(d, "photo_variants", [])
            write_new(d, "rendered", [a, b])
            errs = check(d).errors
            self.assertEqual([e for e in errs if "duplicate of biz-1001" in e and "biz-1002" in e].__len__(), 1, errs)
            b["en"]["instr"] = "Every bar is taller than the first bar"          # another wording: not the same question
            write_new(d, "rendered", [a, b])
            self.assertEqual(check(d).errors, [])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class SharedWorkflowTests(unittest.TestCase):
    def test_reapplying_the_real_base_verdicts_changes_no_byte(self):
        """work/review/out/ holds the 33 base verdict files; a run of apply_review over them (what happens when a new-question writer forgets
        --tag) must leave the base files and the base manifests byte-identical. Skipped when the review folder is not on this machine."""
        rdir = _paths.ROOT / "work" / "review"
        if not (rdir / "out").is_dir() or not list(rdir.glob("batch_*.json")):
            self.skipTest("work/review (batches and verdicts) not on this machine")
        d = tmp_v1()
        try:
            q, m = d / "q" / "v1", d / "m"
            # only the base verdict files (batch_*): the new-question verdicts (new_*) belong to rows this temporary copy does not have
            only = d / "review_base"
            (only / "out").mkdir(parents=True)
            for f in rdir.glob("batch_*.json"):
                shutil.copy2(f, only / f.name)
            for f in (rdir / "out").glob("batch_*.jsonl"):
                shutil.copy2(f, only / "out" / f.name)
            before = {p.name: sha(p) for p in list(q.glob("*")) + list(m.glob("*"))}
            code, text = ar.process(only, q, m, "2026-10-12", apply=True)
            self.assertEqual(code, 0, text[:300])
            self.assertEqual({p.name: sha(p) for p in list(q.glob("*")) + list(m.glob("*"))}, before)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_write_helpers_leave_an_unchanged_file_alone(self):
        d = pathlib.Path(tempfile.mkdtemp())
        try:
            f = d / "x.jsonl"
            v1_io.write_jsonl(f, [{"a": 1}])
            t = f.stat().st_mtime_ns
            v1_io.write_jsonl(f, [{"a": 1}])
            self.assertEqual(f.stat().st_mtime_ns, t)
            v1_io.write_jsonl(f, [{"a": 2}])
            self.assertEqual(v1_io.read_jsonl(f), [{"a": 2}])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_batch_runner_sends_the_version_of_a_v1_set(self):
        src = (_paths.ROOT / "runner" / "batch.py").read_text(encoding="utf-8")
        self.assertIn('set_version = "legacy" if set_name in LEGACY_SETS else "v1"', src)
        self.assertIn("--dataset-version", src)
        self.assertIn("annotate_calibration(block, set_version", src)


if __name__ == "__main__":
    unittest.main()
