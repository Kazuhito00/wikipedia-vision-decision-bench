# needs_new_image_type の集計と付け替えの状況

レビュアーが「既存の image_type に収まらない」として `needs_new_image_type: <値>` を付けた問（drop された問を除く）の集計です。
`astronomical`（天体）と `satellite`（衛星・航空写真）は `taxonomy.V1_EXTRA_IMAGE_TYPES` に追加済みで、**該当問の image_type を付け替えました**
（`datasets/tools/relabel_image_type.py`。変更した行だけを書き、`review.history` に `{date, what: "image_type", why}` を追加。冪等）。
それ以外の値（medical-scan など）は taxonomy に追加しておらず、付け替えていません。

| 提案 | 問数 | 付け替え先 | 付け替え済み | 備考 |
|---|---|---|---|---|
| astronomical | 34 | astronomical | 34 |  |
| satellite | 24 | satellite | 24 |  |
| astronomy | 4 | astronomical | 4 |  |
| medical-scan | 2 | （付け替えない） | - | taxonomy に無い値。ユーザー判断待ち |
| aerial | 1 | satellite | 1 |  |
| micrograph | 1 | （付け替えない） | - | taxonomy に無い値。ユーザー判断待ち |
| scientific-illustration | 1 | （付け替えない） | - | taxonomy に無い値。ユーザー判断待ち |
| technical-drawing | 1 | （付け替えない） | - | taxonomy に無い値。ユーザー判断待ち |

付け替えた問は合計 63（履歴に image_type の記録があるもの）。現在の image_type の問数: astronomical 38 / satellite 25。

付け替えない提案の ID:

- medical-scan: photo-0912, photo-0913
- micrograph: photo-0131
- scientific-illustration: photo-0563
- technical-drawing: photo-0807
