# -*- coding: utf-8 -*-
"""Validate the new v1 questions (datasets/questions/v1/new_<tag>.jsonl) and, if asked, write their manifests.

    python datasets/tools/validate_new.py [--tag TAG ...] [--v1dir DIR] [--images-root DIR ...] [--no-image-check] [--write-manifests --tag TAG]

Exit code 0 = no error (warnings may remain), 1 = errors (each printed as ``<file>:<line> <id>: <problem>``). Run it on your own file
before handing it over; it is also what the tests run over a temporary directory.

What is checked, per row (E = error, W = warning):
  schema     E: required keys (id, origin "new", derived_from (id or null), group, source, image_type, skill, difficulty,
                lang, langs, modality, kind, answer_format, review, local_images, tags); values inside taxonomy.py's lists; answer_format
                equals the one computed from the options; unknown keys W.
  id         E: <group>-NNNN with the prefix equal to ``group``; inside the id ranges reserved for the file's tag (datasets/newq.py RANGES);
                unique across ALL v1 files (base and new); the tag itself must be registered in newq.RANGES.
  options    E: choice: correct not among the wrong ones, no duplicate / empty option (case and spacing ignored), 2..16 options (QEV's
                limit), the same number in en and ja, "none of the above" style options special in en <=> special in ja (they are pinned to the
                end of the list at run time); yes/no: ``answer`` is true/false and no options; score: 2..10 levels (OneJev / Strands limit),
                distinct, the same number in en and ja, ``answer`` = level index in range. W: option wording that depends on the order
                ("all of the above", 「上記のすべて」), a ja option that looks like "none of the above" but is not recognised as one.
  language   E: lang both / en / ja agrees with langs and with which of en / ja are present; a ja side (lang both or ja) contains Japanese
                characters in its question; tag ja_specific needs lang "ja". W: Japanese characters in an English-only row.
  duplicates E: a new row repeating an earlier row (same picture, wording, right answer and answer_format; other wrong options do not make
                it different) is a duplicate. A variant must change the option count / kind, the wording (negation), the picture (mirror) or
                the right answer.
  pictures   E: an image row has exactly ONE picture, a text row none. The picture is either ``generated/<own id>.<png|jpg|jpeg|webp>``
                (a NEW file, found under one of the image roots: work/generated/ by default) or, for a variant of an existing question
                (``derived_from``), the very same path as that question's picture. File names are unique across all v1 pictures (a flipped
                or edited picture is a new file named after its own id). The file opens as an image (Pillow). A reused picture that is not on
                this machine is a W. source commons-*: ``images`` = ["File:..."] (one per picture); source commons-new: ``credit`` =
                {license CC0 / public domain, author, url on commons.wikimedia.org}.
  text only  E: NO Wikipedia text anywhere: a text-only row either has ``article`` ({lang: {title, revid}}, optional evidence_sha256, and no
                ``state``: the passage is read from the local passages.json at run time) or, as a control (the picture removed from an image
                question), has no ``article``, an authored ``state`` of at most 600 characters per language and ``derived_from`` = an image
                question. Keys evidence / passage / text / body are refused; no string longer than 600 characters anywhere.
Per file (W): the right level of score questions spread over 0..n-1 (difference of at most 1 per n); yes/no answers about half true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import newq, options, taxonomy  # noqa: E402
from datasets.tools import v1_io  # noqa: E402

MAX_CHOICE, MIN_CHOICE = 16, 2          # QEV: 2..16 options (adapters/qev.py LIMITS); the other models take more
MAX_SCORE, MIN_SCORE = 10, 2            # OneJev / Strands: at most 10 levels (QEV 16)
MAX_STATE, MAX_STRING = 600, 600
REQUIRED = ("id", "origin", "derived_from", "group", "source", "image_type", "skill", "difficulty", "lang", "langs", "modality",
            "kind", "answer_format", "review", "local_images", "tags")
OPTIONAL = {"images", "sha1", "credit", "relation", "article", "evidence_sha256", "answer", "en", "ja", "note", "used_by", "articles"}
RELATIONS = ("variant", "mirror", "control", "rewrite", "extension")
FORBIDDEN_KEYS = ("evidence", "passage", "passages", "text", "body", "article_text", "extract")
JA_CHAR = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ]")
NEAR_NONE_JA = re.compile(r"上記|いずれ|どれも|この中|以外|該当")
ORDER_DEP_EN = re.compile(r"\b(all of the above|both of the above|any of the above|the (previous|preceding|first|last) (option|answer))\b", re.I)
ORDER_DEP_JA = re.compile(r"上記のすべて|上のすべて|すべて正しい|前の選択肢|上の選択肢")
PIC_EXT = ("png", "jpg", "jpeg", "webp")
FREE_LICENSES = ("cc0", "public domain", "pd")
REVIEW_STATES = v1_io.REVIEW_STATES


def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()


def default_image_roots() -> list:
    roots = [os.environ.get("WIKIQA_IMAGES"), ROOT / "work", os.environ.get("WIKIQA_DATA_ROOT")]
    return [pathlib.Path(r) for r in roots if r]


class Report:
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []
        self.counts: dict = {}                 # tag -> rows
        self.bad_tags: set = set()             # tags with at least one error

    def err(self, where, msg, tag=None):
        self.errors.append("%s: %s" % (where, msg))
        if tag:
            self.bad_tags.add(tag)

    def warn(self, where, msg):
        self.warnings.append("%s: %s" % (where, msg))

    @property
    def ok(self) -> bool:
        return not self.errors


def _leaf_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _leaf_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _leaf_strings(v)


def _find_picture(path: str, roots: list):
    for r in roots:
        if (pathlib.Path(r) / path).is_file():
            return pathlib.Path(r) / path
    return None


def _check_picture_file(f: pathlib.Path, where, rep: Report, tag):
    try:
        from PIL import Image
    except ImportError:
        if f.stat().st_size == 0:
            rep.err(where, "picture %s is empty" % f.name, tag)
        return
    try:
        with Image.open(f) as im:
            im.verify()
        with Image.open(f) as im:
            w, h = im.size
    except Exception as e:  # noqa: BLE001
        rep.err(where, "picture %s cannot be opened as an image (%s)" % (f.name, str(e)[:60]), tag)
        return
    if min(w, h) < 64:
        rep.warn(where, "picture %s is only %dx%d px" % (f.name, w, h))


def check_options(row: dict, lang: str, where: str, rep: Report, tag):
    """Choice / score contents of one language side. Returns the number of options (or None when unusable)."""
    q = row[lang]
    bad = lambda m: rep.err(where, "%s: %s" % (lang, m), tag)
    if not isinstance(q, dict):
        bad("must be an object")
        return None
    if not isinstance(q.get("instr"), str) or not q["instr"].strip():
        bad("instr must be a non-empty string")
    kind = row["kind"]
    if kind == "choice":
        c, w = q.get("correct"), q.get("wrong")
        if not isinstance(c, str) or not isinstance(w, list) or not all(isinstance(x, str) for x in w):
            bad("choice needs correct (string) and wrong (list of strings)")
            return None
        opts = [c] + w
        if any(not o.strip() for o in opts):
            bad("empty option")
        if len({_norm(o) for o in opts}) != len(opts):
            bad("duplicate options (the right answer must not appear among the wrong ones)")
        if not MIN_CHOICE <= len(opts) <= MAX_CHOICE:
            bad("%d options: a choice question needs %d..%d (QEV's limit is %d)" % (len(opts), MIN_CHOICE, MAX_CHOICE, MAX_CHOICE))
        for o in opts:
            if lang == "en" and ORDER_DEP_EN.search(o) or lang == "ja" and ORDER_DEP_JA.search(o):
                rep.warn(where, "%s: option %r depends on the order of the options (v1 shuffles them)" % (lang, o))
            if lang == "ja" and NEAR_NONE_JA.search(o) and not options.is_special(o):
                rep.warn(where, "ja: option %r looks like a 'none of the above' option but is not recognised as one (see NOTES.md "
                                "for the canonical wording: 該当なし / どれも当てはまらない / 判断できない ...)" % o)
        return len(opts)
    if kind == "score":
        lv = q.get("levels")
        if not isinstance(lv, list) or not all(isinstance(x, str) for x in lv):
            bad("score needs levels (list of strings)")
            return None
        if not MIN_SCORE <= len(lv) <= MAX_SCORE:
            bad("%d levels: a score question needs %d..%d (OneJev / Strands accept at most %d)" % (len(lv), MIN_SCORE, MAX_SCORE, MAX_SCORE))
        if any(not x.strip() for x in lv) or len({_norm(x) for x in lv}) != len(lv):
            bad("levels must be distinct and non-empty")
        return len(lv)
    if kind == "noul":
        extra = set(q) - {"instr", "state"}
        if extra:
            bad("a yes/no question has only instr (and state): unexpected %s" % sorted(extra))
        return 2
    return None


def validate_row(row: dict, tag: str, where: str, ctx: dict, rep: Report) -> None:
    err = lambda m: rep.err(where, m, tag)
    if not isinstance(row, dict):
        err("not an object")
        return
    missing = [k for k in REQUIRED if k not in row]
    if missing:
        err("missing keys %s" % missing)
        return
    unknown = set(row) - set(REQUIRED) - OPTIONAL
    if unknown:
        rep.warn(where, "unknown keys %s (ignored by the loader)" % sorted(unknown))
    for k in FORBIDDEN_KEYS:
        if k in row or any(isinstance(row.get(l), dict) and k in row[l] for l in ("en", "ja")):
            err("key %r is not allowed: Wikipedia text must not be stored (use article {title, revid} and the local passages.json)" % k)
    for sval in _leaf_strings({k: v for k, v in row.items() if k != "review"}):
        if len(sval) > MAX_STRING:
            err("a string of %d characters (limit %d): a copied passage? Wikipedia text must not be stored" % (len(sval), MAX_STRING))
            break
    qid, group = row["id"], row["group"]
    # ---- id
    p = newq.parse_id(qid)
    if p is None:
        err("id %r is not <group>-NNNN" % (qid,))
    else:
        if group not in newq.GROUPS:
            err("group %r is not one of %s" % (group, "/".join(newq.GROUPS)))
        elif p[0] != group:
            err("id prefix %r does not match group %r" % (p[0], group))
        if tag in newq.RANGES:
            if not newq.in_reserved_range(tag, qid):
                rg = ", ".join("%s-%04d..%04d" % (g, lo, hi) for g, (lo, hi) in newq.RANGES[tag].items())
                err("id %s is outside the range reserved for tag %s (%s)" % (qid, tag, rg))
    if row["origin"] != newq.ORIGIN:
        err('origin must be "%s"' % newq.ORIGIN)
    df = row["derived_from"]
    parent = None
    if df is not None:
        if not isinstance(df, str):
            err("derived_from must be a v1 id or null")
        elif df == qid:
            err("derived_from points at the row itself")
        else:
            parent = ctx["all_rows"].get(df)
            if parent is None:
                err("derived_from %s is not a known v1 id" % df)
    if row.get("relation") is not None and row["relation"] not in RELATIONS:
        err("relation must be one of %s" % "/".join(RELATIONS))
    # ---- classification
    if row["difficulty"] not in taxonomy.V1_DIFFICULTIES:
        err("difficulty must be one of %s" % "/".join(taxonomy.V1_DIFFICULTIES))
    if row["source"] not in taxonomy.V1_SOURCES:
        err("source %r not in %s" % (row["source"], sorted(taxonomy.V1_SOURCES)))
    if group == "txt":
        if row["modality"] != "text":
            err('a txt row must have modality "text"')
        if row["image_type"] != taxonomy.V1_TEXT_IMAGE_TYPE or row["source"] != "none":
            err('a txt row has image_type "none" and source "none"')
        if row["skill"] != taxonomy.V1_TEXT_SKILL:
            err('a txt row has skill "%s" (the link to the original skill is derived_from)' % taxonomy.V1_TEXT_SKILL)
    else:
        if row["modality"] != "image":
            err('a %s row must have modality "image"' % group)
        if row["image_type"] not in taxonomy.V1_IMAGE_TYPES:
            err("image_type %r not allowed (allowed: %s; ask the coordinator to extend taxonomy.py rather than inventing a value)"
                % (row["image_type"], ", ".join(sorted(taxonomy.V1_IMAGE_TYPES))))
        if row["skill"] not in taxonomy.V1_SKILLS:
            err("skill %r not allowed (allowed: %s)" % (row["skill"], ", ".join(sorted(taxonomy.V1_SKILLS))))
        if row["source"] == "none":
            err('source "none" is only for txt rows')
    if not (isinstance(row["tags"], list) and all(isinstance(t, str) for t in row["tags"])):
        err("tags must be a list of strings")
    # ---- language
    lang, langs = row["lang"], row["langs"]
    want = {"both": ["en", "ja"], "en": ["en"], "ja": ["ja"]}.get(lang)
    if want is None:
        err('lang must be "both", "en" or "ja"')
        return
    if langs != want:
        err("langs %r does not match lang %r (expected %r)" % (langs, lang, want))
    present = [l for l in ("en", "ja") if l in row]
    if present != want:
        err("lang %s needs exactly the side(s) %s, found %s" % (lang, want, present))
        return
    if tag == "ja_specific" and lang != "ja":
        err('tag ja_specific is for lang "ja" questions')
    # ---- kind / options
    kind = row["kind"]
    if kind not in ("choice", "noul", "score"):
        err("kind must be choice / noul / score")
        return
    ns = {l: check_options(row, l, where, rep, tag) for l in want}
    if len(set(ns.values())) > 1:
        err("en and ja differ in the number of %s (%s)" % ("options" if kind == "choice" else "levels", ns))
    if kind == "noul":
        if not isinstance(row.get("answer"), bool):
            err("a yes/no question needs answer true / false (a boolean)")
    elif kind == "score":
        n = next((v for v in ns.values() if v), None)
        a = row.get("answer")
        if isinstance(a, bool) or not isinstance(a, int) or (n and not 0 <= a < n):
            err("score answer must be the level index (integer in 0..%s)" % ((n - 1) if n else "n-1"))
    elif "answer" in row:
        err("a choice question has no top-level answer (the right option is ``correct``)")
    if kind == "choice" and len(want) == 2 and all(isinstance(row[l], dict) and isinstance(row[l].get("wrong"), list) for l in want):
        sp = {l: [options.is_special(o) for o in [row[l].get("correct", "")] + row[l]["wrong"]] for l in want}
        if len(sp["en"]) == len(sp["ja"]) and sp["en"] != sp["ja"]:
            err('a "none of the above" style option must be special in both languages (use the canonical wording of NOTES.md); '
                "special flags en %s / ja %s" % (sp["en"], sp["ja"]))
    try:
        fmt = v1_io.answer_format(row)[0]
        if row["answer_format"] != fmt:
            err("answer_format %r does not match the options (%s)" % (row["answer_format"], fmt))
    except (KeyError, TypeError, ValueError):
        pass
    # ---- Japanese
    if "ja" in want and isinstance(row.get("ja"), dict) and not JA_CHAR.search(str(row["ja"].get("instr", ""))):
        err("the ja question contains no Japanese characters")
    if lang == "en" and JA_CHAR.search(str(row["en"].get("instr", ""))):
        rep.warn(where, "an English-only row whose question contains Japanese characters")
    # ---- review block
    rv = row["review"]
    if not (isinstance(rv, dict) and rv.get("state") in REVIEW_STATES and isinstance(rv.get("history"), list)
            and all(isinstance(h, dict) and {"date", "what", "why"} <= set(h) for h in rv["history"])):
        err('review must be {"state": %s, "history": [{date, what, why}]}' % "|".join(REVIEW_STATES))
    # ---- pictures / text
    li = row["local_images"]
    if not (isinstance(li, list) and all(isinstance(x, str) for x in li)):
        err("local_images must be a list of strings")
        return
    if row["modality"] == "image":
        check_picture(row, li, parent, where, ctx, rep, tag)
    else:
        if li:
            err("a text-only row has no picture")
        check_text_row(row, want, parent, where, rep, tag)
    if str(row["source"]).startswith("commons"):
        im = row.get("images")
        if not (isinstance(im, list) and len(im) == len(li) and all(isinstance(x, str) and x.startswith("File:") for x in im)):
            err('source %s needs images = ["File:..."] (one per picture)' % row["source"])
    if row["source"] == "commons-new":
        c = row.get("credit")
        if not (isinstance(c, dict) and all(isinstance(c.get(k), str) and c[k].strip() for k in ("license", "author", "url"))):
            err("source commons-new needs credit = {license, author, url}")
        else:
            if not any(f in c["license"].lower() for f in FREE_LICENSES):
                err("credit.license %r: only CC0 / public domain pictures are used" % c["license"])
            if not c["url"].startswith("https://commons.wikimedia.org/"):
                err("credit.url must be a https://commons.wikimedia.org/ page")


def check_picture(row, li, parent, where, ctx, rep: Report, tag):
    err = lambda m: rep.err(where, m, tag)
    if len(li) != 1:
        err("an image row has exactly one picture (1 question = 1 picture), found %d" % len(li))
        return
    path, qid = li[0], row["id"]
    if path.startswith(("/", "\\")) or ".." in pathlib.PurePosixPath(path).parts or "\\" in path or re.match(r"^[A-Za-z]:", path):
        err("picture path %r must be relative with forward slashes" % path)
        return
    own = re.match(r"^generated/%s\.(%s)$" % (re.escape(qid), "|".join(PIC_EXT)), path)
    reuse = parent is not None and parent.get("local_images") == [path]
    if not own and not reuse:
        msg = "picture %r: use generated/%s.<%s> (a new file named after this id)" % (path, qid, "|".join(PIC_EXT))
        if parent is not None:
            msg += ", or the very same path as derived_from %s (%s)" % (row["derived_from"], (parent.get("local_images") or ["no picture"])[0])
        err(msg)
        return
    others = ctx["basenames"].get(pathlib.PurePosixPath(path).name, set())
    if own and others - {qid}:
        err("picture file name %s is also used by %s: names must be unique across v1" % (pathlib.PurePosixPath(path).name, sorted(others - {qid})))
    f = _find_picture(path, ctx["roots"])
    if f is None:
        if not ctx["check_images"]:
            return
        if own:
            err("picture %s not found under %s" % (path, ", ".join(str(r) for r in ctx["roots"])))
        else:
            rep.warn(where, "picture %s (shared with %s) is not on this machine" % (path, row["derived_from"]))
        return
    if own:
        _check_picture_file(f, where, rep, tag)


def check_text_row(row, langs, parent, where, rep: Report, tag):
    err = lambda m: rep.err(where, m, tag)
    art = row.get("article")
    if art is not None:
        ok = isinstance(art, dict) and all(isinstance(art.get(l), dict) and isinstance(art[l].get("title"), str) and art[l]["title"].strip()
                                           and isinstance(art[l].get("revid"), int) and not isinstance(art[l]["revid"], bool)
                                           and art[l]["revid"] > 0 for l in langs)
        if not ok:
            err("article must be {%s: {title, revid (integer)}}: a reference to the article revision, never its text" % "|".join(langs))
        for l in langs:
            if isinstance(row.get(l), dict) and "state" in row[l]:
                err("%s: a passage-based row has no state (the passage is read from the local passages.json)" % l)
        return
    # a control: authored state, derived from an image question
    if parent is None:
        err("a text-only row without article is a control and needs derived_from = the image question it controls")
    elif parent.get("modality") != "image":
        err("derived_from %s is not an image question" % row["derived_from"])
    for l in langs:
        st = row[l].get("state") if isinstance(row.get(l), dict) else None
        if not isinstance(st, str) or not st.strip():
            err("%s: a control needs an authored state (say that no picture is attached and give what the question needs)" % l)
        elif len(st) > MAX_STATE:
            err("%s: state is %d characters (limit %d): authored text only, never Wikipedia text" % (l, len(st), MAX_STATE))


def file_stats(rows: list, where: str, rep: Report) -> None:
    """Warnings about the spread of the right answers inside one file."""
    yn = [r for r in rows if r.get("kind") == "noul" and isinstance(r.get("answer"), bool)]
    if len(yn) >= 20 and not 0.35 <= sum(r["answer"] for r in yn) / len(yn) <= 0.65:
        rep.warn(where, "yes/no answers are %d true / %d false: aim for about half each" % (sum(r["answer"] for r in yn), sum(not r["answer"] for r in yn)))
    by = {}
    for r in rows:
        if r.get("kind") == "score" and isinstance(r.get("answer"), int) and isinstance(r.get("en", r.get("ja")), dict):
            n = len((r.get("en") or r.get("ja")).get("levels", []))
            if n:
                by.setdefault(n, [0] * n)
                if 0 <= r["answer"] < n:
                    by[n][r["answer"]] += 1
    for n, c in sorted(by.items()):
        if sum(c) >= n and max(c) - min(c) > 1:
            rep.warn(where, "score:%d right levels are %s: spread them evenly (options.suggest_score_answers gives a spread)" % (n, c))


def dup_key(row: dict, picture: str) -> tuple | None:
    """What makes two questions the same question: kind, answer_format, modality, the picture, and per language the question wording (and
    the state), plus the right answer (choice: the correct option; yes/no and score: the answer). The WRONG options are deliberately not
    part of it: the same question with another set of distractors is a duplicate.
    A variant is therefore a different question when it changes the option count / the kind (answer_format), the wording (negation), the
    picture (mirror) or the right answer."""
    try:
        parts = [row["kind"], row["answer_format"], row["modality"], picture]
        for l in (row.get("langs") or [l for l in ("en", "ja") if l in row]):
            q = row[l]
            parts += [_norm(q.get("instr", "")), _norm(q.get("state", ""))]
            if row["kind"] == "choice":
                parts.append(_norm(q["correct"]))
        if row["kind"] != "choice":
            parts.append(repr(row.get("answer")))
        return tuple(parts)
    except (KeyError, TypeError, AttributeError):
        return None


def check_duplicates(base_rows: list, parsed: dict, files: dict, roots: list, tags, rep: Report) -> None:
    """A new row that repeats an earlier row (base, or a new row with a smaller id) is an error. Own pictures are compared by content
    (sha256), shared paths by path. This is the duplicate rule for new rows."""
    seen: dict = {}
    for r in base_rows:
        k = dup_key(r, (r.get("local_images") or [""])[0])
        if k:
            seen.setdefault(k, r["id"])
    todo = sorted(((r.get("id", ""), tag, n, r) for tag, items in parsed.items() for n, r in items if isinstance(r, dict)),
                  key=lambda x: x[0])
    for rid, tag, n, r in todo:
        pic = (r.get("local_images") or [""])[0] if isinstance(r.get("local_images"), list) else ""
        f = _find_picture(pic, roots) if isinstance(pic, str) and pic.startswith("generated/") else None
        k = dup_key(r, hashlib.sha256(f.read_bytes()).hexdigest() if f else pic)
        if not k:
            continue
        if k in seen and seen[k] != rid:
            if not tags or tag in tags:
                rep.err("%s:%d %s" % (files[tag].name, n, rid),
                        "duplicate of %s (same picture, question wording, answer and answer_format; a variant must change the option count "
                        "or kind, the wording (negation), the picture (a new file) or the right answer)" % seen[k], tag)
        else:
            seen[k] = rid


def validate(v1dir: pathlib.Path = v1_io.V1DIR, tags=None, image_roots=None, check_images: bool = True) -> Report:
    """Validate every new_<tag>.jsonl of ``v1dir`` (or only ``tags``). ``image_roots``: where pictures are looked for."""
    rep = Report()
    v1dir = pathlib.Path(v1dir)
    for m in newq.check_table():
        rep.err("datasets/newq.py", m)
    base = v1_io.load_v1(v1dir)
    base_rows = v1_io.all_rows(base)
    files = {newq.tag_of_filename(p.name): p for p in newq.new_files(v1dir)}
    parsed: dict = {}                                     # tag -> [(line, row)]
    for tag, path in files.items():
        parsed[tag] = []
        for n, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not ln.strip():
                continue
            try:
                parsed[tag].append((n, json.loads(ln)))
            except ValueError as e:
                rep.err("%s:%d" % (path.name, n), "not JSON (%s)" % e, tag)
    # context over ALL v1 rows (a parent may be in another file; ids and picture names are unique across everything)
    all_rows = {r["id"]: r for r in base_rows}
    owner = {r["id"]: "base" for r in base_rows}
    for tag, items in parsed.items():
        for n, r in items:
            rid = r.get("id") if isinstance(r, dict) else None
            if rid in owner:
                rep.err("%s:%d %s" % (files[tag].name, n, rid), "duplicate id (already in %s)" % owner[rid], tag)
            elif isinstance(rid, str):
                owner[rid] = "%s:%d" % (files[tag].name, n)
                all_rows[rid] = r
    basenames: dict = {}
    for rid, r in all_rows.items():
        for pth in (r.get("local_images") or []) if isinstance(r, dict) else []:
            if isinstance(pth, str):
                basenames.setdefault(pathlib.PurePosixPath(pth).name, set()).add(rid)
    ctx = dict(all_rows=all_rows, basenames=basenames, roots=[pathlib.Path(r) for r in (image_roots or default_image_roots())],
               check_images=check_images)
    for tag, items in sorted(parsed.items()):
        if tags and tag not in tags:
            continue
        rep.counts[tag] = len(items)
        if tag not in newq.RANGES:
            rep.err(files[tag].name, "tag %r is not registered in datasets/newq.py RANGES (add its id ranges there first)" % tag, tag)
            continue
        for n, row in items:
            validate_row(row, tag, "%s:%d %s" % (files[tag].name, n, row.get("id") if isinstance(row, dict) else "?"), ctx, rep)
        file_stats([r for _, r in items if isinstance(r, dict)], files[tag].name, rep)
    check_duplicates(base_rows, parsed, files, ctx["roots"], tags, rep)
    for t in tags or ():
        if t not in files:
            rep.err("--tag %s" % t, "no new_%s.jsonl in %s" % (t, v1dir))
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--v1dir", default=str(v1_io.V1DIR))
    ap.add_argument("--tag", action="append", default=None, help="only this tag (repeatable)")
    ap.add_argument("--images-root", action="append", default=None, help="directory that contains generated/ (repeatable; default work/)")
    ap.add_argument("--no-image-check", action="store_true", help="do not require the picture files to exist")
    ap.add_argument("--write-manifests", action="store_true",
                    help="with --tag: write manifests/questions_v1_new_<tag>.csv for that tag if it has no error")
    ap.add_argument("--manifests", default=str(v1_io.MANIFESTS))
    a = ap.parse_args(argv)
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    rep = validate(pathlib.Path(a.v1dir), a.tag, a.images_root, not a.no_image_check)
    for w in rep.warnings:
        print("warning: " + w)
    for e in rep.errors:
        print("ERROR: " + e)
    print("%s: %d rows in %d new file(s) (%s); %d error(s), %d warning(s)" % (
        "OK" if rep.ok else "FAILED", sum(rep.counts.values()), len(rep.counts),
        ", ".join("%s %d" % kv for kv in sorted(rep.counts.items())) or "none", len(rep.errors), len(rep.warnings)))
    if a.write_manifests and not a.tag:
        print("ERROR: --write-manifests needs --tag <your tag> (it writes only that tag's manifests, never another writer's)")
        return 2
    if a.write_manifests:
        by_tag = {t: rows for t, rows in v1_io.load_new(pathlib.Path(a.v1dir)).items() if t in rep.counts and t not in rep.bad_tags}
        done = v1_io.write_new_manifests(by_tag, pathlib.Path(a.manifests))
        print("manifests written: %s" % (", ".join(p.name for p in done) or "none"))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
