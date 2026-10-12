# -*- coding: utf-8 -*-
"""Polite, cached HTTP for the Wikimedia APIs (copied from the old wiki_qa/wikiqa/http.py; the cache lives in <repo>/work/cache).

* A contact string is mandatory (WIKIQA_CONTACT) -- Wikimedia's User-Agent policy asks for one.
* maxlag, exponential back-off on 429/5xx, one connection at a time.
* Every JSON response is cached on disk, so a re-run is offline.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

CACHE = pathlib.Path(os.environ.get("WIKIQA_CACHE", pathlib.Path(__file__).resolve().parents[2] / "work" / "cache"))
_last = 0.0


def user_agent() -> str:
    contact = os.environ.get("WIKIQA_CONTACT", "").strip()
    if not contact:
        raise SystemExit(
            "Set WIKIQA_CONTACT to a URL or e-mail where Wikimedia can reach you "
            "(User-Agent policy), e.g.  set WIKIQA_CONTACT=https://github.com/you/yourrepo")
    return "jev-like-wikiqa/1.0 (%s)" % contact


def _sleep(min_gap: float = 1.0) -> None:
    global _last
    wait = _last + min_gap - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last = time.monotonic()


def fetch(url: str, *, tries: int = 6, timeout: int = 60, gap: float = 1.0, max_bytes: int | None = None,
          deadline: float | None = None) -> bytes:
    """gap: minimum seconds between requests (media downloads from upload.wikimedia.org can use a smaller one)."""
    delay = 2.0
    for attempt in range(tries):
        _sleep(gap)
        req = urllib.request.Request(url, headers={"User-Agent": user_agent()})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if max_bytes is None and deadline is None:
                    return resp.read()
                # bounded read: a huge original or a trickling connection must not hang the whole run
                t0, chunks, total = time.monotonic(), [], 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        return b"".join(chunks)
                    total += len(chunk)
                    chunks.append(chunk)
                    if max_bytes is not None and total > max_bytes:
                        raise ValueError("response larger than %d bytes" % max_bytes)
                    if deadline is not None and time.monotonic() - t0 > deadline:
                        raise TimeoutError("download took longer than %.0f s" % deadline)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                retry = e.headers.get("Retry-After")
                time.sleep(float(retry) if retry and retry.isdigit() else delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def api_json(base: str, params: dict) -> dict:
    """GET base?params as JSON, cached by the full URL."""
    params = dict(params, format="json", maxlag=5)
    url = base + "?" + urllib.parse.urlencode(sorted(params.items()))
    key = hashlib.sha1(url.encode()).hexdigest()
    path = CACHE / (key + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    data = json.loads(fetch(url).decode("utf-8"))
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data
