# -*- coding: utf-8 -*-
"""Image items, h1548-h1601 (pictures used by the English article only), somewhat demanding set.
Aircraft dropping bombs, war scenes, genocide remains, anaesthesia/medical pictures and portraits were left out."""
from templates import Q, N, TYPE, S, colour

Q("h1548", "Which island is shown in this view from space?", "宇宙から見たこの島はどれですか？", "Timor|ティモール島",
  ["Borneo|ボルネオ島", "Sumatra|スマトラ島", "Sri Lanka|スリランカ"], tags=["geo"], diff="hard")
Q("h1549", "Which animal is shown?", "どの動物が写っていますか？", "A bed bug|トコジラミ", ["A tick|マダニ", "A beetle|甲虫", "A cockroach|ゴキブリ"], tags=["classify", "animal"], diff="hard")
Q("h1550", "What kind of scene is this?", "これはどんな景色ですか？", "A city at night with lit towers|ライトアップされた塔のある夜の都市",
  ["A mountain at dawn|夜明けの山", "A harbour in daylight|昼の港", "A village at noon|昼の村"], tags=["scene"], diff="medium")
Q("h1555", "Which plant family does this flower belong to?", "この花はどの科の植物ですか？", "The rose family|バラ科",
  ["The orchid family|ラン科", "The daisy family|キク科", "The lily family|ユリ科"], tags=["classify", "plant"], diff="hard")
N("h1555", "The flower has white petals", "花びらは白い", True, tags=["attribute"])
Q("h1556", "What does the colour scale of the map show?", "地図の色は何を表していますか？", "The annual inflation rate|年間のインフレ率",
  ["Rainfall|降水量", "Population|人口", "Average height|平均身長"], tags=["ocr", "map"], diff="hard")
Q("h1557", "Which newspaper is this?", "これはどの新聞ですか？", "The New York Times|ニューヨーク・タイムズ",
  ["The Washington Post|ワシントン・ポスト", "The Times (London)|ザ・タイムズ（ロンドン）", "Le Monde|ル・モンド"], tags=["ocr"], diff="medium")
Q("h1558", "Which lakes are shown in this satellite image?", "この衛星画像に写っている湖はどれですか？", "The Great Lakes|五大湖",
  ["The East African Great Lakes|東アフリカの大地溝帯の湖", "The lakes of Finland|フィンランドの湖群", "Lake Baikal|バイカル湖"], tags=["geo"], diff="hard")
Q("h1561", "What is the red powder in the tube?", "試験管の中の赤い粉は何ですか？", "Red phosphorus|赤リン",
  ["Iron rust|鉄さび", "Chili powder|唐辛子の粉", "Brick dust|レンガの粉"], tags=["classify", "object"], diff="hard")
Q("h1563", "What does the swirl behind the aircraft show?", "航空機の後ろの渦は何を示していますか？", "A wingtip vortex|翼端渦",
  ["Exhaust smoke|排気煙", "A cloud|雲", "A shadow|影"], tags=["scene"], diff="hard")
Q("h1565", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Little Women|若草物語",
  ["Pride and Prejudice|高慢と偏見", "Anne of Green Gables|赤毛のアン", "Heidi|ハイジ"], tags=["ocr", "book"], diff="medium")
Q("h1567", "Which famous fresco detail is this?", "これはどの有名なフレスコ画の一部ですか？", "The Creation of Adam|アダムの創造",
  ["The Last Supper|最後の晩餐", "The School of Athens|アテネの学堂", "The Birth of Venus|ヴィーナスの誕生"], tags=["art"], diff="medium")
Q("h1569", "What colour is the crystal?", "結晶は何色ですか？", "Purple|紫", ["Green|緑", "Red|赤", "Yellow|黄"], tags=["colour", "attribute"], diff="medium")
Q("h1570", "Which animal is shown?", "どの動物が写っていますか？", "A red fox|アカギツネ", ["A wolf|オオカミ", "A dog|犬", "A cat|猫"], tags=["classify", "animal"], diff="medium")
N("h1570", "There is snow on the ground", "地面に雪がある", True, tags=["scene"])
Q("h1572", "Which plant is illustrated?", "どの植物が描かれていますか？", "A coconut palm|ココヤシ", ["A banana plant|バナナ", "A date palm|ナツメヤシ", "A bamboo|竹"], tags=["classify", "plant"], diff="hard")
Q("h1573", "What are the round objects hanging along the ship's side?", "船の側面に並んでいる丸い物は何ですか？", "Shields|盾", ["Barrels|樽", "Lanterns|ランタン", "Cannon|大砲"], tags=["detail"], diff="hard")
Q("h1574", "What does this diagram show?", "この図は何を示していますか？", "The water cycle|水の循環",
  ["The carbon cycle|炭素の循環", "A food chain|食物連鎖", "A river map|河川の地図"], tags=["diagram"], diff="medium")
Q("h1576", "What is being made in the engraving?", "版画では何が作られていますか？", "Beer|ビール", ["Bread|パン", "Cloth|布", "Soap|石けん"], tags=["detail"], diff="hard")
Q("h1577", "What does the cut face of the ground show?", "地面の断面は何を示していますか？", "Layers of soil|土壌の層", ["Layers of a cake|ケーキの層", "Lava flows|溶岩の流れ", "Tree rings|年輪"], tags=["scene"], diff="medium")
Q("h1578", "What is the object?", "これは何ですか？", "A small cannon|小さな大砲", ["A telescope|望遠鏡", "A plough|鋤", "A cart|荷車"], tags=["classify", "object"], diff="medium")
Q("h1579", "Which famous photograph is this?", "これはどの有名な写真ですか？", "The Blue Marble (Earth)|ブルー・マーブル（地球）",
  ["Earthrise|地球の出", "Pale Blue Dot|ペイル・ブルー・ドット", "The Moon landing|月面着陸"], tags=["classify", "space"], diff="hard")
Q("h1580", "Which regions are shown on this old map?", "この古い地図に描かれている地域はどれですか？", "Turkey in Asia and Asia Minor|アジア側のトルコ（小アジア）",
  ["Scandinavia|スカンディナヴィア", "South America|南アメリカ", "Japan|日本"], tags=["ocr", "map"], diff="hard")
colour("h1581", "the flower", "花", "red", ["white", "yellow", "blue"], tags=("colour", "attribute"))
Q("h1581", "Which plant is shown?", "どの植物が写っていますか？", "An anthurium|アンスリウム", ["A rose|バラ", "A tulip|チューリップ", "A cactus|サボテン"], tags=["classify", "plant"], diff="hard")
Q("h1584", "Which animals are shown?", "どの動物が写っていますか？", "Manatees and dugongs|マナティーとジュゴン",
  ["Seals|アザラシ", "Dolphins|イルカ", "Sharks|サメ"], tags=["classify", "animal"], diff="hard")
Q("h1586", "Which building is this?", "これはどの建物ですか？", "The Alhambra|アルハンブラ宮殿",
  ["The Louvre|ルーブル宮殿", "Himeji Castle|姫路城", "The Kremlin|クレムリン"], tags=["classify", "structure"], diff="hard")
Q("h1587", "Which lake is shown?", "写っている湖はどれですか？", "Lake Superior|スペリオル湖", ["Lake Victoria|ヴィクトリア湖", "Lake Baikal|バイカル湖", "Lake Biwa|琵琶湖"], tags=["geo"], diff="hard")
Q("h1590", "Whose book is the title page of 'Leviathan'?", "『リヴァイアサン』の扉絵は誰の著書のものですか？", "Thomas Hobbes|トマス・ホッブズ",
  ["John Locke|ジョン・ロック", "Adam Smith|アダム・スミス", "Francis Bacon|フランシス・ベーコン"], tags=["ocr", "book"], diff="hard")
Q("h1591", "What does the thermometer in the glass show?", "グラスの中の温度計はどんな状態を示していますか？", "About zero degrees, with ice|氷とともに約 0 度",
  ["About 100 degrees|約 100 度", "About 40 degrees|約 40 度", "About 20 degrees below zero|氷点下約 20 度"], tags=["detail"], diff="hard")
Q("h1593", "Which animal is shown?", "どの動物が写っていますか？", "A chimaera (a cartilaginous fish)|ギンザメ（軟骨魚類）",
  ["An eel|ウナギ", "A trout|マス", "A seahorse|タツノオトシゴ"], tags=["classify", "animal"], diff="hard")
Q("h1594", "What does the picture mainly show?", "写真は主に何を写していますか？", "A variety of foods|さまざまな食品",
  ["Furniture|家具", "Tools|工具", "Toys|おもちゃ"], tags=["classify", "food"], diff="medium")
Q("h1595", "What kind of vessels are in the old engraving?", "古い版画に描かれている船はどんな船ですか？", "Sailing ships among icebergs|氷山の間の帆船",
  ["Steamships in a harbour|港の蒸気船", "Rowing boats on a river|川の手漕ぎ舟", "Fishing canoes|漁の丸木舟"], tags=["scene"], diff="hard")
Q("h1597", "In which language is the manuscript written?", "写本はどの言語で書かれていますか？", "Latin|ラテン語", ["Greek|ギリシャ語", "Arabic|アラビア語", "English|英語"], tags=["ocr", "language"], diff="hard")
Q("h1599", "Which fish is shown?", "どの魚が写っていますか？", "A marlin|マカジキ", ["A salmon|サケ", "A shark|サメ", "A tuna|マグロ"], tags=["classify", "animal"], diff="hard")
Q("h1600", "Which animal is shown?", "どの動物が写っていますか？", "A lion|ライオン", ["A tiger|トラ", "A bear|クマ", "A hyena|ハイエナ"], tags=["classify", "animal"], diff="medium")
Q("h1601", "Which herb is shown?", "どのハーブが写っていますか？", "Thyme|タイム", ["Basil|バジル", "Mint|ミント", "Parsley|パセリ"], tags=["classify", "plant"], diff="hard")
