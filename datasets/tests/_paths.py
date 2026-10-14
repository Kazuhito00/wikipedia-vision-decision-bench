# -*- coding: utf-8 -*-
"""Test plumbing: puts the repository root first on sys.path (so `datasets` is this repo's package, not another one)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
