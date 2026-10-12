# -*- coding: utf-8 -*-
"""Make the golden data for the legacy option order (one-off; the result is committed).

    python datasets/tools/make_golden_order.py --src <path to the old wiki_qa/>

Runs the OLD loader (wiki_qa/wikiqa/dataset.py, read only) over all 1962 legacy questions and records, per question, what it
produced: the permutation of the options, the position / value of the right answer, and a sha256 of each language's
``state`` text (not the text itself: for the text-only questions it is Wikipedia text). tests/test_options.py then checks the
new datasets/options.py + datasets/loader.py against this file, so the equality with the old loader keeps being tested after
the old tree is gone. Output: datasets/manifests/legacy_option_order.csv
"""
import argparse
import csv
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "datasets" / "manifests" / "legacy_option_order.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    src = pathlib.Path(ap.parse_args().src).resolve()
    sys.path.insert(0, str(src))
    from wikiqa.dataset import load_cases  # the old loader
    rows = []
    for f in ("linked.jsonl", "synthetic.jsonl", "reasoning.jsonl"):
        raw = {json.loads(l)["id"]: json.loads(l) for l in (src / "data" / f).read_text(encoding="utf-8").splitlines() if l.strip()}
        for c in load_cases(src, files=(f,)):
            r = raw[c["id"]]
            order = ""
            if c["kind"] == "choice":
                items = [r["en"]["correct"]] + list(r["en"]["wrong"])
                assert len(set(items)) == len(items), c["id"]
                order = "-".join(str(items.index(o[0])) for o in c["en"]["options"])
            sha = lambda lang: hashlib.sha256(c[lang]["state"].encode("utf-8")).hexdigest() if lang in c else ""
            rows.append(dict(id=c["id"], kind=c["kind"], n_options=len(c["en"]["options"] or []), order=order,
                             expected=c["expected"], state_sha256_en=sha("en"), state_sha256_ja=sha("ja")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("wrote %d rows to %s" % (len(rows), OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
