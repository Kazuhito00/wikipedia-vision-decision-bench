# -*- coding: utf-8 -*-
"""Build the v1 report page (report/v1_report.py) from ANY set of results, without editing report/.

    python colab/make_v1_report.py [--out work/colab/out/v1_report.html] [--runs-dir results/runs/v1] [--include-all-blocks]

report/v1_report.py is written for one trial (jevision cpu / cuda and openai, the `all` blocks, git-ignored dist/v1 files, a summary_v1.json
and a per_question_v1.csv made by runner/analyze_v1.py). This wrapper makes those inputs from what the Colab run produced, in a TEMPORARY
folder (the real dist/ and results/ are never written):

  * results/runs/v1/<model>_<set code>_<lang>_224<suffix>.json|csv blocks (photo / biz / rsn / txt / all / new) are merged per
    (model, suffix, language) into one run, as the report expects (`<model>_v1all_<lang>_224<suffix>`);
  * only the (id, language) pairs that EVERY run answered are compared (a run that did not ask a question must not count as wrong);
  * dist/v1/cases_v1.jsonl and questions_v1.jsonl are rebuilt from datasets/questions (build_v1's own record functions, no pictures needed);
  * MODELS / RUNS / DIST of the report module are replaced at run time, and the one line that compares with per_question_v1.csv (which
    names jev_cpu / jev_cuda / openai) is neutralised IN MEMORY. If that line changed, this stops with a message instead of guessing.
Only blocks that a Colab run made (a sidecar in work/colab/blocks) are used, unless --include-all-blocks.
Pictures are not embedded (--no-images): images-224px.zip is not part of dist/ on a fresh clone.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import re
import sys
import tempfile
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BLOCK = re.compile(r"^(?P<model>[a-z0-9]+)_(?P<code>v1photo|v1biz|v1rsn|v1txt|v1all|v1new)_(?P<lang>en|ja)_(?P<px>\d+)(?P<suffix>.*)$")
COLORS = ["#3b73d8", "#e0861a", "#2a9d6f", "#c0453f", "#8a5fc7", "#b58900", "#2b9bb5", "#d2578f", "#6c7a89", "#7f9c1e", "#a8643c", "#4c6ef5", "#12a594"]


def device_of(suffix: str) -> str:
    return "cuda" if suffix.startswith("_cuda") else "cpu" if suffix.startswith("_cpu") else "remote"


def collect(runs_dir: pathlib.Path, blocks_dir: pathlib.Path, include_all: bool) -> dict:
    """{(model, suffix): {lang: [(block, json, csv rows)]}}"""
    out: dict = {}
    for p in sorted(runs_dir.glob("*.json")):
        m = BLOCK.match(p.stem)
        if not m or "_smoke" in m["suffix"]:
            continue
        if not include_all and not (blocks_dir / (p.stem + ".env.json")).exists():
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("dataset_version") != "v1":
            continue
        rows = list(csv.DictReader(open(p.with_suffix(".csv"), encoding="utf-8", newline=""))) if p.with_suffix(".csv").exists() else []
        out.setdefault((m["model"], m["suffix"]), {}).setdefault(m["lang"], []).append((p.stem, m["code"], rec, rows))
    return out


def merge_rows(blocks) -> list:
    seen, rows = set(), []
    for _, code, _, rs in sorted(blocks, key=lambda b: b[1] != "v1all"):      # an `all` block first: it covers the others
        for r in rs:
            if r["id"] not in seen:
                seen.add(r["id"])
                rows.append(r)
    return rows


def merge_meta(blocks) -> dict:
    metas = [b[2] for b in blocks]
    m = dict(metas[0])
    m["questions_in_block"] = sum(x.get("questions_in_block") or 0 for x in metas)
    m["started"] = min(x.get("started") or "" for x in metas) or None
    m["finished"] = max(x.get("finished") or "" for x in metas) or None
    us = [x["usage"] for x in metas if x.get("usage")]
    if us:
        m["usage"] = {k: sum(u.get(k) or 0 for u in us) for k in us[0]}
    return m


def build_dist_lite(dist: pathlib.Path, keep: dict) -> int:
    """cases_v1.jsonl / questions_v1.jsonl without pictures, restricted to the (id, lang) pairs in `keep` (id -> set of langs)."""
    from datasets import build_v1 as B, loader
    rows = loader.load_rows("v1")
    rowmap = {r["id"]: r for r in rows}
    cases = [B.case_record(c, rowmap) for c in loader.load_v1_cases(images_root=pathlib.Path("."), strict_passages=False)]
    kept = []
    for c in cases:
        langs = [l for l in c["langs"] if l in keep.get(c["id"], ())]
        if langs:
            kept.append(dict(c, langs=langs))
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "cases_v1.jsonl").write_bytes(B.jl(kept))
    (dist / "questions_v1.jsonl").write_bytes(B.jl([B.question_record(r) for r in rows]))
    return len(kept)


def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    work = pathlib.Path(os.environ.get("BENCH_WORK") or ROOT / "work")
    ap.add_argument("--out", default=str(work / "colab" / "out" / "v1_report.html"))
    ap.add_argument("--runs-dir", default=str(ROOT / "results" / "runs" / "v1"))
    ap.add_argument("--blocks-dir", default=str(work / "colab" / "blocks"))
    ap.add_argument("--include-all-blocks", action="store_true", help="also use blocks that this machine did not run (no Colab sidecar)")
    a = ap.parse_args(argv)

    from runner import cases as _rc                                      # noqa: F401  (import check)
    from datasets import loader
    from adapters import REGISTRY
    groups = collect(pathlib.Path(a.runs_dir), pathlib.Path(a.blocks_dir), a.include_all_blocks)
    if not groups:
        print("no v1 results to report (blocks of this machine: none in %s)" % a.runs_dir)
        return 2
    # runs: one per (model, suffix); both languages (an absent one stays empty)
    runs = {}
    for (model, suffix), by_lang in groups.items():
        runs[(model, suffix)] = {lg: (merge_rows(b), merge_meta(b)) for lg, b in by_lang.items()}
    pairs = None
    for k, by in runs.items():
        have = {(r["id"], lg) for lg, (rows, _) in by.items() for r in rows}
        pairs = have if pairs is None else pairs & have
    if not pairs:
        print("the runs have no (question, language) in common: nothing to compare (check --sample / sets of each model)")
        return 2
    keep: dict = {}
    for i, lg in pairs:
        keep.setdefault(i, set()).add(lg)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="v1report_"))
    dist, runs_tmp = tmp / "dist", tmp / "runs"
    runs_tmp.mkdir(parents=True)
    n_cases = build_dist_lite(dist, keep)

    models = {}
    for (model, suffix), by in sorted(runs.items()):
        dev = device_of(suffix)
        key = model + suffix
        stem = "%s_v1all_{lang}_224%s" % (model, suffix)
        any_lang = next(iter(by.values()))
        for lg in ("en", "ja"):
            rows, meta = by.get(lg, ([], any_lang[1]))
            rows = [r for r in rows if (r["id"], lg) in pairs]
            cols = list(rows[0]) if rows else ["dataset_version", "id", "model", "lang", "kind", "expected", "got", "ok", "rev_ok", "ms"]
            with open(runs_tmp / (stem.format(lang=lg) + ".csv"), "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            (runs_tmp / (stem.format(lang=lg) + ".json")).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        name = REGISTRY.get(model, (None, model))[1]
        m = models.setdefault(model, dict(key=model, name=name, short=name.split(" ")[0], kind="api" if dev == "remote" else "local", color=None, runs=[]))
        m["runs"].append(dict(key=key, label="%s %s" % (name, {"cpu": "CPU", "cuda": "GPU", "remote": "API"}[dev]), file=stem, device=dev))
    mlist = list(models.values())
    # the report pairs the FIRST cpu run with the FIRST cuda run: put a model that has both first, so that the pair is one model on two devices
    both = [m for m in mlist if {r["device"] for r in m["runs"]} >= {"cpu", "cuda"}]
    if both:
        mlist.remove(both[0])
        mlist.insert(0, both[0])
        both[0]["runs"].sort(key=lambda r: r["device"] != "cpu")
    else:
        print("note: no model has both a cpu and a cuda run: the report's CPU-vs-GPU panel (if any) would compare different models; read it with care")
    for i, m in enumerate(mlist):
        m["color"] = COLORS[i % len(COLORS)]

    prim = [m["runs"][0]["key"] for m in mlist]
    pa, pb = prim[0], prim[1] if len(prim) > 1 else prim[0]
    ok = {}
    for k, by in runs.items():
        for lg, (rows, _) in by.items():
            for r in rows:
                if (r["id"], lg) in pairs:
                    ok[(k[0] + k[1], r["id"], lg)] = r["ok"] in ("1", "True", "true")
    wrong = {}
    for (i, lg) in pairs:
        wrong.setdefault(i, []).append(not ok.get((pa, i, lg), False) and not ok.get((pb, i, lg), False))
    (runs_tmp / "summary_v1.json").write_text(json.dumps(dict(cases=len(pairs), both_wrong=sorted(i for i, v in wrong.items() if all(v)), accuracy={},
                                                              label_check_candidates=[]), ensure_ascii=False), encoding="utf-8")
    (runs_tmp / "per_question_v1.csv").write_text("id,lang,ok_jev_cpu,ok_jev_cuda,ok_openai\n", encoding="utf-8")

    src_path = ROOT / "report" / "v1_report.py"
    src = src_path.read_text(encoding="utf-8")
    new, n = re.subn(r"^(\s*)mism = sum\(1 for x in asked if pq_ok\.get.*$", r"\1mism = 0", src, flags=re.M)
    if n != 1:
        print("report/v1_report.py changed (the per_question_v1.csv comparison line was not found): colab/make_v1_report.py needs an update")
        return 3
    mod = types.ModuleType("v1_report_colab")
    mod.__file__ = str(src_path)
    sys.modules["v1_report_colab"] = mod
    exec(compile(new, str(src_path), "exec"), mod.__dict__)                 # noqa: S102  (the repository's own report code, one line neutralised)
    mod.MODELS, mod.RUNS, mod.DIST = mlist, runs_tmp, dist
    print("v1 report: %d runs (%s), %d (question, language) pairs answered by every run, %d questions" %
          (sum(len(m["runs"]) for m in mlist), ", ".join(r["key"] for m in mlist for r in m["runs"]), len(pairs), n_cases))
    out = pathlib.Path(a.out)
    return mod.main(["--out", str(out), "--no-images"])


if __name__ == "__main__":
    sys.exit(main())
