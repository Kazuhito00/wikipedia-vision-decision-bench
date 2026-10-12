# -*- coding: utf-8 -*-
"""Make the first version of the v1 question files: the frozen legacy questions, renamed to their v1 ids.

    python datasets/tools/make_v1_seed.py [--force]

Why: v1 is "legacy, reviewed one question at a time". Before the review a v1 row must say the same as its legacy row, so the review
(datasets/REVIEW_GUIDE.md, export_review_batches.py, apply_review.py) starts from a known, reproducible state.

Input : datasets/questions/legacy/{linked,synthetic,reasoning}.jsonl (frozen), manifests/idmap_legacy_v1.csv, manifests/questions_legacy.csv.
Output: datasets/questions/v1/{photo,biz,rsn,txt}.jsonl (v1 id order), manifests/questions_v1.csv.
A v1 row = the legacy row with: id = the v1 id, legacy_id, group, source / image_type / skill (from questions_legacy.csv, not recomputed),
answer_format (the "answer" axis, see v1_io.py), lang, and review = {state: "unreviewed", history: []}. Nothing else changes
(options, tags, difficulty, local_images, evidence_sha256 stay as in legacy). It is deterministic: the same input gives the same bytes.
It refuses to overwrite v1 files that already contain a reviewed row (use --force to start over).
"""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets.tools import v1_io  # noqa: E402

LEGACY_FILES = ("linked.jsonl", "synthetic.jsonl", "reasoning.jsonl")


def build(qdir: pathlib.Path = v1_io.QDIR, manifests: pathlib.Path = v1_io.MANIFESTS) -> dict:
    """{group: [v1 rows]} built from the frozen legacy files and the manifests."""
    legacy = {}
    for name in LEGACY_FILES:
        for r in v1_io.read_jsonl(pathlib.Path(qdir) / "legacy" / name):
            legacy[r["id"]] = r
    cls = {c["id"]: c for c in v1_io.read_csv(pathlib.Path(manifests) / "questions_legacy.csv")}
    out = {g: [] for g in v1_io.GROUPS}
    for m in v1_io.load_idmap(manifests):                     # the id map is in legacy order; sorted below by v1 id
        r, c = legacy[m["legacy_id"]], cls[m["legacy_id"]]
        row = {"id": m["v1_id"], "legacy_id": m["legacy_id"], "group": m["group_v1"], "source": c["source"], "image_type": c["image_type"],
               "skill": c["skill"], "answer_format": c["answer"], "lang": c["lang"]}
        for k, v in r.items():
            if k not in ("id", "source"):                    # legacy "source" ("synthetic") is replaced by the new source axis
                row[k] = v
        row["review"] = {"state": "unreviewed", "history": []}
        out[m["group_v1"]].append(row)
    for g in out:
        out[g].sort(key=lambda r: r["id"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite v1 files even if they hold reviewed questions")
    a = ap.parse_args()
    existing = v1_io.load_v1()
    touched = [r["id"] for r in v1_io.all_rows(existing) if r.get("review", {}).get("state") != "unreviewed"]
    if touched and not a.force:
        print("refusing to overwrite: %d v1 questions already reviewed (e.g. %s). Use --force." % (len(touched), touched[:3]))
        return 1
    by_group = build()
    v1_io.save_v1(by_group)
    v1_io.write_questions_csv(by_group)
    print("wrote v1:", {g: len(r) for g, r in by_group.items()}, "total", sum(len(r) for r in by_group.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
