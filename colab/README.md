# colab: Google Colab でベンチを回す

`wikipedia_vision_decision_bench.ipynb`（ワンストップのノートブック）と `run_colab.py`（中身。ノートブック無しでも動く CLI）です。
**実際の Colab ではまだ一度も実行していません**（作成した PC に Colab が無いため）。ローカルで確かめたのは、ノートブックが有効な JSON であること・コードセルの構文・`--help` と `--dry-run`・v1 画像 zip の sha256 照合と展開と全問の画像の存在・モデルの取得失敗／CUDA フォールバック／VRAM 不足をスキップして続ける制御（モデルの呼び出しを擬似にした実行）です。実 GPU・実ダウンロード・実推論は未検証です（下の「未検証」）。

## 流れ（1 本で回る）

1. `nvidia-smi` でランタイム確認（GPU は「ランタイムのタイプを変更」で T4 を選ぶ）
2. bench を clone（非公開なら Colab Secrets の `GITHUB_TOKEN`）。モデルのリポジトリ（`Kazuhito00/<Model>-ONNX-CPU`）は、実行時にモデルごと clone
3. uv で依存（pillow / numpy、GPU があれば onnxruntime-gpu、無ければ onnxruntime）。CUDA が本当に使えるか、手書きの小さな ONNX で確認
4. 画像 `images-224px.zip`（sha256 照合 → 展開 → 全問の画像の存在確認）
5. モデルごとに「clone → 重み取得（`download_model.py`）→ デバイス（cpu / cuda）ごとに スモーク → 本番ブロック →（必要なら）重み削除」。取得できない・載らない・CPU に落ちるモデルは**そのデバイスだけスキップ**して次へ、最後に一覧で表示
6. OpenAI Decisions API は、Colab Secrets に `OPENAI_API_KEY` があるときだけ（有料。未設定なら理由を表示してスキップ）
7. 集計（markdown / csv / html）と結果 zip。Drive を使えばログ・結果・画像 zip・重みを保存

CLI だけで回すとき:

```bash
git clone <bench の URL> && cd wikipedia-vision-decision-bench
python colab/run_colab.py --steps setup,images,bench,report --models jevision,intern --devices auto --sample 300 \
    --images-zip /content/drive/MyDrive/images-224px.zip --drive /content/drive/MyDrive/wikipedia-vision-decision-bench-colab
python colab/run_colab.py --dry-run --steps plan --models all        # 計画だけ（ネットワーク・GPU 不要）
```

`--steps` は `env,setup,images,bench,report,sync,plan`。引数の一覧は `--help`。

## 設定のしどころ

| 設定 | 意味 |
|---|---|
| `MODELS` / `--models` | モデルの一覧（既定は REGISTRY の全部。追加は `adapters/__init__.py` の REGISTRY と `run_colab.py` の `SPECS` に 1 件） |
| `DEVICES` / `--devices` | `auto`（cpu + GPU があれば cuda）/ `cpu` / `cuda` / `cpu,cuda` |
| `SAMPLE_N` / `--sample N` | セット × 言語ごとに N 問を `--seed` で選ぶ（全モデル同じ問）。0 で全問。ブロック名に `_n<N>` が付き、全問のブロックと混ざらない |
| `SETS` | 既定 `photo,biz,rsn`。`txt` / `all` は Wikipedia 本文（配布しない `passages.json`）が要る。無いときは `--skip-missing-passages`（本文の無い記事問 87 を除く。ブロックの問数が減る） |
| `WEIGHTS` / `--weights` | `purge`: 1 モデルずつ「取得 → 測定 → 重み削除」。`auto`: 選んだモデルの重みの合計が空きディスクに入らないときだけ purge。取得時に空きが足りなければ、測定済みの重みを消して続行。Drive キャッシュは残る |
| `--time-budget-h` | 既定 11。超えたら新しいブロックを始めない（無料枠は 12 時間で切れる。同じコマンドで続きから） |
| `MODEL_DIRS` / `--model-dir KEY=PATH` | 取得済みの重みの場所（Drive でよい）。通常は不要（各 `download_model.py` が取る）。使うと取得は行わず、重みも消さない |
| `RELEASE_TAG` / `--release-tag` | 各 `download_model.py` に渡す `--tag`。既定 `v0.0.0`（全リポジトリの最初の Release。`latest` が使えない場合に備えて固定）。`""` で各スクリプトの既定（最新の Release） |
| `IMAGES_URL` / `IMAGES_ZIP` | 画像 zip の Release URL / Drive 等のパス |

## 再開と保存（/content は揮発する）

- 再開の仕組みは bench の既存動作です: `runner.run` は問ごとのログ（`work/logs/v1/<ブロック>.log`）を見て、終わったブロックは飛ばし、途中のブロックは続きから回します（`--force` 無し）。**結果 json はブロックの最後にしか書かれません**ので、ログも一緒に保存・復元します（`--drive` で 10 分ごと＋ブロックごと＋終了時に `logs_v1/`・`runs_v1/`・`colab_*` を Drive にコピーし、起動時に戻します）。
- Drive からの復元は「ローカルより新しいファイルだけ」で、ローカルの長いログを古い Drive のログで上書きしません。重みの取得・Drive キャッシュは完了マーカー（`.colab_complete`、最後に書く）で判定します。途中で切れた取得は、次回 `download_model.py` をもう一度流して続きを取ります。
- **同時に 2 つ流さない**: セルを止めても子プロセスが残ることがあるので、`work/colab/run.lock`（PID）で 2 重起動を断ります。ノートブックは子をプロセスグループで起動し、セル停止で PID（グループ）を指定して止めます。
- ログだけ残って結果 json が無いブロックは、`--force` で（問は全部ログにあるので一瞬で）json を作り直します。
- スモークの結果（デバイス確認）は、**成功したものだけ** `work/colab/checks/` に残し（GPU 無しの最初のセッションの失敗が居座らないように）、再開時は繰り返しません（`--recheck` で取り直し）。スモークのブロックには `_smoke` が付き、本番のログ・結果とは別です（結果は `results/runs/v1` に置かず `work/colab/checks/smoke_records/` へ）。
- 画像 zip と重みは `--drive` の `cache/` に置けます。重みは `--drive-cache-max-gb`（既定 10。無料の Drive は 15 GB）を超えるものは保存しません。

## モデル別の目安（根拠は各リポジトリの記述。ここに書いたものだけが事実）

T4 は VRAM 16 GB・RAM 約 12 GB（無料枠）というのが一般的な想定ですが、Colab の仕様は変わるので `nvidia-smi` と実測で確認してください。

| モデル | 重み / 取得 | RAM / VRAM の記述 | T4 での可否 |
|---|---|---|---|
| JEVision 0.8B | `download_model.py --variant fp16`。このスクリプトは fp16 だけ取得。ローカルの `models/jevision` は全 variant で 7.6 GB | 記述なし | 未検証（小さいので載る見込みだが、実測なし） |
| Intern-Decision 0.8B | `download_model.py`。Release 約 4.1 GB（fp32 の重み 3.3 GB） | ピーク RAM 5.4〜6.1 GB（L≤512）。4 GB GPU では載らず CPU に落ちた（作者の測定） | VRAM 16 GB には重み 3.3 GB が入る見込み。未検証 |
| Strands Decider 2B | `download_model.py`。Release 約 9.4 GB（重み 7.5 GB、結合時に一時的に +7.5 GB のディスク） | RAM 8 GB 以上、L=384 のピーク 7.4 GB。VRAM は torso 約 7.7 GB（4 GB GPU では載らず CPU に落ちた）。16 GB 以上の GPU での測定は無い（README） | 重みの大きさ上は載る見込み。未検証 |
| QEV 2B | `download_model.py`（引数なし = 全ファイル）。Release 約 9.9 GB（L=256〜2048 の全グラフ、共有の重み 7.5 GB、視覚エンコーダ 1.3 GB）。結合の間は一時的に約 7.5 GB 余分に使う | 空きメモリ約 8 GB 以上（重みは fp32 で 7.5 GB。ピーク RAM は未計測）。VRAM 4 GB には載らない（README） | 重みの大きさ上は T4 の VRAM 16 GB に入る見込み（画像ありは +1.3 GB）。未検証 |
| clef-flash 9B | `download_model.py`。約 21 GB（重みは約 19〜20 GB、bf16。分割を結合するので一時的に追加のディスク） | README: CPU のピーク RAM 約 14.5 GB（32 GB の機械での測定）。4 GB の GPU では CUDA のロードで out of memory になり CPU に落ちた。何 GB の VRAM なら載るかは**未検証**（README） | CUDA: 重み約 19〜20 GB が T4 の VRAM 16 GB を超えるため、このスクリプトは 19 GB 未満ならスキップする（重みの大きさからの**推定**。`--force-models` で試せる）。CPU: ピーク RAM 14.5 GB は Colab の標準 RAM（約 12 GB 前後の想定）を超える可能性が高い |
| OneJev 0.8B / 4B | `download_model.py` を**引数なし**で 1 回（0.8B と 4B の両方、約 13 GB。0.8B は `models/onnx`、4B は `models/onnx-4b`）。`onejev` と `onejev4` は同じリポジトリなので取得は 1 回だけ（共有） | 4B は実行に約 10 GB の RAM（README）。0.8B の記述なし | 未検証。ディスクを節約したいときは `--download-args "onejev=--model-size 0.8b"`（0.8B のみ約 2.9 GB。この場合 4B は取れないので `MODELS` から `onejev4` を外す） |
| D3 Edge / Lite / Nano | 統合リポジトリ `D3-ONNX-CPU`（`Kazuhito00/D3-ONNX-CPU`）。`download_model.py` を引数なしで 1 回（edge 2.6 GB + lite 4.2 GB + nano 9.3 GB = 約 16 GB。`models/edge` / `models/lite` / `models/nano`）。`d3edge` / `d3lite` / `d3nano` は共有で取得は 1 回だけ。tokenizers が必要（setup が入れる）。**d3-mini（5B）は未対応**（export に約 25 GB の RAM が要るため。このスクリプトの対象外） | 重みだけの VRAM: edge 2.0 GB / lite 3.0 GB / nano 7.5 GB（README）。ピーク RAM（640x480 画像 + 3 設問）: edge 3.2 GB / lite 5.5 GB / nano 10.0 GB。edge だけ読み込みたいときは `--download-args "d3edge=--model edge"` | 未検証（取得できなければスキップ） |
| OpenAI Decisions API | 重みなし。`OPENAI_API_KEY`、有料、3 並列 | — | GPU 不要 |

GPU 1 問あたりの時間は、作者の PC（RTX 3050 Ti Laptop 4 GB）の値しかありません（JEVision 75 ms / OneJev 87 ms）。T4 は未測定。

## 時間について（参考値の扱い）

- bench の時間の採用ルールは「ブロックの前後に GLiNER 較正（固定の CPU 処理の中央値）を測り、どちらも 600 ms 以下」（静かな作者の PC で約 170〜200 ms）。**Colab の CPU は別の機械**なので、この閾値で「有効」になっても PC の表と並べて比べてはいけません。
- `run_colab.py` は CPU ブロックの前後に較正を測って `results/runs/v1/<ブロック>.json` の `calibration` と `blocks.log` に書きます（GLiNER2.5-Decide を取得できたとき）。**CPU の時間は参考値**として扱います。GPU の時間は bench でも較正の対象外です。
- `runner.batch` は使いません（較正が 600 ms を超えると 300 秒 × 12 回待つため）。`runner.run` を直接呼びます。
- スレッド数は既定で `min(8, CPU 数)`（Colab 無料枠は少ない）で、実際の値が結果に記録されます。CPU の測定は onnxruntime-gpu の CPU プロバイダ（GPU があるとき）で行うため、CPU 専用ビルドとは差が出る可能性があります（未確認）。

## Colab 固有の落とし穴

- **CUDA / cuDNN と onnxruntime-gpu**: 各モデルの README は onnxruntime-gpu 1.31 + CUDA 13 + cuDNN 9 で書かれています（作者の PC）。Colab のドライバが CUDA 12 系なら、既定で `onnxruntime-gpu>=1.20,<1.24`（CUDA 12 版の想定。**未検証**）、13 系なら無指定を入れます。`ORT_GPU_SPEC` 環境変数で上書きできます。`LD_LIBRARY_PATH` に `site-packages/nvidia/*/lib` と `/usr/local/cuda/lib64` を足して子プロセスを起動します。
- **onnxruntime と onnxruntime-gpu は併存できない**（同じ `onnxruntime/` を上書き）: 先に両方を外してから片方を入れ、入れたあと両方が入っていないか確認します。
- **CPU フォールバックの検知**: ①入れた直後に小さな ONNX で CUDA セッションが本当に作れるか確認、②スモークの結果の `providers_used`（各セッションの先頭のプロバイダ）がすべて `CUDAExecutionProvider` か確認。空（読めない）のときは未確認として**スキップ**（`--allow-unconfirmed-cuda` で実行）。**グラフの一部のノードだけが CPU に落ちる場合は、この方法では見えません。**
- **OOM**: `runner.run` は例外を握りつぶして `got=NA`（誤答扱い）にするため、スモークで NA が半分を超えたらそのモデルをスキップし、本番ブロックでも NA が半分を超えたら「failed」としてそのモデル・デバイスを打ち切ります。それ未満の NA は集計表の正答率に誤答として入るので、n と正答率を見てください。デバイスは cuda を先に回します（CPU の長い時間が時間予算を使い切る前に GPU の結果を得るため）。モデルの取得より前に、文書化された RAM / VRAM の下限で全デバイスが無理と分かるモデル（例: 無料枠の T4 での clef）は、重みを取得せずにスキップします。
- **Python のバージョン**: bench は Python 3.11 以上（`tomllib`）。Colab の Python 3.12 前後を想定（未検証）。各モデルのパッケージは 3.10 以上（`pyproject.toml`）。モデルのパッケージは `[tool.uv] package = false` なので、pip / uv でのインストールではなく、**clone したチェックアウトを `PYTHONPATH` に置いて**使います（bench README の「暫定」の方法）。
- **uv**: Colab に uv が無いときだけ、uv を入れるために pip を 1 回使います。`uv pip install --system`（externally managed と言われたら `--break-system-packages` を付けて再試行）。
- **非公開リポジトリ**: `GITHUB_TOKEN` は git のヘッダでだけ渡します（URL にも `.git/config` にも入りません）。**各モデルの `download_model.py` には認証が無い**ので、非公開 Release の重みは取れません。
- **リポジトリ名**: GitHub 上の名前は各 `download_model.py` の `DEFAULT_REPO` とローカルの名前に合わせました（`JEVision-ONNX-CPU`、`Clef-Flash-ONNX-CPU`、`QEV-ONNX-CPU`、`OneJev-ONNX-CPU`、`D3-ONNX-CPU`）。`adapters/REPOS` の表記（`JEVision-0.8B-ONNX-CPU`、`clef-flash-ONNX-CPU`、`QEV-2B-ONNX-CPU`）とは違います。リポジトリが無ければ取得失敗として一覧に出るだけで、他は続行します。

## 画像について

Wikimedia Commons の写真を含むため、画像はリポジトリにも入っていません。データセット v1 の Release（`images-224px.zip`、約 20 MB）を公開したら `--images-url`（`IMAGES_URL`）に URL を入れます。公開前は、手元の `dist/v1/images-224px.zip` を Drive に置いて `--images-zip` で指します。sha256 の既定値は 2026-10-11 のビルド（`c079de92...`、2128 ファイル）で、Release を作り直したら `--images-sha256` で更新します。展開は zip の外に出る名前を拒否します。

## 集計と HTML

`report` ステップは次を作ります（`work/colab/out/`）。
- `colab_summary.{md,csv,html}`: ブロック別、グループ別・形式別の正答率、モデル × デバイスの状態（ok / skipped: 理由 / failed: 理由）。「run here」列は、この Colab（または Drive から戻したこの環境のセッション）で測ったブロックかどうか。
- `v1_report.html`: `report/v1_report.py` のダッシュボード。v1_report.py は 1 回の試行（jevision の CPU・GPU と openai の `all` ブロック）専用で、git 管理外の `dist/v1/*`、`summary_v1.json`、`per_question_v1.csv` が前提です。`colab/make_v1_report.py` が、`report/` を変更せずに、それらを**一時フォルダ**に作って呼びます。
  - `photo` / `biz` / `rsn` / `txt` / `all` のブロックを、(モデル, デバイス, 言語) ごとに 1 つの run に結合
  - **全 run が答えた (問, 言語) だけ**を比べる（答えていない問を誤答として数えないため。サンプルやスキップしたモデルがあると、共通の問だけになる）
  - `cases_v1.jsonl` / `questions_v1.jsonl` は `datasets/build_v1.py` の関数で `datasets/questions` から作り直す（画像は不要。画像は埋め込まない）
  - `MODELS` / `RUNS` / `DIST` を実行時に差し替え、`per_question_v1.csv`（jev_cpu / jev_cuda / openai の名前を直書きしている）と比べる 1 行だけをメモリ上で無効化する。その行が変わっていたら、推測せずに「更新が必要」と表示して止まる
  - ダッシュボードの「CPU と GPU の比較」は、v1_report.py の作りで最初の CPU の run と最初の cuda の run を対にします。両方を持つモデルを先頭に並べますが、どのモデルも片方だけのときは別のモデル同士の比較になります（実行時に注意を表示）。
  - 結果にはこの Colab のブロックだけを使います（`work/colab/blocks/` のサイドカーがあるもの。`--include-all-blocks` で全部）。
  - ローカルで、このリポジトリの試行結果（jevision CPU/GPU と openai の `all`）に対して実行し、HTML が作られ検査 3 件が OK になることを確認しました。ブロックを分けた結果の結合も、試行結果を分割した擬似データで確認しました（実際の Colab の結果では未実行）。
- 結果の zip（`colab_results_<日時>.zip`: 結果 json/csv、ログ、デバイス確認、集計、v1_report.html）

## 秘密の扱い

`GITHUB_TOKEN` / `OPENAI_API_KEY` は環境変数だけ（ノートブックが Colab Secrets から入れる）。出力・ファイル・URL には出しません（子プロセスの出力は、値が含まれていたら `***` に置き換えます）。ノートブックは出力を消した状態で保存してあります。コミット前に `python tools/scan_secrets.py` を実行してください。

## 未検証（実際の Colab でしか確認できない）

- Colab 上での実行全体（uv のインストール、`--system` と externally managed の扱い、Python のバージョン）
- onnxruntime-gpu の版（CUDA 12 系 / 13 系の選び方）と CUDA ライブラリの検索、T4 での各モデルの動作・速度・VRAM
- Drive のマウント・保存・復元の実動作、`google.colab.userdata` と `files.download`
- 各モデルのリポジトリ・Release の公開状況、`download_model.py` の実動作（非公開は取得不可）
- 画像 Release の URL（未公開）
- `providers_used` が各モデルの実装で読めるか（読めないモデルは cuda がスキップされる）
