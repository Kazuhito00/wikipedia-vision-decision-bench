# -*- coding: utf-8 -*-
"""Make the image list (manifest) of a question set: datasets/manifests/images_legacy.json.   NO picture and NO Wikipedia text goes into it.

    uv run python -m datasets.fetch.make_image_manifest --data-root <folder with data/> --px224 <folder with the 224 px pictures>
                                                        [--cache <folder with cached Commons API answers>] [--out PATH]

Per Commons image: file (the local name, <sha1>.jpg), title, license, author, source_url, sha1 (Commons' sha1 of the ORIGINAL file),
sha256_original (of the stored file, see below), sha256_224 (of the 224 px picture the models were given), fetched_at, description_sha256
(a hash, not the text), question_ids (the legacy questions that use it), timestamp (null: the answers cached when the set was built did not
ask for it; ``check`` then compares the sha1 only).
Per rendered picture (synthetic / reasoning): file, generator, sha256_original, sha256_224, question_ids. They are not Commons files.

What "original" means here: the stored file is Commons' THUMBNAIL at width 640 px (``iiurlwidth=640``, what ``fetch_dataset.py`` downloaded), not the
full-size original; ``sha1`` is the sha1 of the full-size file on Commons. The manifest records ``source_width_px: 640``.

Where the facts come from (not from ATTRIBUTION.md, which is hard to parse): every cached Commons API answer under --cache is scanned for
imageinfo records; a record is used only if its sha1 equals the one in linked.jsonl. fetched_at is the modification time of the stored file
(the download time), in UTC.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import json
import pathlib
import sys

from . import commons, fetch_images

ROOT = pathlib.Path(__file__).resolve().parents[2]


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cached_infos(cache_dir: pathlib.Path) -> tuple[dict, dict]:
    """(canonical title -> [imageinfo records], alias title -> canonical title) from every cached API answer."""
    infos, alias = collections.defaultdict(list), {}
    for f in sorted(glob.glob(str(cache_dir / "*.json"))):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        q = d.get("query", {}) if isinstance(d, dict) else {}
        n = {x["from"]: x["to"] for x in q.get("normalized", [])}
        r = {x["from"]: x["to"] for x in q.get("redirects", [])}
        for a in set(n) | set(r):
            alias[a] = r.get(n.get(a, a), n.get(a, a))
        for p in q.get("pages", {}).values():
            for ii in p.get("imageinfo", []):
                infos[p["title"]].append(ii)
    return infos, alias


def build(data_root: pathlib.Path, px224: pathlib.Path, cache: pathlib.Path) -> dict:
    data = data_root / "data"
    read = lambda name: [json.loads(ln) for ln in (data / name).read_text(encoding="utf-8").splitlines() if ln.strip()]  # noqa: E731
    infos, alias = cached_infos(cache)

    # ---- Commons images (linked.jsonl) ----
    wanted: dict[str, dict] = {}
    for r in read("linked.jsonl"):
        for t, sha1, local in zip(r.get("images", []), r.get("sha1", []), r.get("local_images", [])):
            e = wanted.setdefault(t, dict(sha1=sha1, local=local, question_ids=[]))
            assert e["sha1"] == sha1, t
            e["question_ids"].append(r["id"])
    images, problems = [], []
    for title, w in sorted(wanted.items(), key=lambda kv: pathlib.Path(kv[1]["local"]).name):
        canon = alias.get(title, title)
        cand = [ii for ii in infos.get(canon, []) + infos.get(title, []) if ii.get("sha1") == w["sha1"] and ii.get("extmetadata")]
        if not cand:
            problems.append("no cached imageinfo with the right sha1: " + title)
            continue
        cand.sort(key=lambda ii: "descriptionurl" not in ii)                 # prefer a record that has the page URL
        meta = commons.describe(cand[0])
        file = pathlib.Path(w["local"]).name
        src = data_root / w["local"]
        out224 = px224 / file
        entry = dict(file=file, title=title, source="commons", license=meta["license"], author=meta["author"],
                     source_url=meta["source_url"] or "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                     sha1=w["sha1"], timestamp=None, sha256_original=sha256_file(src),
                     sha256_224=sha256_file(out224) if out224.exists() else None,
                     fetched_at=datetime.datetime.fromtimestamp(src.stat().st_mtime, datetime.timezone.utc).isoformat(timespec="seconds"),
                     description_sha256=meta["description_sha256"], question_ids=sorted(set(w["question_ids"])))
        if not commons.OK_LICENSE.match(meta["license"]):
            problems.append("license not CC0/PD: %s (%s)" % (title, meta["license"]))
        images.append(entry)

    # ---- rendered pictures (synthetic, reasoning) ----
    rendered: dict[str, dict] = {}
    for name, gen in (("synthetic.jsonl", "datasets/synthetic (set: synthetic)"), ("reasoning.jsonl", "datasets/synthetic (set: reasoning)")):
        for r in read(name):
            for local in r.get("local_images", []):
                f = pathlib.Path(local).name
                e = rendered.setdefault(f, dict(file=f, source="rendered", generator=gen, license=None,
                                                sha256_original=sha256_file(data_root / local),
                                                sha256_224=sha256_file(px224 / f) if (px224 / f).exists() else None, question_ids=[]))
                e["question_ids"].append(r["id"])
    for e in rendered.values():
        e["question_ids"] = sorted(set(e["question_ids"]))

    # ---- does a fresh 224 px shrink of the stored file give the sha256 that was used? (Pillow / libjpeg differences) ----
    import PIL
    regen = collections.Counter()
    for e in images:
        if e["sha256_224"]:
            same = fetch_images.sha256_bytes(fetch_images.shrink((data_root / wanted[e["title"]]["local"]).read_bytes(), 224)) == e["sha256_224"]
            regen["same" if same else "differs"] += 1
    lic = collections.Counter(e["license"] for e in images)
    return dict(
        manifest_version="legacy", dataset_version="legacy", generator="datasets/fetch/make_image_manifest.py",
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        note="The list only: no picture and no Wikipedia text. 'sha256_original' is of the stored file = Commons' thumbnail at source_width_px; "
             "'sha1' is of the full-size file on Commons. Pictures of source 'rendered' are drawn by datasets/synthetic (not Commons files).",
        source_width_px=640, input_px=224,
        resize="longest side 224, PIL Image.thumbnail with LANCZOS, saved as JPEG with PIL defaults (runner/run.py)",
        pillow_regen_check=dict(pillow=PIL.__version__, fresh_shrink_equals_recorded_sha256_224=dict(regen)),
        counts=dict(commons_images=len(images), rendered=len(rendered), licenses=dict(lic),
                    questions_with_commons_images=len({q for e in images for q in e["question_ids"]})),
        problems=problems, images=images, rendered=sorted(rendered.values(), key=lambda e: e["file"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", required=True, help="folder that contains data/ (linked.jsonl, synthetic.jsonl, reasoning.jsonl, images/, ...)")
    ap.add_argument("--px224", required=True, help="folder with the 224 px pictures that the evaluation used")
    ap.add_argument("--cache", help="folder with cached Commons API answers (default <data-root>/work/cache)")
    ap.add_argument("--out", default=str(ROOT / "datasets" / "manifests" / "images_legacy.json"))
    args = ap.parse_args(argv)
    root = pathlib.Path(args.data_root)
    m = build(root, pathlib.Path(args.px224), pathlib.Path(args.cache) if args.cache else root / "work" / "cache")
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("wrote %s: %s" % (out, json.dumps(m["counts"], ensure_ascii=False)))
    print("pillow regen check:", m["pillow_regen_check"])
    for p in m["problems"]:
        print("PROBLEM:", p)
    return 1 if m["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
