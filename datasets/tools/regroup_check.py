# -*- coding: utf-8 -*-
"""Gate of the regrouping: the totals per model must not change when the 4 old groups become the 4 new groups.

    python datasets/tools/regroup_check.py --logs <eval_common dir> [--html <old report html>] [--out datasets/manifests/regroup_check.md]

Reads the old measurement logs (results_w, results_s, results_t of eval_common/: lines "ok  <id> got=.. exp=.. rev=.. ms=..") with
exactly the rules of eval_common/wiki_report.py (same LINE regex, NUL/CR stripping, precedence: main -> _fill -> _exp, each later
file overwriting the earlier; the timed logs of results_t only add ids that are still missing; QEV skips the questions tagged
two-images), then tallies correct / answered per (model, language) twice:
  old   wikipedia / expansion / synthetic / reasoning       (group of the legacy id, as wiki_report.py: source_unverified, id prefix)
  new   photo / biz / rsn / txt                              (legacy id -> v1 id through manifests/idmap_legacy_v1.csv, group from the v1 id)
and compares: per model and language the grand totals (correct and answered) and the identities
  photo = wikipedia + expansion,  biz + rsn = synthetic + reasoning,  rsn = reasoning + the 94 reasoning-tagged synthetic questions.
txt (text-only, 87) has no logs in these directories: reported as "no results", not as 0.
With --html it also compares the old tallies with the answers embedded in the existing report (the oracle: 'ok' of every
item/model/language), so a wrong log parsing cannot go unnoticed. The tool only reads; it writes the markdown given by --out.
Exit code 1 on any mismatch.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import loader, taxonomy  # noqa: E402

LINE = re.compile(r"(ok |XX )\s+(\S+)\s+got=(\S+) exp=(\S+) rev=(\S+) ms=(\d+)")
MODELS = ["openjev", "intern", "jevision", "onejev", "qev", "strands", "openjev4", "onejev4", "clef", "openai"]
OUT_OF_SCOPE = {"qev": "two-images"}
# source file of the legacy rows -> (results dir, log name pattern); the same table as wiki_report.main()
SOURCES = [("linked.jsonl", "results_w", "%s_wiki_%s_224"), ("synthetic.jsonl", "results_s", "%s_syn_%s_224"),
           ("reasoning.jsonl", "results_s", "%s_rsn_%s_224")]


def read_lines(path: pathlib.Path):
    raw = path.read_bytes().replace(bytes([0]), b"")
    return raw.decode("utf-8", errors="replace").replace(chr(13), "").split(chr(10))


def parse(path: pathlib.Path) -> dict:
    out = {}
    if not path.exists():
        return out
    for ln in read_lines(path):
        m = LINE.search(ln)
        if m:
            out[m.group(2)] = m.group(1) == "ok "
    return out


def results_for(logs: pathlib.Path, res_dir: str, pattern: str, key: str, lang: str) -> dict:
    """id -> ok, with the precedence of wiki_report.main()."""
    stem = pattern % (key, lang)
    rec = {}
    for suffix in ("", "_fill", "_exp"):
        rec.update(parse(logs / res_dir / (stem + suffix + ".log")))
    for cid, ok in parse(logs / "results_t" / (stem + ".log")).items():
        rec.setdefault(cid, ok)
    return rec


def compute(logs: pathlib.Path) -> dict:
    """{(model, lang, legacy_id): ok} for every answered question (out-of-scope ones omitted)."""
    res = {}
    for fname, res_dir, pattern in SOURCES:
        rows = [r for r in loader.load_rows("legacy", (fname,)) if r["modality"] == "image"]
        for key in MODELS:
            for lang in ("en", "ja"):
                rec = results_for(logs, res_dir, pattern, key, lang)
                for r in rows:
                    if key in OUT_OF_SCOPE and OUT_OF_SCOPE[key] in r.get("tags", []):
                        continue
                    if r["id"] in rec:
                        res[(key, lang, r["id"])] = rec[r["id"]]
    return res


def tally(res: dict, group_of: dict) -> dict:
    """{(model, lang, group): [correct, answered]}"""
    t: dict = {}
    for (key, lang, qid), ok in res.items():
        g = group_of.get(qid)
        if g is None:
            continue
        c = t.setdefault((key, lang, g), [0, 0])
        c[0] += ok
        c[1] += 1
    return t


def run(logs: pathlib.Path, html: pathlib.Path | None = None, manifests: pathlib.Path = loader.MANIFESTS) -> dict:
    rows = loader.load_rows("legacy")
    res = compute(logs)
    old_of = {r["id"]: taxonomy.old_group(r) for r in rows}
    # new group: through the id map (legacy id -> v1 id) and the group of the v1 id
    v1_of = {m["legacy_id"]: m["v1_id"] for m in loader.idmap_legacy_v1(manifests)}
    new_of = {legacy: v1.split("-")[0] for legacy, v1 in v1_of.items()}
    sub94 = {r["id"]: "rsn_from_synthetic" for r in rows if r["id"].startswith("syn-") and "reasoning" in r["tags"]}
    old = tally(res, old_of)
    new = tally(res, new_of)
    sub = tally(res, sub94)
    out = dict(old=old, new=new, sub=sub, problems=[], rows=[])
    g = lambda t, k, l, grp: t.get((k, l, grp), [0, 0])
    for k in MODELS:
        for l in ("en", "ja"):
            o = {grp: g(old, k, l, grp) for grp in taxonomy.OLD_GROUPS}
            n = {grp: g(new, k, l, grp) for grp in taxonomy.NEW_GROUPS}
            s94 = g(sub, k, l, "rsn_from_synthetic")
            tot_o = [sum(v[0] for v in o.values()), sum(v[1] for v in o.values())]
            tot_n = [sum(v[0] for v in n.values()), sum(v[1] for v in n.values())]
            checks = {
                "total": tot_o == tot_n,
                "photo=wikipedia+expansion": n["photo"] == [o["wikipedia"][0] + o["expansion"][0], o["wikipedia"][1] + o["expansion"][1]],
                "biz+rsn=synthetic+reasoning": [n["biz"][0] + n["rsn"][0], n["biz"][1] + n["rsn"][1]] ==
                                               [o["synthetic"][0] + o["reasoning"][0], o["synthetic"][1] + o["reasoning"][1]],
                "rsn=reasoning+94": n["rsn"] == [o["reasoning"][0] + s94[0], o["reasoning"][1] + s94[1]],
                "txt has no results": n["txt"] == [0, 0],
            }
            for name, ok in checks.items():
                if not ok:
                    out["problems"].append("%s %s: %s" % (k, l, name))
            out["rows"].append(dict(model=k, lang=l, old=o, new=n, s94=s94, tot_old=tot_o, tot_new=tot_n, checks=checks))
    if html:
        t = html.read_text(encoding="utf-8")
        d, _ = json.JSONDecoder().raw_decode(t[t.find('{"items":'):])
        ho: dict = {}
        for it in d["items"]:
            for l in it["langs"]:
                for k, a in it[l]["answers"].items():
                    if a:
                        c = ho.setdefault((k, l, it["set"]), [0, 0])
                        c[0] += a["ok"]
                        c[1] += 1
        out["html_diff"] = []
        for k in MODELS:
            for l in ("en", "ja"):
                for grp in taxonomy.OLD_GROUPS:
                    a, b = g(old, k, l, grp), ho.get((k, l, grp), [0, 0])
                    if a != b:
                        out["html_diff"].append((k, l, grp, a, b))
        out["html_items"] = len(d["items"])
    return out


def markdown(out: dict, logs_label: str, html_label: str | None) -> str:
    f = lambda v: "%d/%d" % tuple(v)
    L = ["# Regrouping check (legacy: old 4 groups vs new 4 groups)", "",
         "Generated by `datasets/tools/regroup_check.py` (logs: `%s`). Numbers are correct/answered per model and language." % logs_label,
         "Rule: the regrouping only merges and moves questions, so the **total per model and language must be identical** and the "
         "group identities must hold (photo = wikipedia + expansion; biz + rsn = synthetic + reasoning; rsn = reasoning + the 94 "
         "reasoning-tagged synthetic questions). txt (87 text-only questions) has no results in these logs: no result, not 0%.", ""]
    L += ["| model | lang | wikipedia | expansion | synthetic | reasoning | **old total** | photo | biz | rsn | txt | **new total** | rsn from synthetic (94) | match |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        o, n = r["old"], r["new"]
        L.append("| %s | %s | %s | %s | %s | %s | **%s** | %s | %s | %s | - | **%s** | %s | %s |" % (
            r["model"], r["lang"], f(o["wikipedia"]), f(o["expansion"]), f(o["synthetic"]), f(o["reasoning"]), f(r["tot_old"]),
            f(n["photo"]), f(n["biz"]), f(n["rsn"]), f(r["tot_new"]), f(r["s94"]), "OK" if all(r["checks"].values()) else "**MISMATCH**"))
    L.append("")
    if html_label:
        L += ["## Oracle: the existing HTML report", "",
              "Tallies of the old 4 groups from the logs compared with the `ok` flags embedded in `%s` (%d items): %s" % (
                  html_label, out["html_items"], "identical for every model, language and group." if not out["html_diff"]
                  else "**%d differences**" % len(out["html_diff"]))]
        for d in out["html_diff"]:
            L.append("- %s %s %s: logs %s vs html %s" % d)
        L.append("")
    L.append("## Result")
    L.append("")
    L.append("**PASS: all totals and identities match.**" if not out["problems"] else "**FAIL**: " + "; ".join(out["problems"]))
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True, help="eval_common/ directory (contains results_w, results_s, results_t)")
    ap.add_argument("--html", default=None)
    ap.add_argument("--out", default=str(loader.MANIFESTS / "regroup_check.md"))
    a = ap.parse_args()
    out = run(pathlib.Path(a.logs), pathlib.Path(a.html) if a.html else None)
    md = markdown(out, "eval_common/results_{w,s,t}", pathlib.Path(a.html).name if a.html else None)
    pathlib.Path(a.out).write_text(md, encoding="utf-8", newline="\n")
    print(md)
    bad = bool(out["problems"]) or bool(out.get("html_diff"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
