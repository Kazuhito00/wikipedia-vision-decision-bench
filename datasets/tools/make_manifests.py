# -*- coding: utf-8 -*-
"""Write datasets/manifests/questions_legacy.csv (the new axes of every legacy question) and idmap_legacy_v1.csv (legacy id -> v1 id).

    python datasets/tools/make_manifests.py

v1 is mainly "the legacy questions, reviewed and polished one by one", so the id map is 1:1 for now. v1 ids are numbered per new
group in legacy order: photo-/biz- from 1; rsn-: the 225 old reasoning questions keep their number (rsn-0001..0225) and the 94 plain
visual-reasoning questions of the old synthetic set follow (rsn-0226..0319); txt-0001..0087 keep their number. A legacy id and a
v1 id may therefore be spelled the same (rsn-0001, txt-0001) -- they are told apart by the version (see datasets/NOTES.md).
Columns that later work fills in: status (kept / rewritten / dropped / pending), review_state, change_note.
The 13 two-picture reasoning questions are 'pending' (rebuild as one picture, or drop: decided later).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import loader, taxonomy  # noqa: E402


def main() -> int:
    rows = loader.load_rows("legacy")
    cls = [taxonomy.classify(r) for r in rows]
    by_id = {r["id"]: r for r in rows}
    counters = {g: 0 for g in taxonomy.NEW_GROUPS}
    ordered = [c for c in cls if c["group"] != "rsn"] + [c for c in cls if c["old_group"] == "reasoning"] + \
              [c for c in cls if c["group"] == "rsn" and c["old_group"] == "synthetic"]
    v1 = {}
    for c in ordered:
        counters[c["group"]] += 1
        v1[c["id"]] = "%s-%04d" % (c["group"], counters[c["group"]])
    mdir = ROOT / "datasets" / "manifests"
    mdir.mkdir(parents=True, exist_ok=True)
    with open(mdir / "questions_legacy.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cls[0]) + ["v1_id"], lineterminator="\n")
        w.writeheader()
        for c in cls:
            w.writerow(dict(c, v1_id=v1[c["id"]]))
    with open(mdir / "idmap_legacy_v1.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["legacy_id", "v1_id", "group_legacy", "group_v1", "status", "review_state", "change_note"])
        for c in sorted(cls, key=lambda c: v1[c["id"]]):
            two = len(by_id[c["id"]].get("images", [])) > 1
            w.writerow([c["id"], v1[c["id"]], c["old_group"], c["group"], "pending" if two else "kept", "unreviewed",
                        "two pictures: rebuild as one picture or drop" if two else ""])
    print(counters, "total", sum(counters.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
