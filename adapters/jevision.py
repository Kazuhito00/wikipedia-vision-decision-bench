# -*- coding: utf-8 -*-
"""JEVision (ONNX, onnxruntime + numpy) -> ``ask``.  Key: ``jevision``.

Install:  the ``jevision_decide`` package (``uv pip install git+https://github.com/Kazuhito00/JEVision-ONNX-CPU@<tag>``).
Model directory: ``--model-dir`` or ``JEVISION_MODEL_DIR`` (the ``models/jevision`` folder). Variant: fp16 (default) | fp32;
the environment variable ``JEVISION_VARIANT`` overrides the default.

Differences from the OneJev adapter, all following JEVision's own request format:
  * the state goes in as is; images are NOT referenced from it (``<image:N>`` is a OneJev convention),
  * choice options are sent as "key: text" (just "key" if the text is empty), noul as "no" / "yes", score levels as their labels,
  * without images the TEXT decoder runs (Base + text LoRA); with images the VISUAL decoder (Base + the visual-sidecar LoRA).
    ``lang`` is unused: the model has no language switch, the strings pass through unchanged.

Limits of the reference serving path, kept: 1..4 images per request, 1..255 options (score: >= 2 levels), non-empty option strings
for image requests, image token region <= 8192, whole request <= 80000 tokens (an image costs ~64 tokens at 224 px: the minimum
65536 px is applied, so 224 px is upscaled to 256 px). A request beyond a limit raises ValueError (the runner records got=NA, counted
wrong). Duplicate choice keys also raise.
"""
from __future__ import annotations

import os

from . import _common as C

LIMITS = dict(max_images=4, max_choice_options=255, max_score_levels=255, gpu=True, note="image token region <= 8192, request <= 80000 tokens")


def build(model_dir=None, threads=8, providers=None, lang="en", part="text", variant=None, key="jevision"):
    R = C.import_runtime("jevision_decide", "uv pip install git+https://github.com/Kazuhito00/JEVision-ONNX-CPU@<tag>")
    Decider, choice, noul, score = R.Decider, R.choice, R.noul, R.score
    variant = variant or os.environ.get("JEVISION_VARIANT", "fp16")
    load_vision = C.needs_vision(part)
    d = Decider(C.model_dir_of(model_dir, "JEVISION_MODEL_DIR"), variant=variant, intra_op_threads=threads, load_vision=load_vision,
                providers=providers)

    def ask(state, images, kind, instr, options):
        images = list(images or [])
        if images and not load_vision:
            raise ValueError("this ask was built for part=%r (text only); images need an image part" % part)
        if kind == "noul":
            q = noul(instr)
        elif kind == "choice":
            keys = [k for k, _ in options]
            if len(set(keys)) != len(keys):
                raise ValueError("duplicate option keys: %r" % (keys,))
            q = choice(instr, dict(options))
        elif kind == "score":
            q = score(instr, list(options))
        else:
            raise ValueError("unknown kind %r" % (kind,))
        a = d.decide(state, {"q": q}, images=images)["q"]
        p = a["raw_probabilities"]            # unrounded: the answers' 2-decimal values would tie at 0.5
        if kind == "noul":
            return p[1] > 0.5
        return max(range(len(p)), key=p.__getitem__)

    return C.finish(ask, d, variant=variant, limits=LIMITS)
