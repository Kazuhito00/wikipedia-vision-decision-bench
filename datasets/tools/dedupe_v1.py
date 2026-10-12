# -*- coding: utf-8 -*-
"""Find duplicates ACROSS review batches in v1 and drop the later id of each pair.

    python datasets/tools/dedupe_v1.py [--apply] [--date 2026-10-11] [--px224 <dir> ...] [--report datasets/manifests/dedupe_v1.md]

Duplicate = same 224 px picture(s) (sha256 of the file bytes; a text-only question: same article revision ids) AND the same
question (English instruction, normalised) AND the same right answer, of the same kind:
  exact              the set of options is the same too (yes/no: same truth; score: same levels and level)
  wrong-set-differs  only the wrong options differ (the question is still the same question with another distractor set)
A picture shared by questions that ask different things (different instruction, or the same instruction with a different right
answer) is NOT a duplicate. Within a group of duplicates the first id (by group, then id) stays; every later id gets
review.state = "dropped", a history entry {date, what: "drop", why: "duplicate of <ID> (cross-batch)"} and idmap status = dropped.
Rows that are already dropped are ignored, so a second run finds nothing new; the report is rebuilt from the history entries.
Default is a dry run. Reads pictures only (never writes them); no network, no .env.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets.tools import v1_io  # noqa: E402

JEV = ROOT.parents[1]
WHAT = "drop"
WHY_RE = re.compile(r"^duplicate of (\S+) \(cross-batch\)$")
DEFAULT_PX224 = [ROOT / "work" / "px224", JEV / "wiki_qa" / "work" / "px224", ROOT / "work" / "generated" / "px224"]


def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()


def find_image(local_image: str, px224_dirs: list) -> pathlib.Path | None:
    name = pathlib.Path(local_image).name
    for d in px224_dirs:
        p = pathlib.Path(d) / name
        if p.exists():
            return p
    return None


def image_signature(row: dict, px224_dirs: list):
    """Tuple of sha256 of the 224 px pictures; ("text", revids...) for a text-only question; None if a picture is missing."""
    if row.get("modality") == "text" or not row.get("local_images"):
        arts = row.get("article") or {}
        return ("text",) + tuple(str(arts[l].get("revid")) for l in sorted(arts))
    out = []
    for li in row["local_images"]:
        p = find_image(li, px224_dirs)
        if p is None:
            return None
        out.append(hashlib.sha256(p.read_bytes()).hexdigest())
    return tuple(out)


def question_key(row: dict) -> tuple:
    """(kind, instruction, right answer): what makes two questions about one picture the same question."""
    lang = "en" if "en" in (row.get("langs") or ["en", "ja"]) else row["langs"][0]
    q = row[lang]
    if row["kind"] == "choice":
        right = _norm(q["correct"])
    elif row["kind"] == "noul":
        right = bool(row["answer"])
    else:
        right = _norm(q["levels"][int(row["answer"])])
    return (row["kind"], _norm(q["instr"]), right)


def option_set(row: dict) -> frozenset:
    lang = "en" if "en" in (row.get("langs") or ["en", "ja"]) else row["langs"][0]
    q = row[lang]
    if row["kind"] == "choice":
        return frozenset(_norm(x) for x in [q["correct"]] + list(q["wrong"]))
    if row["kind"] == "score":
        return frozenset(_norm(x) for x in q["levels"])
    return frozenset()


def find_duplicates(rows: list, sig_of) -> list:
    """[(kept_id, dropped_id, "exact" | "wrong-set-differs")] over the rows that are not dropped. `sig_of(row)` = picture signature."""
    order = {g: i for i, g in enumerate(v1_io.GROUPS)}
    live = sorted((r for r in rows if r["review"]["state"] != "dropped"), key=lambda r: (order.get(r["group"], 9), r["id"]))
    groups = {}
    for r in live:
        sig = sig_of(r)
        if sig is None or sig == ("text",):
            continue
        groups.setdefault((sig,) + question_key(r), []).append(r)
    pairs = []
    for rs in groups.values():
        first = rs[0]
        for r in rs[1:]:
            pairs.append((first["id"], r["id"], "exact" if option_set(first) == option_set(r) else "wrong-set-differs"))
    return sorted(pairs, key=lambda p: (order.get(p[1].split("-")[0], 9), p[1]))


def apply_pairs(by_group: dict, idmap: list, pairs: list, date: str) -> int:
    rows = {r["id"]: r for r in v1_io.all_rows(by_group)}
    im = {m["v1_id"]: m for m in idmap}
    n = 0
    for kept, dup, _ in pairs:
        why = "duplicate of %s (cross-batch)" % kept
        rev = rows[dup]["review"]
        if rev["state"] != "dropped":
            n += 1
        rev["state"] = "dropped"
        if not any(h["what"] == WHAT and h["why"] == why for h in rev["history"]):
            rev["history"].append({"date": date, "what": WHAT, "why": why})
        im[dup]["status"], im[dup]["change_note"] = "dropped", why
    return n


def recorded_pairs(by_group: dict) -> list:
    """Duplicates already recorded in the history (what == drop, why == 'duplicate of X (cross-batch)')."""
    out = []
    rows = {r["id"]: r for r in v1_io.all_rows(by_group)}
    for r in v1_io.all_rows(by_group):
        for h in r["review"]["history"]:
            m = WHY_RE.match(h.get("why", "")) if h.get("what") == WHAT else None
            if m:
                kept = rows.get(m.group(1))
                kind = "exact" if kept is not None and option_set(kept) == option_set(r) and question_key(kept) == question_key(r) else "wrong-set-differs"
                out.append((m.group(1), r["id"], kind, h["date"]))
                break
    return out


def summarize(row: dict) -> str:
    lang = "en" if "en" in (row.get("langs") or ["en", "ja"]) else row["langs"][0]
    q = row[lang]
    if row["kind"] == "choice":
        return "%s -> %s" % (q["instr"], q["correct"])
    if row["kind"] == "noul":
        return "%s -> %s" % (q["instr"], "yes" if row["answer"] else "no")
    return "%s -> %s" % (q["instr"], q["levels"][int(row["answer"])])


def report(by_group: dict, extra_note: str = "") -> str:
    rows = {r["id"]: r for r in v1_io.all_rows(by_group)}
    rec = sorted(recorded_pairs(by_group), key=lambda p: p[1])
    L = ["# v1: 重複問の検査（バッチをまたぐ）", "",
         "`datasets/tools/dedupe_v1.py` が作る。重複 = **同じ 224px 画像（ファイルの sha256 が一致）で、設問（英語）・正解・種類が同じ**。"
         "前の ID を残し、後ろの ID を `dropped` にした（`review.history` に `drop` / `duplicate of <ID> (cross-batch)`、idmap の status も `dropped`）。",
         "", "- `exact`: 選択肢の集合も同じ。`wrong-set-differs`: 誤答の組だけ違う（実質同じ問）。",
         "- 同じ画像でも設問か正解が違うもの（個数・色・有無など別の観点を問うもの）は重複にしない。"
         "同じ画像を共有する問の群は多数あるが、設問まで同じなのはこの一覧だけ。", "",
         "合計: **%d 問を追加で drop**（レビュー時点で dropped だった重複は含まない）。" % len(rec), ""]
    if extra_note:
        L += [extra_note, ""]
    L += ["| 残す ID | drop した ID | 種類 | 設問と正解 | 日付 |", "|---|---|---|---|---|"]
    for kept, dup, kind, date in rec:
        L.append("| %s | %s | %s | %s | %s |" % (kept, dup, kind, summarize(rows[dup]).replace("|", "/"), date))
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--px224", action="append", default=None)
    ap.add_argument("--report", default=str(v1_io.MANIFESTS / "dedupe_v1.md"))
    a = ap.parse_args()
    dirs = [pathlib.Path(p) for p in (a.px224 or DEFAULT_PX224)]
    by_group = v1_io.load_v1()
    idmap = v1_io.load_idmap()
    cache = {}

    def sig_of(r):
        if r["id"] not in cache:
            cache[r["id"]] = image_signature(r, dirs)
        return cache[r["id"]]

    pairs = find_duplicates(v1_io.all_rows(by_group), sig_of)
    missing = [r["id"] for r in v1_io.all_rows(by_group) if r["review"]["state"] != "dropped" and sig_of(r) is None]
    print("new duplicate pairs: %d; rows whose picture was not found: %d" % (len(pairs), len(missing)))
    for p in pairs:
        print("  keep %s  drop %s  (%s)" % p)
    if a.apply:
        apply_pairs(by_group, idmap, pairs, a.date)
        v1_io.save_v1(by_group)
        v1_io.save_idmap(idmap)
        v1_io.write_questions_csv(by_group)
        pathlib.Path(a.report).write_text(report(by_group), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
