# -*- coding: utf-8 -*-
"""Test plumbing: puts the repository root first on sys.path (so `datasets` is this repo's package, not another one),
and finds the optional local material (old wiki_qa tree, old logs) that some checks compare against."""
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

# optional: the old tree, for the checks that compare with the original implementation / logs (skipped when absent)
OLD_WIKI_QA = pathlib.Path(os.environ.get("WIKIQA_LEGACY_ORIGIN", ROOT.parents[1] / "wiki_qa"))
OLD_EVAL_COMMON = pathlib.Path(os.environ.get("WIKIQA_LEGACY_LOGS", ROOT.parents[1] / "eval_common"))
OLD_HTML = OLD_EVAL_COMMON.parent / "まとめ（Wikipedia画像セット）.html"
