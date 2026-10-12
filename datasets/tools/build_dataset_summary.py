# -*- coding: utf-8 -*-
"""Build dataset_summary.html: every v1 question to look at (cards with the 224 px picture, filters, search) plus statistics.

    python datasets/tools/build_dataset_summary.py [--out dataset_summary.html] [--public]
        [--v1dir datasets/questions/v1] [--review-out work/review/out] [--logs <eval_common>] [--px224 <dir> ...]

Local, self-contained (no CDN, no network, never reads .env). Re-runnable: the v1 files are being post-processed (more drops,
12 questions to one picture), so run it again whenever they change; the output is rebuilt from scratch.

  full   (default)  dataset_summary.html + dataset_summary_files/img/<picture>   (pictures are copied next to the page)
  --public          dataset_summary_public.html: tables and figures only. NO pictures, NO question cards, no passage text.

Never in the page: the Wikipedia passage of a text-only question (shown as "passage hidden" with the article title). The pictures
and the page are git-ignored (see .gitignore). Every number of the statistics view is computed here from the v1 files, the id map,
the review output and the old logs; nothing is typed in.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import options  # noqa: E402
from datasets.tools import export_review_batches, regroup_check, v1_io  # noqa: E402

JEV = ROOT.parents[1]
MODELS = regroup_check.MODELS
FILES_DIR = "dataset_summary_files"
DEFAULT_OUT = ROOT / "dataset_summary.html"
PUBLIC_OUT = ROOT / "dataset_summary_public.html"
REVIEW_OUT = ROOT / "work" / "review" / "out"
STATUS_ORDER = ["kept", "rewritten", "pending", "dropped"]


# ------------------------------------------------------------------------------------------------------ inputs
def read_review_out(path: pathlib.Path) -> dict:
    """{v1 id: {verdict, issues, reason}} of work/review/out/*.jsonl (the originals). A later file name overrides an earlier one."""
    out = {}
    if not pathlib.Path(path).exists():
        return out
    for f in sorted(pathlib.Path(path).glob("*.jsonl")):
        for r in v1_io.read_jsonl(f):
            out[r["id"]] = dict(verdict=r.get("verdict", ""), issues=list(r.get("issues") or []), reason=r.get("reason", ""))
    return out


def issue_tag(s: str) -> str:
    """Short tag of a free-form issue string: the part before ':' or '(' , lower-cased (``duplicate (photo-0012)`` -> duplicate)."""
    t = re.split(r"[:：(（]", str(s), maxsplit=1)[0].strip().lower()
    return t[:48] if t else "(empty)"


def n_options(row: dict) -> int | None:
    return answer_n(row) if row["kind"] == "choice" else None


def answer_n(row: dict) -> int:
    return v1_io.answer_format(row)[2]


def af_label(row: dict) -> str:
    """Answer format with 5+ options grouped is done in the view; here the exact format (choice:4 / yesno / score:5)."""
    return v1_io.answer_format(row)[0]


def positions(rows: list, mode: str) -> dict:
    """{id: position of the right answer} for the choice questions of ``rows``: legacy = the order the models saw (legacy id; new questions
    have none and are left out), balanced = the v1 assignment computed over exactly these rows (as the loader does it)."""
    out = {}
    choice = [r for r in rows if r["kind"] == "choice"]
    if mode == options.LEGACY:
        for r in choice:
            if r.get("legacy_id"):
                out[r["id"]] = options.expected_of(options.legacy_order(r["legacy_id"], n_options(r)))
        return out
    orders = options.v1_orders(choice)
    return {r["id"]: options.expected_of(orders[r["id"]]) for r in choice}


# ------------------------------------------------------------------------------------------------------ records
def old_stats(row: dict, res: dict) -> dict:
    s = export_review_batches.stats_for(row.get("legacy_id") or "", res, row["group"])
    cells = []
    for m in export_review_batches.MODELS:
        e = s["per_model"].get(m, {})
        cells.append("".join("-" if e.get(l) is None else ("1" if e[l] else "0") for l in ("en", "ja")))
    return dict(o=cells, an=s["answered"], wr=s["wrong"], pri=s["priority"])


def record(row: dict, rev: dict, idm: dict, res: dict, image_files: list, pos_legacy: dict) -> dict:
    """One question as the page shows it. A text-only question carries the article TITLE only, never its passage."""
    kind = row["kind"]
    rv = rev.get(row["id"], {})
    rec = dict(id=row["id"], legacy=row.get("legacy_id") or "", g=row["group"], src=row["source"], it=row["image_type"], sk=row["skill"],
               af=af_label(row), kd=kind, df=row.get("difficulty") or "", lg=row.get("lang", "both"), st=row["review"]["state"],
               tg=list(row.get("tags", [])), ver=rv.get("verdict", ""), iss=rv.get("issues", []), rsn=rv.get("reason", ""),
               hist=[dict(d=h.get("date", ""), w=h.get("what", ""), y=h.get("why", "")) for h in row["review"].get("history", [])],
               im=image_files, ms=idm.get("status", ""), cn=idm.get("change_note", ""))
    if kind == "choice":
        rec["n"] = n_options(row)
        rec["pl"] = pos_legacy.get(row["id"])
    elif kind == "score":
        rec["n"] = answer_n(row)
    for lang in row.get("langs") or ["en", "ja"]:
        q = row[lang]
        side = dict(q=q["instr"])
        if kind == "choice":
            side.update(c=q["correct"], w=list(q["wrong"]))
        elif kind == "score":
            side.update(lv=list(q["levels"]))
        if ("article" not in row) and q.get("state"):
            side["s"] = q["state"]                       # a short authored caption, not a Wikipedia passage
        rec[lang] = side
    if kind == "noul":
        rec["truth"] = bool(row["answer"])
    elif kind == "score":
        rec["ans"] = int(row["answer"])
    if row.get("modality") == "text" and "article" in row:
        rec["txt"] = {l: (row.get("article", {}).get(l, {}) or {}).get("title", "") for l in ("en", "ja")}
    rec.update(old_stats(row, res))
    return rec


# ------------------------------------------------------------------------------------------------------ statistics
def count(rows: list, key) -> list:
    c = collections.Counter(key(r) for r in rows)
    return sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))


def fmt_group(af: str) -> str:
    """Answer formats for the overview: choice:2 / 3 / 4 / 5+ , yesno, score:n."""
    if af.startswith("choice:"):
        n = int(af.split(":")[1])
        return "choice:5+" if n >= 5 else af
    return af


def cross(rows: list, rkey, ckey, rorder=None) -> dict:
    cols = sorted({ckey(r) for r in rows}, key=lambda x: (-sum(1 for r in rows if ckey(r) == x), str(x)))
    rws = list(rorder) if rorder else sorted({rkey(r) for r in rows})
    cells = [[sum(1 for r in rows if rkey(r) == a and ckey(r) == b) for b in cols] for a in rws]
    return dict(rows=rws, cols=cols, cells=cells)


def stats_for_scope(rows: list, recs: dict, idmap: list, scope_name: str) -> dict:
    """All the numbers of one population (all questions, or without the dropped ones)."""
    G = v1_io.GROUPS
    rs = [recs[r["id"]] for r in rows]
    out = dict(name=scope_name, total=len(rows))
    out["groups"] = [[g, sum(1 for r in rows if r["group"] == g)] for g in G]
    dims = {"group": lambda r: r["group"], "image_type": lambda r: r["image_type"], "skill": lambda r: r["skill"],
            "answer_format": lambda r: fmt_group(af_label(r)), "answer_format_exact": lambda r: af_label(r),
            "difficulty": lambda r: r.get("difficulty") or "(none)", "lang": lambda r: r.get("lang", "both"),
            "source": lambda r: r["source"], "kind": lambda r: r["kind"], "review_state": lambda r: r["review"]["state"]}
    out["dims"] = {k: count(rows, f) for k, f in dims.items()}
    out["dims_by_group"] = {k: {g: count([r for r in rows if r["group"] == g], f) for g in G} for k, f in dims.items()
                            if k in ("image_type", "skill", "answer_format", "difficulty", "source")}
    out["cross"] = {
        "group_skill": cross(rows, lambda r: r["group"], lambda r: r["skill"], G),
        "group_difficulty": cross(rows, lambda r: r["group"], lambda r: r.get("difficulty") or "(none)", G),
        "group_image_type": cross(rows, lambda r: r["group"], lambda r: r["image_type"], G),
        "group_format": cross(rows, lambda r: r["group"], lambda r: fmt_group(af_label(r)), G),
        "skill_difficulty": cross(rows, lambda r: r["skill"], lambda r: r.get("difficulty") or "(none)"),
    }
    # position of the right answer: legacy (what the models saw) and balanced (the v1 assignment over this population)
    pos = {}
    for mode in (options.LEGACY, options.BALANCED):
        p = positions(rows, mode)
        by = {}
        for r in rows:
            if r["kind"] == "choice":
                if r["id"] in p:
                    by.setdefault((r["group"], n_options(r)), [0] * n_options(r))[p[r["id"]]] += 1
        pos[mode] = [dict(group=g, n=n, counts=c) for (g, n), c in sorted(by.items(), key=lambda kv: (G.index(kv[0][0]), kv[0][1]))]
    out["pos"] = pos
    yn = [r for r in rows if r["kind"] == "noul"]
    yes = lambda sub: [sum(1 for r in sub if r["answer"]), sum(1 for r in sub if not r["answer"])]
    out["yesno"] = dict(total=yes(yn), by_group=[[g] + yes([r for r in yn if r["group"] == g]) for g in G],
                        by_skill=[[k] + yes([r for r in yn if r["skill"] == k]) for k, _ in count(yn, lambda r: r["skill"])],
                        by_image_type=[[k] + yes([r for r in yn if r["image_type"] == k]) for k, _ in count(yn, lambda r: r["image_type"])],
                        by_source=[[k] + yes([r for r in yn if r["source"] == k]) for k, _ in count(yn, lambda r: r["source"])])
    out["score_levels"] = count([r for r in rows if r["kind"] == "score"], lambda r: answer_n(r))
    # review: verdicts (from the review output) and issue tags
    out["verdicts"] = count(rs, lambda x: x["ver"] or "(none)")
    tags = collections.Counter()
    tags_by_group = {g: collections.Counter() for g in G}
    n_with = 0
    for x in rs:
        ts = {issue_tag(i) for i in x["iss"]}
        n_with += bool(ts)
        for t in ts:
            tags[t] += 1
            tags_by_group[x["g"]][t] += 1
    out["issue_tags"] = sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))
    out["issue_tags_by_group"] = {g: sorted(c.items(), key=lambda kv: (-kv[1], kv[0])) for g, c in tags_by_group.items()}
    out["with_issues"] = n_with
    out["priority"] = count([x for x in rs], lambda x: x["pri"])
    out["priority_by_group"] = {g: count([x for x in rs if x["g"] == g], lambda x: x["pri"]) for g in G}
    # old model results: correct/answered per model, language and group (this population only)
    ids = {r["id"] for r in rows}
    models = []
    for mi, m in enumerate(export_review_batches.MODELS):
        for li, lang in enumerate(("en", "ja")):
            cells = {}
            for g in G:
                c = a = 0
                for x in rs:
                    if x["g"] != g:
                        continue
                    ch = x["o"][mi][li]
                    if ch != "-":
                        a += 1
                        c += ch == "1"
                cells[g] = [c, a]
            models.append(dict(model=m, lang=lang, cells=cells, total=[sum(v[0] for v in cells.values()), sum(v[1] for v in cells.values())]))
    out["models"] = models
    out["n_ids"] = len(ids)
    return out


def idmap_stats(idmap: list, idmap_new: list = ()) -> dict:
    """legacy -> v1 movement from datasets/manifests/idmap_legacy_v1.csv (status kept / rewritten / pending / dropped); ``idmap_new`` = the rows
    of idmap_v1_new_<tag>.csv: they add to the v1 count of their group (``new`` = not dropped) and never to the legacy columns."""
    G = v1_io.GROUPS
    by = {}
    for m in idmap:
        by.setdefault(m["group_v1"], collections.Counter())[m["status"]] += 1
    new_by = collections.Counter(m["group_v1"] for m in idmap_new if m["status"] != "dropped")
    rows = []
    for g in G:
        c = by.get(g, collections.Counter())
        legacy_n = sum(c.values())
        kept = c.get("kept", 0)
        rows.append(dict(group=g, legacy=legacy_n, kept=kept, rewritten=c.get("rewritten", 0), pending=c.get("pending", 0), dropped=c.get("dropped", 0),
                         new=new_by.get(g, 0), v1=legacy_n - c.get("dropped", 0) + new_by.get(g, 0)))
    flow = count(idmap, lambda m: (m["group_legacy"], m["group_v1"]))
    return dict(rows=rows, flow=[[a, b, n] for (a, b), n in flow], status=count(idmap, lambda m: m["status"]),
                total=len(idmap), dropped_v1=None)


def build_data(rows: list, idmap: list, rev: dict, res: dict, image_files: dict, public: bool = False, idmap_new: list = ()) -> dict:
    """The data object embedded in the page. ``image_files``: {id: [relative picture paths]} (ignored when public). ``idmap`` = the legacy->v1
    map (idmap_legacy_v1.csv); ``idmap_new`` = the new questions' rows (idmap_v1_new_<tag>.csv)."""
    full_map = list(idmap) + list(idmap_new)
    idm = {m["v1_id"]: m for m in full_map}
    pos_legacy = positions(rows, options.LEGACY)
    recs = {r["id"]: record(r, rev, idm.get(r["id"], {}), res, [] if public else image_files.get(r["id"], []), pos_legacy) for r in rows}
    active = [r for r in rows if r["review"]["state"] != "dropped"]
    data = dict(public=public, stats=dict(all=stats_for_scope(rows, recs, idmap, "all"), active=stats_for_scope(active, recs, idmap, "active")),
                idmap_stats=idmap_stats(idmap, idmap_new), models=list(export_review_batches.MODELS),
                idmap=[{k: m.get(k, "") for k in v1_io.IDMAP_COLS} for m in full_map])
    dropped_jsonl = {r["id"] for r in rows if r["review"]["state"] == "dropped"}
    dropped_map = {m["v1_id"] for m in full_map if m["status"] == "dropped"}
    data["idmap_stats"]["dropped_v1"] = len(dropped_jsonl)
    data["idmap_stats"]["dropped_mismatch"] = sorted(dropped_jsonl ^ dropped_map)
    if not public:
        data["records"] = [recs[r["id"]] for r in rows]
    return data


# ------------------------------------------------------------------------------------------------------ pictures
def find_pictures(rows: list, px224: list, files_dir: pathlib.Path | None) -> tuple:
    """Copy the 224 px picture of every row to files_dir/img and return ({id: [relative paths]}, [missing names])."""
    out, missing = {}, []
    img_dir = files_dir / "img" if files_dir else None
    if img_dir:
        if img_dir.exists():
            shutil.rmtree(img_dir)
        img_dir.mkdir(parents=True)
    for r in rows:
        paths = []
        for li in r.get("local_images", []):
            name = pathlib.Path(li).name
            src = next((d / name for d in px224 if (d / name).exists()), None)
            if src is None:                              # no 224 px picture yet: make one from the original (work/<local path>)
                orig = ROOT / "work" / li
                if img_dir and orig.exists():
                    from PIL import Image
                    im = Image.open(orig).convert("RGB")
                    im.thumbnail((224, 224), Image.LANCZOS)
                    im.save(img_dir / name)
                else:
                    missing.append(name)
                    continue
            elif img_dir and not (img_dir / name).exists():
                shutil.copyfile(src, img_dir / name)
            paths.append("%s/img/%s" % (FILES_DIR, name))
        out[r["id"]] = paths
    return out, missing


# ------------------------------------------------------------------------------------------------------ HTML
def render(data: dict, template: str | None = None) -> str:
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return (template or TEMPLATE).replace("/*__DATA__*/null", blob).replace("__TITLE__", "v1 データセット概要" + ("（公開版）" if data["public"] else ""))


def extract_script(html: str) -> str:
    """The main <script> of a page (for node --check)."""
    return re.findall(r"<script>(.*?)</script>", html, flags=re.S)[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=None, help="output html (default dataset_summary.html, or dataset_summary_public.html with --public)")
    ap.add_argument("--public", action="store_true", help="tables and figures only: no pictures, no question cards")
    ap.add_argument("--v1dir", default=str(v1_io.V1DIR))
    ap.add_argument("--review-out", default=str(REVIEW_OUT))
    ap.add_argument("--logs", default=str(JEV / "eval_common"))
    ap.add_argument("--px224", action="append", default=None)
    a = ap.parse_args()
    out = pathlib.Path(a.out) if a.out else (PUBLIC_OUT if a.public else DEFAULT_OUT)
    by_group = v1_io.load_v1(pathlib.Path(a.v1dir))
    rows = v1_io.all_rows(by_group) + v1_io.all_new_rows(v1_io.load_new(pathlib.Path(a.v1dir)))      # base, then the new_<tag> files
    idmap, idmap_new = v1_io.load_idmap(), v1_io.load_new_idmap()
    rev = read_review_out(pathlib.Path(a.review_out))
    logs = pathlib.Path(a.logs)
    res = regroup_check.compute(logs) if logs.exists() else {}
    if not res:
        print("WARNING: no old logs under %s: model results are empty" % logs, file=sys.stderr)
    pictures, missing = {}, []
    if not a.public:
        px = [pathlib.Path(p) for p in (a.px224 or [ROOT / "work" / "generated" / "px224", ROOT / "work" / "px224", JEV / "wiki_qa" / "work" / "px224"])]
        pictures, missing = find_pictures(rows, px, out.parent / FILES_DIR)
    data = build_data(rows, idmap, rev, res, pictures, public=a.public, idmap_new=idmap_new)
    out.write_text(render(data), encoding="utf-8", newline="\n")
    n_img = sum(len(v) for v in pictures.values())
    print("wrote %s: %d questions, %d pictures, %d missing pictures, %.1f KB html%s" % (
        out, len(rows), n_img, len(missing), out.stat().st_size / 1024, " (public)" if a.public else ""))
    if missing:
        print("missing pictures: %s" % ", ".join(sorted(set(missing))[:10]), file=sys.stderr)
    if data["idmap_stats"]["dropped_mismatch"]:
        print("note: %d ids differ between review.state=dropped and idmap status=dropped" % len(data["idmap_stats"]["dropped_mismatch"]))
    return 0


TEMPLATE = r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--text:#1c2430;--muted:#5d6877;--line:#d9dee6;--accent:#2457c5;--ok:#1a7f37;--okbg:#dff3e4;--bad:#c62828;--badbg:#fbe3e3;
--gray:#e9ecf1;--warn:#9a6700;--warnbg:#fff1c9;--c1:#2457c5;--c2:#d9822b;--c3:#2a9d8f;--c4:#9b59b6;--c5:#c0392b;--c6:#7f8c8d;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12161c;--panel:#1b212a;--text:#e4e8ee;--muted:#9aa5b4;--line:#2f3846;--accent:#6ea0ff;
--ok:#56d17a;--okbg:#1d3a28;--bad:#ff7b72;--badbg:#412222;--gray:#2a313c;--warn:#e3b341;--warnbg:#3b3014;--c1:#6ea0ff;--c2:#f0a35e;--c3:#4fc3b4;--c4:#c39bd3;--c5:#ec7063;--c6:#aab7b8;}}
:root[data-theme="dark"]{--bg:#12161c;--panel:#1b212a;--text:#e4e8ee;--muted:#9aa5b4;--line:#2f3846;--accent:#6ea0ff;--ok:#56d17a;--okbg:#1d3a28;--bad:#ff7b72;
--badbg:#412222;--gray:#2a313c;--warn:#e3b341;--warnbg:#3b3014;--c1:#6ea0ff;--c2:#f0a35e;--c3:#4fc3b4;--c4:#c39bd3;--c5:#ec7063;--c6:#aab7b8;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,-apple-system,"Segoe UI","Hiragino Sans","Yu Gothic UI",Meiryo,sans-serif}
header{padding:12px 16px;border-bottom:1px solid var(--line);background:var(--panel);display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;position:sticky;top:0;z-index:5}
h1{font-size:17px;margin:0}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav button,.btn{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--text);padding:5px 12px;border-radius:6px;cursor:pointer}
nav button.on{background:var(--accent);border-color:var(--accent);color:#fff}
main{padding:16px;max-width:1280px;margin:0 auto}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:14px}
h2{font-size:16px;margin:22px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
h3{font-size:14px;margin:14px 0 6px}
.filters{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}
.filters label{display:flex;flex-direction:column;font-size:12px;color:var(--muted);gap:2px}
select,input[type=text],input[type=search]{font:inherit;padding:5px 6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--text);width:100%}
.bar{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:8px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;margin-bottom:12px;padding:10px 12px;display:flex;gap:12px;scroll-margin-top:70px}
.card.sel{outline:2px solid var(--accent)}
.card.flag{border-left:5px solid var(--warn)}
.card.dropped{opacity:.78;background:repeating-linear-gradient(135deg,var(--panel),var(--panel) 10px,var(--gray) 10px,var(--gray) 11px)}
.imgs{flex:0 0 232px;display:flex;flex-direction:column;gap:6px}
.imgs img{width:224px;height:auto;max-width:100%;border:1px solid var(--line);border-radius:4px;cursor:zoom-in;background:var(--gray);image-rendering:auto}
.noimg{width:224px;max-width:100%;padding:18px 8px;border:1px dashed var(--line);border-radius:4px;color:var(--muted);text-align:center;font-size:12px}
.body{flex:1;min-width:0}
.head{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;margin-bottom:4px}
.id{font-weight:700;font-family:ui-monospace,Consolas,monospace}
.sub{color:var(--muted);font-family:ui-monospace,Consolas,monospace;font-size:12px}
.chip{display:inline-block;padding:0 7px;border-radius:10px;background:var(--gray);font-size:12px;color:var(--text);white-space:nowrap}
.chip.ok{background:var(--okbg);color:var(--ok)} .chip.bad{background:var(--badbg);color:var(--bad)} .chip.warn{background:var(--warnbg);color:var(--warn)}
.chip.acc{background:var(--accent);color:#fff}
.q{margin:2px 0}
.langs{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px}
.opt{display:block;padding:1px 8px;margin:2px 0;border-radius:5px;background:var(--gray);color:var(--muted)}
.opt.right{background:var(--okbg);color:var(--ok);font-weight:600}
.opt.right::before{content:"\2713  "}
.tag{font-size:11px;color:var(--muted)}
.dots{display:flex;flex-wrap:wrap;gap:2px 10px;margin-top:6px}
.dotg{display:inline-flex;gap:1px;align-items:center;font-size:10px;color:var(--muted)}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;background:var(--gray);border:1px solid var(--line)}
.dot.y{background:var(--ok);border-color:var(--ok)} .dot.n{background:var(--bad);border-color:var(--bad)}
details{margin-top:4px} summary{cursor:pointer;color:var(--muted);font-size:12px}
.hist{font-size:12px;margin:3px 0 3px 4px;padding-left:8px;border-left:3px solid var(--line);word-break:break-word}
.pager{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
table{border-collapse:collapse;font-size:12.5px;width:100%}
th,td{border:1px solid var(--line);padding:3px 7px;text-align:right;vertical-align:top}
th:first-child,td:first-child{text-align:left}
td.l{text-align:left}
thead th{background:var(--gray);position:sticky;top:0}
.tw{overflow-x:auto;max-height:560px;margin-bottom:8px}
.tw.full{max-height:none}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.note{color:var(--muted);font-size:12px}
svg text{fill:var(--text);font-size:11px;font-family:inherit}
svg .mut{fill:var(--muted)}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.82);display:none;align-items:center;justify-content:center;z-index:20;gap:10px;flex-wrap:wrap;padding:12px;overflow:auto}
.lb.on{display:flex}
.lb img{max-width:46vw;min-width:224px;width:auto;height:auto;max-height:90vh;image-rendering:auto;background:#fff;border-radius:4px;cursor:zoom-out}
.heat td{text-align:right}
.hide{display:none}
@media (max-width:760px){.card{flex-direction:column}.imgs{flex-basis:auto}.langs{grid-template-columns:1fr}main{padding:10px}.lb img{max-width:92vw}}
</style>
</head>
<body>
<header>
<h1>__TITLE__</h1>
<nav id="tabs"></nav>
<span class="note" id="hdrinfo"></span>
</header>
<main>
<section id="v-cards" class="hide"></section>
<section id="v-stats" class="hide"></section>
<section id="v-idmap" class="hide"></section>
</main>
<div class="lb" id="lb"></div>
<script>
"use strict";
const D = /*__DATA__*/null;
const $ = (s, r) => (r || document).querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt = n => Number(n).toLocaleString("ja-JP");
const pct = (a, b) => b ? (100 * a / b).toFixed(1) + "%" : "-";
const GROUPS = ["photo", "biz", "rsn", "txt"];
const PAL = ["--c1", "--c2", "--c3", "--c4", "--c5", "--c6"];
const col = i => "var(" + PAL[i % PAL.length] + ")";
const MODELS = D.models;
const GJ = {photo: "photo（実写）", biz: "biz（業務画像）", rsn: "rsn（推論）", txt: "txt（文章のみ）"};
const STATE_JA = {reviewed: "reviewed（問題なし）", changed: "changed（修正）", dropped: "dropped（除外）", unreviewed: "unreviewed"};
const PRI_JA = {all_wrong: "全モデルが外した", majority_wrong: "半数以上が外した", normal: "通常", no_results: "測定なし"};

/* ---------------- statistics helpers (pure) ---------------- */
function sumOf(list) { return list.reduce((a, x) => a + x[1], 0); }
function barSvg(items, opt) {
  opt = opt || {};
  const W = 560, lh = 20, lw = opt.lw || 150, pad = 52, n = items.length;
  const max = Math.max(1, ...items.map(x => x[1]));
  let s = '<svg viewBox="0 0 ' + W + " " + (n * lh + 6) + '" width="100%" role="img" aria-label="' + esc(opt.title || "") + '">';
  items.forEach((x, i) => {
    const w = (W - lw - pad) * x[1] / max, y = i * lh + 3;
    s += '<text x="' + (lw - 6) + '" y="' + (y + 13) + '" text-anchor="end">' + esc(String(x[0]).slice(0, 26)) + "</text>";
    s += '<rect x="' + lw + '" y="' + y + '" width="' + Math.max(w, x[1] ? 1 : 0).toFixed(1) + '" height="14" rx="2" fill="' + col(opt.color || 0) + '"/>';
    s += '<text x="' + (lw + w + 4) + '" y="' + (y + 12) + '" class="mut">' + fmt(x[1]) + "</text>";
  });
  return s + "</svg>";
}
function stackSvg(cr, opt) {  /* one horizontal bar per row, stacked by column */
  const W = 560, lh = 22, lw = 80, n = cr.rows.length;
  const tot = cr.cells.map(r => r.reduce((a, b) => a + b, 0)), max = Math.max(1, ...tot);
  let s = '<svg viewBox="0 0 ' + W + " " + (n * lh + 8) + '" width="100%">';
  cr.rows.forEach((rn, i) => {
    const y = i * lh + 4; let x = lw;
    s += '<text x="' + (lw - 6) + '" y="' + (y + 13) + '" text-anchor="end">' + esc(rn) + "</text>";
    cr.cells[i].forEach((v, j) => {
      const w = (W - lw - 50) * v / max;
      if (v) s += '<rect x="' + x.toFixed(1) + '" y="' + y + '" width="' + w.toFixed(1) + '" height="16" fill="' + col(j) + '"><title>' + esc(rn + " / " + cr.cols[j] + ": " + v) + "</title></rect>";
      x += w;
    });
    s += '<text x="' + (x + 4) + '" y="' + (y + 13) + '" class="mut">' + fmt(tot[i]) + "</text>";
  });
  return s + "</svg>" + legend(cr.cols);
}
function legend(cols) {
  return '<div class="note" style="display:flex;flex-wrap:wrap;gap:2px 12px">' + cols.map((c, j) => '<span><span class="dot" style="background:' + col(j) + ';border-color:' + col(j) + '"></span> ' + esc(c) + "</span>").join("") + "</div>";
}
function table(head, rows, cls) {
  return '<div class="tw ' + (cls || "") + '"><table><thead><tr>' + head.map(h => "<th>" + esc(h) + "</th>").join("") + "</tr></thead><tbody>" +
    rows.map(r => "<tr>" + r.map((c, i) => "<td" + (typeof c === "string" && i === 0 ? "" : "") + ">" + (c && c.html != null ? c.html : esc(c)) + "</td>").join("") + "</tr>").join("") + "</tbody></table></div>";
}
function countTable(items, label) {
  const t = sumOf(items);
  return table([label, "問数", "割合"], items.map(x => [x[0], fmt(x[1]), pct(x[1], t)]).concat([["合計", fmt(t), "100%"]]));
}
function crossTable(cr, rowLabel) {
  const ct = cr.cols.map((_, j) => cr.cells.reduce((a, r) => a + r[j], 0));
  const body = cr.rows.map((rn, i) => [rn].concat(cr.cells[i].map(v => fmt(v)), [fmt(cr.cells[i].reduce((a, b) => a + b, 0))]));
  body.push(["合計"].concat(ct.map(fmt), [fmt(ct.reduce((a, b) => a + b, 0))]));
  return table([rowLabel].concat(cr.cols, ["計"]), body);
}
function posTable(list) {
  const maxn = Math.max(0, ...list.map(x => x.n));
  const head = ["群", "選択肢数", "問数"].concat(Array.from({length: maxn}, (_, i) => "位置" + (i + 1)), ["最大-最小"]);
  return table(head, list.map(x => {
    const tot = x.counts.reduce((a, b) => a + b, 0);
    return [x.group, x.n, fmt(tot)].concat(Array.from({length: maxn}, (_, i) => i < x.n ? x.counts[i] + " (" + pct(x.counts[i], tot) + ")" : ""), [Math.max(...x.counts) - Math.min(...x.counts)]);
  }));
}
function yesTable(rows, label) {
  return table([label, "はい", "いいえ", "計", "はいの割合"], rows.map(r => [r[0], fmt(r[1]), fmt(r[2]), fmt(r[1] + r[2]), pct(r[1], r[1] + r[2])]));
}

/* ---------------- stats view ---------------- */
let scope = "active";
function renderStats() {
  const S = D.stats[scope], I = D.idmap_stats, el = $("#v-stats");
  const dims = S.dims, dbg = S.dims_by_group;
  let h = '<div class="panel"><div class="bar"><b>集計の対象:</b> <label><input type="radio" name="sc" value="active"' + (scope === "active" ? " checked" : "") +
    '> dropped を除く（' + fmt(D.stats.active.total) + ' 問）</label> <label><input type="radio" name="sc" value="all"' + (scope === "all" ? " checked" : "") +
    '> 全問（dropped を含む ' + fmt(D.stats.all.total) + ' 問）</label></div><div class="note">数値は全て v1 の問題ファイル・ID 対応表・レビュー原本・旧ログから生成時に計算した値です。legacy→v1 の表だけは対象の切り替えに依らず ID 対応表の全行です。</div></div>';
  h += "<h2>1. 群別の問数と legacy→v1 の増減</h2><div class='grid2'><div>";
  h += table(["v1 群", "legacy から", "kept", "rewritten", "pending", "dropped", "新規（new）", "v1 の問数（dropped を除く）", "増減"],
    I.rows.map(r => [r.group, fmt(r.legacy), fmt(r.kept), fmt(r.rewritten), fmt(r.pending), fmt(r.dropped), fmt(r.new || 0), fmt(r.v1), (r.v1 - r.legacy >= 0 ? "+" : "") + (r.v1 - r.legacy)]).concat(
      [["合計", fmt(I.total), fmt(I.rows.reduce((a, r) => a + r.kept, 0)), fmt(I.rows.reduce((a, r) => a + r.rewritten, 0)), fmt(I.rows.reduce((a, r) => a + r.pending, 0)),
        fmt(I.rows.reduce((a, r) => a + r.dropped, 0)), fmt(I.rows.reduce((a, r) => a + (r.new || 0), 0)), fmt(I.rows.reduce((a, r) => a + r.v1, 0)), ""]]));
  h += '<div class="note">ID 対応表の status による。新規（new）は後から足した問（new_&lt;tag&gt;.jsonl）で、legacy の列には入らない。pending は 2 枚画像の問で、1 枚に作り直すか外すかを決める前のもの。</div>';
  if (I.dropped_mismatch.length) h += '<div class="note"><span class="chip warn">注意</span> review.state=dropped と ID 対応表 status=dropped が食い違う問が ' + I.dropped_mismatch.length + ' 件あります（' + esc(I.dropped_mismatch.slice(0, 8).join(", ")) + (I.dropped_mismatch.length > 8 ? " ..." : "") + '）。</div>';
  h += "</div><div>" + table(["legacy の群", "v1 の群", "問数"], I.flow.map(f => [f[0], f[1], fmt(f[2])])) + "</div></div>";
  h += "<h3>v1 の問数（問題ファイル）</h3><div class='grid2'><div>" + barSvg(S.groups.map(g => [g[0], g[1]]), {title: "群別"}) + "</div><div>" + countTable(S.groups, "群") + "</div></div>";
  const dimBlock = (key, title, label, lw) => {
    let x = "<h2>" + title + "</h2><div class='grid2'><div>" + barSvg(dims[key], {lw: lw || 150, title: title}) + "</div><div>" + countTable(dims[key], label) + "</div></div>";
    if (dbg[key]) x += "<h3>群別</h3><div class='tw'>" + table([label].concat(GROUPS, ["計"]), dims[key].map(d => [d[0]].concat(GROUPS.map(g => { const f = dbg[key][g].find(z => z[0] === d[0]); return fmt(f ? f[1] : 0); }), [fmt(d[1])]))) + "</div>";
    return x;
  };
  h += dimBlock("image_type", "2. image_type 別", "image_type");
  h += dimBlock("skill", "3. skill 別", "skill");
  h += "<h2>4. answer_format 別（選択肢数・段階数）</h2><div class='grid2'><div>" + barSvg(dims.answer_format, {title: "answer_format"}) + "</div><div>" + countTable(dims.answer_format, "形式（choice:n = 選択肢数）") + "</div></div>";
  h += "<h3>厳密な形式（5 択以上を分けない）</h3>" + countTable(dims.answer_format_exact, "answer_format");
  h += "<h3>群別</h3>" + table(["形式"].concat(GROUPS, ["計"]), dims.answer_format.map(d => [d[0]].concat(GROUPS.map(g => { const f = dbg.answer_format[g].find(z => z[0] === d[0]); return fmt(f ? f[1] : 0); }), [fmt(d[1])])));
  if (S.score_levels.length) h += "<h3>段階評価の段階数</h3>" + countTable(S.score_levels.map(x => [x[0] + " 段階", x[1]]), "段階数");
  h += dimBlock("difficulty", "5. 難度別", "difficulty");
  h += dimBlock("lang", "6. 言語別（lang）", "lang");
  h += dimBlock("source", "7. source 別", "source");
  h += "<h3>kind 別</h3>" + countTable(dims.kind, "kind") + "<h3>レビュー状態（review.state）</h3>" + countTable(dims.review_state, "state");
  h += "<h2>8. 正解位置の分布</h2><div class='note'>legacy = 旧ローダーの並び（legacy の ID から決まる固定の並び。legacy のモデル測定で見た並び）。balanced = v1 の割り当て（群×選択肢数で均等。この表の対象の問だけで計算）。位置は 1 始まり。</div>";
  h += "<h3>legacy（現行の並び）</h3>" + posTable(S.pos.legacy) + "<h3>balanced</h3>" + posTable(S.pos.balanced);
  h += "<h2>9. はい／いいえ問の正解比</h2><div class='grid2'><div>" + yesTable(S.yesno.by_group.concat([["合計"].concat(S.yesno.total)]), "群") + "<h3>source 別</h3>" + yesTable(S.yesno.by_source, "source") +
    "</div><div><h3>skill 別</h3>" + yesTable(S.yesno.by_skill, "skill") + "<h3>image_type 別</h3>" + yesTable(S.yesno.by_image_type, "image_type") + "</div></div>";
  h += "<h2>10. レビューの verdict と issues タグ</h2><div class='grid2'><div><h3>verdict（レビュー原本）</h3>" + countTable(S.verdicts, "verdict") +
    "<div class='note'>issues が付いた問: " + fmt(S.with_issues) + " 問（タグは issue 文字列の ':' や '(' より前）。</div><h3>旧モデル結果の区分</h3>" + countTable(S.priority.map(p => [PRI_JA[p[0]] || p[0], p[1]]), "区分") +
    "</div><div><h3>issues タグ（問数）</h3>" + table(["タグ", "問数"].concat(GROUPS), S.issue_tags.map(t => [t[0], fmt(t[1])].concat(GROUPS.map(g => { const f = S.issue_tags_by_group[g].find(z => z[0] === t[0]); return fmt(f ? f[1] : 0); })))) + "</div></div>";
  h += "<h3>注目タグ</h3>" + table(["タグ", "問数"], ["privacy-check", "hard-but-valid", "needs_new_image_type", "duplicate", "unverifiable"].map(k => [k, fmt((S.issue_tags.find(z => z[0] === k) || [0, 0])[1])]));
  h += "<h2>11. 既存モデルの正答率（legacy の測定。en/ja）</h2><div class='note'>各セルは 正解数/回答数（割合）。測定が無い問（txt、legacy で回答なし、QEV の 2 枚画像）は分母に入らない。この表の対象の問だけで集計。</div>";
  h += table(["model", "lang"].concat(GROUPS, ["全体"]), S.models.map(m => [m.model, m.lang].concat(GROUPS.map(g => m.cells[g][1] ? m.cells[g][0] + "/" + m.cells[g][1] + " (" + pct(m.cells[g][0], m.cells[g][1]) + ")" : "-"),
    [m.total[1] ? m.total[0] + "/" + m.total[1] + " (" + pct(m.total[0], m.total[1]) + ")" : "-"])));
  h += "<h3>群別の正答率（en と ja の平均）</h3>" + barSvg(S.models.filter(m => m.lang === "en").map(m => [m.model, 0]).map((x, i) => {
    const e = S.models[2 * i].total, j = S.models[2 * i + 1].total; const a = e[1] + j[1]; return [x[0] + " (%)", a ? Math.round(1000 * (e[0] + j[0]) / a) / 10 : 0];
  }), {title: "モデル別の正答率", lw: 120});
  h += "<h2>12. クロス集計</h2><h3>群 × skill</h3><div class='grid2'><div>" + crossTable(S.cross.group_skill, "群") + "</div><div>" + stackSvg(S.cross.group_skill) + "</div></div>";
  h += "<h3>群 × 難度</h3><div class='grid2'><div>" + crossTable(S.cross.group_difficulty, "群") + "</div><div>" + stackSvg(S.cross.group_difficulty) + "</div></div>";
  h += "<h3>群 × image_type</h3><div class='grid2'><div>" + crossTable(S.cross.group_image_type, "群") + "</div><div>" + stackSvg(S.cross.group_image_type) + "</div></div>";
  h += "<h3>群 × 形式</h3><div class='grid2'><div>" + crossTable(S.cross.group_format, "群") + "</div><div>" + stackSvg(S.cross.group_format) + "</div></div>";
  h += "<h3>skill × 難度</h3>" + crossTable(S.cross.skill_difficulty, "skill");
  el.innerHTML = h;
  el.querySelectorAll("input[name=sc]").forEach(r => r.onchange = () => { scope = r.value; renderStats(); });
}

/* ---------------- idmap view ---------------- */
let idPage = 0;
function renderIdmap() {
  const el = $("#v-idmap");
  if (!el.dataset.init) {
    el.dataset.init = 1;
    const opts = k => ["<option value=''>すべて</option>"].concat([...new Set(D.idmap.map(m => m[k]))].sort().map(v => "<option>" + esc(v) + "</option>")).join("");
    el.innerHTML = '<div class="panel"><div class="filters"><label>検索（ID・change_note）<input type="search" id="im-q" placeholder="img-0016 / photo-0001 / 語句"></label>' +
      '<label>status<select id="im-st">' + opts("status") + '</select></label><label>legacy の群<select id="im-g1">' + opts("group_legacy") + '</select></label><label>v1 の群<select id="im-g2">' + opts("group_v1") +
      '</select></label><label>review_state<select id="im-rs">' + opts("review_state") + '</select></label></div><div class="bar"><span id="im-n"></span><span class="pager" id="im-pg"></span></div></div><div id="im-t"></div>';
    ["#im-q", "#im-st", "#im-g1", "#im-g2", "#im-rs"].forEach(s => $(s).oninput = () => { idPage = 0; drawIdmap(); });
  }
  drawIdmap();
}
function drawIdmap() {
  const q = $("#im-q").value.trim().toLowerCase(), st = $("#im-st").value, g1 = $("#im-g1").value, g2 = $("#im-g2").value, rs = $("#im-rs").value;
  const rows = D.idmap.filter(m => (!st || m.status === st) && (!g1 || m.group_legacy === g1) && (!g2 || m.group_v1 === g2) && (!rs || m.review_state === rs) &&
    (!q || (m.legacy_id + " " + m.v1_id + " " + m.change_note).toLowerCase().includes(q)));
  const PS = 100, pages = Math.max(1, Math.ceil(rows.length / PS)); idPage = Math.min(idPage, pages - 1);
  $("#im-n").textContent = fmt(rows.length) + " / " + fmt(D.idmap.length) + " 件";
  $("#im-pg").innerHTML = '<button class="btn" id="im-p">前</button> ' + (idPage + 1) + " / " + pages + ' <button class="btn" id="im-nx">次</button>';
  $("#im-p").onclick = () => { idPage = Math.max(0, idPage - 1); drawIdmap(); };
  $("#im-nx").onclick = () => { idPage = Math.min(pages - 1, idPage + 1); drawIdmap(); };
  const link = id => D.public ? esc(id) : '<a href="#" data-go="' + esc(id) + '">' + esc(id) + "</a>";
  $("#im-t").innerHTML = '<div class="tw full"><table><thead><tr><th>legacy_id</th><th>v1_id</th><th>legacy 群</th><th>v1 群</th><th>status</th><th>review_state</th><th>change_note</th></tr></thead><tbody>' +
    rows.slice(idPage * PS, idPage * PS + PS).map(m => "<tr><td>" + esc(m.legacy_id) + "</td><td>" + link(m.v1_id) + "</td><td>" + esc(m.group_legacy) + "</td><td>" + esc(m.group_v1) + "</td><td class='l'>" + esc(m.status) + "</td><td class='l'>" + esc(m.review_state) + "</td><td class='l'>" + esc(m.change_note) + "</td></tr>").join("") + "</tbody></table></div>";
  $("#im-t").querySelectorAll("a[data-go]").forEach(a => a.onclick = e => { e.preventDefault(); gotoCard(a.dataset.go); });
}

/* ---------------- cards view ---------------- */
let FLAGS = new Set();
try { FLAGS = new Set(JSON.parse(localStorage.getItem("dsum_flags_v1") || localStorage.getItem("dsum_flags_v2") || "[]")); } catch (e) {}   // dsum_flags_v2: the key before the rename (flags a reviewer already set)
function saveFlags() { try { localStorage.setItem("dsum_flags_v1", JSON.stringify([...FLAGS])); } catch (e) {} }
const PS = 30;
let F = {}, list = [], page = 0, selIdx = 0;
const R = D.records || [];
const tagsOf = r => [...new Set(r.iss.map(issueTag))];
function issueTag(s) { const t = String(s).split(/[:：(（]/)[0].trim().toLowerCase().slice(0, 48); return t || "(empty)"; }
R.forEach(r => { const en = r.en || {}, ja = r.ja || {}; r._tags = tagsOf(r); r._hay = [r.id, r.legacy, en.q, ja.q, en.c, ja.c, (en.w || []).join(" "), (ja.w || []).join(" "), r.iss.join(" "), r.rsn, r.cn, r.tg.join(" ")].join("\n").toLowerCase(); });
function opts(vals, sel) { return ["<option value=''>すべて</option>"].concat(vals.map(v => "<option value='" + esc(v[0]) + "'>" + esc(v[1]) + "</option>")).join(""); }
function uniq(key, f) { const c = {}; R.forEach(r => { const v = f ? f(r) : r[key]; c[v] = (c[v] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)); }
function renderCards() {
  const el = $("#v-cards");
  if (!el.dataset.init) {
    el.dataset.init = 1;
    const vopt = (key, f) => opts(uniq(key, f).map(x => [x[0], x[0] + "（" + x[1] + "）"]));
    const tagc = {}; R.forEach(r => r._tags.forEach(t => tagc[t] = (tagc[t] || 0) + 1));
    const tagOpts = opts(Object.entries(tagc).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).map(x => [x[0], x[0] + "（" + x[1] + "）"]));
    el.innerHTML = '<div class="panel"><div class="filters">' +
      '<label>検索（ID・設問・選択肢・issues）<input type="search" id="f-q" placeholder="photo-0001 / img-0016 / 語句"></label>' +
      '<label>群<select id="f-g">' + vopt("g") + '</select></label><label>image_type<select id="f-it">' + vopt("it") + '</select></label>' +
      '<label>skill<select id="f-sk">' + vopt("sk") + '</select></label><label>answer_format<select id="f-af">' + vopt("af") + '</select></label>' +
      '<label>選択肢数（choice）<select id="f-n">' + opts([["2", "2"], ["3", "3"], ["4", "4"], ["5+", "5 以上"], ["yn", "はい/いいえ"], ["sc", "段階評価"]]) + '</select></label>' +
      '<label>難度<select id="f-df">' + vopt("df") + '</select></label><label>review 状態<select id="f-st">' + vopt("st") + '</select></label>' +
      '<label>ID 対応の status<select id="f-ms">' + vopt("ms") + '</select></label><label>issues タグ<select id="f-tag">' + tagOpts + '</select></label>' +
      '<label>言語<select id="f-lg">' + vopt("lg") + '</select></label>' +
      '<label>旧モデル結果<select id="f-pri">' + opts([["all_wrong", "全モデルが外した"], ["maj", "半数以上が外した（全モデル含む）"], ["normal", "通常"], ["no_results", "測定なし"]]) + '</select></label>' +
      '<label>並び<select id="f-sort"><option value="id">ID 順</option><option value="wrong">外したモデルが多い順</option></select></label></div>' +
      '<div class="bar"><label><input type="checkbox" id="f-drop" checked> dropped を含める</label> <label><input type="checkbox" id="f-flag"> 要確認のみ</label> ' +
      '<button class="btn" id="f-reset">条件をクリア</button> <button class="btn" id="f-exp">要確認 ID を表示</button> <span class="note">キー: ← / k 前、→ / j 次、f 要確認、Enter 画像拡大、Esc 閉じる</span></div>' +
      '<div class="bar"><b id="f-n-out"></b><span class="pager" id="pg-top"></span></div><textarea id="f-exptext" class="hide" rows="4" style="width:100%" readonly></textarea></div>' +
      '<div id="cards"></div><div class="bar"><span class="pager" id="pg-bot"></span></div>';
    el.querySelectorAll("select,input").forEach(x => x.oninput = () => { page = 0; selIdx = 0; applyFilter(); });
    $("#f-reset").onclick = () => { el.querySelectorAll("select").forEach(s => s.selectedIndex = 0); $("#f-q").value = ""; $("#f-drop").checked = true; $("#f-flag").checked = false; page = 0; selIdx = 0; applyFilter(); };
    $("#f-exp").onclick = () => { const t = $("#f-exptext"); t.value = [...FLAGS].sort().join("\n"); t.classList.toggle("hide"); if (!t.classList.contains("hide")) t.select(); };
  }
  applyFilter();
}
function match(r) {
  const v = id => $(id).value;
  if (!$("#f-drop").checked && r.st === "dropped") return false;
  if ($("#f-flag").checked && !FLAGS.has(r.id)) return false;
  if (v("#f-g") && r.g !== v("#f-g")) return false;
  if (v("#f-it") && r.it !== v("#f-it")) return false;
  if (v("#f-sk") && r.sk !== v("#f-sk")) return false;
  if (v("#f-af") && r.af !== v("#f-af")) return false;
  const n = v("#f-n");
  if (n) { if (n === "yn" ? r.kd !== "noul" : n === "sc" ? r.kd !== "score" : (r.kd !== "choice" || (n === "5+" ? r.n < 5 : r.n !== +n))) return false; }
  if (v("#f-df") && r.df !== v("#f-df")) return false;
  if (v("#f-st") && r.st !== v("#f-st")) return false;
  if (v("#f-ms") && r.ms !== v("#f-ms")) return false;
  if (v("#f-tag") && !r._tags.includes(v("#f-tag"))) return false;
  if (v("#f-lg") && r.lg !== v("#f-lg")) return false;
  const p = v("#f-pri");
  if (p === "maj" ? !(r.pri === "all_wrong" || r.pri === "majority_wrong") : (p && r.pri !== p)) return false;
  const q = v("#f-q").trim().toLowerCase();
  if (q && !r._hay.includes(q)) return false;
  return true;
}
function applyFilter() {
  list = R.filter(match);
  if ($("#f-sort").value === "wrong") list = list.slice().sort((a, b) => (b.an ? b.wr / b.an : -1) - (a.an ? a.wr / a.an : -1) || (a.id < b.id ? -1 : 1));
  const pages = Math.max(1, Math.ceil(list.length / PS));
  page = Math.min(page, pages - 1); selIdx = Math.min(selIdx, Math.max(0, list.length - 1));
  $("#f-n-out").textContent = fmt(list.length) + " / " + fmt(R.length) + " 問";
  drawCards();
}
function drawPager() {
  const pages = Math.max(1, Math.ceil(list.length / PS));
  const pg = '<button class="btn" data-p="-1">前のページ</button> ' + (page + 1) + " / " + pages + ' <button class="btn" data-p="1">次のページ</button>';
  ["#pg-top", "#pg-bot"].forEach(s => { const e = $(s); if (!e) return; e.innerHTML = pg; e.querySelectorAll("button").forEach(b => b.onclick = () => { page = Math.max(0, Math.min(pages - 1, page + +b.dataset.p)); selIdx = page * PS; drawCards(); window.scrollTo(0, 0); }); });
}
function optsHtml(r, l) {
  const s = r[l]; if (!s) return "";
  if (r.kd === "choice") return '<span class="opt right">' + esc(s.c) + "</span>" + s.w.map(w => '<span class="opt">' + esc(w) + "</span>").join("");
  if (r.kd === "score") return s.lv.map((t, i) => '<span class="opt' + (i === r.ans ? " right" : "") + '">' + (i + 1) + ". " + esc(t) + "</span>").join("");
  return '<span class="opt right">' + (r.truth ? "はい（true）" : "いいえ（false）") + "</span>";
}
function cardHtml(r, i) {
  const bad = r.st === "dropped", chipSt = r.st === "dropped" ? "bad" : r.st === "changed" ? "warn" : "ok";
  let h = '<div class="card' + (bad ? " dropped" : "") + (FLAGS.has(r.id) ? " flag" : "") + (i === selIdx ? " sel" : "") + '" id="c-' + esc(r.id) + '" data-i="' + i + '">';
  h += '<div class="imgs">';
  if (r.txt) h += '<div class="noimg">文章のみの問<br>本文あり（非表示）<br><span class="tag">' + esc(r.txt.en) + " / " + esc(r.txt.ja) + "</span></div>";
  else if (r.im.length) h += r.im.map(p => '<img loading="lazy" src="' + esc(p) + '" alt="' + esc(r.id) + '" data-z="1">').join("");
  else h += '<div class="noimg">画像なし</div>';
  h += '<div class="dots">' + MODELS.map((m, k) => { const c = r.o[k]; return '<span class="dotg" title="' + esc(m + "  en:" + (c[0] === "1" ? "正" : c[0] === "0" ? "誤" : "-") + " ja:" + (c[1] === "1" ? "正" : c[1] === "0" ? "誤" : "-")) + '">' +
    [0, 1].map(j => '<span class="dot ' + (c[j] === "1" ? "y" : c[j] === "0" ? "n" : "") + '"></span>').join("") + m.slice(0, 3) + "</span>"; }).join("") + "</div>";
  h += '<div class="tag">旧モデル: ' + (r.an ? esc(PRI_JA[r.pri]) + "（" + r.wr + "/" + r.an + " 誤り）" : "測定なし") + " ・ 点は左 en・右 ja（緑=正解 赤=誤答）</div></div>";
  h += '<div class="body"><div class="head"><span class="id">' + esc(r.id) + '</span><span class="sub">legacy: ' + esc(r.legacy) + '</span><span class="chip">' + esc(r.g) + '</span><span class="chip ' + chipSt + '">' + esc(r.st) + "</span>" +
    (r.ms ? '<span class="chip">' + esc(r.ms) + "</span>" : "") + (r.ver ? '<span class="chip">verdict: ' + esc(r.ver) + "</span>" : "") + (FLAGS.has(r.id) ? '<span class="chip warn">要確認</span>' : "") +
    '<button class="btn" data-flag="' + esc(r.id) + '" style="padding:0 8px">要確認</button></div>';
  h += '<div class="head"><span class="chip">' + esc(r.src) + '</span><span class="chip">' + esc(r.it) + '</span><span class="chip">' + esc(r.sk) + '</span><span class="chip acc">' + esc(r.af) + '</span><span class="chip">' + esc(r.df) +
    '</span><span class="chip">lang: ' + esc(r.lg) + "</span>" + (r.kd === "choice" && r.pl != null ? '<span class="chip">旧並びの正解位置 ' + (r.pl + 1) + "</span>" : "") + "</div>";
  h += '<div class="langs">' + ["en", "ja"].map(l => r[l] ? '<div><div class="q"><b>' + l.toUpperCase() + "</b> " + esc(r[l].q) + "</div>" + (r[l].s ? '<div class="tag">state: ' + esc(r[l].s) + "</div>" : "") + optsHtml(r, l) + "</div>" : "").join("") + "</div>";
  if (r.iss.length) h += '<div class="head" style="margin-top:6px">' + r.iss.map(x => '<span class="chip warn">' + esc(x) + "</span>").join("") + "</div>";
  if (r.rsn) h += '<div class="q"><span class="tag">レビュー理由:</span> ' + esc(r.rsn) + "</div>";
  if (r.hist.length) h += "<details" + (r.st === "changed" ? " open" : "") + "><summary>変更履歴（" + r.hist.length + "）</summary>" + r.hist.map(x => '<div class="hist"><span class="tag">' + esc(x.d) + "</span> " + esc(x.w) + (x.y ? "<br><b>理由:</b> " + esc(x.y) : "") + "</div>").join("") + "</details>";
  if (r.cn) h += '<div class="tag" style="margin-top:3px">ID 対応メモ: ' + esc(r.cn) + "</div>";
  if (r.tg.length) h += '<div class="tag">tags: ' + esc(r.tg.join(", ")) + "</div>";
  return h + "</div></div>";
}
function drawCards() {
  drawPager();
  $("#cards").innerHTML = list.slice(page * PS, page * PS + PS).map((r, k) => cardHtml(r, page * PS + k)).join("") || '<div class="panel">該当する問はありません。</div>';
  document.querySelectorAll("#cards img[data-z]").forEach(im => im.onclick = e => zoom(e.target.closest(".imgs")));
  document.querySelectorAll("#cards [data-flag]").forEach(b => b.onclick = () => toggleFlag(b.dataset.flag));
}
function toggleFlag(id) { FLAGS.has(id) ? FLAGS.delete(id) : FLAGS.add(id); saveFlags(); const keep = selIdx; drawCards(); selIdx = keep; }
function select(i, scroll) {
  if (!list.length) return;
  selIdx = Math.max(0, Math.min(list.length - 1, i));
  const np = Math.floor(selIdx / PS);
  if (np !== page) { page = np; applyFilter0(); } else { document.querySelectorAll("#cards .card.sel").forEach(c => c.classList.remove("sel")); const c = document.querySelector('#cards .card[data-i="' + selIdx + '"]'); if (c) c.classList.add("sel"); }
  const c = document.querySelector('#cards .card[data-i="' + selIdx + '"]'); if (c && scroll !== false) c.scrollIntoView({block: "nearest"});
}
function applyFilter0() { const k = selIdx; applyFilter(); selIdx = k; drawCards(); }
function gotoCard(id) {
  show("cards"); renderCards();
  $("#f-q").value = id; $("#f-drop").checked = true;
  ["#f-g", "#f-it", "#f-sk", "#f-af", "#f-n", "#f-df", "#f-st", "#f-ms", "#f-tag", "#f-lg", "#f-pri"].forEach(s => $(s).selectedIndex = 0);
  $("#f-flag").checked = false; page = 0; selIdx = 0; applyFilter();
}
function zoom(box) {
  const imgs = [...box.querySelectorAll("img")], lb = $("#lb");
  lb.innerHTML = imgs.map(i => '<img src="' + esc(i.getAttribute("src")) + '">').join(""); lb.classList.add("on");
}
$("#lb").onclick = () => $("#lb").classList.remove("on");
document.addEventListener("keydown", e => {
  if (e.target.matches("input,select,textarea")) return;
  const open = !$("#v-cards").classList.contains("hide");
  if (e.key === "Escape") $("#lb").classList.remove("on");
  if (!open || D.public) return;
  if (e.key === "ArrowRight" || e.key === "j") { select(selIdx + 1); e.preventDefault(); }
  else if (e.key === "ArrowLeft" || e.key === "k") { select(selIdx - 1); e.preventDefault(); }
  else if (e.key === "f" && list[selIdx]) toggleFlag(list[selIdx].id);
  else if (e.key === "Enter" && list[selIdx]) { const c = document.querySelector('#cards .card[data-i="' + selIdx + '"] .imgs'); if (c && c.querySelector("img")) zoom(c); }
});

/* ---------------- tabs ---------------- */
const TABS = (D.public ? [] : [["cards", "問題一覧（目視確認）"]]).concat([["stats", "統計"], ["idmap", "ID 対応（legacy→v1）"]]);
function show(name) {
  TABS.forEach(t => { $("#v-" + t[0]).classList.toggle("hide", t[0] !== name); });
  document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.t === name));
  if (name === "cards") renderCards(); else if (name === "stats") renderStats(); else renderIdmap();
}
$("#tabs").innerHTML = TABS.map(t => '<button data-t="' + t[0] + '">' + t[1] + "</button>").join("");
document.querySelectorAll("#tabs button").forEach(b => b.onclick = () => show(b.dataset.t));
$("#hdrinfo").textContent = "v1 " + fmt(D.stats.all.total) + " 問（dropped " + fmt(D.stats.all.total - D.stats.active.total) + "）" + (D.public ? " ・ 公開版（画像・設問カードなし）" : " ・ ローカル専用（画像を含む）");
show((TABS.find(t => "#" + t[0] === location.hash) || TABS[0])[0]);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    raise SystemExit(main())
