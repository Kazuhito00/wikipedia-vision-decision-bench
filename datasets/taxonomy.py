# -*- coding: utf-8 -*-
"""Deterministic mapping from the legacy records (ids, old tags) to the new classification axes and the four new groups.

Why: the legacy groups (wikipedia / expansion / synthetic / reasoning) describe when a question was made, not what it asks. This
module derives, from the legacy id prefix, the legacy tags and the record fields only, the new axes
    group (photo / biz / rsn / txt), source, image_type, skill, answer (kind + n), difficulty, lang
and the old group (to tally the old report). The rules are the tables below; datasets/NOTES.md prints the same tables.
Nothing is looked at by eye: image_type and skill are coarse, tag-derived labels (see the "default" rows).
"""
from __future__ import annotations

OLD_GROUPS = ("wikipedia", "expansion", "synthetic", "reasoning")
NEW_GROUPS = ("photo", "biz", "rsn", "txt")


def old_group(r: dict) -> str:
    """The set of the old report (eval_common/wiki_report.py); text-only questions have none here: 'text'."""
    pre = r["id"].split("-")[0]
    if pre == "txt":
        return "text"
    if pre == "syn":
        return "synthetic"
    if pre == "rsn":
        return "reasoning"
    return "expansion" if r.get("source_unverified") else "wikipedia"


def new_group(r: dict) -> str:
    og = old_group(r)
    if og in ("wikipedia", "expansion"):
        return "photo"
    if og == "text":
        return "txt"
    if og == "reasoning" or "reasoning" in r["tags"]:   # 225 + the 94 plain visual-reasoning questions of the synthetic set
        return "rsn"
    return "biz"


def source(r: dict) -> str:
    return {"wikipedia": "commons-article", "expansion": "commons-category", "synthetic": "rendered", "reasoning": "rendered",
            "text": "none"}[old_group(r)]


# image_type: first matching rule wins (tag set, value).
PHOTO_IMAGE_TYPE = [
    ({"map", "diagram"}, "diagram-map"),
    ({"sign", "safety"}, "sign"),
    ({"book", "poster", "script", "record", "code", "language"}, "document"),
    ({"animal"}, "photo-animal"), ({"plant"}, "photo-plant"), ({"vehicle"}, "photo-vehicle"), ({"food"}, "photo-food"),
    ({"structure"}, "photo-structure"), ({"art"}, "art"), ({"sport", "action"}, "photo-person"),
    ({"space", "scene", "geo", "life", "sci"}, "photo-scene"),
    ({"image-type"}, "mixed"),
    ({"object"}, "photo-object"),
    ({"ocr"}, "text-in-image"),
]
PHOTO_IMAGE_TYPE_DEFAULT = "photo-other"
RENDERED_IMAGE_TYPE = [
    ({"chart", "bar", "pie", "line", "trend", "gauge"}, "chart"),
    ({"dashboard", "ui", "button", "toggle", "error", "form"}, "ui"),
    ({"document", "table", "receipt", "timetable", "lookup", "calendar", "stamp", "checklist"}, "document"),
    ({"map", "exit", "grid", "path"}, "diagram-map"),
    ({"sign", "safety", "ppe", "triage"}, "sign"),
]
RENDERED_IMAGE_TYPE_DEFAULT = "figure"      # shapes, arrows, dials, gears, rotations ... drawn for the question
# Values added for v1 after the review (the reviewers wrote needs_new_image_type: astronomical 33 + astronomy 4, satellite 23 + aerial 1).
# The legacy rules above never produce them (legacy tags cannot tell); they are set by hand on v1 rows. Existing values are unchanged.
V1_EXTRA_IMAGE_TYPES = ("astronomical", "satellite")


def image_type(r: dict) -> str:
    if r["modality"] == "text":
        return "none"
    tags = set(r["tags"])
    table, default = (PHOTO_IMAGE_TYPE, PHOTO_IMAGE_TYPE_DEFAULT) if source(r).startswith("commons") else \
        (RENDERED_IMAGE_TYPE, RENDERED_IMAGE_TYPE_DEFAULT)
    for keys, val in table:
        if tags & keys:
            return val
    return default


# skill: first matching rule wins (tag set, value).
SKILL = [
    ({"r-negation"}, "negation"), ({"r-consistency"}, "contradiction"), ({"r-uncertainty"}, "uncertainty"),
    ({"r-rules", "r-physics", "r-time", "threshold", "validation", "triage", "ppe"}, "rules"),
    ({"r-compare"}, "compare"), ({"r-count", "count"}, "count"),
    ({"r-space", "position", "arrow", "exit"}, "spatial"),
    ({"r-quantity", "r-instrument", "r-two-images", "gauge", "level"}, "quantity"),
    ({"max", "size", "order", "odd-one-out", "compare", "trend"}, "compare"),
    ({"ocr", "language", "script", "code", "read", "receipt", "calendar"}, "ocr"),
]
SKILL_DEFAULT = "recognition"   # classify / object / scene / colour / attribute / presence / detail / state ...
SKILL_TEXT = "text-comprehension"


def skill(r: dict) -> str:
    if r["modality"] == "text":
        return SKILL_TEXT
    tags = set(r["tags"])
    for keys, val in SKILL:
        if tags & keys:
            return val
    return SKILL_DEFAULT


def answer(r: dict) -> tuple:
    """(kind, n): choice -> n options; yesno -> None; score -> n levels."""
    lang0 = (r.get("langs") or ["en"])[0]
    if r["kind"] == "choice":
        return "choice", 1 + len(r[lang0]["wrong"])
    if r["kind"] == "score":
        return "score", len(r[lang0]["levels"])
    return "yesno", None


def lang(r: dict) -> str:
    ls = set(r.get("langs") or ["en", "ja"])
    return "both" if ls == {"en", "ja"} else sorted(ls)[0]


def classify(r: dict) -> dict:
    kind, n = answer(r)
    return dict(id=r["id"], old_group=old_group(r), group=new_group(r), source=source(r), image_type=image_type(r),
                skill=skill(r), answer="%s:%d" % (kind, n) if n else kind, answer_kind=kind, answer_n=n if n else "",
                difficulty=r["difficulty"], lang=lang(r), n_images=len(r.get("images", [])), tags_legacy="|".join(r["tags"]))


# ---- the allowed values of a v1 row (one list for apply_review.py and validate_new.py) --------------------------------------
V1_DIFFICULTIES = ("easy", "medium", "hard")
V1_IMAGE_TYPES = frozenset({"photo-scene", "document", "figure", "photo-other", "chart", "ui", "mixed", "photo-object", "photo-animal",
                            "sign", "diagram-map", "photo-person", "photo-vehicle", "art", "photo-food", "photo-structure",
                            "photo-plant", "text-in-image", *V1_EXTRA_IMAGE_TYPES})
V1_SKILLS = frozenset({"recognition", "ocr", "compare", "rules", "count", "spatial", "quantity", "negation", "contradiction",
                       "uncertainty"})
V1_TEXT_IMAGE_TYPE, V1_TEXT_SKILL = "none", SKILL_TEXT
#: where the picture / text of a v1 row comes from. "commons-new" = a Commons picture chosen for a NEW question (CC0 / public domain;
#: the row carries ``credit``). Rows derived from an existing picture keep the parent's source.
V1_SOURCES = frozenset({"commons-article", "commons-category", "commons-new", "rendered", "none"})
