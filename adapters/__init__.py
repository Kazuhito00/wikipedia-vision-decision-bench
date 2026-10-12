# -*- coding: utf-8 -*-
"""Adapters: the only place where the bench meets a model.

One calling convention for every model (one module per model; the 0.8B and 4B sizes of a family share a module):

    from adapters import load
    ask = load("onejev", model_dir=None, threads=8, providers=None, lang="en", part="wiki")
    got = ask(state, images, kind, instr, options)

``load`` calls the module's ``build(model_dir, threads, providers, lang, part, variant, key)``; it returns ``ask`` with ``ask.info``
(variant, providers actually used, the model's limits) for the results record.

ask(state, images, kind, instr, options)
    state    str                                       the evidence text ("Look at the attached photograph." for picture questions)
    images   list of picture file paths (224 px)       [] for a text-only question; the bench asks ONE picture per question
    kind     "noul" | "choice" | "score"               yes/no | pick one of the options | graded level
    instr    str                                       the question
    options  choice: [(key, text), ...]   score: [level label, ...]   noul: None
returns
    noul     bool   (p(yes) > 0.5)
    choice   int    index into ``options`` of the most probable option
    score    int    index of the most probable level
A request beyond the model's limits raises ValueError; the runner records it as got=NA (counted wrong), except QEV's more-than-one-picture
case, which is out of scope (not run, not scored).

Where the model is: the model's own package must be installed in the environment that runs this (``uv pip install`` from its repository,
or a checkout on PYTHONPATH), and its model files are given by ``--model-dir`` or the model's environment variable (see each module).
GPU: ``providers`` = ``adapters._common.GPU_PROVIDERS`` (CUDA, CPU last); None = CPU.
kev is not part of this bench (no picture input): there is no adapter for it.
"""
from __future__ import annotations

import importlib

from ._common import GPU_PROVIDERS  # noqa: F401

#: runner key -> (module, display name). Keys are the ones the log names and the report use.
REGISTRY = {
    "onejev": ("onejev", "OneJev 0.8B"),
    "onejev4": ("onejev", "OneJev 4B"),
    "openjev": ("openjev", "OpenJev 0.8B"),
    "openjev4": ("openjev", "OpenJev 4B"),
    "intern": ("intern", "Intern-Decision 0.8B"),
    "strands": ("strands", "Strands Decider 2B"),
    "clef": ("clef", "clef-flash 9B"),
    "jevision": ("jevision", "JEVision 0.8B"),
    "qev": ("qev", "QEV 2B"),
    "d3edge": ("d3", "d3-edge 0.6B"),
    "d3lite": ("d3", "d3-lite 0.9B"),
    "d3nano": ("d3", "d3-nano 2B"),
    "openai": ("openai_decisions", "OpenAI Decisions API"),
}
#: model repository the runtime comes from (recorded with the results; "<OWNER>" is a placeholder until the repositories exist)
REPOS = {
    "onejev": "<OWNER>/OneJev-ONNX-CPU", "onejev4": "<OWNER>/OneJev-ONNX-CPU",
    "openjev": "<OWNER>/OpenJev-ONNX-CPU", "openjev4": "<OWNER>/OpenJev-ONNX-CPU",
    "intern": "<OWNER>/Intern-Decision-0.8B-ONNX-CPU", "strands": "<OWNER>/Strands-Decider-2B-ONNX-CPU", "clef": "<OWNER>/clef-flash-ONNX-CPU",
    "jevision": "<OWNER>/JEVision-0.8B-ONNX-CPU", "qev": "<OWNER>/QEV-2B-ONNX-CPU",
    "d3edge": "Kazuhito00/D3-ONNX-CPU", "d3lite": "Kazuhito00/D3-ONNX-CPU", "d3nano": "Kazuhito00/D3-ONNX-CPU",   # d3-mini 5B: not supported (export needs ~25 GB RAM)
    "openai": "https://api.openai.com/v1/decisions (remote API)",
}


def module_of(key: str):
    if key == "kev":
        raise SystemExit("kev is not part of the picture bench (it takes no images): no adapter")
    if key not in REGISTRY:
        raise SystemExit("unknown model %r; choose one of %s" % (key, ", ".join(REGISTRY)))
    return importlib.import_module("." + REGISTRY[key][0], __name__)


def load(key: str, model_dir=None, threads: int = 8, providers=None, lang: str = "en", part: str = "wiki", variant=None):
    return module_of(key).build(model_dir=model_dir, threads=threads, providers=providers, lang=lang, part=part, variant=variant, key=key)


def limits(key: str) -> dict:
    """The model's limits without loading it (image count, choice options, score levels)."""
    return dict(module_of(key).LIMITS)
