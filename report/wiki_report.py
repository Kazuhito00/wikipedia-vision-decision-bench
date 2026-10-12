# -*- coding: utf-8 -*-
"""Build the report page (the table, the figures and the question explorer) from the measurement logs and the question sets.

    uv run python -m report.wiki_report [--logs DIR] [--data-root DIR] [--out PATH] [--public]

    --logs       the folder with the per-question logs, laid out as results_w/ results_s/ results_t/ results_g/ below it (default
                 work/logs; the old eval_common/ folder has exactly this layout and can be given as it is: it is only read)
    --data-root  the folder that contains data/ (default: runner.config.data_root(): WIKIQA_DATA_ROOT or work/)
    --out        default work/report/wiki_report.html (git-ignored)
    --public     the version for publishing: NO thumbnails and no picture links (tables and figures only)

Data sets (every picture question is asked in English and in Japanese):
    wikipedia  pictures that Wikipedia articles use         data/linked.jsonl   logs results_w/<m>_wiki_<lang>_224{,_fill}.log
    expansion  Commons pictures picked by category          (same file; tagged sci / life / record)   logs ..._224_exp.log
    synthetic  pictures drawn by datasets/synthetic         data/synthetic.jsonl   logs results_s/<m>_syn_<lang>_224.log
    reasoning  drawn reasoning pictures                     data/reasoning.jsonl   logs results_s/<m>_rsn_<lang>_224.log
Output: one self-contained HTML (thumbnails embedded; the 224 px inputs and the originals are linked relatively). The full report is a
LOCAL page: the pictures are Wikimedia Commons files that the repository never publishes, so it stays out of git (*.html is ignored).

Timings: only the quiet main runs on the Wikipedia set are kept (a fill-in or expansion run, a run on a slow machine, and every
Strands run carry none); the API's round-trip time is always kept (it does not depend on the machine).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pathlib
import re
import sys

from runner import config as _config
from runner.cases import load_cases

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LOGS = _config.work_dir() / "logs"                 # --logs
DATA_ROOT = _config.data_root()                    # --data-root
RES_W, RES_S, RES_T, RES_G = (LOGS / "results_w", LOGS / "results_s", LOGS / "results_t", LOGS / "results_g")
# results_g: the same timed blocks run on the GPU (CUDA)
PUBLIC = False                                     # --public: no pictures in the page
#: a timed block counts only if the machine calibration (GLiNER ms) before and after it was at most this (quiet machine: ~170-200; the limit is about 3x)
CAL_LIMIT = 600
DISTURBED_BLOCKS = ("strands_wiki_en_224", "strands_wiki_ja_224",
                    # QEV: calibration rose from ~185 to ~520 ms from 18:25 on (cause not found): reference values only
                    "qev_syn_en_224", "qev_syn_ja_224", "qev_rsn_en_224", "qev_rsn_ja_224")
LINE = re.compile(r"(ok |XX )\s+(\S+)\s+got=(\S+) exp=(\S+) rev=(\S+) ms=(\d+)")
TOKENS = re.compile(r"\((\d+) s, (\d+) input tokens\)")
MODELS = [("openjev", "OpenJev 0.8B", "fp16"), ("intern", "Intern-Decision 0.8B", "fp32"),
          ("jevision", "JEVision 0.8B", "fp16"), ("onejev", "OneJev 0.8B", "fp16"),
          ("qev", "QEV 2B", "fp32"), ("strands", "Strands Decider 2B", "fp32"),
          ("openjev4", "OpenJev 4B", "q4f16"), ("onejev4", "OneJev 4B", "fp16"),
          ("clef", "clef-flash 9B", "bf16→fp32"),
          ("openai", "OpenAI Decisions API (gpt-6-luna)", "API")]   # parameter size ascending, then overall accuracy ascending; the API last
#: short names for the narrow column headers
SHORT = {"jevision": "JEVision 0.8B", "qev": "QEV 2B", "onejev": "OneJev 0.8B", "onejev4": "OneJev 4B", "openjev": "OpenJev 0.8B", "intern": "Intern 0.8B", "openjev4": "OpenJev 4B", "strands": "Strands 2B",
         "clef": "clef 9B", "openai": "OpenAI API"}
#: the same model at two sizes
FAMILY = {"openjev": "openjev", "openjev4": "openjev"}
#: base model and whether it was fine-tuned: OpenJev is the stock Qwen3.5 (0.8B / 4B) behind a typed-decision prompt, OneJev and
#: Intern-Decision are full fine-tunes of Qwen3.5-0.8B, Strands is Qwen3.5-2B-Base + LoRA; the API model is not known
BASE = {"jevision": ("qwen3.5-0.8b", True), "qev": ("qwen3.5-2b", True), "onejev": ("qwen3.5-0.8b", True), "onejev4": ("qwen3.5-4b", True), "openjev": ("qwen3.5-0.8b", False), "intern": ("qwen3.5-0.8b", True),
        "openjev4": ("qwen3.5-4b", False), "strands": ("qwen3.5-2b", True), "clef": ("qwen3.5-9b", True)}
#: questions a model cannot take are out of scope for it: no answer is shown and the question is not in its tally
#: (QEV accepts one picture per request; the 13 questions of the reasoning set that show two pictures are skipped, not scored wrong)
OUT_OF_SCOPE = {"qev": "two-images"}
#: measured while the machine ran slow (GLiNER reference ~3x its quiet value): accuracy counts, CPU times do not
UNTIMED = {"strands", "clef"}
#: OpenAI has published no price for the Decisions API; the GPT-6 Luna input rate is the estimate (stated on the page)
PRICING = {"openai": {"usd_per_m_input": 0.10,
                      "basis": "GPT-6 Luna の入力料金（100 万トークンあたり 0.10 ドル）を仮に当てはめた概算。Decisions API 自体の料金は未公表"}}
EXPANSION: set = set()
BLOCKS: dict = {}


def read_lines(path: pathlib.Path):
    raw = path.read_bytes().replace(bytes([0]), b"")
    return raw.decode("utf-8", errors="replace").replace(chr(13), "").split(chr(10))


def parse(path: pathlib.Path, timed: bool = True):
    """case id -> dict(ok, got, ms) ; errors become got='NA'. ``timed=False``: the times are not kept."""
    out = {}
    if not path.exists():
        return out
    for ln in read_lines(path):
        m = LINE.search(ln)
        if m:
            out[m.group(2)] = dict(ok=m.group(1) == "ok ", got=m.group(3), ms=int(m.group(6)) if timed else None)
    return out


def valid_blocks(res_dir: pathlib.Path = None) -> dict:
    """name -> True/False for the blocks of the timed re-measurement (results_t/blocks.log: 'name before=N after=M time')."""
    out = {}
    path = (res_dir or RES_T) / "blocks.log"
    if path.exists():
        for ln in read_lines(path):
            m = re.match(r"(\S+) before=(\d*) after=(\d*)", ln)
            if m:
                a, b = m.group(2), m.group(3)
                out[m.group(1)] = bool(a and b and max(int(a), int(b)) <= CAL_LIMIT)
    # Calibration only brackets a block, so a stray process that hogged the CPU in between is invisible to it
    # (an orphan `find` ran 10:23-13:45 on 2026-10-08): keep these two Strands blocks as reference values (※).
    for name in (DISTURBED_BLOCKS if res_dir is None else ()):
        if name in out:
            out[name] = False
    return out


def tokens_of(path: pathlib.Path) -> int:
    """Input tokens the API reported in the summary line of one log."""
    if not path.exists():
        return 0
    found = TOKENS.findall(path.read_bytes().replace(bytes([0]), b"").decode("utf-8", errors="replace"))
    return int(found[-1][1]) if found else 0


def option_text(case, lang, got):
    """What a raw answer (index, or True/False) means in words, for this language."""
    L = case[lang]
    if case["kind"] == "noul":
        yes, no = ("yes", "no") if lang == "en" else ("はい", "いいえ")
        return yes if got == "True" else (no if got == "False" else "—")
    if got in ("NA", None):
        return "—"
    try:
        return L["options"][int(got)][0]
    except (ValueError, IndexError):
        return "—"


def thumb(path: pathlib.Path) -> str:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((112, 112))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=62)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def input_picture(src: str, px: int = 224) -> pathlib.Path:
    """The picture as the models were given it: longest side ``px``, LANCZOS (what runner/run.py writes to
    work/px<px>/). Written here when a runner has not done it yet."""
    from PIL import Image

    out = _config.work_dir() / ("px%d" % px) / pathlib.Path(src).name
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src).convert("RGB")
        im.thumbnail((px, px), Image.LANCZOS)
        im.save(out)
    return out


def expansion_ids() -> set:
    """Question ids of the Commons expansion: their pictures come from categories, not from an article (``source_unverified``
    in linked.jsonl, set by the question build)."""
    out = set()
    path = DATA_ROOT / "data" / "linked.jsonl"
    if path.exists():
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln)
                if r.get("source_unverified"):
                    out.add(r["id"])
    return out


def set_of(case, source: str, expansion: set) -> str:
    if source in ("synthetic", "reasoning"):
        return source
    return "expansion" if case["id"] in expansion else "wikipedia"


def time_of(set_name: str, key: str, r: dict) -> dict:
    """The time of one answer and whether it was measured on a quiet machine (q): the API round trip always; the timed re-measurement
    when its block's calibration was good; the old main runs of the Wikipedia set (calibration 171-184 ms). Everything else (fill-in,
    expansion, a machine that ran slow, Strands/clef before the re-measurement) is kept as a reference value only (q False)."""
    if key == "openai":
        return dict(ms=r["ms"], q=True)
    if r.get("has_t"):
        return dict(ms=r["tms"], q=bool(r.get("tq")))
    return dict(ms=r["ms"], q=keep_ms(set_name, key, r["kind"]))


def keep_ms(set_name: str, key: str, kind: str) -> bool:
    """Which times may be shown: the API round trip, and the quiet main runs of the local models on the Wikipedia set."""
    return key == "openai" or (set_name == "wikipedia" and key not in UNTIMED and kind == "main")


def main(argv=None) -> int:
    global EXPANSION, BLOCKS, LOGS, DATA_ROOT, RES_W, RES_S, RES_T, RES_G, PUBLIC
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--logs", default=str(LOGS))
    ap.add_argument("--data-root", default=str(DATA_ROOT))
    ap.add_argument("--out", default=str(_config.work_dir() / "report" / "wiki_report.html"))
    ap.add_argument("--public", action="store_true", help="no thumbnails / picture links: tables and figures only")
    args = ap.parse_args(argv)
    LOGS, DATA_ROOT, PUBLIC = pathlib.Path(args.logs), pathlib.Path(args.data_root), args.public
    RES_W, RES_S, RES_T, RES_G = (LOGS / "results_w", LOGS / "results_s", LOGS / "results_t", LOGS / "results_g")
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    EXPANSION = expansion_ids()
    BLOCKS = valid_blocks()
    BLOCKS_G = valid_blocks(RES_G)
    out_dir = pathlib.Path(args.out).resolve().parent

    sources = [("commons", ("linked.jsonl",), RES_W, "%s_wiki_%s_224"), ("synthetic", ("synthetic.jsonl",), RES_S, "%s_syn_%s_224"),
               ("reasoning", ("reasoning.jsonl",), RES_S, "%s_rsn_%s_224")]
    items, cost = [], {"openai": {}}
    for source, files, res_dir, pattern in sources:
        if not all((DATA_ROOT / "data" / f).exists() for f in files):
            continue
        cases = [c for c in load_cases(source, DATA_ROOT) if c["modality"] == "image"]
        results = {}                                     # (model, lang) -> {id: dict(ok, got, ms, kind)}
        for key, _, _ in MODELS:
            for lang in ("en", "ja"):
                stem = pattern % (key, lang)
                rec = {}
                for suffix, kind in (("", "main"), ("_fill", "fill"), ("_exp", "exp")):
                    for cid, r in parse(res_dir / (stem + suffix + ".log"), timed=True).items():
                        rec[cid] = dict(r, kind=kind)
                # the timed re-measurement (quiet machine): its times replace the old ones when the block's calibration is good; it also supplies
                # answers for questions no earlier log has (e.g. the reasoning set, clef-flash)
                tname = pattern % (key, lang)
                tpath = RES_T / (tname + ".log")
                if tpath.exists():
                    ok_block = BLOCKS.get(tname, False)
                    for cid, r in parse(tpath, timed=True).items():
                        if cid in rec:
                            rec[cid]["tms"], rec[cid]["tq"], rec[cid]["has_t"] = r["ms"], ok_block, True
                        else:
                            rec[cid] = dict(r, kind="timed", tms=r["ms"], tq=ok_block, has_t=True)
                gpath = RES_G / (tname + ".log")
                if gpath.exists():                     # GPU times: the same questions, one more number per answer
                    for cid, r in parse(gpath, timed=True).items():
                        if cid in rec:
                            rec[cid]["gms"], rec[cid]["gq"] = r["ms"], BLOCKS_G.get(tname, False)
                results[(key, lang)] = rec
        for lang in ("en", "ja"):
            if source == "commons":
                cost["openai"].setdefault("wikipedia", {})[lang] = tokens_of(RES_W / ("openai_wiki_%s_224.log" % lang))
                cost["openai"].setdefault("expansion", {})[lang] = tokens_of(RES_W / ("openai_wiki_%s_224_exp.log" % lang))
            elif source == "synthetic":
                cost["openai"].setdefault("synthetic", {})[lang] = tokens_of(RES_S / ("openai_syn_%s_224.log" % lang))
            else:
                cost["openai"].setdefault("reasoning", {})[lang] = tokens_of(RES_S / ("openai_rsn_%s_224.log" % lang))
        for c in cases:
            sname = set_of(c, source, EXPANSION)
            row = dict(id=c["id"], set=sname, kind=c["kind"], difficulty=c.get("difficulty"), tags=c.get("tags", []),
                       thumb="" if PUBLIC else thumb(pathlib.Path(c["images"][0])), images=len(c["images"]), langs=[],
                       full=[] if PUBLIC else [os.path.relpath(q, out_dir).replace(chr(92), "/") for q in c["images"]],
                       inp=[] if PUBLIC else [os.path.relpath(input_picture(q), out_dir).replace(chr(92), "/") for q in c["images"]])
            for lang in ("en", "ja"):
                if lang not in c:
                    continue
                row["langs"].append(lang)
                L = c[lang]
                e = c["expected"]
                exp_text = ("yes" if lang == "en" else "はい") if e is True else (
                    ("no" if lang == "en" else "いいえ") if e is False else L["options"][e][0])
                answers = {}
                for key, _, _ in MODELS:
                    r = results[(key, lang)].get(c["id"])
                    if key in OUT_OF_SCOPE and OUT_OF_SCOPE[key] in c.get("tags", []):
                        r = None
                    answers[key] = None if r is None else dict(
                        ok=r["ok"], t=option_text(c, lang, r["got"]), **time_of(sname, key, r),
                        **({"g": r["gms"], "gq": r["gq"]} if "gms" in r else {}))
                row[lang] = dict(state=L["state"], q=L["instr"], options=[o[0] for o in L["options"]] if L["options"] else None,
                                 expected=exp_text, answers=answers)
            items.append(row)

    data = dict(items=items, pricing=PRICING, cost=cost,
                models=[dict(key=k, name=n, short=SHORT.get(k, n), prec=p, fam=FAMILY.get(k, k), base=BASE.get(k, (k, True))[0],
                             tuned=BASE.get(k, (k, True))[1], oos=OUT_OF_SCOPE.get(k)) for k, n, p in MODELS])
    html = TEMPLATE.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*PUBLIC*/false", "true" if PUBLIC else "false")
    pathlib.Path(args.out).write_text(html, encoding="utf-8", newline="\n")
    print("wrote %s  (%d KB, %d items)" % (args.out, len(html) // 1024, len(items)))
    for sn in ("wikipedia", "expansion", "synthetic", "reasoning"):
        sel = [i for i in items if i["set"] == sn]
        line = []
        for key, _, _ in MODELS:
            for lang in ("en", "ja"):
                a = [i[lang]["answers"][key] for i in sel if lang in i["langs"] and i[lang]["answers"][key]]
                line.append("%s-%s %d/%d" % (key, lang, sum(x["ok"] for x in a), len(a)))
        print("  %-9s %4d items | %s" % (sn, len(sel), "  ".join(line)))
    return 0


TEMPLATE = (HERE / "wiki_report_template.html").read_text(encoding="utf-8")

if __name__ == "__main__":
    raise SystemExit(main())
