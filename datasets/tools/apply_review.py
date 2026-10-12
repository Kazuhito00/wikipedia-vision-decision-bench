# -*- coding: utf-8 -*-
"""Validate the reviewers' output and write it into the v1 question files.

    python datasets/tools/apply_review.py [--review-dir work/review] [--date YYYY-MM-DD] [--apply] [--report <md>]

Input : work/review/out/<batch name>.jsonl, one line per question (format: datasets/REVIEW_GUIDE.md section "Output"). The batch
        names are batch_<group>_<NN> (legacy-derived questions) and new_<tag>_<NN> (new questions of datasets/questions/v1/new_<tag>.jsonl):
        {id, verdict: ok|fix|drop|rewrite_1image, issues: [str], fix: {...only what changes}, reason}
Default is a DRY RUN: everything is validated and a report is printed, nothing is written. With --apply, datasets/questions/v1/*.jsonl,
manifests/idmap_legacy_v1.csv and manifests/questions_v1.csv are written. If any line is invalid nothing is written (all problems are listed).

Validation (a line is rejected when): the id is not a v1 id / not in the batch the file is named after / appears twice (also across
files); verdict unknown; `issues` not a list of strings; reason missing (any verdict but ok); fix present with ok / drop /
rewrite_1image, or empty with fix; unknown fix key or wrong type; a fix key that does not fit the question kind (correct_* / wrong_* for
choice only, truth for yes/no only, levels_* / score for score only); difficulty / image_type / skill outside the allowed values; a choice
question whose right answer is among the wrong ones, with duplicate or empty options, with fewer than 2 options, or with a different
number of wrong options in English and Japanese; a score question whose levels differ in number between the languages or whose score is
out of range; a two-picture question with verdict ok or fix (it must be rewrite_1image or drop: one picture per question).
The `answer` key of a fix (the format axis choice:n / yesno / score:n) is never trusted: answer_format is recomputed from the options.

Effects (state of the row / status of the idmap): ok -> reviewed / kept; fix -> changed / rewritten (only if the content really
changed, else reviewed); drop -> dropped / dropped (the row stays in the file; consumers must skip review.state == "dropped");
rewrite_1image -> reviewed / pending (a new picture is needed: the row stays as it is and the note says what to do). Each effect adds a
history entry {date, what, why} unless the same (what, why) is already there, so running the tool twice changes nothing.
A state never goes backwards (unreviewed < reviewed < changed < dropped) except by --force-state.

New questions (origin "new") are handled like the others, with two differences: they have no row in idmap_legacy_v1.csv (their
manifests/idmap_v1_new_<tag>.csv is regenerated from the rows), and --apply writes ONLY the files that received a verdict (a base group
file, or the new_<tag>.jsonl of that tag), so one writer's apply never rewrites another writer's file.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import taxonomy  # noqa: E402
from datasets.tools import v1_io  # noqa: E402

VERDICTS = ("ok", "fix", "drop", "rewrite_1image")
DIFFICULTIES = taxonomy.V1_DIFFICULTIES
IMAGE_TYPES = taxonomy.V1_IMAGE_TYPES
SKILLS = taxonomy.V1_SKILLS
TEXT_IMAGE_TYPE, TEXT_SKILL = taxonomy.V1_TEXT_IMAGE_TYPE, taxonomy.V1_TEXT_SKILL
FIX_KEYS = {"instr_en": str, "instr_ja": str, "correct_en": str, "correct_ja": str, "wrong_en": list, "wrong_ja": list,
            "difficulty": str, "image_type": str, "skill": str, "answer": str,
            # extension for yes/no and score questions (418 + 49 of them): the right answer itself can be wrong
            "truth": bool, "levels_en": list, "levels_ja": list, "score": int}
CHOICE_ONLY = {"correct_en", "correct_ja", "wrong_en", "wrong_ja"}
RANK = {s: i for i, s in enumerate(v1_io.REVIEW_STATES)}
ANSWER_RE = re.compile(r"^(choice:\d+|yesno|score:\d+)$")


def _norm(s: str) -> str:
    return " ".join(s.split()).casefold()


# ----------------------------------------------------------------------------------------------------------------- reading
def read_outputs(out_dir: pathlib.Path, prefixes: tuple = ()) -> tuple:
    """([entry], [error]) over every <out_dir>/*.jsonl (only the files whose name starts with one of ``prefixes``, if given). An entry
    is the parsed line plus _file and _line."""
    entries, errors = [], []
    for p in sorted(pathlib.Path(out_dir).glob("*.jsonl")):
        if prefixes and not p.name.startswith(tuple(prefixes)):
            continue
        for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if not ln.strip():
                continue
            try:
                e = json.loads(ln)
            except ValueError as ex:
                errors.append("%s:%d: not JSON (%s)" % (p.name, n, ex))
                continue
            if not isinstance(e, dict):
                errors.append("%s:%d: not an object" % (p.name, n))
                continue
            e["_file"], e["_line"] = p.name, n
            entries.append(e)
    return entries, errors


def batch_members(review_dir: pathlib.Path) -> dict:
    """{batch name: set of ids} from work/review/batch_*.json and new_*.json (empty if the batches were not exported)."""
    out = {}
    for p in sorted(list(pathlib.Path(review_dir).glob("batch_*.json")) + list(pathlib.Path(review_dir).glob("new_*_*.json"))):
        out[p.stem] = {q["id"] for q in json.loads(p.read_text(encoding="utf-8"))["questions"]}
    return out


# -------------------------------------------------------------------------------------------------------------- validation
def effective(row: dict, fix: dict) -> dict:
    """The text fields of `row` after `fix` (language -> dict), used to validate the result."""
    out = {}
    for lang in (row.get("langs") or ["en", "ja"]):
        q = row[lang]
        d = {"instr": fix.get("instr_" + lang, q["instr"])}
        if row["kind"] == "choice":
            d["correct"] = fix.get("correct_" + lang, q["correct"])
            d["wrong"] = fix.get("wrong_" + lang, q["wrong"])
        elif row["kind"] == "score":
            d["levels"] = fix.get("levels_" + lang, q["levels"])
        out[lang] = d
    return out


def validate_entry(e: dict, row: dict | None) -> list:
    """Problems of one line (empty list = valid). `row` = the v1 row of e["id"] (None if unknown)."""
    where = "%s:%d %s" % (e.get("_file"), e.get("_line"), e.get("id"))
    bad = lambda m: "%s: %s" % (where, m)
    errs = []
    if not isinstance(e.get("id"), str) or row is None:
        return [bad("unknown v1 id")]
    v = e.get("verdict")
    if v not in VERDICTS:
        return [bad("verdict must be one of %s, got %r" % ("|".join(VERDICTS), v))]
    extra = set(e) - {"id", "verdict", "issues", "fix", "reason", "_file", "_line"}
    if extra:
        errs.append(bad("unknown keys %s" % sorted(extra)))
    iss = e.get("issues", [])
    if not isinstance(iss, list) or not all(isinstance(x, str) and x.strip() for x in iss):
        errs.append(bad("issues must be a list of non-empty strings"))
    reason = e.get("reason")
    if v != "ok" and not (isinstance(reason, str) and reason.strip()):
        errs.append(bad("reason is required for verdict %s" % v))
    if reason is not None and not isinstance(reason, str):
        errs.append(bad("reason must be a string"))
    fix = e.get("fix")
    if v != "fix":
        if fix:
            errs.append(bad("fix is only allowed with verdict fix"))
    elif not isinstance(fix, dict) or not fix:
        errs.append(bad("verdict fix needs a non-empty fix object"))
    if len(row.get("local_images", [])) > 1 and v in ("ok", "fix"):
        errs.append(bad("two-picture question: verdict must be rewrite_1image or drop"))
    if v != "fix" or not isinstance(fix, dict) or not fix:
        return errs
    # ---- the fix itself
    kind, grp = row["kind"], row["group"]
    langs = row.get("langs") or ["en", "ja"]
    for k, val in fix.items():
        if k not in FIX_KEYS:
            errs.append(bad("unknown fix key %r" % k))
            continue
        t = FIX_KEYS[k]
        if not isinstance(val, t) or (t is int and isinstance(val, bool)):
            errs.append(bad("fix.%s must be %s" % (k, t.__name__)))
            continue
        if k.endswith(("_en", "_ja")) and k.split("_")[-1] not in langs:
            errs.append(bad("fix.%s: the question has no such language" % k))
        if k in CHOICE_ONLY and kind != "choice":
            errs.append(bad("fix.%s only for choice questions" % k))
        if k == "truth" and kind != "noul":
            errs.append(bad("fix.truth only for yes/no questions"))
        if k in ("levels_en", "levels_ja", "score") and kind != "score":
            errs.append(bad("fix.%s only for score questions" % k))
        if k == "difficulty" and val not in DIFFICULTIES:
            errs.append(bad("difficulty must be easy|medium|hard"))
        if k == "image_type" and (val not in IMAGE_TYPES if grp != "txt" else val != TEXT_IMAGE_TYPE):
            errs.append(bad("image_type %r not allowed for group %s" % (val, grp)))
        if k == "skill" and (val not in SKILLS if grp != "txt" else val != TEXT_SKILL):
            errs.append(bad("skill %r not allowed for group %s" % (val, grp)))
        if k == "answer" and not ANSWER_RE.match(val):
            errs.append(bad("answer must look like choice:n | yesno | score:n"))
        if k.startswith("instr_") and not val.strip():
            errs.append(bad("fix.%s is empty" % k))
        if t is list and not all(isinstance(x, str) for x in val):
            errs.append(bad("fix.%s must be a list of strings" % k))
    if errs:
        return errs
    eff = effective(row, fix)
    n_wrong = set()
    for lang, d in eff.items():
        if kind == "choice":
            opts = [d["correct"]] + list(d["wrong"])
            if any(not o.strip() for o in opts):
                errs.append(bad("%s: empty option" % lang))
            if len(opts) < 2:
                errs.append(bad("%s: a choice question needs at least 2 options" % lang))
            if len({_norm(o) for o in opts}) != len(opts):
                errs.append(bad("%s: duplicate options (the right answer must not appear among the wrong ones)" % lang))
            n_wrong.add(len(d["wrong"]))
        elif kind == "score":
            lv = d["levels"]
            if len(lv) < 2 or any(not s.strip() for s in lv) or len({_norm(s) for s in lv}) != len(lv):
                errs.append(bad("%s: levels need >= 2 distinct non-empty strings" % lang))
            n_wrong.add(len(lv))
    if len(n_wrong) > 1:
        errs.append(bad("English and Japanese differ in the number of %s" % ("wrong options" if kind == "choice" else "levels")))
    if kind == "score" and len(n_wrong) == 1:
        n = next(iter(n_wrong))
        if not 0 <= int(fix.get("score", row["answer"])) < n:
            errs.append(bad("score out of range for %d levels" % n))
    return errs


def validate(entries: list, rows_by_id: dict, members: dict) -> list:
    errs, seen = [], {}
    for e in entries:
        errs += validate_entry(e, rows_by_id.get(e.get("id")))
        i = e.get("id")
        if i in seen:
            errs.append("%s:%d %s: appears twice (also %s:%d)" % (e["_file"], e["_line"], i, *seen[i]))
        else:
            seen[i] = (e["_file"], e["_line"])
        b = pathlib.Path(e["_file"]).stem
        if members and i in rows_by_id and (b not in members or i not in members[b]):
            errs.append("%s:%d %s: not a member of batch %s" % (e["_file"], e["_line"], i, b))
    return errs


# ------------------------------------------------------------------------------------------------------------------ applying
def apply_fix(row: dict, fix: dict) -> list:
    """Change `row` in place; returns ["key: old -> new", ...] for what really changed."""
    changes = []

    def setv(label, d, key, new):
        if d.get(key) != new:
            changes.append("%s: %s -> %s" % (label, json.dumps(d.get(key), ensure_ascii=False), json.dumps(new, ensure_ascii=False)))
            d[key] = new

    relabelled = any(h.get("what") == "image_type" for h in row.get("review", {}).get("history", []))
    for k, val in fix.items():
        if k == "answer":
            continue                                    # recomputed below
        if k == "image_type" and relabelled:
            continue                                    # tools/relabel_image_type.py set it later on purpose: a re-run keeps that
        if k.startswith("instr_"):
            setv(k, row[k[-2:]], "instr", val)
        elif k.startswith(("correct_", "wrong_")):
            setv(k, row[k[-2:]], k.split("_")[0], val)
        elif k.startswith("levels_"):
            setv(k, row[k[-2:]], "levels", val)
        elif k == "truth":
            setv(k, row, "answer", val)
        elif k == "score":
            setv(k, row, "answer", val)
        else:                                           # difficulty / image_type / skill
            setv(k, row, k, val)
    new_fmt = v1_io.answer_format(row)[0]
    if row.get("answer_format") != new_fmt:
        changes.append("answer_format: %s -> %s" % (row.get("answer_format"), new_fmt))
        row["answer_format"] = new_fmt
    return changes


def target_state(verdict: str, changed: bool) -> str:
    return {"ok": "reviewed", "fix": "changed" if changed else "reviewed", "drop": "dropped", "rewrite_1image": "reviewed"}[verdict]


def apply_entries(by_group: dict, idmap: list, entries: list, date: str, force_state: bool = False, new_rows: list = ()) -> dict:
    """Apply validated entries in place. Returns the summary used by the report. ``new_rows``: the rows of the new_<tag>.jsonl
    files (no id-map row: their manifests are regenerated from the rows afterwards)."""
    rows = {r["id"]: r for r in list(v1_io.all_rows(by_group)) + list(new_rows)}
    im = {m["v1_id"]: m for m in idmap}
    S = dict(verdicts=collections.Counter(), by_group=collections.defaultdict(collections.Counter), fixes=[], issues=collections.Counter(),
             noop=[], changed_rows=0, warnings=[])
    for e in entries:
        row, m, v = rows[e["id"]], im.get(e["id"]), e["verdict"]
        S["verdicts"][v] += 1
        S["by_group"][row["group"]][v] += 1
        S["issues"].update(x.strip() for x in e.get("issues", []))
        changes = apply_fix(row, e["fix"]) if v == "fix" else []
        if v == "fix":
            fmt = e["fix"].get("answer")
            if fmt and fmt != row["answer_format"]:
                S["warnings"].append("%s: reviewer said answer=%s, recomputed %s" % (e["id"], fmt, row["answer_format"]))
            if changes:
                S["fixes"].append((e["id"], changes, e.get("reason", "")))
            else:
                S["noop"].append(e["id"])
        rev = row["review"]
        tgt = target_state(v, bool(changes))
        if force_state or RANK[tgt] >= RANK[rev["state"]]:
            rev["state"] = tgt
        what = {"ok": "reviewed: no change", "drop": "dropped", "rewrite_1image": "needs a 1-picture rebuild (or drop)",
                "fix": "fix: " + "; ".join(changes) if changes else "reviewed: fix already applied"}[v]
        why = (e.get("reason") or "; ".join(e.get("issues", [])) or "").strip()
        already = v == "fix" and not changes and rev["state"] in ("changed", "dropped")      # re-run of a fix that is in the file
        if not already and not any(h["what"] == what and h["why"] == why for h in rev["history"]):
            rev["history"].append({"date": date, "what": what, "why": why})
        if changes:
            S["changed_rows"] += 1
        if m is None:                                   # a new question: nothing in idmap_legacy_v1.csv to update
            continue
        # id map
        m["review_state"] = "reviewed" if m["review_state"] in ("unreviewed", "reviewed") else m["review_state"]
        if v == "ok" and m["status"] == "kept":
            pass
        elif v == "fix" and m["status"] in ("kept", "rewritten"):
            m["status"] = "rewritten"
            if why:
                m["change_note"] = why
        elif v == "drop":
            m["status"], m["change_note"] = "dropped", why
        elif v == "rewrite_1image" and m["status"] not in ("rewritten", "dropped"):     # a later rebuild / dedupe is not undone
            m["status"], m["change_note"] = "pending", "rewrite_1image: " + why
    return S


def report(S: dict, n_rows: int, n_entries: int, missing: int, applied: bool) -> str:
    L = ["# Review result (%s)" % ("APPLIED" if applied else "dry run: nothing written"), "",
         "%d lines read, %d of %d v1 questions have no verdict yet." % (n_entries, missing, n_rows), "", "## Verdicts", "",
         "| group | ok | fix | drop | rewrite_1image |", "|---|---|---|---|---|"]
    for g in v1_io.GROUPS:
        c = S["by_group"].get(g, {})
        L.append("| %s | %d | %d | %d | %d |" % (g, c.get("ok", 0), c.get("fix", 0), c.get("drop", 0), c.get("rewrite_1image", 0)))
    t = S["verdicts"]
    L.append("| **total** | %d | %d | %d | %d |" % (t["ok"], t["fix"], t["drop"], t["rewrite_1image"]))
    L += ["", "%d rows changed; %d fix lines changed nothing (already applied)." % (S["changed_rows"], len(S["noop"])), ""]
    if S["warnings"]:
        L += ["## Warnings", ""] + ["- " + w for w in S["warnings"]] + [""]
    if S["issues"]:
        L += ["## Issues named most often", ""] + ["- %s (%d)" % kv for kv in S["issues"].most_common(15)] + [""]
    L += ["## Fixes", ""]
    for qid, changes, why in S["fixes"]:
        L.append("- **%s** (%s)" % (qid, why))
        L += ["  - " + c for c in changes]
    return "\n".join(L) + "\n"


def process(review_dir, v1dir=v1_io.V1DIR, manifests=v1_io.MANIFESTS, date=None, apply=False, force_state=False, report_path=None,
            tags=None) -> tuple:
    """Read, validate and (with apply) write. Returns (exit code, text). ``v1dir`` / ``manifests`` can point at a copy (tests).
    ``tags``: only the verdict files ``out/new_<tag>_*.jsonl`` of these new-question tags are read (and so only those files are written):
    what a new-question writer must use, because out/ also holds the base verdicts and other writers' files."""
    date = date or datetime.date.today().isoformat()
    rdir = pathlib.Path(review_dir)
    entries, errs = read_outputs(rdir / "out", tuple("new_%s_" % t for t in tags) if tags else ())
    by_group, by_tag = v1_io.load_v1(v1dir), v1_io.load_new(v1dir)
    rows = {r["id"]: r for r in v1_io.all_rows(by_group) + v1_io.all_new_rows(by_tag)}
    errs += validate(entries, rows, batch_members(rdir))
    if errs:
        return 2, "REJECTED: %d problems, nothing written\n" % len(errs) + "".join("  %s\n" % x for x in errs[:200])
    work_groups, work_new = copy.deepcopy(by_group), copy.deepcopy(by_tag)
    work_map = copy.deepcopy(v1_io.load_idmap(manifests))
    S = apply_entries(work_groups, work_map, entries, date, force_state, new_rows=v1_io.all_new_rows(work_new))
    md = report(S, len(rows), len(entries), len(rows) - len({e["id"] for e in entries}), apply)
    if report_path:
        pathlib.Path(report_path).write_text(md, encoding="utf-8", newline="\n")
    if apply:
        touched = {e["id"] for e in entries}
        groups = {g for g, rs in by_group.items() if any(r["id"] in touched for r in rs)}
        tags = {t for t, rs in by_tag.items() if any(r["id"] in touched for r in rs)}
        if groups:                                      # only what received a verdict is written
            v1_io.save_v1({g: work_groups[g] for g in groups}, v1dir)
            v1_io.save_idmap(work_map, manifests)
            v1_io.write_questions_csv(work_groups, manifests)
        if tags:
            v1_io.save_new({t: work_new[t] for t in tags}, v1dir)
            v1_io.write_new_manifests(work_new, manifests, tags=sorted(tags))
    return 0, md


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-dir", default=str(ROOT / "work" / "review"))
    ap.add_argument("--v1dir", default=str(v1_io.V1DIR), help="question directory (default datasets/questions/v1)")
    ap.add_argument("--manifests", default=str(v1_io.MANIFESTS))
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="date written into history entries")
    ap.add_argument("--tag", action="append", default=None,
                    help="new questions: read only out/new_<tag>_*.jsonl (repeatable). A new-question writer always passes its own tag")
    ap.add_argument("--apply", action="store_true", help="write the result (default: dry run)")
    ap.add_argument("--force-state", action="store_true", help="let a later verdict lower review.state")
    ap.add_argument("--report", default=None, help="also write the report here")
    a = ap.parse_args()
    code, text = process(a.review_dir, pathlib.Path(a.v1dir), pathlib.Path(a.manifests), a.date, a.apply, a.force_state, a.report,
                         a.tag)
    print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
