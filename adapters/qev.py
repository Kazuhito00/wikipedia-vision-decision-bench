# -*- coding: utf-8 -*-
"""QEV 0.2.1 (ONNX CPU, no torch) -> ``ask``.  Key: ``qev``.

Install:  the ``qev_decide`` package (``uv pip install git+https://github.com/Kazuhito00/QEV-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``QEV_MODEL_DIR`` (the ``models/onnx`` folder).

Limits and what this adapter does about them (``ask.stats`` counts every case that hit one):
  * ONE picture per request. More than one raises ValueError (the question is OUT OF SCOPE for QEV: the runner records it as not run,
    the report leaves it out of QEV's tally). No tiling or dropping of pictures.
  * choice / score need 2..16 options; fewer or more raises ValueError (no silent dropping of the right answer).
  * more than 2048 tokens in total (QEV refuses) -> the evidence text is cut from the end (halving) until it fits (``truncated``).
  * choice options must have distinct, non-blank descriptions and QEV renders the DESCRIPTION, never the key, and sorts the options by
    description (so the model's letters are a permutation of the caller's order): the adapter gives every option a synthetic key
    o0..oN, uses the caller's text as description (the key text if blank, " (i)" appended when two collide) and maps the answer back to
    the caller's index.
  * a blank state with no picture -> "(no evidence)".
  * abstention is ignored: the argmax is always returned. noul uses QEV's default true/false criteria in both languages.
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=1, max_choice_options=16, max_score_levels=16, min_options=2, gpu=True, note="2048 tokens in total")


def build(model_dir=None, threads=8, providers=None, lang="en", part="text", variant=None, key="qev"):
    R = C.import_runtime("qev_decide", "uv pip install git+https://github.com/Kazuhito00/QEV-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    d = Decider(C.model_dir_of(model_dir, "QEV_MODEL_DIR"), intra_op_threads=threads, load_vision=C.needs_vision(part), providers=providers)
    stats = {"calls": 0, "truncated": 0, "dup_or_blank_descriptions": 0, "abstained": 0}

    def run(state, qobj, images):
        try:
            return d.decide(state, {"q": qobj}, images=images)["q"]
        except ValueError as e:
            if "exceeding" not in str(e):
                raise
        stats["truncated"] += 1                 # over the 2048-token budget: cut the evidence from the end until the request fits
        text = state
        while True:
            text = text[: max(1, len(text) // 2)]
            try:
                return d.decide(text, {"q": qobj}, images=images)["q"]
            except ValueError as e:
                if "exceeding" not in str(e) or len(text) <= 1:
                    raise

    def ask(state, images, kind, instr, options):
        stats["calls"] += 1
        images = list(images or [])
        if len(images) > 1:
            raise ValueError("QEV takes one image per request (out of scope)")
        if not state or not state.strip():
            state = "(no evidence)" if not images else ""
        if kind == "noul":
            a = run(state, noul(instr), images)
            stats["abstained"] += bool(a["abstained"])
            return a["noul"] > 0.5
        if not 2 <= len(options) <= 16:
            raise ValueError("QEV takes 2 to 16 options (got %d)" % len(options))
        if kind == "choice":
            texts = []
            for i, (k, t) in enumerate(options):
                texts.append((t or "").strip() or str(k).strip() or "option %d" % i)
            seen, fixed = set(), False
            for i, t in enumerate(texts):
                u = t
                while u in seen:
                    u = "%s (%d)" % (t, i + 1)
                    fixed = True
                seen.add(u)
                texts[i] = u
            stats["dup_or_blank_descriptions"] += fixed
            a = run(state, choice(instr, {"o%d" % i: t for i, t in enumerate(texts)}), images)
            stats["abstained"] += bool(a["abstained"])
            return int(a["choice"][1:])
        levels = [(str(t).strip() or str(i)) for i, t in enumerate(options)]
        a = run(state, score(instr, levels), images)
        stats["abstained"] += bool(a["abstained"])
        p = a["probabilities"]
        return int(max(p, key=p.get))

    f = C.finish(ask, d, variant="fp32", limits=LIMITS)
    f.stats = stats
    return f
