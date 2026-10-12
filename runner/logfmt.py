# -*- coding: utf-8 -*-
"""The per-question log format (kept byte-compatible with the old eval_common logs) and the blocks.log gate record.

    ok  img-0016           got=0 exp=0 rev=None ms=1220          one line per question ("XX " when wrong)
    WIKI[onejev,en,224px] 1179/1268  choice fwd+rev both correct 0/0  (1866 s)     the last line of a finished block
blocks.log (one line per timed block):   <block> before=<ms> after=<ms> <HH:MM:SS>
"""
from __future__ import annotations

import pathlib
import re

LINE = re.compile(r"(ok |XX )\s+(\S+)\s+got=(\S+) exp=(\S+) rev=(\S+) ms=(\d+)")
SUMMARY = re.compile(r"^WIKI\[", re.M)
BLOCK = re.compile(r"(\S+) before=(\d*) after=(\d*)")


def read_text(path: pathlib.Path) -> str:
    """Logs written by PowerShell redirection can be UTF-16-ish with NULs: drop them, tolerate bad bytes."""
    return path.read_bytes().replace(bytes([0]), b"").decode("utf-8", errors="replace").replace("\r", "")


def parse(path: pathlib.Path) -> dict:
    """id -> dict(ok, got, exp, rev, ms) from one log (the last line wins when an id repeats)."""
    out = {}
    if path.exists():
        for ln in read_text(path).split("\n"):
            m = LINE.search(ln)
            if m:
                out[m.group(2)] = dict(ok=m.group(1) == "ok ", got=m.group(3), exp=m.group(4), rev=m.group(5), ms=int(m.group(6)))
    return out


def is_finished(path: pathlib.Path) -> bool:
    """True when the log's tail holds the summary line (the done marker the batch checks)."""
    return path.exists() and bool(SUMMARY.search(read_text(path)[-400:]))


def valid_blocks(blocks_log: pathlib.Path, limit: int) -> dict:
    """block name -> True when both calibrations of the block were at most ``limit`` ms."""
    out = {}
    if blocks_log.exists():
        for ln in read_text(blocks_log).split("\n"):
            m = BLOCK.match(ln)
            if m:
                a, b = m.group(2), m.group(3)
                out[m.group(1)] = bool(a and b and max(int(a), int(b)) <= limit)
    return out
