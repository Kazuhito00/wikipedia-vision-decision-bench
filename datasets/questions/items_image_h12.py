# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0601-h0700 (pictures used by the Japanese article only).
Weapons, soldiers, nudity, skin close-ups and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0601", "painting", ["photo", "diagram", "satellite"], diff="medium")
S("h0603", "truck", "vehicle")
colour("h0603", "the truck's cargo box", "トラックの荷台", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
TYPE("h0605", "painting", ["photo", "diagram", "satellite"], diff="medium")
TYPE("h0607", "diagram", ["photo", "painting", "satellite"])
Q("h0609", "What kind of building is this?", "これはどんな建物ですか？", "A Buddhist pagoda temple|仏塔（パゴダ）",
  ["A castle|城", "A lighthouse|灯台", "A windmill|風車"], tags=["classify", "structure"], diff="medium")
N("h0609", "There is a golden dome in the picture", "写真に金色の塔の屋根がある", True, tags=["presence"])
Q("h0614", "What is shown?", "何が写っていますか？", "The Earth seen from space|宇宙から見た地球",
  ["The Moon|月", "Mars|火星", "A basketball|バスケットボール"], tags=["classify", "space"])
Q("h0617", "What weather system is shown?", "どんな気象現象が写っていますか？", "A hurricane (typhoon)|台風（ハリケーン）",
  ["A volcano eruption|火山の噴火", "A forest fire|山火事", "A tornado|竜巻"], tags=["scene"], diff="medium")
TYPE("h0619", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0621", "What stands on the snow?", "雪の上に立っているものは何ですか？", "Flags|旗", ["Trees|木", "Houses|家", "Cars|自動車"], tags=["scene"])
Q("h0623", "What is the figure doing?", "像は何をしていますか？", "Aiming a bow|弓を構えている",
  ["Playing a flute|笛を吹いている", "Swimming|泳いでいる", "Writing|書いている"], tags=["action"], diff="medium")
TYPE("h0624", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("h0629", "Which animal is shown?", "どの動物が写っていますか？", "Sloth|ナマケモノ", ["Monkey|サル", "Bear|クマ", "Cat|猫"], tags=["classify", "animal"], diff="hard")
N("h0629", "The animal is in a tree", "動物は木の上にいる", True, tags=["scene"])
Q("h0634", "What is on the spoon?", "スプーンの上にあるものは何ですか？", "Cereal|シリアル", ["Rice|ご飯", "Pasta|パスタ", "Soup|スープ"], tags=["classify", "food"], diff="medium")
N("h0637", "An airplane is in the picture", "写真に飛行機が写っている", True)
Q("h0638", "What is the woman doing?", "女性は何をしていますか？", "Singing|歌っている", ["Reading|読書している", "Cooking|料理している", "Swimming|泳いでいる"], tags=["action"])
N("h0638", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
TYPE("h0639", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0655", "Which creature is depicted on the wall?", "壁に描かれている生き物はどれですか？", "Dragons|竜", ["Tigers|トラ", "Eagles|ワシ", "Horses|馬"], tags=["detail"])
S("h0656", "tractor", "vehicle")
TYPE("h0658", "satellite", ["photo", "painting", "diagram"], diff="medium")
N("h0659", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0661", "Which fruit is shown?", "どの果物が写っていますか？", "Oranges|オレンジ", ["Apples|りんご", "Bananas|バナナ", "Grapes|ぶどう"], tags=["classify", "food"])
N("h0661", "Some of the oranges are cut in half", "半分に切られたオレンジがある", True, tags=["detail"])
Q("h0662", "What kind of building is lit up?", "ライトアップされている建物はどれですか？", "A church|教会", ["A castle|城", "A windmill|風車", "A barn|納屋"], tags=["classify", "structure"], diff="medium")
TYPE("h0663", "map", ["photo", "painting", "satellite"])
TYPE("h0664", "painting", ["photo", "diagram", "satellite"], diff="medium")
Q("h0665", "What large vessel is shown?", "写っている大きな船は何ですか？", "An aircraft carrier|空母",
  ["A sailboat|ヨット", "A cargo ferry|貨物フェリー", "A fishing boat|漁船"], tags=["classify", "vehicle"], diff="medium")
Q("h0666", "What natural event is shown?", "どんな自然現象が写っていますか？", "A volcanic eruption|火山の噴火",
  ["A tornado|竜巻", "A flood|洪水", "A snowstorm|吹雪"], tags=["scene"])
TYPE("h0667", "painting", ["photo", "diagram", "satellite"], diff="medium")
TYPE("h0668", "drawing", ["photo", "satellite", "map"])
colour("h0672", "the book cover", "本の表紙", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
Q("h0673", "Which animals are on the plant?", "植物にとまっている動物はどれですか？", "Grasshoppers|バッタ",
  ["Bees|ミツバチ", "Butterflies|チョウ", "Ants|アリ"], tags=["classify", "animal"], diff="medium")
TYPE("h0675", "diagram", ["photo", "painting", "satellite"], diff="medium")
Q("h0676", "What is painted on the back wall of the stage?", "舞台の奥の壁には何が描かれていますか？", "A pine tree|松",
  ["A dragon|竜", "Mount Fuji|富士山", "A wave|波"], tags=["detail"], diff="hard")
TYPE("h0677", "space", ["photo", "painting", "map"], diff="medium")
Q("h0678", "What hangs from the ceiling?", "天井から下がっているものは何ですか？", "A chandelier|シャンデリア",
  ["A fan|扇風機", "A hammock|ハンモック", "A flag|旗"], tags=["detail"])
TYPE("h0679", "painting", ["photo", "diagram", "satellite"])
TYPE("h0681", "map", ["photo", "painting", "satellite"], diff="medium")
Q("h0683", "What is the person holding?", "手に持っているものは何ですか？", "Eyeglasses|眼鏡",
  ["A magnifying glass|虫眼鏡", "A camera|カメラ", "A spoon|スプーン"], tags=["detail"])
N("h0683", "An eye chart is visible", "視力検査表が見える", True, tags=["presence"], diff="medium")
Q("h0684", "What is beside the bronze statue?", "ブロンズ像のそばにあるものは何ですか？", "Suitcases|スーツケース",
  ["Dogs|犬", "Bicycles|自転車", "Flowers|花"], tags=["detail"], diff="medium")
TYPE("h0685", "space", ["photo", "painting", "map"], diff="medium")
TYPE("h0687", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0690", "Which animals are illustrated?", "描かれている動物はどれですか？", "Frogs|カエル", ["Snakes|ヘビ", "Birds|鳥", "Butterflies|チョウ"], tags=["classify", "animal"])
TYPE("h0691", "page", ["photo", "map", "satellite"], diff="medium")
S("h0692", "ship", "vehicle")
Q("h0694", "Which star name is labelled?", "名前が書かれている星はどれですか？", "Polaris|ポラリス（北極星）",
  ["Sirius|シリウス", "Vega|ベガ", "Betelgeuse|ベテルギウス"], tags=["ocr", "diagram"], diff="medium")
Q("h0695", "What are the two people doing?", "2 人は何をしていますか？", "Hiking in the mountains|山でハイキングをしている",
  ["Swimming|泳いでいる", "Playing tennis|テニスをしている", "Cooking|料理している"], tags=["action"])
TYPE("h0696", "satellite", ["photo", "painting", "diagram"], diff="medium")
TYPE("h0697", "diagram", ["photo", "painting", "satellite"])
Q("h0700", "What shape is the island?", "この島はどんな形をしていますか？", "A ring (atoll)|輪の形（環礁）",
  ["A square|四角形", "A triangle|三角形", "A star|星形"], tags=["shape"], diff="medium")
