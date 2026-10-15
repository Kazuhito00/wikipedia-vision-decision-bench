# -*- coding: utf-8 -*-
"""TypeSafe Jev API (``POST https://api.typesafe.ai/v1/systemone``) -> ``ask``.  Runner key: ``jev``.

Standard library + Pillow (to re-encode the pictures). No model files: ``--model-dir`` is ignored.

Environment:
  TYPESAFE_API_KEY        the API key (required). It is only put into the Authorization header of the request; it is never printed,
                          logged or recorded, and every error text is scrubbed of it before it leaves this module.
  TYPESAFE_JEV_MODEL      model id (default ``jev-preview`` = Jev 1.14; ``jev-latest`` = Jev 1.13). Jev 1.13 and later accept pictures.
  TYPESAFE_MAX_WORKERS    concurrent requests the runner may use (default 3; the runner's --workers is capped by it)

Request (https://docs.typesafe.ai/api.md, https://docs.typesafe.ai/images.md):
    {"model": M, "state": STATE, "questions": {"q": {"type": "noul", "instructions": ...}
                                              | {"type": "choice", "instructions": ..., "criteria": {option: null, ...}}
                                              | {"type": "score", "instructions": ..., "criteria": [level, ...]}},
     "assets": {REF: {"type": "image", "format": "png", "data_base64": ...}}}
A picture is an asset; the state refers to it by its reference string (``{"context": text, "image": REF}``). Requests with a picture carry the
header ``TypeSafe-Danger-Zone-Images: true``. The API takes PNG / JPEG with each side 280..1568 (the docs say 256, but the live API rejects a side of 279 or less) px and 78,400..2,458,624 pixels in all, and
REJECTS (does not resize) anything else, so the bench's 224 px pictures are scaled up (LANCZOS, aspect kept; padded with white when an extreme
aspect ratio cannot satisfy both limits). The picture content is the same; only the pixel grid differs from what the local models get.
Answers: noul -> ``noul`` (0..1, > 0.5 = yes), choice -> ``choice`` (the option), score -> argmax of ``probabilities`` (keyed by level index).
Retries: 429 / 5xx / 529 / network errors / timeouts with exponential backoff (up to 6 attempts; Retry-After honoured). A request that still
fails raises RuntimeError; the runner records got=NA. Pictures go to the cloud: only CC0 / public-domain and drawn pictures are in the bench.
"""
from __future__ import annotations

import base64
import io
import json
import math
import os
import threading
import time
import urllib.error
import urllib.request
import uuid

URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-preview"
LIMITS = dict(max_images=None, max_choice_options=255, max_score_levels=10, gpu=False, note="remote API; 255 options, 2..10 score levels")
RETRY_CODES = (429, 500, 502, 503, 504, 529)
ATTEMPTS = 6
MIN_SIDE, MAX_SIDE, MIN_PIXELS, MAX_PIXELS = 280, 1568, 78_400, 2_458_624


def fit_size(w: int, h: int) -> tuple[int, int]:
    """The size the API accepts that is closest to (w, h): every side >= 280 and <= 1568, total pixels within the limits (aspect kept
    where the two limits allow it; otherwise the long side is capped and the caller pads the short one)."""
    s = max(MIN_SIDE / w, MIN_SIDE / h, math.sqrt(MIN_PIXELS / (w * h)))
    nw, nh = math.ceil(w * s), math.ceil(h * s)
    if max(nw, nh) > MAX_SIDE:
        s2 = MAX_SIDE / max(nw, nh)
        nw, nh = max(MIN_SIDE, int(nw * s2)), max(MIN_SIDE, int(nh * s2))
    while nw * nh > MAX_PIXELS:
        nw, nh = int(nw * 0.98), int(nh * 0.98)
    while nw * nh < MIN_PIXELS:
        nw, nh = nw + 1, nh + 1
    return nw, nh


def encode_image(path: str) -> str:
    """The picture as base64 PNG that satisfies the API's size limits."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    nw, nh = fit_size(w, h)
    k = min(nw / w, nh / h)                                   # scale to fit inside (nw, nh) keeping the aspect ...
    iw, ih = max(1, round(w * k)), max(1, round(h * k))
    if (iw, ih) != (w, h):
        im = im.resize((iw, ih), Image.LANCZOS)
    if (iw, ih) != (nw, nh):                                  # ... then pad to exactly (nw, nh) with white
        canvas = Image.new("RGB", (nw, nh), (255, 255, 255))
        canvas.paste(im, ((nw - iw) // 2, (nh - ih) // 2))
        im = canvas
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build_request(model: str, state, images, kind: str, instr: str, options) -> dict:
    """The JSON body (pure; the pictures are passed as already-encoded base64 strings in ``images``)."""
    assets = {}
    refs = []
    for b64 in images or []:
        ref = "img-%s" % uuid.uuid4()
        assets[ref] = {"type": "image", "format": "png", "data_base64": b64}
        refs.append(ref)
    if not refs:
        st = state
    else:
        st = {"image": refs[0]} if len(refs) == 1 else {"images": refs}
        if state:
            st = dict(st, context=state)
    q: dict = {"instructions": instr}
    if kind == "noul":
        q["type"] = "noul"
    elif kind == "choice":
        keys = [k for k, _ in options]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate option keys: %r" % (keys,))
        q["type"] = "choice"
        q["criteria"] = {k: None for k in keys}
    elif kind == "score":
        q["type"] = "score"
        q["criteria"] = list(options)
    else:
        raise ValueError("unknown kind %r" % (kind,))
    body = {"model": model, "state": st, "questions": {"q": q}}
    if assets:
        body["assets"] = assets
    return body


def read_answer(kind: str, options, answers: dict):
    """The bench's answer (bool for noul, option index for choice / score) from the API's ``answers`` map."""
    a = answers["q"]
    if kind == "noul":
        return a["noul"] > 0.5
    if kind == "choice":
        return [k for k, _ in options].index(a["choice"])
    probs = a["probabilities"]
    return int(max(probs, key=lambda i: probs[i]))


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="jev"):
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise SystemExit("TYPESAFE_API_KEY is not set (put it into the environment of this process only)")
    model = variant or os.environ.get("TYPESAFE_JEV_MODEL") or DEFAULT_MODEL
    max_workers = int(os.environ.get("TYPESAFE_MAX_WORKERS", "3"))
    usage = dict(requests=0, input_tokens=0, output_tokens=0, retries=0, round_trip_s=0.0)
    lock = threading.Lock()

    def scrub(text) -> str:
        return str(text).replace(api_key, "***")

    def post(body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
        if body.get("assets"):
            headers["TypeSafe-Danger-Zone-Images"] = "true"
        last = "unknown error"
        for attempt in range(ATTEMPTS):
            req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
            t = time.perf_counter()
            wait = 2 ** attempt
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    res = json.loads(r.read())
                with lock:
                    usage["round_trip_s"] += time.perf_counter() - t
                return res
            except urllib.error.HTTPError as e:
                msg = scrub(e.read().decode("utf-8", "replace")[:200]).replace("\n", " ")
                last = "HTTP %d %s" % (e.code, msg)
                if e.code not in RETRY_CODES:
                    raise RuntimeError(last) from None
                ra = e.headers.get("Retry-After") if e.headers else None
                if ra and ra.isdigit():
                    wait = max(wait, min(int(ra), 60))
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last = "network: %s" % scrub(e)
            except ValueError as e:                                   # a body that is not JSON
                last = "bad response: %s" % scrub(e)
            if attempt < ATTEMPTS - 1:
                with lock:
                    usage["retries"] += 1
                time.sleep(wait)
        raise RuntimeError(last)

    def ask(state, images, kind, instr, options):
        body = build_request(model, state, [encode_image(p) for p in (images or [])], kind, instr, options)
        res = post(body)
        try:
            ans = read_answer(kind, options, res["answers"])
            u = res.get("usage") or {}
            with lock:
                usage["requests"] += 1
                usage["input_tokens"] += int(u.get("input_tokens", 0))
                usage["output_tokens"] += int(u.get("output_tokens", 0))
            return ans
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError("unexpected answer shape: %s" % scrub(repr(e))[:100]) from None

    ask.info = dict(variant=model, providers_used=["remote:" + URL], limits=LIMITS, endpoint=URL, model_name=model,
                    max_workers=max_workers, usage=usage, remote=True)
    return ask
