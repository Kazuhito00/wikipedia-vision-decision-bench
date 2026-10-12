# -*- coding: utf-8 -*-
"""Sample rows of the new-question format (one per kind of question). NOTES.md prints exactly these lines between the markers
``<!-- samples:begin -->`` / ``<!-- samples:end -->``; test_new_questions.py checks that the text in NOTES.md is identical to
``sample_lines()`` and that every sample passes tools/validate_new.py (so a follower who copies a sample gets a valid row).

The ids are the first free ones of each tag's reserved range (datasets/newq.py). The pictures of the rendered samples are
``generated/<id>.png`` (new files under work/); the photo variant reuses the picture of its parent (photo-0001).
"""
import json

PARENT_PICTURE = "data/images/b68ae37691c83e58bfc75db7e37b3546c9cfc400.jpg"        # the picture of photo-0001
PARENT_FILE = "File:Sheep lounging in the shade of a tree at Röe Castle.jpg"


def review():
    return {"state": "unreviewed", "history": []}


def photo_choice():
    """A 6-choice variant of photo-0001 (same picture, derived_from = the parent)."""
    return {"id": "photo-2001", "legacy_id": None, "origin": "new", "derived_from": "photo-0001", "relation": "variant",
            "group": "photo", "source": "commons-article", "image_type": "photo-animal", "skill": "recognition",
            "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "choice",
            "answer_format": "choice:6", "tags": ["classify", "animal", "many-options"],
            "images": [PARENT_FILE], "local_images": [PARENT_PICTURE],
            "en": {"instr": "Which animal is mainly shown?", "correct": "sheep", "wrong": ["goat", "pig", "rabbit", "cow", "None of the above"]},
            "ja": {"instr": "主に写っている動物はどれですか？", "correct": "羊", "wrong": ["ヤギ", "豚", "ウサギ", "牛", "該当なし"]},
            "review": review()}


def rendered_yesno():
    return {"id": "biz-1001", "legacy_id": None, "origin": "new", "derived_from": None, "group": "biz", "source": "rendered",
            "image_type": "chart", "skill": "negation", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"],
            "modality": "image", "kind": "noul", "answer_format": "yesno", "tags": ["synthetic", "chart", "negation"],
            "local_images": ["generated/biz-1001.png"],
            "en": {"instr": "No bar is taller than the first bar"},
            "ja": {"instr": "最初の棒より高い棒はない"},
            "answer": True, "review": review()}


def rendered_score():
    return {"id": "rsn-1001", "legacy_id": None, "origin": "new", "derived_from": None, "group": "rsn", "source": "rendered",
            "image_type": "ui", "skill": "quantity", "difficulty": "medium", "lang": "both", "langs": ["en", "ja"],
            "modality": "image", "kind": "score", "answer_format": "score:7", "tags": ["synthetic", "gauge", "level"],
            "local_images": ["generated/rsn-1001.png"],
            "en": {"instr": "How full is the gauge?",
                   "levels": ["0-14%", "15-28%", "29-42%", "43-57%", "58-71%", "72-85%", "86-100%"]},
            "ja": {"instr": "ゲージはどれくらい満たされていますか？",
                   "levels": ["0〜14%", "15〜28%", "29〜42%", "43〜57%", "58〜71%", "72〜85%", "86〜100%"]},
            "answer": 3, "review": review()}


def japanese_only():
    """A Japanese-specific question: lang "ja", only the ja side, a rendered picture with Japanese text."""
    return {"id": "biz-2001", "legacy_id": None, "origin": "new", "derived_from": None, "group": "biz", "source": "rendered",
            "image_type": "sign", "skill": "ocr", "difficulty": "medium", "lang": "ja", "langs": ["ja"],
            "modality": "image", "kind": "choice", "answer_format": "choice:5", "tags": ["synthetic", "japanese", "sign"],
            "local_images": ["generated/biz-2001.png"],
            "ja": {"instr": "この標識が示している意味はどれですか？", "correct": "一時停止",
                   "wrong": ["徐行", "進入禁止", "駐車禁止", "該当なし"]},
            "review": review()}


def text_control():
    """A text-only control: the picture of biz-0015 removed; an authored state says so; no Wikipedia text."""
    return {"id": "txt-1001", "legacy_id": None, "origin": "new", "derived_from": "biz-0015", "relation": "control", "group": "txt",
            "source": "none", "image_type": "none", "skill": "text-comprehension", "difficulty": "easy", "lang": "both",
            "langs": ["en", "ja"], "modality": "text", "kind": "noul", "answer_format": "yesno", "tags": ["control", "no-picture"],
            "local_images": [],
            "en": {"instr": "The values rise from left to right", "state": "No picture is attached to this question."},
            "ja": {"instr": "値は左から右に向かって増えている", "state": "この問題には画像が添付されていません。"},
            "answer": True, "review": review()}


SAMPLES = [photo_choice, rendered_yesno, rendered_score, japanese_only, text_control]


def sample_rows() -> list:
    return [f() for f in SAMPLES]


def sample_lines() -> list:
    return [json.dumps(r, ensure_ascii=False) for r in sample_rows()]
