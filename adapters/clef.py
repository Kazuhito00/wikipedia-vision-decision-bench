# -*- coding: utf-8 -*-
"""clef-flash 9B (ONNX graph + the official safetensors by offset; onnxruntime + numpy) -> ``ask``.  Key: ``clef``.

Install:  the ``clef_decide`` package (``uv pip install git+https://github.com/Kazuhito00/Clef-Flash-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``CLEF_MODEL_DIR`` (the ``models/onnx`` folder).
Memory: a 9B model (bf16 weights read by offset, fp32 compute): plan for a large RAM; do not run it next to another heavy job.

Limits: at most 4 pictures per request (longer side scaled to 448 px inside the runtime). Option limits: not stated by the runtime
(unconfirmed). The vision tower is always loaded (``load_vision=True``: every request, text too, goes through the VL graph).
Options are sent without descriptions (criteria values None), which clef's encoder leaves out of the option text.
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=4, max_choice_options=None, max_score_levels=None, gpu=True, note="option limits not stated by the runtime")


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="clef"):
    R = C.import_runtime("clef_decide", "uv pip install git+https://github.com/Kazuhito00/Clef-Flash-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    d = Decider(C.model_dir_of(model_dir, "CLEF_MODEL_DIR"), intra_op_threads=threads, load_vision=True, providers=providers)

    def ask(state, images, kind, instr, options):
        if kind == "noul":
            a = d.decide(state, {"q": noul(instr)}, images=images)["q"]
            return a["noul"] > 0.5
        if kind == "choice":
            a = d.decide(state, {"q": choice(instr, {k: None for k, _ in options})}, images=images)["q"]
            return [k for k, _ in options].index(a["choice"])
        a = d.decide(state, {"q": score(instr, options)}, images=images)["q"]
        p = a["probabilities"]
        return int(max(p, key=p.get))

    return C.finish(ask, d, variant="bf16->fp32", limits=LIMITS)
