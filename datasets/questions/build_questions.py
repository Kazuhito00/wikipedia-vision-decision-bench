# -*- coding: utf-8 -*-
"""Author-side tool (legacy history): compile the hand-written items (questions/items_*.py) into work/legacy_rebuild/questions.jsonl.

    python datasets/questions/build_questions.py

The frozen legacy set is datasets/questions/legacy/*.jsonl and is NEVER written by this script (the output goes to the ignored work/
directory, so a re-run cannot change legacy). Two things differ from the old wiki_qa/ original: the text items' evidence strings
(Wikipedia text) were emptied before they were copied here, so their evidence check passes trivially unless you restore them
from a local copy; and the candidate lists (work/candidates.json ...) are not part of the repository.

Needs work/candidates.json and work/leads.json (tools/collect_*.py, tools/fetch_leads.py). Checks, per item:
  image : candidate id exists (-> Commons title + sha1 of the original)
  text  : every evidence string occurs in the passage (en and ja), every `absent` string does not, and no wrong
          option of a choice question occurs in the passage (the answer must be the only candidate in it).
Only titles, revision ids, hashes and the questions themselves are written -- no image, no Wikipedia text.
"""
import importlib.util
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from datasets.questions import wikitext  # noqa: E402
import dsl  # noqa: E402

WORK = ROOT / "work"


def main() -> int:
    for p in sorted(HERE.glob("items_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    cands = {}
    for name in ("candidates.json", "harvest_candidates.json", "expansion_candidates.json"):
        if (WORK / name).exists():
            cands.update(json.loads((WORK / name).read_text(encoding="utf-8")))
    leads = json.loads((WORK / "leads.json").read_text(encoding="utf-8")) if (WORK / "leads.json").exists() else {}
    passage_cache: dict = {}
    errors, out = [], []
    counters = Counter()

    def passage(lang, a):
        key = (lang, a["revid"])
        if key not in passage_cache:
            passage_cache[key] = wikitext.lead_text(lang, a["revid"])
        return passage_cache[key]

    dropped = Counter()
    for it in dsl.ITEMS:
        # difficulty policy: "what kind of image is this?" questions (photo / painting / diagram ...) that are easy are
        # not published -- the set is meant to be somewhat demanding.
        if it["modality"] == "image" and "image-type" in it["tags"] and it["difficulty"] == "easy":
            dropped["easy image-type"] += 1
            continue
        mod = it["modality"]
        counters[mod] += 1
        rec = dict(id="%s-%04d" % ("img" if mod == "image" else "txt", counters[mod]), modality=mod, kind=it["kind"],
                   tags=it["tags"], difficulty=it["difficulty"])
        if mod == "image":
            titles, shas = [], []
            langs = ["en", "ja"]
            articles = {"en": [], "ja": []}
            for cid in it["images"]:
                c = cands.get(cid)
                if not c:
                    errors.append("%s: unknown candidate %s" % (rec["id"], cid))
                    continue
                titles.append(c["title"])
                shas.append(c["sha1"])
                for lang in ("en", "ja"):
                    if lang in c and c.get("via") != "expansion":   # Wikipedia membership known (harvest) -> language is only
                        if not c[lang]:                 # offered when the article of that wiki really uses the file
                            langs = [l for l in langs if l != lang]
                        articles[lang] += c[lang][:2]
                    else:
                        rec["source_unverified"] = True
            if not langs:
                continue                                 # file used by neither wiki (should not happen for harvest)
            # Every picture question is published in BOTH languages (the same picture and the same question, translated),
            # so the two languages can be compared on identical items. `used_by` records which Wikipedias show the picture.
            rec["images"], rec["sha1"], rec["langs"] = titles, shas, ["en", "ja"]
            rec["used_by"] = langs
            rec["articles"] = {l: articles[l] for l in langs}
        else:
            langs = it.get("langs", ["en", "ja"])
            lead = leads.get(it["title"])
            if not lead or ("ja" in langs and not lead.get("ja")):
                errors.append("%s: no lead for %r (%s)" % (rec["id"], it["title"], "+".join(langs)))
                continue
            rec["langs"] = langs
            rec["article"] = {l: dict(title=lead[l]["title"], revid=lead[l]["revid"]) for l in langs}
            for lang in langs:
                text = passage(lang, lead[lang])
                for ev in it["evidence"][lang]:
                    if ev not in text:
                        errors.append("%s: evidence %r not in %s passage of %s" % (rec["id"], ev, lang, it["title"]))
                for ab in (it.get("absent") or {}).get(lang, []):
                    if ab in text:
                        errors.append("%s: absent %r IS in %s passage of %s" % (rec["id"], ab, lang, it["title"]))
                if it["kind"] == "choice":
                    for w in it[lang]["wrong"]:
                        if w in text:
                            errors.append("%s: wrong option %r occurs in %s passage of %s" % (rec["id"], w, lang, it["title"]))
            rec["evidence"] = {l: it["evidence"][l] for l in langs}
        for lang in rec.get("langs", it.get("langs", ["en", "ja"])):
            rec[lang] = it[lang]
        if "answer" in it:
            rec["answer"] = it["answer"]
        out.append(rec)

    for e in errors:
        print("ERROR", e)
    if errors:
        print(len(errors), "errors -- work/legacy_rebuild/questions.jsonl not written")
        return 1
    OUT = ROOT / "work" / "legacy_rebuild"
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "questions.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if dropped:
        print("dropped by the difficulty policy:", dict(dropped))
    print("difficulty:", dict(Counter(r["difficulty"] for r in out)))
    kinds = Counter((r["modality"], r["kind"]) for r in out)
    per_lang = {l: sum(1 for r in out if r["modality"] == "text" and l in r.get("langs", [])) for l in ("en", "ja")}
    print("text items per language:", per_lang)
    print("wrote %d items" % len(out), dict(kinds))
    nou = [r["answer"] for r in out if r["kind"] == "noul"]
    if nou:
        print("noul True ratio %.2f (%d)" % (sum(nou) / len(nou), len(nou)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
