# -*- coding: utf-8 -*-
"""Image items, h1388-h1467 (pictures used by the English article only), written for a somewhat demanding set.
Wars, weapons, slavery, labour of children, crowds and portraits of private people were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h1388", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Madame Bovary|ボヴァリー夫人",
  ["Anna Karenina|アンナ・カレーニナ", "Lolita|ロリータ", "Emma|エマ"], tags=["ocr", "book"], diff="medium")
Q("h1388", "Who is named as the author on the title page?", "表紙に著者として書かれているのは誰ですか？", "Gustave Flaubert|ギュスターヴ・フローベール",
  ["Victor Hugo|ヴィクトル・ユゴー", "Émile Zola|エミール・ゾラ", "Honoré de Balzac|オノレ・ド・バルザック"], tags=["ocr", "book"], diff="hard")
Q("h1391", "What kind of machine is this?", "これはどんな機械ですか？", "A cipher machine|暗号機",
  ["A typewriter|タイプライター", "A sewing machine|ミシン", "A printing press|印刷機"], tags=["classify", "object"], diff="hard")
Q("h1392", "What kind of car is this?", "これはどんな車ですか？", "An early Ford Model T|初期のフォード・モデルT",
  ["A modern sports car|現代のスポーツカー", "A tractor|トラクター", "A steam locomotive|蒸気機関車"], tags=["classify", "vehicle"], diff="medium")
Q("h1394", "Which fairy tale does the painting show?", "この絵はどの童話の場面ですか？", "Little Red Riding Hood|赤ずきん",
  ["Cinderella|シンデレラ", "Snow White|白雪姫", "Hansel and Gretel|ヘンゼルとグレーテル"], tags=["art"], diff="hard")
Q("h1395", "What is the animal doing?", "動物はどんな姿勢ですか？", "Lying coiled up|とぐろを巻いている",
  ["Flying|飛んでいる", "Swimming|泳いでいる", "Jumping|跳んでいる"], tags=["detail"], diff="medium")
Q("h1396", "What machine is silhouetted against the sky?", "空を背景にシルエットになっている機械は何ですか？", "An oil pump (pumpjack)|石油の汲み上げポンプ",
  ["A windmill|風車", "A construction crane|クレーン", "A water tower|給水塔"], tags=["classify", "object"], diff="medium")
Q("h1407", "Which building is this?", "これはどの建物ですか？", "The Sydney Opera House|シドニー・オペラハウス",
  ["The Guggenheim Museum|グッゲンハイム美術館", "The Taj Mahal|タージ・マハル", "The Eiffel Tower|エッフェル塔"], tags=["classify", "structure"], diff="medium")
N("h1407", "A boat is visible on the water", "水面に船が見える", True, tags=["presence"])
Q("h1408", "What is this document?", "これはどんな文書ですか？", "A handwritten music score|手書きの楽譜",
  ["A map|地図", "A poem manuscript|詩の原稿", "A calendar|カレンダー"], tags=["classify", "object"], diff="medium")
Q("h1412", "Which instrument does the goddess play?", "女神が演奏している楽器はどれですか？", "A veena (a stringed instrument)|ヴィーナ（弦楽器）",
  ["A flute|フルート", "A drum|太鼓", "A trumpet|トランペット"], tags=["detail"], diff="hard")
Q("h1413", "What is written on one of the signs?", "プラカードの 1 つには何と書かれていますか？", "VOTING RIGHTS NOW",
  ["FREE LUNCH FOR ALL", "STOP THE WAR", "LOWER TAXES"], tags=["ocr", "sign"], diff="hard")
Q("h1416", "Which peninsula is highlighted?", "強調されているのはどの半島ですか？", "The Korean Peninsula|朝鮮半島",
  ["The Malay Peninsula|マレー半島", "The Arabian Peninsula|アラビア半島", "The Italian Peninsula|イタリア半島"], tags=["geo", "map"], diff="medium")
Q("h1417", "Which animal is shown?", "どの動物が写っていますか？", "A cougar (mountain lion)|ピューマ",
  ["A leopard|ヒョウ", "A lion|ライオン", "A cheetah|チーター"], tags=["classify", "animal"], diff="hard")
Q("h1418", "Which waterway is shown in this satellite image?", "この衛星画像に写っている海峡はどれですか？", "The Strait of Hormuz|ホルムズ海峡",
  ["The Strait of Gibraltar|ジブラルタル海峡", "The Bering Strait|ベーリング海峡", "The Bosporus|ボスポラス海峡"], tags=["geo"], diff="hard")
Q("h1419", "What kind of landscape is this?", "これはどんな景色ですか？", "Sand dunes by the sea|海辺の砂丘",
  ["Snow drifts|雪の吹き溜まり", "Salt flats|塩原", "Rocky hills|岩山"], tags=["scene"], diff="medium")
Q("h1420", "Which animals does this chart show?", "この図は何の動物を示していますか？", "Chickens (breeds of poultry)|ニワトリ（家禽の品種）",
  ["Ducks|アヒル", "Geese|ガチョウ", "Turkeys|七面鳥"], tags=["classify", "animal"], diff="hard")
Q("h1421", "What is the structure at the right edge?", "右端に写っている構造物は何ですか？", "A space station|宇宙ステーション",
  ["A satellite TV dish|衛星放送アンテナ", "A drone|ドローン", "An airplane wing|飛行機の翼"], tags=["classify", "object"], diff="medium")
Q("h1422", "Which crop is shown?", "どの作物が写っていますか？", "Soybeans|大豆", ["Peanuts|ピーナッツ", "Corn|トウモロコシ", "Rice|稲"], tags=["classify", "plant"], diff="hard")
Q("h1425", "What is the man doing?", "男性は何をしていますか？", "Mowing grass|芝を刈っている",
  ["Painting a fence|柵を塗っている", "Digging a hole|穴を掘っている", "Washing a car|洗車している"], tags=["action"], diff="medium")
N("h1425", "The man is wearing ear protection", "男性は耳当てをつけている", True, tags=["attribute"], diff="medium")
Q("h1426", "Whose lives does the book describe?", "この本は誰の伝記を集めたものですか？", "Plutarch's Lives|プルタルコス（英雄伝）",
  ["Lives of the Poets|詩人列伝", "Lives of the Saints|聖人伝", "Vasari's Lives|ヴァザーリ（美術家列伝）"], tags=["ocr", "book"], diff="hard")
Q("h1427", "What is being tested?", "何が試験されていますか？", "A jet engine|ジェットエンジン",
  ["A steam engine|蒸気機関", "A wind turbine|風力タービン", "A car engine|自動車エンジン"], tags=["classify", "object"], diff="hard")
Q("h1428", "Which animals are the tube-shaped orange and purple organisms?", "筒状のオレンジ色・紫色の生物は何ですか？", "Sponges|カイメン",
  ["Corals|サンゴ", "Sea cucumbers|ナマコ", "Seaweeds|海藻"], tags=["classify", "animal"], diff="hard")
Q("h1429", "Which rocket is shown?", "どのロケットが写っていますか？", "Saturn V|サターンV",
  ["The Space Shuttle|スペースシャトル", "Soyuz|ソユーズ", "Falcon 9|ファルコン9"], tags=["classify", "vehicle"], diff="hard")
Q("h1440", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Van Gogh|ゴッホ", ["Monet|モネ", "Cézanne|セザンヌ", "Renoir|ルノワール"], tags=["art"], diff="medium")
Q("h1446", "Which activity is shown in the old illustration?", "古い絵に描かれている活動はどれですか？", "Capoeira|カポエイラ",
  ["Ballet|バレエ", "Fencing|フェンシング", "Judo|柔道"], tags=["action"], diff="hard")
Q("h1447", "Which story does the illustration come from?", "この挿絵はどの物語のものですか？", "Alice's Adventures in Wonderland|不思議の国のアリス",
  ["Peter Pan|ピーター・パン", "The Wizard of Oz|オズの魔法使い", "Pinocchio|ピノキオ"], tags=["art"], diff="hard")
Q("h1453", "Which brand name is printed on the remote control?", "リモコンに印刷されているブランド名はどれですか？", "Samsung",
  ["Sony", "Panasonic", "LG"], tags=["ocr"], diff="medium")
Q("h1457", "What kind of landscape is this?", "これはどんな景色ですか？", "A flat grassland|平らな草原",
  ["A desert|砂漠", "A rainforest|熱帯雨林", "A glacier|氷河"], tags=["scene"], diff="medium")
N("h1459", "A person is standing next to the well", "井戸のそばに人が立っている", True, tags=["presence"], diff="medium")
Q("h1461", "In which language is the title page written?", "表紙はどの言語で書かれていますか？", "French|フランス語",
  ["English|英語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
Q("h1464", "Which plant is shown?", "どの植物が写っていますか？", "Yucca|ユッカ", ["A cactus|サボテン", "Bamboo|竹", "A palm tree|ヤシの木"], tags=["classify", "plant"], diff="hard")
Q("h1465", "What colour is the house?", "家は何色ですか？", "Light blue|水色", ["Red|赤", "Yellow|黄", "Green|緑"], tags=["colour", "attribute"], diff="medium")
N("h1465", "The house has a garage", "この家にはガレージがある", True, tags=["presence"])
