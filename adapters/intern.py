# -*- coding: utf-8 -*-
"""Intern-Decision 0.8B (ONNX, onnxruntime + numpy, own tokenizer) -> ``ask``.  Key: ``intern``.

Install:  the ``intern_decide`` package (``uv pip install git+https://github.com/<OWNER>/Intern-Decision-0.8B-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``INTERN_MODEL_DIR`` (the ``models/onnx`` folder); the tokenizer: ``INTERN_TOKENIZER_JSON``
(the ``tokenizer.json``; default: ``<model-dir>/../hf/tokenizer.json``).

Limits: at most 8 pictures per request, 16 questions (the bench asks one), choice up to 255 options. The shipped graph is fixed at
512 tokens (L=512): a 224 px picture fits, a larger one does not, which is why the bench feeds 224 px pictures (px = 224).
GPU: ``providers`` is passed through (the runtime supports it; the measurements so far ran this model on the CPU only).
"""
from __future__ import annotations

import os
import pathlib

from . import _common as C

LIMITS = dict(max_images=8, max_choice_options=255, max_score_levels=None, gpu=True, note="graph fixed at L=512 tokens: 224 px pictures only")


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="intern"):
    R = C.import_runtime("intern_decide", "uv pip install git+https://github.com/<OWNER>/Intern-Decision-0.8B-ONNX-CPU@<tag>")
    base = C.model_dir_of(model_dir, "INTERN_MODEL_DIR")
    tok = pathlib.Path(os.environ.get("INTERN_TOKENIZER_JSON") or base.parent / "hf" / "tokenizer.json")
    d = R.DecisionEngine(base, tokenizer_json=tok, intra_op_threads=threads, providers=providers)

    def ask(state, images, kind, instr, options):
        if kind == "noul":
            q = {"type": "noul", "instructions": instr, "criteria": {}}
        elif kind == "choice":
            q = {"type": "choice", "instructions": instr, "criteria": dict(options)}
        else:
            q = {"type": "score", "instructions": instr, "criteria": list(options)}
        req = {"state": state, "questions": {"q": q}}
        if images:
            req["images"] = images
        a = d.predict(req)["answers"]["q"]
        if kind == "noul":
            return a["decision"] in ("yes", True, "true")
        if kind == "choice":
            return [k for k, _ in options].index(a["decision"])
        return int(a["decision"])

    return C.finish(ask, d, variant="fp32", limits=LIMITS)
