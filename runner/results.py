# -*- coding: utf-8 -*-
"""Aggregated results of one block: results/runs/<dataset_version>/<block>.json (+ .csv). Keyed by (dataset_version, id).

The per-question LOG (work/logs/...) is local and git-ignored; what is committed is this record: the conditions the block was measured
under, the model repository + tag, the providers that were really used, the tallies, and one CSV row per question.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import pathlib
import platform
import statistics
import sys

from . import config

COLUMNS = ["dataset_version", "id", "model", "lang", "kind", "expected", "got", "ok", "rev_ok", "ms"]


def results_dir(version: str) -> pathlib.Path:
    if os.environ.get("BENCH_RESULTS_RUNS"):          # e.g. results/runs/v1_localpc: results of another machine kept apart
        return pathlib.Path(os.environ["BENCH_RESULTS_RUNS"])
    return config.ROOT / "results" / "runs" / version


def manifest_ref() -> dict | None:
    """Which image list (manifest) the questions' pictures are described by: file name + sha256 of the file."""
    p = config.ROOT / "datasets" / "manifests" / "images_legacy.json"
    if not p.exists():
        return None
    return dict(file="datasets/manifests/" + p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def question_list_ref(version: str) -> dict | None:
    """The question list the run is keyed to (file name + sha256): datasets/manifests/questions_<version>.csv."""
    p = config.ROOT / "datasets" / "manifests" / ("questions_%s.csv" % version)
    if not p.exists():
        return None
    return dict(file="datasets/manifests/" + p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def tally(rows: list[dict]) -> dict:
    """rows: dict(id, kind, difficulty, ok, rev_ok, ms) -> counts overall and by kind / difficulty."""
    def acc(sel):
        return dict(n=len(sel), correct=sum(r["ok"] for r in sel), accuracy=round(sum(r["ok"] for r in sel) / len(sel), 4) if sel else None)
    out = dict(overall=acc(rows), by_kind={}, by_difficulty={})
    for k in sorted({r["kind"] for r in rows}):
        out["by_kind"][k] = acc([r for r in rows if r["kind"] == k])
    for d in sorted({str(r.get("difficulty")) for r in rows}):
        out["by_difficulty"][d] = acc([r for r in rows if str(r.get("difficulty")) == d])
    ch = [r for r in rows if r.get("rev_ok") is not None]
    if ch:
        out["choice_fwd_and_rev_both_correct"] = dict(n=len(ch), correct=sum(1 for r in ch if r["ok"] and r["rev_ok"]))
    ms = [r["ms"] for r in rows if r["ms"]]
    out["ms_median"] = int(statistics.median(ms)) if ms else None
    return out


def keep_earlier_host(rec: dict, path: pathlib.Path) -> dict:
    """A resumed block keeps the host its record already has (never overwritten). Resumed on another machine (other host_id): warn, and
    list that machine under host["also_resumed_on"]. An earlier record without a host: the new host is kept but marked, because the
    earlier part of the block was measured on an unknown machine."""
    if not rec.get("resumed") or not path.exists():
        return rec
    try:
        old = json.loads(path.read_text(encoding="utf-8")).get("host")
    except (OSError, ValueError):
        old = None
    new = rec.get("host")
    if not new:
        return rec
    if not old:
        rec["host"] = dict(new, earlier_session_host_unknown=True)
        print("warning: %s was resumed but its earlier record has no host: the earlier part was measured on an unknown machine" % path.name,
              file=sys.stderr, flush=True)
        return rec
    host = dict(old)
    if old.get("host_id") != new.get("host_id"):
        print("warning: %s was started on host %s (%s) and is resumed on host %s (%s): its times mix two machines"
              % (path.name, old.get("host_id"), old.get("label"), new.get("host_id"), new.get("label")), file=sys.stderr, flush=True)
        seen = host.get("also_resumed_on") or []
        if new.get("host_id") not in [x.get("host_id") for x in seen]:
            seen.append({k: new.get(k) for k in ("host_id", "label", "threads", "source")})
        host["also_resumed_on"] = seen
    rec["host"] = host
    return rec


def write(block: str, meta: dict, rows: list[dict]) -> pathlib.Path:
    """Write <block>.json and <block>.csv. ``meta`` carries the conditions; ``rows`` one dict per question."""
    d = results_dir(meta["dataset_version"])
    d.mkdir(parents=True, exist_ok=True)
    rec = dict(meta, python=platform.python_version(), manifest=manifest_ref(), question_list=question_list_ref(meta["dataset_version"]), counts=tally(rows))
    rec = keep_earlier_host(rec, d / (block + ".json"))
    (d / (block + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(d / (block + ".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([meta["dataset_version"], r["id"], meta["model"], meta["lang"], r["kind"], r["expected"], r["got"],
                        int(r["ok"]), "" if r.get("rev_ok") is None else int(r["rev_ok"]), r["ms"]])
    return d / (block + ".json")


def annotate_calibration(block: str, version: str, before: str, after: str, limit: int) -> None:
    """The batch adds the gate result to a finished block's record (the run itself does not calibrate)."""
    p = results_dir(version) / (block + ".json")
    if not p.exists():
        return
    rec = json.loads(p.read_text(encoding="utf-8"))
    ok = bool(before and after and max(int(before), int(after)) <= limit)
    rec["calibration"] = dict(before_ms=int(before) if before else None, after_ms=int(after) if after else None, limit_ms=limit,
                              timing_valid=ok)
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
