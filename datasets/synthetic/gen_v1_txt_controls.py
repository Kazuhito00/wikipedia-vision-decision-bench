# -*- coding: utf-8 -*-
"""New v1 questions, tag ``txt_controls``: text-only controls of image questions.

    python datasets/synthetic/gen_v1_txt_controls.py            # dry run: builds everything in memory, prints a summary
    python datasets/synthetic/gen_v1_txt_controls.py --write    # writes datasets/questions/v1/new_txt_controls.jsonl (only that file)

What a control is: the SAME question (current wording / options / right answer of the reviewed image question) with the picture removed
and an authored ``state`` that describes the picture's content in words. Comparing the accuracy on the image question with the accuracy on
its control tells how much the picture matters.

How the description is made: nothing is typed by hand per question. The three picture generators (gen_v1_new.py, gen_v1_tk_ui.py,
gen_v1_ja.py) are IMPORTED (never run, never ``--apply``) and their spec functions are called in memory:
  * rendered: every ``p_*`` function is called as ``main`` does and its local variables (the drawing parameters) are read from the frame
    when it returns (``sys.setprofile``); ``shape`` calls are recorded as well.
  * tk_ui: the ``build_*`` widget builders are replaced by recorders, so ``build(None)`` returns the exact arguments the window would be
    built from (no Tk window is ever opened).
  * ja_specific: the ``draw_*`` functions are replaced by recorders that keep the arguments.
A candidate is used only when the generator's spec equals the CURRENT row of the jsonl (same options as a set, same right answer);
otherwise (reviewed with a changed answer, dropped, ...) it is skipped. Pictures and the three source jsonl files are never written.
"""
from __future__ import annotations

import argparse
import calendar
import collections
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

V1DIR = ROOT / "datasets" / "questions" / "v1"
OUT = V1DIR / "new_txt_controls.jsonl"
FIRST_ID = 1001

import gen_v1_new as GN      # noqa: E402
import gen_v1_tk_ui as GT    # noqa: E402
import gen_v1_ja as GJ       # noqa: E402

EN_FRAME = "No picture is attached. The picture showed: "
JA_FRAME = "画像は添付されていません。画像の内容: "
MAX_STATE = 600


def load(tag):
    with open(V1DIR / ("new_%s.jsonl" % tag), encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}


def same_spec(spec_en, spec_ja, spec_kind, spec_answer, row):
    """The generator's spec equals the current row (options as a set, right answer, kind). Returns (ok, wording_changed)."""
    if row["kind"] != spec_kind:
        return False, False
    wording = False
    for L, sp in (("en", spec_en), ("ja", spec_ja)):
        if sp is None:
            if L in row:
                return False, False
            continue
        cur = row.get(L)
        if cur is None:
            return False, False
        if sp.get("instr") != cur.get("instr"):
            wording = True
        if spec_kind == "choice":
            if sp["correct"] != cur["correct"] or sorted(sp["wrong"]) != sorted(cur["wrong"]):
                return False, False
        elif spec_kind == "score":
            if sp["levels"] != cur["levels"]:
                return False, False
    if spec_kind in ("noul", "score") and spec_answer != row.get("answer"):
        return False, False
    return True, wording


# ============================================================================================ helpers for wording
def art(w):
    return "an" if w[:1].lower() in "aeiou" else "a"


def cj(c):
    return GN.COLOR_JA[c]


def sj(k):
    return GN.SHAPE_JA[k]


RGB2NAME = {tuple(v): k for k, v in GN.COLORS.items()}


def cname(rgb):
    return RGB2NAME.get(tuple(rgb), "grey")


def join_en(xs):
    return ", ".join(xs)


def join_ja(xs):
    return "、".join(xs)


class Skip(Exception):
    pass


# ============================================================================================ rendered describers
# each takes (locals of the p_* function, recorded shape calls, spec) -> (en, ja)
def r_bar_tallest(l, rec, sp):
    vals, n = l["vals"], l["n"]
    L = GN.LET[:n]
    en = ("A bar chart with %d vertical bars labelled %s from left to right (axis 0-100, gridlines at 25, 50, 75 and 100). Bar heights: %s."
          % (n, join_en(L), join_en("%s %d" % (a, v) for a, v in zip(L, vals))))
    ja = ("縦棒グラフ。棒が %d 本あり、左から %s のラベルが付いている（軸は 0〜100、目盛り線は 25・50・75・100）。棒の高さ: %s。"
          % (n, "・".join(L), join_ja("%s %d" % (a, v) for a, v in zip(L, vals))))
    return en, ja


def r_pie(l, rec, sp):
    v, n = l["v"], l["n"]
    L = GN.LET[:n]
    rv = [round(x) for x in v]
    if sorted(rv)[-1] == sorted(rv)[-2] or rv.index(max(rv)) != v.index(max(v)):
        raise Skip("pie rounding")
    en = ("A pie chart with %d slices labelled %s, going clockwise from the top. Share of the whole: %s."
          % (n, join_en(L), join_en("%s about %d%%" % (a, x) for a, x in zip(L, rv))))
    ja = ("円グラフ。区画が %d 個あり、上から時計回りに %s のラベルが付いている。全体に占める割合: %s。"
          % (n, "・".join(L), join_ja("%s 約 %d%%" % (a, x) for a, x in zip(L, rv))))
    return en, ja


def _level_of(sp, val, lo_hi):
    """Re-derive the level from the printed number with the row's own level labels."""
    return None


def r_hbar(l, rec, sp):
    v, n, w = l["v"], l["n"], l["w"]
    vr = round(v)
    if int(vr // w) != l["level"]:
        raise Skip("rounding")
    mx = n * w
    return ('A horizontal bar gauge titled "Download speed", scale 0 to %d (unit Mbps), tick marks every %d. The filled part of the bar ends at %d.'
            % (mx, w, vr),
            "「Download speed」という見出しの横棒ゲージ。目盛りは 0〜%d（単位 Mbps）で、%d ごとに刻みがある。塗られた部分は %d の位置まで。" % (mx, w, vr))


def r_thermo(l, rec, sp):
    v, n, w = l["v"], l["n"], l["w"]
    vr = round(v)
    if int(vr // w) != l["level"]:
        raise Skip("rounding")
    mx = n * w
    return ('A thermometer labelled "Water temperature (°C)", scale 0 to %d with marks every %d. The red liquid column reaches %d °C.' % (mx, w, vr),
            "「Water temperature (°C)」と書かれた温度計。目盛りは 0〜%d で、%d ごとに刻みがある。赤い液柱は %d °C の位置まで。" % (mx, w, vr))


def r_dial(l, rec, sp):
    v, n, w = l["v"], l["n"], l["w"]
    vr = round(v)
    if int(vr // w) != l["level"]:
        raise Skip("rounding")
    mx = n * w
    return ('A semicircular dial titled "Speed", scale 0 to %d (unit km/h) with marks every %d. The red needle points at %d km/h.' % (mx, w, vr),
            "「Speed」という見出しの半円形のダイヤル。目盛りは 0〜%d（単位 km/h）で、%d ごとに刻みがある。赤い針は %d km/h を指している。" % (mx, w, vr))


def r_donut(l, rec, sp):
    pct, n = l["pct"], l["n"]
    pr = round(pct)
    if int(pct // (100 / n)) != int(pr // (100 / n)):
        raise Skip("rounding")
    return ('A ring-shaped progress indicator labelled "Upload progress", with %d evenly spaced marks around it. The coloured arc, starting at the top and going clockwise, covers %d%% of the ring.'
            % (n, pr),
            "「Upload progress」と書かれたリング状の進捗表示。リングの周りには等間隔に %d 個の目盛りがある。上から時計回りに色が付いた部分は、リング全体の %d%% を占めている。" % (n, pr))


def r_battery(l, rec, sp):
    pct = l["pct"]
    pr = round(pct)
    if int(pct // (100 / 3)) != int(pr // (100 / 3)):
        raise Skip("rounding")
    return ('A battery icon titled "Battery" with marks at 0%%, 33%%, 67%% and 100%% under it. The green fill covers %d%% of the battery.' % pr,
            "「Battery」という見出しの電池の絵。下に 0%%・33%%・67%%・100%% の目盛りがある。緑の塗りは電池全体の %d%% を占めている。" % pr)


def r_stars(l, rec, sp):
    k = l["k"]
    title = ["Customer rating", "Hotel rating", "Movie rating", "Service rating"][l["i"] % 4]
    rest_en = "" if k == 5 else (" The other %s grey outline%s." % ("one is a" if k == 4 else "%d are" % (5 - k), "" if k == 4 else "s"))
    rest_ja = "" if k == 5 else "残りの %d 個は灰色の枠だけ。" % (5 - k)
    return ('A row of 5 stars under the title "%s". %s%s'
            % (title, ("All 5 stars are filled yellow." if k == 5 else "The first %d star%s (from the left) %s filled yellow." % (k, "" if k == 1 else "s", "is" if k == 1 else "are")), rest_en),
            "「%s」という見出しの下に星が 5 個並んでいる。%s%s" % (title, "5 個とも黄色で塗られている。" if k == 5 else "左から %d 個が黄色で塗られ、" % k, rest_ja))


def r_signal(l, rec, sp):
    k = l["k"]
    if k == 7:
        return ('Titled "Signal strength": 7 vertical bars of increasing height from left to right, all dark blue.',
                "「Signal strength」という見出し。左から右へだんだん高くなる縦棒が 7 本あり、すべて濃い青。")
    return ('Titled "Signal strength": 7 vertical bars of increasing height from left to right. The first %d bar%s (from the left) %s dark blue, the other %d %s light grey.'
            % (k, "" if k == 1 else "s", "is" if k == 1 else "are", 7 - k, "is" if 7 - k == 1 else "are"),
            "「Signal strength」という見出し。左から右へだんだん高くなる縦棒が 7 本ある。左から %d 本は濃い青、残りの %d 本は薄い灰色。" % (k, 7 - k))


def r_volume(l, rec, sp):
    k = l["k"]
    if k == 10:
        return ('Titled "Volume": a row of 10 equal blocks, all orange.', "「Volume」という見出し。同じ大きさのブロックが 10 個横に並んでいて、すべてオレンジ色。")
    return ('Titled "Volume": a row of 10 equal blocks. The first %d block%s (from the left) %s orange, the other %d %s light grey.'
            % (k, "" if k == 1 else "s", "is" if k == 1 else "are", 10 - k, "is" if 10 - k == 1 else "are"),
            "「Volume」という見出し。同じ大きさのブロックが 10 個横に並んでいる。左から %d 個はオレンジ色、残りの %d 個は薄い灰色。" % (k, 10 - k))


def r_two_bars(l, rec, sp):
    a, b = l["a"], l["b"]
    return ("Two bars standing on a common baseline, A (blue, left) and B (orange, right), each as wide as the other. On a common scale where the maximum possible height is 100, A is %d tall and B is %d tall." % (a, b),
            "同じ基準線の上に、同じ幅の棒が 2 本立っている。左が A（青）、右が B（橙）。最大を 100 とする共通の目盛りで、A の高さは %d、B の高さは %d。" % (a, b))


def r_larger2(l, rec, sp):
    ra, rb = l["ra"], l["rb"]
    return ("Two circles on one row of a 640 x 480 picture: A (green, left) with radius %d px and B (purple, right) with radius %d px." % (ra, rb),
            "640 x 480 の画像の同じ高さに円が 2 つある。左が A（緑）で半径 %d px、右が B（紫）で半径 %d px。" % (ra, rb))


def r_circles3(l, rec, sp):
    rs = l["rs"]
    cn_ = [("blue", "青"), ("orange", "橙"), ("green", "緑")]
    L = "ABC"
    return ("Three circles in a row on a 640 x 480 picture, labelled A, B, C from left to right: A (blue) radius %d px, B (orange) radius %d px, C (green) radius %d px." % tuple(rs),
            "640 x 480 の画像に円が横一列に 3 つあり、左から A・B・C のラベルが付いている。A（青）は半径 %d px、B（橙）は半径 %d px、C（緑）は半径 %d px。" % tuple(rs))


def r_colour_most(l, rec, sp):
    cols, cnt = l["cols"], l["cnt"]
    en = "Plain circles of the same size scattered over the picture, %d in total, in %d colours: %s." % (
        sum(cnt), len(cols), join_en("%s %d" % (c, k) for c, k in zip(cols, cnt)))
    ja = "同じ大きさの円が画像に散らばっていて、全部で %d 個、%d 色ある。色ごとの個数: %s。" % (
        sum(cnt), len(cols), join_ja("%s %d" % (cj(c), k) for c, k in zip(cols, cnt)))
    return en, ja


def r_absent_colour(l, rec, sp):
    shown = l["shown"]
    return ("Circles of the same size on a plain background, one for each of these colours: %s (%d circles in total)." % (join_en(shown), len(shown)),
            "同じ大きさの円が無地の背景に並んでいる。円の色は次のとおりで、各色 1 個ずつ（全部で %d 個）: %s。" % (len(shown), join_ja(cj(c) for c in shown)))


def r_absent_shape(l, rec, sp):
    shown, cols = l["shown"], l["cols"]
    pairs = list(zip(shown, cols))
    return ("Shapes of the same size on a plain background, one each (%d in total): %s." % (len(pairs), join_en("%s %s %s" % (art(c), c, k) for k, c in pairs)),
            "同じ大きさの図形が無地の背景に 1 個ずつ並んでいる（全部で %d 個）: %s。" % (len(pairs), join_ja("%sの%s" % (cj(c), sj(k)) for k, c in pairs)))


def r_no_taller_first(l, rec, sp):
    vals = l["vals"]
    L = GN.LET[:len(vals)]
    return ("A bar chart with %d vertical bars labelled %s from left to right (axis 0-100). Bar heights: %s." % (len(vals), join_en(L), join_en("%s %d" % (a, v) for a, v in zip(L, vals))),
            "縦棒グラフ。棒が %d 本あり、左から %s のラベルが付いている（軸は 0〜100）。棒の高さ: %s。" % (len(vals), "・".join(L), join_ja("%s %d" % (a, v) for a, v in zip(L, vals))))


def r_no_red_circle(l, rec, sp):
    items = l["items"]
    return ("Six circles of the same size scattered over the picture. Their colours: %s." % join_en(items),
            "同じ大きさの円が 6 個、画像に散らばっている。円の色: %s。" % join_ja(cj(c) for c in items))


def r_no_triangle(l, rec, sp):
    kinds = l["kinds"]
    return ("Six shapes of the same size scattered over the picture, in assorted colours. Their shapes: %s." % join_en(kinds),
            "同じ大きさの図形が 6 個、画像に散らばっている（色はさまざま）。図形の種類: %s。" % join_ja(sj(k) for k in kinds))


def r_labeled_bars(l, rec, sp):
    vals = l["vals"]
    L = GN.LET[:len(vals)]
    return ("A bar chart with %d vertical bars labelled %s from left to right; the value of each bar is printed above it: %s." % (len(vals), join_en(L), join_en("%s = %d" % (a, v) for a, v in zip(L, vals))),
            "縦棒グラフ。棒が %d 本あり、左から %s のラベルが付いていて、各棒の上にその値が書かれている: %s。" % (len(vals), "・".join(L), join_ja("%s は %d" % (a, v) for a, v in zip(L, vals))))


def r_dice(l, rec, sp):
    vals = l["vals"]
    L = GN.LET[:len(vals)]
    return ("%d dice (white, black pips) laid out in rows, labelled %s; the number of pips on each: %s." % (len(vals), join_en(L), join_en("%s %d" % (a, v) for a, v in zip(L, vals))),
            "さいころが %d 個、何列かに並んでいて、%s のラベルが付いている。各さいころの目の数: %s。" % (len(vals), "・".join(L), join_ja("%s は %d" % (a, v) for a, v in zip(L, vals))))


def r_row_neighbour(l, rec, sp):
    cols = l["cols"]
    return ("Five circles of the same size in one row, from left to right: %s." % join_en(cols),
            "同じ大きさの円が横一列に 5 個ある。左から順に: %s。" % join_ja(cj(c) for c in cols))


def r_between(l, rec, sp):
    cols = l["cols"]
    return ("Five circles of the same size in one row, from left to right: %s." % join_en(cols),
            "同じ大きさの円が横一列に 5 個ある。左から順に: %s。" % join_ja(cj(c) for c in cols))


def r_grid_rel(l, rec, sp):
    cells = l["cells"]
    rows_en = ["row %d: %s" % (i + 1, join_en("%s %s" % (c, k) for k, c in cells[3 * i:3 * i + 3])) for i in range(3)]
    rows_ja = ["%d 行目: %s" % (i + 1, join_ja("%sの%s" % (cj(c), sj(k)) for k, c in cells[3 * i:3 * i + 3])) for i in range(3)]
    return ("A 3 x 3 arrangement of shapes (no grid lines); from the top, each row from left to right - %s." % "; ".join(rows_en),
            "図形が 3 x 3 に並んでいる（罫線なし）。上の行から、各行は左から順に - %s。" % "。".join(rows_ja))


def r_count_red(l, rec, sp):
    circles = sorted((cx, cname(f)) for (kd, cx, cy, rr, f) in rec if kd == "circle")
    cols = [c for _, c in circles]
    if len(cols) > 16:
        raise Skip("too many")
    return ("%d circles of the same size scattered over the picture. Their colours, listed from the leftmost to the rightmost: %s." % (len(cols), join_en(cols)),
            "同じ大きさの円が %d 個、画像に散らばっている。色を左のものから右のものへ順に: %s。" % (len(cols), join_ja(cj(c) for c in cols)))


def r_caption_shapes(l, rec, sp):
    a, b, ca, cb = l["a"], l["b"], l["ca"], l["cb"]
    cap = '"%d red circle%s, %d blue square%s"' % (ca, "" if ca == 1 else "s", cb, "" if cb == 1 else "s")
    return ("Red circles and blue squares scattered over the upper part of the picture: %d red circles and %d blue squares. A dark caption bar along the bottom reads %s." % (a, b, cap),
            "画像の上の方に赤い円が %d 個と青い四角が %d 個、散らばっている。下には暗い帯があり、英語で「%s」と書かれている。" % (a, b, cap.strip('"')))


def r_caption_chart(l, rec, sp):
    vals, cap = l["vals"], l["cap"]
    L = GN.LET[:len(vals)]
    return ('A bar chart with %d vertical bars labelled %s from left to right (axis 0-100). Bar heights: %s. A dark caption bar along the bottom reads "%s".'
            % (len(vals), join_en(L), join_en("%s %d" % (a, v) for a, v in zip(L, vals)), cap),
            "縦棒グラフ。棒が %d 本あり、左から %s のラベルが付いている（軸は 0〜100）。棒の高さ: %s。下には暗い帯があり、英語で「%s」と書かれている。"
            % (len(vals), "・".join(L), join_ja("%s %d" % (a, v) for a, v in zip(L, vals)), cap))


def r_hidden_bar(l, rec, sp):
    vals, hidden = l["vals"], l["hidden"]
    if hidden:
        return ("A bar chart with 4 vertical bars labelled A, B, C, D from left to right (axis 0-100). A is %d, B is %d and C is %d. Bar D is completely covered by a grey box marked \"?\" that reaches above the top of every bar, so its height cannot be seen."
                % (vals[0], vals[1], vals[2]),
                "縦棒グラフ。棒が 4 本あり、左から A・B・C・D のラベルが付いている（軸は 0〜100）。A は %d、B は %d、C は %d。D の棒は「?」と書かれた灰色の箱で完全に隠されていて、箱はどの棒よりも高い位置まで届いているため、D の高さは見えない。"
                % (vals[0], vals[1], vals[2]))
    return ("A bar chart with 4 vertical bars labelled A, B, C, D from left to right (axis 0-100). A is %d, B is %d and C is %d. A grey box marked \"?\" covers the lower part of bar D only; the top of D is visible, at height %d."
            % (vals[0], vals[1], vals[2], vals[3]),
            "縦棒グラフ。棒が 4 本あり、左から A・B・C・D のラベルが付いている（軸は 0〜100）。A は %d、B は %d、C は %d。D の棒は下の部分だけ「?」と書かれた灰色の箱で隠されていて、棒の先端は見えており、高さ %d の位置にある。"
            % (vals[0], vals[1], vals[2], vals[3]))


def r_grid_cell(l, rec, sp):
    n = l["n"]
    L = GN.LET[:n]
    if len(rec) != n:
        raise Skip("shape records")
    cells = [("%s: %s %s" % (L[k], cname(f), kd), "%s: %sの%s" % (L[k], cj(cname(f)), sj(kd))) for k, (kd, cx, cy, rr, f) in enumerate(rec)]
    rows, cols = GN.grid_dims(n)
    return ("A grid of %d lettered cells (%d rows x %d columns, letters %s in reading order, each letter in the top-left corner of its cell), one shape in each cell: %s."
            % (n, rows, cols, "A-" + L[-1], "; ".join(c[0] for c in cells)),
            "文字の付いたマスが %d 個の格子（%d 行 x %d 列）。文字は読む順に %s で、各マスの左上に書かれている。各マスには図形が 1 つずつ: %s。"
            % (n, rows, cols, "A〜" + L[-1], "、".join(c[1] for c in cells)))


def r_color_circle(l, rec, sp):
    x, kinds, opt_pool = l["x"], l["kinds"], l["opt_pool"]
    parts = [("%s %s" % (x, "circle"), "%sの%s" % (cj(x), sj("circle")))]
    for k in range(4):
        parts.append(("%s %s" % (opt_pool[k], kinds[k]), "%sの%s" % (cj(opt_pool[k]), sj(kinds[k]))))
    return ("Five shapes of the same size scattered over a plain background: %s." % join_en(p[0] for p in parts),
            "同じ大きさの図形が無地の背景に 5 個散らばっている: %s。" % join_ja(p[1] for p in parts))


RENDERED = {
    "p_bar_tallest": r_bar_tallest, "p_pie": r_pie, "p_hbar": r_hbar, "p_thermo": r_thermo, "p_dial": r_dial, "p_donut": r_donut,
    "p_battery": r_battery, "p_stars": r_stars, "p_signal": r_signal, "p_volume": r_volume, "p_two_bars": r_two_bars,
    "p_larger2": r_larger2, "p_circles3": r_circles3, "p_colour_most": r_colour_most, "p_absent_colour": r_absent_colour,
    "p_absent_shape": r_absent_shape, "p_no_taller_first": r_no_taller_first, "p_no_red_circle": r_no_red_circle,
    "p_no_triangle": r_no_triangle, "p_labeled_bars": r_labeled_bars, "p_dice": r_dice, "p_row_neighbour": r_row_neighbour,
    "p_between": r_between, "p_grid_rel": r_grid_rel, "p_count_red": r_count_red, "p_caption_shapes": r_caption_shapes,
    "p_caption_chart": r_caption_chart, "p_hidden_bar": r_hidden_bar, "p_grid_cell": r_grid_cell, "p_color_circle": r_color_circle,
}

# quotas: pattern -> how many controls (spread evenly over the usable variants)
RENDERED_QUOTA = {
    "p_bar_tallest": 2, "p_pie": 2, "p_hbar": 1, "p_thermo": 1, "p_dial": 1, "p_donut": 1, "p_battery": 1,
    "p_stars": 1, "p_signal": 1, "p_volume": 1, "p_two_bars": 1, "p_larger2": 1, "p_circles3": 1, "p_colour_most": 2,
    "p_absent_colour": 2, "p_absent_shape": 2, "p_no_taller_first": 2, "p_no_red_circle": 1, "p_no_triangle": 1,
    "p_labeled_bars": 2, "p_dice": 2, "p_row_neighbour": 2, "p_grid_rel": 2, "p_between": 1, "p_count_red": 2,
    "p_caption_shapes": 1, "p_caption_chart": 2, "p_hidden_bar": 2, "p_grid_cell": 2, "p_color_circle": 1,
}


def collect_rendered(rows):
    out = []
    plan = GN.build_plan()
    GN.assign_levels(plan)
    rec = []
    orig_shape = GN.shape

    def shape_rec(d, kind, cx, cy, r, fill, outline=GN.INK, w=3):
        rec.append((kind, cx, cy, r, fill))
        return orig_shape(d, kind, cx, cy, r, fill, outline, w)

    GN.shape = shape_rec
    try:
        for e in plan:
            fn = e["fn"]
            rec.clear()
            box = {}

            def prof(frame, event, arg, fn=fn, box=box):
                if event == "return" and frame.f_code is fn.__code__:
                    box["l"] = dict(frame.f_locals)
            sys.setprofile(prof)
            try:
                im, spec = fn(e["id"], **e["kw"])
            finally:
                sys.setprofile(None)
            row = rows.get(e["id"])
            if row is None or row["review"]["state"] == "dropped":
                continue
            ok, wording = same_spec(spec.get("en"), spec.get("ja"), spec["kind"], spec.get("answer"), row)
            if not ok:
                continue
            desc = RENDERED.get(fn.__name__)
            if desc is None:
                continue
            try:
                en, ja = desc(box["l"], list(rec), spec)
            except Skip:
                continue
            out.append(dict(src="rendered", qid=e["id"], pat=fn.__name__, row=row, wording=wording, en=en, ja=ja))
    finally:
        GN.shape = orig_shape
    return out


# ============================================================================================ tk_ui describers
def yn_en(on, a, b):
    return a if on else b


def t_checks(L, sl, head, items, cols=1):
    if L == "en":
        return 'A settings window titled "%s" with a list of checkboxes: %s.' % (head, join_en("%s (%s)" % (t, "checked" if on else "unchecked") for t, on in items))
    return "「%s」というタイトルの設定画面。チェックボックスの一覧: %s。" % (head, join_ja("%s（%s）" % (t, "チェックあり" if on else "チェックなし") for t, on in items))


def t_groups(L, sl, head, groups):
    if L == "en":
        return 'A window titled "%s" with group boxes side by side, each holding checkboxes: %s.' % (
            head, "; ".join('group "%s": %s' % (g, join_en("%s (%s)" % (t, "checked" if on else "unchecked") for t, on in its)) for g, its in groups))
    return "「%s」というタイトルの画面。チェックボックスを入れた枠（グループ）が横に並んでいる: %s。" % (
        head, "。".join("グループ「%s」: %s" % (g, join_ja("%s（%s）" % (t, "チェックあり" if on else "チェックなし") for t, on in its)) for g, its in groups))


def t_radio(L, sl, head, opts, selected, cols=1):
    if L == "en":
        return 'A group box titled "%s" with radio buttons: %s.' % (head, join_en("%s (%s)" % (o, "selected" if o == selected else "not selected") for o in opts))
    return "「%s」という枠の中にラジオボタンがある: %s。" % (head, join_ja("%s（%s）" % (o, "選択中" if o == selected else "未選択") for o in opts))


def t_combos(L, sl, head, rows):
    if L == "en":
        return 'A window titled "%s" with closed dropdown boxes, each showing its current value: %s.' % (head, join_en("%s = %s" % (lb, cur) for lb, vals, cur in rows))
    return "「%s」というタイトルの画面。閉じたドロップダウンが並び、それぞれ現在の値が表示されている: %s。" % (head, join_ja("%s = %s" % (lb, cur) for lb, vals, cur in rows))


def t_switches(L, sl, head, items, show_text):
    if L == "en":
        return 'A window titled "%s" with toggle switches (green = on, grey = off%s): %s.' % (
            head, ", with an ON/OFF text beside each" if show_text else "", join_en("%s (%s)" % (t, "on" if on else "off") for t, on in items))
    return "「%s」というタイトルの画面。トグルスイッチが並んでいる（緑がオン、灰色がオフ%s）: %s。" % (
        head, "。各スイッチの横に ON / OFF の文字もある" if show_text else "", join_ja("%s（%s）" % (t, "オン" if on else "オフ") for t, on in items))


def t_form(L, sl, head, rows, err_idx):
    en_p, ja_p = [], []
    for label, text, err, show in rows:
        if show:
            val_en, val_ja = "masked with asterisks (%d characters)" % len(text), "アスタリスクで伏せられている（%d 文字）" % len(text)
        elif text == "":
            val_en, val_ja = "empty", "空欄"
        else:
            val_en, val_ja = '"%s"' % text, "「%s」" % text
        if err:
            en_p.append('%s: %s, red outline, with the red message "%s" under it' % (label, val_en, err))
            ja_p.append("%s: %s、赤い枠で、その下に赤い文字で「%s」と表示" % (label, val_ja, err))
        else:
            en_p.append("%s: %s, grey outline, no message" % (label, val_en))
            ja_p.append("%s: %s、灰色の枠で、メッセージなし" % (label, val_ja))
    if L == "en":
        return 'A form titled "%s" with entry boxes: %s.' % (head, "; ".join(en_p))
    return "「%s」というタイトルの入力フォーム。入力欄: %s。" % (head, "。".join(ja_p))


def t_dialog(L, sl, kind, msg, btns, disabled):
    color, ten, tja = GT.DLG_STYLE[kind]
    hdr = ten if sl == "en" else tja
    colname_en = {"error": "red", "warning": "orange", "confirm": "blue", "info": "green"}[kind]
    colname_ja = {"error": "赤", "warning": "橙", "confirm": "青", "info": "緑"}[kind]
    m = msg.replace("\n", " / ")
    names = [GT.lab(GT.BTN[b], sl) for b in btns]
    if L == "en":
        return 'A dialog box with a %s header strip reading "%s". Message: "%s". Buttons: %s.' % (
            colname_en, hdr, m, join_en("%s (%s)" % (n, "grayed out, disabled" if b in disabled else "enabled") for n, b in zip(names, btns)))
    return "ダイアログ。%s色の帯に「%s」と書かれている。メッセージ: 『%s』。ボタン: %s。" % (
        colname_ja, hdr, m, join_ja("%s（%s）" % (n, "グレーアウトで無効" if b in disabled else "有効") for n, b in zip(names, btns)))


def t_tree(L, sl, head, cols, rows, selected=None):
    rr = []
    for i, r in enumerate(rows):
        s = " | ".join(str(x) for x in r)
        if selected is not None and i == selected:
            s += (" (highlighted row)" if L == "en" else "（ハイライトされた行）")
        rr.append(s)
    if L == "en":
        return 'A table titled "%s" with columns %s. Rows from top to bottom: %s.' % (head, join_en(cols), "; ".join(rr))
    return "「%s」というタイトルの表。列は %s。上から順の行: %s。" % (head, join_ja(cols), "、".join(rr))


def t_notebook(L, sl, tabs, cur, extra):
    if L == "en":
        return ("A tabbed panel with %d tabs from left to right: %s. The selected tab is drawn blue with white text, the others grey; the page body only shows placeholder grey bars."
                % (len(tabs), join_en("%s%s" % (t, " (selected)" if i == cur else "") for i, t in enumerate(tabs))))
    return ("タブ付きのパネル。左から順に %d 個のタブ: %s。選択中のタブは青地に白文字、ほかは灰色。中身は灰色の線だけのプレースホルダー。"
            % (len(tabs), join_ja("%s%s" % (t, "（選択中）" if i == cur else "") for i, t in enumerate(tabs))))


def t_menu(L, sl, menus, cur, items):
    if L == "en":
        return ('A menu bar with %s; the "%s" menu (highlighted blue) is open. Its items from top to bottom, with the keyboard shortcut at the right: %s.'
                % (join_en('"%s"' % m for m in menus), menus[cur],
                   join_en("%s%s%s" % (lb, (" " + sc) if sc else "", " (grayed out)" if dis else "") for lb, sc, dis in items)))
    return ("メニューバーに %s が並び、「%s」メニュー（青く強調）が開いている。上から順の項目（右端はショートカットキー）: %s。"
            % (join_ja("「%s」" % m for m in menus), menus[cur],
               join_ja("%s%s%s" % (lb, (" " + sc) if sc else "", "（グレーアウト）" if dis else "") for lb, sc, dis in items)))


def t_sliders(L, sl, rows, show_val):
    if L == "en":
        if show_val:
            return "Horizontal sliders with scale 0 to 100, the value printed at the right of each: %s." % join_en("%s %d" % (lb, v) for lb, v in rows)
        return "Horizontal sliders with scale 0 to 100 (only the end values 0 and 100 are printed, no current value). Knob positions: %s." % join_en(
            "%s at about %d%% of the track" % (lb, v) for lb, v in rows)
    if show_val:
        return "横向きのスライダー（目盛りは 0〜100）。各スライダーの右に現在の値が書かれている: %s。" % join_ja("%s %d" % (lb, v) for lb, v in rows)
    return "横向きのスライダー（目盛りは 0〜100。両端の 0 と 100 だけが書かれ、現在の値は書かれていない）。つまみの位置: %s。" % join_ja(
        "%s は軌道の約 %d%% の位置" % (lb, v) for lb, v in rows)


def t_bars(L, sl, rows, show_val, wide=420):
    if L == "en":
        if show_val:
            return "Horizontal progress bars (full = 100%%), each with its percentage printed at the right: %s." % join_en("%s %d%%" % (lb, v) for lb, v in rows)
        return "Horizontal progress bars (full = 100%%), no number printed. Filled lengths: %s." % join_en("%s filled to about %d%%" % (lb, v) for lb, v in rows)
    if show_val:
        return "横向きの進捗バー（満タンが 100%%）。各バーの右に割合が書かれている: %s。" % join_ja("%s %d%%" % (lb, v) for lb, v in rows)
    return "横向きの進捗バー（満タンが 100%%、数字の表示はない）。塗られた長さ: %s。" % join_ja("%s は約 %d%%" % (lb, v) for lb, v in rows)


def t_list_spin(L, sl, items, cur, qty):
    qlabel = "Quantity" if sl == "en" else "数量"
    if L == "en":
        return 'A list box with the items %s, and next to it a spin box labelled "%s" showing %d.' % (
            join_en("%s%s" % (t, " (highlighted in blue)" if i == cur else "") for i, t in enumerate(items)), qlabel, qty)
    return "リストボックスに上から順に %s が並び、その横に「%s」というラベルのスピンボックスがあって %d と表示されている。" % (
        join_ja("%s%s" % (t, "（青くハイライト）" if i == cur else "") for i, t in enumerate(items)), qlabel, qty)


def t_mail(L, sl, folders, sel, rows, status):
    if L == "en":
        fo = join_en("%s%s%s" % (n, (" with red badge %d" % u) if u else "", " (selected)" if i == sel else "") for i, (n, u) in enumerate(folders))
        ro = join_en("%s - %s%s" % (a, b, " (bold)" if f else "") for a, b, f in rows)
        return 'A mail window. Left sidebar folders: %s. Right table (From - Subject), rows from top to bottom: %s. Status bar: "%s".' % (fo, ro, status)
    fo = join_ja("%s%s%s" % (n, ("（赤いバッジ %d）" % u) if u else "", "（選択中）" if i == sel else "") for i, (n, u) in enumerate(folders))
    ro = join_ja("%s - %s%s" % (a, b, "（太字）" if f else "") for a, b, f in rows)
    return "メールの画面。左のサイドバーのフォルダー: %s。右の表（差出人 - 件名）の上から順の行: %s。ステータスバー:「%s」。" % (fo, ro, status)


def t_orders(L, sl, tabs, rows, status):
    idx = 0 if sl == "en" else 1
    colour = {"Paid": ("green", "緑"), "Pending": ("yellow", "黄"), "Error": ("red", "赤"), "Cancelled": ("grey", "灰色")}
    if L == "en":
        ro = "; ".join("%s | %s | %s (%s row)" % (oid, GT.ST[st][idx], amt, colour[st][0]) for oid, st, amt in rows)
        return 'A window with tabs %s (first tab selected). The table (Order | Status | Amount), rows from top to bottom: %s. Status bar: "%s".' % (join_en(tabs), ro, status)
    ro = "、".join("%s | %s | %s（%s色の行）" % (oid, GT.ST[st][idx], amt, colour[st][1]) for oid, st, amt in rows)
    return "タブ（%s）のある画面（先頭のタブを選択中）。表（注文 | 状態 | 金額）の上から順の行: %s。ステータスバー:「%s」。" % (join_ja(tabs), ro, status)


TK_DESC = {
    "build_checks": t_checks, "build_groups": t_groups, "build_radio": t_radio, "build_combos": t_combos, "build_switches": t_switches,
    "build_form": t_form, "build_dialog": t_dialog, "build_tree": t_tree, "build_notebook": t_notebook, "build_menu": t_menu,
    "build_sliders": t_sliders, "build_bars": t_bars, "build_list_spin": t_list_spin, "build_mail": t_mail, "build_orders": t_orders,
}

TK_QUOTA = {
    "chk_list": 3, "chk_group": 2, "radio": 2, "combo": 1, "slider": 2, "progress": 1, "prog_cmp": 1, "switches": 3, "form_err": 2,
    "form_val": 1, "dialog_btn": 2, "dialog_cat": 1, "tree_maxmin": 2, "tree_sum": 2, "tree_sel": 1, "tree_sorted": 2, "notebook": 1,
    "menu": 2, "list_spin": 1, "mail": 2, "orders": 2, "chk_list_ja": 1, "form_err_ja": 1, "dialog_btn_ja": 1, "tree_ja": 1,
}


def collect_tk(rows):
    calls = []
    saved = {}
    for name in TK_DESC:
        saved[name] = getattr(GT, name)

        def mk(nm):
            def rec(*a, **k):
                calls.append((nm, a, k))
            return rec
        setattr(GT, name, mk(name))
    out = []
    try:
        items = GT.build_all()
        for i, (pattern, build, theme, fs, q) in enumerate(items):
            qid = "biz-%04d" % (GT.START_ID + i)
            row = rows.get(qid)
            calls.clear()
            try:
                build(None)
            except Exception:
                continue
            if row is None or row["review"]["state"] == "dropped" or len(calls) != 1:
                continue
            lang = q["lang"]
            sp_en, sp_ja = q.get("en"), q.get("ja")
            ok, wording = same_spec(sp_en, sp_ja, q["kind"], q.get("answer"), row)
            if not ok:
                continue
            nm, a, k = calls[0]
            fn = TK_DESC[nm]
            args = list(a[1:])           # drop the app
            if nm == "build_dialog":
                args = args[:4]
            texts = {}
            for L in ("en", "ja"):
                if L == "en" and lang != "en":
                    continue
                texts[L] = fn(L, lang, *args, **k)
            out.append(dict(src="tk_ui", qid=qid, pat=pattern, row=row, wording=wording, en=texts.get("en"), ja=texts["ja"]))
    finally:
        for name, f in saved.items():
            setattr(GT, name, f)
    return out


# ============================================================================================ ja_specific describers
def j_receipt(shop, y, m, d, to, amount, proviso, tax=None, stamp=None, seal=True, show_to=True, show_date=True,
              show_amount=True, show_proviso=True, show_issuer=True, note=None, serif=False):
    p = ["「領 収 書」と題した領収書"]
    if show_date:
        p.append("右上に日付「%s」" % GJ.jdate(y, m, d))
    if show_to:
        p.append("宛名「%s」" % (to if to.endswith("様") else to + " 様"))
    if show_amount:
        p.append("金額欄に「¥{:,}-」{}".format(amount, "（金額の右下に小さく「%s」）" % note if note else ""))
    if stamp:
        p.append("右側に「収入印紙」と書かれた枠")
    if show_proviso:
        p.append("「但し %sとして」「上記正に領収いたしました」" % proviso)
    if tax:
        _, base, rate, tx = tax
        p.append("内訳として「税抜金額 {:,}円」「消費税等（{}%） {:,}円」".format(base, rate, tx))
    if show_issuer:
        p.append("下に発行者名「%s」%s" % (shop, "と赤い丸印" if seal else ""))
    return "。".join(p) + "。"


def j_invoice(to, y, m, d, rows, rate, due=None, show_sub=False, show_total=False, sub=None):
    p = ["「請 求 書」と題した請求書", "宛先「%s 御中」" % to, "発行日「%s」" % GJ.jdate(y, m, d),
         "表（品名・数量・単価・金額）: " + "、".join("%s %d {:,} {:,}".format(u, q * u) % (n, q) for n, q, u in rows)]
    s = sub if sub is not None else sum(q * u for _, q, u in rows)
    if show_sub:
        p.append("「小計（税抜） {:,}円」「消費税（{}%） {:,}円」".format(s, rate, s * rate // 100))
    if show_total:
        p.append("「合計（税込） {:,}円」".format(s + s * rate // 100))
    else:
        p.append("赤字の注記「※ 表の金額は税抜です。消費税は %d%% です。」" % rate)
    if due:
        p.append("「お支払期限 %s」" % GJ.jdate(*due))
    return "。".join(p) + "。"


def j_timetable(station, deps, now=None, title="平日・上り"):
    rows = []
    for t, k, dst in deps:
        shown = GJ.TT_ALT.get(dst, dst) if dst == station else dst
        rows.append("%d:%02d %s %s行き" % (t[0], t[1], k, shown))
    s = "「%s駅 時刻表」（%s）。発車の一覧（時刻 種別 行き先）: %s" % (station, title, "、".join(rows))
    if now:
        s += "。下に「ただいまの時刻  %d:%02d」" % now
    return s + "。"


def j_hourly(station, rows, dirn="上り"):
    return "「%s駅 %s」（平日）の時刻表。時と分の一覧: %s。" % (station, dirn, "、".join("%d時台 %s" % (h, " ".join("%02d" % m for m in ms)) for h, ms in rows))


def j_route(line, stations, transfer=(), start_label=True):
    p = []
    for i, s in enumerate(stations):
        t = s
        marks = []
        if start_label and i == 0:
            marks.append("始発")
        if start_label and i == len(stations) - 1:
            marks.append("終点")
        if i in transfer:
            marks.append("乗換")
        p.append("%s%s" % (t, "（%s）" % "・".join(marks) if marks else ""))
    return "「%s」の路線図。駅が左から右へ順に %d 個並ぶ（駅名は縦書き）: %s。" % (line, len(stations), "、".join(p))


def j_hours(shop, hours, lo=None, closed="水曜日", rest=None, always=False):
    p = ["「%s」の営業案内の看板" % shop, "「営業時間  %s〜%s」" % hours]
    if lo:
        p.append("「ラストオーダー  %s」" % lo)
    if rest:
        p.append("「中休み  %s〜%s」" % rest)
    p.append("「年中無休」" if always else "「定休日  %s」" % closed)
    return "。".join(p) + "。"


def j_board(rows, title, bg=None, head=None):
    return "「%s」という見出しの掲示板。本文（上から順）: %s。" % (title, "、".join("「%s」" % s.replace("　", " ") for s, c in rows))


def j_status(title, big, sub=None, panel=None, fg=None):
    return "「%s」と書かれた表示板。大きな文字で「%s」%s。" % (title, big, "、その下に「%s」" % sub if sub else "")


def j_gauge(title, frac, left, right, ticks=None, color=None):
    s = "「%s」の横棒ゲージ。バーの左端の下に「%s」、右端の下に「%s」と書かれている。バーは全体の約 %d%% まで色が付いている" % (title, left, right, round(frac * 100))
    if ticks:
        s += "。目盛りは " + "・".join("%d" % t for t in ticks)
    return s + "。"


def j_menu(title, items, cols=1, tax_note=None, serif=False):
    s = "「%s」というメニュー表。品名と価格: %s" % (title, "、".join("%s %s" % (n, GJ.yen(p)) for n, p in items))
    if tax_note:
        s += "。下に「%s」" % tax_note
    return s + "。"


def j_form(title, name, checks=None, birth=None, now=None, seal=None, sex=None, agree=None, kana=None):
    p = ["「%s」という用紙" % title, "氏名欄に「%s」" % name]
    if seal is not None:
        p.append("右側の押印欄に%s" % ("赤い印が押されている" if seal else "「印」と薄い文字があるだけで、押されていない"))
    if birth:
        era, yy, mm, dd = birth
        p.append("生年月日欄は「昭和・平成・令和」のうち「%s」に赤い丸が付き、「%d 年  %d 月  %d 日」" % (era, yy, mm, dd))
    if now:
        p.append("「記入日　%s」" % GJ.jdate(*now))
    if sex:
        p.append("性別欄の「男・女・回答しない」のうち「%s」に赤い丸が付いている" % sex)
    if checks:
        p.append("チェック欄（赤いレ点があれば有）: " + "、".join("%s（%s）" % (lb, "有" if on else "無") for lb, on in checks))
    if agree is not None:
        p.append("下に「上記に同意します」の四角欄（%s）" % ("レ点あり" if agree else "レ点なし"))
    return "。".join(p) + "。"


def j_vertical(cols, title_sz=42, sz=38, bg=None, edge=None, serif=True, first_bigger=True):
    return "縦書きの文書。右の列から左の列へ順に読む。各列の文字: %s。" % "、".join("%d 列目「%s」" % (i + 1, c) for i, c in enumerate(cols))


def j_month(y, m, hol=None, closed=(), mark=None):
    e, n = GJ.era_of(y)
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(y, m)
    rows = ["（%s）" % "、".join(" " if not d else "%d" % d for d in wk) for wk in weeks]
    s = "「%s%d年 %d月」のカレンダー。曜日の列は左から日・月・火・水・木・金・土。週ごとの日付（上から順、空欄は空白）: %s" % (e, n, m, "".join(rows))
    notes = []
    if hol:
        notes.append("日付が赤字で右下に「祝」の印がある日: %s" % "・".join("%d" % d for d in sorted(hol)))
    if closed:
        notes.append("右下に「休」の印がある日: %s" % "・".join("%d" % d for d in closed))
    if mark:
        notes.append("緑の丸が付いた日: %s" % "・".join("%d" % d for d in mark))
    if notes:
        s += "。" + "。".join(notes)
    return s + "。"


def j_forecast(y, m, d0, days, title="週間天気"):
    p = []
    for i, (w, hi, lo, pr) in enumerate(days):
        dt = datetime.date(y, m, d0) + datetime.timedelta(days=i)
        p.append("%d/%d（%s）%s 最高%d 最低%d 降水確率%d%%" % (dt.month, dt.day, GJ.WDAY[dt.weekday()], w, hi, lo, pr))
    return "「%s」の天気予報。日ごとの欄（日付（曜日）・天気・最高気温・最低気温・降水確率）: %s。" % (title, "、".join(p))


JA_DRAW = {"draw_receipt": j_receipt, "draw_invoice": j_invoice, "draw_timetable": j_timetable, "draw_hourly": j_hourly,
           "draw_route": j_route, "draw_hours": j_hours, "draw_board": j_board, "draw_status": j_status, "draw_gauge": j_gauge,
           "draw_menu": j_menu, "draw_form": j_form, "draw_vertical": j_vertical, "draw_month": j_month, "draw_forecast": j_forecast}

# the builders chosen for ja_specific (a builder not listed, or whose spec no longer equals the row, is not used)
JA_PICK = ["a03", "a04", "a05", "a09", "a10", "a12", "b02", "b06", "b11", "c16", "c17", "c19", "c23", "d04", "d10", "e01", "e04",
           "f02", "g05", "w02", "b07"]


def collect_ja(rows):
    calls = []
    saved = {}
    for name in JA_DRAW:
        saved[name] = getattr(GJ, name)

        def mk(nm):
            def rec(*a, **k):
                calls.append((nm, a, k))
                return None
            return rec
        setattr(GJ, name, mk(name))
    out = []
    try:
        for i, (name, pattern, itype, fn) in enumerate(GJ.BUILDERS):
            qid = "biz-%04d" % (GJ.FIRST_ID + i)
            row = rows.get(qid)
            calls.clear()
            _, spec = fn(GJ.rng_of(name))
            if name not in JA_PICK or row is None or row["review"]["state"] == "dropped" or len(calls) != 1:
                continue
            ok, wording = same_spec(None, spec["ja"], spec["kind"], spec.get("answer"), row)
            if not ok:
                continue
            nm, a, k = calls[0]
            out.append(dict(src="ja_specific", qid=qid, pat=pattern, name=name, row=row, wording=wording, en=None, ja=JA_DRAW[nm](*a, **k)))
    finally:
        for name, f in saved.items():
            setattr(GJ, name, f)
    return out


# ============================================================================================ selection and rows
def spread(cands, q):
    """q items spread evenly over cands (deterministic)."""
    if q >= len(cands):
        return list(cands)
    return [cands[int((j + 0.5) * len(cands) / q)] for j in range(q)]


BAD_INSTR = ("What does the error message say?", "What error code is shown in the dialog?",
             "エラーメッセージの内容はどれですか？", "ダイアログに表示されているエラーコードはどれですか？")


def fits(c):
    if (c["row"].get("en") or c["row"]["ja"]).get("instr") in BAD_INSTR:      # pure reading of one string: the state would just be the answer
        return False
    for key, frame in (("en", EN_FRAME), ("ja", JA_FRAME)):
        if c[key] is not None and len(frame + c[key]) > MAX_STATE:
            return False
    return True


def make_row(c, n):
    row = c["row"]
    out = {"id": "txt-%04d" % n, "legacy_id": None, "origin": "new", "derived_from": c["qid"], "relation": "control", "group": "txt",
           "source": "none", "image_type": "none", "skill": "text-comprehension", "difficulty": row["difficulty"], "lang": row["lang"],
           "langs": list(row["langs"]), "modality": "text", "kind": row["kind"], "answer_format": row["answer_format"],
           "tags": ["control", "no-picture", "from-" + c["src"], c["pat"]], "local_images": []}
    for L, frame in (("en", EN_FRAME), ("ja", JA_FRAME)):
        if L not in row["langs"]:
            continue
        side = {"instr": row[L]["instr"]}
        for k in ("correct", "wrong", "levels"):
            if k in row[L]:
                side[k] = list(row[L][k]) if isinstance(row[L][k], list) else row[L][k]
        side["state"] = frame + c[L]
        out[L] = side
    if "answer" in row:
        out["answer"] = row["answer"]
    out["review"] = {"state": "unreviewed", "history": []}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write datasets/questions/v1/new_txt_controls.jsonl (the only file this script writes)")
    ap.add_argument("--show", action="store_true", help="print every state")
    a = ap.parse_args()
    ren = load("rendered")
    tkr = load("tk_ui")
    jar = load("ja_specific")
    cands = []
    ren_c = [c for c in collect_rendered(ren) if fits(c)]
    tk_c = [c for c in collect_tk(tkr) if fits(c)]
    ja_c = [c for c in collect_ja(jar) if fits(c)]
    for src, pool, quota in (("rendered", ren_c, RENDERED_QUOTA), ("tk_ui", tk_c, TK_QUOTA)):
        by = collections.defaultdict(list)
        for c in pool:
            by[c["pat"]].append(c)
        for pat, q in quota.items():
            pool_p = sorted(by.get(pat, []), key=lambda c: c["qid"])
            if pool_p and pool_p[0]["row"]["kind"] == "noul":       # yes/no: alternate true / false
                t = [c for c in pool_p if c["row"]["answer"]]
                f = [c for c in pool_p if not c["row"]["answer"]]
                cands += spread(t, (q + 1) // 2) + spread(f, q // 2)
            else:
                cands += spread(pool_p, q)
    cands += sorted(ja_c, key=lambda c: c["qid"])
    rows = [make_row(c, FIRST_ID + i) for i, c in enumerate(cands)]
    print("usable: rendered %d, tk_ui %d, ja_specific %d -> controls %d" % (len(ren_c), len(tk_c), len(ja_c), len(rows)))
    print("by source:", dict(collections.Counter(c["src"] for c in cands)))
    print("by kind:", dict(collections.Counter(r["answer_format"].split(":")[0] if r["kind"] != "noul" else "yesno" for r in rows)))
    print("wording differs from generator:", [c["qid"] for c in cands if c["wording"]])
    if a.show:
        for r, c in zip(rows, cands):
            print(r["id"], c["qid"], c["pat"], r["answer_format"])
            for L in ("en", "ja"):
                if L in r:
                    print("  ", L, r[L]["instr"], "|", r[L].get("correct", r.get("answer")))
                    print("     ", r[L]["state"])
    if a.write:
        assert OUT.name == "new_txt_controls.jsonl" and OUT.parent == V1DIR
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("written", OUT, len(rows))
    else:
        print("dry run (use --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
