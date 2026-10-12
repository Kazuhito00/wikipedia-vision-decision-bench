# -*- coding: utf-8 -*-
"""Licence regex (CC0 / public domain only), lead-section text shaping, the regrouping gate."""
import importlib.util
import pathlib
import unittest

import _paths
from datasets import loader
from datasets.questions import http, wikitext
from datasets.tools import regroup_check


def _find_ok_license():
    """The licence regex lives with the fetch scripts (datasets/fetch/, written by another part of the work): load whichever
    module there defines OK_LICENSE."""
    for p in sorted((loader.ROOT / "datasets" / "fetch").glob("*.py")):
        if "OK_LICENSE" in p.read_text(encoding="utf-8"):
            spec = importlib.util.spec_from_file_location("_lic_" + p.stem, p)
            m = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(m)
            except Exception:
                continue
            if hasattr(m, "OK_LICENSE"):
                return m.OK_LICENSE
    return None


class LicenceTests(unittest.TestCase):
    def test_license_regex_passes_only_cc0_and_public_domain(self):
        """Only CC0 / public-domain pictures may be collected: these pass, anything with attribution or share-alike fails."""
        rx = _find_ok_license()
        if rx is None:
            self.skipTest("no OK_LICENSE in datasets/fetch/ yet")
        for s in ["CC0", "Public domain", "PD-USGov", "CC-Zero", "PD old"]:
            self.assertTrue(rx.match(s), s)
        for s in ["CC BY-SA 4.0", "CC BY 2.0", "GFDL", "Copyrighted free use", "Attribution"]:
            self.assertFalse(rx.match(s), s)


class LeadTextTests(unittest.TestCase):
    def test_lead_cleaning(self):
        """Broken-reference messages and emptied parentheses are removed; whitespace is collapsed."""
        text = "カナダは国。 引用エラー: 「注釈」という名前のグループの <ref> タグがありますが、対応する <references/> タグが見つかりません"
        self.assertNotIn("引用エラー", wikitext._clean(text))
        self.assertEqual(wikitext._clean("A ( ) b"), "A b")
        self.assertEqual(wikitext._clean("x （ ） y"), "x y")

    def test_lead_text_takes_the_first_paragraphs_without_references_and_tables(self):
        """The lead of an article is its paragraphs joined, with [1]-style marks, tables, infoboxes and hatnotes dropped and
        the length capped at a sentence end (no network: the API answer is replaced by a fixed page)."""
        page = ('<div class="hatnote">For other uses</div><table><tr><td>box</td></tr></table>'
                '<p>Alpha is a letter.[1] It is first.</p><p>Beta follows[a] alpha.</p><p class="mw-empty-elt"></p>')
        orig = http.api_json
        http.api_json = lambda base, params: {"parse": {"text": {"*": page}}}
        try:
            self.assertEqual(wikitext.lead_text("en", 1), "Alpha is a letter. It is first. Beta follows alpha.")
            long_page = "<p>" + "Sentence one is here. " * 80 + "</p>"
            http.api_json = lambda base, params: {"parse": {"text": {"*": long_page}}}
            out = wikitext.lead_text("en", 1, max_chars=300)
            self.assertLessEqual(len(out), 300)
            self.assertTrue(out.endswith("."))
        finally:
            http.api_json = orig


class RegroupGateTests(unittest.TestCase):
    def test_gate_logic_on_a_tiny_log_tree(self):
        """The tally keeps per-model totals when questions move between groups: a made-up log tree with one model, checked with
        the same functions as the real gate (precedence: main, then _fill, then _exp; timed log only fills gaps)."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            for d in ("results_w", "results_s", "results_t"):
                (root / d).mkdir()
            line = "%s %s got=0 exp=0 rev=None ms=5\n"
            (root / "results_w" / "openjev_wiki_en_224.log").write_text(line % ("ok ", "img-0016") + line % ("XX ", "img-0018"), encoding="utf-8")
            (root / "results_w" / "openjev_wiki_en_224_fill.log").write_text(line % ("ok ", "img-0018"), encoding="utf-8")
            (root / "results_t" / "openjev_wiki_en_224.log").write_text(line % ("XX ", "img-0016") + line % ("ok ", "img-0019"), encoding="utf-8")
            res = regroup_check.compute(root)
            self.assertTrue(res[("openjev", "en", "img-0016")])        # the timed log does not overwrite
            self.assertTrue(res[("openjev", "en", "img-0018")])        # fill overwrites main
            self.assertTrue(res[("openjev", "en", "img-0019")])        # timed fills a gap

    @unittest.skipUnless((_paths.OLD_EVAL_COMMON / "results_w").exists(), "old measurement logs not available")
    def test_old_and_new_groups_give_identical_totals_for_every_model(self):
        """THE GATE. From the real logs: per model and language, correct/answered summed over the 4 old groups equals the sum over
        the 4 new groups; photo = wikipedia + expansion; biz + rsn = synthetic + reasoning; rsn = reasoning + 94; the old tallies
        equal the ok flags of the existing HTML report (if present)."""
        html = _paths.OLD_HTML if _paths.OLD_HTML.exists() else None
        out = regroup_check.run(_paths.OLD_EVAL_COMMON, html)
        self.assertEqual(out["problems"], [])
        self.assertEqual(out.get("html_diff", []), [])
        self.assertEqual(len(out["rows"]), 20)


if __name__ == "__main__":
    unittest.main()
