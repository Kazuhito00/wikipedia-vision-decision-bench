# -*- coding: utf-8 -*-
"""Pack the pictures for a GitHub Release: two zips in dist/ (git-ignored). NOTHING IS UPLOADED: uploading is a separate, approved step.

    uv run python -m release.make_image_release [--manifest datasets/manifests/images_legacy.json]
        [--originals DIR] [--px224 DIR] [--dist dist] [--no-rendered] [--no-write-manifest]

  images-224px.zip      the pictures as the models were given them (longest side 224 px): the 1023 Commons pictures and, unless --no-rendered,
                        the 620 pictures drawn by datasets/synthetic. About 12-16 MB. Enough to reproduce the evaluation.
  images-original.zip   the stored Commons files (the 640 px thumbnails the evaluation was made from; see the manifest's ``note``), about 290 MB.
                        Needed to re-shrink, to try another resolution, and to tell which version of a picture was evaluated.
Each zip holds ATTRIBUTION.md (title, author, license, URL per picture, made from the manifest) and the pictures flat, named by ``file``.
Only CC0 / public-domain Commons pictures go in (anything else in the manifest stops the script); excluded pictures are left out.
Every file is checked against the manifest's sha256 BEFORE it is packed, so a stale working folder cannot slip in.
The zips are deterministic (sorted names, fixed timestamps, stored without compression, fixed attributes): the same inputs give the same
sha256. Each zip must be < 2 GiB (the Release asset limit); its sha256 and size are written to the manifest ("release") and to
dist/release_manifest.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
from datasets.fetch.commons import OK_LICENSE  # noqa: E402

LIMIT = 2 * 1024 ** 3 - 1                       # < 2 GiB per asset
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def attribution(manifest: dict, with_rendered: bool) -> str:
    L = ["# Attribution", "",
         "Pictures from Wikimedia Commons, CC0 / public domain only. License labels are those on Commons when the list was made;",
         "run `python -m datasets.fetch check` to see whether Commons has changed since. No Wikipedia article text is included.", ""]
    for e in sorted(manifest["images"], key=lambda e: e["file"]):
        if e.get("excluded"):
            continue
        L.append("- %s: %s - %s - %s - <%s>" % (e["file"], e["title"], e["author"] or "unknown", e["license"], e["source_url"]))
    if with_rendered:
        L += ["", "Pictures drawn by this repository's datasets/synthetic scripts (not Commons files; deterministic, seeded):", ""]
        L += ["- %s" % e["file"] for e in sorted(manifest.get("rendered", []), key=lambda e: e["file"])]
    return "\n".join(L) + "\n"


def write_zip(path: pathlib.Path, members: list[tuple[str, bytes]]) -> dict:
    """A deterministic zip: sorted names, fixed timestamp, stored, unix attributes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        for name, data in sorted(members):
            zi = zipfile.ZipInfo(name, FIXED_DATE)
            zi.compress_type = zipfile.ZIP_STORED
            zi.create_system = 3
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)
    raw = path.read_bytes()
    if len(raw) > LIMIT:
        raise SystemExit("%s is %d bytes: a Release asset must be < 2 GiB" % (path.name, len(raw)))
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), members=len(members))


def collect(entries: list[dict], folder: pathlib.Path, key: str) -> list[tuple[str, bytes]]:
    out = []
    for e in entries:
        data = (folder / e["file"]).read_bytes()
        want = e.get(key)
        if want and hashlib.sha256(data).hexdigest() != want:
            raise SystemExit("%s differs from the manifest's %s: refusing to pack a stale file" % (folder / e["file"], key))
        if not want:
            raise SystemExit("manifest has no %s for %s" % (key, e["file"]))
        out.append((e["file"], data))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(ROOT / "datasets" / "manifests" / "images_legacy.json"))
    ap.add_argument("--originals", default=str(ROOT / "work" / "data" / "images"))
    ap.add_argument("--px224", default=str(ROOT / "work" / "px224"))
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--no-rendered", action="store_true", help="leave the drawn (synthetic / reasoning) pictures out of images-224px.zip")
    ap.add_argument("--no-write-manifest", action="store_true", help="do not record the zips' sha256 in the manifest")
    args = ap.parse_args(argv)

    mpath = pathlib.Path(args.manifest)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    commons = [e for e in manifest["images"] if not e.get("excluded")]
    bad = [e["title"] for e in commons if not OK_LICENSE.match(e["license"] or "")]
    if bad:
        raise SystemExit("not CC0 / public domain, refusing to pack: %s" % bad[:5])
    rendered = [] if args.no_rendered else manifest.get("rendered", [])
    dist = pathlib.Path(args.dist)

    m224 = collect(commons, pathlib.Path(args.px224), "sha256_224") + collect(rendered, pathlib.Path(args.px224), "sha256_224")
    mori = collect(commons, pathlib.Path(args.originals), "sha256_original")
    att = attribution(manifest, bool(rendered)).encode("utf-8")
    release = {}
    release["images-224px.zip"] = write_zip(dist / "images-224px.zip", m224 + [("ATTRIBUTION.md", att)])
    release["images-original.zip"] = write_zip(dist / "images-original.zip", mori + [("ATTRIBUTION.md", att)])
    release["images-224px.zip"]["includes_rendered"] = bool(rendered)
    (dist / "release_manifest.json").write_text(json.dumps(release, indent=1) + "\n", encoding="utf-8", newline="\n")
    if not args.no_write_manifest:
        manifest["release"] = release
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for name, r in release.items():
        print("%-22s %9.1f MB  %5d files  sha256 %s" % (name, r["bytes"] / 1e6, r["members"], r["sha256"]))
    print("written to %s (nothing uploaded)" % dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ------------------------------------------------------------------------------------------------------ catalog packs (images_v1.json)
# The pictures of a question-set catalog (``datasets/build_v1.py`` writes it): Commons pictures (CC0 / public domain only) and the
# pictures drawn by this repository's scripts. Members are named by the logical path the question rows use (``data/images/<sha1>.jpg``,
# ``data/synthetic/syn-0001.png``, ``generated/biz-1001.png``), so an unpacked zip can be used as ``images_root`` as it is, and the
# legacy-era ``rsn-0102.png`` and the v1 ``rsn-0102.png`` (different pictures) never collide. NOTHING IS UPLOADED; the legacy zips and
# images_legacy.json are never touched (output goes where the caller says).
def attribution_catalog(catalog: dict) -> str:
    L = ["# Attribution", "",
         "Dataset version: %s. No Wikipedia article text is included." % catalog["dataset_version"], "",
         "## Photographs (Wikimedia Commons, CC0 / public domain only)", "",
         "License labels are those on Commons when the list was made; run `python -m datasets.fetch check` to see whether Commons changed.", ""]
    for e in sorted(catalog["images"], key=lambda e: e["path"]):
        if e["source"] == "commons":
            L.append("- %s: %s - %s - %s - <%s>" % (e["path"], e["title"], e.get("author") or "unknown", e["license"], e["source_url"]))
    L += ["", "## Pictures drawn or captured by this repository's scripts (not Commons files)", "",
          "License: CC0-1.0 (Creative Commons Zero 1.0, Public Domain Dedication) - decided by the repository owner. This covers every",
          "picture below, i.e. the pictures made for this version (drawings, Tkinter screenshots, Japanese-specific pictures, single-picture",
          "rebuilds) and the drawn pictures reused from the earlier version. The scripts that draw them are under datasets/synthetic",
          "(deterministic: fixed seeds; text-bearing pictures also depend on the installed fonts, and the Tkinter screenshots on the OS).", "",
          "Fonts (facts only; fonts are NOT redistributed):",
          "- Japanese text drawn by datasets/synthetic/gen_v1_ja.py uses Noto Sans JP / Noto Serif JP (SIL Open Font License 1.1).",
          "- Latin text drawn by datasets/synthetic/gen.py (and the generators that import it) uses Arial when the machine has it, else DejaVu Sans.",
          "- The Tkinter pictures are screenshots of windows built by datasets/synthetic/gen_v1_tk_ui.py (our own screens; no OS title bar or",
          "  frame, no application of another company is shown). The text in them is drawn with the fonts bundled with Windows: Segoe UI",
          "  (English UI) and Yu Gothic UI (Japanese UI). The ids are listed in datasets/manifests/windows_fonts_images_v1.md.", ""]
    for e in sorted(catalog["images"], key=lambda e: e["path"]):
        if e["source"] != "commons":
            L.append("- %s: %s, seed: %s, license %s%s" % (e["path"], e["generator"], e.get("seed") or "per script", e["license"],
                                                         ", fonts: Segoe UI / Yu Gothic UI (Windows)" if e.get("fonts") else ""))
    return "\n".join(L) + "\n"


def pack_catalog(catalog: dict, get_original, get_224, dist: pathlib.Path, names=("images-224px.zip", "images-original.zip")) -> dict:
    """Write the two deterministic zips into ``dist``. ``get_original(entry)`` / ``get_224(entry)`` return the file's bytes; each is
    checked against the catalog's sha256 before it is packed. Returns {zip name: {sha256, bytes, members}}."""
    bad = [e["path"] for e in catalog["images"] if e["source"] == "commons" and not OK_LICENSE.match(e["license"] or "")]
    if bad:
        raise SystemExit("not CC0 / public domain, refusing to pack: %s" % bad[:5])
    names_seen = [e["path"] for e in catalog["images"]]
    if len(set(names_seen)) != len(names_seen):
        raise SystemExit("duplicate member names in the catalog")
    m224, mori = [], []
    for e in catalog["images"]:
        for key, getter, out in (("sha256_224", get_224, m224), ("sha256_original", get_original, mori)):
            data = getter(e)
            if hashlib.sha256(data).hexdigest() != e[key]:
                raise SystemExit("%s differs from the catalog's %s: refusing to pack a stale file" % (e["path"], key))
            out.append((e["path"], data))
    att = attribution_catalog(catalog).encode("utf-8")
    dist = pathlib.Path(dist)
    return {names[0]: write_zip(dist / names[0], m224 + [("ATTRIBUTION.md", att)]),
            names[1]: write_zip(dist / names[1], mori + [("ATTRIBUTION.md", att)])}
