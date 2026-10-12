# -*- coding: utf-8 -*-
"""Authoring helpers. Questions are written by hand (by Claude Code, from looking at each picture / reading
each lead section); these helpers only fix the record shape. build_questions.py compiles them to
questions.jsonl and checks them against the downloaded material.

Image items refer to candidates by id (c0123); the compiler swaps the id for the Commons title and the sha1
of the original file. Text items refer to an English article title; the compiler adds the pinned revisions.

choice : correct + wrong (aligned en/ja: wrong[i] in en is the translation of wrong[i] in ja)
noul   : a statement the model answers true/false (answer = True / False)
score  : ordered levels, answer = index of the right level
"""
from __future__ import annotations

ITEMS: list[dict] = []


def _add(rec):
    ITEMS.append(rec)
    return rec


def ichoice(imgs, en_q, en_ok, en_bad, ja_q, ja_ok, ja_bad, tags=(), diff="easy", en_state=None, ja_state=None):
    imgs = [imgs] if isinstance(imgs, str) else list(imgs)
    assert len(en_bad) == len(ja_bad) and len(en_bad) >= 1, (en_q, en_bad, ja_bad)
    return _add(dict(modality="image", kind="choice", images=imgs, tags=list(tags), difficulty=diff,
                     en=dict(instr=en_q, correct=en_ok, wrong=list(en_bad), **({"state": en_state} if en_state else {})),
                     ja=dict(instr=ja_q, correct=ja_ok, wrong=list(ja_bad), **({"state": ja_state} if ja_state else {}))))


def inoul(imgs, en_stmt, ja_stmt, answer, tags=(), diff="easy"):
    imgs = [imgs] if isinstance(imgs, str) else list(imgs)
    return _add(dict(modality="image", kind="noul", images=imgs, tags=list(tags), difficulty=diff, answer=bool(answer),
                     en=dict(instr=en_stmt), ja=dict(instr=ja_stmt)))


def iscore(imgs, en_q, en_levels, ja_q, ja_levels, answer, tags=(), diff="medium"):
    imgs = [imgs] if isinstance(imgs, str) else list(imgs)
    assert len(en_levels) == len(ja_levels)
    return _add(dict(modality="image", kind="score", images=imgs, tags=list(tags), difficulty=diff, answer=int(answer),
                     en=dict(instr=en_q, levels=list(en_levels)), ja=dict(instr=ja_q, levels=list(ja_levels))))


def tchoice(title, en_q, en_ok, en_bad, ja_q, ja_ok, ja_bad, ev_en, ev_ja, tags=(), diff="easy", only=None):
    """ev_en / ev_ja: strings that must occur in the passage (the evidence for the right answer).
    only="en" / "ja": a single-language item (the other language's arguments may be None / empty)."""
    if only != "ja" and only != "en":
        assert len(en_bad) == len(ja_bad) and len(en_bad) >= 1, (title, en_bad, ja_bad)
    return _add(dict(modality="text", kind="choice", title=title, tags=list(tags), difficulty=diff, langs=_langs(only),
                     en=dict(instr=en_q, correct=en_ok, wrong=list(en_bad or [])),
                     ja=dict(instr=ja_q, correct=ja_ok, wrong=list(ja_bad or [])),
                     evidence=dict(en=list(ev_en or []), ja=list(ev_ja or []))))


def tnoul(title, en_stmt, ja_stmt, answer, ev_en, ev_ja, absent_en=(), absent_ja=(), tags=(), diff="easy", only=None):
    """For a false statement, ev_* is the true fact in the passage and absent_* the wrong detail that must NOT be there."""
    return _add(dict(modality="text", kind="noul", title=title_check(title), tags=list(tags), difficulty=diff, langs=_langs(only),
                     answer=bool(answer), en=dict(instr=en_stmt), ja=dict(instr=ja_stmt),
                     evidence=dict(en=list(ev_en or []), ja=list(ev_ja or [])),
                     absent=dict(en=list(absent_en), ja=list(absent_ja))))


def _langs(only):
    return [only] if only in ("en", "ja") else ["en", "ja"]


def title_check(t):
    return t
