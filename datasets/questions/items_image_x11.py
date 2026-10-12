# -*- coding: utf-8 -*-
"""Expansion set, field "life" (daily life and society): x0278-x0317 -- restaurants, bakeries, pharmacies, libraries,
hospitals. Pictures where a person (a child, a patient, a shopper) is the subject were not used."""
from templates import Q, N, TYPE

Q("x0278", "What colour is the long building?", "細長い建物は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Yellow|黄色"], tags=["colour", "life"], diff="easy")
Q("x0280", "What name is on the shop sign?", "店の看板に書かれている名前はどれですか？", "SYRIANA", ["ARIANA", "SIRENA", "SYLVIA"], tags=["ocr", "life"], diff="hard")
N("x0282", "Cutlery stands in a container on the table", "テーブルの上の容器にカトラリーが立てられている", True, tags=["detail", "life"], diff="medium")
Q("x0284", "What does the glass counter display?", "ガラスのカウンターには何が並んでいますか？", "Cakes and pastries|ケーキや菓子パン", ["Shoes|靴", "Books|本", "Flowers|花"],
  tags=["classify", "food", "life"], diff="easy")
Q("x0285", "What colour are the walls?", "壁は何色ですか？", "Yellow|黄色", ["Blue|青", "Red|赤", "White|白"], tags=["colour", "life"], diff="easy")
Q("x0285", "What stands on the shelves?", "棚の上に並んでいるものは何ですか？", "Bottles and jars|瓶", ["Shoes|靴", "Books|本", "Cameras|カメラ"],
  tags=["classify", "object", "life"], diff="medium")
Q("x0286", "What part of which equipment is this?", "これはどの機器のどの部品ですか？", "The dough hook of a mixer|ミキサーの生地用フック",
  ["The handle of a bicycle|自転車のハンドル", "The handle of a door|ドアの取っ手", "A fishing hook|釣り針"], tags=["detail", "object", "life"], diff="hard")
Q("x0289", "What is the name on the shop sign?", "店の看板に書かれている名前はどれですか？", "Catherine's Bakery", ["Charlie's Bakery", "Cathy's Cafe", "Katherine's Books"],
  tags=["ocr", "life"], diff="medium")
Q("x0290", "What kind of shop is this?", "これはどんな店ですか？", "A pastry and chocolate shop|ケーキとチョコレートの店", ["A shoe shop|靴屋", "A bank|銀行", "A pharmacy|薬局"],
  tags=["classify", "life"], diff="medium")
Q("x0291", "Which word is on the label of the middle bottle?", "中央の瓶のラベルに書かれている語はどれですか？", "COFFEA", ["THEA", "CACAO", "MENTHA"], tags=["ocr", "life"], diff="hard")
Q("x0292", "What animal pulls the carriage?", "馬車を引いている動物は何ですか？", "A horse|馬", ["A dog|犬", "An ox|牛", "A donkey|ロバ"], tags=["classify", "animal", "life"], diff="medium")
Q("x0294", "What kind of place is shown in this old picture?", "この古い絵に描かれているのはどんな場所ですか？", "An old pharmacy with shelves of jars|薬の壺が並ぶ古い薬局",
  ["A fish market|魚市場", "A railway station|駅", "A school classroom|教室"], tags=["classify", "scene", "life"], diff="medium")
Q("x0296", "Which of these words appears on the signs?", "標識に書かれている語は次のうちどれですか？", "Pharmacy", ["Bakery", "Library", "Laundry"], tags=["ocr", "life"], diff="medium")
N("x0299", "The corridor in the picture has arched vaults", "写真の廊下にはアーチ形の天井がある", True, tags=["scene", "life"], diff="medium")
Q("x0301", "What kind of place is this?", "ここはどんな場所ですか？", "A library|図書館", ["A supermarket|スーパーマーケット", "A pharmacy|薬局", "A gym|ジム"],
  tags=["classify", "scene", "life"], diff="easy")
Q("x0302", "What does the sign say?", "看板には何と書かれていますか？", "WELCOME TO THE LIBRARY", ["WELCOME TO THE GYM", "NO ENTRY", "CLOSED FOR LUNCH"],
  tags=["ocr", "life"], diff="easy")
Q("x0303", "What kind of place do the gold characters name?", "金色の文字が示している場所はどれですか？", "A library|図書館", ["A hospital|病院", "A school|学校", "A bank|銀行"],
  tags=["ocr", "language", "life"], diff="hard")
Q("x0304", "What kind of room is this?", "ここはどんな部屋ですか？", "A large library reading room|大きな図書館の閲覧室", ["A church|教会", "A railway workshop|鉄道工場", "A ballroom|舞踏室"],
  tags=["classify", "scene", "life"], diff="hard")
Q("x0307", "Which hospital name is written in the caption?", "キャプションに書かれている病院名はどれですか？", "General Hospital Nafada",
  ["Central Hospital Kano", "General Hospital Lagos", "Regional Clinic Abuja"], tags=["ocr", "life"], diff="hard")
Q("x0308", "Which place is named in the caption?", "キャプションに書かれている地名はどれですか？", "West Maitland", ["Sydney", "Perth", "Melbourne"], tags=["ocr", "life"], diff="hard")
Q("x0311", "What kind of institution does the caption name?", "キャプションが示している施設はどれですか？", "A hospital and sanatorium|病院・療養所",
  ["A university|大学", "A railway station|駅", "A prison|刑務所"], tags=["ocr", "life"], diff="hard")
