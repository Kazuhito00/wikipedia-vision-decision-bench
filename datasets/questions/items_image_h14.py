# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0592-h0650 (pictures used by the English article only).
Battle scenes, violence and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0592", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0592", "Which mountain range is shown?", "写っている山脈はどれですか？", "The Alps|アルプス山脈",
  ["The Andes|アンデス山脈", "The Rockies|ロッキー山脈", "The Himalayas|ヒマラヤ山脈"], tags=["geo"], diff="hard")
TYPE("h0594", "drawing", ["photo", "satellite", "map"])
Q("h0595", "What is the person doing?", "人は何をしていますか？", "Painting with watercolours|水彩画を描いている",
  ["Playing the piano|ピアノを弾いている", "Cooking|料理している", "Cutting hair|髪を切っている"], tags=["action"])
Q("h0602", "What is the person doing?", "人は何をしていますか？", "Performing acrobatics on red silks|赤い布でアクロバットをしている",
  ["Swimming|泳いでいる", "Playing tennis|テニスをしている", "Riding a bicycle|自転車に乗っている"], tags=["action"], diff="medium")
colour("h0602", "the silks", "布", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
TYPE("h0606", "painting", ["photo", "diagram", "satellite"])
TYPE("h0608", "map", ["photo", "painting", "satellite"])
Q("h0610", "What kind of scene is this?", "これはどんな景色ですか？", "A busy city street|にぎやかな市街地の通り",
  ["A quiet forest|静かな森", "A desert|砂漠", "A farm field|畑"], tags=["scene"])
N("h0610", "There is a railway or monorail above the street", "通りの上に高架の鉄道が走っている", True, tags=["presence"], diff="medium")
TYPE("h0613", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("h0615", "What are the aircraft?", "写っている航空機は何ですか？", "Fighter planes|戦闘機", ["Passenger airliners|旅客機", "Helicopters|ヘリコプター", "Hot-air balloons|熱気球"], tags=["classify", "vehicle"], diff="medium")
N("h0616", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0618", "What is growing in the pot?", "鉢で育っているものは何ですか？", "A young plant|若い植物", ["A cactus|サボテン", "A mushroom|キノコ", "A toy|おもちゃ"], tags=["classify", "plant"])
colour("h0620", "the largest spheres", "一番大きな球", "purple", ["white", "blue", "green"], tags=("colour", "attribute"))
Q("h0622", "Which instrument is shown?", "どの楽器が写っていますか？", "A sitar|シタール", ["A violin|バイオリン", "A trumpet|トランペット", "A piano|ピアノ"], tags=["classify", "object"], diff="hard")
Q("h0627", "Which kind of animals are shown?", "どの種類の動物が写っていますか？", "Snails and sea slugs|カタツムリ・ナメクジの仲間",
  ["Birds|鳥", "Fish|魚", "Dogs|犬"], tags=["classify", "animal"], diff="medium")
TYPE("h0628", "satellite", ["photo", "painting", "diagram"], diff="medium")
TYPE("h0631", "painting", ["photo", "diagram", "satellite"])
TYPE("h0632", "map", ["photo", "painting", "satellite"])
Q("h0633", "Which animal is shown?", "どの動物が写っていますか？", "A ladybug|てんとう虫", ["A bee|ミツバチ", "A butterfly|チョウ", "An ant|アリ"], tags=["classify", "animal"])
colour("h0633", "the insect's wing cover", "虫の背中の殻", "red", ["blue", "green", "white"], tags=("colour", "attribute"))
Q("h0636", "What kind of scene is this?", "これはどんな景色ですか？", "A waterfront city|海辺の都市", ["A snowy mountain|雪山", "A desert|砂漠", "A forest|森"], tags=["scene"])
Q("h0642", "What do the objects show?", "並んでいる物は何を示していますか？", "How mobile phones changed over time|携帯電話の変化",
  ["Kinds of fruit|果物の種類", "Phases of the moon|月の満ち欠け", "Types of shoes|靴の種類"], tags=["classify", "object"], diff="medium")
Q("h0646", "What is the object made of?", "この物は何でできていますか？", "Clay|粘土", ["Metal|金属", "Paper|紙", "Glass|ガラス"], tags=["classify", "object"], diff="medium")
N("h0648", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0650", "What is the person pulling?", "人は何を引いていますか？", "A sled|そり", ["A cart|荷車", "A boat|舟", "A bicycle|自転車"], tags=["detail"])
N("h0650", "There is snow on the ground", "地面に雪がある", True, tags=["scene"])
