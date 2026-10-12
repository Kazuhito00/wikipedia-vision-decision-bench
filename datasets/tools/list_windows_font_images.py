# -*- coding: utf-8 -*-
"""List the pictures whose text was drawn with fonts bundled with Windows (facts only, no legal judgement).

    python datasets/tools/list_windows_font_images.py [--write]

Source: datasets/synthetic/gen_v1_tk_ui.py, which draws real Tk windows in Segoe UI (English UI) and Yu Gothic UI (Japanese UI)
(``FAM`` there). A question's UI language is its ``lang``: "ja" -> Yu Gothic UI, otherwise (en / both) -> Segoe UI. Reads
datasets/questions/v1/new_tk_ui.jsonl (dropped rows left out); with --write, writes datasets/manifests/windows_fonts_images_v1.md.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "datasets" / "synthetic" / "gen_v1_tk_ui.py"
JSONL = ROOT / "datasets" / "questions" / "v1" / "new_tk_ui.jsonl"
OUT = ROOT / "datasets" / "manifests" / "windows_fonts_images_v1.md"


def families() -> dict:
    m = re.search(r"^FAM = (\{.*\})$", SRC.read_text(encoding="utf-8"), re.M)
    return ast.literal_eval(m.group(1))                    # {"en": "Segoe UI", "ja": "Yu Gothic UI"}


def collect() -> dict:
    fam, out = families(), collections.defaultdict(list)
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["review"]["state"] == "dropped":
            continue
        out[fam["ja" if r["lang"] == "ja" else "en"]].append((r["id"], r["local_images"][0]))
    return out


def render(by_font: dict) -> str:
    n = sum(len(v) for v in by_font.values())
    L = ["# Windows 同梱フォントで文字を描いた画像（%d 問）" % n, "",
         "事実の記載のみで、法的な判断はしません。`datasets/synthetic/gen_v1_tk_ui.py` が本物の Tk / ttk のウィンドウを作り、画面を撮った画像です。"
         "ウィンドウ内の文字は OS のフォント（英語 UI は Segoe UI、日本語 UI は Yu Gothic UI。どちらも Windows に同梱）で描かれています。"
         "OS の枠は写っていません。フォント自体は配布しません。", "",
         "| フォント | UI の言語 | 問数 |", "|---|---|---|"]
    for f, v in sorted(by_font.items()):
        L.append("| %s | %s | %d |" % (f, "日本語" if f == "Yu Gothic UI" else "英語（問は英日の両方）", len(v)))
    L += ["", "このほか、描画画像の一部（`datasets/synthetic/gen.py` の `font()`）は、その機械に Arial があれば Arial（Windows 同梱）、"
          "なければ DejaVu Sans で文字を描きます。どちらが使われたかは画像からは分かりません（旧版で作った画像の再現記録なし）。", ""]
    for f, v in sorted(by_font.items()):
        L += ["## %s（%d 問）" % (f, len(v)), "", "ID（画像の path は `generated/<ID>.png`）:", "", ", ".join(i for i, _ in sorted(v)), ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = render(collect())
    if a.write:
        OUT.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
