# runner: how the v1 trial measurement was run (2026-10-11)

A trial of dataset v1 (2768 questions; en 2596 + ja 2768 = 5364 cases) with JEVision 0.8B (CPU and GPU) and the OpenAI Decisions API.
Accuracy is the goal; times are reference values (the GPU ones are not gated, the CPU ones were gated by the calibration).
Results: `results/runs/v1/` (`<block>.json|csv`, `per_question_v1.csv`, `summary_v1.md|json`, `label_check_v1.md`, `blocks_v1_cpu.txt`).
Per-question logs go to `work/logs/v1/` (git-ignored).

## Setup used

- The images and passages live in the old tree: `work/data` is a directory junction to `wiki_qa/data` (`mklink /J work\data <...>\wiki_qa\data`);
  the generated pictures are in `work/generated`.
- JEVision runtime: `JEVision/` (package `jevision_decide`, no git/tag: `MODEL_TAG=local-untagged`), model `JEVision/models/jevision`, fp16.
  PYTHONPATH = this repository + `JEVision/`; `JEVISION_MODEL_DIR` or `--model-dir`.
  CPU: `OneJev/.venv-min` (onnxruntime 1.30, CPU only), 8 threads. GPU: `JEVision/.venv-cuda` (onnxruntime-gpu 1.31) with CUDA 13 / cuDNN 9 first on PATH
  (`export PATH="/c/Program Files/NVIDIA/CUDNN/v9.20/bin/13.2/x64:/c/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin/x64:/c/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.4/bin:$PATH"`).
- OpenAI: `OPENAI_API_KEY` (and optionally `OPENAI_DECISION_MODEL`, default `gpt-6-luna`) only in the environment of the process
  (`set -a; . <path to .env>; set +a`); never written to a file here. Adapter: `adapters/openai_decisions.py` (urllib only, 3 workers, retries on 429/5xx/timeouts).
- Shared heavy lock: `mkdir _temp/heavy.lock` during the GPU and CPU runs (rmdir at the end). Order: OpenAI, then GPU, then CPU (quiet machine, nothing else running).

## Commands (from the repository root, bash; `PYTHONIOENCODING=utf-8`)

```bash
# 1. OpenAI (network; 3 concurrent requests)
export PYTHONPATH="$PWD" MODEL_TAG=api
set -a; . /f/01.windows_work/01.github/jev-like/.env; set +a
for lang in en ja; do
  JEVision/.venv-cuda/Scripts/python.exe -m runner.run --model openai --set all --mod all --lang $lang --workers 3 --log-dir work/logs/v1
done

# 2. JEVision on the GPU (block names get the suffix _cuda; device=cuda recorded)
export PYTHONPATH="$PWD:<JEVision>" JEVISION_MODEL_DIR=<JEVision>/models/jevision MODEL_TAG=local-untagged
mkdir ../heavy.lock
for lang in en ja; do
  <JEVision>/.venv-cuda/Scripts/python.exe -m runner.run --model jevision --set all --mod all --lang $lang --gpu --suffix _cuda --device cuda --log-dir work/logs/v1
done
rmdir ../heavy.lock

# 3. JEVision on the CPU, behind the calibration gate (runner/models.local.toml: python = OneJev/.venv-min, calibration = GLiNER fixed job)
python -m runner.batch --models jevision --sets all --langs en,ja --mod all --suffix _cpu --log-dir work/logs/v1 --lock ../heavy.lock
# before/after calibration per block -> work/logs/v1/blocks.log (copy: results/runs/v1/blocks_v1_cpu.txt) and the block's json "calibration"

# 4. summary (reads results/runs/v1 and the old logs of eval_common for the legacy comparison)
python -m runner.analyze_v1
python tools/scan_secrets.py        # must print: clean
```

`--set all --mod all` runs the 4 groups (photo, biz, rsn, txt) with pictures and the text-only questions in one block per language.
Every json records: dataset_version=v1, the question list file + sha256 (`datasets/manifests/questions_v1.csv`), model repo / tag, variant, device,
providers requested and used (`CPUExecutionProvider` / `CUDAExecutionProvider`; OpenAI: the endpoint), threads, px, and for OpenAI the model name and token usage.
A run is resumable (the block's log is continued; `--force` re-opens a finished block after removing wrong lines from the log).
