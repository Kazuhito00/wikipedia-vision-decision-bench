# -*- coding: utf-8 -*-
"""Machine calibration for the timing gate: GLiNER2.5-Decide fp32, 4 threads, a 3-question case; prints the median ms of 15 calls.

    GLINER_MODEL_DIR=<...>/GLiNER2.5-Decide-ONNX-CPU/models/onnx  uv run python -m runner.calibrate

Needs the ``gliner_decide`` package (GLiNER2.5-Decide-ONNX-CPU) in the environment (dependency group ``calibrate``) and its model files
(``GLINER_MODEL_DIR``). The last line is read by runner/batch.py:  "<HH:MM:SS> calibration median N ms (quiet machine: ~199 ms)".
It is a fixed CPU job, so a value far above ~200 ms means something else is using the machine and a timed block must not run.
"""
import os
import statistics
import sys
import time

try:
    from gliner_decide import Decider
except ImportError as e:
    raise SystemExit("cannot import gliner_decide (%s): install the GLiNER2.5-Decide-ONNX-CPU package into this environment" % e)
if not os.environ.get("GLINER_MODEL_DIR"):
    raise SystemExit("set GLINER_MODEL_DIR to the GLiNER2.5-Decide-ONNX-CPU models/onnx folder")

d = Decider(os.environ["GLINER_MODEL_DIR"], variant="fp32", intra_op_threads=4)
text = "Hi, I was charged twice for my Pro subscription this month. Please refund the duplicate payment."
q = [("team", ["billing", "technical support", "sales"], None),
     ("intent", ["refund_request", "order_status", "cancel_subscription", "login_problem", "other"], None),
     ("angry", ["yes", "no"], None)]
for _ in range(3):
    d.decide(text, q)
ts = []
for _ in range(15):
    t = time.perf_counter()
    d.decide(text, q)
    ts.append((time.perf_counter() - t) * 1000)
print("%s calibration median %.0f ms (quiet machine: ~199 ms)" % (time.strftime("%H:%M:%S"), statistics.median(ts)))
sys.stdout.flush()
