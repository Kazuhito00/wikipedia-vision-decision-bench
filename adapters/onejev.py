# -*- coding: utf-8 -*-
"""OneJev 0.8B / 4B (ONNX, onnxruntime + numpy) -> ``ask``.  Runner keys: ``onejev`` (0.8B) and ``onejev4`` (4B).

    from adapters import load
    ask = load("onejev", model_dir=..., threads=8, providers=None, lang="en", part="wiki")

Install:  the ``onejev_decide`` package of the OneJev repository (``uv pip install git+https://github.com/<OWNER>/OneJev-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``ONEJEV_MODEL_DIR`` (0.8B) / ``ONEJEV4_MODEL_DIR`` (4B): the folder with ``onnx/`` and the variant graphs.
Variant: fp16 (both sizes); override with ``variant=``.

Limits (the runtime's own checks, raised as ValueError -> the runner records got=NA):
  * choice: at most 255 options; score: at most 10 levels;
  * images: referenced from the state as ``<image:N>`` (this adapter builds the references); a limit on the number of pictures is not
    stated by the runtime (unconfirmed). The bench asks one picture per question.
Contract: see adapters/__init__.py. GPU: ``providers=["CUDAExecutionProvider", "CPUExecutionProvider"]`` is passed through.
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=None, max_choice_options=255, max_score_levels=10, gpu=True, note="image count limit not stated by the runtime")
MODEL_DIR_ENV = {"onejev": ("ONEJEV_MODEL_DIR",), "onejev4": ("ONEJEV4_MODEL_DIR",)}


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="onejev"):
    R = C.import_runtime("onejev_decide", "uv pip install git+https://github.com/<OWNER>/OneJev-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    variant = variant or "fp16"
    d = Decider(C.model_dir_of(model_dir, *MODEL_DIR_ENV[key]), variant=variant, intra_op_threads=threads,
                load_vision=C.needs_vision(part), providers=providers)

    def ask(state, images, kind, instr, options):
        if images:
            st = {("image%d" % (i + 1)): "<image:%d>" % (i + 1) for i in range(len(images))}
            st["context"] = state
        else:
            st = state
        if kind == "noul":
            q = noul(instr)
        elif kind == "choice":
            q = choice(instr, dict(options))
        else:
            q = score(instr, options)
        a = d.decide(st, {"q": q}, images=images or [])["q"]
        if kind == "noul":
            return a["noul"] > 0.5
        if kind == "choice":
            return [k for k, _ in options].index(a["choice"])
        p = a["probabilities"]
        keys = list(p)
        return keys.index(max(p, key=p.get))

    return C.finish(ask, d, variant=variant, limits=LIMITS)
