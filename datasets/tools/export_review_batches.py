# -*- coding: utf-8 -*-
"""Write the review input: every v1 question, in batches of about 60 per group, for the reviewer agents (Opus).

    python datasets/tools/export_review_batches.py [--out work/review] [--logs <eval_common>] [--passages <passages.json>]
                                                   [--px224 <dir>] [--origin <wiki_qa/data parent>]

Output (all under work/, git-ignored: it holds pictures and Wikipedia passages, never to be committed):
    work/review/batch_<group>_<NN>.json   one batch; groups photo 1268 / biz 288 / rsn 319 / txt 87 -> 21 / 5 / 5 / 2 batches
    work/review/index.json                batch names, sizes, priority counts
    work/review/out/                      where the reviewer writes <batch name>.jsonl (see datasets/REVIEW_GUIDE.md)
    work/review/images/                   only used if a 224 px picture is missing from the normal place (then made from the original)

Per question: v1 id / legacy id, group, kind, difficulty, tags, current classification (source, image_type, skill, answer_format),
English and Japanese side (instr; choice: the options in the order the models SAW them = the legacy order made from the legacy id,
the index of the right one, plus the plain correct / wrong lists; yes/no: the truth; score: levels and the right index),
the state text (text-only questions: the Wikipedia passage, read from the local passages.json), the absolute paths of the 224 px
picture(s) the models actually received (the reviewer opens them with Read), and the statistics of the old measurements
(10 models x en/ja: right / wrong per model; flags all_wrong / majority_wrong; txt has no measurements: priority "no_results").
Deterministic: the same inputs give the same batch files. Needs no network and never reads .env.

New questions (datasets/questions/v1/new_<tag>.jsonl): ``python datasets/tools/export_review_batches.py --new [tag ...]`` writes
    work/review/new_<tag>_<NN>.json      about 60 questions per batch (sorted by id), the options in the order the models will SEE
                                         (the balanced order over the whole v1 set), with display labels A, B, C ...
    work/review/index_new_<tag>.json
and the reviewer writes work/review/out/new_<tag>_<NN>.jsonl (REVIEW_GUIDE.md). No old logs or passages are needed (a new row has no old
result; a text-only row with an ``article`` needs its local passage, a control carries its own state). Pictures are looked up under
work/generated/px224/, then work/generated/ (a 224 px copy is made into work/review/images/), then the old tree. Batches are numbered by
id order: export once the tag's file is complete (re-exporting after adding rows in the middle renumbers the batches).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import newq, options  # noqa: E402
from datasets.tools import regroup_check, v1_io  # noqa: E402

JEV = ROOT.parents[1]                                   # .../jev-like (the old tree: wiki_qa, eval_common)
BATCH_COUNT = {"photo": 21, "biz": 5, "rsn": 5, "txt": 2}   # about 60 questions each (txt carries the whole passage: smaller)
GUIDE = ROOT / "datasets" / "REVIEW_GUIDE.md"
MODELS = regroup_check.MODELS


def chunks(rows: list, n_batches: int) -> list:
    """Split into n_batches consecutive chunks whose sizes differ by at most one."""
    q, r = divmod(len(rows), n_batches)
    out, i = [], 0
    for b in range(n_batches):
        k = q + (1 if b < r else 0)
        out.append(rows[i:i + k])
        i += k
    return out


def stats_for(legacy_id: str, res: dict, group: str) -> dict:
    """Old-measurement statistics of one question: per model {en: bool|None, ja: bool|None}, counts and a priority flag."""
    per = {}
    answered = wrong = 0
    for m in MODELS:
        e = {}
        for lang in ("en", "ja"):
            ok = res.get((m, lang, legacy_id))
            if ok is not None:
                e[lang] = bool(ok)
                answered += 1
                wrong += 0 if ok else 1
        if e:
            per[m] = e
    if group == "txt" or answered == 0:
        pri = "no_results"
    elif wrong == answered:
        pri = "all_wrong"
    elif wrong * 2 >= answered:
        pri = "majority_wrong"
    else:
        pri = "normal"
    return dict(priority=pri, answered=answered, wrong=wrong,
                wrong_en=sum(1 for e in per.values() if e.get("en") is False), wrong_ja=sum(1 for e in per.values() if e.get("ja") is False),
                per_model=per)


def image_paths(row: dict, px224: list, origin: pathlib.Path, extra_dir: pathlib.Path) -> list:
    """Absolute paths of the 224 px pictures of a row (as the models received them). A missing one is made from the original."""
    from PIL import Image
    out = []
    for li in row.get("local_images", []):
        name = pathlib.Path(li).name
        for d in px224:
            if (d / name).exists():
                out.append(str(d / name))
                break
        else:
            src = origin / li                                   # li = data/images/<sha1>.jpg relative to the old wiki_qa tree
            if not src.exists():
                raise FileNotFoundError("no 224 px picture and no original for %s (%s)" % (row["id"], li))
            extra_dir.mkdir(parents=True, exist_ok=True)
            im = Image.open(src).convert("RGB")
            im.thumbnail((224, 224), Image.LANCZOS)
            dst = extra_dir / name
            im.save(dst)
            out.append(str(dst))
    return out


def lang_side(row: dict, lang: str, order: list, passages: dict) -> dict:
    q = row[lang]
    side = {"instr": q["instr"]}
    if row.get("modality") == "text" and "article" in row:
        a = row["article"][lang]
        try:
            side["state"] = passages["%s:%s" % (lang, a["revid"])]["text"]
        except KeyError:
            raise FileNotFoundError("passage %s:%s missing from passages.json (local data)" % (lang, a["revid"])) from None
        side["article_title"] = a["title"]
    elif q.get("state"):
        side["state"] = q["state"]
    if row["kind"] == "choice":
        items = [q["correct"]] + list(q["wrong"])
        side.update(options_as_shown=[items[i] for i in order], expected_index=options.expected_of(order), correct=q["correct"],
                    wrong=list(q["wrong"]))
    elif row["kind"] == "noul":
        side["truth"] = bool(row["answer"])
    else:
        side.update(levels=list(q["levels"]), expected_index=int(row["answer"]))
    return side


def question_record(row: dict, res: dict, passages: dict, px224: list, origin: pathlib.Path, extra_dir: pathlib.Path) -> dict:
    langs = row.get("langs") or ["en", "ja"]
    order = None
    if row["kind"] == "choice":
        order = options.legacy_order(row["legacy_id"], 1 + len(row[langs[0]]["wrong"]))   # legacy id: the order the models saw
    rec = dict(id=row["id"], legacy_id=row["legacy_id"], group=row["group"], kind=row["kind"], difficulty=row.get("difficulty"),
               tags=row.get("tags", []), source=row["source"], image_type=row["image_type"], skill=row["skill"],
               answer_format=row["answer_format"], langs=langs, review_state=row["review"]["state"],
               images=image_paths(row, px224, origin, extra_dir))
    if len(rec["images"]) > 1:
        rec["two_images"] = True
    for lang in langs:
        rec[lang] = lang_side(row, lang, order, passages)
    rec["old_results"] = stats_for(row["legacy_id"], res, row["group"])
    return rec


def export(out: pathlib.Path, logs: pathlib.Path, passages_path: pathlib.Path, px224: list, origin: pathlib.Path,
           v1dir: pathlib.Path = v1_io.V1DIR) -> list:
    by_group = v1_io.load_v1(v1dir)
    res = regroup_check.compute(logs)
    passages = json.loads(passages_path.read_text(encoding="utf-8"))
    (out / "out").mkdir(parents=True, exist_ok=True)
    index = []
    for g in v1_io.GROUPS:
        rows = sorted(by_group.get(g, []), key=lambda r: r["id"])
        for i, chunk in enumerate(chunks(rows, BATCH_COUNT[g]), 1):
            name = "batch_%s_%02d" % (g, i)
            qs = [question_record(r, res, passages, px224, origin, out / "images") for r in chunk]
            pri = lambda p: [q["id"] for q in qs if q["old_results"]["priority"] == p]
            batch = dict(batch=name, group=g, n_questions=len(qs), guide=str(GUIDE),
                         output_file=str(out / "out" / (name + ".jsonl")),
                         priority_all_wrong=pri("all_wrong"), priority_majority_wrong=pri("majority_wrong"), questions=qs)
            (out / (name + ".json")).write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            index.append(dict(batch=name, group=g, n=len(qs), first=qs[0]["id"], last=qs[-1]["id"],
                              all_wrong=len(batch["priority_all_wrong"]), majority_wrong=len(batch["priority_majority_wrong"]),
                              images=sum(len(q["images"]) for q in qs)))
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return index


# ------------------------------------------------------------------------------------------------ new questions
NEW_PER_BATCH = 60


def new_batches(rows: list, per_batch: int = NEW_PER_BATCH) -> list:
    """Consecutive chunks of about per_batch rows (sizes differ by at most one), in id order."""
    rows = sorted(rows, key=lambda r: r["id"])
    return chunks(rows, max(1, -(-len(rows) // per_batch))) if rows else []


def new_image_paths(row: dict, px224: list, roots: list, extra_dir: pathlib.Path) -> list:
    """224 px picture paths of a new row: a ready 224 px copy, else made from the original found under one of ``roots``."""
    last = None
    for root in roots or [pathlib.Path(".")]:
        try:
            return image_paths(row, px224, pathlib.Path(root), extra_dir)
        except FileNotFoundError as e:
            last = e
    raise last


def new_question_record(row: dict, order, passages: dict, px224: list, roots: list, extra_dir: pathlib.Path) -> dict:
    """One new question for the reviewer: like question_record, with the BALANCED order (what the models will see) and no old results."""
    langs = row.get("langs") or ["en", "ja"]
    rec = dict(id=row["id"], legacy_id=None, new=True, origin=row.get("origin"), derived_from=row.get("derived_from"),
               relation=row.get("relation"), group=row["group"], kind=row["kind"], difficulty=row.get("difficulty"),
               tags=row.get("tags", []), source=row["source"], image_type=row["image_type"], skill=row["skill"],
               answer_format=row["answer_format"], lang=row.get("lang", "both"), langs=langs, review_state=row["review"]["state"],
               images=new_image_paths(row, px224, roots, extra_dir) if row.get("local_images") else [])
    for lang in langs:
        side = lang_side(row, lang, order, passages)
        if row["kind"] == "choice":
            side["option_labels"] = options.option_labels(len(side["options_as_shown"]))
        rec[lang] = side
    return rec


def export_new(out: pathlib.Path, v1dir: pathlib.Path = v1_io.V1DIR, px224: list = (), roots: list = (), passages_path=None,
               tags: list | None = None, per_batch: int = NEW_PER_BATCH, manifests: pathlib.Path | None = None) -> list:
    """Write work/review/new_<tag>_<NN>.json for the new questions (not dropped) of the given tags (default all) and index_new.json."""
    from datasets import loader
    by_tag = v1_io.load_new(v1dir)
    drop = loader.dropped_ids(manifests) if manifests is not None else set()
    universe = [r for r in v1_io.all_rows(v1_io.load_v1(v1dir)) + v1_io.all_new_rows(by_tag) if not loader.is_dropped(r, drop)]
    orders = options.v1_orders(universe)
    passages = {}
    if passages_path and pathlib.Path(passages_path).exists():
        passages = json.loads(pathlib.Path(passages_path).read_text(encoding="utf-8"))
    (out / "out").mkdir(parents=True, exist_ok=True)
    index = []
    for tag in sorted(tags or by_tag):
        if tag not in by_tag:
            raise SystemExit("no new_%s.jsonl in %s" % (tag, v1dir))
        rows = [r for r in by_tag[tag] if not loader.is_dropped(r, drop)]
        for i, chunk in enumerate(new_batches(rows, per_batch), 1):
            name = "new_%s_%02d" % (tag, i)
            qs = [new_question_record(r, orders.get(r["id"]), passages, list(px224), list(roots), out / "images") for r in chunk]
            batch = dict(batch=name, group="new:" + tag, tag=tag, n_questions=len(qs), guide=str(GUIDE),
                         output_file=str(out / "out" / (name + ".jsonl")), priority_all_wrong=[], priority_majority_wrong=[], questions=qs)
            (out / (name + ".json")).write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            index.append(dict(batch=name, tag=tag, n=len(qs), first=qs[0]["id"], last=qs[-1]["id"], images=sum(len(q["images"]) for q in qs)))
    for tag in sorted({b["tag"] for b in index}):                          # one index per tag: writers never share a file
        (out / ("index_new_%s.json" % tag)).write_text(json.dumps([b for b in index if b["tag"] == tag], ensure_ascii=False, indent=1) + "\n",
                                                     encoding="utf-8", newline="\n")
    return index


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work" / "review"))
    ap.add_argument("--logs", default=str(JEV / "eval_common"))
    ap.add_argument("--passages", default=str(JEV / "wiki_qa" / "data" / "passages.json"))
    ap.add_argument("--px224", action="append", default=None, help="directory with the 224 px pictures (repeatable)")
    ap.add_argument("--origin", default=str(JEV / "wiki_qa"), help="old tree holding data/images and data/reasoning (fallback)")
    ap.add_argument("--new", nargs="+", default=None, metavar="TAG",
                    help="export the NEW questions of these tags (new_<tag>.jsonl) instead of the legacy-derived ones (a tag is required: "
                         "batches of other writers are never renumbered)")
    ap.add_argument("--v1dir", default=str(v1_io.V1DIR))
    a = ap.parse_args()
    if a.new is not None:
        px = [pathlib.Path(p) for p in (a.px224 or [ROOT / "work" / "generated" / "px224", ROOT / "work" / "px224"])]
        roots = [ROOT / "work", pathlib.Path(a.origin)]
        index = export_new(pathlib.Path(a.out), pathlib.Path(a.v1dir), px, roots, a.passages, a.new, manifests=v1_io.MANIFESTS)
        print("%d new batches, %d questions, %d picture paths" % (len(index), sum(b["n"] for b in index), sum(b["images"] for b in index)))
        for b in index:
            print("  %-26s %3d  %s..%s" % (b["batch"], b["n"], b["first"], b["last"]))
        return 0
    px = [pathlib.Path(p) for p in (a.px224 or [ROOT / "work" / "px224", JEV / "wiki_qa" / "work" / "px224", ROOT / "work" / "generated" / "px224"])]
    index = export(pathlib.Path(a.out), pathlib.Path(a.logs), pathlib.Path(a.passages), px, pathlib.Path(a.origin))
    print("%d batches, %d questions, %d picture paths" % (len(index), sum(b["n"] for b in index), sum(b["images"] for b in index)))
    for b in index:
        print("  %-16s %3d  %s..%s  all_wrong=%d majority_wrong=%d" % (b["batch"], b["n"], b["first"], b["last"], b["all_wrong"],
                                                                     b["majority_wrong"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
