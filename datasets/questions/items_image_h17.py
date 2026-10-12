# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0761-h0800 (pictures used by the Japanese article only), written with the
"somewhat demanding" policy: look-alike distractors, fine-grained identification, printed words and symbols.
War pictures, propaganda, nudity and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h0761", "Which plant is illustrated?", "どの植物が描かれていますか？", "Parsnip|パースニップ",
  ["Carrot|にんじん", "Radish|大根", "Ginger|ショウガ"], tags=["classify", "plant"], diff="hard")
Q("h0766", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Gauguin|ゴーギャン",
  ["Van Gogh|ゴッホ", "Monet|モネ", "Matisse|マティス"], tags=["art"], diff="hard")
Q("h0769", "What is the woman using to take a picture?", "女性は何で写真を撮っていますか？", "A compact digital camera|コンパクトデジタルカメラ",
  ["A smartphone|スマートフォン", "A video camcorder|ビデオカメラ", "A film SLR camera|フィルム一眼レフ"], tags=["detail"], diff="hard")
Q("h0772", "Which instrument is shown?", "どの楽器が写っていますか？", "A pipe organ|パイプオルガン",
  ["A harpsichord|チェンバロ", "A grand piano|グランドピアノ", "An accordion|アコーディオン"], tags=["classify", "object"], diff="medium")
Q("h0773", "Which part of the world is shown?", "写っているのはどの海域ですか？", "The Strait of Hormuz area|ホルムズ海峡付近",
  ["The Strait of Gibraltar|ジブラルタル海峡", "The Bering Strait|ベーリング海峡", "The Panama Canal|パナマ運河"], tags=["geo"], diff="hard")
Q("h0775", "What is the large animal doing?", "大きな動物は何をしていますか？", "Nursing a piglet|子ブタに乳をやっている",
  ["Fighting another pig|別の豚と戦っている", "Sleeping|眠っている", "Swimming|泳いでいる"], tags=["action"], diff="medium")
Q("h0776", "Which sport is shown?", "どのスポーツですか？", "Road cycling|ロードレース",
  ["Mountain biking|マウンテンバイク", "Triathlon swimming|トライアスロンの水泳", "Motorcycle racing|オートバイレース"], tags=["classify", "sport"], diff="hard")
colour("h0776", "the front rider's jersey", "先頭の選手のジャージ", "orange", ["blue", "green", "white"], tags=("colour", "attribute"))
Q("h0777", "Which two main islands are in the picture?", "写っている主な 2 つの島はどれですか？", "Great Britain and Ireland|グレートブリテン島とアイルランド島",
  ["Honshu and Kyushu|本州と九州", "Sicily and Sardinia|シチリア島とサルデーニャ島", "Cuba and Jamaica|キューバとジャマイカ"], tags=["geo"], diff="hard")
Q("h0778", "Which vehicles are on the road?", "道路を走っている乗り物はどれですか？", "Minibuses and cars|ミニバスと乗用車",
  ["Trams only|路面電車だけ", "Bicycles only|自転車だけ", "Horse carts only|馬車だけ"], tags=["detail"], diff="medium")
Q("h0779", "What does the colour scale show?", "色の目盛りは何を表していますか？", "Water depth|水深",
  ["Temperature|温度", "Rainfall|降水量", "Population|人口"], tags=["ocr", "diagram"], diff="medium")
Q("h0783", "Which insects are illustrated?", "どの昆虫が描かれていますか？", "Flies|ハエ", ["Bees|ミツバチ", "Beetles|甲虫", "Ants|アリ"], tags=["classify", "animal"], diff="medium")
Q("h0785", "What colour is the horse?", "馬は何色ですか？", "Black|黒", ["White|白", "Brown|茶色", "Grey|灰色"], tags=["colour", "attribute"], diff="medium")
N("h0785", "A person is leading the horse", "人が馬を引いている", True, tags=["presence"])
Q("h0788", "Which ancient animals are illustrated?", "どんな古代の動物が描かれていますか？", "Sea scorpions|ウミサソリ",
  ["Dinosaurs|恐竜", "Trilobites|三葉虫", "Mammoths|マンモス"], tags=["classify", "animal"], diff="hard")
Q("h0789", "Which animal is shown?", "どの動物が写っていますか？", "Japanese macaque|ニホンザル",
  ["Orangutan|オランウータン", "Gorilla|ゴリラ", "Chimpanzee|チンパンジー"], tags=["classify", "animal"], diff="hard")
Q("h0791", "Which sport does this equipment belong to?", "この用具はどのスポーツのものですか？", "Field hockey|フィールドホッケー",
  ["Golf|ゴルフ", "Baseball|野球", "Cricket|クリケット"], tags=["classify", "sport"], diff="hard")
Q("h0792", "Which writing system is on the tablet?", "粘土板に書かれている文字体系はどれですか？", "Cuneiform|楔形文字",
  ["Hieroglyphs|ヒエログリフ", "Chinese characters|漢字", "Runes|ルーン文字"], tags=["ocr", "script"], diff="hard")
Q("h0793", "In which language are the labels written?", "ラベルはどの言語で書かれていますか？", "German|ドイツ語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
Q("h0797", "What are the objects?", "これらは何ですか？", "Spools of thread|糸巻き", ["Candles|ろうそく", "Bottles|瓶", "Pipes|パイプ"], tags=["classify", "object"], diff="medium")
Q("h0799", "What are the dark thread-like structures inside the cells?", "細胞の中の黒い糸状の構造は何ですか？", "Chromosomes|染色体",
  ["Bacteria|細菌", "Hairs|毛", "Roots|根"], tags=["classify", "object"], diff="hard")
Q("h0800", "Which moon is shown?", "どの衛星が写っていますか？", "Callisto|カリスト", ["Earth's Moon|月", "Europa|エウロパ", "Titan|タイタン"], tags=["classify", "space"], diff="hard")
