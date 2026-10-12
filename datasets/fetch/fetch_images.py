# -*- coding: utf-8 -*-
"""fetch: get the pictures of the image list (manifest) and verify them by sha256. Pictures go to the git-ignored work/ folder.

From Commons (default):
  1. ask the API for the current sha1 and the thumbnail URL (``iiurlwidth`` = the manifest's source width, 640 px);
  2. download the thumbnail to work/data/images/<file> (skipped when the file is already there with the right sha256);
  3. compare its sha256 with ``sha256_original``:
       match                                  fine
       differs, Commons sha1 unchanged        "thumbnail re-rendered": Commons made the thumbnail again, the original is the same
       differs, Commons sha1 changed          "replaced": the file was replaced; the evaluation's picture is no longer the one on Commons
  4. shrink to 224 px (longest side, LANCZOS, JPEG: the same recipe as runner/run.py) into work/px224/<file> and compare with ``sha256_224``;
     a difference with an unchanged original is only a WARNING: a Pillow / libjpeg version writes different pixels. For an exact
     reproduction use the Release's images-224px.zip.
From a Release (``--from-release DIR``): read images-224px.zip and/or images-original.zip in DIR, check EVERY member against the manifest's
sha256 (a wrong or unknown member stops the extraction of that file), and extract into the same places. No network.
Rendered pictures (synthetic / reasoning) are not on Commons: they come from datasets/synthetic or from the Release's 224 px zip.
"""
from __future__ import annotations

import hashlib
import io
import pathlib
import zipfile
from typing import Callable

from . import commons, http

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = http.WORK
IMAGES = WORK / "data" / "images"
PX224 = WORK / "px224"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def shrink(data: bytes, px: int) -> bytes:
    """The model input: longest side ``px``, LANCZOS, saved like runner/run.py does (PIL default JPEG settings)."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((px, px), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG")
    return buf.getvalue()


def fetch_commons(manifest: dict, *, api: Callable = http.api_json, download: Callable = http.fetch, limit: int | None = None,
                  images_dir: pathlib.Path = IMAGES, px_dir: pathlib.Path = PX224, update_hashes: bool = False) -> dict:
    """-> a report dict (counts and the files that differ). ``update_hashes``: fill empty sha256 fields (after ``refresh``) instead of comparing."""
    imgs = manifest["images"][:limit] if limit else manifest["images"]
    imgs = [im for im in imgs if not im.get("excluded")]
    px = manifest.get("input_px", 224)
    got = commons.image_info([im["title"] for im in imgs], px=manifest.get("source_width_px", 640), api=api, use_cache=False)
    images_dir.mkdir(parents=True, exist_ok=True)
    px_dir.mkdir(parents=True, exist_ok=True)
    rep = dict(images=len(imgs), original=dict(match=0, thumbnail_rerendered=0, replaced=0, missing=0, cached=0),
               px224=dict(match=0, differs=0), problems=[])
    for im in imgs:
        g = got[im["title"]]
        dest = images_dir / im["file"]
        data = None
        if dest.exists() and im.get("sha256_original") and sha256_bytes(dest.read_bytes()) == im["sha256_original"]:
            data = dest.read_bytes()
            rep["original"]["cached"] += 1
        else:
            if g["state"] != "found" or not g["info"].get("thumb_url"):
                rep["original"]["missing"] += 1
                rep["problems"].append(dict(file=im["file"], title=im["title"], problem="missing on Commons (%s)" % g["state"]))
                continue
            data = download(g["info"]["thumb_url"], gap=0.3)
            h = sha256_bytes(data)
            if update_hashes and not im.get("sha256_original"):
                im["sha256_original"] = h
            if h == im.get("sha256_original"):
                rep["original"]["match"] += 1
                dest.write_bytes(data)
            elif g["info"]["sha1"] == im.get("sha1"):
                rep["original"]["thumbnail_rerendered"] += 1
                rep["problems"].append(dict(file=im["file"], title=im["title"], problem="thumbnail re-rendered (Commons sha1 unchanged)"))
                dest.write_bytes(data)
            else:
                rep["original"]["replaced"] += 1
                rep["problems"].append(dict(file=im["file"], title=im["title"], problem="replaced (Commons sha1 changed)"))
                continue                                             # not saved: it is not the picture the questions were written for
        small = shrink(data, px)
        h224 = sha256_bytes(small)
        if update_hashes and not im.get("sha256_224"):
            im["sha256_224"] = h224
        if h224 == im.get("sha256_224"):
            rep["px224"]["match"] += 1
        else:
            rep["px224"]["differs"] += 1
            rep["problems"].append(dict(file=im["file"], title=im["title"],
                                        problem="224 px sha256 differs (warning: Pillow/libjpeg version; use the Release's images-224px.zip)"))
        (px_dir / im["file"]).write_bytes(small)
    return rep


def fetch_release(manifest: dict, release_dir: pathlib.Path, *, images_dir: pathlib.Path = IMAGES, px_dir: pathlib.Path = PX224) -> dict:
    """Extract and verify the Release zips (no network). Members are checked against the manifest's sha256 values."""
    want224 = {e["file"]: e.get("sha256_224") for e in manifest["images"] + manifest.get("rendered", [])}
    wanto = {e["file"]: e.get("sha256_original") for e in manifest["images"] if not e.get("excluded")}
    rep = {}
    for zname, want, dest in (("images-224px.zip", want224, px_dir), ("images-original.zip", wanto, images_dir)):
        z = release_dir / zname
        if not z.exists():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        r = rep[zname] = dict(ok=0, wrong_sha256=[], unknown=[], missing=[])
        seen = set()
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                base = name.split("/")[-1]
                if not base or base == "ATTRIBUTION.md":
                    continue
                data = zf.read(name)
                if base not in want:
                    r["unknown"].append(name)
                elif want[base] and sha256_bytes(data) != want[base]:
                    r["wrong_sha256"].append(name)
                else:
                    (dest / base).write_bytes(data)
                    r["ok"] += 1
                    seen.add(base)
        r["missing"] = sorted(f for f in want if f not in seen and want[f])[:50]
    return rep
