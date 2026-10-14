# -*- coding: utf-8 -*-
"""Where the runner (and the report) get their questions: ONE function, ``load_cases``.

    load_cases("photo" | "biz" | "rsn" | "txt" | "all" | "new", data_root=None) -> list of case dicts
        dict(id, kind, modality, tags, difficulty, images=[abs paths], expected, en=dict(state, instr, options), ja=...)
        choice options are (key, text) pairs, score options are level strings, noul has options=None.

Sets: photo / biz / rsn / txt / all (the four groups) and new (only the questions added after the first review,
datasets/questions/v1/new_<tag>.jsonl). Dropped questions are skipped, the options follow the balanced order, new questions are
included. Results are keyed by (dataset_version, id).

It uses the repository's loader (``datasets.loader``). ``BENCH_LOADER=pkg.mod:func`` (a callable with the signature
``func(set_name, data_root)``) overrides it. Nothing else in runner/ or report/ reads questions.
"""
from __future__ import annotations

import importlib
import os
import pathlib

from . import config

#: v1 set name -> (groups, only the new questions?)
V1_SETS = {"photo": (("photo",), False), "biz": (("biz",), False), "rsn": (("rsn",), False), "txt": (("txt",), False),
           "all": (("photo", "biz", "rsn", "txt"), False), "new": (("photo", "biz", "rsn", "txt"), True)}


def v1_set(set_name: str) -> tuple:
    """"photo" -> (("photo",), False). Raises ValueError for a name that is not a v1 set."""
    if set_name not in V1_SETS:
        raise ValueError("%r is not a v1 set (use %s)" % (set_name, ", ".join(sorted(V1_SETS))))
    return V1_SETS[set_name]


def load_cases(set_name: str, data_root: pathlib.Path | None = None, version: str = "v1", *, strict_passages: bool = True) -> list[dict]:
    """The cases of one question group. Order of preference: ``BENCH_LOADER`` (a hook), the repository's own loader
    (``datasets.loader.load_v1_cases``: dropped skipped, balanced order, new questions included)."""
    hook = os.environ.get("BENCH_LOADER")
    if hook:                                            # "package.module:function"
        mod, _, fn = hook.partition(":")
        return getattr(importlib.import_module(mod), fn)(set_name, data_root)
    root = data_root or config.data_root()
    if version != "v1":
        raise ValueError("unknown dataset version %r" % version)
    groups, only_new = v1_set(set_name)
    from datasets import loader
    return loader.load_v1_cases(groups, images_root=root, only_new=only_new, strict_passages=strict_passages,
                                passages_path=os.environ.get("WIKIQA_PASSAGES") or root / "data" / "passages.json")


# ---- v1 checks that need no model: limits and a dry run ------------------------------------------------------------------
def check_limits(cases: list[dict], limits: dict) -> list[str]:
    """What in ``cases`` is beyond one model's ``limits`` (an adapter's LIMITS dict: max_images, max_choice_options, max_score_levels,
    min_options). One string per offending (case, language); empty list = every question is within the limits."""
    out = []
    for c in cases:
        if limits.get("max_images") is not None and len(c["images"]) > limits["max_images"]:
            out.append("%s: %d pictures (max %d)" % (c["id"], len(c["images"]), limits["max_images"]))
        for lang in ("en", "ja"):
            if lang not in c:
                continue
            o = c[lang]["options"]
            if c["kind"] == "choice":
                n, hi, lo = len(o), limits.get("max_choice_options"), limits.get("min_options")
            elif c["kind"] == "score":
                n, hi, lo = len(o), limits.get("max_score_levels"), limits.get("min_options")
            else:
                continue
            if hi is not None and n > hi:
                out.append("%s/%s: %d %s (max %d)" % (c["id"], lang, n, "options" if c["kind"] == "choice" else "levels", hi))
            if lo is not None and n < lo:
                out.append("%s/%s: %d options (min %d)" % (c["id"], lang, n, lo))
    return out


def check_all_limits(cases: list[dict], limits_by_model: dict | None = None) -> dict:
    """{model key: [problems]} for every adapter of the registry (``adapters.limits(key)`` imports the adapter module only, never a model).
    A model whose adapter cannot be imported here maps to None. Pass ``limits_by_model`` to check other limits."""
    if limits_by_model is None:
        limits_by_model = {}
        import adapters
        for key in adapters.REGISTRY:
            try:
                limits_by_model[key] = adapters.limits(key)
            except Exception:                                      # noqa: BLE001  (the runtime package is not installed here)
                limits_by_model[key] = None
    return {k: (check_limits(cases, v) if v is not None else None) for k, v in limits_by_model.items()}


def dry_run(cases: list[dict], ask=None, lang: str | None = None, check_images: bool = False) -> dict:
    """Walk every case with a dummy ``ask`` (default: always the first option / yes / level 0) exactly as runner.run does and verify what
    the runner and the adapters rely on: the return type and range of ``ask``, ``expected`` in range, distinct options, at most one picture
    (with ``check_images`` they must exist), a non-empty state and question. Returns counts and ``problems`` (a list of strings)."""
    problems, counts = [], {"cases": 0, "asked": 0, "choice_options": {}, "score_levels": {}}
    for c in cases:
        counts["cases"] += 1
        if len(c["images"]) > 1:
            problems.append("%s: %d pictures (one per question)" % (c["id"], len(c["images"])))
        if check_images:
            problems += ["%s: picture not found: %s" % (c["id"], i) for i in c["images"] if not pathlib.Path(i).is_file()]
        for lg in ([lang] if lang else ["en", "ja"]):
            if lg not in c:
                continue
            L = c[lg]
            if not str(L["state"]).strip() or not str(L["instr"]).strip():
                problems.append("%s/%s: empty state or question" % (c["id"], lg))
            o, kind = L["options"], c["kind"]
            if kind == "choice":
                if len({t for _, t in o}) != len(o):
                    problems.append("%s/%s: duplicate option texts" % (c["id"], lg))
                if not 0 <= c["expected"] < len(o):
                    problems.append("%s/%s: expected %r outside 0..%d" % (c["id"], lg, c["expected"], len(o) - 1))
                counts["choice_options"][len(o)] = counts["choice_options"].get(len(o), 0) + 1
            elif kind == "score":
                if not 0 <= c["expected"] < len(o):
                    problems.append("%s/%s: expected level %r outside 0..%d" % (c["id"], lg, c["expected"], len(o) - 1))
                counts["score_levels"][len(o)] = counts["score_levels"].get(len(o), 0) + 1
            elif o is not None or not isinstance(c["expected"], bool):
                problems.append("%s/%s: a yes/no case needs options=None and a boolean expected" % (c["id"], lg))
            got = ask(L["state"], list(c["images"]), kind, L["instr"], o) if ask else (True if kind == "noul" else 0)
            counts["asked"] += 1
            if kind == "noul":
                valid = isinstance(got, bool)
            else:
                valid = isinstance(got, int) and not isinstance(got, bool) and 0 <= got < len(o)
            if not valid:
                problems.append("%s/%s: ask returned %r, not a valid answer for kind %s" % (c["id"], lg, got, kind))
    counts["problems"] = problems
    return counts
