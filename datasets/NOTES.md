# datasets/ ノート

ベンチの問題・分類・選択肢の並べ替え・テストの説明です。画像、Wikipedia の本文、ログ、`.env` はこのリポジトリに含めません（`work/` と `data/` は gitignore）。

## 1. 版（legacy と v1）と ID の規則

| 版 | 中身 | ID |
|---|---|---|
| **legacy** | これまでの 1962 問（linked 1355 = 画像 1268 + 文章のみ 87、synthetic 382、reasoning 225）。**凍結**。`datasets/questions/legacy/*.jsonl` | `img-NNNN`、`txt-NNNN`、`syn-NNNN`、`rsn-NNNN`（元のまま） |
| **v1** | legacy の 1962 問を 1 問ずつ見直して磨いた版（反映済み。§9）。足りない分の新問 927 を §10 の受け皿に書き足した。**最終は 2768 問**（§11） | `photo-NNNN`、`biz-NNNN`、`rsn-NNNN`、`txt-NNNN` |

- **版名**: このリポジトリの最初の版が **version 1（`v1`）**。**`legacy`** は、リポジトリ作成前に別の場所で作った旧素材（凍結した 1962 問）で、対応表（`manifests/idmap_legacy_v1.csv`）と旧結果の再現ゲート（`tools/regroup_check.py`）のためだけに残す。もとは v1 が旧素材・v2 が現行の呼び名だった。改名の全対応は `manifests/RENAMES.md`。問の ID は版名を含まず、変わっていない。
- **キーは常に `(dataset_version, id)`。** legacy は `rsn-NNNN`・`txt-NNNN` を既に使っていて、v1 の同じ綴りは別の問になり得ます（例: `rsn-0226` は v1 にしかない）。結果・manifest・集計は ID だけで引かないこと。ローダー（`datasets/loader.py`）の `case_key(version, id)`、`legacy_to_v1()`、`v1_to_legacy()` は版つきのキーだけを使います。
- legacy のデータは `version="legacy"` 固定で、legacy の ID のまま読めます。legacy を測った結果は、旧 ID（`img-0016` など）で残っています。
- 対応表 `manifests/idmap_legacy_v1.csv`: legacy の 1962 ID がそれぞれちょうど 1 回。v1 は「legacy を磨いたもの」が基本なので **1:1**。列は `legacy_id, v1_id, group_legacy, group_v1, status, review_state, change_note`。
  - `status`: `kept`（そのまま）/ `rewritten`（直した。2 枚画像を 1 枚に作り直した 12 問を含む）/ `dropped`（外した）/ `pending`（未決。現在 0 件。2 枚画像の問は反映直後だけ `pending` で、作り直して `rewritten`、または `dropped` にした）。
  - `review_state`: `unreviewed`（初期値）/ `reviewed` / `approved`。`change_note`: 何をなぜ直したか。
  - v1 の ID は、新しい群ごとに legacy の並び順で振った（photo と biz は 1 から。rsn は旧 reasoning の 225 問が `rsn-0001`〜`0225` で番号そのまま、そのあとに合成中の推論タグ 94 問が `rsn-0226`〜`0319`。txt は `txt-0001`〜`0087` で番号そのまま）。
- **v1 の問の行の書式**（legacy の行の項目に加えて。`datasets/questions/v1/{photo,biz,rsn,txt}.jsonl`、UTF-8・LF）:
  - `id`（`photo-0001` など）、`legacy_id`（元の問。新設なら空）、`group`（photo / biz / rsn / txt）、`source`、`image_type`、`skill`、`difficulty`、`lang`（both / en / ja）。
  - **`answer_format`**: 答え方の軸（`choice:4` / `yesno` / `score:5`）。選択肢の数から自動で再計算する（レビュアーが書いても採用しない）。**`answer` は legacy と同じく正解の値**（はい/いいえなら true/false、段階評価なら段階の位置）。軸の名前が `answer` と衝突するため、行では `answer_format`、分類表（`questions_v1.csv`）の列名だけ `answer`。
  - 選択問題は `en` / `ja` に `instr`・`correct`・`wrong`（誤答の配列。en と ja の個数は同じ）。段階評価は `levels`。選択肢の並びは行に持たず、実行時に決める（§5）。
  - **`review`**: `{state, history: [{date, what, why}, ...]}`。`state` は `unreviewed` < `reviewed`（確認済み・変更なし）< `changed`（直した）< `dropped`（外した。行はファイルに残る）。`history` は、変更の履歴（何をしたか・理由）。**同じ内容を 2 回反映しても履歴は増えない**（`apply_review.py` / `dedupe_v1.py` / `gen_v1_rewrite.py` は冪等）。
  - **評価対象から外す**: `review.state == "dropped"`（および対応表の `status == "dropped"`）の問は、ローダーが既定で除外する（§3 の `loader.py`、`include_dropped=True` で含める）。legacy には影響しない。

## 2. 本文の扱い（Wikipedia の本文は載せない）

- 文章のみの問 87 問の元データには `evidence`（記事の冒頭から取った根拠文の抜粋。英・日）があり、`items_text_*.py` にも同じ文字列が引数として入っていた。**CC BY-SA の本文なので、コピーせず除去**した。
  - 凍結した jsonl では `evidence` を `evidence_sha256`（各文字列の sha256）に置き換えた。手元に本文がある人は、一致を確かめられる。
  - `items_text_*.py` は、`tchoice` / `tnoul` の根拠の引数（`ev_en`、`ev_ja`）を `[]` にした（`datasets/tools/freeze_legacy.py` が `ast` で機械的に実行）。そのため `build_questions.py` の「根拠文が本文にあるか」の検査は、根拠を戻さない限り空振りになる。
  - 問の本体（質問・正解・誤答・記事のタイトルと revision ID）は残す。`state`（問題に付ける本文）は、手元の `passages.json`（gitignore）から実行時に読む。無いときは `FileNotFoundError`。
- 画像のファイルは含めない。行に残る `local_images` は `data/...` という論理パスだけ（`images_root` からの相対）。
- テスト `test_manifests.py` が、凍結ファイルに `evidence` が無いこと、`items_text_*.py` の根拠引数が空であること、画像ファイルと `.env` が無いことを確かめる。

## 3. ファイルの目的

| ファイル | 目的 |
|---|---|
| `newq.py` | 新問の置き場・ID の予約範囲の表（§10）。ローダー・検証・レビューが共通で使う |
| `loader.py` | 問題を評価用のケースとして読む（旧 `wikiqa.dataset.load_cases` と同じ形・同じ並び）。`(version, id)` のキー、対応表・分類表の読み込み。v1 は dropped を既定で除外（`load_cases("v1", include_dropped=False)`、`load_v1_cases(["photo", ...])`、`dropped_ids()`） |
| `options.py` | 選択肢の並べ替え（legacy / balanced / 逆順）。§5 |
| `taxonomy.py` | legacy の ID・タグから新しい分類軸と新しい 4 群を決定的に出す規則（§4 の表の実体） |
| `questions/` | 質問の定義。`dsl.py`・`templates.py`・`items_*.py`（手書きの問）、`build_questions.py`（コンパイル。legacy の履歴用。出力は `work/legacy_rebuild/` で legacy 凍結ファイルを上書きしない）、`article_titles.txt`、`http.py`・`wikitext.py`（記事冒頭の取得と整形）、`legacy/`（凍結した legacy） |
| `synthetic/gen.py`、`gen_reasoning.py` | 描画画像と問の生成（乱数の種を固定・決定的）。出力は `work/legacy_regen/`。再生成した行は凍結した legacy と一致し、画像の PNG もバイト単位で一致した（620 枚） |
| `manifests/questions_legacy.csv` | legacy の全問の分類（新しい軸） |
| `manifests/idmap_legacy_v1.csv` | legacy ID と v1 ID の対応（status・review_state・change_note） |
| `manifests/questions_v1.csv` | v1 の全問の分類（`apply_review.py` / `dedupe_v1.py` / `gen_v1_rewrite.py` が更新） |
| `manifests/dedupe_v1.md` | 重複で追加 drop した問の一覧 |
| `manifests/gap_analysis_v1.md` | v1 の不足の分析と、足す問数の提案 |
| `manifests/legacy_freeze.json` | 元ファイルと凍結ファイルの sha256、行数 |
| `manifests/legacy_option_order.csv` | 旧ローダーが作った並べ替えの正解データ（1962 問） |
| `manifests/regroup_check.md` | ゲートの結果（旧 4 群と新 4 群の総計の一致） |
| `tools/freeze_legacy.py` | legacy の凍結（本文の除去を含む。一度だけ実行した記録） |
| `tools/make_manifests.py` | 分類表と対応表を作る |
| `tools/make_golden_order.py` | 旧ローダーから並べ替えの正解データを作る（一度だけ） |
| `tools/apply_review.py` | レビュー結果（`work/review/out/*.jsonl`）を検証して v1 の行・対応表・分類表に反映する（既定は dry run、`--apply`）。冪等 |
| `tools/dedupe_v1.py` | バッチをまたぐ重複の検出と、後ろの ID の drop（§9）。`manifests/dedupe_v1.md` を作る |
| `synthetic/gen_v1_rewrite.py` | 2 枚画像の 12 問を 1 枚版に作り直す（§9）。出力は `work/generated/` |
| `tools/validate_new.py` | 新問（`new_<tag>.jsonl`）の検証と、tag ごとの manifest の書き出し（§10） |
| `tools/gap_analysis_v1.py` | 不足分析を出す（`--write` で `manifests/gap_analysis_v1.md` を再生成: 追加前後の比較表と付録の表） |
| `build_v1.py` | 最終ビルド: `dist/v1/` に問題・ケース・画像一覧・zip・検査結果を作る（§11.8） |
| `version.py` | 版名の定数 `DATASET_VERSION` |
| `tools/relabel_image_type.py` | astronomical / satellite の付け替え（変更行だけ書き、履歴に記録。冪等） |
| `tools/review_notes_v1.py` | `manifests/privacy_check_v1.md` と `needs_new_image_type_v1.md` を作る |
| `tools/drop_ids.py` | 指定した ID の問を個別に除外する（`review.state = dropped` と idmap の更新。既定は dry-run、`--apply` で書く。privacy-check の要望対応用） |
| `tools/list_windows_font_images.py` | Windows 同梱フォントで文字を描いた画像（Tkinter 249 問）の ID 一覧を `manifests/windows_fonts_images_v1.md` に作る |
| `tools/regroup_check.py` | 旧ログを旧 4 群と新 4 群で集計して総計を比べる（ゲート） |
| `tools/list_ja_for_review.py` | 日本語の質問を英語と並べて出す（機械翻訳くさくないかを目視する用。自動判定しない） |
| `tests/` | ネットワーク不要のテスト（§6） |

`fetch/`（取得と検査）は別の担当で、ここでは扱わない。

## 4. 分類の定義と写像表

軸: `group`（問題群）、`source`、`image_type`、`skill`、`answer`、`difficulty`、`lang`。**どれも legacy の ID・タグ・項目から決定的に出す**（`taxonomy.py`。目視のラベルではない）。`questions_legacy.csv` に全問分が入っている。

**問題群（`group`）** — 旧 → 新

| 旧 | 判定 | 新 | 問数 |
|---|---|---|---|
| wikipedia | `img-` で `source_unverified` なし | photo | 797 |
| expansion | `img-` で `source_unverified` あり | photo | 471 |
| synthetic（推論でない） | `syn-` でタグに `reasoning` なし | biz | 288 |
| synthetic（推論） | `syn-` でタグに `reasoning` あり（count/position/arrow/size/odd-one-out/order） | rsn | 94 |
| reasoning | `rsn-` | rsn | 225 |
| 文章のみ | `txt-` | txt | 87 |

**`source`**: wikipedia → `commons-article`、expansion → `commons-category`、synthetic・reasoning → `rendered`、文章のみ → `none`（画像なし）。

**`answer`**: `choice:n`（n = 正解 + 誤答の数）、`yesno`、`score:n`（n = 段階の数）。legacy: choice:4 = 1416、choice:3 = 78、choice:2 = 1、score:5 = 49、yesno = 418。
**`difficulty`**: legacy の値（easy/medium/hard。作る側の付け方）をそのまま。モデルの正答率に基づく基準は v1 で併記する。 **`lang`**: legacy は全問 `both`（en・ja）。

**`image_type`**（上から最初に当てはまった規則。タグが 1 つでも含まれれば当てはまる）

| 対象 | タグ | image_type |
|---|---|---|
| 写真 | map, diagram | diagram-map |
| | sign, safety | sign |
| | book, poster, script, record, code, language | document |
| | animal / plant / vehicle / food / structure | photo-animal / photo-plant / photo-vehicle / photo-food / photo-structure |
| | art | art |
| | sport, action | photo-person |
| | space, scene, geo, life, sci | photo-scene |
| | image-type | mixed（「どの種類の画像か」を問う問） |
| | object | photo-object |
| | ocr | text-in-image |
| | （上のどれでもない: detail, attribute, colour, presence, count など） | **photo-other（既定。172 問）** |
| 描画 | chart, bar, pie, line, trend, gauge | chart |
| | dashboard, ui, button, toggle, error, form | ui |
| | document, table, receipt, timetable, lookup, calendar, stamp, checklist | document |
| | map, exit, grid, path | diagram-map |
| | sign, safety, ppe, triage | sign |
| | （上のどれでもない） | **figure（既定。236 問）**: 図形・矢印・ダイヤル・歯車・回転など問のために描いた図 |
| 文章のみ | | none |

**`skill`**（上から最初に当てはまった規則）

| タグ | skill |
|---|---|
| r-negation | negation（否定） |
| r-consistency | contradiction（矛盾の検出） |
| r-uncertainty | uncertainty（不確かさの扱い） |
| r-rules, r-physics, r-time, threshold, validation, triage, ppe | rules（規則・条件・因果） |
| r-compare | compare |
| r-count, count | count |
| r-space, position, arrow, exit | spatial（位置関係） |
| r-quantity, r-instrument, r-two-images, gauge, level | quantity（計算・数量） |
| max, size, order, odd-one-out, compare, trend | compare |
| ocr, language, script, code, read, receipt, calendar | ocr（文字の読み取り） |
| 上のどれでもない | **recognition（認識。既定。1068 問）** |
| 文章のみ | text-comprehension |

結果（legacy 全問）: skill = recognition 1068 / ocr 296 / compare 123 / rules 100 / count 96 / text-comprehension 87 / spatial 76 / quantity 71 / negation 20 / contradiction 17 / uncertainty 8。
source = commons-article 797 / commons-category 471 / rendered 607 / none 87。
legacy の旧タグ（`ocr`、`count`、`animal`、`ui`、`synthetic`、`sci`、`life`、`record` など）は `tags_legacy` に残してある。`sci`・`life`・`record` は拡充でカテゴリを選んだ経緯のタグなので、分類軸には使っていない（photo-scene などに寄せた）。

## 5. 選択肢の並べ替え（`options.py`）

| モード | 版 | 内容 |
|---|---|---|
| `legacy` | legacy だけ | 旧 `load_cases` と完全に同じ。問題 ID の sha1（先頭 12 桁の 16 進数）を種にした固定のシャッフル。`order.index(0)` が正解の位置。**legacy の ID を使う**（v1 の ID で種を作ると全部変わる）。1495 問の選択問題すべてが旧ローダーと一致（正解データ `legacy_option_order.csv` と、旧ツリーがあるときは旧 `load_cases` との直接比較で確認） |
| `balanced` | v1 だけ | 問題群 × 選択肢数ごとに、正解の位置が均等（各位置の数の差が 1 以下）になる割り当て（ID の sha1 で並べて順番に配る。入力順に依存しない）。誤答の順は種つきシャッフル。**legacy で呼ぶと `ValueError`** |

- 特殊な選択肢（「該当なし」「どれでもない」「判断できない」など。`is_special`）は、`balanced` では**シャッフルの対象外**で、元の相対順のまま末尾に置く。正解が特殊な選択肢の問は、位置が末尾に決まり、均等割り当ての対象外。
- 逆順（`REV`）: `reverse_options` と `reversed_expected(expected, n)` = `n-1-expected`。通常は使わず（`REV=0`）、位置の偏りを見るときだけ。特殊な選択肢も含めて反転する。
- legacy の位置の偏り（legacy）: biz の 3 択は 16/12/11、4 択は 36/36/39/35。rsn の 3 択は 15/10/11、4 択は 48/52/37/38。

## 6. テスト

`python -m unittest discover -s datasets/tests`（リポジトリのルートで。ネットワーク不要）。`uv run --no-project python -m unittest discover -s datasets/tests` でもよい。各テストの docstring に「何を守るか」を書いてある。

| ファイル | 内容 |
|---|---|
| `test_options.py` | legacy が旧ローダーと一致、決定性、balanced が legacy で拒否される、位置の均等、選択肢 2〜12 個の正解の対応、特殊な選択肢の規則、逆順 |
| `test_loader.py` | 正解の対応（英・日）、単一言語の問、文章のみの問の state、`(version, id)` のキー、1 問 1 枚（legacy の 2 枚 13 問は既知。v1 は 0 枚〜1 枚）、日本語の目視用一覧 |
| `test_manifests.py` | 凍結ファイルの sha256、本文・画像・`.env` が無いこと、legacy の全 ID が対応表にちょうど 1 回、新 4 群の問数、分類表と規則の一致 |
| `test_review_seed.py` / `test_review_export.py` / `test_review_apply.py` | v1 の初期化・レビュー用バッチの出力・レビューの反映（検証、冪等、状態の遷移） |
| `test_v1_dropped_dedupe_rewrite.py` | dropped の除外（行の状態・対応表・位置の割り当て・legacy は対象外）、重複検出（画像の sha256 と設問と正解、冪等）、12 問の 1 枚版（絵の画素から読み戻した内容と、スクリプトが導いた正解の一致） |
| `test_new_questions.py` | 新問の受け皿: ID 範囲の表、検証（各種の誤りを具体的に拒否）、ローダー（既存の位置が動かない）、選択肢 2〜16・段階 3/7/10、ランナーの限界チェックとダミー ask、ロード→検証→balanced→レビューバッチ→反映→summary の一巡。NOTES のサンプル行がテスト済みのものと一致すること |
| `test_helpers.py` | ライセンスの正規表現（`datasets/fetch/` に `OK_LICENSE` があるとき。無ければ skip）、記事冒頭の整形、ゲート（旧ログがあるとき） |

旧ツリー（`wiki_qa/`、`eval_common/`）が見つからないテストは skip する。場所は環境変数 `WIKIQA_LEGACY_ORIGIN`、`WIKIQA_LEGACY_LOGS` で指定できる。

## 7. ゲート（統合だけで数値が変わらないこと）

`tools/regroup_check.py` が、旧ログ（`results_w`、`results_s`、`results_t`）を `wiki_report.py` と同じ規則（main → fill → exp の順に上書き、timed は欠けている ID だけ補う、QEV は 2 枚画像の 13 問を除外）で読み、モデル × 言語ごとの正答数 / 回答数を、旧 4 群と新 4 群（legacy ID → 対応表 → v1 の群）の両方で集計して比べる。さらに、既存 HTML に埋め込まれた各問の `ok` と旧 4 群の集計が一致することも確かめる。結果は `manifests/regroup_check.md`。文章のみの 87 問はこのログに結果がなく、「結果なし」として扱う（0 ではない）。

## 8. 既知の制約

- 分類（`image_type`・`skill`）は legacy のタグからの粗い写像で、`photo-other`（172）と `figure`（236）は既定値。v1 で問を磨くときに、目視で付け直す。
- 難度は作る側の付け方のまま。
- `build_questions.py` は、`work/candidates.json` などの作業ファイル（リポジトリに無い）と、根拠文を戻した `items_text_*.py` が揃わないと legacy を再現できない。legacy の正本は凍結ファイル。
- `fetch/`（取得・検査）と画像の置き場所は別の担当。ローダーの `images_root`（既定 `work/`）は仮の置き場所。

## 9. v1 のレビュー結果と、その後の処理（2026-10-11）

**レビュー**: Opus が legacy の 1962 問を全問（33 バッチ）見て、1 問 1 行の判定を書いた（`work/review/out/*.jsonl`。原本は変更しない。手順は `REVIEW_GUIDE.md`）。`apply_review.py --apply` で反映済み。

| 判定 | 問数 | 意味 |
|---|---|---|
| ok | 854 | 変更なし（`review.state = reviewed`、status = kept） |
| fix | 978 | 直した（`changed`、status = rewritten） |
| drop | 118 | 外した（`dropped`） |
| rewrite_1image | 12 | 2 枚画像の問。1 枚に作り直す（下記） |

その後の処理を含めた現在の状態（対応表の status）: **kept 854 / rewritten 987 / dropped 121 / pending 0**（rewritten = fix 975 + 作り直し 12、dropped = drop 118 + 重複 3）。評価対象（dropped を除く）は **1841 問**: photo 1265 / biz 197 / rsn 292 / txt 87。

- **2 枚画像の扱い**: 1 問 1 枚の規則（方針書）。legacy の 2 枚画像 13 問のうち、1 問（rsn-0105）はレビューが重複として drop、残り 12 問は **1 枚の画像に作り直した**。`synthetic/gen_v1_rewrite.py`（乱数の種を固定・決定的）が、前後の物体の比較 4 問（rsn-0102/0103/0104/0106: 上段 BEFORE・下段 AFTER の 1 枚）と、棒グラフの合計比較 8 問（rsn-0188〜0195: 左右 LEFT/RIGHT を共通の目盛りで 1 枚に）を描く。**正解は描画の仕様（集合の差・合計）から機械的に導き**、テストが画像の画素（図形の色と形、棒の高さ）を読み戻して一致を確かめる。legacy では 8 問中 6 問が「1 枚目」だった正解の偏りも、左 4 / 右 4 にした。画像は `work/generated/<ID>.png`（原寸 640x480）と `work/generated/px224/<ID>.png`（224px）で gitignore、行の `local_images` は `generated/<ID>.png`（`images_root` からの相対）。履歴に `rewrite_1image: rebuilt as one picture` を記録。legacy の凍結ファイルには 2 枚画像のまま残る（legacy は変更しない）。
- **重複の扱い**: 同じ 224px 画像（sha256 一致）で、設問（英語）・正解・種類が同じ問を重複とし、**後ろの ID を dropped、前の ID は残す**（`dedupe_v1.py`、`review.history` に `drop` / `duplicate of <ID> (cross-batch)`）。誤答の組だけ違うものも同じ扱い（`wrong-set-differs`）。同じ画像でも設問か正解が違う問（個数・色・有無など）は重複にしない。結果は **3 問**（biz-0232、0233、0237。曜日の円の問）。一覧は `manifests/dedupe_v1.md`。
- **privacy-check の方針**: 人物が写っているだけでは drop しない。設問が人物の同定を求めない限り、人物の写真は **残し、`privacy-check` の注記を issues に付ける**（現在 84 問、すべて photo）。同定を求める問だけ drop / fix。**決定: 84 問は残す（2026-10-11）**。要望があれば個別に除外できる（`tools/drop_ids.py`。手順は `manifests/privacy_check_v1.md`）。画像はすべて CC0・パブリックドメインの Commons 写真。
- **画像の種類（`image_type`）の追加**: レビュアーが `needs_new_image_type` を付けた問の集計は astronomical 33（+ astronomy 4）、satellite 23（+ aerial 1）、medical-scan 2、micrograph 1、scientific-illustration 1、technical-drawing 1。**astronomical（37 問）と satellite（24 問）を追加する**ことを提案し、値は `taxonomy.V1_EXTRA_IMAGE_TYPES` と `apply_review.py` の許可値に入れた。既存の値は壊していない。**該当問の付け替えは実施した**（§11.3。astronomical 38 / satellite 25。`tools/relabel_image_type.py`、履歴に記録）。少数の 4 種（計 5 問）は追加しない。
- **不足の分析**: `manifests/gap_analysis_v1.md`（選択肢の数・段階評価の段階数・否定・「該当なし」・日本語固有・文章のみの対照・はい/いいえの偏りなど、足すべき問数の提案つき）。新問はその後に作成した（§10、§11）。最終状態の分析は `gap_analysis_v1.md`、追加前の分析は `gap_analysis_v1_before.md`。

## 10. 新問を足す（v1 に追加する問の作り方）

v1 の 1841 問に足りない分（`manifests/gap_analysis_v1.md`）を、後から **別々の担当が並行して**書き足す。衝突しないよう、新問は担当（tag）ごとに別ファイル・別の ID 範囲に置く。**既存の v1 行（`photo/biz/rsn/txt.jsonl`）と `idmap_legacy_v1.csv`・`questions_v1.csv` は変更しない。** 実データの `new_*.jsonl` は作成済み（§11）。画像・Wikipedia 本文は commit しない（`work/` は gitignore）。

### 10.1 置き場と ID の予約範囲

- 置き場: `datasets/questions/v1/new_<tag>.jsonl`（UTF-8・LF・1 行 1 問）。**自分の tag のファイルだけ書く。** 他の tag のファイルや共有ファイルは触らない。
- ID: `<群>-NNNN`（群 = photo / biz / rsn / txt、4 桁）。**0001〜0999 は legacy 由来の帯**で、新問は **1001 以降**。tag ごとに下の範囲を予約する（`datasets/newq.py` の `RANGES` が正本。表は `python -m datasets.newq` で再生成できる）。範囲の外、他の tag の範囲、既存 ID との重複は検証がエラーにする。新しい tag が要るときは、先に `newq.RANGES` に 1 行足す（予備の範囲を使う）。

| tag（ファイル） | 予約範囲 | 用途 |
|---|---|---|
| `photo_variants`（`new_photo_variants.jsonl`） | `photo-2001`〜`photo-2399` | photo-derived variants: 2/3/5-16 choices, negation, none-of-the-above, position, count, score on photos |
| `rendered`（`new_rendered.jsonl`） | `biz-1001`〜`biz-1399` / `rsn-1001`〜`rsn-1199` | newly drawn pictures (biz / rsn): many-option, 3/7/10-level scores, negation, none-of-the-above, contradiction, uncertainty |
| `ja_specific`（`new_ja_specific.jsonl`） | `biz-2001`〜`biz-2199` / `photo-3001`〜`photo-3099` | Japanese-specific questions (lang=ja): rendered Japanese signs / timetables / receipts, real Japanese signs (photo) |
| `txt_controls`（`new_txt_controls.jsonl`） | `txt-1001`〜`txt-1199` | text-only controls: the same question as an image question with the picture removed (derived_from = that question) |
| `txt_forms`（`new_txt_forms.jsonl`） | `txt-2001`〜`txt-2199` | new passage-based text-only questions in the missing forms (2/3/5 choices, score); article revision references only |
| （予備） | `photo-4001`〜`photo-4999` / `biz-3001`〜`biz-3999` / `rsn-2001`〜`rsn-2999` / `txt-3001`〜`txt-3999` | 新しい tag を `newq.RANGES` に登録するときの置き場。登録前は使わない |

番号は範囲の先頭から詰めて使う（途中が欠けてもよい）。`derived_from` で派生元（v1 の ID）を指せる。

### 10.2 new 行のスキーマ

既存の v1 行と同じ項目で、legacy 由来の項目（`legacy_id`、`sha1`、`used_by`、`articles`）は不要。

| 項目 | 値 |
|---|---|
| `id` | `<群>-NNNN`（接頭辞 = `group`、tag の予約範囲内） |
| `legacy_id` | **`null`**（必ず） |
| `origin` | **`"new"`**（必ず） |
| `derived_from` | 派生元の v1 ID（既存または他の new 行）、無ければ `null`。文章のみの対照は元の画像問を指す |
| `relation` | 任意。`variant` / `mirror` / `control` / `rewrite` / `extension` |
| `group` / `source` / `image_type` / `skill` / `difficulty` | 既存と同じ値（`taxonomy.py` の `V1_*`）。`source` は `commons-article` / `commons-category` / `commons-new`（新しく選んだ Commons の CC0・PD 画像） / `rendered` / `none`（txt）。派生は親の `source` のまま。**値を勝手に増やさない**（足りない分類値は調整役が `taxonomy.py` に足す） |
| `lang` / `langs` | `both` + `["en","ja"]`（既定）、`ja` + `["ja"]`（日本語固有）、`en` + `["en"]`（英語のみ）。無い言語の側（`en`/`ja`）は行に書かない |
| `modality` / `kind` | `image` / `text`。`choice` / `noul`（はい・いいえ） / `score` |
| `answer_format` | `choice:N` / `yesno` / `score:N`（選択肢・段階の数と一致させる。検証が照合） |
| `en` / `ja` | choice: `instr`・`correct`・`wrong`（誤答の配列。en と ja の個数は同じ）。noul: `instr` だけ。score: `instr`・`levels`。任意で `state`（画像問は短い補足、対照は必須） |
| `answer` | noul: `true`/`false`。score: 正解の段階の位置（0 始まり）。choice には書かない |
| `local_images` | 画像問は**ちょうど 1 枚**: `["generated/<自分の id>.png"]`（新規）または、派生で同じ画像を使うなら**親と全く同じパス**。txt は `[]` |
| `images` | `source` が `commons-*` のとき `["File:..."]`（画像と同数） |
| `credit` | `commons-new` のとき `{"license": "CC0"か"Public domain", "author": ..., "url": "https://commons.wikimedia.org/..."}` |
| `article` | 記事由来の txt 問だけ: `{"en": {"title", "revid"}, "ja": {...}}`（本文は持たない。§10.4） |
| `tags` | 文字列の配列（空でもよい。必須の項目） |
| `review` | 初期値 `{"state": "unreviewed", "history": []}` |

サンプル（5 行。`datasets/tests/_newq_samples.py` から生成し、テストが検証済み。コピーして書き換える）: 1) 6 択（写真の派生・親と同じ画像・末尾に「該当なし」）、2) はい/いいえ（描画）、3) 7 段階の段階評価（描画）、4) 日本語固有（`lang="ja"`・ja 側だけ・5 択）、5) 文章のみの対照（元の画像問から画像を外した変種）。

<!-- samples:begin -->
```jsonl
{"id": "photo-2001", "legacy_id": null, "origin": "new", "derived_from": "photo-0001", "relation": "variant", "group": "photo", "source": "commons-article", "image_type": "photo-animal", "skill": "recognition", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "choice", "answer_format": "choice:6", "tags": ["classify", "animal", "many-options"], "images": ["File:Sheep lounging in the shade of a tree at Röe Castle.jpg"], "local_images": ["data/images/b68ae37691c83e58bfc75db7e37b3546c9cfc400.jpg"], "en": {"instr": "Which animal is mainly shown?", "correct": "sheep", "wrong": ["goat", "pig", "rabbit", "cow", "None of the above"]}, "ja": {"instr": "主に写っている動物はどれですか？", "correct": "羊", "wrong": ["ヤギ", "豚", "ウサギ", "牛", "該当なし"]}, "review": {"state": "unreviewed", "history": []}}
{"id": "biz-1001", "legacy_id": null, "origin": "new", "derived_from": null, "group": "biz", "source": "rendered", "image_type": "chart", "skill": "negation", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "noul", "answer_format": "yesno", "tags": ["synthetic", "chart", "negation"], "local_images": ["generated/biz-1001.png"], "en": {"instr": "No bar is taller than the first bar"}, "ja": {"instr": "最初の棒より高い棒はない"}, "answer": true, "review": {"state": "unreviewed", "history": []}}
{"id": "rsn-1001", "legacy_id": null, "origin": "new", "derived_from": null, "group": "rsn", "source": "rendered", "image_type": "ui", "skill": "quantity", "difficulty": "medium", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "score", "answer_format": "score:7", "tags": ["synthetic", "gauge", "level"], "local_images": ["generated/rsn-1001.png"], "en": {"instr": "How full is the gauge?", "levels": ["0-14%", "15-28%", "29-42%", "43-57%", "58-71%", "72-85%", "86-100%"]}, "ja": {"instr": "ゲージはどれくらい満たされていますか？", "levels": ["0〜14%", "15〜28%", "29〜42%", "43〜57%", "58〜71%", "72〜85%", "86〜100%"]}, "answer": 3, "review": {"state": "unreviewed", "history": []}}
{"id": "biz-2001", "legacy_id": null, "origin": "new", "derived_from": null, "group": "biz", "source": "rendered", "image_type": "sign", "skill": "ocr", "difficulty": "medium", "lang": "ja", "langs": ["ja"], "modality": "image", "kind": "choice", "answer_format": "choice:5", "tags": ["synthetic", "japanese", "sign"], "local_images": ["generated/biz-2001.png"], "ja": {"instr": "この標識が示している意味はどれですか？", "correct": "一時停止", "wrong": ["徐行", "進入禁止", "駐車禁止", "該当なし"]}, "review": {"state": "unreviewed", "history": []}}
{"id": "txt-1001", "legacy_id": null, "origin": "new", "derived_from": "biz-0015", "relation": "control", "group": "txt", "source": "none", "image_type": "none", "skill": "text-comprehension", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "text", "kind": "noul", "answer_format": "yesno", "tags": ["control", "no-picture"], "local_images": [], "en": {"instr": "The values rise from left to right", "state": "No picture is attached to this question."}, "ja": {"instr": "値は左から右に向かって増えている", "state": "この問題には画像が添付されていません。"}, "answer": true, "review": {"state": "unreviewed", "history": []}}
```
<!-- samples:end -->

### 10.3 画像

- 画像は `work/generated/<自分の id>.png`（原寸）に置く。224px 版は `work/generated/px224/<id>.png`（なければレビュー・実行時に作る）。**gitignore で commit されない。**
- 1 問 1 枚。ファイル名は v1 全体で一意（反転・加工した画像も、親と別の新しいファイル `<自分の id>.png` にする）。
- 親の画像をそのまま使う変種（選択肢だけ変える等）は、親の `local_images` と**同じパス**を書く（親が既存の写真なら `data/images/...`）。新しい画像ファイルは作らない。
- 画像の探し場所は、検証が `--images-root`（既定: `$WIKIQA_IMAGES`、`work/`、`$WIKIQA_DATA_ROOT`、旧ツリー `wiki_qa/`）。新規画像が無いとエラー。親の画像がこの機械に無いときは警告だけ。
- 新しく選んだ Commons 画像（`commons-new`）は CC0・パブリックドメインだけ。出典（`images` の File 名と `credit`）を行に残す。人物の同定を求める問は作らない。

### 10.4 Wikipedia の本文を載せない

- 記事由来の txt 問は `article`（タイトルと revision ID）だけ持ち、本文・根拠文は書かない（`evidence`、`passage`、`text`、`body` のキーは検証が拒否する）。実行時に手元の `passages.json` から読む（無い機械では動かない）。`state` は書かない。新しい記事を使うときは、その revision の本文を手元の `passages.json` に足す（commit しない）。
- 文章のみの対照（対照用の txt 問）は `article` を持たず、**自分で書いた `state`（各言語 600 字以内）** を持つ。画像が付いていないことを書き、問に必要な情報は state に自分の言葉で入れる。`derived_from` = 元の画像問（必須）。`skill` は `text-comprehension`、`image_type`/`source` は `none`。
- どの文字列も 600 字を超えない（コピーした本文の混入を防ぐ）。

### 10.5 選択肢・段階・はい/いいえ

- 選択肢は **2〜16 個**（QEV の上限が 16）。段階評価は **2〜10 段階**（OneJev / Strands の上限が 10。3・5・7・10 を使う）。段階は順序のある値で、並べ替えない。各段階に数値の範囲や基準を書く。
- 選択肢は実行時に `balanced` で並べ替える（§5）。**順序に依存する選択肢は書かない**（「上記のすべて」「前の選択肢」「両方」など。検証が警告）。選択肢の重複（大文字小文字・空白を無視）、正解と同じ誤答は不可。
- 「該当なし」類は正準の表記で書く（末尾に固定され、シャッフルされない。en と ja で**同じ位置**に置く）。en: `None of the above` / `Cannot be determined` / `Not enough information`。ja: `該当なし` / `どれも当てはまらない` / `上記のいずれでもない` / `判断できない`。他の言い回しだと特殊な選択肢として扱われず、途中にシャッフルされる（ja で「上記」「該当」「いずれ」を含む選択肢が特殊と認識されないと警告）。
- 正解の位置は、群 × 選択肢数で均等になるよう**実行時に割り当てる**（行には持たない）。new 行は、既存の行の位置を**動かさず**、その上に均等に足される（`options.assign_positions_with_base`）。new 行どうしの位置は、new の集合が固まった時点で確定する（行を足すと new の位置は変わりうる）。正解が「該当なし」の問は末尾に固定され、均等割り当ての対象外。
- 段階評価の正解の段階は 0〜n-1 に均等に配る（`options.suggest_score_answers(ids, n)` が決定的な配分を出す。ファイルごとに検証が偏りを警告）。はい/いいえは「はい」「いいえ」をおよそ半々にする（20 問以上で偏りを警告）。
- 日本語固有（`lang="ja"`）は ja 側だけ書く。ja の問に日本語の文字が無いとエラー。画像内の文字を読む問は、選択肢も画像に印刷された原語のまま。`ja_specific` の tag は `lang="ja"` 必須。

### 10.6 検証と manifest

```
python datasets/tools/validate_new.py [--tag TAG] [--images-root DIR] [--no-image-check] [--write-manifests --tag TAG]
```

自分のファイルを渡す前に必ず通す（エラーは `ファイル:行 ID: 内容` で出る。終了コード 0 = エラーなし）。見るもの: スキーマ、ID が予約範囲内・全 v1 で一意、**重複問（下記）**、正解が選択肢内・重複なし、en/ja の個数一致、選択肢 ≤ 16・段階 ≤ 10、画像（1 問 1 枚・存在・開ける・名前の一意）、本文を含まない、日本語の文字、はい/いいえ・段階の形式。`--write-manifests` は **`--tag` が必須**（無いと何も書かず終了コード 2。他の担当の manifest を書かないため）で、その tag にエラーが無いとき `manifests/idmap_v1_new_<tag>.csv`（`legacy_id` 空欄・`group_legacy="new"`・`status` は `new`、drop されたら `dropped`）と `manifests/questions_v1_new_<tag>.csv`（分類表。`origin`・`derived_from` つき）を**その行から作り直す**（中身が変わらなければファイルは書き換えない）。tag ごとの別ファイルなので担当どうしで衝突しない。`idmap_legacy_v1.csv` の「legacy の 1962 ID が 1 回ずつ」は変わらない（`loader.legacy_to_v1()` に new は入らない。`loader.idmap_v1_new()`、`loader.classification("v1")` は new も含む）。

**重複問（new 行）**: 同じ画像（自前の画像は内容の sha256、共有する画像はパス）・同じ設問文（en/ja）・同じ正解・同じ `answer_format` の問は重複で、**後ろの ID がエラー**（誤答の組だけ違っても重複。§9 の `wrong-set-differs` と同じ規則）。変種が別の問になるのは、**選択肢の数か種類（`answer_format`）、設問文（否定など）、画像（反転・加工したら新ファイル）、正解**のどれかが変わるとき。したがって `photo-0001`（4 択）の「同じ 4 択で誤答だけ替えた」問は重複、「6 択にした」「はい/いいえにした」問は変種。既存の v1 の重複排除（`tools/dedupe_v1.py`）は base だけが対象のままで、new 行の重複は `validate_new.py` が見る。

### 10.7 review の流れ

1. 作成担当が検証を通す（`--write-manifests --tag <自分の tag>` も）。
2. `python datasets/tools/export_review_batches.py --new <自分の tag>` が `work/review/new_<tag>_<NN>.json`（約 60 問ずつ、ID 順）と `work/review/index_new_<tag>.json` を書く。**tag は必須**（他の担当のバッチを作り直さない）。選択肢は実行時に見える順（balanced）で、`option_labels`（A, B, ...）つき。旧モデルの結果・旧ログ・passages は要らない。バッチ番号は ID 順なので、tag のファイルが固まってから出す（途中で行を足すとバッチが番号替えされ、書きかけの判定が「バッチの外」で拒否される）。
3. レビュアーが `datasets/REVIEW_GUIDE.md`（「新問のチェック項目」）に従い、`work/review/out/new_<tag>_<NN>.jsonl` に 1 問 1 行で書く。
4. `python datasets/tools/apply_review.py --tag <自分の tag>`（dry run）→ `--apply`。**`--tag` を付けると `out/new_<tag>_*.jsonl` だけを読む**（`work/review/out/` には legacy 由来の 33 バッチの判定と、他の担当の判定も入っている。`--tag` 無しは全部を読むので、new の担当は必ず付ける）。書くのは判定を受けた行のファイルだけ（`new_<tag>.jsonl` とその tag の manifest）で、中身が変わらないファイルは書き換えない。legacy 由来の判定を `--tag` 無しで再反映しても、既存の v1 と manifest はバイト単位で変わらないことをテストで確認している（`SharedWorkflowTests`）。drop された new 行は行がファイルに残り、ローダー・ランナーが除外する。

### 10.8 ランナー・ローダー・集計

- `datasets.loader.load_v1_cases(groups, include_new=True, only_new=False)` と `runner.cases.load_cases(set, version="v1")`: dropped 除外・balanced の順・new 行を含む。セット名は `photo` / `biz` / `rsn` / `txt` / `all` / `new`（new だけ）。`python -m runner.run --dataset-version v1 --set all ...`。`runner.batch` は `v1…` のセットを自動で `--dataset-version v1` にし、校正メモも `results/runs/v1` に付ける。ログのブロック名は legacy と衝突しない（`v1…`）。224px のキャッシュも v1 は別（`work/px224_v1`。v1 の `rsn-0102.png` は legacy の同名ファイルと別の絵なので混ぜない）。結果の保存キーは `(dataset_version="v1", id)`。
- `runner.cases.dry_run(cases)`（ダミーの ask で全問を一巡し、返り値の型・範囲、expected、画像の枚数、選択肢の重複を検査）と `runner.cases.check_all_limits(cases)`（全アダプタの `LIMITS` の選択肢数・段階数・画像枚数の上限と照合）。v1 全体（new を含む）でテストが通ること。
- ローダーの正解位置は、**v1 全体（base + 全 new、dropped 除く）で計算してから**ファイル・群で絞る。一部だけ読んでも位置は変わらない。
- `tools/build_dataset_summary.py` は new 行も一覧・統計に入れる（legacy→v1 の表には「新規」の列。legacy の旧並びの位置は new に無いので除く）。単一言語の行は片側だけ表示する。

### 10.9 この受け皿で変えた既存の挙動（すべて）

追加のファイルだけでなく、次の既存の挙動を変えた。**既存の v1 行・`idmap_legacy_v1.csv`・`questions_v1.csv`・legacy のデータは 1 バイトも変えていない**（作業の前後で sha256 を照合した）。

1. **正解が「該当なし」類の問を、均等割り当ての対象から外した**（`options.v1_orders`。`loader`・レビュー出力・summary・`gap_analysis_v1.py` が共通で使う）。以前は、正解が末尾に固定される問（rsn-0151〜0154 など 4 問）も位置の枠を消費していて、`assign_positions` の docstring（対象外）と食い違っていた。影響したのは rsn の 2 つのバケットだけで、`gap_analysis_v1.md` 付録 §6 の balanced 位置を更新した: rsn 3 択（30 問）10/12/8 → **9/10/11**、rsn 4 択（158 問）39/38/40/41 → **40/39/38/41**（末尾固定の問を含む全体の分布。末尾固定でない問だけの分布は差 1 以下）。`results/runs/` に v1 の結果は無い（v1 はまだ測定していない）ので、結果への影響はない。
2. 日本語・英語の「該当なし」類の判定を広げた（`上記のいずれでもない`・`上記以外`・`この中にはない`・`いずれでもない`・`いずれも当てはまらない`・`None of the listed/options/choices`）。**既存の v1 の全選択問で、特殊な選択肢と判定される位置が変わらないことを確認した**（11 問が特殊な選択肢を持つ。前後で同一）。
3. ローダー: v1 の読み込みは new_*.jsonl も読み、位置は v1 全体（base + new、dropped 除く）で計算してから絞る。`load_rows` / `load_cases` / `load_v1_cases` の引数に `groups` / `include_new` / `only_new` / `strict_passages`（既定は従来どおり）を足した。`article` の無い text 行は自前の `state` を使う。`dropped_ids` は new の manifest も見る。`classification("v1")` は new の分類表も含む。
4. `runner/cases.py`: `load_cases(set, version="v1")` と `check_limits` / `check_all_limits` / `dry_run` を足した。`runner/run.py`: `select_cases` が `args.dataset_version` を渡す。v1 の 224px キャッシュは `work/px224_v1`（legacy は `work/px224` のまま）。`runner/config.toml` の `[blocks]` に `photo` / `biz` / `rsn` / `txt` / `all` / `new` の 6 行（ブロック名は legacy と別）。`runner/batch.py`: `v1…` のセットに `--dataset-version v1` を渡し、校正メモを v1 の結果に付ける。
5. `apply_review.py`: new 行に対応し、`--tag`・`--v1dir`・`--manifests` を足した。書くのは判定を受けた行のファイルだけで、中身が同じファイルは書き換えない（`v1_io.write_jsonl` / `write_csv` が同じ内容なら書かない）。許可する `image_type` / `skill` の一覧は `taxonomy.V1_*` に移した（値は同じ）。`export_review_batches.py`: `--new <tag>` を足し、text 行で `article` が無いものを扱えるようにした。`build_dataset_summary.py` / `gap_analysis_v1.py`: new 行を入れ、new には legacy の旧並びが無いので除く。JS の検索の索引が、片言語だけの行で落ちないようにした。
6. 予約範囲のうち、依頼の例にない追加: `ja_specific` の写真用 `photo-3001`〜`photo-3099`、tag `txt_forms`（`txt-2001`〜`txt-2199`。記事由来の文章のみの新形式）、予備の範囲（`photo-4001`〜`4999`、`biz-3001`〜`3999`、`rsn-2001`〜`2999`、`txt-3001`〜`3999`）。

## 11. v1 の最終状態とビルド（2026-10-11）

評価対象は **2768 問** = legacy を磨いたもの 1841 + 新問 927（dropped は 135 行で、行はファイルに残るが評価には入らない）。数字はすべて `dist/v1/manifest_v1.json`（`python -m datasets.build_v1`）から取った。

### 11.1 構成（群 × origin）

| 群 | legacy を磨いたもの | 新問 | 計 | 新問の中身（tag） |
|---|---|---|---|---|
| photo | 1265 | 211 | **1476** | photo_variants 105 + photo_variants_b 106（写真の派生: 2・3・5〜16 択、否定、該当なし、位置、数える、段階評価） |
| biz | 197 | 449 | **646** | rendered 描画（biz 分）、rendered_b、tk_ui 249（本物の Tkinter 画面のスクリーンショット）、ja_specific 101（日本語の標識・時刻表・レシート等。lang=ja） |
| rsn | 292 | 168 | **460** | rendered / rendered_b の推論問（多択、3/7/10 段階、否定、矛盾、不確かさ） |
| txt | 87 | 99 | **186** | txt_controls 99（画像問から画像を外した文章のみの対照） |
| **計** | **1841** | **927** | **2768** | |

- 形式別: 選択 2091 / はい・いいえ 537 / 段階評価 140（3 段階 35・5 段階 45・7 段階 35・10 段階 25）。
- 選択肢数別: 2 択 72 / 3 択 125 / 4 択 1495 / 5 択 145 / 6 択 78 / 7 択 62 / 8 択 58 / 9 択 24 / 10 択 11 / 11 択 6 / 12 択 8 / 13 択 4 / 16 択 3。
- 言語別: en・ja 両方 2596 問、日本語のみ 172 問（`lang=ja`。ja_specific）。評価ケースは en 2596 + ja 2768。
- 難度別（作る側 / レビュアーの付け方）: easy 961 / medium 1328 / hard 479。
- 画像: 2127 枚 = Commons 1021（CC0 / パブリックドメイン）+ legacy の描画画像の再利用 477 + v1 で新しく作った画像 629（描画・Tkinter・1 枚化 12 問）。
- 新問の review: reviewed 824 / changed 103 / dropped 14（新問 941 行のうち）。

### 11.2 作り方

1. 底: legacy の 1962 問を Opus が全問レビュー → 854 ok（そのまま）/ 978 fix / 118 drop / 12 rewrite_1image（§9）+ 重複 3 を drop。
2. 新問: 足りない形式（`manifests/gap_analysis_v1.md`）を tag ごとの担当が `new_<tag>.jsonl` に書き、Opus がレビュー（§10）。描画は `datasets/synthetic/gen_v1_*.py`（正解は描画の仕様から機械的に導く）。
3. `python -m datasets.build_v1` が評価対象だけを `dist/v1/` に書き出し、自己検査（`build_report.md`）を行う（§11.7）。
4. 派生物: `tools/gap_analysis_v1.py --write`（不足分析）、`tools/review_notes_v1.py`（privacy-check と needs_new_image_type の一覧）、`tools/build_dataset_summary.py`。

### 11.3 legacy → v1 の変更点（磨き上げの種類と件数）

| 区分 | 問数 | 内容 |
|---|---|---|
| そのまま（kept） | 854 | 変更なし |
| 直した（rewritten） | 975 | fix の内訳（複数にまたがる問がある）: 難度の付け直し 185、日本語の誤答 158（英語は 27）、日本語の設問 93、画像の種類 81、日本語の正解 26、段階の文言 21、skill 16、答え方 14、英語の正解 4、はい/いいえの正解 1 |
| 1 枚に作り直した | 12 | 2 枚画像の問（比較 4 + 棒グラフの合計比較 8）。`gen_v1_rewrite.py` |
| 外した（dropped） | 121 | レビューの drop 118 + 重複 3（biz-0232/0233/0237） |
| 画像の種類の付け替え | 63 | astronomical 38 / satellite 25（§9。`tools/relabel_image_type.py`。履歴に記録）。legacy 由来 61 + 新問 2 |

privacy-check が付いた問は 84（`manifests/privacy_check_v1.md`。決定: 残す、2026-10-11）。needs_new_image_type の集計は `manifests/needs_new_image_type_v1.md`。

### 11.4 文章のみの対照（txt_controls）の注意

対照 99 問は、画像問から画像を外した変種で、**問に必要な情報を `state` に自分の言葉で入れている**。画像にはない**正確な数値**（棒の高さ、金額、時刻など）が state に入るため、**文章版は画像版より易しくなり得る**（画像から読み取る難しさがなく、数値が与えられる）。画像版と比べるときは、この点を明記すること（「画像を読む力」ではなく「文章で与えた情報で答える力」との差になる）。state は各言語 600 字以下の自作文で、Wikipedia の本文は入らない。記事由来の文章のみ問（87 問）は `state` を持たず、実行時に手元の `passages.json` から読む（`dist` の `cases_v1.jsonl` では `state: null` と記事の参照）。

### 11.5 重複・near-duplicate の扱い

- 底: 同じ 224px 画像（sha256 一致）で設問・正解・種類が同じ問は後ろの ID を dropped（§9。3 問）。誤答の組だけ違うものも同じ扱い。
- 新問: `validate_new.py` が、同じ画像・同じ設問・同じ正解・同じ `answer_format` の問をエラーにする（後ろの ID）。親と同じ画像を使う変種は、選択肢の数・種類、設問（否定など）、正解のどれかが変わるときだけ別の問。
- **意図的な near-duplicate**: 写真の派生（photo_variants）は、同じ画像に別の形式（2 択・6 択・否定・該当なし等）を付けた問で、重複ではなく**同じ画像の別の問い**。集計で画像単位にまとめるときは `images_v1.json` の `question_ids`（画像ごとの問の一覧）を使う。同じ元から作った文章のみ対照は `derived_from` で元の画像問を指す。
- 新問どうし・新問と底の「意味が近い問」は自動検出していない（レビューで確認）。

### 11.6 既知の制約

- **画像の判読性**: 入力は長辺 224px。描画画像の小さい文字（表・レシート・時刻表）は 224px で読めないことがあり、難度に反映してあるが、モデルの誤りが「読めない」ためか「理解できない」ためかは区別していない。
- **フォント**: 日本語の描画は Noto Sans JP / Noto Serif JP（OFL。この機械の Windows フォルダのもの）。別のフォントでは文字の形・幅が変わる（答えは変わらない）。フォント自体は配布しない。
- **Tkinter の画像（tk_ui 249 問）**: 本物の Tk / ttk のウィンドウをスクリーンショットしたもので、OS・テーマ・DPI・フォントに依存する。**画素は他の機械で一致しない**（答えは設定から導くので変わらない）。再生成は同じ画像を保証しない。配布物は作成時の画像そのもの（zip の sha256 で固定）。
- **生成スクリプトを `--apply` すると jsonl が上書きされる**: `gen_v1_*.py` は、レビュー済みの `datasets/questions/v1/*.jsonl` を上書きし、レビューの履歴（`review.state` / `history`）を `unreviewed` に戻して失う。書き込みの条件はスクリプトごとに違う: `gen_v1_new.py` と `gen_v1_tk_ui.py` は**既定で書く**（`--dry` のときだけ書かない。tk_ui は `--rows-only` でも jsonl を書く）、`gen_v1_ja.py` と `gen_v1_rewrite.py` は `--apply`、`gen_v1_txt_controls.py` は `--write`、`gen_v1_new_b.py` は reviewed 行があると `--force` が無い限り拒否する。**最終版では実行しない**。再生成が必要なときは出力先を変えて差分を確かめる。`build_v1` と集計ツールは読み取りだけ。
- 正解位置の均等化は、新問を足しても既存の問の位置を動かさない設計だが、新問どうしの位置は集合が固まった時点の値（今回確定）。追加すると新問の位置が変わり得る。
- 段階評価の正解の段階は new_rendered_b の 3 段階で [3, 3, 1] と少し偏る（validate_new の警告 1 件）。
- 2 枚画像の legacy 13 問は legacy 凍結に残る（v1 は 1 問 1 枚）。

### 11.7 ライセンス方針

- Commons 写真: CC0 / パブリックドメインだけ（zip 作成時に検査。他のライセンスなら止まる）。作者・URL・ライセンスは `images_v1.json` と各 zip の `ATTRIBUTION.md`。
- 自作画像のライセンスは **CC0-1.0 で確定**（決定: 2026-10-11）。対象は生成画像 629 枚（Tkinter・描画・日本語固有・1 枚化）と、旧版の描画画像 477 枚。`images_v1.json` の該当項目は `license: "CC0-1.0"`・`license_status: "decided"`（`license_proposed` は廃止）。各 zip の `ATTRIBUTION.md` に CC0-1.0（Public Domain Dedication）、描画スクリプト（`datasets/synthetic`）、使ったフォントを書く。
- フォント（事実の記載。フォント自体は配布しない）: 日本語の描画は Noto Sans JP / Noto Serif JP（OFL 1.1）、英数字の描画は Arial（その機械にあれば。なければ DejaVu Sans）。Tkinter の画像は自作画面のスクリーンショットで OS の枠は含まず、画面内の文字は **Windows 同梱のフォント（英語 UI は Segoe UI、日本語 UI は Yu Gothic UI）** で描かれている（249 問: Segoe UI 203・Yu Gothic UI 46。ID の一覧は `manifests/windows_fonts_images_v1.md`、`tools/list_windows_font_images.py` が `gen_v1_tk_ui.py` の使用フォントから作る）。法的な判断はしない。
- 問題文・選択肢は自作（Wikipedia の本文は含めない。記事の revision の参照だけ）。

### 11.8 ビルドと検査（`python -m datasets.build_v1`）

`dist/v1/`（gitignore）に次を作る。決定的で冪等（日付は `--date`、zip は名前順・固定時刻）。画像は Commons 写真と legacy の描画画像を旧ツリー（`wiki_qa/`）または `--root` / `$WIKIQA_DATA_ROOT`、新しい画像を `work/generated/` から読む。224px 画像は `work/px224` 等を先に見つけたものを使うので、`work/px224_v1` など別の目的の 224px 画像が `work/` にあると取り違える（zip 作成が「stale」で止まる）。その場合は旧ツリーを先に指定する: `--root <jev-like>/wiki_qa`。

| ファイル | 内容 |
|---|---|
| `questions_v1.jsonl` | 評価対象の全問（問・正解・誤答・state（対照のみ自作）・分類・難度・review・origin・derived_from・legacy_id・画像の path） |
| `cases_v1.jsonl` | `datasets.loader` の評価用ケース（balanced の選択肢の並びと expected を確定。en / ja を 1 行に並べる。画像は論理パス、記事由来の txt は `state: null`） |
| `manifest_v1.json` | 版、日付、問数（群・形式・origin・言語・選択肢数・難度ほか）、各ファイルの sha256 |
| `idmap_legacy_v1_full.csv` / `questions_v1_all.csv` | legacy→v1（dropped と新問を含む）/ 評価対象の分類表 |
| `images_v1.json` | 使う画像の全一覧（Commons: 作者・ライセンス・URL・sha。生成: `source: "generated"`、スクリプト、seed、sha、ライセンス CC0-1.0、Tkinter の画像はフォントの注記） |
| `images-224px.zip` / `images-original.zip` | 画像（zip のメンバー名は論理パス `data/images/...`、`generated/...`。展開してそのまま `images_root` に使える）+ `ATTRIBUTION.md`。**アップロードはしない** |
| `build_report.md` | 自己検査（画像の存在・sha256、選択肢数の上限、1 問 1 枚、ID 一意、en/ja 一致、txt の state、dropped 不含、位置の偏り、runner の v1 セット、validate_new ほか） |

版名は `datasets/version.py` の `DATASET_VERSION` から取る（出力先 `dist/<版>/` もここから）。
