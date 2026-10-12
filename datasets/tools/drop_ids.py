# -*- coding: utf-8 -*-
"""Drop individual v1 questions on request (e.g. a privacy-check question someone wants out).

    python datasets/tools/drop_ids.py photo-0030 photo-0062 --reason "requested exclusion" [--date YYYY-MM-DD] [--apply]

Default is a DRY RUN. With --apply: each id gets review.state = "dropped" (plus a history entry), its row in manifests/idmap_legacy_v1.csv
gets status "dropped" (new questions have no such row; their manifests/idmap_v1_new_<tag>.csv and the classification tables are
regenerated), and the question files are written. Uses the same code as apply_review.py (apply_entries), so the effect is identical to a
"drop" verdict. The row stays in the file; consumers skip review.state == "dropped". Afterwards run `python -m datasets.build_v1`.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datasets.tools import apply_review, v1_io  # noqa: E402


def drop(ids, reason, date, apply=False, v1dir=v1_io.V1DIR, manifests=v1_io.MANIFESTS) -> str:
    by_group, by_tag = v1_io.load_v1(v1dir), v1_io.load_new(v1dir)
    known = {r["id"] for r in v1_io.all_rows(by_group) + v1_io.all_new_rows(by_tag)}
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise SystemExit("unknown ids: %s" % ", ".join(unknown))
    entries = [dict(id=i, verdict="drop", issues=[], fix={}, reason=reason) for i in ids]
    wg, wn, wm = copy.deepcopy(by_group), copy.deepcopy(by_tag), copy.deepcopy(v1_io.load_idmap(manifests))
    apply_review.apply_entries(wg, wm, entries, date, new_rows=v1_io.all_new_rows(wn))
    if apply:
        touched = set(ids)
        groups = {g for g, rs in by_group.items() if any(r["id"] in touched for r in rs)}
        tags = {t for t, rs in by_tag.items() if any(r["id"] in touched for r in rs)}
        if groups:
            v1_io.save_v1({g: wg[g] for g in groups}, v1dir)
            v1_io.save_idmap(wm, manifests)
            v1_io.write_questions_csv(wg, manifests)
        if tags:
            v1_io.save_new({t: wn[t] for t in tags}, v1dir)
            v1_io.write_new_manifests(wn, manifests, tags=sorted(tags))
    return "%s %d question(s): %s" % ("dropped" if apply else "dry run, would drop", len(ids), ", ".join(ids))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(drop(a.ids, a.reason, a.date, a.apply))
    return 0


if __name__ == "__main__":
    sys.exit(main())
