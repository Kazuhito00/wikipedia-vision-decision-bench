# -*- coding: utf-8 -*-
"""check / refresh: has Commons changed under the image list (manifest)?

``check``   asks the Commons API (imageinfo, 50 titles per request) for every image of the manifest and compares METADATA only (nothing is
            downloaded) and writes results/checks/check_<date>.json: when, the count per state, the images that are not 正常, and the
            questions that must be disabled (their picture is gone or no longer CC0 / public domain) or flagged (their picture was replaced).
``refresh`` takes a check (the newest file, or a fresh one with --recheck) and shows what it would change in the manifest. It never writes
            unless ``--apply`` is given and the change list is confirmed (``--yes`` skips the question for scripts).

States (the policy's table):
    ok              正常              exists; sha1, timestamp and license are as in the manifest
    broken          リンク切れ        404, deleted, or renamed (redirect)
    replaced        差し替え          sha1 differs, or the version (timestamp) differs when the manifest has one
    license         ライセンス変更    no longer CC0 / public domain: leave the manifest and the Release
    meta            作者・説明の変更  author, description, or the license LABEL (still CC0 / PD) changed: update the manifest
The first state that applies wins in this order: broken, license, replaced, meta.
"""
from __future__ import annotations

import datetime
import json
import pathlib
from typing import Callable

from . import commons, http

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "datasets" / "manifests" / "images_v1.json"
CHECKS = ROOT / "results" / "checks"
LABELS = {"ok": "正常", "broken": "リンク切れ", "replaced": "差し替え", "license": "ライセンス変更", "meta": "作者・説明の変更"}
ORDER = ["ok", "broken", "replaced", "license", "meta"]


def load_manifest(path: pathlib.Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(m: dict, path: pathlib.Path = MANIFEST) -> None:
    path.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def classify(entry: dict, got: dict) -> tuple[str, list[str], dict]:
    """(state, differences, new values) for one manifest image against its Commons answer (see ``commons.image_info``)."""
    if got["state"] != "found":
        return "broken", ["missing" if got["state"] == "missing" else "renamed to " + got["moved_to"]], {}
    info = got["info"]
    diffs, state = [], "ok"
    if not commons.OK_LICENSE.match(info["license"] or ""):
        diffs.append("license: %s -> %s" % (entry.get("license"), info["license"]))
        state = "license"
    if info["sha1"] != entry.get("sha1"):
        diffs.append("sha1: %s -> %s" % (entry.get("sha1"), info["sha1"]))
        state = state if state != "ok" else "replaced"
    if entry.get("timestamp") and info.get("timestamp") and entry["timestamp"] != info["timestamp"]:
        diffs.append("timestamp: %s -> %s" % (entry["timestamp"], info["timestamp"]))
        state = state if state != "ok" else "replaced"
    for key in ("author", "license"):
        if info[key] != entry.get(key) and not any(d.startswith(key + ":") for d in diffs):
            diffs.append("%s: %r -> %r" % (key, entry.get(key), info[key]))
            state = state if state != "ok" else "meta"
    if entry.get("description_sha256") and info["description_sha256"] != entry["description_sha256"]:
        diffs.append("description changed")
        state = state if state != "ok" else "meta"
    return state, diffs, {k: info[k] for k in ("sha1", "timestamp", "license", "author", "description_sha256", "source_url")}


def check(manifest: dict, *, api: Callable = http.api_json, limit: int | None = None, now: datetime.datetime | None = None) -> dict:
    """Compare the manifest's Commons images with Commons now. ``limit``: only the first N images (a trial)."""
    images = manifest["images"][:limit] if limit else manifest["images"]
    got = commons.image_info([im["title"] for im in images], api=api, use_cache=False)
    items, counts = [], {s: 0 for s in ORDER}
    for im in images:
        state, diffs, new = classify(im, got[im["title"]])
        counts[state] += 1
        if state != "ok":
            items.append(dict(title=im["title"], file=im["file"], state=state, label=LABELS[state], differences=diffs, new=new,
                              question_ids=im.get("question_ids", [])))
    invalid = sorted({q for it in items if it["state"] in ("broken", "license") for q in it["question_ids"]})
    affected = sorted({q for it in items if it["state"] == "replaced" for q in it["question_ids"]})
    return dict(checked_at=(now or datetime.datetime.now().astimezone()).isoformat(timespec="seconds"),
                manifest=dict(version=manifest.get("manifest_version"), images=len(manifest["images"])), checked=len(images),
                counts=dict(counts, labels=LABELS), items=items, invalid_questions=invalid, affected_questions=affected)


def write_check(result: dict, directory: pathlib.Path = CHECKS) -> pathlib.Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = result["checked_at"].replace(":", "").replace("-", "")[:15]
    p = directory / ("check_%s.json" % stamp)
    p.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return p


def latest_check(directory: pathlib.Path = CHECKS) -> pathlib.Path | None:
    files = sorted(directory.glob("check_*.json"))
    return files[-1] if files else None


def plan_refresh(manifest: dict, result: dict, accept_replaced: bool = False) -> list[dict]:
    """The changes ``refresh`` would make: one dict(title, action, set) per image. Nothing is written here.
        meta      -> update author / description hash / license label / page URL
        license   -> exclude (the image leaves the manifest's usable set; remove it from the Release by hand)
        broken    -> exclude (the questions that use it are disabled)
        replaced  -> only with ``accept_replaced``: take the new sha1/timestamp and clear the sha256 values (re-run ``fetch --update-hashes``)
    """
    by_title = {im["title"]: im for im in manifest["images"]}
    plan = []
    for it in result["items"]:
        im = by_title.get(it["title"])
        if im is None:
            continue
        if it["state"] == "meta":
            plan.append(dict(title=it["title"], action="update", set={k: v for k, v in it["new"].items() if im.get(k) != v}))
        elif it["state"] in ("license", "broken"):
            plan.append(dict(title=it["title"], action="exclude", set=dict(excluded=it["label"] + ": " + "; ".join(it["differences"]))))
        elif it["state"] == "replaced" and accept_replaced:
            plan.append(dict(title=it["title"], action="replace",
                             set=dict(it["new"], sha256_original=None, sha256_224=None)))
    return plan


def apply_plan(manifest: dict, plan: list[dict], checked_at: str) -> dict:
    by_title = {im["title"]: im for im in manifest["images"]}
    for p in plan:
        by_title[p["title"]].update(p["set"])
    manifest.setdefault("refresh_log", []).append(dict(at=checked_at, changes=len(plan),
                                                       actions={a: sum(1 for p in plan if p["action"] == a) for a in {p["action"] for p in plan}}))
    return manifest
