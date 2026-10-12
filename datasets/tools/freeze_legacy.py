# -*- coding: utf-8 -*-
"""Freeze the legacy question set into this repository (one-off, kept for provenance).

    python datasets/tools/freeze_legacy.py --src <path to the old wiki_qa/>  [--check]

What it does
  * copies wiki_qa/data/{linked,synthetic,reasoning}.jsonl and wiki_qa/questions/questions.jsonl to
    datasets/questions/legacy/ **unchanged, except for the Wikipedia text**: the 87 text-only questions carry an `evidence`
    field (verbatim strings from the article lead sections, en and ja). Wikipedia text (CC BY-SA) must not be in the
    repository, so `evidence` is replaced by `evidence_sha256` (the sha256 of each string: with the local passage one can
    still check that the string is in it).
  * rewrites datasets/questions/items_text_*.py the same way (the evidence arguments `ev_en` / `ev_ja` of tchoice/tnoul are
    emptied) -- done with the `ast` module so nothing else in those files changes.
  * writes datasets/manifests/legacy_freeze.json: sha256 of every original file and of every frozen file, and row counts.
    tests/test_legacy_frozen.py fails when a frozen file changes, so legacy stays legacy.

Nothing is read from or written to the old wiki_qa/ tree except the files listed above (read only).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEGACY = ROOT / "datasets" / "questions" / "legacy"
QDIR = ROOT / "datasets" / "questions"
FREEZE = ROOT / "datasets" / "manifests" / "legacy_freeze.json"
FILES = [("data/linked.jsonl", "linked.jsonl"), ("data/synthetic.jsonl", "synthetic.jsonl"),
         ("data/reasoning.jsonl", "reasoning.jsonl"), ("questions/questions.jsonl", "questions.jsonl")]
# positional index of the evidence arguments: tchoice(title, en_q, en_ok, en_bad, ja_q, ja_ok, ja_bad, ev_en, ev_ja, ...)
# and tnoul(title, en_stmt, ja_stmt, answer, ev_en, ev_ja, ...)
EV_ARGS = {"tchoice": (7, 8), "tnoul": (4, 5)}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strip_row(r: dict) -> dict:
    """The row without Wikipedia text: `evidence` -> `evidence_sha256` (same position in the key order)."""
    out = {}
    for k, v in r.items():
        if k == "evidence":
            out["evidence_sha256"] = {lang: [sha256(s.encode("utf-8")) for s in v[lang]] for lang in v}
        else:
            out[k] = v
    return out


def strip_items_text(src: str) -> str:
    """Empty the evidence arguments of tchoice/tnoul calls (source-level splice, everything else byte-identical)."""
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln.encode("utf-8")))
    raw = src.encode("utf-8")
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in EV_ARGS:
            for i in EV_ARGS[node.func.id]:
                a = node.args[i]
                spans.append((offs[a.lineno - 1] + a.col_offset, offs[a.end_lineno - 1] + a.end_col_offset))
    for s, e in sorted(spans, reverse=True):
        raw = raw[:s] + b"[]" + raw[e:]
    return raw.decode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="the old wiki_qa/ directory")
    ap.add_argument("--check", action="store_true", help="only verify that the frozen files match a fresh run")
    args = ap.parse_args()
    src = pathlib.Path(args.src)
    LEGACY.mkdir(parents=True, exist_ok=True)
    info = {"note": "legacy frozen set. originals = the files of the old wiki_qa/ tree; frozen = this repository's copy "
                    "(Wikipedia evidence strings replaced by sha256).", "files": {}}
    for rel, name in FILES:
        raw = (src / rel).read_bytes()
        rows = [json.loads(ln) for ln in raw.decode("utf-8").splitlines() if ln.strip()]
        text = "".join(json.dumps(strip_row(r), ensure_ascii=False) + "\n" for r in rows)
        out = LEGACY / name
        if args.check:
            assert out.read_text(encoding="utf-8") == text, name
        else:
            out.write_text(text, encoding="utf-8", newline="\n")
        info["files"][name] = dict(rows=len(rows), original_sha256=sha256(raw), frozen_sha256=sha256(text.encode("utf-8")))
    n_ev = 0
    for p in sorted(QDIR.glob("items_text_*.py")):
        new = strip_items_text(p.read_text(encoding="utf-8"))
        ast.parse(new)
        if not args.check:
            p.write_text(new, encoding="utf-8", newline="\n")
        n_ev += 1
    info["items_text_files_evidence_emptied"] = n_ev
    if not args.check:
        FREEZE.parent.mkdir(parents=True, exist_ok=True)
        FREEZE.write_text(json.dumps(info, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
