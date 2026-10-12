# -*- coding: utf-8 -*-
"""d3 (Decision 3.0: d3-edge 0.6B / d3-lite 0.9B / d3-nano 2B; ONNX, onnxruntime + tokenizers + numpy) -> ``ask``.
Keys: ``d3edge``, ``d3lite``, ``d3nano``.  (d3-mini 5B is not supported: its fp32 export needs about 25 GB of RAM.)

Install:  the ``d3_decide`` package of D3-ONNX-CPU (one repository, one package, all three sizes):
    uv pip install git+https://github.com/Kazuhito00/D3-ONNX-CPU@<tag>
or a checkout on PYTHONPATH.
Model directory: ``--model-dir`` or ``D3_EDGE_MODEL_DIR`` / ``D3_LITE_MODEL_DIR`` / ``D3_NANO_MODEL_DIR`` (the repository's
``models/<size>`` folder: graphs in ``onnx/``, ``tokenizer.json``, ``decision_config.json`` ...).

One question is one forward pass over its own prompt (the options are listed under single-token codes). The graphs are fixed at one
of several token lengths (128 ... 2048); the runtime loads the smallest that holds the prompt and then only grows. A 224 px picture
becomes 256 x 256 pixels (the vendor's minimum, 64 tokens). Limits: choice up to 255 options, score 2 to 10 levels; any number of pictures
that fit the largest graph. Weights fp32.
"""
from __future__ import annotations

from . import _common as C

LIMITS = dict(max_images=None, max_choice_options=255, max_score_levels=10, gpu=True,
              note="graph fixed at one of 128/256/384/512/1024/2048 tokens per question (smallest that fits is loaded)")

#: key -> environment variable of the model directory
KEYS = {"d3edge": "D3_EDGE_MODEL_DIR", "d3lite": "D3_LITE_MODEL_DIR", "d3nano": "D3_NANO_MODEL_DIR"}


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="d3edge"):
    R = C.import_runtime("d3_decide", "uv pip install git+https://github.com/Kazuhito00/D3-ONNX-CPU@<tag>")
    base = C.model_dir_of(model_dir, KEYS[key])
    d = R.D3Engine(base, intra_op_threads=threads, providers=providers)

    def ask(state, images, kind, instr, options):
        return d.ask(state, images, kind, instr, options)

    return C.finish(ask, d, variant="fp32", limits=LIMITS)
