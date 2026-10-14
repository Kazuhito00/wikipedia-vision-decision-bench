# -*- coding: utf-8 -*-
"""Build the v1 report page (comparison table, selectable details, all-model heat map, question explorer) from the v1 results.

    uv run python -m report.v1_report [--out results/まとめ_v1.html] [--no-images] [--runs-dir results/runs/v1] [--dist-dir dist/v1]

Inputs:
    <dist-dir>/cases_v1.jsonl, questions_v1.jsonl, manifest_v1.json, images-224px.zip   (the question set; pictures only for thumbnails)
    <runs-dir>/<model>_v1all_{en,ja}_224[_cpu|_cuda].csv|json   every such pair is a run: models and runs are DETECTED (report/v1_models.py),
        nothing is listed by hand; a new model only needs its result files. Optional: summary_v1.json, per_question_v1.csv (cross-checks of
        the numbers, written by runner/analyze_v1.py), label_check_v1.md, blocks_v1_cpu.txt (calibration of the CPU blocks).
All numbers on the page are computed here from those files. The page is one self-contained HTML (no CDN; charts are CSS/inline SVG; light
and dark theme). Only the (question, language) pairs that EVERY run answered are compared (--all-pairs: all asked; a missing answer is wrong).

The page embeds small thumbnails of the pictures (Wikimedia Commons files and drawn/generated figures). It is therefore a LOCAL,
GENERATED page: *.html is git-ignored and the page must not be committed or published. --no-images builds it without pictures.
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import math
import pathlib
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from report import v1_models  # noqa: E402

DIST = ROOT / "dist" / "v1"
RUNS = ROOT / "results" / "runs" / "v1"
LANGS = v1_models.LANGS
#: a timed CPU block counts only if the calibration (GLiNER ms) before and after it was at most this (quiet machine: ~170-250)
CAL_LIMIT = 600
#: Decisions API has no published price; the GPT-6 Luna input rate is an assumption (stated on the page)
PRICING = dict(usd_per_m_input=0.10,
               basis="GPT-6 Luna の入力料金（100 万トークンあたり 0.10 ドル）を仮に当てはめた概算。Decisions API 自体の料金は未公表。")
#: names in summary_v1.json / per_question_v1.csv (runner/analyze_v1.py) -> run key
SUMMARY_KEYS = {"jev_cpu": "jevision_cpu", "jev_cuda": "jevision_cuda", "openai": "openai"}

KIND_LABEL = {"choice": "choice", "noul": "yes/no", "score": "score"}
GROUP_ORDER = ["photo", "biz", "rsn", "txt"]
DIFF_ORDER = ["easy", "medium", "hard"]
ORIGIN_LABEL = {"base": "base", "new": "new"}


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def ok_of(v) -> int:
    return 1 if str(v).strip() in ("1", "True", "true") else 0


def nopt_label(kind, n_opts):
    if kind == "noul":
        return "yes/no"
    return "%s %d" % (kind, n_opts)


def nopt_bucket(kind, n_opts):
    if kind == "noul":
        return "yes/no"
    if kind == "score":
        return "score %d" % n_opts
    if n_opts >= 10:
        return "choice 10+"
    if n_opts >= 7:
        return "choice 7-9"
    return "choice %d" % n_opts


def bucket_order(label):
    if label == "yes/no":
        return (2, 0)
    kind, n = label.split(" ")
    n = int(re.match(r"\d+", n).group())
    return (0 if kind == "choice" else 1, n)


def option_text(case, lang, got):
    L = case[lang]
    if case["kind"] == "noul":
        yes, no = ("yes", "no") if lang == "en" else ("はい", "いいえ")
        return yes if got in ("True", "1") else (no if got in ("False", "0") else "—")
    try:
        return L["options"][int(got)]
    except (ValueError, IndexError, TypeError):
        return "—"


def make_thumbs(cases, enabled, dist):
    """image path -> index; list of data URIs (one per unique picture)."""
    paths = []
    seen = {}
    for c in cases:
        for p in c["images"][:1]:
            if p not in seen:
                seen[p] = len(paths)
                paths.append(p)
    if not enabled:
        return seen, [], paths
    from PIL import Image
    uris = []
    z = zipfile.ZipFile(dist / "images-224px.zip")
    for p in paths:
        im = Image.open(io.BytesIO(z.read(p))).convert("RGB")
        im.thumbnail((160, 160))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
        uris.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode())
    return seen, uris, paths


def parse_blocks(runs_dir):
    out = []
    p = runs_dir / "blocks_v1_cpu.txt"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\S+) before=(\d*) after=(\d*)\s*(.*)", ln.strip())
            if m:
                b, a = m.group(2), m.group(3)
                out.append(dict(block=m.group(1), before=int(b) if b else None, after=int(a) if a else None, time=m.group(4),
                                valid=bool(b and a and max(int(b), int(a)) <= CAL_LIMIT)))
    return out


def parse_label_check(runs_dir):
    p = runs_dir / "label_check_v1.md"
    res = dict(title="", intro="", rows=[], notes=[])
    if not p.exists():
        return res
    for ln in p.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("# "):
            res["title"] = s[2:]
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if cells[0] in ("id",) or set(cells[0]) <= set("-: "):
                continue
            if len(cells) >= 4:
                res["rows"].append(dict(id=cells[0], q=cells[1], exp=cells[2], finding="|".join(cells[3:])))
        elif not res["intro"]:
            res["intro"] = s
        else:
            res["notes"].append(s)
    return res


def _vram(run, meta_json):
    """Peak GPU memory (MiB, the largest over the run's blocks) and a tooltip text; (None, "") when no block recorded it (older results / CPU / API)."""
    g = [(meta_json[(run["key"], lg)] or {}).get("gpu_memory") for lg in LANGS if (run["key"], lg) in meta_json]
    g = [x for x in g if x]
    if not g:
        return None, ""
    own = [x["process_peak"] for x in g if x.get("process_peak") is not None]
    if own:
        v, how = max(own), "このプロセスのピーク"
    else:
        dl = [x["gpu_delta"] for x in g if x.get("gpu_delta") is not None]
        if not dl:
            return None, ""
        v, how = max(dl), "GPU 全体のピーク − 開始前（他のプログラムの増減を含む）"
    tot = next((x["gpu_total"] for x in g if x.get("gpu_total")), None)
    return v, "%s: %d MiB%s。CUDA アロケータが確保した量で、モデルが必要とする最小量ではありません" % (how, v, (" / GPU %d MiB" % tot) if tot else "")


def timing_status(run, metas, blocks):
    """How far the time of a run can be trusted: ok (CPU, calibration within the limit) / uncal (CPU, no calibration record) /
    invalid (CPU or GPU, calibration out of range: the time is NOT shown) / ref (GPU, no calibration: reference only) / api (round trip)."""
    if run["device"] == "remote":
        return "api"
    cals = [m.get("calibration") for m in metas.values() if m]
    flags = [c.get("timing_valid") for c in cals if c and c.get("timing_valid") is not None]
    if not flags:
        bl = [b for lg, stem in run["files"].items() for b in blocks if b["block"] == stem]
        flags = [b["valid"] for b in bl]
    if flags and not all(flags):
        return "invalid"
    if run["device"] == "cuda":
        return "ref"
    return "ok" if flags else "uncal"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "results" / "まとめ_v1.html"))
    ap.add_argument("--runs-dir", default=str(RUNS), help="folder with the <model>_v1all_<lang>_224[_cpu|_cuda].csv|json results")
    ap.add_argument("--dist-dir", default=str(DIST), help="folder with cases_v1.jsonl, questions_v1.jsonl (and images-224px.zip)")
    ap.add_argument("--no-images", action="store_true", help="no thumbnails (the page then has no pictures)")
    ap.add_argument("--images-base", default="", help="folder (relative to the page) holding <base>/224/<path> and <base>/original/<path>: the picture dialog then offers the 224 px and the original files (local use only; never publish)")
    ap.add_argument("--all-pairs", action="store_true", help="compare every asked (question, language), not only those every run answered")
    ap.add_argument("--only", default="", help="comma separated run keys (e.g. jevision_cpu,openai): leave the others out")
    args = ap.parse_args(argv)
    runs_dir, dist = pathlib.Path(args.runs_dir), pathlib.Path(args.dist_dir)
    no_images = args.no_images or not (dist / "images-224px.zip").exists()
    if no_images and not args.no_images:
        print("note: %s not found: no pictures on the page" % (dist / "images-224px.zip"))

    cases = read_jsonl(dist / "cases_v1.jsonl")
    qmeta = {q["id"]: q for q in read_jsonl(dist / "questions_v1.jsonl")}
    manifest = json.loads((dist / "manifest_v1.json").read_text(encoding="utf-8")) if (dist / "manifest_v1.json").exists() else {}
    summary = json.loads((runs_dir / "summary_v1.json").read_text(encoding="utf-8")) if (runs_dir / "summary_v1.json").exists() else {}

    # ---- models and runs: detected from the result files
    found = v1_models.discover_runs(runs_dir)
    if args.only:
        keep = {k.strip() for k in args.only.split(",") if k.strip()}
        found = {k: v for k, v in found.items() if k in keep}
    if not found:
        print("no <model>_v1all_<lang>_224[_cpu|_cuda].csv|json results in %s" % runs_dir)
        return 2
    MODELS = v1_models.build_models(found)
    runs = [r for m in MODELS for r in m["runs"]]
    rkeys = [r["key"] for r in runs]
    mdl_of = {r["key"]: m for m in MODELS for r in m["runs"]}

    # ---- the answers: run key -> (id, lang) -> row
    ans, meta_json = {}, {}
    for r in runs:
        rows = {}
        for lang, stem in r["files"].items():
            for row in read_csv(runs_dir / (stem + ".csv")):
                rows[(row["id"], row["lang"])] = row
            meta_json[(r["key"], lang)] = json.loads((runs_dir / (stem + ".json")).read_text(encoding="utf-8"))
        ans[r["key"]] = rows

    # ---- one record per compared (id, lang)
    universe = [(c["id"], lang) for c in cases for lang in c["langs"] if lang in LANGS]
    pairs = set(universe)
    if not args.all_pairs:
        for k in rkeys:
            pairs &= set(ans[k])
    dropped = len(universe) - len(pairs)
    if dropped:
        print("note: %d of %d asked (question, language) pairs were not answered by every run and are left out (--all-pairs keeps them as wrong)"
              % (dropped, len(universe)))
    asked = []
    for c in cases:
        qm = qmeta[c["id"]]
        for lang in c["langs"]:
            if lang not in LANGS or (c["id"], lang) not in pairs:
                continue
            n_opts = len(c[lang]["options"]) if c[lang].get("options") else 0
            rec = dict(id=c["id"], lang=lang, group=c["group"], kind=c["kind"], kindl=KIND_LABEL[c["kind"]],
                       diff=c["difficulty"], origin=ORIGIN_LABEL.get(qm["origin"], qm["origin"]),
                       itype=qm["image_type"], skill=qm["skill"], modality=("text only" if c["modality"] == "text" else "picture"),
                       nopt=nopt_bucket(c["kind"], n_opts), nopt_full=nopt_label(c["kind"], n_opts), case=c)
            for k in rkeys:
                row = ans[k].get((c["id"], lang))
                if row is None:
                    rec[k] = dict(ok=0, got="NA", ms=None, missing=True)
                else:
                    rec[k] = dict(ok=ok_of(row["ok"]), got=row["got"], ms=int(float(row["ms"])) if row.get("ms") else None)
            asked.append(rec)
    if not asked:
        print("no (question, language) in common between the runs: nothing to compare (check the result files)")
        return 2

    # ---- aggregates
    def agg(recs, keyfn):
        d = defaultdict(lambda: dict(n=0, c={k: 0 for k in rkeys}))
        for x in recs:
            kk = keyfn(x)
            d[kk]["n"] += 1
            for k in rkeys:
                d[kk]["c"][k] += x[k]["ok"]
        return d

    dims = [("group", "group", GROUP_ORDER), ("origin", "origin", ["base", "new"]), ("kind", "kindl", ["choice", "yes/no", "score"]),
            ("nopt", "nopt", None), ("difficulty", "diff", DIFF_ORDER), ("image_type", "itype", None), ("skill", "skill", None),
            ("modality", "modality", ["picture", "text only"]), ("nopt_full", "nopt_full", None)]

    def order_rows(d, order, key):
        if order:
            return [(k, d[k]) for k in order if k in d]
        if key in ("nopt", "nopt_full"):
            return sorted(d.items(), key=lambda t: bucket_order(t[0]))
        return sorted(d.items(), key=lambda t: -t[1]["n"])

    aggs = {}
    for lg in ("all",) + LANGS:
        recs = asked if lg == "all" else [x for x in asked if x["lang"] == lg]
        a = {"overall": dict(n=len(recs), c={k: sum(x[k]["ok"] for x in recs) for k in rkeys})}
        if lg == "all":
            a["lang"] = [dict(label=k, n=v["n"], c=v["c"]) for k, v in order_rows(agg(recs, lambda x: x["lang"]), ["en", "ja"], "lang")]
        for name, attr, order in dims:
            d = agg(recs, lambda x, attr=attr: x[attr])
            a[name] = [dict(label=k, n=v["n"], c=v["c"]) for k, v in order_rows(d, order, name)]

        def heat(rk, ck, rorder, corder):
            d = agg(recs, lambda x: (x[rk], x[ck]))
            rows = rorder or [k for k, _ in sorted(agg(recs, lambda x: x[rk]).items(), key=lambda t: -t[1]["n"])]
            cols = corder or [k for k, _ in sorted(agg(recs, lambda x: x[ck]).items(), key=lambda t: -t[1]["n"])]
            return dict(rows=rows, cols=cols, cells={"%s|%s" % k: v for k, v in d.items()})
        a["heat_skill_itype"] = heat("skill", "itype", None, None)
        a["heat_diff_kind"] = heat("diff", "kindl", DIFF_ORDER, ["choice", "yes/no", "score"])
        a["heat_group_diff"] = heat("group", "diff", GROUP_ORDER, DIFF_ORDER)
        a["heat_group_origin"] = heat("group", "origin", GROUP_ORDER, ["base", "new"])
        aggs[lg] = a

    # ---- time per run (a time that is not measured properly is not shown) and CPU/GPU pairs of one model
    blocks = parse_blocks(runs_dir)
    for r in runs:
        r["timing"] = timing_status(r, {lg: meta_json.get((r["key"], lg)) for lg in LANGS}, blocks)
    shown = {r["key"] for r in runs if r["timing"] != "invalid"}

    def ms_stats(vals):
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            return {}
        return dict(n=len(vals), median=statistics.median(vals), mean=statistics.fmean(vals), p90=vals[int(0.9 * (len(vals) - 1))],
                    p99=vals[int(0.99 * (len(vals) - 1))], max=vals[-1], total_s=sum(vals) / 1000)
    speed = {"runs": [], "by_group": [], "models": {}}
    for r in runs:
        k = r["key"]
        for lg in ("all",) + LANGS:
            recs = asked if lg == "all" else [x for x in asked if x["lang"] == lg]
            speed["runs"].append(dict(run=k, lang=lg, **(ms_stats([x[k]["ms"] for x in recs]) if k in shown else {})))
        for g in GROUP_ORDER:
            speed["by_group"].append(dict(run=k, group=g, **(ms_stats([x[k]["ms"] for x in asked if x["group"] == g]) if k in shown else {})))
    edges = [10 ** (e / 4) for e in range(0, 21)]     # 1 ms .. 100 s
    hist = {}
    for r in runs:
        if r["key"] not in shown:
            continue
        cnt = [0] * (len(edges) - 1)
        for x in asked:
            v = x[r["key"]]["ms"]
            if v:
                cnt[min(len(cnt) - 1, max(0, int(math.log10(max(v, 1)) * 4)))] += 1
        hist[r["key"]] = cnt
    speed["hist"] = dict(edges=edges, counts=hist)
    for m in MODELS:
        cpu = next((r for r in m["runs"] if r["device"] == "cpu"), None)
        gpu = next((r for r in m["runs"] if r["device"] == "cuda"), None)
        if not (cpu and gpu):
            continue
        same_got = sum(1 for x in asked if x[cpu["key"]]["got"] == x[gpu["key"]]["got"])
        same_ok = sum(1 for x in asked if x[cpu["key"]]["ok"] == x[gpu["key"]]["ok"])
        e = dict(cpu=cpu["key"], gpu=gpu["key"], n=len(asked), same_got=same_got, same_ok=same_ok,
                 diff_ids=["%s/%s" % (x["id"], x["lang"]) for x in asked if x[cpu["key"]]["got"] != x[gpu["key"]]["got"]][:50])
        if cpu["key"] in shown and gpu["key"] in shown:
            pr = [(x[cpu["key"]]["ms"], x[gpu["key"]]["ms"]) for x in asked if x[cpu["key"]]["ms"] and x[gpu["key"]]["ms"]]
            if pr:
                ratios = [a / b for a, b in pr]
                e["pairs"] = [[a, b] for a, b in pr]
                e["ratio"] = dict(median=statistics.median(ratios), mean=statistics.fmean(ratios), total=sum(a for a, _ in pr) / sum(b for _, b in pr),
                                  n=len(pr), gpu_slower=sum(1 for q in ratios if q < 1))
        speed["models"][m["key"]] = e

    # ---- CPU speed reference (timing-only blocks, speed_cpu_v1.json: a few questions on the CPU in a GPU-only session). NOT an accuracy run.
    cpu_speed = []
    sp_path = runs_dir / "speed_cpu_v1.json"
    sp_in = json.loads(sp_path.read_text(encoding="utf-8")).get("models", {}) if sp_path.exists() else {}
    name_of = {m["key"]: m["short"] for m in MODELS}
    for mk, e in sorted(sp_in.items()):
        good = [r for r in e["rows"] if r["ms"] and not r.get("na")]
        ms = sorted(r["ms"] for r in good)
        if not ms:
            continue
        gk = mk + "_cuda"
        pr = [(r["ms"], ans[gk][(r["id"], r["lang"])]) for r in good if gk in ans and (r["id"], r["lang"]) in ans[gk]]
        pr = [(a, int(float(b["ms"]))) for a, b in pr if b.get("ms") and float(b["ms"]) > 0]
        ent = dict(model=mk, name=name_of.get(mk, mk), n=len(ms), planned=e.get("planned"), stopped_early=bool(e.get("stopped_early")),
                   max_seconds=e.get("max_seconds"), median=statistics.median(ms), mean=statistics.fmean(ms), p90=ms[int(0.9 * (len(ms) - 1))], max=ms[-1],
                   threads=e.get("threads"), host=e.get("host"), timing_valid=e.get("timing_valid"), blocks=e.get("blocks"),
                   na=sum(1 for r in e["rows"] if r.get("na")), gpu_key=gk if gk in ans else None)
        if pr:
            ent["gpu_same_median"] = statistics.median(b for _, b in pr)
            ent["cpu_same_median"] = statistics.median(a for a, _ in pr)
            ent["ratio_median"] = statistics.median(a / b for a, b in pr)
            ent["pairs_n"] = len(pr)
        cpu_speed.append(ent)

    # ---- cost (API runs)
    cost = []
    for r in runs:
        if r["device"] != "remote" or mdl_of[r["key"]]["kind"] != "api":
            continue
        tok = {lg: ((meta_json.get((r["key"], lg)) or {}).get("usage") or {}) for lg in LANGS}
        if not any(tok.values()):
            continue
        cost.append(dict(run=r["key"], label=r["label"],
                         model_name=next((meta_json[(r["key"], lg)].get("model_name") for lg in LANGS if (r["key"], lg) in meta_json), None),
                         requests={lg: tok[lg].get("requests") for lg in LANGS}, input_tokens={lg: tok[lg].get("input_tokens") for lg in LANGS},
                         output_tokens={lg: tok[lg].get("output_tokens") for lg in LANGS}, retries={lg: tok[lg].get("retries") for lg in LANGS},
                         round_trip_s={lg: tok[lg].get("round_trip_s") for lg in LANGS}))

    # ---- dataset statistics (the question set itself)
    qs = list(qmeta.values())

    def cnt(fn, order=None):
        c = Counter(fn(q) for q in qs)
        keys = order or [k for k, _ in c.most_common()]
        return [dict(label=k, n=c[k]) for k in keys if k in c]
    nopt_q = Counter(nopt_bucket(c["kind"], len(c["en"]["options"] or []) if "en" in c and c["en"].get("options") else
                                  (len(c["ja"]["options"]) if c["ja"].get("options") else 0)) for c in cases)
    dsstat = dict(
        total=len(qs), asked=len(asked), images=len({p for c in cases for p in c["images"]}),
        group=cnt(lambda q: q["group"], GROUP_ORDER), kind=cnt(lambda q: KIND_LABEL[q["kind"]], ["choice", "yes/no", "score"]),
        difficulty=cnt(lambda q: q["difficulty"], DIFF_ORDER),
        origin=cnt(lambda q: ORIGIN_LABEL.get(q["origin"], q["origin"]), ["base", "new"]),
        image_type=cnt(lambda q: q["image_type"]), skill=cnt(lambda q: q["skill"]),
        source=cnt(lambda q: q["source"]),
        lang=cnt(lambda q: "en+ja" if q["lang"] == "both" else "ja only", ["en+ja", "ja only"]),
        nopt=[dict(label=k, n=v) for k, v in sorted(nopt_q.items(), key=lambda t: bucket_order(t[0]))],
        relation=cnt(lambda q: q.get("relation") or "—"),
        group_origin={"%s|%s" % (g, o): sum(1 for q in qs if q["group"] == g and ORIGIN_LABEL.get(q["origin"], q["origin"]) == o)
                      for g in GROUP_ORDER for o in ("base", "new")},
        review=cnt(lambda q: (q.get("review") or {}).get("state", "—")),
        manifest_counts=(json.loads((dist / "images_v1.json").read_text(encoding="utf-8")).get("counts") if (dist / "images_v1.json").exists() else None),
    )

    # ---- explorer items and thumbnails
    seen, uris, img_paths = make_thumbs(cases, not no_images, dist)
    label_check = parse_label_check(runs_dir)
    lc_ids = set(summary.get("label_check_candidates", []))
    items, placeholder = [], 0
    for c in cases:
        qm = qmeta[c["id"]]
        it = dict(id=c["id"], g=c["group"], o=ORIGIN_LABEL.get(qm["origin"], qm["origin"]), k=KIND_LABEL[c["kind"]], d=c["difficulty"],
                  it=qm["image_type"], sk=qm["skill"], im=seen[c["images"][0]] if c["images"] else -1, lc=int(c["id"] in lc_ids), l={})
        for lang in c["langs"]:
            if lang not in LANGS or (c["id"], lang) not in pairs:
                continue
            L = c[lang]
            e = c["expected"]
            if c["kind"] == "noul":
                exp_text = ("yes" if lang == "en" else "はい") if e is True else ("no" if lang == "en" else "いいえ")
            else:
                exp_text = L["options"][e]
            a = {}
            for k in rkeys:
                row = ans[k].get((c["id"], lang))
                a[k] = [option_text(c, lang, row["got"]) if row else "—", ok_of(row["ok"]) if row else 0,
                        int(float(row["ms"])) if row and row.get("ms") else 0]
            if str(L.get("state") or "").startswith("[passage "):
                placeholder += 1
            it["l"][lang] = dict(q=L["instr"], s=L.get("state") or "", o=L.get("options") or [], e=exp_text, a=a)
        if it["l"]:
            items.append(it)

    # ---- check against summary_v1.json and per_question_v1.csv (written by runner/analyze_v1.py; both optional)
    checks = []

    def chk(name, got, want):
        checks.append(dict(name=name, got=got, want=want, ok=(abs(got - want) < 1e-9)))
    OV = aggs["all"]["overall"]
    if dropped == 0:
        for sk, want in (summary.get("accuracy") or {}).items():
            k = SUMMARY_KEYS.get(sk, sk)
            if k in OV["c"]:
                chk("accuracy " + k, OV["c"][k] / OV["n"], want)
        if "cases" in summary:
            chk("cases", OV["n"], summary["cases"])
        a_k, b_k = SUMMARY_KEYS["jev_cpu"], SUMMARY_KEYS["openai"]
        if a_k in OV["c"] and b_k in OV["c"] and "both_wrong" in summary:
            wrong_all = defaultdict(list)
            for x in asked:
                wrong_all[x["id"]].append(not x[a_k]["ok"] and not x[b_k]["ok"])
            bw_all = sorted(i for i, v in wrong_all.items() if all(v))
            chk("both_wrong ids (jevision_cpu and openai wrong in every language) equal summary", float(bw_all == sorted(summary["both_wrong"])), 1.0)
        pqp = runs_dir / "per_question_v1.csv"
        if pqp.exists():
            pq = read_csv(pqp)
            cols = {c[3:]: c for c in (pq[0].keys() if pq else []) if c.startswith("ok_")}
            for sk, colname in cols.items():
                k = SUMMARY_KEYS.get(sk, sk)
                if k not in OV["c"]:
                    continue
                pqk = {(r["id"], r["lang"]): r[colname] for r in pq}
                mism = sum(1 for x in asked if pqk.get((x["id"], x["lang"])) != str(x[k]["ok"]))
                chk("per_question_v1.csv mismatching rows (%s)" % k, float(mism), 0.0)

    # ---- environments (the `host` key of the result files; a run without it is "unknown")
    hosts, run_host = {}, {}
    for r in runs:
        hs = [meta_json[(r["key"], lg)].get("host") for lg in LANGS if (r["key"], lg) in meta_json]
        hs = [h for h in hs if h and h.get("host_id")]
        ids = []
        for h in hs:
            ids += [h["host_id"]] + [x["host_id"] for x in (h.get("also_resumed_on") or []) if x.get("host_id")]
            hosts.setdefault(h["host_id"], dict(h, runs=[]))
            if r["key"] not in hosts[h["host_id"]]["runs"]:
                hosts[h["host_id"]]["runs"].append(r["key"])
        run_host[r["key"]] = dict(host_id=hs[0]["host_id"] if hs else None, label=hs[0].get("label") if hs else None,
                                  source=hs[0].get("source") if hs else None, remote=bool(hs and hs[0].get("remote")),
                                  threads=hs[0].get("threads") if hs else None, mixed=len(set(ids)) > 1,
                                  missing=len(hs) < len([1 for lg in LANGS if (r["key"], lg) in meta_json]))
    for h in hosts.values():
        h.pop("also_resumed_on", None)

    data = dict(
        hosts=list(hosts.values()), generated=manifest.get("generated_at"), dataset=manifest.get("dataset_version", "v1"),
        models=[dict(key=m["key"], name=m["name"], short=m["short"], kind=m["kind"], color=m["color"], weights_gb=m.get("weights_gb"),
                     runs=[r["key"] for r in m["runs"]]) for m in MODELS],
        runs=[dict(key=r["key"], label=r["label"], device=r["device"], model=mdl_of[r["key"]]["key"], name=mdl_of[r["key"]]["name"],
                   short=mdl_of[r["key"]]["short"], kind=mdl_of[r["key"]]["kind"], color=mdl_of[r["key"]]["color"], timing=r["timing"],
                   weights_gb=next((meta_json[(r["key"], lg)].get("weights_gb") for lg in LANGS if (r["key"], lg) in meta_json
                                    and meta_json[(r["key"], lg)].get("weights_gb") is not None), mdl_of[r["key"]].get("weights_gb")),
                   variant=next((meta_json[(r["key"], lg)].get("variant") for lg in LANGS if (r["key"], lg) in meta_json), None),
                   vram_mib=_vram(r, meta_json)[0], vram_note=_vram(r, meta_json)[1],
                   langs=sorted(r["files"]), host=run_host[r["key"]],
                   ort=next(((meta_json[(r["key"], lg)].get("host") or {}).get("onnxruntime") for lg in LANGS if (r["key"], lg) in meta_json), None)) for r in runs],
        aggs=aggs, speed=speed, cpu_speed=cpu_speed, blocks=blocks, cal_limit=CAL_LIMIT, cost=cost, pricing=PRICING,
        ds=dsstat, label_check=label_check, lc_ids=sorted(lc_ids), checks=checks,
        items=items, thumbs=uris, img_paths=img_paths, img_base=args.images_base or None, has_images=not no_images, dropped=dropped, placeholder=placeholder,
        run_meta=[dict(run=r["key"], lang=lg, providers=meta_json[(r["key"], lg)].get("providers_used"), threads=meta_json[(r["key"], lg)].get("threads"),
                       started=meta_json[(r["key"], lg)].get("started"), finished=meta_json[(r["key"], lg)].get("finished"),
                       variant=meta_json[(r["key"], lg)].get("variant"), workers=meta_json[(r["key"], lg)].get("workers"),
                       model_name=meta_json[(r["key"], lg)].get("model_name")) for r in runs for lg in LANGS if (r["key"], lg) in meta_json],
    )
    tpl = (HERE / "v1_report_template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace("/*DATA*/null", payload)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    print("wrote %s  (%.1f MB, %d models, %d runs, %d questions, %d compared, %d pictures)" %
          (out, len(html.encode("utf-8")) / 1e6, len(MODELS), len(runs), len(items), len(asked), len(uris)))
    for e in cpu_speed:
        print("  %-16s CPU speed reference: median %d ms over %d q (timing only, not in the accuracy tables)" % (e["model"], e["median"], e["n"]))
    for k in rkeys:
        print("  %-16s %d/%d = %.2f%%   timing: %s" % (k, OV["c"][k], OV["n"], 100 * OV["c"][k] / OV["n"], next(r["timing"] for r in runs if r["key"] == k)))
    bad = [c for c in checks if not c["ok"]]
    for c in checks:
        print("  check %-70s %s" % (c["name"], "OK" if c["ok"] else "MISMATCH got=%r want=%r" % (c["got"], c["want"])))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
