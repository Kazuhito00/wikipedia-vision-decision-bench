# -*- coding: utf-8 -*-
"""Japanese-specific v1 questions (tag ``ja_specific``, ids biz-2001..): pictures with Japanese text drawn by this script.

    python datasets/synthetic/gen_v1_ja.py            # dry run: builds everything in memory, prints a summary
    python datasets/synthetic/gen_v1_ja.py --apply    # writes work/generated/<id>.png (+ px224/<id>.png) and
                                                      # datasets/questions/v1/new_ja_specific.jsonl

Every row is lang "ja" / langs ["ja"] (no English side). Deterministic: each builder has its own random.Random seeded from its
name. The right answer is always computed from the drawing parameters (the totals, the weekday of a date, the number of ticked boxes,
the level of a gauge ...), never typed in next to the picture; ``verify()`` re-derives a few of them a second way.

Fonts (the text in the pictures): Noto Sans JP and Noto Serif JP (variable fonts, SIL Open Font License 1.1), found in the Windows
font folder of this machine (C:\\Windows\\Fonts\\NotoSansJP-VF.ttf / NotoSerifJP-VF.ttf). Only the pictures are a product of this
script; the font files are never copied into the repository or a release. Meiryo / Yu Gothic / MS Gothic are NOT used.
All shop, company, station and person names are invented.
"""
from __future__ import annotations

import argparse
import calendar
import datetime
import json
import math
import pathlib
import random
import sys
import zlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "work" / "generated"
JSONL = ROOT / "datasets" / "questions" / "v1" / "new_ja_specific.jsonl"
FONT_DIR = pathlib.Path(r"C:\Windows\Fonts")
SANS, SERIF = FONT_DIR / "NotoSansJP-VF.ttf", FONT_DIR / "NotoSerifJP-VF.ttf"
FIRST_ID = 2001
W, H = 640, 480

PAPER = (250, 247, 238)
INK = (28, 28, 32)
RED = (200, 40, 40)
BLUE = (30, 80, 190)
GREEN = (30, 130, 70)
GREY = (120, 120, 120)
WDAY = "月火水木金土日"          # calendar.weekday(): 0 = Monday

_fc = {}


def F(size, w=500, serif=False):
    key = (size, w, serif)
    if key not in _fc:
        f = ImageFont.truetype(str(SERIF if serif else SANS), size)
        f.set_variation_by_axes([w if not serif else max(200, min(900, w))])
        _fc[key] = f
    return _fc[key]


def T(d, xy, s, size=36, fill=INK, w=500, anchor="la", serif=False):
    d.text(xy, s, font=F(size, w, serif), fill=fill, anchor=anchor)


def tw(s, size, w=500, serif=False):
    return F(size, w, serif).getlength(s)


def fit(s, maxw, size, w=500, serif=False):
    while size > 12 and tw(s, size, w, serif) > maxw:
        size -= 2
    return size


def vtext(d, xc, yt, s, size, fill=INK, w=500, serif=False, step=1.1):
    """Vertical writing: one character per cell, top to bottom, centred on x = xc. (Avoid the long vowel mark and brackets.)"""
    y = yt
    for ch in s:
        if ch in "、。":
            d.text((xc + size * 0.55, y - size * 0.45), ch, font=F(size, w, serif), fill=fill, anchor="ma")
        else:
            d.text((xc, y), ch, font=F(size, w, serif), fill=fill, anchor="ma")
        y += size * step
    return y


def canvas(bg=PAPER):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def era_of(y):
    if y >= 2019:
        return "令和", y - 2018
    if y >= 1989:
        return "平成", y - 1988
    return "昭和", y - 1925


def jdate(y, m, d):
    e, n = era_of(y)
    return "%s%d年%d月%d日" % (e, n, m, d)


def yen(n):
    return "{:,}円".format(n)


def box(d, xy, fill=None, outline=INK, width=3, r=0):
    if r:
        d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=width)
    else:
        d.rectangle(xy, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------------------------------------------------------- registry
BUILDERS = []


def reg(pattern, itype):
    def deco(fn):
        BUILDERS.append((fn.__name__, pattern, itype, fn))
        return fn
    return deco


def choice(instr, correct, wrong, skill, difficulty="medium", tags=()):
    assert correct not in wrong and len(set(wrong)) == len(wrong), (instr, correct, wrong)
    return dict(kind="choice", ja={"instr": instr, "correct": correct, "wrong": list(wrong)}, skill=skill, difficulty=difficulty,
                tags=list(tags), fmt="choice:%d" % (len(wrong) + 1))


def yesno(instr, truth, skill, difficulty="easy", tags=()):
    return dict(kind="noul", ja={"instr": instr}, answer=bool(truth), skill=skill, difficulty=difficulty, tags=list(tags), fmt="yesno")


def score(instr, levels, ans, skill, difficulty="medium", tags=()):
    assert 0 <= ans < len(levels)
    return dict(kind="score", ja={"instr": instr, "levels": list(levels)}, answer=ans, skill=skill, difficulty=difficulty,
                tags=list(tags), fmt="score:%d" % len(levels))


def rng_of(name):
    return random.Random(zlib.crc32(name.encode()))


def pick_wrong(rng, pool, correct, k):
    c = [p for p in pool if p != correct]
    rng.shuffle(c)
    return c[:k]


# ================================================================================================ A. 領収書・請求書
SHOPS = ["喫茶 みなと", "そば処 つむぎ庵", "ひなた書店", "ベーカリー こむぎ", "旅館 せせらぎ", "あおば電機", "寿司処 なぎさ", "星野クリーニング"]
COMPANIES = ["有限会社 北斗工務店", "株式会社 あおば商事", "株式会社 みなと運輸", "有限会社 ひかり電機"]
PROVISO = ["お食事代", "宿泊料", "書籍代", "修理代", "会費", "コピー用紙代", "クリーニング代", "製本代"]


def draw_receipt(shop, y, m, d, to, amount, proviso, tax=None, stamp=None, seal=True, show_to=True, show_date=True,
                 show_amount=True, show_proviso=True, show_issuer=True, note=None, serif=False):
    """tax: None | ("税抜", base, rate, taxamount).  stamp: None | True (a revenue-stamp box is drawn)."""
    im, dr = canvas((232, 232, 226))
    box(dr, (24, 16, 616, 464), fill=(255, 255, 252), outline=(150, 150, 140), width=3)
    T(dr, (320, 52), "領 収 書", 46, INK, 800, "mm", serif=serif)
    if show_date:
        T(dr, (600, 98), jdate(y, m, d), 28, INK, 500, "rm")
    if show_to:
        addr = to if to.endswith("様") else to + " 様"      # one honorific only ("上様" / "... 様" are used as they are)
        T(dr, (48, 124), addr, fit(addr, 400, 36), INK, 500, "la")
        dr.line((48, 168, 450, 168), fill=INK, width=2)
    if show_amount:
        box(dr, (48, 176, 430, 246), outline=INK, width=3)
        T(dr, (62, 211), "¥{:,}-".format(amount), 46, INK, 800, "lm")
        if note:
            T(dr, (420, 236), note, 24, GREY, 500, "rd")
    if stamp:
        box(dr, (466, 176, 592, 262), outline=GREY, width=2)
        T(dr, (529, 219), "収入印紙", 24, GREY, 500, "mm")
        dr.line((466, 176, 592, 262), fill=(215, 215, 210), width=1)
    if show_proviso:
        T(dr, (48, 270), "但し %sとして" % proviso, fit("但し %sとして" % proviso, 540, 34), INK, 500, "la")
        T(dr, (48, 316), "上記正に領収いたしました", 30, INK, 400, "la")
    if tax:
        _, base, rate, tx = tax
        T(dr, (48, 354), "内訳  税抜金額 {:,}円".format(base), 28, INK, 400, "la")
        T(dr, (48, 384), "消費税等（{}%） {:,}円".format(rate, tx), 28, INK, 400, "la")
    if show_issuer:
        T(dr, (330, 434), shop, fit(shop, 220, 34), INK, 700, "lm")
        if seal:
            dr.ellipse((560, 412, 604, 456), outline=RED, width=3)
            T(dr, (582, 434), "印", 28, RED, 700, "mm")
    return im


@reg("receipt", "document")
def a01(rng):
    shop, comp = rng.choice(SHOPS), "株式会社 あおば商事"
    prov, others = "宿泊料", ["お食事代", "書籍代", "修理代", "会費"]
    im = draw_receipt("旅館 せせらぎ", 2024, 3, 15, comp, 33000, prov, stamp=True)
    return im, choice("この領収書の但し書きはどれですか？", "宿泊料として", [o + "として" for o in others], "ocr", "easy", ["receipt"])


@reg("receipt", "document")
def a02(rng):
    comp = "有限会社 北斗工務店"
    wrong = ["株式会社 北斗工務店", "有限会社 北斗工業", "有限会社 北斗建設", "有限会社 星野工務店"]
    im = draw_receipt("ひなた書店", 2024, 6, 3, comp, 4180, "書籍代")
    return im, choice("この領収書の宛名はどれですか？", comp, wrong, "ocr", "medium", ["receipt"])


@reg("receipt", "document")
def a03(rng):
    y, m, d = 2024, 4, 27
    im = draw_receipt("そば処 つむぎ庵", y, m, d, "上様", 2860, "お食事代")
    ans = "%d年" % y
    return im, choice("この領収書の日付を西暦で表すと、何年ですか？", ans, ["%d年" % (y - 1), "%d年" % (y + 1), "%d年" % (y - 6)], "ocr", "medium", ["receipt", "wareki"])


@reg("receipt", "document")
def a04(rng):
    y, m, d = 2017, 11, 8
    im = draw_receipt("星野クリーニング", y, m, d, "青柳 修 様", 1760, "クリーニング代")
    # 平成29年 -> 2017
    return im, choice("この領収書の日付を西暦で表すと、何年ですか？", "%d年" % y, ["%d年" % (y - 1), "%d年" % (y + 1)], "ocr", "medium", ["receipt", "wareki"])


@reg("receipt", "document")
def a05(rng):
    base, rate = 5000, 8
    tx = base * rate // 100
    im = draw_receipt("ベーカリー こむぎ", 2024, 9, 14, "柏木 みのり 様", base + tx, "パン代", tax=("税抜", base, rate, tx))
    return im, choice("この領収書の消費税等は、いくらですか？", yen(tx), [yen(base), yen(base + tx), yen(base * 10 // 100)], "quantity", "medium", ["receipt", "tax"])


@reg("receipt", "document")
def a06(rng):
    im = draw_receipt("喫茶 みなと", 2024, 5, 21, "真壁 修 様", 1450, "お食事代", stamp=True)
    return im, yesno("この領収書には、収入印紙を貼る欄がある", True, "recognition", "easy", ["receipt", "stamp"])




@reg("receipt", "document")
def a08(rng):
    im = draw_receipt("寿司処 なぎさ", 2024, 7, 6, "青柳 修 様", 12100, "お食事代", note="（税込）")
    return im, choice("この領収書の金額は、税込と税抜のどちらですか？", "税込", ["税抜"], "ocr", "easy", ["receipt", "tax"])


@reg("receipt", "document")
def a09(rng):
    amt = 38500
    levels = ["999円以下", "1,000〜9,999円", "10,000〜99,999円", "100,000〜999,999円", "1,000,000円以上"]
    ans = sum(amt >= t for t in (1000, 10000, 100000, 1000000))
    im = draw_receipt("旅館 せせらぎ", 2024, 10, 2, "柏木 みのり 様", amt, "宿泊料", stamp=True)
    return im, score("この領収書の金額は、どの範囲にありますか？", levels, ans, "quantity", "easy", ["receipt", "level"])


@reg("receipt", "document")
def a10(rng):
    labels = ["宛名", "日付", "金額", "但し書き", "発行者名", "収入印紙欄"]
    miss = "但し書き"
    im = draw_receipt("ひなた書店", 2024, 8, 9, "有限会社 ひかり電機 様", 7260, "書籍代", stamp=True, show_proviso=miss != "但し書き")
    return im, choice("次のうち、この領収書に書かれていないものはどれですか？", miss, [l for l in labels if l != miss], "negation", "medium", ["receipt", "negation"])


@reg("receipt", "document")
def a11(rng):
    im = draw_receipt("そば処 つむぎ庵", 2024, 2, 10, "上様", 1980, "お食事代")
    return im, choice("宛名として書かれている会社名はどれですか？", "該当なし", ["株式会社 あおば商事", "有限会社 北斗工務店", "株式会社 みなと運輸"], "ocr", "medium", ["receipt", "none-of-above"])


def draw_invoice(to, y, m, d, rows, rate, due=None, show_sub=False, show_total=False, sub=None):
    im, dr = canvas((236, 238, 244))
    box(dr, (20, 14, 620, 466), fill=(255, 255, 255), outline=(140, 150, 170), width=3)
    T(dr, (320, 56), "請 求 書", 50, (30, 50, 110), 800, "mm")
    T(dr, (40, 84), to + " 御中", fit(to + " 御中", 520, 34), INK, 500, "la")
    T(dr, (40, 122), "発行日 " + jdate(y, m, d), 24, INK, 400, "la")
    x0 = 40
    dr.rectangle((x0, 150, 600, 186), fill=(215, 222, 240))
    for x, s, a in ((52, "品名", "la"), (330, "数量", "ra"), (450, "単価", "ra"), (590, "金額", "ra")):
        T(dr, (x, 168), s, 26, INK, 600, a[0] + "m")
    yy = 192
    for name, q, u in rows:
        T(dr, (52, yy + 22), name, 30, INK, 500, "lm")
        T(dr, (330, yy + 22), str(q), 30, INK, 500, "rm")
        T(dr, (450, yy + 22), "{:,}".format(u), 30, INK, 500, "rm")
        T(dr, (590, yy + 22), "{:,}".format(q * u), 30, INK, 500, "rm")
        dr.line((x0, yy + 46, 600, yy + 46), fill=(190, 190, 200), width=1)
        yy += 48
    sub = sub if sub is not None else sum(q * u for _, q, u in rows)
    if show_sub:
        T(dr, (590, yy + 22), "小計（税抜） {:,}円".format(sub), 30, INK, 500, "rm")
        T(dr, (590, yy + 66), "消費税（{}%） {:,}円".format(rate, sub * rate // 100), 30, INK, 500, "rm")
        yy += 88
    if show_total:
        T(dr, (590, yy + 22), "合計（税込） {:,}円".format(sub + sub * rate // 100), 32, INK, 700, "rm")
    else:
        T(dr, (40, 404), "※ 表の金額は税抜です。消費税は %d%% です。" % rate, 26, RED, 500, "lm")
    if due:
        T(dr, (40, 440), "お支払期限 " + jdate(*due), 28, INK, 600, "lm")
    return im


@reg("invoice", "document")
def a12(rng):
    rows = [("コピー用紙（箱）", 2, 1800), ("ボールペン", 10, 120), ("ファイル", 5, 300)]
    im = draw_invoice("株式会社 あおば商事", 2024, 4, 1, rows, 10)
    sub = sum(q * u for _, q, u in rows)
    tot = sub + sub * 10 // 100
    return im, choice("消費税10%を含めた請求額は、いくらですか？", yen(tot), [yen(sub), yen(tot + 330), yen(tot - 330)], "quantity", "hard", ["invoice", "tax"])


@reg("invoice", "document")
def a13(rng):
    rows = [("製本代", 1, 4200), ("印刷代", 3, 900)]
    im = draw_invoice("有限会社 ひかり電機", 2024, 3, 31, rows, 10, due=(2024, 4, 30), show_sub=True)
    due = (2024, 4, 30)
    wrong = [jdate(2024, 3, 31), jdate(2024, 5, 31)]
    return im, choice("この請求書のお支払期限は、いつですか？", jdate(*due), wrong, "ocr", "medium", ["invoice", "wareki"])


# ================================================================================================ B. 時刻表・路線図
DEST = ["海浜公園", "みどり野", "桜台", "若葉町", "港北", "白浜"]
KIND_COL = {"普通": (40, 140, 70), "快速": (230, 130, 20), "急行": (200, 40, 40)}


TT_ALT = {"みどり野": "白浜", "桜台": "港北", "海浜公園": "若葉町"}


def draw_timetable(station, deps, now=None, title="平日・上り"):
    im, dr = canvas((245, 248, 252))
    dr.rectangle((0, 0, W, 76), fill=(24, 70, 150))
    T(dr, (24, 38), station + "駅 時刻表", 38, (255, 255, 255), 700, "lm")
    T(dr, (616, 38), title, 28, (255, 255, 255), 500, "rm")
    y = 88
    for t, k, dst in deps:
        T(dr, (36, y + 24), "%d:%02d" % t, 40, INK, 700, "lm")
        dr.rounded_rectangle((176, y + 5, 268, y + 45), 10, fill=KIND_COL[k])
        T(dr, (222, y + 25), k, 28, (255, 255, 255), 700, "mm")
        shown = TT_ALT.get(dst, dst) if dst == station else dst      # never "this station" as its own destination
        T(dr, (290, y + 24), shown + " 行き", 36, INK, 500, "lm")
        dr.line((24, y + 50, 616, y + 50), fill=(200, 205, 215), width=1)
        y += 52
    if now:
        dr.rounded_rectangle((24, 418, 616, 470), 12, fill=(255, 244, 200), outline=(200, 160, 40), width=3)
        T(dr, (320, 444), "ただいまの時刻  %d:%02d" % now, 34, INK, 700, "mm")
    return im


def make_deps(rng, n=6, start=(7, 5), kinds=("普通", "快速"), dests=DEST[:3]):
    t = start[0] * 60 + start[1]
    out = []
    for _ in range(n):
        out.append(((t // 60, t % 60), rng.choice(kinds), rng.choice(dests)))
        t += rng.randint(9, 19)
    return out


def fmt(t):
    return "%d:%02d" % t


@reg("timetable", "document")
def b01(rng):
    deps = make_deps(rng)
    now = (deps[1][0][0], deps[1][0][1] + 3)
    im = draw_timetable("みどり野", deps, now)
    nxt = deps[2][0]
    return im, choice("ただいまの時刻のあと、いちばん早く発車するのは何時何分発ですか？", fmt(nxt), [fmt(deps[1][0]), fmt(deps[3][0]), fmt(deps[4][0])], "compare", "easy", ["timetable"])


@reg("timetable", "document")
def b02(rng):
    deps = [((8, 2), "普通", "海浜公園"), ((8, 15), "快速", "桜台"), ((8, 27), "普通", "海浜公園"), ((8, 40), "普通", "桜台"), ((8, 52), "快速", "海浜公園"), ((9, 4), "普通", "海浜公園")]
    im = draw_timetable("若葉町", deps)
    n = sum(1 for _, _, dst in deps if dst == "海浜公園")
    return im, choice("海浜公園行きは、この時刻表に何本ありますか？", "%d本" % n, ["%d本" % x for x in (n - 1, n + 1, n + 2)], "count", "easy", ["timetable", "count"])


@reg("timetable", "document")
def b03(rng):
    deps = make_deps(rng, kinds=("普通", "快速"))
    deps[3] = (deps[3][0], "快速", deps[3][2])
    im = draw_timetable("桜台", deps, title="休日・下り")
    return im, yesno("この時刻表には、快速が含まれている", any(k == "快速" for _, k, _ in deps), "recognition", "easy", ["timetable"])




@reg("timetable", "document")
def b05(rng):
    deps = [((7, 41), "急行", "海浜公園"), ((7, 53), "普通", "桜台"), ((8, 10), "急行", "海浜公園"), ((8, 22), "普通", "若葉町"), ((8, 35), "普通", "桜台"), ((8, 48), "快速", "海浜公園")]
    now = (8, 14)
    im = draw_timetable("みどり野", deps, now)
    later = [t for t, k, _ in deps if t > now and k == "急行"]
    assert not later
    wrong = [fmt(t) for t, k, _ in deps if t > now][:3]
    return im, choice("ただいまの時刻のあと、いちばん早く発車する急行は何時何分発ですか？", "該当なし", wrong, "rules", "hard", ["timetable", "none-of-above"])


@reg("timetable", "document")
def b06(rng):
    deps = [((9, 5), "普通", "海浜公園"), ((9, 18), "普通", "桜台"), ((9, 31), "快速", "若葉町"), ((9, 44), "普通", "桜台"), ((9, 57), "快速", "若葉町"), ((10, 9), "普通", "桜台")]
    im = draw_timetable("白浜", deps)
    shown = {dst for _, _, dst in deps}
    absent = "港北"
    assert absent not in shown
    return im, choice("次のうち、この時刻表に行き先として出ていないものはどれですか？", absent + "行き", [x + "行き" for x in sorted(shown)], "negation", "medium", ["timetable", "negation"])


def draw_hourly(station, rows, dirn="上り"):
    im, dr = canvas((245, 248, 252))
    dr.rectangle((0, 0, W, 70), fill=(24, 110, 90))
    T(dr, (24, 36), station + "駅 " + dirn, 36, (255, 255, 255), 700, "lm")
    T(dr, (616, 36), "平日", 30, (255, 255, 255), 500, "rm")
    n = len(rows)
    h = min(70, (H - 76) // (n + 1))
    dr.rectangle((0, 76, W, 76 + h), fill=(220, 235, 230))
    T(dr, (66, 76 + h // 2), "時", 30, INK, 600, "mm")
    T(dr, (130, 76 + h // 2), "分", 30, INK, 600, "lm")
    y = 76 + h
    for hr, mins in rows:
        T(dr, (66, y + h // 2), str(hr), 44, INK, 700, "mm")
        T(dr, (130, y + h // 2), "  ".join("%02d" % m for m in mins), 40, INK, 500, "lm")
        dr.line((0, y + h, W, y + h), fill=(200, 205, 215), width=1)
        y += h
    return im


@reg("timetable", "document")
def b07(rng):
    rows = [(7, [5, 24, 41, 58]), (8, [10, 22, 35, 49]), (9, [4, 31, 52]), (10, [15, 45]), (11, [8, 38]), (12, [10, 40])]
    im = draw_hourly("みどり野", rows)
    n = len(dict(rows)[9])
    return im, choice("9時台に発車する電車は、何本ですか？", "%d本" % n, ["%d本" % x for x in (2, 4, 5)], "count", "easy", ["timetable", "count"])


@reg("timetable", "document")
def b08(rng):
    rows = [(20, [8, 27, 46]), (21, [5, 24, 50]), (22, [15, 40]), (23, [12, 41])]
    im = draw_hourly("桜台", rows, "下り")
    last = rows[-1][0], rows[-1][1][-1]
    return im, choice("最終電車は、何時何分に発車しますか？", fmt(last), ["23:12", "22:40", "0:12"], "compare", "easy", ["timetable"])




def draw_route(line, stations, transfer=(), start_label=True):
    im, dr = canvas((248, 250, 246))
    dr.rectangle((0, 0, W, 66), fill=(30, 140, 80))
    T(dr, (320, 34), line, 40, (255, 255, 255), 700, "mm")
    n = len(stations)
    xs = [58 + i * (524 // (n - 1)) for i in range(n)]
    ly = 150
    dr.line((xs[0], ly, xs[-1], ly), fill=(30, 140, 80), width=12)
    for i, (x, s) in enumerate(zip(xs, stations)):
        if i in transfer:
            dr.ellipse((x - 17, ly - 17, x + 17, ly + 17), fill=(255, 255, 255), outline=(220, 120, 20), width=7)
            T(dr, (x, ly - 40), "乗換", 24, (200, 100, 10), 700, "mm")
        else:
            dr.ellipse((x - 11, ly - 11, x + 11, ly + 11), fill=(255, 255, 255), outline=(20, 90, 50), width=5)
        vtext(dr, x, ly + 32, s, 38, INK, 600, step=1.12)
    if start_label:
        T(dr, (xs[0], ly - 40), "始発", 24, GREY, 600, "mm")
        T(dr, (xs[-1], ly - 40), "終点", 24, GREY, 600, "mm")
    return im


ST = ["桜台", "若葉町", "港北", "青海", "川原", "白浜", "松原", "双葉", "朝日", "風見", "星野"]


@reg("route-map", "diagram-map")
def b10(rng):
    st = ST[:7]
    im = draw_route("さくら線", st)
    return im, choice("始発駅から数えて4番目の駅は、どこですか？", st[3], [st[2], st[4], st[5]], "spatial", "easy", ["route-map"])


@reg("route-map", "diagram-map")
def b11(rng):
    st = ["朝日", "風見", "星野", "双葉", "松原", "川原", "港北"]
    tr = (2, 5)
    im = draw_route("つばめ線", st, transfer=tr)
    n = len(tr)
    return im, choice("この路線図で、乗換ができる駅はいくつありますか？", "%d駅" % n, ["%d駅" % x for x in (1, 3, 4)], "count", "easy", ["route-map", "count"])


@reg("route-map", "diagram-map")
def b12(rng):
    st = ["青海", "松原", "桜台", "川原", "白浜", "双葉", "若葉町"]
    im = draw_route("かもめ線", st)
    return im, choice("乗換ができる駅は、どこですか？", "該当なし", [st[1], st[3], st[5]], "recognition", "medium", ["route-map", "none-of-above"])


@reg("route-map", "diagram-map")
def b13(rng):
    st = ["星野", "朝日", "風見", "松原", "青海", "桜台", "若葉町"]
    im = draw_route("ひばり線", st, transfer=(4,))
    ok = abs(st.index("風見") - st.index("松原")) == 1
    return im, yesno("「風見」と「松原」は、隣り合った駅である", ok, "spatial", "easy", ["route-map"])


@reg("route-map", "diagram-map")
def b14(rng):
    st = ["双葉", "川原", "松原", "桜台", "青海", "朝日", "港北"]
    im = draw_route("たんぽぽ線", st)
    i = st.index("川原")
    near = "始発駅" if i < len(st) - 1 - i else "終点駅"
    return im, choice("「川原」は、始発駅と終点駅のどちらに近いですか？", near, ["終点駅" if near == "始発駅" else "始発駅"], "spatial", "easy", ["route-map"])




# ================================================================================================ C. 看板・標識・掲示
def draw_sign(lines, panel, fg, border=None, stripes=False, slash=False, sub=None, size_max=132, serif=False, bg=(226, 226, 222)):
    im, dr = canvas(bg)
    box(dr, (36, 56, 604, 424), fill=panel, outline=border or (60, 60, 60), width=8, r=22)
    if stripes:
        layer, mask = Image.new("RGB", (W, H), (20, 20, 20)), Image.new("L", (W, H), 0)      # stripes clipped to the rounded panel
        md = ImageDraw.Draw(mask)
        for yy in (56, 392):
            for x in range(36, 604, 48):
                md.polygon([(x, yy + 32), (x + 24, yy), (x + 48, yy), (x + 24, yy + 32)], fill=255)
        clip = Image.new("L", (W, H), 0)
        ImageDraw.Draw(clip).rounded_rectangle((40, 60, 600, 420), 18, fill=255)
        im.paste(layer, (0, 0), Image.composite(mask, Image.new("L", (W, H), 0), clip))
    cx, tmax = (418, 270) if slash else (320, 500)      # the prohibition mark sits beside the text, never over it
    total = []
    for s in lines:
        total.append(fit(s, tmax, size_max, 800, serif))
    gap = 10
    ht = sum(total) + gap * (len(lines) - 1)
    y = 240 - ht // 2 - (14 if sub else 0)
    for s, sz in zip(lines, total):
        T(dr, (cx, y + sz // 2), s, sz, fg, 800, "mm", serif=serif)
        y += sz + gap
    if sub:
        T(dr, (320, y + 18), sub, 34, fg, 500, "mm")
    if slash:
        mx, my, mr = 190, 240, 120
        dr.rectangle((mx - 78, my + 8, mx + 40, my + 30), fill=(235, 235, 230), outline=(90, 90, 90), width=3)      # a cigarette
        dr.rectangle((mx + 40, my + 8, mx + 78, my + 30), fill=(225, 150, 60), outline=(90, 90, 90), width=3)
        dr.arc((mx - 60, my - 70, mx - 10, my), 200, 340, fill=(130, 130, 130), width=4)
        dr.ellipse((mx - mr, my - mr, mx + mr, my + mr), outline=RED, width=14)
        dr.line((mx - 85, my - 85, mx + 85, my + 85), fill=RED, width=14)
    return im


def meaning(instr, correct, wrong, sub_tags, difficulty="easy"):
    return choice(instr, correct, wrong, "recognition", difficulty, ["sign"] + list(sub_tags))


@reg("sign", "sign")
def c01(rng):
    im = draw_sign(["立入禁止"], (255, 214, 40), (190, 20, 20), stripes=True)
    return im, meaning("この掲示を見た人は、どうすればよいですか？", "中に入らない", ["靴を脱ぐ", "静かに待つ"], ["meaning"])


@reg("sign", "sign")
def c02(rng):
    im = draw_sign(["営業中"], (44, 110, 60), (255, 255, 255), border=(230, 220, 190))
    return im, meaning("この看板が出ているお店の状態は、どれですか？", "営業している", ["準備している", "本日は休み", "改装している", "閉店した"], ["meaning"])


@reg("sign", "sign")
def c03(rng):
    im = draw_sign(["準備中"], (150, 90, 50), (255, 245, 220))
    return im, meaning("この看板が出ているお店について、正しいのはどれですか？", "まだ営業していない", ["営業している", "満席である", "貸し切りである"], ["meaning"])


@reg("sign", "sign")
def c04(rng):
    im = draw_sign(["非常口"], (20, 140, 80), (255, 255, 255))
    return im, meaning("この表示は、何の場所を示していますか？", "災害のときに避難する出口", ["お手洗い", "エレベーター", "受付", "喫煙所", "駐輪場"], ["meaning"])


@reg("sign", "sign")
def c05(rng):
    im = draw_sign(["土足厳禁"], (255, 255, 255), (30, 30, 30), border=(190, 30, 30))
    return im, meaning("この掲示のある場所に上がるときは、どうしますか？", "靴を脱ぐ", ["傘を預ける", "帽子を取る", "静かにする"], ["meaning"])


@reg("sign", "sign")
def c06(rng):
    im = draw_sign(["禁煙"], (255, 255, 255), (30, 30, 30), slash=True, border=(120, 120, 120), size_max=100)
    return im, meaning("この表示が示していることは、どれですか？", "たばこを吸ってはいけない", ["飲食してはいけない", "写真を撮ってはいけない", "通話してはいけない", "走ってはいけない", "立ち止まってはいけない", "該当なし"], ["meaning"])


@reg("sign", "sign")
def c07(rng):
    im = draw_sign(["駐車場"], (30, 80, 170), (255, 255, 255))
    return im, meaning("この看板は、何ができる場所を示していますか？", "車を止められる", ["自転車を借りられる", "バスに乗れる", "タクシーを呼べる", "荷物を預けられる"], ["meaning"])


@reg("sign", "sign")
def c08(rng):
    im = draw_sign(["関係者以外", "立入禁止"], (255, 255, 255), (200, 30, 30), border=(200, 30, 30), size_max=100)
    return im, yesno("この掲示は、誰でも自由に立ち入ってよいという意味である", False, "recognition", "easy", ["sign", "meaning"])


@reg("sign", "sign")
def c09(rng):
    im = draw_sign(["駐車禁止"], (255, 255, 255), (30, 60, 160), slash=False, border=(30, 60, 160))
    return im, yesno("この看板のある場所には、車を止めてよい", False, "recognition", "easy", ["sign", "meaning"])




def draw_hours(shop, hours, lo=None, closed="水曜日", rest=None, always=False):
    im, dr = canvas((236, 228, 214))
    box(dr, (30, 30, 610, 450), fill=(92, 58, 34), outline=(52, 30, 16), width=8, r=14)
    T(dr, (320, 84), shop, fit(shop, 520, 54), (255, 240, 210), 800, "mm")
    dr.line((60, 118, 580, 118), fill=(220, 190, 140), width=3)
    y = 170
    T(dr, (60, y), "営業時間  %s〜%s" % hours, 44, (255, 255, 255), 600, "lm")
    y += 68
    if lo:
        T(dr, (60, y), "ラストオーダー  %s" % lo, 40, (255, 235, 190), 500, "lm")
        y += 64
    if rest:
        T(dr, (60, y), "中休み  %s〜%s" % rest, 40, (255, 235, 190), 500, "lm")
        y += 64
    T(dr, (60, y), "年中無休" if always else "定休日  %s" % closed, 44, (255, 255, 255), 600, "lm")
    return im


@reg("hours", "sign")
def c11(rng):
    im = draw_hours("そば処 つむぎ庵", ("11:00", "21:00"), lo="20:30", closed="水曜日")
    return im, choice("このお店の閉店時刻は、何時ですか？", "21:00", ["20:30", "22:00", "20:00", "19:00"], "ocr", "easy", ["hours"])




@reg("hours", "sign")
def c13(rng):
    closed = "水曜日"
    today = "火曜日"
    im = draw_hours("ベーカリー こむぎ", ("7:30", "19:00"), closed=closed)
    return im, yesno("今日が%sのとき、このお店は営業している" % today, today != closed, "rules", "easy", ["hours"])


@reg("hours", "sign")
def c14(rng):
    closed = "木曜日"
    today = "木曜日"
    im = draw_hours("寿司処 なぎさ", ("11:30", "22:00"), closed=closed, lo="21:30")
    return im, yesno("今日が%sのとき、このお店は営業している" % today, today != closed, "rules", "easy", ["hours"])


@reg("hours", "sign")
def c15(rng):
    im = draw_hours("ひなた書店", ("10:00", "20:00"), always=True)
    return im, choice("このお店の定休日は、何曜日ですか？", "該当なし", ["月曜日", "水曜日", "日曜日"], "ocr", "medium", ["hours", "none-of-above"])


@reg("hours", "sign")
def c16(rng):
    rest = ("14:00", "17:00")
    im = draw_hours("旅館 せせらぎ 食事処", ("11:00", "21:00"), closed="火曜日", rest=rest)
    return im, yesno("15:00 に入店して食事ができる", False, "rules", "medium", ["hours"])


def draw_board(rows, title, bg=(236, 240, 246), head=(30, 70, 150)):
    im, dr = canvas(bg)
    dr.rectangle((0, 0, W, 84), fill=head)
    T(dr, (320, 44), title, 46, (255, 255, 255), 800, "mm")
    y = 160
    for s, c in rows:
        T(dr, (40, y), s, 44, c or INK, 600, "lm")
        y += 100
    return im


@reg("parking", "sign")
def c17(rng):
    rows = [("最初の60分　300円", None), ("以降30分ごと　100円", None), ("1日最大　1,200円", RED)]
    dur = 150
    fee = min(1200, 300 + math.ceil(max(0, dur - 60) / 30) * 100)
    im = draw_board(rows, "駐車料金のご案内")
    return im, choice("%d分（2時間30分）止めたときの料金は、いくらですか？" % dur, yen(fee), [yen(fee - 100), yen(fee + 100), yen(fee + 200), yen(1200)], "rules", "hard", ["parking", "price"])


@reg("parking", "sign")
def c18(rng):
    rows = [("最初の30分　無料", GREEN), ("以降20分ごと　200円", None), ("夜間　最大500円", None)]
    im = draw_board(rows, "コインパーキング料金", head=(30, 120, 80))
    return im, yesno("止めてから30分以内なら、料金はかからない", True, "rules", "easy", ["parking", "price"])


def draw_status(title, big, sub=None, panel=(255, 255, 255), fg=INK):
    im, dr = canvas((230, 230, 226))
    box(dr, (36, 56, 604, 424), fill=panel, outline=(70, 70, 70), width=8, r=22)
    T(dr, (320, 120), title, 44, fg, 800, "mm")
    T(dr, (320, 250), big, fit(big, 500, 110, 800), fg, 800, "mm")
    if sub:
        T(dr, (320, 360), sub, 42, fg, 600, "mm")
    return im


@reg("level-sign", "sign")
def c19(rng):
    free, tot = 12, 40
    levels = ["空いている（空き50%以上）", "やや混んでいる（空き20〜49%）", "ほぼ満車（空き20%未満）"]
    r = free / tot
    ans = 0 if r >= .5 else 1 if r >= .2 else 2
    im = draw_status("駐車場　空き台数", "空き %d台" % free, "全 %d台" % tot, panel=(30, 80, 170), fg=(255, 255, 255))
    return im, score("この駐車場の混み具合は、どの程度ですか？", levels, ans, "quantity", "medium", ["level", "parking"])


@reg("level-sign", "sign")
def c20(rng):
    mins = 40
    levels = ["10分以内", "11〜20分", "21〜30分", "31〜45分", "46分以上"]
    ans = 0 if mins <= 10 else 1 if mins <= 20 else 2 if mins <= 30 else 3 if mins <= 45 else 4
    im = draw_status("ただいまの待ち時間", "約 %d分" % mins, "ご案内までお待ちください", panel=(255, 244, 214))
    return im, score("この表示から、待ち時間はどの範囲だとわかりますか？", levels, ans, "quantity", "easy", ["level", "wait"])


def draw_gauge(title, frac, left, right, ticks=None, color=(40, 130, 220)):
    im, dr = canvas((240, 242, 244))
    T(dr, (320, 74), title, 60, INK, 800, "mm")
    x0, x1, y0, y1 = 70, 570, 170, 280
    box(dr, (x0, y0, x1, y1), fill=(255, 255, 255), outline=INK, width=6, r=12)
    fx = x0 + 6 + int((x1 - x0 - 12) * frac)
    dr.rectangle((x0 + 6, y0 + 6, fx, y1 - 6), fill=color)
    T(dr, (x0, 330), left, 46, INK, 700, "ma")
    T(dr, (x1, 330), right, 46, INK, 700, "ma")
    if ticks:
        for t in ticks:
            x = x0 + 6 + int((x1 - x0 - 12) * t / 100)
            dr.line((x, y1, x, y1 + 18), fill=INK, width=3)
            if "%d" % t not in (left, right):      # the end values are already printed once, as the left / right labels
                T(dr, (x, y1 + 24), "%d" % t, 30, INK, 500, "ma")
    return im


@reg("gauge", "ui")
def c21(rng):
    f = 0.82
    levels = ["ほぼ空（3分の1未満）", "半分前後（3分の1以上、3分の2未満）", "多い（3分の2以上）"]
    ans = int(f * 3)
    im = draw_gauge("燃料", f, "空", "満", color=(230, 140, 30))
    return im, score("燃料計は、どれくらい残っていますか？", levels, ans, "quantity", "easy", ["gauge", "level"])


@reg("gauge", "ui")
def c22(rng):
    f = 0.13
    levels = ["ほぼ空（3分の1未満）", "半分前後（3分の1以上、3分の2未満）", "多い（3分の2以上）"]
    ans = int(f * 3)
    im = draw_gauge("ポットの水", f, "空", "満", color=(60, 150, 230))
    return im, score("ポットの水は、どれくらい残っていますか？", levels, ans, "quantity", "easy", ["gauge", "level"])


@reg("gauge", "ui")
def c23(rng):
    p = 20
    levels = ["0〜14%", "15〜28%", "29〜42%", "43〜57%", "58〜71%", "72〜85%", "86〜100%"]
    ans = [p <= t for t in (14, 28, 42, 57, 71, 85)].index(True) if p <= 85 else 6
    im = draw_gauge("電池残量", p / 100, "0", "100", ticks=(0, 25, 50, 75, 100), color=(60, 170, 90))
    return im, score("電池残量は、どの範囲にありますか？", levels, ans, "quantity", "medium", ["gauge", "level"])


# ================================================================================================ D. メニュー・価格表
def draw_menu(title, items, cols=1, tax_note=None, serif=False):
    im, dr = canvas((250, 240, 220))
    box(dr, (14, 14, 626, 466), outline=(120, 70, 30), width=5)
    T(dr, (320, 58), title, fit(title, 556, 46, 800, serif), (120, 50, 20), 800, "mm", serif=serif)
    dr.line((50, 94, 590, 94), fill=(150, 90, 40), width=3)
    n = len(items)
    per = math.ceil(n / cols)
    rowh = min(60, (420 - (32 if tax_note else 0) - 106) // per)
    cw = 580 // cols
    for i, (nm, pr) in enumerate(items):
        c, r = divmod(i, per)
        x = 36 + c * cw
        y = 112 + r * rowh
        sz = 34 if cols == 1 else 30
        T(dr, (x, y + rowh // 2), nm, sz, INK, 600, "lm", serif=serif)
        T(dr, (x + cw - 24, y + rowh // 2), yen(pr), sz, RED if False else INK, 700, "rm")
        dr.line((x, y + rowh - 2, x + cw - 24, y + rowh - 2), fill=(200, 170, 120), width=1)
    if tax_note:
        T(dr, (320, 440), tax_note, 24, (110, 60, 20), 600, "mm")
    return im


M1 = [("ざるそば", 780), ("天そば", 1150), ("親子丼", 980), ("かつ丼", 1080), ("魚定食", 1280), ("肉定食", 1180), ("餃子", 480), ("ビール", 650)]
M2 = [("醤油ラーメン", 850), ("味噌ラーメン", 950), ("チャーハン", 780), ("餃子", 480), ("冷やし中華", 900), ("杏仁豆腐", 380)]


@reg("menu", "document")
def d01(rng):
    items = M2
    cheapest = min(items, key=lambda x: x[1])[0]
    im = draw_menu("お品書き", items)
    return im, choice("このメニューでいちばん安いのは、どれですか？", cheapest, [n for n, _ in items if n != cheapest], "compare", "easy", ["menu"])


@reg("menu", "document")
def d02(rng):
    items = M1
    top = max(items, key=lambda x: x[1])[0]
    im = draw_menu("お食事メニュー", items, cols=2)
    return im, choice("このメニューでいちばん高いのは、どれですか？", top, [n for n, _ in items if n != top], "compare", "easy", ["menu"])




@reg("menu", "document")
def d04(rng):
    items = [("かけうどん", 400), ("きつねうどん", 550), ("天ぷらうどん", 750), ("カレーうどん", 700), ("おにぎり", 150)]
    p = dict(items)
    tot = p["きつねうどん"] + p["おにぎり"]
    im = draw_menu("うどん処 メニュー", items)
    return im, choice("きつねうどんとおにぎりを1つずつ頼むと、合計はいくらですか？", yen(tot), [yen(tot - 50), yen(tot + 50), yen(p["天ぷらうどん"] + p["おにぎり"]), yen(tot + 100)], "quantity", "medium", ["menu", "sum"])


@reg("menu", "document")
def d05(rng):
    p = dict(M2)
    ok = p["味噌ラーメン"] > p["醤油ラーメン"]
    im = draw_menu("お品書き", M2)
    return im, yesno("味噌ラーメンは、醤油ラーメンより高い", ok, "compare", "easy", ["menu"])




@reg("menu", "document")
def d07(rng):
    items = [("焼き魚定食", 1280), ("唐揚げ定食", 1180), ("天ぷら定食", 1380), ("かつ丼", 1080), ("親子丼", 980)]
    im = draw_menu("定食・丼", items)
    return im, choice("500円以下で食べられるものは、どれですか？", "該当なし", [n for n, _ in items[:3]], "compare", "medium", ["menu", "none-of-above"])


@reg("menu", "document")
def d08(rng):
    items = [("ミニサラダ", 300), ("ポテトフライ", 380), ("枝豆", 330), ("焼き鳥盛り合わせ", 780), ("刺身三点盛り", 980), ("唐揚げ", 580)]
    base = dict(items)["焼き鳥盛り合わせ"]
    tot = base + base // 10
    im = draw_menu("おつまみ（表示は税抜価格）", items, tax_note="※ 消費税10%が別にかかります")
    return im, choice("焼き鳥盛り合わせを1つ頼むと、税込でいくらですか？", yen(tot), [yen(base), yen(base + 100), yen(tot + 100)], "quantity", "medium", ["menu", "tax"])




@reg("menu", "document")
def d10(rng):
    items = [("天ぷら盛り合わせ", 1280), ("刺身定食", 1180), ("すき焼き膳", 1680), ("うな重", 1480), ("ざるそば", 780), ("茶碗蒸し", 480)]
    top = max(p for _, p in items)
    levels = ["399円以下", "400〜599円", "600〜799円", "800〜999円", "1,000〜1,199円", "1,200〜1,499円", "1,500円以上"]
    ans = sum(top >= t for t in (400, 600, 800, 1000, 1200, 1500))
    im = draw_menu("お品書き", items)
    return im, score("このメニューでいちばん高い品の値段は、どの範囲にありますか？", levels, ans, "quantity", "medium", ["menu", "level"])


@reg("menu", "document")
def d11(rng):
    items = [("天ぷら", 900), ("刺身", 800), ("焼き魚", 700), ("煮物", 500), ("茶碗蒸し", 400), ("味噌汁", 200)]
    absent = "ぎょうざ"
    im = draw_menu("小鉢・一品", items)
    return im, choice("次のうち、このメニューにないものはどれですか？", "餃子", ["天ぷら", "焼き魚", "味噌汁", "煮物"], "negation", "easy", ["menu", "negation"])


# ================================================================================================ E. 申込用紙・フォーム
def check(dr, x, y, on, s=34):
    box(dr, (x, y, x + s, y + s), fill=(255, 255, 255), outline=INK, width=3)
    if on:
        dr.line((x + 6, y + s * .55, x + s * .4, y + s - 7, x + s - 4, y + 2), fill=RED, width=6)


def draw_form(title, name, checks=None, birth=None, now=None, seal=None, sex=None, agree=None, kana=None):
    im, dr = canvas((248, 250, 252))
    dr.rectangle((0, 0, W, 70), fill=(60, 90, 160))
    T(dr, (320, 36), title, 42, (255, 255, 255), 800, "mm")
    T(dr, (30, 102), "氏名", 30, GREY, 600, "lm")
    T(dr, (110, 102), name, 40, INK, 600, "lm")
    dr.line((100, 126, 470, 126), fill=INK, width=2)
    if seal is not None:
        box(dr, (500, 76, 600, 176), outline=GREY, width=2)
        if seal:
            dr.ellipse((510, 86, 590, 166), outline=RED, width=5)
            T(dr, (550, 126), name.split()[0][:1], 46, RED, 800, "mm", serif=True)
        else:
            T(dr, (550, 126), "印", 30, (190, 190, 190), 500, "mm")
    y = 150
    if birth:
        era, yy, mm, dd = birth
        T(dr, (30, y + 40), "生年月日", 30, GREY, 600, "lm")
        x = 170
        for e in ("昭和", "平成", "令和"):
            T(dr, (x, y + 40), e, 38, INK, 600, "lm")
            if e == era:
                dr.ellipse((x - 12, y + 10, x + 88, y + 70), outline=RED, width=5)
            x += 110
        T(dr, (30, y + 120), "%d 年  %d 月  %d 日" % (yy, mm, dd), 44, INK, 600, "lm")
        y += 170
    if now:
        T(dr, (30, y + 30), "記入日　" + jdate(*now), 38, INK, 500, "lm")
        y += 80
    if sex:
        T(dr, (30, y + 40), "性別", 30, GREY, 600, "lm")
        x = 140
        for s in ("男", "女", "回答しない"):
            T(dr, (x, y + 40), s, 38, INK, 600, "lm")
            if s == sex:
                wd = tw(s, 38, 600)
                dr.ellipse((x - 14, y + 8, x + wd + 14, y + 72), outline=RED, width=5)
            x += tw(s, 38, 600) + 60
        y += 100
    if checks:
        step = min(54, (H - y - 14) // len(checks))
        for lab, on in checks:
            check(dr, 40, y + 6, on)
            T(dr, (96, y + 24), lab, fit(lab, 520, 34), INK, 500, "lm")
            y += step
    if agree is not None:
        check(dr, 40, 400, agree, 40)
        T(dr, (100, 420), "上記に同意します", 36, INK, 600, "lm")
    return im


CHK = ["資料の送付を希望する", "メールマガジンを受け取る", "電話での連絡を希望する", "会員証を郵送で受け取る", "領収書の発行を希望する", "ポイントカードを持っている"]


@reg("form", "document")
def e01(rng):
    on = [True, False, True, True, False, False]
    im = draw_form("会員申込書", "柏木 みのり", list(zip(CHK, on)))
    n = sum(on)
    return im, choice("チェックが入っている項目は、いくつありますか？", "%d個" % n, ["%d個" % x for x in (n - 1, n + 1, n + 2, n - 2)], "count", "easy", ["form", "count"])


@reg("form", "document")
def e02(rng):
    on = [False, True, False, False, True, False]
    im = draw_form("会員申込書", "真壁 修", list(zip(CHK, on)))
    n = sum(1 for x in on if not x)
    return im, choice("チェックが入っていない項目は、いくつありますか？", "%d個" % n, ["%d個" % x for x in (n - 1, n + 1, n - 2, n + 2, 1)], "count", "medium", ["form", "count"])


@reg("form", "document")
def e03(rng):
    y, m, d = 1975, 4, 8
    era, n = era_of(y)
    im = draw_form("ご利用申込書", "青柳 修", birth=(era, n, m, d))
    return im, choice("申込書に書かれた生年月日の年を西暦で表すと、何年ですか？", "%d年" % y, ["%d年" % (y - 1), "%d年" % (y + 1), "%d年" % (y - 10), "%d年" % (y + 10)], "ocr", "hard", ["form", "wareki"])


@reg("form", "document")
def e04(rng):
    by, bm, bd = 1997, 8, 20
    now = (2024, 4, 1)
    age = now[0] - by - ((now[1], now[2]) < (bm, bd))
    era, n = era_of(by)
    im = draw_form("ご利用申込書", "柏木 みのり", birth=(era, n, bm, bd), now=now)
    return im, choice("記入日の時点で、この人は満何歳ですか？", "%d歳" % age, ["%d歳" % (age + 1), "%d歳" % (age - 1), "%d歳" % (age + 2)], "rules", "hard", ["form", "wareki", "age"])


@reg("form", "document")
def e05(rng):
    im = draw_form("お客様情報カード", "真壁 修", seal=True)
    return im, yesno("この用紙の押印欄には、印が押されている", True, "recognition", "easy", ["form", "seal"])


@reg("form", "document")
def e06(rng):
    im = draw_form("お客様情報カード", "青柳 みなみ", seal=False)
    return im, yesno("この用紙の押印欄には、印が押されている", False, "recognition", "easy", ["form", "seal"])




@reg("form", "document")
def e08(rng):
    items = ["コース A（朝）", "コース B（昼）", "コース C（夜）", "コース D（週末）", "コース E（通信）", "コース F（体験）"]
    on = [False, False, False, False, True, False]
    im = draw_form("講座申込書", "真壁 修", list(zip(items, on)))
    return im, choice("チェックが入っているコースはどれですか？", items[4], [x for i, x in enumerate(items) if i != 4], "recognition", "medium", ["form", "many-options"])


@reg("form", "document")
def e09(rng):
    items = ["資料の送付を希望する", "電話での連絡を希望する", "メールでの連絡を希望する", "郵送での連絡を希望する"]
    im = draw_form("お問い合わせ票", "青柳 修", [(x, False) for x in items])
    return im, choice("チェックが入っている項目はどれですか？", "該当なし", items[:3], "recognition", "easy", ["form", "none-of-above"])


@reg("form", "document")
def e10(rng):
    items = ["資料の送付を希望する", "電話での連絡を希望する", "領収書の発行を希望する", "会員証を郵送で受け取る"]
    on = [True, True, False, True]
    im = draw_form("お申込み確認票", "柏木 みのり", list(zip(items, on)))
    off = [x for x, o in zip(items, on) if not o]
    assert len(off) == 1
    return im, choice("チェックが入っていない項目はどれですか？", off[0], [x for x in items if x != off[0]], "negation", "easy", ["form", "negation"])




@reg("form", "document")
def e12(rng):
    im = draw_form("利用規約の確認", "小野寺 ひなた", agree=False)
    return im, yesno("同意欄にチェックが入っている", False, "recognition", "easy", ["form"])


# ================================================================================================ F. 縦書きの文書
KN = "〇一二三四五六七八九"


def kan(n):
    """Kanji numeral for 0 < n < 10000 (e.g. 1450 -> 千四百五十, 20 -> 二十, 300 -> 三百)."""
    out = ""
    for v, u in ((1000, "千"), (100, "百"), (10, "十")):
        q, n = divmod(n, v)
        if q:
            out += ("" if q == 1 and v != 1000 else KN[q]) + u if q != 1 else u
    if n:
        out += KN[n]
    return out


def draw_vertical(cols, title_sz=42, sz=38, bg=(248, 240, 220), edge=(150, 110, 70), serif=True, first_bigger=True):
    im, dr = canvas(bg)
    box(dr, (14, 14, 626, 466), outline=edge, width=4)
    n = len(cols)
    gap = 84 if n <= 6 else 74
    x = 590 - 30
    for i, s_ in enumerate(cols):
        size = title_sz if (i == 0 and first_bigger) else sz
        size = min(size, int(400 / (1.12 * len(s_))))
        vtext(dr, x, 40, s_, size, INK, 600, serif=serif, step=1.12)
        x -= gap + (10 if i == 0 and first_bigger else 0)
    return im


@reg("vertical", "document")
def f01(rng):
    d = 20
    cols = ["夏祭りのお知らせ", "日時八月%s日土曜日" % kan(d), "午後五時から", "場所中央公園", "会費%s円" % kan(300)]
    im = draw_vertical(cols)
    return im, choice("夏祭りが開かれるのは、何月何日ですか？", "8月%d日" % d, ["8月%d日" % x for x in (2, 12, 27)], "ocr", "medium", ["vertical", "notice"])


@reg("vertical", "document")
def f02(rng):
    cols = ["お休みのお知らせ", "八月十三日から", "八月十六日まで", "お盆休みです", "店主"]
    im = draw_vertical(cols, serif=False)
    n = 16 - 13 + 1
    return im, choice("お休みは、全部で何日間ですか？", "%d日間" % n, ["%d日間" % x for x in (3, 5, 6)], "rules", "hard", ["vertical", "notice", "count"])


@reg("vertical", "document")
def f03(rng):
    cols = ["町内会総会のご案内", "日時六月九日日曜日", "午前十時から", "場所公民館二階", "持ち物は印鑑"]
    im = draw_vertical(cols)
    return im, choice("総会が開かれる場所は、どこですか？", "公民館の2階", ["公民館の1階", "中央公園", "小学校の体育館", "市役所の会議室", "駅前の広場"], "ocr", "medium", ["vertical", "notice"])


@reg("vertical", "document")
def f04(rng):
    cols = ["謹賀新年", "令和八年", "元旦", "旧年中は大変お世話になりました", "本年もよろしく"]
    im, dr = canvas((252, 244, 232))
    box(dr, (14, 14, 626, 466), outline=(190, 40, 40), width=5)
    vtext(dr, 520, 40, "謹賀新年", 76, (190, 40, 40), 800, serif=True)
    vtext(dr, 380, 60, "令和八年", 52, INK, 700, serif=True)
    vtext(dr, 300, 60, "元旦", 52, INK, 700, serif=True)
    vtext(dr, 180, 60, "本年もよろしく", 38, INK, 500, serif=True)
    vtext(dr, 120, 60, "お願いします", 38, INK, 500, serif=True)
    return im, choice("この年賀状の年は、西暦で何年ですか？", "2026年", ["2024年", "2025年", "2027年", "2028年"], "ocr", "medium", ["vertical", "nengajo", "wareki"])


@reg("vertical", "document")
def f05(rng):
    cols = ["引越しのお知らせ", "十月五日より", "左記に移転しました", "新住所", "港北区若葉町三丁目"]
    cols = ["転居のお知らせ", "十月五日より", "下記へ移りました", "若葉町三丁目", "電話は変わりません"]
    im = draw_vertical(cols, serif=False)
    return im, yesno("転居後も、電話番号は変わらない", True, "ocr", "easy", ["vertical", "notice"])


@reg("vertical", "document")
def f06(rng):
    cols = ["休業のお知らせ", "毎週水曜日は", "定休日です", "営業時間は", "九時から十七時"]
    im = draw_vertical(cols)
    return im, choice("このお知らせによると、毎週お休みの曜日はどれですか？", "水曜日", ["月曜日", "火曜日", "木曜日", "金曜日", "日曜日", "土曜日"], "ocr", "easy", ["vertical", "notice"])


@reg("vertical", "document")
def f07(rng):
    cols = ["秋の演奏会", "十一月三日祝日", "午後二時開演", "会場市民ホール", "入場無料"]
    im = draw_vertical(cols, serif=False)
    return im, yesno("この演奏会は、入場料が必要である", False, "ocr", "easy", ["vertical", "notice"])


@reg("vertical", "document")
def f08(rng):
    cols = ["お花見のご案内", "三月三十日日曜日", "午前十一時集合", "場所は桜台公園", "雨天の場合は中止"]
    im = draw_vertical(cols)
    return im, choice("集合時刻は、何時ですか？", "午前11時", ["午前10時", "午後1時", "午前9時"], "ocr", "medium", ["vertical", "notice"])


@reg("vertical", "document")
def f09(rng):
    cols = ["清掃活動のお知らせ", "七月六日土曜日", "午前七時から", "集合場所は児童館", "軍手をご持参"]
    im = draw_vertical(cols, serif=False)
    return im, choice("集合場所として書かれているのはどこですか？", "該当なし", ["公民館", "中央公園", "市役所"], "ocr", "medium", ["vertical", "notice", "none-of-above"])


@reg("vertical", "document")
def f10(rng):
    cols = ["バス運行のお知らせ", "毎日運行です", "最終は午後九時発", "料金二百円", "子どもは百円"]
    im = draw_vertical(cols)
    return im, choice("次のうち、このお知らせに書かれていないものはどれですか？", "電話番号", ["料金", "最終バスの時刻", "運行日", "子どもの料金"], "negation", "medium", ["vertical", "notice", "negation"])


# ================================================================================================ G. カレンダー・天気
HOL = {(2024, 5): {3: "憲法記念日", 4: "みどりの日", 5: "こどもの日", 6: "振替休日"}, (2024, 9): {16: "敬老の日", 22: "秋分の日", 23: "振替休日"},
       (2024, 6): {}, (2024, 11): {3: "文化の日", 4: "振替休日", 23: "勤労感謝の日"}, (2024, 7): {15: "海の日"}}


def draw_month(y, m, hol=None, closed=(), mark=None):
    im, dr = canvas((255, 255, 255))
    e, n = era_of(y)
    T(dr, (320, 34), "%s%d年 %d月" % (e, n, m), 44, INK, 800, "mm")
    cw, ch = 88, 60
    x0, y0 = 12, 66
    for i, wd in enumerate("日月火水木金土"):
        c = RED if i == 0 else BLUE if i == 6 else INK
        dr.rectangle((x0 + i * cw, y0, x0 + (i + 1) * cw, y0 + 40), fill=(238, 238, 240), outline=(170, 170, 170))
        T(dr, (x0 + i * cw + cw // 2, y0 + 20), wd, 32, c, 700, "mm")
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(y, m)
    for r, wk in enumerate(weeks):
        for c, dd in enumerate(wk):
            x, yy = x0 + c * cw, y0 + 40 + r * ch
            dr.rectangle((x, yy, x + cw, yy + ch), outline=(170, 170, 170))
            if not dd:
                continue
            isred = c == 0 or (hol and dd in hol)
            col = RED if isred else BLUE if c == 6 else INK
            T(dr, (x + 8, yy + 6), str(dd), 30, col, 700, "la")
            if hol and dd in hol:
                T(dr, (x + cw - 8, yy + ch - 6), "祝", 26, RED, 700, "rd")
            if dd in closed:
                T(dr, (x + cw - 8, yy + ch - 6), "休", 28, RED, 800, "rd")
            if mark and dd in mark:
                dr.ellipse((x + 4, yy + 3, x + 46, yy + 45), outline=GREEN, width=4)
    return im


@reg("calendar", "document")
def g01(rng):
    y, m, d = 2024, 5, 15
    wd = WDAY[datetime.date(y, m, d).weekday()]
    im = draw_month(y, m, HOL[(y, m)], mark=(d,))
    return im, choice("丸がついた日は、何曜日ですか？", wd + "曜日", [x + "曜日" for x in "月火木金" if x != wd][:3], "spatial", "easy", ["calendar", "weekday"])


@reg("calendar", "document")
def g02(rng):
    y, m = 2024, 5
    n = len(HOL[(y, m)])
    im = draw_month(y, m, HOL[(y, m)])
    return im, choice("この月に「祝」の印がついている日は、何日ありますか？", "%d日" % n, ["%d日" % x for x in (n - 1, n + 1)], "count", "medium", ["calendar", "holiday", "count"])




@reg("calendar", "document")
def g04(rng):
    y, m = 2024, 11
    real = WDAY[datetime.date(y, m, 1).weekday()]
    claim = "木"
    im = draw_month(y, m, HOL[(y, m)])
    return im, yesno("この月の1日は、%s曜日である" % claim, real == claim, "spatial", "easy", ["calendar", "weekday"])


@reg("calendar", "document")
def g05(rng):
    y, m = 2024, 9
    mons = [d for d in range(1, 31) if datetime.date(y, m, d).weekday() == 0]
    t = mons[2]
    im = draw_month(y, m, HOL[(y, m)])
    return im, choice("この月の第3月曜日は、何日ですか？", "%d日" % t, ["%d日" % x for x in (mons[1], mons[3], mons[0], mons[4])], "rules", "hard", ["calendar", "weekday"])


@reg("calendar", "document")
def g06(rng):
    y, m = 2024, 6
    assert not HOL[(y, m)]
    im = draw_month(y, m, HOL[(y, m)])
    return im, choice("この月の祝日は、何日ですか？", "該当なし", ["3日", "10日", "20日"], "recognition", "medium", ["calendar", "holiday", "none-of-above"])


@reg("calendar", "document")
def g07(rng):
    y, m = 2024, 7
    closed = [d for d in range(1, 32) if datetime.date(y, m, d).weekday() == 2]
    im = draw_month(y, m, HOL[(y, m)], closed=closed)
    n = len(closed)
    return im, choice("この月に「休」の印がついている日は、何日ありますか？", "%d日" % n, ["%d日" % x for x in (n - 2, n - 1, n + 1, n + 2)], "count", "easy", ["calendar", "shop-calendar", "count"])




ROKU = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]


def draw_week(y, m, d0, s, hl=None):
    im, dr = canvas((255, 252, 244))
    e, n = era_of(y)
    T(dr, (320, 36), "%s%d年 %d月の暦" % (e, n, m), 40, INK, 800, "mm")
    cw = 88
    for i in range(7):
        dd = d0 + i
        wd = datetime.date(y, m, dd).weekday()
        x = 12 + i * cw
        c = RED if wd == 6 else BLUE if wd == 5 else INK
        dr.rectangle((x, 80, x + cw, 440), fill=(255, 255, 255), outline=(170, 160, 140), width=2)
        T(dr, (x + cw // 2, 130), str(dd), 46, c, 800, "mm")
        T(dr, (x + cw // 2, 196), WDAY[wd], 38, c, 700, "mm")
        lab = ROKU[(s + i) % 6]
        T(dr, (x + cw // 2, 300), lab[0], 50, (140, 40, 40) if lab == "大安" else INK, 700, "mm", serif=True)
        T(dr, (x + cw // 2, 358), lab[1], 50, (140, 40, 40) if lab == "大安" else INK, 700, "mm", serif=True)
    return im


@reg("calendar-week", "document")
def g09(rng):
    y, m, d0, s = 2024, 10, 13, 2
    labs = [ROKU[(s + i) % 6] for i in range(7)]
    t = 15
    im = draw_week(y, m, d0, s)
    return im, choice("%d日の六曜は、どれですか？" % t, labs[t - d0], [r for r in ROKU if r != labs[t - d0]], "ocr", "medium", ["calendar", "rokuyo"])


@reg("calendar-week", "document")
def g10(rng):
    y, m, d0, s = 2024, 10, 13, 2
    labs = [ROKU[(s + i) % 6] for i in range(7)]
    tgt = "仏滅"
    assert labs.count(tgt) == 1
    day = d0 + labs.index(tgt)
    im = draw_week(y, m, d0, s)
    return im, choice("%sの日は、何日ですか？" % tgt, "%d日" % day, ["%d日" % x for x in range(d0, d0 + 7) if x != day][:3], "ocr", "medium", ["calendar", "rokuyo"])




WEATHER = {"晴": (240, 150, 30), "曇": (130, 130, 140), "雨": (50, 100, 210), "雪": (60, 170, 190)}


def draw_forecast(y, m, d0, days, title="週間天気"):
    im, dr = canvas((240, 246, 252))
    T(dr, (320, 40), title, 44, INK, 800, "mm")
    cw = 116
    for i, (w, hi, lo, pr) in enumerate(days):
        dt = datetime.date(y, m, d0) + datetime.timedelta(days=i)
        x = 30 + i * cw
        box(dr, (x, 84, x + cw - 8, 450), fill=(255, 255, 255), outline=(150, 165, 190), width=2, r=10)
        wd = dt.weekday()
        c = RED if wd == 6 else BLUE if wd == 5 else INK
        T(dr, (x + cw // 2 - 4, 120), "%d/%d" % (dt.month, dt.day), 30, INK, 500, "mm")
        T(dr, (x + cw // 2 - 4, 164), "（%s）" % WDAY[wd], 32, c, 700, "mm")
        dr.ellipse((x + 14, 200, x + cw - 22, 200 + cw - 36), fill=WEATHER[w])
        T(dr, (x + cw // 2 - 4, 240), w, 64, (255, 255, 255), 800, "mm")
        T(dr, (x + cw // 2 - 4, 336), "%d" % hi, 44, RED, 800, "mm")
        T(dr, (x + cw // 2 - 4, 388), "%d" % lo, 40, BLUE, 700, "mm")
        T(dr, (x + cw // 2 - 4, 430), "%d%%" % pr, 28, INK, 500, "mm")
    return im


FC1 = [("晴", 24, 14, 10), ("曇", 22, 15, 30), ("雨", 19, 14, 80), ("雨", 18, 13, 70), ("曇", 20, 13, 40)]    # 2024-10-14 (Mon) ...
FC2 = [("雨", 17, 11, 70), ("雨", 19, 12, 80), ("曇", 21, 13, 40), ("雨", 18, 12, 60), ("雨", 16, 10, 90)]    # 2024-11-04 (Mon)
FC3 = [("晴", 25, 15, 0), ("晴", 27, 16, 10), ("曇", 23, 15, 30), ("晴", 26, 17, 10), ("曇", 22, 14, 20)]    # 2024-09-30 (Mon)


@reg("weather", "document")
def w01(rng):
    y, m, d0 = 2024, 10, 14
    im = draw_forecast(y, m, d0, FC1)
    n = sum(1 for w, *_ in FC1 if w == "雨")
    return im, choice("この予報で、雨になる日は何日ありますか？", "%d日" % n, ["%d日" % x for x in (n - 1, n + 1, n + 2, n + 3)], "count", "easy", ["weather", "count"])


@reg("weather", "document")
def w02(rng):
    y, m, d0 = 2024, 10, 14
    days = FC1
    hi = max(range(5), key=lambda i: days[i][1])
    wd = lambda i: WDAY[(datetime.date(y, m, d0) + datetime.timedelta(days=i)).weekday()] + "曜日"
    im = draw_forecast(y, m, d0, days)
    return im, choice("最高気温がいちばん高い日は、何曜日ですか？", wd(hi), [wd(i) for i in range(5) if i != hi], "compare", "medium", ["weather", "weekday"])


@reg("weather", "document")
def w03(rng):
    y, m, d0 = 2024, 10, 14
    days = FC1
    i = [(datetime.date(y, m, d0) + datetime.timedelta(days=k)).weekday() for k in range(5)].index(3)
    return draw_forecast(y, m, d0, days), yesno("木曜日は、雨の予報である", days[i][0] == "雨", "recognition", "easy", ["weather"])


@reg("weather", "document")
def w04(rng):
    y, m, d0 = 2024, 11, 4
    days = FC2
    wd = lambda i: WDAY[(datetime.date(y, m, d0) + datetime.timedelta(days=i)).weekday()] + "曜日"
    non = [i for i in range(5) if days[i][0] != "雨"]
    assert len(non) == 1
    im = draw_forecast(y, m, d0, days)
    return im, choice("この予報で、雨ではない日はどれですか？", wd(non[0]), [wd(i) for i in range(5) if i != non[0]], "negation", "medium", ["weather", "negation"])


@reg("weather", "document")
def w05(rng):
    y, m, d0 = 2024, 9, 30
    days = FC3
    assert not any(w == "雪" for w, *_ in days)
    im = draw_forecast(y, m, d0, days)
    return im, choice("雪の予報が出ているのは、何曜日ですか？", "該当なし", ["火曜日", "水曜日", "金曜日"], "recognition", "easy", ["weather", "none-of-above"])


@reg("weather", "document")
def w06(rng):
    p = 10
    levels = ["0〜10%", "20〜30%", "40〜50%", "60〜70%", "80〜100%"]
    ans = 0 if p <= 10 else 1 if p <= 30 else 2 if p <= 50 else 3 if p <= 70 else 4
    im, dr = canvas((240, 246, 252))
    T(dr, (320, 70), "あしたの天気", 52, INK, 800, "mm")
    dr.ellipse((200, 130, 440, 370), fill=WEATHER["晴"])
    T(dr, (320, 250), "晴", 150, (255, 255, 255), 800, "mm")
    T(dr, (320, 420), "降水確率 %d%%" % p, 56, BLUE, 800, "mm")
    return im, score("あしたの降水確率は、どの範囲にありますか？", levels, ans, "quantity", "easy", ["weather", "level"])




# ================================================================================================ H. 漢字・かな・数字の混在
def draw_card(lines, bg=(250, 248, 240), serif=False, edge=(100, 100, 100)):
    im, dr = canvas(bg)
    box(dr, (20, 20, 620, 460), outline=edge, width=4)
    total = sum(sz for _, sz, _ in lines) + 18 * (len(lines) - 1)
    y = 240 - total // 2
    for s, sz, col in lines:
        sz2 = fit(s, 560, sz, 700, serif)
        T(dr, (320, y + sz2 // 2), s, sz2, col or INK, 700, "mm", serif=serif)
        y += sz2 + 18
    return im


@reg("kanji-numeral", "text-in-image")
def h01(rng):
    n = 325
    im = draw_card([("領収金額", 40, GREY), ("%s円" % kan(n), 96, None)])
    return im, choice("書かれている金額を算用数字で表すと、いくらですか？", yen(n), [yen(235), yen(352), yen(3025)], "ocr", "medium", ["script", "kanji-numeral"])


@reg("kanji-numeral", "text-in-image")
def h02(rng):
    im = draw_card([("金", 60, None), ("壱万弐千円也", 84, None)], serif=True)
    return im, choice("書かれている金額を算用数字で表すと、いくらですか？", yen(12000), [yen(1200), yen(10200), yen(120000), yen(11000)], "ocr", "hard", ["script", "kanji-numeral"])




OLD = [("學校", "がっこう", ["がくこう", "がっこ", "がくごう"]), ("國會", "こっかい", ["こくかい", "こっかん", "ごっかい"]), ("驛前", "えきまえ", ["えきぜん", "いきまえ", "えきもと"]),
       ("體育", "たいいく", ["たいくい", "からだいく", "たいこう"]), ("廣場", "ひろば", ["ひろじょう", "こうば", "ひろま"])]


def _old(i):
    w, ok, bad = OLD[i]
    im = draw_card([("旧字体の看板", 36, GREY), (w, 150, None)], serif=True)
    return im, choice("この言葉の読み方は、どれですか？", ok, bad, "ocr", "hard", ["script", "kyujitai"])


@reg("kyujitai", "text-in-image")
def h04(rng):
    return _old(0)


@reg("kyujitai", "text-in-image")
def h05(rng):
    return _old(1)




@reg("kyujitai", "text-in-image")
def h07(rng):
    return _old(3)




def _width_card(top_half):
    im, dr = canvas((250, 248, 240))
    box(dr, (20, 20, 620, 460), outline=(100, 100, 100), width=4)
    a, b = "TEL 03-1234-5678", "ＴＥＬ　０３－１２３４－５６７８"
    rows = [a, b] if top_half else [b, a]
    T(dr, (320, 150), rows[0], 32, INK, 600, "mm")
    T(dr, (320, 330), rows[1], 32, INK, 600, "mm")
    T(dr, (40, 60), "上の行", 24, GREY, 500, "lm")
    T(dr, (40, 240), "下の行", 24, GREY, 500, "lm")
    return im, rows.index(b)


@reg("zenkaku", "text-in-image")
def h09(rng):
    im, idx = _width_card(True)
    return im, choice("全角で書かれているのは、どちらの行ですか？", ["上の行", "下の行"][idx], ["下の行" if idx == 0 else "上の行"], "recognition", "medium", ["script", "zenkaku"])


@reg("zenkaku", "text-in-image")
def h10(rng):
    im, idx = _width_card(False)
    return im, choice("半角で書かれているのは、どちらの行ですか？", ["上の行", "下の行"][1 - idx], ["下の行" if idx == 1 else "上の行"], "recognition", "medium", ["script", "zenkaku"])


@reg("address-card", "text-in-image")
def h11(rng):
    zip_ = "〒153-0064"
    im = draw_card([("ご住所", 36, GREY), (zip_, 96, None), ("みどり市 若葉町 3-12-8", 44, None)])
    return im, choice("書かれている郵便番号は、どれですか？", "153-0064", ["153-0046", "135-0064", "153-0604"], "ocr", "medium", ["script", "postal"])


@reg("eto", "text-in-image")
def h12(rng):
    im, dr = canvas((252, 244, 232))
    box(dr, (14, 14, 626, 466), outline=(190, 40, 40), width=5)
    T(dr, (320, 70), "謹賀新年", 64, (190, 40, 40), 800, "mm", serif=True)
    T(dr, (320, 250), "巳", 200, INK, 800, "mm", serif=True)
    T(dr, (320, 410), "令和七年　元旦", 44, INK, 600, "mm", serif=True)
    return im, choice("年賀状に大きく書かれた干支は、どの動物ですか？", "ヘビ", ["ウマ", "ウシ", "トリ", "サル", "トラ", "イヌ", "ネズミ"], "recognition", "medium", ["script", "eto"])


@reg("eto", "text-in-image")
def h13(rng):
    im, dr = canvas((252, 244, 232))
    box(dr, (14, 14, 626, 466), outline=(190, 40, 40), width=5)
    T(dr, (320, 70), "謹賀新年", 64, (190, 40, 40), 800, "mm", serif=True)
    T(dr, (320, 250), "午", 200, INK, 800, "mm", serif=True)
    T(dr, (320, 410), "令和八年　元旦", 44, INK, 600, "mm", serif=True)
    return im, choice("年賀状に大きく書かれた干支は、どの動物ですか？", "ウマ", ["ヘビ", "ヒツジ", "ネズミ", "トラ", "イヌ", "イノシシ"], "recognition", "medium", ["script", "eto", "many-options"])


@reg("address-card", "text-in-image")
def h14(rng):
    rooms = [("洋室", 6.0), ("和室", 4.5), ("台所", 3.0)]
    tot = sum(a for _, a in rooms)
    im, dr = canvas((246, 250, 244))
    T(dr, (320, 50), "賃貸物件の間取り", 44, (30, 100, 60), 800, "mm")
    y = 120
    for n, a in rooms:
        T(dr, (120, y), n, 48, INK, 700, "lm")
        T(dr, (520, y), "%s畳" % ("%g" % a), 52, INK, 700, "rm")
        dr.line((100, y + 40, 540, y + 40), fill=(180, 190, 180), width=2)
        y += 90
    T(dr, (320, 410), "（1畳は約1.65平方メートル）", 28, GREY, 500, "mm")
    f = lambda v: "%g畳" % v
    return im, choice("3つの部屋の広さを合計すると、何畳ですか？", f(tot), [f(tot - 1.5), f(tot + 1.5), f(tot + 3), f(tot - 3)], "quantity", "medium", ["script", "tatami", "sum"])


@reg("address-card", "text-in-image")
def h15(rng):
    im = draw_card([("お届け先", 36, GREY), ("東京都みなと区", 54, None), ("青海一丁目十二番八号", 54, None)], serif=False)
    return im, choice("住所の「番」の数字は、いくつですか？", "12番", ["8番", "1番", "18番", "21番"], "ocr", "hard", ["script", "address"])


def _ruby(base, ru, wrong):
    im, dr = canvas((250, 248, 240))
    box(dr, (20, 20, 620, 460), outline=(100, 100, 100), width=4)
    sz = 120 if len(base) <= 2 else 96
    wd = tw(base, sz, 700, True)
    T(dr, (320, 330), base, sz, INK, 700, "mm", serif=True)
    T(dr, (320, 190), ru, 52, (180, 40, 40), 600, "mm")
    return im, choice("この言葉に付けられたふりがなは、どれですか？", ru, wrong, "ocr", "medium", ["script", "furigana"])


@reg("furigana", "text-in-image")
def h16(rng):
    return _ruby("東雲", "しののめ", ["とううん", "あずまぐも", "ひがしぐも"])


@reg("furigana", "text-in-image")
def h17(rng):
    return _ruby("雪崩", "なだれ", ["ゆきくずれ", "せつほう", "なたれ", "ゆきなだ"])






# ---------------------------------------------------------------------------------------------------------------- assemble
def build_all():
    out = []
    for i, (name, pattern, itype, fn) in enumerate(BUILDERS):
        img, spec = fn(rng_of(name))
        qid = "biz-%04d" % (FIRST_ID + i)
        row = {"id": qid, "origin": "new", "derived_from": None, "group": "biz", "source": "rendered",
               "image_type": itype, "skill": spec["skill"], "difficulty": spec["difficulty"], "lang": "ja", "langs": ["ja"],
               "modality": "image", "kind": spec["kind"], "answer_format": spec["fmt"],
               "tags": ["synthetic", "japanese", pattern] + [t for t in spec["tags"] if t != pattern],
               "local_images": ["generated/%s.png" % qid], "ja": spec["ja"]}
        if "answer" in spec:
            row["answer"] = spec["answer"]
        row["review"] = {"state": "unreviewed", "history": []}
        out.append((row, img, name))
    return out


def verify(items):
    """Second derivation of a few answers (the builders computed them already); a mismatch is a bug."""
    by = {n: r for r, _, n in items}
    assert by["g01"]["ja"]["correct"] == "水曜日" and by["g05"]["ja"]["correct"] == "16日"
    assert by["a12"]["ja"]["correct"] == yen(int((2 * 1800 + 10 * 120 + 5 * 300) * 1.1))
    assert by["a05"]["ja"]["correct"] == "400円" and by["h14"]["ja"]["correct"] == "13.5畳"
    assert by["e04"]["ja"]["correct"] == "26歳", by["e04"]["ja"]["correct"]
    assert by["c17"]["ja"]["correct"] == "600円"
    assert kan(325) == "三百二十五" and kan(6840) == "六千八百四十" and kan(300) == "三百" and kan(20) == "二十"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    items = build_all()
    verify(items)
    for row, img, name in items:
        assert img.size == (W, H)
    print("%d questions" % len(items))
    if not a.apply:
        print("dry run (use --apply)")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "px224").mkdir(parents=True, exist_ok=True)
    for row, img, _ in items:
        img.save(OUT_DIR / ("%s.png" % row["id"]), optimize=True)
        t = img.copy()
        t.thumbnail((224, 224), Image.LANCZOS)
        t.save(OUT_DIR / "px224" / ("%s.png" % row["id"]), optimize=True)
    with open(JSONL, "w", encoding="utf-8", newline="\n") as f:
        for row, _, _ in items:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("written: %s and %d pictures" % (JSONL, len(items)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
