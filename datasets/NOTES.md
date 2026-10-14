# datasets/ ノート

ベンチの問題・分類・選択肢の並べ替え・新問の足し方・ビルド・テストの説明です。画像、Wikipedia の本文、ログ、`.env` はこのリポジトリに含めません（`work/` と `data/` は gitignore）。

## 1. 版と ID の規則

版は **v1** だけです（`datasets/version.py` の `DATASET_VERSION`）。問は `datasets/questions/v1/*.jsonl`（UTF-8・LF・1 行 1 問）にあります。

| 群 | ファイル | ID |
|---|---|---|
| photo | `photo.jsonl` | `photo-NNNN` |
| biz | `biz.jsonl` | `biz-NNNN` |
| rsn | `rsn.jsonl` | `rsn-NNNN` |
| txt | `txt.jsonl` | `txt-NNNN` |
| 新問 | `new_<tag>.jsonl`（§10） | 上と同じ接頭辞、番号は 1001 以降（tag ごとの予約範囲） |

- **キーは常に `(dataset_version, id)`。** ローダーの `case_key(version, id)` が作ります。結果・manifest・集計は ID だけで引かないこと。
- **評価対象は 2768 問**（§11）。レビューで外した問（`review.state == "dropped"`）は行がファイルに残り、ローダーが既定で除外します（`include_dropped=True` で含める。dropped は全部で 135 行）。
- **v1 の行の書式**:
  - `id`、`group`（photo / biz / rsn / txt）、`source`、`image_type`、`skill`、`difficulty`、`lang`（both / en / ja）、`langs`、`modality`（image / text）、`kind`（choice / noul / score）、`origin`（`base` = 最初の 1841 問 / `new` = 後から足した問）、`tags`。
  - **`answer_format`**: 答え方の軸（`choice:4` / `yesno` / `score:5`）。選択肢の数から決まる。**`answer` は正解の値**（はい/いいえなら true/false、段階評価なら段階の位置）。軸の名前が `answer` と衝突するため、行では `answer_format`、分類表（`questions_v1.csv`）の列名だけ `answer`。
  - 選択問題は `en` / `ja` に `instr`・`correct`・`wrong`（誤答の配列。en と ja の個数は同じ）。段階評価は `levels`。選択肢の並びは行に持たず、実行時に決める（§5）。
  - **`review`**: `{state, history: [{date, what, why}, ...]}`。`state` は `unreviewed` < `reviewed`（確認済み・変更なし）< `changed`（直した）< `dropped`（外した）。
  - `local_images`: 画像問はちょうど 1 枚（`images_root` からの相対の論理パス）。`images`: Commons の File 名。

## 2. 本文の扱い（Wikipedia の本文は載せない）

- 文章のみの問（記事由来）は `article`（記事のタイトルと revision ID）と `evidence_sha256`（根拠文の sha256）だけを持ち、**本文・根拠文は持たない**（CC BY-SA の本文なので）。`state`（問題に付ける本文）は、手元の `passages.json`（gitignore）から実行時に読む。無いときは `FileNotFoundError`。手元に本文がある人は sha256 の一致を確かめられる。
- 画像のファイルは含めない。行に残る `local_images` は論理パスだけ。
- テスト `test_manifests.py` が、`evidence` が無いこと、画像ファイルと `.env` が無いことを確かめる。

## 3. ファイルの目的

| ファイル | 目的 |
|---|---|
| `newq.py` | 新問の置き場・ID の予約範囲の表（§10）。ローダー・検証が共通で使う |
| `loader.py` | 問題を評価用のケースとして読む。`(version, id)` のキー、分類表の読み込み、dropped の除外（`load_cases("v1")`、`load_v1_cases(["photo", ...])`、`is_dropped(row)`） |
| `options.py` | 選択肢の並べ替え（balanced / 逆順）。§5 |
| `taxonomy.py` | 分類軸の許可値（`V1_*`。検証が使う） |
| `version.py` | 版名の定数 `DATASET_VERSION` |
| `build_v1.py` | 最終ビルド: `dist/v1/` に問題・ケース・画像一覧・zip・検査結果を作る（§11.5） |
| `questions/v1/` | v1 の問（上の表） |
| `manifests/questions_v1.csv`、`questions_v1_new_<tag>.csv` | 分類表（行から作る。ローダーの `classification()` が読む） |
| `manifests/images_v1.json` | Commons の画像と、以前に描いた画像の一覧（sha256・ライセンス・作者・URL。`question_ids` は画像ごとの問の一覧） |
| `manifests/privacy_check_v1.md` | 人物が写る問の一覧と方針 |
| `manifests/windows_fonts_images_v1.md` | Windows 同梱フォントで文字を描いた画像（Tkinter 249 問）の ID 一覧 |
| `manifests/domain_probe.*` | 取得先ドメインの確認結果 |
| `tools/v1_io.py` | v1 の行・分類表の読み書き（同じ内容ならファイルを書き換えない） |
| `tools/validate_new.py` | 新問（`new_<tag>.jsonl`）の検証と、tag ごとの分類表の書き出し（§10.6） |
| `tools/drop_ids.py` | 指定した ID の問を個別に除外する（`review.state = dropped`。既定は dry-run、`--apply` で書く） |
| `tools/list_windows_font_images.py` | Tkinter 画像の使用フォントの一覧を作る |
| `tools/probe_domains.py` | 取得先ドメインの疎通確認 |
| `synthetic/gen.py`、`gen_reasoning.py` | 描画画像と問の生成（乱数の種を固定・決定的）。出力は `work/regen/` |
| `synthetic/gen_v1_*.py` | v1 の描画画像と新問の生成（§11.4 の注意あり） |
| `fetch/` | Commons からの画像の取得と検査（`python -m datasets.fetch`） |
| `tests/` | ネットワーク不要のテスト（§6） |

## 4. 分類の定義

軸: `group`（問題群）、`source`、`image_type`、`skill`、`answer`、`difficulty`、`lang`。許可値は `taxonomy.py`。

- **`group`**: photo（Commons の写真）/ biz（業務・UI・書類など描いた画像）/ rsn（推論の図）/ txt（文章のみ）。
- **`source`**: `commons-article`・`commons-category`（Commons の写真）/ `commons-new`（新問のために選んだ CC0・PD の写真。行に `credit`）/ `rendered`（描画）/ `none`（画像なし）。
- **`image_type`**: photo-scene / document / figure / photo-other / chart / ui / mixed / photo-object / photo-animal / sign / diagram-map / photo-person / photo-vehicle / art / photo-food / photo-structure / photo-plant / text-in-image / astronomical / satellite、文章のみは none。`photo-other` と `figure` は粗い既定値。
- **`skill`**: recognition / ocr / compare / rules / count / spatial / quantity / negation / contradiction / uncertainty、文章のみは text-comprehension。
- **`answer`**: `choice:n`（n = 正解 + 誤答の数）、`yesno`、`score:n`。
- **`difficulty`**: easy / medium / hard（作る側・レビュアーの付け方。モデルの正答率に基づくものではない）。
- **`lang`**: both（en・ja）/ ja（日本語固有）/ en。

## 5. 選択肢の並べ替え（`options.py`）

- **`balanced`**: 問題群 × 選択肢数ごとに、正解の位置が均等（各位置の数の差が 1 以下）になる割り当て（ID の sha1 で並べて順番に配る。入力順に依存しない）。誤答の順は種つきシャッフル。版は v1 だけで、他は `ValueError`。
- 特殊な選択肢（「該当なし」「どれでもない」「判断できない」など。`is_special`）は、シャッフルの対象外で、元の相対順のまま末尾に置く。正解が特殊な選択肢の問は、位置が末尾に決まり、均等割り当ての対象外。
- 逆順（`REV`）: `reverse_options` と `reversed_expected(expected, n)` = `n-1-expected`。通常は使わず（`REV=0`）、位置の偏りを見るときだけ。
- ローダーの正解位置は、**v1 全体（dropped を除く）で計算してから**ファイル・群で絞る。一部だけ読んでも位置は変わらない。

## 6. テスト

`python -m unittest discover -s datasets/tests`（リポジトリのルートで。ネットワーク不要）。各テストの docstring に「何を守るか」を書いてある。

| ファイル | 内容 |
|---|---|
| `test_options.py` | 決定性、位置の均等、選択肢 2〜12 個の正解の対応、特殊な選択肢の規則、逆順、v1 以外の拒否 |
| `test_loader.py` | 正解の対応（英・日）、単一言語の問、文章のみの問の state、`(version, id)` のキー、1 問 1 枚、v1 の問数 |
| `test_manifests.py` | 本文・画像・`.env` が無いこと、dropped の扱い、分類表と行の一致、画像一覧（`images_v1.json`）との対応 |
| `test_new_questions.py` | 新問の受け皿: ID 範囲の表、検証（各種の誤りを具体的に拒否）、ローダー（既存の位置が動かない）、選択肢 2〜16・段階 3/7/10、ランナーの限界チェックとダミー ask、検証→分類表→ロードの一巡。NOTES のサンプル行がテスト済みのものと一致すること |

## 7. 既知の制約

- 分類（`image_type`・`skill`）は粗いラベルで、`photo-other` と `figure` は既定値。
- 難度は作る側・レビュアーの付け方のまま。
- 画像の置き場所は `images_root`（既定 `work/`）。

## 10. 新問を足す（v1 に問を追加するとき）

新問は、**別々の担当が並行して**書き足せるように、担当（tag）ごとに別ファイル・別の ID 範囲に置く。**既存の v1 行（`photo/biz/rsn/txt.jsonl`）と `questions_v1.csv` は変更しない。** 画像・Wikipedia 本文は commit しない（`work/` は gitignore）。

### 10.1 置き場と ID の予約範囲

- 置き場: `datasets/questions/v1/new_<tag>.jsonl`（UTF-8・LF・1 行 1 問）。**自分の tag のファイルだけ書く。**
- ID: `<群>-NNNN`（群 = photo / biz / rsn / txt、4 桁）。**0001〜0999 は最初の帯（origin `base`）**で、新問は **1001 以降**。tag ごとに下の範囲を予約する（`datasets/newq.py` の `RANGES` が正本。表は `python -m datasets.newq` で再生成できる）。範囲の外、他の tag の範囲、既存 ID との重複は検証がエラーにする。新しい tag が要るときは、先に `newq.RANGES` に 1 行足す（予備の範囲を使う）。

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

既存の v1 行と同じ項目です。

| 項目 | 値 |
|---|---|
| `id` | `<群>-NNNN`（接頭辞 = `group`、tag の予約範囲内） |
| `origin` | **`"new"`**（必ず） |
| `derived_from` | 派生元の v1 ID（既存または他の new 行）、無ければ `null`。文章のみの対照は元の画像問を指す |
| `relation` | 任意。`variant` / `mirror` / `control` / `rewrite` / `extension` |
| `group` / `source` / `image_type` / `skill` / `difficulty` | 既存と同じ値（`taxonomy.py` の `V1_*`）。派生は親の `source` のまま。**値を勝手に増やさない**（足りない分類値は調整役が `taxonomy.py` に足す） |
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
{"id": "photo-2001", "origin": "new", "derived_from": "photo-0001", "relation": "variant", "group": "photo", "source": "commons-article", "image_type": "photo-animal", "skill": "recognition", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "choice", "answer_format": "choice:6", "tags": ["classify", "animal", "many-options"], "images": ["File:Sheep lounging in the shade of a tree at Röe Castle.jpg"], "local_images": ["data/images/b68ae37691c83e58bfc75db7e37b3546c9cfc400.jpg"], "en": {"instr": "Which animal is mainly shown?", "correct": "sheep", "wrong": ["goat", "pig", "rabbit", "cow", "None of the above"]}, "ja": {"instr": "主に写っている動物はどれですか？", "correct": "羊", "wrong": ["ヤギ", "豚", "ウサギ", "牛", "該当なし"]}, "review": {"state": "unreviewed", "history": []}}
{"id": "biz-1001", "origin": "new", "derived_from": null, "group": "biz", "source": "rendered", "image_type": "chart", "skill": "negation", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "noul", "answer_format": "yesno", "tags": ["synthetic", "chart", "negation"], "local_images": ["generated/biz-1001.png"], "en": {"instr": "No bar is taller than the first bar"}, "ja": {"instr": "最初の棒より高い棒はない"}, "answer": true, "review": {"state": "unreviewed", "history": []}}
{"id": "rsn-1001", "origin": "new", "derived_from": null, "group": "rsn", "source": "rendered", "image_type": "ui", "skill": "quantity", "difficulty": "medium", "lang": "both", "langs": ["en", "ja"], "modality": "image", "kind": "score", "answer_format": "score:7", "tags": ["synthetic", "gauge", "level"], "local_images": ["generated/rsn-1001.png"], "en": {"instr": "How full is the gauge?", "levels": ["0-14%", "15-28%", "29-42%", "43-57%", "58-71%", "72-85%", "86-100%"]}, "ja": {"instr": "ゲージはどれくらい満たされていますか？", "levels": ["0〜14%", "15〜28%", "29〜42%", "43〜57%", "58〜71%", "72〜85%", "86〜100%"]}, "answer": 3, "review": {"state": "unreviewed", "history": []}}
{"id": "biz-2001", "origin": "new", "derived_from": null, "group": "biz", "source": "rendered", "image_type": "sign", "skill": "ocr", "difficulty": "medium", "lang": "ja", "langs": ["ja"], "modality": "image", "kind": "choice", "answer_format": "choice:5", "tags": ["synthetic", "japanese", "sign"], "local_images": ["generated/biz-2001.png"], "ja": {"instr": "この標識が示している意味はどれですか？", "correct": "一時停止", "wrong": ["徐行", "進入禁止", "駐車禁止", "該当なし"]}, "review": {"state": "unreviewed", "history": []}}
{"id": "txt-1001", "origin": "new", "derived_from": "biz-0015", "relation": "control", "group": "txt", "source": "none", "image_type": "none", "skill": "text-comprehension", "difficulty": "easy", "lang": "both", "langs": ["en", "ja"], "modality": "text", "kind": "noul", "answer_format": "yesno", "tags": ["control", "no-picture"], "local_images": [], "en": {"instr": "The values rise from left to right", "state": "No picture is attached to this question."}, "ja": {"instr": "値は左から右に向かって増えている", "state": "この問題には画像が添付されていません。"}, "answer": true, "review": {"state": "unreviewed", "history": []}}
```
<!-- samples:end -->

### 10.3 画像

- 画像は `work/generated/<自分の id>.png`（原寸）に置く。224px 版は `work/generated/px224/<id>.png`（なければ実行時に作る）。**gitignore で commit されない。**
- 1 問 1 枚。ファイル名は v1 全体で一意（反転・加工した画像も、親と別の新しいファイル `<自分の id>.png` にする）。
- 親の画像をそのまま使う変種（選択肢だけ変える等）は、親の `local_images` と**同じパス**を書く（親が既存の写真なら `data/images/...`）。新しい画像ファイルは作らない。
- 画像の探し場所は、検証が `--images-root`（既定: `$WIKIQA_IMAGES`、`work/`、`$WIKIQA_DATA_ROOT`）。新規画像が無いとエラー。親の画像がこの機械に無いときは警告だけ。
- 新しく選んだ Commons 画像（`commons-new`）は CC0・パブリックドメインだけ。出典（`images` の File 名と `credit`）を行に残す。人物の同定を求める問は作らない。

### 10.4 Wikipedia の本文を載せない

- 記事由来の txt 問は `article`（タイトルと revision ID）だけ持ち、本文・根拠文は書かない（`evidence`、`passage`、`text`、`body` のキーは検証が拒否する）。実行時に手元の `passages.json` から読む（無い機械では動かない）。`state` は書かない。新しい記事を使うときは、その revision の本文を手元の `passages.json` に足す（commit しない）。
- 文章のみの対照（対照用の txt 問）は `article` を持たず、**自分で書いた `state`（各言語 600 字以内）** を持つ。画像が付いていないことを書き、問に必要な情報は state に自分の言葉で入れる。`derived_from` = 元の画像問（必須）。`skill` は `text-comprehension`、`image_type`/`source` は `none`。
- どの文字列も 600 字を超えない（コピーした本文の混入を防ぐ）。

### 10.5 選択肢・段階・はい/いいえ

- 選択肢は **2〜16 個**（QEV の上限が 16）。段階評価は **2〜10 段階**（OneJev / Strands の上限が 10。3・5・7・10 を使う）。段階は順序のある値で、並べ替えない。各段階に数値の範囲や基準を書く。
- 選択肢は実行時に `balanced` で並べ替える（§5）。**順序に依存する選択肢は書かない**（「上記のすべて」「前の選択肢」「両方」など。検証が警告）。選択肢の重複（大文字小文字・空白を無視）、正解と同じ誤答は不可。
- 「該当なし」類は正準の表記で書く（末尾に固定され、シャッフルされない。en と ja で**同じ位置**に置く）。en: `None of the above` / `Cannot be determined` / `Not enough information`。ja: `該当なし` / `どれも当てはまらない` / `上記のいずれでもない` / `判断できない`。他の言い回しだと特殊な選択肢として扱われず、途中にシャッフルされる。
- 正解の位置は、群 × 選択肢数で均等になるよう**実行時に割り当てる**（行には持たない）。new 行は、既存の行の位置を**動かさず**、その上に均等に足される（`options.assign_positions_with_base`）。正解が「該当なし」の問は末尾に固定され、均等割り当ての対象外。
- 段階評価の正解の段階は 0〜n-1 に均等に配る（`options.suggest_score_answers(ids, n)` が決定的な配分を出す。ファイルごとに検証が偏りを警告）。はい/いいえは「はい」「いいえ」をおよそ半々にする（20 問以上で偏りを警告）。
- 日本語固有（`lang="ja"`）は ja 側だけ書く。ja の問に日本語の文字が無いとエラー。画像内の文字を読む問は、選択肢も画像に印刷された原語のまま。`ja_specific` の tag は `lang="ja"` 必須。

### 10.6 検証と分類表

```
python datasets/tools/validate_new.py [--tag TAG] [--images-root DIR] [--no-image-check] [--write-manifests --tag TAG]
```

自分のファイルを渡す前に必ず通す（エラーは `ファイル:行 ID: 内容` で出る。終了コード 0 = エラーなし）。見るもの: スキーマ、ID が予約範囲内・全 v1 で一意、**重複問（下記）**、正解が選択肢内・重複なし、en/ja の個数一致、選択肢 ≤ 16・段階 ≤ 10、画像（1 問 1 枚・存在・開ける・名前の一意）、本文を含まない、日本語の文字、はい/いいえ・段階の形式。`--write-manifests` は **`--tag` が必須**（無いと何も書かず終了コード 2。他の担当の分類表を書かないため）で、その tag にエラーが無いとき `manifests/questions_v1_new_<tag>.csv`（分類表。`origin`・`derived_from` つき）を**その行から作り直す**（中身が変わらなければファイルは書き換えない）。tag ごとの別ファイルなので担当どうしで衝突しない。

**重複問（new 行）**: 同じ画像（自前の画像は内容の sha256、共有する画像はパス）・同じ設問文（en/ja）・同じ正解・同じ `answer_format` の問は重複で、**後ろの ID がエラー**（誤答の組だけ違っても重複）。変種が別の問になるのは、**選択肢の数か種類（`answer_format`）、設問文（否定など）、画像（反転・加工したら新ファイル）、正解**のどれかが変わるとき。したがって `photo-0001`（4 択）の「同じ 4 択で誤答だけ替えた」問は重複、「6 択にした」「はい/いいえにした」問は変種。

### 10.7 除外

評価から外す問は `python datasets/tools/drop_ids.py <ID...> --reason "..."`（dry-run。`--apply` で書く）。`review.state` を `dropped` にし履歴に理由を残す。行はファイルに残り、ローダー・ランナーが除外する。

### 10.8 ランナー・ローダー

- `datasets.loader.load_v1_cases(groups, include_new=True, only_new=False)` と `runner.cases.load_cases(set, version="v1")`: dropped 除外・balanced の順・new 行を含む。セット名は `photo` / `biz` / `rsn` / `txt` / `all` / `new`（new だけ）。`python -m runner.run --set all ...`。224px のキャッシュは `work/px224_v1`。結果の保存キーは `(dataset_version="v1", id)`。
- `runner.cases.dry_run(cases)`（ダミーの ask で全問を一巡し、返り値の型・範囲、expected、画像の枚数、選択肢の重複を検査）と `runner.cases.check_all_limits(cases)`（全アダプタの `LIMITS` の選択肢数・段階数・画像枚数の上限と照合）。v1 全体（new を含む）でテストが通ること。

## 11. v1 の最終状態とビルド

評価対象は **2768 問** = base（origin `base`）1841 + 新問（origin `new`）927。dropped は 135 行で、行はファイルに残るが評価には入らない。数字はすべて `dist/v1/manifest_v1.json`（`python -m datasets.build_v1`）から取った。

### 11.1 構成（群 × origin）

| 群 | base | 新問 | 計 | 新問の中身（tag） |
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
- 画像: 2127 枚 = Commons 1021（CC0 / パブリックドメイン）+ 以前に描いた画像 477 + 新しく作った画像 629（描画・Tkinter・1 枚化 12 問）。
- 新問の review: reviewed 824 / changed 103 / dropped 14（新問 941 行のうち）。

privacy-check が付いた問は 84（`manifests/privacy_check_v1.md`。決定: 残す）。

### 11.2 文章のみの対照（txt_controls）の注意

対照 99 問は、画像問から画像を外した変種で、**問に必要な情報を `state` に自分の言葉で入れている**。画像にはない**正確な数値**（棒の高さ、金額、時刻など）が state に入るため、**文章版は画像版より易しくなり得る**（画像から読み取る難しさがなく、数値が与えられる）。画像版と比べるときは、この点を明記すること（「画像を読む力」ではなく「文章で与えた情報で答える力」との差になる）。state は各言語 600 字以下の自作文で、Wikipedia の本文は入らない。記事由来の文章のみ問（87 問）は `state` を持たず、実行時に手元の `passages.json` から読む（`dist` の `cases_v1.jsonl` では `state: null` と記事の参照）。

### 11.3 重複・near-duplicate の扱い

- base: 同じ 224px 画像（sha256 一致）で設問・正解・種類が同じ問は後ろの ID を dropped にした（3 問）。
- 新問: `validate_new.py` が、同じ画像・同じ設問・同じ正解・同じ `answer_format` の問をエラーにする（後ろの ID）。親と同じ画像を使う変種は、選択肢の数・種類、設問（否定など）、正解のどれかが変わるときだけ別の問。
- **意図的な near-duplicate**: 写真の派生（photo_variants）は、同じ画像に別の形式（2 択・6 択・否定・該当なし等）を付けた問で、重複ではなく**同じ画像の別の問い**。集計で画像単位にまとめるときは `images_v1.json` の `question_ids`（画像ごとの問の一覧）を使う。同じ元から作った文章のみ対照は `derived_from` で元の画像問を指す。
- 新問どうし・新問と base の「意味が近い問」は自動検出していない（レビューで確認）。

### 11.4 既知の制約

- **画像の判読性**: 入力は長辺 224px。描画画像の小さい文字（表・レシート・時刻表）は 224px で読めないことがあり、難度に反映してあるが、モデルの誤りが「読めない」ためか「理解できない」ためかは区別していない。
- **フォント**: 日本語の描画は Noto Sans JP / Noto Serif JP（OFL。この機械の Windows フォルダのもの）。別のフォントでは文字の形・幅が変わる（答えは変わらない）。フォント自体は配布しない。
- **Tkinter の画像（tk_ui 249 問）**: 本物の Tk / ttk のウィンドウをスクリーンショットしたもので、OS・テーマ・DPI・フォントに依存する。**画素は他の機械で一致しない**（答えは設定から導くので変わらない）。再生成は同じ画像を保証しない。配布物は作成時の画像そのもの（zip の sha256 で固定）。
- **生成スクリプトを `--apply` すると jsonl が上書きされる**: `gen_v1_*.py` は、レビュー済みの `datasets/questions/v1/*.jsonl` を上書きし、レビューの履歴（`review.state` / `history`）を `unreviewed` に戻して失う。書き込みの条件はスクリプトごとに違う: `gen_v1_new.py` と `gen_v1_tk_ui.py` は**既定で書く**（`--dry` のときだけ書かない。tk_ui は `--rows-only` でも jsonl を書く）、`gen_v1_ja.py` と `gen_v1_rewrite.py` は `--apply`、`gen_v1_txt_controls.py` は `--write`、`gen_v1_new_b.py` は reviewed 行があると `--force` が無い限り拒否する。**最終版では実行しない**。再生成が必要なときは出力先を変えて差分を確かめる。`build_v1` と集計ツールは読み取りだけ。
- 正解位置の均等化は、新問を足しても既存の問の位置を動かさない設計だが、新問どうしの位置は集合が固まった時点の値。追加すると新問の位置が変わり得る。
- 段階評価の正解の段階は new_rendered_b の 3 段階で [3, 3, 1] と少し偏る（validate_new の警告 1 件）。

### 11.5 ライセンス方針とビルド

- Commons 写真: CC0 / パブリックドメインだけ（zip 作成時に検査。他のライセンスなら止まる）。作者・URL・ライセンスは `images_v1.json` と各 zip の `ATTRIBUTION.md`。
- 自作画像のライセンスは **CC0-1.0 で確定**。対象は生成画像 629 枚（Tkinter・描画・日本語固有・1 枚化）と、以前に描いた画像 477 枚。各 zip の `ATTRIBUTION.md` に CC0-1.0（Public Domain Dedication）、描画スクリプト（`datasets/synthetic`）、使ったフォントを書く。
- フォント（事実の記載。フォント自体は配布しない）: 日本語の描画は Noto Sans JP / Noto Serif JP（OFL 1.1）、英数字の描画は Arial（その機械にあれば。なければ DejaVu Sans）。Tkinter の画像は自作画面のスクリーンショットで OS の枠は含まず、画面内の文字は **Windows 同梱のフォント（英語 UI は Segoe UI、日本語 UI は Yu Gothic UI）** で描かれている（249 問: Segoe UI 203・Yu Gothic UI 46。ID の一覧は `manifests/windows_fonts_images_v1.md`）。法的な判断はしない。
- 問題文・選択肢は自作（Wikipedia の本文は含めない。記事の revision の参照だけ）。

`python -m datasets.build_v1` は `dist/v1/`（gitignore）に次を作る。決定的で冪等（日付は `--date`、zip は名前順・固定時刻）。画像は `--root` / `$WIKIQA_DATA_ROOT` の下の `data/...`（Commons と以前に描いた画像）と、`work/generated/`（新しい画像）から読む。

| ファイル | 内容 |
|---|---|
| `questions_v1.jsonl` | 評価対象の全問（問・正解・誤答・state（対照のみ自作）・分類・難度・review・origin・derived_from・画像の path） |
| `cases_v1.jsonl` | `datasets.loader` の評価用ケース（balanced の選択肢の並びと expected を確定。en / ja を 1 行に並べる。画像は論理パス、記事由来の txt は `state: null`） |
| `manifest_v1.json` | 版、日付、問数（群・形式・origin・言語・選択肢数・難度ほか）、各ファイルの sha256 |
| `questions_v1_all.csv` | 評価対象の分類表 |
| `images_v1.json` | 使う画像の全一覧（Commons: 作者・ライセンス・URL・sha。生成: `source: "generated"`、スクリプト、seed、sha、ライセンス CC0-1.0、Tkinter の画像はフォントの注記） |
| `images-224px.zip` / `images-original.zip` | 画像（zip のメンバー名は論理パス `data/images/...`、`generated/...`。展開してそのまま `images_root` に使える）+ `ATTRIBUTION.md`。**アップロードはしない** |
| `build_report.md` | 自己検査（画像の存在・sha256、選択肢数の上限、1 問 1 枚、ID 一意、en/ja 一致、txt の state、dropped 不含、位置の偏り、runner の v1 セット、validate_new ほか） |

版名は `datasets/version.py` の `DATASET_VERSION` から取る（出力先 `dist/<版>/` もここから）。
