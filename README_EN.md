# wikipedia-vision-decision-bench

[日本語](README.md)

A benchmark of the **picture understanding** of typed-decision models (`choice`, yes/no `noul`, graded `score`). It uses Wikimedia Commons photographs (CC0 / public domain only), business-style pictures drawn by script (UI, forms, charts) and drawn reasoning pictures. Every question is asked in English and in Japanese.

- What it measures: accuracy (per language, question group and answer form) and the time per question on CPU / GPU (calibrated blocks only).
- A model meets the bench only in `adapters/`. Each model runs in an environment that has **its own repository's package** (`<OWNER>/<model name>-ONNX-CPU`).
- **No pictures and no Wikipedia text are in this repository.** It holds the list (ids, license, author, URL, sha256) and the questions. The pictures are distributed as Release zips (in preparation).
- **Dataset versions**: the first version of this repository is **version 1 (`v1`)** (2768 questions, `datasets/questions/v1/`, `dist/v1/`). **`legacy`** is the older material made elsewhere before this repository existed (the frozen 1962 questions, `datasets/questions/legacy/`); it is kept only for the mapping table to v1 (`datasets/manifests/idmap_legacy_v1.csv`) and for the gate that reproduces the old results. Question ids (`photo-0001`, `biz-1001`, ...) carry no version and did not change in the rename (rename map: `datasets/manifests/RENAMES.md`).

## Layout

```
wikipedia-vision-decision-bench/
├─ README.md  README_EN.md  pyproject.toml  .env.example  .gitignore
├─ adapters/        one ask() per model, ONE calling convention (adapters/__init__.py)
├─ runner/          run.py (one model x question group x language; resumable), batch.py (calibration-gated batch), config.toml (measurement conditions)
├─ report/          wiki_report.py + HTML template (--public: tables and figures, no pictures)
├─ datasets/        questions/, synthetic/ (drawn pictures), fetch/ (download and inspection), manifests/ (lists), tests/, NOTES.md
├─ release/         make_image_release.py (builds the picture zips in dist/; never uploads)
├─ results/         aggregates only (runs/<dataset_version>/*.json, *.csv; checks/*.json). Per-question logs and generated HTML are not committed
├─ colab/           run it on Google Colab (notebook + run_colab.py: fetch -> CPU / GPU runs -> summary in one go; `colab/README.md`, Japanese)
├─ tools/           scan_secrets.py (key scan before a commit)
└─ work/ dist/      local only (git-ignored): pictures, logs, API cache, generated HTML, zips
```

## Reproduction (uv only)

```powershell
uv sync                                             # the bench itself (pillow, numpy)
copy .env.example .env                              # fill in what you need (.env is git-ignored)
```

**1. Get the pictures** (either)

```powershell
# (a) from the Release zips (no network; every picture is checked against its sha256; the Release is in preparation)
uv run python -m datasets.fetch fetch --from-release <folder with the zips>
# (b) from Commons (WIKIQA_CONTACT is required: an e-mail address or the repository URL)
$env:WIKIQA_CONTACT = "<contact>"
uv run python -m datasets.fetch fetch
```

Pictures go to `work/data/images/` (the stored Commons files) and `work/px224/` (the model input: longest side 224 px).

**2. Make an environment per model** (one venv per model; the weights come from each model repository's Release)

```powershell
uv venv .venv-onejev
uv pip install --python .venv-onejev onnxruntime numpy pillow
uv pip install --python .venv-onejev "git+https://github.com/<OWNER>/OneJev-ONNX-CPU@<tag>"      # the model's package
# until the model repository has a pyproject: put a checkout on PYTHONPATH instead
$env:PYTHONPATH = "<checkout of OneJev-ONNX-CPU>"
$env:ONEJEV_MODEL_DIR = "<OneJev-ONNX-CPU>/models/onnx"       # the model location: an environment variable or --model-dir
```

The dependencies are also listed as optional groups in `pyproject.toml` (`onejev`, `openjev`, `intern`, `strands`, `clef`, `jevision`, `qev`, `d3` (for d3edge / d3lite / d3nano), `calibrate`). For a GPU, install `onnxruntime-gpu` (on Windows `onnxruntime-directml` also works) instead of `onnxruntime` and run with `uv run --no-sync` (so that uv does not put the CPU build back).

**3. Measure**

```powershell
.venv-onejev\Scripts\python -m runner.run --model onejev --set commons --lang en          # one block
.venv-onejev\Scripts\python -m runner.run --model onejev --set commons --lang en --gpu    # CUDA (CPU is the fallback)
copy runner\models.example.toml runner\models.local.toml                                  # per model: python, model_dir
uv run python -m runner.batch --models onejev,jevision --sets commons,synthetic,reasoning --langs en,ja   # calibration-gated, resumable
```

**4. Report**

```powershell
uv run python -m report.wiki_report --logs work/logs                 # work/report/wiki_report.html (with pictures; local only)
uv run python -m report.wiki_report --logs work/logs --public --out work/report/public.html   # tables and figures only (no thumbnails)
```

**5. Tests** (no network)

```powershell
uv run python -m unittest discover -s datasets/tests
uv run python -m unittest discover -s datasets/fetch/tests -t .
uv run python -m unittest discover -s tools -p "test_*.py"
```

## Measurement conditions

| Item | Value | Where |
|---|---|---|
| Threads (onnxruntime) | 8 | `threads` in `runner/config.toml` (`THREADS`, `--threads`) |
| Picture shrink | longest side 224 px (LANCZOS, JPEG) | `px` (`PX`, `--px`) |
| Option order | not reversed (`REV=0`); `--rev 1` only to look at position bias | `rev` (`REV`) |
| Pictures | one per question (legacy reasoning has 13 two-picture questions; QEV takes one, so they are out of scope for it) | - |
| Which times count | the machine is calibrated (median of a fixed CPU job) before and after each block; only blocks with both at most 600 ms count. Quiet machine: about 170-200 ms | `[gate]`, `runner/calibrate.py`, `blocks.log` |
| What a result records | model repository and tag, variant, providers really used, threads, px, rev, dataset_version, sha256 of the picture list | `results/runs/<dataset_version>/<block>.json` |

Results are keyed by `(dataset_version, id)` (`results/runs/legacy/*.csv`: one row per question). A block is named `<model>_<group>_<lang>_<px>` (group: `wiki` = commons, `syn`, `rsn`); the per-question logs (`work/logs`, git-ignored) keep the format used so far.

## Current question groups (legacy, English side)

| Group | Questions | Form | Options | Difficulty | Pictures |
|---|---|---|---|---|---|
| Commons (Wikipedia 797 + expansion 471 = 1268 pictures, text-only 87) | 1355 | choice 1099 / yes-no 256 | almost all 4-way (4: 1095, 3: 3, 2: 1) | easy 276 / medium 692 / hard 387 | 1 |
| synthetic | 382 | choice 247 / yes-no 106 / score 29 | choice: 3-way 39 / 4-way 208; score: 5 levels only (29) | easy 79 / medium 224 / hard 79 | 1 |
| reasoning | 225 | choice 149 / yes-no 56 / score 20 | choice: 3-way 36 / 4-way 113; score: 5 levels only (20) | medium 83 / hard 142 | 1 for 212 / 2 for 13 |

- 1875 questions have pictures (Commons 1268, synthetic 382, reasoning 225). The accuracies below use these 1875 (QEV: 1862, without the 13 two-picture questions); the 87 text-only questions are not included.
- Known skews: options are 4 or fewer; score has 5 levels only; few text-only questions; the groups follow how the questions were collected (reasoning tags overlap). v1 revises this.

### v1: 2768 questions (done)

The final version: the 1841 questions of legacy that an Opus review polished one by one, plus 927 new questions that fill the gaps. It has more option counts (2 to 16), more score level counts (3 / 5 / 7 / 10), negation / counting / spatial / "none of the above" questions, one picture per question, Japanese-specific questions, balanced answer positions, and a cleaner classification (photos / business pictures / reasoning / text-only). The numbers come from `dist/v1/manifest_v1.json` (`python -m datasets.build_v1`).

| Group | polished from legacy | new | total | what the new ones are |
|---|---|---|---|---|
| photo | 1265 | 211 | **1476** | photo variants (2 / 3 / 5-16 options, negation, none of the above, position, counting, score) |
| biz | 197 | 449 | **646** | drawn pictures, 249 screenshots of real Tkinter windows, 101 Japanese-specific |
| rsn | 292 | 168 | **460** | many options, 3 / 7 / 10 levels, negation, contradiction, uncertainty |
| txt (text only) | 87 | 99 | **186** | controls: an image question with the picture removed |
| **total** | **1841** | **927** | **2768** | |

- Formats: choice 2091 / yes-no 537 / score 140 (3 levels 35, 5 levels 45, 7 levels 35, 10 levels 25). Options: 2: 72, 3: 125, 4: 1495, 5-8: 343, 9-16: 56.
- Languages: en and ja 2596 questions, Japanese only 172. Difficulty: easy 961 / medium 1328 / hard 479.
- 2127 pictures: 1021 Commons photographs (CC0 / public domain), 477 pictures drawn for legacy, 629 made for v1. One picture per question. The zips are about 20 MB (224 px) and about 308 MB (original); they are meant for a Release and have not been uploaded.
- **Caution on the text-only controls**: their `state` holds exact numbers that the picture does not give, so the text version can be easier than the picture version. Say so when comparing them.
- Results are keyed by `(dataset_version, id)` (legacy `rsn-0001` and v1 `rsn-0001` are different questions). v1 has not been measured yet.
- Definitions, how it was made and known limits (legibility of pictures, fonts, OS dependence of the Tkinter pictures, the generator scripts overwrite the jsonl when run with `--apply`) are in `datasets/NOTES.md` section 11; the gap analysis is `datasets/manifests/gap_analysis_v1.md`.

Usage:

```powershell
uv run python -m datasets.build_v1                 # writes dist/v1/: questions, cases, picture list, zips, build_report.md
# pictures: unpack images-original.zip (or images-224px.zip) into an empty folder and point at it
$env:WIKIQA_DATA_ROOT = "<unpacked folder>"        # must contain data/images/... and generated/...
.venv-onejev\Scripts\python -m runner.run --model onejev --set all --dataset-version v1 --lang en
# sets: photo / biz / rsn / txt / all / new (new questions only). Article-based txt questions need a local passages.json (the text is not distributed)
```

## Comparison of all models

Accuracy is on the 1875 picture questions of legacy. Only measured values are listed. Conditions: 8 threads, 224 px, `REV=0`.

| Model | Size / precision | Base | Dependencies | Picture limit | Option limit | Where from (planned) |
|---|---|---|---|---|---|---|
| OpenJev 0.8B | 0.8B / fp16 | Qwen3.5-0.8B (not tuned) | onnxruntime, numpy, pillow | unconfirmed | 255 | Release of `<OWNER>/OpenJev-ONNX-CPU` |
| Intern-Decision 0.8B | 0.8B / fp32 | Qwen3.5-0.8B (full fine-tune) | same | 8 (graph fixed at 512 tokens: 224 px only) | 255 | `<OWNER>/Intern-Decision-0.8B-ONNX-CPU` |
| d3-edge 0.6B | 0.59B / fp32 | Qwen3.5-0.8B (tuned, cut to 12 layers) | onnxruntime, tokenizers, numpy, pillow | no limit (up to the 2048-token graph) | 255 (levels 2-10) | `Kazuhito00/D3-ONNX-CPU` (key `d3edge`; release not uploaded yet) |
| d3-lite 0.9B | 0.85B / fp32 | Qwen3.5-0.8B (tuned) | same | same | same | same (key `d3lite`) |
| d3-nano 2B | 2.21B / fp32 | Qwen3.5-2B (tuned) | same | same | same | same (key `d3nano`). d3-mini 5B is not supported (export needs ~25 GB RAM) |
| JEVision 0.8B | 0.8B / fp16 | Qwen3.5-0.8B (tuned) | same | 4 | 255 | `<OWNER>/JEVision-0.8B-ONNX-CPU` (in progress) |
| OneJev 0.8B | 0.8B / fp16 | Qwen3.5-0.8B (full fine-tune) | same | unconfirmed | 255 (score 10) | `<OWNER>/OneJev-ONNX-CPU` |
| QEV 2B | 2B / fp32 | Qwen3.5-2B (tuned) | same | **1** | 2 to 16 | `<OWNER>/QEV-2B-ONNX-CPU` (in progress) |
| Strands Decider 2B | 2B / fp32 | Qwen3.5-2B-Base + LoRA | same | 4 | 2 to 255 (score 2 to 10) | `<OWNER>/Strands-Decider-2B-ONNX-CPU` |
| OpenJev 4B | 4B / q4f16 | Qwen3.5-4B (not tuned) | same | unconfirmed | 255 | `<OWNER>/OpenJev-ONNX-CPU` |
| OneJev 4B | 4B / fp16 | Qwen3.5-4B (tuned) | same | unconfirmed | 255 (score 10) | `<OWNER>/OneJev-ONNX-CPU` |
| clef-flash 9B | 9B / bf16 weights, fp32 compute | Qwen3.5-9B (tuned) | same (large memory) | 4 | unconfirmed | `<OWNER>/clef-flash-ONNX-CPU` |
| OpenAI Decisions API | not public | unknown | network and an API key | - | - | - |

### Accuracy (%, Commons 1268 / synthetic 382 / reasoning 225)

| Model | Commons en | Commons ja | synthetic en | synthetic ja | reasoning en | reasoning ja |
|---|---|---|---|---|---|---|
| OpenJev 0.8B | 90.0 | 80.8 | 86.9 | 81.4 | 38.2 | 36.0 |
| Intern-Decision 0.8B | 92.2 | 85.2 | 88.2 | 83.2 | 44.0 | 40.9 |
| JEVision 0.8B | 92.4 | 85.3 | 87.7 | 86.6 | 42.7 | 40.9 |
| OneJev 0.8B | 93.0 | 87.0 | 91.6 | 89.0 | 45.8 | 47.6 |
| QEV 2B | 96.7 | 93.8 | 94.0 | 91.1 | 52.4 (212 q.) | 50.9 (212 q.) |
| Strands Decider 2B | 98.1 | 94.2 | 92.7 | 92.4 | 50.2 | 48.0 |
| OpenJev 4B | 96.0 | 93.9 | 92.7 | 89.8 | 64.0 | 59.1 |
| OneJev 4B | 97.9 | 96.8 | 95.3 | 95.0 | 68.9 | 67.6 |
| clef-flash 9B | 98.3 | 98.2 | 97.4 | 96.1 | 76.4 | 80.0 |
| OpenAI Decisions API (gpt-6-luna) | 97.2 | 97.2 | 97.6 | 98.4 | 72.4 | 71.1 |

Reasoning includes forms where a guess is often right (few options, yes/no): read it with chance in mind (v1 revises this). QEV's reasoning figure leaves out the 13 two-picture questions (212 questions): QEV takes one picture, so they are not run and not scored.

### Time per question (median, Commons 1268 questions, calibrated blocks only)

| Model | CPU (8 threads) | GPU (RTX 3050 Ti Laptop 4 GB, CUDA) |
|---|---|---|
| JEVision 0.8B | 0.73 s | 75 ms |
| OneJev 0.8B | 1.2 s | 87 ms |
| OpenJev 0.8B | 1.3 s | 0.36 s |
| Intern-Decision 0.8B | 3.4 s | not measured |
| OpenJev 4B | 4.0 s | 1.0 s |
| QEV 2B | 4.7 s | not measured |
| OneJev 4B | 6.5 to 7.1 s | not measured |
| Strands Decider 2B / clef-flash 9B | not listed (measured while the machine was off calibration) | not measured |

These values come from the measurement logs (with the calibration record `blocks.log`) summarised by `report/wiki_report.py`. They are from the measurements made before the move; they will be replaced when the runs are repeated with this repository's `runner`.

## Data inspection (dead links, replaced pictures, license changes)

The picture list is `datasets/manifests/images_legacy.json` (1023 Commons pictures and 620 drawn pictures). These commands detect changes on Commons (`WIKIQA_CONTACT` is required):

```powershell
uv run python -m datasets.fetch check --limit 20     # metadata only, 50 titles per request (nothing downloaded)
uv run python -m datasets.fetch check                # everything -> results/checks/check_<date>.json
uv run python -m datasets.fetch fetch                # download, compare sha256 with the list, shrink to 224 px, compare again
uv run python -m datasets.fetch refresh              # show the planned changes (writes nothing)
uv run python -m datasets.fetch refresh --apply      # write them to the list after confirmation
```

| State | Meaning | What to do |
|---|---|---|
| ok | exists; sha1 and license as in the list | nothing |
| broken | 404, deleted, renamed | disable the questions or pick a replacement (record the change in the denominator) |
| replaced | sha1 (or timestamp) differs | review the difference, then `refresh --accept-replaced`; results already measured came from the old picture |
| license changed | no longer CC0 / public domain | remove it from the list and the Release |
| author / description changed | attribution changed | update the list |

Notes on the legacy list: the stored picture is Commons' **640 px wide thumbnail**; `sha1` is that of the full-size original on Commons. legacy has no `timestamp` (`null`), so `check` compares the sha1 only. The sha256 of a 224 px picture can change with the Pillow / libjpeg version (when the list was made, a fresh shrink of the stored files matched the recorded sha256 for all 1023); for an exact reproduction use the Release's `images-224px.zip`.

## License and attribution

- Pictures: Wikimedia Commons, CC0 / public domain only (counts in the list: public domain 781, CC0 242). Author, license and URL are in the list and in each zip's `ATTRIBUTION.md`. Before publishing, `check` confirms that the license labels have not changed since the pictures were collected.
- Wikipedia article text (CC BY-SA) is placed neither in the repository nor in a Release (the fetch command puts what a question needs in the local `work/` only).
- Pictures made by this repository's scripts (629 under `generated/` and the 477 drawn pictures of legacy) are **CC0-1.0** (Public Domain Dedication), decided. The drawing scripts are in `datasets/synthetic`; Japanese text in the pictures is drawn with Noto Sans JP / Noto Serif JP (OFL 1.1; fonts are not distributed).
- Transparency note: some pictures have text drawn with fonts bundled with Windows (the Tkinter screens, 249 questions: Segoe UI for the English UI 203, Yu Gothic UI for the Japanese UI 46; the screens are our own and the screenshots contain no OS frame). The ids are listed in `datasets/manifests/windows_fonts_images_v1.md`. This states facts only, not a legal judgement.
- Generated HTML contains Commons pictures, so it is **local only** (`*.html` is git-ignored). Use `--public` (no pictures) to publish.
- The OpenAI key is read from the environment. `.env` is git-ignored; run `python tools/scan_secrets.py` before a commit (it never prints a key).

## Before publishing

```powershell
uv run python tools/scan_secrets.py                 # no key in the files
uv run python -m datasets.fetch check               # changes on Commons
uv run python -m release.make_image_release --originals work/data/images --px224 work/px224   # zips in dist/ (never uploaded)
```
