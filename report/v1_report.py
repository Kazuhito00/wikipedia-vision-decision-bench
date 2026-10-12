# -*- coding: utf-8 -*-
"""Build the v1 report page (dashboard, charts, question explorer) from the v1 measurement results.

    uv run python -m report.v1_report [--out results/まとめ_v1.html] [--no-images]

Inputs (all under the bench root):
    dist/v1/cases_v1.jsonl, questions_v1.jsonl, manifest_v1.json, images-224px.zip   (the question set; pictures only for thumbnails)
    results/runs/v1/<model run>.csv|json  (one per language and run), summary_v1.json, label_check_v1.md, blocks_v1_cpu.txt
All numbers on the page are computed here from those files; nothing is typed in by hand. The page is one self-contained HTML
(no CDN; charts are CSS/inline SVG; light and dark theme).

The page embeds small thumbnails of the pictures (Wikimedia Commons files and drawn/generated figures). It is therefore a LOCAL,
GENERATED page: *.html is git-ignored and the page must not be committed or published. --no-images builds it without pictures.

To add a model: append an entry to MODELS (runs: first run is the primary one; file = file stem with {lang}), re-run.
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import pathlib
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "dist" / "v1"
RUNS = ROOT / "results" / "runs" / "v1"
LANGS = ("en", "ja")
#: a timed CPU block counts only if the calibration (GLiNER ms) before and after it was at most this (quiet machine: ~170-250)
CAL_LIMIT = 600

#: the models on the page. A model has one or more runs; the first run is its primary result (the one in the tables); the others are
#: shown in the agreement/time comparison. Add a model here to get it into every table and chart.
MODELS = [
    dict(key="jev", name="JEVision 0.8B", short="JEVision", kind="local", color="#3b73d8",
         runs=[dict(key="jev_cpu", label="JEVision CPU", file="jevision_v1all_{lang}_224_cpu", device="cpu"),
               dict(key="jev_cuda", label="JEVision GPU", file="jevision_v1all_{lang}_224_cuda", device="cuda")]),
    dict(key="openai", name="OpenAI Decisions API (gpt-6-luna)", short="OpenAI", kind="api", color="#e0861a",
         runs=[dict(key="openai", label="OpenAI API", file="openai_v1all_{lang}_224", device="remote")]),
]
#: Decisions API has no published price; the GPT-6 Luna input rate is an assumption (stated on the page)
PRICING = dict(usd_per_m_input=0.10,
               basis="GPT-6 Luna の入力料金（100 万トークンあたり 0.10 ドル）を仮に当てはめた概算。Decisions API 自体の料金は未公表。")

KIND_LABEL = {"choice": "choice", "noul": "yes/no", "score": "score"}
GROUP_ORDER = ["photo", "biz", "rsn", "txt"]
DIFF_ORDER = ["easy", "medium", "hard"]
ORIGIN_LABEL = {"legacy-derived": "polished", "new": "new"}


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


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


def make_thumbs(cases, enabled):
    """image path -> index; list of data URIs (one per unique picture)."""
    paths = []
    seen = {}
    for c in cases:
        for p in c["images"][:1]:
            if p not in seen:
                seen[p] = len(paths)
                paths.append(p)
    uris = []
    if not enabled:
        return seen, [""] * len(paths)
    from PIL import Image
    z = zipfile.ZipFile(DIST / "images-224px.zip")
    for p in paths:
        im = Image.open(io.BytesIO(z.read(p))).convert("RGB")
        im.thumbnail((120, 120))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=58, optimize=True)
        uris.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode())
    return seen, uris


def parse_blocks():
    out = []
    p = RUNS / "blocks_v1_cpu.txt"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\S+) before=(\d*) after=(\d*)\s*(.*)", ln.strip())
            if m:
                b, a = m.group(2), m.group(3)
                out.append(dict(block=m.group(1), before=int(b) if b else None, after=int(a) if a else None, time=m.group(4),
                                valid=bool(b and a and max(int(b), int(a)) <= CAL_LIMIT)))
    return out


def parse_label_check():
    p = RUNS / "label_check_v1.md"
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


def pct(c, n):
    return None if not n else c / n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "results" / "まとめ_v1.html"))
    ap.add_argument("--no-images", action="store_true", help="no thumbnails (the page then has no pictures)")
    args = ap.parse_args(argv)

    cases = read_jsonl(DIST / "cases_v1.jsonl")
    qmeta = {q["id"]: q for q in read_jsonl(DIST / "questions_v1.jsonl")}
    manifest = json.loads((DIST / "manifest_v1.json").read_text(encoding="utf-8")) if (DIST / "manifest_v1.json").exists() else {}
    summary = json.loads((RUNS / "summary_v1.json").read_text(encoding="utf-8"))
    runs = [r for m in MODELS for r in m["runs"]]
    prim = [m["runs"][0]["key"] for m in MODELS]

    # ---- the answers: run key -> (id, lang) -> row
    ans = {}
    meta_json = {}
    for r in runs:
        rows = {}
        for lang in LANGS:
            for row in read_csv(RUNS / (r["file"].format(lang=lang) + ".csv")):
                rows[(row["id"], row["lang"])] = row
            meta_json[(r["key"], lang)] = json.loads((RUNS / (r["file"].format(lang=lang) + ".json")).read_text(encoding="utf-8"))
        ans[r["key"]] = rows

    # ---- one record per asked (id, lang)
    asked = []
    for c in cases:
        qm = qmeta[c["id"]]
        for lang in c["langs"]:
            if lang not in LANGS:
                continue
            n_opts = len(c[lang]["options"]) if c[lang].get("options") else 0
            rec = dict(id=c["id"], lang=lang, group=c["group"], kind=c["kind"], kindl=KIND_LABEL[c["kind"]],
                       diff=c["difficulty"], origin=ORIGIN_LABEL.get(qm["origin"], qm["origin"]),
                       itype=qm["image_type"], skill=qm["skill"], modality=("text only" if c["modality"] == "text" else "picture"),
                       nopt=nopt_bucket(c["kind"], n_opts), nopt_full=nopt_label(c["kind"], n_opts), case=c)
            for r in runs:
                row = ans[r["key"]].get((c["id"], lang))
                if row is None:
                    rec[r["key"]] = dict(ok=0, got="NA", ms=None, missing=True)
                else:
                    rec[r["key"]] = dict(ok=int(row["ok"]), got=row["got"], ms=int(row["ms"]) if row["ms"] else None)
            asked.append(rec)

    # ---- aggregates
    def agg(recs, keyfn):
        d = defaultdict(lambda: dict(n=0, c={r["key"]: 0 for r in runs}))
        for x in recs:
            k = keyfn(x)
            d[k]["n"] += 1
            for r in runs:
                d[k]["c"][r["key"]] += x[r["key"]]["ok"]
        return d

    dims = [("group", "group", GROUP_ORDER), ("origin", "origin", ["polished", "new"]), ("kind", "kindl", ["choice", "yes/no", "score"]),
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
        a = {"overall": dict(n=len(recs), c={r["key"]: sum(x[r["key"]]["ok"] for x in recs) for r in runs})}
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
        a["heat_group_origin"] = heat("group", "origin", GROUP_ORDER, ["polished", "new"])
        aggs[lg] = a

    # ---- agreement between the two primary models (and CPU vs GPU)
    pa, pb = prim[0], prim[1] if len(prim) > 1 else prim[0]
    venn = {}
    for lg in ("all",) + LANGS:
        recs = asked if lg == "all" else [x for x in asked if x["lang"] == lg]
        v = Counter()
        for x in recs:
            v[("A" if x[pa]["ok"] else "a") + ("B" if x[pb]["ok"] else "b")] += 1
        venn[lg] = dict(both=v["AB"], a_only=v["Ab"], b_only=v["aB"], none=v["ab"], n=len(recs))
    both_same_wrong = 0
    for x in asked:
        if not x[pa]["ok"] and not x[pb]["ok"] and x[pa]["got"] == x[pb]["got"]:
            both_same_wrong += 1
    venn["same_wrong"] = both_same_wrong
    venn_group = {g: Counter(("A" if x[pa]["ok"] else "a") + ("B" if x[pb]["ok"] else "b") for x in asked if x["group"] == g) for g in GROUP_ORDER}
    venn_group = {g: dict(both=v["AB"], a_only=v["Ab"], b_only=v["aB"], none=v["ab"]) for g, v in venn_group.items()}

    # ---- speed: CPU vs GPU etc.
    speed = {"runs": [], "pairs": [], "by_group": []}
    local = [r for m in MODELS for r in m["runs"] if r["device"] in ("cpu", "cuda")]
    cpu = next((r for r in local if r["device"] == "cpu"), None)
    gpu = next((r for r in local if r["device"] == "cuda"), None)

    def ms_stats(vals):
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            return {}
        return dict(n=len(vals), median=statistics.median(vals), mean=statistics.fmean(vals), p90=vals[int(0.9 * (len(vals) - 1))],
                    p99=vals[int(0.99 * (len(vals) - 1))], max=vals[-1], total_s=sum(vals) / 1000)
    for r in runs:
        for lg in ("all",) + LANGS:
            recs = asked if lg == "all" else [x for x in asked if x["lang"] == lg]
            speed["runs"].append(dict(run=r["key"], lang=lg, **ms_stats([x[r["key"]]["ms"] for x in recs])))
        for g in GROUP_ORDER:
            speed["by_group"].append(dict(run=r["key"], group=g, **ms_stats([x[r["key"]]["ms"] for x in asked if x["group"] == g])))
    if cpu and gpu:
        pairs = [(x["id"], x["lang"], x[cpu["key"]]["ms"], x[gpu["key"]]["ms"]) for x in asked
                 if x[cpu["key"]]["ms"] and x[gpu["key"]]["ms"]]
        speed["pairs"] = [[p[2], p[3]] for p in pairs]
        ratios = [p[2] / p[3] for p in pairs]
        speed["ratio"] = dict(median=statistics.median(ratios), mean=statistics.fmean(ratios),
                              total=sum(p[2] for p in pairs) / sum(p[3] for p in pairs), n=len(pairs),
                              gpu_slower=sum(1 for q in ratios if q < 1))
        same_got = sum(1 for x in asked if x[cpu["key"]]["got"] == x[gpu["key"]]["got"])
        same_ok = sum(1 for x in asked if x[cpu["key"]]["ok"] == x[gpu["key"]]["ok"])
        speed["agree"] = dict(n=len(asked), same_got=same_got, same_ok=same_ok,
                              diff_ids=["%s/%s" % (x["id"], x["lang"]) for x in asked if x[cpu["key"]]["got"] != x[gpu["key"]]["got"]][:50])
        # first-answer warm-up is part of the times; report the first question's time per block
        speed["first"] = {r["key"] + "_" + lg: next((x[r["key"]]["ms"] for x in asked if x["lang"] == lg), None) for r in (cpu, gpu) for lg in LANGS}
        # log-binned histogram of ms
        import math
        edges = [10 ** (e / 4) for e in range(0, 21)]     # 1 ms .. 100 s
        hist = {}
        for r in runs:
            cnt = [0] * (len(edges) - 1)
            for x in asked:
                v = x[r["key"]]["ms"]
                if v:
                    i = min(len(cnt) - 1, max(0, int(math.log10(max(v, 1)) * 4)))
                    cnt[i] += 1
            hist[r["key"]] = cnt
        speed["hist"] = dict(edges=edges, counts=hist)
    blocks = parse_blocks()

    # ---- cost (API)
    cost = []
    for m in MODELS:
        if m["kind"] != "api":
            continue
        for r in m["runs"]:
            tok = {lg: (meta_json[(r["key"], lg)].get("usage") or {}) for lg in LANGS}
            cost.append(dict(run=r["key"], label=r["label"], model_name=meta_json[(r["key"], "en")].get("model_name"),
                             requests={lg: tok[lg].get("requests") for lg in LANGS},
                             input_tokens={lg: tok[lg].get("input_tokens") for lg in LANGS},
                             output_tokens={lg: tok[lg].get("output_tokens") for lg in LANGS},
                             retries={lg: tok[lg].get("retries") for lg in LANGS},
                             round_trip_s={lg: tok[lg].get("round_trip_s") for lg in LANGS}))

    # ---- dataset statistics (the question set itself)
    qs = list(qmeta.values())
    def cnt(fn, order=None):
        c = Counter(fn(q) for q in qs)
        keys = order or [k for k, _ in c.most_common()]
        return [dict(label=k, n=c[k]) for k in keys if k in c]
    case_by_id = {c["id"]: c for c in cases}
    nopt_q = Counter(nopt_bucket(c["kind"], len(c["en"]["options"] or []) if "en" in c and c["en"].get("options") else
                                  (len(c["ja"]["options"]) if c["ja"].get("options") else 0)) for c in cases)
    dsstat = dict(
        total=len(qs), asked=len(asked), images=len({p for c in cases for p in c["images"]}),
        group=cnt(lambda q: q["group"], GROUP_ORDER), kind=cnt(lambda q: KIND_LABEL[q["kind"]], ["choice", "yes/no", "score"]),
        difficulty=cnt(lambda q: q["difficulty"], DIFF_ORDER),
        origin=cnt(lambda q: ORIGIN_LABEL.get(q["origin"], q["origin"]), ["polished", "new"]),
        image_type=cnt(lambda q: q["image_type"]), skill=cnt(lambda q: q["skill"]),
        source=cnt(lambda q: q["source"]),
        lang=cnt(lambda q: "en+ja" if q["lang"] == "both" else "ja only", ["en+ja", "ja only"]),
        nopt=[dict(label=k, n=v) for k, v in sorted(nopt_q.items(), key=lambda t: bucket_order(t[0]))],
        relation=cnt(lambda q: q.get("relation") or "—"),
        group_origin={"%s|%s" % (g, o): sum(1 for q in qs if q["group"] == g and ORIGIN_LABEL.get(q["origin"], q["origin"]) == o)
                      for g in GROUP_ORDER for o in ("polished", "new")},
        review=cnt(lambda q: (q.get("review") or {}).get("state", "—")),
        manifest_counts=(json.loads((DIST / "images_v1.json").read_text(encoding="utf-8")).get("counts") if (DIST / "images_v1.json").exists() else None),
    )

    # ---- explorer items and thumbnails
    seen, uris = make_thumbs(cases, not args.no_images)
    label_check = parse_label_check()
    lc_ids = set(summary.get("label_check_candidates", []))
    items = []
    for c in cases:
        qm = qmeta[c["id"]]
        it = dict(id=c["id"], g=c["group"], o=ORIGIN_LABEL.get(qm["origin"], qm["origin"]), k=KIND_LABEL[c["kind"]], d=c["difficulty"],
                  it=qm["image_type"], sk=qm["skill"], im=seen[c["images"][0]] if c["images"] else -1, lc=int(c["id"] in lc_ids), l={})
        for lang in c["langs"]:
            if lang not in LANGS:
                continue
            L = c[lang]
            e = c["expected"]
            if c["kind"] == "noul":
                exp_text = ("yes" if lang == "en" else "はい") if e is True else ("no" if lang == "en" else "いいえ")
            else:
                exp_text = L["options"][e]
            ok_bits = ""
            a = {}
            for r in runs:
                row = ans[r["key"]].get((c["id"], lang))
                a[r["key"]] = [option_text(c, lang, row["got"]) if row else "—", int(row["ok"]) if row else 0, int(row["ms"]) if row and row["ms"] else 0]
            it["l"][lang] = dict(q=L["instr"], s=L.get("state") or "", o=L.get("options") or [], e=exp_text, a=a)
        items.append(it)

    # ---- check against summary_v1.json and per_question_v1.csv
    checks = []
    def chk(name, got, want):
        checks.append(dict(name=name, got=got, want=want, ok=(abs(got - want) < 1e-9)))
    for key, sk in (("jev_cpu", "jev_cpu"), ("jev_cuda", "jev_cuda"), ("openai", "openai")):
        if key in aggs["all"]["overall"]["c"] and sk in summary.get("accuracy", {}):
            chk("accuracy " + key, aggs["all"]["overall"]["c"][key] / aggs["all"]["overall"]["n"], summary["accuracy"][sk])
    chk("cases", aggs["all"]["overall"]["n"], summary["cases"])
    both_wrong = sorted({x["id"] for x in asked if not x[pa]["ok"] and not x[pb]["ok"]})
    # summary 'both_wrong' = wrong in every language? compare as sets of ids wrong in all asked languages
    wrong_all = defaultdict(list)
    for x in asked:
        wrong_all[x["id"]].append(not x[pa]["ok"] and not x[pb]["ok"])
    bw_all = sorted(i for i, v in wrong_all.items() if all(v))
    chk("both_wrong ids (wrong in every language) equal summary", float(bw_all == sorted(summary["both_wrong"])), 1.0)
    pq = read_csv(RUNS / "per_question_v1.csv")
    pq_ok = {(r["id"], r["lang"]): (r["ok_jev_cpu"], r["ok_jev_cuda"], r["ok_openai"]) for r in pq}
    mism = sum(1 for x in asked if pq_ok.get((x["id"], x["lang"])) != (str(x["jev_cpu"]["ok"]), str(x["jev_cuda"]["ok"]), str(x["openai"]["ok"])))
    chk("per_question_v1.csv mismatching rows", float(mism), 0.0)
    if manifest.get("counts") or True:
        mc = json.loads((DIST / "manifest_v1.json").read_text(encoding="utf-8")) if (DIST / "manifest_v1.json").exists() else {}
    # the 'both wrong in all languages' list for the explorer is computed in JS from the items; here: counts for the headline
    headline = dict(both_wrong_ids=len(bw_all), a_only_ids=None)

    data = dict(
        generated=json.loads(json.dumps(manifest.get("generated_at"))), dataset=manifest.get("dataset_version", "v1"),
        models=[dict(key=m["key"], name=m["name"], short=m["short"], kind=m["kind"], color=m["color"],
                     runs=[dict(key=r["key"], label=r["label"], device=r["device"]) for r in m["runs"]]) for m in MODELS],
        prim=prim, runs=[dict(key=r["key"], label=r["label"], device=r["device"]) for r in runs],
        aggs=aggs, venn=venn, venn_group=venn_group, speed=speed, blocks=blocks, cal_limit=CAL_LIMIT, cost=cost, pricing=PRICING,
        ds=dsstat, label_check=label_check, lc_ids=sorted(lc_ids), summary_cases=summary["cases"], checks=checks,
        items=items, thumbs=uris, has_images=not args.no_images,
        run_meta=[dict(run=r["key"], lang=lg, providers=meta_json[(r["key"], lg)].get("providers_used"), threads=meta_json[(r["key"], lg)].get("threads"),
                       started=meta_json[(r["key"], lg)].get("started"), finished=meta_json[(r["key"], lg)].get("finished"),
                       variant=meta_json[(r["key"], lg)].get("variant"), workers=meta_json[(r["key"], lg)].get("workers"),
                       model_name=meta_json[(r["key"], lg)].get("model_name")) for r in runs for lg in LANGS],
    )
    tpl = (HERE / "v1_report_template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = tpl.replace("/*DATA*/null", payload)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    print("wrote %s  (%.1f MB, %d questions, %d asked, %d pictures)" % (out, len(html.encode("utf-8")) / 1e6, len(items), len(asked), len(uris)))
    for r in runs:
        o = aggs["all"]["overall"]
        print("  %-10s %d/%d = %.2f%%" % (r["key"], o["c"][r["key"]], o["n"], 100 * o["c"][r["key"]] / o["n"]))
    bad = [c for c in checks if not c["ok"]]
    for c in checks:
        print("  check %-60s %s" % (c["name"], "OK" if c["ok"] else "MISMATCH got=%r want=%r" % (c["got"], c["want"])))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
