# -*- coding: utf-8 -*-
"""List the Japanese questions next to the English ones, for a human to read (no automatic judgement).

    python datasets/tools/list_ja_for_review.py [--version legacy|v1] [--group photo|biz|rsn|txt] [--out FILE]

Purpose: find Japanese questions that read like a machine translation of the English (stiff word order, English idioms, a
Japanese picture question that is only a translation). One line per question: id, group, English question, Japanese question,
the correct option and the wrong ones in both languages. Nothing is scored; the output is a reading aid (TSV, UTF-8).
"""
import argparse
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import loader, taxonomy  # noqa: E402


def rows_for_review(version: str = "legacy", group: str | None = None) -> list[list]:
    out = []
    for r in loader.load_rows(version):
        g = r.get("group") or taxonomy.new_group(r)
        if group and g != group:
            continue
        if "ja" not in (r.get("langs") or ["en", "ja"]):
            continue
        en, ja = r.get("en", {}), r["ja"]
        opts = lambda q: " / ".join([q["correct"]] + list(q["wrong"])) if "correct" in q else " / ".join(q.get("levels", []))
        out.append([version, r["id"], g, en.get("instr", ""), ja["instr"], opts(en) if en else "", opts(ja)])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="legacy")
    ap.add_argument("--group", default=None)
    ap.add_argument("--out", default="-")
    a = ap.parse_args()
    rows = rows_for_review(a.version, a.group)
    f = sys.stdout if a.out == "-" else open(a.out, "w", encoding="utf-8", newline="")
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["version", "id", "group", "en_question", "ja_question", "en_options", "ja_options"])
    w.writerows(rows)
    print("%d questions" % len(rows), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
