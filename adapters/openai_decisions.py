# -*- coding: utf-8 -*-
"""OpenAI Decisions API (``POST https://api.openai.com/v1/decisions``) -> ``ask``.  Runner key: ``openai``.

Standard library only (urllib). No package to install, no model files: ``--model-dir`` is ignored.

Environment:
  OPENAI_API_KEY          the API key (required). It is only put into the Authorization header of the request; it is never printed,
                          logged or recorded, and every error text is scrubbed of it before it leaves this module.
  OPENAI_DECISION_MODEL   model name (default ``gpt-6-luna``, the one eval_common/run_openai.py used)
  OPENAI_MAX_WORKERS      concurrent requests the runner may use (default 3; the runner's --workers is capped by it)

The request shape is the one the API accepted (no public reference exists; found from the API's validation errors, see
eval_common/run_openai.py of the old bench):
    {"model": M, "input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": STATE},
                                                                          {"type": "input_image", "image_url": "data:image/png;base64,..."}]}],
     "questions": [{"type": "choice", "instructions": ..., "choices": [{"value": key}, ...]}
                   | {"type": "predicate", "instructions": ...}
                   | {"type": "score", "instructions": ..., "levels": [{"label": ...}, ...]}]}
Pictures are the bench's 224 px files, re-encoded as PNG data URLs (what the old bench sent). Retries: 429 / 5xx / network errors / timeouts
with exponential backoff (up to 6 attempts; Retry-After honoured). A request that still fails raises RuntimeError; the runner records got=NA.
Pictures go to the cloud: only CC0 / public-domain and drawn pictures are in the bench.
"""
from __future__ import annotations

import base64
import io
import json
import os
import threading
import time
import urllib.error
import urllib.request

URL = "https://api.openai.com/v1/decisions"
DEFAULT_MODEL = "gpt-6-luna"
LIMITS = dict(max_images=None, max_choice_options=None, max_score_levels=None, gpu=False, note="remote API; limits not published")
RETRY_CODES = (429, 500, 502, 503, 504)
ATTEMPTS = 6


def build(model_dir=None, threads=8, providers=None, lang="en", part="wiki", variant=None, key="openai"):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set (put it into the environment of this process only)")
    model = variant or os.environ.get("OPENAI_DECISION_MODEL") or DEFAULT_MODEL
    max_workers = int(os.environ.get("OPENAI_MAX_WORKERS", "3"))
    usage = dict(requests=0, input_tokens=0, output_tokens=0, retries=0, round_trip_s=0.0)
    lock = threading.Lock()
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}

    def scrub(text) -> str:
        return str(text).replace(api_key, "***")

    def post(body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
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

    def data_url(path: str) -> str:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    def ask(state, images, kind, instr, options):
        content = [{"type": "input_text", "text": state}] + [{"type": "input_image", "image_url": data_url(p)} for p in (images or [])]
        q: dict = {"instructions": instr}
        if kind == "noul":
            q["type"] = "predicate"
        elif kind == "choice":
            keys = [k for k, _ in options]
            if len(set(keys)) != len(keys):
                raise ValueError("duplicate option keys: %r" % (keys,))
            q["type"] = "choice"
            q["choices"] = [{"value": k} for k in keys]
        elif kind == "score":
            q["type"] = "score"
            q["levels"] = [{"label": s} for s in options]
        else:
            raise ValueError("unknown kind %r" % (kind,))
        res = post({"model": model, "input": [{"type": "message", "role": "user", "content": content}], "questions": [q]})
        try:
            a = res["answers"][0]
            u = res.get("usage") or {}
            with lock:
                usage["requests"] += 1
                usage["input_tokens"] += int(u.get("input_tokens", 0))
                usage["output_tokens"] += int(u.get("output_tokens", 0))
            if kind == "noul":
                return a["probability"] > 0.5
            if kind == "choice":
                return [k for k, _ in options].index(a["choice"])
            probs = a["probabilities"]
            return int(max(probs, key=lambda p: p["probability"])["value"])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError("unexpected answer shape: %s" % scrub(repr(e))[:100]) from None

    ask.info = dict(variant=model, providers_used=["remote:" + URL], limits=LIMITS, endpoint=URL, model_name=model,
                    max_workers=max_workers, usage=usage, remote=True)
    return ask
