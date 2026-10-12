# v1: 重複問の検査（バッチをまたぐ）

`datasets/tools/dedupe_v1.py` が作る。重複 = **同じ 224px 画像（ファイルの sha256 が一致）で、設問（英語）・正解・種類が同じ**。前の ID を残し、後ろの ID を `dropped` にした（`review.history` に `drop` / `duplicate of <ID> (cross-batch)`、idmap の status も `dropped`）。

- `exact`: 選択肢の集合も同じ。`wrong-set-differs`: 誤答の組だけ違う（実質同じ問）。
- 同じ画像でも設問か正解が違うもの（個数・色・有無など別の観点を問うもの）は重複にしない。同じ画像を共有する問の群は多数あるが、設問まで同じなのはこの一覧だけ。

合計: **3 問を追加で drop**（レビュー時点で dropped だった重複は含まない）。

| 残す ID | drop した ID | 種類 | 設問と正解 | 日付 |
|---|---|---|---|---|
| biz-0227 | biz-0232 | exact | Which weekday is circled in red? -> Thu | 2026-10-11 |
| biz-0229 | biz-0233 | exact | Which weekday is circled in red? -> Mon | 2026-10-11 |
| biz-0228 | biz-0237 | exact | Which weekday is circled in red? -> Fri | 2026-10-11 |
