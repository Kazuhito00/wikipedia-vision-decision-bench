# -*- coding: utf-8 -*-
"""Strands Decider 2B (ONNX, onnxruntime + numpy; Qwen3.5-2B-Base + LoRA) -> ``ask``.  Key: ``strands``.

Install:  the ``strands_decide`` package (``uv pip install git+https://github.com/<OWNER>/Strands-Decider-2B-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``STRANDS_MODEL_DIR`` (the ``models/onnx`` folder).

Limits: at most 4 pictures per request (longer side scaled to 448 px inside the runtime), choice 2..255 options, score 2..10 levels.
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=4, max_choice_options=255, max_score_levels=10, gpu=True, note="")


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="strands"):
    R = C.import_runtime("strands_decide", "uv pip install git+https://github.com/<OWNER>/Strands-Decider-2B-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    # the measurements used the runtime's default for load_vision (kept: the runtime decides from the images it is given)
    d = Decider(C.model_dir_of(model_dir, "STRANDS_MODEL_DIR"), intra_op_threads=threads, providers=providers)

    def ask(state, images, kind, instr, options):
        if kind == "noul":
            a = d.decide(state, {"q": noul(instr)}, images=images)["q"]
            return a["noul"] > 0.5
        if kind == "choice":
            a = d.decide(state, {"q": choice(instr, {k: "" for k, _ in options})}, images=images)["q"]
            return [k for k, _ in options].index(a["choice"])
        a = d.decide(state, {"q": score(instr, options)}, images=images)["q"]
        p = a["probabilities"]
        return int(max(p, key=p.get))

    return C.finish(ask, d, variant="fp32", limits=LIMITS)
