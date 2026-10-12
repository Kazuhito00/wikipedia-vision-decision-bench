# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0553-h0597 (pictures used by the Japanese article only).
Skin close-ups, prisoners, rallies and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0553", "space", ["photo", "painting", "map"], diff="medium")
TYPE("h0560", "page", ["photo", "map", "satellite"], diff="medium")
Q("h0562", "Which three island regions are labelled on the map?", "地図に書かれている 3 つの島々の地域はどれですか？",
  "Polynesia, Micronesia and Melanesia|ポリネシア・ミクロネシア・メラネシア",
  ["Scandinavia, Iberia and the Balkans|スカンディナヴィア・イベリア・バルカン", "Siberia, Manchuria and Tibet|シベリア・満洲・チベット"],
  tags=["ocr", "map"], diff="medium")
TYPE("h0564", "map", ["photo", "painting", "satellite"])
Q("h0565", "What kind of scene is this?", "これはどんな場面ですか？", "A crowd in front of a grand building|壮大な建物の前の人々",
  ["A forest|森", "A beach|ビーチ", "A desert|砂漠"], tags=["scene"], diff="medium")
Q("h0567", "Which instrument is shown?", "どの楽器が写っていますか？", "A cymbal|シンバル", ["A guitar|ギター", "A violin|バイオリン", "A flute|フルート"], tags=["classify", "object"])
Q("h0567", "What brand name is printed on it?", "刻印されているブランド名は何ですか？", "Zildjian", ["Yamaha", "Fender", "Roland"], tags=["ocr"], diff="hard")
TYPE("h0569", "painting", ["photo", "diagram", "satellite"])
TYPE("h0571", "map", ["photo", "painting", "satellite"])
Q("h0574", "Which animals flank the lady in the tapestry?", "タペストリーの女性の両脇にいる動物はどれですか？", "A lion and a unicorn|ライオンとユニコーン",
  ["Two dogs|犬 2 匹", "Two horses|馬 2 頭", "Two eagles|ワシ 2 羽"], tags=["detail"], diff="hard")
Q("h0590", "Which animal is shown?", "どの動物が写っていますか？", "Whale|クジラ", ["Shark|サメ", "Seal|アザラシ", "Turtle|カメ"], tags=["classify", "animal"], diff="medium")
Q("h0591", "Which historic weapon is displayed?", "展示されている昔の武器はどれですか？", "A crossbow|クロスボウ",
  ["A rifle|ライフル", "A sword|刀", "A cannon|大砲"], tags=["classify", "object"], diff="hard")
Q("h0593", "What colours is the animal?", "動物は何色ですか？", "Black and yellow|黒と黄色",
  ["Red and blue|赤と青", "All white|真っ白", "Green|緑"], tags=["colour", "attribute"])
Q("h0596", "Which desert is shown in this satellite image?", "この衛星画像に写っている砂漠はどれですか？", "The Sahara|サハラ砂漠",
  ["The Gobi|ゴビ砂漠", "The Atacama|アタカマ砂漠", "The Kalahari|カラハリ砂漠"], tags=["geo"], diff="hard")
