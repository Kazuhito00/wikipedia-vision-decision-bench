# -*- coding: utf-8 -*-
"""One-off: add a `host` key to result JSONs that were measured before the runner recorded it (host.source = "backfilled").

    uv run python -m tools.backfill_host [--runs-dir results/runs/v1] [--dry-run]

The hardware is collected NOW on this machine (runner/hostinfo.py); the software versions that cannot be read from here are the ones
documented in runner/README.md (CPU blocks: onnxruntime 1.30, GPU blocks: onnxruntime-gpu 1.31, CUDA 13.4 / cuDNN 9.20); they are listed
in host["reported_fields"]. Threads come from the block's own record. Only the `host` key is added: nothing else in the file changes.
A file that already has a host is skipped.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runner import hostinfo  # noqa: E402

REPORTED = {"cpu": dict(onnxruntime={"onnxruntime": "1.30.0"}), "cuda": dict(onnxruntime={"onnxruntime-gpu": "1.31.0"}, cuda_runtime="13.4", cudnn="9.20")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-dir", default=str(ROOT / "results" / "runs" / "v1"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    n = 0
    for p in sorted(pathlib.Path(args.runs_dir).glob("*_v1all_*_224*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if "host" in rec:
            print("skip (has host):", p.name)
            continue
        remote = rec.get("device") == "remote"
        h = hostinfo.collect(threads=rec.get("threads"), remote=remote, source="backfilled")
        rep = REPORTED.get(rec.get("device"), {})
        reported = []
        if "onnxruntime" in rep and not remote:
            h["onnxruntime"] = rep["onnxruntime"]
            reported.append("onnxruntime")
        for k in ("cuda_runtime", "cudnn"):
            if k in rep and h.get("gpu"):
                h["gpu"][k] = rep[k]
                reported.append("gpu." + k)
        h["reported_fields"] = reported
        h["backfill_note"] = "hardware collected after the measurement on the same PC; fields in reported_fields come from runner/README.md"
        rec["host"] = hostinfo.sanitize(h)
        print("%s %s: %s" % ("would add" if args.dry_run else "add", p.name, h["label"]))
        if not args.dry_run:
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n += 1
    print("%d file(s)" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
