# -*- coding: utf-8 -*-
"""Final build of the question set: everything a user (or another repository) needs, in dist/<version>/ (git-ignored).

    python -m datasets.build_v1 [--out dist/v1] [--date 2026-10-11] [--root DIR ...] [--no-zip] [--no-runner-check]

Reads the question files (datasets/questions/v1/*.jsonl, dropped rows left out), the image list (manifests/images_v1.json) and the
classification tables; READS ONLY: no question file is ever written. Needs the pictures on this machine: Commons pictures and the
drawn pictures under ``<root>/data/...`` (``$WIKIQA_DATA_ROOT``), the other drawn pictures under ``<root>/generated/`` (work/), and their 224 px
copies (``<root>/work/px224``, ``work/generated/px224``). Deterministic and idempotent (sorted, fixed zip timestamps, ``--date`` instead of
a clock): two builds give byte-identical files.

Outputs (dist/<version>/):
  questions_v1.jsonl        every evaluated question (dropped left out): text, answer, wrong answers, own state (text-only controls only; never
                            Wikipedia text), classification, difficulty, review state, origin, derived_from, picture path
  cases_v1.jsonl            the evaluation cases as ``datasets.loader.load_v1_cases`` returns them (balanced option order and ``expected`` fixed);
                            en and ja side by side; pictures as logical paths; passage-based text-only questions carry ``state: null`` + article ref
  manifest_v1.json          version, date, counts (group / kind / origin / language / ...), sha256 of every other file (written last)
  questions_v1_all.csv      classification table of the evaluated questions
  images_v1.json            every picture in use (Commons: licence / author / URL / sha; generated: script, seed scheme, sha, licence CC0-1.0)
  images-224px.zip / images-original.zip   the pictures (names = logical paths) + ATTRIBUTION.md.  NOTHING IS UPLOADED.
  build_report.md           the self-check (every check with its result)
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datasets import loader, newq, options  # noqa: E402
from datasets.tools import v1_io  # noqa: E402
from datasets.version import DATASET_VERSION, DIST_SUBDIR  # noqa: E402

DEFAULT_DATE = "2026-10-11"
MAX_STATE = 600
LICENSE_DECIDED = "CC0-1.0"            # decided by the repository owner (2026-10-11): pictures made by this repository's scripts are CC0-1.0
#: new-question file tag -> (generator script, seed scheme). Base rows with a generated picture are the 12 rebuilt rsn questions.
TK_FONTS = {"tk_ui": "text drawn by the Tk widgets in the OS fonts Segoe UI (English UI) / Yu Gothic UI (Japanese UI), bundled with Windows; fonts not redistributed"}
GENERATORS = {
    "rendered": ("datasets/synthetic/gen_v1_new.py", 'random.Random("v2new:" + pattern + ":" + k)'),
    "rendered_b": ("datasets/synthetic/gen_v1_new_b.py", "random.Random seeded per pattern and number"),
    "tk_ui": ("datasets/synthetic/gen_v1_tk_ui.py", 'random.Random("<pattern>-<k>"); real Tkinter windows captured with ImageGrab'),
    "ja_specific": ("datasets/synthetic/gen_v1_ja.py", "random.Random(zlib.crc32(builder name))"),
    "rewrite": ("datasets/synthetic/gen_v1_rewrite.py", "seeds t_ba<i>, w_two<i>; geometry fixed"),
}


# ------------------------------------------------------------------------------------------------------------- finding pictures
def image_roots(extra=()) -> list:
    r = list(extra) + [os.environ.get("WIKIQA_IMAGES"), os.environ.get("WIKIQA_DATA_ROOT"), ROOT / "work"]
    return [pathlib.Path(x) for x in r if x]


def px224_dirs(roots) -> list:
    out = []
    for r in roots:
        out += [pathlib.Path(r) / "work" / "px224", pathlib.Path(r) / "px224", pathlib.Path(r) / "px224_v1"]
    return out


def find_original(path: str, roots) -> pathlib.Path | None:
    for r in roots:
        if (pathlib.Path(r) / path).is_file():
            return pathlib.Path(r) / path
    return None


def find_224(path: str, roots) -> pathlib.Path | None:
    name = pathlib.PurePosixPath(path).name
    if path.startswith("generated/"):
        cands = [pathlib.Path(r) / "generated" / "px224" / name for r in roots]
    else:
        cands = [d / name for d in px224_dirs(roots)]
    return next((c for c in cands if c.is_file()), None)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def img_size(data: bytes) -> list:
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        return list(im.size)


def fresh_224_equal(orig: bytes, stored: bytes, px: int = 224) -> bool:
    """True when shrinking the original (longest side px, LANCZOS, as runner/run.py does) gives the stored picture's pixels."""
    from PIL import Image
    a = Image.open(io.BytesIO(orig)).convert("RGB")
    a.thumbnail((px, px), Image.LANCZOS)
    b = Image.open(io.BytesIO(stored)).convert("RGB")
    return a.size == b.size and a.tobytes() == b.tobytes()


# ------------------------------------------------------------------------------------------------------------- catalog
def row_tag_map() -> dict:
    """{id: tag or None (base file)} of every v1 row."""
    out = {}
    for g, rows in v1_io.load_v1().items():
        for r in rows:
            out[r["id"]] = None
    for t, rows in v1_io.load_new().items():
        for r in rows:
            out[r["id"]] = t
    return out


def build_catalog(rows: list, roots, date: str, problems: list) -> tuple:
    """(catalog dict, {path: (original bytes, 224 bytes)}). Commons and the earlier drawn pictures inherit their entry of
    manifests/images_v1.json; the pictures under generated/ are made by the scripts: source "generated"."""
    listed = json.loads((loader.MANIFESTS / "images_v1.json").read_text(encoding="utf-8"))
    by_file = {e["file"]: e for e in listed["images"]}
    by_file.update({e["file"]: e for e in listed.get("rendered", [])})
    tags = row_tag_map()
    users = collections.defaultdict(list)
    first_row = {}
    for r in rows:
        for p in r.get("local_images", []):
            users[p].append(r["id"])
            first_row.setdefault(p, r)
    entries, blobs = [], {}
    for p in sorted(users):
        name = pathlib.PurePosixPath(p).name
        r = first_row[p]
        orig_f, f224 = find_original(p, roots), find_224(p, roots)
        if orig_f is None or f224 is None:
            problems.append("picture not found: %s (original %s, 224px %s)" % (p, bool(orig_f), bool(f224)))
            continue
        ob, sb = orig_f.read_bytes(), f224.read_bytes()
        so, s2 = sha256_bytes(ob), sha256_bytes(sb)
        qids = sorted(users[p])
        if p.startswith("generated/"):
            tag = tags.get(r["id"]) or "rewrite"
            gen, seed = GENERATORS[tag]
            e = dict(path=p, file=name, source="generated", generator=gen, seed=seed, license=LICENSE_DECIDED, license_status="decided",
                     sha256_original=so, sha256_224=s2,
                     size_original=img_size(ob), size_224=img_size(sb), question_ids=qids)
            if tag in TK_FONTS:
                e["fonts"] = TK_FONTS[tag]
            if not fresh_224_equal(ob, sb):
                problems.append("warning: 224px copy of %s is not the fresh LANCZOS shrink of its original (using the stored copy)" % p)
        else:
            old = by_file.get(name)
            if old is None:
                problems.append("%s is not in images_v1.json" % p)
                continue
            e = {k: v for k, v in old.items() if k != "question_ids"}
            if (so, s2) != (old["sha256_original"], old["sha256_224"]):
                problems.append("%s differs from images_v1.json (original %s, 224px %s)" % (
                    p, so == old["sha256_original"], s2 == old["sha256_224"]))
            if e.get("author"):                                      # a Commons author line may carry a private e-mail address: drop it
                e["author"] = re.sub(r"\s*\(?[\w.+-]+@[\w-]+\.[\w.-]+\)?", "", e["author"]).strip()
            e = dict(path=p, **e)
            if old["source"] == "rendered":
                e["license"] = LICENSE_DECIDED
                e["license_status"] = "decided"
                e["seed"] = "fixed seeds of datasets/synthetic (see generator)"
            e.update(size_original=img_size(ob), size_224=img_size(sb), question_ids=qids)
        entries.append(e)
        blobs[p] = (ob, sb)
    counts = collections.Counter(e["source"] for e in entries)
    cat = dict(manifest_version=DATASET_VERSION, dataset_version=DATASET_VERSION, generator="datasets/build_v1.py", generated_at=date,
               note="The list only: no picture and no Wikipedia text. 'path' is the logical path used by the question rows and the zip member "
                    "name. Commons: sha256_original = the stored file (640 px thumbnail), sha1 = the full-size file on Commons. "
                    "source 'rendered' = drawn by datasets/synthetic (earlier build); 'generated' = made for this version.",
               input_px=224, counts=dict(images=len(entries), **counts), images=entries)
    return cat, blobs


# ------------------------------------------------------------------------------------------------------------- outputs
def jl(rows: list) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n" for r in rows).encode("utf-8")


def csv_bytes(cols: list, rows: list) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def question_record(r: dict) -> dict:
    out = {k: v for k, v in r.items() if k not in ("version",)}
    out["dataset_version"] = DATASET_VERSION
    out["origin"] = r.get("origin") or "base"
    out.setdefault("derived_from", None)
    out["image"] = (r.get("local_images") or [None])[0]
    return out


def case_record(c: dict, rowmap: dict) -> dict:
    r = rowmap[c["id"]]
    rec = dict(version=DATASET_VERSION, id=c["id"], key=[DATASET_VERSION, c["id"]], group=r["group"], kind=c["kind"],
               modality=c["modality"], tags=c["tags"], difficulty=c["difficulty"], langs=r.get("langs") or ["en", "ja"],
               images=list(r.get("local_images", [])), expected=c["expected"])
    if "article" in r:
        rec["article"] = r["article"]
    for lang in rec["langs"]:
        L = c[lang]
        state = None if "article" in r else L["state"]
        opts = [t for _, t in L["options"]] if (c["kind"] == "choice") else L["options"]
        rec[lang] = dict(state=state, instr=L["instr"], options=opts)
    return rec


def stats(rows: list) -> dict:
    def cnt(f):
        return dict(sorted(collections.Counter(f(r) for r in rows).items(), key=lambda kv: str(kv[0])))
    return dict(total=len(rows), by_group=cnt(lambda r: r["group"]), by_kind=cnt(lambda r: r["kind"]),
                by_origin=cnt(lambda r: r.get("origin") or "base"),
                by_group_origin=cnt(lambda r: "%s/%s" % (r["group"], r.get("origin") or "base")),
                by_language=cnt(lambda r: r.get("lang", "both")),
                by_answer_format=cnt(lambda r: v1_io.answer_format(r)[0]), by_difficulty=cnt(lambda r: r.get("difficulty")),
                by_skill=cnt(lambda r: r["skill"]), by_image_type=cnt(lambda r: r["image_type"]),
                by_review_state=cnt(lambda r: r["review"]["state"]))


# ------------------------------------------------------------------------------------------------------------- checks
class Checks:
    def __init__(self):
        self.items = []

    def add(self, name: str, ok: bool, detail: str = "", level: str = "error"):
        self.items.append((name, ok, detail, level))

    @property
    def failed(self) -> list:
        return [i for i in self.items if not i[1] and i[3] == "error"]

    def md(self) -> str:
        L = ["| 検査 | 結果 | 内容 |", "|---|---|---|"]
        for n, ok, d, lv in self.items:
            L.append("| %s | %s | %s |" % (n, "OK" if ok else ("NG" if lv == "error" else "注意"), d.replace("|", "/").replace("\n", " ")))
        return "\n".join(L)


def leaf_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from leaf_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from leaf_strings(v)


def passages_texts(roots) -> list:
    for p in [os.environ.get("WIKIQA_PASSAGES")] + [pathlib.Path(r) / "data" / "passages.json" for r in roots]:
        if p and pathlib.Path(p).exists():
            d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
            return [v["text"] for v in d.values() if isinstance(v, dict) and v.get("text")]
    return []


def balanced_report(rows: list, orders: dict) -> tuple:
    """({(group, n_free): [count per position]}, worst difference). Questions whose right answer is a special option sit at the tail
    and are outside the balancing."""
    c = {}
    for r in rows:
        if r["kind"] != "choice":
            continue
        langs = r.get("langs") or ["en", "ja"]
        lists = [[r[l]["correct"]] + list(r[l]["wrong"]) for l in langs]
        pin = options.pinned_indices(*lists)
        if 0 in pin:
            continue
        n_free = max(len(lists[0]) - len(pin), 1)
        c.setdefault((r["group"], n_free), [0] * n_free)[options.expected_of(orders[r["id"]])] += 1
    worst = max((max(v) - min(v) for v in c.values()), default=0)
    return c, worst


def run_checks(rows: list, all_rows: list, catalog: dict, cases: list, qrecs: list, out_bytes: dict, roots, zips: dict | None,
               problems: list, zip_members: dict | None) -> tuple:
    ck = Checks()
    ids = [r["id"] for r in rows]
    ck.add("ID 一意", len(ids) == len(set(ids)), "%d 問" % len(ids))
    keys = [tuple(c["key"]) for c in cases]
    ck.add("(version,id) キー一意・版が一致", len(set(keys)) == len(keys) and all(k[0] == DATASET_VERSION for k in keys),
           "%d ケース、版 %s" % (len(keys), DATASET_VERSION))
    ck.add("loader の版名 = DATASET_VERSION", loader.VERSIONS[-1] == DATASET_VERSION, "loader.VERSIONS = %s" % (loader.VERSIONS,))
    dropped_all = {r["id"] for r in all_rows if loader.is_dropped(r)}
    ck.add("dropped が含まれない", not (dropped_all & set(ids)) and not (dropped_all & {c["id"] for c in cases}),
           "評価対象 %d / 全行 %d（dropped %d）" % (len(rows), len(all_rows), len(dropped_all)))
    ck.add("cases と questions の問数・ID 一致", [c["id"] for c in cases] == ids and [q["id"] for q in qrecs] == ids, "%d" % len(cases))
    # pictures
    have = {e["path"] for e in catalog["images"]}
    miss = [r["id"] for r in rows if any(p not in have for p in r.get("local_images", []))]
    ck.add("全問の画像が存在（一覧に載り、ファイルが読める）", not miss and not problems_errors(problems),
           "画像を使う問 %d、一覧 %d 枚%s" % (sum(1 for r in rows if r.get("local_images")), len(have), "; 欠け: %s" % miss[:5] if miss else ""))
    bad_sha = []
    for e in catalog["images"]:
        f, f2 = find_original(e["path"], roots), find_224(e["path"], roots)
        if f is None or f2 is None or sha256_bytes(f.read_bytes()) != e["sha256_original"] or sha256_bytes(f2.read_bytes()) != e["sha256_224"]:
            bad_sha.append(e["path"])
    ck.add("画像 sha256 が一覧と一致（original と 224px、ディスクを再読込）", not bad_sha, "%d 枚を照合%s" % (len(have), "; 不一致: %s" % bad_sha[:5] if bad_sha else ""))
    used = {p for r in rows for p in r.get("local_images", [])}
    ck.add("一覧は使っている画像だけ（dropped のみの画像を含まない）", used == have, "使用 %d / 一覧 %d" % (len(used), len(have)))
    ck.add("1 問 1 枚", all(len(r.get("local_images", [])) == (0 if r["modality"] == "text" else 1) for r in rows),
           "画像の問 %d は 1 枚、文章のみ %d は 0 枚" % (sum(1 for r in rows if r["modality"] == "image"), sum(1 for r in rows if r["modality"] == "text")))
    ck.add("画像の許可ライセンス（Commons は CC0 / パブリックドメインのみ）",
           all(e["source"] != "commons" or (e["license"] or "").lower().startswith(("cc0", "public domain")) for e in catalog["images"]),
           ", ".join("%s %d" % kv for kv in sorted(collections.Counter(e.get("license") or "(generated)" for e in catalog["images"]).items())))
    # limits
    from runner import cases as rc
    lim = rc.check_all_limits(rc_cases_for_limits(cases))
    nones = [k for k, v in lim.items() if v is None]
    offenders = {k: v for k, v in lim.items() if v}
    mx_c = max((len(c[l]["options"]) for c in cases for l in c["langs"] if c["kind"] == "choice"), default=0)
    mx_s = max((len(c[l]["options"]) for c in cases for l in c["langs"] if c["kind"] == "score"), default=0)
    ck.add("選択肢数・段階数が全モデルの上限以内（adapters の LIMITS）", not offenders and not nones,
           "最大 選択肢 %d・段階 %d。モデル: %s%s%s" % (mx_c, mx_s, ", ".join(sorted(k for k in lim if lim[k] is not None)),
                                              "; 上限を超える: %s" % {k: v[:2] for k, v in offenders.items()} if offenders else "",
                                              "; 上限を読めない: %s" % nones if nones else ""))
    # en / ja
    diffs = [c["id"] for c in cases if c["kind"] != "noul" and len(c["langs"]) == 2 and len(c["en"]["options"]) != len(c["ja"]["options"])]
    both = [r for r in rows if (r.get("langs") or ["en", "ja"]) == ["en", "ja"]]
    en_n, ja_n = sum(1 for c in cases if "en" in c), sum(1 for c in cases if "ja" in c)
    ja_only = sum(1 for r in rows if r.get("langs") == ["ja"])
    ck.add("en/ja の個数一致（選択肢・段階の数。en/ja 両方の問すべて）", not diffs and en_n + ja_only == ja_n + 0 * en_n and en_n == len(both),
           "両言語 %d 問、日本語のみ %d 問（ja %d / en %d ケース）%s" % (len(both), ja_only, ja_n, en_n, "; 不一致: %s" % diffs[:5] if diffs else ""))
    # text state
    txt = [r for r in rows if r["modality"] == "text"]
    over, nonstate, forb = [], [], []
    for r in txt:
        for l in r.get("langs") or ["en", "ja"]:
            st = r[l].get("state")
            if "article" in r:
                if st is not None:
                    nonstate.append(r["id"])
            elif not st or len(st) > MAX_STATE:
                over.append("%s/%s" % (r["id"], l))
    for r in rows:
        for k in ("evidence", "passage", "passages", "text", "body", "article_text", "extract"):
            if k in r:
                forb.append(r["id"])
        if any(len(s) > MAX_STATE for s in leaf_strings(r)):
            forb.append(r["id"] + "(long string)")
    ctrl = [r for r in txt if "article" not in r]
    ck.add("txt の state が 600 字以下で自作（対照）／記事問は state なし、本文キー・長文なし", not over and not nonstate and not forb,
           "記事由来 %d（state なし）、対照 %d（自作 state）%s" % (len(txt) - len(ctrl), len(ctrl), "; 違反: %s" % (over + nonstate + forb)[:5] if (over or nonstate or forb) else ""))
    texts = passages_texts(roots)
    leaked = []
    blob = (out_bytes["questions_v1.jsonl"] + out_bytes["cases_v1.jsonl"]).decode("utf-8")
    for t in texts:
        for off in range(0, max(len(t) - 60, 1), 400):
            piece = t[off:off + 60]
            if len(piece) >= 40 and piece in blob:
                leaked.append(piece[:30])
                break
    ck.add("Wikipedia 本文が出力に混入していない（手元の passages.json %d 本と 60 字の断片で照合）" % len(texts), not leaked,
           "混入なし" if not leaked else "混入の疑い: %s" % leaked[:3], level="error" if texts else "warn")
    # balanced
    ordr = options.v1_orders(rows)
    pos, worst = balanced_report(rows, ordr)
    ck.add("balanced の正解位置の偏り（群 × 選択肢数ごとの最大差 ≤ 1）", worst <= 1,
           "最大差 %d。例: %s" % (worst, "; ".join("%s/%d択 %s" % (g, n, "/".join(map(str, v))) for (g, n), v in sorted(pos.items())[:6])))
    expd = all(c["expected"] == options.expected_of(ordr[c["id"]]) for c in cases if c["kind"] == "choice")
    ck.add("cases の expected が balanced の順と一致", expd, "選択問題 %d" % sum(1 for c in cases if c["kind"] == "choice"))
    # zips
    if zips is not None:
        ok = True
        det = []
        for zn, kind in (("images-224px.zip", "sha256_224"), ("images-original.zip", "sha256_original")):
            members = zip_members[zn]
            want = {e["path"]: e[kind] for e in catalog["images"]}
            got = {n: h for n, h in members.items() if n != "ATTRIBUTION.md"}
            good = got == want and "ATTRIBUTION.md" in members
            ok &= good
            det.append("%s: %d 枚 + ATTRIBUTION.md %s" % (zn, len(got), "一致" if good else "不一致"))
        ck.add("zip の中身が一覧と一致（名前と sha256。展開して再計算）", ok, "; ".join(det))
    return ck, pos


def problems_errors(problems: list) -> list:
    return [p for p in problems if not p.startswith("warning")]


def rc_cases_for_limits(cases: list) -> list:
    """The shape runner.cases.check_limits reads: images, kind, en / ja options."""
    out = []
    for c in cases:
        d = dict(id=c["id"], images=c["images"], kind=c["kind"])
        for l in c["langs"]:
            d[l] = dict(options=c[l]["options"])
        out.append(d)
    return out


def runner_check(expected_total: int, expected_new: int, by_group: dict) -> tuple:
    """Walk every v1 set of runner/cases.py with the dummy ask; counts must match the question file."""
    from runner import cases as rc
    lines, ok = [], True
    for name, want in [("photo", by_group.get("photo")), ("biz", by_group.get("biz")), ("rsn", by_group.get("rsn")),
                       ("txt", by_group.get("txt")), ("all", expected_total), ("new", expected_new)]:
        cs = rc.load_cases(name, version="v1", strict_passages=False)
        res = rc.dry_run(cs)
        good = len(cs) == want and not res["problems"]
        ok &= good
        lines.append((name, len(cs), want, res["asked"], len(res["problems"]), good))
    return ok, lines


def collect_notes(roots) -> None:
    return None


# ------------------------------------------------------------------------------------------------------------- main
import time  # noqa: E402
_T0 = time.time()


def stage(msg: str) -> None:
    print("[%5.0fs] %s" % (time.time() - _T0, msg), file=sys.stderr, flush=True)


def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        st.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "dist" / DIST_SUBDIR))
    ap.add_argument("--date", default=DEFAULT_DATE)
    ap.add_argument("--root", action="append", default=[], help="extra folder that contains data/ and generated/ (repeatable)")
    ap.add_argument("--no-zip", action="store_true")
    ap.add_argument("--no-runner-check", action="store_true")
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    roots = image_roots(a.root)

    all_rows = loader.load_rows("v1", include_dropped=True)
    rows = loader.load_rows("v1")
    rowmap = {r["id"]: r for r in rows}
    problems: list = []
    stage('catalog')
    catalog, blobs = build_catalog(rows, roots, a.date, problems)
    stage('cases')
    cases_raw = loader.load_v1_cases(images_root=pathlib.Path("."), strict_passages=False)
    cases = [case_record(c, rowmap) for c in cases_raw]
    qrecs = [question_record(r) for r in rows]
    files = {
        "questions_v1.jsonl": jl(qrecs),
        "cases_v1.jsonl": jl(cases),
        "images_v1.json": (json.dumps(catalog, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
    }
    cls = v1_io.classification_rows(rows)
    for c, r in zip(cls, rows):
        c.update(origin=r.get("origin") or "base", derived_from=r.get("derived_from") or "", review_state=r["review"]["state"])
    files["questions_v1_all.csv"] = csv_bytes(v1_io.Q2_COLS + ["origin", "derived_from", "review_state"], cls)

    stage('zip')
    zips, zip_members = None, None
    if not a.no_zip:
        from release import make_image_release as mir
        zips = mir.pack_catalog(catalog, lambda e: blobs[e["path"]][0], lambda e: blobs[e["path"]][1], out)
        import zipfile
        zip_members = {}
        for zn in zips:
            with zipfile.ZipFile(out / zn) as z:
                zip_members[zn] = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
    for n, b in files.items():
        (out / n).write_bytes(b)

    stage('checks')
    ck, pos = run_checks(rows, all_rows, catalog, cases, qrecs, files, roots, zips, problems, zip_members)
    stage('validate_new')
    from datasets.tools import validate_new
    vrep = validate_new.validate(image_roots=roots)
    ck.add("新問の検証（validate_new: スキーマ・範囲・重複・画像・本文）", vrep.ok, "新問 %d 行、エラー %d、警告 %d" % (
        sum(vrep.counts.values()), len(vrep.errors), len(vrep.warnings)))
    stage('runner')
    rc_lines = None
    if not a.no_runner_check:
        ok, rc_lines = runner_check(len(rows), sum(1 for r in rows if r.get("origin") == newq.ORIGIN), stats(rows)["by_group"])
        ck.add("runner の v1 セットをダミー ask で 1 周（問数が questions と一致）", ok,
               "; ".join("%s %d/%d" % (n, got, want) for n, got, want, _, _, _ in rc_lines))

    st = stats(rows)
    manifest = dict(dataset_version=DATASET_VERSION, generated_at=a.date, counts=st, images=catalog["counts"],
                    cases=dict(total=len(cases), en=sum(1 for c in cases if "en" in c["langs"]), ja=sum(1 for c in cases if "ja" in c["langs"])),
                    files={})
    for n in files:
        manifest["files"][n] = dict(sha256=sha256_bytes(files[n]), bytes=len(files[n]))
    for zn in (zips or {}):
        manifest["files"][zn] = dict(sha256=zips[zn]["sha256"], bytes=zips[zn]["bytes"], members=zips[zn]["members"])
    report = render_report(a.date, st, catalog, ck, vrep, problems, pos, zips, rc_lines, manifest)
    (out / "build_report.md").write_bytes(report.encode("utf-8"))
    manifest["files"]["build_report.md"] = dict(sha256=sha256_bytes(report.encode("utf-8")), bytes=len(report.encode("utf-8")))
    (out / "manifest_v1.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print("built %s: %d questions, %d pictures; %d check(s) failed" % (out, len(rows), len(catalog["images"]), len(ck.failed)))
    for n, ok, d, lv in ck.items:
        if not ok:
            print("  %s: %s" % (n, d))
    return 1 if ck.failed else 0


def render_report(date, st, catalog, ck, vrep, problems, pos, zips, rc_lines, manifest) -> str:
    L = ["# build_report（%s・%s）" % (DATASET_VERSION, date), "",
         "評価対象 **%d 問**（dropped を除く）、画像 %d 枚。検査 %d 項目中、失敗 %d。" % (st["total"], len(catalog["images"]), len(ck.items), len(ck.failed)), "",
         "## 検査結果", "", ck.md(), ""]
    if problems:
        L += ["## 画像の注意", ""] + ["- %s" % p for p in problems] + [""]
    if vrep.warnings:
        L += ["## validate_new の警告（新問）", ""] + ["- %s" % w for w in vrep.warnings[:30]] + [""]
    L += ["## balanced の正解位置（群 × 選択肢の自由位置数ごと。「該当なし」が正解の問は末尾固定で除く）", "",
          "| 群 | 自由な位置数 | 問数 | 各位置の数 | 最大差 |", "|---|---|---|---|---|"]
    for (g, n), v in sorted(pos.items()):
        L.append("| %s | %d | %d | %s | %d |" % (g, n, sum(v), " / ".join(map(str, v)), max(v) - min(v)))
    if rc_lines:
        L += ["", "## runner のセット（ダミー ask で全問を一巡）", "", "| セット | ケース数 | 期待 | ask 回数（言語別） | 問題 | 結果 |", "|---|---|---|---|---|---|"]
        for n, got, want, asked, np_, good in rc_lines:
            L.append("| %s | %d | %s | %d | %d | %s |" % (n, got, want, asked, np_, "OK" if good else "NG"))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
