# privacy-check が付いた問（84 問）

レビュアーが「人物が写っている（顔・個人が特定され得る）」として `privacy-check` を付けた、評価対象の問の一覧です（drop された問は含みません）。
方針: 人物が写っているだけでは外さず、設問が人物の同定を求めない限り残しました（同定を求める問は drop / fix 済み）。画像はすべて CC0・パブリックドメインの Commons 写真です。
**決定: 残す（2026-10-11）。** ただし、人物の同定を求める設問は含まれません。
要望があれば個別に除外できます: `python datasets/tools/drop_ids.py <ID> ... --reason "..." --apply` が、各 ID の `review.state` を `dropped` にし、対応表（`idmap_legacy_v1.csv` / `idmap_v1_new_<tag>.csv`）の status を `dropped` にして、分類表を作り直します（`v1_io` と `apply_review.apply_entries` の drop 判定と同じ）。その後 `python -m datasets.build_v1` で `dist/v1` を作り直します。
人物の顔の画像はここに載せていません（ID と理由のみ）。画像は `dist/v1/images_v1.json` の `question_ids` から引けます。

群別: photo 84

| ID | 群 | image_type | 理由の要約 |
|---|---|---|---|
| photo-0014 | photo | sign | faces of historical persons visible, but question is about the banner text |
| photo-0015 | photo | photo-person | セピアの白黒写真でカラーでない（false）は妥当。image_type を人物写真に付け直した。 |
| photo-0026 | photo | photo-person | レビュアーはプライバシーを理由に drop を提案したが、設問は人物の同定を求めない白黒判定で、画像は CC0/PD。残して、drop の判断はユーザーに委ねる（privacy-check）。 |
| photo-0027 | photo | photo-other | レビュアーはプライバシーを理由に drop を提案したが、設問は人物の同定を求めない白黒判定で、画像は CC0/PD。残して、drop の判断はユーザーに委ねる（privacy-check）。 |
| photo-0030 | photo | photo-person | private individuals' faces visible |
| photo-0062 | photo | photo-person | (理由の記載なし) |
| photo-0075 | photo | photo-person | (理由の記載なし) |
| photo-0076 | photo | photo-person | テーブルに子ども 2 人がいて true は妥当。image_type を photo-person に。 |
| photo-0084 | photo | photo-person | 薬局で 2 人が向き合って話しており true は妥当。image_type を photo-person に。 |
| photo-0106 | photo | photo-scene | (理由の記載なし) |
| photo-0120 | photo | photo-scene | 白黒写真で false は妥当。image_type を photo-scene に。 |
| photo-0127 | photo | photo-person | 後ろ向きに座りオールを漕ぐエイト（漕手 8 人＋舵手）で、ボート競技は一目で分かる。水泳・スキー・自転車は無関係すぎるため、帆も球もなく画像で区別できる水上競技の誤答に替えた。人物は写るが同定は求めない。 |
| photo-0128 | photo | photo-scene | (理由の記載なし) |
| photo-0150 | photo | photo-person | (理由の記載なし) |
| photo-0151 | photo | photo-person | 白衣の人がピペットで試料を扱う実験室の写真で正解は妥当。人物が主題なので image_type を photo-person にした（同定は求めない）。 |
| photo-0152 | photo | photo-person | 白衣を着ているのが見え正解（はい）は妥当。ja の「人は」が不自然なので「この人は」にし、image_type を photo-person にした。 |
| photo-0198 | photo | photo-person | (理由の記載なし) |
| photo-0199 | photo | photo-person | 白黒写真なので正解（いいえ）は妥当。image_typeを人物写真に直した。 |
| photo-0207 | photo | photo-person | (理由の記載なし) |
| photo-0210 | photo | photo-scene | (理由の記載なし) |
| photo-0214 | photo | photo-object | 三脚上の緑色の測量機器（トータルステーション様）で正解は妥当。人物は写るが同定を求めない。image_typeを直した。 |
| photo-0216 | photo | photo-person | (理由の記載なし) |
| photo-0217 | photo | photo-person | 4人とも白い制服姿で正解（はい）は妥当。image_typeを人物写真に直した。 |
| photo-0221 | photo | photo-person | 兵士が旗を持って整列しており正解（はい）は妥当。主題が人物の集団なのでimage_typeを直した。 |
| photo-0222 | photo | photo-scene | (理由の記載なし) |
| photo-0227 | photo | photo-person | (理由の記載なし) |
| photo-0231 | photo | photo-person | リング上で蹴りを出しており正解は妥当。誤答が水泳・スキーなど無関係なので、蹴りを見れば区別できるボクシング・レスリングに替えた。 |
| photo-0238 | photo | photo-person | 会場全体を引きで撮った写真で選手は小さいが、氷上の複数シートとハウス（同心円の的）が明瞭に見え正解カーリングは妥当。アイスホッケー（同じく氷上の会場）が紛らわしいため外したモデルが多いと考えられる。 |
| photo-0243 | photo | photo-other | (理由の記載なし) |
| photo-0244 | photo | photo-person | 白黒写真なので正解（いいえ）は妥当。image_typeを人物写真に直した。 |
| photo-0277 | photo | photo-person | (理由の記載なし) |
| photo-0288 | photo | photo-scene | 白黒写真なので false で正しい。村の情景なので photo-scene に付け直した。 |
| photo-0292 | photo | photo-person | (理由の記載なし) |
| photo-0294 | photo | photo-person | 白黒写真なので false で正しい。人物の写真なので photo-person に付け直した。 |
| photo-0311 | photo | photo-scene | 白黒写真で truth=false は正しい。大型計算機の前の人物（後ろ向き）がいる室内の場面なので image_type を photo-scene に。 |
| photo-0340 | photo | photo-scene | (理由の記載なし) |
| photo-0342 | photo | text-in-image | キリル文字の標語が読め、ロシア語で正解は妥当。人物の同定は求めていない。文字を読む問なので image_type を text-in-image に。 |
| photo-0360 | photo | photo-person | 白黒写真で truth=false は正しい。人物が主題の写真なので image_type を photo-person に（人物の同定は求めていない）。 |
| photo-0378 | photo | photo-scene | (crowd, not identifiable) |
| photo-0402 | photo | photo-person | 短髪の男性に見える人物が口を大きく開けて歌っている。設問の『女性』が画像と合わないので『この人』に直した。人物の同定は求めていない。 |
| photo-0403 | photo | photo-other | (理由の記載なし) |
| photo-0408 | photo | photo-scene | 白黒の舞台写真で truth=false は妥当。image_type を photo-scene に。 |
| photo-0432 | photo | photo-person | (理由の記載なし) |
| photo-0444 | photo | photo-person | (理由の記載なし) |
| photo-0468 | photo | photo-person | (理由の記載なし) |
| photo-0469 | photo | photo-person | (理由の記載なし) |
| photo-0475 | photo | photo-person | セピア調の白黒写真で truth=いいえは正しい。人物の同定は求めていない。image_type を photo-person に。 |
| photo-0486 | photo | photo-other | (理由の記載なし) |
| photo-0487 | photo | photo-other | (理由の記載なし) |
| photo-0488 | photo | photo-scene | (理由の記載なし) |
| photo-0496 | photo | art | 挿絵で、手前に並んで歩く男性は 4 人だが、右奥にも人物が描かれていて「描かれている男性」全体の数が曖昧（8/20 誤答）。手前に限定した。描かれた絵なので image_type は art。 |
| photo-0515 | photo | photo-scene | 迷彩服の人々が芝生で綱を引いている。個人の同定は求めない。群衆の場面なので photo-scene、一目で分かるため easy。 |
| photo-0545 | photo | photo-object | 女性が後ろ向きでコンパクトデジタルカメラの液晶を見ている。顔は見えず個人の同定は求めない。主題はカメラなので photo-object。 |
| photo-0556 | photo | photo-other | (理由の記載なし) |
| photo-0589 | photo | photo-other | 人物は画面中央の中景に立っており、「遠くに」と言えるかは曖昧。答えが一意になるよう位置の修飾を外した。 |
| photo-0609 | photo | sign | (理由の記載なし) |
| photo-0617 | photo | photo-person | (理由の記載なし) |
| photo-0618 | photo | photo-person | 芝刈り中の男性が黄色い耳当てをつけているのが見え、正解は妥当。分類を photo-person に付け直した。 |
| photo-0628 | photo | photo-scene | 女性は左の井戸の木組みから離れた右端に立っており「そば」かどうかは曖昧。位置関係で一意に決まる「右側」に直した（正解は はい のまま）。 |
| photo-0647 | photo | photo-scene | 操作卓とモニターの並ぶ管制室で、誤答も遠いため hard は過大。人物の同定は求めていない。 |
| photo-0655 | photo | photo-scene | (理由の記載なし) |
| photo-0752 | photo | photo-scene | ヤシの木と白い砂浜・青い海で一目で熱帯のビーチと分かるため easy にした。人物は小さく後ろ姿。 |
| photo-0768 | photo | photo-person | 警官 2 人に連行される女性の白黒写真で、船は写っていないので false は正しい。image_type を photo-person にした（人物の同定は求めない）。 |
| photo-0805 | photo | photo-scene | (理由の記載なし) |
| photo-0806 | photo | photo-person | (理由の記載なし) |
| photo-0808 | photo | photo-person | (理由の記載なし) |
| photo-0848 | photo | photo-scene | (small workers, not identifiable) |
| photo-0849 | photo | photo-scene | 画像中央に作業員が乗ったシザースリフトがはっきり写っており、一目で判断できるため easy にした。 |
| photo-0870 | photo | text-in-image | 左上の「In space, Orion capsule」が 224px で読め正解は妥当。画面上の文字を読む問なので text-in-image。 |
| photo-0906 | photo | photo-scene | (理由の記載なし) |
| photo-0929 | photo | photo-scene | 文字盤・記録計などの測器が壁に並ぶ部屋で、選択肢の中では正解以外ありえない。人物（女性）が写るが同定を求めないため privacy-check のみ。難度を medium にした。 |
| photo-0942 | photo | photo-person | (理由の記載なし) |
| photo-0979 | photo | photo-plant | ビニールハウス内に葉物（チャード・レタス類）が茂り、正解は妥当。人物が写るが同定は求めていない。主題は作物なので photo-plant に。 |
| photo-0995 | photo | photo-structure | 人々は木造の桟橋（櫓付き）の上に立っており、正解は妥当。人物は小さく同定不能。主題は桟橋なので photo-structure に。 |
| photo-1114 | photo | photo-scene | small pedestrians, not identifiable |
| photo-1131 | photo | photo-vehicle | firefighters standing in front of truck, small |
| photo-1136 | photo | document | page contains a portrait photo, question does not ask identity |
| photo-1137 | photo | document | newspaper photo of a missing child, question asks only language |
| photo-1227 | photo | photo-scene | (理由の記載なし) |
| photo-1245 | photo | photo-scene | (理由の記載なし) |
| photo-2220 | photo | photo-vehicle | 赤い車体と消防士の装備で一目で消防車と分かり、12 択でも hard は過大なので medium にした。前に消防士が数人立っている（同定は求めていない）。 |
| photo-2245 | photo | photo-vehicle | (理由の記載なし) |
| photo-2247 | photo | photo-vehicle | (理由の記載なし) |
| photo-2263 | photo | photo-vehicle | 消防車と消防士。乗り物の選択肢（バス・救急車・タクシー・トラクター）はどれも写っておらず該当なしで一意。人物は小さく同定は求めていない。 |
