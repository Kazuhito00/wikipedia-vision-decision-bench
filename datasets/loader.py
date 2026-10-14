# -*- coding: utf-8 -*-
"""Read the question sets as evaluation cases. Every question is identified by (version, id), never by the id alone.

A result is always keyed by ``(dataset_version, id)``; the only version is "v1" (``photo-0001``, ``biz-0001``, ``rsn-0001``,
``txt-0001``). ``case_key`` builds the key. Pictures and the Wikipedia passages are not part of the repository: ``images_root``
(default: <repo>/work, or $WIKIQA_IMAGES) is the directory that contains the ``data/...`` paths of the rows, and the passages come
from ``passages.json`` (default <repo>/work/passages.json, or $WIKIQA_PASSAGES), which is git-ignored.

Dropped questions: the v1 files keep every question the review dropped (``review.state == "dropped"``); ``load_rows`` /
``load_cases`` / ``load_v1_cases`` skip them by default (``include_dropped=True`` keeps them). The balanced option positions are
assigned over the kept questions only. A rebuilt v1 row (history "rewrite") keeps its id; its picture is ``generated/<id>.png`` under
``images_root`` (work/), 224 px copy in ``work/generated/px224/``.

New questions (one file per writer: ``datasets/questions/v1/new_<tag>.jsonl``, row ``origin == "new"``, id ranges in
``datasets/newq.py``) are read together with the base files and behave like any other v1 row. The balanced positions are
always computed over the WHOLE v1 set (base + every new file, dropped ones removed) and only then restricted to the files / groups asked
for, so a subset never changes an answer position. A text-only row without ``article`` (a "control": the picture removed from an image
question) carries its own authored ``state`` and needs no passage.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib

from . import newq, options

ROOT = pathlib.Path(__file__).resolve().parents[1]
QDIR = ROOT / "datasets" / "questions"
MANIFESTS = ROOT / "datasets" / "manifests"
VERSIONS = ("v1",)
DEFAULT_STATE = {"en": "Look at the attached photograph.", "ja": "添付の写真を見てください。"}
TWO_STATE = {"en": "Two photographs are attached.", "ja": "2 枚の写真が添付されています。"}


def case_key(version: str, qid: str) -> tuple:
    if version not in VERSIONS:
        raise ValueError("unknown dataset version %r" % version)
    return (version, qid)


def read_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def is_dropped(row: dict) -> bool:
    """True for a v1 row the review dropped (review.state == "dropped")."""
    return row.get("review", {}).get("state") == "dropped"


def _read_v1(qdir: pathlib.Path, include_dropped: bool) -> list:
    """[(file name, row)] of every v1 file: the base files (sorted by name), then the new_<tag>.jsonl files (sorted)."""
    base = qdir / "v1"
    if not base.exists():
        raise FileNotFoundError("v1 questions are not written yet (%s)" % base)
    names = sorted(p.name for p in base.glob("*.jsonl") if not newq.tag_of_filename(p.name))
    names += [p.name for p in newq.new_files(base)]
    return [(n, r) for n in names for r in read_jsonl(base / n) if include_dropped or not is_dropped(r)]


def load_rows(version: str, files: tuple | None = None, qdir: pathlib.Path = QDIR, *, include_dropped: bool = False,
              groups: tuple | None = None, include_new: bool = True) -> list[dict]:
    """The raw question records, each with ``version`` added. The dropped questions are left out unless ``include_dropped``.
    By default every file of the directory is read, the new_<tag>.jsonl files included (``include_new=False``: the base files
    only); ``files`` picks files by name, ``groups`` keeps the rows of those groups."""
    if version != "v1":
        raise ValueError("unknown dataset version %r" % version)
    rows = []
    for name, r in _read_v1(qdir, include_dropped):
        if files is not None and name not in files:
            continue
        if not include_new and newq.tag_of_filename(name):
            continue
        if groups is not None and r.get("group") not in groups:
            continue
        rows.append(dict(r, version=version))
    return rows


def _passages(path) -> dict:
    p = pathlib.Path(path or os.environ.get("WIKIQA_PASSAGES") or ROOT / "work" / "passages.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_cases(version: str = "v1", files: tuple | None = None, *, mode: str | None = None, images_root=None,
               passages_path=None, qdir: pathlib.Path = QDIR, include_dropped: bool = False,
               groups: tuple | None = None, include_new: bool = True, only_new: bool = False,
               strict_passages: bool = True) -> list[dict]:
    """Cases in the shape of the old loader: dict(id, images, kind, expected, modality, tags, difficulty, en=dict(state, instr,
    options), ja=...) plus ``version`` and ``key``. Choice options are (text, text) pairs, score options the level strings,
    yes/no questions have options=None. ``include_dropped``: also return the questions the review dropped (default: they are skipped, and not counted when the
    balanced positions are assigned). ``files`` / ``groups`` / ``include_new`` / ``only_new`` choose which questions are
    RETURNED; the balanced positions never depend on that choice (they are computed over the whole v1 set).
    ``strict_passages=False``: a text-only question whose Wikipedia passage is not on this machine gets a placeholder state instead
    of raising (for dry runs / limit checks; never for a measurement)."""
    mode = mode or options.BALANCED
    img_root = pathlib.Path(images_root or os.environ.get("WIKIQA_IMAGES") or ROOT / "work")
    passages = _passages(passages_path)
    if version != "v1":
        raise ValueError("unknown dataset version %r" % version)
    if mode != options.BALANCED:
        raise ValueError("v1 uses the balanced order")
    universe = load_rows("v1", None, qdir, include_dropped=include_dropped)
    orders = options.v1_orders(universe)
    rows = [r for r in load_rows("v1", files, qdir, include_dropped=include_dropped, groups=groups, include_new=include_new)
            if not only_new or r.get("origin") == newq.ORIGIN]
    cases = []
    for r in rows:
        case = dict(id=r["id"], version=version, key=case_key(version, r["id"]), kind=r["kind"], modality=r["modality"],
                    tags=r.get("tags", []), difficulty=r.get("difficulty"),
                    images=[str(img_root / p) for p in r.get("local_images", [])])
        order = None
        if r["kind"] == "choice":
            langs = r.get("langs") or ["en", "ja"]
            n = 1 + len(r[langs[0]]["wrong"])
            order = orders[r["id"]]
            case["expected"] = options.expected_of(order)
        for lang in (r.get("langs") or ["en", "ja"]):
            q = r[lang]
            if r["modality"] == "text" and "article" in r:
                a = r["article"][lang]
                try:
                    state = passages["%s:%s" % (lang, a["revid"])]["text"]
                except KeyError:
                    if strict_passages:
                        raise FileNotFoundError("Wikipedia passage %s:%s not found (passages.json is local data, not in the repository)"
                                                % (lang, a["revid"])) from None
                    state = "[passage %s:%s is not on this machine]" % (lang, a["revid"])
            elif r["modality"] == "text":                    # a control: no article, the question carries its own authored state
                state = q["state"]
            else:
                state = q.get("state") or (TWO_STATE if len(case["images"]) > 1 else DEFAULT_STATE)[lang]
            if r["kind"] == "choice":
                items_ = [q["correct"]] + list(q["wrong"])
                opts = [(items_[i], items_[i]) for i in order]
            elif r["kind"] == "score":
                opts = list(q["levels"])
            else:
                opts = None
            case[lang] = dict(state=state, instr=q["instr"], options=opts)
        if r["kind"] == "noul":
            case["expected"] = bool(r["answer"])
        elif r["kind"] == "score":
            case["expected"] = int(r["answer"])
        cases.append(case)
    return cases


V1_GROUPS = ("photo", "biz", "rsn", "txt")


def load_v1_cases(groups: tuple | list | None = None, *, include_dropped: bool = False, mode: str | None = None, images_root=None,
                  passages_path=None, qdir: pathlib.Path = QDIR, include_new: bool = True,
                  only_new: bool = False, strict_passages: bool = True) -> list[dict]:
    """The v1 cases of the given groups (default: all of photo, biz, rsn, txt), dropped questions skipped, new questions
    (new_<tag>.jsonl) included unless ``include_new=False`` (``only_new=True``: only those). Entry point for the runner:
    ``load_v1_cases(["photo"])`` -> cases with ``version="v1"`` and ``key=("v1", id)``. Text-only questions need passages.json
    (except controls, which carry their own state)."""
    groups = tuple(groups or V1_GROUPS)
    bad = [g for g in groups if g not in V1_GROUPS]
    if bad:
        raise ValueError("unknown v1 group(s) %s (use %s)" % (bad, "/".join(V1_GROUPS)))
    return load_cases("v1", mode=mode, images_root=images_root, passages_path=passages_path, qdir=qdir, include_dropped=include_dropped,
                      groups=groups, include_new=include_new, only_new=only_new, strict_passages=strict_passages)


# ------------------------------------------------------------------------------------------------------ manifests
def _read_csv(path: pathlib.Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def classification(manifests: pathlib.Path = MANIFESTS) -> dict:
    """{("v1", id): row} of datasets/manifests/questions_v1.csv (source, image_type, skill, answer, ...) and the tables of the new
    questions (questions_v1_new_<tag>.csv), if any."""
    rows = _read_csv(manifests / "questions_v1.csv")
    for p in sorted(pathlib.Path(manifests).glob("questions_v1_new_*.csv")):
        rows += _read_csv(p)
    return {case_key("v1", r["id"]): r for r in rows}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
