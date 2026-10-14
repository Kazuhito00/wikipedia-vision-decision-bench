# wikipedia-vision-decision-bench

[English](README_EN.md)

型付き判定モデル（選択 `choice`・はい／いいえ `noul`・段階評価 `score`）の**画像理解**を、Wikimedia Commons の写真（CC0／パブリックドメインのみ）、スクリプトで描いた業務画像（UI・帳票・チャート）、推論用の描画画像で測るベンチマークです。質問は英語と日本語の両方で出します。

- 測るもの: 正答率（言語別・問題群別・形式別）と、CPU／GPU での 1 問あたりの時間（較正が合った測定だけ）。
- モデルとの結合は `adapters/` だけです。各モデルは**自分のリポジトリ（`<OWNER>/<モデル名>-ONNX-CPU`）のパッケージ**を入れた環境で動かします。
- **画像と Wikipedia の本文は、このリポジトリに入っていません。** 入っているのは一覧（ID・ライセンス・作者・URL・sha256）と質問だけです。画像は Release の zip で配ります（準備中）。
- **データセットの版**: 現行は **version 1（`v1`）**（2768 問、`datasets/questions/v1/`、`dist/v1/`）です。問の ID（`photo-0001`、`biz-1001` など）は版名を含みません。

## 構成

```
wikipedia-vision-decision-bench/
├─ README.md  README_EN.md  pyproject.toml  .env.example  .gitignore
├─ adapters/        モデルごとの ask()。呼び出し規約は 1 つ（adapters/__init__.py）
├─ runner/          run.py（1 モデル×問題群×言語。再開可能）、batch.py（較正ゲートつきの一括実行）、config.toml（測定条件）
├─ report/          v1_report.py ＋ HTML テンプレート（結果のまとめページ。`--no-images` で画像なし）
├─ datasets/        questions/（質問）、synthetic/（描画画像）、fetch/（取得と検査）、manifests/（一覧）、tests/、NOTES.md
├─ release/         make_image_release.py（画像 zip を dist/ に作る。アップロードはしない）
├─ results/         集計だけ（runs/<dataset_version>/*.json・*.csv、checks/*.json）。問ごとのログと生成 HTML は載せない
├─ colab/           Google Colab で回す（ノートブックと run_colab.py。取得→CPU・GPU 測定→集計を 1 本で。`colab/README.md`）
├─ tools/           scan_secrets.py（コミット前のキー混入検査）
└─ work/ dist/      ローカル専用（git 管理外）: 画像、ログ、API キャッシュ、生成 HTML、zip
```

## 再現手順（環境は uv だけ）

```powershell
uv sync                                             # ベンチ本体（pillow, numpy）
copy .env.example .env                              # 必要な値だけ入れる（.env は git 管理外）
```

**1. 画像を用意する**（どちらか）

```powershell
# (a) Release の zip から（ネットワーク不要・sha256 を 1 枚ずつ照合。Release は準備中）
uv run python -m datasets.fetch fetch --from-release <zip を置いたフォルダ>
# (b) Commons から取得（WIKIQA_CONTACT 必須: メールアドレスかリポジトリの URL）
$env:WIKIQA_CONTACT = "<連絡先>"
uv run python -m datasets.fetch fetch
```

画像は `work/data/images/`（Commons の保存画像）と `work/px224/`（モデルへの入力: 長辺 224px）に置かれます。

**2. モデルの環境を作る**（モデルごとに別の venv。モデルの重みは各モデルのリポジトリの Release から取得）

```powershell
uv venv .venv-onejev
uv pip install --python .venv-onejev onnxruntime numpy pillow
uv pip install --python .venv-onejev "git+https://github.com/<OWNER>/OneJev-ONNX-CPU@<tag>"      # モデルのパッケージ
# モデルのリポジトリに pyproject がまだ無い間の暫定: チェックアウトを PYTHONPATH に置く
$env:PYTHONPATH = "<OneJev-ONNX-CPU のチェックアウト>"
$env:ONEJEV_MODEL_DIR = "<OneJev-ONNX-CPU>/models/onnx"       # モデルの場所は環境変数か --model-dir
```

依存は `pyproject.toml` の任意グループ（`onejev` `openjev` `intern` `strands` `clef` `jevision` `qev` `d3`（d3edge / d3lite / d3nano 用） `calibrate`）にも書いてあります。GPU は `onnxruntime` の代わりに `onnxruntime-gpu`（Windows は `onnxruntime-directml` も可）を入れ、`uv run --no-sync` で動かします（CPU 版に戻されないため）。

**3. 測る**

```powershell
.venv-onejev\Scripts\python -m runner.run --model onejev --set photo --lang en            # 1 ブロック
.venv-onejev\Scripts\python -m runner.run --model onejev --set photo --lang en --gpu      # CUDA（CPU がフォールバック）
copy runner\models.example.toml runner\models.local.toml                                  # モデルごとの python / model_dir を書く
uv run python -m runner.batch --models onejev,jevision --sets photo,biz,rsn,txt --langs en,ja   # 較正ゲートつきの一括（再開可能）
```

**4. 見る**

```powershell
uv run python -m runner.analyze_v1                                   # results/runs/v1/summary_v1.md・per_question_v1.csv
uv run python -m report.v1_report --out results/まとめ_v1.html          # 結果のまとめページ（画像つき・ローカル専用）
uv run python -m report.v1_report --no-images --out results/まとめ_v1.html   # サムネイルなし
```

**5. テスト**（ネットワーク不要）

```powershell
uv run python -m unittest discover -s datasets/tests
uv run python -m unittest discover -s datasets/fetch/tests -t .
uv run python -m unittest discover -s tools -p "test_*.py"
```

## 測定条件

| 項目 | 値 | 設定の場所 |
|---|---|---|
| スレッド数（onnxruntime） | 8 | `runner/config.toml` の `threads`（`THREADS`、`--threads`） |
| 画像の縮小 | 長辺 224px（LANCZOS、JPEG） | `px`（`PX`、`--px`） |
| 選択肢の順序の入れ替え | なし（`REV=0`）。位置の偏りを見たいときだけ `--rev 1` | `rev`（`REV`） |
| 画像 | 1 問 1 枚 | — |
| 時間の採用 | ブロックの前後に較正（固定の CPU 処理の中央値）を測り、どちらも 600 ms 以下のブロックだけ。静かな機械で約 170〜200 ms | `[gate]`、`runner/calibrate.py`、`blocks.log` |
| 結果の記録 | モデルのリポジトリとタグ、variant、実際に使われたプロバイダ、スレッド数、px、rev、dataset_version、一覧の sha256 | `results/runs/<dataset_version>/<ブロック>.json` |

結果は `(dataset_version, id)` をキーに保存します（`results/runs/<dataset_version>/*.csv` は 1 問 1 行）。

## 問題群の構成（v1: 2768 問）

選択肢の数は 2〜16 択、段階の数は 3・5・7・10 段階で、否定・数える・位置関係・「該当なし」の問、日本語固有の問、均等な正解位置、1 問 1 枚を備えます。分類は実写／業務画像／推論／文章のみ。数字は `dist/v1/manifest_v1.json`（`python -m datasets.build_v1`）から取っています。

| 群 | 問数 | 中身 |
|---|---|---|
| photo（実写） | 1476 | Commons 写真（2・3・5〜16 択、否定、該当なし、位置、数える、段階評価） |
| biz（業務画像） | 646 | 描画、本物の Tkinter 画面のスクリーンショット 249、日本語固有 101 |
| rsn（推論） | 460 | 多択、3/7/10 段階、否定、矛盾、不確かさ |
| txt（文章のみ） | 186 | 画像問から画像を外した対照 99 ほか |
| **計** | **2768** | |

- 形式: 選択 2091 / はい・いいえ 537 / 段階評価 140（3 段階 35・5 段階 45・7 段階 35・10 段階 25）。選択肢数: 2 択 72 / 3 択 125 / 4 択 1495 / 5〜8 択 343 / 9〜16 択 56。
- 言語: en・ja 両方 2596 問、日本語のみ 172 問。難度: easy 961 / medium 1328 / hard 479。
- 画像 2127 枚: Commons 写真 1021（CC0・パブリックドメイン）、描画画像 1106（スクリプトで作成）。1 問 1 枚。画像の zip は 224px 版 約 20 MB・原寸版 約 308 MB（Release に置く予定。まだアップロードしていません）。
- **文章のみの対照の注意**: 対照の `state` には画像にない正確な数値が入るため、文章版は画像版より易しくなり得ます。比較するときは、この点を明記してください。
- 結果は `(dataset_version, id)` で記録します。
- 定義・作り方・既知の制約（画像の判読性、フォント、Tkinter 画像の OS 依存、生成スクリプトの `--apply` で jsonl が上書きされる注意）は `datasets/NOTES.md` §11。

使い方:

```powershell
uv run python -m datasets.build_v1                 # dist/v1/ に問題・ケース・画像一覧・zip・検査結果（build_report.md）を作る
# 画像: images-original.zip（または images-224px.zip）を空のフォルダに展開し、そのフォルダを指す
$env:WIKIQA_DATA_ROOT = "<展開したフォルダ>"        # <フォルダ>/data/images/..., <フォルダ>/generated/... が見える場所
.venv-onejev\Scripts\python -m runner.run --model onejev --set all --dataset-version v1 --lang en
# セット: photo / biz / rsn / txt / all / new（新問だけ）。txt の記事由来の問は手元の passages.json（本文は配布しない）が要ります
```

## 全モデルの比較表

| モデル | サイズ / 精度 | 基になるモデル | 依存 | 画像の上限 | 選択肢の上限 | 取得（予定） |
|---|---|---|---|---|---|---|
| OpenJev 0.8B | 0.8B / fp16 | Qwen3.5-0.8B（無調整） | onnxruntime・numpy・pillow | 未確認 | 255 | `<OWNER>/OpenJev-ONNX-CPU` の Release |
| Intern-Decision 0.8B | 0.8B / fp32 | Qwen3.5-0.8B（全体を調整） | 同上 | 8 枚（グラフは 512 トークン固定: 224px 専用） | 255 | `<OWNER>/Intern-Decision-0.8B-ONNX-CPU` |
| d3-edge 0.6B | 0.59B / fp32 | Qwen3.5-0.8B（12 層に刈った調整版） | onnxruntime・tokenizers・numpy・pillow | 枚数の制限なし（最大グラフ 2048 トークンまで） | 255（段階 2〜10） | `Kazuhito00/D3-ONNX-CPU`（キー `d3edge`。Release は未アップロード） |
| d3-lite 0.9B | 0.85B / fp32 | Qwen3.5-0.8B（調整） | 同上 | 同上 | 同上 | 同上（キー `d3lite`） |
| d3-nano 2B | 2.21B / fp32 | Qwen3.5-2B（調整） | 同上 | 同上 | 同上 | 同上（キー `d3nano`）。d3-mini 5B は未対応（export にメモリ約 25GB） |
| JEVision 0.8B | 0.8B / fp16 | Qwen3.5-0.8B（調整） | 同上 | 4 枚 | 255 | `<OWNER>/JEVision-0.8B-ONNX-CPU`（作成中） |
| OneJev 0.8B | 0.8B / fp16 | Qwen3.5-0.8B（全体を調整） | 同上 | 未確認 | 255（段階 10） | `<OWNER>/OneJev-ONNX-CPU` |
| QEV 2B | 2B / fp32 | Qwen3.5-2B（調整） | 同上 | **1 枚** | 2〜16 | `<OWNER>/QEV-2B-ONNX-CPU`（作成中） |
| Strands Decider 2B | 2B / fp32 | Qwen3.5-2B-Base ＋ LoRA | 同上 | 4 枚 | 2〜255（段階 2〜10） | `<OWNER>/Strands-Decider-2B-ONNX-CPU` |
| OpenJev 4B | 4B / q4f16 | Qwen3.5-4B（無調整） | 同上 | 未確認 | 255 | `<OWNER>/OpenJev-ONNX-CPU` |
| OneJev 4B | 4B / fp16 | Qwen3.5-4B（調整） | 同上 | 未確認 | 255（段階 10） | `<OWNER>/OneJev-ONNX-CPU` |
| clef-flash 9B | 9B / bf16 重み・fp32 計算 | Qwen3.5-9B（調整） | 同上（メモリ大） | 4 枚 | 未確認 | `<OWNER>/clef-flash-ONNX-CPU` |
| OpenAI Decisions API | 非公開 | 不明 | ネットワークと API キー | — | — | — |

測定結果は `report/v1_report.py` で作るレポート（`results/runs/v1/`）にまとめます。

## データの検査（リンク切れ・差し替え・ライセンス変更）

画像の一覧は `datasets/manifests/` にあります。Commons 側の変化を検出するコマンドがあります（`WIKIQA_CONTACT` 必須）。

```powershell
uv run python -m datasets.fetch check --limit 20     # メタデータだけを 50 件ずつ問い合わせる（ダウンロードしない）
uv run python -m datasets.fetch check                # 全件 → results/checks/check_<日時>.json
uv run python -m datasets.fetch fetch                # 画像を取得し sha256 を一覧と照合、224px に縮小して再照合
uv run python -m datasets.fetch refresh              # 変更の予定を表示（書き換えない）
uv run python -m datasets.fetch refresh --apply      # 確認のうえで一覧に反映
```

| 状態 | 意味 | 対応 |
|---|---|---|
| 正常 | 存在し、sha1 とライセンスが一覧と同じ | なし |
| リンク切れ | 404・削除・名前の変更 | 問を無効にするか代わりを選ぶ（結果に母数の変化を記録） |
| 差し替え | sha1（または更新日時）が違う | 差分を確認して `refresh --accept-replaced`。評価済みの結果は古い画像によると明記 |
| ライセンス変更 | CC0／パブリックドメイン以外になった | 一覧と Release から外す |
| 作者・説明の変更 | 帰属情報が変わった | 一覧を更新 |

注意: 保存画像は Commons の**幅 640px のサムネイル**で、`sha1` は Commons 上のフルサイズ原画のものです。224px 画像の sha256 は Pillow／libjpeg の版で変わりうるため、厳密な再現には Release の `images-224px.zip` を使ってください。

## ライセンスと帰属

- 画像: Wikimedia Commons の CC0／パブリックドメインのみ（一覧の集計: パブリックドメイン 781 枚・CC0 242 枚）。作者・ライセンス・URL は一覧と、各 zip の `ATTRIBUTION.md` にあります。公開前に `check` で、集めた後にライセンス表示が変わっていないかを確認します。
- Wikipedia の本文（CC BY-SA）は、リポジトリにも Release にも置きません（必要な問だけ、取得コマンドがローカルの `work/` に置きます）。
- 自作の画像（描画画像 1106 枚）は **CC0-1.0**（Public Domain Dedication）で確定しています。描画スクリプトは `datasets/synthetic`、画像内の日本語は Noto Sans JP / Noto Serif JP（OFL 1.1。フォントは配布しません）で描いています。
- 透明性の注記: 画像内の文字の描画に Windows 同梱フォントを使った画像が含まれます（Tkinter の画面 249 問: 英語 UI の Segoe UI 203、日本語 UI の Yu Gothic UI 46。画面は自作でスクリーンショットに OS の枠は含みません）。該当 ID の一覧は `datasets/manifests/windows_fonts_images_v1.md` です。事実の記載であり、法的な判断ではありません。
- 生成した HTML は Commons の画像を含むため**ローカル専用**です（`*.html` は git 管理外）。公開するときは `--public`（画像なし）を使います。
- OpenAI のキーは環境変数から読みます。`.env` は git 管理外で、`python tools/scan_secrets.py` をコミット前に実行します（キーの文字列は表示しません）。

## 公開前チェック

```powershell
uv run python tools/scan_secrets.py                 # キー混入の検査
uv run python -m datasets.fetch check               # Commons 側の変化
uv run python -m release.make_image_release --originals work/data/images --px224 work/px224   # dist/ に zip（アップロードはしない）
```
