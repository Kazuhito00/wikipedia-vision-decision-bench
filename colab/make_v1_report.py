# -*- coding: utf-8 -*-
"""Build the v1 report page (report/v1_report.py) from ANY set of results, without editing report/.

    python colab/make_v1_report.py [--out work/colab/out/v1_report.html] [--runs-dir results/runs/v1] [--include-all-blocks] [--strict-passages]

report/v1_report.py detects the models and runs itself (report/v1_models.py: `<model>_v1all_<lang>_224[_cpu|_cuda].csv|json`), so no model
list is kept here. What this wrapper still does is to make the inputs that report expects from what the Colab run produced, in a TEMPORARY
folder (the real dist/ and results/ are never written):

  * results/runs/v1/<model>_<set code>_<lang>_224<suffix>.json|csv blocks (photo / biz / rsn / txt / all / new) are merged per
    (model, suffix, language) into one run (`<model>_v1all_<lang>_224<suffix>`);
  * only the (id, language) pairs that EVERY run answered are compared (a run that did not ask a question must not count as wrong);
  * dist/build/cases_v1.jsonl and questions_v1.jsonl are rebuilt from datasets/questions (build_v1's own record functions, no pictures needed).
    A text-only question whose Wikipedia passage is not on the machine gets a placeholder text (the page says so; the right/wrong counts do not
    depend on it). --strict-passages makes a missing passage an error instead (use it where passages.json exists and the text matters);
  * display names come from adapters.REGISTRY; colours and the local/api kind from the defaults of report/v1_models.py (unknown models: automatic).
  * timing-only blocks (``..._cpu_speed<N>``, `speed_only: true`) never become a run: they are written as speed_cpu_v1.json and shown only in the
    speed section (CPU reference next to the GPU time of the same questions);
Only blocks that a Colab run made (a sidecar in work/colab/blocks) are used, unless --include-all-blocks.
Pictures: thumbnails are embedded when images-320px.zip (or the earlier images-224px.zip) is given (--images-zip, or dist/v1/); otherwise the page has none.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import sys
import shutil
import zipfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CODES = ("v1photo", "v1biz", "v1rsn", "v1txt", "v1all", "v1new")


def collect(runs_dir: pathlib.Path, blocks_dir: pathlib.Path, include_all: bool) -> dict:
    """{(model, suffix): {lang: [(block, code, json, csv rows)]}}"""
    from report import v1_models as vm
    out: dict = {}
    for p in sorted(runs_dir.glob("*.json")):
        m = vm.parse_stem(p.stem)
        if not m or m["code"] not in CODES:
            continue
        if not include_all and not (blocks_dir / (p.stem + ".env.json")).exists():
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("dataset_version") != "v1":
            continue
        rows = list(csv.DictReader(open(p.with_suffix(".csv"), encoding="utf-8", newline=""))) if p.with_suffix(".csv").exists() else []
        out.setdefault((m["model"], m["suffix"]), {}).setdefault(m["lang"], []).append((p.stem, m["code"], rec, rows))
    return out


def collect_speed(runs_dir: pathlib.Path, blocks_dir: pathlib.Path, include_all: bool) -> dict:
    """Timing-only blocks (``<model>_<code>_<lang>_224_cpu_speed<N>``, record speed_only=true) -> {"models": {model: {...}}} for speed_cpu_v1.json.
    They are NOT runs: the accuracy tables, the common question set, the heat maps and the Venn diagrams never see them (report/v1_models.py
    ignores the ``_speed`` suffix); report/v1_report.py shows them only in the speed section, next to the same model's GPU time."""
    from report import v1_models as vm
    out: dict = {}
    for p in sorted(runs_dir.glob("*.json")):
        m = vm.parse_speed_stem(p.stem)
        if not m:
            continue
        if not include_all and not (blocks_dir / (p.stem + ".env.json")).exists():
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("dataset_version") != "v1" or not rec.get("speed_only"):
            continue
        rows = list(csv.DictReader(open(p.with_suffix(".csv"), encoding="utf-8", newline=""))) if p.with_suffix(".csv").exists() else []
        e = out.setdefault(m["model"], dict(model=m["model"], device=rec.get("device"), blocks=[], rows=[], planned=0, stopped_early=False, max_seconds=None,
                                            threads=rec.get("threads"), host=None, calibration=[], providers=rec.get("providers_used")))
        e["blocks"].append(p.stem)
        e["planned"] += rec.get("questions_in_block") or rec.get("speed_questions") or len(rows)
        e["stopped_early"] = e["stopped_early"] or bool(rec.get("speed_stopped_early"))
        e["max_seconds"] = rec.get("speed_max_seconds") or e["max_seconds"]
        e["rows"] += [dict(id=r["id"], lang=r["lang"], ms=int(float(r["ms"] or 0)), na=r["got"] == "NA") for r in rows]
        h = rec.get("host") or {}
        if h and not e["host"]:
            cpu = h.get("cpu") or {}
            e["host"] = dict(label=h.get("label"), host_id=h.get("host_id"), cpu=cpu.get("name"), physical_cores=cpu.get("physical_cores"),
                             logical_cores=cpu.get("logical_cores"), ram_gb=h.get("ram_gb"), threads=h.get("threads"), source=h.get("source"))
        c = rec.get("calibration")
        e["calibration"].append(c.get("timing_valid") if c else None)
    for e in out.values():                       # valid: every block calibrated and within the limit; None: no calibration record
        flags = e.pop("calibration")
        e["timing_valid"] = None if (not flags or any(f is None for f in flags)) else all(flags)
    return dict(models=out)


def extract_images(zpath: pathlib.Path, dest: pathlib.Path) -> int:
    """Extract the picture files (data/..., generated/...; not ATTRIBUTION.md) of a dataset zip into dest, keeping the zip's relative paths.
    Entries that would leave `dest` are skipped; a file that already has the right size is left alone. -> number of pictures available."""
    n = 0
    root = dest.resolve()
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            target = (dest / info.filename).resolve()
            if root not in target.parents:
                continue
            n += 1
            if target.exists() and target.stat().st_size == info.file_size:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    return n


def merge_rows(blocks) -> list:
    seen, rows = set(), []
    for _, code, _, rs in sorted(blocks, key=lambda b: b[1] != "v1all"):      # an `all` block first: it covers the others
        for r in rs:
            if r["id"] not in seen:
                seen.add(r["id"])
                rows.append(r)
    return rows


def merge_meta(blocks) -> dict:
    metas = [b[2] for b in blocks]
    m = dict(metas[0])
    m["questions_in_block"] = sum(x.get("questions_in_block") or 0 for x in metas)
    m["started"] = min(x.get("started") or "" for x in metas) or None
    m["finished"] = max(x.get("finished") or "" for x in metas) or None
    gm = [x["gpu_memory"] for x in metas if x.get("gpu_memory")]
    if gm:                                                    # peak GPU memory of the run: the largest over its blocks
        m["gpu_memory"] = {k: max((g[k] for g in gm if g.get(k) is not None), default=None) for k in ("process_peak", "gpu_peak", "gpu_baseline", "gpu_delta", "gpu_total")}
    us = [x["usage"] for x in metas if x.get("usage")]
    if us:
        m["usage"] = {k: sum(u.get(k) or 0 for u in us) for k in us[0]}
    hosts = {x["host"]["host_id"]: x["host"] for x in metas if x.get("host") and x["host"].get("host_id")}
    if len(hosts) > 1 and m.get("host"):                      # blocks of one run measured on different machines: say so (the report warns)
        m["host"] = dict(m["host"], also_resumed_on=[{k: h.get(k) for k in ("host_id", "label", "threads", "source")}
                                                     for i, h in hosts.items() if i != m["host"].get("host_id")])
    return m


def build_dist_lite(dist: pathlib.Path, keep: dict, strict_passages: bool = False) -> int:
    """cases_v1.jsonl / questions_v1.jsonl without pictures, restricted to the (id, lang) pairs in `keep` (id -> set of langs)."""
    from datasets import build_v1 as B, loader
    rows = loader.load_rows("v1")
    rowmap = {r["id"]: r for r in rows}
    cases = [B.case_record(c, rowmap) for c in loader.load_v1_cases(images_root=pathlib.Path("."), strict_passages=strict_passages)]
    kept = []
    for c in cases:
        langs = [l for l in c["langs"] if l in keep.get(c["id"], ())]
        if langs:
            kept.append(dict(c, langs=langs))
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "cases_v1.jsonl").write_bytes(B.jl(kept))
    (dist / "questions_v1.jsonl").write_bytes(B.jl([B.question_record(r) for r in rows]))
    return len(kept)


def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    work = pathlib.Path(os.environ.get("BENCH_WORK") or ROOT / "work")
    ap.add_argument("--out", default=str(work / "colab" / "out" / "v1_report.html"))
    ap.add_argument("--runs-dir", default=str(ROOT / "results" / "runs" / "v1"))
    ap.add_argument("--images-zip", default="", help="images-320px.zip (or images-224px.zip) to embed thumbnails from (default: dist/v1/images-320px.zip, release320/, or images-224px.zip, the first that exists)")
    ap.add_argument("--no-images", action="store_true", help="build the page without pictures")
    ap.add_argument("--images-original-zip", default="", help="images-original.zip (default: dist/build/images-original.zip when it exists): with it the picture dialog also offers the originals")
    ap.add_argument("--no-image-files", action="store_true", help="do not write the <page>_images folder (input / original files next to the page); the dialog then shows the embedded thumbnail only")
    ap.add_argument("--blocks-dir", default=str(work / "colab" / "blocks"))
    ap.add_argument("--include-all-blocks", action="store_true", help="also use blocks that this machine did not run (no Colab sidecar)")
    ap.add_argument("--strict-passages", action="store_true",
                    help="a text-only question without its Wikipedia passage on this machine is an error (default: a placeholder text)")
    a = ap.parse_args(argv)

    from report import v1_models as vm, v1_report
    try:
        from adapters import REGISTRY
        vm.set_names(REGISTRY)
    except Exception:                                                    # the registry only gives the display names
        pass
    groups = collect(pathlib.Path(a.runs_dir), pathlib.Path(a.blocks_dir), a.include_all_blocks)
    if not groups:
        print("no v1 results to report (blocks of this machine: none in %s)" % a.runs_dir)
        return 2
    # runs: one per (model, suffix); both languages (an absent one stays absent)
    runs = {}
    for (model, suffix), by_lang in groups.items():
        runs[(model, suffix)] = {lg: (merge_rows(b), merge_meta(b)) for lg, b in by_lang.items()}
    pairs = None
    for k, by in runs.items():
        have = {(r["id"], lg) for lg, (rows, _) in by.items() for r in rows}
        pairs = have if pairs is None else pairs & have
    if not pairs:
        print("the runs have no (question, language) in common: nothing to compare (check --sample / sets of each model)")
        return 2
    keep: dict = {}
    for i, lg in pairs:
        keep.setdefault(i, set()).add(lg)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="v1report_"))
    dist, runs_tmp = tmp / "dist", tmp / "runs"
    runs_tmp.mkdir(parents=True)
    n_cases = build_dist_lite(dist, keep, a.strict_passages)
    for (model, suffix), by in sorted(runs.items()):
        for lg, (rows, meta) in by.items():
            rows = [r for r in rows if (r["id"], lg) in pairs]
            stem = "%s_v1all_%s_224%s" % (model, lg, suffix)
            cols = list(rows[0]) if rows else ["dataset_version", "id", "model", "lang", "kind", "expected", "got", "ok", "rev_ok", "ms"]
            with open(runs_tmp / (stem + ".csv"), "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            (runs_tmp / (stem + ".json")).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    speed = collect_speed(pathlib.Path(a.runs_dir), pathlib.Path(a.blocks_dir), a.include_all_blocks)
    if speed["models"]:
        (runs_tmp / "speed_cpu_v1.json").write_text(json.dumps(speed, ensure_ascii=False), encoding="utf-8")
        print("CPU speed reference (timing only, not in the accuracy tables): %s" % ", ".join(
            "%s %d q" % (k, len(v["rows"])) for k, v in sorted(speed["models"].items())))
    found = vm.discover_runs(runs_tmp)
    print("v1 report: %d runs (%s), %d (question, language) pairs answered by every run, %d questions" %
          (len(found), ", ".join(sorted(found)), len(pairs), n_cases))
    zp = pathlib.Path(a.images_zip) if a.images_zip else next((p for p in (ROOT / "dist" / "v1" / "images-320px.zip", ROOT / "dist" / "build" / "images-224px.zip") if p.exists()), ROOT / "dist" / "v1" / "images-320px.zip")
    args = ["--out", str(a.out), "--runs-dir", str(runs_tmp), "--dist-dir", str(dist)]
    if a.no_images or not zp.exists():
        print("no pictures in the page (%s)" % ("--no-images" if a.no_images else "%s not found; pass --images-zip" % zp))
        args.append("--no-images")
    else:
        shutil.copyfile(zp, dist / zp.name)          # thumbnails are embedded in the page (the zip itself is not kept)
        if not a.no_image_files:
            op = pathlib.Path(a.images_original_zip) if a.images_original_zip else ROOT / "dist" / "build" / "images-original.zip"
            folder = pathlib.Path(a.out).with_name(pathlib.Path(a.out).stem + "_images")
            n224 = extract_images(zp, folder / "input")
            nor = extract_images(op, folder / "original") if op.exists() else 0
            print("picture files next to the page: %s (input: %d, original: %d)  -- local use only, never publish or commit them" % (folder, n224, nor))
            if n224:
                args += ["--images-base", folder.name]
    return v1_report.main(args)


if __name__ == "__main__":
    sys.exit(main())
