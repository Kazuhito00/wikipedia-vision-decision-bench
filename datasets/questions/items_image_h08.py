# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0401-h0450 (E / J = used by one wiki only; see items_image_h07.py).
Surgery, punishment, wartime violence and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour, count

Q("h0401", "What is on the leaf?", "葉の上にあるものは何ですか？", "A water droplet|水滴", ["A ladybug|てんとう虫", "A feather|羽根", "A coin|硬貨"], tags=["detail"], diff="medium")
Q("h0402", "Which planet is shown?", "どの惑星が写っていますか？", "Venus|金星", ["Mars|火星", "Jupiter|木星", "Saturn|土星"], tags=["classify", "space"], diff="hard")
TYPE("h0403", "map", ["photo", "painting", "satellite"])
Q("h0406", "What are the men standing next to?", "男性たちは何のそばに立っていますか？", "An early airplane|初期の飛行機",
  ["A boat|舟", "A train|電車", "A tractor|トラクター"], tags=["detail"], diff="medium")
N("h0406", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0407", "What is the object?", "これは何ですか？", "A brick|レンガ", ["A loaf of bread|パン", "A stone ball|石の球", "A book|本"], tags=["classify", "object"])
Q("h0408", "Which fruit grows on this tree?", "この木になっている果物はどれですか？", "Apples|りんご",
  ["Oranges|オレンジ", "Bananas|バナナ", "Grapes|ぶどう"], tags=["classify", "food"])
Q("h0409", "What large feature of ice and rock is shown?", "氷と岩でできた大きな地形は何ですか？", "A glacier|氷河",
  ["A river|川", "A road|道路", "A canal|運河"], tags=["scene"], diff="medium")
TYPE("h0410", "map", ["photo", "painting", "satellite"])
Q("h0411", "What does the chart show?", "この図は何を示していますか？", "Weather and air pressure|天気・気圧",
  ["Bus routes|バス路線", "Election results|選挙結果", "Population density|人口密度"], tags=["diagram"], diff="hard")
TYPE("h0412", "painting", ["photo", "diagram", "satellite"])
Q("h0415", "Which animal is shown?", "どの動物が写っていますか？", "Owl|フクロウ", ["Eagle|ワシ", "Duck|アヒル", "Penguin|ペンギン"], tags=["classify", "animal"], diff="medium")
TYPE("h0416", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("h0417", "What does the poster say at the bottom?", "ポスターの下部には何と書かれていますか？", "Be Patriotic",
  ["Buy Bonds", "Save Water", "Join Now"], tags=["ocr", "poster"], diff="medium")
Q("h0418", "Which vegetable is shown?", "どの野菜が写っていますか？", "Cabbage|キャベツ", ["Carrots|にんじん", "Potatoes|じゃがいも", "Tomatoes|トマト"], tags=["classify", "food"])
TYPE("h0419", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0420", "Which animal is shown?", "どの動物が写っていますか？", "Snake|ヘビ", ["Frog|カエル", "Lizard|トカゲ", "Worm|ミミズ"], tags=["classify", "animal"], diff="medium")
N("h0421", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0422", "Which continent is mostly shown?", "主に写っている大陸はどれですか？", "Europe|ヨーロッパ",
  ["Africa|アフリカ", "South America|南アメリカ", "Australia|オーストラリア"], tags=["geo"], diff="medium")
Q("h0424", "What do the large words on the poster say?", "ポスターの大きな文字は何と書かれていますか？", "DON'T MIX 'EM",
  ["DRINK UP", "BUY NOW", "KEEP OUT"], tags=["ocr", "poster"], diff="medium")
N("h0424", "A skull is drawn on the poster", "ポスターにドクロが描かれている", True, tags=["presence"])
Q("h0425", "Which book series is printed on the spines?", "背表紙に書かれている本のシリーズはどれですか？", "The Chronicles of Narnia|ナルニア国物語",
  ["Harry Potter|ハリー・ポッター", "The Lord of the Rings|指輪物語", "Sherlock Holmes|シャーロック・ホームズ"], tags=["ocr", "book"], diff="medium")
Q("h0426", "What condition are the trees in?", "木々はどんな状態ですか？", "Bare and dead|葉がなく枯れている",
  ["Covered in flowers|花で覆われている", "Full of green leaves|緑の葉でいっぱい", "Heavy with fruit|果実がたわわに実っている"], tags=["scene"], diff="medium")
Q("h0427", "What natural rock feature is shown?", "どんな岩の地形が写っていますか？", "An arch|アーチ状の岩",
  ["A waterfall|滝", "A glacier|氷河", "A volcano|火山"], tags=["classify", "scene"])
colour("h0427", "the rock arch", "岩のアーチ", "orange", ["blue", "green", "white"], tags=("colour", "attribute"))
Q("h0428", "Which animal is shown?", "どの動物が写っていますか？", "Whale|クジラ", ["Shark|サメ", "Seal|アザラシ", "Turtle|カメ"], tags=["classify", "animal"], diff="medium")
N("h0428", "There are two whales in the picture", "写真にクジラが 2 頭いる", True, tags=["count"], diff="hard")
Q("h0429", "What kind of artwork is this?", "これはどんな種類の作品ですか？", "An embroidered tapestry|刺繍のタペストリー",
  ["A photograph|写真", "An oil painting|油彩画", "A map|地図"], tags=["image-type"], diff="hard")
Q("h0430", "Which animal is shown?", "どの動物が写っていますか？", "Crane (bird)|ツル", ["Duck|アヒル", "Penguin|ペンギン", "Owl|フクロウ"], tags=["classify", "animal"], diff="medium")
Q("h0434", "What is happening?", "何が起きていますか？", "A rocket is launching|ロケットが打ち上げられている",
  ["A plane is landing|飛行機が着陸している", "A ship is sailing|船が出航している", "A train is departing|電車が出発している"], tags=["scene"])
count("h0439", "bird", 2, options=("one", "two", "three"))
Q("h0443", "What is shown?", "何が写っていますか？", "A marble bust|大理石の胸像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"])
Q("h0444", "Which language is the title page written in?", "表紙はどの言語で書かれていますか？", "Latin|ラテン語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
Q("h0446", "What is on the wrist?", "手首には何がありますか？", "A wristwatch|腕時計", ["A bracelet|ブレスレット", "A ring|指輪", "A scarf|スカーフ"], tags=["classify", "object"])
N("h0446", "The watch face is multicoloured", "時計の文字盤は多色である", True, tags=["attribute"], diff="medium")
Q("h0447", "What shapes are painted on the rock?", "岩に描かれている形は何ですか？", "Hands|手形", ["Houses|家", "Flowers|花", "Boats|舟"], tags=["detail"], diff="medium")
TYPE("h0448", "space", ["photo", "painting", "map"], diff="medium")
Q("h0449", "Which animal is shown?", "どの動物が写っていますか？", "Wolverine|クズリ", ["Cat|猫", "Rabbit|ウサギ", "Horse|馬"], tags=["classify", "animal"], diff="hard")
