# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0501-h0588 (pictures used by the English article only; the compiler
publishes them in English). Portraits of private people, medical scenes, soldiers and nudity were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h0501", "Which bird is shown?", "どの鳥が写っていますか？", "Toucan|オオハシ", ["Parrot|オウム", "Owl|フクロウ", "Duck|アヒル"], tags=["classify", "animal"], diff="medium")
S("h0502", "ship", "vehicle")
Q("h0504", "Who is the character in the illustration?", "イラストの人物は誰ですか？", "Santa Claus|サンタクロース",
  ["Uncle Sam|アンクル・サム", "A pirate|海賊", "A wizard|魔法使い"], tags=["classify", "art"])
TYPE("h0508", "drawing", ["photo", "satellite", "map"])
Q("h0511", "What do the black dots on the map mark?", "地図の黒い点は何を示していますか？", "Earthquake epicentres|震源",
  ["Cities|都市", "Airports|空港", "Rivers|河川"], tags=["ocr", "map"], diff="medium")
Q("h0512", "Which monument is in the foreground?", "手前にある記念物はどれですか？", "The Great Sphinx|スフィンクス",
  ["The Statue of Liberty|自由の女神", "The Eiffel Tower|エッフェル塔", "Big Ben|ビッグ・ベン"], tags=["classify", "structure"])
N("h0512", "A pyramid is visible in the background", "背景にピラミッドが見える", True, tags=["presence"])
Q("h0513", "In which language is the title written?", "題名はどの言語で書かれていますか？", "German|ドイツ語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
colour("h0516", "the flowers", "花", "purple", ["red", "yellow", "white"], tags=("colour", "attribute"))
Q("h0525", "Which plant is shown?", "どの植物が写っていますか？", "Cattails|ガマ", ["Bamboo|竹", "Corn|トウモロコシ", "Sunflowers|ヒマワリ"], tags=["classify", "plant"], diff="hard")
Q("h0526", "Which sport is being played?", "どのスポーツをしていますか？", "Golf|ゴルフ", ["Tennis|テニス", "Baseball|野球", "Soccer|サッカー"], tags=["classify", "sport"])
Q("h0527", "What is the colourful pool?", "色鮮やかな池は何ですか？", "A hot spring|温泉",
  ["A swimming pool|プール", "A lake of paint|絵の具の湖", "A rice field|田んぼ"], tags=["scene"], diff="medium")
N("h0527", "Steam is rising from the water", "水面から湯気が立ちのぼっている", True, tags=["scene"])
Q("h0528", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Paradise Lost|失楽園",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Dracula|吸血鬼ドラキュラ"], tags=["ocr", "book"])
Q("h0529", "Which bird is shown?", "どの鳥が写っていますか？", "Pheasant|キジ", ["Penguin|ペンギン", "Owl|フクロウ", "Eagle|ワシ"], tags=["classify", "animal"], diff="medium")
TYPE("h0531", "painting", ["photo", "diagram", "satellite"])
Q("h0537", "Which island is shown?", "写っている島はどれですか？", "Kyushu|九州", ["Hokkaido|北海道", "Sicily|シチリア島", "Iceland|アイスランド"], tags=["geo"], diff="hard")
Q("h0539", "How many white spheres surround the dark sphere?", "黒い球の周りにある白い球はいくつですか？", "Four|4 つ",
  ["Two|2 つ", "Three|3 つ", "Five|5 つ"], tags=["count"], diff="medium")
TYPE("h0543", "painting", ["photo", "diagram", "satellite"])
TYPE("h0544", "painting", ["photo", "diagram", "satellite"])
Q("h0549", "What kind of scene is this?", "これはどんな景色ですか？", "A city skyline|都市の景色", ["A forest|森", "A desert|砂漠", "A beach|ビーチ"], tags=["classify", "scene"])
Q("h0550", "Which drink is in the glass at the top right?", "右上のグラスに入っている飲み物はどれですか？", "Orange juice|オレンジジュース",
  ["Milk|牛乳", "Beer|ビール", "Red wine|赤ワイン"], tags=["detail"], diff="medium")
TYPE("h0554", "page", ["photo", "map", "satellite"], diff="medium")
Q("h0555", "What kind of vessel is this?", "これはどんな船ですか？", "A submarine|潜水艦", ["A sailboat|ヨット", "A ferry|フェリー", "A canoe|カヌー"], tags=["classify", "vehicle"], diff="medium")
TYPE("h0557", "drawing", ["photo", "satellite", "map"])
TYPE("h0561", "drawing", ["photo", "satellite", "map"])
Q("h0568", "Which board game is shown?", "どのボードゲームが写っていますか？", "Go|囲碁", ["Chess|チェス", "Backgammon|バックギャモン", "Checkers|チェッカー"], tags=["classify", "game"], diff="medium")
TYPE("h0575", "map", ["photo", "painting", "satellite"])
Q("h0576", "Which sport is shown?", "どのスポーツですか？", "Car racing|自動車レース", ["Horse racing|競馬", "Rowing|ボート競技", "Cycling|自転車競技"], tags=["classify", "sport"])
Q("h0577", "Which object is in the painting?", "絵に描かれている物はどれですか？", "A skull|頭蓋骨", ["A globe|地球儀", "A clock|時計", "A violin|バイオリン"], tags=["detail"], diff="medium")
Q("h0579", "What colour are the tulips?", "チューリップは何色ですか？", "Red|赤", ["Blue|青", "White|白", "Green|緑"], tags=["colour", "attribute"])
Q("h0580", "What kind of screen is this?", "これはどんな画面ですか？", "A video website|動画サイトの画面",
  ["A weather map|天気図", "A calendar|カレンダー", "A map app|地図アプリ"], tags=["classify", "object"], diff="medium")
Q("h0581", "Which vegetable is shown?", "どの野菜が写っていますか？", "Carrots|にんじん", ["Potatoes|じゃがいも", "Tomatoes|トマト", "Apples|りんご"], tags=["classify", "food"])
N("h0584", "A goldfish bowl is on the table", "テーブルの上に金魚鉢がある", True, tags=["presence"], diff="medium")
Q("h0585", "What kinds of objects are shown?", "どんな物が写っていますか？", "Balls|ボール", ["Fruits|果物", "Cookies|クッキー", "Eggs|卵"], tags=["classify", "object"])
N("h0585", "There is a basketball among them", "その中にバスケットボールがある", True, tags=["presence"])
Q("h0586", "From where was the picture taken?", "この写真はどこから撮影されましたか？", "From above the clouds|雲の上から",
  ["From under water|水中から", "From inside a cave|洞窟の中から", "From inside a car|車の中から"], tags=["scene"], diff="medium")
Q("h0588", "Which script is the writing in?", "書かれている文字は何ですか？", "Japanese script|日本語（漢字・かな）",
  ["Latin letters|ラテン文字", "Arabic script|アラビア文字", "Cyrillic letters|キリル文字"], tags=["ocr", "script"], diff="medium")
