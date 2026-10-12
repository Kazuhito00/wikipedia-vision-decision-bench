# -*- coding: utf-8 -*-
"""OpenJev 0.8B / 4B (ONNX, onnxruntime + numpy; stock Qwen3.5 behind a typed-decision prompt) -> ``ask``.  Keys: ``openjev``, ``openjev4``.

Install:  the ``openjev_decide`` package of the OpenJev repository (``uv pip install git+https://github.com/<OWNER>/OpenJev-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``OPENJEV_MODEL_DIR`` (0.8B) / ``OPENJEV4_MODEL_DIR`` (4B).
Variant: fp16 for 0.8B, q4f16 for 4B (the variants the measurements used); override with ``variant=``.

Limits: choice labels at most 255 (the runtime's ``max_labels``); images: no stated limit (unconfirmed), one picture per question here.
The yes/no words go into the question: "yes"/"no" for en, the Japanese yes/no words for ja (so the ``lang`` argument matters here).
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=None, max_choice_options=255, max_score_levels=None, gpu=True, note="image count and score level limits not stated by the runtime")
MODEL_DIR_ENV = {"openjev": ("OPENJEV_MODEL_DIR",), "openjev4": ("OPENJEV4_MODEL_DIR",)}
DEFAULT_VARIANT = {"openjev": "fp16", "openjev4": "q4f16"}
YES_NO = {"en": ("yes", "no"), "ja": ("はい", "いいえ")}


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="openjev"):
    R = C.import_runtime("openjev_decide", "uv pip install git+https://github.com/<OWNER>/OpenJev-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    variant = variant or DEFAULT_VARIANT[key]
    d = Decider(C.model_dir_of(model_dir, *MODEL_DIR_ENV[key]), variant=variant, intra_op_threads=threads, providers=providers)

    def ask(state, images, kind, instr, options):
        if kind == "noul":
            yes, no = YES_NO["en" if lang == "en" else "ja"]
            q = noul("q", yes, no, instr)
        elif kind == "choice":
            q = choice("q", dict(options), instr)
        else:
            q = score("q", options, instr)
        a = d.decide(state, [q], images=images or ())[0]
        if kind == "noul":
            return a.label == "true"
        if kind == "choice":
            return [k for k, _ in options].index(a.label)
        return int(a.label)

    return C.finish(ask, d, variant=variant, limits=LIMITS)
