# -*- coding: utf-8 -*-
"""Shared helpers of the v1 question tools: read / write the v1 question files and the v1 classification table. Pure standard
library; every file is written as UTF-8 with LF.

Row key note: in the loader ``answer`` of a yes/no or score question is the VALUE of the right answer (true / false, or the level
index). NOTES.md also names an ``answer`` classification axis (choice:4 / yesno / score:5); in a v1 row that axis is stored as
``answer_format`` so that the loader keeps working. (The classification csv keeps its column name ``answer``.)
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from datasets import newq  # noqa: E402
QDIR = ROOT / "datasets" / "questions"
V1DIR = QDIR / "v1"
MANIFESTS = ROOT / "datasets" / "manifests"
GROUPS = ("photo", "biz", "rsn", "txt")
Q2_COLS = ["id", "group", "source", "image_type", "skill", "answer", "answer_kind", "answer_n", "difficulty", "lang", "n_images"]
REVIEW_STATES = ("unreviewed", "reviewed", "changed", "dropped")


def read_jsonl(path: pathlib.Path) -> list:
    return [json.loads(ln) for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def _write_if_changed(path: pathlib.Path, data: bytes) -> None:
    """Write ``data`` unless the file already holds exactly these bytes (a re-run never touches a file it would not change)."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return
    path.write_bytes(data)


def write_jsonl(path: pathlib.Path, rows: list) -> None:
    _write_if_changed(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))


def v1_files(v1dir: pathlib.Path = V1DIR) -> list:
    return [pathlib.Path(v1dir) / ("%s.jsonl" % g) for g in GROUPS]


def load_v1(v1dir: pathlib.Path = V1DIR) -> dict:
    """{group: [rows]} in file order (photo, biz, rsn, txt)."""
    return {g: read_jsonl(p) for g, p in zip(GROUPS, v1_files(v1dir)) if p.exists()}


def save_v1(by_group: dict, v1dir: pathlib.Path = V1DIR) -> None:
    for g, rows in by_group.items():
        write_jsonl(pathlib.Path(v1dir) / ("%s.jsonl" % g), rows)


def all_rows(by_group: dict) -> list:
    return [r for g in GROUPS for r in by_group.get(g, [])]


def read_csv(path: pathlib.Path) -> list:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: pathlib.Path, cols: list, rows: list) -> None:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    _write_if_changed(path, buf.getvalue().encode("utf-8"))


def answer_format(row: dict) -> tuple:
    """(format string, kind, n) of a row: choice:n (n = right + wrong options) / yesno / score:n (n = levels)."""
    lang0 = (row.get("langs") or ["en", "ja"])[0]
    if row["kind"] == "choice":
        n = 1 + len(row[lang0]["wrong"])
        return "choice:%d" % n, "choice", n
    if row["kind"] == "noul":
        return "yesno", "yesno", 2
    if row["kind"] == "score":
        n = len(row[lang0]["levels"])
        return "score:%d" % n, "score", n
    raise ValueError("unknown kind %r" % row["kind"])


def classification_rows(rows: list) -> list:
    out = []
    for r in rows:
        fmt, kind, n = answer_format(r)
        out.append(dict(id=r["id"], group=r["group"], source=r["source"], image_type=r["image_type"], skill=r["skill"], answer=fmt,
                        answer_kind=kind, answer_n="" if kind == "yesno" else n, difficulty=r.get("difficulty"), lang=r.get("lang", "both"),
                        n_images=len(r.get("local_images", []))))
    return out


def write_questions_csv(by_group: dict, manifests: pathlib.Path = MANIFESTS) -> None:
    write_csv(pathlib.Path(manifests) / "questions_v1.csv", Q2_COLS, classification_rows(all_rows(by_group)))


# ------------------------------------------------------------------------------------------------ new questions (new_<tag>.jsonl)
# Kept apart from the base files on purpose: load_v1 / save_v1 never see them (a base save must not pull new rows into photo.jsonl, and
# several writers each own one new_<tag>.jsonl). One classification csv per tag, regenerated from the jsonl only.
Q2_NEW_COLS = Q2_COLS + ["origin", "derived_from"]


def new_path(tag: str, v1dir: pathlib.Path = V1DIR) -> pathlib.Path:
    return pathlib.Path(v1dir) / newq.new_filename(tag)


def load_new(v1dir: pathlib.Path = V1DIR) -> dict:
    """{tag: [rows]} of the new_<tag>.jsonl files in file order (empty dict when there are none)."""
    return {newq.tag_of_filename(p.name): read_jsonl(p) for p in newq.new_files(v1dir)}


def save_new(by_tag: dict, v1dir: pathlib.Path = V1DIR) -> None:
    for tag, rows in by_tag.items():
        write_jsonl(new_path(tag, v1dir), rows)


def all_new_rows(by_tag: dict) -> list:
    return [r for tag in sorted(by_tag) for r in by_tag[tag]]


def load_v1_all(v1dir: pathlib.Path = V1DIR) -> list:
    """Every v1 row, base then new (tags sorted)."""
    return all_rows(load_v1(v1dir)) + all_new_rows(load_new(v1dir))


def write_new_manifests(by_tag: dict, manifests: pathlib.Path = MANIFESTS, tags=None) -> list:
    """Write manifests/questions_v1_new_<tag>.csv for the given tags (default all), from the rows only.
    A tag with no rows has its files removed. Returns the written paths."""
    manifests = pathlib.Path(manifests)
    written = []
    for tag in (tags if tags is not None else sorted(by_tag)):
        rows = by_tag.get(tag, [])
        qs = manifests / ("questions_v1_new_%s.csv" % tag)
        if not rows:
            if qs.exists():
                qs.unlink()
            continue
        cls = classification_rows(rows)
        for c, r in zip(cls, rows):
            c.update(origin=r.get("origin", ""), derived_from=r.get("derived_from") or "")
        write_csv(qs, Q2_NEW_COLS, cls)
        written.append(qs)
    return written
