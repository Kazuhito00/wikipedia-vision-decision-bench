# -*- coding: utf-8 -*-
"""Drop the near-duplicate rows of new_rendered.jsonl that the Opus review flagged (same value / question / answer, only the
background colour differs): the LATER id is dropped, the earlier one stays. Idempotent; every other line of the file is kept
byte for byte (only the matching lines are re-serialised), then the tag's two manifests are rebuilt from the rows.

    python datasets/tools/drop_near_dups.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from datasets.tools import v1_io  # noqa: E402

TAG = "rendered"
DATE = "2026-10-11"
#: later id -> earlier id that stays
NEAR_DUPS = {"biz-1005": "biz-1004", "biz-1009": "biz-1008", "biz-1012": "biz-1010", "biz-1044": "biz-1043", "rsn-1038": "rsn-1037"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    path = v1_io.new_path(TAG)
    lines = path.read_bytes().decode("utf-8").split("\n")
    trailing = lines[-1] == ""
    if trailing:
        lines = lines[:-1]
    state = {json.loads(ln)["id"]: json.loads(ln)["review"]["state"] for ln in lines if ln.strip()}
    out, changed = [], []
    for ln in lines:
        r = json.loads(ln) if ln.strip() else None
        if r and r["id"] in NEAR_DUPS and r["review"]["state"] != "dropped":
            keep = NEAR_DUPS[r["id"]]
            assert state.get(keep) not in (None, "dropped"), "%s: the kept row %s is missing or dropped" % (r["id"], keep)
            r["review"]["state"] = "dropped"
            r["review"]["history"].append(dict(date=DATE, what="drop", why="near-duplicate of %s (same value/question/answer, background colour only)" % keep))
            ln = json.dumps(r, ensure_ascii=False)
            changed.append(r["id"])
        out.append(ln)
    print("to drop:" if not a.apply else "dropped:", changed or "nothing (already done)")
    if a.apply and changed:
        v1_io._write_if_changed(path, ("\n".join(out) + ("\n" if trailing else "")).encode("utf-8"))
    if a.apply:
        v1_io.write_new_manifests(v1_io.load_new(), tags=[TAG])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
