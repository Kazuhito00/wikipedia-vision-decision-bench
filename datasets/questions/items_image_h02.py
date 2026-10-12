# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0041-h0100 (pictures used by both wikis). Pictures that show
patients, injuries or other distressing medical content were left out on purpose."""
from templates import Q, N, TYPE, S, colour

# -- false statements for pictures from the first batch (balance)
N("h0008", "There is a car in the picture", "写真に自動車が写っている", False)
N("h0032", "There is snow on the ground", "地面に雪がある", False)
N("h0017", "There is a cat in the picture", "写真に猫が写っている", False)

Q("h0041", "In which language is the title written?", "題名はどの言語で書かれていますか？", "Italian|イタリア語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
TYPE("h0042", "satellite", ["photo", "painting", "map"], diff="medium")
TYPE("h0043", "diagram", ["photo", "painting", "satellite"])
Q("h0044", "What is the round dish with the coloured spots?", "色のついた点が並んだ丸い容器は何ですか？", "A petri dish|ペトリ皿",
  ["A frying pan|フライパン", "A dinner plate|食事用の皿", "A coin|硬貨"], tags=["classify", "object"], diff="medium")
Q("h0045", "What kind of scene is this?", "これはどんな景色ですか？", "A city skyline|都市の景色",
  ["A forest|森", "A desert|砂漠", "A beach|ビーチ"], tags=["classify", "scene"])
N("h0045", "There is snow in the picture", "写真に雪がある", False)
TYPE("h0046", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("h0047", "What is shown?", "何が写っていますか？", "A marble sculpture|大理石の彫刻",
  ["A painting|絵画", "A fossil|化石", "A building|建物"], tags=["classify", "object"], diff="medium")
TYPE("h0048", "map", ["photo", "painting", "diagram"])
TYPE("h0049", "page", ["photo", "map", "satellite"], diff="medium")
Q("h0050", "Which season does the scenery suggest?", "この景色はどの季節を思わせますか？", "Autumn|秋",
  ["Spring|春", "Winter|冬", "Summer|夏"], tags=["scene", "season"])
TYPE("h0051", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0052", "What shape does the galaxy have?", "この銀河はどんな形をしていますか？", "A spiral|渦巻き",
  ["A ring|輪", "A cross|十字", "A square|四角形"], tags=["shape"])
Q("h0053", "Which body is labelled at the upper left?", "左上に名前が書かれている天体はどれですか？", "Sun|太陽",
  ["Mars|火星", "Jupiter|木星", "Venus|金星"], tags=["ocr", "diagram"])
Q("h0054", "What has been folded from the paper?", "紙で折られているものは何ですか？", "Cranes|折り鶴",
  ["Boats|舟", "Flowers|花", "Hats|帽子"], tags=["classify", "object"])
Q("h0056", "Which country occupies most of the land shown?", "写っている陸地の大部分を占める国はどれですか？", "Spain|スペイン",
  ["Japan|日本", "Brazil|ブラジル", "Egypt|エジプト"], tags=["geo"], diff="hard")
colour("h0057", "the display shelves", "展示棚", "green", ["red", "blue", "black"], tags=("colour", "attribute"))
TYPE("h0059", "space", ["photo", "painting", "map"], diff="medium")
Q("h0060", "Which animal is shown?", "どの動物が写っていますか？", "Whale|クジラ", ["Seal|アザラシ", "Penguin|ペンギン", "Turtle|カメ"], tags=["classify", "animal"], diff="medium")
Q("h0061", "Which script is the word written in?", "この単語はどの文字で書かれていますか？", "Latin|ラテン文字",
  ["Cyrillic|キリル文字", "Arabic|アラビア文字", "Greek|ギリシャ文字"], tags=["ocr", "script"], diff="medium")
Q("h0062", "Which material is being worked?", "加工されている素材はどれですか？", "Leather|革", ["Glass|ガラス", "Stone|石", "Paper|紙"], tags=["classify", "object"], diff="medium")
Q("h0064", "What do the spheres represent?", "球は何を表していますか？", "Atoms|原子", ["Planets|惑星", "Cells|細胞", "Eggs|卵"], tags=["diagram"], diff="medium")
Q("h0065", "What is being measured?", "何を測っていますか？", "Blood pressure|血圧", ["Body weight|体重", "Height|身長", "Temperature|体温"], tags=["action"], diff="medium")
TYPE("h0067", "painting", ["photo", "satellite", "map"])
N("h0068", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0068", "What is the setting?", "ここはどんな場所ですか？", "A hospital ward|病室",
  ["A school gym|学校の体育館", "A train station|駅", "A factory|工場"], tags=["scene"], diff="medium")
Q("h0069", "In which language is the title page written?", "この表紙はどの言語で書かれていますか？", "Russian|ロシア語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0073", "What kind of view is this?", "これはどんな眺めですか？", "An aerial view of a city|都市の空撮",
  ["A forest|森", "A beach|ビーチ", "A mountain range|山脈"], tags=["scene"])
TYPE("h0074", "painting", ["photo", "satellite", "map"])
Q("h0074", "What does the standing woman on the right hold?", "右側に立っている女性は何を持っていますか？", "A parasol|日傘",
  ["A basket|かご", "A guitar|ギター", "A baby|赤ちゃん"], tags=["detail"], diff="hard")
Q("h0077", "Which animal is shown?", "どの動物が写っていますか？", "Sunfish|マンボウ", ["Dolphin|イルカ", "Turtle|カメ", "Penguin|ペンギン"], tags=["classify", "animal"], diff="medium")
N("h0077", "The animal is underwater", "動物は水中にいる", True)
Q("h0078", "What landscape is this?", "これはどんな景色ですか？", "A desert mountain range|砂漠の山地",
  ["A snowy forest|雪の森", "A tropical beach|熱帯のビーチ", "A city street|市街地"], tags=["scene"])
N("h0078", "There is green vegetation in the valley", "谷に緑の植物がある", True, tags=["scene"])
Q("h0080", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Uncle Tom's Cabin|アンクル・トムの小屋",
  ["Moby-Dick|白鯨", "Gulliver's Travels|ガリバー旅行記", "Oliver Twist|オリバー・ツイスト"], tags=["ocr", "book"])
Q("h0081", "Where are the small objects?", "小さな物体はどこにありますか？", "In orbit above the Earth|地球の周回軌道上",
  ["On a beach|砂浜", "In a forest|森の中", "Inside a house|家の中"], tags=["scene"])
Q("h0085", "Which instrument is shown?", "どの楽器が写っていますか？", "A viola (violin family)|ヴィオラ（バイオリンの仲間）",
  ["A guitar|ギター", "A piano|ピアノ", "A flute|フルート"], tags=["classify", "object"])
Q("h0086", "What are the people doing?", "人々は何をしていますか？", "Playing a board game|ボードゲームをしている",
  ["Cooking|料理している", "Swimming|泳いでいる", "Painting|絵を描いている"], tags=["action"])
N("h0086", "A child is at the table", "テーブルに子どもがいる", True)
TYPE("h0088", "painting", ["photo", "satellite", "map"])
N("h0088", "There is a watermelon in the picture", "絵に西瓜が描かれている", True, diff="medium")
TYPE("h0089", "page", ["photo", "map", "satellite"], diff="medium")
TYPE("h0090", "painting", ["photo", "diagram", "satellite"])
Q("h0091", "What does the diagram show?", "この図は何を示していますか？", "Layers of soil|土壌の層",
  ["Layers of a cake|ケーキの層", "Layers of clothing|重ね着", "Stages of a tree's growth|木の成長段階"], tags=["diagram"], diff="medium")
TYPE("h0092", "painting", ["photo", "diagram", "satellite"])
Q("h0093", "What colour are the crystals?", "結晶は何色ですか？", "Blue|青", ["Red|赤", "Yellow|黄", "Green|緑"], tags=["colour", "attribute"])
Q("h0094", "In which script is the text written?", "文章はどの文字で書かれていますか？", "Chinese characters|漢字",
  ["Latin letters|ラテン文字", "Arabic script|アラビア文字", "Cyrillic letters|キリル文字"], tags=["ocr", "script"])
Q("h0096", "What is being poured into the glass?", "グラスに注がれているのは何ですか？", "Orange juice|オレンジジュース",
  ["Milk|牛乳", "Water|水", "Red wine|赤ワイン"], tags=["classify", "food"])
Q("h0097", "Where is this scene?", "ここはどこですか？", "A pharmacy|薬局", ["A library|図書館", "A bakery|パン屋", "A gym|ジム"], tags=["scene"])
N("h0097", "Two people are talking", "2 人が話している", True)
colour("h0098", "the largest spheres", "一番大きな球", "purple", ["white", "blue", "green"], tags=("colour", "attribute"))
Q("h0100", "Which language is the title written in?", "題名はどの言語で書かれていますか？", "French|フランス語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
