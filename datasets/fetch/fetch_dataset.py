# -*- coding: utf-8 -*-
"""Build the local question data from scratch: download the pictures and passages that the question file points at, and link them.

    set WIKIQA_CONTACT=<e-mail or repository URL>          (Wikimedia User-Agent policy: REQUIRED)
    uv run python -m datasets.fetch.fetch_dataset [--questions datasets/questions/legacy/questions.jsonl] [--limit N] [--px 640] [--out work]

For every question it
  * image items : asks the Commons API for the file's license (CC0 / public domain only, anything else is skipped), downloads a <= --px
                  thumbnail, and compares the original's sha1 with the one recorded when the question was written (a mismatch = the file
                  was replaced; reported, and the question is skipped because its answer may no longer hold);
  * text items  : fetches the lead section of the pinned revision (en and ja) and checks that every evidence string is still in it.
Nothing from Wikipedia / Commons is stored in git: the output goes to <out>/data/ (default work/data/, git-ignored):
  data/images/<sha1>.jpg   data/passages.json   data/linked.jsonl   data/ATTRIBUTION.md   data/report.json
For a faster, network-free start use the Release's images-224px.zip (``python -m datasets.fetch fetch --from-release DIR``); this script is
for rebuilding everything. The commands ``check`` / ``fetch`` / ``refresh`` (datasets/fetch/__main__.py) are the maintenance tools.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import commons, http, wikitext

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_QUESTIONS = ROOT / "datasets" / "questions" / "legacy" / "questions.jsonl"


def _readable(path: pathlib.Path) -> bool:
    """True if Pillow (when installed) can open the file; without Pillow the check is skipped."""
    try:
        from PIL import Image
    except ImportError:
        return True
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:  # noqa: BLE001
        return False


def load_questions(path: pathlib.Path, limit: int | None) -> list[dict]:
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return rows[:limit] if limit else rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--px", type=int, default=640, help="thumbnail width to download")
    ap.add_argument("--out", default=str(http.WORK), help="folder that gets data/ (default work/)")
    args = ap.parse_args(argv)
    http.user_agent()                                              # stop early without WIKIQA_CONTACT
    data = pathlib.Path(args.out) / "data"
    (data / "images").mkdir(parents=True, exist_ok=True)

    rows = load_questions(pathlib.Path(args.questions), args.limit)
    titles = sorted({t for r in rows for t in r.get("images", [])})
    info = commons.image_info(titles, px=args.px, use_cache=True) if titles else {}

    report = dict(questions=len(rows), kept=0, skipped={})
    attribution: dict[str, dict] = {}
    passages: dict[str, dict] = {}
    linked = []

    def skip(why, r):
        report["skipped"].setdefault(why, []).append(r["id"])

    for r in rows:
        rec = dict(r)
        if r["modality"] == "image":
            local, bad = [], None
            for t, want in zip(r["images"], r["sha1"]):
                got = info.get(t)
                if got is None or got["state"] != "found":
                    bad = "file missing"
                    break
                ii = got["info"]
                if not commons.OK_LICENSE.match(ii["license"]):
                    bad = "license changed: " + ii["license"]
                    break
                if ii["sha1"] != want:
                    bad = "file replaced (sha1 differs)"
                    break
                path = data / "images" / (want + ".jpg")
                if not path.exists() or not _readable(path):
                    path.write_bytes(http.fetch(ii["thumb_url"], gap=0.3))
                    if not _readable(path):                      # truncated transfer: try once more
                        path.write_bytes(http.fetch(ii["thumb_url"], gap=0.3))
                local.append("data/images/%s.jpg" % want)
                attribution[t] = dict(license=ii["license"], author=ii["author"][:160], page=ii["source_url"])
            if bad:
                skip(bad, r)
                continue
            rec["local_images"] = local
        else:
            ok = True
            for lang in r.get("langs", ["en", "ja"]):
                a = r["article"][lang]
                key = "%s:%s" % (lang, a["revid"])
                if key not in passages:
                    passages[key] = dict(lang=lang, title=a["title"], revid=a["revid"], text=wikitext.lead_text(lang, a["revid"]))
                text = passages[key]["text"]
                missing = [e for e in r["evidence"][lang] if e not in text]
                if missing:
                    skip("evidence not in passage (%s)" % lang, r)
                    ok = False
                    break
            if not ok:
                continue
        linked.append(rec)
        report["kept"] += 1

    (data / "passages.json").write_text(json.dumps(passages, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(data / "linked.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for rec in linked:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    lines = ["# Attribution", "",
             "Images are from Wikimedia Commons (CC0 / public domain only; license re-checked on every run).", ""]
    for t, a in sorted(attribution.items()):
        lines.append("- %s - %s - %s - <%s>" % (t, a["author"] or "unknown", a["license"], a["page"]))
    lines += ["", "Text passages are lead sections of Wikipedia articles (CC BY-SA 4.0), fetched at run time (local only, never redistributed):", ""]
    for key, p in sorted(passages.items()):
        lines.append("- %s.wikipedia.org \"%s\", revision %s - <https://%s.wikipedia.org/?oldid=%s>"
                     % (p["lang"], p["title"], p["revid"], p["lang"], p["revid"]))
    (data / "ATTRIBUTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (data / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("questions %d  kept %d  skipped %d" % (report["questions"], report["kept"], sum(len(v) for v in report["skipped"].values())))
    for why, ids in report["skipped"].items():
        print("  %-40s %d  e.g. %s" % (why, len(ids), ", ".join(ids[:3])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
