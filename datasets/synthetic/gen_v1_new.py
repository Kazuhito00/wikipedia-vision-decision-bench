# -*- coding: utf-8 -*-
"""New v1 questions, tag ``rendered``: pictures drawn with PIL, answers DERIVED from the drawing parameters.

    python datasets/synthetic/gen_v1_new.py [--out work/generated] [--jsonl datasets/questions/v1/new_rendered.jsonl] [--dry]

Writes work/generated/<id>.png (640x480), work/generated/px224/<id>.png (what the models receive) and new_rendered.jsonl
(ids biz-1001..  / rsn-1001..  inside the range reserved for the tag). Deterministic: every random choice is seeded from the pattern name and the
variant number; the layout is fixed (only the font may differ by machine: Arial if present). Text in the pictures is Latin letters and digits, so one
picture serves English and Japanese. Every spec (values, positions, colours, counts) is drawn first and the right answer is computed FROM THE
SPEC (argmax, set difference, bin of a value, ...), never typed in.

Kinds covered: many options (6..16), 2 and 3 options, score scales (3 / 7 / 10 levels), negation, "None of the above" /
"Cannot be determined" right answers, position, counting, caption-vs-picture contradiction, uncertainty (hidden information).
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import random
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from gen import COLORS as BASE_COLORS, font  # noqa: E402
from datasets import options  # noqa: E402

W, H = 640, 480
INK = (25, 25, 25)
GREY = (205, 205, 205)
OUT_DIR = ROOT / "work" / "generated"
JSONL = ROOT / "datasets" / "questions" / "v1" / "new_rendered.jsonl"
TAG = "rendered"

COLORS = dict(BASE_COLORS, pink=(240, 120, 175), brown=(125, 75, 35), cyan=(30, 190, 210))
COLOR_JA = {"red": "赤", "blue": "青", "green": "緑", "yellow": "黄色", "orange": "オレンジ", "purple": "紫", "grey": "灰色", "black": "黒",
            "pink": "ピンク", "brown": "茶色", "cyan": "水色"}
CNAMES = ["red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "cyan", "grey", "black"]
SHAPES = ["circle", "square", "triangle", "star", "diamond", "hexagon", "pentagon", "cross"]
SHAPE_JA = {"circle": "円", "square": "四角", "triangle": "三角", "star": "星", "diamond": "ひし形", "hexagon": "六角形",
            "pentagon": "五角形", "cross": "十字"}
BGS = [(255, 255, 255), (250, 250, 244), (244, 248, 253), (253, 247, 243), (246, 250, 246)]
NONE_EN, NONE_JA = "None of the above", "該当なし"
CBD_EN, CBD_JA = "Cannot be determined", "判断できない"
LET = "ABCDEFGHIJKLMNOP"


def R(*key) -> random.Random:
    # the seed spelling "v2new:" is FROZEN (the dataset was called v2 when the pictures were drawn; renaming it would redraw them)
    return random.Random("v2new:" + ":".join(str(k) for k in key))


def canvas(r: random.Random | None = None, bg=None):
    bg = bg or (r.choice(BGS) if r else BGS[0])
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def T(d, xy, s, size=30, fill=INK, bold=True, anchor="mm"):
    d.text(xy, str(s), font=font(size, bold), fill=fill, anchor=anchor)


# ================================================================================================ shapes
def shape_points(kind, cx, cy, r):
    if kind == "triangle":
        return [(cx, cy - r), (cx - r, cy + r * 0.8), (cx + r, cy + r * 0.8)]
    if kind == "diamond":
        return [(cx, cy - r), (cx + r * 0.8, cy), (cx, cy + r), (cx - r * 0.8, cy)]
    if kind == "star":
        return [(cx + (r if k % 2 == 0 else r * 0.45) * math.sin(math.pi * k / 5), cy - (r if k % 2 == 0 else r * 0.45) * math.cos(math.pi * k / 5))
                for k in range(10)]
    if kind == "hexagon":
        return [(cx + r * math.cos(math.pi / 3 * k), cy + r * math.sin(math.pi / 3 * k)) for k in range(6)]
    if kind == "pentagon":
        return [(cx + r * math.sin(2 * math.pi * k / 5), cy - r * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    if kind == "cross":
        a, b = r, r * 0.38
        return [(cx - b, cy - a), (cx + b, cy - a), (cx + b, cy - b), (cx + a, cy - b), (cx + a, cy + b), (cx + b, cy + b), (cx + b, cy + a),
                (cx - b, cy + a), (cx - b, cy + b), (cx - a, cy + b), (cx - a, cy - b), (cx - b, cy - b)]
    raise ValueError(kind)


def shape(d, kind, cx, cy, r, fill, outline=INK, w=3):
    if kind == "circle":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=outline, width=w)
    elif kind == "square":
        d.rectangle((cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9), fill=fill, outline=outline, width=w)
    else:
        pts = shape_points(kind, cx, cy, r)
        d.polygon(pts, fill=fill)
        d.line(pts + [pts[0]], fill=outline, width=w, joint="curve")


def scatter(r, n, rad, box=(30, 30, 610, 450), mind=None, avoid=()):
    pts = []
    mind = mind or 2 * rad + 10
    tries = 0
    while len(pts) < n:
        tries += 1
        assert tries < 50000, "scatter failed"
        x, y = r.uniform(box[0] + rad, box[2] - rad), r.uniform(box[1] + rad, box[3] - rad)
        if all((x - px) ** 2 + (y - py) ** 2 >= mind ** 2 for px, py in list(pts) + list(avoid)):
            pts.append((x, y))
    return pts


# ================================================================================================ row helpers
def cn(c):                     # colour: (en, ja)
    return c, COLOR_JA[c]


def choice(en_q, ja_q, correct, wrong, *, special=None):
    """correct / wrong are (en, ja) pairs; special = list of canonical special options appended last (en, ja pairs)."""
    wr = list(wrong) + list(special or [])
    return dict(kind="choice",
                en=dict(instr=en_q, correct=correct[0], wrong=[w[0] for w in wr]),
                ja=dict(instr=ja_q, correct=correct[1], wrong=[w[1] for w in wr]))


def yesno(en_q, ja_q, answer):
    return dict(kind="noul", en=dict(instr=en_q), ja=dict(instr=ja_q), answer=bool(answer))


def lab(c):
    return (c, c)


NONE = (NONE_EN, NONE_JA)
CBD = (CBD_EN, CBD_JA)


# ================================================================================================ 1. many options
def p_bar_tallest(qid, i, n, mode):
    r = R("bar_tallest", i)
    while True:
        vals = r.sample(range(12, 96), n)
        s = sorted(vals)
        if (mode == "max" and s[-1] - s[-2] >= 10) or (mode == "min" and s[1] - s[0] >= 8):
            break
    im, d = canvas(r)
    left, right, base, top = 30, 610, 400, 70
    d.line((left, base, right, base), fill=INK, width=3)
    for g in (25, 50, 75, 100):
        y = base - (base - top) * g / 100
        d.line((left, y, right, y), fill=(225, 225, 225), width=1)
    slot = (right - left) / n
    col = r.choice([(70, 110, 205), (40, 150, 110), (210, 110, 40), (130, 70, 170)])
    for k, v in enumerate(vals):
        x0, x1 = left + slot * k + slot * 0.15, left + slot * (k + 1) - slot * 0.15
        d.rectangle((x0, base - (base - top) * v / 100, x1, base), fill=col)
        T(d, ((x0 + x1) / 2, base + 28), LET[k], 34 if n <= 10 else 28)
    idx = vals.index(max(vals) if mode == "max" else min(vals))
    q = ("Which bar is the tallest?", "いちばん高い棒はどれですか？") if mode == "max" else ("Which bar is the shortest?", "いちばん低い棒はどれですか？")
    return im, dict(image_type="chart", skill="compare", difficulty="easy" if n <= 8 else "medium", tags=["synthetic", "chart", "bar", "many-options"],
                    **choice(q[0], q[1], lab(LET[idx]), [lab(LET[k]) for k in range(n) if k != idx]))


def p_color_circle(qid, i, n, with_none=False, none_answer=False):
    """One circle among squares / triangles / diamonds; 'What colour is the circle?'. none_answer: the circle's colour is NOT in the options."""
    r = R("color_circle", i)
    colours = r.sample(CNAMES, n)
    x = colours[0]
    others = [c for c in CNAMES if c != x]
    slots = [(110, 150), (320, 125), (530, 150), (215, 345), (430, 345)]
    r.shuffle(slots)
    kinds = ["square", "triangle", "diamond", "square"]
    r.shuffle(kinds)
    im, d = canvas(r)
    opt_pool = [c for c in colours if c != x] if not none_answer else r.sample(others, n - 1)
    for k in range(4):
        cx, cy = slots[k + 1][0] + r.randint(-15, 15), slots[k + 1][1] + r.randint(-12, 12)
        shape(d, kinds[k], cx, cy, 58, COLORS[opt_pool[k]])
    cx, cy = slots[0][0] + r.randint(-15, 15), slots[0][1] + r.randint(-12, 12)
    shape(d, "circle", cx, cy, 58, COLORS[x])
    q = ("What colour is the circle?", "円は何色ですか？")
    if none_answer:
        wrong = [cn(c) for c in opt_pool]
        assert x not in [w[0] for w in wrong]
        return im, dict(image_type="figure", skill="recognition", difficulty="medium", tags=["synthetic", "colour", "none-of-the-above"],
                        **choice(q[0], q[1], NONE, wrong))
    wrong = [cn(c) for c in colours if c != x]
    return im, dict(image_type="figure", skill="recognition", difficulty="easy" if n <= 7 else "medium",
                    tags=["synthetic", "colour", "many-options"],
                    **choice(q[0], q[1], cn(x), wrong, special=[NONE] if with_none else None))


def station_layout(n):
    return [(320 + 170 * math.sin(2 * math.pi * k / n), 245 - 170 * math.cos(2 * math.pi * k / n)) for k in range(n)]


def p_station(qid, i, n, highlighted=True, with_none=False):
    r = R("station", i)
    im, d = canvas(r)
    pts = station_layout(n)
    d.line(pts + [pts[0]], fill=(150, 150, 150), width=8)
    hi = r.randrange(n) if highlighted else None
    rad = 34 if n <= 10 else 30
    for k, (x, y) in enumerate(pts):
        on = (k == hi)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(215, 40, 40) if on else (255, 255, 255), outline=INK, width=4)
        T(d, (x, y), k + 1, 34 if n <= 10 else 30, fill=(255, 255, 255) if on else INK)
    T(d, (320, 245), "LOOP LINE", 30, fill=(110, 110, 110))
    q = ("Which station is highlighted in red?", "赤く強調されている駅はどれですか？")
    nums = [lab(str(k + 1)) for k in range(n)]
    if highlighted:
        return im, dict(image_type="diagram-map", skill="recognition", difficulty="easy" if n <= 8 else "medium",
                        tags=["synthetic", "map", "station", "many-options"],
                        **choice(q[0], q[1], nums[hi], [x for k, x in enumerate(nums) if k != hi], special=[NONE] if with_none else None))
    return im, dict(image_type="diagram-map", skill="recognition", difficulty="medium", tags=["synthetic", "map", "station", "none-of-the-above"],
                    **choice(q[0], q[1], NONE, nums))


def grid_dims(n):
    return {6: (2, 3), 8: (2, 4), 9: (3, 3), 12: (3, 4), 16: (4, 4)}[n]


def p_grid_cell(qid, i, n, present=True, sub=None):
    """Grid of lettered cells with blue / green circles and squares; one red target shape (star / triangle / cross / hexagon) in one cell, or none.
    sub = number of lettered options (None-answer variants list only some cells)."""
    r = R("grid_cell", i)
    rows, cols = grid_dims(n)
    cw, ch = 600 / cols, 440 / rows
    tk = r.choice(["star", "triangle", "cross", "hexagon"])
    tpos = r.randrange(n) if present else None
    im, d = canvas(r)
    for k in range(n):
        rr, cc = divmod(k, cols)
        x0, y0 = 20 + cc * cw, 20 + rr * ch
        d.rectangle((x0, y0, x0 + cw, y0 + ch), outline=(120, 120, 120), width=2)
        cx, cy = x0 + cw / 2 + 8, y0 + ch / 2 + 8
        rad = min(cw, ch) * 0.28
        if k == tpos:
            shape(d, tk, cx, cy, rad * 1.1, COLORS["red"])
        else:
            shape(d, r.choice(["circle", "square"]), cx, cy, rad, COLORS[r.choice(["blue", "green", "grey", "orange"])])
        T(d, (x0 + 24, y0 + 22), LET[k], 34, fill=(30, 50, 140))
    en_s, ja_s = tk, SHAPE_JA[tk]
    q = ("Which cell contains the %s?" % en_s, "%sが入っているマスはどれですか？" % ja_s)
    if present:
        opts = [lab(LET[k]) for k in range(n)]
        return im, dict(image_type="diagram-map", skill="spatial", difficulty="easy" if n <= 9 else "medium",
                        tags=["synthetic", "grid", "many-options"],
                        **choice(q[0], q[1], opts[tpos], [x for k, x in enumerate(opts) if k != tpos]))
    ks = sorted(r.sample(range(n), sub))
    return im, dict(image_type="diagram-map", skill="spatial", difficulty="medium", tags=["synthetic", "grid", "none-of-the-above"],
                    **choice(q[0], q[1], NONE, [lab(LET[k]) for k in ks]))


PIE_COLS = [(70, 110, 205), (230, 130, 40), (60, 170, 90), (200, 70, 70), (140, 90, 190), (150, 110, 70), (230, 150, 190), (110, 190, 210),
            (200, 190, 50), (120, 120, 120)]


def p_pie(qid, i, n):
    r = R("pie", i)
    while True:
        w = [r.uniform(1, 3) for _ in range(n)]
        s = sum(w)
        v = [100 * x / s for x in w]
        sv = sorted(v)
        if sv[0] >= 5 and sv[-1] >= 1.3 * sv[-2]:
            break
    im, d = canvas(r)
    cx, cy, rad = 320, 255, 160
    a = -90.0
    for k, x in enumerate(v):
        a2 = a + 360 * x / 100
        d.pieslice((cx - rad, cy - rad, cx + rad, cy + rad), a, a2, fill=PIE_COLS[k], outline=(255, 255, 255), width=3)
        m = math.radians((a + a2) / 2)
        T(d, (cx + (rad + 36) * math.cos(m), cy + (rad + 36) * math.sin(m)), LET[k], 34)
        a = a2
    idx = v.index(max(v))
    return im, dict(image_type="chart", skill="compare", difficulty="easy" if n <= 7 else "medium", tags=["synthetic", "pie", "many-options"],
                    **choice("Which slice of the pie is the largest?", "円グラフでいちばん大きい区画はどれですか？", lab(LET[idx]),
                             [lab(LET[k]) for k in range(n) if k != idx]))


def p_colour_most(qid, i, n):
    """Circles of n colours, one colour clearly the most frequent."""
    r = R("colour_most", i)
    cols = r.sample(CNAMES, n)
    while True:
        cnt = [r.randint(1, 4) for _ in range(n)]
        cnt[0] = r.randint(6, 8)
        if sorted(cnt)[-1] - sorted(cnt)[-2] >= 2:
            break
    items = [c for c, k in zip(cols, cnt) for _ in range(k)]
    r.shuffle(items)
    im, d = canvas(r)
    pts = scatter(r, len(items), 22, box=(25, 25, 615, 455), mind=58)
    for c, (x, y) in zip(items, pts):
        shape(d, "circle", x, y, 22, COLORS[c])
    best = collections.Counter(items).most_common(1)[0][0]
    return im, dict(image_type="figure", skill="count", difficulty="medium" if n <= 7 else "hard", tags=["synthetic", "count", "colour", "many-options"],
                    **choice("Which colour appears most often?", "いちばん多く出てくる色はどれですか？", cn(best), [cn(c) for c in cols if c != best]))


# ================================================================================================ 2. two / three options
def p_two_bars(qid, i, mode):
    r = R("two_bars", i)
    while True:
        a, b = r.randint(25, 95), r.randint(25, 95)
        if abs(a - b) >= 22:
            break
    im, d = canvas(r)
    d.line((60, 400, 580, 400), fill=INK, width=3)
    for k, (v, x) in enumerate(((a, 190), (b, 450))):
        d.rectangle((x - 60, 400 - 3.2 * v, x + 60, 400), fill=[(70, 110, 205), (230, 130, 40)][k])
        T(d, (x, 438), "AB"[k], 40)
    idx = 0 if (a > b) == (mode == "tall") else 1
    q = ("Which bar is taller?", "高いのはどちらの棒ですか？") if mode == "tall" else ("Which bar is shorter?", "低いのはどちらの棒ですか？")
    return im, dict(image_type="chart", skill="compare", difficulty="easy", tags=["synthetic", "chart", "two-options"],
                    **choice(q[0], q[1], lab("AB"[idx]), [lab("AB"[1 - idx])]))


def p_side(qid, i):
    r = R("side", i)
    left = r.random() < 0.5
    x = r.uniform(70, 230) if left else r.uniform(410, 570)
    y = r.uniform(110, 370)
    im, d = canvas(r)
    pts = scatter(r, 3, 40, box=(20, 20, 620, 460), mind=100, avoid=[(x, y)])
    for (px, py) in pts:
        shape(d, "square", px, py, 38, COLORS["blue"])
    shape(d, "circle", x, y, 44, COLORS["red"])
    return im, dict(image_type="figure", skill="spatial", difficulty="easy", tags=["synthetic", "position", "two-options"],
                    **choice("Is the red circle on the left or the right side of the picture?", "赤い円は画像の左側と右側のどちらにありますか？",
                             ("left", "左") if x < 320 else ("right", "右"), [("right", "右")] if x < 320 else [("left", "左")]))


def p_front(qid, i):
    r = R("front", i)
    c1, c2 = r.sample(["red", "blue", "green", "yellow", "purple", "orange"], 2)
    kind = r.choice(["square", "circle"])
    im, d = canvas(r)
    ox = r.choice([-1, 1]) * 55
    oy = r.choice([-1, 1]) * 35
    shape(d, kind, 320 - ox / 2, 240 - oy / 2, 105, COLORS[c1], w=5)
    shape(d, kind, 320 + ox / 2, 240 + oy / 2, 105, COLORS[c2], w=5)       # the second one is drawn last = in front
    en_q = "Which shape is in front, the %s one or the %s one?" % (c1, c2)
    ja_q = "手前にあるのは、%sの図形と%sの図形のどちらですか？" % (COLOR_JA[c1], COLOR_JA[c2])
    return im, dict(image_type="figure", skill="spatial", difficulty="medium", tags=["synthetic", "position", "depth", "two-options"],
                    **choice(en_q, ja_q, cn(c2), [cn(c1)]))


def p_arrow(qid, i):
    r = R("arrow", i)
    left = r.random() < 0.5
    im, d = canvas(r)
    cy = r.randint(200, 280)
    pts = [(120, cy - 40), (360, cy - 40), (360, cy - 100), (540, cy), (360, cy + 100), (360, cy + 40), (120, cy + 40)]
    if left:
        pts = [(640 - x, y) for x, y in pts]
    d.polygon(pts, fill=COLORS["blue"], outline=INK)
    return im, dict(image_type="figure", skill="spatial", difficulty="easy", tags=["synthetic", "arrow", "two-options"],
                    **choice("Which way does the arrow point?", "矢印はどちらを向いていますか？", ("left", "左") if left else ("right", "右"),
                             [("right", "右")] if left else [("left", "左")]))


def p_larger2(qid, i):
    r = R("larger2", i)
    while True:
        ra, rb = r.randint(45, 110), r.randint(45, 110)
        if abs(ra - rb) >= 22:
            break
    im, d = canvas(r)
    for (x, rr, l) in ((170, ra, "A"), (470, rb, "B")):
        shape(d, "circle", x, 225, rr, COLORS["green"] if l == "A" else COLORS["purple"])
        T(d, (x, 420), l, 44)
    idx = 0 if ra > rb else 1
    return im, dict(image_type="figure", skill="compare", difficulty="easy", tags=["synthetic", "size", "two-options"],
                    **choice("Which circle is larger?", "大きいのはどちらの円ですか？", lab("AB"[idx]), [lab("AB"[1 - idx])]))


def p_circles3(qid, i, mode):
    r = R("circles3", i)
    while True:
        rs = r.sample(range(30, 100), 3)
        s = sorted(rs)
        if (mode == "max" and s[2] - s[1] >= 14) or (mode == "min" and s[1] - s[0] >= 14):
            break
    im, d = canvas(r)
    for k, (x, rr) in enumerate(zip((120, 320, 520), rs)):
        shape(d, "circle", x, 215, rr, [COLORS["blue"], COLORS["orange"], COLORS["green"]][k])
        T(d, (x, 420), LET[k], 44)
    idx = rs.index(max(rs) if mode == "max" else min(rs))
    q = ("Which circle is the largest?", "いちばん大きい円はどれですか？") if mode == "max" else ("Which circle is the smallest?", "いちばん小さい円はどれですか？")
    return im, dict(image_type="figure", skill="compare", difficulty="easy", tags=["synthetic", "size", "three-options"],
                    **choice(q[0], q[1], lab(LET[idx]), [lab(LET[k]) for k in range(3) if k != idx]))


def p_slots3(qid, i):
    r = R("slots3", i)
    k = r.randrange(3)
    im, d = canvas(r)
    for s, x in enumerate((130, 320, 510)):
        shape(d, "square", x, 240, 62, COLORS["red"] if s == k else COLORS["grey"])
    names = [("left", "左"), ("middle", "真ん中"), ("right", "右")]
    return im, dict(image_type="figure", skill="spatial", difficulty="easy", tags=["synthetic", "position", "three-options"],
                    **choice("Where is the red square: left, middle or right?", "赤い四角はどこにありますか？", names[k], [n for j, n in enumerate(names) if j != k]))


def p_traffic(qid, i):
    r = R("traffic", i)
    k, horizontal = [(0, False), (1, True), (2, False), (0, True)][i]
    im, d = canvas(r)
    lit = [(235, 40, 40), (245, 205, 30), (50, 180, 80)]
    dark = [(95, 60, 60), (95, 90, 55), (55, 90, 65)]
    if horizontal:
        d.rounded_rectangle((40, 150, 600, 330), radius=24, fill=(60, 60, 60), outline=INK, width=4)
        for s in range(3):
            d.ellipse((85 + s * 175, 180, 175 + s * 175, 300), fill=lit[s] if s == k else dark[s], outline=(20, 20, 20), width=3)
    else:
        d.rounded_rectangle((250, 30, 390, 450), radius=24, fill=(60, 60, 60), outline=INK, width=4)
        for s in range(3):
            d.ellipse((275, 55 + s * 130, 365, 145 + s * 130), fill=lit[s] if s == k else dark[s], outline=(20, 20, 20), width=3)
    names = [("red", "赤"), ("yellow", "黄"), ("green", "緑")]
    return im, dict(image_type="figure", skill="recognition", difficulty="easy", tags=["synthetic", "traffic-light", "three-options"],
                    **choice("Which light of the traffic signal is on?", "信号のどの色が点灯していますか？", names[k], [n for j, n in enumerate(names) if j != k]))


# ================================================================================================ 3. score scales
def level_ranges(n, w, unit):
    en = ["%d-%d %s" % (j * w, (j + 1) * w, unit) for j in range(n)]
    ja = ["%d〜%d %s" % (j * w, (j + 1) * w, unit) for j in range(n)]
    return en, ja


def pct_ranges(n):
    e = [round(100 * j / n) for j in range(n + 1)]
    return ["%d-%d%%" % (e[j], e[j + 1]) for j in range(n)], ["%d〜%d%%" % (e[j], e[j + 1]) for j in range(n)]


def value_in_level(r, level, n, width):
    """A value in the middle 60% of the level's bin, so that it is never near a boundary."""
    v = (level + 0.5) * width + r.uniform(-0.3, 0.3) * width
    assert int(v // width) == level
    return v


def score_row(img_type, skill, diff, tags, en_q, ja_q, en_lv, ja_lv, level):
    return dict(image_type=img_type, skill=skill, difficulty=diff, tags=["synthetic", "level"] + tags, kind="score",
                en=dict(instr=en_q, levels=en_lv), ja=dict(instr=ja_q, levels=ja_lv), answer=level)


DIFF = {3: "easy", 7: "medium", 10: "hard"}
HB = {"Download speed": "ダウンロード速度", "Water temperature": "水温", "Speed": "速度"}


def p_hbar(qid, i, n, level):
    r = R("hbar", i)
    w = 10
    mx = n * w
    v = value_in_level(r, level, n, w)
    im, d = canvas(r)
    T(d, (320, 70), "Download speed", 40)
    x0, x1, y0, y1 = 60, 580, 170, 235
    d.rectangle((x0, y0, x1, y1), fill=(230, 230, 230), outline=INK, width=3)
    d.rectangle((x0, y0, x0 + (x1 - x0) * v / mx, y1), fill=(70, 110, 205))
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        d.line((x, y1, x, y1 + 14), fill=INK, width=3)
        T(d, (x, y1 + 34), k * w, 22 if n == 10 else 26, bold=False)
    T(d, (320, 330), "Mbps", 34, fill=(90, 90, 90))
    en, ja = level_ranges(n, w, "Mbps")
    return im, score_row("ui", "quantity", DIFF[n], ["gauge", "bar"], "Which range does the value shown by the bar fall in?",
                         "バーが示している値はどの範囲に入りますか？", en, ja, level)


def p_thermo(qid, i, n, level):
    r = R("thermo", i)
    w = 10
    mx = n * w
    v = value_in_level(r, level, n, w)
    im, d = canvas(r)
    ytop, ybot = 60, 380
    d.rounded_rectangle((300, ytop - 12, 340, ybot + 10), radius=20, fill=(235, 235, 235), outline=INK, width=4)
    d.ellipse((275, 380, 365, 470), fill=(215, 40, 40), outline=INK, width=4)
    y = ybot - (ybot - ytop) * v / mx
    d.rectangle((308, y, 332, ybot + 30), fill=(215, 40, 40))
    d.ellipse((283, 388, 357, 462), fill=(215, 40, 40))
    for k in range(n + 1):
        yy = ybot - (ybot - ytop) * k / n
        d.line((344, yy, 366, yy), fill=INK, width=3)
        T(d, (372, yy), k * w, 24, anchor="lm", bold=False)
    T(d, (150, 120), "Water", 40)
    T(d, (150, 170), "temperature", 34)
    T(d, (150, 230), "(°C)", 38, fill=(90, 90, 90))
    en, ja = level_ranges(n, w, "°C")
    return im, score_row("chart", "quantity", DIFF[n], ["thermometer"], "Which range does the temperature on the thermometer fall in?",
                         "温度計が示している温度はどの範囲に入りますか？", en, ja, level)


def p_dial(qid, i, n, level):
    r = R("dial", i)
    w = 10
    mx = n * w
    v = value_in_level(r, level, n, w)
    im, d = canvas(r)
    cx, cy, rad = 320, 380, 220
    T(d, (320, 38), "Speed", 40)
    d.arc((cx - rad, cy - rad, cx + rad, cy + rad), 180, 360, fill=INK, width=8)
    for k in range(n + 1):
        th = math.pi * (1 - k / n)
        c, s = math.cos(th), math.sin(th)
        d.line((cx + (rad - 24) * c, cy - (rad - 24) * s, cx + rad * c, cy - rad * s), fill=INK, width=5)
        T(d, (cx + (rad + 28) * c, cy - (rad + 28) * s), k * w, 22 if n == 10 else 26, bold=False)
    th = math.pi * (1 - v / mx)
    d.line((cx, cy, cx + 190 * math.cos(th), cy - 190 * math.sin(th)), fill=(200, 30, 30), width=9)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=INK)
    T(d, (cx, 440), "km/h", 34, fill=(90, 90, 90))
    en, ja = level_ranges(n, w, "km/h")
    return im, score_row("chart", "quantity", DIFF[n], ["gauge", "dial"], "Which range does the speed shown by the needle fall in?",
                         "針が示している速度はどの範囲に入りますか？", en, ja, level)


def p_donut(qid, i, n, level):
    r = R("donut", i)
    pct = value_in_level(r, level, n, 100 / n)
    im, d = canvas(r)
    cx, cy, rad, th = 320, 250, 165, 52
    d.arc((cx - rad, cy - rad, cx + rad, cy + rad), 0, 360, fill=(222, 222, 222), width=th)
    d.arc((cx - rad, cy - rad, cx + rad, cy + rad), -90, -90 + 360 * pct / 100, fill=(70, 110, 205), width=th)
    for k in range(n):
        a = math.radians(-90 + 360 * k / n)
        d.line((cx + (rad - th) * math.cos(a), cy + (rad - th) * math.sin(a), cx + (rad + 4) * math.cos(a), cy + (rad + 4) * math.sin(a)),
               fill=INK, width=4)
        T(d, (cx + (rad + 32) * math.cos(a), cy + (rad + 32) * math.sin(a)), round(100 * k / n), 22, bold=False)
    T(d, (cx, cy - 15), "Upload", 36)
    T(d, (cx, cy + 25), "progress", 30, fill=(90, 90, 90))
    en, ja = pct_ranges(n)
    return im, score_row("chart", "quantity", DIFF[n], ["gauge", "donut"], "Which range does the progress ring show?",
                         "進捗リングが示している進み具合はどの範囲ですか？", en, ja, level)


def p_battery(qid, i, level):
    r = R("battery", i)
    n = 3
    pct = value_in_level(r, level, n, 100 / n)
    im, d = canvas(r)
    T(d, (320, 80), "Battery", 44)
    x0, x1, y0, y1 = 70, 540, 170, 330
    d.rectangle((x0, y0, x1, y1), fill=(235, 235, 235), outline=INK, width=6)
    d.rectangle((x1, 220, x1 + 28, 280), fill=INK)
    d.rectangle((x0 + 3, y0 + 3, x0 + 3 + (x1 - x0 - 6) * pct / 100, y1 - 3), fill=(60, 170, 90))
    for k in (1, 2):
        x = x0 + (x1 - x0) * k / 3
        d.line((x, y0 - 12, x, y1 + 12), fill=INK, width=4)
    for k in range(4):
        T(d, (x0 + (x1 - x0) * k / 3, y1 + 40), "%d%%" % round(100 * k / 3), 26, bold=False)
    en, ja = pct_ranges(3)
    return im, score_row("ui", "quantity", "easy", ["gauge", "battery"], "Which range is the battery charge in?", "バッテリー残量はどの範囲ですか？", en, ja, level)


def p_stars(qid, i, level):
    r = R("stars", i)
    bins = [(0, 1), (2, 3), (4, 5)]
    k = r.randint(*bins[level])
    im, d = canvas(r)
    T(d, (320, 90), ["Customer rating", "Hotel rating", "Movie rating", "Service rating"][i % 4], 44)
    for s in range(5):
        shape(d, "star", 92 + s * 114, 250, 52, COLORS["yellow"] if s < k else (232, 232, 232), outline=(120, 100, 20) if s < k else (150, 150, 150))
    en = ["0-1 stars", "2-3 stars", "4-5 stars"]
    ja = ["星 0〜1 個", "星 2〜3 個", "星 4〜5 個"]
    return im, score_row("ui", "count", "easy", ["rating", "stars"], "How many of the stars are filled in?", "色のついた星はいくつありますか？", en, ja,
                         [j for j, (a, b) in enumerate(bins) if a <= k <= b][0])


def p_signal(qid, i, level):
    k = level + 1
    r = R("signal", i)
    im, d = canvas(r)
    T(d, (320, 70), "Signal strength", 42)
    for s in range(7):
        h = 40 + s * 40
        x = 90 + s * 70
        d.rectangle((x, 420 - h, x + 48, 420), fill=(40, 60, 110) if s < k else (225, 225, 225), outline=INK, width=3)
    en = ["%d bar%s" % (j, "" if j == 1 else "s") for j in range(1, 8)]
    ja = ["%d 本" % j for j in range(1, 8)]
    return im, score_row("ui", "count", "medium", ["signal", "level"], "How many signal bars are lit?", "点灯している電波バーは何本ですか？", en, ja, level)


def p_volume(qid, i, level):
    k = level + 1
    r = R("volume", i)
    im, d = canvas(r)
    T(d, (320, 70), "Volume", 44)
    for s in range(10):
        x = 40 + s * 56
        d.rectangle((x, 160, x + 44, 380), fill=(230, 130, 40) if s < k else (228, 228, 228), outline=INK, width=3)
    en = ["%d block%s" % (j, "" if j == 1 else "s") for j in range(1, 11)]
    ja = ["%d 個" % j for j in range(1, 11)]
    return im, score_row("ui", "count", "medium", ["volume", "level"], "How many volume blocks are lit?", "点灯している音量ブロックは何個ですか？", en, ja, level)


# ================================================================================================ 4. negation
def p_absent_colour(qid, i, n):
    r = R("absent_colour", i)
    k = n - 1
    shown = r.sample(CNAMES, k)
    absent = r.choice([c for c in CNAMES if c not in shown])
    im, d = canvas(r)
    per = 4 if k > 4 else k
    rows = [shown[j:j + per] for j in range(0, k, per)]
    for ri, row in enumerate(rows):
        for ci, c in enumerate(row):
            shape(d, "circle", 320 + (ci - (len(row) - 1) / 2) * 135, 240 + (ri - (len(rows) - 1) / 2) * 150, 54, COLORS[c])
    return im, dict(image_type="figure", skill="negation", difficulty="easy" if n <= 6 else "medium", tags=["synthetic", "colour", "negation", "many-options"],
                    **choice("Which of the listed colours does NOT appear in the picture?", "次の色のうち、画像に出てこない色はどれですか？", cn(absent),
                             [cn(c) for c in shown]))


def p_absent_shape(qid, i, n):
    r = R("absent_shape", i)
    k = n - 1
    kinds = r.sample(SHAPES, n)
    absent, shown = kinds[0], kinds[1:]
    im, d = canvas(r)
    per = 4 if k > 4 else k
    rows = [shown[j:j + per] for j in range(0, k, per)]
    cols = r.sample([c for c in CNAMES if c not in ("yellow",)], k)
    idx = 0
    for ri, row in enumerate(rows):
        for ci, kd in enumerate(row):
            shape(d, kd, 320 + (ci - (len(row) - 1) / 2) * 135, 240 + (ri - (len(rows) - 1) / 2) * 150, 54, COLORS[cols[idx]])
            idx += 1
    return im, dict(image_type="figure", skill="negation", difficulty="easy" if n <= 6 else "medium", tags=["synthetic", "shape", "negation", "many-options"],
                    **choice("Which of the listed shapes does NOT appear in the picture?", "次の形のうち、画像に出てこない形はどれですか？",
                             (absent, SHAPE_JA[absent]), [(s, SHAPE_JA[s]) for s in shown]))


def bars_draw(d, vals, r, labels=True, base=400, top=80, left=60, right=580, col=(70, 110, 205), show_values=False):
    n = len(vals)
    slot = (right - left) / n
    d.line((left - 10, base, right + 10, base), fill=INK, width=3)
    mx = 100
    boxes = []
    for k, v in enumerate(vals):
        x0, x1 = left + slot * k + slot * 0.2, left + slot * (k + 1) - slot * 0.2
        y = base - (base - top) * v / mx
        d.rectangle((x0, y, x1, base), fill=col)
        boxes.append((x0, x1, y))
        if labels:
            T(d, ((x0 + x1) / 2, base + 30), LET[k], 34)
        if show_values:
            T(d, ((x0 + x1) / 2, y - 20), v, 30)
    return boxes


def p_no_taller_first(qid, i, truth):
    r = R("no_taller_first", i)
    n = 5
    while True:
        vals = r.sample(range(15, 95), n)
        mx = max(vals)
        srt = sorted(vals)
        first_max = vals[0] == mx
        if srt[-1] - srt[-2] >= 10 and first_max == truth:
            break
    im, d = canvas(r)
    bars_draw(d, vals, r)
    return im, yesno_row("chart", "negation", "medium", ["synthetic", "chart", "negation", "yes-no"], "No bar is taller than bar A",
                         "棒 A より高い棒はない", all(v <= vals[0] for v in vals))


def yesno_row(it, skill, diff, tags, en, ja, ans):
    return dict(image_type=it, skill=skill, difficulty=diff, tags=tags, **yesno(en, ja, ans))


def p_no_red_circle(qid, i, truth):
    r = R("no_red_circle", i)
    cols = [c for c in CNAMES if c not in ("red", "orange", "pink", "brown")]
    items = [r.choice(cols) for _ in range(6)]
    if not truth:
        items[r.randrange(6)] = "red"
    im, d = canvas(r)
    for c, (x, y) in zip(items, scatter(r, 6, 44, box=(25, 25, 615, 455), mind=105)):
        shape(d, "circle", x, y, 44, COLORS[c])
    return im, yesno_row("figure", "negation", "easy", ["synthetic", "colour", "negation", "yes-no"], "None of the circles is red", "赤い円はひとつもない",
                         "red" not in items)


def p_no_triangle(qid, i, truth):
    r = R("no_triangle", i)
    kinds = [r.choice(["circle", "square", "star", "diamond", "hexagon"]) for _ in range(6)]
    if not truth:
        kinds[r.randrange(6)] = "triangle"
    im, d = canvas(r)
    for kd, (x, y) in zip(kinds, scatter(r, 6, 46, box=(25, 25, 615, 455), mind=110)):
        shape(d, kd, x, y, 46, COLORS[r.choice(["blue", "green", "orange", "purple", "grey"])])
    return im, yesno_row("figure", "negation", "easy", ["synthetic", "shape", "negation", "yes-no"], "There is no triangle in the picture",
                         "画像に三角形はない", "triangle" not in kinds)


def p_not_circle(qid, i, n):
    r = R("not_circle", i)
    odd = r.randrange(n)
    oddkind = r.choice(["square", "diamond", "hexagon", "triangle"])
    cols = [r.choice(["blue", "green", "orange", "purple", "cyan"]) for _ in range(n)]
    per = (n + 1) // 2
    im, d = canvas(r)
    for k in range(n):
        rr, cc = divmod(k, per)
        cnt = per if rr == 0 else n - per
        x = 320 + (cc - (cnt - 1) / 2) * 140
        y = 150 + rr * 200
        shape(d, oddkind if k == odd else "circle", x, y, 48, COLORS[cols[k]])
        T(d, (x, y + 76), LET[k], 34)
    return im, dict(image_type="figure", skill="negation", difficulty="easy" if n <= 6 else "medium", tags=["synthetic", "shape", "negation", "many-options"],
                    **choice("Which shape is NOT a circle?", "円ではない図形はどれですか？", lab(LET[odd]), [lab(LET[k]) for k in range(n) if k != odd]))


# ================================================================================================ 5. none of the above
def p_labeled_bars(qid, i, n, target_present):
    r = R("labeled_bars", i)
    pool = list(range(10, 100, 5))
    target = r.choice([30, 40, 50, 60, 70, 80])
    vals = r.sample([v for v in pool if v != target], n)
    if target_present:
        vals[r.randrange(n)] = target
    im, d = canvas(r)
    bars_draw(d, vals, r, show_values=True, col=(60, 150, 110))
    q = ("Which bar has the value %d?" % target, "値が %d の棒はどれですか？" % target)
    if target_present:
        k = vals.index(target)
        return im, dict(image_type="chart", skill="ocr", difficulty="easy", tags=["synthetic", "chart", "read", "many-options"],
                        **choice(q[0], q[1], lab(LET[k]), [lab(LET[j]) for j in range(n) if j != k], special=[NONE]))
    assert target not in vals
    return im, dict(image_type="chart", skill="ocr", difficulty="medium", tags=["synthetic", "chart", "read", "none-of-the-above"],
                    **choice(q[0], q[1], NONE, [lab(LET[j]) for j in range(n)]))


PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}


def p_dice(qid, i, n):
    r = R("dice", i)
    vals = [r.randint(1, 5) for _ in range(n)]
    per = 4 if n > 5 else 3
    rows = [list(range(j, min(j + per, n))) for j in range(0, n, per)]
    im, d = canvas(r)
    for ri, row in enumerate(rows):
        for ci, k in enumerate(row):
            cx = 320 + (ci - (len(row) - 1) / 2) * 150
            cy = 140 + ri * 200
            d.rounded_rectangle((cx - 55, cy - 55, cx + 55, cy + 55), radius=14, fill=(255, 255, 255), outline=INK, width=4)
            for (dx, dy) in PIPS[vals[k]]:
                d.ellipse((cx + dx * 28 - 11, cy + dy * 28 - 11, cx + dx * 28 + 11, cy + dy * 28 + 11), fill=INK)
            T(d, (cx, cy + 82), LET[k], 32)
    assert 6 not in vals
    return im, dict(image_type="figure", skill="recognition", difficulty="medium", tags=["synthetic", "dice", "none-of-the-above"],
                    **choice("Which die shows six dots?", "6 の目が出ているサイコロはどれですか？", NONE, [lab(LET[k]) for k in range(n)]))


# ================================================================================================ 6. position / count / contradiction / uncertainty
def p_row_neighbour(qid, i, n, side):
    r = R("row_neighbour", i)
    cols = r.sample(CNAMES, 5)
    idx = r.randrange(0, 4) if side == "right" else r.randrange(1, 5)
    ref = cols[idx]
    ans = cols[idx + 1] if side == "right" else cols[idx - 1]
    im, d = canvas(r)
    for k, c in enumerate(cols):
        shape(d, "circle", 80 + k * 120, 240, 50, COLORS[c])
    others = [c for c in cols if c not in (ref, ans)]
    absent = [c for c in CNAMES if c not in cols]
    wrong = others + r.sample(absent, n - 4)
    sd = ("right", "右") if side == "right" else ("left", "左")
    en_q = "What colour is the circle directly to the %s of the %s circle?" % (sd[0], ref)
    ja_q = "%sの円の%s隣にある円は何色ですか？" % (COLOR_JA[ref], sd[1])
    return im, dict(image_type="figure", skill="spatial", difficulty="easy" if n == 4 else "medium", tags=["synthetic", "position", "row"],
                    **choice(en_q, ja_q, cn(ans), [cn(c) for c in wrong]))


COMBOS = [(s, c) for s in ("circle", "square", "triangle") for c in ("red", "blue", "green")]
REL = {"above": ((-1, 0), "above", "の真上"), "below": ((1, 0), "below", "の真下"), "left": ((0, -1), "to the left of", "の左隣"),
       "right": ((0, 1), "to the right of", "の右隣")}


def combo(c):
    return ("%s %s" % (c[1], c[0]), "%sの%s" % (COLOR_JA[c[1]], SHAPE_JA[c[0]]))


def p_grid_rel(qid, i, rel):
    r = R("grid_rel", i)
    cells = COMBOS[:]
    r.shuffle(cells)
    dr, dc = REL[rel][0]
    while True:
        k = r.randrange(9)
        rr, cc = divmod(k, 3)
        if 0 <= rr + dr < 3 and 0 <= cc + dc < 3:
            break
    ref, ans = cells[k], cells[(rr + dr) * 3 + cc + dc]
    im, d = canvas(r)
    for j, (kd, c) in enumerate(cells):
        y0, x0 = divmod(j, 3)
        shape(d, kd, 150 + x0 * 170, 80 + y0 * 160, 55, COLORS[c])
    others = r.sample([c for c in cells if c not in (ref, ans)], 3)
    en_q = "What is directly %s the %s?" % (REL[rel][1], combo(ref)[0])
    ja_q = "%s%sにあるのはどれですか？" % (combo(ref)[1], REL[rel][2])
    return im, dict(image_type="figure", skill="spatial", difficulty="medium", tags=["synthetic", "position", "grid"],
                    **choice(en_q, ja_q, combo(ans), [combo(c) for c in others]))


def p_between(qid, i, n):
    r = R("between", i)
    cols = r.sample(CNAMES, 5)
    k = r.randrange(1, 4)
    a, m, b = cols[k - 1], cols[k], cols[k + 1]
    if r.random() < 0.5:
        a, b = b, a
    im, d = canvas(r)
    for j, c in enumerate(cols):
        shape(d, "circle", 80 + j * 120, 240, 50, COLORS[c])
    others = [c for c in cols if c not in (a, m, b)]
    absent = [c for c in CNAMES if c not in cols]
    wrong = others + r.sample(absent, n - 3) if n > 3 else others
    wrong = wrong[:n - 1]
    en_q = "Which circle is between the %s circle and the %s circle?" % (a, b)
    ja_q = "%sの円と%sの円の間にある円は何色ですか？" % (COLOR_JA[a], COLOR_JA[b])
    return im, dict(image_type="figure", skill="spatial", difficulty="medium", tags=["synthetic", "position", "between"],
                    **choice(en_q, ja_q, cn(m), [cn(c) for c in wrong]))


def p_count_red(qid, i, k, nopt):
    r = R("count_red", i)
    nblue = r.randint(3, 8)
    pts = scatter(r, k + nblue, 17, box=(25, 25, 615, 455), mind=44)
    r.shuffle(pts)
    im, d = canvas(r)
    for j, (x, y) in enumerate(pts):
        shape(d, "circle", x, y, 17, COLORS["red"] if j < k else COLORS["blue"], w=2)
    drawn_red = k
    cand = [c for c in range(max(0, k - 4), k + 5) if c != drawn_red]
    wrong = r.sample(cand, nopt - 1)
    return im, dict(image_type="figure", skill="count", difficulty="easy" if k <= 5 else "medium" if k <= 10 else "hard",
                    tags=["synthetic", "count", "colour"],
                    **choice("How many red circles are there?", "赤い円はいくつありますか？", lab(str(drawn_red)), [lab(str(c)) for c in sorted(wrong)]))


def p_caption_shapes(qid, i, truth):
    r = R("caption_shapes", i)
    a, b = r.randint(2, 5), r.randint(1, 4)
    pts = scatter(r, a + b, 30, box=(25, 25, 615, 385), mind=74)
    im, d = canvas(r)
    for j, (x, y) in enumerate(pts):
        shape(d, "circle" if j < a else "square", x, y, 28, COLORS["red"] if j < a else COLORS["blue"])
    ca, cb = a, b
    if not truth:
        if r.random() < 0.5:
            ca = a + r.choice([-1, 1])
        else:
            cb = b + r.choice([-1, 1])
        ca, cb = max(ca, 1), max(cb, 1)
        if (ca, cb) == (a, b):
            ca = a + 1
    d.rectangle((15, 405, 625, 470), fill=(60, 60, 70))
    T(d, (320, 438), '"%d red circle%s, %d blue square%s"' % (ca, "" if ca == 1 else "s", cb, "" if cb == 1 else "s"), 30, fill=(255, 255, 255))
    return im, yesno_row("figure", "contradiction", "medium", ["synthetic", "caption", "contradiction", "yes-no"],
                         "Does the caption at the bottom correctly describe the picture?", "下にあるキャプションは画像の内容と合っていますか？",
                         (ca, cb) == (a, b))


def p_caption_chart(qid, i, truth, form):
    r = R("caption_chart", i)
    n = 4
    while True:
        if form == "increasing":
            vals = sorted(r.sample(range(15, 95), n))
            if not truth:
                j = r.randrange(n - 1)
                vals[j], vals[j + 1] = vals[j + 1], vals[j]
            ok = all(vals[k + 1] - vals[k] >= 10 for k in range(n - 1)) if truth else True
            srt = sorted(vals)
            ok = ok and all(srt[k + 1] - srt[k] >= 10 for k in range(n - 1))
        else:
            vals = r.sample(range(15, 95), n)
            srt = sorted(vals)
            ok = srt[-1] - srt[-2] >= 10 and srt[1] - srt[0] >= 6
        if ok:
            break
    if form == "increasing":
        cap = "Each bar is taller than the one before"
        holds = all(vals[k + 1] > vals[k] for k in range(n - 1))
    else:
        cl = r.randrange(n) if truth else r.choice([k for k in range(n) if k != vals.index(max(vals))])
        if truth:
            cl = vals.index(max(vals))
        cap = "Bar %s is the tallest" % LET[cl]
        holds = vals.index(max(vals)) == cl
    im, d = canvas(r)
    bars_draw(d, vals, r, base=335, top=40, left=60, right=580, col=(210, 110, 40))
    d.rectangle((15, 405, 625, 470), fill=(60, 60, 70))
    T(d, (320, 438), '"%s"' % cap, 30, fill=(255, 255, 255))
    return im, yesno_row("chart", "contradiction", "medium", ["synthetic", "caption", "contradiction", "yes-no"],
                         "Does the caption at the bottom correctly describe the chart?", "下にあるキャプションはグラフの内容と合っていますか？", holds)


def p_hidden_bar(qid, i, hidden):
    r = R("hidden_bar", i)
    vals = r.sample(range(20, 90), 4)
    while abs(vals[2] - vals[3]) < 15:
        vals = r.sample(range(20, 90), 4)
    im, d = canvas(r)
    base, top, left, right = 400, 70, 60, 580
    boxes = bars_draw(d, vals, r, base=base, top=top, left=left, right=right)
    x0, x1, y = boxes[3]
    if hidden:
        d.rectangle((x0 - 10, top - 20, x1 + 10, base), fill=(150, 150, 150), outline=INK, width=3)
        T(d, ((x0 + x1) / 2, 240), "?", 70, fill=(255, 255, 255))
    else:
        cover_h = 0.4 * min(vals[2], vals[3]) * (base - top) / 100
        assert base - cover_h > y + 8
        d.rectangle((x0 - 10, base - cover_h, x1 + 10, base), fill=(150, 150, 150), outline=INK, width=3)
        T(d, ((x0 + x1) / 2, base - cover_h / 2), "?", 26, fill=(255, 255, 255))
    en_q, ja_q = "Is bar D taller than bar C?", "棒 D は棒 C より高いですか？"
    yes, no = ("Yes", "はい"), ("No", "いいえ")
    if hidden:
        return im, dict(image_type="chart", skill="uncertainty", difficulty="medium", tags=["synthetic", "chart", "uncertainty", "hidden"],
                        **choice(en_q, ja_q, CBD, [yes, no]))
    right_ans = yes if vals[3] > vals[2] else no
    return im, dict(image_type="chart", skill="uncertainty", difficulty="medium", tags=["synthetic", "chart", "uncertainty", "partly-hidden"],
                    **choice(en_q, ja_q, right_ans, [no if right_ans is yes else yes], special=[CBD]))


def p_card(qid, i):
    r = R("card", i)
    cols = r.sample(["red", "blue", "green", "yellow", "purple", "orange"], 3)
    im, d = canvas(r)
    for k in range(3):
        x0 = 60 + k * 190
        if k < 2:
            d.rounded_rectangle((x0, 120, x0 + 150, 360), radius=14, fill=COLORS[cols[k]], outline=INK, width=4)
        else:
            d.rounded_rectangle((x0, 120, x0 + 150, 360), radius=14, fill=(95, 95, 110), outline=INK, width=4)
            T(d, (x0 + 75, 240), "?", 90, fill=(255, 255, 255))
    return im, dict(image_type="figure", skill="uncertainty", difficulty="medium", tags=["synthetic", "cards", "uncertainty", "hidden"],
                    **choice("What colour is the face-down card (marked ?)?", "裏向きのカード（?）は何色ですか？", CBD, [cn(c) for c in cols]))


# ================================================================================================ plan
def build_plan():
    plan = []
    cnt = {"biz": 1000, "rsn": 1000}

    def add(group, fn, **kw):
        cnt[group] += 1
        plan.append(dict(group=group, id="%s-%04d" % (group, cnt[group]), fn=fn, kw=kw))

    # --- score scales first (biz-1001..1050): the right level is spread evenly per n afterwards
    for pat, ns in (("hbar", (3, 7, 10)), ("thermo", (3, 7, 10)), ("dial", (3, 7, 10))):
        for n in ns:
            for _ in range(3):
                add("biz", {"hbar": p_hbar, "thermo": p_thermo, "dial": p_dial}[pat], n=n, level=None, i=len(plan))
    for _ in range(4):
        add("biz", p_battery, level=None, i=len(plan), n=3)
    for _ in range(4):
        add("biz", p_stars, level=None, i=len(plan), n=3)
    for n, c in ((7, 4), (10, 3)):
        for _ in range(c):
            add("biz", p_donut, n=n, level=None, i=len(plan))
    for _ in range(4):
        add("biz", p_signal, level=None, i=len(plan), n=7)
    for _ in range(4):
        add("biz", p_volume, level=None, i=len(plan), n=10)
    # --- many options
    for k, (n, mode) in enumerate([(6, "max"), (6, "min"), (7, "max"), (7, "min"), (8, "max"), (8, "min"), (9, "max"), (10, "max"), (10, "min"), (12, "max")]):
        add("biz", p_bar_tallest, i=k, n=n, mode=mode)
    for k, n in enumerate((6, 7, 8, 9, 10, 11)):
        add("rsn", p_color_circle, i=k, n=n, with_none=(k in (1, 4)))
    for k, n in enumerate((6, 7, 8, 9, 10, 12)):
        add("rsn", p_station, i=k, n=n, with_none=(k in (2, 5)))
    for k, n in enumerate((6, 9, 12, 16, 16, 16)):
        add("rsn", p_grid_cell, i=k, n=n, present=True)
    for k, n in enumerate((6, 7, 8, 8, 9, 10, 10, 6)):
        add("biz", p_pie, i=k, n=n)
    for k, n in enumerate((6, 7, 8, 9, 6, 8)):
        add("rsn", p_colour_most, i=k, n=n)
    # --- two / three options
    for k, m in enumerate(("tall", "short", "tall", "short", "tall")):
        add("biz", p_two_bars, i=k, mode=m)
    for k in range(4):
        add("rsn", p_side, i=k)
    for k in range(5):
        add("rsn", p_front, i=k)
    for k in range(3):
        add("rsn", p_arrow, i=k)
    for k in range(3):
        add("rsn", p_larger2, i=k)
    for k, m in enumerate(("max", "min", "max", "min")):
        add("rsn", p_circles3, i=k, mode=m)
    for k in range(4):
        add("rsn", p_slots3, i=k)
    for k in range(4):
        add("rsn", p_traffic, i=k)
    # --- negation
    for k, n in enumerate((4, 5, 6, 7, 8, 9, 5)):
        add("rsn", p_absent_colour, i=k, n=n)
    for k, n in enumerate((5, 6, 7, 8, 5, 6, 7)):
        add("rsn", p_absent_shape, i=k, n=n)
    for k, t in enumerate((True, False, True, False)):
        add("biz", p_no_taller_first, i=k, truth=t)
    for k, t in enumerate((True, False, False, True)):
        add("rsn", p_no_red_circle, i=k, truth=t)
    for k, t in enumerate((False, True, True, False)):
        add("rsn", p_no_triangle, i=k, truth=t)
    for k, n in enumerate((5, 6, 7, 8)):
        add("rsn", p_not_circle, i=k, n=n)
    # --- none of the above
    for k, n in enumerate((6, 7, 8, 9)):
        add("rsn", p_color_circle, i=10 + k, n=n, none_answer=True)
    for k, (n, sub) in enumerate(((6, 5), (9, 6), (12, 7), (16, 8))):
        add("rsn", p_grid_cell, i=10 + k, n=n, present=False, sub=sub)
    for k, n in enumerate((6, 8, 10, 12)):
        add("rsn", p_station, i=10 + k, n=n, highlighted=False)
    for k, (n, pr) in enumerate(((5, False), (6, False), (7, False), (8, False), (6, False), (7, False), (5, True), (6, True))):
        add("biz", p_labeled_bars, i=k, n=n, target_present=pr)
    for k, n in enumerate((5, 6, 6, 7, 8)):
        add("rsn", p_dice, i=k, n=n)
    # --- position / count / contradiction / uncertainty
    for k, (n, s) in enumerate(((4, "right"), (4, "left"), (5, "right"), (5, "left"), (6, "right"), (6, "left"))):
        add("rsn", p_row_neighbour, i=k, n=n, side=s)
    for k, rel in enumerate(("above", "below", "left", "right", "above")):
        add("rsn", p_grid_rel, i=k, rel=rel)
    for k, n in enumerate((4, 5, 4, 5, 6)):
        add("rsn", p_between, i=k, n=n)
    for k, (c, no) in enumerate(((0, 5), (1, 5), (2, 5), (3, 6), (5, 5), (6, 5), (8, 6), (9, 5), (10, 6), (12, 5), (15, 6), (20, 5))):
        add("rsn", p_count_red, i=k, k=c, nopt=no)
    for k, t in enumerate((True, False, False, True)):
        add("rsn", p_caption_shapes, i=k, truth=t)
    for k, (t, f) in enumerate(((True, "increasing"), (False, "increasing"), (True, "tallest"), (False, "tallest"))):
        add("biz", p_caption_chart, i=k, truth=t, form=f)
    for k, h in enumerate((True, True, True, True, False, False, False)):
        add("biz", p_hidden_bar, i=k, hidden=h)
    for k in range(4):
        add("rsn", p_card, i=k)
    return plan


def assign_levels(plan):
    by_n = collections.defaultdict(list)
    for e in plan:
        if "level" in e["kw"]:
            by_n[e["kw"]["n"]].append(e)
    for n, es in by_n.items():
        want = options.suggest_score_answers([e["id"] for e in es], n)
        for e in es:
            e["kw"]["level"] = want[e["id"]]
    for e in plan:
        e["kw"].pop("n", None) if e["fn"] in (p_battery, p_stars, p_signal, p_volume) else None


def make_row(qid, group, spec):
    row = {"id": qid, "origin": "new", "derived_from": None, "group": group, "source": "rendered",
           "image_type": spec["image_type"], "skill": spec["skill"], "difficulty": spec["difficulty"], "lang": "both", "langs": ["en", "ja"],
           "modality": "image", "kind": spec["kind"], "tags": spec["tags"], "local_images": ["generated/%s.png" % qid],
           "en": spec["en"], "ja": spec["ja"]}
    n = None
    if spec["kind"] == "choice":
        row["answer_format"] = "choice:%d" % (1 + len(spec["en"]["wrong"]))
    elif spec["kind"] == "noul":
        row["answer_format"] = "yesno"
        row["answer"] = spec["answer"]
    else:
        row["answer_format"] = "score:%d" % len(spec["en"]["levels"])
        row["answer"] = spec["answer"]
    row["review"] = {"state": "unreviewed", "history": []}
    return row


def thumb224(im):
    t = im.copy()
    t.thumbnail((224, 224), Image.LANCZOS)
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--jsonl", default=str(JSONL))
    ap.add_argument("--dry", action="store_true", help="build everything in memory, write nothing")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    plan = build_plan()
    assign_levels(plan)
    rows = []
    for e in plan:
        im, spec = e["fn"](e["id"], **e["kw"])
        assert im.size == (W, H)
        rows.append(make_row(e["id"], e["group"], spec))
        if not a.dry:
            out.mkdir(parents=True, exist_ok=True)
            (out / "px224").mkdir(parents=True, exist_ok=True)
            im.save(out / ("%s.png" % e["id"]), optimize=True)
            thumb224(im).save(out / "px224" / ("%s.png" % e["id"]), optimize=True)
    rows.sort(key=lambda r: r["id"])
    if not a.dry:
        pathlib.Path(a.jsonl).parent.mkdir(parents=True, exist_ok=True)
        with open(a.jsonl, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("%d rows (%s)" % (len(rows), collections.Counter(r["group"] for r in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
