"""Peak GPU memory of one block: a background thread polls nvidia-smi while the model loads and the questions run.

Recorded (MiB) as ``gpu_memory`` in the block's JSON:
  process_peak  this process's own peak (nvidia-smi per-process figure; null where the driver hides it, e.g. Windows WDDM)
  gpu_peak      peak of the whole GPU's used memory
  gpu_baseline  the whole GPU's used memory before the model was built (other programs' share)
  gpu_delta     gpu_peak - gpu_baseline  (the best figure when process_peak is null; includes other programs' growth)
  gpu_total     the GPU's memory size
It is what the CUDA allocator (arena) took, not the least memory the model needs. Best effort: any failure -> None."""
from __future__ import annotations

import os
import subprocess
import threading


def _smi(args: list[str]) -> list[list[str]] | None:
    try:
        r = subprocess.run(["nvidia-smi"] + args + ["--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        return [[c.strip() for c in ln.split(",")] for ln in r.stdout.splitlines() if ln.strip()]
    except Exception:                                              # noqa: BLE001  (no nvidia-smi / hung driver)
        return None


def _num(s: str) -> int | None:
    try:
        return int(float(s))
    except ValueError:
        return None


class Sampler:
    def __init__(self, interval: float = 1.0) -> None:
        self.interval = interval
        self.pid = os.getpid()
        self.process_peak: int | None = None
        self.gpu_peak: int | None = None
        self.gpu_baseline: int | None = None
        self.gpu_total: int | None = None
        self._stop = threading.Event()
        self._t: threading.Thread | None = None

    def _sample(self) -> None:
        g = _smi(["--query-gpu=memory.used,memory.total"])
        if g and len(g[0]) >= 2:
            used, total = _num(g[0][0]), _num(g[0][1])
            if used is not None:
                self.gpu_peak = used if self.gpu_peak is None else max(self.gpu_peak, used)
            if total is not None:
                self.gpu_total = total
        p = _smi(["--query-compute-apps=pid,used_memory"]) or []
        for row in p:
            if len(row) >= 2 and _num(row[0]) == self.pid:
                v = _num(row[1])
                if v is not None:
                    self.process_peak = v if self.process_peak is None else max(self.process_peak, v)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._sample()
            self._stop.wait(self.interval)

    def start(self) -> "Sampler":
        g = _smi(["--query-gpu=memory.used"])
        if g and g[0]:
            self.gpu_baseline = _num(g[0][0])
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        return self

    def stop(self) -> dict | None:
        self._stop.set()
        if self._t:
            self._t.join(timeout=15)
        self._sample()
        if self.gpu_peak is None and self.process_peak is None:
            return None
        delta = None if self.gpu_peak is None or self.gpu_baseline is None else max(0, self.gpu_peak - self.gpu_baseline)
        return dict(process_peak=self.process_peak, gpu_peak=self.gpu_peak, gpu_baseline=self.gpu_baseline, gpu_delta=delta,
                    gpu_total=self.gpu_total, unit="MiB", interval_s=self.interval)
