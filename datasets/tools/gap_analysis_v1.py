# -*- coding: utf-8 -*-
"""Tables for datasets/manifests/gap_analysis_v1.md: what the reviewed v1 (dropped questions excluded) has and what it lacks.

    python datasets/tools/gap_analysis_v1.py [--review-out work/review/out] > tables.md

Counts only (no new question is made). Groups, skills, difficulty, option counts, score levels, yes/no truth ratio (by group and by
id block), right-answer position (legacy position of the legacy order vs the balanced assignment), language-specific questions, text-only
vs picture, negation / count / spatial / none-of-the-above, and the reviewers' hints (issues such as could-be-2-options, needs_new_image_type).
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datasets import loader, options  # noqa: E402
from datasets.tools import v1_io  # noqa: E402

GROUPS = v1_io.GROUPS


def live_rows() -> list:
    return loader.load_rows("v1")


def first_lang(r: dict) -> str:
    return "en" if "en" in (r.get("langs") or ["en", "ja"]) else r["langs"][0]


def fmt_of(r: dict) -> str:
    return v1_io.answer_format(r)[0]


def md_table(header: list, rows: list) -> str:
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def cross(rows: list, key_row, key_col, cols: list, total=True, row_order=None) -> str:
    c = collections.Counter((key_row(r), key_col(r)) for r in rows)
    rkeys = row_order or sorted({k[0] for k in c}, key=str)
    body = []
    for rk in rkeys:
        vals = [c[(rk, ck)] for ck in cols]
        body.append([rk] + vals + ([sum(vals)] if total else []))
    if total:
        body.append(["**合計**"] + [sum(c[(rk, ck)] for rk in rkeys) for ck in cols] + [sum(c.values())])
    return md_table([""] + cols + (["計"] if total else []), body)


def n_bucket(r: dict) -> str:
    kind = v1_io.answer_format(r)[1]
    n = v1_io.answer_format(r)[2]
    if kind == "yesno":
        return "はい/いいえ"
    if kind == "score":
        return "段階評価"
    return "%d択" % n if n <= 4 else "5択以上"


def has_special(r: dict) -> tuple:
    """(any special option, the right one is special) for a choice question."""
    if r["kind"] != "choice":
        return False, False
    q = r[first_lang(r)]
    allo = [q["correct"]] + list(q["wrong"])
    pin = any(options.is_special(x) for x in allo)
    return pin, options.is_special(q["correct"])


def hints(out_dir: pathlib.Path, live_ids: set) -> tuple:
    """(Counter of issue labels, Counter of needs_new_image_type proposals, {proposal: [ids]}) over the live questions."""
    lab, need, ids = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    for p in sorted(pathlib.Path(out_dir).glob("*.jsonl")):
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            e = json.loads(ln)
            if e["id"] not in live_ids:
                continue
            for s in e.get("issues", []):
                s = s.strip()
                m = re.match(r"needs_new_image_type\s*[:：]\s*(.*)$", s)
                if m:
                    key = m.group(1).strip().lower()
                    need[key] += 1
                    ids[key].append(e["id"])
                else:
                    lab[s] += 1
    return lab, need, ids


def _share(rows, kind, pred):
    return sum(1 for r in rows if r["kind"] == kind and pred(r))


def metrics(rows: list) -> list:
    """[(label, value as text)] of the before / after comparison."""
    ch = [r for r in rows if r["kind"] == "choice"]
    sc = [r for r in rows if r["kind"] == "score"]
    yn = [r for r in rows if r["kind"] == "noul"]
    n_of = lambda r: v1_io.answer_format(r)[2]
    orders = options.v1_orders(rows)
    bal = collections.Counter()
    for r in ch:                                          # bucket = (group, free positions); a pinned right answer is outside the balancing
        langs = r.get("langs") or ["en", "ja"]
        lists = [[r[l]["correct"]] + list(r[l]["wrong"]) for l in langs]
        pin = options.pinned_indices(*lists)
        if 0 in pin:
            continue
        bal[(r["group"], len(lists[0]) - len(pin), options.expected_of(orders[r["id"]]))] += 1
    p4 = [bal[("photo", 4, p)] for p in range(4)]
    worst = 0
    for g, n in {(g, n) for g, n, _ in bal}:
        v = [bal[(g, n, p)] for p in range(n)]
        worst = max(worst, max(v) - min(v))
    sp = [has_special(r) for r in ch]
    ja_only = sum(1 for r in rows if r.get("lang") == "ja")
    ctrl = sum(1 for r in rows if r.get("relation") == "control")
    return [
        ("評価対象の問数", len(rows)),
        ("選択問題 / はい・いいえ / 段階評価", "%d / %d / %d" % (len(ch), len(yn), len(sc))),
        ("2 択", sum(1 for r in ch if n_of(r) == 2)), ("3 択", sum(1 for r in ch if n_of(r) == 3)),
        ("4 択", sum(1 for r in ch if n_of(r) == 4)), ("5〜8 択", sum(1 for r in ch if 5 <= n_of(r) <= 8)),
        ("9〜16 択", sum(1 for r in ch if n_of(r) >= 9)), ("選択肢数の種類", len({n_of(r) for r in ch})),
        ("段階評価の段階数（段階: 問数）", ", ".join("%d: %d" % kv for kv in sorted(collections.Counter(n_of(r) for r in sc).items())) or "なし"),
        ("日本語固有（lang=ja）", ja_only),
        ("否定（skill=negation）", sum(1 for r in rows if r["skill"] == "negation")),
        ("矛盾 / 不確かさ（skill）", "%d / %d" % (sum(1 for r in rows if r["skill"] == "contradiction"), sum(1 for r in rows if r["skill"] == "uncertainty"))),
        ("選択肢に「該当なし」系がある / 正解がそれ", "%d / %d" % (sum(1 for a_, b_ in sp if a_), sum(1 for a_, b_ in sp if b_))),
        ("balanced の正解位置: 全バケットの最大差", worst),
        ("balanced の正解位置: photo 4 択（位置 0〜3。「該当なし」が正解の問は除く）", " / ".join(map(str, p4))),
        ("文章のみ（txt）の問 / うち画像問の対照", "%d / %d" % (sum(1 for r in rows if r["group"] == "txt"), ctrl)),
        ("難度 easy / medium / hard", " / ".join(str(sum(1 for r in rows if r.get("difficulty") == d)) for d in ("easy", "medium", "hard"))),
        ("はい/いいえ: はい / いいえ（はい率）", "%d / %d（%.0f%%）" % (sum(1 for r in yn if r["answer"]), sum(1 for r in yn if not r["answer"]),
                                                          100.0 * sum(1 for r in yn if r["answer"]) / max(len(yn), 1))),
        ("画像の種類 astronomical / satellite", "%d / %d" % (sum(1 for r in rows if r["image_type"] == "astronomical"),
                                                       sum(1 for r in rows if r["image_type"] == "satellite"))),
    ]


def summary_md(rows: list) -> str:
    base = [r for r in rows if r.get("origin") != "new"]
    new = [r for r in rows if r.get("origin") == "new"]
    mb, mn, ma = metrics(base), metrics(new), metrics(rows)
    L = ["# v1 の不足分析（最終版・新問を含む）", "",
         "評価対象（dropped を除く）**%d 問** = legacy を磨いたもの %d + 新問 %d。`python datasets/tools/gap_analysis_v1.py --write` で再生成します（数字はすべて問題ファイルから計算）。" % (
             len(rows), len(base), len(new)),
         "新問を足す前の分析と提案（当時の数字）は `gap_analysis_v1_before.md` に記録として残してあります。", "",
         "## 追加前後の比較", "", "「追加前」は legacy を磨いたもの（新問を除く）、「新問のみ」は追加分、「追加後」は最終の v1。", "",
         md_table(["観点", "追加前", "新問のみ", "追加後"], [[a[0], a[1], ("（追加後の全体で計算）" if a[0].startswith("balanced") else b[1]), c[1]] for a, b, c in zip(mb, mn, ma)]), "",
         "読み方: 追加前に不足していた「2 択・5〜16 択、3/7/10 段階、日本語固有、否定、「該当なし」、文章のみの対照」は新問で埋まりました。",
         "はい/いいえの比、難度の比、balanced の位置は、追加後の全体で計算し直した値です（正解位置は新問を足しても既存の問の位置を動かしません）。", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review-out", default=str(ROOT / "work" / "review" / "out"))
    ap.add_argument("--write", action="store_true", help="write datasets/manifests/gap_analysis_v1.md (summary + appendix) instead of printing the appendix")
    a = ap.parse_args()
    rows = live_rows()
    if a.write:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _tables(a, rows)
        text = summary_md(rows) + "\n## 付録: 自動生成の表（`gap_analysis_v1.py`）\n\n" + buf.getvalue()
        (ROOT / "datasets" / "manifests" / "gap_analysis_v1.md").write_text(text, encoding="utf-8", newline="\n")
        print("written gap_analysis_v1.md (%d rows)" % len(rows))
        return 0
    return _tables(a, rows)


def _tables(a, rows) -> int:
    P = print
    P("## 0. 母数\n")
    allr = loader.load_rows("v1", include_dropped=True)
    P("v1 の行 %d、dropped %d、評価対象 **%d**。\n" % (len(allr), len(allr) - len(rows), len(rows)))
    P(cross(rows, lambda r: r["group"], lambda r: r["source"], sorted({r["source"] for r in rows}), row_order=list(GROUPS)))

    P("\n## 1. 群 × skill\n")
    skills = ["recognition", "ocr", "count", "spatial", "compare", "quantity", "rules", "negation", "contradiction", "uncertainty",
              "text-comprehension"]
    P(cross(rows, lambda r: r["group"], lambda r: r["skill"], skills, row_order=list(GROUPS)))
    P("\n## 2. 群 × 難度\n")
    P(cross(rows, lambda r: r["group"], lambda r: r.get("difficulty"), ["easy", "medium", "hard"], row_order=list(GROUPS)))
    P("\n## 3. 群 × 答え方（選択肢数）\n")
    bk = ["2択", "3択", "4択", "5択以上", "はい/いいえ", "段階評価"]
    P(cross(rows, lambda r: r["group"], n_bucket, bk, row_order=list(GROUPS)))
    P("\n選択肢数の内訳: " + ", ".join("%s: %d" % kv for kv in sorted(collections.Counter(fmt_of(r) for r in rows).items())))
    P("\n## 4. 段階評価の段階数\n")
    sc = [r for r in rows if r["kind"] == "score"]
    P(cross(sc, lambda r: r["group"], fmt_of, sorted({fmt_of(r) for r in sc}), row_order=sorted({r["group"] for r in sc})))
    P("\n正解の段階（0 始まり）の分布: " + ", ".join("%s: %d" % kv for kv in sorted(collections.Counter(int(r["answer"]) for r in sc).items())))
    P("\n## 5. はい/いいえの正解比\n")
    yn = [r for r in rows if r["kind"] == "noul"]
    c = collections.Counter((r["group"], bool(r["answer"])) for r in yn)
    P(md_table(["群", "問数", "はい", "いいえ", "はい率"],
               [[g, c[(g, True)] + c[(g, False)], c[(g, True)], c[(g, False)],
                 "%.0f%%" % (100.0 * c[(g, True)] / max(1, c[(g, True)] + c[(g, False)]))] for g in GROUPS if c[(g, True)] + c[(g, False)]]
               + [["**合計**", len(yn), sum(1 for r in yn if r["answer"]), sum(1 for r in yn if not r["answer"]),
                   "%.0f%%" % (100.0 * sum(1 for r in yn if r["answer"]) / len(yn))]]))
    P("\n群の中で ID の連続した区間ごと（photo は 50 問刻み、他は 25 問刻み、はい/いいえの問だけ）:\n")
    blocks = collections.defaultdict(lambda: [0, 0])
    for r in yn:
        n = int(r["id"].split("-")[1])
        step = 50 if r["group"] == "photo" else 25
        lo = (n - 1) // step * step + 1
        blocks[(r["group"], lo, lo + step - 1)][0 if r["answer"] else 1] += 1
    P(md_table(["区間", "はい", "いいえ", "はい率"],
               [["%s-%04d..%04d" % (g, lo, hi), t, f, "%.0f%%" % (100.0 * t / (t + f))] for (g, lo, hi), (t, f) in sorted(blocks.items())]))
    P("\n同じ答えが続く区間（ID 順に並べたはい/いいえの問のうち、同じ答えが 8 問以上続くもの）:\n")
    runs = []
    for g in GROUPS:
        seq = sorted((r for r in yn if r["group"] == g), key=lambda r: r["id"])
        i = 0
        while i < len(seq):
            j = i
            while j + 1 < len(seq) and bool(seq[j + 1]["answer"]) == bool(seq[i]["answer"]):
                j += 1
            if j - i + 1 >= 8:
                runs.append([g, seq[i]["id"] + ".." + seq[j]["id"], j - i + 1, "はい" if seq[i]["answer"] else "いいえ"])
            i = j + 1
    P(md_table(["群", "区間", "連続した問数", "答え"], runs))
    c2 = collections.Counter((r["source"], bool(r["answer"])) for r in yn if r["group"] == "photo")
    P("\nphoto の出どころ別: " + ", ".join("%s はい %d / いいえ %d" % (s_, c2[(s_, True)], c2[(s_, False)])
                                           for s_ in ("commons-article", "commons-category")))
    P("\n## 6. 正解位置の分布（選択問題）\n")
    ch = [r for r in rows if r["kind"] == "choice"]
    leg = collections.Counter()
    for r in ch:
        if not r.get("legacy_id"):                            # a new question has no legacy order
            continue
        n = v1_io.answer_format(r)[2]
        order = options.legacy_order(r["legacy_id"], n)
        leg[(r["group"], n, order.index(0))] += 1
    orders = options.v1_orders(ch)                        # the rule of loader.load_cases (balanced; new rows on top of the base)
    bal = collections.Counter()
    for r in ch:
        bal[(r["group"], v1_io.answer_format(r)[2], options.expected_of(orders[r["id"]]))] += 1
    keys = sorted({(g, n) for g, n, _ in list(leg) + list(bal)})
    rowsx = []
    for g, n in keys:
        L = [leg[(g, n, p)] for p in range(n)] if any(leg[(g, n, p)] for p in range(n)) else [0] * n
        B = [bal[(g, n, p)] for p in range(n)]
        rowsx.append([g, "%d択" % n, sum(L), " / ".join(map(str, L)), "%.0f%%" % (100.0 * max(L) / max(sum(L), 1)), " / ".join(map(str, B))])
    P(md_table(["群", "選択肢数", "問数", "legacy 位置 0/1/2…", "最多位置の割合", "balanced 位置 0/1/2…"], rowsx))
    P("\n## 7. 言語・文章のみ\n")
    P("lang: " + ", ".join("%s %d" % kv for kv in sorted(collections.Counter(r.get("lang", "both") for r in rows).items())))
    P("\n文章のみ（txt）: %d 問、画像の問: %d 問。" % (sum(1 for r in rows if r["group"] == "txt"), sum(1 for r in rows if r["group"] != "txt")))
    P("\n## 8. negation / count / spatial / none-of-the-above\n")
    sp = [(r, has_special(r)) for r in rows]
    P(md_table(["観点", "問数"], [
        ["skill=negation", sum(1 for r in rows if r["skill"] == "negation")],
        ["skill=count", sum(1 for r in rows if r["skill"] == "count")],
        ["skill=spatial", sum(1 for r in rows if r["skill"] == "spatial")],
        ["skill=contradiction", sum(1 for r in rows if r["skill"] == "contradiction")],
        ["skill=uncertainty", sum(1 for r in rows if r["skill"] == "uncertainty")],
        ["選択肢に「該当なし」系がある", sum(1 for _, (a_, b_) in sp if a_)],
        ["正解が「該当なし」系", sum(1 for _, (a_, b_) in sp if b_)],
    ]))
    P("\n## 9. 画像の種類（image_type）\n")
    P(cross(rows, lambda r: r["image_type"], lambda r: r["group"], list(GROUPS)))
    lab, need, ids = hints(pathlib.Path(a.review_out), {r["id"] for r in rows})
    P("\n## 10. レビュアーの指摘（issues。dropped の問を除く）\n")
    keys = ["could-be-2-options", "could-have-6-options", "score-3-levels", "negation-variant", "count-variant", "position-variant",
            "none-of-the-above-variant", "text-only-control", "ja-specific", "privacy-check", "hard-but-valid", "unverifiable"]
    P(md_table(["指摘", "問数"], [[k, sum(v for s, v in lab.items() if k in s)] for k in keys]))
    P("\n他に多かった指摘（上位 25）:\n")
    P(md_table(["指摘", "問数"], [[s, v] for s, v in lab.most_common(25)]))
    P("\n### needs_new_image_type（提案ごと）\n")
    P(md_table(["提案", "問数"], [[k, v] for k, v in need.most_common()]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
