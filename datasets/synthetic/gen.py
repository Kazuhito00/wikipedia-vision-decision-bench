# -*- coding: utf-8 -*-
"""Synthetic practical-question set: pictures drawn by this script, answers known exactly because the script drew them.

    python datasets/synthetic/gen.py   # writes work/legacy_regen/synthetic/*.png and work/legacy_regen/synthetic.jsonl
    (the frozen legacy rows are datasets/questions/legacy/synthetic.jsonl; this script never overwrites them -- tests/ compares)

Broadens the Wikipedia/Commons set with the pictures an agent actually meets: charts and tables, dashboards and gauges,
UI screens, receipts and invoices, floor plans and warning signs, plus plain visual reasoning (counting, position, odd one
out). Every item is a bilingual pair (the same picture, an English and a Japanese question) like the Commons items, and the
rows have the same schema as data/linked.jsonl, so eval_common/run.py and wiki_report.py read them unchanged (they are
tagged "synthetic" and tallied separately: nothing here is a photograph and nothing here comes from Wikipedia).

Deterministic: every random choice is seeded from the item id. Text inside pictures is Latin letters and digits, so one
picture serves both languages. Fonts: Arial if present, else Pillow's built-in font.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work" / "legacy_regen" / "synthetic"
JSONL = ROOT / "work" / "legacy_regen" / "synthetic.jsonl"
W, H = 640, 480

COLORS = {"red": (210, 40, 40), "blue": (40, 80, 210), "green": (40, 160, 70), "yellow": (240, 200, 30),
          "orange": (240, 140, 30), "purple": (130, 60, 170), "grey": (130, 130, 130), "black": (30, 30, 30)}
NAMES_JA = {"red": "赤", "blue": "青", "green": "緑", "yellow": "黄色", "orange": "オレンジ", "purple": "紫", "grey": "灰色", "black": "黒"}
BG = (248, 248, 244)

_font_cache = {}


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key not in _font_cache:
        for name in (("arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("arial.ttf", "DejaVuSans.ttf")):
            try:
                _font_cache[key] = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        else:
            _font_cache[key] = ImageFont.load_default(size)
    return _font_cache[key]


def canvas(bg=BG):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def text(d, xy, s, size=28, fill=(20, 20, 20), bold=False, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


ITEMS: list[dict] = []
_counter = [0]


def rng_for(tag: str) -> random.Random:
    return random.Random("syn:" + tag)


def add(group: str, tags: list[str], img: Image.Image, kind: str, en: dict, ja: dict, answer=None, difficulty="medium",
        state_en: str = "", state_ja: str = ""):
    """One bilingual item. choice: en/ja = {instr, correct, wrong}; noul: {instr}, answer bool; score: {instr, levels}, answer idx."""
    _counter[0] += 1
    qid = "syn-%04d" % _counter[0]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    name = qid + ".png"
    img.save(OUT_DIR / name, optimize=True)
    row = {"id": qid, "modality": "image", "kind": kind, "tags": ["synthetic", group] + tags, "difficulty": difficulty,
           "images": [name], "langs": ["en", "ja"], "used_by": ["en", "ja"], "articles": {}, "source": "synthetic",
           "en": dict(en), "ja": dict(ja), "local_images": ["data/synthetic/" + name]}
    if state_en:
        row["en"]["state"] = state_en
        row["ja"]["state"] = state_ja
    if kind in ("noul", "score"):
        row["answer"] = answer
    ITEMS.append(row)


def yesno(img, group, tags, en, ja, answer, **kw):
    add(group, tags, img, "noul", {"instr": en}, {"instr": ja}, answer, **kw)


def pick(img, group, tags, en_q, ja_q, en_correct, ja_correct, en_wrong, ja_wrong, **kw):
    add(group, tags, img, "choice", {"instr": en_q, "correct": en_correct, "wrong": en_wrong},
        {"instr": ja_q, "correct": ja_correct, "wrong": ja_wrong}, **kw)


def wrong_ints(correct: int, pool, k=3, rng=None):
    rest = [x for x in pool if x != correct]
    (rng or random).shuffle(rest)
    return [str(x) for x in rest[:k]]


# ---------------------------------------------------------------------------------------------- charts

def bar_chart(values, colors=None, labels=None, threshold=None, title=None):
    im, d = canvas((255, 255, 255))
    n = len(values)
    left, right, top, bottom = 70, 600, 70 if title else 40, 400
    top_val = max(max(values), threshold or 0) * 1.15
    d.line((left, top, left, bottom), fill=(0, 0, 0), width=2)
    d.line((left, bottom, right, bottom), fill=(0, 0, 0), width=2)
    if title:
        text(d, (W // 2, 25), title, 28, bold=True, anchor="mm")
    slot = (right - left) / n
    for i, v in enumerate(values):
        x0 = left + slot * i + slot * 0.18
        x1 = left + slot * (i + 1) - slot * 0.18
        y = bottom - (bottom - top) * v / top_val
        col = (colors[i] if colors else (60, 100, 200))
        d.rectangle((x0, y, x1, bottom), fill=col)
        if labels:
            text(d, ((x0 + x1) / 2, bottom + 25), labels[i], 28, bold=True, anchor="mm")
    if threshold is not None:
        y = bottom - (bottom - top) * threshold / top_val
        for x in range(left, right, 16):
            d.line((x, y, x + 8, y), fill=(200, 0, 0), width=3)
    return im


def make_charts():
    names = ["A", "B", "C", "D"]
    for i in range(14):                                     # highest bar
        r = rng_for("barmax%d" % i)
        vals = r.sample(range(20, 100, 5), 4)
        im = bar_chart(vals, labels=names, title="Monthly sales" if i % 2 else None)
        best = names[vals.index(max(vals))]
        pick(im, "chart", ["max", "read"], "Which bar is the tallest?", "いちばん高い棒はどれですか？",
             best, best, [n for n in names if n != best], [n for n in names if n != best])
    for i in range(14):                                     # trend
        r = rng_for("trend%d" % i)
        up = i % 2 == 0
        base = sorted(r.sample(range(15, 95, 7), 5), reverse=not up)
        im = bar_chart(base, colors=[COLORS["blue"]] * 5)
        yesno(im, "chart", ["trend"], "The values rise from left to right", "値は左から右に向かって増えている", up)
    for i in range(12):                                     # threshold crossing count
        r = rng_for("thr%d" % i)
        vals = [r.randrange(20, 95) for _ in range(5)]
        thr = r.randrange(40, 70)
        if any(abs(v - thr) < 6 for v in vals):
            vals = [v + 8 if abs(v - thr) < 6 else v for v in vals]
        above = sum(v > thr for v in vals)
        im = bar_chart(vals, threshold=thr, labels=list("12345"))
        pool = [0, 1, 2, 3, 4, 5]
        pick(im, "chart", ["count", "threshold"], "How many bars rise above the red dashed line?",
             "赤い点線より高い棒は何本ありますか？", str(above), str(above), wrong_ints(above, pool, 3, r), wrong_ints(above, pool, 3, r),
             difficulty="hard")
    for i in range(12):                                     # line chart end comparison
        r = rng_for("line%d" % i)
        im, d = canvas((255, 255, 255))
        d.line((60, 40, 60, 410), fill=(0, 0, 0), width=2)
        d.line((60, 410, 600, 410), fill=(0, 0, 0), width=2)
        ends = {}
        for col in ("red", "blue"):
            ys = [r.randrange(80, 380) for _ in range(6)]
            pts = [(60 + 90 * k + 20, ys[k]) for k in range(6)]
            d.line(pts, fill=COLORS[col], width=5)
            ends[col] = ys[-1]
        if abs(ends["red"] - ends["blue"]) < 25:
            continue
        higher = "red" if ends["red"] < ends["blue"] else "blue"
        other = "blue" if higher == "red" else "red"
        pick(im, "chart", ["compare", "line"], "Which line ends higher at the right edge?", "右端でより高い位置にある線はどちらですか？",
             higher, NAMES_JA[higher], [other, "they end at the same height"], [NAMES_JA[other], "同じ高さで終わる"])
    for i in range(12):                                     # pie chart largest slice
        r = rng_for("pie%d" % i)
        cols = r.sample(["red", "blue", "green", "yellow", "orange", "purple"], 4)
        parts = [r.randrange(8, 40) for _ in range(4)]
        if sorted(parts)[-1] - sorted(parts)[-2] < 6:
            parts[parts.index(max(parts))] += 8
        tot = sum(parts)
        im, d = canvas((255, 255, 255))
        ang = -90.0
        for p, c in zip(parts, cols):
            d.pieslice((140, 40, 500, 400), ang, ang + 360 * p / tot, fill=COLORS[c], outline=(255, 255, 255), width=2)
            ang += 360 * p / tot
        best = cols[parts.index(max(parts))]
        rest = [c for c in cols if c != best]
        pick(im, "chart", ["pie", "max"], "Which colour is the largest slice of the pie?", "円グラフでいちばん大きい扇形は何色ですか？",
             best, NAMES_JA[best], rest, [NAMES_JA[c] for c in rest])


# ---------------------------------------------------------------------------------------- dashboards

def traffic_light(lit: str):
    im, d = canvas()
    d.rounded_rectangle((240, 30, 400, 450), 30, fill=(40, 40, 40))
    for k, c in enumerate(("red", "yellow", "green")):
        cy = 110 + k * 125
        col = COLORS[c] if c == lit else (70, 70, 70)
        d.ellipse((275, cy - 45, 365, cy + 45), fill=col)
    return im


def gauge_bar(frac: float, vertical=False, battery=False):
    im, d = canvas()
    if battery:
        d.rectangle((120, 150, 500, 330), outline=(0, 0, 0), width=8)
        d.rectangle((500, 205, 530, 275), fill=(0, 0, 0))
        col = COLORS["green"] if frac > 0.5 else COLORS["orange"] if frac > 0.2 else COLORS["red"]
        d.rectangle((130, 160, 130 + 360 * frac, 320), fill=col)
    else:
        d.rounded_rectangle((60, 190, 580, 290), 20, outline=(0, 0, 0), width=5)
        d.rounded_rectangle((66, 196, 66 + 508 * frac, 284), 16, fill=COLORS["blue"])
    return im


def status_grid(reds: int, rng):
    im, d = canvas((30, 34, 40))
    cells = list(range(20))
    rng.shuffle(cells)
    red_set = set(cells[:reds])
    for k in range(20):
        cx, cy = 60 + (k % 5) * 110, 60 + (k // 5) * 100
        d.rounded_rectangle((cx, cy, cx + 90, cy + 80), 10, fill=COLORS["red"] if k in red_set else COLORS["green"])
    return im


def make_dashboards():
    order = ["red", "yellow", "green"]
    for i in range(15):                                     # traffic light
        lit = order[i % 3]
        pick(traffic_light(lit), "dashboard", ["status", "light"], "Which light is lit?", "点灯しているのはどの色ですか？",
             lit, NAMES_JA[lit], [c for c in order if c != lit], [NAMES_JA[c] for c in order if c != lit], difficulty="easy")
    levels_en = ["empty or almost empty", "low", "medium", "high", "full or almost full"]
    levels_ja = ["空かほぼ空", "低い", "中程度", "高い", "満タンかほぼ満タン"]
    for i in range(15):                                     # progress bar level (score)
        r = rng_for("gauge%d" % i)
        frac = [0.04, 0.2, 0.5, 0.78, 0.97][i % 5] + r.uniform(-0.03, 0.03)
        frac = min(max(frac, 0.0), 1.0)
        idx = [0.04, 0.2, 0.5, 0.78, 0.97].index([0.04, 0.2, 0.5, 0.78, 0.97][i % 5])
        add("dashboard", ["gauge", "level"], gauge_bar(frac, battery=(i % 2 == 1)), "score",
            {"instr": "How full is the %s?" % ("battery" if i % 2 else "progress bar"), "levels": levels_en},
            {"instr": "%sはどのくらい満たされていますか？" % ("バッテリー" if i % 2 else "進捗バー"), "levels": levels_ja}, idx)
    for i in range(16):                                     # status grid, count of red tiles
        r = rng_for("grid%d" % i)
        reds = r.randrange(0, 7)
        pool = list(range(0, 9))
        pick(status_grid(reds, r), "dashboard", ["count", "status"], "How many tiles are red?", "赤いタイルはいくつありますか？",
             str(reds), str(reds), wrong_ints(reds, pool, 3, r), wrong_ints(reds, pool, 3, r), difficulty="hard")


# ---------------------------------------------------------------------------------------------- UI

def ui_screen(rng, banner: bool, primary: str, switch_on: bool, buttons=("Save", "Cancel", "Delete")):
    im, d = canvas((255, 255, 255))
    d.rectangle((0, 0, W, 56), fill=(35, 45, 95))
    text(d, (20, 28), "Account settings", 26, (255, 255, 255), True, "lm")
    if banner:
        d.rectangle((30, 76, 610, 136), fill=(255, 228, 228), outline=COLORS["red"], width=3)
        text(d, (50, 106), "Error: could not save changes", 26, (160, 0, 0), True, "lm")
    text(d, (40, 170), "Notifications", 28, anchor="lm")
    d.rounded_rectangle((440, 150, 560, 192), 21, fill=COLORS["green"] if switch_on else (170, 170, 170))
    d.ellipse((518 if switch_on else 444, 154, 556 if switch_on else 482, 188), fill=(255, 255, 255))
    for k, b in enumerate(buttons):
        x0 = 40 + k * 200
        if b == primary:
            d.rounded_rectangle((x0, 330, x0 + 170, 400), 12, fill=COLORS["blue"])
            text(d, (x0 + 85, 365), b, 28, (255, 255, 255), True, "mm")
        else:
            d.rounded_rectangle((x0, 330, x0 + 170, 400), 12, outline=(120, 120, 120), width=3)
            text(d, (x0 + 85, 365), b, 28, (60, 60, 60), False, "mm")
    return im


def make_ui():
    for i in range(16):                                     # error banner
        r = rng_for("ui_banner%d" % i)
        banner = i % 2 == 0
        im = ui_screen(r, banner, r.choice(["Save", "Cancel", "Delete"]), r.random() < 0.5)
        yesno(im, "ui", ["error", "presence"], "An error message is shown on the screen", "画面にエラーメッセージが表示されている", banner,
              difficulty="easy")
    btn = ["Save", "Cancel", "Delete"]
    for i in range(15):                                     # highlighted button
        r = rng_for("ui_primary%d" % i)
        primary = btn[i % 3]
        im = ui_screen(r, r.random() < 0.5, primary, r.random() < 0.5)
        pick(im, "ui", ["button", "agent"], "Which button is highlighted as the primary action?", "主要な操作として強調されているボタンはどれですか？",
             primary, primary, [b for b in btn if b != primary], [b for b in btn if b != primary],
             state_en="Settings page of a web app.", state_ja="Web アプリの設定画面。")
    for i in range(16):                                     # switch state
        r = rng_for("ui_switch%d" % i)
        on = i % 2 == 0
        im = ui_screen(r, False, r.choice(btn), on)
        yesno(im, "ui", ["toggle", "state"], "The notifications switch is turned on", "通知のスイッチはオンになっている", on)
    for i in range(12):                                     # form validation
        r = rng_for("ui_form%d" % i)
        im, d = canvas((255, 255, 255))
        bad = r.sample(range(4), r.choice([0, 1, 1, 2]))
        for k, label in enumerate(["Name", "Email", "Phone", "City"]):
            y = 40 + k * 100
            text(d, (50, y), label, 22, (80, 80, 80))
            d.rectangle((50, y + 30, 590, y + 78), outline=COLORS["red"] if k in bad else (150, 150, 150), width=4 if k in bad else 2)
        yesno(im, "ui", ["form", "validation"], "At least one field is marked with a red outline", "赤い枠で示されている入力欄が少なくとも 1 つある",
              bool(bad), state_en="A form after the user pressed Submit.", state_ja="送信ボタンを押した後のフォーム。")
    for i in range(12):                                     # checkboxes
        r = rng_for("ui_check%d" % i)
        im, d = canvas((255, 255, 255))
        n_checked = r.randrange(0, 5)
        checked = set(r.sample(range(4), n_checked))
        for k, label in enumerate(["Tests", "Review", "Docs", "Deploy"]):
            y = 70 + k * 90
            d.rectangle((90, y, 140, y + 50), outline=(40, 40, 40), width=4)
            if k in checked:
                d.line((98, y + 26, 114, y + 42), fill=COLORS["green"], width=7)
                d.line((114, y + 42, 134, y + 8), fill=COLORS["green"], width=7)
            text(d, (170, y + 25), label, 30, anchor="lm")
        pick(im, "ui", ["checklist", "count"], "How many checklist items are ticked?", "チェックされている項目はいくつありますか？",
             str(n_checked), str(n_checked), wrong_ints(n_checked, [0, 1, 2, 3, 4], 3, r), wrong_ints(n_checked, [0, 1, 2, 3, 4], 3, r))


# ------------------------------------------------------------------------------------------ documents

def receipt(items, total_text, paid=False, rng=None):
    im, d = canvas((255, 255, 250))
    text(d, (W // 2, 36), "CORNER MARKET", 30, bold=True, anchor="mm")
    y = 90
    for name, price in items:
        text(d, (60, y), name, 26)
        text(d, (580, y), price, 26, anchor="ra")
        y += 46
    d.line((60, y + 4, 580, y + 4), fill=(0, 0, 0), width=2)
    text(d, (60, y + 24), "TOTAL", 30, bold=True)
    text(d, (580, y + 24), total_text, 30, bold=True, anchor="ra")
    if paid:
        d.rounded_rectangle((330, 330, 590, 420), 10, outline=COLORS["red"], width=6)
        text(d, (460, 375), "PAID", 48, COLORS["red"], True, "mm")
    return im


def make_documents():
    goods = ["Milk", "Bread", "Eggs", "Apples", "Rice", "Tea", "Soap", "Salt"]
    for i in range(16):                                     # receipt total
        r = rng_for("receipt%d" % i)
        picks = r.sample(goods, 3)
        prices = [round(r.uniform(1.2, 9.9), 2) for _ in picks]
        tot = round(sum(prices), 2)
        items = [(g, "%.2f" % p) for g, p in zip(picks, prices)]
        im = receipt(items, "%.2f" % tot, paid=False)
        wrong = []
        while len(wrong) < 3:
            c = round(tot + r.choice([-3, -1.5, 1.2, 2.5, 4, 0.9]), 2)
            if "%.2f" % c != "%.2f" % tot and "%.2f" % c not in wrong and c > 0:
                wrong.append("%.2f" % c)
        pick(im, "document", ["receipt", "read"], "What is the total on the receipt?", "レシートの合計金額はいくらですか？",
             "%.2f" % tot, "%.2f" % tot, wrong, wrong, difficulty="hard")
    for i in range(16):                                     # paid stamp
        r = rng_for("stamp%d" % i)
        paid = i % 2 == 0
        picks = r.sample(goods, 3)
        items = [(g, "%.2f" % r.uniform(1.2, 9.9)) for g in picks]
        im = receipt(items, "%.2f" % sum(float(p) for _, p in items), paid=paid)
        yesno(im, "document", ["stamp", "presence"], "The document carries a PAID stamp", "この書類には「PAID」のスタンプが押されている", paid,
              difficulty="easy", state_en="An invoice scan.", state_ja="請求書のスキャン。")
    people = ["Ana", "Ben", "Cho", "Dev", "Eli"]
    for i in range(16):                                     # table: highest value
        r = rng_for("table%d" % i)
        vals = r.sample(range(10, 99), 5)
        im, d = canvas((255, 255, 255))
        d.rectangle((40, 30, 600, 90), fill=(225, 230, 245))
        text(d, (70, 60), "Name", 28, bold=True, anchor="lm")
        text(d, (540, 60), "Score", 28, bold=True, anchor="rm")
        for k, (p, v) in enumerate(zip(people, vals)):
            y = 90 + k * 62
            d.line((40, y + 62, 600, y + 62), fill=(190, 190, 190), width=2)
            text(d, (70, y + 31), p, 28, anchor="lm")
            text(d, (540, y + 31), str(v), 28, anchor="rm")
        best = people[vals.index(max(vals))]
        pick(im, "document", ["table", "max"], "Who has the highest score in the table?", "表でスコアがいちばん高いのは誰ですか？",
             best, best, [p for p in people if p != best][:3], [p for p in people if p != best][:3])
    for i in range(12):                                     # calendar circled date
        r = rng_for("cal%d" % i)
        im, d = canvas((255, 255, 255))
        text(d, (W // 2, 30), "Week", 28, bold=True, anchor="mm")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        pos = r.randrange(5)
        for k, dn in enumerate(days):
            x = 40 + k * 112
            d.rectangle((x, 70, x + 100, 400), outline=(150, 150, 150), width=2)
            text(d, (x + 50, 100), dn, 26, bold=True, anchor="mm")
            if k == pos:
                d.ellipse((x + 8, 170, x + 92, 254), outline=COLORS["red"], width=6)
            text(d, (x + 50, 212), str(10 + k), 30, anchor="mm")
        pick(im, "document", ["calendar", "read"], "Which weekday is circled in red?", "赤で丸が付けられているのは何曜日ですか？",
             days[pos], days[pos], [x for x in days if x != days[pos]][:3], [x for x in days if x != days[pos]][:3])


# -------------------------------------------------------------------------------------------- reasoning

def scatter_shapes(rng, n, shape="circle", color="red", others=0, other_shapes=("square", "triangle")):
    im, d = canvas((255, 255, 255))
    placed = []

    def free(x, y, s):
        return all(abs(x - px) > s + ps + 10 or abs(y - py) > s + ps + 10 for px, py, ps in placed)

    def draw(kind, c, x, y, s):
        if kind == "circle":
            d.ellipse((x - s, y - s, x + s, y + s), fill=COLORS[c])
        elif kind == "square":
            d.rectangle((x - s, y - s, x + s, y + s), fill=COLORS[c])
        else:
            d.polygon([(x, y - s), (x - s, y + s), (x + s, y + s)], fill=COLORS[c])

    for kind, c, count in [(shape, color, n)] + [(rng.choice(other_shapes), rng.choice([k for k in COLORS if k != color and k not in ("black", "grey")]), others)]:
        before = len(placed)
        for _ in range(count):
            for _try in range(200):
                s = rng.randrange(26, 40)
                x, y = rng.randrange(60, W - 60), rng.randrange(60, H - 60)
                if free(x, y, s):
                    placed.append((x, y, s))
                    draw(kind, c, x, y, s)
                    break
        if len(placed) - before != count:
            raise RuntimeError("could not place %d %s %ss" % (count, c, kind))
    return im


def make_reasoning():
    for i in range(18):                                     # count shapes
        r = rng_for("count%d" % i)
        n = r.randrange(1, 6)
        im = scatter_shapes(r, n, "circle", "red", others=r.randrange(0, 3))
        pool = [1, 2, 3, 4, 5, 6]
        pick(im, "reasoning", ["count"], "How many red circles are there?", "赤い円はいくつありますか？",
             str(n), str(n), wrong_ints(n, pool, 3, r), wrong_ints(n, pool, 3, r), difficulty="hard" if n > 3 else "medium")
    for i in range(18):                                     # left / right
        r = rng_for("lr%d" % i)
        im, d = canvas((255, 255, 255))
        left_red = i % 2 == 0
        xr, xb = (150, 470) if left_red else (470, 150)
        y1, y2 = r.randrange(130, 350), r.randrange(130, 350)
        d.rectangle((xr - 50, y1 - 50, xr + 50, y1 + 50), fill=COLORS["red"])
        d.ellipse((xb - 50, y2 - 50, xb + 50, y2 + 50), fill=COLORS["blue"])
        yesno(im, "reasoning", ["position"], "The red square is to the left of the blue circle", "赤い四角は青い円の左側にある", left_red)
    for i in range(14):                                     # largest shape
        r = rng_for("big%d" % i)
        cols = r.sample(["red", "blue", "green", "yellow", "orange", "purple"], 3)
        sizes = r.sample([40, 60, 85], 3)
        im, d = canvas((255, 255, 255))
        for k, (c, s) in enumerate(zip(cols, sizes)):
            cx = 120 + k * 200
            d.ellipse((cx - s, 240 - s, cx + s, 240 + s), fill=COLORS[c])
        best = cols[sizes.index(max(sizes))]
        rest = [c for c in cols if c != best]
        pick(im, "reasoning", ["size"], "Which coloured circle is the largest?", "いちばん大きい円は何色ですか？",
             best, NAMES_JA[best], rest + ["they are the same size"], [NAMES_JA[c] for c in rest] + ["すべて同じ大きさ"])
    for i in range(14):                                     # odd one out
        r = rng_for("odd%d" % i)
        a, b = r.sample(["red", "blue", "green", "orange", "purple"], 2)
        im, d = canvas((255, 255, 255))
        odd = r.randrange(6)
        for k in range(6):
            cx, cy = 110 + (k % 3) * 210, 150 + (k // 3) * 190
            d.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), fill=COLORS[b if k == odd else a])
        pick(im, "reasoning", ["odd-one-out", "colour"], "Which colour is the one circle that differs from the others?",
             "他と違う 1 つの円は何色ですか？", b, NAMES_JA[b], [x for x in [a, "yellow", "grey"] if x != b][:3],
             [NAMES_JA[x] for x in [a, "yellow", "grey"] if x != b][:3], difficulty="hard")
    dirs = {"up": "上", "down": "下", "left": "左", "right": "右"}
    for i in range(16):                                     # arrow direction
        r = rng_for("arrow%d" % i)
        dr = list(dirs)[i % 4]
        im, d = canvas((255, 255, 255))
        cx, cy = 320, 240
        pts = {"up": [(cx, cy - 150), (cx - 90, cy - 20), (cx + 90, cy - 20)], "down": [(cx, cy + 150), (cx - 90, cy + 20), (cx + 90, cy + 20)],
               "left": [(cx - 150, cy), (cx - 20, cy - 90), (cx - 20, cy + 90)], "right": [(cx + 150, cy), (cx + 20, cy - 90), (cx + 20, cy + 90)]}[dr]
        d.polygon(pts, fill=COLORS[r.choice(["red", "blue", "green"])])
        pick(im, "reasoning", ["arrow"], "Which way does the arrow point?", "矢印はどちらを向いていますか？",
             dr, dirs[dr], [x for x in dirs if x != dr], [dirs[x] for x in dirs if x != dr], difficulty="easy")
    for i in range(14):                                     # sorted
        r = rng_for("sorted%d" % i)
        vals = r.sample(range(15, 95, 5), 5)
        asc = i % 2 == 0
        if asc:
            vals = sorted(vals)
        else:
            while vals == sorted(vals):
                r.shuffle(vals)
        yesno(bar_chart(vals, colors=[COLORS["purple"]] * 5), "reasoning", ["order"], "The bars are arranged from shortest to tallest, left to right",
              "棒は左から右へ、低いものから高いものの順に並んでいる", asc, difficulty="medium")


# ------------------------------------------------------------------------------------------- field/safety

def floor_plan(exit_side: str):
    im, d = canvas((255, 255, 255))
    d.rectangle((90, 60, 550, 420), outline=(0, 0, 0), width=8)
    box = {"left": (70, 190, 110, 290), "right": (530, 190, 570, 290), "top": (270, 40, 370, 80), "bottom": (270, 400, 370, 440)}[exit_side]
    d.rectangle(box, fill=COLORS["green"])
    text(d, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), "EXIT", 20, (255, 255, 255), True, "mm")
    d.ellipse((300, 220, 340, 260), fill=COLORS["blue"])
    return im


def sign(kind: str, rng):
    im, d = canvas((255, 255, 255))
    cx, cy = 320, 240
    if kind == "warning":
        d.polygon([(cx, 50), (cx - 190, 400), (cx + 190, 400)], fill=COLORS["yellow"], outline=(0, 0, 0))
        text(d, (cx, 300), "!", 150, (0, 0, 0), True, "mm")
    elif kind == "prohibition":
        d.ellipse((cx - 170, cy - 170, cx + 170, cy + 170), fill=(255, 255, 255), outline=COLORS["red"], width=26)
        d.line((cx - 120, cy - 120, cx + 120, cy + 120), fill=COLORS["red"], width=26)
    elif kind == "mandatory":
        d.ellipse((cx - 170, cy - 170, cx + 170, cy + 170), fill=COLORS["blue"])
        text(d, (cx, cy), "ok", 130, (255, 255, 255), True, "mm")
    else:
        d.rectangle((cx - 170, cy - 170, cx + 170, cy + 170), fill=COLORS["green"])
        text(d, (cx, cy), "i", 190, (255, 255, 255), True, "mm")
    return im


def make_field():
    for i in range(16):                                     # exit side
        side = ["left", "right", "top", "bottom"][i % 4]
        ja = {"left": "左", "right": "右", "top": "上", "bottom": "下"}
        pick(floor_plan(side), "field", ["map", "exit"], "On which side of the room is the green EXIT?", "緑の「EXIT」は部屋のどの側にありますか？",
             side, ja[side], [s for s in ja if s != side], [ja[s] for s in ja if s != side], difficulty="easy",
             state_en="Floor plan of one room.", state_ja="1 つの部屋の平面図。")
    kinds = {"warning": ("a warning sign (yellow triangle)", "警告標識（黄色い三角形）"),
             "prohibition": ("a prohibition sign (red circle with a slash)", "禁止標識（斜線入りの赤い円）"),
             "mandatory": ("a mandatory-action sign (blue circle)", "指示標識（青い円）"),
             "info": ("an information sign (green square)", "案内標識（緑の四角形）")}
    for i in range(20):                                     # sign type
        r = rng_for("sign%d" % i)
        k = list(kinds)[i % 4]
        pick(sign(k, r), "field", ["sign", "safety"], "What kind of sign is this?", "これはどの種類の標識ですか？",
             kinds[k][0], kinds[k][1], [kinds[x][0] for x in kinds if x != k], [kinds[x][1] for x in kinds if x != k])
    for i in range(14):                                     # PPE checklist score by count of green ticks
        r = rng_for("ppe%d" % i)
        im, d = canvas((255, 255, 255))
        n = r.randrange(0, 5)
        ok = set(r.sample(range(4), n))
        for k, label in enumerate(["Helmet", "Gloves", "Vest", "Boots"]):
            y = 70 + k * 90
            d.ellipse((90, y, 140, y + 50), fill=COLORS["green"] if k in ok else COLORS["red"])
            text(d, (115, y + 25), "OK" if k in ok else "X", 22, (255, 255, 255), True, "mm")
            text(d, (170, y + 25), label, 30, anchor="lm")
        levels_en = ["none ready", "one ready", "two ready", "three ready", "all four ready"]
        levels_ja = ["準備できているものはない", "1 つ準備できている", "2 つ準備できている", "3 つ準備できている", "4 つすべて準備できている"]
        add("field", ["ppe", "triage"], im, "score", {"instr": "How many protective items are marked OK?", "levels": levels_en},
            {"instr": "OK と示されている保護具はいくつですか？", "levels": levels_ja}, n, difficulty="hard")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("syn-*.png"):
        f.unlink()
    for make in (make_charts, make_dashboards, make_ui, make_documents, make_reasoning, make_field):
        make()
    with JSONL.open("w", encoding="utf-8") as fh:
        for row in ITEMS:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    by = {}
    for row in ITEMS:
        by[row["tags"][1]] = by.get(row["tags"][1], 0) + 1
    print("wrote %d items (%s) to %s" % (len(ITEMS), ", ".join("%s %d" % kv for kv in sorted(by.items())), JSONL))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
