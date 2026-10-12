# -*- coding: utf-8 -*-
"""Run ONE model on ONE question group in ONE language. Resumable: a re-run continues the block's log where it stopped.

    uv run python -m runner.run --model onejev --set commons --lang en [--gpu] [--model-dir DIR] [--limit N]
        --model     onejev | onejev4 | openjev | openjev4 | intern | strands | clef | jevision | qev | d3edge | d3lite | d3nano      (adapters/)
        --set       commons | synthetic | reasoning      (the question groups of legacy)
                    photo | biz | rsn | txt | all | new   (with --dataset-version v1; new = only the new questions)
        --lang      en | ja
        --mod       image (default) | text | all          picture questions, text-only questions, or both
        --log-dir   where the per-question logs go (default work/logs/timed); one file per block: <model>_<code>_<lang>_<px>.log
        --ids-file  only the question ids listed there (one per line: a sample)
        --skip-log  skip the ids an earlier log already has (fill-in run; comma separated)
        --suffix    appended to the block name (e.g. _exp)

Conditions (threads, px, rev, gpu) come from runner/config.toml, overridden by THREADS / PX / REV / GPU or by the options.
Output: one line per question in the old log format (stdout and the log file), then a summary line `WIKI[model,lang,224px] n/m ...`;
and results/runs/<dataset_version>/<block>.json + .csv (the aggregated record, keyed by (dataset_version, id)).
Environment: run it in the python that has the model's package installed (see README "Environments").
"""
from __future__ import annotations

import argparse
import datetime
import os
import threading
import pathlib
import sys
import time

from . import config, logfmt, results
from .cases import load_cases


def parse_args(argv=None):
    cfg = config.load()
    m = cfg["measure"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--set", dest="set_name", required=True, choices=sorted(cfg["blocks"]))
    ap.add_argument("--lang", required=True, choices=["en", "ja"])
    ap.add_argument("--mod", default="image", choices=["image", "text", "all"])
    ap.add_argument("--model-dir")
    ap.add_argument("--variant")
    ap.add_argument("--threads", type=int, default=m["threads"])
    ap.add_argument("--px", type=int, default=m["px"])
    ap.add_argument("--rev", type=int, default=m["rev"], choices=[0, 1])
    ap.add_argument("--gpu", action="store_true", default=m["gpu"])
    ap.add_argument("--workers", type=int, default=1, help="concurrent questions (only for remote adapters that allow it, e.g. openai; capped by the adapter)")
    ap.add_argument("--device", choices=["cpu", "cuda", "remote"], help="label recorded with the results (default: cuda with --gpu, remote for an API adapter, else cpu)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids-file")
    ap.add_argument("--skip-log")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--log-dir", default=str(config.work_dir() / "logs" / "timed"))
    ap.add_argument("--dataset-version", default=cfg["dataset"]["version"])
    ap.add_argument("--force", action="store_true", help="run even when the block's log already has its summary line")
    ap.add_argument("--no-results", action="store_true", help="do not write results/runs/...")
    args = ap.parse_args(argv)
    args.cfg = cfg
    return args


def select_cases(args) -> list[dict]:
    cases = load_cases(args.set_name, version=args.dataset_version)
    if args.mod != "all":
        cases = [c for c in cases if c["modality"] == args.mod]
    if args.limit:
        cases = cases[: args.limit]
    cases = [c for c in cases if args.lang in c]                 # single-language questions exist only in their language
    if args.ids_file:
        keep = set(pathlib.Path(args.ids_file).read_text(encoding="utf-8").split())
        cases = [c for c in cases if c["id"] in keep]
        print("sample: %d questions" % len(cases), flush=True)
    if args.skip_log:
        done = set()
        for p in args.skip_log.split(","):
            done |= set(logfmt.parse(pathlib.Path(p)))
        cases = [c for c in cases if c["id"] not in done]
        print("fill-in: %d questions not in the earlier log" % len(cases), flush=True)
    return cases


def prepare_images(case, small: pathlib.Path, px: int) -> list[str]:
    """The pictures as the models get them: longest side ``px``, LANCZOS. A picture already in ``small`` (made by an earlier run, or
    fetched from the Release's images-224px.zip and sha256-checked) is used as it is."""
    from PIL import Image
    out = []
    for n in case["images"]:
        outp = small / pathlib.Path(n).name
        if not outp.exists():
            im = Image.open(n).convert("RGB")
            im.thumbnail((px, px), Image.LANCZOS)
            tmp = outp.with_name("%s.%d.%d.tmp.png" % (outp.stem, os.getpid(), threading.get_ident()))   # atomic: threads share pictures
            im.save(tmp)
            try:
                os.replace(tmp, outp)
            except OSError:                                        # Windows: another thread just made it (and may be reading it)
                if not outp.exists():
                    raise
            finally:
                if tmp.exists():
                    tmp.unlink()
        out.append(str(outp))
    return out


def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    from adapters import GPU_PROVIDERS, REGISTRY, REPOS, load
    if args.model not in REGISTRY:
        raise SystemExit("unknown model %r (kev is not part of the picture bench)" % args.model)
    code = args.cfg["blocks"][args.set_name]
    block = "%s_%s_%s_%d%s" % (args.model, code, args.lang, args.px, args.suffix)
    log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / (block + ".log")
    if logfmt.is_finished(log_path) and not args.force:
        print("%s: already finished (%s)" % (block, log_path))
        return 0

    cases = select_cases(args)
    earlier = logfmt.parse(log_path)                              # resume: what this block's log already has
    todo = [c for c in cases if c["id"] not in earlier]
    if earlier:
        print("resume: %d of %d questions already in %s" % (len(cases) - len(todo), len(cases), log_path.name), flush=True)

    providers = GPU_PROVIDERS if args.gpu else None
    part = "text" if args.mod == "text" else "wiki"
    base = load(args.model, model_dir=args.model_dir, threads=args.threads, providers=providers, lang=args.lang, part=part,
                variant=args.variant)
    info = getattr(base, "info", {})
    remote = bool(info.get("remote"))
    workers = max(1, min(args.workers, int(info.get("max_workers", 1)))) if remote else 1

    def ask(*a, **k):                                              # -> (answer, wall ms of this call); thread-safe (no shared list)
        t = time.perf_counter()
        return base(*a, **k), int((time.perf_counter() - t) * 1000)

    # v1 has its own 224 px cache: a v1 picture can share a file name with a different legacy one (rsn-0102.png), so the caches must not mix
    small = config.work_dir() / ("px%d" % args.px + ("" if args.dataset_version == "legacy" else "_" + args.dataset_version))
    small.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.perf_counter()
    logf = open(log_path, "a", encoding="utf-8", newline="\n")

    def emit(line):
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    def one(c):
        """-> (case, got, ok, rev_ok, ms, error text or None)"""
        L = c[args.lang]
        try:
            imgs = prepare_images(c, small, args.px)
            got, ms = ask(L["state"], imgs, c["kind"], L["instr"], L["options"])
            ok = got == c["expected"]
            rev_ok = None
            if c["kind"] == "choice" and args.rev:
                ro = list(reversed(L["options"]))
                got_r, _ = ask(L["state"], imgs, c["kind"], L["instr"], ro)
                rev_ok = (len(ro) - 1 - got_r) == c["expected"]
            return c, got, ok, rev_ok, ms, None
        except Exception as e:                                     # noqa: BLE001  (a limit of the model -> got=NA, counted wrong)
            return c, "NA", False, None, 0, str(e)[:100].replace("\n", " ")

    def finish_line(res):
        c, got, ok, rev_ok, ms, err = res
        if err:
            emit("   error: " + err)
        emit("%s %-18s got=%s exp=%s rev=%s ms=%d" % ("ok " if ok else "XX ", c["id"], got, c["expected"], rev_ok, ms))

    if workers > 1:
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(workers) as pool:
            for res in pool.map(one, todo):                       # results come back in order
                finish_line(res)
    else:
        for c in todo:
            finish_line(one(c))

    log = logfmt.parse(log_path)                                  # the tally covers the whole block, earlier session included
    mine = [c for c in cases if c["id"] in log]
    n = len(mine)
    acc = sum(log[c["id"]]["ok"] for c in mine)
    ch = [c for c in mine if c["kind"] == "choice" and log[c["id"]]["rev"] != "None"]
    both = sum(1 for c in ch if log[c["id"]]["ok"] and log[c["id"]]["rev"] == "True")
    emit("%s[%s,%s,%dpx] %d/%d  choice fwd+rev both correct %d/%d  (%.0f s)" %
         ("WIKI", args.model, args.lang, args.px, acc, n, both, len(ch), time.perf_counter() - t0))
    logf.close()

    if not args.no_results:
        rows = []
        for c in mine:
            r = log[c["id"]]
            rows.append(dict(id=c["id"], kind=c["kind"], difficulty=c.get("difficulty"), expected=c["expected"], got=r["got"], ok=r["ok"],
                             rev_ok=None if r["rev"] == "None" else r["rev"] == "True", ms=r["ms"]))
        import PIL
        meta = dict(dataset_version=args.dataset_version, block=block, model=args.model, model_repo=REPOS[args.model],
                    model_tag=os.environ.get("MODEL_TAG") or "local", variant=info.get("variant"),
                    providers_requested=["remote"] if remote else (providers or ["CPUExecutionProvider"]), providers_used=info.get("providers_used"),
                    threads=args.threads, px=args.px, rev=args.rev, lang=args.lang, set=args.set_name, modality=args.mod,
                    questions_in_block=len(cases), limits=info.get("limits"), pillow=PIL.__version__,
                    device=args.device or ("remote" if remote else "cuda" if args.gpu else "cpu"), workers=workers,
                    endpoint=info.get("endpoint"), model_name=info.get("model_name"),
                    usage=dict(info["usage"]) if info.get("usage") else None,     # this session's requests / tokens (remote adapters)
                    started=started, finished=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                    resumed=bool(earlier))
        print("results:", results.write(block, meta, rows), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
