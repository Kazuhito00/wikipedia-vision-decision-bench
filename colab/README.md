# colab: Google Colab でベンチを回す

`wikipedia_vision_decision_bench.ipynb`（ワンストップのノートブック）と `run_colab.py`（中身。ノートブック無しでも動く CLI）です。
**実際の Colab ではまだ一度も実行していません**（作成した PC に Colab が無いため）。ローカルで確かめたのは、ノートブックが有効な JSON であること・コードセルの構文・`--help` と `--dry-run`・v1 画像 zip の sha256 照合と展開と全問の画像の存在・モデルの取得失敗／CUDA フォールバック／VRAM 不足をスキップして続ける制御（モデルの呼び出しを擬似にした実行）です。実 GPU・実ダウンロード・実推論は未検証です（下の「未検証」）。

## 流れ（1 本で回る）

1. `nvidia-smi` でランタイム確認（GPU は「ランタイムのタイプを変更」で T4 を選ぶ）
2. bench を clone（非公開なら Colab Secrets の `GITHUB_TOKEN`）。モデルのリポジトリ（`Kazuhito00/<Model>-ONNX-CPU`）は、実行時にモデルごと clone
3. uv で依存（pillow / numpy、GPU があれば onnxruntime-gpu、無ければ onnxruntime）。CUDA が本当に使えるか、手書きの小さな ONNX で確認
4. 画像 `images-224px.zip`（既定: bench の GitHub Release `v0.0.0` からダウンロード → `SHA256SUMS` で照合 → 展開 → 全問の画像の存在確認）
5. モデルごとに「clone → 重み取得（`download_model.py`）→ デバイス（cpu / cuda）ごとに スモーク → 本番ブロック →（必要なら）重み削除」。取得できない・載らない・CPU に落ちるモデルは**そのデバイスだけスキップ**して次へ、最後に一覧で表示
6. OpenAI Decisions API は Colab Secrets の `OPENAI_API_KEY`、Jev API（`jev-preview` = Jev 1.14）は `TYPESAFE_API_KEY` があるときだけ（有料。未設定なら理由を表示してスキップ）
7. 集計（markdown / csv / html）と結果 zip。**Drive は既定でオフ**（結果は `/content` のローカルだけ。zip をダウンロードして持ち帰る）。`--use-drive` のときだけログ・結果・画像 zip・重みを Drive に保存

CLI だけで回すとき:

```bash
git clone <bench の URL> && cd wikipedia-vision-decision-bench
python colab/run_colab.py --steps setup,images,bench,report --models jevision,intern --devices auto --sample 300 \
    --images-tag v0.0.0          # 画像は既定で bench の Release から取得。Drive を使うときだけ: --use-drive --drive /content/drive/MyDrive/wikipedia-vision-decision-bench-colab
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
| `CPU_SPEED_N` / `--cpu-speed-n N` | 既定 25（0 = 無効）。`DEVICES` に cuda があり cpu が**無い**ときだけ、各モデルの cuda ブロックの後に、**同じ N 問**（先頭の set × 先頭の言語から固定 seed で選ぶ。全モデル共通）を CPU でも解き、1 問あたりの時間（中央値）の参考値を出す。cpu デバイスを回すときは不要なので何もしない。下の「CPU 速度の参考値」 |
| `CPU_SPEED_MAX_S` / `--cpu-speed-max-s S` | 既定 600。1 モデルの CPU 速度測定の問の処理時間の上限（秒。モデルの読み込みは数えない）。超えたら、そこまでの問数で打ち切り（最低 3 問は解く）。結果に `speed_stopped_early: true` |
| `--time-budget-h` | 既定 11。超えたら新しいブロックを始めない（無料枠は 12 時間で切れる。同じコマンドで続きから） |
| `MODEL_DIRS` / `--model-dir KEY=PATH` | 取得済みの重みの場所（Drive でよい）。通常は不要（各 `download_model.py` が取る）。使うと取得は行わず、重みも消さない |
| `RELEASE_TAG` / `--release-tag` | 各 `download_model.py` に渡す `--tag`。既定 `v0.0.0`（全リポジトリの最初の Release。`latest` が使えない場合に備えて固定）。`""` で各スクリプトの既定（最新の Release） |
| `IMAGES_TAG` / `IMAGES_URL` / `IMAGES_ZIP` / `IMAGES_SHA256` | 画像 zip: 既定は bench の Release（`--images-tag`、既定 `v0.0.0`）。別の URL / 手元・Drive のパス（URL より優先）/ sha256 で上書き |
| `USE_DRIVE` / `--use-drive` | **CLI の既定はオフ**（ノートブックの設定セルは `USE_DRIVE = True`、`DEVICES = "cuda"`、`RUN_SIZE = "全問"` が既定）（マウント・同期・キャッシュ・復元をしない）。`True` / 指定したときだけ Drive を使う（`DRIVE_DIR` / `--drive`） |
| `MODELS` / `--models` の既定 | 全モデル。**全リポジトリを最初に clone**（共有は 1 回）し、重みは `download_model.py` で取得。重みの削除は `WEIGHTS=auto`（全部は入らないときだけ、測定後に削除）|

## 再開と保存（/content は揮発する）

**Drive オフ（既定）のとき**: 結果・ログは `/content`（`results/runs/v1`、`work/logs/v1`）に置かれ、**セッションが切れると消えます**。持ち帰り: ① bench の最中も 1 モデルごとに `work/colab/out/colab_results_partial.zip` を作り直す、② `report` ステップ（ノートブックの `cli("report")`）が最終の `colab_results_<日時>.zip` を作る、③ ノートブックの「結果のダウンロード」セルが `files.download` で zip を落とす（左のファイルパネルからも取れる）。止めたあとでも `report` を実行すればその時点までの zip になります。ログまで消えた新しいセッションでは最初からやり直しです（Drive を使えば続きから）。

**Drive オン**（`--use-drive`）のとき:

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
| Jev API | 重みなし。`TYPESAFE_API_KEY`、有料、3 並列（画像は 256 px 以上に拡大して送る） | — | GPU 不要 |

GPU 1 問あたりの時間は、作者の PC（RTX 3050 Ti Laptop 4 GB）の値しかありません（JEVision 75 ms / OneJev 87 ms）。T4 は未測定。

## 時間について（参考値の扱い）

- bench の時間の採用ルールは「ブロックの前後に GLiNER 較正（固定の CPU 処理の中央値）を測り、どちらも 600 ms 以下」（静かな作者の PC で約 170〜200 ms）。**Colab の CPU は別の機械**なので、この閾値で「有効」になっても PC の表と並べて比べてはいけません。
- `run_colab.py` は CPU ブロックの前後に較正を測って `results/runs/v1/<ブロック>.json` の `calibration` と `blocks.log` に書きます（GLiNER2.5-Decide を取得できたとき）。**CPU の時間は参考値**として扱います。GPU の時間は bench でも較正の対象外です。
- `runner.batch` は使いません（較正が 600 ms を超えると 300 秒 × 12 回待つため）。`runner.run` を直接呼びます。
- スレッド数は既定で `min(8, CPU 数)`（Colab 無料枠は少ない）で、実際の値が結果に記録されます。CPU の測定は onnxruntime-gpu の CPU プロバイダ（GPU があるとき）で行うため、CPU 専用ビルドとは差が出る可能性があります（未確認）。

## CPU 速度の参考値（GPU だけで実行するとき）

`--devices cuda`（ノートブックの `DEVICES = "cuda"`）では本番ブロックは GPU だけです。精度は GPU の結果で足りるので、CPU は**少数問だけ**解いて、1 問あたりの時間の参考値を出します。

- **対象**: `cuda` を含み `cpu` を含まないとき（`--cpu-speed-n 0` で無効）。ローカルモデルだけ（OpenAI は対象外）。cpu デバイスも回す設定のときは、本番ブロックの CPU 時間があるので何もしません。
- **問**: 先頭の set × 先頭の言語（既定 photo / en）から、固定 seed（20261012）で N 問を選び、**全モデルで同じ問**（`work/colab/samples/cpuspeed_*.txt`）。
- **ブロック名**: `<model>_v1photo_en_224_cpu_speed<N>`（結果 `results/runs/v1/` の json / csv、ログ `work/logs/v1/`）。json に `speed_only: true`・`speed_questions`・`speed_max_seconds`・`speed_stopped_early` が入ります。再実行は既存の再開に乗り（終わったブロックは飛ばす）、Drive 同期の対象でもあります。
- **精度の集計には入りません**: `report/v1_models.py` は suffix に `_speed` を含む結果を run として拾わないので、正答率の表・「全 run が答えた質問」の共通集合・ヒートマップ・ベン図には混ざりません（`colab_summary.md` でも別の節）。`v1_report.html` の「速度」セクションにだけ、「CPU 速度の参考値」の表（CPU の問数・中央値・平均・90%、**同じ問の GPU 中央値**、問ごとの CPU / GPU の比、測定環境の CPU 名・コア数、較正の状態）として出ます。`colab/make_v1_report.py` が `speed_cpu_v1.json` を一時フォルダに作って `report/v1_report.py` に渡します。
- **時間の有効性**: CPU ブロックの前後の GLiNER 較正は、GLiNER2.5-Decide を取得できたときだけ記録します（記録が無ければ表に「較正なし（参考値）」）。Colab の CPU は少数コアで、手元の PC とは別の機械です。**手元 PC の CPU 時間と並べて比べないでください**（ページにも注記があります）。
- **上限と失敗**: 1 モデルあたり `--cpu-speed-max-s`（既定 600 秒）。重い CPU モデルは上限で打ち切って、そこまでの問数の中央値を出します（最低 3 問）。モデルの読み込み時間と、1 問の途中は上限に数えません（1 問がとても長いと上限を超えます）。メモリ不足・読み込み失敗・半数超が NA のときは、他のモデルを止めずに、最後の一覧（`cpu-speed` 行）に理由を出します。文書化された RAM の下限に届かないモデルは、重みを取得せずにスキップします。
- **メモリ**: モデルごとに「cuda ブロック → CPU 速度ブロック」の順で、どれも**別の子プロセス**なので、GPU 用のセッションは CPU の測定の前に解放済みです（VRAM / RAM を圧迫しません）。
- 先頭の問には、モデル読み込み直後の初回実行の時間が入ります（中央値なので影響は小さい）。

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

画像（`images-224px.zip`、約 20 MB、2127 枚 + `ATTRIBUTION.md`）は Wikimedia Commons の CC0 / パブリックドメインの写真と、bench のスクリプトが描いた画像で、リポジトリには入っていません。モデルの重みと同じく **bench リポジトリの GitHub Release からダウンロード**します（既定: `https://github.com/<owner>/wikipedia-vision-decision-bench/releases/download/v0.0.0/images-224px.zip`）。優先順は `--images-zip`（`IMAGES_ZIP`）→ Drive キャッシュ（`--use-drive` のとき）→ `--images-url`（空なら上の既定の Release）。sha256 は Release の `SHA256SUMS` と照合（無ければ `--images-sha256`、それも無ければ 2026-10-11 のビルドの値 `c079de92...`）。途中で切れたダウンロードは `.part` から再開し、Release が `images-224px.zip.partNN`（2 GiB 超）に分かれていれば `SHA256SUMS` を見て結合します。展開は zip の外に出る名前を拒否します。

失敗の原因は終了コードで区別し、ノートブックが案内を出します: 3 = Release 未公開 / タグ違い（404）または `--images-zip` が無い、4 = ネットワーク、5 = sha256 不一致、6 = 展開後に問の画像が足りない。Release が取れないときの最後の手段は、Commons からの自前取得（`python -m datasets.fetch fetch`）の**案内のみ**です（Commons の写真しか取れず、biz / rsn の描画画像は含まれない。連絡先は環境変数 `WIKIQA_CONTACT` で渡す: Colab では Secrets に自分の連絡先を設定し、ファイル・ログ・出力には書かない）。

### Release を作る（作者側。アップロードはしていない）

```bash
uv run python -m datasets.build_v1                 # dist/v1/images-224px.zip（画像が手元にあるとき）
uv run python tools/make_images_release.py         # 検査（問が使う 2127 枚が全部入っているか・sha256_224・ATTRIBUTION.md）→ dist/v1/release/{images-224px.zip,SHA256SUMS}
gh release create v0.0.0 --repo <owner>/wikipedia-vision-decision-bench --title "v1 images (224 px)" --notes "..." dist/v1/release/images-224px.zip dist/v1/release/SHA256SUMS
```

zip に `ATTRIBUTION.md`（ファイルごとの題名・作者・ライセンス・元 URL。Commons 由来の画像は CC0 / パブリックドメインのみ）を同梱します。Wikipedia の本文は含みません。zip が 2 GiB を超えるときは `make_images_release.py` が `images-224px.zip.partNN` に分割します（今回は約 20 MB で 1 ファイル）。`.zip` と `dist/` は git に入りません。

## 集計と HTML

`report` ステップは次を作ります（`work/colab/out/`）。
- `colab_summary.{md,csv,html}`: ブロック別、グループ別・形式別の正答率、モデル × デバイスの状態（ok / skipped: 理由 / failed: 理由）。「run here」列は、この Colab（または Drive から戻したこの環境のセッション）で測ったブロックかどうか。
- `v1_report.html`: `report/v1_report.py` のダッシュボード（全 run の比較表・A/B 選択式の詳細・全モデルのヒートマップ・質問探索）。モデルと run は結果ファイル名（`<model>_v1all_<lang>_224[_cpu|_cuda]`）から**自動検出**します（`report/v1_models.py`。表示名・色は既定の表、未知のモデルは自動）。`colab/make_v1_report.py` が、`report/` を変更せずに、問題ファイルなどの入力を**一時フォルダ**に作って呼びます。
  - `photo` / `biz` / `rsn` / `txt` / `all` のブロックを、(モデル, デバイス, 言語) ごとに 1 つの run に結合
  - **全 run が答えた (問, 言語) だけ**を比べる（答えていない問を誤答として数えないため。サンプルやスキップしたモデルがあると、共通の問だけになる）
  - `cases_v1.jsonl` / `questions_v1.jsonl` は `datasets/build_v1.py` の関数で `datasets/questions` から作り直す（画像は不要。画像は埋め込まない）
  - 本文（Wikipedia の passages.json）がない機械では、文章のみの問の本文は代わりの表示になり、ページにその旨を出す（正誤の集計には影響しない）。`--strict-passages` を付けると、本文がないとき代わりの表示にせずエラーで止める
  - 「CPU と GPU の比較」は、同じモデルが cpu と cuda の run を両方持つときだけ出ます（詳細の A で選んだモデル）。
  - 結果にはこの Colab のブロックだけを使います（`work/colab/blocks/` のサイドカーがあるもの。`--include-all-blocks` で全部）。
  - ローカルで、このリポジトリの試行結果（jevision CPU/GPU と openai の `all`）に対して実行し、HTML が作られ検査 3 件が OK になることを確認しました。ブロックを分けた結果の結合も、試行結果を分割した擬似データで確認しました（実際の Colab の結果では未実行）。
- 結果の zip（`colab_results_<日時>.zip`: 結果 json/csv、ログ、デバイス確認、集計、v1_report.html）

## 実行環境の記録

Colab も `runner.run` 経由なので、結果 json に `host`（CPU・コア数・RAM・OS・GPU 名/VRAM/ドライバ/CUDA・onnxruntime・スレッド数、`source: "measured"`）が自動で入り、`v1_report.html` の「実行環境」と比較表の環境列に出ます（ホスト名・ユーザー名・パスは書きません）。自分の PC と Colab の結果が混ざるときは、時間の列を環境をまたいで比べないでください（ページに注記が出ます）。

## clef の CUDA 診断（任意）

スモークで clef が CUDA だけ全問失敗したとき（例: `MemcpyToHost ... CUDA failure 1: invalid argument`。スモークの失敗文には各問の最初のエラー文が入ります。OOM とは限りません）は、`python colab/diagnose_clef_cuda.py [--download] [--quick]` で切り分けます（ノートブックからは削除済み。Colab のセルで `!python colab/diagnose_clef_cuda.py --download` として呼べます。clef の CUDA は Clef リポジトリの修正後に A100 で動作確認済み）。環境情報（onnxruntime / -gpu、プロバイダ、GPU・ドライバ・CUDA / cuDNN）を出したあと、1 問だけ `CUDA_LAUNCH_BLOCKING=1` と ORT の詳細ログで実行して最初のエラーと失敗ノード周辺を要約し、続けて条件を変えた再試行（テキストのみ、`require_gpu`、アリーナ / cuDNN / `gpu_mem_limit` / TF32 / コピーストリームの CUDA オプション、最適化レベル低下、メモリパターン無効。`--heavy` で `keep_bf16=False`）を 1 条件 1 プロセスで行い、成功 / 失敗 / 最初のエラーを 1 行ずつの表にします（1 試行 240 秒・全体 20 分が上限。生ログは `work/colab/diag_clef/NN_<条件>.log`、要約は `summary.json`）。読み方: 全条件が失敗なら「この Colab（A100）の CUDA では clef は非対応（CPU のみ）」とみなし、最初のエラーと `01_blocking_verbose.log` を作者に渡す材料にします。特定の条件だけ成功したら、その設定が回避策の候補です（ベンチへ反映するには clef アダプタの変更が必要）。ベースラインが成功した場合は未再現（ベンチ側の状態の違いを疑い、スモークを `--recheck` で再実行）、成功した CUDA 条件は CPU の出力との差も表示します。ローカル（GPU なし・重みなし）では構文・`--dry-run`・1 試行の配管までの確認で、Colab での実行結果は未確認です。

## 秘密の扱い

`GITHUB_TOKEN` / `OPENAI_API_KEY` は環境変数だけ（ノートブックが Colab Secrets から入れる）。出力・ファイル・URL には出しません（子プロセスの出力は、値が含まれていたら `***` に置き換えます）。ノートブックは出力を消した状態で保存してあります。コミット前に `python tools/scan_secrets.py` を実行してください。

## 未検証（実際の Colab でしか確認できない）

- Colab 上での実行全体（uv のインストール、`--system` と externally managed の扱い、Python のバージョン）
- onnxruntime-gpu の版（CUDA 12 系 / 13 系の選び方）と CUDA ライブラリの検索、T4 での各モデルの動作・速度・VRAM
- Drive のマウント・保存・復元の実動作、`google.colab.userdata` と `files.download`
- 各モデルのリポジトリ・Release の公開状況、`download_model.py` の実動作（非公開は取得不可）
- 画像 Release（`v0.0.0` の `images-224px.zip` + `SHA256SUMS`）が公開されていること・GitHub からのダウンロードの実動作（ローカルでは、同じ形式の Release をローカルの HTTP サーバに置いて、単一 / 分割 / 404 / sha256 不一致の 4 通りの取得を確認した）
- `providers_used` が各モデルの実装で読めるか（読めないモデルは cuda がスキップされる）
