# -*- coding: utf-8 -*-
"""v1 new questions, tag ``tk_ui``: UI pictures built as REAL Tkinter / ttk windows and captured as screenshots.

    python datasets/synthetic/gen_v1_tk_ui.py [--rows-only] [--limit N]

Writes datasets/questions/v1/new_tk_ui.jsonl (ids biz-3001..) and work/generated/<id>.png (original, <= 640x480) +
work/generated/px224/<id>.png (long side 224, LANCZOS).

How the pictures are made: one borderless (``overrideredirect``) Tk window per question, placed at the top-left of the desktop,
built from ttk / tk widgets (Checkbutton, Radiobutton, Combobox, Scale, Progressbar, Treeview, Notebook, Listbox, Spinbox, Button,
Entry, Canvas, Label), then ``PIL.ImageGrab.grab(bbox=<window inner area>)``. No OS title bar / frame is captured (only our own
header strips drawn inside the window), no Microsoft application is shown, themes are the stock ttk "clam" and "vista".
The window really appears on the desktop for ~0.3 s, one at a time. Tk's scaling is pinned to 96 dpi so point sizes give the same
pixel sizes on every machine; the screenshot is taken with the process DPI-aware (physical pixels).

Answers are NOT read from the picture: each screen is generated from a configuration (which boxes are checked, which button is
disabled, the error texts, the slider value, the table cells ...) and the answer is derived from that configuration. A capture is
retried when the grabbed window is blank / uniform or its four corners do not match the window background (something was in front).

Determinism: every screen uses ``random.Random("<pattern>-<k>")`` and the question order is fixed, so rows are identical on every
run. Pixels are NOT guaranteed identical across machines: the stock vista theme draws native widgets at the system DPI and the
fonts (Segoe UI / Yu Gothic UI) come from the OS, so anti-aliasing and glyph metrics can differ (the answers do not).
A watchdog kills the process after 20 minutes.
"""
from __future__ import annotations

import argparse
import collections
import ctypes
import json
import os
import pathlib
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_JSONL = ROOT / "datasets" / "questions" / "v1" / "new_tk_ui.jsonl"
IMG_DIR = ROOT / "work" / "generated"
PX_DIR = IMG_DIR / "px224"
FAM = {"en": "Segoe UI", "ja": "Yu Gothic UI"}
NONE = ("None of the above", "該当なし")
START_ID = 3001
STATS = {"captures": 0, "retries": 0, "failures": 0}
TAG = "tk_ui"


# ============================================================ capture layer
class App:
    pass


def dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def new_app(theme: str, lang: str, fs: int = 15):
    a = App()
    a.root = r = tk.Tk()
    r.overrideredirect(True)
    r.tk.call("tk", "scaling", 96 / 72)
    a.lang, a.theme, a.fs, a.fam = lang, theme, fs, FAM[lang]
    a.font = (a.fam, fs)
    a.bold = (a.fam, fs, "bold")
    a.small = (a.fam, max(fs - 3, 9))
    a.keep = []
    st = a.st = ttk.Style(r)
    st.theme_use(theme)
    st.configure(".", font=a.font)
    ind = 26 if theme == "clam" else 16
    st.configure("TCheckbutton", font=a.font, indicatorsize=ind)
    st.configure("TRadiobutton", font=a.font, indicatorsize=ind)
    st.map("TCheckbutton", foreground=[("disabled", "#6a6a6a")], indicatorforeground=[("disabled", "#555555")], indicatorbackground=[("disabled", "#e8e8e8")])
    st.configure("TButton", font=a.font, padding=(14, 6))
    st.configure("TLabelframe.Label", font=a.bold)
    st.configure("Treeview", font=a.font, rowheight=int(fs * 2.4))
    st.configure("Treeview.Heading", font=a.bold)
    st.map("Treeview", background=[("selected", "#2f6fd0")], foreground=[("selected", "white")])
    st.configure("TNotebook.Tab", font=a.font, padding=(12, 6))
    st.configure("TCombobox", font=a.font)
    st.configure("Horizontal.TProgressbar", thickness=26)
    st.configure("Horizontal.TScale", sliderlength=30, sliderthickness=28)
    if theme == "clam":
        st.configure("Horizontal.TProgressbar", background="#2f6fd0", troughcolor="#d4d4d4", bordercolor="#888888", lightcolor="#2f6fd0", darkcolor="#2f6fd0")
        st.configure("Horizontal.TScale", background="#2f6fd0", troughcolor="#a8a8a8", bordercolor="#555555", lightcolor="#2f6fd0", darkcolor="#2f6fd0")
    r.option_add("*TCombobox*Listbox.font", a.font)
    a.bgc = st.lookup("TFrame", "background") or "#f0f0f0"
    r.configure(bg=a.bgc)
    a.body = ttk.Frame(r, padding=(20, 16))
    a.body.pack(fill="both", expand=True)
    return a


def corner_ok(im, bg):
    """The two bottom corners must have the same colour (window background or status bar); a window in front would break that."""
    w, h = im.size
    p, q = im.getpixel((0, h - 1))[:3], im.getpixel((w - 1, h - 1))[:3]
    return max(abs(p[i] - q[i]) for i in range(3)) <= 8


def capture(build, theme, lang, fs=15, minw=420, tries=4):
    from PIL import ImageGrab
    for t in range(tries):
        a = new_app(theme, lang, fs)
        r = a.root
        try:
            build(a)
            r.update_idletasks()
            w, h = max(r.winfo_reqwidth(), minw), r.winfo_reqheight()
            if w > 640 or h > 480:
                raise RuntimeError("window too large: %dx%d (%s)" % (w, h, getattr(build, "__name__", "")))
            r.geometry("%dx%d+0+0" % (w, h))
            r.attributes("-topmost", True)
            r.update()
            time.sleep(0.2)
            r.update()
            x, y = r.winfo_rootx(), r.winfo_rooty()
            bg = tuple(c >> 8 for c in r.winfo_rgb(a.bgc))
            im = ImageGrab.grab(bbox=(x, y, x + w, y + h)).convert("RGB")
        finally:
            r.destroy()
        STATS["captures"] += 1
        colors = im.getcolors(maxcolors=100000)
        if im.size == (w, h) and (colors is None or len(colors) > 12) and corner_ok(im, bg):
            return im
        STATS["retries"] += 1
    STATS["failures"] += 1
    raise RuntimeError("capture failed after %d tries" % tries)


# ============================================================ question helpers
def pick(rng, seq):
    return seq[rng.randrange(len(seq))]


class Ctx:
    """Counters that make yes/no halves, score levels and the like balanced over the whole file."""

    def __init__(self):
        self.yn = 0
        self.sc = {3: 0, 7: 0, 10: 0}
        self.perm = {}
        pr = random.Random("tk-score-perm")
        for n in self.sc:
            p = list(range(n))
            pr.shuffle(p)
            self.perm[n] = p

    def next_yn(self):
        self.yn += 1
        return self.yn % 2 == 0

    def next_score(self, n):
        a = self.perm[n][self.sc[n] % n]
        self.sc[n] += 1
        return a


CTX = Ctx()


def en_t(x):
    return x if isinstance(x, str) else str(x) if isinstance(x, int) else x[0]


def ja_t(x):
    return x if isinstance(x, str) else str(x) if isinstance(x, int) else x[1]


def CQ(lang, en_i, ja_i, correct, wrongs, skill, diff, tags):
    """A choice question. Option items: str / int (same in both languages) or (en, ja) pairs."""
    q = {"kind": "choice", "skill": skill, "difficulty": diff, "tags": tags, "lang": lang}
    if lang == "en":
        q["en"] = {"instr": en_i, "correct": en_t(correct), "wrong": [en_t(w) for w in wrongs]}
    q["ja"] = {"instr": ja_i, "correct": ja_t(correct), "wrong": [ja_t(w) for w in wrongs]}
    return q


def YQ(lang, en_s, ja_s, ans, skill, diff, tags):
    q = {"kind": "noul", "skill": skill, "difficulty": diff, "tags": tags, "lang": lang, "answer": ans}
    if lang == "en":
        q["en"] = {"instr": en_s}
    q["ja"] = {"instr": ja_s}
    return q


BOUNDS = {3: [0, 34, 67], 7: [0, 15, 29, 43, 58, 72, 86], 10: list(range(0, 100, 10))}


def level_labels(n, ja):
    b = BOUNDS[n]
    return ["%d%s%d%%" % (b[j], "〜" if ja else "-", (b[j + 1] - 1) if j + 1 < n else 100) for j in range(n)]


def value_in_level(n, ans, rng, margin):
    b = BOUNDS[n]
    lo, hi = b[ans], (b[ans + 1] - 1) if ans + 1 < n else 100
    m = min(margin, (hi - lo) // 3)
    return rng.randint(lo + m, hi - m)


def SQ(lang, en_i, ja_i, n, ans, skill, diff, tags):
    q = {"kind": "score", "skill": skill, "difficulty": diff, "tags": tags, "lang": lang, "answer": ans}
    if lang == "en":
        q["en"] = {"instr": en_i, "levels": level_labels(n, False)}
    q["ja"] = {"instr": ja_i, "levels": level_labels(n, True)}
    return q


def numopts(correct, n_opts, rng, lo=0, hi=None):
    """Distinct integer distractors around the correct number."""
    hi = hi if hi is not None else correct + n_opts + 2
    pool = [v for v in range(lo, hi + 1) if v != correct]
    rng.shuffle(pool)
    return pool[: n_opts - 1]


def fill(rng, onscreen, extras, n):
    """n-1 wrong options: on-screen ones first, padded with off-screen extras (never the correct one)."""
    on = list(onscreen)
    rng.shuffle(on)
    ex = list(extras)
    rng.shuffle(ex)
    return (on + ex)[: n - 1]


def lab(pair, lang):
    return pair[0] if lang == "en" else pair[1]


# ============================================================ pools (en, ja)
SETTINGS = [("Dark mode", "ダークモード"), ("Notifications", "通知"), ("Auto update", "自動更新"), ("Sound effects", "効果音"),
            ("Location access", "位置情報"), ("Wi-Fi only sync", "Wi-Fi のみで同期"), ("Show previews", "プレビュー表示"),
            ("Save passwords", "パスワードを保存"), ("Crash reports", "クラッシュレポート"), ("Biometric login", "生体認証"),
            ("Developer mode", "開発者モード"), ("Offline maps", "オフラインマップ"), ("Spell check", "スペルチェック"),
            ("Auto save", "自動保存")]
GROUPS = [("Privacy", "プライバシー"), ("Display", "表示"), ("Sync", "同期"), ("Alerts", "アラート")]
RADIO = [("Export format", "出力形式", [("PDF", "PDF"), ("PNG", "PNG"), ("JPEG", "JPEG"), ("SVG", "SVG"), ("CSV", "CSV"), ("TXT", "TXT"),
                                       ("HTML", "HTML"), ("XML", "XML"), ("JSON", "JSON"), ("DOCX", "DOCX")]),
         ("Paper size", "用紙サイズ", [("A3", "A3"), ("A4", "A4"), ("A5", "A5"), ("B5", "B5"), ("Letter", "レター"), ("Legal", "リーガル")]),
         ("Priority", "優先度", [("Low", "低"), ("Normal", "標準"), ("High", "高"), ("Urgent", "緊急")]),
         ("Delivery", "配送方法", [("Standard", "通常便"), ("Express", "速達"), ("Overnight", "翌日便"), ("Pickup", "店頭受取")])]
COMBOS = [("Theme", "テーマ", ["Light", "Dark", "System", "High contrast"]),
          ("Language", "言語", ["English", "Japanese", "French", "German", "Spanish", "Korean", "Chinese", "Portuguese"]),
          ("Font size", "文字サイズ", ["Small", "Medium", "Large", "Extra large"]),
          ("Date format", "日付形式", ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"]),
          ("Units", "単位", ["Metric", "Imperial"]),
          ("Time zone", "タイムゾーン", ["UTC", "JST", "PST", "EST", "CET", "IST"]),
          ("Refresh", "更新間隔", ["Every minute", "Every 5 min", "Every 15 min", "Every 30 min", "Hourly", "Daily", "Weekly", "Never"])]
SWITCHES = [("Wi-Fi", "Wi-Fi"), ("Bluetooth", "Bluetooth"), ("Airplane mode", "機内モード"), ("Hotspot", "ホットスポット"),
            ("Night light", "ナイトライト"), ("Battery saver", "バッテリーセーバー"), ("Auto-rotate", "自動回転"), ("Vibration", "バイブレーション")]
FIELDS = [("Name", "氏名", "Alex Moore", "田中 美咲", "required"), ("Email", "メール", "alex@example.com", "misaki@example.jp", "email"),
          ("Phone", "電話番号", "5550142", "0312345678", "digits"), ("Password", "パスワード", "hunter2024", "sakura2024", "short"),
          ("Postal code", "郵便番号", "90210", "1500001", "digits"), ("Address", "住所", "12 Oak Street", "渋谷区神南1-2-3", "required"),
          ("Company", "会社名", "Northwind Ltd", "青空商事", "required"), ("Age", "年齢", "34", "29", "digits")]
ERR = {"required": ("This field is required", "必須項目です"), "email": ("Enter a valid email address", "メールアドレスの形式が正しくありません"),
       "digits": ("Numbers only", "数字のみ入力してください"), "short": ("Must be at least 8 characters", "8 文字以上で入力してください")}
BAD = {"email": "alex.example.com", "digits": "12ab", "short": "abc", "required": ""}
VALUES = [("City", "市区町村", ["Osaka", "Berlin", "Toronto", "Lima", "Oslo", "Seoul", "Nairobi", "Dublin", "Cairo"],
           ["大阪市", "札幌市", "福岡市", "仙台市", "名古屋市", "金沢市", "神戸市"]),
          ("Country", "国", ["Japan", "Norway", "Kenya", "Peru", "Canada", "Ireland", "Egypt", "Brazil"], ["日本", "ノルウェー", "ケニア", "ペルー", "カナダ"]),
          ("Job title", "役職", ["Engineer", "Designer", "Accountant", "Nurse", "Chef", "Pilot", "Teacher"], ["技師", "デザイナー", "会計士", "看護師", "料理人"]),
          ("Department", "部署", ["Sales", "Legal", "Support", "Research", "Finance", "Marketing"], ["営業部", "法務部", "総務部", "開発部", "経理部"]),
          ("Favorite color", "好きな色", ["Red", "Green", "Blue", "Orange", "Purple", "Yellow"], ["赤", "緑", "青", "橙", "紫"]),
          ("Language", "言語", ["Dutch", "Swahili", "Thai", "Polish", "Greek", "Hindi"], ["英語", "中国語", "韓国語", "ドイツ語", "フランス語"])]
BTN = {"OK": ("OK", "OK"), "Cancel": ("Cancel", "キャンセル"), "Retry": ("Retry", "再試行"), "Ignore": ("Ignore", "無視"),
       "Abort": ("Abort", "中止"), "Yes": ("Yes", "はい"), "No": ("No", "いいえ"), "Save": ("Save", "保存"),
       "Dont": ("Don't Save", "保存しない"), "Continue": ("Continue", "続行"), "Skip": ("Skip", "スキップ"),
       "SaveAs": ("Save As", "別名保存"), "Help": ("Help", "ヘルプ"), "Close": ("Close", "閉じる"), "Details": ("Details", "詳細")}
DLG = [  # kind, en text, ja text, category (en, ja) or None, buttons
    ("error", "Cannot save 'report.docx'. There is not enough free space on the disk.", "「report.docx」を保存できません。ディスクの空き容量が不足しています。",
     ("Disk full", "ディスクの空き容量不足"), ["Retry", "Cancel"]),
    ("error", "The server did not respond. Check your connection and try again.", "サーバーが応答しません。接続を確認してもう一度お試しください。",
     ("Network error", "ネットワークエラー"), ["Retry", "Ignore", "Abort"]),
    ("error", "You do not have permission to open this folder.", "このフォルダーを開く権限がありません。",
     ("Permission denied", "アクセス権限がない"), ["OK", "Help"]),
    ("error", "The file 'data.csv' could not be found.", "ファイル「data.csv」が見つかりません。",
     ("File not found", "ファイルが見つからない"), ["Retry", "Skip", "Cancel"]),
    ("warning", "Your session has expired. Please sign in again.", "セッションの有効期限が切れました。もう一度サインインしてください。",
     ("Session expired", "セッションの期限切れ"), ["Continue", "Cancel"]),
    ("warning", "The password must contain at least 8 characters.", "パスワードは 8 文字以上にしてください。",
     ("Invalid password", "パスワードが不正"), ["OK", "Cancel", "Help"]),
    ("confirm", "Do you want to save changes to 'notes.txt'?", "「notes.txt」への変更を保存しますか？", None, ["Save", "Dont", "Cancel"]),
    ("confirm", "Delete 3 items permanently?", "3 件の項目を完全に削除しますか？", None, ["Yes", "No"]),
    ("confirm", "Replace the existing file 'photo.png'?", "既存のファイル「photo.png」を置き換えますか？", None, ["Yes", "No", "SaveAs", "Cancel", "Help"]),
    ("info", "Update 4.2 is ready to install.", "アップデート 4.2 のインストール準備ができました。", None, ["Continue", "Details", "Skip", "Close"]),
]
DLG_STYLE = {"error": ("#c62828", "Error", "エラー"), "warning": ("#e08a00", "Warning", "警告"), "confirm": ("#1f6fb5", "Confirm", "確認"),
             "info": ("#2e7d6b", "Information", "情報")}
PRODUCTS = [("Apples", "りんご"), ("Bananas", "バナナ"), ("Cherries", "さくらんぼ"), ("Grapes", "ぶどう"), ("Lemons", "レモン"),
            ("Mangoes", "マンゴー"), ("Melons", "メロン"), ("Peaches", "もも"), ("Pears", "なし"), ("Plums", "すもも"), ("Kiwis", "キウイ")]
TABS = [("General", "一般"), ("Network", "ネットワーク"), ("Display", "表示"), ("Sound", "サウンド"), ("Privacy", "プライバシー"),
        ("Updates", "更新"), ("Advanced", "詳細設定"), ("Accounts", "アカウント")]
MENUS = [("File", "ファイル", [("New", "新規", "Ctrl+N"), ("Open...", "開く...", "Ctrl+O"), ("Save", "保存", "Ctrl+S"), ("Save As...", "名前を付けて保存...", ""),
                              ("Print", "印刷", "Ctrl+P"), ("Export", "エクスポート", ""), ("Close", "閉じる", "Ctrl+W"), ("Exit", "終了", "Alt+F4")]),
         ("Edit", "編集", [("Undo", "元に戻す", "Ctrl+Z"), ("Redo", "やり直し", "Ctrl+Y"), ("Cut", "切り取り", "Ctrl+X"), ("Copy", "コピー", "Ctrl+C"),
                          ("Paste", "貼り付け", "Ctrl+V"), ("Delete", "削除", "Del"), ("Select All", "すべて選択", "Ctrl+A"), ("Find", "検索", "Ctrl+F")])]
PROGRESS = [("Downloading update", "アップデートをダウンロード中"), ("Uploading photos", "写真をアップロード中"), ("Installing", "インストール中"),
            ("Scanning files", "ファイルをスキャン中"), ("Battery", "バッテリー"), ("Disk usage", "ディスク使用量")]
SLIDERS = [("Volume", "音量"), ("Brightness", "明るさ"), ("Contrast", "コントラスト"), ("Zoom", "ズーム"), ("Opacity", "不透明度"), ("Speed", "速度")]
LIST_ITEMS = [("Inbox", "受信トレイ"), ("Drafts", "下書き"), ("Sent", "送信済み"), ("Archive", "アーカイブ"), ("Spam", "迷惑メール"), ("Trash", "ごみ箱")]


# ============================================================ widget builders
def title(a, text):
    ttk.Label(a.body, text=text, font=(a.fam, a.fs + 3, "bold")).pack(anchor="w", pady=(0, 10))


def build_checks(a, head, items, cols=1):
    title(a, head)
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    per = (len(items) + cols - 1) // cols
    for i, (t, on) in enumerate(items):
        v = tk.BooleanVar(master=a.root, value=on)
        a.keep.append(v)
        ttk.Checkbutton(fr, text=t, variable=v).grid(row=i % per, column=i // per, sticky="w", padx=(0, 40), pady=4)


def build_groups(a, head, groups):
    title(a, head)
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for gi, (gname, items) in enumerate(groups):
        lf = ttk.Labelframe(fr, text=gname, padding=(12, 6))
        lf.grid(row=0, column=gi, padx=(0, 18), sticky="n")
        for t, on in items:
            v = tk.BooleanVar(master=a.root, value=on)
            a.keep.append(v)
            ttk.Checkbutton(lf, text=t, variable=v).pack(anchor="w", pady=3)


def build_radio(a, head, opts, selected, cols=1):
    lf = ttk.Labelframe(a.body, text=head, padding=(14, 8))
    lf.pack(anchor="w")
    v = tk.StringVar(master=a.root, value=selected if selected is not None else "")
    a.keep.append(v)
    per = (len(opts) + cols - 1) // cols
    for i, t in enumerate(opts):
        ttk.Radiobutton(lf, text=t, value=t, variable=v).grid(row=i % per, column=i // per, sticky="w", padx=(0, 40), pady=4)


def build_combos(a, head, rows):
    title(a, head)
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for i, (label, values, cur) in enumerate(rows):
        ttk.Label(fr, text=label).grid(row=i, column=0, sticky="w", padx=(0, 20), pady=7)
        cb = ttk.Combobox(fr, values=values, state="readonly", width=16, font=a.font)
        cb.set(cur)
        cb.grid(row=i, column=1, sticky="w")


def build_switches(a, head, items, show_text):
    title(a, head)
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for i, (label, on) in enumerate(items):
        ttk.Label(fr, text=label, width=20 if a.lang == "en" else 18).grid(row=i, column=0, sticky="w", pady=5)
        c = tk.Canvas(fr, width=76, height=38, bg=a.bgc, highlightthickness=0)
        col = "#2e9e4f" if on else "#9aa0a6"
        c.create_oval(2, 2, 36, 36, fill=col, outline=col)
        c.create_oval(40, 2, 74, 36, fill=col, outline=col)
        c.create_rectangle(19, 2, 57, 36, fill=col, outline=col)
        kx = 56 if on else 20
        c.create_oval(kx - 15, 5, kx + 15, 33, fill="white", outline="#dddddd")
        c.grid(row=i, column=1, padx=(0, 14))
        if show_text:
            tk.Label(fr, text=("ON" if on else "OFF"), font=a.bold, bg=a.bgc, fg=("#1b6e35" if on else "#555555"),
                     width=4).grid(row=i, column=2)


def build_form(a, head, rows, err_lang_idx):
    """rows: (label, text, error text or None, show). The error message sits under its entry, in red."""
    title(a, head)
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for i, (label, text, err, show) in enumerate(rows):
        ttk.Label(fr, text=label).grid(row=2 * i, column=0, sticky="w", padx=(0, 14), pady=(5, 0 if err else 5))
        col = "#d32f2f" if err else "#9e9e9e"
        e = tk.Entry(fr, font=a.font, width=20, relief="solid", bd=1, highlightthickness=3, highlightbackground=col, highlightcolor=col,
                     show="*" if show else "")
        e.insert(0, text)
        e.grid(row=2 * i, column=1, pady=(5, 0 if err else 5), sticky="w")
        if err:
            tk.Label(fr, text=err, font=(a.fam, a.fs - 1), fg="#d32f2f", bg=a.bgc).grid(row=2 * i + 1, column=1, sticky="w", pady=(0, 3))


def build_dialog(a, kind, msg, btns, disabled):
    color, ten, tja = DLG_STYLE[kind]
    hd = tk.Frame(a.root, bg=color)
    hd.pack(fill="x", before=a.body)
    tk.Label(hd, text=(ten if a.lang == "en" else tja), font=a.bold, bg=color, fg="white").pack(anchor="w", padx=18, pady=7)
    tk.Label(a.body, text=msg, font=a.font, wraplength=470, justify="left", bg=a.bgc).pack(anchor="w", pady=(12, 22))
    bf = ttk.Frame(a.body)
    stack = len(btns) >= 4  # many buttons: stack them vertically so the window stays narrow and the text large
    bf.pack(anchor="e")
    for b in btns:
        w = ttk.Button(bf, text=lab(BTN[b], a.lang), width=16 if stack else None)
        if b in disabled:
            w.state(["disabled"])
        if stack:
            w.pack(side="top", pady=3)
        else:
            w.pack(side="left", padx=5)


def build_tree(a, head, cols, rows, selected=None):
    title(a, head)
    tv = ttk.Treeview(a.body, columns=list(range(len(cols))), show="headings", height=len(rows), selectmode="browse")
    for i, c in enumerate(cols):
        tv.heading(i, text=c)
        tv.column(i, width=a.fs * (11 if i == 0 else 7), anchor="w" if i == 0 else "e")
    ids = [tv.insert("", "end", values=r) for r in rows]
    if selected is not None:
        tv.selection_set(ids[selected])
    tv.pack(anchor="w")


def build_notebook(a, tabs, cur, extra_lines):
    a.st.configure("TNotebook.Tab", padding=(8 if len(tabs) >= 5 else 12, 6), font=a.font)
    a.st.map("TNotebook.Tab", background=[("selected", "#2f6fd0"), ("!selected", "#c9c9c9")], foreground=[("selected", "white"), ("!selected", "#222222")])
    nb = ttk.Notebook(a.body, width=500, height=110)
    for t in tabs:
        fr = ttk.Frame(nb, padding=16)
        for ln in extra_lines:
            ttk.Label(fr, text=ln, foreground="#8a8a8a").pack(anchor="w", pady=2)
        nb.add(fr, text=t)
    nb.select(cur)
    nb.pack(anchor="w")


def build_menu(a, menus, cur_menu, items):
    bar = tk.Frame(a.body, bg=a.bgc)
    bar.pack(anchor="w")
    for i, m in enumerate(menus):
        on = i == cur_menu
        tk.Label(bar, text=m, font=a.font, padx=14, pady=4, bg=("#2f6fd0" if on else a.bgc), fg=("white" if on else "black")).pack(side="left")
    box = tk.Frame(a.body, bg="white", highlightthickness=1, highlightbackground="#777777")
    box.pack(anchor="w", pady=(2, 0))
    for label, sc, dis in items:
        row = tk.Frame(box, bg="white")
        row.pack(fill="x")
        fg = "#a0a0a0" if dis else "black"
        tk.Label(row, text=label, font=a.font, bg="white", fg=fg, width=18 if a.lang == "en" else 20, anchor="w", padx=14, pady=3).pack(side="left")
        tk.Label(row, text=sc, font=a.small, bg="white", fg="#a0a0a0" if dis else "#555555", width=8, anchor="e", padx=10).pack(side="left")


def build_sliders(a, rows, show_val):
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for i, (label, val) in enumerate(rows):
        ttk.Label(fr, text=label, width=14 if a.lang == "en" else 12).grid(row=i * 2, column=0, sticky="w", pady=(10, 0))
        sc = ttk.Scale(fr, from_=0, to=100, length=340, orient="horizontal")
        sc.set(val)
        sc.grid(row=i * 2, column=1, pady=(10, 0))
        if show_val:
            ttk.Label(fr, text=str(val), width=4, anchor="e", font=a.bold).grid(row=i * 2, column=2, padx=(8, 0), pady=(10, 0))
        else:
            ttk.Label(fr, text="0", font=a.small).grid(row=i * 2 + 1, column=1, sticky="w")
            ttk.Label(fr, text="100", font=a.small).grid(row=i * 2 + 1, column=1, sticky="e")


def build_bars(a, rows, show_val, wide=420):
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    for i, (label, val) in enumerate(rows):
        ttk.Label(fr, text=label).grid(row=i * 2, column=0, sticky="w", columnspan=2, pady=(10, 2))
        pb = ttk.Progressbar(fr, length=wide, maximum=100, mode="determinate")
        pb["value"] = val
        pb.grid(row=i * 2 + 1, column=0, sticky="w")
        if show_val:
            ttk.Label(fr, text="%d%%" % val, font=a.bold, width=5, anchor="e").grid(row=i * 2 + 1, column=1, padx=(8, 0))


def build_list_spin(a, items, cur, qty):
    fr = ttk.Frame(a.body)
    fr.pack(anchor="w")
    lb = tk.Listbox(fr, font=a.font, height=len(items), width=18, exportselection=False, selectbackground="#2f6fd0",
                    selectforeground="white", activestyle="none", relief="solid", bd=1, highlightthickness=0)
    for t in items:
        lb.insert("end", " " + t)
    lb.selection_set(cur)
    lb.grid(row=0, column=0, rowspan=3, padx=(0, 30), sticky="n")
    ttk.Label(fr, text=("Quantity" if a.lang == "en" else "数量")).grid(row=0, column=1, sticky="sw")
    sp = ttk.Spinbox(fr, from_=0, to=99, width=6, font=a.font)
    sp.set(qty)
    sp.grid(row=1, column=1, sticky="w", pady=4)


# ============================================================ patterns
# each gen_* returns (build, theme, fs, question)
def difficulty_by_n(n, base="easy"):
    return "hard" if n >= 8 else ("medium" if n >= 5 and base == "easy" else base)


def gen_chk_list(rng, lang, variant, k):
    cols = 1
    if variant == "neg":
        n = [2, 3, 4, 5, 6, 8, 10][k % 7]
    elif variant == "none":
        n = rng.choice([6, 7, 8])
    else:
        n = rng.choice([4, 5, 6, 7, 8])
    cols = 2 if n >= 9 else 1
    idx = list(range(len(SETTINGS)))
    rng.shuffle(idx)
    labs = [lab(SETTINGS[i], lang) for i in idx[:n]]
    if variant == "neg":
        off = rng.randrange(n)
        states = [i != off for i in range(n)]
    elif variant == "none":
        states = [rng.random() < 0.5 for _ in range(n)]
    else:
        kk = rng.randint(1, n - 1)
        states = [True] * kk + [False] * (n - kk)
        rng.shuffle(states)
    tags = ["synthetic", "tkinter", "settings", "checkbox"]
    head = "Settings" if lang == "en" else "設定"
    items = list(zip(labs, states))
    if variant == "count":
        kk = sum(states)
        N = [3, 4, 5, 6, 8][k % 5]
        wr = numopts(kk, N, rng, 0, max(n, N))
        q = CQ(lang, "How many checkboxes are checked?", "チェックが入っているチェックボックスはいくつありますか？", kk, wr, "count",
               "medium", tags + ["count"])
    elif variant == "neg":
        q = CQ(lang, "Which setting is NOT checked?", "チェックが入っていない設定はどれですか？", labs[off],
               [labs[i] for i in range(n) if i != off], "negation", difficulty_by_n(n, "medium"), tags + ["negation"])
    elif variant == "yn":
        t = CTX.next_yn()
        cands = [i for i in range(n) if states[i] == t] or list(range(n))
        i = pick(rng, cands)
        truth = states[i]
        q = YQ(lang, "'%s' is checked" % labs[i], "「%s」にチェックが入っている" % labs[i], truth, "recognition", "easy", tags + ["yesno"])
    else:  # none of the listed is checked  /  exactly one listed is checked
        unchecked = [i for i in range(n) if not states[i]]
        checked = [i for i in range(n) if states[i]]
        if k % 2 == 0 and len(unchecked) >= 3:
            sel = rng.sample(unchecked, min(len(unchecked), rng.choice([3, 4, 5])))
            q = CQ(lang, "Which of the following settings is checked?", "次の設定のうち、チェックが入っているのはどれですか？", NONE,
                   [labs[i] for i in sel], "negation", "medium", tags + ["none-of-the-above"])
        else:
            if not checked or len(unchecked) < 3:
                states[:] = [i < 2 for i in range(n)]
                rng.shuffle(states)
                items[:] = list(zip(labs, states))
                unchecked = [i for i in range(n) if not states[i]]
                checked = [i for i in range(n) if states[i]]
            c = pick(rng, checked)
            sel = rng.sample(unchecked, min(len(unchecked), rng.choice([2, 3, 4])))
            q = CQ(lang, "Which of the following settings is checked?", "次の設定のうち、チェックが入っているのはどれですか？", labs[c],
                   [labs[i] for i in sel] + [NONE], "recognition", "medium", tags + ["none-of-the-above"])
            # only one of the listed items may be checked: the others are unchecked by construction
    return (lambda a: build_checks(a, head, items, cols)), "clam", 15, q


def gen_chk_group(rng, lang, variant, k):
    idx = list(range(len(SETTINGS)))
    rng.shuffle(idx)
    gi = rng.sample(range(len(GROUPS)), 2)
    groups, pos = [], 0
    sizes = []
    for g in gi:
        sz = rng.choice([3, 4, 5]) if k % 2 == 0 else rng.choice([3, 4])
        sizes.append(sz)
    states_all = []
    for g, sz in zip(gi, sizes):
        sts = [rng.random() < 0.5 for _ in range(sz)]
        if variant == "yn":
            pass
        states_all.append(sts)
    tags = ["synthetic", "tkinter", "settings", "checkbox", "groups"]
    target = rng.randrange(2)
    if variant == "count":
        kk = rng.randint(0, sizes[target])
        sts = [True] * kk + [False] * (sizes[target] - kk)
        rng.shuffle(sts)
        states_all[target] = sts
    elif variant == "yn":
        t = CTX.next_yn()
        sts = states_all[target]
        # statement: "All options in the group are checked" -> true iff all True
        sts[:] = [True] * len(sts) if t else [True] * (len(sts) - 1) + [False]
        rng.shuffle(sts)
    for g, sz, sts in zip(gi, sizes, states_all):
        items = [(lab(SETTINGS[idx[pos + j]], lang), sts[j]) for j in range(sz)]
        pos += sz
        groups.append((lab(GROUPS[g], lang), items))
    gname = groups[target][0]
    sts = states_all[target]
    if variant == "count":
        kk = sum(sts)
        N = [3, 4, 5, 6][k % 4]
        q = CQ(lang, "How many options are checked in the '%s' group?" % gname, "「%s」グループでチェックが入っている項目はいくつですか？" % gname,
               kk, numopts(kk, N, rng, 0, max(sizes[target], N)), "count", "medium", tags + ["count"])
    else:
        q = YQ(lang, "Every option in the '%s' group is checked" % gname, "「%s」グループの項目はすべてチェックされている" % gname, all(sts),
               "recognition", "medium", tags + ["yesno"])
    head = "Preferences" if lang == "en" else "環境設定"
    return (lambda a: build_groups(a, head, groups)), "clam", 15, q


def gen_radio(rng, lang, variant, k):
    N = [2, 4, 6, 8, 5, 10, 3, 4][k % 8]
    gname_pair = RADIO[0] if N > 6 else rng.choice([g for g in RADIO if len(g[2]) >= N])
    opts_all = gname_pair[2]
    sel_idx = sorted(rng.sample(range(len(opts_all)), N))
    opts = [lab(opts_all[i], lang) for i in sel_idx]
    head = lab((gname_pair[0], gname_pair[1]), lang)
    cur = rng.randrange(N)
    tags = ["synthetic", "tkinter", "radio"]
    selected = opts[cur]
    if variant == "none":
        selected = None
        q = CQ(lang, "Which option is selected?", "選択されているのはどれですか？", NONE, opts, "recognition", "medium", tags + ["none-of-the-above"])
    elif variant == "yn":
        t = CTX.next_yn()
        i = cur if t else pick(rng, [j for j in range(N) if j != cur])
        q = YQ(lang, "'%s' is selected" % opts[i], "「%s」が選択されている" % opts[i], i == cur, "recognition", "easy", tags + ["yesno"])
    else:
        q = CQ(lang, "Which option is selected in '%s'?" % head, "「%s」で選択されているのはどれですか？" % head, opts[cur],
               [o for j, o in enumerate(opts) if j != cur], "recognition", difficulty_by_n(N), tags)
    return (lambda a: build_radio(a, head, opts, selected, 2 if N >= 8 else 1)), "clam", 15, q


def gen_combo(rng, lang, variant, k):
    asked = [c for c in COMBOS if len(c[2]) >= 2]
    c = COMBOS[[1, 0, 4, 5, 2, 3][k % 6]]
    others = [x for x in COMBOS if x is not c]
    rows_def = [c] + rng.sample(others, 2)
    rng.shuffle(rows_def)
    rows = []
    cur = {}
    for r in rows_def:
        v = pick(rng, r[2])
        cur[r[0]] = v
        rows.append((lab((r[0], r[1]), lang), r[2], v))
    head = "Preferences" if lang == "en" else "環境設定"
    tags = ["synthetic", "tkinter", "combobox"]
    name = lab((c[0], c[1]), lang)
    if variant == "yn":
        t = CTX.next_yn()
        v = cur[c[0]]
        shown = v if t else pick(rng, [x for x in c[2] if x != v])
        q = YQ(lang, "'%s' is set to '%s'" % (name, shown), "「%s」は「%s」に設定されている" % (name, shown), shown == v, "recognition", "easy", tags + ["yesno"])
    else:
        v = cur[c[0]]
        q = CQ(lang, "What is selected in the '%s' dropdown?" % name, "「%s」のドロップダウンで選ばれているのはどれですか？" % name, v,
               [x for x in c[2] if x != v], "recognition", difficulty_by_n(len(c[2])), tags)
    return (lambda a: build_combos(a, head, rows)), "vista", 15, q


def gen_slider(rng, lang, variant, k):
    n = [3, 7, 10, 7, 10, 3, 10, 7][k % 8]
    ans = CTX.next_score(n)
    bar_only = (n == 3)
    val = value_in_level(n, ans, rng, 8 if bar_only else 3)
    nm = rng.sample(SLIDERS, rng.choice([1, 2, 3]))
    ti = rng.randrange(len(nm))
    rows = []
    for j, p in enumerate(nm):
        v = val if j == ti else rng.choice([v for v in range(5, 96, 5) if abs(v - val) > 12])
        rows.append((lab(p, lang), v))
    name = rows[ti][0]
    tags = ["synthetic", "tkinter", "slider", "score", "score%d" % n]
    q = SQ(lang, "Which range does the '%s' slider value fall into?" % name, "「%s」スライダーの値はどの範囲にありますか？" % name, n, ans, "quantity",
           "easy" if n == 3 else "medium", tags)
    show = not bar_only
    return (lambda a: build_sliders(a, rows, show)), "clam", 15, q


def gen_progress(rng, lang, variant, k):
    n = [7, 3, 10, 10, 7, 3, 7, 10][k % 8]
    ans = CTX.next_score(n)
    bar_only = (n == 3)
    val = value_in_level(n, ans, rng, 8 if bar_only else 3)
    nm = rng.sample(PROGRESS, rng.choice([1, 2]))
    ti = rng.randrange(len(nm))
    rows = []
    for j, p in enumerate(nm):
        v = val if j == ti else rng.choice([v for v in range(5, 96, 5) if abs(v - val) > 12])
        rows.append((lab(p, lang), v))
    name = rows[ti][0]
    tags = ["synthetic", "tkinter", "progressbar", "score", "score%d" % n]
    q = SQ(lang, "How far along is the '%s' bar?" % name, "「%s」のバーはどれくらい進んでいますか？" % name, n, ans, "quantity",
           "easy" if n == 3 else "medium", tags)
    show = not bar_only
    return (lambda a: build_bars(a, rows, show)), "vista", 15, q


def gen_prog_cmp(rng, lang, variant, k):
    N = [3, 4, 5, 6][k % 4]
    nm = rng.sample(PROGRESS, N)
    vals = rng.sample(range(8, 97, 8), N)
    rows = [(lab(p, lang), v) for p, v in zip(nm, vals)]
    hi = k % 2 == 0
    best = max(range(N), key=lambda i: vals[i]) if hi else min(range(N), key=lambda i: vals[i])
    names = [r[0] for r in rows]
    en_i = "Which task has the %s progress?" % ("highest" if hi else "lowest")
    ja_i = "進捗が最も%sのはどれですか？" % ("高い" if hi else "低い")
    q = CQ(lang, en_i, ja_i, names[best], [x for i, x in enumerate(names) if i != best], "compare", difficulty_by_n(N),
           ["synthetic", "tkinter", "progressbar", "compare"])
    return (lambda a: build_bars(a, rows, False, 360)), "vista", 15, q


def gen_switches(rng, lang, variant, k):
    n = [3, 4, 5, 6, 7, 8][k % 6]
    names = [lab(p, lang) for p in rng.sample(SWITCHES, n)]
    tags = ["synthetic", "tkinter", "switch"]
    show = k % 2 == 0
    head = "Quick settings" if lang == "en" else "クイック設定"
    if variant == "neg":
        off = rng.randrange(n)
        states = [i != off for i in range(n)]
        q = CQ(lang, "Which switch is OFF?", "オフになっているスイッチはどれですか？", names[off], [x for i, x in enumerate(names) if i != off], "recognition",
               difficulty_by_n(n), tags + ["negation"])
    elif variant == "yn":
        states = [rng.random() < 0.5 for _ in range(n)]
        t = CTX.next_yn()
        i = pick(rng, [j for j in range(n) if states[j] == t] or list(range(n)))
        q = YQ(lang, "The '%s' switch is on" % names[i], "「%s」のスイッチはオンになっている" % names[i], states[i], "recognition", "easy", tags + ["yesno"])
    else:
        kk = rng.randint(1, n - 1)
        states = [True] * kk + [False] * (n - kk)
        rng.shuffle(states)
        N = [3, 4, 5, 6][k % 4]
        q = CQ(lang, "How many switches are ON?", "オンになっているスイッチはいくつですか？", kk, numopts(kk, N, rng, 0, max(n, N)), "count", "medium",
               tags + ["count"])
    items = list(zip(names, states))
    return (lambda a: build_switches(a, head, items, show)), "clam", 15, q


def gen_form_err(rng, lang, variant, k):
    n = [3, 4, 5, 6, 6, 5, 4, 6][k % 8]
    fidx = rng.sample(range(len(FIELDS)), n)
    L = 0 if lang == "en" else 1
    if variant == "which":
        err_set = {rng.randrange(n)}
    elif variant == "count":
        err_set = set(rng.sample(range(n), rng.randint(1, min(n - 1, 4))))
    elif variant == "msg":
        err_set = {rng.randrange(n)}
    else:
        err_set = set(rng.sample(range(n), rng.randint(1, min(n - 1, 3))))
    rows, names, kinds = [], [], []
    for j, fi in enumerate(fidx):
        f = FIELDS[fi]
        names.append(f[1 + 0] if lang == "ja" else f[0])
        if j in err_set:
            kind = f[4]
            txt = BAD[kind]
            rows.append((names[-1], txt, ERR[kind][L], kind == "short"))
            kinds.append(kind)
        else:
            rows.append((names[-1], f[2 + L], None, f[0] == "Password"))
            kinds.append(None)
    tags = ["synthetic", "tkinter", "form", "validation"]
    head = "Sign up" if lang == "en" else "新規登録"
    if variant == "which":
        e = next(iter(err_set))
        q = CQ(lang, "Which field shows an error message?", "エラーメッセージが表示されているのはどの項目ですか？", names[e],
               [x for i, x in enumerate(names) if i != e], "recognition", difficulty_by_n(n), tags + ["error"])
    elif variant == "count":
        kk = len(err_set)
        N = [3, 4, 5, 6][k % 4]
        q = CQ(lang, "How many fields show an error message?", "エラーメッセージが表示されている項目はいくつですか？", kk,
               numopts(kk, N, rng, 0, max(n, N)), "count", "medium", tags + ["count"])
    elif variant == "msg":
        e = next(iter(err_set))
        msgs = [ERR[x][L] for x in ("required", "email", "digits", "short")]
        correct = ERR[kinds[e]][L]
        N = rng.choice([3, 4])
        wr = [m for m in msgs if m != correct][: N - 1]
        q = CQ(lang, "What does the error message say?", "エラーメッセージの内容はどれですか？", correct, wr, "ocr", "easy", tags + ["error"])
    else:
        t = CTX.next_yn()
        cand = [i for i in range(n) if (i in err_set) == t] or list(range(n))
        i = pick(rng, cand)
        q = YQ(lang, "The '%s' field shows an error message" % names[i], "「%s」の項目にエラーメッセージが表示されている" % names[i], i in err_set,
               "recognition", "easy", tags + ["yesno"])
    return (lambda a: build_form(a, head, rows, L)), "vista", 15, q


def gen_form_val(rng, lang, variant, k):
    n = [3, 4, 5, 6][k % 4]
    L = 0 if lang == "en" else 1
    defs = rng.sample(VALUES, n)
    vals = [pick(rng, d[2 + L]) for d in defs]
    names = [d[L] for d in defs]
    rows = [(names[i], vals[i], None, False) for i in range(n)]
    ai = rng.randrange(n)
    d = defs[ai]
    pool = d[2 + L]
    tags = ["synthetic", "tkinter", "form", "entry"]
    head = "Profile" if lang == "en" else "プロフィール"
    if variant == "yn":
        t = CTX.next_yn()
        shown = vals[ai] if t else pick(rng, [x for x in pool if x != vals[ai]])
        q = YQ(lang, "The '%s' field contains '%s'" % (names[ai], shown), "「%s」には「%s」と入力されている" % (names[ai], shown), shown == vals[ai], "ocr", "easy",
               tags + ["yesno"])
    else:
        N = [3, 4, 5, 6][k % 4]
        wr = [x for x in pool if x != vals[ai]][: N - 1]
        q = CQ(lang, "What is entered in the '%s' field?" % names[ai], "「%s」に入力されている値はどれですか？" % names[ai], vals[ai], wr, "ocr",
               "easy" if N <= 4 else "medium", tags)
    return (lambda a: build_form(a, head, rows, L)), "vista", 15, q


def gen_dialog_btn(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    cand = [d for d in DLG if len(d[4]) >= (3 if variant == "en1" else 2)]
    if k % 5 == 4:
        cand = [d for d in DLG if len(d[4]) >= 4]
    d = pick(rng, cand)
    kind, ten, tja, cat, btns = d
    msg = (ten, tja)[L]
    nb = len(btns)
    code = None
    if variant == "code":
        code = "E-%d" % rng.randrange(1000, 9999)
        msg = msg + ("\n" + ("Error code: %s" if L == 0 else "エラーコード: %s") % code)
    dis = set()
    tags = ["synthetic", "tkinter", "dialog", "button-state"]
    names = [lab(BTN[b], lang) for b in btns]
    if variant == "dis1":
        dd = rng.randrange(nb)
        dis = {btns[dd]}
        q = CQ(lang, "Which button is disabled (grayed out)?", "無効（グレーアウト）になっているボタンはどれですか？", names[dd],
               [x for i, x in enumerate(names) if i != dd], "recognition", difficulty_by_n(nb, "medium"), tags)
    elif variant == "en1":
        ee = rng.randrange(nb)
        dis = {b for i, b in enumerate(btns) if i != ee}
        q = CQ(lang, "Which button is NOT disabled?", "無効になっていないボタンはどれですか？", names[ee], [x for i, x in enumerate(names) if i != ee],
               "negation", "medium", tags + ["negation"])
    elif variant == "cnt":
        kk = rng.randint(1, nb - 1)
        dis = set(rng.sample(btns, nb - kk))
        N = [3, 4, 5][k % 3]
        q = CQ(lang, "How many buttons can be clicked?", "クリックできるボタンはいくつですか？", kk, numopts(kk, N, rng, 1, max(nb, N)), "count",
               "medium", tags + ["count"])
    elif variant == "yn":
        dis = set(rng.sample(btns, rng.randint(1, nb - 1)))
        t = CTX.next_yn()
        cand_b = [i for i, b in enumerate(btns) if (b in dis) == t]
        i = pick(rng, cand_b)
        q = YQ(lang, "The '%s' button is disabled" % names[i], "「%s」ボタンは無効になっている" % names[i], btns[i] in dis, "recognition", "easy", tags + ["yesno"])
    else:  # code
        dis = set(rng.sample(btns, rng.randint(0, nb - 1)))
        N = [4, 5, 6][k % 3]
        wr = []
        while len(wr) < N - 1:
            c = "E-%d" % rng.randrange(1000, 9999)
            if c != code and c not in wr:
                wr.append(c)
        q = CQ(lang, "What error code is shown in the dialog?", "ダイアログに表示されているエラーコードはどれですか？", code, wr, "ocr", "medium",
               ["synthetic", "tkinter", "dialog", "ocr"])
    return (lambda a: build_dialog(a, kind, msg, btns, dis)), "vista", 15, q


def gen_dialog_cat(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    cats = [d for d in DLG if d[3]]
    d = cats[k % len(cats)] if k < len(cats) else pick(rng, cats)
    kind, ten, tja, cat, btns = d
    N = [3, 4, 5, 6][k % 4]
    wr = [c[3] for c in cats if c[3] != cat]
    rng.shuffle(wr)
    q = CQ(lang, "What kind of problem does the dialog report?", "このダイアログが伝えている問題の種類はどれですか？", cat, wr[: N - 1], "recognition", "medium",
           ["synthetic", "tkinter", "dialog", "error-type"])
    msg = (ten, tja)[L]
    return (lambda a: build_dialog(a, kind, msg, btns, set())), "vista", 15, q


def make_table(rng, lang, n, distinct_col=1):
    idx = rng.sample(range(len(PRODUCTS)), n)
    qty = rng.sample(range(3, 60), n)
    price = [rng.randrange(2, 20) for _ in range(n)]
    rows = [(lab(PRODUCTS[idx[i]], lang), qty[i], "%d.%02d" % (price[i], rng.choice([0, 25, 50, 75, 99]))) for i in range(n)]
    cols = ["Product", "Qty", "Price"] if lang == "en" else ["商品", "数量", "価格"]
    return rows, cols, idx


def gen_tree_maxmin(rng, lang, variant, k):
    n = [4, 5, 6, 3, 7, 8][k % 6]
    rows, cols, idx = make_table(rng, lang, n)
    hi = k % 2 == 0
    best = max(range(n), key=lambda i: rows[i][1]) if hi else min(range(n), key=lambda i: rows[i][1])
    names = [r[0] for r in rows]
    extras = [lab(p, lang) for p in PRODUCTS if lab(p, lang) not in names]
    N = {3: 4, 4: 6, 5: 5, 6: 6, 7: 8, 8: 10}[n]
    wr = fill(rng, [x for i, x in enumerate(names) if i != best], extras, N)
    q = CQ(lang, "Which product has the %s quantity?" % ("largest" if hi else "smallest"),
           "数量が最も%s商品はどれですか？" % ("多い" if hi else "少ない"), names[best], wr, "compare", difficulty_by_n(len(wr) + 1, "medium"),
           ["synthetic", "tkinter", "table", "treeview", "compare"])
    head = "Inventory" if lang == "en" else "在庫一覧"
    return (lambda a: build_tree(a, head, cols, rows)), "vista", 17, q


def gen_tree_sum(rng, lang, variant, k):
    n = [3, 4, 5, 4, 6, 5][k % 6]
    rows, cols, idx = make_table(rng, lang, n)
    head = "Inventory" if lang == "en" else "在庫一覧"
    tags = ["synthetic", "tkinter", "table", "treeview"]
    if k % 2 == 0:
        s = sum(r[1] for r in rows)
        N = [4, 5, 6][k % 3]
        pool = [s + d for d in (-10, -5, -3, -2, -1, 1, 2, 3, 5, 10) if s + d > 0]
        rng.shuffle(pool)
        q = CQ(lang, "What is the total of the Qty column?", "数量の列の合計はいくつですか？", s, pool[: N - 1], "quantity", "medium", tags + ["sum"])
    else:
        thr = 20
        kk = sum(1 for r in rows if r[1] > thr)
        N = [3, 4, 5][k % 3]
        q = CQ(lang, "How many rows have a Qty greater than 20?", "数量が 20 より大きい行はいくつですか？", kk, numopts(kk, N, rng, 0, max(n, N)), "count", "medium",
               tags + ["count"])
    return (lambda a: build_tree(a, head, cols, rows)), "vista", 17, q


def gen_tree_sel(rng, lang, variant, k):
    n = [4, 5, 6, 3, 7, 5][k % 6]
    rows, cols, idx = make_table(rng, lang, n)
    sel = rng.randrange(n)
    names = [r[0] for r in rows]
    head = "Inventory" if lang == "en" else "在庫一覧"
    tags = ["synthetic", "tkinter", "table", "treeview", "selection"]
    if k % 3 == 2:
        correct = rows[sel][1]
        N = 4
        wr = [r[1] for i, r in enumerate(rows) if i != sel]
        rng.shuffle(wr)
        wr = (wr + [correct + d for d in (-3, 4, 7, -6) if correct + d > 0])[: N - 1]
        q = CQ(lang, "What is the Qty of the highlighted row?", "ハイライトされている行の数量はいくつですか？", correct, wr, "ocr", "medium", tags)
    else:
        q = CQ(lang, "Which product is highlighted?", "ハイライトされている商品はどれですか？", names[sel], [x for i, x in enumerate(names) if i != sel],
               "recognition", difficulty_by_n(n), tags)
    return (lambda a: build_tree(a, head, cols, rows, sel)), "vista", 17, q


def gen_tree_sorted(rng, lang, variant, k):
    n = [4, 5, 6, 5, 4, 6][k % 6]
    rows, cols, idx = make_table(rng, lang, n)
    mode = ["asc", "desc", "none"][k % 3]
    if mode == "asc":
        rows.sort(key=lambda r: r[1])
    elif mode == "desc":
        rows.sort(key=lambda r: -r[1])
    else:
        while True:
            rng.shuffle(rows)
            q_ = [r[1] for r in rows]
            if q_ != sorted(q_) and q_ != sorted(q_, reverse=True):
                break
    head = "Inventory" if lang == "en" else "在庫一覧"
    tags = ["synthetic", "tkinter", "table", "treeview", "sort"]
    if k % 2 == 0:
        q = CQ(lang, "How are the rows ordered by Qty?", "数量による行の並びはどれですか？",
               {"asc": ("Ascending", "昇順"), "desc": ("Descending", "降順"), "none": ("Not sorted", "並んでいない")}[mode],
               [v for m, v in (("asc", ("Ascending", "昇順")), ("desc", ("Descending", "降順")), ("none", ("Not sorted", "並んでいない"))) if m != mode],
               "compare", "medium", tags)
    else:
        t = CTX.next_yn()
        # the statement is "Qty increases from top to bottom": true only for asc
        if t and mode != "asc":
            rows.sort(key=lambda r: r[1])
            mode = "asc"
        elif not t and mode == "asc":
            rows.sort(key=lambda r: -r[1])
            mode = "desc"
        q = YQ(lang, "The Qty values increase from top to bottom", "数量は上から下へ増えていく", mode == "asc", "compare", "medium", tags + ["yesno"])
    return (lambda a: build_tree(a, head, cols, rows)), "vista", 17, q


def gen_notebook(rng, lang, variant, k):
    nt = [3, 4, 5, 4, 3, 5, 4, 5][k % 8]
    tabs_p = rng.sample(TABS, nt)
    tabs = [lab(p, lang) for p in tabs_p]
    cur = rng.randrange(nt)
    tags = ["synthetic", "tkinter", "notebook", "tabs"]
    lines = ["▬▬▬▬▬▬▬▬▬▬▬", "▬▬▬▬▬▬▬▬"]
    if variant == "count":
        N = [3, 4, 5, 6][k % 4]
        q = CQ(lang, "How many tabs does the window have?", "このウィンドウにはタブがいくつありますか？", nt, numopts(nt, N, rng, 2, max(nt + 2, N + 2)), "count", "easy", tags + ["count"])
    elif variant == "yn":
        t = CTX.next_yn()
        i = cur if t else pick(rng, [j for j in range(nt) if j != cur])
        q = YQ(lang, "The '%s' tab is currently selected" % tabs[i], "「%s」タブが選択されている" % tabs[i], i == cur, "recognition", "easy", tags + ["yesno"])
    else:
        N = [nt, nt, 6, 8][k % 4]
        extras = [lab(p, lang) for p in TABS if lab(p, lang) not in tabs]
        wr = fill(rng, [x for i, x in enumerate(tabs) if i != cur], extras, max(N, nt))
        q = CQ(lang, "Which tab is currently selected?", "現在選択されているタブはどれですか？", tabs[cur], wr, "recognition",
               difficulty_by_n(len(wr) + 1), tags)
    return (lambda a: build_notebook(a, tabs, cur, lines)), "clam", 15, q


def gen_menu(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    mi = k % 2
    mname, mja, items_all = MENUS[mi]
    n = [3, 4, 5, 6, 7, 8][k % 6]
    sub = sorted(rng.sample(range(len(items_all)), n))
    sub_items = [items_all[i] for i in sub]
    names = [it[L] for it in sub_items]
    tags = ["synthetic", "tkinter", "menu", "disabled"]
    if variant == "dis1":
        d = {rng.randrange(n)}
        q = CQ(lang, "Which menu item is grayed out (disabled)?", "グレーアウト（無効）になっているメニュー項目はどれですか？", names[next(iter(d))],
               [x for i, x in enumerate(names) if i not in d], "recognition", difficulty_by_n(n, "medium"), tags)
    elif variant == "cnt":
        kk = rng.randint(1, n - 1)
        d = set(rng.sample(range(n), kk))
        N = [3, 4, 5][k % 3]
        q = CQ(lang, "How many menu items are grayed out?", "グレーアウトされているメニュー項目はいくつですか？", kk, numopts(kk, N, rng, 0, max(n, N)), "count",
               "medium", tags + ["count"])
    else:
        d = set(rng.sample(range(n), rng.randint(1, n - 1)))
        t = CTX.next_yn()
        i = pick(rng, [j for j in range(n) if (j not in d) == t])
        q = YQ(lang, "'%s' can be selected in the menu" % names[i], "メニューの「%s」は選択できる" % names[i], i not in d, "rules", "medium", tags + ["yesno"])
    items = [(it[L], it[2], i in d) for i, it in enumerate(sub_items)]
    menus = [m[L] for m in MENUS] + [("View", "表示")[L]]
    return (lambda a: build_menu(a, menus, mi, items)), "vista", 15, q


def gen_list_spin(rng, lang, variant, k):
    n = [3, 4, 5, 6][k % 4]
    items = [lab(p, lang) for p in rng.sample(LIST_ITEMS, n)]
    cur = rng.randrange(n)
    qty = rng.randrange(1, 40)
    tags = ["synthetic", "tkinter", "listbox", "spinbox"]
    if k % 2 == 0:
        q = CQ(lang, "Which item is highlighted in the list?", "リストでハイライトされている項目はどれですか？", items[cur], [x for i, x in enumerate(items) if i != cur],
               "recognition", "easy", tags)
    else:
        t = CTX.next_yn()
        shown = qty if t else qty + pick(rng, [-3, -2, 2, 5, 9])
        q = YQ(lang, "The quantity box shows %d" % shown, "数量の欄には %d と表示されている" % shown, shown == qty, "ocr", "easy", tags + ["yesno"])
    return (lambda a: build_list_spin(a, items, cur, qty)), "vista", 15, q


# ============================================================ compound screens (medium / hard)
def statusbar(a, text):
    tk.Label(a.root, text=" " + text, anchor="w", bg="#cfcfcf", fg="black", font=a.bold).pack(side="bottom", fill="x")


MAIL_FOLDERS = [("Inbox", "受信箱"), ("Drafts", "下書き"), ("Sent", "送信済み"), ("Archive", "保存済み"), ("Spam", "迷惑メール"), ("Trash", "ごみ箱")]
MAIL_ROWS = [("Amy", "Invoice", "エミ", "請求書"), ("Ben", "Lunch?", "ケン", "ランチ"), ("Chloe", "Report", "ユイ", "報告書"), ("Dan", "Meeting", "ソウ", "会議"),
             ("Eva", "Update", "リナ", "更新"), ("Finn", "Tickets", "タク", "チケット")]
EXTRA_FOLDERS = [("Notes", "メモ"), ("Work", "仕事"), ("Travel", "旅行"), ("Receipts", "領収書")]


def build_mail(a, folders, sel, rows, status):
    a.body.configure(padding=(8, 8))
    wrap = ttk.Frame(a.body)
    wrap.pack()
    side = tk.Frame(wrap, bg="#e4e6ee")
    side.pack(side="left", fill="y")
    for i, (name, unread) in enumerate(folders):
        bg = "#2f6fd0" if i == sel else "#e4e6ee"
        row = tk.Frame(side, bg=bg)
        row.pack(fill="x")
        tk.Label(row, text=name, font=a.bold, fg="white" if i == sel else "black", bg=bg, anchor="w", width=8 if a.lang == "en" else 9, padx=6, pady=6).pack(side="left")
        if unread:
            tk.Label(row, text=str(unread), font=a.bold, bg="#d32f2f", fg="white", padx=6).pack(side="left", padx=2)
    tv = ttk.Treeview(wrap, columns=(0, 1), show="headings", height=len(rows))
    tv.heading(0, text="From" if a.lang == "en" else "差出人")
    tv.heading(1, text="Subject" if a.lang == "en" else "件名")
    tv.column(0, width=a.fs * 6)
    tv.column(1, width=a.fs * 8)
    tv.tag_configure("u", font=a.bold)
    for fr, sub, unread in rows:
        tv.insert("", "end", values=(fr, sub), tags=("u",) if unread else ())
    tv.pack(side="left", anchor="n", padx=(8, 0))
    statusbar(a, status)


def gen_mail(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nf = rng.choice([4, 5, 6])
    fol = rng.sample(MAIL_FOLDERS, nf)
    names = [f[L] for f in fol]
    if variant == "max":
        unread = rng.sample(range(0, 15), nf)
    else:
        unread = [rng.choice([0, 0, 1, 2, 3, 4, 5, 8, 11]) for _ in range(nf)]
    sel = rng.randrange(nf)
    if variant != "max":
        unread[sel] = max(unread[sel], 1)
    nr = rng.choice([3, 4, 5])
    pool = rng.sample(MAIL_ROWS, nr)
    flags = [rng.random() < 0.5 for _ in range(nr)]
    if not any(flags):
        flags[0] = True
    bold = sum(flags)
    tags = ["synthetic", "tkinter", "compound", "mail", "multi-widget"]
    if variant == "cross":
        t = CTX.next_yn()
        unread[sel] = bold if t else bold + rng.choice([1, 2, 3])
    rows = [(p[2 * L], p[2 * L + 1], f) for p, f in zip(pool, flags)]
    msgs = nr
    if variant == "status":
        t = CTX.next_yn()
        msgs = nr if t else nr + rng.choice([1, 2])
    status = ("%d messages" % msgs) if lang == "en" else "%d 件のメッセージ" % msgs
    folders = list(zip(names, unread))
    if variant == "sum":
        s = sum(unread)
        N = rng.choice([4, 5, 6])
        pool_n = [s + d for d in (-3, -2, -1, 1, 2, 3, 5, 10) if s + d >= 0]
        rng.shuffle(pool_n)
        q = CQ(lang, "What is the total of the red unread badges in the sidebar?", "サイドバーの赤い未読バッジの合計はいくつですか？", s, pool_n[: N - 1],
               "quantity", "medium", tags + ["sum"])
    elif variant == "max":
        best = max(range(nf), key=lambda i: unread[i])
        ex = [f[L] for f in MAIL_FOLDERS + EXTRA_FOLDERS if f[L] not in names]
        N = rng.choice([nf, 6, 8])
        wr = fill(rng, [n for i, n in enumerate(names) if i != best], ex, max(N, nf))
        q = CQ(lang, "Which folder has the most unread messages?", "未読メッセージが最も多いフォルダーはどれですか？", names[best], wr, "compare",
               "medium" if len(wr) < 6 else "hard", tags + ["compare"])
    elif variant == "status":
        q = YQ(lang, "The number in the status bar equals the number of rows in the table", "ステータスバーの件数は表の行数と一致している", msgs == nr, "compare",
               "hard", tags + ["yesno", "cross-check"])
    elif variant == "bold":
        N = rng.choice([4, 5, 6])
        q = CQ(lang, "How many messages in the table are unread (bold)?", "表の中で未読（太字）のメッセージはいくつですか？", bold, numopts(bold, N, rng, 0, max(nr, N)),
               "count", "hard", tags + ["count"])
    else:
        q = YQ(lang, "The number of bold rows in the table equals the badge of the selected folder",
               "表の太字の行数は、選択中のフォルダーのバッジの数と一致している", unread[sel] == bold, "compare", "hard", tags + ["yesno", "cross-check"])
    return (lambda a: build_mail(a, folders, sel, rows, status)), "clam", 14, q


ST = {"Paid": ("Paid", "支払済", "#d5f0d5"), "Pending": ("Pending", "保留", "#fff2c0"), "Error": ("Error", "エラー", "#f8c9c9"),
      "Cancelled": ("Cancelled", "取消", "#e3e3e3")}


def build_orders(a, tabs, rows, status):
    a.body.configure(padding=(8, 8))
    a.st.configure("TNotebook.Tab", padding=(10, 5), font=a.bold)
    a.st.map("TNotebook.Tab", background=[("selected", "#2f6fd0"), ("!selected", "#c9c9c9")], foreground=[("selected", "white"), ("!selected", "#222222")])
    nb = ttk.Notebook(a.body)
    pages = []
    for t in tabs:
        fr = ttk.Frame(nb, padding=6)
        nb.add(fr, text=t)
        pages.append(fr)
    tv = ttk.Treeview(pages[0], columns=(0, 1, 2), show="headings", height=len(rows))
    hd = ["Order", "Status", "Amount"] if a.lang == "en" else ["注文", "状態", "金額"]
    for i, h in enumerate(hd):
        tv.heading(i, text=h)
        tv.column(i, width=a.fs * (6 if i != 1 else 8), anchor="w" if i < 2 else "e")
    for key, v in ST.items():
        tv.tag_configure(key, background=v[2])
    for oid, st, amt in rows:
        tv.insert("", "end", values=(oid, ST[st][0 if a.lang == "en" else 1], amt), tags=(st,))
    tv.pack()
    ttk.Label(pages[1], text="...", foreground="#888888").pack()
    nb.select(0)
    nb.pack()
    statusbar(a, status)


def gen_orders(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nr = rng.choice([5, 6, 7])
    ids = sorted(rng.sample(range(1001, 1099), nr))
    amts = rng.sample(range(10, 100, 5), nr)
    sts = None
    for _ in range(2000):
        cand = [rng.choice(["Paid", "Paid", "Pending", "Error", "Cancelled"]) for _ in range(nr)]
        c = collections.Counter(cand)
        top = c.most_common()
        if c["Paid"] >= 2 and c["Pending"] >= 2 and c["Error"] >= 1 and (len(top) == 1 or top[0][1] > top[1][1]):
            sts = cand
            break
    if sts is None:
        sts = (["Paid", "Paid", "Paid", "Pending", "Pending", "Error", "Error"])[:nr]
    rows = [("#%d" % ids[i], sts[i], amts[i]) for i in range(nr)]
    tabs = ["Orders", "Customers", "Reports"] if lang == "en" else ["注文", "顧客", "レポート"]
    shown = nr
    tags = ["synthetic", "tkinter", "compound", "orders", "notebook", "treeview", "multi-widget"]
    if variant == "status":
        t = CTX.next_yn()
        shown = nr if t else nr + rng.choice([1, 2])
    status = ("Showing %d orders" % shown) if lang == "en" else "%d 件の注文を表示中" % shown
    pn = ST["Paid"][L]
    if variant == "paidsum":
        s = sum(r[2] for r in rows if r[1] == "Paid")
        N = rng.choice([4, 5, 6])
        pool_n = [s + d for d in (-10, -5, 5, 10, -15, 15, 20, -20) if s + d > 0]
        rng.shuffle(pool_n)
        q = CQ(lang, "What is the total Amount of the rows whose status is Paid?", "状態が「%s」の行の金額の合計はいくつですか？" % pn, s, pool_n[: N - 1],
               "quantity", "hard", tags + ["sum", "conditional"])
    elif variant == "errbig":
        kk = sum(1 for r in rows if r[1] == "Error" and r[2] > 50)
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "How many rows have the status Error and an Amount above 50?", "状態が「%s」で、金額が 50 を超える行はいくつですか？" % ST["Error"][L], kk,
               numopts(kk, N, rng, 0, max(N, 4)), "count", "hard", tags + ["count", "conditional"])
    elif variant == "status":
        q = YQ(lang, "The number in the status bar equals the number of rows in the table", "ステータスバーの件数は表の行数と一致している", shown == nr, "compare", "hard",
               tags + ["yesno", "cross-check"])
    elif variant == "maxpend":
        pend = [r for r in rows if r[1] == "Pending"]
        best = max(pend, key=lambda r: r[2])
        wr = [r[0] for r in rows if r is not best]
        q = CQ(lang, "Which order has the highest Amount among the Pending rows?", "状態が「%s」の行のうち、金額が最も大きい注文はどれですか？" % ST["Pending"][L], best[0], wr,
               "compare", "hard", tags + ["compare", "conditional"])
    else:
        c = collections.Counter(r[1] for r in rows)
        mode = c.most_common(1)[0][0]
        others = [ST[x][L] for x in ST if x != mode]
        q = CQ(lang, "Which status appears most often in the table?", "表で最も多く現れている状態はどれですか？", ST[mode][L], others, "count", "medium",
               tags + ["count"])
    return (lambda a: build_orders(a, tabs, rows, status)), "clam", 14, q


CONDS = [("Auto update ON", "「自動更新」オン", lambda A, B: A), ("Auto update OFF", "「自動更新」オフ", lambda A, B: not A),
         ("Notifications ON", "「通知」オン", lambda A, B: B), ("Notifications OFF", "「通知」オフ", lambda A, B: not B),
         ("both ON", "両方オン", lambda A, B: A and B),
         ("Auto update ON, Notifications OFF", "「自動更新」オン・「通知」オフ", lambda A, B: A and not B),
         ("both OFF", "両方オフ", lambda A, B: not A and not B)]
ACTIONS = [("Sync now", "今すぐ同期"), ("Export", "エクスポート"), ("Reset", "リセット"), ("Publish", "公開")]
LOCKED = [("Admin mode", "管理者モード"), ("Safe mode", "セーフモード"), ("Debug log", "デバッグログ"), ("Beta channel", "ベータ版"), ("Telemetry", "テレメトリ")]


def build_rules(a, A, B, locked, acts):
    a.body.configure(padding=(10, 8))
    top = ttk.Frame(a.body)
    top.pack(anchor="w")
    lf = ttk.Labelframe(top, text="Settings" if a.lang == "en" else "設定", padding=(10, 4))
    lf.pack(side="left", anchor="n")
    for name, on in (("Auto update" if a.lang == "en" else "自動更新", A), ("Notifications" if a.lang == "en" else "通知", B)):
        v = tk.BooleanVar(master=a.root, value=on)
        a.keep.append(v)
        ttk.Checkbutton(lf, text=name, variable=v).pack(anchor="w", pady=3)
    lk = ttk.Labelframe(top, text="Locked" if a.lang == "en" else "変更不可", padding=(10, 4))
    lk.pack(side="left", anchor="n", padx=(14, 0))
    for name, on in locked:
        v = tk.BooleanVar(master=a.root, value=on)
        a.keep.append(v)
        c = ttk.Checkbutton(lk, text=name, variable=v)
        c.state(["disabled"])
        c.pack(anchor="w", pady=2)
    hf = ttk.Labelframe(a.body, text="Help" if a.lang == "en" else "ヘルプ", padding=(10, 4))
    hf.pack(anchor="w", pady=(8, 0), fill="x")
    for name, cond in acts:
        r = ttk.Frame(hf)
        r.pack(anchor="w", pady=2)
        ttk.Button(r, text=name, width=11).pack(side="left")
        txt = ("needs: %s" % cond[0]) if a.lang == "en" else "条件: %s" % cond[1]
        ttk.Label(r, text=txt, font=a.font).pack(side="left", padx=8)


def gen_rules(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    A, B = rng.random() < 0.5, rng.random() < 0.5
    nact = rng.choice([3, 4])
    acts_n = rng.sample(ACTIONS, nact)
    cs, truth = None, None
    for _ in range(500):
        cs = rng.sample(CONDS, nact)
        truth = [c[2](A, B) for c in cs]
        if variant == "which" and sum(truth) == 1:
            break
        if variant == "cnt" and 1 <= sum(truth) <= nact - 1:
            break
        if variant in ("yn", "locked") and 1 <= sum(truth) <= nact - 1:
            break
    names = [x[L] for x in acts_n]
    cons = list(zip(names, cs))
    locked = [(x[L], rng.random() < 0.5) for x in rng.sample(LOCKED, rng.choice([3, 4, 5]))]
    tags = ["synthetic", "tkinter", "compound", "rules", "multi-widget"]
    if variant == "which":
        if sum(truth) != 1:
            raise RuntimeError("no rule set with exactly one usable button")
        i = truth.index(True)
        q = CQ(lang, "Following the help text and the current settings, which button can be used?", "ヘルプの条件と現在の設定に従うと、使えるボタンはどれですか？", names[i],
               [n for j, n in enumerate(names) if j != i], "rules", "hard", tags + ["rule-application"])
    elif variant == "cnt":
        kk = sum(truth)
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "Following the help text and the current settings, how many buttons can be used?", "ヘルプの条件と現在の設定に従うと、使えるボタンはいくつですか？", kk,
               numopts(kk, N, rng, 0, max(N, nact)), "rules", "hard", tags + ["rule-application", "count"])
    elif variant == "yn":
        t = CTX.next_yn()
        cand = [j for j in range(nact) if truth[j] == t] or list(range(nact))
        j = pick(rng, cand)
        q = YQ(lang, "With the current settings, the '%s' button can be used" % names[j], "現在の設定では、「%s」ボタンは使える" % names[j], truth[j], "rules",
               "hard", tags + ["yesno", "rule-application"])
    else:
        kk = sum(1 for n, on in locked if on)
        N = rng.choice([3, 4, 5, 6])
        q = CQ(lang, "How many of the grayed-out (locked) options are checked?", "グレーアウトされている（変更不可の）項目のうち、チェックが入っているのはいくつですか？", kk,
               numopts(kk, N, rng, 0, max(N, len(locked))), "count", "medium", tags + ["count", "disabled"])
    return (lambda a: build_rules(a, A, B, locked, cons)), "clam", 15, q


def build_overlap(a, rows, selected, n_dialog):
    a.body.configure(padding=(0, 0))
    box = tk.Frame(a.body, width=520, height=400, bg=a.bgc)
    box.pack_propagate(False)
    box.pack()
    tb = ttk.Frame(box, padding=6)
    tb.pack(fill="x")
    for t in (("New", "Edit", "Delete") if a.lang == "en" else ("新規", "編集", "削除")):
        ttk.Button(tb, text=t, width=7).pack(side="left", padx=3)
    tv = ttk.Treeview(box, columns=(0, 1), show="headings", height=len(rows), selectmode="extended")
    tv.heading(0, text="Name" if a.lang == "en" else "名前")
    tv.heading(1, text="Qty" if a.lang == "en" else "数量")
    tv.column(0, width=300)
    tv.column(1, width=170, anchor="e")
    ids = [tv.insert("", "end", values=r) for r in rows]
    tv.selection_set([ids[i] for i in selected])
    tv.pack(padx=8, anchor="w")
    dlg = tk.Frame(box, bg="white", highlightthickness=2, highlightbackground="#444444")
    hd = tk.Frame(dlg, bg="#c62828")
    hd.pack(fill="x")
    tk.Label(hd, text="Confirm delete" if a.lang == "en" else "削除の確認", bg="#c62828", fg="white", font=a.bold, padx=10, pady=4).pack(anchor="w")
    tk.Label(dlg, text=("Delete %d items?" % n_dialog) if a.lang == "en" else "%d 件の項目を削除しますか？" % n_dialog, bg="white", font=a.bold, padx=14, pady=14).pack()
    bf = tk.Frame(dlg, bg="white")
    bf.pack(pady=(0, 10))
    for t in (("Delete", "Cancel") if a.lang == "en" else ("削除", "キャンセル")):
        ttk.Button(bf, text=t, width=9).pack(side="left", padx=5)
    dlg.place(x=190, y=150)


def gen_overlap(rng, lang, variant, k):
    nr = rng.choice([5, 6, 7])
    names = [lab(p, lang) for p in rng.sample(PRODUCTS, nr)]
    rows = [(names[i], rng.randrange(3, 60)) for i in range(nr)]
    h = rng.randint(1, min(4, nr - 1))
    selected = sorted(rng.sample(range(nr), h))
    tags = ["synthetic", "tkinter", "compound", "dialog-overlap", "treeview", "multi-widget"]
    if variant == "count":
        N = rng.choice([4, 5, 6])
        n_dialog = rng.choice([x for x in range(1, 8) if x != h])
        q = CQ(lang, "How many rows are highlighted in the table behind the dialog?", "ダイアログの背後の表でハイライトされている行はいくつですか？", h,
               numopts(h, N, rng, 1, max(N + 1, nr)), "count", "hard", tags + ["count", "occlusion"])
    else:
        t = CTX.next_yn()
        n_dialog = h if t else rng.choice([x for x in range(1, 8) if x != h])
        q = YQ(lang, "The number in the dialog equals the number of highlighted rows in the table behind it",
               "ダイアログの数は、背後の表でハイライトされている行数と一致している", n_dialog == h, "compare", "hard", tags + ["yesno", "cross-check", "occlusion"])
    return (lambda a: build_overlap(a, rows, selected, n_dialog)), "vista", 16, q


TILES = [("Web", "ウェブ"), ("Database", "データベース"), ("Mail", "メール"), ("Search", "検索"), ("Backup", "バックアップ"), ("Billing", "請求"), ("Cache", "キャッシュ")]
TCOL = {"ok": ("#2e9e4f", "white"), "warn": ("#f2c230", "black"), "err": ("#d32f2f", "white")}


def build_dash(a, tiles, used, quota):
    a.body.configure(padding=(10, 8))
    g = ttk.Frame(a.body)
    g.pack(anchor="w")
    for i, (name, st) in enumerate(tiles):
        bg, fg = TCOL[st]
        tk.Label(g, text=name, bg=bg, fg=fg, font=a.bold, width=12 if a.lang == "en" else 11, height=2).grid(row=i // 3, column=i % 3, padx=4, pady=4)
    lg = ttk.Frame(a.body)
    lg.pack(anchor="w", pady=(6, 0))
    for st, t in (("ok", "OK" if a.lang == "en" else "正常"), ("warn", "Warning" if a.lang == "en" else "警告"), ("err", "Error" if a.lang == "en" else "異常")):
        tk.Label(lg, text="  ", bg=TCOL[st][0]).pack(side="left", padx=(0, 4))
        ttk.Label(lg, text=t, font=(a.fam, a.fs - 1)).pack(side="left", padx=(0, 14))
    ttk.Label(a.body, text=("Storage: %d of %d GB used" % (used, quota)) if a.lang == "en" else "ストレージ: %d / %d GB 使用中" % (used, quota),
              font=a.bold).pack(anchor="w", pady=(12, 4))
    pb = ttk.Progressbar(a.body, length=420, maximum=100, mode="determinate")
    pb["value"] = used * 100.0 / quota
    pb.pack(anchor="w")


def level_of(n, pct):
    b = BOUNDS[n]
    return max(j for j in range(n) if b[j] <= pct)


def gen_dash(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nt = rng.choice([4, 5, 6])
    names = [t[L] for t in rng.sample(TILES, nt)]
    tags = ["synthetic", "tkinter", "compound", "dashboard", "multi-widget"]
    if variant == "red":
        sts = ["ok"] * nt
        sts[rng.randrange(nt)] = "err"
        for j in range(nt):
            if sts[j] == "ok" and rng.random() < 0.3:
                sts[j] = "warn"
    elif variant == "neg":
        sts = ["ok"] * nt
        sts[rng.randrange(nt)] = rng.choice(["warn", "err"])
    else:
        sts = [rng.choice(["ok", "ok", "warn", "err"]) for _ in range(nt)]
        if all(s == "ok" for s in sts):
            sts[0] = "warn"
    n = {"score3": 3, "score7": 7, "score10": 10}.get(variant, rng.choice([3, 7, 10]))
    ans = CTX.next_score(n) if variant.startswith("score") else rng.randrange(n)
    quota = rng.choice([100, 200, 500, 1000])
    used = None
    for _ in range(200):
        pct = value_in_level(n, ans, rng, 3)
        u = round(pct * quota / 100)
        if 0 < u < quota and level_of(n, u * 100.0 / quota) == ans:
            used = u
            break
    if used is None:
        used = 50 * quota // 100
        ans = level_of(n, 50.0)
    if variant.startswith("score"):
        q = SQ(lang, "What share of the storage quota is used?", "ストレージの割り当てのうち、使用済みの割合はどれですか？", n, ans, "quantity", "hard",
               tags + ["score", "score%d" % n, "calculation"])
    elif variant == "count":
        kk = sum(1 for s in sts if s != "ok")
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "How many tiles show a problem (warning or error)?", "問題（警告または異常）を示しているタイルはいくつですか？", kk, numopts(kk, N, rng, 0, max(N, nt)),
               "count", "medium", tags + ["count", "legend"])
    elif variant == "red":
        e = sts.index("err")
        ex = [t[L] for t in TILES if t[L] not in names]
        N = rng.choice([nt, 7, 8])
        wr = fill(rng, [x for i, x in enumerate(names) if i != e], ex, max(N, nt))
        q = CQ(lang, "Which service is shown in red?", "赤で表示されているサービスはどれですか？", names[e], wr, "recognition", "medium", tags + ["legend"])
    else:
        e = [i for i, s in enumerate(sts) if s != "ok"][0]
        q = CQ(lang, "Which service is NOT shown in green?", "緑で表示されていないサービスはどれですか？", names[e], [x for i, x in enumerate(names) if i != e], "negation",
               "medium", tags + ["negation", "legend"])
    tiles = list(zip(names, sts))
    return (lambda a: build_dash(a, tiles, used, quota)), "clam", 14, q


LOGMSG = [("Disk check", "ディスク確認"), ("Login", "ログイン"), ("Backup done", "バックアップ完了"), ("Timeout", "タイムアウト"), ("Sync ok", "同期完了"),
          ("Low memory", "メモリ不足"), ("Cache clear", "キャッシュ削除"), ("Update found", "更新あり")]
LV = {"INFO": ("INFO", "情報", "#ffffff"), "WARN": ("WARN", "警告", "#fff2c0"), "ERROR": ("ERROR", "エラー", "#f8c9c9")}


def build_log(a, rows, status):
    a.body.configure(padding=(8, 8))
    f = ttk.Frame(a.body)
    f.pack(anchor="w", pady=(0, 6))
    ttk.Label(f, text="Level:" if a.lang == "en" else "レベル:", font=a.bold).pack(side="left")
    cb = ttk.Combobox(f, values=["All"], state="readonly", width=8, font=a.font)
    cb.set("All" if a.lang == "en" else "すべて")
    cb.pack(side="left", padx=8)
    tv = ttk.Treeview(a.body, columns=(0, 1, 2), show="headings", height=len(rows))
    hd = ["Time", "Level", "Message"] if a.lang == "en" else ["時刻", "レベル", "メッセージ"]
    for i, h in enumerate(hd):
        tv.heading(i, text=h)
    tv.column(0, width=a.fs * 5)
    tv.column(1, width=a.fs * 6)
    tv.column(2, width=a.fs * 12)
    for key, v in LV.items():
        tv.tag_configure(key, background=v[2])
    for tm, lv, msg in rows:
        tv.insert("", "end", values=(tm, LV[lv][0 if a.lang == "en" else 1], msg), tags=(lv,))
    tv.pack(anchor="w")
    statusbar(a, status)


def gen_log(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nr = rng.choice([6, 7, 8])
    msgs = [m[L] for m in rng.sample(LOGMSG, nr)]
    mins = sorted(rng.sample(range(0, 59), nr))
    lvs = None
    for _ in range(2000):
        cand = [rng.choice(["INFO", "INFO", "WARN", "ERROR"]) for _ in range(nr)]
        if cand.count("ERROR") >= 2 and cand.count("WARN") >= 1:
            lvs = cand
            break
    rows = [("09:%02d" % mins[i], lvs[i], msgs[i]) for i in range(nr)]
    shown = nr
    tags = ["synthetic", "tkinter", "compound", "log-viewer", "treeview", "multi-widget"]
    if variant == "status":
        t = CTX.next_yn()
        shown = nr if t else nr + rng.choice([-2, -1, 2])
    status = ("%d entries" % shown) if lang == "en" else "%d 件" % shown
    ne = lvs.count("ERROR")
    if variant == "errcount":
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "How many log entries have the level ERROR?", "レベルが「%s」のログはいくつですか？" % LV["ERROR"][L], ne, numopts(ne, N, rng, 0, max(N, 5)), "count",
               "medium", tags + ["count"])
    elif variant == "warnerr":
        kk = ne + lvs.count("WARN")
        N = rng.choice([4, 5])
        q = CQ(lang, "How many entries are WARN or ERROR?", "レベルが「%s」または「%s」のログはいくつですか？" % (LV["WARN"][L], LV["ERROR"][L]), kk,
               numopts(kk, N, rng, 0, max(N + 2, nr)), "count", "hard", tags + ["count", "conditional"])
    elif variant == "status":
        q = YQ(lang, "The number in the status bar equals the number of rows in the table", "ステータスバーの件数は表の行数と一致している", shown == nr, "compare", "hard",
               tags + ["yesno", "cross-check"])
    else:
        first = [r for r in rows if r[1] == "ERROR"][0]
        q = CQ(lang, "What is the message of the first ERROR entry from the top?", "上から数えて最初の「%s」のログのメッセージはどれですか？" % LV["ERROR"][L], first[2],
               [r[2] for r in rows if r is not first], "recognition", "hard", tags + ["conditional"])
    return (lambda a: build_log(a, rows, status)), "vista", 14, q


# ============================================================ compound screens, second batch (chat / files / schedule / wizard / filter / servers)
def mk_tree(a, parent, cols, widths, rows, height=None, tagcol=None, anchors=None):
    tv = ttk.Treeview(parent, columns=list(range(len(cols))), show="headings", height=height or len(rows))
    for i, c in enumerate(cols):
        tv.heading(i, text=c)
        tv.column(i, width=widths[i], anchor=(anchors[i] if anchors else "w"))
    return tv


CONTACTS = [("Amy", "エミ"), ("Ben", "ケン"), ("Chloe", "ユイ"), ("Dan", "ソウ"), ("Eva", "リナ"), ("Finn", "タク")]
MSGS = [("OK", "了解"), ("Thanks", "ありがとう"), ("See you", "またね"), ("Lunch?", "ランチ？"), ("Done", "完了"), ("Soon", "もうすぐ")]


def build_chat(a, contacts, sel, msgs, typed, me):
    a.body.configure(padding=(8, 8))
    wrap = ttk.Frame(a.body)
    wrap.pack()
    side = tk.Frame(wrap, bg="#e4e6ee")
    side.pack(side="left", fill="y")
    for i, (name, online, unread) in enumerate(contacts):
        bg = "#c9d8f5" if i == sel else "#e4e6ee"
        row = tk.Frame(side, bg=bg)
        row.pack(fill="x")
        tk.Label(row, text="  ", bg="#2e9e4f" if online else "#9aa0a6").pack(side="left", padx=(6, 2))
        tk.Label(row, text=name, font=a.bold, bg=bg, anchor="w", width=6 if a.lang == "en" else 4, pady=6).pack(side="left")
        if unread:
            tk.Label(row, text=str(unread), font=a.bold, bg="#d32f2f", fg="white", padx=6).pack(side="left", padx=2)
    pane = tk.Frame(wrap, bg="white", width=300)
    pane.pack(side="left", fill="y", padx=(8, 0))
    for who, text in msgs:
        mine = who == me
        r = tk.Frame(pane, bg="white")
        r.pack(fill="x", pady=2)
        tk.Label(r, text="%s: %s" % (who, text), font=a.bold if mine else a.font, bg="#bcd4ff" if mine else "#eeeeee", padx=8, pady=3,
                 anchor="e" if mine else "w").pack(side="right" if mine else "left", padx=4)
    bot = ttk.Frame(a.body)
    bot.pack(anchor="w", pady=(8, 0))
    e = tk.Entry(bot, font=a.font, width=20, relief="solid", bd=1)
    e.insert(0, typed)
    e.pack(side="left")
    b = ttk.Button(bot, text="Send" if a.lang == "en" else "送信")
    if not typed:
        b.state(["disabled"])
    b.pack(side="left", padx=8)
    ttk.Label(a.body, text="Send is disabled while the box is empty" if a.lang == "en" else "入力欄が空のあいだは送信できません", font=(a.fam, a.fs - 2)).pack(anchor="w", pady=(4, 0))


def gen_chat(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nc = rng.choice([4, 5, 6])
    people = rng.sample(CONTACTS, nc)
    names = [p[L] for p in people]
    for _ in range(3000):
        online = [rng.random() < 0.5 for _ in range(nc)]
        unread = [rng.choice([0, 0, 1, 2, 3, 5]) for _ in range(nc)]
        both = [i for i in range(nc) if online[i] and unread[i] > 0]
        off_sum = sum(u for o, u in zip(online, unread) if not o)
        if len(both) == 1 and off_sum > 0:
            break
    sel = rng.randrange(nc)
    me = "Me" if lang == "en" else "自分"
    other = names[sel]
    nm = rng.choice([4, 5, 6])
    mm = rng.sample(MSGS, nm)
    msgs = [(pick(rng, [me, other]), m[L]) for m in mm]
    typed = "" if k % 2 == 1 else ("Hello" if L == 0 else "こんにちは")
    contacts = list(zip(names, online, unread))
    tags = ["synthetic", "tkinter", "compound", "chat", "multi-widget"]
    if variant == "online_unread":
        i = both[0]
        q = CQ(lang, "Which contact is online (green dot) and has unread messages?", "オンライン（緑の点）で未読メッセージがある連絡先はどれですか？", names[i],
               [n for j, n in enumerate(names) if j != i], "compare", "hard", tags + ["conditional", "legend"])
    elif variant == "offline_sum":
        N = rng.choice([4, 5])
        pool_n = [off_sum + d for d in (-2, -1, 1, 2, 3, 5) if off_sum + d >= 0]
        rng.shuffle(pool_n)
        q = CQ(lang, "What is the total of the unread badges of the contacts that are offline (gray dot)?", "オフライン（灰色の点）の連絡先の未読バッジの合計はいくつですか？", off_sum,
               pool_n[: N - 1], "quantity", "hard", tags + ["sum", "conditional", "legend"])
    elif variant == "count_me":
        kk = sum(1 for w, _ in msgs if w == me)
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "How many messages in the conversation were sent by the user (right side, blue)?", "会話のうち、自分が送ったメッセージ（右側・青）はいくつですか？", kk,
               numopts(kk, N, rng, 0, max(N, nm)), "count", "medium", tags + ["count"])
    else:
        t = typed != ""
        q = YQ(lang, "The Send button can be clicked", "「送信」ボタンはクリックできる", t, "rules", "medium", tags + ["yesno", "rule-application"])
    return (lambda a: build_chat(a, contacts, sel, msgs, typed, me)), "clam", 14, q


FILES = [("report.docx", 220), ("photo.png", 840), ("notes.txt", 12), ("data.csv", 96), ("setup.zip", 1500), ("music.mp3", 3100), ("slides.pptx", 450)]
FOLDERS = [("Docs", "書類"), ("Photos", "写真"), ("Backup", "バックアップ")]


def build_files(a, rows, selected, status):
    a.body.configure(padding=(8, 8))
    tb = ttk.Frame(a.body)
    tb.pack(anchor="w", pady=(0, 6))
    for t in (("Back", "Up", "Refresh") if a.lang == "en" else ("戻る", "上へ", "更新")):
        ttk.Button(tb, text=t, width=7).pack(side="left", padx=3)
    cols = ["Name", "Type", "Size (KB)"] if a.lang == "en" else ["名前", "種類", "サイズ (KB)"]
    tv = mk_tree(a, a.body, cols, [a.fs * 11, a.fs * 7, a.fs * 8], rows, anchors=["w", "w", "e"])
    ids = [tv.insert("", "end", values=r) for r in rows]
    tv.selection_set([ids[i] for i in selected])
    tv.pack()
    statusbar(a, status)


def gen_files(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    nfold = rng.choice([1, 2])
    nfile = rng.choice([4, 5])
    fo = rng.sample(FOLDERS, nfold)
    fi = rng.sample(FILES, nfile)
    ent = [(f[L], "Folder" if L == 0 else "フォルダー", "-") for f in fo] + [(f[0], "File" if L == 0 else "ファイル", s) for f, s in [(x, x[1]) for x in fi]]
    rng.shuffle(ent)
    n = len(ent)
    fidx = [i for i, e in enumerate(ent) if e[2] != "-"]
    for _ in range(500):
        selected = sorted(rng.sample(range(n), rng.randint(2, min(4, n - 1))))
        sfiles = [i for i in selected if ent[i][2] != "-"]
        if len(sfiles) >= 2 and len({ent[i][2] for i in sfiles}) == len(sfiles):
            break
    total = sum(ent[i][2] for i in sfiles)
    shown_total, shown_n = total, n
    tags = ["synthetic", "tkinter", "compound", "files", "treeview", "multi-widget"]
    if variant == "sel_sum":
        t = CTX.next_yn()
        shown_total = total if t else total + rng.choice([-40, -12, 8, 60, 150])
    if variant == "items_yn":
        t = CTX.next_yn()
        shown_n = n if t else n + rng.choice([-1, 1, 2])
    status = ("%d items, %d selected, %d KB" % (shown_n, len(selected), shown_total)) if lang == "en" else "%d 個の項目、%d 個選択、%d KB" % (shown_n, len(selected), shown_total)
    names = [e[0] for e in ent]
    if variant == "sel_sum":
        q = YQ(lang, "The size in the status bar equals the total size of the highlighted files", "ステータスバーのサイズは、選択中のファイルのサイズ合計と一致している",
               shown_total == total, "compare", "hard", tags + ["yesno", "cross-check", "sum"])
    elif variant == "items_yn":
        q = YQ(lang, "The item count in the status bar equals the number of rows in the table", "ステータスバーの項目数は表の行数と一致している", shown_n == n, "compare", "hard",
               tags + ["yesno", "cross-check"])
    elif variant == "count_folders":
        kk = nfold
        N = rng.choice([3, 4, 5])
        q = CQ(lang, "How many folders are listed?", "表に並んでいるフォルダーはいくつですか？", kk, numopts(kk, N, rng, 0, max(N, 4)), "count", "medium", tags + ["count"])
    elif variant == "largest":
        best = max(sfiles, key=lambda i: ent[i][2])
        q = CQ(lang, "Which highlighted file is the largest?", "選択中のファイルのうち、最もサイズが大きいのはどれですか？", names[best], [x for i, x in enumerate(names) if i != best],
               "compare", "hard", tags + ["conditional", "compare"])
    else:
        N = rng.choice([4, 5, 6])
        pool_n = [total + d for d in (-30, -10, 10, 30, 100, -100, 200) if total + d > 0]
        rng.shuffle(pool_n)
        q = CQ(lang, "What is the total size in KB of the highlighted files?", "選択中のファイルのサイズ合計は何 KB ですか？", total, pool_n[: N - 1], "quantity", "hard",
               tags + ["sum", "conditional"])
    return (lambda a: build_files(a, ent, selected, status)), "clam", 14, q


DAYS = [("Mon", "月"), ("Tue", "火"), ("Wed", "水"), ("Thu", "木"), ("Fri", "金")]
EVENTS = [("Mtg", "会議"), ("Gym", "運動"), ("Lab", "実験"), ("Call", "通話"), ("Demo", "発表"), ("Review", "確認")]
TIMES = ["9:00", "10:00", "11:00", "13:00", "14:00"]


def build_sched(a, grid, status):
    a.body.configure(padding=(8, 8))
    cols = [("Time" if a.lang == "en" else "時刻")] + [d[0 if a.lang == "en" else 1] for d in DAYS]
    rows = [[TIMES[r]] + [grid[r][c] or "" for c in range(5)] for r in range(5)]
    tv = mk_tree(a, a.body, cols, [a.fs * 6] * 6, rows)
    tv.tag_configure("odd", background="#ececf4")
    for i, r in enumerate(rows):
        tv.insert("", "end", values=r, tags=("odd",) if i % 2 else ())
    tv.pack()
    if status:
        statusbar(a, status)


def gen_sched(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    evn = [e[L] for e in EVENTS]
    days = [d[L] for d in DAYS]
    tags = ["synthetic", "tkinter", "compound", "schedule", "treeview", "multi-widget"]
    for _ in range(5000):
        grid = [[(pick(rng, evn) if rng.random() < 0.5 else None) for _c in range(5)] for _r in range(5)]
        per_day = [sum(1 for r in range(5) if grid[r][c]) for c in range(5)]
        total = sum(per_day)
        top = max(per_day)
        if variant == "busiest":
            if per_day.count(top) == 1 and top >= 3:
                break
        elif variant == "free":
            tr = rng.randrange(5)
            fc = rng.randrange(5)
            for c in range(5):
                grid[tr][c] = None if c == fc else (grid[tr][c] or pick(rng, evn))
            break
        elif variant == "count_event":
            ev = pick(rng, evn)
            kk = sum(1 for r in range(5) for c in range(5) if grid[r][c] == ev)
            if 1 <= kk <= 4:
                break
        elif variant == "conflict":
            break
        else:
            if 8 <= total <= 16:
                break
    if variant == "busiest":
        best = per_day.index(top)
        q = CQ(lang, "Which day has the most events?", "予定が最も多い曜日はどれですか？", days[best], [d for i, d in enumerate(days) if i != best], "compare", "medium",
               tags + ["compare", "count"])
    elif variant == "free":
        q = CQ(lang, "Which day is free (empty) at %s?" % TIMES[tr], "%s に予定が入っていない（空いている）曜日はどれですか？" % TIMES[tr], days[fc], [d for i, d in enumerate(days) if i != fc],
               "recognition", "hard", tags + ["conditional"])
    elif variant == "count_event":
        q = CQ(lang, "How many times does '%s' appear in the schedule?" % ev, "予定表に「%s」は何回出てきますか？" % ev, kk, numopts(kk, rng.choice([4, 5]), rng, 0, 7), "count",
               "hard", tags + ["count"])
    elif variant == "conflict":
        t = CTX.next_yn()
        c = rng.randrange(5)
        r1, r2 = rng.sample(range(5), 2)
        if t:
            grid[r1][c] = grid[r1][c] or pick(rng, evn)
            grid[r2][c] = grid[r2][c] or pick(rng, evn)
        else:
            grid[r1][c] = None
        truth = bool(grid[r1][c] and grid[r2][c])
        q = YQ(lang, "%s has events at both %s and %s" % (days[c], TIMES[r1], TIMES[r2]), "%s は %s と %s の両方に予定がある" % (days[c], TIMES[r1], TIMES[r2]), truth, "compare",
               "hard", tags + ["yesno", "cross-check"])
    else:
        N = rng.choice([4, 5])
        q = CQ(lang, "How many time slots are filled in the whole week?", "1 週間で予定が入っている枠はいくつですか？", total, numopts(total, N, rng, max(0, total - 4), total + 4),
               "count", "hard", tags + ["count"])
    g = [row[:] for row in grid]
    return (lambda a: build_sched(a, g, None)), "clam", 16, q


STEPS = [("Account", "アカウント"), ("Profile", "プロフィール"), ("Plan", "プラン"), ("Payment", "支払い"), ("Confirm", "確認")]


def build_wizard(a, cur, name, agree, can_next):
    a.body.configure(padding=(10, 8))
    sf = tk.Frame(a.body)
    sf.pack(anchor="w")
    for i, (s_en, s_ja) in enumerate(STEPS):
        bg, fg = ("#2e9e4f", "white") if i < cur else (("#2f6fd0", "white") if i == cur else ("#d0d0d0", "#333333"))
        tk.Label(sf, text="%d %s" % (i + 1, s_en if a.lang == "en" else s_ja), bg=bg, fg=fg, font=(a.fam, a.fs - 1, "bold"), padx=4, pady=5).pack(side="left", padx=1)
    ttk.Label(a.body, text="done = green, current = blue" if a.lang == "en" else "緑 = 完了、青 = 現在", font=(a.fam, a.fs - 3)).pack(anchor="w", pady=(2, 8))
    f = ttk.Frame(a.body)
    f.pack(anchor="w")
    ttk.Label(f, text="Name" if a.lang == "en" else "氏名").grid(row=0, column=0, sticky="w", padx=(0, 10))
    e = tk.Entry(f, font=a.font, width=18, relief="solid", bd=1)
    e.insert(0, name)
    e.grid(row=0, column=1, pady=4)
    v = tk.BooleanVar(master=a.root, value=agree)
    a.keep.append(v)
    ttk.Checkbutton(a.body, text="I agree to the terms" if a.lang == "en" else "利用規約に同意する", variable=v).pack(anchor="w", pady=4)
    ttk.Label(a.body, text="Next needs a name and agreement" if a.lang == "en" else "「次へ」には氏名の入力と同意が必要です", font=(a.fam, a.fs - 2)).pack(anchor="w")
    bf = ttk.Frame(a.body)
    bf.pack(anchor="e", pady=(8, 0))
    back = ttk.Button(bf, text="Back" if a.lang == "en" else "戻る")
    if cur == 0:
        back.state(["disabled"])
    back.pack(side="left", padx=4)
    nx = ttk.Button(bf, text="Next" if a.lang == "en" else "次へ")
    if not can_next:
        nx.state(["disabled"])
    nx.pack(side="left", padx=4)


def gen_wizard(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    cur = rng.randrange(5)
    steps = [s[L] for s in STEPS]
    named, agree = rng.random() < 0.5, rng.random() < 0.5
    if variant == "why":
        named, agree = [(False, True), (True, False), (False, False)][k % 3]
    name = ("Alex Moore" if L == 0 else "田中 美咲") if named else ""
    can_next = named and agree
    tags = ["synthetic", "tkinter", "compound", "wizard", "multi-widget"]
    if variant == "cur_step":
        q = CQ(lang, "Which step is the current one (blue)?", "現在のステップ（青）はどれですか？", steps[cur], [s for i, s in enumerate(steps) if i != cur], "recognition", "medium",
               tags + ["legend"])
    elif variant == "done_count":
        N = rng.choice([4, 5, 6])
        q = CQ(lang, "How many steps are already completed (green)?", "すでに完了している（緑の）ステップはいくつですか？", cur, numopts(cur, N, rng, 0, max(N, 5)), "count", "medium", tags + ["count", "legend"])
    elif variant == "why":
        opts = [("The name is empty", "氏名が空である"), ("The terms are not accepted", "同意にチェックが入っていない"),
                ("Both the name is empty and the terms are not accepted", "氏名が空で、同意にもチェックが入っていない")]
        ci = [(False, True), (True, False), (False, False)].index((named, agree))
        wr = [o for i, o in enumerate(opts) if i != ci] + [("Next is not disabled", "「次へ」は無効になっていない")]
        q = CQ(lang, "Why is the Next button disabled?", "「次へ」ボタンが無効になっている理由はどれですか？", opts[ci], wr, "rules", "hard", tags + ["rule-application"])
    elif variant == "back_next":
        back = cur > 0
        lbl = {(True, False): ("Back only", "「戻る」だけ"), (False, True): ("Next only", "「次へ」だけ"), (True, True): ("Both", "両方"), (False, False): ("No button", "どちらも無効")}
        c = lbl[(back, can_next)]
        q = CQ(lang, "Which buttons can be clicked?", "クリックできるボタンはどれですか？", c, [v for kk_, v in lbl.items() if v != c], "rules", "hard", tags + ["rule-application"])
    else:
        q = YQ(lang, "The Next button can be clicked", "「次へ」ボタンはクリックできる", can_next, "rules", "medium", tags + ["yesno", "rule-application"])
    return (lambda a: build_wizard(a, cur, name, agree, can_next)), "clam", 15, q


INV = {"Fruit": ("Fruit", "果物", [("Apples", "りんご"), ("Pears", "なし"), ("Plums", "すもも"), ("Kiwis", "キウイ")]),
       "Dairy": ("Dairy", "乳製品", [("Milk", "牛乳"), ("Cheese", "チーズ"), ("Yogurt", "ヨーグルト"), ("Butter", "バター")]),
       "Snacks": ("Snacks", "お菓子", [("Chips", "ポテチ"), ("Nuts", "ナッツ"), ("Cookies", "クッキー"), ("Candy", "あめ")])}


def build_filter(a, cat, low, rows, status):
    a.body.configure(padding=(8, 8))
    f = ttk.Frame(a.body)
    f.pack(anchor="w", pady=(0, 6))
    ttk.Label(f, text="Category:" if a.lang == "en" else "分類:", font=a.bold).pack(side="left")
    cb = ttk.Combobox(f, values=[cat], state="readonly", width=8, font=a.font)
    cb.set(cat)
    cb.pack(side="left", padx=8)
    v = tk.BooleanVar(master=a.root, value=low)
    a.keep.append(v)
    ttk.Checkbutton(f, text="Low stock (< 10)" if a.lang == "en" else "在庫少 (< 10)", variable=v).pack(side="left", padx=8)
    cols = ["Item", "Qty"] if a.lang == "en" else ["品名", "数量"]
    tv = mk_tree(a, a.body, cols, [a.fs * 12, a.fs * 6], rows, anchors=["w", "e"])
    for r in rows:
        tv.insert("", "end", values=r)
    tv.pack(anchor="w")
    statusbar(a, status)


def gen_filter(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    cat = ["Fruit", "Dairy", "Snacks"][k % 3]
    low = variant == "rule_yn" and k % 2 == 0 or (variant != "rule_yn" and rng.random() < 0.5)
    items_all = []
    for c, (_e, _j, its) in INV.items():
        for it in its:
            items_all.append((c, it[L], rng.randrange(2, 40)))
    for _ in range(2000):
        items_all = [(c, n, rng.randrange(2, 40)) for c, n, _q in items_all]
        shown = [(n, q) for c, n, q in items_all if c == cat and (not low or q < 10)]
        if len(shown) >= 2 and len({q for _n, q in shown}) == len(shown):
            if variant == "rule_yn" and not low and all(q < 10 for _n, q in shown):
                continue
            break
    M = len(items_all)
    X = len(shown)
    shownN = X
    tags = ["synthetic", "tkinter", "compound", "filter", "treeview", "multi-widget"]
    if variant == "status_yn":
        t = CTX.next_yn()
        shownN = X if t else X + rng.choice([-1, 1, 2])
    status = ("Showing %d of %d items" % (shownN, M)) if lang == "en" else "%d / %d 件を表示" % (shownN, M)
    cat_label = INV[cat][L]
    if variant == "hidden":
        kk = M - X
        N = rng.choice([4, 5, 6])
        q = CQ(lang, "How many items are hidden by the filters?", "フィルターで非表示になっている項目はいくつですか？", kk, numopts(kk, N, rng, max(0, kk - 5), kk + 5), "count", "hard",
               tags + ["calculation", "cross-check"])
    elif variant == "sum":
        s = sum(q_ for _n, q_ in shown)
        N = rng.choice([4, 5])
        pool_n = [s + d for d in (-5, -3, 3, 5, 10, -10, 1, -1) if s + d > 0]
        rng.shuffle(pool_n)
        q = CQ(lang, "What is the total Qty of the rows shown in the table?", "表に表示されている行の数量の合計はいくつですか？", s, pool_n[: N - 1], "quantity", "medium", tags + ["sum"])
    elif variant == "status_yn":
        q = YQ(lang, "The 'Showing' number equals the number of rows in the table", "「表示」の件数は表の行数と一致している", shownN == X, "compare", "hard", tags + ["yesno", "cross-check"])
    elif variant == "rule_yn":
        q = YQ(lang, "Every row in the table has a Qty below 10", "表のすべての行で数量が 10 未満である", all(q_ < 10 for _n, q_ in shown), "compare", "hard",
               tags + ["yesno", "conditional"])
    else:
        best = max(shown, key=lambda r: r[1])
        q = CQ(lang, "Which item has the largest Qty among the rows shown?", "表示されている行のうち、数量が最も多い品名はどれですか？", best[0], [n for n, _q in shown if n != best[0]],
               "compare", "medium", tags + ["compare"])
    return (lambda a: build_filter(a, cat_label, low, shown, status)), "clam", 15, q


SERVERS = ["web-01", "web-02", "db-01", "cache-01", "mail-01", "api-01", "api-02"]
SVST = {"Up": ("Up", "稼働", "#d5f0d5"), "Warn": ("Warn", "注意", "#fff2c0"), "Down": ("Down", "停止", "#f8c9c9")}


def build_servers(a, rows, banner_red, used, total):
    a.body.configure(padding=(8, 8))
    tk.Label(a.body, text=("Attention needed" if banner_red else "All systems normal") if a.lang == "en" else ("要対応" if banner_red else "すべて正常"),
             bg="#d32f2f" if banner_red else "#2e9e4f", fg="white", font=a.bold, pady=5).pack(fill="x")
    ttk.Label(a.body, text="Rule: the banner is red if any server is Down" if a.lang == "en" else "ルール: 停止中のサーバーが 1 台でもあれば帯は赤", font=(a.fam, a.fs - 2)).pack(anchor="w", pady=(2, 6))
    cols = ["Server", "CPU %", "Status"] if a.lang == "en" else ["サーバー", "CPU %", "状態"]
    tv = mk_tree(a, a.body, cols, [a.fs * 9, a.fs * 6, a.fs * 7], rows, anchors=["w", "e", "w"])
    for key, v in SVST.items():
        tv.tag_configure(key, background=v[2])
    for name, cpu, st in rows:
        tv.insert("", "end", values=(name, cpu, SVST[st][0 if a.lang == "en" else 1]), tags=(st,))
    tv.pack(anchor="w")
    ttk.Label(a.body, text=("Memory: %d of %d GB" % (used, total)) if a.lang == "en" else "メモリ: %d / %d GB" % (used, total), font=a.bold).pack(anchor="w", pady=(8, 2))
    pb = ttk.Progressbar(a.body, length=380, maximum=100, mode="determinate")
    pb["value"] = used * 100.0 / total
    pb.pack(anchor="w")


def gen_servers(rng, lang, variant, k):
    L = 0 if lang == "en" else 1
    ns = rng.choice([4, 5, 6])
    names = rng.sample(SERVERS, ns)
    for _ in range(3000):
        cpus = rng.sample(range(5, 99, 3), ns)
        sts = [rng.choice(["Up", "Up", "Up", "Warn", "Down"]) for _ in range(ns)]
        ups = [i for i in range(ns) if sts[i] != "Down"]
        if sts.count("Down") >= 1 and len(ups) >= 2:
            if variant == "down_cpu":
                d = [i for i in range(ns) if sts[i] == "Down"]
                if max(cpus[i] for i in d) <= max(cpus[i] for i in ups):
                    continue
            break
    rows = [(names[i], cpus[i], sts[i]) for i in range(ns)]
    any_down = "Down" in sts
    banner_red = any_down
    tags = ["synthetic", "tkinter", "compound", "servers", "treeview", "multi-widget"]
    n = {"mem3": 3, "mem7": 7, "mem10": 10}.get(variant, 7)
    ans = CTX.next_score(n) if variant.startswith("mem") else rng.randrange(n)
    total = rng.choice([8, 16, 32, 64])
    used = None
    for _ in range(200):
        u = round(value_in_level(n, ans, rng, 3) * total / 100)
        if 0 < u < total and level_of(n, u * 100.0 / total) == ans:
            used = u
            break
    if used is None:
        used = total // 2
        ans = level_of(n, 50.0)
    if variant == "banner_yn":
        t = CTX.next_yn()
        banner_red = any_down if t else (not any_down)
        q = YQ(lang, "The banner color agrees with the rule", "帯の色はルールと一致している", banner_red == any_down, "rules", "hard", tags + ["yesno", "rule-application", "legend"])
    elif variant == "down_cpu":
        best = max(ups, key=lambda i: cpus[i])
        q = CQ(lang, "Which server that is NOT Down has the highest CPU?", "停止していないサーバーのうち、CPU が最も高いのはどれですか？", names[best],
               [x for i, x in enumerate(names) if i != best], "compare", "hard", tags + ["conditional", "negation"])
    elif variant == "cnt_high":
        kk = sum(1 for c in cpus if c > 80)
        q = CQ(lang, "How many servers have a CPU above 80%?", "CPU が 80% を超えているサーバーはいくつですか？", kk, numopts(kk, rng.choice([3, 4]), rng, 0, 6), "count", "medium", tags + ["count"])
    elif variant.startswith("mem"):
        q = SQ(lang, "What share of the memory is used?", "メモリのうち、使用中の割合はどれですか？", n, ans, "quantity", "hard", tags + ["score", "score%d" % n, "calculation"])
    else:
        kk = sts.count("Down")
        q = CQ(lang, "How many servers are Down?", "停止中のサーバーはいくつですか？", kk, numopts(kk, rng.choice([3, 4]), rng, 0, 5), "count", "medium", tags + ["count", "legend"])
    return (lambda a: build_servers(a, rows, banner_red, used, total)), "clam", 14, q


# ============================================================ plan (fixed order = fixed ids)
def ten(*v):
    return list(v)


PLAN = [
    ("chk_list", gen_chk_list, "en", ["count", "count", "count", "neg", "neg", "neg", "yn", "yn", "none", "none"]),
    ("chk_group", gen_chk_group, "en", ["count", "count", "count", "yn", "yn", "count"]),
    ("radio", gen_radio, "en", ["sel", "sel", "sel", "sel", "yn", "yn", "none", "none"]),
    ("combo", gen_combo, "en", ["sel", "sel", "sel", "sel", "yn", "yn"]),
    ("slider", gen_slider, "en", ["s"] * 8),
    ("progress", gen_progress, "en", ["s"] * 8),
    ("prog_cmp", gen_prog_cmp, "en", ["c"] * 4),
    ("switches", gen_switches, "en", ["cnt", "cnt", "neg", "neg", "neg", "yn", "yn", "cnt"]),
    ("form_err", gen_form_err, "en", ["which", "which", "which", "count", "count", "msg", "msg", "yn", "yn", "which"]),
    ("form_val", gen_form_val, "en", ["val", "val", "val", "val", "yn", "yn"]),
    ("dialog_btn", gen_dialog_btn, "en", ["dis1", "dis1", "dis1", "en1", "en1", "cnt", "cnt", "yn", "yn", "code"]),
    ("dialog_cat", gen_dialog_cat, "en", ["c"] * 4),
    ("tree_maxmin", gen_tree_maxmin, "en", ["m"] * 6),
    ("tree_sum", gen_tree_sum, "en", ["s"] * 6),
    ("tree_sel", gen_tree_sel, "en", ["s"] * 6),
    ("tree_sorted", gen_tree_sorted, "en", ["s"] * 6),
    ("notebook", gen_notebook, "en", ["sel", "sel", "sel", "count", "count", "yn", "yn", "sel"]),
    ("menu", gen_menu, "en", ["dis1", "dis1", "dis1", "cnt", "cnt", "yn", "yn", "dis1"]),
    ("list_spin", gen_list_spin, "en", ["l"] * 4),
    # Japanese UI (lang = ja)
    ("chk_list_ja", gen_chk_list, "ja", ["count", "neg", "yn", "none"]),
    ("radio_ja", gen_radio, "ja", ["sel", "yn"]),
    ("slider_ja", gen_slider, "ja", ["s", "s"]),
    ("progress_ja", gen_progress, "ja", ["s"]),
    ("form_err_ja", gen_form_err, "ja", ["which", "count", "msg", "yn"]),
    ("dialog_btn_ja", gen_dialog_btn, "ja", ["dis1", "cnt", "yn"]),
    ("tree_ja", gen_tree_maxmin, "ja", ["m", "m"]),
    ("tree_sum_ja", gen_tree_sum, "ja", ["s"]),
    ("notebook_ja", gen_notebook, "ja", ["sel", "count"]),
    ("menu_ja", gen_menu, "ja", ["dis1"]),
    # compound screens (medium / hard): several widgets on one screen, cross-widget reasoning
    ("mail", gen_mail, "en", ["sum", "max", "status", "bold", "cross", "max"]),
    ("mail_ja", gen_mail, "ja", ["bold", "cross"]),
    ("orders", gen_orders, "en", ["paidsum", "errbig", "status", "maxpend", "common", "paidsum"]),
    ("orders_ja", gen_orders, "ja", ["errbig", "maxpend"]),
    ("rules", gen_rules, "en", ["which", "cnt", "yn", "locked", "which", "yn"]),
    ("rules_ja", gen_rules, "ja", ["which", "locked"]),
    ("overlap", gen_overlap, "en", ["count", "match", "count", "match", "match"]),
    ("overlap_ja", gen_overlap, "ja", ["count", "match"]),
    ("dash", gen_dash, "en", ["score3", "score7", "score10", "count", "red", "neg"]),
    ("dash_ja", gen_dash, "ja", ["score7", "red"]),
    ("log", gen_log, "en", ["errcount", "warnerr", "status", "first", "errcount", "first"]),
    ("log_ja", gen_log, "ja", ["errcount", "first"]),
    # compound screens, second batch
    ("chat", gen_chat, "en", ["online_unread", "offline_sum", "count_me", "send_yn", "online_unread", "offline_sum"]),
    ("chat_ja", gen_chat, "ja", ["online_unread", "send_yn"]),
    ("files", gen_files, "en", ["sel_sum", "count_folders", "largest", "items_yn", "sum_sel", "sel_sum"]),
    ("files_ja", gen_files, "ja", ["sel_sum", "largest"]),
    ("sched", gen_sched, "en", ["busiest", "free", "count_event", "conflict", "total", "free"]),
    ("sched_ja", gen_sched, "ja", ["busiest", "conflict"]),
    ("wizard", gen_wizard, "en", ["cur_step", "done_count", "why", "why", "back_next", "next_yn"]),
    ("wizard_ja", gen_wizard, "ja", ["why", "back_next"]),
    ("filter", gen_filter, "en", ["hidden", "sum", "status_yn", "hidden", "rule_yn", "max"]),
    ("filter_ja", gen_filter, "ja", ["hidden", "status_yn"]),
    ("servers", gen_servers, "en", ["banner_yn", "down_cpu", "cnt_high", "mem7", "mem10", "banner_yn"]),
    ("servers_ja", gen_servers, "ja", ["down_cpu", "mem3"]),
]


EASY_BASES = {"chk_list", "radio", "combo", "switches", "form_val", "dialog_cat", "tree_sel", "tree_sorted", "notebook", "menu", "list_spin", "dialog_btn",
              "form_err", "tree_maxmin", "prog_cmp"}


def make_row(qid, pattern, q):
    lang = q["lang"]
    kind = q["kind"]
    row = {"id": qid, "legacy_id": None, "origin": "new", "derived_from": None, "group": "biz", "source": "rendered", "image_type": "ui",
           "skill": q["skill"], "difficulty": q["difficulty"], "lang": "both" if lang == "en" else "ja", "langs": ["en", "ja"] if lang == "en" else ["ja"],
           "modality": "image", "kind": kind}
    if kind == "choice":
        row["answer_format"] = "choice:%d" % (1 + len(q["ja"]["wrong"]))
    elif kind == "noul":
        row["answer_format"] = "yesno"
    else:
        row["answer_format"] = "score:%d" % len(q["ja"]["levels"])
    row["tags"] = q["tags"] + [pattern]
    if "multi-widget" not in q["tags"]:
        # simple one-or-two-widget screens: the answer is decided by one or two parts, so they are easy unless a count / sum / negation is involved
        base = pattern[:-3] if pattern.endswith("_ja") else pattern
        hard_kind = {"count", "sum", "negation", "none-of-the-above", "score"} & set(q["tags"])
        if row["difficulty"] == "hard":
            row["difficulty"] = "medium"
        if row["difficulty"] == "medium" and base in EASY_BASES and not hard_kind:
            row["difficulty"] = "easy"
    row["local_images"] = ["generated/%s.png" % qid]
    if lang == "en":
        row["en"] = q["en"]
    row["ja"] = q["ja"]
    if kind in ("noul", "score"):
        row["answer"] = q["answer"]
    row["review"] = {"state": "unreviewed", "history": []}
    return row


def build_all():
    items = []
    for pattern, fn, lang, variants in PLAN:
        for k, v in enumerate(variants):
            rng = random.Random("%s-%d" % (pattern, k))
            build, theme, fs, q = fn(rng, lang, v, k)
            q["lang"] = lang
            items.append((pattern, build, theme, fs, q))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="capture only ids a:b (numbers); all rows are still written")
    args = ap.parse_args()
    wd = threading.Timer(1200, lambda: os._exit(3))
    wd.daemon = True
    wd.start()
    items = build_all()
    if args.limit:
        items = items[: args.limit]
    rows = [make_row("biz-%04d" % (START_ID + i), p, q) for i, (p, b, t, fs, q) in enumerate(items)]
    if not args.rows_only:
        dpi_aware()
        try:
            ctypes.windll.user32.SetCursorPos(1900, 1100)  # keep the pointer away from the capture area
        except Exception:
            pass
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        PX_DIR.mkdir(parents=True, exist_ok=True)
        from PIL import Image
        lo, hi = (map(int, args.only.split(":")) if args.only else (0, 10 ** 9))
        for row, (p, build, theme, fs, q) in zip(rows, items):
            if not lo <= int(row["id"][4:]) <= hi:
                continue
            try:
                im = capture(build, theme, q["lang"], fs)
            except Exception as e:
                print("FAILED", row["id"], p, q["lang"], row["answer_format"], e)
                raise
            im.save(IMG_DIR / (row["id"] + ".png"), optimize=True)
            s = 224 / max(im.size)
            im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS).save(PX_DIR / (row["id"] + ".png"))
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("rows", len(rows), "stats", STATS)


if __name__ == "__main__":
    main()
