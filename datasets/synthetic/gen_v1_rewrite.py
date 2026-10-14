# -*- coding: utf-8 -*-
"""v1: rebuild the 12 two-picture reasoning questions (rsn-0102/0103/0104/0106 before-after, rsn-0188..0195 two bar charts) as
questions about ONE picture ("1 question, 1 picture").

    python datasets/synthetic/gen_v1_rewrite.py [--apply] [--date 2026-10-11] [--out work/generated]

* before-after (4): one picture, upper row "BEFORE", lower row "AFTER"; "Which object is in the top row but not in the bottom row?"
  The scene (which 4 shapes, which one disappears) is the one of the original item (same seed as gen_reasoning.cat_time); the right answer is
  DERIVED from the scene specification (set difference), never typed in.
* two bar charts (8): one picture, two 3-bar charts side by side ("LEFT" / "RIGHT") on ONE common value scale (so bar heights never
  mislead), values printed on the bars; "Which chart has the larger total of its three bars, left or right?" The values are the ones of
  the original item (same seed as gen_reasoning.cat_two); the larger total is placed left for even i, right for odd i.
  The right answer is derived from the sums.
Deterministic (seeds from the item; geometry fixed; only the font may differ by machine). Writes work/generated/<id>.png (640x480) and
work/generated/px224/<id>.png (224 px, what the models receive). Default is a dry run (prints the specs); --apply writes the pictures and
updates datasets/questions/v1/rsn.jsonl and manifests/questions_v1.csv (idempotent). Pictures are git-ignored.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import pathlib
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from gen import COLORS, NAMES_JA, font, rng_for  # noqa: E402
from datasets.tools import v1_io  # noqa: E402

W, H = 640, 480
INK = (25, 25, 25)
BAR = (70, 110, 205)
OUT_DIR = ROOT / "work" / "generated"
LOGICAL_DIR = "generated"                      # local_images of a rebuilt row = generated/<id>.png, relative to images_root (work/)
BA_IDS = ["rsn-0102", "rsn-0103", "rsn-0104", "rsn-0106"]
BAR_IDS = ["rsn-%04d" % n for n in range(188, 196)]
KINDS = [("circle", "red"), ("square", "blue"), ("triangle", "green"), ("circle", "yellow")]
KIND_JA = {"circle": "円", "square": "四角", "triangle": "三角"}
SHAPE_R = 50
BAND_H = H // 2


# ============================================================================================== specs (what is drawn)
def before_after_spec(qid: str) -> dict:
    """{before: [(kind, colour)], after: [...], gone: (kind, colour)}. Same draws as gen_reasoning.cat_time (seed t_ba<i>), the order of
    the shapes inside the rows is shuffled (same order in BEFORE and AFTER)."""
    i = int(qid.split("-")[1]) - 102                    # rsn-0102 .. rsn-0106 are t_ba0 .. t_ba4
    r = rng_for("t_ba%d" % i)
    gone = r.randrange(4)
    order = rng_for("v2_ba_%d" % i).sample(range(4), 4)   # seed spelling FROZEN (the dataset was called v2 when this was drawn)
    before = [KINDS[k] for k in order]
    after = [KINDS[k] for k in order if k != gone]
    return dict(before=before, after=after)


def answer_before_after(spec: dict) -> tuple:
    """The one object in BEFORE that is not in AFTER, derived from the scene."""
    gone = [x for x in spec["before"] if x not in spec["after"]]
    assert len(gone) == 1, gone
    return gone[0]


def bar_pair_spec(qid: str) -> dict:
    """{left: [3 values], right: [3 values]}. Values of the original item (seed w_two<i>), the larger total on the left for even i."""
    i = int(qid.split("-")[1]) - 188
    r = rng_for("w_two%d" % i)
    a, b = r.sample(range(5, 30), 3), r.sample(range(5, 30), 3)
    assert abs(sum(a) - sum(b)) >= 6                    # gen_reasoning skipped closer pairs; none of the 8 ids is one
    big, small = (a, b) if sum(a) > sum(b) else (b, a)
    left, right = (big, small) if i % 2 == 0 else (small, big)
    return dict(left=left, right=right)


def answer_bars(spec: dict) -> str:
    sl, sr = sum(spec["left"]), sum(spec["right"])
    return "left" if sl > sr else "right" if sr > sl else "equal"


# ============================================================================================== drawing
def _txt(d, xy, s, size, bold=True, fill=INK, anchor="mm"):
    d.text(xy, str(s), font=font(size, bold), fill=fill, anchor=anchor)


def slot_centres(n: int) -> list:
    return [320 + (i - (n - 1) / 2) * 150 for i in range(n)]


def shape_centre(band: int, idx: int, n: int) -> tuple:
    return (slot_centres(n)[idx], band * BAND_H + 140)


def draw_before_after(spec: dict) -> Image.Image:
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for band, (label, items) in enumerate((("BEFORE", spec["before"]), ("AFTER", spec["after"]))):
        _txt(d, (18, band * BAND_H + 32), label, 34, anchor="lm")
        for idx, (kind, colour) in enumerate(items):
            cx, cy = shape_centre(band, idx, len(items))
            s = SHAPE_R
            if kind == "circle":
                d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=COLORS[colour])
            elif kind == "square":
                d.rectangle((cx - s, cy - s, cx + s, cy + s), fill=COLORS[colour])
            else:
                d.polygon([(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)], fill=COLORS[colour])
    d.line((0, BAND_H, W, BAND_H), fill=(120, 120, 120), width=4)
    return im


def read_before_after(im: Image.Image) -> dict:
    """Read the scene back from the pixels (colour at the centre, corner pixels for the shape). Used by the tests to prove that the
    picture shows what the specification says."""
    px = im.convert("RGB").load()
    inv = {v: k for k, v in COLORS.items()}
    out = {}
    for band, name in ((0, "before"), (1, "after")):
        out[name] = []
        for n in (5, 4, 3, 2, 1):                       # the largest layout whose every slot centre is a coloured shape
            got = []
            for cx in slot_centres(n):
                cy = band * BAND_H + 140
                colour = inv.get(px[int(cx), int(cy)])
                if colour is None:
                    break
                s = SHAPE_R
                top_left = px[int(cx - s + 4), int(cy - s + 4)] == COLORS[colour]
                bottom_left = px[int(cx - s + 4), int(cy + s - 4)] == COLORS[colour]
                got.append(("square" if top_left else "triangle" if bottom_left else "circle", colour))
            else:
                out[name] = got
                break
    return out


def draw_bar_pair(spec: dict) -> Image.Image:
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    ymax = max(spec["left"] + spec["right"])
    for p, (title, vals) in enumerate((("LEFT", spec["left"]), ("RIGHT", spec["right"]))):
        x_off = 10 + p * 320
        d.rectangle((x_off + 2, 8, x_off + 298, 462), outline=(150, 150, 150), width=2)
        _txt(d, (x_off + 150, 42), title, 38)
        d.line((x_off + 14, BASE, x_off + 286, BASE), fill=INK, width=3)
        for k, v in enumerate(vals):
            cx = x_off + 50 + k * 100
            top = BASE - PLOT_H * v / ymax
            d.rectangle((cx - 30, top, cx + 30, BASE), fill=BAR)
            _txt(d, (cx, top - 22), v, 36)
            _txt(d, (cx, BASE + 32), "ABC"[k], 36)
    return im


BASE, PLOT_H = 410, 270


def read_bar_pair(im: Image.Image, ymax: int) -> dict:
    """Read the bar values back from the bar heights (common scale): value = height * ymax / PLOT_H."""
    px = im.convert("RGB").load()
    out = {}
    for p, name in enumerate(("left", "right")):
        vals = []
        for k in range(3):
            cx = 10 + p * 320 + 50 + k * 100
            h = 0
            for y in range(BASE, 60, -1):
                if px[cx + 20, y] == BAR:
                    h += 1
                elif h:
                    break
            vals.append(round(h * ymax / PLOT_H))
        out[name] = vals
    return out


# ============================================================================================== rows
def shape_name_en(item: tuple) -> str:
    return "%s %s" % (item[1], item[0])


def _ja_shape(item: tuple) -> str:
    return "%sの%s" % (NAMES_JA[item[1]], KIND_JA[item[0]])


def rebuild_row(row: dict, date: str) -> tuple:
    """(new row, spec, drawn picture, description). The row must be one of the 12 ids."""
    qid = row["id"]
    new = copy.deepcopy(row)
    if qid in BA_IDS:
        spec = before_after_spec(qid)
        gone = answer_before_after(spec)
        names = [x for x in KINDS if x != gone]
        right = shape_name_en(gone)
        new["en"].update(instr="Which object is in the top row (BEFORE) but not in the bottom row (AFTER)?", correct=right,
                         wrong=[shape_name_en(x) for x in names])
        new["ja"].update(instr="上段（BEFORE）にあって下段（AFTER）にない物体はどれですか？", correct=_ja_shape(gone),
                         wrong=[_ja_shape(x) for x in names])
        new["tags"] = ["synthetic", "reasoning", "r-time", "before-after", "one-image"]
        new["image_type"], new["difficulty"] = "figure", "medium"
        img = draw_before_after(spec)
        desc = "BEFORE row / AFTER row in one picture; answer %s (derived by set difference)" % right
    elif qid in BAR_IDS:
        spec = bar_pair_spec(qid)
        side = answer_bars(spec)
        assert side != "equal"
        gap = abs(sum(spec["left"]) - sum(spec["right"]))
        ja = {"left": "左", "right": "右", "equal": "同じ"}
        other = "right" if side == "left" else "left"
        new["en"].update(instr="Which chart has the larger total of its three bars, the left one or the right one?", correct=side,
                         wrong=[other, "they are equal"])
        new["ja"].update(instr="3 本の棒の合計が大きいのは、左右どちらのグラフですか？", correct=ja[side], wrong=[ja[other], "同じ"])
        new["tags"] = ["synthetic", "reasoning", "r-quantity", "side-by-side", "sum", "one-image"]
        new["image_type"], new["difficulty"] = "chart", "hard" if gap <= 12 else "medium"
        img = draw_bar_pair(spec)
        desc = "LEFT/RIGHT bar charts on one common scale; totals %d vs %d, answer %s (derived from the sums)" % (
            sum(spec["left"]), sum(spec["right"]), side)
    else:
        raise ValueError("%s is not one of the 12 rewrite ids" % qid)
    for lang in ("en", "ja"):
        new[lang].pop("state", None)                    # one picture: the loader's default state text applies
    new["images"] = ["%s.png" % qid]
    new["local_images"] = ["%s/%s.png" % (LOGICAL_DIR, qid)]
    new["answer_format"] = v1_io.answer_format(new)[0]
    return new, spec, img, desc


def thumb224(im: Image.Image) -> Image.Image:
    t = im.copy()
    t.thumbnail((224, 224), Image.LANCZOS)
    return t


def apply_rewrite(by_group: dict, date: str, out: pathlib.Path, write_images: bool = True) -> list:
    """Rebuild the 12 rows in place (idempotent). Returns [(id, description)]."""
    rows = {r["id"]: r for r in by_group["rsn"]}
    done = []
    for qid in BA_IDS + BAR_IDS:
        old = rows[qid]
        if old["review"]["state"] == "dropped":
            continue
        new, _, img, desc = rebuild_row(old, date)
        if write_images:
            out.mkdir(parents=True, exist_ok=True)
            (out / "px224").mkdir(parents=True, exist_ok=True)
            img.save(out / ("%s.png" % qid), optimize=True)
            thumb224(img).save(out / "px224" / ("%s.png" % qid), optimize=True)
        rev = old["review"]
        # the history text keeps the script's OLD file name (gen_v2_rewrite.py): it is the recorded original wording, and the
        # idempotency check below compares it with the entries already written in rsn.jsonl
        entry = {"date": date, "what": "rewrite_1image: rebuilt as one picture", "why": desc + " (gen_v2_rewrite.py)"}
        old.clear()
        old.update(new)
        old["review"] = rev
        if not any(h["what"] == entry["what"] and h["why"] == entry["why"] for h in rev["history"]):
            rev["history"].append(entry)
        rev["state"] = "changed"
        done.append((qid, desc))
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--out", default=str(OUT_DIR))
    a = ap.parse_args()
    by_group = v1_io.load_v1()
    done = apply_rewrite(by_group, a.date, pathlib.Path(a.out), write_images=a.apply)
    for qid, desc in done:
        print("%s: %s" % (qid, desc))
    if a.apply:
        v1_io.save_v1(by_group)
        v1_io.write_questions_csv(by_group)
        print("written: %d pictures in %s (+ px224/), rsn.jsonl, questions_v1.csv" % (len(done), a.out))
    else:
        print("dry run (use --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
