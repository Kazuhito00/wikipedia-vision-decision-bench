# -*- coding: utf-8 -*-
"""How a picture becomes model input at the bench's 320 px condition: a square canvas of ``px`` x ``px``, the picture scaled to fit inside
(aspect kept, LANCZOS) and centred on mid-grey (128). One definition, used by the runner, the Release builder and the checks."""
from __future__ import annotations

PX = 320
PAD = (128, 128, 128)


def letterbox(im, px: int = PX, pad=PAD):
    """PIL image -> RGB image of exactly (px, px)."""
    from PIL import Image
    im = im.convert("RGB")
    w, h = im.size
    k = px / max(w, h)
    iw, ih = max(1, round(w * k)), max(1, round(h * k))
    if (iw, ih) != (w, h):
        im = im.resize((iw, ih), Image.LANCZOS)
    canvas = Image.new("RGB", (px, px), pad)
    canvas.paste(im, ((px - iw) // 2, (px - ih) // 2))
    return canvas


def encode(im, name: str, px: int = PX) -> bytes:
    """The file bytes of a model-input picture: letterbox(im), stored as JPEG (quality 95, no chroma subsampling) when ``name`` ends in
    .jpg / .jpeg and as PNG otherwise. The runner's local cache and the Release zip use this one function, so both hold the same bytes."""
    import io
    out = io.BytesIO()
    lb = letterbox(im, px)
    if name.lower().endswith((".jpg", ".jpeg")):
        lb.save(out, "JPEG", quality=95, subsampling=0)
    else:
        lb.save(out, "PNG", optimize=True)
    return out.getvalue()
