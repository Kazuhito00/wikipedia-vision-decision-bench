# -*- coding: utf-8 -*-
"""Find the models and runs of the v1 trial in a results folder (no hand-written model list).

    from report import v1_models
    runs = v1_models.discover_runs(results_dir)          # {run key: dict(model, suffix, device, files={lang: file stem})}
    models = v1_models.build_models(runs)                # [dict(key, name, short, kind, color, runs=[dict(key, label, device, files, ...)])]

A result file is ``<model>_v1all_<lang>_224<suffix>.json`` (+ the same stem with .csv), ``<lang>`` en|ja, ``<suffix>`` ``_cpu`` / ``_cuda`` /
nothing (a remote API). The run key is ``<model><suffix>`` (``jevision_cpu``, ``jevision_cuda``, ``openai``). Anything that is not an `all`
block, a smoke run (``_smoke`` in the suffix) or another pixel size than the first one found is ignored.

Display name, colour and kind (local / api) come from the default tables below; a model that is not in them gets its key as the name and the
next free colour, so a new model needs no configuration. ``set_names()`` lets a caller (colab/make_v1_report.py) pass the adapters' registry.
"""
from __future__ import annotations

import json
import pathlib
import re

LANGS = ("en", "ja")
STEM = re.compile(r"^(?P<model>[a-z0-9]+)_(?P<code>v1[a-z]+)_(?P<lang>en|ja)_(?P<px>\d+)(?P<suffix>.*)$")
DEVICE_LABEL = {"cpu": "CPU", "cuda": "GPU", "remote": "API"}
DEVICE_ORDER = {"cpu": 0, "cuda": 1, "remote": 2}

#: model key -> (display name, short name). Order = the order of the page. adapters.REGISTRY has the same names (kept in step by hand;
#: set_names() overrides these at run time).
NAMES = {
    "jevision": ("JEVision 0.8B", "JEVision"), "onejev": ("OneJev 0.8B", "OneJev 0.8B"), "onejev4": ("OneJev 4B", "OneJev 4B"),
    "openjev": ("OpenJev 0.8B", "OpenJev 0.8B"), "openjev4": ("OpenJev 4B", "OpenJev 4B"),
    "intern": ("Intern-Decision 0.8B", "Intern"), "strands": ("Strands Decider 2B", "Strands"), "clef": ("clef-flash 9B", "clef-flash"),
    "qev": ("QEV 2B", "QEV"), "d3edge": ("d3-edge 0.6B", "d3-edge"), "d3lite": ("d3-lite 0.9B", "d3-lite"), "d3nano": ("d3-nano 2B", "d3-nano"),
    "openai": ("OpenAI Decisions API", "OpenAI"),
}
#: a model that is an API (no device of its own); every other model is local. A run with no cpu/cuda suffix is "remote" either way.
API_MODELS = {"openai"}
#: fixed colours of the models seen so far (the first two keep the colours of the first version of the page)
COLORS = {"jevision": "#3b73d8", "openai": "#e0861a", "onejev": "#2a9d6f", "onejev4": "#1b6e4d", "openjev": "#6fb7a0", "openjev4": "#3d8b7a",
          "intern": "#8a5fc7", "strands": "#c0453f", "clef": "#b58900", "qev": "#2b9bb5", "d3edge": "#d2578f", "d3lite": "#a8643c",
          "d3nano": "#7f9c1e"}
#: for an unknown model: the next one that nobody uses
SPARE = ["#4c6ef5", "#12a594", "#6c7a89", "#e05d44", "#9467bd", "#8c8c3c", "#17a2b8", "#c2579a", "#5b8c3a", "#a35d8f", "#2f7fa8", "#b9772e"]
#: weight (download) size in GB where the repositories document one (colab/run_colab.py SPECS and the model READMEs). None = not documented.
#: These are approximate download sizes, not the memory a run needs. A run's json may carry "weights_gb" and then wins.
WEIGHT_GB = {"onejev": 2.9, "onejev4": 10, "intern": 4.1, "strands": 9.4, "clef": 21, "qev": 9.9, "d3edge": 2.6, "d3lite": 4.2, "d3nano": 9.3}


def set_names(registry: dict) -> None:
    """registry: runner key -> (module, display name) as in adapters.REGISTRY. Adds/overrides display names of the known keys."""
    for k, v in registry.items():
        name = v[1]
        if k in NAMES:
            NAMES[k] = (name, NAMES[k][1] if NAMES[k][0] == name else name)
        else:
            NAMES[k] = (name, name)


def device_of(suffix: str) -> str:
    return "cuda" if suffix.startswith("_cuda") else "cpu" if suffix.startswith("_cpu") else "remote"


def parse_stem(stem: str):
    """-> dict(model, code, lang, px, suffix, device) or None. ``code`` is the block (v1all, v1photo, v1biz, v1rsn, v1txt, v1new)."""
    m = STEM.match(stem)
    if not m or "_smoke" in m["suffix"]:
        return None
    d = m.groupdict()
    d["device"] = device_of(d["suffix"])
    return d


def discover_runs(runs_dir, code: str = "v1all") -> dict:
    """All runs with a json+csv `code` block in `runs_dir`. -> {run key: dict(model, suffix, device, px, files={lang: stem})}."""
    runs_dir = pathlib.Path(runs_dir)
    found: dict = {}
    for p in sorted(runs_dir.glob("*.json")):
        d = parse_stem(p.stem)
        if not d or d["code"] != code or not p.with_suffix(".csv").exists():
            continue
        key = d["model"] + d["suffix"]
        r = found.setdefault(key, dict(key=key, model=d["model"], suffix=d["suffix"], device=d["device"], px=d["px"], files={}))
        if r["px"] != d["px"]:                       # another picture size of the same run: the first one found (sorted) wins
            continue
        r["files"][d["lang"]] = p.stem
    return found


def _model_rank(model: str):
    order = list(NAMES)
    return (order.index(model), "") if model in order else (len(order), model)


def build_models(runs: dict, order: list | None = None) -> list:
    """Group runs by model, style them. -> [dict(key, name, short, kind, color, runs=[dict(key, label, device, files, weights_gb?)])]"""
    models: dict = {}
    for r in sorted(runs.values(), key=lambda r: (_model_rank(r["model"]), DEVICE_ORDER[r["device"]], r["key"])):
        mk = r["model"]
        if mk not in models:
            name, short = NAMES.get(mk, (mk, mk))
            kind = "api" if (mk in API_MODELS or r["device"] == "remote") else "local"
            models[mk] = dict(key=mk, name=name, short=short, kind=kind, color=None, runs=[])
        m = models[mk]
        dev = DEVICE_LABEL[r["device"]]
        label = ("%s %s" % (m["short"], dev)) if r["device"] != "remote" else ("%s API" % m["short"] if m["kind"] == "api" else m["short"])
        m["runs"].append(dict(key=r["key"], label=label, device=r["device"], files=dict(r["files"]), file_pattern=None))
    used = {COLORS[k] for k in models if k in COLORS}
    spare = [c for c in SPARE if c not in used]
    for k, m in models.items():
        m["color"] = COLORS.get(k) or (spare.pop(0) if spare else "#6c7a89")
        m["weights_gb"] = WEIGHT_GB.get(k)
    return list(models.values())


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
