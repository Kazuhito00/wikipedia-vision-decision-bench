# -*- coding: utf-8 -*-
"""New v1 questions, tag ``rendered_b``: follow-ups to the review of ``rendered`` (biz-3300.. / rsn-2001..).

    python datasets/synthetic/gen_v1_new_b.py [--dry] [--force]

Writes work/generated/<id>.png (640x480), work/generated/px224/<id>.png and datasets/questions/v1/new_rendered_b.jsonl.
Does NOT touch new_rendered.jsonl (reviewed; gen_v1_new.py must never be re-run with writes). Deterministic (seeded per pattern and number).
Every right answer is derived from the drawing parameters. Refuses to overwrite a jsonl that already holds reviewed rows unless --force.

Contents
  A. contrast pairs: "None of the above" / "Cannot be determined" is a WRONG option, the right answer is in the picture
     (grid cell, dice, cards, colour of the circle, highlighted station)  -> the special option is not a shortcut
  B. balancing the skewed answers found by the review: left/right (1:3), in front (3 of 5 orange), 3-level thermometer (all 20-30 degC)
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import gen_v1_new as g  # noqa: E402  (only functions are used; importing writes nothing)
from gen_v1_new import (R, T, W, INK, COLORS, COLOR_JA, SHAPE_JA, NONE, CBD, canvas, shape, scatter, choice, cn, lab, grid_dims,  # noqa: E402
                        p_color_circle, p_station, p_thermo, value_in_level, make_row, thumb224)

OUT_DIR = ROOT / "work" / "generated"
JSONL = ROOT / "datasets" / "questions" / "v1" / "new_rendered_b.jsonl"
DLET = "KLMNPQRS"      # die labels: deliberately NOT A-H (the runner's own option labels), so a label never collides with an option letter


# ================================================================================================ A. special option is WRONG
def p_grid_b(qid, i, n, target):
    """Numbered cells (1..n); one red `target` shape in one cell, the rest blue/green/grey/orange circles and squares. Options: ALL cells + None of the above."""
    r = R("grid_b", i)
    rows, cols = grid_dims(n)
    cw, ch = 600 / cols, 440 / rows
    tpos = r.randrange(n)
    im, d = canvas(r)
    for k in range(n):
        rr, cc = divmod(k, cols)
        x0, y0 = 20 + cc * cw, 20 + rr * ch
        d.rectangle((x0, y0, x0 + cw, y0 + ch), outline=(120, 120, 120), width=2)
        cx, cy = x0 + cw / 2 + 8, y0 + ch / 2 + 8
        rad = min(cw, ch) * 0.28
        if k == tpos:
            shape(d, target, cx, cy, rad * 1.1, COLORS["red"])
        else:
            shape(d, r.choice(["circle", "square"]), cx, cy, rad, COLORS[r.choice(["blue", "green", "grey", "orange"])])
        T(d, (x0 + 24, y0 + 22), k + 1, 36, fill=(30, 50, 140))
    nums = [lab(str(k + 1)) for k in range(n)]
    return im, dict(image_type="figure", skill="spatial", difficulty="easy" if n <= 9 else "medium",
                    tags=["synthetic", "grid", "many-options", "special-option-wrong"],
                    **choice("Which cell contains the %s?" % target, "%sが入っているマスはどれですか？" % SHAPE_JA[target], nums[tpos],
                             [x for k, x in enumerate(nums) if k != tpos], special=[NONE]))


def p_dice_b(qid, i, n, t):
    """n dice, exactly one shows t dots (the others show 1..6 except t). Options: all dice (letters K..) + None of the above."""
    r = R("dice_b", i)
    pos = r.randrange(n)
    vals = [t if k == pos else r.choice([v for v in range(1, 7) if v != t]) for k in range(n)]
    assert vals.count(t) == 1
    per = 4 if n > 5 else 3
    rows = [list(range(j, min(j + per, n))) for j in range(0, n, per)]
    im, d = canvas(r)
    for ri, row in enumerate(rows):
        for ci, k in enumerate(row):
            cx = 320 + (ci - (len(row) - 1) / 2) * 150
            cy = 140 + ri * 200
            d.rounded_rectangle((cx - 55, cy - 55, cx + 55, cy + 55), radius=14, fill=(255, 255, 255), outline=INK, width=4)
            for (dx, dy) in g.PIPS[vals[k]]:
                d.ellipse((cx + dx * 28 - 11, cy + dy * 28 - 11, cx + dx * 28 + 11, cy + dy * 28 + 11), fill=INK)
            T(d, (cx, cy + 82), DLET[k], 32)
    labs = [lab(DLET[k]) for k in range(n)]
    return im, dict(image_type="figure", skill="recognition", difficulty="medium", tags=["synthetic", "dice", "many-options", "special-option-wrong"],
                    **choice("Which die shows %d dots?" % t, "%d の目が出ているサイコロはどれですか？" % t, labs[pos],
                             [x for k, x in enumerate(labs) if k != pos], special=[NONE]))


def p_card_b(qid, i, n, target, down):
    """n cards numbered 1..n; card `down` is face down (grey, ?), the others face up in distinct colours. The question asks about the face-up card `target`
    (never the face-down one). Options: 4 colours (3 for n=3 cards... see below) + Cannot be determined (wrong: the colour is visible)."""
    r = R("card_b", i)
    assert target != down
    pool = ["red", "blue", "green", "yellow", "purple", "orange"]
    cols = r.sample(pool, n - 1)
    up = [k for k in range(n) if k != down]
    colour = dict(zip(up, cols))
    im, d = canvas(r)
    w, gap, x00 = (150, 190, 60) if n == 3 else (120, 150, 30)
    for k in range(n):
        x0 = x00 + k * gap
        if k == down:
            d.rounded_rectangle((x0, 110, x0 + w, 350), radius=14, fill=(95, 95, 110), outline=INK, width=4)
            T(d, (x0 + w / 2, 230), "?", 90, fill=(255, 255, 255))
        else:
            d.rounded_rectangle((x0, 110, x0 + w, 350), radius=14, fill=COLORS[colour[k]], outline=INK, width=4)
        T(d, (x0 + w / 2, 405), k + 1, 44)
    spare = [c for c in pool if c not in cols]
    others = [colour[k] for k in up if k != target]
    n_colours = 3 if n == 3 else 4                       # 3 cards: 3 colours + special = 4 options; 4 cards: 4 colours + special = 5 options
    wrong = others + r.sample(spare, n_colours - 1 - len(others))
    return im, dict(image_type="figure", skill="recognition", difficulty="medium", tags=["synthetic", "cards", "special-option-wrong"],
                    **choice("What colour is card %d?" % (target + 1), "カード %d は何色ですか？" % (target + 1), cn(colour[target]), [cn(c) for c in wrong],
                             special=[CBD]))


# ================================================================================================ B. skew fixes
def p_side_b(i, left):
    r = R("side_b", i)
    x = r.uniform(70, 230) if left else r.uniform(410, 570)
    y = r.uniform(110, 370)
    im, d = canvas(r)
    pts = scatter(r, 3, 40, box=(20, 20, 620, 460), mind=100, avoid=[(x, y)])
    for (px, py) in pts:
        shape(d, "square", px, py, 38, COLORS["blue"])
    shape(d, "circle", x, y, 44, COLORS["red"])
    L, Rr = ("left", "左"), ("right", "右")
    return im, dict(image_type="figure", skill="spatial", difficulty="easy", tags=["synthetic", "position", "two-options"],
                    **choice("Is the red circle on the left or the right side of the picture?", "赤い円は画像の左側と右側のどちらにありますか？",
                             L if x < 320 else Rr, [Rr] if x < 320 else [L]))


def p_front_b(i, ask, c_front, c_back):
    """Two overlapping shapes; ask = which one is in front / behind. The question lists the two colours in a random order."""
    r = R("front_b", i)
    kind = r.choice(["square", "circle"])
    im, d = canvas(r)
    ox, oy = r.choice([-1, 1]) * 55, r.choice([-1, 1]) * 35
    shape(d, kind, 320 - ox / 2, 240 - oy / 2, 105, COLORS[c_back], w=5)
    shape(d, kind, 320 + ox / 2, 240 + oy / 2, 105, COLORS[c_front], w=5)       # drawn last = in front
    a, b = (c_front, c_back) if r.random() < 0.5 else (c_back, c_front)
    if ask == "front":
        en_q = "Which shape is in front, the %s one or the %s one?" % (a, b)
        ja_q = "手前にあるのは、%sの図形と%sの図形のどちらですか？" % (COLOR_JA[a], COLOR_JA[b])
        ok, ng = c_front, c_back
    else:
        en_q = "Which shape is behind, the %s one or the %s one?" % (a, b)
        ja_q = "奥にあるのは、%sの図形と%sの図形のどちらですか？" % (COLOR_JA[a], COLOR_JA[b])
        ok, ng = c_back, c_front
    return im, dict(image_type="figure", skill="spatial", difficulty="medium", tags=["synthetic", "position", "depth", "two-options"],
                    **choice(en_q, ja_q, cn(ok), [cn(ng)]))


#: (level, lowest, highest) of the value drawn: three thermometers of the same level sit in clearly different bands (no near-duplicates), and the
#: level-2 one stays away from biz-1010..1012 (about 26 degC)
THERMO_BANDS = [(0, 2, 3.5), (1, 11, 12.5), (0, 4.5, 6), (1, 14, 15.5), (0, 7, 8), (1, 16.5, 19), (2, 21, 24)]


def thermo_values(bands=THERMO_BANDS):
    """For each band the first seed number i whose drawn value (middle 60% of the 10-degree bin) falls in it. Returns [(i, level, value)]."""
    chosen, i = [], 100
    for lv, lo, hi in bands:
        while True:
            i += 1
            assert i < 20000, "no thermometer seed"
            v = value_in_level(R("thermo", i), lv, 3, 10)
            if lo <= v < hi:
                chosen.append((i, lv, v))
                break
    return chosen


# ================================================================================================ plan
def _thermo(qid, i, level):
    return p_thermo(qid, i, 3, level)


def _color(qid, i, n):
    return p_color_circle(qid, i, n, with_none=True)


def _station(qid, i, n):
    return p_station(qid, i, n, highlighted=True, with_none=True)


def _side(qid, i, left):
    return p_side_b(i, left)


def _front(qid, i, ask, cf, cb):
    return p_front_b(i, ask, cf, cb)


def build_plan():
    plan = []
    cnt = {"biz": 3299, "rsn": 2000}

    def add(group, fn, **kw):
        cnt[group] += 1
        plan.append(dict(group=group, id="%s-%04d" % (group, cnt[group]), fn=fn, kw=kw))

    for i, lv, v in thermo_values():
        add("biz", _thermo, i=i, level=lv)
    for k, (n, t) in enumerate(((6, "star"), (6, "triangle"), (8, "cross"), (8, "hexagon"), (9, "star"), (9, "cross"), (12, "triangle"), (12, "hexagon"))):
        add("rsn", p_grid_b, i=k, n=n, target=t)
    for k, (n, t) in enumerate(((5, 6), (6, 6), (6, 5), (7, 6), (8, 4), (8, 6), (5, 3), (7, 5))):
        add("rsn", p_dice_b, i=k, n=n, t=t)
    for k, (n, tg, dn) in enumerate(((3, 0, 2), (3, 2, 0), (3, 2, 1), (3, 0, 1), (4, 1, 3), (4, 3, 0), (4, 0, 2), (4, 2, 1))):
        add("rsn", p_card_b, i=k, n=n, target=tg, down=dn)
    for k, n in enumerate((6, 8, 10)):
        add("rsn", _color, i=20 + k, n=n)
    for k, n in enumerate((6, 8, 10)):
        add("rsn", _station, i=20 + k, n=n)
    for k, left in enumerate((True, True, False, True, False, True)):
        add("rsn", _side, i=k, left=left)
    for k, (ask, cf, cb) in enumerate((("front", "red", "orange"), ("behind", "blue", "purple"), ("front", "yellow", "green"),
                                       ("behind", "orange", "red"), ("front", "purple", "blue"), ("behind", "green", "yellow"))):
        add("rsn", _front, i=k, ask=ask, cf=cf, cb=cb)
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--jsonl", default=str(JSONL))
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite even if the jsonl already holds reviewed rows (their review is lost)")
    a = ap.parse_args()
    out, jp = pathlib.Path(a.out), pathlib.Path(a.jsonl)
    if not a.dry and jp.exists() and not a.force:
        old = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if any(r["review"]["state"] != "unreviewed" or r["review"]["history"] for r in old):
            print("refusing: %s holds reviewed rows (use --force to discard the review)" % jp)
            return 1
    rows = []
    for e in build_plan():
        im, spec = e["fn"](e["id"], **e["kw"])
        assert im.size == (W, 480)
        rows.append(make_row(e["id"], e["group"], spec))
        if not a.dry:
            (out / "px224").mkdir(parents=True, exist_ok=True)
            im.save(out / ("%s.png" % e["id"]), optimize=True)
            thumb224(im).save(out / "px224" / ("%s.png" % e["id"]), optimize=True)
    rows.sort(key=lambda r: r["id"])
    if not a.dry:
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("%d rows (%s)" % (len(rows), dict(collections.Counter(r["group"] for r in rows))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
