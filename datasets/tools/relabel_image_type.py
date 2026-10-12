# -*- coding: utf-8 -*-
"""Relabel image_type astronomical / satellite for the questions the reviewers flagged ``needs_new_image_type: <x>``.

    python datasets/tools/relabel_image_type.py [--apply] [--date 2026-10-11] [--review-out work/review/out]

Only the extra types of ``taxonomy.V1_EXTRA_IMAGE_TYPES`` are applied (astronomical/astronomy -> astronomical, satellite/aerial ->
satellite); other proposals (medical-scan ...) are left. Only live (not dropped) rows that do not already have the type are changed;
only those rows are rewritten and each gets a review.history entry {date, what: "image_type", why}. Idempotent. Dry run by default.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import taxonomy  # noqa: E402
from datasets.tools import v1_io  # noqa: E402

MAP = {"astronomical": "astronomical", "astronomy": "astronomical", "satellite": "satellite", "aerial": "satellite"}


def proposals(review_out: pathlib.Path) -> dict:
    """{id: proposed image_type} from the reviewers' issues."""
    out = {}
    for p in sorted(pathlib.Path(review_out).glob("*.jsonl")):
        for r in v1_io.read_jsonl(p):
            for s in r.get("issues") or []:
                m = re.match(r"needs_new_image_type\s*[:：]\s*(.*)$", str(s).strip())
                if m and m.group(1).strip().lower() in MAP:
                    out[r["id"]] = (MAP[m.group(1).strip().lower()], m.group(1).strip())
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date", default="2026-10-11")
    ap.add_argument("--review-out", default=str(ROOT / "work" / "review" / "out"))
    a = ap.parse_args(argv)
    assert set(MAP.values()) <= set(taxonomy.V1_EXTRA_IMAGE_TYPES)
    props = proposals(pathlib.Path(a.review_out))
    base, new = v1_io.load_v1(), v1_io.load_new()
    changed, skipped = collections.Counter(), collections.Counter()
    touched_groups, touched_tags = set(), set()
    for scope, key, bucket in [("base", g, base[g]) for g in base] + [("new", t, new[t]) for t in new]:
        for r in bucket:
            if r["id"] not in props:
                continue
            if r.get("review", {}).get("state") == "dropped":
                skipped["dropped"] += 1
                continue
            want, raw = props[r["id"]]
            if r["image_type"] == want:
                skipped["already"] += 1
                continue
            old = r["image_type"]
            why = "reviewer proposed needs_new_image_type: %s; %s -> %s" % (raw, old, want)
            r["image_type"] = want
            r["review"].setdefault("history", []).append(dict(date=a.date, what="image_type", why=why))
            changed[want] += 1
            (touched_groups if scope == "base" else touched_tags).add(key)
    print("changed", dict(changed), "total", sum(changed.values()), "skipped", dict(skipped))
    if a.apply and sum(changed.values()):
        v1_io.save_v1({g: base[g] for g in touched_groups})
        v1_io.save_new({t: new[t] for t in touched_tags})
        v1_io.write_questions_csv(base)
        v1_io.write_new_manifests(new, tags=sorted(touched_tags))
        print("written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
