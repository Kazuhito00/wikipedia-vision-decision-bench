# -*- coding: utf-8 -*-
"""Build the 320 px pictures Release assets (images-320px.zip + SHA256SUMS) in dist/v1/release320/ (git-ignored). NOTHING IS UPLOADED.

    uv run python tools/make_images_320.py [--out dist/v1/release320] [--attribution-from dist/v1/images-224px.zip]

Every picture an evaluated v1 question uses (member name = its logical path, e.g. data/images/<sha1>.jpg) is made from its ORIGINAL file on this
machine (the 640 px Commons thumbnail, or the 640x480 drawn picture; never from the 224 px copy) by datasets/imgfit.py: scaled to fit inside a
320 x 320 square (LANCZOS) and centred on mid-grey (128). Files named .jpg are stored as JPEG (quality 95), the others as PNG.
Also written: datasets/manifests/images_v1_320.json (path -> sha256 of the 320 px file; no pictures) -- colab/run_colab.py and the checks read it.
ATTRIBUTION.md is copied from the 224 px zip (same pictures, same licenses). The zip is deterministic (sorted, fixed timestamps).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from datasets import build_v1, imgfit  # noqa: E402
from tools.make_images_release import question_pictures, sha256_file  # noqa: E402

NAME = "images-320px.zip"
MANIFEST = ROOT / "datasets" / "manifests" / "images_v1_320.json"
STAMP = (2026, 10, 15, 0, 0, 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "dist" / "v1" / "release320"))
    ap.add_argument("--attribution-from", default=str(ROOT / "dist" / "v1" / "images-224px.zip"))
    ap.add_argument("--owner", default="Kazuhito00")
    ap.add_argument("--tag", default="v0.0.1")
    args = ap.parse_args(argv)
    from PIL import Image
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    roots = build_v1.image_roots()
    paths = sorted(question_pictures())
    blobs, missing = {}, []
    for p in paths:
        f = build_v1.find_original(p, roots)
        if f is None:
            missing.append(p)
            continue
        blobs[p] = imgfit.encode(Image.open(f), pathlib.PurePosixPath(p).name, imgfit.PX)
    if missing:
        raise SystemExit("%d original picture(s) not found, e.g. %s (set WIKIQA_DATA_ROOT / WIKIQA_IMAGES)" % (len(missing), missing[:3]))
    with zipfile.ZipFile(args.attribution_from) as z:
        attribution = z.read("ATTRIBUTION.md")
    zpath = out / NAME
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        for n, data in [("ATTRIBUTION.md", attribution)] + sorted(blobs.items()):
            zi = zipfile.ZipInfo(n, STAMP)
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, data)
    sums = {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()}
    MANIFEST.write_text(json.dumps(dict(px=imgfit.PX, fit="letterbox", pad=list(imgfit.PAD), recipe="datasets/imgfit.py encode(): LANCZOS fit inside px x px, "
                                        "centred on pad; .jpg -> JPEG q95 subsampling 0, else PNG", count=len(sums), sha256_320=sums),
                                   indent=0, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    # re-read the zip and check it against the manifest, and every picture is exactly 320 x 320
    with zipfile.ZipFile(zpath) as z:
        got = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n != "ATTRIBUTION.md"}
        bad = [n for n in got if Image.open(io.BytesIO(z.read(n))).size != (imgfit.PX, imgfit.PX)]
    if got != sums or bad:
        raise SystemExit("zip does not match: %d differ, %d not 320x320" % (len(set(got.items()) ^ set(sums.items())), len(bad)))
    (out / "SHA256SUMS").write_text("%s  %s\n" % (sha256_file(zpath), NAME), encoding="utf-8", newline="\n")
    print("wrote %s: %d pictures + ATTRIBUTION.md, %.1f MB; sha256 %s" % (zpath, len(sums), zpath.stat().st_size / 1e6, sha256_file(zpath)))
    print("manifest: %s" % MANIFEST)
    print("\nUpload (YOU run this; nothing was uploaded):")
    print("  gh release create %s --repo %s/wikipedia-vision-decision-bench --title \"v1 images (320 px letterbox)\" \\" % (args.tag, args.owner))
    print("      --notes \"Dataset v1: 320x320 letterboxed pictures (mid-grey 128). See ATTRIBUTION.md inside the zip.\" \\")
    print("      \"%s\" \"%s\"" % (str(zpath).replace("\\", "/"), str(out / "SHA256SUMS").replace("\\", "/")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
