# -*- coding: utf-8 -*-
"""Measurement settings: runner/config.toml, overridden by the environment (THREADS, PX, REV, GPU), then by the command line."""
from __future__ import annotations

import os
import pathlib
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG_PATH = HERE / "config.toml"


def load() -> dict:
    cfg = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    m = cfg["measure"]
    env = os.environ
    if env.get("THREADS"):
        m["threads"] = int(env["THREADS"])
    if env.get("PX"):
        m["px"] = int(env["PX"])
    if env.get("REV") is not None and env.get("REV") != "":
        m["rev"] = int(env["REV"])
    if env.get("GPU"):
        m["gpu"] = env["GPU"] == "1"
    return cfg


def work_dir() -> pathlib.Path:
    """Local, git-ignored working folder (logs, 224 px pictures, API cache, dist). ``BENCH_WORK`` moves it."""
    return pathlib.Path(os.environ.get("BENCH_WORK") or ROOT / "work")


def data_root() -> pathlib.Path:
    """The folder that contains ``data/`` (linked.jsonl, synthetic.jsonl, reasoning.jsonl, images/, synthetic/, reasoning/, passages.json).
    ``WIKIQA_DATA_ROOT`` points it elsewhere (for example at a checkout of the old wiki_qa/ folder)."""
    return pathlib.Path(os.environ.get("WIKIQA_DATA_ROOT") or work_dir())
