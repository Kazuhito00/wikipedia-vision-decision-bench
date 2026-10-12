# -*- coding: utf-8 -*-
"""Reasoning set (data set 4): pictures drawn by this script, questions that need an operation on what is seen, answers exact by
construction.

    python datasets/synthetic/gen_reasoning.py   # writes work/legacy_regen/reasoning/*.png and work/legacy_regen/reasoning.jsonl
(the frozen legacy rows are datasets/questions/legacy/reasoning.jsonl; this script never overwrites them)

Why: the first three sets are mostly "what is in the picture" (classify / read a word), which saturates (about 80 % of the questions
are answered correctly by every model). Two independent reviews (Opus, Codex) agreed that what is missing is the step after
perception: combine conditions, calculate, follow a rule, transform in space, reason about time and cause, handle negation and
exceptions, check a statement against a figure, compare, say "cannot be determined". Each category below has several operation
types (not just changed numbers), and the difficulty comes from the number of steps, not from small print.

Rules for the pictures: everything that matters is drawn large (the models see 224 px: text >= 36 px in the 640x480 canvas),
at most about eight elements, numbers printed (no estimating from pixels), and no ambiguity in what "left / larger / touching" mean.
Rows have the schema of the legacy synthetic rows (set "reasoning").
Deterministic: every random choice is seeded from the item.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gen import COLORS, NAMES_JA, font, rng_for  # noqa: E402

ROOT = HERE.parents[1]
OUT_DIR = ROOT / "work" / "legacy_regen" / "reasoning"
JSONL = ROOT / "work" / "legacy_regen" / "reasoning.jsonl"
W, H = 640, 480
BG = (250, 250, 246)
INK = (25, 25, 25)

ITEMS: list = []


def canvas(bg=BG):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def txt(d, xy, s, size=40, fill=INK, bold=False, anchor="la"):
    d.text(xy, str(s), font=font(size, bold), fill=fill, anchor=anchor)


def save(img, qid, suffix=""):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    name = "%s%s.png" % (qid, suffix)
    img.save(OUT_DIR / name, optimize=True)
    return name


def add(cat, tags, imgs, kind, en, ja, answer=None, diff="medium", state_en="", state_ja=""):
    imgs = imgs if isinstance(imgs, list) else [imgs]
    qid = "rsn-%04d" % (len(ITEMS) + 1)
    names = [save(im, qid, "" if len(imgs) == 1 else "_%d" % (i + 1)) for i, im in enumerate(imgs)]
    row = {"id": qid, "modality": "image", "kind": kind, "tags": ["synthetic", "reasoning", "r-" + cat] + tags, "difficulty": diff,
           "images": names, "langs": ["en", "ja"], "used_by": ["en", "ja"], "articles": {}, "source": "synthetic",
           "en": dict(en), "ja": dict(ja), "local_images": ["data/reasoning/" + n for n in names]}
    if state_en:
        row["en"]["state"], row["ja"]["state"] = state_en, state_ja
    if kind in ("noul", "score"):
        row["answer"] = answer
    ITEMS.append(row)


def choice(cat, tags, img, q_en, q_ja, right, wrong, right_ja=None, wrong_ja=None, **kw):
    add(cat, tags, img, "choice", {"instr": q_en, "correct": right, "wrong": wrong},
        {"instr": q_ja, "correct": right_ja if right_ja is not None else right, "wrong": wrong_ja if wrong_ja is not None else wrong}, **kw)


def yesno(cat, tags, img, en, ja, answer, **kw):
    add(cat, tags, img, "noul", {"instr": en}, {"instr": ja}, answer, **kw)


def numopts(correct, extras, rng, k=3, lo=0):
    """k distinct wrong numbers: the plausible mistakes first (extras), then neighbours of the right answer."""
    out = []
    for x in list(extras) + [correct + d for d in (-10, 10, -2, 2, -5, 5, -1, 1, 20, -20, 3, -3)]:
        x = int(x)
        if x != correct and x >= lo and x not in out:
            out.append(x)
        if len(out) == k:
            break
    return [str(x) for x in out]


def bars(values, labels, colors=None, ymax=None, label_size=40, title=None):
    """Bar chart with the value printed above every bar and the label below."""
    im, d = canvas((255, 255, 255))
    n = len(values)
    top = 70 if title else 40
    base = 400
    ymax = ymax or max(values) * 1.15
    slot = 540 / n
    if title:
        txt(d, (W // 2, 28), title, 36, bold=True, anchor="mm")
    d.line((50, base, 610, base), fill=INK, width=3)
    for i, v in enumerate(values):
        x0 = 70 + slot * i + slot * 0.15
        x1 = 70 + slot * (i + 1) - slot * 0.15
        y = base - (base - top - 40) * v / ymax
        d.rectangle((x0, y, x1, base), fill=(colors[i] if colors else (70, 110, 205)))
        txt(d, ((x0 + x1) / 2, y - 22), v, 40, bold=True, anchor="mm")
        txt(d, ((x0 + x1) / 2, base + 34), labels[i], label_size, bold=True, anchor="mm")
    return im


def table(rows, header, col_w, size=38, hl=None):
    im, d = canvas((255, 255, 255))
    x0, y0, rh = 30, 40, 70
    xs = [x0]
    for w in col_w:
        xs.append(xs[-1] + w)
    d.rectangle((x0, y0, xs[-1], y0 + rh), fill=(225, 230, 245))
    for j, h in enumerate(header):
        txt(d, (xs[j] + 14, y0 + rh // 2), h, size - 4, bold=True, anchor="lm")
    for i, row in enumerate(rows):
        y = y0 + rh * (i + 1)
        d.line((x0, y, xs[-1], y), fill=(150, 150, 150), width=2)
        for j, c in enumerate(row):
            txt(d, (xs[j] + 14, y + rh // 2), c, size, anchor="lm")
    d.line((x0, y0 + rh * (len(rows) + 1), xs[-1], y0 + rh * (len(rows) + 1)), fill=(150, 150, 150), width=2)
    for x in xs:
        d.line((x, y0, x, y0 + rh * (len(rows) + 1)), fill=(150, 150, 150), width=2)
    return im


# =============================================================================================== 1. quantity / calculation
def cat_quantity():
    cat = "quantity"
    L = list("ABCDE")
    for i in range(6):                                                         # sum of two bars
        r = rng_for("q_sum%d" % i)
        vals = r.sample(range(8, 40), 5)
        a, b = r.sample(range(5), 2)
        c = vals[a] + vals[b]
        im = bars(vals, L)
        ex = [abs(vals[a] - vals[b]), sum(vals) - c, c + 10]
        choice(cat, ["sum", "chart"], im, "What is the sum of bars %s and %s?" % (L[a], L[b]), "棒 %s と棒 %s の合計はいくつですか？" % (L[a], L[b]),
               str(c), numopts(c, ex, r), diff="medium")
    for i in range(6):                                                         # tallest minus shortest
        r = rng_for("q_range%d" % i)
        vals = r.sample(range(6, 45), 5)
        c = max(vals) - min(vals)
        im = bars(vals, L)
        choice(cat, ["difference", "chart"], im, "By how much does the tallest bar exceed the shortest bar?", "いちばん高い棒は、いちばん低い棒より、いくつ大きいですか？",
               str(c), numopts(c, [max(vals), min(vals), sum(vals) - c], r), diff="medium")
    for i in range(6):                                                         # receipt: pay amount (no total printed)
        r = rng_for("q_receipt%d" % i)
        prices = r.sample([100, 150, 200, 250, 300, 350, 400, 500], 3)
        qty = [r.randrange(1, 4) for _ in range(3)]
        disc = r.choice([50, 100, 200])
        c = sum(p * q for p, q in zip(prices, qty)) - disc
        im, d = canvas((255, 255, 250))
        txt(d, (W // 2, 36), "RECEIPT", 40, bold=True, anchor="mm")
        for k, (p, q) in enumerate(zip(prices, qty)):
            txt(d, (40, 100 + k * 62), "Item %s  %d x %d" % ("ABC"[k], q, p), 38, anchor="lm")
        txt(d, (40, 100 + 3 * 62), "Discount  -%d" % disc, 38, anchor="lm")
        txt(d, (40, 100 + 4 * 62 + 10), "Pay: ?", 40, bold=True, anchor="lm")
        choice(cat, ["receipt", "arithmetic"], im, "How much must be paid after the discount (no tax)?", "値引き後の支払額はいくらですか（税なし）？",
               str(c), numopts(c, [c + disc, sum(prices) - disc, c + 100], r), diff="hard")
    for i in range(6):                                                         # table: cost of one row
        r = rng_for("q_cost%d" % i)
        names = r.sample(["Pen", "Book", "Cup", "Bag", "Lamp"], 3)
        qty = [r.randrange(2, 7) for _ in names]
        unit = [r.choice([10, 20, 30, 40, 50]) for _ in names]
        k = r.randrange(3)
        c = qty[k] * unit[k]
        im = table([[n, str(q), str(u)] for n, q, u in zip(names, qty, unit)], ["Item", "Qty", "Unit"], [220, 160, 220])
        choice(cat, ["table", "arithmetic"], im, "What is the total cost of the %s row (Qty x Unit)?" % names[k], "「%s」の行の合計金額（Qty × Unit）はいくらですか？" % names[k],
               str(c), numopts(c, [qty[k] + unit[k], unit[k], sum(q * u for q, u in zip(qty, unit))], r), diff="medium")


# =============================================================================================== 2. rule application
def cat_rules():
    cat = "rules"
    for i in range(8):                                                         # who may enter (2 conditions, each one tested)
        r = rng_for("r_enter%d" % i)
        # one adult WITHOUT a permit, one minor WITH a permit, one adult with a permit (the only one who may enter)
        people = [(r.choice([19, 21, 24, 30]), False), (r.choice([13, 15, 16, 17]), True), (r.choice([18, 20, 22, 27]), True)]
        order = [0, 1, 2]
        r.shuffle(order)
        people = [people[k] for k in order]
        ok = [a >= 18 and p for a, p in people]
        im = table([[n, str(a), "yes" if p else "no"] for n, (a, p) in zip("ABC", people)], ["Name", "Age", "Permit"], [200, 180, 220])
        right = "ABC"[ok.index(True)]
        if i % 2 == 0:
            choice(cat, ["conditions"], im, "Only people aged 18 or older who also have a permit may enter. Who may enter?", "18 歳以上で、かつ許可がある人だけ入れます。入れるのは誰ですか？",
                   right, [x for x in "ABC" if x != right], diff="hard")
        else:
            who = r.choice("ABC")
            yesno(cat, ["conditions"], im, "Only people aged 18 or older who also have a permit may enter. Person %s may enter" % who,
                  "18 歳以上で、かつ許可がある人だけ入れます。%s さんは入れる" % who, ok["ABC".index(who)], diff="hard")
    for i in range(6):                                                         # earliest train
        r = rng_for("r_train%d" % i)
        base = r.randrange(8, 16)
        times = sorted(r.sample(range(0, 60, 5), 4))
        deps = ["%d:%02d" % (base, t) for t in times]
        arrive = times[1] + r.choice([-3, 2, 3])
        arr = "%d:%02d" % (base, max(0, arrive) if arrive >= 0 else 0)
        right = next(d for d, t in zip(deps, times) if t >= arrive)
        im, d = canvas((255, 255, 255))
        txt(d, (W // 2, 40), "Departures", 40, bold=True, anchor="mm")
        for k, dep in enumerate(deps):
            txt(d, (W // 2, 105 + k * 55), dep, 42, anchor="mm")
        txt(d, (W // 2, 400), "You arrive at %s" % arr, 40, bold=True, fill=(160, 30, 30), anchor="mm")
        wrong = [x for x in deps if x != right]
        choice(cat, ["timetable"], im, "What is the earliest train you can catch?", "乗れる最も早い電車はどれですか？", right, wrong, diff="hard")
    for i in range(6):                                                         # fee by weight band
        r = rng_for("r_fee%d" % i)
        bands = [("0-1 kg", 100), ("1-3 kg", 200), ("3-6 kg", 350), ("6-10 kg", 500)]
        wgt = r.choice([0.6, 2.4, 2.8, 4.5, 5.2, 7.5, 8.8])
        right = next(p for (lbl, p), hi in zip(bands, (1, 3, 6, 10)) if wgt <= hi)
        im, d = canvas((255, 255, 255))
        for k, (lbl, p) in enumerate(bands):
            txt(d, (60, 50 + k * 62), lbl, 40, anchor="lm")
            txt(d, (340, 50 + k * 62), "%d yen" % p, 40, anchor="lm")
        d.rectangle((120, 330, 520, 440), outline=INK, width=4)
        txt(d, (320, 385), "Parcel: %s kg" % wgt, 44, bold=True, anchor="mm")
        wrong = [str(p) for _, p in bands if p != right]
        choice(cat, ["table", "lookup"], im, "What is the fee (yen) for the parcel?", "この荷物の料金（円）はいくらですか？", str(right), wrong, diff="medium")
    for i in range(6):                                                         # operation chain
        r = rng_for("r_ops%d" % i)
        start = r.randrange(2, 8)
        ops = [r.choice([("+3", lambda x: x + 3), ("+5", lambda x: x + 5), ("x2", lambda x: x * 2), ("-2", lambda x: x - 2)]) for _ in range(r.choice([2, 3]))]
        val = start
        for _, f in ops:
            val = f(val)
        im, d = canvas((255, 255, 255))
        txt(d, (60, 120), "Start: %d" % start, 46, bold=True, anchor="lm")
        x = 60
        for lbl, _ in ops:
            d.rounded_rectangle((x, 220, x + 130, 300), 14, outline=INK, width=4)
            txt(d, (x + 65, 260), lbl, 44, anchor="mm")
            if x + 200 < 600:
                txt(d, (x + 165, 260), "->", 40, anchor="mm")
            x += 190
        txt(d, (60, 400), "Apply the boxes from left to right.", 34, anchor="lm")
        choice(cat, ["operations", "sequence"], im, "What is the final value?", "最終的な値はいくつですか？", str(val), numopts(val, [start + 5, val + 2, val - 2], r), diff="hard")


# =============================================================================================== 3. space and routes
def cat_space():
    cat = "space"
    for i in range(8):                                                         # shortest path on a grid
        r = rng_for("s_path%d" % i)
        cols, rows = 6, 4
        start, goal = (0, r.randrange(rows)), (cols - 1, r.randrange(rows))
        cells = [(x, y) for x in range(1, cols - 1) for y in range(rows)]
        obst = set(r.sample(cells, r.randrange(3, 7)))
        dist = {start: 0}
        queue = [start]
        for cur in queue:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cur[0] + dx, cur[1] + dy
                if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in obst and (nx, ny) not in dist:
                    dist[(nx, ny)] = dist[cur] + 1
                    queue.append((nx, ny))
        if goal not in dist:
            continue
        right = dist[goal]
        direct = abs(goal[0] - start[0]) + abs(goal[1] - start[1])
        im, d = canvas((255, 255, 255))
        cw = 90
        ox, oy = 50, 60
        for x in range(cols):
            for y in range(rows):
                col = (60, 60, 60) if (x, y) in obst else (235, 240, 250)
                d.rectangle((ox + x * cw, oy + y * cw, ox + (x + 1) * cw - 3, oy + (y + 1) * cw - 3), fill=col)
        txt(d, (ox + start[0] * cw + 43, oy + start[1] * cw + 43), "S", 46, fill=(20, 120, 40), bold=True, anchor="mm")
        txt(d, (ox + goal[0] * cw + 43, oy + goal[1] * cw + 43), "G", 46, fill=(180, 30, 30), bold=True, anchor="mm")
        txt(d, (W // 2, 440), "Black cells are walls.", 32, anchor="mm")
        choice(cat, ["grid", "path"], im, "Moving one cell at a time (up, down, left, right), what is the fewest steps from S to G?",
               "上下左右に 1 マスずつ動くとき、S から G までの最少の歩数はいくつですか？", str(right), numopts(right, [direct, right + 2, right - 1], r, lo=1), diff="hard")
    DIRS = [("up", "上"), ("right", "右"), ("down", "下"), ("left", "左")]
    for i in range(6):                                                         # rotate an arrow card
        r = rng_for("s_rot%d" % i)
        k0 = r.randrange(4)
        turns = r.choice([1, 2, 3])
        k1 = (k0 + turns) % 4
        im, d = canvas((255, 255, 255))
        cx, cy = 320, 215
        v = [(0, -1), (1, 0), (0, 1), (-1, 0)][k0]
        px, py = -v[1], v[0]
        d.polygon([(cx + v[0] * 130, cy + v[1] * 130), (cx - v[0] * 20 + px * 70, cy - v[1] * 20 + py * 70), (cx - v[0] * 20 - px * 70, cy - v[1] * 20 - py * 70)], fill=COLORS["blue"])
        d.rectangle((60, 40, 580, 400), outline=INK, width=4)
        txt(d, (W // 2, 440), "Card", 34, anchor="mm")
        word = {1: "90 degrees clockwise", 2: "180 degrees", 3: "90 degrees counter-clockwise"}[turns]
        wja = {1: "時計回りに 90 度", 2: "180 度", 3: "反時計回りに 90 度"}[turns]
        choice(cat, ["rotation"], im, "The whole card is turned %s. Which way does the arrow point now?" % word, "カード全体を%s回すと、矢印はどちらを向きますか？" % wja,
               DIRS[k1][0], [x[0] for x in DIRS if x[0] != DIRS[k1][0]], DIRS[k1][1], [x[1] for x in DIRS if x[0] != DIRS[k1][0]], diff="hard")
    for i in range(6):                                                         # robot turn sequence
        r = rng_for("s_robot%d" % i)
        k0 = r.randrange(4)
        seq = [r.choice(["right", "left"]) for _ in range(r.choice([2, 3]))]
        k = k0
        for t in seq:
            k = (k + (1 if t == "right" else -1)) % 4
        im, d = canvas((255, 255, 255))
        cx, cy = 320, 190
        d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=(190, 190, 195), outline=INK, width=4)
        v = [(0, -1), (1, 0), (0, 1), (-1, 0)][k0]
        d.polygon([(cx + v[0] * 110, cy + v[1] * 110), (cx + v[1] * 30, cy - v[0] * 30), (cx - v[1] * 30, cy + v[0] * 30)], fill=COLORS["red"])
        txt(d, (W // 2, 360), "Turn: " + ", ".join(seq), 38, anchor="mm")
        txt(d, (W // 2, 420), "(red tip = front)", 30, anchor="mm")
        choice(cat, ["turns", "sequence"], im, "After the turns, which side of the picture does the front face?", "回転したあと、前方は画像のどちら側を向きますか？",
               DIRS[k][0], [x[0] for x in DIRS if x[0] != DIRS[k][0]], DIRS[k][1], [x[1] for x in DIRS if x[0] != DIRS[k][0]], diff="hard")


# =============================================================================================== 4. negation, exceptions, counterfactuals
def shapes_scene(rng, items, jitter=True):
    """items: list of (kind, colour). Returns the image; each shape is drawn big and apart."""
    im, d = canvas((255, 255, 255))
    n = len(items)
    cols = 4 if n > 4 else n
    rows = (n + cols - 1) // cols
    for i, (kind, colour) in enumerate(items):
        cx = 90 + (i % cols) * (460 / max(1, cols - 1) if cols > 1 else 0) + (0 if cols > 1 else 230)
        cy = 130 + (i // cols) * 170
        s = 55
        if kind == "circle":
            d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=COLORS[colour])
        elif kind == "square":
            d.rectangle((cx - s, cy - s, cx + s, cy + s), fill=COLORS[colour])
        else:
            d.polygon([(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)], fill=COLORS[colour])
    return im


def cat_negation():
    cat = "negation"
    for i in range(6):                                                         # all circles red?
        r = rng_for("n_all%d" % i)
        allred = i % 2 == 0
        items = [("circle", "red") for _ in range(r.randrange(2, 4))]
        if not allred:
            items.append(("circle", r.choice(["blue", "green"])))
        items += [("square", r.choice(["blue", "green", "yellow"])) for _ in range(r.randrange(1, 3))]
        r.shuffle(items)
        yesno(cat, ["universal"], shapes_scene(r, items), "Every circle in the picture is red", "画像の円はすべて赤い", allred, diff="medium")
    for i in range(5):                                                         # rule with an exception
        r = rng_for("n_exc%d" % i)
        im, d = canvas((255, 255, 255))
        cards = [("red", False), ("red", True), ("blue", False)]
        r.shuffle(cards)
        for k, (colr, star) in enumerate(cards):
            x = 70 + k * 190
            d.rounded_rectangle((x, 140, x + 160, 300), 16, fill=COLORS[colr])
            if star:
                txt(d, (x + 80, 220), "*", 110, fill=(255, 255, 255), bold=True, anchor="mm")
            txt(d, (x + 80, 345), "ABC"[k], 48, bold=True, anchor="mm")
        txt(d, (W // 2, 50), "Red cards are rejected,", 36, anchor="mm")
        txt(d, (W // 2, 95), "unless they have a star.", 36, anchor="mm")
        right = "ABC"[[c == ("red", False) for c in cards].index(True)]
        choice(cat, ["exception"], im, "Which card is rejected?", "却下されるカードはどれですか？", right, [x for x in "ABC" if x != right], diff="hard")
    for i in range(5):                                                         # counterfactual repaint
        r = rng_for("n_cf%d" % i)
        red, blue = r.randrange(2, 5), r.randrange(1, 4)
        k = r.randrange(1, red)
        items = [("circle", "red")] * red + [("circle", "blue")] * blue
        c = blue + k
        yes = False
        choice(cat, ["counterfactual"], shapes_scene(r, items), "If exactly %d of the red circles were repainted blue, how many blue circles would there be?" % k,
               "赤い円のうちちょうど %d 個を青く塗り替えたら、青い円はいくつになりますか？" % k, str(c), numopts(c, [blue, red, red + blue], r, lo=1), diff="hard")
    for i in range(4):                                                         # which colour has no ...
        r = rng_for("n_none%d" % i)
        cols = ["red", "blue", "green", "yellow"]
        missing = r.choice(cols)
        items = [("square", c) for c in cols if c != missing for _ in range(r.randrange(1, 3))]
        r.shuffle(items)
        choice(cat, ["absence"], shapes_scene(r, items[:8]), "Which of these colours has NO square in the picture?", "この画像に四角が 1 つもない色はどれですか？",
               missing, [c for c in cols if c != missing], NAMES_JA[missing], [NAMES_JA[c] for c in cols if c != missing], diff="medium")


# =============================================================================================== 5. time, procedure, cause
def clock(h, m):
    im, d = canvas((255, 255, 255))
    cx, cy, R = 320, 240, 190
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=INK, width=6, fill=(252, 252, 252))
    for k in range(12):
        a = math.radians(k * 30)
        d.line((cx + math.sin(a) * (R - 22), cy - math.cos(a) * (R - 22), cx + math.sin(a) * (R - 4), cy - math.cos(a) * (R - 4)), fill=INK, width=5)
    for n, (dx, dy) in {12: (0, -1), 3: (1, 0), 6: (0, 1), 9: (-1, 0)}.items():
        txt(d, (cx + dx * (R - 55), cy + dy * (R - 55)), n, 44, bold=True, anchor="mm")
    am = math.radians(m * 6)
    ah = math.radians((h % 12) * 30 + m * 0.5)
    d.line((cx, cy, cx + math.sin(ah) * 100, cy - math.cos(ah) * 100), fill=INK, width=11)
    d.line((cx, cy, cx + math.sin(am) * 150, cy - math.cos(am) * 150), fill=(60, 60, 60), width=6)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=INK)
    return im


def cat_time():
    cat = "time"
    for i in range(6):                                                         # clock arithmetic
        r = rng_for("t_clock%d" % i)
        h, m = r.randrange(1, 13), r.choice([0, 15, 30, 45])
        add_min = r.choice([30, 45, 75, 90])
        tot = (h * 60 + m + add_min) % (12 * 60)
        rh, rm = (tot // 60) or 12, tot % 60
        right = "%d:%02d" % (rh, rm)
        wrong = []
        for dm in (-30, 30, 60, -60, 15, -15):
            t2 = (tot + dm) % (12 * 60)
            s = "%d:%02d" % ((t2 // 60) or 12, t2 % 60)
            if s != right and s not in wrong:
                wrong.append(s)
        choice(cat, ["clock", "arithmetic"], clock(h, m), "What time will it be in %d minutes?" % add_min, "%d 分後は何時何分ですか？" % add_min, right, wrong[:3], diff="hard")
    STEPS = [("Boil water", "お湯を沸かす"), ("Add tea bag", "ティーバッグを入れる"), ("Pour water", "お湯を注ぐ"), ("Wait 3 minutes", "3 分待つ")]
    for i in range(5):                                                         # what comes right after step X
        r = rng_for("t_proc%d" % i)
        order = [0, 1, 2, 3]
        shown = order[:]
        r.shuffle(shown)
        if shown == order:
            shown = order[::-1]
        k = r.randrange(0, 3)
        im, d = canvas((255, 255, 255))
        for j, s in enumerate(shown):
            txt(d, (50, 60 + j * 90), "%d. %s" % (j + 1, STEPS[s][0]), 40, anchor="lm")
        txt(d, (50, 430), "(boxes are in random order)", 30, anchor="lm")
        choice(cat, ["procedure"], im, "In the natural order of making tea, which step comes right after \"%s\"?" % STEPS[k][0],
               "お茶を入れる自然な順番で、「%s」の直後に来る手順はどれですか？" % STEPS[k][1], STEPS[k + 1][0], [STEPS[j][0] for j in range(4) if j != k + 1 and j != k],
               STEPS[k + 1][1], [STEPS[j][1] for j in range(4) if j != k + 1 and j != k], diff="hard")
    for i in range(5):                                                         # before / after (two pictures)
        r = rng_for("t_ba%d" % i)
        kinds = [("circle", "red"), ("square", "blue"), ("triangle", "green"), ("circle", "yellow")]
        gone = r.randrange(4)
        before = shapes_scene(r, kinds)
        after = shapes_scene(r, [k for j, k in enumerate(kinds) if j != gone])
        names = ["%s %s" % (c, k) for k, c in kinds]
        right = names[gone]
        choice(cat, ["before-after", "two-images"], [before, after], "Which object is in the first picture but not in the second?", "1 枚目にあって 2 枚目にない物体はどれですか？",
               right, [x for x in names if x != right], "%s の%s" % (NAMES_JA[kinds[gone][1]], {"circle": "円", "square": "四角", "triangle": "三角"}[kinds[gone][0]]),
               ["%s の%s" % (NAMES_JA[c], {"circle": "円", "square": "四角", "triangle": "三角"}[k]) for j, (k, c) in enumerate(kinds) if j != gone],
               diff="medium", state_en="Two pictures are attached.", state_ja="2 枚の画像が添付されています。")
    for i in range(4):                                                         # AND lamp
        r = rng_for("t_lamp%d" % i)
        a_open = i % 2 == 0
        im, d = canvas((255, 255, 255))
        d.line((60, 240, 160, 240), fill=INK, width=6)
        d.line((160, 240, 240, 240 if not a_open else 190), fill=INK, width=6)
        txt(d, (200, 295), "A", 44, bold=True, anchor="mm")
        d.line((260, 240, 340, 240), fill=INK, width=6)
        d.line((340, 240, 420, 240), fill=INK, width=6)
        txt(d, (380, 295), "B", 44, bold=True, anchor="mm")
        d.ellipse((470, 200, 550, 280), outline=INK, width=6)
        txt(d, (510, 240), "L", 44, bold=True, anchor="mm")
        d.line((550, 240, 600, 240), fill=INK, width=6)
        txt(d, (W // 2, 400), "The lamp L is on only when A and B are both closed.", 30, anchor="mm")
        txt(d, (W // 2, 440), "A is %s, B is closed." % ("open" if a_open else "closed"), 36, bold=True, anchor="mm")
        yesno(cat, ["circuit", "cause"], im, "The lamp L is on", "ランプ L は点灯している", not a_open, diff="medium")


# =============================================================================================== 6. checking a statement against a figure
def cat_consistency():
    cat = "consistency"
    for i in range(6):                                                         # receipt: printed total correct?
        r = rng_for("c_total%d" % i)
        prices = [r.choice([120, 180, 250, 300, 340, 410]) for _ in range(3)]
        true = sum(prices)
        ok = i % 2 == 0
        printed = true if ok else true + r.choice([-60, -30, 30, 50, 90])
        im, d = canvas((255, 255, 250))
        for k, p in enumerate(prices):
            txt(d, (60, 70 + k * 70), "Item %s" % "ABC"[k], 42, anchor="lm")
            txt(d, (580, 70 + k * 70), p, 42, anchor="rm")
        d.line((50, 290, 590, 290), fill=INK, width=4)
        txt(d, (60, 345), "TOTAL", 44, bold=True, anchor="lm")
        txt(d, (580, 345), printed, 44, bold=True, anchor="rm")
        yesno(cat, ["receipt", "arithmetic"], im, "The printed total equals the sum of the three items", "印字された合計は、3 つの品目の合計と一致している", ok, diff="hard")
    for i in range(6):                                                         # caption vs chart
        r = rng_for("c_cap%d" % i)
        vals = r.sample(range(5, 40), 4)
        lab = list("ABCD")
        claim_max = i % 2 == 0
        target = r.randrange(4)
        truth = (vals.index(max(vals)) == target) if claim_max else (vals.index(min(vals)) == target)
        im = bars(vals, lab)
        yesno(cat, ["chart", "caption"], im, "The caption says: \"%s is the %s.\" The caption matches the chart." % (lab[target], "highest" if claim_max else "lowest"),
              "キャプションは「%s が最も%s」と述べている。キャプションはグラフと一致している" % (lab[target], "高い" if claim_max else "低い"), truth, diff="medium")
    for i in range(6):                                                         # legend: colour -> series
        r = rng_for("c_leg%d" % i)
        cities = ["Tokyo", "Osaka", "Kyoto"]
        cols = ["red", "blue", "green"]
        vals = {c: [r.randrange(10, 90) for _ in range(5)] for c in cities}
        x_idx = r.randrange(5)
        col_vals = {c: vals[c][x_idx] for c in cities}
        if len(set(col_vals.values())) < 3:
            continue
        im, d = canvas((255, 255, 255))
        d.line((70, 40, 70, 330), fill=INK, width=3)
        d.line((70, 330, 600, 330), fill=INK, width=3)
        for c, cl in zip(cities, cols):
            pts = [(100 + k * 120, 330 - vals[c][k] * 3) for k in range(5)]
            d.line(pts, fill=COLORS[cl], width=7)
        for k in range(5):
            txt(d, (100 + k * 120, 360), str(k + 1), 34, anchor="mm")
        order = cities[:]
        r.shuffle(order)
        for j, c in enumerate(order):
            d.rectangle((70 + j * 190, 410, 100 + j * 190, 440), fill=COLORS[cols[cities.index(c)]])
            txt(d, (108 + j * 190, 425), c, 34, anchor="lm")
        right = min(col_vals, key=col_vals.get)
        choice(cat, ["legend", "chart"], im, "Which city has the lowest value at x = %d?" % (x_idx + 1), "x = %d のとき、値がいちばん低い都市はどれですか？" % (x_idx + 1), right,
               [c for c in cities if c != right], diff="hard")


# =============================================================================================== 7. comparison, normalisation
def cat_compare():
    cat = "compare"
    for i in range(6):                                                         # per-hour production
        r = rng_for("p_rate%d" % i)
        hours = [2, 4, 1, 3]
        rows = []
        rates = []
        for k in range(3):
            h = r.choice(hours)
            rate = r.choice([3, 4, 5, 6, 7, 8])
            rows.append(["ABC"[k], str(rate * h), "%d h" % h])
            rates.append(rate)
        if len(set(rates)) < 3:
            continue
        right = "ABC"[rates.index(max(rates))]
        by_total = "ABC"[[int(x[1]) for x in rows].index(max(int(x[1]) for x in rows))]
        im = table(rows, ["Line", "Made", "Time"], [200, 200, 200])
        choice(cat, ["rate", "table"], im, "Which line makes the most items PER HOUR?", "1 時間あたりの生産数がいちばん多いラインはどれですか？", right, [x for x in "ABC" if x != right], diff="hard")
    for i in range(6):                                                         # largest increase
        r = rng_for("p_inc%d" % i)
        start = [r.randrange(2, 12) for _ in range(3)]
        end = [s + r.randrange(0, 9) for s in start]
        inc = [e - s for s, e in zip(start, end)]
        if len(set(inc)) < 3:
            continue
        right = "ABC"[inc.index(max(inc))]
        im = table([[n, str(s), str(e)] for n, s, e in zip("ABC", start, end)], ["Item", "Before", "After"], [200, 200, 200])
        choice(cat, ["difference", "table"], im, "Which item increased the most (After minus Before)?", "増加量（After − Before）がいちばん大きい項目はどれですか？", right, [x for x in "ABC" if x != right], diff="medium")
    BANDS = ["0-<20%", "20-<40%", "40-<60%", "60-<80%", "80-100%"]
    for i in range(6):                                                         # pass rate band (score)
        r = rng_for("p_band%d" % i)
        n = r.choice([7, 8, 9, 11, 12])
        p = r.randrange(1, n)
        rate = 100 * p / n
        if any(abs(rate - e) < 3 for e in (20, 40, 60, 80)):
            continue
        band = min(4, int(rate // 20))
        im, d = canvas((255, 255, 255))
        for k in range(n):
            cx = 70 + (k % 6) * 90
            cy = 130 + (k // 6) * 120
            ok = k < p
            d.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=COLORS["green"] if ok else COLORS["red"])
            txt(d, (cx, cy), "ok" if ok else "x", 34, fill=(255, 255, 255), bold=True, anchor="mm")
        txt(d, (W // 2, 400), "Green = pass, red = fail", 34, anchor="mm")
        add(cat, ["rate", "score"], im, "score", {"instr": "Which band contains the pass rate?", "levels": BANDS}, {"instr": "合格率はどの区間に入りますか？", "levels": BANDS}, band, diff="hard")


# =============================================================================================== 8. physical common sense
def gear(d, cx, cy, r, colour):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colour, outline=INK, width=5)
    for k in range(10):
        a = math.radians(k * 36)
        x, y = cx + math.sin(a) * r, cy - math.cos(a) * r
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=colour, outline=INK, width=2)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=INK)


def cat_physics():
    cat = "physics"
    for i in range(6):                                                         # gear train
        r = rng_for("h_gear%d" % i)
        n = r.choice([3, 4])
        first_cw = r.random() < 0.5
        im, d = canvas((255, 255, 255))
        step = 520 // n
        for k in range(n):
            gear(d, 90 + k * step, 250, 62 if k % 2 == 0 else 52, (190 + 20 * (k % 2), 200, 225))
        txt(d, (90, 120), "clockwise" if first_cw else "counter-clockwise", 34, bold=True, anchor="mm")
        d.polygon([(90, 150), (70, 178), (110, 178)], fill=COLORS["red"])
        txt(d, (W // 2, 400), "Left gear: %s. Gears mesh." % ("clockwise" if first_cw else "counter-clockwise"), 32, anchor="mm")
        last_cw = first_cw if (n - 1) % 2 == 0 else not first_cw
        right = "clockwise" if last_cw else "counter-clockwise"
        other = "counter-clockwise" if last_cw else "clockwise"
        choice(cat, ["gears"], im, "Which way does the right-most gear turn?", "いちばん右の歯車はどちら向きに回りますか？", right, [other, "it does not turn", "it turns back and forth"],
               "時計回り" if last_cw else "反時計回り", ["反時計回り" if last_cw else "時計回り", "回らない", "行ったり来たりする"], diff="hard")
    for i in range(5):                                                         # balance
        r = rng_for("h_bal%d" % i)
        wl, wr = r.sample(range(1, 6), 2)
        dl, dr = r.randrange(1, 5), r.randrange(1, 5)
        tl, tr = wl * dl, wr * dr
        if tl == tr and i % 3:
            continue
        im, d = canvas((255, 255, 255))
        d.line((60, 250, 580, 250), fill=INK, width=8)
        d.polygon([(320, 250), (285, 340), (355, 340)], fill=(120, 120, 130))
        for k in range(1, 5):
            for sgn in (-1, 1):
                x = 320 + sgn * k * 62
                d.line((x, 244, x, 262), fill=INK, width=4)
        for sgn, w, dist in ((-1, wl, dl), (1, wr, dr)):
            x = 320 + sgn * dist * 62
            d.rectangle((x - 30, 170, x + 30, 240), fill=COLORS["orange"], outline=INK, width=3)
            txt(d, (x, 205), "%d kg" % w, 30, bold=True, anchor="mm")
        txt(d, (W // 2, 400), "Each tick is 1 unit from the centre.", 32, anchor="mm")
        right = "left" if tl > tr else "right" if tr > tl else "balanced"
        jr = {"left": "左", "right": "右", "balanced": "つり合う"}[right]
        choice(cat, ["balance", "torque"], im, "Weight x distance decides. Which side goes down?", "「重さ × 支点からの距離」で決まります。どちら側が下がりますか？", right,
               [x for x in ("left", "right", "balanced", "cannot tell") if x != right][:3], jr,
               [{"left": "左", "right": "右", "balanced": "つり合う", "cannot tell": "判断できない"}[x] for x in ("left", "right", "balanced", "cannot tell") if x != right][:3], diff="hard")
    for i in range(5):                                                         # bridge limit
        r = rng_for("h_bridge%d" % i)
        limit = r.choice([100, 150, 200])
        a = r.choice([limit - 30, limit - 50, limit + 30, limit + 60])
        b = r.choice([limit - 20, limit + 20, limit + 50])
        im, d = canvas((255, 255, 255))
        d.rectangle((60, 190, 580, 220), fill=(130, 100, 70))
        d.rectangle((250, 60, 390, 140), fill=(255, 255, 255), outline=COLORS["red"], width=8)
        txt(d, (320, 100), "max %d kg" % limit, 34, bold=True, anchor="mm")
        for x, nm, w in ((120, "A", a), (440, "B", b)):
            d.rectangle((x, 300, x + 90, 360), fill=COLORS["blue"])
            txt(d, (x + 45, 330), nm, 44, fill=(255, 255, 255), bold=True, anchor="mm")
            txt(d, (x + 45, 400), "%d kg" % w, 36, bold=True, anchor="mm")
        okA, okB = a <= limit, b <= limit
        right = {(True, True): "both", (True, False): "A only", (False, True): "B only", (False, False): "neither"}[(okA, okB)]
        ja = {"both": "両方", "A only": "A だけ", "B only": "B だけ", "neither": "どちらも不可"}
        allo = ["A only", "B only", "both", "neither"]
        choice(cat, ["limit"], im, "Which cart(s) can cross without exceeding the limit?", "制限を超えずに渡れるのはどの台車ですか？", right, [x for x in allo if x != right], ja[right],
               [ja[x] for x in allo if x != right], diff="medium")


# =============================================================================================== 9. insufficient information
def cat_uncertain():
    cat = "uncertainty"
    for i in range(6):                                                         # can the highest be identified?
        r = rng_for("u_max%d" % i)
        a, c = r.sample(range(8, 20), 2)
        known_max = max(a, c)
        determinable = i % 2 == 0
        if determinable:
            lo, hi = 1, known_max - r.randrange(1, 4)
        else:
            lo, hi = known_max - r.randrange(1, 4), known_max + r.randrange(2, 6)
        im, d = canvas((255, 255, 255))
        for k, (nm, label) in enumerate((("A", str(a)), ("B", "%d to %d" % (lo, hi)), ("C", str(c)))):
            txt(d, (60, 90 + k * 110), nm, 52, bold=True, anchor="lm")
            txt(d, (170, 90 + k * 110), label, 48, anchor="lm")
        txt(d, (W // 2, 430), "B is only known to lie in its range.", 32, anchor="mm")
        yesno(cat, ["range", "determinable"], im, "It is certain which of A, B and C has the highest value", "A・B・C のうち値がいちばん高いのはどれか、確実に分かる", determinable, diff="hard")
    for i in range(6):                                                         # probability from a bag
        r = rng_for("u_prob%d" % i)
        red, blue, green = r.randrange(1, 5), r.randrange(1, 5), r.randrange(0, 3)
        tot = red + blue + green
        if tot not in (4, 5, 8, 10):
            continue
        p = round(100 * red / tot)
        im, d = canvas((255, 255, 255))
        balls = ["red"] * red + ["blue"] * blue + ["green"] * green
        r.shuffle(balls)
        for k, c in enumerate(balls):
            d.ellipse((60 + (k % 5) * 105, 100 + (k // 5) * 110, 150 + (k % 5) * 105, 190 + (k // 5) * 110), fill=COLORS[c])
        txt(d, (W // 2, 400), "One ball is drawn at random.", 38, anchor="mm")
        cand = [p, 100 - p, round(100 * blue / tot), round(100 * (red + blue) / tot), 50, 25]
        wrong = []
        for x in cand:
            if x != p and x not in wrong:
                wrong.append(x)
        choice(cat, ["probability"], im, "What is the probability (%) that the ball drawn is red?", "引いた玉が赤である確率（%）はいくつですか？", str(p), [str(x) for x in wrong[:3]], diff="hard")


# =============================================================================================== 10. conditional counting
def cat_count():
    cat = "count"
    for i in range(14):
        r = rng_for("k_cnt%d" % i)
        cols = ["red", "blue", "green"]
        kinds = ["circle", "square"]
        sizes = {"big": 50, "small": 26}
        n = r.randrange(7, 12)
        objs = [(r.choice(kinds), r.choice(cols), r.choice(list(sizes))) for _ in range(n)]
        im, d = canvas((255, 255, 255))
        pos = []
        tries = 0
        for kind, colr, sz in objs:
            s = sizes[sz]
            while tries < 4000:
                tries += 1
                x, y = r.randrange(70, 570), r.randrange(70, 410)
                if all((x - px) ** 2 + (y - py) ** 2 > (s + ps + 14) ** 2 for px, py, ps in pos):
                    pos.append((x, y, s))
                    if kind == "circle":
                        d.ellipse((x - s, y - s, x + s, y + s), fill=COLORS[colr])
                    else:
                        d.rectangle((x - s, y - s, x + s, y + s), fill=COLORS[colr])
                    break
        if len(pos) != n:
            continue
        mode = i % 3
        if mode == 0:
            colr, sz = r.choice(cols), r.choice(["big", "small"])
            c = sum(1 for o in objs if o[1] == colr and o[2] == sz)
            en, ja = "How many %s %s shapes are there?" % (sz, colr), "%s%s図形はいくつありますか？" % ("大きい" if sz == "big" else "小さい", {"red": "赤い", "blue": "青い", "green": "緑色の", "yellow": "黄色い"}[colr])
        elif mode == 1:
            colr = r.choice(cols)
            c = sum(1 for o in objs if o[0] == "circle" and o[1] != colr)
            en, ja = "How many circles are NOT %s?" % colr, "%sでない円はいくつありますか？" % NAMES_JA[colr]
        else:
            colr = r.choice(cols)
            c = sum(1 for o in objs if o[0] == "square" and o[1] == colr) + sum(1 for o in objs if o[0] == "circle" and o[1] == colr)
            en, ja = "How many shapes are %s (circles and squares together)?" % colr, "%s の図形（円も四角も）はいくつありますか？" % NAMES_JA[colr]
        choice(cat, ["conditional-count"], im, en, ja, str(c), numopts(c, [n, c + 1, max(0, c - 1)], r), diff="hard")


# =============================================================================================== 11. instruments (score)
def cat_instruments():
    cat = "instrument"
    BANDS = ["0-<20", "20-<40", "40-<60", "60-<80", "80-100"]
    for i in range(12):
        r = rng_for("m_dial%d" % i)
        v = r.randrange(2, 99)
        if any(abs(v - e) < 5 for e in (20, 40, 60, 80)):
            continue
        im, d = canvas((255, 255, 255))
        cx, cy, R = 320, 330, 230
        d.pieslice((cx - R, cy - R, cx + R, cy + R), 180, 360, outline=INK, width=6, fill=(250, 250, 250))
        for k in range(0, 101, 20):
            a = math.radians(180 + k * 1.8)
            d.line((cx + math.cos(a) * (R - 30), cy + math.sin(a) * (R - 30), cx + math.cos(a) * R, cy + math.sin(a) * R), fill=INK, width=6)
            txt(d, (cx + math.cos(a) * (R - 62), cy + math.sin(a) * (R - 62)), k, 34, bold=True, anchor="mm")
        a = math.radians(180 + v * 1.8)
        d.line((cx, cy, cx + math.cos(a) * (R - 40), cy + math.sin(a) * (R - 40)), fill=COLORS["red"], width=9)
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=INK)
        txt(d, (W // 2, 440), "Dial 0 to 100", 34, anchor="mm")
        add(cat, ["dial", "score"], im, "score", {"instr": "Which band does the needle point to?", "levels": BANDS}, {"instr": "針が指しているのはどの区間ですか？", "levels": BANDS}, min(4, v // 20), diff="medium")


# =============================================================================================== 12. two pictures compared
def cat_two():
    cat = "two-images"
    for i in range(8):
        r = rng_for("w_two%d" % i)
        a = r.sample(range(5, 30), 3)
        b = r.sample(range(5, 30), 3)
        if abs(sum(a) - sum(b)) < 6:
            continue
        right = "first" if sum(a) > sum(b) else "second"
        ja = {"first": "1 枚目", "second": "2 枚目"}
        choice(cat, ["two-images", "sum"], [bars(a, list("ABC")), bars(b, list("ABC"))], "Which chart has the larger total of its three bars?", "3 本の棒の合計が大きいのはどちらのグラフですか？",
               right, [x for x in ("first", "second") if x != right] + ["they are equal"], ja[right], [ja[x] for x in ("first", "second") if x != right] + ["同じ"],
               diff="hard", state_en="Two pictures are attached.", state_ja="2 枚の画像が添付されています。")


# =============================================================================================== extra yes/no and score variants
def cat_extra():
    """Statements to be judged true / false (about half each) and a numeric-band score: the same skills as above in another form."""
    L = list("ABCDE")
    for i in range(8):                                                         # sum statement
        r = rng_for("x_sum%d" % i)
        vals = r.sample(range(8, 40), 5)
        a, b = r.sample(range(5), 2)
        c = vals[a] + vals[b]
        true = i % 2 == 0
        shown = c if true else r.choice([abs(vals[a] - vals[b]), c + 10, c - 10, sum(vals) - c])
        if shown == c and not true:
            shown = c + 10
        yesno("quantity", ["sum", "chart", "statement"], bars(vals, L), "The sum of bars %s and %s is %d" % (L[a], L[b], shown), "棒 %s と棒 %s の合計は %d である" % (L[a], L[b], shown),
              shown == c, diff="medium")
    DIRS = [("up", "上"), ("right", "右"), ("down", "下"), ("left", "左")]
    for i in range(6):                                                         # rotation statement
        r = rng_for("x_rot%d" % i)
        k0 = r.randrange(4)
        turns = r.choice([1, 2, 3])
        k1 = (k0 + turns) % 4
        shown = k1 if i % 2 == 0 else r.choice([k for k in range(4) if k != k1])
        im, d = canvas((255, 255, 255))
        cx, cy = 320, 215
        v = [(0, -1), (1, 0), (0, 1), (-1, 0)][k0]
        px, py = -v[1], v[0]
        d.polygon([(cx + v[0] * 130, cy + v[1] * 130), (cx - v[0] * 20 + px * 70, cy - v[1] * 20 + py * 70), (cx - v[0] * 20 - px * 70, cy - v[1] * 20 - py * 70)], fill=COLORS["red"])
        d.rectangle((60, 40, 580, 400), outline=INK, width=4)
        word = {1: "90 degrees clockwise", 2: "180 degrees", 3: "90 degrees counter-clockwise"}[turns]
        wja = {1: "時計回りに 90 度", 2: "180 度", 3: "反時計回りに 90 度"}[turns]
        yesno("space", ["rotation", "statement"], im, "The card is turned %s. Afterwards the arrow points %s" % (word, DIRS[shown][0]),
              "カードを%s回す。回したあと、矢印は%sを向く" % (wja, DIRS[shown][1]), shown == k1, diff="hard")
    for i in range(6):                                                         # per-hour statement
        r = rng_for("x_rate%d" % i)
        rows, rates = [], []
        for k in range(2):
            h = r.choice([1, 2, 3, 4])
            rate = r.choice([3, 4, 5, 6, 7, 8])
            rows.append(["AB"[k], str(rate * h), "%d h" % h])
            rates.append(rate)
        if rates[0] == rates[1]:
            continue
        im = table(rows, ["Line", "Made", "Time"], [200, 200, 200])
        yesno("compare", ["rate", "statement"], im, "Line B makes more items PER HOUR than line A", "ライン B は、ライン A より 1 時間あたりの生産数が多い", rates[1] > rates[0], diff="hard")
    for i in range(6):                                                         # exact count statement
        r = rng_for("x_cnt%d" % i)
        cols = ["red", "blue", "green"]
        n = r.randrange(7, 11)
        objs = [(r.choice(["circle", "square"]), r.choice(cols), r.choice(["big", "small"])) for _ in range(n)]
        sizes = {"big": 50, "small": 26}
        im, d = canvas((255, 255, 255))
        pos, tries = [], 0
        for kind, colr, sz in objs:
            sv = sizes[sz]
            while tries < 4000:
                tries += 1
                x, y = r.randrange(70, 570), r.randrange(70, 410)
                if all((x - px) ** 2 + (y - py) ** 2 > (sv + ps + 14) ** 2 for px, py, ps in pos):
                    pos.append((x, y, sv))
                    (d.ellipse if kind == "circle" else d.rectangle)((x - sv, y - sv, x + sv, y + sv), fill=COLORS[colr])
                    break
        if len(pos) != n:
            continue
        colr = r.choice(cols)
        c = sum(1 for o in objs if o[1] == colr and o[2] == "big")
        shown = c if i % 2 == 0 else max(0, c + r.choice([-1, 1, 2]))
        if shown == c and i % 2:
            shown = c + 1
        yesno("count", ["conditional-count", "statement"], im, "There are exactly %d big %s shapes" % (shown, colr), "大きい%s図形はちょうど %d 個ある" % ({"red": "赤い", "blue": "青い", "green": "緑色の"}[colr], shown),
              shown == c, diff="hard")
    BANDS = ["0-<50", "50-<100", "100-<150", "150-<200", "200-250"]
    for i in range(8):                                                         # a filled bar with a numeric scale, five bands
        r = rng_for("x_bar%d" % i)
        v = r.randrange(5, 246)
        if any(abs(v - e) < 12 for e in (50, 100, 150, 200)):
            continue
        im, d = canvas((255, 255, 255))
        x0, x1 = 60, 580
        d.rectangle((x0, 170, x1, 250), outline=INK, width=5)
        d.rectangle((x0 + 3, 173, x0 + 3 + (x1 - x0 - 6) * v / 250, 247), fill=COLORS["orange"])
        for k in range(0, 251, 50):
            x = x0 + (x1 - x0) * k / 250
            d.line((x, 250, x, 275), fill=INK, width=4)
            txt(d, (x, 305), k, 34, bold=True, anchor="mm")
        txt(d, (W // 2, 90), "Load (0 to 250)", 40, bold=True, anchor="mm")
        add("instrument", ["bar", "score"], im, "score", {"instr": "Which band does the filled part reach?", "levels": BANDS},
            {"instr": "塗りつぶされた部分は、どの区間まで達していますか？", "levels": BANDS}, min(4, v // 50), diff="medium")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("rsn-*.png"):
        f.unlink()
    for make in (cat_quantity, cat_rules, cat_space, cat_negation, cat_time, cat_consistency, cat_compare, cat_physics, cat_uncertain,
                 cat_count, cat_instruments, cat_two, cat_extra):
        make()
    with JSONL.open("w", encoding="utf-8") as fh:
        for row in ITEMS:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    by = {}
    for row in ITEMS:
        by[row["tags"][2]] = by.get(row["tags"][2], 0) + 1
    kinds = {}
    for row in ITEMS:
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
    print("wrote %d items (%s) kinds %s to %s" % (len(ITEMS), ", ".join("%s %d" % kv for kv in sorted(by.items())), kinds, JSONL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
