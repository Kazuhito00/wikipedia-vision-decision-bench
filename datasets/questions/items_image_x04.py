# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0061-x0100 (satellites, rocket launches, the Moon, planets, nebulae, galaxies)."""
from templates import Q, N, TYPE

Q("x0061", "What kind of image is this?", "これはどんな種類の画像ですか？", "A line diagram with labels|ラベル付きの線画の図",
  ["A photograph of a city|都市の写真", "A satellite photo of a forest|森の衛星写真", "A painting of a harbour|港の絵画"], tags=["image-type", "sci"], diff="medium")
N("x0061", "The word NASA appears in the diagram", "図の中に「NASA」の文字がある", True, tags=["ocr", "sci"], diff="hard")
Q("x0063", "What is above the clouds?", "雲の上にあるものは何ですか？", "A spacecraft or satellite|宇宙機・人工衛星", ["A kite|凧", "A hot-air balloon|熱気球", "A bird|鳥"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0065", "What is the aircraft doing?", "航空機は何をしていますか？", "Taking off with a steep climb|急角度で離陸している",
  ["Landing|着陸している", "Refuelling in the air|空中給油している", "Parked on the ground|地上に駐機している"], tags=["action", "sci"], diff="medium")
Q("x0067", "What does the long curved white trail in the sky come from?", "空に伸びる長く曲がった白い筋は何によるものですか？", "A rocket launch|ロケットの打ち上げ",
  ["A comet|彗星", "Smoke from a chimney|煙突の煙", "A kite string|凧の糸"], tags=["classify", "sci"], diff="medium")
N("x0068", "The large aircraft is propeller-driven", "大きな航空機はプロペラ機である", False, tags=["attribute", "sci"], diff="medium")
Q("x0070", "What rises straight up from near the water's edge?", "水際から真っすぐ立ち上っているものは何ですか？", "A rocket's exhaust trail|ロケットの噴煙",
  ["A fountain|噴水", "A flagpole|旗竿", "A tree|木"], tags=["detail", "scene", "sci"], diff="hard")
Q("x0072", "What is happening in front of the house?", "家の前で何が起きていますか？", "A small rocket is being launched|小さなロケットが打ち上げられている",
  ["A barbecue|バーベキュー", "A bonfire|焚き火", "A car is being washed|洗車している"], tags=["action", "sci"], diff="hard")
TYPE("x0073", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("x0073", "What object is in the sky at the top of the picture?", "絵の上部の空にあるものは何ですか？", "A crescent moon|三日月", ["The sun|太陽", "A full moon|満月", "A comet|彗星"],
  tags=["detail", "sci"], diff="medium")
Q("x0074", "What kind of picture is this?", "これはどんな絵・図ですか？", "An old chart with astronomical diagrams|天文の図が並んだ古い図版",
  ["A modern photograph of a street|現代の街角の写真", "A satellite photo|衛星写真", "A restaurant menu|レストランのメニュー"], tags=["image-type", "sci"], diff="medium")
Q("x0075", "Which spacecraft name is given in the on-screen text?", "画面上の文字に書かれている宇宙船の名前はどれですか？", "Orion", ["Apollo", "Soyuz", "Dragon"],
  tags=["ocr", "sci"], diff="hard")
Q("x0078", "Which phase of the Moon is shown?", "月のどの満ち欠けが写っていますか？", "A half Moon|半月", ["A full Moon|満月", "A new Moon|新月", "A thin crescent|細い三日月"],
  tags=["detail", "sci"], diff="medium")
N("x0078", "The picture shows two views of the Moon side by side", "写真には月の像が 2 つ並んでいる", True, tags=["count", "sci"], diff="medium")
Q("x0079", "Which phase of the Moon is shown?", "月のどの満ち欠けが写っていますか？", "More than half lit (gibbous)|半分より多く照らされている月",
  ["A thin crescent|細い三日月", "A new Moon|新月", "A total lunar eclipse|皆既月食"], tags=["detail", "sci"], diff="hard")
Q("x0081", "What do the two circular drawings show?", "2 つの円形の図は何を表していますか？", "Orbits or paths around a centre|中心の周りの軌道や経路",
  ["Slices of fruit|切った果物", "Clock faces|時計の文字盤", "Car wheels|車の車輪"], tags=["detail", "sci"], diff="hard")
Q("x0082", "Which planet with prominent rings is in the middle of the picture?", "写真の中ほどにある、輪の目立つ惑星はどれですか？", "Saturn|土星",
  ["Mars|火星", "Venus|金星", "Earth|地球"], tags=["classify", "space", "sci"], diff="easy")
N("x0082", "Four planets are shown", "惑星が 4 つ写っている", True, tags=["count", "sci"], diff="medium")
Q("x0084", "Which body is the largest in the picture?", "写真でいちばん大きく写っている天体はどれですか？", "Earth|地球", ["The Moon|月", "Mars|火星", "Mercury|水星"],
  tags=["detail", "space", "sci"], diff="medium")
Q("x0085", "Which labelled body has the tallest bar in the chart?", "グラフでいちばん高い棒のラベルはどれですか？", "Neptune", ["Jupiter", "Mars", "Pluto"],
  tags=["ocr", "sci"], diff="hard")
N("x0085", "The vertical axis of the chart uses a logarithmic scale", "グラフの縦軸は対数目盛りである", True, tags=["detail", "sci"], diff="hard")
Q("x0086", "What do the circles in this picture show?", "この図の円は何を表していますか？", "Cross-sections of planets with their layers|層構造を示した惑星の断面",
  ["Maps of continents|大陸の地図", "Menus|メニュー", "Coins|硬貨"], tags=["detail", "sci"], diff="medium")
Q("x0089", "What name appears in the caption of the image?", "画像のキャプションに書かれている名前はどれですか？", "Black Widow Nebula",
  ["Orion Nebula", "Crab Nebula", "Horsehead Nebula"], tags=["ocr", "sci"], diff="hard")
Q("x0093", "Which telescope is named in the caption?", "キャプションに書かれている望遠鏡はどれですか？", "Spitzer Space Telescope|スピッツァー宇宙望遠鏡",
  ["Hubble Space Telescope|ハッブル宇宙望遠鏡", "Kepler|ケプラー", "Webb|ウェッブ"], tags=["ocr", "sci"], diff="hard")
Q("x0090", "What shape is the blue structure around the central star?", "中心の星の周りの青い構造はどんな形ですか？", "A ring|輪", ["A cross|十字", "A triangle|三角形", "A spiral arm|渦巻きの腕"],
  tags=["detail", "sci"], diff="medium")
TYPE("x0091", "space", ["photo", "painting", "map"], diff="medium")
Q("x0092", "Which designation appears at the top of the text panel?", "文字パネルの先頭に出ている名称はどれですか？", "RCW 135", ["NGC 7000", "M 31", "IC 1396"],
  tags=["ocr", "sci"], diff="hard")
Q("x0095", "What is the large round cluster of stars in the upper part?", "上部の大きな丸い星の集まりは何ですか？", "A globular cluster|球状星団",
  ["A spiral galaxy|渦巻銀河", "A comet|彗星", "The Milky Way band|天の川の帯"], tags=["classify", "space", "sci"], diff="hard")
TYPE("x0096", "space", ["photo", "painting", "map"], diff="medium")
Q("x0098", "Which designation is written in yellow next to the galaxy?", "銀河の横に黄色で書かれている名称はどれですか？", "IC 1496", ["IC 1501", "NGC 1496", "M 1496"],
  tags=["ocr", "sci"], diff="hard")
Q("x0099", "Into how many panels is the picture divided?", "画像はいくつのパネルに分かれていますか？", "Four|4 つ", ["Two|2 つ", "Three|3 つ", "Six|6 つ"],
  tags=["count", "sci"], diff="medium")
Q("x0100", "Which designation is written in yellow next to the galaxy?", "銀河の横に黄色で書かれている名称はどれですか？", "IC 1501", ["IC 1496", "NGC 1501", "IC 5010"],
  tags=["ocr", "sci"], diff="hard")
