# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0451-h0500 (E / J = used by one wiki only; see items_image_h07.py).
Pictures of torture, refugees, nudity and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour, count

S("h0452", "skyscraper", "structure")
Q("h0454", "What is the object?", "これは何ですか？", "A chair|椅子", ["A lamp|ランプ", "A piano|ピアノ", "A bottle|瓶"], tags=["classify", "object"])
colour("h0454", "the seat cushion", "座面", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
Q("h0455", "What is shown?", "何が写っていますか？", "A marble bust|大理石の胸像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"])
TYPE("h0456", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0459", "What are these small objects?", "これらの小さな物は何ですか？", "Electronic components|電子部品",
  ["Candies|お菓子", "Tools|工具", "Seeds|種"], tags=["classify", "object"])
Q("h0460", "What covers the ground?", "地面を覆っているものは何ですか？", "Snow|雪", ["Sand|砂", "Grass|草", "Fallen leaves|落ち葉"], tags=["scene"])
Q("h0461", "What kind of facility is this?", "これはどんな施設ですか？", "A grain storage facility with silos|サイロのある穀物施設",
  ["A hospital|病院", "A stadium|スタジアム", "A shopping mall|ショッピングモール"], tags=["scene"], diff="medium")
TYPE("h0462", "map", ["photo", "painting", "satellite"])
Q("h0463", "What kind of room is this?", "ここはどんな部屋ですか？", "A control room|制御室", ["A kitchen|台所", "A classroom|教室", "A bedroom|寝室"], tags=["scene"], diff="medium")
TYPE("h0464", "painting", ["photo", "diagram", "satellite"], diff="medium")
Q("h0465", "In which language is the poster written?", "ポスターはどの言語で書かれていますか？", "Russian|ロシア語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"])
TYPE("h0466", "painting", ["photo", "diagram", "satellite"], diff="medium")
Q("h0467", "What does the painting show?", "この絵には何が描かれていますか？", "A table with food|食べ物が並んだ食卓",
  ["A battle|戦い", "A seascape|海の景色", "A portrait of a king|王の肖像"], tags=["classify", "scene"])
Q("h0474", "What does the poster say?", "ポスターには何と書かれていますか？", "I WANT YOU FOR U.S. ARMY",
  ["BUY WAR BONDS", "JOIN THE NAVY", "VOTE TODAY"], tags=["ocr", "poster"])
Q("h0475", "What kind of site is this?", "これはどんな場所ですか？", "A quarry|採石場", ["A farm|農場", "A beach|ビーチ", "A parking lot|駐車場"], tags=["scene"], diff="hard")
TYPE("h0476", "satellite", ["photo", "painting", "diagram"], diff="medium")
S("h0477", "eagle", "animal", diff="medium")
count("h0477", "eagle", 2, options=("one", "two", "three"))
Q("h0478", "Which continent is shown on the map?", "地図に描かれている大陸はどれですか？", "South America|南アメリカ",
  ["Africa|アフリカ", "Europe|ヨーロッパ", "Asia|アジア"], tags=["geo", "map"])
colour("h0479", "the flower", "花", "purple", ["red", "yellow", "white"], tags=("colour", "attribute"))
Q("h0480", "In which language is the title page written?", "表紙はどの言語で書かれていますか？", "Russian|ロシア語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0482", "Which sport is drawn?", "どのスポーツが描かれていますか？", "Archery|弓術（アーチェリー）", ["Swimming|水泳", "Tennis|テニス", "Football|サッカー"], tags=["classify", "sport"], diff="medium")
TYPE("h0483", "painting", ["photo", "diagram", "satellite"])
Q("h0488", "Which animal is shown?", "どの動物が写っていますか？", "Deer|シカ", ["Horse|馬", "Cow|牛", "Sheep|羊"], tags=["classify", "animal"], diff="medium")
N("h0488", "The animal has antlers", "動物には枝角がある", True, tags=["attribute"])
Q("h0490", "Which vegetable is shown?", "どの野菜が写っていますか？", "Potatoes|じゃがいも", ["Carrots|にんじん", "Tomatoes|トマト", "Apples|りんご"], tags=["classify", "food"])
TYPE("h0491", "satellite", ["photo", "painting", "diagram"], diff="medium")
N("h0491", "Most of the land in the picture is desert", "写真の陸地の大部分は砂漠である", True, tags=["scene"], diff="medium")
Q("h0492", "What kind of landscape is this?", "これはどんな景色ですか？", "A mountain lake|山の湖", ["A city|都市", "A desert|砂漠", "A farm field|畑"], tags=["scene"])
N("h0494", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0495", "Which country is shown on the map?", "地図に描かれている国はどれですか？", "Italy|イタリア",
  ["Spain|スペイン", "Greece|ギリシャ", "Japan|日本"], tags=["geo", "map"], diff="medium")
TYPE("h0496", "painting", ["photo", "diagram", "satellite"])
Q("h0497", "Which animals surround the man?", "男性を囲んでいる動物はどれですか？", "Lions|ライオン", ["Wolves|オオカミ", "Horses|馬", "Cows|牛"], tags=["classify", "animal"])
TYPE("h0498", "satellite", ["photo", "painting", "diagram"], diff="medium")
TYPE("h0499", "page", ["photo", "map", "satellite"], diff="medium")
Q("h0500", "In which language is the title page written?", "表紙はどの言語で書かれていますか？", "Spanish|スペイン語",
  ["English|英語", "Italian|イタリア語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
