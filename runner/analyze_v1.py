# -*- coding: utf-8 -*-
"""Summary of the v1 trial measurement (JEVision cpu = main, JEVision cuda = agreement + timing, OpenAI Decisions API).

    python -m runner.analyze_v1 [--old-logs <eval_common dir>] [--out results/runs/v1/summary_v1.md]

Reads results/runs/v1/<block>.csv|json written by runner.run (blocks ``jevision_v1all_<lang>_224_cpu``, ``..._cuda``,
``openai_v1all_<lang>_224``) and the question attributes of datasets/questions/v1 (read only). Writes the markdown, a per-question CSV
(``per_question_v1.csv``: one row per (id, lang) with every model's answer) and ``summary_v1.json``. Nothing is measured here.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from datasets import loader  # noqa: E402

RUNS = ROOT / "results" / "runs" / "v1"
MODELS = [("jev_cpu", "jevision_v1all_%s_224_cpu", "JEVision CPU"), ("jev_cuda", "jevision_v1all_%s_224_cuda", "JEVision GPU"),
          ("openai", "openai_v1all_%s_224", "OpenAI")]
USD_PER_M_INPUT = 0.10      # estimate, same assumption as report/wiki_report.py PRICING (the Decisions API has no published price)


def pct(a, n):
    return "%.1f%% (%d/%d)" % (100.0 * a / n, a, n) if n else "-"


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def load_attrs():
    attrs = {}
    for r in loader.load_rows("v1"):
        af = r["answer_format"]
        kind = r["kind"]
        nopt = int(af.split(":")[1]) if ":" in af else None
        attrs[r["id"]] = dict(id=r["id"], group=r["group"], origin=r.get("origin") or "polished", kind=kind, modality=r["modality"],
                              nopt=("choice %d" % nopt if kind == "choice" else "score %d" % nopt if kind == "score" else "yes/no"),
                              difficulty=r.get("difficulty") or "?", image_type=r.get("image_type") or "?", skill=r.get("skill") or "?",
                              legacy_id=r.get("legacy_id"), derived_from=r.get("derived_from"), langs=r["langs"])
    return attrs


def load_blocks():
    """{model: {(id, lang): row dict}} and {model: [meta json]}"""
    res, meta = {}, {}
    for key, pat, _ in MODELS:
        res[key], meta[key] = {}, []
        for lang in ("en", "ja"):
            p = RUNS / ((pat % lang) + ".csv")
            if not p.exists():
                continue
            for r in csv.DictReader(open(p, encoding="utf-8")):
                res[key][(r["id"], lang)] = dict(got=r["got"], ok=r["ok"] == "1", ms=int(r["ms"]), exp=r["expected"], kind=r["kind"])
            meta[key].append(json.loads((RUNS / ((pat % lang) + ".json")).read_text(encoding="utf-8")))
    return res, meta


def dim_table(title, cases, keyfn, models, order=None):
    groups = collections.defaultdict(list)
    for c in cases:
        groups[keyfn(c)].append(c)
    keys = order or sorted(groups, key=lambda k: (-len(groups[k]), str(k)))
    rows = []
    for k in keys:
        g = groups.get(k, [])
        if not g:
            continue
        rows.append([k, len(g)] + [pct(sum(c["ok"][m] for c in g), len(g)) for m in models])
    return "#### %s\n\n" % title + md_table([title.split(" ")[0] if False else "category", "n"] + [dict((m[0], m[2]) for m in MODELS)[x] for x in models], rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-logs", default=str(ROOT.parent.parent / "eval_common"))
    ap.add_argument("--out", default=str(RUNS / "summary_v1.md"))
    a = ap.parse_args()
    attrs = load_attrs()
    res, meta = load_blocks()
    present = [k for k, _, _ in MODELS if res[k]]
    show = [m for m in ("jev_cpu", "openai") if m in present] or present
    # one case per (id, lang) answered by the main models
    cases = []
    for (qid, lang) in sorted(res[show[0]]):
        c = dict(attrs[qid], lang=lang, ok={m: res[m][(qid, lang)]["ok"] for m in present if (qid, lang) in res[m]},
                 got={m: res[m][(qid, lang)]["got"] for m in present if (qid, lang) in res[m]}, exp=res[show[0]][(qid, lang)]["exp"])
        if all(m in c["ok"] for m in show):
            cases.append(c)
    out = ["# v1 trial measurement: JEVision 0.8B and OpenAI Decisions API\n"]
    out.append("Cases: %d (id x language; en 2596 + ja 2768 = 5364 when complete). Accuracy = correct / asked, NA counted wrong. "
               "JEVision CPU is the main result; JEVision GPU is the agreement check and the time comparison.\n" % len(cases))
    # (a) accuracy tables
    out.append("## (a) Accuracy\n")
    out.append(md_table(["model", "all", "en", "ja"], [[dict((m[0], m[2]) for m in MODELS)[m], pct(sum(c["ok"][m] for c in cases), len(cases)),
                                                         pct(sum(c["ok"][m] for c in cases if c["lang"] == "en"), sum(1 for c in cases if c["lang"] == "en")),
                                                         pct(sum(c["ok"][m] for c in cases if c["lang"] == "ja"), sum(1 for c in cases if c["lang"] == "ja"))]
                                                        for m in [x for x in ("jev_cpu", "jev_cuda", "openai") if x in present]]))
    cases_all = [c for c in cases if all(m in c["ok"] for m in present)]
    models = [m for m in ("jev_cpu", "openai") if m in present]
    out.append(dim_table("language", cases, lambda c: c["lang"], models))
    out.append(dim_table("group", cases, lambda c: c["group"], models, ["photo", "biz", "rsn", "txt"]))
    out.append(dim_table("origin (polished = legacy, polished in v1)", cases, lambda c: c["origin"], models))
    out.append(dim_table("format", cases, lambda c: {"choice": "choice", "noul": "yes/no", "score": "score"}[c["kind"]], models))
    out.append(dim_table("options", cases, lambda c: c["nopt"], models,
                         sorted({c["nopt"] for c in cases}, key=lambda s: (s.split()[0], int(s.split()[1]) if " " in s else 0))))
    out.append(dim_table("difficulty", cases, lambda c: c["difficulty"], models, ["easy", "medium", "hard"]))
    out.append(dim_table("modality", cases, lambda c: "picture" if c["modality"] == "image" else "text only", models))
    out.append(dim_table("image_type", cases, lambda c: c["image_type"], models))
    out.append(dim_table("skill", cases, lambda c: c["skill"], models))
    # (b) text-only controls vs the picture question they came from
    out.append("## (b) Text-only controls (99) vs the picture questions they were made from\n")
    out.append("Caution: the control puts the exact numbers (bar heights, amounts, times) into the `state`, so the text version can be EASIER than "
               "the picture version. The difference is 'answer from text that gives the information' vs 'read it from a 224 px picture', "
               "not a pure 'does the picture matter' effect.\n")
    byid = {(c["id"], c["lang"]): c for c in cases}
    pairs = [(byid[(q, l)], byid[(a_["derived_from"], l)]) for (q, l), _ in [(k, 0) for k in byid] for a_ in [attrs[q]]
             if a_["derived_from"] and a_["modality"] == "text" and (a_["derived_from"], l) in byid]
    rows = []
    for lab, sel in (("all", lambda l: True), ("en", lambda l: l == "en"), ("ja", lambda l: l == "ja")):
        ps = [p for p in pairs if sel(p[0]["lang"])]
        for m in models:
            t, i = sum(p[0]["ok"][m] for p in ps), sum(p[1]["ok"][m] for p in ps)
            both = sum(p[0]["ok"][m] and p[1]["ok"][m] for p in ps)
            rows.append([lab, dict((x[0], x[2]) for x in MODELS)[m], len(ps), pct(i, len(ps)), pct(t, len(ps)),
                         "%+.1f pt" % (100.0 * (t - i) / len(ps)) if ps else "-", both, sum(p[0]["ok"][m] and not p[1]["ok"][m] for p in ps),
                         sum(p[1]["ok"][m] and not p[0]["ok"][m] for p in ps)])
    out.append(md_table(["lang", "model", "pairs", "picture question", "text-only control", "text - picture", "both right", "only text right",
                         "only picture right"], rows))
    # (c) polished questions vs the old bench
    out.append("## (c) Polished (legacy -> v1) questions vs the old bench\n")
    try:
        sys.path.insert(0, str(ROOT / "datasets" / "tools"))
        from datasets.tools import regroup_check as rc  # noqa: WPS433
        old = rc.compute(pathlib.Path(a.old_logs))
    except Exception as e:                                                 # noqa: BLE001
        old = {}
        out.append("(old logs could not be read: %s)\n" % e)
    rows, moved = [], {}
    for m, oldkey, label in (("jev_cpu", "jevision", "JEVision (old: CPU)"), ("openai", "openai", "OpenAI")):
        if m not in present:
            continue
        for lang in ("en", "ja"):
            n = o_ok = n_ok = up = down = 0
            for c in cases:
                if c["lang"] != lang or not c["legacy_id"] or (oldkey, lang, c["legacy_id"]) not in old:
                    continue
                n += 1
                oo, nn = old[(oldkey, lang, c["legacy_id"])], c["ok"][m]
                o_ok += oo
                n_ok += nn
                up += (not oo) and nn
                down += oo and not nn
                moved.setdefault((m, lang), []).append((c["id"], c["legacy_id"], oo, nn))
            rows.append([label, lang, n, pct(o_ok, n), pct(n_ok, n), "%+.1f pt" % (100.0 * (n_ok - o_ok) / n) if n else "-", up, down])
    out.append(md_table(["model", "lang", "same questions", "old bench", "v1 (polished)", "change", "wrong -> right", "right -> wrong"], rows))
    out.append("Matched by legacy_id; 'old' = the legacy logs (eval_common results_*) read with datasets/tools/regroup_check.py. The polish changed wording, "
               "wrong options, answer positions (balanced order), image types and some answers, so a change is not a pure model effect.\n")
    # (d) misses
    out.append("## (d) Questions both models missed / only one missed\n")
    per_id = collections.defaultdict(dict)
    for c in cases:
        per_id[c["id"]][c["lang"]] = c
    both_wrong, only_j, only_o = [], [], []
    for qid, d in per_id.items():
        jw = sum(not x["ok"]["jev_cpu"] for x in d.values())
        ow = sum(not x["ok"]["openai"] for x in d.values())
        k = len(d)
        if jw == k and ow == k:
            both_wrong.append(qid)
        elif jw == k and ow == 0:
            only_j.append(qid)
        elif ow == k and jw == 0:
            only_o.append(qid)
    out.append("Per question id over its languages: wrong in every language by both models: **%d**; wrong only by JEVision (OpenAI right in every language): **%d**; "
               "wrong only by OpenAI (JEVision right in every language): **%d**.\n" % (len(both_wrong), len(only_j), len(only_o)))
    bc = collections.Counter((attrs[q]["group"], attrs[q]["origin"]) for q in both_wrong)
    out.append("Both wrong by group/origin: " + ", ".join("%s/%s %d" % (g, o, n) for (g, o), n in sorted(bc.items())) + "\n")

    def lst(ids, title, limit=40):
        rows = []
        for q in sorted(ids)[:limit]:
            d = per_id[q]
            x = d.get("en") or d.get("ja")
            rows.append([q, attrs[q]["group"], attrs[q]["origin"], attrs[q]["kind"], attrs[q]["nopt"], attrs[q]["difficulty"], attrs[q]["image_type"],
                         x["exp"], "/".join("%s:%s" % (l, d[l]["got"]["jev_cpu"]) for l in d), "/".join("%s:%s" % (l, d[l]["got"]["openai"]) for l in d)])
        return "#### %s (first %d of %d, by id)\n\n" % (title, min(limit, len(ids)), len(ids)) + md_table(
            ["id", "group", "origin", "kind", "options", "difficulty", "image_type", "expected", "JEVision got", "OpenAI got"], rows)
    out.append(lst(both_wrong, "Both models wrong in every language"))
    out.append(lst(only_j, "Only JEVision wrong", 25))
    out.append(lst(only_o, "Only OpenAI wrong", 25))
    # (e) candidates for the label check: both wrong, same wrong answer in every language
    cand = []
    for q in both_wrong:
        d = per_id[q]
        sig = {(x["got"]["jev_cpu"], x["got"]["openai"]) for x in d.values()}
        if len(sig) == 1 and next(iter(sig))[0] == next(iter(sig))[1] and next(iter(sig))[0] != "NA":
            cand.append(q)
    out.append("#### Label-check candidates: both models wrong, giving the SAME wrong answer in every language (%d)\n\n%s\n" % (len(cand), ", ".join(sorted(cand))))
    # (f) NA, time, cost
    out.append("## (f) NA, time and cost\n")
    rows = []
    for m in present:
        na = [(k, v) for k, v in res[m].items() if v["got"] == "NA"]
        rows.append([dict((x[0], x[2]) for x in MODELS)[m], len(res[m]), len(na), ", ".join(sorted("%s/%s" % k for k, _ in na)[:12])])
    out.append(md_table(["model", "asked (id x lang)", "NA", "NA ids (first 12)"], rows))
    if "openai" in present:
        tok = sum((m.get("usage") or {}).get("input_tokens", 0) for m in meta["openai"])
        reqs = sum((m.get("usage") or {}).get("requests", 0) for m in meta["openai"])
        rt = sum((m.get("usage") or {}).get("round_trip_s", 0) for m in meta["openai"])
        retries = sum((m.get("usage") or {}).get("retries", 0) for m in meta["openai"])
        out.append("OpenAI (model %s, endpoint %s): %d requests, %d input tokens, %d retries, summed round trip %.0f s. Estimated cost at an ASSUMED "
                   "$%.2f per 1M input tokens (GPT-6 Luna input rate; the Decisions API has no published price; same assumption as report/wiki_report.py): "
                   "**$%.3f**. Output tokens were not billed in the assumption (they are reported as %d).\n" % (
                       meta["openai"][0].get("model_name"), meta["openai"][0].get("endpoint"), reqs, tok, retries, rt, USD_PER_M_INPUT,
                       tok / 1e6 * USD_PER_M_INPUT, sum((m.get("usage") or {}).get("output_tokens", 0) for m in meta["openai"])))
    # CPU vs GPU
    if "jev_cpu" in present and "jev_cuda" in present:
        out.append("## JEVision CPU vs GPU\n")
        keys = [k for k in res["jev_cpu"] if k in res["jev_cuda"]]
        diff = [k for k in keys if res["jev_cpu"][k]["got"] != res["jev_cuda"][k]["got"]]
        out.append("Same answer on %d of %d (id x lang); different on %d. Correctness differs on %d.\n" % (
            len(keys) - len(diff), len(keys), len(diff), sum(res["jev_cpu"][k]["ok"] != res["jev_cuda"][k]["ok"] for k in keys)))
        if diff:
            out.append(md_table(["id", "lang", "kind", "expected", "CPU", "GPU"], [[k[0], k[1], res["jev_cpu"][k]["kind"], res["jev_cpu"][k]["exp"],
                                                                                    res["jev_cpu"][k]["got"], res["jev_cuda"][k]["got"]] for k in sorted(diff)[:25]]))

        def med(ms):
            ms = [x for x in ms if x]
            return statistics.median(ms) if ms else None

        def trow(label, sel):
            ks = [k for k in keys if sel(attrs[k[0]], k)]
            c, g = med([res["jev_cpu"][k]["ms"] for k in ks]), med([res["jev_cuda"][k]["ms"] for k in ks])
            return [label, len(ks), "%.0f" % c if c else "-", "%.0f" % g if g else "-", "%.1fx" % (c / g) if c and g else "-"]
        rows = [trow("all", lambda a_, k: True)]
        rows += [trow("group " + g, lambda a_, k, g=g: a_["group"] == g) for g in ("photo", "biz", "rsn", "txt")]
        rows += [trow("format " + f, lambda a_, k, f=f: a_["kind"] == f) for f in ("choice", "noul", "score")]
        rows += [trow("picture", lambda a_, k: a_["modality"] == "image"), trow("text only", lambda a_, k: a_["modality"] == "text")]
        rows += [trow("lang " + l, lambda a_, k, l=l: k[1] == l) for l in ("en", "ja")]
        out.append("Median ms per question (wall time of the ask call; GPU first-call warm-up outliers do not move a median). The CPU times count only "
                   "for blocks whose calibration was valid (see below).\n")
        out.append(md_table(["subset", "n", "CPU ms", "GPU ms", "CPU/GPU"], rows))
        cal = [(m["block"], m.get("calibration")) for m in meta["jev_cpu"]]
        valid = sum(1 for _, c in cal if c and c.get("timing_valid"))
        out.append("CPU calibration (GLiNER fixed job before/after each block, limit 600 ms): %d of %d blocks valid. %s\n" % (
            valid, len(cal), "; ".join("%s before=%s after=%s %s" % (b, c and c.get("before_ms"), c and c.get("after_ms"),
                                                                       "valid" if c and c.get("timing_valid") else "reference only (*)") for b, c in cal)))
    out.append("## Conditions recorded\n")
    for m in present:
        for mt in meta[m]:
            out.append("- %s: model=%s repo=%s tag=%s variant=%s device=%s providers_requested=%s providers_used=%s threads=%s dataset_version=%s "
                       "question_list sha256=%s started=%s finished=%s" % (
                           mt["block"], mt["model"], mt["model_repo"], mt["model_tag"], mt["variant"], mt.get("device"), mt["providers_requested"],
                           mt["providers_used"], mt["threads"], mt["dataset_version"], (mt.get("question_list") or {}).get("sha256"),
                           mt["started"], mt["finished"]))
    pathlib.Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    # per-question merged CSV
    with open(RUNS / "per_question_v1.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "lang", "group", "origin", "kind", "options", "difficulty", "image_type", "skill", "modality", "legacy_id", "derived_from", "expected"]
                   + ["got_" + m for m in present] + ["ok_" + m for m in present])
        for c in sorted(cases, key=lambda c: (c["id"], c["lang"])):
            w.writerow([c["id"], c["lang"], c["group"], c["origin"], c["kind"], c["nopt"], c["difficulty"], c["image_type"], c["skill"], c["modality"],
                        c["legacy_id"] or "", c["derived_from"] or "", c["exp"]] + [c["got"].get(m, "") for m in present]
                       + [int(c["ok"][m]) if m in c["ok"] else "" for m in present])
    summ = dict(cases=len(cases), accuracy={m: sum(c["ok"][m] for c in cases if m in c["ok"]) / max(1, len(cases)) for m in present},
                both_wrong=sorted(both_wrong), label_check_candidates=sorted(cand))
    (RUNS / "summary_v1.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
