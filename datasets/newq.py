# -*- coding: utf-8 -*-
"""New v1 questions (added after the first review): where they live, how they are numbered, the one table of reserved id ranges.

Why: several agents add questions in parallel. Each works in its OWN file ``datasets/questions/v1/new_<tag>.jsonl`` and only inside
the id ranges reserved for its tag, so no two writers ever touch the same file or draw the same number. This module is the single
source of that table (``RANGES``); the validator (tools/validate_new.py), the loader and NOTES.md all use / print it.

Numbering: ids keep the group prefix (photo / biz / rsn / txt) and four digits. 0001..0999 is the base band (photo-0001..1268
etc.), the new bands start at 1001, so a new id can never be mistaken for a base one. A tag not in ``RANGES`` is not accepted:
add it here first (one line), then use it.
"""
from __future__ import annotations

import pathlib
import re

GROUPS = ("photo", "biz", "rsn", "txt")
ORIGIN = "new"
NEW_PREFIX = "new_"
ID_RE = re.compile(r"^(photo|biz|rsn|txt)-(\d{4})$")

#: tag -> {group: (first number, last number)}   (inclusive). One file per tag: new_<tag>.jsonl
RANGES: dict = {
    "photo_variants": {"photo": (2001, 2199)},
    "photo_variants_b": {"photo": (2201, 2399)},
    "tk_ui": {"biz": (3001, 3299)},
    "rendered_b": {"biz": (3300, 3399), "rsn": (2001, 2099)},
    "rendered": {"biz": (1001, 1399), "rsn": (1001, 1199)},
    "ja_specific": {"biz": (2001, 2199), "photo": (3001, 3099)},
    "txt_controls": {"txt": (1001, 1199)},
    "txt_forms": {"txt": (2001, 2199)},
}
#: kept free for tags registered later (nothing may use these before its tag is added to RANGES)
SPARE = {"photo": (4001, 4999), "biz": (3400, 3999), "rsn": (2100, 2999), "txt": (3001, 3999)}
#: what each tag is for (printed in NOTES.md / the validator's help)
PURPOSE = {
    "photo_variants": "photo-derived variants: 2/3/5-16 choices, negation, none-of-the-above, position, count, score on photos",
    "photo_variants_b": "photo-derived variants, second half of the work (same kinds as photo_variants; separate file so two authors never collide)",
    "rendered_b": "drawn-picture follow-ups found in review: contrast pairs where 'none of the above' / 'cannot be determined' is a wrong option (the right answer is in the picture), skewed-answer fixes",
    "tk_ui": "UI pictures built as real Tkinter/ttk windows and captured as screenshots (answers derived from the widget settings; also Japanese UI)",
    "rendered": "newly drawn pictures (biz / rsn): many-option, 3/7/10-level scores, negation, none-of-the-above, contradiction, uncertainty",
    "ja_specific": "Japanese-specific questions (lang=ja): rendered Japanese signs / timetables / receipts, real Japanese signs (photo)",
    "txt_controls": "text-only controls: the same question as an image question with the picture removed (derived_from = that question)",
    "txt_forms": "new passage-based text-only questions in the missing forms (2/3/5 choices, score); article revision references only",
}


def new_filename(tag: str) -> str:
    return "%s%s.jsonl" % (NEW_PREFIX, tag)


def tag_of_filename(name: str) -> str | None:
    """``new_rendered.jsonl`` -> ``rendered`` (None when the name is not a new-question file)."""
    n = pathlib.Path(name).name
    if n.startswith(NEW_PREFIX) and n.endswith(".jsonl") and len(n) > len(NEW_PREFIX) + len(".jsonl"):
        return n[len(NEW_PREFIX):-len(".jsonl")]
    return None


def new_files(v1dir: pathlib.Path) -> list:
    """The new_<tag>.jsonl files of a v1 directory, sorted by name."""
    return sorted(p for p in pathlib.Path(v1dir).glob(NEW_PREFIX + "*.jsonl") if tag_of_filename(p.name))


def parse_id(qid: str):
    """``photo-2001`` -> ("photo", 2001); None if it is not of the form <group>-NNNN."""
    m = ID_RE.match(qid) if isinstance(qid, str) else None
    return (m.group(1), int(m.group(2))) if m else None


def in_reserved_range(tag: str, qid: str) -> bool:
    p = parse_id(qid)
    if not p or tag not in RANGES or p[0] not in RANGES[tag]:
        return False
    lo, hi = RANGES[tag][p[0]]
    return lo <= p[1] <= hi


def format_id(group: str, number: int) -> str:
    return "%s-%04d" % (group, number)


def ranges_markdown() -> str:
    """The reservation table, as printed in NOTES.md (``python -m datasets.newq`` prints it)."""
    lines = ["| tag（ファイル） | 予約範囲 | 用途 |", "|---|---|---|"]
    for tag, rg in RANGES.items():
        r = " / ".join("`%s-%04d`〜`%s-%04d`" % (g, lo, g, hi) for g, (lo, hi) in rg.items())
        lines.append("| `%s`（`new_%s.jsonl`） | %s | %s |" % (tag, tag, r, PURPOSE.get(tag, "")))
    r = " / ".join("`%s-%04d`〜`%s-%04d`" % (g, lo, g, hi) for g, (lo, hi) in SPARE.items())
    lines.append("| （予備） | %s | 新しい tag を `newq.RANGES` に登録するときの置き場。登録前は使わない |" % r)
    return "\n".join(lines)


def check_table() -> list:
    """Problems of the table itself (overlaps, ranges that reach the base band, bad groups). Empty = fine."""
    errs, spans = [], []
    for tag, rg in list(RANGES.items()) + [("(spare)", SPARE)]:
        for g, (lo, hi) in rg.items():
            if g not in GROUPS:
                errs.append("%s: unknown group %r" % (tag, g))
            if not 1000 <= lo <= hi <= 9999:
                errs.append("%s: %s range %d..%d must lie in 1000..9999 (0001..0999 is the base band)" % (tag, g, lo, hi))
            spans.append((g, lo, hi, tag))
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if a[0] == b[0] and b[1] <= a[2]:
            errs.append("ranges overlap: %s %s %d..%d and %s %d..%d" % (a[3], a[0], a[1], a[2], b[3], b[1], b[2]))
    return errs


if __name__ == "__main__":
    print(ranges_markdown())
