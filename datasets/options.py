# -*- coding: utf-8 -*-
"""Order of the options of a choice question: two modes, one reversal.

Why this file exists: the position of the right answer must not be guessable and must be the same on every machine.

legacy    (version "legacy" only)  the order of the old wikiqa.dataset.load_cases, reproduced exactly: a seeded shuffle per question,
                     seed = int(sha1(<legacy question id>)[:12], 16). Position 0 of the shuffled list is NOT special: the shuffle is
                     over the indices [0 = correct answer, 1.. = wrong answers]; the right answer's new position is
                     ``order.index(0)``. Changing one byte of this function changes the legacy answer keys, so it is frozen
                     (tests/test_options.py compares it with golden data made from the old loader).
balanced  (version "v1" only)  the right answer's position is spread evenly *per question group and number of options* (the counts of the
                     positions differ by at most one in each bucket), deterministically; the order of the wrong answers is a
                     seeded shuffle. It raises for version "legacy": legacy results were measured with the legacy order.
                     Special options ("none of the above", "cannot be determined", ...; see ``is_special``) are not shuffled:
                     they stay at the end, in their original relative order, so the layout of a question stays natural.
                     A question whose right answer is a special option has a fixed position (the tail) and is left out of the
                     balancing of the free positions (``v1_orders`` does this; the loader, review export and summary use it).
                     New questions (origin "new") are dealt on top of the base ones without moving any base question
                     (``assign_positions_with_base``). Works for 2..16 options (QEV's limit) and more; score levels are ordinal and
                     never reordered (``suggest_score_answers`` only helps authors spread the right level).

reversal (REV)       ask the same question with the options in the opposite order (to detect a position bias). Normal runs use
                     REV=0. ``reverse_options`` / ``reversed_expected`` do it for any option count; the special options are
                     reversed too (it is only a probe of position bias).

All functions are pure and need no network.
"""
from __future__ import annotations

import hashlib
import random
import re
from typing import Iterable, Sequence

LEGACY = "legacy"
BALANCED = "balanced"
MODES = (LEGACY, BALANCED)

# options that mean "no listed answer applies / not decidable" (v1 rule: pinned to the end, not shuffled)
_SPECIAL_EN = re.compile(r"^\s*(none of (the above|these|them|the (listed|options|choices))|neither|no (correct )?answer|not applicable|n/?a|"
                         r"cannot be determined|can'?t be determined|can'?t tell|cannot tell|not enough information|"
                         r"insufficient information|unknown|undetermined)\.?\s*$", re.I)
_SPECIAL_JA = re.compile(r"^\s*(該当なし|該当するものはない|どれも(当てはまらない|あてはまらない|違う)|どれでもない|"
                         r"いずれでもない|いずれも(当てはまらない|あてはまらない|違う)|"
                         r"上記(の)?(いずれ|どれ)(でもない|も(当てはまらない|あてはまらない|違う))|上記以外|この中にはない|"
                         r"判断できない|判断不能|わからない|分からない|決められない|情報が足りない|不明)[。．.]?\s*$")


def is_special(text: str) -> bool:
    """True for a 'none of the above / cannot be determined' style option (English or Japanese wording)."""
    return bool(_SPECIAL_EN.match(text) or _SPECIAL_JA.match(text))


def pinned_indices(*option_lists: Sequence[str]) -> list[int]:
    """Indices (0 = correct, 1.. = wrong, as in the question record) of the special options. ``option_lists`` = the
    [correct] + wrong lists of each language; an index is special if it is special in any language."""
    n = len(option_lists[0])
    return [i for i in range(n) if any(is_special(lst[i]) for lst in option_lists)]


def _seed(text: str) -> int:
    return int(hashlib.sha1(text.encode()).hexdigest()[:12], 16)


# ------------------------------------------------------------------------------------------------------ legacy order
def legacy_order(qid: str, n: int) -> list[int]:
    """The old order. ``qid`` must be the legacy question id. Returns ``order``: the option shown at position p is item
    ``order[p]`` of [correct, wrong1, ...]; the right answer is at ``order.index(0)``."""
    order = list(range(n))
    random.Random(_seed(qid)).shuffle(order)
    return order


# ---------------------------------------------------------------------------------------------------- balanced (v1)
#: The sort key of a question hashes "<version>:<id>". The current dataset was named "v2" while the answer positions were assigned and
#: published; it is "v1" now (the repository's first version). The positions must NOT move, so the hash keeps the old spelling.
_HASH_VERSION = {"v1": "v2"}


def _key_hash(k: tuple) -> str:
    return hashlib.sha1(("%s:%s" % (_HASH_VERSION.get(k[0], k[0]), k[1])).encode()).hexdigest()


def assign_positions(items: Iterable[tuple]) -> dict:
    """Even positions of the right answer.

    ``items``: (key, bucket, n_free) per choice question: key = (version, id); bucket = the question group (photo / biz / rsn
    / txt ...); n_free = the number of options that take part in the shuffle (all options minus the pinned special ones).
    Returns {key: position in range(n_free)}. Within each (bucket, n_free) the questions are sorted by the sha1 of the key and
    dealt out round-robin from a bucket-specific start, so every position gets floor or ceil of count / n_free. The same set of
    questions always gives the same answer, whatever the input order.
    """
    buckets: dict = {}
    for key, bucket, n_free in items:
        buckets.setdefault((bucket, n_free), []).append(key)
    out = {}
    for (bucket, n_free), keys in buckets.items():
        keys.sort(key=_key_hash)
        start = _seed("%s:%d" % (bucket, n_free)) % n_free
        for i, k in enumerate(keys):
            out[k] = (start + i) % n_free
    return out


def balanced_order(qid: str, n: int, position: int, pinned: Sequence[int] = ()) -> list[int]:
    """The order of one v1 question. ``position``: where the right answer goes among the free (non-pinned) positions, from
    ``assign_positions``; ignored when the right answer itself is pinned (index 0 in ``pinned``)."""
    pinned = sorted(pinned)
    free = [i for i in range(n) if i not in pinned]
    rng = random.Random(_seed("balanced:" + qid))
    if 0 in pinned:                                   # the right answer is "none of the above": it stays in the tail
        wrong_free = free[:]
        rng.shuffle(wrong_free)
        return wrong_free + pinned
    if not 0 <= position < len(free):
        raise ValueError("position %d out of range for %d free options" % (position, len(free)))
    wrong_free = [i for i in free if i != 0]
    rng.shuffle(wrong_free)
    order = wrong_free[:position] + [0] + wrong_free[position:]
    return order + pinned


# ------------------------------------------------------------------------------------- balanced (v1, with new questions)
def assign_positions_with_base(base_items: Iterable[tuple], new_items: Iterable[tuple]) -> dict:
    """``assign_positions`` for the v1 base questions, then the new questions on top of them, WITHOUT moving any base question.

    Why: v1 questions are added over time by several writers; the answer position of an already-published question must not change
    when someone adds a question to its bucket. The base items get exactly what ``assign_positions`` gives them. Each new item (sorted
    by the sha1 of its key) then takes the position that currently has the fewest right answers in its (bucket, n_free) (ties: the
    bucket's start order), so the union keeps a spread of at most one whenever the base had one. (The new questions' own positions
    depend on the whole new set: they are final when the new set is frozen.)
    """
    base_items = list(base_items)
    out = assign_positions(base_items)
    counts: dict = {}
    for key, bucket, n_free in base_items:
        counts.setdefault((bucket, n_free), [0] * n_free)[out[key]] += 1
    new_buckets: dict = {}
    for key, bucket, n_free in new_items:
        new_buckets.setdefault((bucket, n_free), []).append(key)
    for (bucket, n_free), keys in sorted(new_buckets.items()):
        keys.sort(key=_key_hash)
        start = _seed("%s:%d" % (bucket, n_free)) % n_free
        c = counts.setdefault((bucket, n_free), [0] * n_free)
        for k in keys:
            pos = min(range(n_free), key=lambda i: (c[i], (i - start) % n_free))
            c[pos] += 1
            out[k] = pos
    return out


def v1_orders(rows: Iterable[dict]) -> dict:
    """{id: order} of every choice question among the v1 ``rows`` (base and new, dropped ones already removed by the caller).

    The one place that decides the balanced positions: the loader, the review export and the summary all call it. A row is "new" when
    ``row["origin"] == "new"``. A question whose right answer is a special option ("none of the above" ...) sits at the tail and is
    left OUT of the balancing (it would otherwise use up a position slot that ``balanced_order`` ignores).
    """
    base, new, pins, ns = [], [], {}, {}
    for r in rows:
        if r.get("kind") != "choice":
            continue
        langs = r.get("langs") or ["en", "ja"]
        pin = pinned_indices(*[[r[l]["correct"]] + list(r[l]["wrong"]) for l in langs])
        n = 1 + len(r[langs[0]]["wrong"])
        pins[r["id"]], ns[r["id"]] = pin, n
        if 0 in pin:
            continue
        item = (("v1", r["id"]), r.get("group", "?"), max(n - len(pin), 1))
        (new if r.get("origin") == "new" else base).append(item)
    pos = assign_positions_with_base(base, new)
    return {qid: balanced_order(qid, ns[qid], pos.get(("v1", qid), 0), pins[qid]) for qid in ns}


def suggest_score_answers(ids: Sequence[str], n_levels: int) -> dict:
    """A deterministic, even spread of the right level over score questions, for the AUTHOR to use when writing them
    ({id: level in range(n_levels)}; each level used floor or ceil of len(ids) / n_levels times). The levels themselves are ordinal and are
    never reordered at run time: ``row["answer"]`` is the level index and stays as written."""
    keys = sorted(ids, key=lambda i: hashlib.sha1(i.encode()).hexdigest())
    start = _seed("score:%d" % n_levels) % n_levels
    return {k: (start + i) % n_levels for i, k in enumerate(keys)}


def option_labels(n: int) -> list:
    """Display labels A, B, ... Z, AA, AB ... for n options (review batches and reports show 10-16 option questions with them)."""
    out = []
    for i in range(n):
        k, lab = i, ""
        while True:
            lab = chr(65 + k % 26) + lab
            k = k // 26 - 1
            if k < 0:
                break
        out.append(lab)
    return out


# --------------------------------------------------------------------------------------------------------- dispatch
def order_for(mode: str, version: str, qid: str, n: int, *, position: int | None = None, pinned: Sequence[int] = ()) -> list[int]:
    """One entry point. version legacy -> the legacy mode only (balanced raises), version v1 -> the balanced mode only (legacy raises)."""
    if mode not in MODES:
        raise ValueError("unknown mode %r" % mode)
    if version == "legacy" and mode != LEGACY:
        raise ValueError("legacy results were measured with the legacy order: balanced must never be used for legacy")
    if version == "v1" and mode != BALANCED:
        raise ValueError("v1 uses the balanced order")
    if mode == LEGACY:
        return legacy_order(qid, n)
    if position is None:
        raise ValueError("balanced mode needs the position from assign_positions()")
    return balanced_order(qid, n, position, pinned)


def apply_order(items: Sequence, order: Sequence[int]) -> list:
    return [items[i] for i in order]


def expected_of(order: Sequence[int]) -> int:
    """Position of the right answer (item 0)."""
    return list(order).index(0)


# ---------------------------------------------------------------------------------------------------- reversal (REV)
def reverse_options(options: Sequence) -> list:
    return list(reversed(options))


def reversed_expected(expected: int, n: int) -> int:
    """Where the right answer is after ``reverse_options`` (the old run.py: ``len(ro) - 1 - got_r`` is compared with
    ``expected``, i.e. a reversed index maps back with the same formula)."""
    return n - 1 - expected
