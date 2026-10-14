# -*- coding: utf-8 -*-
"""The allowed values of the classification axes of a v1 row (used by tools/validate_new.py).

Axes: group (photo / biz / rsn / txt), source, image_type, skill, answer (kind + n), difficulty, lang. The image_type and skill are
coarse labels; datasets/NOTES.md describes them.
"""
from __future__ import annotations

NEW_GROUPS = ("photo", "biz", "rsn", "txt")
SKILL_TEXT = "text-comprehension"
# image types added after the first review (astronomical photographs, satellite pictures)
V1_EXTRA_IMAGE_TYPES = ("astronomical", "satellite")

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
