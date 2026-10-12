# -*- coding: utf-8 -*-
"""Question loader hook for runner/run.py (``BENCH_LOADER=colab_loader:load``), used with run_colab.py --skip-missing-passages.

runner/cases.py loads the v1 sets with strict_passages=True, so `txt` / `all` raise on a machine without passages.json (Wikipedia text is
not distributed). This hook loads the same cases with strict_passages=False and DROPS every question whose passage is missing (the 87
article-based text questions); the 99 authored text-only controls stay. The block then holds fewer questions than a full `all` /
`txt` block: results/runs/v1/<block>.json records it as questions_in_block, and the numbers must not be compared with a full run.
Nothing in adapters/, runner/ or datasets/ is changed. v1 only (the hook ignores the dataset version, as runner/cases.py documents).
"""
from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PLACEHOLDER = "[passage "


def load(set_name, data_root=None):
    from datasets import loader
    from runner import cases as rc, config
    groups, only_new = rc.v1_set(set_name)
    root = pathlib.Path(data_root) if data_root else config.data_root()
    cs = loader.load_v1_cases(groups, images_root=root, only_new=only_new, strict_passages=False,
                              passages_path=os.environ.get("WIKIQA_PASSAGES") or root / "data" / "passages.json")
    return [c for c in cs if not any(str(c[l]["state"]).startswith(PLACEHOLDER) for l in ("en", "ja") if l in c)]
