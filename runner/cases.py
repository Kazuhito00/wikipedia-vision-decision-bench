# -*- coding: utf-8 -*-
"""Where the runner (and the report) get their questions: ONE function, ``load_cases``.

    load_cases("commons" | "synthetic" | "reasoning" | "all", data_root=None) -> list of case dicts
        dict(id, kind, modality, tags, difficulty, images=[abs paths], expected, en=dict(state, instr, options), ja=...)
        choice options are (key, text) pairs, score options are level strings, noul has options=None.

Version "v1" (``load_cases(set, version="v1")``): the sets are photo / biz / rsn / txt / all (the four groups) and new (only
the questions added after the polish, datasets/questions/v1/new_<tag>.jsonl); (the sets of version legacy are commons / synthetic / reasoning).
Dropped questions are skipped, the options follow the balanced order, new questions are included. A legacy set name with version v1 (and the
reverse) is an error. Results are keyed by (dataset_version, id): v1 ids such as rsn-0001 are NOT the legacy ones.

It uses the repository's loader (``datasets.loader``: same option order and ``expected`` as the old one for legacy) when the question files are
there, otherwise a verbatim port of the old ``wiki_qa/wikiqa/dataset.py`` (``BENCH_LEGACY_LOADER=1`` forces it). ``BENCH_LOADER=pkg.mod:func``
(a callable with the signature ``func(set_name, data_root)``) overrides both. Nothing else in runner/ or report/ reads questions.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import pathlib
import random

from . import config

#: set name -> the jsonl files under <data_root>/data/ (legacy layout, written by datasets/fetch/fetch_dataset.py and datasets/synthetic)
LEGACY_FILES = {"commons": ("linked.jsonl",), "synthetic": ("synthetic.jsonl",), "reasoning": ("reasoning.jsonl",),
            "all": ("linked.jsonl", "synthetic.jsonl")}
DEFAULT_STATE = {"en": "Look at the attached photograph.", "ja": "添付の写真を見てください。"}
TWO_STATE = {"en": "Two photographs are attached.", "ja": "2 枚の写真が添付されています。"}


#: v1 set name -> (groups, only the new questions?)
V1_SETS = {"photo": (("photo",), False), "biz": (("biz",), False), "rsn": (("rsn",), False), "txt": (("txt",), False),
           "all": (("photo", "biz", "rsn", "txt"), False), "new": (("photo", "biz", "rsn", "txt"), True)}


def v1_set(set_name: str) -> tuple:
    """"photo" -> (("photo",), False). Raises ValueError for a name that is not a v1 set."""
    if set_name not in V1_SETS:
        raise ValueError("%r is not a v1 set (use %s)" % (set_name, ", ".join(sorted(V1_SETS))))
    return V1_SETS[set_name]


def load_cases(set_name: str, data_root: pathlib.Path | None = None, version: str = "legacy", *, strict_passages: bool = True) -> list[dict]:
    """The cases of one question group. Order of preference: ``BENCH_LOADER`` (a hook), the repository's own loader
    (``datasets.loader``, when ``datasets/questions/<version>/`` has the group's file), the legacy loader below.
    version "v1": ``datasets.loader.load_v1_cases`` (dropped skipped, balanced order, new questions included); the hook still wins."""
    hook = os.environ.get("BENCH_LOADER")
    if hook:                                            # "package.module:function"
        mod, _, fn = hook.partition(":")
        return getattr(importlib.import_module(mod), fn)(set_name, data_root)
    root = data_root or config.data_root()
    if version == "v1":
        if os.environ.get("BENCH_LEGACY_LOADER"):
            raise ValueError("BENCH_LEGACY_LOADER only knows the legacy questions")
        if set_name in ("commons", "synthetic", "reasoning"):
            raise ValueError("%r is a legacy set; the v1 sets are %s" % (set_name, ", ".join(sorted(V1_SETS))))
        groups, only_new = v1_set(set_name)
        from datasets import loader as new_loader
        return new_loader.load_v1_cases(groups, images_root=root, only_new=only_new, strict_passages=strict_passages,
                                        passages_path=os.environ.get("WIKIQA_PASSAGES") or root / "data" / "passages.json")
    if version != "legacy":
        raise ValueError("unknown dataset version %r" % version)
    if set_name in V1_SETS and set_name not in LEGACY_FILES:
        raise ValueError("%r is a v1 set: pass version='v1' (--dataset-version v1)" % set_name)
    if not os.environ.get("BENCH_LEGACY_LOADER"):
        try:
            from datasets import loader as new_loader
            files = LEGACY_FILES[set_name]
            if all((new_loader.QDIR / version / f).exists() for f in files):
                return new_loader.load_cases(version, files=files, images_root=root,
                                             passages_path=os.environ.get("WIKIQA_PASSAGES") or root / "data" / "passages.json")
        except ImportError:
            pass
    return load_cases_legacy(LEGACY_FILES[set_name], root)


# ---- legacy loader (verbatim logic of wiki_qa/wikiqa/dataset.py) -------------------------------------------------------------
def _rng(qid: str) -> random.Random:
    return random.Random(int(hashlib.sha1(qid.encode()).hexdigest()[:12], 16))


def load_cases_legacy(files: tuple, root: pathlib.Path) -> list[dict]:
    data = root / "data"
    passages = json.loads((data / "passages.json").read_text(encoding="utf-8")) if (data / "passages.json").exists() else {}
    cases = []
    lines = [ln for f in files for ln in (data / f).read_text(encoding="utf-8").splitlines()]
    for ln in lines:
        if not ln.strip():
            continue
        r = json.loads(ln)
        rng = _rng(r["id"])
        case = dict(id=r["id"], kind=r["kind"], modality=r["modality"], tags=r.get("tags", []),
                    difficulty=r.get("difficulty"), images=[str(root / p) for p in r.get("local_images", [])])
        if r["kind"] == "choice":
            first = (r.get("langs") or ["en", "ja"])[0]
            order = list(range(1 + len(r[first]["wrong"])))          # 0 = the correct answer
            rng.shuffle(order)
            case["expected"] = order.index(0)
        for lang in (r.get("langs") or ["en", "ja"]):
            q = r[lang]
            if r["modality"] == "text":
                a = r["article"][lang]
                state = passages["%s:%s" % (lang, a["revid"])]["text"]
            else:
                state = q.get("state") or (TWO_STATE if len(case["images"]) > 1 else DEFAULT_STATE)[lang]
            if r["kind"] == "choice":
                items = [q["correct"]] + list(q["wrong"])
                options = [(items[i], items[i]) for i in order]
            elif r["kind"] == "score":
                options = list(q["levels"])
            else:
                options = None
            case[lang] = dict(state=state, instr=q["instr"], options=options)
        if r["kind"] == "noul":
            case["expected"] = bool(r["answer"])
        elif r["kind"] == "score":
            case["expected"] = int(r["answer"])
        cases.append(case)
    return cases


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
