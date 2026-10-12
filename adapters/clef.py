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

LIMITS = dict(max_images=4, max_choice_options=None, max_score_levels=None, gpu=True,
              note="option limits not stated by the runtime; on CUDA the main graph runs with graph optimization disabled (onnxruntime Memcpy bug)")


def _cuda_graph_workaround():
    """On CUDA the main graph (model-fp32*.onnx) fails in onnxruntime 1.31 with `MemcpyToHost ... CUDA failure 1: invalid argument`
    (Colab A100, diagnosed with colab/diagnose_clef_cuda.py: every condition fails except graph_optimization_level = ORT_DISABLE_ALL;
    the CUDA output then equals the CPU output exactly). The runtime builds its own SessionOptions, so wrap its session factory:
    only for the main graph and only when a CUDA provider is requested. CPU runs are not touched."""
    import importlib

    import onnxruntime as ort
    rt = importlib.import_module("clef_decide.runtime")
    if getattr(rt._create_session, "_bench_wrapped", False):
        return
    orig = rt._create_session

    def wrapped(path, options, providers=None, require_gpu=False, **kw):
        if providers and any("CUDA" in str(p) for p in providers) and str(path).replace("\\", "/").rsplit("/", 1)[-1].startswith("model-fp32"):
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        return orig(path, options, providers, require_gpu, **kw)
    wrapped._bench_wrapped = True
    rt._create_session = wrapped


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="clef"):
    R = C.import_runtime("clef_decide", "uv pip install git+https://github.com/Kazuhito00/Clef-Flash-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    _cuda_graph_workaround()
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
