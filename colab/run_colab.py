# -*- coding: utf-8 -*-
"""Run wikipedia-vision-decision-bench on Google Colab (also usable on any Linux box). Standard library only, so it runs before anything is installed.

One-stop (what the notebook does, in one command):

    python colab/run_colab.py --steps setup,images,bench,report --models all --devices auto

Steps (--steps, comma separated; default setup,images,bench,report):
  env      print the runtime (GPU, CUDA version, RAM, disk, onnxruntime) and write work/colab/env.json
  setup    install dependencies with uv (`uv pip install --system`): pillow, numpy, onnxruntime-gpu (or onnxruntime), tokenizers (d3 only)
  images   get images-224px.zip: --images-zip / Drive cache (only with --use-drive) / --images-url / the bench repository's GitHub Release (default:
           <owner>/wikipedia-vision-decision-bench, tag v0.0.0, like the models' download_model.py); SHA256SUMS or --images-sha256 is checked,
           split parts are joined, an interrupted download resumes; extract, check every question's picture exists
  bench    per model, in order: clone the model repository -> download the weights -> for each device (cpu, cuda): smoke -> full blocks
           -> (cuda without cpu only, --cpu-speed-n N > 0) CPU SPEED REFERENCE: the same N questions for every model on the CPU, after the cuda
           blocks of that model -> (optionally) delete the weights.  A model that cannot be fetched / does not fit / falls back to the CPU is
           SKIPPED and listed at the end; the others continue.  Resumable: finished blocks are skipped, an interrupted block continues from its log.
  report   summary of every result (markdown / csv / html), the v1 report page when its inputs exist, a zip bundle for download
  sync     copy logs + results to / from Google Drive (only with --use-drive; also done every --sync-min minutes while a block runs)
  plan     print the plan only (no network, no install, no GPU needed).  --dry-run does the same for any steps.

Google Drive is OFF by default (no mount, no sync, no cache, no restore): results and logs stay on the local disk and `report` makes a zip to download.
Pass --use-drive (the notebook: USE_DRIVE = True) to use Drive.  Everything is cloned by default (--models all: every repository, shared ones once; weights via
download_model.py; with --weights auto they are deleted after each model only when they do not all fit the disk).

Secrets: GITHUB_TOKEN (private repositories) and OPENAI_API_KEY (the openai model) are read from the environment ONLY; the notebook fills
them from Colab Secrets. They are never printed, never written to a file, never put in a URL.
Block names / results are the bench's own (runner/run.py): results/runs/v1/<model>_<set code>_<lang>_224_<cpu|cuda>.json.
CPU speed reference (a GPU-only run, --devices cuda): a few questions per model are also solved on the CPU, only to give a time per question
(results/runs/v1/<model>_<set code>_<lang>_224_cpu_speed<N>.json, speed_only: true; never part of an accuracy table, see report/v1_models.py).
CPU times on Colab are REFERENCE values: the machine is not the one the calibration gate (runner/calibrate.py) was set up on.
"""
from __future__ import annotations

import argparse
import base64
import collections
import csv
import datetime
import hashlib
import html
import json
import os
import pathlib
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GB = 1024 ** 3

# ----------------------------------------------------------------------------------------------------------- model table
# ONE place to add a model: an entry here (+ its adapter in adapters/ and the notebook's MODELS list).
#   repo       GitHub repository name under --owner (download_model.py's DEFAULT_REPO / the local checkout name; "-" = none)
#   shared     key of the entry that owns the checkout/download (onejev + onejev4 share one repository; d3edge + d3lite + d3nano share one).
#              The owner's disk_gb is the size of the WHOLE download, the members have 0. The download runs once; every member's model_dir is marked.
#   model_dir  weights folder inside the checkout after the download
#   download   argv of the download script inside the checkout (None: use download_model.py when the clone has one, else --model-dir KEY=PATH). Run WITHOUT model arguments = every model of the repository
#   disk_gb    what the weights take (source in `src`), ram_gb / vram_gb: minimum that the repository documents (None: not documented)
#   cpu_s      median seconds per question on the author's PC, CPU 8 threads (bench README) -> only used for the time ESTIMATE
SPECS = {
    "jevision": dict(repo="JEVision-ONNX-CPU", model_dir="models/jevision", download=["download_model.py", "--variant", "fp16"], disk_gb=None, ram_gb=None,
                     vram_gb=None, cpu_s=0.73, gpu_s=0.075, src="local models/jevision (all variants) = 7.6 GB; fp16 only: unconfirmed"),
    "onejev": dict(repo="OneJev-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=13, ram_gb=None, vram_gb=None, cpu_s=1.2, gpu_s=0.087,
                   src="download_model.py with no arguments fetches BOTH sizes (0.8B + 4B, about 13 GB, one download shared with onejev4); 4B needs about 10 GB of RAM"),
    "onejev4": dict(repo="OneJev-ONNX-CPU", shared="onejev", model_dir="models/onnx-4b", download=["download_model.py"], disk_gb=0, ram_gb=None, vram_gb=None, cpu_s=6.8,
                    gpu_s=None, src="same repository and download as onejev (counted there); weights in models/onnx-4b (fp16, about 10 GB)"),
    "intern": dict(repo="Intern-Decision-0.8B-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=4.1, ram_gb=6, vram_gb=3.3,
                   cpu_s=3.4, gpu_s=None, src="README: release 4.1 GB, peak RAM 5.4-6.1 GB (L<=512), fp32 weights 3.3 GB"),
    "strands": dict(repo="Strands-Decider-2B-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=9.4, ram_gb=8, vram_gb=7.7,
                    cpu_s=None, gpu_s=None, src="README: release 9.4 GB (+7.5 GB temporary while joining the split weights), RAM >= 8 GB, torso 7.7 GB"),
    "clef": dict(repo="Clef-Flash-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=21, ram_gb=14.5, vram_gb=19, cpu_s=None,
                 gpu_s=None, src="README: CPU peak RAM ~14.5 GB, ~21 GB on disk (split parts joined -> temporary extra disk); on a 4 GB GPU the CUDA load ran out of memory and fell back to CPU; VRAM needed: unconfirmed (skip below 19 GB is an inference from the weight size)"),
    "qev": dict(repo="QEV-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=9.9, ram_gb=8, vram_gb=None, cpu_s=4.7, gpu_s=None,
                src="README: release about 9.9 GB (all token-length graphs, shared 7.5 GB weights; +7.5 GB temporary while joining the split weights), free RAM >= 8 GB"),
    "d3edge": dict(repo="D3-ONNX-CPU", model_dir="models/edge", download=["download_model.py"], disk_gb=16, ram_gb=None, vram_gb=None, cpu_s=None, gpu_s=None,
                   src="D3-ONNX-CPU: ONE download (edge 2.6 GB + lite 4.2 GB + nano 9.3 GB = about 16 GB, shared by d3edge/d3lite/d3nano); d3-mini is not supported"),
    "d3lite": dict(repo="D3-ONNX-CPU", shared="d3edge", model_dir="models/lite", download=["download_model.py"], disk_gb=0, ram_gb=None, vram_gb=None, cpu_s=None, gpu_s=None,
                   src="same repository and download as d3edge (counted there); weights in models/lite (4.2 GB)"),
    "d3nano": dict(repo="D3-ONNX-CPU", shared="d3edge", model_dir="models/nano", download=["download_model.py"], disk_gb=0, ram_gb=None, vram_gb=None, cpu_s=None, gpu_s=None,
                   src="same repository and download as d3edge (counted there); weights in models/nano (9.3 GB)"),
    "openai": dict(repo="-", remote=True, src="remote API (costs money; needs OPENAI_API_KEY in the environment)"),
}
GLINER = dict(repo="GLiNER2.5-Decide-ONNX-CPU", model_dir="models/onnx", download=["download_model.py"], disk_gb=1.7)   # calibration only
ALL_MODELS = list(SPECS)

# images-224px.zip of dataset v1 as built on 2026-10-11 (dist/v1/manifest_v1.json). Used only when the Release has no SHA256SUMS and --images-sha256 is not given.
IMAGES_ZIP = "images-224px.zip"
BENCH_REPO_NAME = "wikipedia-vision-decision-bench"           # the Release that holds images-224px.zip (public, like the models' repositories)
DEFAULT_DRIVE_DIR = "/content/drive/MyDrive/wikipedia-vision-decision-bench-colab"
# exit codes of the images step (the notebook explains each one)
EXIT_NO_RELEASE, EXIT_DOWNLOAD, EXIT_SHA, EXIT_PICTURES = 3, 4, 5, 6
IMAGES_SHA256 = "c079de9251aa1eed4c779472b4c515ade955d7553b119c0b848444f73cd299b2"
IMAGES_MEMBERS = 2128


# ----------------------------------------------------------------------------------------------------------- small helpers
def say(msg: str = "") -> None:
    print(msg, flush=True)


def hdr(msg: str) -> None:
    say("\n=== " + msg)


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run_quiet(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    except (OSError, subprocess.SubprocessError) as e:
        return subprocess.CompletedProcess(cmd, 127, "", str(e))


def work_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("BENCH_WORK") or ROOT / "work")


def colab_dir() -> pathlib.Path:
    d = work_dir() / "colab"
    d.mkdir(parents=True, exist_ok=True)
    return d


def free_gb(path: pathlib.Path) -> float:
    p = path
    while not p.exists() and p != p.parent:
        p = p.parent
    return shutil.disk_usage(p).free / GB


def dir_gb(p: pathlib.Path) -> float:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / GB if p.exists() else 0.0


def mem_total_gb() -> float | None:
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemTotal"):
                return int(ln.split()[1]) / 1024 / 1024
    except OSError:
        pass
    return None


def gpu_info() -> dict:
    """nvidia-smi facts: name, VRAM (GB), driver, the CUDA version the driver supports. {} without a GPU."""
    r = run_quiet(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    if r.returncode != 0 or not r.stdout.strip():
        return {}
    name, mem, drv = [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")][:3]
    out = dict(name=name, vram_gb=round(float(mem) / 1024, 1), driver=drv)
    m = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", run_quiet(["nvidia-smi"]).stdout)
    if m:
        out["cuda_driver"] = "%s.%s" % m.groups()
    return out


def is_colab() -> bool:
    return os.path.isdir("/content") and ("COLAB_RELEASE_TAG" in os.environ or "COLAB_GPU" in os.environ or os.path.isdir("/content/sample_data"))


def git_env() -> dict:
    """Environment for git that authenticates to github.com with GITHUB_TOKEN without putting the token in a URL or in .git/config."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        b = base64.b64encode(("x-access-token:" + tok).encode()).decode()
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraHeader", GIT_CONFIG_VALUE_0="Authorization: Basic " + b)
    return env


def scrub(text: str) -> str:
    for name in ("GITHUB_TOKEN", "OPENAI_API_KEY"):
        v = os.environ.get(name)
        if v:
            text = text.replace(v, "***")
    return text


def stream(cmd, env=None, cwd=None, quiet_pred=None, tail=60):
    """Run a command, print its output live (the notebook shows it), return (returncode, last lines). quiet_pred(line) -> True: not printed."""
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
    last = collections.deque(maxlen=tail)
    for ln in p.stdout:
        ln = scrub(ln.rstrip("\n"))
        last.append(ln)
        if not (quiet_pred and quiet_pred(ln)):
            say(ln)
    p.wait()
    return p.returncode, list(last)


_PROGRESS = re.compile(r"^\s*\S.*\s+\d+(\.\d+)?%\s+[\d.]+\s*[KMG]?B/s\s*$")


def quiet_download(ln: str) -> bool:
    """Hide the per-file progress lines (hundreds per model) and the blank lines of download_model.py; the `got ...` / sha256 / summary lines stay."""
    return not ln.strip() or bool(_PROGRESS.match(ln))


# ----------------------------------------------------------------------------------------------------------- Drive sync
def _copy_if_newer(src: pathlib.Path, dst: pathlib.Path, only_newer: bool = False, skip=()) -> int:
    """Copy files that are missing / differ. only_newer (a PULL from Drive): never replace a local file that is as new or newer."""
    n = 0
    if not src.exists():
        return 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        t = dst / f.relative_to(src)
        try:
            if f.name in skip or f.name.endswith(".part"):
                continue
            if t.exists() and t.stat().st_size == f.stat().st_size and t.stat().st_mtime + 2 >= f.stat().st_mtime:
                continue
            if only_newer and t.exists() and t.stat().st_mtime + 2 >= f.stat().st_mtime:
                continue
            t.parent.mkdir(parents=True, exist_ok=True)
            tmp = t.with_name(t.name + ".part")
            shutil.copy2(f, tmp)
            os.replace(tmp, t)
            n += 1
        except OSError as e:
            say("  sync: %s: %s" % (f.name, e))
    return n


class DriveSync:
    """Logs (the resume state), results and the colab folder <-> Drive. The per-question LOG is what resumes a block, so it is always included."""

    def __init__(self, drive: str | None):
        self.root = pathlib.Path(drive) if drive else None
        self.pairs = []
        self._stop = threading.Event()

    @property
    def enabled(self) -> bool:
        return bool(self.root) and self.root.parent.exists()

    def add(self, local: pathlib.Path, name: str):
        self.pairs.append((local, name))

    def push(self) -> int:
        if not self.enabled:
            return 0
        return sum(_copy_if_newer(l, self.root / "results" / n) for l, n in self.pairs)

    def pull(self) -> int:
        if not self.enabled:
            return 0
        n = 0
        for l, name in self.pairs:
            n += _copy_if_newer(self.root / "results" / name, l, only_newer=True)
        return n

    def start(self, minutes: float):
        if not self.enabled or minutes <= 0:
            return

        def loop():
            while not self._stop.wait(minutes * 60):
                try:
                    self.push()
                except Exception as e:            # noqa: BLE001  (a Drive hiccup must not stop the run)
                    say("  sync failed: %s" % e)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self._stop.set()


# ----------------------------------------------------------------------------------------------------------- arguments
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", default="setup,images,bench,report")
    ap.add_argument("--models", default="all", help="comma separated runner keys, or all (%s)" % ",".join(ALL_MODELS))
    ap.add_argument("--devices", default="auto", help="cpu, cuda, or cpu,cuda; auto = cpu plus cuda when a GPU is there")
    ap.add_argument("--langs", default="en,ja")
    ap.add_argument("--sets", default="photo,biz,rsn", help="v1 sets. txt / all need the Wikipedia passages (WIKIQA_PASSAGES) or --skip-missing-passages")
    ap.add_argument("--mod", default="image", choices=["image", "text", "all"])
    ap.add_argument("--skip-missing-passages", action="store_true", help="drop the questions whose Wikipedia passage is not on this machine (txt / all)")
    ap.add_argument("--sample", type=int, default=0, help="N questions per (set, lang) chosen with --seed (the same ids for every model); 0 = every question")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cpu-speed-n", type=int, default=25,
                    help="GPU-only runs (cuda without cpu in --devices): also solve the SAME N questions per model on the CPU, only for a time-per-question reference "
                         "(speed_only block, not in any accuracy table). 0 = off. Not used when the cpu device runs anyway")
    ap.add_argument("--cpu-speed-max-s", type=float, default=600.0,
                    help="upper limit of the question time of one model's CPU speed block (seconds, model loading not counted; at least 3 questions are answered first)")
    ap.add_argument("--smoke", type=int, default=25, help="questions of the smoke run (device check + quick accuracy); 0 = no smoke (not recommended)")
    ap.add_argument("--threads", type=int, default=0, help="onnxruntime threads (0: min(8, CPU count)); the value used is recorded in every result")
    ap.add_argument("--px", type=int, default=224)
    ap.add_argument("--workers", type=int, default=3, help="concurrent requests (openai only)")
    # sources
    ap.add_argument("--owner", default="Kazuhito00")
    ap.add_argument("--release-tag", default="v0.0.0", help="Release tag passed to every download_model.py as --tag (default v0.0.0, the first release; '' = the scripts' own default, the latest release)")
    ap.add_argument("--repos-dir", default="/content/model_repos" if os.path.isdir("/content") else str(ROOT.parent / "model_repos"))
    ap.add_argument("--model-ref", action="append", default=[], metavar="REPO=REF", help="branch / tag of a model repository (default: its default branch)")
    ap.add_argument("--model-dir", action="append", default=[], metavar="KEY=PATH", help="weights folder of a model that has no download script (Drive path ok)")
    ap.add_argument("--download-args", action="append", default=[], metavar="KEY=ARGS", help='extra download_model.py arguments, e.g. "strands=--seq-len 384"')
    ap.add_argument("--images-url", default="", help="URL of images-224px.zip (empty = the default Release: https://github.com/<owner>/%s/releases/download/<--images-tag>/%s)" % (BENCH_REPO_NAME, IMAGES_ZIP))
    ap.add_argument("--images-tag", default="v0.0.0", help="Release tag of the bench repository that holds images-224px.zip (+ SHA256SUMS; > 2 GiB: %s.partNN parts)" % IMAGES_ZIP)
    ap.add_argument("--images-zip", default="", help="a local / Drive path of images-224px.zip (takes precedence over every URL)")
    ap.add_argument("--images-sha256", default="", help="expected sha256 of images-224px.zip (empty: the Release's SHA256SUMS, else the built-in value of the 2026-10-11 build)")
    ap.add_argument("--images-members", type=int, default=IMAGES_MEMBERS)
    # resources / persistence
    ap.add_argument("--use-drive", action="store_true", help="use Google Drive (logs, results, images zip, weights cache; restore + sync). DEFAULT OFF: nothing touches Drive. The notebook mounts it (USE_DRIVE = True)")
    ap.add_argument("--drive", default="", help="Drive folder for logs, results and caches, used only with --use-drive (default %s)" % DEFAULT_DRIVE_DIR)
    ap.add_argument("--drive-cache-max-gb", type=float, default=10.0, help="do not cache a model's weights on Drive above this size (free Drive is 15 GB)")
    ap.add_argument("--no-drive-cache", action="store_true", help="Drive keeps logs/results only, never weights")
    ap.add_argument("--weights", default="auto", choices=["auto", "keep", "purge"],
                    help="purge = delete a model's weights after it (sequential: fetch -> measure -> delete); keep = keep them; auto = purge when all do not fit the disk")
    ap.add_argument("--disk-reserve-gb", type=float, default=15.0)
    ap.add_argument("--time-budget-h", type=float, default=11.0, help="stop starting new blocks after this many hours (Colab free: 12 h per session)")
    ap.add_argument("--sync-min", type=float, default=10.0)
    ap.add_argument("--calibrate", default="auto", choices=["auto", "on", "off"], help="GLiNER reference calibration around CPU blocks (auto: cpu device, when GLiNER can be fetched)")
    ap.add_argument("--allow-unconfirmed-cuda", action="store_true", help="run a cuda model although providers_used could not be read")
    ap.add_argument("--force-models", action="store_true", help="try a model although its documented RAM / VRAM minimum is above this machine")
    ap.add_argument("--recheck", action="store_true", help="repeat the smoke / device check")
    ap.add_argument("--no-api", action="store_true", help="never run the openai model")
    ap.add_argument("--no-v1-report", action="store_true", help="skip the report/v1_report.py page (colab/make_v1_report.py)")
    ap.add_argument("--include-all-blocks", action="store_true", help="report: also blocks in results/runs/v1 that this machine did not run (default: Colab-run blocks only)")
    ap.add_argument("--dry-run", action="store_true", help="print what would be done; no install, no network, no run")
    args = ap.parse_args(argv)
    return args


def resolve_models(args) -> list[str]:
    keys = ALL_MODELS if args.models.strip() == "all" else [k.strip() for k in args.models.split(",") if k.strip()]
    bad = [k for k in keys if k not in SPECS]
    if bad:
        raise SystemExit("unknown model(s) %s; known: %s" % (bad, ", ".join(ALL_MODELS)))
    return keys


def resolve_devices(args, gpu: dict) -> list[str]:
    ds = ["cpu", "cuda"] if args.devices == "auto" else [d.strip() for d in args.devices.split(",") if d.strip()]
    ds = [d for d in ds if d in ("cpu", "cuda")]
    if "cuda" in ds and not gpu:
        say("no GPU visible (nvidia-smi): the cuda device is dropped. On Colab: Runtime > Change runtime type > T4 GPU.")
        ds.remove("cuda")
    if args.devices == "auto" and not gpu:
        ds = ["cpu"]
    return sorted(set(ds), key=lambda d: d != "cuda")          # cuda first: GPU results arrive before the CPU hours use the time budget


def cpu_speed_on(args, devices: list[str]) -> bool:
    """The CPU speed reference runs only when the real run is GPU-only (a cpu device in the run already gives CPU times)."""
    return args.cpu_speed_n > 0 and "cuda" in devices and "cpu" not in devices


def kv(items: list[str]) -> dict:
    out = {}
    for it in items:
        k, _, v = it.partition("=")
        out[k.strip()] = v.strip()
    return out


def threads_of(args) -> int:
    return args.threads or min(8, os.cpu_count() or 2)


# ----------------------------------------------------------------------------------------------------------- bench imports
def bench_imports():
    """runner / datasets are plain stdlib modules of the checkout."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    from runner import cases as rc, config as rcfg, logfmt, results      # noqa: E402
    return rc, rcfg, logfmt, results


def load_set(args, set_name: str):
    rc, rcfg, _, _ = bench_imports()
    if args.skip_missing_passages:
        import colab_loader
        return colab_loader.load(set_name, rcfg.data_root())
    try:
        return rc.load_cases(set_name, version="v1")
    except FileNotFoundError as e:
        raise SystemExit("%s\n-> use --sets photo,biz,rsn (no article questions), or --skip-missing-passages, or point WIKIQA_PASSAGES at your passages.json" % e)


def block_cases(args, set_name: str, lang: str) -> list[dict]:
    cs = load_set(args, set_name)
    if args.mod != "all":
        cs = [c for c in cs if c["modality"] == args.mod]
    return [c for c in cs if lang in c]


def sample_file(args, set_name: str, lang: str) -> pathlib.Path | None:
    """The same random ids for every model: work/colab/samples/<set>_<lang>_<mod>_n<N>_s<seed>.txt"""
    if not args.sample:
        return None
    p = colab_dir() / "samples" / ("%s_%s_%s_n%d_s%d.txt" % (set_name, lang, args.mod, args.sample, args.seed))
    if not p.exists():
        ids = sorted(c["id"] for c in block_cases(args, set_name, lang))
        pick = sorted(random.Random(args.seed).sample(ids, min(args.sample, len(ids))))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(pick) + "\n", encoding="utf-8")
    return p


def smoke_file(args, set_name: str, lang: str) -> pathlib.Path:
    p = colab_dir() / "samples" / ("smoke_%s_%s_%s_n%d.txt" % (set_name, lang, args.mod, args.smoke))
    if not p.exists():
        ids = sorted(c["id"] for c in block_cases(args, set_name, lang))
        pick = sorted(random.Random(12345).sample(ids, min(args.smoke, len(ids))))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(pick) + "\n", encoding="utf-8")
    return p


def cpu_speed_file(args, set_name: str, lang: str) -> pathlib.Path:
    """The same N random ids for every model (fixed seed): work/colab/samples/cpuspeed_<set>_<lang>_<mod>_n<N>.txt"""
    p = colab_dir() / "samples" / ("cpuspeed_%s_%s_%s_n%d.txt" % (set_name, lang, args.mod, args.cpu_speed_n))
    if not p.exists():
        ids = sorted(c["id"] for c in block_cases(args, set_name, lang))
        pick = sorted(random.Random(20261012).sample(ids, min(args.cpu_speed_n, len(ids))))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(pick) + "\n", encoding="utf-8")
    return p


# ----------------------------------------------------------------------------------------------------------- env / setup
def step_env(args) -> dict:
    hdr("runtime")
    g = gpu_info()
    info = dict(colab=is_colab(), python=platform.python_version(), platform=platform.platform(), cpu_count=os.cpu_count(),
                ram_gb=round(mem_total_gb() or 0, 1), disk_free_gb=round(free_gb(ROOT), 1), gpu=g)
    try:
        import importlib.metadata as md
        for dist in ("onnxruntime", "onnxruntime-gpu"):
            try:
                info[dist] = md.version(dist)
            except md.PackageNotFoundError:
                pass
    except ImportError:
        pass
    for k, v in info.items():
        say("  %-14s %s" % (k, v))
    if not g:
        say("  (no NVIDIA GPU visible: only the cpu device will run; the openai model needs no GPU)")
    colab_dir().joinpath("env.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return info


def ensure_uv() -> list[str]:
    exe = shutil.which("uv")
    if exe:
        return [exe]
    say("uv is not installed: bootstrapping it with pip (the ONLY use of pip here; uv installs everything else)")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"])
    if r.returncode != 0 or not shutil.which("uv"):
        raise SystemExit("could not install uv")
    return [shutil.which("uv")]


def uv_install(uv: list[str], pkgs: list[str], extra=()) -> None:
    cmd = uv + ["pip", "install", "--system"] + list(extra) + pkgs
    r = run_quiet(cmd)
    if r.returncode != 0 and "externally managed" in (r.stderr + r.stdout).lower():
        r = run_quiet(cmd + ["--break-system-packages"])
    say((r.stdout + r.stderr).strip()[-1500:])
    if r.returncode != 0:
        raise SystemExit("install failed: %s" % " ".join(pkgs))


def ort_gpu_spec(gpu: dict) -> tuple[str, list[str]]:
    """onnxruntime-gpu requirement for this machine. The models' READMEs were written against onnxruntime-gpu 1.31 with CUDA 13.
    Colab's driver CUDA is usually 12.x, whose default wheels are the 1.2x line: UNVERIFIED here -> overridable with ORT_GPU_SPEC."""
    if os.environ.get("ORT_GPU_SPEC"):
        return os.environ["ORT_GPU_SPEC"], []
    major = int((gpu.get("cuda_driver") or "12.0").split(".")[0])
    if major >= 13:
        return "onnxruntime-gpu", []
    return "onnxruntime-gpu>=1.20,<1.24", []


def cuda_lib_dirs() -> list[str]:
    import site
    import sysconfig
    cands = []
    for sp in set(site.getsitepackages() + [sysconfig.get_paths()["purelib"]]):
        cands += sorted(str(p) for p in pathlib.Path(sp, "nvidia").glob("*/lib"))
    cands += ["/usr/local/cuda/lib64", "/usr/lib64-nvidia", "/usr/lib/x86_64-linux-gnu"]
    return [c for c in cands if os.path.isdir(c)]


def child_env(extra_path: list[str] | None = None, **kv_) -> dict:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    libs = cuda_lib_dirs()
    if libs:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(libs + [env["LD_LIBRARY_PATH"]] if env.get("LD_LIBRARY_PATH") else libs)
    pp = [str(ROOT)] + (extra_path or [])
    env["PYTHONPATH"] = os.pathsep.join(pp + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env.update({k: str(v) for k, v in kv_.items()})
    return env


def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _ld(field: int, payload: bytes) -> bytes:
    return _varint(field << 3 | 2) + _varint(len(payload)) + payload


def _vi(field: int, n: int) -> bytes:
    return _varint(field << 3) + _varint(n)


def identity_onnx() -> bytes:
    """A 1-node ONNX model (Identity on a float[1] tensor) written by hand: no `onnx` package needed for the CUDA check."""
    shape = _ld(2, _ld(1, _vi(1, 1)))
    ttype = _ld(1, _vi(1, 1) + shape)
    vinfo = lambda name: _ld(1, name) + _ld(2, ttype)                                  # noqa: E731
    node = _ld(1, b"x") + _ld(2, b"y") + _ld(3, b"n") + _ld(4, b"Identity")
    graph = _ld(1, node) + _ld(2, b"g") + _ld(11, vinfo(b"x")) + _ld(12, vinfo(b"y"))
    return _vi(1, 10) + _ld(7, graph) + _ld(8, _vi(2, 21))          # ir_version 10, opset 21: what the models' graphs use


CUDA_CHECK = r"""
import sys, json
import onnxruntime as ort
sys.path.insert(0, %r)
from run_colab import identity_onnx
out = dict(version=ort.__version__, available=ort.get_available_providers())
try:
    s = ort.InferenceSession(identity_onnx(), providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    out["session_providers"] = s.get_providers()
except Exception as e:
    out["error"] = str(e)[:300]
print("CUDA_CHECK " + json.dumps(out))
"""


def check_cuda() -> dict:
    """Does a CUDA session really start (not only 'CUDAExecutionProvider is listed')? Run in a child process with the CUDA libraries on the path."""
    r = run_quiet([sys.executable, "-c", CUDA_CHECK % str(HERE)], env=child_env())
    for ln in (r.stdout + r.stderr).splitlines():
        if ln.startswith("CUDA_CHECK "):
            d = json.loads(ln[len("CUDA_CHECK "):])
            d["ok"] = bool(d.get("session_providers")) and d["session_providers"][0] == "CUDAExecutionProvider"
            return d
    return dict(ok=False, error=(r.stderr or r.stdout)[-300:])


def step_setup(args, devices: list[str], models: list[str], gpu: dict) -> None:
    hdr("setup (uv)")
    if sys.version_info < (3, 11):
        raise SystemExit("the bench needs Python >= 3.11 (this is %s)" % platform.python_version())
    if args.dry_run:
        say("[dry-run] would: ensure uv; uv pip install --system pillow numpy%s; %s"
            % (" tokenizers" if any(m.startswith("d3") for m in models) else "", "onnxruntime-gpu (spec %s)" % ort_gpu_spec(gpu)[0] if "cuda" in devices else "onnxruntime"))
        return
    uv = ensure_uv()
    pk = ["pillow>=10.0", "numpy>=1.26"] + (["tokenizers>=0.20"] if any(m.startswith("d3") for m in models) else [])
    uv_install(uv, pk)
    if all(SPECS[m].get("remote") for m in models):
        say("only remote models: no onnxruntime needed")
        return
    # onnxruntime and onnxruntime-gpu write into the same folder: never both.
    run_quiet(uv + ["pip", "uninstall", "--system", "onnxruntime", "onnxruntime-gpu"])
    if "cuda" in devices:
        spec, _ = ort_gpu_spec(gpu)
        say("installing %s (driver CUDA %s). The CPU device then runs on the same wheel (its CPU provider)." % (spec, gpu.get("cuda_driver", "?")))
        uv_install(uv, [spec])
    else:
        uv_install(uv, ["onnxruntime>=1.20"])
    import importlib.metadata as md
    both = []
    for d in ("onnxruntime", "onnxruntime-gpu"):
        try:
            md.version(d)
            both.append(d)
        except md.PackageNotFoundError:
            pass
    say("installed onnxruntime builds: %s" % both)
    if len(both) > 1:
        raise SystemExit("both onnxruntime and onnxruntime-gpu are installed (they overwrite each other): uninstall one")
    if "cuda" in devices:
        c = check_cuda()
        say("CUDA check: %s" % json.dumps(c))
        if not c.get("ok"):
            say("!! a CUDA session did not start: the cuda device will be skipped for every model (CPU fallback). Check the driver CUDA version / onnxruntime-gpu "
                "build (ORT_GPU_SPEC) / cuDNN. The cpu device is unaffected.")
        colab_dir().joinpath("cuda_check.json").write_text(json.dumps(c, indent=1) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------------------- images
def safe_extract(z: zipfile.ZipFile, dest: pathlib.Path) -> int:
    n = 0
    base = dest.resolve()
    for info in z.infolist():
        if info.is_dir():
            continue
        t = (dest / info.filename).resolve()
        if base != t and base not in t.parents:
            raise SystemExit("unsafe path in the zip: %s" % info.filename)
        t.parent.mkdir(parents=True, exist_ok=True)
        with z.open(info) as src, open(t, "wb") as out:
            shutil.copyfileobj(src, out)
        n += 1
    return n


UA = {"User-Agent": "wikipedia-vision-decision-bench-colab/0.2"}


class DownloadError(Exception):
    def __init__(self, msg: str, code: int = EXIT_DOWNLOAD):
        super().__init__(msg)
        self.code = code


def download(url: str, dest: pathlib.Path, tries: int = 6) -> None:
    """GET url -> dest. Resumes an interrupted download (dest.part + Range), retries with back-off, prints the progress. A 404 -> DownloadError(EXIT_NO_RELEASE)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    delay, last_pct, err = 2.0, -1, ""
    for attempt in range(tries):
        have = tmp.stat().st_size if tmp.exists() else 0
        req = urllib.request.Request(url, headers=dict(UA, **({"Range": "bytes=%d-" % have} if have else {})))
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resumed = bool(have) and r.status == 206
                total = (int(r.headers.get("Content-Length") or 0) + (have if resumed else 0)) or None
                done = have if resumed else 0
                with open(tmp, "ab" if resumed else "wb") as f:
                    for chunk in iter(lambda: r.read(1 << 20), b""):
                        f.write(chunk)
                        done += len(chunk)
                        pct = int(100 * done / total) // 10 * 10 if total else -1
                        if pct != last_pct and total and total > (8 << 20):
                            last_pct = pct
                            say("    %s: %d%% (%.0f MB)" % (dest.name, pct, done / 1e6))
            os.replace(tmp, dest)
            return
        except urllib.error.HTTPError as e:
            if e.code == 416 and tmp.exists():                  # the .part already is the whole file
                os.replace(tmp, dest)
                return
            if e.code in (401, 403, 404, 410):
                raise DownloadError("HTTP %d for %s (not published yet / wrong tag / private?)" % (e.code, url), EXIT_NO_RELEASE)
            err = "HTTP %d" % e.code
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            err = "%s" % e
        if attempt < tries - 1:
            say("    %s failed (%s): retry %d/%d in %.0f s (resumes from the .part file)" % (dest.name, err, attempt + 1, tries - 1, delay))
            time.sleep(delay)
            delay *= 2
    raise DownloadError("download of %s failed after %d tries (%s)" % (url, tries, err))


def fetch_sums(base: str) -> dict:
    """SHA256SUMS of the Release (sha256sum format: '<hex>  <name>'). {} when there is none."""
    try:
        req = urllib.request.Request(base + "/SHA256SUMS", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return {}
    return parse_sums(text)


def parse_sums(text: str) -> dict:
    out = {}
    for ln in text.splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(\S+)\s*$", ln)
        if m:
            out[m.group(2)] = m.group(1).lower()
    return out


def images_asset_name(args) -> str:
    return args.images_url.rsplit("/", 1)[1] if args.images_url else IMAGES_ZIP


def images_release_base(args) -> str:
    """Folder URL of the Release assets (no trailing slash)."""
    if args.images_url:
        return args.images_url.rsplit("/", 1)[0]
    return "https://github.com/%s/%s/releases/download/%s" % (args.owner, BENCH_REPO_NAME, args.images_tag)


def download_images_zip(args, dest_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    """-> (zip path, expected sha256). Single asset, or the .partNN assets listed in SHA256SUMS (each checked, then joined). Raises DownloadError."""
    base, name = images_release_base(args), images_asset_name(args)
    sums = fetch_sums(base)
    say("Release %s : SHA256SUMS %s" % (base, ("found (%d entries)" % len(sums)) if sums else "not found"))
    want = args.images_sha256 or sums.get(name) or sums.get(name + ".joined") or IMAGES_SHA256
    zp = dest_dir / name
    if zp.exists() and sha256_file(zp) == want:
        say("already downloaded: %s" % zp)
        return zp, want
    parts = sorted(n for n in sums if n.startswith(name + ".part"))
    if name not in sums and parts:
        say("the Release has %s as %d parts: downloading and joining them" % (name, len(parts)))
        for n in parts:
            pp = dest_dir / n
            if not (pp.exists() and sha256_file(pp) == sums[n]):
                say("downloading %s/%s" % (base, n))
                download("%s/%s" % (base, n), pp)
                if sha256_file(pp) != sums[n]:
                    pp.unlink()
                    raise DownloadError("sha256 of %s differs from SHA256SUMS (file deleted: run again)" % n, EXIT_SHA)
        tmp = zp.with_name(zp.name + ".join")
        with open(tmp, "wb") as out:
            for n in parts:
                with open(dest_dir / n, "rb") as f:
                    shutil.copyfileobj(f, out, 1 << 20)
        os.replace(tmp, zp)
        for n in parts:
            (dest_dir / n).unlink()
        return zp, want
    say("downloading %s/%s" % (base, name))
    download("%s/%s" % (base, name), zp)
    return zp, want


def no_release_help(args) -> str:
    return ("images-224px.zip could not be fetched from the Release (%s).\n"
            "  - Release not published yet / wrong tag: publish it (colab/README.md: gh release create ...) or pass --images-tag / --images-url.\n"
            "  - Own copy of the zip: --images-zip PATH (IMAGES_ZIP in the notebook).\n"
            "  - Last resort without the Release (covers only the Wikimedia Commons photos, NOT the drawn pictures of biz/rsn): the bench's own tool\n"
            "    `python -m datasets.fetch fetch` fetches them politely (1 request/s); it needs WIKIQA_CONTACT = your own contact in the environment\n"
            "    (Colab Secrets -> WIKIQA_CONTACT; never print or save it). Pictures are not redistributed with the repository." % images_release_base(args))


def check_pictures(args, sets: list[str]) -> list[str]:
    """Every picture of the questions exists, and the 224 px cache (named by file name only) cannot mix two pictures."""
    problems = []
    base = collections.defaultdict(set)
    for s in sets:
        for c in load_set(args, s):
            for p in c["images"]:
                base[pathlib.Path(p).name].add(p)
                if not os.path.exists(p):
                    problems.append("missing: " + p)
    clash = [b for b, v in base.items() if len(v) > 1]
    if clash:
        problems.append("%d picture file names are used by two different files (the px cache is keyed by file name): %s" % (len(clash), clash[:3]))
    say("pictures: %d distinct in the questions of %s" % (len(base), ",".join(sets)))
    return problems


def step_images(args, sets: list[str], sync: DriveSync) -> None:
    hdr("images (dataset v1, %s)" % IMAGES_ZIP)
    rc, rcfg, _, _ = bench_imports()
    root = rcfg.data_root()
    cache = sync.root / "cache" / IMAGES_ZIP if sync.enabled else None
    if args.dry_run:
        say("[dry-run] images root %s" % root)
        say("[dry-run] source order: 1. --images-zip %r  2. Drive cache %s  3. %s/%s" % (
            args.images_zip, cache if cache else "(Drive off)", images_release_base(args), images_asset_name(args)))
        say("[dry-run] the sha256 is checked (SHA256SUMS of the Release, or --images-sha256); a Release with %s.partNN parts is joined; an interrupted download resumes" % IMAGES_ZIP)
        say("[dry-run] expected: %d members (2127 pictures + ATTRIBUTION.md), about 20 MB" % IMAGES_MEMBERS)
        if (root / "data").exists():
            probs = check_pictures(args, sets)
            say("pictures check: %s" % ("OK" if not probs else probs[:5]))
        return
    marker = root / ".images_v1_ok"
    if marker.exists() and (not args.images_sha256 or marker.read_text().strip() == args.images_sha256):
        say("already extracted (%s)" % marker)
    else:
        zp, want = None, ""
        for cand in (pathlib.Path(args.images_zip) if args.images_zip else None, cache if cache and cache.exists() else None):
            if cand and cand.exists():
                zp, want = cand, args.images_sha256 or IMAGES_SHA256
                break
        if args.images_zip and zp is None:
            say("!! --images-zip %s does not exist" % args.images_zip)
            raise SystemExit(EXIT_NO_RELEASE)
        if zp is None:
            try:
                zp, want = download_images_zip(args, work_dir() / "dl")
            except DownloadError as e:
                say("!! " + str(e))
                if e.code == EXIT_NO_RELEASE:
                    say(no_release_help(args))
                raise SystemExit(e.code)
        got = sha256_file(zp)
        if got != want:
            say("!! sha256 of %s is %s, expected %s: refusing to extract (corrupt download? delete it and run again; "
                "if the Release was rebuilt, its SHA256SUMS or --images-sha256 must match)" % (zp, got, want))
            raise SystemExit(EXIT_SHA)
        say("sha256 ok: %s" % got)
        if cache and not cache.exists() and zp != cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(zp, cache)
            say("cached on Drive: %s" % cache)
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            if args.images_members and len(names) != args.images_members:
                say("warning: %d members, expected %d" % (len(names), args.images_members))
            n = safe_extract(z, root)
        say("extracted %d files into %s" % (n, root))
        marker.write_text(got + "\n")
    probs = check_pictures(args, sets)
    if probs:
        say("!! picture check failed (%d problems):\n  " % len(probs) + "\n  ".join(probs[:10]))
        raise SystemExit(EXIT_PICTURES)
    say("picture check: OK")


# ----------------------------------------------------------------------------------------------------------- models
def checkout_of(args, key: str) -> pathlib.Path:
    spec = SPECS[SPECS[key].get("shared", key)]
    return pathlib.Path(args.repos_dir) / spec["repo"]


def git_clone(args, repo: str, dest: pathlib.Path) -> str:
    """-> '' on success, else the reason."""
    if (dest / ".git").exists() or dest.exists() and any(dest.iterdir()):
        return ""
    url = "https://github.com/%s/%s" % (args.owner, repo)
    ref = kv(args.model_ref).get(repo)
    cmd = ["git", "clone", "--depth", "1"] + (["--branch", ref] if ref else []) + [url, str(dest)]
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = run_quiet(cmd, env=git_env())
    if r.returncode != 0:
        return scrub((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else "git clone failed") + "  [%s]" % url
    return ""


def populated(d: pathlib.Path, marker_only: bool = False) -> bool:
    """marker_only: a download / cache copy counts only when it FINISHED (the marker is written last); a folder the user filled counts with any .onnx."""
    if (d / ".colab_complete").exists():
        return True
    return (not marker_only) and d.exists() and any(d.rglob("*.onnx"))


def model_cache_dir(args, sync: DriveSync, key: str) -> pathlib.Path | None:
    if not sync.enabled or args.no_drive_cache:
        return None
    return sync.root / "cache" / "models" / (SPECS[key].get("shared", key) + "__" + pathlib.Path(SPECS[key]["model_dir"]).name)


def group_keys(key: str) -> list:
    """Every runner key that shares the download of ``key`` (itself included)."""
    root = SPECS[key].get("shared", key)
    return [k for k in SPECS if SPECS[k].get("shared", k) == root]


def prepare_model(args, key: str, sync: DriveSync) -> dict:
    """Clone + weights. -> dict(model_dir, checkout, tag) ; raises RuntimeError(reason) when the model cannot be prepared."""
    spec = dict(SPECS[SPECS[key].get("shared", key)], **{k: SPECS[key][k] for k in ("model_dir", "download") if k in SPECS[key]})
    co = checkout_of(args, key)
    why = git_clone(args, spec["repo"], co)
    if why:
        raise RuntimeError("repository not available (not public yet?): " + why)
    tag = (run_quiet(["git", "-C", str(co), "describe", "--tags", "--always"]).stdout.strip() or "unknown")
    user_dir = kv(args.model_dir).get(key)
    mdir = pathlib.Path(user_dir) if user_dir else co / spec["model_dir"]
    script = (spec.get("download") or ["download_model.py"])
    has_script = (co / script[0]).exists()
    if user_dir:
        if not populated(mdir):
            raise RuntimeError("--model-dir %s has no .onnx files" % user_dir)
    elif not populated(mdir, marker_only=has_script):                     # not there, or a download that did not finish
        cache = model_cache_dir(args, sync, key)
        if cache and populated(cache, marker_only=True):
            say("  restoring weights from the Drive cache (%s, %.1f GB) ..." % (cache, dir_gb(cache)))
            _copy_if_newer(cache, mdir, skip=(".colab_complete",))
            shutil.copy2(cache / ".colab_complete", mdir / ".colab_complete")
        elif has_script:
            need = (spec.get("disk_gb") or 0) * 1.0
            if free_gb(co) < need + args.disk_reserve_gb:
                raise RuntimeError("not enough disk: %.0f GB free, the weights take about %.1f GB (+ %.0f GB reserve)" % (free_gb(co), need, args.disk_reserve_gb))
            extra = kv(args.download_args).get(key, "").split()
            cmd = [sys.executable] + script + ["--repo", "%s/%s" % (args.owner, spec["repo"])]
            if args.release_tag and "--tag" not in extra:
                cmd += ["--tag", args.release_tag]
            cmd += extra
            say("  downloading weights: %s (cwd %s)" % (" ".join(cmd), co.name))
            rc_, tail = stream(cmd, cwd=co, env=child_env(), quiet_pred=quiet_download)
            if rc_ != 0:
                raise RuntimeError("download_model.py failed (private / unpublished release? it has no authentication): " + " | ".join(tail[-3:]))
            if not populated(mdir):
                raise RuntimeError("weights folder %s has no .onnx files after the download" % mdir)
            (mdir / ".colab_complete").write_text("ok\n")
            for k2 in group_keys(key):                                     # one download serves the whole group: mark every member that arrived
                d2 = co / SPECS[k2]["model_dir"]
                if populated(d2):
                    (d2 / ".colab_complete").write_text("ok\n")
        elif populated(mdir):
            pass                                                           # a folder somebody put into the checkout by hand
        else:
            raise RuntimeError("no weights: this repository has no download_model.py (yet). Put the model folder on Drive and pass --model-dir %s=PATH" % key)
    if not user_dir and (mdir / ".colab_complete").exists():
        cache = model_cache_dir(args, sync, key)
        if cache and not populated(cache, marker_only=True):
            gb = dir_gb(mdir)
            drive_free = shutil.disk_usage(sync.root).free / GB
            if gb > args.drive_cache_max_gb:
                say("  weights are %.1f GB > --drive-cache-max-gb %.1f: not cached on Drive" % (gb, args.drive_cache_max_gb))
            elif gb + 1 > drive_free:
                say("  Drive has %.1f GB free, the weights are %.1f GB: not cached" % (drive_free, gb))
            else:
                say("  caching the weights on Drive (%.1f GB) ..." % gb)
                _copy_if_newer(mdir, cache, skip=(".colab_complete",))
                shutil.copy2(mdir / ".colab_complete", cache / ".colab_complete")         # the marker goes last
    return dict(model_dir=mdir, checkout=co, tag=tag)


def purge_model(args, key: str, info: dict) -> None:
    d = info["model_dir"]
    if kv(args.model_dir).get(key):                         # the user's own folder: never delete
        return
    dirs = [d] + [info["checkout"] / SPECS[k]["model_dir"] for k in group_keys(key)]       # a shared download: every member's folder
    for d in dict.fromkeys(dirs):
        if d.exists():
            say("  deleting the weights %s (%.1f GB)" % (d, dir_gb(d)))
            shutil.rmtree(d, ignore_errors=True)


def check_fit(args, key: str, dev: str, gpu: dict) -> str:
    """Reason to skip from the DOCUMENTED minimums (None when unknown -> try)."""
    if args.force_models:
        return ""
    s = SPECS[key]
    ram = mem_total_gb()
    if dev == "cpu" and s.get("ram_gb") and ram and ram < s["ram_gb"]:
        return "RAM %.1f GB < documented minimum %s GB (%s)" % (ram, s["ram_gb"], s["src"])
    if dev == "cuda" and s.get("vram_gb") and gpu and gpu["vram_gb"] < s["vram_gb"]:
        return "VRAM %.1f GB < weights %s GB (%s)" % (gpu["vram_gb"], s["vram_gb"], s["src"])
    return ""


# ----------------------------------------------------------------------------------------------------------- one block
def read_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def run_one(args, key, set_name, lang, dev, info, suffix, ids_file, log_dir, cfg_blocks, env, force=False, extra=()) -> tuple[int, str, list[str]]:
    cmd = [sys.executable, "-m", "runner.run", "--model", key, "--set", set_name, "--lang", lang, "--mod", args.mod, "--dataset-version", "v1",
           "--threads", str(threads_of(args)), "--px", str(args.px), "--log-dir", str(log_dir), "--device", dev, "--suffix", suffix]
    if dev == "cuda":
        cmd.append("--gpu")
    if dev == "remote":
        cmd += ["--workers", str(args.workers)]
    if info.get("model_dir"):
        cmd += ["--model-dir", str(info["model_dir"])]
    if ids_file:
        cmd += ["--ids-file", str(ids_file)]
    if force:
        cmd.append("--force")
    cmd += list(extra)
    count = {"n": 0, "bad": 0, "t": time.time()}

    def quiet(ln):
        if ln.startswith(("ok ", "XX ")):
            count["n"] += 1
            count["bad"] += ln.startswith("XX ")
            if count["n"] % 100 == 0:
                say("    ... %d questions, %d wrong so far, %.0f s" % (count["n"], count["bad"], time.time() - count["t"]))
            return True
        if ln.startswith("   error:"):
            count.setdefault("err", 0)
            count["err"] += 1
            return count["err"] > 5
        return False
    code, tail = stream(cmd, cwd=ROOT, env=env, quiet_pred=quiet)
    block = "%s_%s_%s_%d%s" % (key, cfg_blocks[set_name], lang, args.px, suffix)
    return code, block, tail


def device_label(dev: str) -> str:
    return {"cpu": "_cpu", "cuda": "_cuda", "remote": ""}[dev]


def smoke_check(args, key, dev, info, env, log_dir, cfg_blocks, gpu) -> tuple[bool, str]:
    """A short run that also tells which providers were really used. -> (ok, reason)."""
    runs = colab_dir() / "checks"
    runs.mkdir(parents=True, exist_ok=True)
    vf = runs / ("%s_%s.json" % (key, dev))
    prev = read_json(vf)
    if prev and not args.recheck:
        say("  device check of an earlier session: %s" % prev["verdict"])
        return prev["ok"], prev["verdict"]
    if not args.smoke:
        return True, "no smoke (--smoke 0): providers not verified"
    s, lang = args.sets.split(",")[0], args.langs.split(",")[0]
    sf = smoke_file(args, s, lang)
    suffix = device_label(dev) + "_smoke"
    block = "%s_%s_%s_%d%s" % (key, cfg_blocks[s], lang, args.px, suffix)
    if args.recheck:
        (log_dir / (block + ".log")).unlink(missing_ok=True)
    code, _, tail = run_one(args, key, s, lang, dev, info, suffix, sf, log_dir, cfg_blocks, env, force=True)
    rj = ROOT / "results" / "runs" / "v1" / (block + ".json")
    rec = read_json(rj)
    ok, why = True, "ok"
    if code != 0 or not rec:
        ok, why = False, "smoke run failed (exit %s): %s" % (code, " | ".join(tail[-3:]))
    else:
        used = rec.get("providers_used") or []
        csvp = rj.with_suffix(".csv")
        rows = list(csv.DictReader(open(csvp, encoding="utf-8"))) if csvp.exists() else []
        na = sum(1 for r in rows if r["got"] == "NA")
        if dev == "cuda":
            if not used:
                if not args.allow_unconfirmed_cuda:
                    ok, why = False, "providers_used is empty: the CUDA use is unconfirmed (--allow-unconfirmed-cuda to run anyway)"
            elif any(p != "CUDAExecutionProvider" for p in used):
                ok, why = False, "CPU fallback: providers_used=%s" % used
        if ok and rows and na > len(rows) / 2:
            ok, why = False, "%d of %d smoke questions failed (got=NA): out of memory or a limit of the model; see the log" % (na, len(rows))
        if ok:
            why = "ok providers_used=%s acc=%s/%s median %s ms" % (used, rec["counts"]["overall"]["correct"], rec["counts"]["overall"]["n"], rec["counts"].get("ms_median"))
    for ext in (".json", ".csv"):                          # smoke records stay out of results/runs/v1
        f = rj.with_suffix(ext)
        if f.exists():
            (runs / "smoke_records").mkdir(exist_ok=True)
            shutil.move(str(f), str(runs / "smoke_records" / f.name))
    if ok:                                                  # a negative verdict (e.g. first session without a GPU) must not stick
        vf.write_text(json.dumps(dict(ok=ok, verdict=why, when=datetime.datetime.now().isoformat(timespec="seconds"), gpu=gpu), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    elif vf.exists():
        vf.unlink()
    say("  smoke %s/%s: %s" % (key, dev, why))
    return ok, why


def na_fraction(rj: pathlib.Path) -> float:
    cp = rj.with_suffix(".csv")
    if not cp.exists():
        return 0.0
    rows = list(csv.DictReader(open(cp, encoding="utf-8", newline="")))
    return (sum(1 for r in rows if r["got"] == "NA") / len(rows)) if rows else 0.0


def run_cpu_speed(args, key, info, gpu, sets, langs, cfg_blocks, cfg, log_dir, gl, results, logfmt, envinfo, status, t_start) -> None:
    """CPU speed reference of one model in a GPU-only run: the same N questions (first set, first language) on the CPU, in a CHILD process (so the GPU
    session of the model's cuda blocks is already gone: VRAM / RAM are free again), as a speed_only block. Never stops the other models."""
    skey = (key, "cpu-speed")
    if time.time() - t_start > args.time_budget_h * 3600:
        status[skey] = "skipped: time budget (%.1f h) used; run again to continue" % args.time_budget_h
        return
    why = check_fit(args, key, "cpu", gpu)
    if why:
        status[skey] = "skipped: " + why
        say("  CPU speed: SKIP: %s" % why)
        return
    s, lang = sets[0], langs[0]
    suffix = "_cpu_speed%d" % args.cpu_speed_n
    block = "%s_%s_%s_%d%s" % (key, cfg_blocks[s], lang, args.px, suffix)
    lp, rj = log_dir / (block + ".log"), ROOT / "results" / "runs" / "v1" / (block + ".json")
    finished = logfmt.is_finished(lp)
    if finished and rj.exists():
        say("  %s: finished earlier" % block)
        status[skey] = "ok: %s (earlier)" % block
        return
    try:
        ids = cpu_speed_file(args, s, lang)
    except SystemExit as e:
        status[skey] = "skipped: questions not available (%s)" % str(e).splitlines()[0]
        return
    env = child_env([str(info["checkout"]), str(HERE)], MODEL_TAG=info["tag"],
                    **({"BENCH_LOADER": "colab_loader:load"} if args.skip_missing_passages else {}))
    cal_before = calibrate_ms(gl) if (gl and not finished) else ""
    say("  -> %s  (CPU speed reference: %d questions, at most %.0f s)" % (block, args.cpu_speed_n, args.cpu_speed_max_s))
    code, _, tail = run_one(args, key, s, lang, "cpu", info, suffix, ids, log_dir, cfg_blocks, env, force=finished,
                            extra=["--speed-only", "--max-seconds", str(args.cpu_speed_max_s), "--min-questions", "3"])
    if code != 0 or not rj.exists():
        status[skey] = "skipped: the CPU run failed (exit %s; out of memory / load error?): %s" % (code, " | ".join(tail[-2:]))
        say("  CPU speed: " + status[skey])
        return
    if na_fraction(rj) > 0.5:
        status[skey] = "failed: more than half of the CPU questions failed (out of memory / a limit of the model: see the log %s)" % lp.name
        say("  CPU speed: " + status[skey])
        return
    if gl and not finished:
        after = calibrate_ms(gl)
        with open(log_dir / "blocks.log", "a", encoding="utf-8", newline="\n") as f:
            f.write("%s before=%s after=%s %s\n" % (block, cal_before, after, time.strftime("%H:%M:%S")))
        results.annotate_calibration(block, "v1", cal_before, after, cfg["gate"]["cal_limit_ms"])
    side = colab_dir() / "blocks"
    side.mkdir(exist_ok=True)
    (side / (block + ".env.json")).write_text(json.dumps(dict(env=envinfo, threads=threads_of(args), device="cpu", tag=info.get("tag"), speed_only=True,
                                                              note="Colab machine: CPU speed REFERENCE (few cores; do not compare with a desktop PC)"), ensure_ascii=False, indent=1) + "\n")
    rec = read_json(rj) or {}
    n = (rec.get("counts") or {}).get("overall", {}).get("n")
    status[skey] = "ok: %s questions, median %s ms%s" % (n, (rec.get("counts") or {}).get("ms_median"), " (stopped at the time limit)" if rec.get("speed_stopped_early") else "")


def calibrate_ms(gl: dict | None) -> str:
    if not gl:
        return ""
    env = child_env([str(gl["checkout"])], GLINER_MODEL_DIR=gl["model_dir"])
    r = run_quiet([sys.executable, "-m", "runner.calibrate"], cwd=ROOT, env=env)
    m = re.search(r"median (\d+) ms", (r.stdout.strip().splitlines() or [""])[-1])
    return m.group(1) if m else ""


def setup_gliner(args, sync):
    if args.calibrate == "off":
        return None
    try:
        spec = GLINER
        co = pathlib.Path(args.repos_dir) / spec["repo"]
        why = git_clone(args, spec["repo"], co)
        if why:
            raise RuntimeError(why)
        mdir = co / spec["model_dir"]
        if not populated(mdir):
            if free_gb(co) < 5:
                raise RuntimeError("not enough disk")
            rc_, tail = stream([sys.executable, "download_model.py"], cwd=co, env=child_env(), quiet_pred=quiet_download)
            if rc_ != 0 or not populated(mdir):
                raise RuntimeError(" | ".join(tail[-2:]))
        return dict(checkout=co, model_dir=str(mdir))
    except RuntimeError as e:
        say("calibration unavailable (GLiNER2.5-Decide could not be fetched: %s): CPU times are recorded without a calibration value" % e)
        return None


def acquire_lock() -> pathlib.Path:
    """One bench run at a time: two writers on the same block log would corrupt it (a stopped notebook cell does not stop its child)."""
    lock = colab_dir() / "run.lock"
    if lock.exists() and os.name == "posix":
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            raise SystemExit("another run_colab.py bench is running (pid %d, %s). Wait for it, or stop it (Runtime > Interrupt, or `kill %d`) and run again." % (pid, lock, pid))
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            pass                                                           # stale lock
    lock.write_text(str(os.getpid()))
    return lock


def release_lock(lock: pathlib.Path) -> None:
    try:
        if lock.read_text().strip() == str(os.getpid()):
            lock.unlink()
    except OSError:
        pass


def run_models(args, models, devices, gpu, sets, langs, sync, status) -> None:
    rc, rcfg, logfmt, results = bench_imports()
    cfg = rcfg.load()
    cfg_blocks = cfg["blocks"]
    log_dir = work_dir() / "logs" / "v1"
    log_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    envinfo = read_json(colab_dir() / "env.json") or {}
    cuda_ok = None
    if "cuda" in devices:
        cc = read_json(colab_dir() / "cuda_check.json")
        cuda_ok = bool(cc and cc.get("ok")) if cc else check_cuda().get("ok")
        if not cuda_ok:
            say("the CUDA session check failed: the cuda device is skipped for every model")
    local = [m for m in models if not SPECS[m].get("remote")]
    hdr("clone every model repository (shallow, no weights; a shared repository once)")
    for rk in dict.fromkeys(SPECS[m].get("shared", m) for m in local):
        why = git_clone(args, SPECS[rk]["repo"], checkout_of(args, rk))
        say("  %-34s %s" % (SPECS[rk]["repo"], ("NOT cloned: " + why) if why else "ok"))
    total_gb = sum((SPECS[m].get("disk_gb") or 0) for m in local)
    purge = args.weights == "purge" or (args.weights == "auto" and total_gb > max(0.0, free_gb(ROOT) - args.disk_reserve_gb))
    say("weights policy: %s (selected models need ~%.0f GB known; %.0f GB free)" % ("sequential, delete after each model" if purge else "keep", total_gb, free_gb(ROOT)))
    speed_on = cpu_speed_on(args, devices)
    if speed_on:
        say("CPU speed reference: %d questions per model on the CPU after its cuda blocks (at most %.0f s each; speed_only, not in any accuracy table)"
            % (args.cpu_speed_n, args.cpu_speed_max_s))
    gl = setup_gliner(args, sync) if (("cpu" in devices or speed_on) and args.calibrate in ("auto", "on") and local) else None
    kept = {}                                            # models whose weights are still on the disk (policy keep)
    todo_after = {}                                      # shared repositories: delete the weights after the LAST model that uses them
    for i, m in enumerate(models):
        todo_after[SPECS[m].get("shared", m)] = i
    for i, key in enumerate(models):
        hdr("model %s (%d/%d)" % (key, i + 1, len(models)))
        spec = SPECS[key]
        remote = bool(spec.get("remote"))
        if remote and (args.no_api or not os.environ.get("OPENAI_API_KEY")):
            reason = "--no-api" if args.no_api else "OPENAI_API_KEY is not set (Colab Secrets -> notebook cell): the OpenAI Decisions API is skipped"
            status[(key, "remote")] = "skipped: " + reason
            say("  " + reason)
            continue
        info = {}
        if not remote:
            fits = {d: check_fit(args, key, d, gpu) for d in devices}
            fits = {d: (("no working CUDA session" if (d == "cuda" and not cuda_ok) else "") or w) for d, w in fits.items()}
            if speed_on:
                fits["cpu-speed"] = check_fit(args, key, "cpu", gpu)
            if all(fits.values()):                                           # nothing would run: do not download gigabytes for it
                for d, w in fits.items():
                    status[(key, d)] = "skipped: " + w
                say("  SKIP (no device can run it, nothing downloaded): %s" % "; ".join("%s: %s" % kv_ for kv_ in fits.items()))
                continue
            try:
                try:
                    info = prepare_model(args, key, sync)
                except RuntimeError as e:
                    if str(e).startswith("not enough disk") and kept and args.weights != "keep":     # make room: weights of the models already measured
                        for k2, i2 in list(kept.items()):
                            purge_model(args, k2, i2)
                        kept.clear()
                        info = prepare_model(args, key, sync)
                    else:
                        raise
            except RuntimeError as e:
                for d in list(devices) + (["cpu-speed"] if speed_on else []):
                    status[(key, d)] = "skipped: " + str(e)
                say("  SKIP: %s" % e)
                continue
        for dev in (["remote"] if remote else devices):
            if time.time() - t_start > args.time_budget_h * 3600:
                status[(key, dev)] = "skipped: time budget (%.1f h) used; run again to continue" % args.time_budget_h
                continue
            if dev == "cuda" and not cuda_ok:
                status[(key, dev)] = "skipped: no working CUDA session (see setup)"
                continue
            why = "" if remote else check_fit(args, key, dev, gpu)
            if why:
                status[(key, dev)] = "skipped: " + why
                say("  SKIP %s: %s" % (dev, why))
                continue
            env = child_env([str(info["checkout"]), str(HERE)] if info else [str(HERE)],
                            MODEL_TAG=("api" if remote else info["tag"]),
                            **({"BENCH_LOADER": "colab_loader:load"} if args.skip_missing_passages else {}))
            ok, why = smoke_check(args, key, dev, info, env, log_dir, cfg_blocks, gpu)
            if not ok:
                status[(key, dev)] = "skipped: " + why
                continue
            done = fails = 0
            for s, lang in [(s_, l_) for s_ in sets for l_ in langs]:
                if time.time() - t_start > args.time_budget_h * 3600:
                    status[(key, dev)] = "partial: time budget used; run again to continue"
                    break
                ids = sample_file(args, s, lang)
                suffix = device_label(dev) + ("_n%d" % args.sample if args.sample else "")
                block = "%s_%s_%s_%d%s" % (key, cfg_blocks[s], lang, args.px, suffix)
                lp = log_dir / (block + ".log")
                rj = ROOT / "results" / "runs" / "v1" / (block + ".json")
                finished = logfmt.is_finished(lp)
                if finished and rj.exists():
                    say("  %s: finished earlier" % block)
                    done += 1
                    continue
                cal_before = calibrate_ms(gl) if (dev == "cpu" and gl and not finished) else ""
                say("  -> %s" % block)
                code, _, tail = run_one(args, key, s, lang, dev, info, suffix, ids, log_dir, cfg_blocks, env, force=finished)
                if code != 0:
                    fails += 1
                    say("  block failed (exit %s): %s" % (code, " | ".join(tail[-3:])))
                    continue
                na_frac = na_fraction(rj)
                if na_frac > 0.5:
                    status[(key, dev)] = "failed: %.0f%% of the answers in %s are NA (out of memory / a limit of the model: see the log); stopped" % (100 * na_frac, block)
                    say("  " + status[(key, dev)])
                    fails += 1
                    break
                done += 1
                if dev == "cpu" and gl and not finished:
                    after = calibrate_ms(gl)
                    with open(log_dir / "blocks.log", "a", encoding="utf-8", newline="\n") as f:
                        f.write("%s before=%s after=%s %s\n" % (block, cal_before, after, time.strftime("%H:%M:%S")))
                    results.annotate_calibration(block, "v1", cal_before, after, cfg["gate"]["cal_limit_ms"])
                side = colab_dir() / "blocks"
                side.mkdir(exist_ok=True)
                (side / (block + ".env.json")).write_text(json.dumps(dict(env=envinfo, threads=threads_of(args), device=dev, tag=info.get("tag"),
                                                                          note="Colab machine: timings are reference values"), ensure_ascii=False, indent=1) + "\n")
                sync.push()
            status.setdefault((key, dev), "ok: %d blocks%s" % (done, ", %d failed" % fails if fails else ""))
        if speed_on and info and not remote:
            run_cpu_speed(args, key, info, gpu, sets, langs, cfg_blocks, cfg, log_dir, gl, results, logfmt, envinfo, status, t_start)
            sync.push()
        if info and purge and todo_after.get(SPECS[key].get("shared", key)) == i:
            purge_model(args, key, info)
        elif info:
            kept[key] = info
        sync.push()
        if not sync.enabled:
            partial_bundle(args)


# ----------------------------------------------------------------------------------------------------------- report
def collect_results() -> list[dict]:
    d = ROOT / "results" / "runs" / "v1"
    out = []
    for p in sorted(d.glob("*.json")):
        rec = read_json(p)
        if not isinstance(rec, dict) or "counts" not in rec or "block" not in rec:
            continue
        csvp = p.with_suffix(".csv")
        rows = list(csv.DictReader(open(csvp, encoding="utf-8"))) if csvp.exists() else []
        out.append(dict(rec=rec, rows=rows))
    return out


def is_speed(r: dict) -> bool:
    return bool(r["rec"].get("speed_only"))


def pct(c, n):
    return "%.1f" % (100.0 * c / n) if n else "-"


def build_summary(status: dict, out_dir: pathlib.Path) -> list[pathlib.Path]:
    allres = collect_results()
    res = [r for r in allres if not is_speed(r)]               # timing-only blocks are never in an accuracy table
    speed_res = [r for r in allres if is_speed(r)]
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# wikipedia-vision-decision-bench on Colab: summary", "",
             "Generated %s. CPU times were measured on a Colab machine: reference values (the calibration gate was set up on another machine)." %
             datetime.datetime.now().isoformat(timespec="seconds"), "",
             "## Blocks", "", "| block | model | device | lang | n | correct | % | median ms | providers used | threads | calibration ms (before/after) | questions in block | run here |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    csv_rows = []
    for r in res:
        m, c = r["rec"], r["rec"]["counts"]["overall"]
        cal = m.get("calibration") or {}
        lines.append("| %s | %s | %s | %s | %d | %d | %s | %s | %s | %s | %s/%s | %s | %s |" % (
            m["block"], m["model"], m.get("device"), m["lang"], c["n"], c["correct"], pct(c["correct"], c["n"]), r["rec"]["counts"].get("ms_median"),
            ",".join(m.get("providers_used") or []) or "-", m.get("threads"), cal.get("before_ms", "-"), cal.get("after_ms", "-"), m.get("questions_in_block"),
            "yes" if (colab_dir() / "blocks" / (m["block"] + ".env.json")).exists() else "no (earlier / other machine)"))
        csv_rows.append(dict(block=m["block"], model=m["model"], device=m.get("device"), lang=m["lang"], n=c["n"], correct=c["correct"],
                             accuracy=c["accuracy"], ms_median=r["rec"]["counts"].get("ms_median")))
    # by group (from the id prefix) and by kind
    groups = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in res:
        m = r["rec"]
        for row in r["rows"]:
            g = row["id"].split("-")[0]
            for dim, val in (("group", g), ("kind", row["kind"])):
                x = groups[(m["model"], m.get("device"), m["lang"])][(dim, val)]
                x[0] += int(row["ok"])
                x[1] += 1
    cols = sorted({k for v in groups.values() for k in v})
    lines += ["", "## Accuracy % by group and by format", "", "| model | device | lang | " + " | ".join("%s:%s" % k for k in cols) + " |", "|---|---|---|" + "---|" * len(cols)]
    for (mo, dv, lg), v in sorted(groups.items()):
        lines.append("| %s | %s | %s | " % (mo, dv, lg) + " | ".join(pct(*v[k]) if k in v else "-" for k in cols) + " |")
    if speed_res:
        lines += ["", "## CPU speed reference (timing only, not in any accuracy table)", "",
                  "Few questions per model, solved on the CPU in a GPU-only run. Colab's CPU has few cores: do not compare these times with a desktop PC.", "",
                  "| block | model | questions | median ms | stopped at time limit | threads | CPU | calibration ms (before/after) |", "|---|---|---|---|---|---|---|---|"]
        for r in speed_res:
            m = r["rec"]
            ms = sorted(int(float(x["ms"])) for x in r["rows"] if x.get("ms") and float(x["ms"]) > 0 and x.get("got") != "NA")
            cal = m.get("calibration") or {}
            cpu = ((m.get("host") or {}).get("cpu") or {})
            lines.append("| %s | %s | %d | %s | %s | %s | %s | %s/%s |" % (
                m["block"], m["model"], len(ms), int(statistics.median(ms)) if ms else "-", "yes" if m.get("speed_stopped_early") else "no", m.get("threads"),
                "%s (%s cores)" % (cpu.get("name"), cpu.get("logical_cores")) if cpu else "-", cal.get("before_ms", "-"), cal.get("after_ms", "-")))
    lines += ["", "## Status of every model / device", "", "| model | device | status |", "|---|---|---|"]
    for (k, d), v in sorted(status.items()):
        lines.append("| %s | %s | %s |" % (k, d, v.replace("|", "/")))
    md = out_dir / "colab_summary.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cv = out_dir / "colab_summary.csv"
    with open(cv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["block", "model", "device", "lang", "n", "correct", "accuracy", "ms_median"], lineterminator="\n")
        w.writeheader()
        w.writerows(csv_rows)
    # self-contained html (no pictures): the same tables
    body, tbl = [], []
    for ln in lines:
        if ln.startswith("|"):
            tbl.append(ln)
            continue
        if tbl:
            body.append(md_table_html(tbl))
            tbl = []
        if ln.startswith("# "):
            body.append("<h1>%s</h1>" % html.escape(ln[2:]))
        elif ln.startswith("## "):
            body.append("<h2>%s</h2>" % html.escape(ln[3:]))
        elif ln.strip():
            body.append("<p>%s</p>" % html.escape(ln))
    if tbl:
        body.append(md_table_html(tbl))
    ht = out_dir / "colab_summary.html"
    ht.write_text("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Colab summary</title>"
                  "<style>:root{color-scheme:light dark}body{font:14px system-ui;margin:16px;max-width:1200px}table{border-collapse:collapse;display:block;overflow-x:auto}"
                  "td,th{border:1px solid #8884;padding:3px 8px;text-align:left}th{background:#8882}</style>" + "\n".join(body), encoding="utf-8")
    return [md, cv, ht]


def md_table_html(rows: list[str]) -> str:
    cells = [[html.escape(c.strip()) for c in r.strip().strip("|").split("|")] for r in rows if not set(r.replace("|", "").strip()) <= set("-: ")]
    out = ["<table>"]
    for i, r in enumerate(cells):
        out.append("<tr>" + "".join("<%s>%s</%s>" % ("th" if i == 0 else "td", c, "th" if i == 0 else "td") for c in r) + "</tr>")
    return "\n".join(out) + "</table>"


def try_v1_report(args) -> str:
    """report/v1_report.py through colab/make_v1_report.py (it makes the inputs that report/ expects in a temporary folder)."""
    out = colab_dir() / "out" / "v1_report.html"
    cmd = [sys.executable, str(HERE / "make_v1_report.py"), "--out", str(out)] + (["--include-all-blocks"] if args.include_all_blocks else [])
    code, tail = stream(cmd, cwd=ROOT, env=child_env())
    return "v1_report.py: %s" % (out if code == 0 and out.exists() else "NOT built (exit %s): %s" % (code, " | ".join(tail[-2:])))


def partial_bundle(args) -> None:
    """Drive off: a zip of whatever exists so far (also rewritten after every model), so an interrupted session can still be downloaded."""
    try:
        z = colab_dir() / "out" / "colab_results_partial.zip"
        write_bundle(args, z, [])
        (colab_dir() / "last_bundle.txt").write_text(str(z), encoding="utf-8")
        say("  partial bundle (download it from the file browser or with the notebook's download cell): %s (%.1f MB)" % (z, z.stat().st_size / 1e6))
    except OSError as e:
        say("  partial bundle failed: %s" % e)


def step_report(args, status, sync) -> None:
    hdr("report")
    out = colab_dir() / "out"
    files = build_summary(status, out)
    for f in files:
        say("  wrote %s" % f)
    v1 = None
    if not args.no_v1_report:
        say("  " + try_v1_report(args))
        v1 = out / "v1_report.html"
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    z = out / ("colab_results_%s.zip" % ts)
    write_bundle(args, z, files + ([v1] if v1 and v1.exists() else []))
    say("  bundle: %s (%.1f MB)" % (z, z.stat().st_size / 1e6))
    (colab_dir() / "last_bundle.txt").write_text(str(z), encoding="utf-8")
    sync.push()


def write_bundle(args, z: pathlib.Path, summary_files) -> None:
    """The zip to download: results json/csv, logs, device checks (+ the summary files when there are any)."""
    z.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, arc in ((ROOT / "results" / "runs" / "v1", "results/runs/v1"), (work_dir() / "logs" / "v1", "logs/v1"), (colab_dir() / "checks", "colab/checks"),
                          (colab_dir() / "blocks", "colab/blocks")):
            if base.exists():
                for f in base.rglob("*"):
                    if f.is_file() and "smoke_records" not in f.parts and (arc != "results/runs/v1" or (colab_dir() / "blocks" / (f.stem + ".env.json")).exists() or args.include_all_blocks):
                        zf.write(f, arc + "/" + str(f.relative_to(base)).replace(os.sep, "/"))
        for f in summary_files:
            zf.write(f, "summary/" + f.name)


# ----------------------------------------------------------------------------------------------------------- plan
def step_plan(args, models, devices, gpu, sets, langs) -> None:
    hdr("plan")
    rc, rcfg, _, _ = bench_imports()
    say("sets %s, langs %s, mod %s, sample %s, smoke %d, threads %d, devices %s" % (sets, langs, args.mod, args.sample or "all", args.smoke, threads_of(args), devices))
    n_by = {}
    try:
        for s in sets:
            for l in langs:
                n = len(block_cases(args, s, l))
                n_by[(s, l)] = min(n, args.sample) if args.sample else n
        total = sum(n_by.values())
        say("questions per model and device: %d  (%s)" % (total, ", ".join("%s/%s %d" % (s, l, n) for (s, l), n in n_by.items())))
    except SystemExit as e:
        total = 0
        say("questions: could not be counted (%s)" % str(e).splitlines()[0])
    say("")
    say("%-9s %-34s %-10s %-9s %-10s %s" % ("model", "repository", "disk GB", "RAM/VRAM", "est. CPU h", "note"))
    for k in models:
        s = SPECS[k]
        if s.get("remote"):
            say("%-9s %-34s %-10s %-9s %-10s %s" % (k, "(remote API)", "-", "-", "-", "OPENAI_API_KEY set: %s; costs money" % ("yes" if os.environ.get("OPENAI_API_KEY") else "NO -> skipped")))
            continue
        est = "%.1f" % (s["cpu_s"] * total / 3600) if s.get("cpu_s") and total else "?"
        say("%-9s %-34s %-10s %-9s %-10s %s" % (k, "%s/%s" % (args.owner, s["repo"]), ("shared" if s.get("shared") else (s.get("disk_gb") or "?")), "%s/%s" % (s.get("ram_gb") or "?", s.get("vram_gb") or "?"), est, s["src"]))
    say("")
    if total:
        h = sum(SPECS[k]["cpu_s"] * total / 3600 for k in models if not SPECS[k].get("remote") and SPECS[k].get("cpu_s") and "cpu" in devices)
        if h > args.time_budget_h:
            say("!! estimated CPU time of the models that have a number is %.0f h > the %.0f h budget: use --sample N (e.g. 300 per set and language), fewer models, or several sessions "
                "(the run resumes)." % (h, args.time_budget_h))
    if cpu_speed_on(args, devices):
        loc = [k for k in models if not SPECS[k].get("remote")]
        est_s = sum(min(args.cpu_speed_n * SPECS[k]["cpu_s"], args.cpu_speed_max_s) if SPECS[k].get("cpu_s") else args.cpu_speed_max_s for k in loc)
        unk = [k for k in loc if not SPECS[k].get("cpu_s")]
        say("CPU speed reference: %d questions per model (%s/%s, the same ids for every model, speed_only), at most %.0f s per model, extra time about %.0f min at most%s"
            % (args.cpu_speed_n, sets[0], langs[0], args.cpu_speed_max_s, est_s / 60, " (models without an author's CPU time counted at the limit: %s)" % ",".join(unk) if unk else ""))
        say("  blocks: " + ", ".join("%s_%s_%s_%d_cpu_speed%d" % (k, rcfg.load()["blocks"][sets[0]], langs[0], args.px, args.cpu_speed_n) for k in loc[:2]) + (", ..." if len(loc) > 2 else ""))
    elif args.cpu_speed_n > 0 and "cuda" in devices:
        say("CPU speed reference: not needed (the cpu device runs anyway)")
    say("time estimate = the author's PC CPU median per question x questions (bench README); a Colab CPU differs (2 vCPU on the free tier: expect it to be slower).")
    say("GPU time per question on the author's 4 GB GPU: jevision 75 ms, onejev 87 ms; T4 is not measured.")
    known = sum((SPECS[k].get("disk_gb") or 0) for k in models if not SPECS[k].get("remote"))
    say("known weights total %.0f GB (unknown sizes not counted); disk free here %.0f GB" % (known, free_gb(ROOT)))
    if not gpu:
        say("no GPU visible")


# ----------------------------------------------------------------------------------------------------------- main
def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    bad = [s for s in steps if s not in ("env", "setup", "images", "bench", "report", "sync", "plan")]
    if bad:
        raise SystemExit("unknown step(s): %s" % bad)
    models = resolve_models(args)
    gpu = gpu_info()
    devices = resolve_devices(args, gpu)
    sets = [s for s in args.sets.split(",") if s]
    langs = [s for s in args.langs.split(",") if s]
    if args.use_drive:
        sync = DriveSync(args.drive or DEFAULT_DRIVE_DIR)
        if not sync.enabled:
            say("--use-drive: the Drive folder %s is not usable (is Drive mounted? the notebook does it): continuing WITHOUT Drive" % sync.root)
    else:
        sync = DriveSync(None)
        if args.drive:
            say("--drive is ignored without --use-drive: Drive is OFF (results stay on this machine; `report` makes a zip to download)")
    rc, rcfg, logfmt, results = bench_imports()
    sync.add(work_dir() / "logs" / "v1", "logs_v1")
    sync.add(ROOT / "results" / "runs" / "v1", "runs_v1")
    sync.add(colab_dir() / "checks", "colab_checks")
    sync.add(colab_dir() / "blocks", "colab_blocks")
    status: dict = {}
    if sync.enabled and not args.dry_run:
        say("Drive: restoring %d earlier files" % sync.pull())
    if args.dry_run or "plan" in steps:
        step_plan(args, models, devices, gpu, sets, langs)
    if "env" in steps:
        step_env(args)
    if "setup" in steps:
        step_setup(args, devices, models, gpu)
    if "images" in steps:
        step_images(args, sets, sync)
    if "bench" in steps:
        if args.dry_run:
            say("[dry-run] bench: first clone EVERY repository of %s (shared ones once); then for each model: weights (download_model.py) -> devices %s -> smoke -> blocks -> "
                "weights deleted afterwards only when they do not all fit (--weights %s)" % (models, devices, args.weights))
            if cpu_speed_on(args, devices):
                say("[dry-run] CPU speed: after the cuda blocks of each model (the GPU session is gone: the blocks run in child processes), the same %d questions on the CPU "
                    "(speed_only block <model>_<set code>_<lang>_%d_cpu_speed%d, at most %.0f s per model, >= 3 questions; a failure is skipped and listed)" % (args.cpu_speed_n, args.px, args.cpu_speed_n, args.cpu_speed_max_s))
            say("[dry-run] Drive: %s" % ("ON (%s)" % sync.root if sync.enabled else "OFF (default; --use-drive to use it): results stay local, zip at the end"))
        else:
            lock = acquire_lock()
            if not sync.enabled:
                say("Drive is OFF: results and logs are kept on this machine only (it is erased when the session ends). A partial zip is rewritten after "
                    "every model, and the `report` step builds the final zip to download.")
            sync.start(args.sync_min)
            try:
                run_models(args, models, devices, gpu, sets, langs, sync, status)
            finally:
                sync.stop()
                sync.push()
                if not sync.enabled:
                    partial_bundle(args)
                release_lock(lock)
            (colab_dir() / "status.json").write_text(json.dumps({"%s|%s" % k: v for k, v in status.items()}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            hdr("status of every model / device")
            for (k, d), v in sorted(status.items()):
                say("  %-9s %-7s %s" % (k, d, v))
    if "report" in steps and not args.dry_run:
        old = read_json(colab_dir() / "status.json") or {}
        for k, v in old.items():
            status.setdefault(tuple(k.split("|")), v)
        step_report(args, status, sync)
    if "sync" in steps and not args.dry_run:
        say("pushed %d files to Drive" % sync.push() if sync.enabled else "Drive is OFF (--use-drive not given): nothing to sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
