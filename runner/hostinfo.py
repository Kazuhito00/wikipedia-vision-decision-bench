# -*- coding: utf-8 -*-
"""The machine a block was measured on, for the `host` key of results/runs/<version>/<block>.json.

    from runner import hostinfo
    host = hostinfo.collect(threads=8, remote=False)       # cached per process (threads / remote are filled in per call)

Standard library only (+ ``nvidia-smi`` when it exists). Every probe may fail: the field is then None and nothing is raised.
Recorded: CPU name, physical / logical cores, RAM, OS name + version, GPU name / VRAM / driver / CUDA version, onnxruntime version(s),
threads. NEVER recorded: user name, host name, paths, IP, serials / UUIDs, e-mail, keys. ``sanitize`` checks every string that is
written and drops (-> None) any that looks like one of those. ``host_id`` is a short hash of the hardware / OS description (not of
anything personal), so two runs on the same machine have the same id and a resume on another machine can be detected.
"""
from __future__ import annotations

import functools
import getpass
import hashlib
import os
import platform
import re
import socket
import subprocess
import sys

SCHEMA = 1


def _run(cmd: list[str], timeout: float = 8.0) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return r.stdout if r.returncode == 0 else None
    except Exception:                                              # noqa: BLE001  (missing exe, timeout, ...)
        return None


def _gb(nbytes) -> float | None:
    return round(nbytes / 1024 ** 3, 1) if nbytes else None


# ---------------------------------------------------------------- CPU / RAM / OS
def _cpu() -> dict:
    name = phys = None
    logical = os.cpu_count()
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                name = winreg.QueryValueEx(k, "ProcessorNameString")[0]
        except Exception:                                          # noqa: BLE001
            name = platform.processor() or None
        out = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                    "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum"], timeout=15)
        if out and out.strip().isdigit():
            phys = int(out.strip())
    else:
        try:
            txt = open("/proc/cpuinfo", encoding="utf-8", errors="replace").read()
            m = re.search(r"^model name\s*:\s*(.+)$", txt, re.M)
            name = m.group(1) if m else None
            pairs = set(re.findall(r"^physical id\s*:\s*(\d+)\s*$[\s\S]*?^cpu cores\s*:\s*(\d+)", txt, re.M))
            if pairs:
                phys = sum(int(c) for _, c in pairs)
            if not name:
                name = platform.processor() or None
        except Exception:                                          # noqa: BLE001
            name = platform.processor() or None
        if phys is None:
            out = _run(["lscpu", "-p=CORE,SOCKET"])
            if out:
                phys = len({l for l in out.splitlines() if l and not l.startswith("#")}) or None
    return dict(name=re.sub(r"\s+", " ", name).strip() if name else None, physical_cores=phys, logical_cores=logical)


def _ram_gb() -> float | None:
    try:
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS()
            ms.dwLength = ctypes.sizeof(MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return _gb(ms.ullTotalPhys)
            return None
        for ln in open("/proc/meminfo", encoding="utf-8"):
            if ln.startswith("MemTotal:"):
                return _gb(int(ln.split()[1]) * 1024)
    except Exception:                                              # noqa: BLE001
        return None
    return None


def _os() -> dict:
    try:
        if sys.platform == "win32":
            ver = platform.version()                              # 10.0.<build>
            build = int(ver.split(".")[-1]) if ver.split(".")[-1].isdigit() else 0
            return dict(name="Windows 11" if build >= 22000 else "Windows " + platform.release(), version=ver)
        name = None
        try:
            name = platform.freedesktop_os_release().get("PRETTY_NAME")
        except Exception:                                          # noqa: BLE001
            pass
        return dict(name=name or platform.system(), version=platform.release())
    except Exception:                                              # noqa: BLE001
        return dict(name=None, version=None)


# ---------------------------------------------------------------- GPU (nvidia-smi) / onnxruntime
def _gpu() -> dict | None:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    if not out or not out.strip():
        return None
    rows = [[c.strip() for c in ln.split(",")] for ln in out.strip().splitlines() if ln.strip()]
    try:
        name, mem, drv = rows[0][0], rows[0][1], rows[0][2]
    except IndexError:
        return None
    head = _run(["nvidia-smi"]) or ""
    m = re.search(r"CUDA Version:\s*([\d.]+)", head)
    return dict(name=name, vram_mb=int(float(mem)) if re.match(r"^[\d.]+$", mem) else None, driver=drv,
                cuda_version=m.group(1) if m else None, count=len(rows))


def _ort() -> dict:
    from importlib import metadata
    out = {}
    for dist in ("onnxruntime", "onnxruntime-gpu", "onnxruntime-directml", "onnxruntime-openvino"):
        try:
            out[dist] = metadata.version(dist)
        except Exception:                                          # noqa: BLE001
            pass
    return out


# ---------------------------------------------------------------- label / id / sanitize
def short_cpu(name: str | None) -> str | None:
    if not name:
        return None
    m = re.search(r"\b(i[3579]-\w+|Ryzen\s+\d\s+\w+|Xeon[^@]*?\w+-?\w*)", name)
    if m and "Xeon" not in m.group(1):
        return re.sub(r"\s+", " ", m.group(1)).strip()
    s = re.sub(r"\((?:R|TM|tm)\)|CPU|@.*$|\d+-Core Processor|Processor", "", name)
    return re.sub(r"\s+", " ", s).strip() or name


def short_gpu(name: str | None, vram_mb) -> str | None:
    if not name:
        return None
    s = re.sub(r"^(NVIDIA|GeForce)\s+", "", name)
    s = re.sub(r"^GeForce\s+", "", s)
    s = re.sub(r"\s+Laptop GPU$", "", s)
    s = s.strip()
    if vram_mb:
        g = vram_mb / 1024
        s += " %s GB" % (("%d" % round(g)) if abs(g - round(g)) < 0.25 else "%.1f" % g)
    return s


def make_label(host: dict) -> str:
    cpu = short_cpu((host.get("cpu") or {}).get("name")) or "CPU 不明"
    gpu = host.get("gpu")
    parts = [cpu]
    if gpu and not host.get("remote"):
        parts.append(short_gpu(gpu.get("name"), gpu.get("vram_mb")))
    return " / ".join(p for p in parts if p)


def make_id(host: dict) -> str:
    cpu, gpu, os_ = host.get("cpu") or {}, host.get("gpu") or {}, host.get("os") or {}
    key = "|".join(str(x) for x in (cpu.get("name"), cpu.get("logical_cores"), round(host.get("ram_gb") or 0), os_.get("name"), gpu.get("name"),
                                    gpu.get("vram_mb")))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def _forbidden() -> list[re.Pattern]:
    """Patterns of what must not be in the record: this user's / host's names, a home path, any path, e-mail, IP, key-like tokens."""
    pats = [re.compile(r"[A-Za-z]:[\\/]"), re.compile(r"\\\\"), re.compile(r"(?:^|\s)/(?:home|Users|root|mnt|content|tmp|var)\b"),
            re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
            re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"), re.compile(r"\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b", re.I),
            re.compile(r"\b(?:GPU|MIG)-[0-9a-f]{8}-", re.I)]
    names = set()
    for fn in (getpass.getuser, socket.gethostname, platform.node):
        try:
            names.add(fn())
        except Exception:                                          # noqa: BLE001
            pass
    for k in ("USERNAME", "USER", "LOGNAME", "COMPUTERNAME", "HOSTNAME"):
        if os.environ.get(k):
            names.add(os.environ[k])
    try:
        names.add(os.path.basename(os.path.expanduser("~")))
    except Exception:                                              # noqa: BLE001
        pass
    for n in names:
        if n and len(n) >= 3:
            pats.append(re.compile(r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])", re.I))
    return pats


def sanitize(obj, _pats=None, _dropped=None):
    """Copy of obj with every string that matches a forbidden pattern replaced by None (a list of the dropped keys goes to _dropped)."""
    pats = _pats if _pats is not None else _forbidden()
    if isinstance(obj, dict):
        return {k: sanitize(v, pats, _dropped) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v, pats, _dropped) for v in obj]
    if isinstance(obj, str) and any(p.search(obj) for p in pats):
        if _dropped is not None:
            _dropped.append("<value>")
        return None
    return obj


# ---------------------------------------------------------------- public
@functools.lru_cache(maxsize=1)
def _base() -> dict:
    gpu = _gpu()
    return dict(schema=SCHEMA, cpu=_cpu(), ram_gb=_ram_gb(), os=_os(), gpu=gpu, onnxruntime=_ort(), python=platform.python_version())


def collect(threads: int | None = None, remote: bool = False, source: str = "measured") -> dict:
    """The host record. The hardware probes run once per process; ``threads`` / ``remote`` are per block.
    remote=True: an API run -- this is the CLIENT's environment and the time of the block is an API round trip, not this machine's speed."""
    import copy
    host = copy.deepcopy(_base())
    host.update(threads=threads, remote=bool(remote), source=source)
    if remote:
        host["note"] = "client side of a remote API call; the time of the block is the API round trip, not this machine's speed"
    host = sanitize(host)
    host["host_id"] = make_id(host)
    host["label"] = make_label(host)
    return host


def same_host(a: dict | None, b: dict | None) -> bool:
    return bool(a and b and a.get("host_id") and a.get("host_id") == b.get("host_id"))


if __name__ == "__main__":
    import json
    print(json.dumps(collect(threads=None), ensure_ascii=False, indent=1))
