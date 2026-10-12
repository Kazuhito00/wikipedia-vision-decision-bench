# -*- coding: utf-8 -*-
"""Expansion set, field "life": x0435-x0474 -- bedrooms, offices, construction sites, farmers' markets, street food.
Pictures with a person as the subject were not used."""
from templates import Q, N, TYPE

Q("x0435", "How many beds are in the room?", "部屋にベッドはいくつありますか？", "Two|2 台", ["One|1 台", "Three|3 台", "Four|4 台"], tags=["count", "life"], diff="medium")
N("x0439", "The bed is neatly made", "ベッドはきちんと整えられている", False, tags=["detail", "life"])
Q("x0440", "What colour are the walls of the room?", "部屋の壁は何色ですか？", "Blue|青", ["Yellow|黄色", "Red|赤", "Green|緑"], tags=["colour", "life"], diff="easy")
Q("x0442", "What colour is the bedspread?", "ベッドカバーは何色ですか？", "White|白", ["Blue|青", "Red|赤", "Green|緑"], tags=["colour", "life"], diff="easy")
Q("x0446", "What is written at the upper right of the drawing?", "図の右上には何と書かれていますか？", "A4 LAMINATING POUCH", ["A3 WRITING PAD", "A4 PRINTER PAPER", "B5 NOTEBOOK COVER"],
  tags=["ocr", "record", "life"], diff="hard")
Q("x0447", "What kind of buildings are these?", "これはどんな建物ですか？", "Stacked portable cabins|積み重ねた仮設ユニット", ["Castles|城", "Lighthouses|灯台", "Barns|納屋"],
  tags=["classify", "structure", "life"], diff="hard")
Q("x0448", "What is on the desk by the window?", "窓際の机の上にあるものは何ですか？", "Computers|コンピューター", ["Sewing machines|ミシン", "Microscopes|顕微鏡", "Cameras|カメラ"],
  tags=["classify", "object", "life"], diff="medium")
Q("x0450", "What kind of place is this?", "ここはどんな場所ですか？", "An open-plan office|オープンスペースのオフィス", ["A classroom|教室", "A hospital ward|病室", "A supermarket|スーパーマーケット"],
  tags=["classify", "scene", "life"], diff="medium")
Q("x0453", "What is happening to the large building?", "大きな建物はどうなっていますか？", "It is under construction or repair with scaffolding|足場を組んで建設中・修理中",
  ["It is being painted blue|青く塗られている", "It is floating on water|水に浮かんでいる", "It is being moved on rails|レールで移動している"], tags=["detail", "scene", "life"], diff="hard")
Q("x0455", "What tall machine stands above the construction site?", "工事現場の上にそびえる背の高い機械は何ですか？", "A crane|クレーン", ["A windmill|風車", "A lighthouse|灯台", "A church tower|教会の塔"],
  tags=["classify", "object", "life"], diff="easy")
Q("x0457", "What kind of place is this?", "ここはどんな場所ですか？", "A large construction site|大規模な建設現場", ["A swimming pool|プール", "A ski slope|スキー場", "A shopping mall|ショッピングモール"],
  tags=["classify", "scene", "life"], diff="medium")
N("x0458", "Scaffolding stands on both sides of the narrow gap", "狭い隙間の両側に足場が組まれている", True, tags=["detail", "life"], diff="medium")
Q("x0463", "What colour are the apples in the lower crates?", "下の箱のりんごは何色ですか？", "Green|緑", ["Red|赤", "Yellow|黄色", "Purple|紫"], tags=["colour", "life"], diff="medium")
Q("x0464", "What fruit is in the baskets?", "かごに入っている果物は何ですか？", "Peaches|桃", ["Oranges|オレンジ", "Tomatoes|トマト", "Apples|りんご"], tags=["classify", "food", "life"], diff="medium")
Q("x0466", "What are the red fruits in the boxes?", "箱に入っている赤い果実は何ですか？", "Tomatoes|トマト", ["Strawberries|いちご", "Cherries|さくらんぼ", "Apples|りんご"], tags=["classify", "food", "life"], diff="medium")
Q("x0467", "What is on the plate?", "皿の上にあるものは何ですか？", "Grilled meat on skewers|串焼きの肉", ["Sushi|寿司", "Ice cream|アイスクリーム", "Salad|サラダ"], tags=["classify", "food", "life"], diff="medium")
N("x0468", "It is a street of food stalls at night", "夜の屋台の通りである", True, tags=["scene", "life"])
Q("x0469", "What is being held up?", "手に持たれているものは何ですか？", "An ice-cream cone|アイスクリームのコーン", ["A lollipop|棒付きキャンディ", "A candle|ろうそく", "A balloon|風船"],
  tags=["classify", "food", "life"], diff="medium")
Q("x0473", "What colour is the sauce in the small bowl at the right?", "右の小さな器のソースは何色ですか？", "Green|緑", ["Red|赤", "Yellow|黄色", "Brown|茶色"], tags=["colour", "food", "life"], diff="hard")
