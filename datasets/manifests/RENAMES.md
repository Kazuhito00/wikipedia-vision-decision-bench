# 版名の改名マップ（2026-10-11）

このリポジトリは新規作成で、**今回のデータセット（それまで "v2"）が version 1（`v1`）**。**旧 wiki_qa 由来の凍結 1962 問（それまで "v1"）は `legacy`**（リポジトリ作成前の素材。対応表 `idmap_legacy_v1.csv` と旧結果の再現ゲート `tools/regroup_check.py` のためだけに残す）。
問の ID（`photo-0001`、`biz-1001`、`rsn-0102` など）は版名を含まないので変えていない。置換の順序は「先に 旧 v1 → legacy、そのあと v2 → v1」（衝突を避けるため）。

## 計画（置換する／しない）

置換する（スクリプトで機械的に。対象は `.py` `.md` `.toml` と manifests の csv ヘッダ・jsonl の 3 項目・画像の置き場）:

| 種類 | 旧 | 新 |
|---|---|---|
| 版の値（dataset_version、`case_key`、`(version, id)` キー、`VERSIONS`、`options` のキー、results のキーとディレクトリ） | `"v1"` / `"v2"` | `"legacy"` / `"v1"` |
| `datasets/version.py` | `DATASET_VERSION = "v2"` | `DATASET_VERSION = "v1"`（`DIST_SUBDIR` は連動し `dist/v1/`） |
| 行のキー | `v1_id` | `legacy_id` |
| 行の `origin` 値 | `"v2-new"` | `"new"` |
| 行の `local_images` | `v2_images/<id>.png` | `generated/<id>.png` |
| idmap の列 | `v1_id, v2_id, group_v1, group_v2` | `legacy_id, v1_id, group_legacy, group_v1` |
| 旧分類表の列 | `tags_v1, v2_id` | `tags_legacy, v1_id` |
| 問題ファイル | `datasets/questions/v1/`（旧凍結）／`v2/` | `legacy/` ／ `v1/`（`new_*.jsonl` も `v1/` 内） |
| manifests | `idmap_v1_v2.csv`、`idmap_v2_new_*.csv`、`questions_v1.csv`、`questions_v2.csv`、`questions_v2_new_*.csv`、`images_v1.json`、`v1_freeze.json`、`v1_option_order.csv`、`gap_analysis_v2*.md`、`privacy_check_v2.md`、`needs_new_image_type_v2.md`、`dedupe_v2.md` | `idmap_legacy_v1.csv`、`idmap_v1_new_*.csv`、`questions_legacy.csv`、`questions_v1.csv`、`questions_v1_new_*.csv`、`images_legacy.json`（中の `manifest_version` / `dataset_version` も `"legacy"`）、`legacy_freeze.json`、`legacy_option_order.csv`、`gap_analysis_v1*.md`、`privacy_check_v1.md`、`needs_new_image_type_v1.md`、`dedupe_v1.md` |
| ツール・スクリプト | `build_v2.py`、`freeze_v1.py`、`make_v2_seed.py`、`v2_io.py`、`dedupe_v2.py`、`gap_analysis_v2.py`、`review_notes_v2.py`、`synthetic/gen_v2_*.py`、`tests/test_v2_dropped_dedupe_rewrite.py` | `build_v1.py`、`freeze_legacy.py`、`make_v1_seed.py`、`v1_io.py`、`dedupe_v1.py`、`gap_analysis_v1.py`、`review_notes_v1.py`、`synthetic/gen_v1_*.py`、`tests/test_v1_dropped_dedupe_rewrite.py` |
| 関数・定数・引数 | `load_v2_cases`、`idmap_v1_v2`、`idmap_v2_new`、`v1_to_v2`、`v2_to_v1`、`v2_orders`、`V1_FILES`、`V2_SETS`、`v2_set`、`load_cases_v1`、`V2DIR`、`--v2dir`、`taxonomy.V2_*`、`group_v1`/`group_v2` など | `load_v1_cases`、`idmap_legacy_v1`、`idmap_v1_new`、`legacy_to_v1`、`v1_to_legacy`、`v1_orders`、`LEGACY_FILES`、`V1_SETS`、`v1_set`、`load_cases_legacy`、`V1DIR`、`--v1dir`、`taxonomy.V1_*`、`group_legacy`/`group_v1` など |
| dist | `dist/v2/{questions_v2.jsonl, cases_v2.jsonl, manifest_v2.json, images_v2.json, idmap_v1_v2_full.csv, questions_v2_all.csv}` | `dist/v1/{questions_v1.jsonl, cases_v1.jsonl, manifest_v1.json, images_v1.json, idmap_legacy_v1_full.csv, questions_v1_all.csv}`（旧 `dist/v2` は削除。旧 `images_v1.json` は先に `images_legacy.json` へ退避） |
| 画像の置き場（ローカル） | `work/v2_images/`（`px224/` ごと）、`work/v1_regen/`、`work/px224_v2`（キャッシュ名。実体なし） | `work/generated/`、`work/legacy_regen/`、`work/px224_v1` |
| 派生 origin（build が付ける） | `"v1-derived"` | `"legacy-derived"`（`dist/v1/questions_v1.jsonl` の `origin`、`manifest_v1.json` の `by_origin`） |
| runner のセット名 | `v2photo / v2biz / v2rsn / v2txt / v2all / v2new` | `photo / biz / rsn / txt / all / new`（旧 legacy 用の `commons / synthetic / reasoning` はそのまま。`--dataset-version` で区別。`batch.py` は `commons/synthetic/reasoning` なら legacy、それ以外は v1） |
| runner のログのブロック名（`[blocks]` の値） | `v2photo` 等 | `v1photo / v1biz / v1rsn / v1txt / v1all / v1new`（legacy の `rsn`＝reasoning とログ名が衝突しないよう、`v1` 接頭辞を付けた） |
| 画像 zip のメンバー名 | `v2_images/<id>.png` | `generated/<id>.png`（zip は build で再生成。sha256 が変わる） |
| `dsum_flags_v2`（dataset_summary の localStorage のキー） | `dsum_flags_v2` | `dsum_flags_v1`（旧キーが残っていれば読み込んで引き継ぐ） |
| モデルの repo 名（`adapters/REPOS`、docstring、README、pyproject のコメント） | `<OWNER>/onejev-onnx` ほか | `<OWNER>/OneJev-ONNX-CPU`、`OpenJev-ONNX-CPU`、`Intern-Decision-0.8B-ONNX-CPU`、`Strands-Decider-2B-ONNX-CPU`、`clef-flash-ONNX-CPU`、`JEVision-0.8B-ONNX-CPU`、`QEV-2B-ONNX-CPU`（`<OWNER>` は仮のまま） |

置換しない（意図して残したもの）:

| 残したもの | 場所 | 理由 |
|---|---|---|
| `review.history` の過去の記録（`gen_v2_rewrite.py` を含む 12 行） | `datasets/questions/v1/rsn.jsonl` | 記録の原文。`gen_v1_rewrite.py` が書く履歴の文言も旧名 `(gen_v2_rewrite.py)` のままにして、再実行時に重複して追記されないようにした |
| 乱数の種の綴り `"v2new:"`、`"v2_ba_%d"` | `synthetic/gen_v1_new.py`、`synthetic/gen_v1_rewrite.py`（と `build_v1.py` の種の説明文字列） | 変えると画像が描き直しになる（画像の sha256 が変わる）。コメントで凍結を明記 |
| 正解位置の割り当てのハッシュ入力 `"v2:<id>"` | `datasets/options.py` の `_HASH_VERSION` | キーのバージョン綴りを変えると全問の正解位置（`expected` と選択肢の並び）が変わる。`("v1", id)` のキーでも、ハッシュには旧綴り `v2` を使い、位置を完全に保った（`cases_v1.jsonl` が旧 `cases_v2.jsonl` と一致することで確認） |
| `dsum_flags_v2`（読み込み側のフォールバック） | `build_dataset_summary.py` の埋め込み JS | ブラウザに保存済みのフラグを失わないため |
| モデルパッケージのタグ `@v1` | `pyproject.toml` のコメント | モデルの repo のタグで、データセットの版ではない |
| `POST /v1/decisions` | `report/wiki_report_template.html` | 外部 API の URL |
| `OGL v1.0`、`btv1b...`、`Inv257`、`Inv2` | `domain_probe.json`、`images_legacy.json`、`photo.jsonl` | ライセンス名・ファイル名の一部で、版名ではない |
| `work/review/batch_*.json`（`v1_id` キー）、`work/cache`、`probe*.log`、`domain_probe.*` | work/、manifests | 過去の書き出し・実行中の下見の生成物。触らない（`apply_review.py` は ID だけを読む） |

## 置換件数

- 文書・コード（`.py` `.md` `.toml`）: 62 ファイル、約 1859 か所（README 32×2、NOTES 289、loader 113、build_dataset_summary 106、test_new_questions 151 など）。ほかに手で直したもの: `runner/cases.py`・`batch.py`・`config.toml`（セット名）、`options.py`（ハッシュ入力）、種の綴りの保持、adapters の repo 名、README・NOTES の版名の説明、`dsum_flags` の引き継ぎ。
- ファイル名の変更: 39 ファイル（manifests 25、tools 6、synthetic 6、build 1、tests 1）、ディレクトリ 2（`questions/v1→legacy`、`questions/v2→v1`）、`work/` 2。
- jsonl（`questions/v1/*.jsonl`、2903 行）: `v1_id` → `legacy_id` 2903 行、`origin "v2-new"` → `"new"` 941 行、`local_images` の `v2_images/` → `generated/` 637 行。
- manifests の csv: ヘッダ行 9 ファイル、`questions_v1_new_*.csv` の `origin` 941 行。

## 検証（問の内容が不変であること）

- `questions/v1/*.jsonl`: 旧 `questions/v2/*.jsonl` と行数が同じ（2903）。各行を JSON として読み、旧行に「`v1_id`→`legacy_id`、`origin`、`local_images`」だけを適用した結果と、キーの順序・値が完全に一致（不一致 0 行）。さらに、新行から 3 か所の置換を逆に戻すと旧行と**バイト単位で一致**（不一致 0 行）。設問・選択肢・正解・review の状態と history は 1 バイトも変わっていない。
- `questions/legacy/*.jsonl` は旧 `questions/v1/*.jsonl` と 4 ファイルともバイト一致（`legacy_freeze.json` の sha256 のテストも通る）。
- 再ビルドした `dist/v1/cases_v1.jsonl`（選択肢の並びと `expected` を含む）は、旧 `cases_v2.jsonl` に同じ置換を当てたものと全 2768 行で一致。`questions_v1.jsonl` も同様（0 行不一致）。画像一覧（2127 枚の sha256・ライセンス・作者・URL）も一致。
- `regroup_check`（旧 4 群と新 4 群の総計一致ゲート）は PASS（20 モデル×言語、HTML オラクル含む）で、出力は改名前のレポートと同一。
