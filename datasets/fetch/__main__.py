# -*- coding: utf-8 -*-
"""Data inspection and download.   uv run python -m datasets.fetch  check | fetch | refresh   [options]

  check     Commons imageinfo for every image of the manifest (50 titles per request), METADATA only, nothing downloaded.
            Reports 正常 / リンク切れ / 差し替え / ライセンス変更 / 作者・説明の変更 and writes results/checks/check_<date>.json.
              --limit N   only the first N images (a trial)       --manifest PATH   (default datasets/manifests/images_legacy.json)
  fetch     Download the pictures (thumbnail at the manifest's width), compare sha256 with the manifest, shrink to 224 px and compare again.
              --from-release DIR   no network: extract + verify DIR/images-224px.zip and/or DIR/images-original.zip
              --limit N   --update-hashes (fill sha256 values that the manifest does not have yet)
  refresh   Show what a check changes in the manifest (dry run). With --apply, ask for confirmation, then write it.
              --recheck (run a new check first)   --check FILE   --accept-replaced   --apply   --yes

WIKIQA_CONTACT (an e-mail address or the repository URL) is REQUIRED for anything that talks to Wikimedia: it goes into the User-Agent.
The Wikimedia API is asked politely: 1 request per second, 50 titles per request. Wikipedia text is never fetched here.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import fetch_images, http, inspect_images as I


def cmd_check(args) -> int:
    http.user_agent()                                     # stop early without WIKIQA_CONTACT
    manifest = I.load_manifest(pathlib.Path(args.manifest))
    res = I.check(manifest, limit=args.limit)
    path = I.write_check(res)
    c = res["counts"]
    print("checked %d images at %s" % (res["checked"], res["checked_at"]))
    for s in I.ORDER:
        print("  %-14s %5d" % (I.LABELS[s], c[s]))
    for it in res["items"][:20]:
        print("   - %s  %s  %s" % (it["label"], it["file"], "; ".join(it["differences"])[:100]))
    print("questions to disable: %d   questions on replaced pictures: %d" % (len(res["invalid_questions"]), len(res["affected_questions"])))
    print("wrote", path)
    return 0


def cmd_fetch(args) -> int:
    manifest = I.load_manifest(pathlib.Path(args.manifest))
    if args.from_release:
        rep = fetch_images.fetch_release(manifest, pathlib.Path(args.from_release))
        if not rep:
            raise SystemExit("no images-224px.zip / images-original.zip in %s" % args.from_release)
    else:
        http.user_agent()
        rep = fetch_images.fetch_commons(manifest, limit=args.limit, update_hashes=args.update_hashes)
        if args.update_hashes:
            I.save_manifest(manifest, pathlib.Path(args.manifest))
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    bad = rep.get("problems") or any(v["wrong_sha256"] or v["unknown"] for v in rep.values() if isinstance(v, dict) and "wrong_sha256" in v)
    return 1 if bad else 0


def cmd_refresh(args) -> int:
    mpath = pathlib.Path(args.manifest)
    manifest = I.load_manifest(mpath)
    if args.recheck:
        http.user_agent()
        res = I.check(manifest)
        print("rechecked: wrote", I.write_check(res))
    else:
        p = pathlib.Path(args.check) if args.check else I.latest_check()
        if p is None:
            raise SystemExit("no check result: run `check` first (or use --recheck)")
        res = json.loads(p.read_text(encoding="utf-8"))
        print("using", p)
    plan = I.plan_refresh(manifest, res, accept_replaced=args.accept_replaced)
    skipped = [it for it in res["items"] if it["state"] == "replaced" and not args.accept_replaced]
    for p_ in plan:
        print("  %-8s %s  %s" % (p_["action"], p_["title"], json.dumps(p_["set"], ensure_ascii=False)[:120]))
    if skipped:
        print("  %d replaced picture(s) NOT changed (review the differences, then --accept-replaced and `fetch --update-hashes`)" % len(skipped))
    print("%d change(s) planned%s" % (len(plan), "" if args.apply else "   (dry run: nothing written; add --apply)"))
    if not args.apply or not plan:
        return 0
    if not args.yes and input("write these %d change(s) to %s ? [y/N] " % (len(plan), mpath)).strip().lower() != "y":
        print("not written")
        return 1
    I.save_manifest(I.apply_plan(manifest, plan, res["checked_at"]), mpath)
    print("manifest updated")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m datasets.fetch", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("fetch", cmd_fetch), ("refresh", cmd_refresh)):
        p = sub.add_parser(name)
        p.add_argument("--manifest", default=str(I.MANIFEST))
        p.add_argument("--limit", type=int)
        p.set_defaults(fn=fn)
        if name == "fetch":
            p.add_argument("--from-release")
            p.add_argument("--update-hashes", action="store_true")
        if name == "refresh":
            p.add_argument("--recheck", action="store_true")
            p.add_argument("--check")
            p.add_argument("--accept-replaced", action="store_true")
            p.add_argument("--apply", action="store_true")
            p.add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
