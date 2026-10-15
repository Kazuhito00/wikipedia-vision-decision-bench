# -*- coding: utf-8 -*-
"""Prepare the assets of the images Release (images-224px.zip + SHA256SUMS) in dist/ (git-ignored). NOTHING IS UPLOADED.

    uv run python tools/make_images_release.py [--src dist/build] [--out dist/build/release] [--max-part-gib 1.9]

Input: dist/build/images-224px.zip and dist/build/images_v1.json, made by ``python -m datasets.build_v1`` (the 224 px pictures every v1 question uses;
member names = the logical paths of the question rows, e.g. data/images/<sha1>.jpg, data/synthetic/syn-0001.png, generated/rsn-2040.png;
ATTRIBUTION.md lists title / author / license / source URL of every Wikimedia Commons picture, from the manifest's metadata).
What this script adds: it CHECKS the zip (every picture the v1 questions use is in it, every member matches the sha256_224 of images_v1.json,
ATTRIBUTION.md names every Commons picture) and writes the Release folder:
    <out>/images-224px.zip        a copy (or, above --max-part-gib, images-224px.zip.part00, .part01, ... : GitHub's limit is 2 GiB per asset)
    <out>/SHA256SUMS              sha256sum format, one line per asset (plus the joined zip when split) -- colab/run_colab.py reads it
It prints the upload commands. The pictures come from Wikimedia Commons (licenses differ per file; CC0 / public domain only, see ATTRIBUTION.md);
nothing from Wikipedia articles is included. The folder is git-ignored (*.zip, dist/).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = "images-224px.zip"


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def question_pictures() -> set[str]:
    """Logical paths (data/images/..., generated/...) of every picture the evaluated v1 questions use."""
    sys.path.insert(0, str(ROOT))
    from datasets import loader
    cases = loader.load_v1_cases(None, images_root=pathlib.PurePosixPath("."), strict_passages=False)
    return {str(p).replace("\\", "/").lstrip("./") for c in cases for p in c["images"]}


def check(zpath: pathlib.Path, manifest: dict) -> list[str]:
    problems = []
    with zipfile.ZipFile(zpath) as z:
        members = {i.filename for i in z.infolist() if not i.is_dir()}
        want = {e["path"]: e for e in manifest["images"]}
        used = question_pictures()
        missing = sorted(used - members)
        if missing:
            problems.append("%d picture(s) used by the questions are not in the zip, e.g. %s" % (len(missing), missing[:3]))
        extra = sorted(members - used - {"ATTRIBUTION.md"})
        if extra:
            print("note: %d member(s) are not used by an evaluated question (dropped questions?), e.g. %s" % (len(extra), extra[:3]))
        bad = [n for n in sorted(members & set(want)) if want[n].get("sha256_224") and hashlib.sha256(z.read(n)).hexdigest() != want[n]["sha256_224"]]
        if bad:
            problems.append("%d member(s) differ from images_v1.json sha256_224, e.g. %s" % (len(bad), bad[:3]))
        unknown = sorted(members - set(want) - {"ATTRIBUTION.md"})
        if unknown:
            problems.append("%d member(s) are not in images_v1.json, e.g. %s" % (len(unknown), unknown[:3]))
        if "ATTRIBUTION.md" not in members:
            problems.append("ATTRIBUTION.md is missing")
        else:
            text = z.read("ATTRIBUTION.md").decode("utf-8")
            commons = [e for e in manifest["images"] if e.get("source") == "commons"]
            lacking = [e["path"] for e in commons if e["path"] in members and e["path"] not in text]
            if lacking:
                problems.append("ATTRIBUTION.md lacks %d Commons picture(s), e.g. %s" % (len(lacking), lacking[:3]))
            no_meta = [e["path"] for e in commons if not (e.get("license") and e.get("source_url"))]
            if no_meta:
                problems.append("%d Commons picture(s) have no license / source_url in the manifest, e.g. %s" % (len(no_meta), no_meta[:3]))
        print("zip: %d members (%d pictures + ATTRIBUTION.md), %d pictures used by the questions" % (len(members), len(members) - 1, len(used)))
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(ROOT / "dist" / "build"))
    ap.add_argument("--out", default="")
    ap.add_argument("--max-part-gib", type=float, default=1.9)
    ap.add_argument("--owner", default="Kazuhito00")
    ap.add_argument("--tag", default="v0.0.0")
    args = ap.parse_args(argv)
    src = pathlib.Path(args.src)
    out = pathlib.Path(args.out) if args.out else src / "release"
    zpath, mpath = src / NAME, src / "images_v1.json"
    if not zpath.exists() or not mpath.exists():
        raise SystemExit("%s / %s not found: run `uv run python -m datasets.build_v1` first (needs the pictures on this machine)" % (zpath, mpath))
    problems = check(zpath, json.loads(mpath.read_text(encoding="utf-8")))
    if problems:
        raise SystemExit("checks failed:\n  " + "\n  ".join(problems))
    print("checks: OK")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(NAME + "*"):
        old.unlink()
    total = zpath.stat().st_size
    limit = int(args.max_part_gib * 1024 ** 3)
    sums, assets = [], []
    if total <= limit:
        shutil.copy2(zpath, out / NAME)
        assets = [out / NAME]
        sums.append((sha256_file(out / NAME), NAME))
    else:
        with open(zpath, "rb") as f:
            i = 0
            while True:
                chunk = f.read(limit)
                if not chunk:
                    break
                pp = out / ("%s.part%02d" % (NAME, i))
                pp.write_bytes(chunk)
                assets.append(pp)
                sums.append((hashlib.sha256(chunk).hexdigest(), pp.name))
                i += 1
        sums.append((sha256_file(zpath), NAME + ".joined"))             # informational: the sha256 of the joined zip
    (out / "SHA256SUMS").write_text("".join("%s  %s\n" % s for s in sums), encoding="utf-8", newline="\n")
    assets.append(out / "SHA256SUMS")
    print("wrote %s (%d asset(s), %.1f MB in total)" % (out, len(assets), sum(a.stat().st_size for a in assets) / 1e6))
    for a in assets:
        print("  %-28s %10d bytes" % (a.name, a.stat().st_size))
    print("\nUpload (YOU run this; nothing was uploaded):")
    print("  gh release create %s --repo %s/wikipedia-vision-decision-bench --title \"v1 images (224 px)\" \\" % (args.tag, args.owner))
    print("      --notes \"Dataset v1: 224 px pictures (Wikimedia Commons CC0/public domain + pictures drawn by this repository's scripts). See ATTRIBUTION.md inside the zip.\" \\")
    print("      " + " ".join("\"%s\"" % str(a).replace("\\", "/") for a in assets))
    print("  (the tag %s may exist already: then `gh release upload %s <files> --repo ...`)" % (args.tag, args.tag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
