# -*- coding: utf-8 -*-
"""Writes datasets/manifests/privacy_check_v1.md and needs_new_image_type_v1.md from the reviewers' output (work/review/out) and the
live v1 rows. Read-only on the question files; both md files are rebuilt from scratch (deterministic).

    python datasets/tools/review_notes_v1.py [--review-out work/review/out]
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import loader  # noqa: E402
from datasets.tools import relabel_image_type, v1_io  # noqa: E402

MANIFESTS = ROOT / "datasets" / "manifests"


def short(s: str, n: int = 110) -> str:
    s = " ".join(str(s).split()).replace("|", "/")
    return s if len(s) <= n else s[:n - 1] + "…"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-out", default=str(ROOT / "work" / "review" / "out"))
    a = ap.parse_args(argv)
    rows = {r["id"]: r for r in loader.load_rows("v1")}
    out = {}
    for p in sorted(pathlib.Path(a.review_out).glob("*.jsonl")):
        for e in v1_io.read_jsonl(p):
            out[e["id"]] = e
    # ---- privacy
    priv = []
    for i, e in sorted(out.items()):
        if i not in rows:
            continue
        hit = [s for s in e.get("issues") or [] if "privacy-check" in str(s)]
        if hit:
            m = re.match(r"privacy-check\s*[:：]?\s*(.*)$", str(hit[0]).strip())
            why = (m.group(1) if m and m.group(1) else e.get("reason") or "(理由の記載なし)")
            r = rows[i]
            priv.append((i, r["group"], r["image_type"], why, (r.get("images") or ["(なし)"])[0]))
    L = ["# privacy-check が付いた問（%d 問）" % len(priv), "",
         "レビュアーが「人物が写っている（顔・個人が特定され得る）」として `privacy-check` を付けた、評価対象の問の一覧です（drop された問は含みません）。",
         "方針: 人物が写っているだけでは外さず、設問が人物の同定を求めない限り残しました（同定を求める問は drop / fix 済み）。画像はすべて CC0・パブリックドメインの Commons 写真です。",
         "**決定: 残す（2026-10-11）。** ただし、人物の同定を求める設問は含まれません。",
         "要望があれば個別に除外できます: `python datasets/tools/drop_ids.py <ID> ... --reason \"...\" --apply` が、各 ID の `review.state` を `dropped` にし、対応表（`idmap_legacy_v1.csv` / `idmap_v1_new_<tag>.csv`）の status を `dropped` にして、分類表を作り直します（`v1_io` と `apply_review.apply_entries` の drop 判定と同じ）。その後 `python -m datasets.build_v1` で `dist/v1` を作り直します。",
         "人物の顔の画像はここに載せていません（ID と理由のみ）。画像は `dist/v1/images_v1.json` の `question_ids` から引けます。", "",
         "群別: " + ", ".join("%s %d" % kv for kv in sorted(collections.Counter(p[1] for p in priv).items())), "",
         "| ID | 群 | image_type | 理由の要約 |", "|---|---|---|---|"]
    for i, g, it, why, f in priv:
        L.append("| %s | %s | %s | %s |" % (i, g, it, short(why)))
    (MANIFESTS / "privacy_check_v1.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    # ---- needs_new_image_type
    need = collections.defaultdict(list)
    for i, e in sorted(out.items()):
        if i not in rows:
            continue
        for s in e.get("issues") or []:
            m = re.match(r"needs_new_image_type\s*[:：]\s*(.*)$", str(s).strip())
            if m:
                need[m.group(1).strip().lower()].append(i)
    cur = collections.Counter(r["image_type"] for r in rows.values() if r["image_type"] in ("astronomical", "satellite"))
    hist = {i for i, r in rows.items() if any(h.get("what") == "image_type" for h in r["review"].get("history", []))}
    L = ["# needs_new_image_type の集計と付け替えの状況", "",
         "レビュアーが「既存の image_type に収まらない」として `needs_new_image_type: <値>` を付けた問（drop された問を除く）の集計です。",
         "`astronomical`（天体）と `satellite`（衛星・航空写真）は `taxonomy.V1_EXTRA_IMAGE_TYPES` に追加済みで、**該当問の image_type を付け替えました**",
         "（`datasets/tools/relabel_image_type.py`。変更した行だけを書き、`review.history` に `{date, what: \"image_type\", why}` を追加。冪等）。",
         "それ以外の値（medical-scan など）は taxonomy に追加しておらず、付け替えていません。", "",
         "| 提案 | 問数 | 付け替え先 | 付け替え済み | 備考 |", "|---|---|---|---|---|"]
    for k, ids in sorted(need.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        tgt = relabel_image_type.MAP.get(k)
        done = sum(1 for i in ids if tgt and rows[i]["image_type"] == tgt)
        L.append("| %s | %d | %s | %s | %s |" % (k, len(ids), tgt or "（付け替えない）", done if tgt else "-", "" if tgt else "taxonomy に無い値。ユーザー判断待ち"))
    L += ["", "付け替えた問は合計 %d（履歴に image_type の記録があるもの）。現在の image_type の問数: astronomical %d / satellite %d。" % (
        len(hist), cur["astronomical"], cur["satellite"]), "",
          "付け替えない提案の ID:", ""]
    for k, ids in sorted(need.items()):
        if k not in relabel_image_type.MAP:
            L.append("- %s: %s" % (k, ", ".join(ids)))
    (MANIFESTS / "needs_new_image_type_v1.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("privacy-check %d; needs_new_image_type %s; relabelled %d" % (len(priv), {k: len(v) for k, v in need.items()}, len(hist)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
