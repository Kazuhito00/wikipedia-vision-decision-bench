# -*- coding: utf-8 -*-
"""Wikimedia Commons imageinfo: batched queries, and what the image list (manifest) keeps of each answer.

``image_info(titles)`` asks the Commons API for 50 titles per request (the API's limit for anonymous clients) and returns, per requested title,
whether the file is still there, whether it was renamed (redirect), and its metadata (sha1, timestamp, license, author, description hash,
page URL, thumbnail URL). Only METADATA is requested; downloading is ``datasets/fetch/fetch.py``.
"""
from __future__ import annotations

import hashlib
import html
import re
from typing import Callable, Iterable

from . import http

COMMONS = "https://commons.wikimedia.org/w/api.php"
BATCH = 50                                       # titles per imageinfo request
#: the licenses the bench accepts: CC0 and public domain only ("Public domain", "PD-...", "CC0", "cc-zero")
OK_LICENSE = re.compile(r"^(cc0|cc-zero|public domain|pd\b|pd-)", re.I)
IIPROP = "url|extmetadata|sha1|mime|size|timestamp"


def strip_html(s: str) -> str:
    """Plain text of an extmetadata value: tags removed, entities decoded, whitespace collapsed."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def describe(ii: dict) -> dict:
    """The part of an imageinfo record that goes into the manifest (and that ``check`` compares)."""
    meta = ii.get("extmetadata")
    if not isinstance(meta, dict):      # [] when the file has no extended metadata
        meta = {}
    val = lambda k: strip_html(meta.get(k, {}).get("value", ""))          # noqa: E731
    return dict(sha1=ii.get("sha1"), timestamp=ii.get("timestamp"), license=val("LicenseShortName"), author=val("Artist"),
                description_sha256=hashlib.sha256(val("ImageDescription").encode("utf-8")).hexdigest(),
                source_url=ii.get("descriptionurl"), thumb_url=ii.get("thumburl"), mime=ii.get("mime"),
                width=ii.get("width"), height=ii.get("height"), size=ii.get("size"))


def image_info(titles: Iterable[str], px: int | None = None, *, api: Callable = http.api_json, batch: int = BATCH,
               use_cache: bool = False) -> dict[str, dict]:
    """requested title -> dict(state="found"|"missing"|"redirected", title=<canonical>, moved_to=<title or None>, info=<describe() or None>).
    ``px``: also ask for a thumbnail URL of that width (iiurlwidth). ``api`` is injectable (tests pass a fake)."""
    titles = list(dict.fromkeys(titles))
    out: dict[str, dict] = {}
    for i in range(0, len(titles), batch):
        chunk = titles[i:i + batch]
        params = dict(action="query", titles="|".join(chunk), prop="imageinfo", iiprop=IIPROP, redirects=1)
        if px:
            params["iiurlwidth"] = px
        d = api(COMMONS, params, use_cache=use_cache, post=True)
        q = d.get("query", {})
        normalized = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redirects = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q.get("pages", {}).values()}
        for t in chunk:
            n = normalized.get(t, t)
            r = redirects.get(n, n)
            page = pages.get(r)
            if page is None or "missing" in page or not page.get("imageinfo"):
                out[t] = dict(state="missing", title=r, moved_to=None, info=None)
            else:
                out[t] = dict(state="redirected" if r != n else "found", title=r, moved_to=r if r != n else None,
                              info=describe(page["imageinfo"][0]))
    return out
