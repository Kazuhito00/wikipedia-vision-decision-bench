# -*- coding: utf-8 -*-
"""Lead-section text of a Wikipedia revision, as plain text (no wikitext parsing, stdlib only).

lead_text(lang, revid) pins the exact revision through action=parse&oldid, so the same
passage comes back on every run (unless the revision is deleted).
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from . import http

_SKIP_TAGS = {"table", "style", "script", "sup", "figure", "math", "ul", "ol", "dl", "h2", "h3"}
_SKIP_CLASSES = ("hatnote", "mw-empty-elt", "noprint", "reference", "thumb", "infobox", "navbox", "IPA",
                 "nowrap-ipa", "mw-editsection", "metadata", "ambox")


class _Lead(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras: list[str] = []
        self._buf: list[str] = []
        self._in_p = 0
        self._skip = 0
        self._stack: list[bool] = []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        skip = tag in _SKIP_TAGS or any(c in cls for c in _SKIP_CLASSES)
        if tag not in ("br", "img", "hr", "meta", "link", "input", "wbr"):
            self._stack.append(skip)
            if skip:
                self._skip += 1
        if tag == "p" and not self._skip:
            self._in_p += 1
            self._buf = []

    def handle_endtag(self, tag):
        if tag in ("br", "img", "hr", "meta", "link", "input", "wbr"):
            return
        if self._stack:
            if self._stack.pop():
                self._skip -= 1
        if tag == "p" and self._in_p and not self._skip:
            self._in_p -= 1
            text = "".join(self._buf)
            text = re.sub(r"\[[^\]]{1,12}\]", "", text)      # [1], [a], [citation needed]
            text = _clean(text)
            if text:
                self.paras.append(text)

    def handle_data(self, data):
        if self._in_p and not self._skip:
            self._buf.append(data)


_NOISE = [
    (re.compile(r"引用エラー[:：].*?(?:見つかりません|ありません)"), ""),   # ja: broken <ref> group message
    (re.compile(r"\(\s*音声ファイル\s*\)"), ""),
    (re.compile(r"[（(]\s*(?:聞く|英語発音:\s*聞く)[^）)]*[）)]"), ""),
    (re.compile(r"\s*\(\s*\)"), ""),                                    # emptied parentheses
    (re.compile(r"[（]\s*[）]"), ""),
    (re.compile(r"\s+"), " "),
]


def _clean(text: str) -> str:
    for rx, rep in _NOISE:
        text = rx.sub(rep, text)
    return text.strip()


def lead_text(lang: str, revid: int, max_chars: int = 900) -> str:
    d = http.api_json("https://%s.wikipedia.org/w/api.php" % lang,
                      dict(action="parse", oldid=revid, prop="text", section=0, disableeditsection=1,
                           disablelimitreport=1, redirects=1))
    page = d["parse"]["text"]["*"]
    p = _Lead()
    p.feed(page)
    out = ""
    for para in p.paras:
        # drop pronunciation / parenthetical clutter that differs between runs of the parser
        para = html.unescape(para)
        if len(out) + len(para) > max_chars and out:
            break
        out = (out + " " + para).strip()
    if len(out) > max_chars:                                   # cut at a sentence boundary
        cut = max(out.rfind("。", 0, max_chars), out.rfind(". ", 0, max_chars))
        out = out[: cut + 1] if cut > 200 else out[:max_chars]
    return out
