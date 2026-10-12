# -*- coding: utf-8 -*-
"""Diagnose why clef (Clef-Flash-ONNX-CPU) fails on CUDA in Colab (smoke: 25/25 "MemcpyToHost ... CUDA failure 1: invalid argument").

    python colab/diagnose_clef_cuda.py                 # all steps with the defaults
    python colab/diagnose_clef_cuda.py --download      # clone the repository / fetch the weights first when they are missing
    python colab/diagnose_clef_cuda.py --quick         # environment + the two first attempts only
    python colab/diagnose_clef_cuda.py --heavy         # also keep_bf16=False (needs ~36 GB fp32 in memory: only for a big machine)

(a) environment  (b) ONE question on CUDA with CUDA_LAUNCH_BLOCKING=1 and the ORT verbose log -> where does it fail
(c) the same question under other conditions (one fresh process per attempt, so memory is released and a dead CUDA context cannot leak)
(d) a hint for the verdict.  The raw logs of every attempt go to work/colab/diag_clef/NN_<name>.log; the summary to summary.json.

Nothing here changes the repositories: the clef runtime is imported from the checkout (Decider is not modified; onnxruntime.InferenceSession is wrapped
inside the attempt's own process only, to inject provider options / session options).
"""
from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "work" / "colab" / "diag_clef"
MARK = "DIAG_RESULT "
REPO_NAME = "Clef-Flash-ONNX-CPU"
STATE = "A product page with one large picture."
QUESTION = "What is the main color of the square in the picture?"
OPTIONS = {"red": None, "blue": None, "green": None}


def find_repo(arg: str | None) -> pathlib.Path | None:
    cands = [arg, os.environ.get("CLEF_REPO"), "/content/model_repos/" + REPO_NAME, str(ROOT.parent / "model_repos" / REPO_NAME), str(ROOT.parent / REPO_NAME)]
    for c in cands:
        if c and (pathlib.Path(c) / "clef_decide" / "runtime.py").exists():
            return pathlib.Path(c)
    return None


def model_dir_of(repo: pathlib.Path, arg: str | None) -> pathlib.Path:
    for c in (arg, os.environ.get("CLEF_MODEL_DIR")):
        if c:
            return pathlib.Path(c)
    return repo / "models" / "onnx"


def sh(cmd, timeout=30) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return (r.stdout or "").strip() if r.returncode == 0 else ""
    except Exception:        # noqa: BLE001
        return ""


# ------------------------------------------------------------------------------------------------------------ child: ONE attempt
def child_main(cond: dict) -> int:
    """Runs in its own process. Prints one `DIAG_RESULT {json}` line; the ORT log goes to stderr (the parent saves it)."""
    t_start = time.time()
    res = dict(name=cond["name"], ok=False, error="", stage="import")
    try:
        import numpy as np
        import onnxruntime as ort
        repo = pathlib.Path(cond["repo"])
        sys.path.insert(0, str(repo))
        sev = int(cond.get("log_sev", 2))
        ort.set_default_logger_severity(sev)
        info = dict(failed_session=None, feeds=None)
        real = ort.InferenceSession

        class Wrapped(real):                                                    # injects the attempt's options; remembers where run() failed
            def __init__(self, path, sess_options=None, providers=None, **kw):
                so = sess_options or ort.SessionOptions()
                so.log_severity_level = sev
                if sev == 0:
                    so.log_verbosity_level = 0
                lvl = cond.get("opt_level")
                if lvl:
                    so.graph_optimization_level = getattr(ort.GraphOptimizationLevel, lvl)
                if cond.get("no_mem_pattern"):
                    so.enable_mem_pattern = False
                if providers and cond.get("cuda_opts"):
                    providers = [(p, dict(cond["cuda_opts"])) if p == "CUDAExecutionProvider" else p for p in providers]
                self._diag_path = pathlib.Path(str(path)).name
                super().__init__(path, sess_options=so, providers=providers, **kw)

            def run(self, output_names, input_feed, *a, **k):
                try:
                    return super().run(output_names, input_feed, *a, **k)
                except Exception:
                    info["failed_session"] = self._diag_path
                    info["feeds"] = {n: "%s%s" % (getattr(v, "dtype", "?"), list(getattr(v, "shape", ()))) for n, v in list(input_feed.items())[:12]}
                    raise
        ort.InferenceSession = Wrapped

        import clef_decide as R
        from clef_decide.protocol import choice
        model_dir = pathlib.Path(cond["model_dir"])
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if cond["device"] == "cuda" else ["CPUExecutionProvider"]
        kw = dict(intra_op_threads=int(cond.get("threads", 8)), load_vision=bool(cond["load_vision"]), providers=providers,
                  require_gpu=bool(cond.get("require_gpu")))
        if "keep_bf16" in cond:
            kw["keep_bf16"] = bool(cond["keep_bf16"])
        res["stage"] = "load"
        t0 = time.time()
        d = R.Decider(model_dir, **kw)
        res["load_s"] = round(time.time() - t0, 1)
        res["providers"] = {k: v for k, v in d.providers_used.items()}
        res["stage"] = "run"
        img = cond.get("image")
        t0 = time.time()
        if cond["load_vision"]:
            out = d.decide(STATE, {"q": choice(QUESTION, OPTIONS)}, images=[img])
        else:
            out = d.decide("I was charged twice for one order.", {"q": choice("Which team should handle this?", {"billing": None, "tech": None})})
        res["run_s"] = round(time.time() - t0, 2)
        res["answer"] = out["q"]
        res["ok"] = True
        first = [v[0] for v in res["providers"].values() if v]
        if cond["device"] == "cuda" and any(p != "CUDAExecutionProvider" for p in first):
            res["ok"] = False
            res["error"] = "CPU fallback (the session did not use CUDA): %s" % res["providers"]
        res["failed_session"], res["feeds"] = info["failed_session"], info["feeds"]
    except BaseException as e:                                                  # noqa: BLE001
        import traceback
        res["error"] = ("%s: %s" % (type(e).__name__, e)).replace("\n", " ")[:2000]
        tb = traceback.extract_tb(e.__traceback__)
        res["where"] = " > ".join("%s:%d %s" % (pathlib.Path(f.filename).name, f.lineno, f.name) for f in tb[-4:])
        res["failed_session"], res["feeds"] = locals().get("info", {}).get("failed_session"), locals().get("info", {}).get("feeds")
    res["total_s"] = round(time.time() - t_start, 1)
    print(MARK + json.dumps(res, ensure_ascii=False, default=str), flush=True)
    return 0


# ------------------------------------------------------------------------------------------------------------ parent
def environment() -> dict:
    env = dict(python=sys.version.split()[0])
    for dist in ("onnxruntime", "onnxruntime-gpu", "numpy", "pillow", "onnx"):
        try:
            env[dist] = md.version(dist)
        except md.PackageNotFoundError:
            env[dist] = "-"
    nv = {}
    for d in md.distributions():
        n = (d.metadata["Name"] or "").lower()
        if n.startswith("nvidia-") and any(k in n for k in ("cudnn", "cuda-runtime", "cublas", "cuda-nvrtc", "cufft")):
            nv[n] = d.version
    env["nvidia_pip_wheels"] = nv
    try:
        import onnxruntime as ort
        env["ort_version_loaded"] = ort.__version__
        env["providers"] = ort.get_available_providers()
        env["ort_device"] = ort.get_device()
    except Exception as e:     # noqa: BLE001
        env["providers"] = "import failed: %s" % e
    q = sh(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader,nounits"])
    env["gpu"] = q or "nvidia-smi: not available (no GPU runtime?)"
    m = re.search(r"CUDA Version:\s*([\d.]+)", sh(["nvidia-smi"]))
    env["driver_cuda_version"] = m.group(1) if m else "?"
    env["nvcc"] = (sh(["nvcc", "--version"]).splitlines() or ["-"])[-1]
    try:
        import ctypes
        for name in ("libcudnn.so.9", "libcudnn.so.8", "libcudnn.so"):
            try:
                env["cudnn_loaded"] = "%s %s" % (name, ctypes.CDLL(name).cudnnGetVersion())
                break
            except OSError:
                continue
    except Exception:          # noqa: BLE001
        pass
    return env


def run_attempt(idx: int, cond: dict, timeout: int, extra_env: dict | None = None) -> dict:
    """One fresh process. The whole output (stdout + stderr = the ORT log) is saved; returns the result dict."""
    log = OUT / ("%02d_%s.log" % (idx, cond["name"]))
    env = dict(os.environ, PYTHONUNBUFFERED="1", **(extra_env or {}))
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), "--child", json.dumps(cond)]
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, start_new_session=(os.name != "nt"))
        try:
            p.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                if os.name != "nt":
                    import signal
                    os.killpg(p.pid, signal.SIGKILL)
                else:
                    p.kill()
            except Exception:    # noqa: BLE001
                p.kill()
            p.wait()
    res = dict(name=cond["name"], ok=False, error="", wall_s=round(time.time() - t0, 1), log=log.name, rc=p.returncode)
    last = None
    with open(log, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if ln.startswith(MARK):
                last = ln[len(MARK):]
    if last:
        res.update(json.loads(last))
        res["wall_s"] = round(time.time() - t0, 1)
    elif timed_out:
        res["error"] = "TIMEOUT after %d s (stage unknown; see %s)" % (timeout, log.name)
    else:
        tail = [x for x in open(log, encoding="utf-8", errors="replace").read().splitlines() if x.strip()][-3:]
        res["error"] = "process ended without a result (exit %s, killed / out of memory?): %s" % (p.returncode, " | ".join(tail))[:600]
    if timed_out and last:
        res["error"] = "TIMEOUT " + res.get("error", "")
    # the ORT [E: lines of the log: the first one, in full, is the best short summary of a CUDA failure
    if not res["ok"]:
        first_e = ""
        with open(log, encoding="utf-8", errors="replace") as f:
            for ln in f:
                if "[E:onnxruntime" in ln:
                    first_e = ln.strip()
                    break
        res["first_ort_error_line"] = first_e[:600]
    return res


def memcpy_context(log: pathlib.Path, node: str | None, limit: int = 12) -> list[str]:
    """Lines of a (verbose) ORT log around the failing node: its own mentions, and the CPU/CUDA placement summary lines."""
    if not log.exists():
        return []
    keep, placement = [], []
    with open(log, encoding="utf-8", errors="replace") as f:
        prev = []
        for ln in f:
            s = ln.rstrip()
            if node and node in s and not s.startswith(MARK):
                keep.extend(prev[-2:])
                keep.append(s)
            if "Node placements" in s or "placed on" in s:
                placement.append(s)
            prev = (prev + [s])[-3:]
            if len(keep) > 400:
                break
    out = []
    for s in keep + placement:
        s = s[:240]
        if s not in out:
            out.append(s)
    return out[:limit]


def fmt_table(rows: list[list[str]], head: list[str]) -> str:
    w = [max(len(str(r[i])) for r in rows + [head]) for i in range(len(head))]
    w[-1] = min(w[-1], 110)
    line = lambda r: "  ".join(str(c).ljust(w[i]) if i < len(w) - 1 else str(c)[:w[i]] for i, c in enumerate(r))
    return "\n".join([line(head), line(["-" * x for x in w])] + [line(r) for r in rows])


def numeric_leaves(x, prefix=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from numeric_leaves(v, prefix + "/" + str(k))
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield prefix, float(x)


def compare(a: dict, b: dict) -> str:
    da, db = dict(numeric_leaves(a)), dict(numeric_leaves(b))
    keys = [k for k in da if k in db]
    if not keys:
        return "no comparable numbers"
    return "max |diff| %.2e (CUDA vs CPU); top choice %s / %s" % (max(abs(da[k] - db[k]) for k in keys), a.get("choice"), b.get("choice"))


def make_image(repo: pathlib.Path) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "probe.png"
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (320, 240), (245, 245, 245))
    ImageDraw.Draw(im).rectangle([100, 60, 220, 180], fill=(220, 30, 30))
    im.save(p)
    return str(p)


def ensure_downloaded(args) -> pathlib.Path | None:
    repo = find_repo(args.repo)
    if repo is None and args.download:
        dest = pathlib.Path("/content/model_repos" if os.path.isdir("/content") else ROOT.parent / "model_repos") / REPO_NAME
        print("cloning https://github.com/%s/%s -> %s ..." % (args.owner, REPO_NAME, dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "clone", "--depth", "1", "https://github.com/%s/%s" % (args.owner, REPO_NAME), str(dest)], capture_output=True, text=True)
        if r.returncode != 0:
            print("clone failed:", (r.stderr or r.stdout).strip()[-300:])
            return None
        repo = dest
    if repo is not None and args.download and not (model_dir_of(repo, args.model_dir) / "model-fp32-vl.onnx").exists():
        print("fetching the weights (download_model.py --tag %s, about 20 GB, several minutes) ..." % args.tag)
        subprocess.run([sys.executable, "download_model.py"] + (["--tag", args.tag] if args.tag else []), cwd=repo)
    return repo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--child", help=argparse.SUPPRESS)
    ap.add_argument("--repo", help="Clef-Flash-ONNX-CPU checkout (default: auto: $CLEF_REPO, /content/model_repos/..., ../model_repos/..., ../Clef-Flash-ONNX-CPU)")
    ap.add_argument("--model-dir", help="weights folder (default: $CLEF_MODEL_DIR, else <repo>/models/onnx)")
    ap.add_argument("--download", action="store_true", help="clone the repository / run download_model.py when they are missing")
    ap.add_argument("--owner", default="Kazuhito00")
    ap.add_argument("--tag", default="v0.0.0", help="release tag for download_model.py (the notebook's RELEASE_TAG)")
    ap.add_argument("--attempt-timeout", type=int, default=240, help="seconds per attempt (loading 18 GB of weights alone can take a minute or two)")
    ap.add_argument("--total-timeout", type=int, default=1200, help="seconds for all attempts together; the rest is skipped")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--quick", action="store_true", help="environment + the first two attempts only")
    ap.add_argument("--heavy", action="store_true", help="also try keep_bf16=False (about 36 GB fp32 in memory)")
    ap.add_argument("--dry-run", action="store_true", help="print the attempts and stop (nothing is loaded)")
    args = ap.parse_args()
    if args.child:
        return child_main(json.loads(args.child))

    OUT.mkdir(parents=True, exist_ok=True)
    print("=== (a) environment ===")
    env = environment()
    for k, v in env.items():
        print("  %-20s %s" % (k, v))
    repo = ensure_downloaded(args)
    if repo is None:
        print("\nThe clef repository was not found. Fetch it first, e.g.:\n"
              "  python colab/diagnose_clef_cuda.py --download\n"
              "or  python colab/run_colab.py --steps bench --models clef --devices cpu --smoke 1 --sample 1   (clones + downloads the weights)")
        return 2
    mdir = model_dir_of(repo, args.model_dir)
    have = (mdir / "model-fp32-vl.onnx").exists() and (mdir / "vision_encoder.onnx").exists()
    print("  clef repo            %s\n  model dir            %s (%s)" % (repo, mdir, "weights present" if have else "WEIGHTS MISSING"))
    if not have and not args.dry_run:
        print("\nThe weights are missing: run with --download (about 20 GB) or fetch them with `python download_model.py --tag %s` in the repository." % args.tag)
        return 2
    if isinstance(env.get("providers"), list) and "CUDAExecutionProvider" not in env["providers"] and not args.dry_run:
        print("\nCUDAExecutionProvider is not offered by this onnxruntime: install onnxruntime-gpu (run_colab.py --steps setup). Nothing to diagnose.")
        return 2

    img = make_image(repo)
    base = dict(repo=str(repo), model_dir=str(mdir), device="cuda", load_vision=True, threads=args.threads, image=img, log_sev=2)
    attempts = [
        ("baseline_as_bench", dict(base), {}),                                                                 # what the bench ran (providers=[CUDA, CPU], vision on)
        ("blocking_verbose", dict(base, log_sev=0), {"CUDA_LAUNCH_BLOCKING": "1"}),                           # pins the failing kernel / copy
        ("text_only_no_vision", dict(base, load_vision=False), {}),
        ("require_gpu", dict(base, require_gpu=True), {}),
        ("arena_same_as_requested", dict(base, cuda_opts={"arena_extend_strategy": "kSameAsRequested"}), {}),
        ("no_mem_pattern", dict(base, no_mem_pattern=True), {}),
        ("conv_algo_default", dict(base, cuda_opts={"cudnn_conv_algo_search": "DEFAULT"}), {}),
        ("conv_algo_heuristic", dict(base, cuda_opts={"cudnn_conv_algo_search": "HEURISTIC"}), {}),
        ("gpu_mem_limit_30GB", dict(base, cuda_opts={"gpu_mem_limit": 30 * 1024 ** 3}), {}),
        ("copy_in_own_stream", dict(base, cuda_opts={"do_copy_in_default_stream": 0}), {}),
        ("tf32_off", dict(base, cuda_opts={"use_tf32": 0}), {}),
        ("opt_basic", dict(base, opt_level="ORT_ENABLE_BASIC"), {}),
        ("opt_disable_all", dict(base, opt_level="ORT_DISABLE_ALL"), {}),
    ]
    if args.heavy:
        attempts.append(("keep_bf16_off", dict(base, keep_bf16=False), {}))
    if args.quick:
        attempts = attempts[:2]
    if args.dry_run:
        print("\n=== attempts (dry run: nothing executed) ===")
        for i, (n, c, e) in enumerate(attempts):
            print("  %02d %-26s %s" % (i, n, json.dumps({k: v for k, v in c.items() if k not in ("repo", "model_dir", "image")}) + (" env=%s" % e if e else "")))
        print("  +  cpu_reference (only when some CUDA attempt succeeds)")
        return 0

    print("\n=== (b)(c) attempts (each in a fresh process; log -> %s) ===" % OUT)
    t_all = time.time()
    results: list[dict] = []
    for i, (name, cond, extra) in enumerate(attempts):
        cond["name"] = name
        left = args.total_timeout - (time.time() - t_all)
        if left < 30:
            results.append(dict(name=name, ok=None, error="skipped (total time limit %d s reached)" % args.total_timeout))
            continue
        print("  [%02d/%02d] %s ..." % (i + 1, len(attempts), name), flush=True)
        r = run_attempt(i, cond, int(min(args.attempt_timeout, left)), extra)
        r["blocking"] = bool(extra)
        results.append(r)
        print("        -> %s (%.0f s)%s" % ("OK" if r["ok"] else "FAIL", r.get("wall_s", 0), "" if r["ok"] else ": " + (r.get("error") or r.get("first_ort_error_line", ""))[:160]), flush=True)
        if i == 0 and r["ok"] and not args.quick:
            print("        the bench's failure was NOT reproduced by the baseline: the remaining attempts are skipped")
            break
    oks = [r for r in results if r["ok"]]
    cpu = None
    if oks and (time.time() - t_all) < args.total_timeout - 60:
        print("  [cpu] reference run on the CPU (about a minute to a few minutes) ...", flush=True)
        cpu = run_attempt(len(attempts), dict(base, name="cpu_reference", device="cpu", log_sev=3), min(args.attempt_timeout * 2, 600))
        print("        -> %s" % ("OK" if cpu["ok"] else "FAIL: " + cpu.get("error", "")[:160]))

    rows = []
    for i, r in enumerate(results):
        prov = ""
        if r.get("providers"):
            prov = "+".join(sorted({v[0].replace("ExecutionProvider", "") for v in r["providers"].values() if v}))
        st = "OK" if r["ok"] else ("SKIP" if r["ok"] is None else "FAIL")
        err = (r.get("error") or r.get("first_ort_error_line") or "").replace("\n", " ")
        rows.append(["%02d" % i, r["name"], st, "%s" % r.get("load_s", "-"), "%s" % r.get("run_s", "-"), prov or "-", err])
    print("\n=== table ===")
    print(fmt_table(rows, ["#", "condition", "result", "load s", "run s", "providers", "first error"]))

    first_fail = next((r for r in results if r["ok"] is False), None)
    print("\n=== first error (full) ===")
    if first_fail:
        print("  attempt  : %s" % first_fail["name"])
        print("  python   : %s" % (first_fail.get("error") or "-")[:600])
        if first_fail.get("first_ort_error_line"):
            print("  ORT log  : %s" % first_fail["first_ort_error_line"])
        print("  stage    : %s   where: %s" % (first_fail.get("stage", "?"), first_fail.get("where", "-")))
        print("  session  : %s   inputs: %s" % (first_fail.get("failed_session") or "-", first_fail.get("feeds") or "-"))
        bv = next((r for r in results if r["name"] == "blocking_verbose" and r["ok"] is False), None)
        if bv:
            print("  CUDA_LAUNCH_BLOCKING=1 (synchronous: the error is reported at the call that really failed):")
            print("    error  : %s" % (bv.get("error") or "-")[:400])
            node = None
            m = re.search(r"Name:'([^']+)'", bv.get("error", "") + (bv.get("first_ort_error_line") or ""))
            node = m.group(1) if m else None
            for s in memcpy_context(OUT / bv["log"], node):
                print("    log    : " + s)
            if node:
                print("    node   : %s = a Memcpy node ORT inserted between a CUDA op and a CPU-only op (the log lines above name the neighbours; "
                      "with verbose logging the placement summary lists what was left on the CPU)" % node)
    else:
        print("  no attempt failed.")

    print("\n=== (d) hint ===")
    real = [r for r in results if r["ok"] is not None]
    if oks:
        print("  CUDA works under: %s" % ", ".join(r["name"] for r in oks))
        if results[0]["ok"]:
            print("  The baseline passed: the bench's failure was not reproduced here (a different ORT / runtime state? re-run the notebook smoke with --recheck).")
        else:
            print("  -> use the passing condition(s) for clef on CUDA (e.g. pass the provider option / session option; needs a clef adapter / runtime change in the bench).")
        if cpu and cpu["ok"]:
            for r in oks:
                print("  CUDA vs CPU [%s]: %s" % (r["name"], compare(r.get("answer", {}), cpu.get("answer", {}))))
    elif real and all(r["ok"] is False for r in real):
        n = len(real)
        print("  All %d attempts failed%s: clef is not supported on this Colab CUDA setup (use the CPU device only for clef)." % (n, "" if n == len(results) else " (the rest skipped by the time limit)"))
        print("  Share the first error above and %s with the model's author (the failure is in the CUDA copy of a graph node, not memory)." % (OUT / "01_blocking_verbose.log"))
        msg = " ".join((r.get("error") or "") + (r.get("first_ort_error_line") or "") for r in real)
        if re.search(r"out of memory|cudaErrorMemoryAllocation|bad_alloc", msg, re.I):
            print("  Some errors look like out of memory: check nvidia-smi for other processes holding VRAM (restart the runtime) and retry.")
    else:
        print("  inconclusive (attempts skipped / timed out): raise --total-timeout or run with --quick.")

    summary = dict(env=env, repo=str(repo), model_dir=str(mdir), results=results, cpu_reference=cpu, elapsed_s=round(time.time() - t_all))
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nlogs and summary.json: %s (%.0f s)" % (OUT, time.time() - t_all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
