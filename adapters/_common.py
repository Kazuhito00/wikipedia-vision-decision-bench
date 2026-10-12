# -*- coding: utf-8 -*-
"""Helpers shared by the adapters (no model code in here)."""
from __future__ import annotations

import importlib
import os
import pathlib

#: what ``--gpu`` asks for: CUDA first, CPU last as the fallback (a graph that does not fit on a small GPU runs on the CPU, with a warning)
GPU_PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]
VISION_PARTS = ("image", "real", "wiki", "vision")


def needs_vision(part: str) -> bool:
    """The runtimes load their vision tower only when asked: every part except ``text`` runs pictures."""
    return part in VISION_PARTS


def model_dir_of(model_dir, *env_names: str) -> pathlib.Path:
    """Where the model's files are: the argument, else the first set environment variable. There is no default path on purpose."""
    if model_dir:
        return pathlib.Path(model_dir)
    for name in env_names:
        if os.environ.get(name):
            return pathlib.Path(os.environ[name])
    raise SystemExit("model directory not given: pass --model-dir or set %s" % " / ".join(env_names))


def import_runtime(module: str, install_hint: str):
    """Import the model's runtime package; a clear message when it is not installed in this environment."""
    try:
        return importlib.import_module(module)
    except ImportError as e:
        raise SystemExit("cannot import %r (%s).\nInstall the model package into this environment (%s), or put a checkout on "
                         "PYTHONPATH for a local run." % (module, e, install_hint))


def used_providers(decider) -> list[str]:
    """Best effort: the execution providers the decider's onnxruntime sessions actually use (first provider of each session,
    de-duplicated). Empty when it cannot be found."""
    found: list[str] = []
    seen = set()

    def visit(obj, depth=0):
        if id(obj) in seen or depth > 2:
            return
        seen.add(id(obj))
        if hasattr(obj, "get_providers"):
            try:
                p = obj.get_providers()[0]
                if p not in found:
                    found.append(p)
            except Exception:      # noqa: BLE001
                pass
            return
        for v in list(getattr(obj, "__dict__", {}).values()):
            if hasattr(v, "get_providers") or hasattr(v, "__dict__"):
                visit(v, depth + 1)
    visit(decider)
    return found


def finish(ask, decider, **info):
    """Attach what the runner records about this model to the ask callable."""
    ask.decider = decider
    ask.info = dict(info, providers_used=used_providers(decider))
    return ask
