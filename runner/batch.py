# -*- coding: utf-8 -*-
"""Batch of timed blocks (models x question groups x languages) behind the calibration gate. Resumable: finished blocks are skipped.

    uv run python -m runner.batch --models onejev,jevision --sets photo,biz,rsn --langs en,ja \\
        [--models-file runner/models.local.toml] [--log-dir work/logs/timed] [--gpu] [--lock PATH]

For every block, in order:
  1. skip it when its log already ends with the summary line;
  2. gate: run the calibration (runner/calibrate.py in the `calibration` environment of the models file) until its median is at most
     cal_limit_ms (up to cal_tries times, cal_wait_s apart);
  3. run `python -m runner.run` in the model's own environment (the `python` / `model_dir` / `env` of its table);
  4. calibrate again and append `<block> before=<ms> after=<ms> <HH:MM:SS>` to <log-dir>/blocks.log (the old format), and put the same
     numbers in the block's results/runs/... record.
A block whose before/after exceeds the limit is still logged (accuracy counts) but its times are marked invalid by the report.
Lock: with --lock PATH (or the HEAVY_LOCK environment variable) the whole batch holds the lock folder (mkdir / rmdir, atomic), so that
two heavy jobs never time each other; without it there is no locking.
Measurement conditions come from runner/config.toml (threads, px, rev); --gpu switches to CUDA providers.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
import time
import tomllib

from . import config, logfmt, results


def calibrate(models: dict) -> str:
    """-> the median ms as a string ('' when the calibration could not run)."""
    cal = models.get("calibration", {})
    py = cal.get("python", sys.executable)
    env = dict(os.environ, **cal.get("env", {}), PYTHONIOENCODING="utf-8")
    res = subprocess.run([py, "-m", "runner.calibrate"], cwd=config.ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    last = (res.stdout.strip().splitlines() or [""])[-1]
    m = re.search(r"median (\d+) ms", last)
    return m.group(1) if m else ""


def gate(models: dict, cfg: dict) -> str:
    g = cfg["gate"]
    c = ""
    for _ in range(g["cal_tries"]):
        c = calibrate(models)
        if c and int(c) <= g["cal_limit_ms"]:
            break
        time.sleep(g["cal_wait_s"])
    return c


class Lock:
    """The shared heavy lock: a folder made with mkdir (atomic) and removed at the end."""

    def __init__(self, path):
        self.path = pathlib.Path(path) if path else None

    def __enter__(self):
        if self.path:
            while True:
                try:
                    self.path.mkdir()
                    break
                except FileExistsError:
                    time.sleep(30)
        return self

    def __exit__(self, *exc):
        if self.path:
            try:
                self.path.rmdir()
            except OSError:
                pass


def main(argv=None) -> int:
    cfg = config.load()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", required=True, help="comma separated runner keys")
    ap.add_argument("--sets", default="photo,biz,rsn,txt")
    ap.add_argument("--langs", default="en,ja")
    ap.add_argument("--models-file", default=str(config.HERE / "models.local.toml"))
    ap.add_argument("--log-dir", default=str(config.work_dir() / "logs" / "timed"))
    ap.add_argument("--gpu", action="store_true", default=cfg["measure"]["gpu"])
    ap.add_argument("--lock", default=os.environ.get("HEAVY_LOCK"))
    ap.add_argument("--mod", default="image")
    ap.add_argument("--suffix", default="", help="appended to the block names (e.g. _cpu / _cuda: the same model on two devices)")
    ap.add_argument("--no-gate", action="store_true", help="skip the calibration (accuracy-only runs)")
    args = ap.parse_args(argv)

    mf = pathlib.Path(args.models_file)
    if not mf.exists():
        raise SystemExit("models file not found: %s (copy runner/models.example.toml to runner/models.local.toml)" % mf)
    models = tomllib.loads(mf.read_text(encoding="utf-8"))
    log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    px, version = cfg["measure"]["px"], cfg["dataset"]["version"]

    with Lock(args.lock):
        for key in args.models.split(","):
            if key not in models:
                raise SystemExit("no [%s] table in %s" % (key, mf))
            t = models[key]
            for set_name in args.sets.split(","):
                for lang in args.langs.split(","):
                    block = "%s_%s_%s_%d%s" % (key, cfg["blocks"][set_name], lang, px, args.suffix)
                    if logfmt.is_finished(log_dir / (block + ".log")):
                        continue
                    before = "" if args.no_gate else gate(models, cfg)
                    cmd = [t.get("python", sys.executable), "-m", "runner.run", "--model", key, "--set", set_name, "--lang", lang,
                           "--mod", args.mod, "--log-dir", str(log_dir)]
                    if args.suffix:
                        cmd += ["--suffix", args.suffix]
                    if t.get("model_dir"):
                        cmd += ["--model-dir", t["model_dir"]]
                    if args.gpu:
                        cmd.append("--gpu")
                    env = dict(os.environ, **t.get("env", {}), PYTHONIOENCODING="utf-8")
                    if "PATH_PREPEND" in t.get("env", {}):               # e.g. CUDA / cuDNN folders first
                        env["PATH"] = t["env"]["PATH_PREPEND"] + os.pathsep + env.get("PATH", "")
                    subprocess.run(cmd, cwd=config.ROOT, env=env)
                    after = "" if args.no_gate else calibrate(models)
                    with open(log_dir / "blocks.log", "a", encoding="utf-8", newline="\n") as f:
                        f.write("%s before=%s after=%s %s\n" % (block, before, after, time.strftime("%H:%M:%S")))
                    if not args.no_gate:
                        results.annotate_calibration(block, version, before, after, cfg["gate"]["cal_limit_ms"])
        (log_dir / "_done").write_text("FINISHED\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
