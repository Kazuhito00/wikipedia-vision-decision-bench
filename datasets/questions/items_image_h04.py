# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0161-h0220 (pictures used by both wikis). Medical close-ups were left out."""
from templates import Q, N, TYPE, S, colour

Q("h0161", "Which animals pull the plough?", "鋤を引いている動物はどれですか？", "Oxen|牛", ["Horses|馬", "Camels|ラクダ", "Dogs|犬"], tags=["classify", "animal"], diff="medium")
Q("h0163", "Which continent is mainly shown?", "主に写っている大陸はどれですか？", "Asia|アジア",
  ["Africa|アフリカ", "South America|南アメリカ", "Australia|オーストラリア"], tags=["geo"], diff="medium")
Q("h0164", "Which sport is shown?", "どのスポーツですか？", "Rowing|ボート競技", ["Swimming|水泳", "Skiing|スキー", "Cycling|自転車競技"], tags=["classify", "sport"])
N("h0164", "The athletes are on water", "選手たちは水の上にいる", True, tags=["scene"])
Q("h0165", "What is the bright object with a long tail?", "長い尾を持つ明るい天体は何ですか？", "A comet|彗星",
  ["A rocket|ロケット", "A firework|花火", "An airplane|飛行機"], tags=["classify", "space"])
Q("h0168", "Which islands are shown?", "写っている島々はどれですか？", "The United Kingdom and Ireland|イギリスとアイルランド",
  ["Japan|日本", "Italy|イタリア", "New Zealand|ニュージーランド"], tags=["geo"], diff="medium")
Q("h0169", "What are the rod-shaped objects?", "棒状のものは何ですか？", "Bacteria|細菌", ["Seeds|種", "Pills|錠剤", "Worms|ミミズ"], tags=["classify", "object"], diff="hard")
Q("h0170", "Which kind of animals are shown?", "どの種類の動物が写っていますか？", "Insects|昆虫", ["Birds|鳥", "Fish|魚", "Mammals|哺乳類"], tags=["classify", "animal"])
colour("h0170", "the background", "背景", "purple", ["green", "blue", "white"], tags=("colour", "attribute"))
TYPE("h0172", "space", ["photo", "painting", "map"], diff="medium")
TYPE("h0173", "diagram", ["photo", "painting", "satellite"], diff="medium")
TYPE("h0174", "painting", ["photo", "diagram", "satellite"])
Q("h0174", "What is the central woman standing on?", "中央の女性は何の上に立っていますか？", "A shell|貝殻",
  ["A boat|舟", "A rock|岩", "A horse|馬"], tags=["detail"], diff="medium")
Q("h0175", "Which animal is shown?", "どの動物が写っていますか？", "Clownfish|カクレクマノミ", ["Shark|サメ", "Seal|アザラシ", "Octopus|タコ"], tags=["classify", "animal"])
colour("h0175", "the fish", "魚", "orange", ["blue", "green", "black"], tags=("colour", "attribute"))
Q("h0177", "What is shown?", "何が写っていますか？", "A marble statue|大理石像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"])
Q("h0178", "Which language is the text written in?", "文章はどの言語で書かれていますか？", "Latin|ラテン語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
TYPE("h0179", "painting", ["photo", "diagram", "satellite"])
Q("h0180", "Which plant is shown?", "どの植物が写っていますか？", "Cucumber|キュウリ", ["Tomato|トマト", "Corn|トウモロコシ", "Wheat|小麦"], tags=["classify", "plant"], diff="medium")
N("h0180", "There are yellow flowers on the plant", "植物に黄色い花が咲いている", True, tags=["attribute"])
Q("h0181", "Which sweet liquid is in the jar?", "瓶に入っている甘い液体はどれですか？", "Honey|はちみつ",
  ["Soy sauce|醤油", "Milk|牛乳", "Olive oil|オリーブオイル"], tags=["classify", "food"], diff="medium")
Q("h0183", "Which animal is shown?", "どの動物が写っていますか？", "Jaguar|ジャガー", ["Zebra|シマウマ", "Giraffe|キリン", "Penguin|ペンギン"], tags=["classify", "animal"])
N("h0183", "The animal has spots on its coat", "動物の毛に斑点がある", True, tags=["attribute"])
Q("h0185", "Which mountain appears in the distance?", "遠くに見える山はどれですか？", "Mount Fuji|富士山",
  ["Mount Everest|エベレスト", "Mont Blanc|モンブラン", "Kilimanjaro|キリマンジャロ"], tags=["detail"], diff="hard")
TYPE("h0187", "space", ["photo", "painting", "map"], diff="medium")
Q("h0188", "What is shown in this aerial view?", "この空撮写真には何が写っていますか？", "A highway interchange|高速道路のインターチェンジ",
  ["A river delta|河川の三角州", "A railway station|鉄道駅", "An airport runway|空港の滑走路"], tags=["scene"], diff="medium")
Q("h0189", "What is the title printed on this book cover?", "この本の表紙に印刷されている題名は何ですか？", "The Sound and the Fury|響きと怒り",
  ["Moby-Dick|白鯨", "The Great Gatsby|グレート・ギャツビー", "Hamlet|ハムレット"], tags=["ocr", "book"], diff="medium")
Q("h0190", "What are the two people doing?", "2 人は何をしていますか？", "Talking in a TV studio|テレビスタジオで話している",
  ["Playing sports|スポーツをしている", "Cooking|料理している", "Swimming|泳いでいる"], tags=["action"], diff="medium")
Q("h0191", "What tool is the person using?", "人は何の道具を使っていますか？", "A pipette|ピペット",
  ["A hammer|ハンマー", "A paintbrush|絵筆", "A fishing rod|釣り竿"], tags=["detail"], diff="medium")
N("h0191", "The person is wearing a white coat", "人は白衣を着ている", True)
Q("h0192", "Which language is the text written in?", "文章はどの言語で書かれていますか？", "Latin|ラテン語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
Q("h0195", "What kind of writing surface is this?", "これはどんな書写材料ですか？", "Papyrus|パピルス",
  ["Plastic|プラスチック", "Metal|金属", "Glass|ガラス"], tags=["classify", "object"], diff="medium")
TYPE("h0196", "painting", ["photo", "diagram", "satellite"])
TYPE("h0199", "painting", ["photo", "diagram", "satellite"])
TYPE("h0200", "space", ["photo", "painting", "map"], diff="medium")
Q("h0203", "Which animal is on the leaf?", "葉の上にいる動物はどれですか？", "A tick|マダニ",
  ["A butterfly|チョウ", "A bee|ミツバチ", "A frog|カエル"], tags=["classify", "animal"], diff="hard")
Q("h0204", "What is shown?", "何が写っていますか？", "A sculpture|彫刻",
  ["A painting|絵画", "A photograph of a person|人物写真", "A building|建物"], tags=["classify", "object"])
Q("h0207", "What is the title printed on this page?", "このページに印刷されている題名は何ですか？", "Shake-speares Sonnets|シェイクスピアのソネット",
  ["Hamlet|ハムレット", "Macbeth|マクベス", "Othello|オセロー"], tags=["ocr", "book"], diff="medium")
TYPE("h0208", "map", ["photo", "painting", "satellite"])
Q("h0208", "Which sea is labelled at the upper right?", "右上に名前が書かれている海はどれですか？", "Sea of Marmara|マルマラ海",
  ["Black Sea|黒海", "Red Sea|紅海", "Baltic Sea|バルト海"], tags=["ocr", "map"], diff="hard")
Q("h0210", "What is written at the top of the poster?", "ポスターの上部には何と書かれていますか？", "THE HIGH ROLLERS",
  ["THE GREAT SHOW", "LAST CHANCE", "GRAND CIRCUS"], tags=["ocr", "poster"], diff="hard")
TYPE("h0211", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0212", "Which sport is shown?", "どのスポーツの道具ですか？", "Darts|ダーツ", ["Archery|アーチェリー", "Golf|ゴルフ", "Billiards|ビリヤード"], tags=["classify", "sport"])
N("h0212", "There are three darts in the picture", "写真にダーツの矢が 3 本ある", True, tags=["count"], diff="medium")
Q("h0213", "What covers the upper slopes of the mountain?", "山の上のほうを覆っているものは何ですか？", "Snow|雪",
  ["Sand|砂", "Grass|草", "Water|水"], tags=["scene"])
TYPE("h0214", "page", ["photo", "satellite", "map"], diff="medium")
Q("h0215", "Which natural phenomenon is shown?", "どの自然現象が写っていますか？", "Lightning|稲妻",
  ["A rainbow|虹", "An aurora|オーロラ", "A tornado|竜巻"], tags=["classify", "scene"])
Q("h0216", "What is shown on the page?", "ページには何が書かれていますか？", "A computer program listing|プログラムのリスト",
  ["A shopping list|買い物リスト", "A map|地図", "A poem|詩"], tags=["classify", "object"], diff="medium")
Q("h0217", "Which food is shown?", "写っている食べ物はどれですか？", "Porridge|おかゆ（オートミール）", ["Pizza|ピザ", "Sushi|寿司", "A hamburger|ハンバーガー"], tags=["classify", "food"], diff="medium")
Q("h0218", "What animal stands next to the statue?", "像のそばにいる動物はどれですか？", "A deer|シカ",
  ["A dog|犬", "A lion|ライオン", "A horse|馬"], tags=["detail"], diff="medium")
Q("h0219", "What word is spelled out with flowers at the bottom?", "下の方に花で綴られている言葉はどれですか？", "BEATLES",
  ["ROLLING", "QUEEN", "ABBA"], tags=["ocr"], diff="medium")
