# -*- coding: utf-8 -*-
"""Pre-commit check: no API key may be in a file that is about to be committed.

    uv run python tools/scan_secrets.py            # the files git would add: tracked + untracked, minus .gitignore
    uv run python tools/scan_secrets.py PATH ...   # explicit files or folders

Looks for OpenAI-style keys (``sk-...``), ``Bearer`` tokens, and ``*_API_KEY=value`` assignments with a non-empty value.
Never prints a key: a hit is shown as file:line with the secret masked (first 3 characters and the length only).
``.env`` and ``.env.*`` files are NOT read, except ``.env.example`` (which must keep its values empty).
Exit status 1 when anything is found (usable as a git pre-commit hook).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_BYTES = 5 * 1024 * 1024
SKIP_DIRS = {".git", ".venv", "__pycache__", "work", "dist", "node_modules"}

PATTERNS = [
    ("openai-style key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_\-]{19,}")),
    ("bearer token", re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]{24,})")),
    ("key assignment", re.compile(r"""\b[A-Z][A-Z0-9_]*(?:API_KEY|SECRET|TOKEN)\s*[=:]\s*["']?([^\s"'#\\]{8,})""")),
]
#: values that are placeholders, not secrets
PLACEHOLDER = re.compile(r"^(<.*>|\$\{?.*|xxx+|your[-_ ].*|changeme|example|none|null|\.\.\.+)$", re.I)


def mask(s: str) -> str:
    return "%s*** (%d chars)" % (s[:3], len(s))


def scan_text(text: str, name: str = "") -> list[tuple[str, int, str, str]]:
    """-> [(name, line number, kind, masked match)]"""
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                secret = m.group(1) if rx.groups else m.group(0)
                if kind != "openai-style key" and PLACEHOLDER.match(secret):
                    continue
                hits.append((name, no, kind, mask(secret)))
    return hits


def is_env_file(p: pathlib.Path) -> bool:
    return (p.name == ".env" or p.name.startswith(".env.")) and p.name != ".env.example"


def candidate_files(args: list[str]) -> list[pathlib.Path]:
    if args:
        out = []
        for a in args:
            p = pathlib.Path(a)
            if p.is_dir():
                out += [q for q in p.rglob("*") if q.is_file() and not (set(q.parts) & SKIP_DIRS)]
            else:
                out.append(p)
        return out
    try:
        res = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True)
        return [ROOT / n.decode("utf-8") for n in res.stdout.split(b"\0") if n]
    except (OSError, subprocess.CalledProcessError):
        return [q for q in ROOT.rglob("*") if q.is_file() and not (set(q.relative_to(ROOT).parts) & SKIP_DIRS)]


def scan_files(files: list[pathlib.Path]) -> list[tuple[str, int, str, str]]:
    hits = []
    for p in files:
        if is_env_file(p) or not p.is_file() or p.stat().st_size > MAX_BYTES:
            continue
        raw = p.read_bytes()
        if b"\0" in raw[:4096]:                      # binary
            continue
        try:
            rel = str(p.relative_to(ROOT))
        except ValueError:
            rel = str(p)
        hits += scan_text(raw.decode("utf-8", errors="replace"), rel)
    return hits


def main(argv: list[str]) -> int:
    files = candidate_files(argv)
    hits = scan_files(files)
    for name, no, kind, masked in hits:
        print("%s:%d: %s: %s" % (name, no, kind, masked))
    print("scanned %d files: %s" % (len(files), "%d possible secret(s)" % len(hits) if hits else "clean"))
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
