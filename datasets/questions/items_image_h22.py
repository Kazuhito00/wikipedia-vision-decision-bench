# -*- coding: utf-8 -*-
"""Image items, h0861-h0940 (pictures used by the Japanese article only), somewhat demanding set.
Firearms, bombers, war scenes, portraits, skin/lung/medical pictures, nudity and protests were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h0863", "Which strait is shown in this satellite image?", "この衛星画像に写っている海峡はどれですか？", "The Strait of Gibraltar|ジブラルタル海峡",
  ["The Bering Strait|ベーリング海峡", "The Strait of Hormuz|ホルムズ海峡", "The Bosporus|ボスポラス海峡"], tags=["geo"], diff="hard")
Q("h0864", "What kind of aircraft is this?", "これはどんな航空機ですか？", "An airship|飛行船", ["A helicopter|ヘリコプター", "A glider|グライダー", "A hot-air balloon|熱気球"], tags=["classify", "vehicle"], diff="medium")
Q("h0864", "What is written on the side of the airship?", "飛行船の側面には何と書かれていますか？", "FLY WITH ME!",
  ["HELLO WORLD", "SKY TOURS", "BUY NOW"], tags=["ocr"], diff="medium")
Q("h0866", "What is this document?", "これはどんな文書ですか？", "A handwritten music score|手書きの楽譜",
  ["A map|地図", "A letter|手紙", "A recipe|レシピ"], tags=["classify", "object"], diff="medium")
Q("h0870", "What are the objects?", "これらは何ですか？", "Socks|靴下", ["Gloves|手袋", "Scarves|スカーフ", "Hats|帽子"], tags=["classify", "object"])
N("h0870", "There are three socks in the picture", "写真に靴下が 3 つある", True, tags=["count"], diff="medium")
Q("h0872", "Which famous painting is this?", "これはどの有名な絵画ですか？", "The Tower of Babel|バベルの塔",
  ["The Garden of Earthly Delights|快楽の園", "The Hunters in the Snow|雪中の狩人", "Las Meninas|ラス・メニーナス"], tags=["art"], diff="hard")
Q("h0873", "What kind of landscape is this?", "これはどんな景色ですか？", "A hilly city seen from above|丘陵地の街の眺め",
  ["A desert|砂漠", "A snowfield|雪原", "A harbour|港"], tags=["scene"], diff="medium")
Q("h0874", "What are the three objects?", "3 つの物は何ですか？", "Lollipops|棒付きキャンディ", ["Spoons|スプーン", "Matches|マッチ", "Pens|ペン"], tags=["classify", "food"], diff="medium")
Q("h0875", "Which peninsula is shown on the map?", "地図に描かれている半島はどれですか？", "The Italian Peninsula|イタリア半島",
  ["The Iberian Peninsula|イベリア半島", "The Korean Peninsula|朝鮮半島", "The Balkan Peninsula|バルカン半島"], tags=["geo", "map"], diff="medium")
Q("h0876", "What is the white substance in the dish?", "皿に入っている白い物質は何ですか？", "A white powder|白い粉",
  ["Salt crystals|塩の結晶", "Snow|雪", "Sugar cubes|角砂糖"], tags=["classify", "object"], diff="hard")
Q("h0877", "What unit is printed on the numbers?", "数字に添えられている単位は何ですか？", "pm (picometres)|pm（ピコメートル）",
  ["cm (centimetres)|cm（センチメートル）", "kg (kilograms)|kg（キログラム）", "ms (milliseconds)|ms（ミリ秒）"], tags=["ocr", "diagram"], diff="hard")
Q("h0878", "Which technique was used for this vase painting?", "この壺の絵にはどの技法が使われていますか？", "Black-figure pottery|黒像式",
  ["Watercolour|水彩", "Mosaic|モザイク", "Woodblock printing|木版画"], tags=["art"], diff="hard")
Q("h0879", "Which fish is shown?", "どの魚が写っていますか？", "A pufferfish|フグ", ["A goldfish|金魚", "A catfish|ナマズ", "A seahorse|タツノオトシゴ"], tags=["classify", "animal"], diff="hard")
Q("h0880", "Which famous painting is this?", "これはどの有名な絵画ですか？", "The Mona Lisa|モナ・リザ",
  ["Girl with a Pearl Earring|真珠の耳飾りの少女", "The Birth of Venus|ヴィーナスの誕生", "The Scream|叫び"], tags=["art"], diff="medium")
Q("h0884", "What does the pyramid picture show?", "ピラミッドの絵は何を表していますか？", "A society divided into classes|階級に分かれた社会",
  ["A mountain climbing route|登山ルート", "A food chain|食物連鎖", "A family tree|家系図"], tags=["diagram"], diff="hard")
Q("h0885", "What instrument is shown?", "これは何の器具ですか？", "An optical microscope|光学顕微鏡",
  ["A telescope|望遠鏡", "A camera|カメラ", "A projector|プロジェクター"], tags=["classify", "object"], diff="medium")
Q("h0886", "Which desert is highlighted in this satellite map?", "この衛星地図で強調されている砂漠はどれですか？", "The Karakum Desert|カラクム砂漠",
  ["The Sahara|サハラ砂漠", "The Gobi|ゴビ砂漠", "The Atacama|アタカマ砂漠"], tags=["geo"], diff="hard")
Q("h0887", "Which lake is shown in this satellite image?", "この衛星画像に写っている湖はどれですか？", "Issyk-Kul|イシク・クル湖",
  ["Lake Biwa|琵琶湖", "Lake Victoria|ヴィクトリア湖", "The Dead Sea|死海"], tags=["geo"], diff="hard")
Q("h0888", "What does the playground building look like?", "遊び場の建物は何の形をしていますか？", "A ship|船", ["A castle|城", "A train|電車", "An airplane|飛行機"], tags=["detail"], diff="medium")
Q("h0889", "What are the shapes of the cut metal pieces?", "切り出された金属部材の断面の特徴は何ですか？", "Hollow profiles with slots|溝のある中空の断面",
  ["Solid round bars|丸棒", "Thin flat sheets|薄い平板", "Twisted wires|より線"], tags=["detail"], diff="hard")
Q("h0892", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Alexandre Cabanel|アレクサンドル・カバネル",
  ["Monet|モネ", "Rembrandt|レンブラント", "Goya|ゴヤ"], tags=["art"], diff="hard")
Q("h0893", "What food is shown with the fruit?", "果物のそばにある食べ物は何ですか？", "A pie|パイ", ["A pizza|ピザ", "A cake|ケーキ", "A loaf of bread|パン"], tags=["classify", "food"], diff="medium")
Q("h0893", "What sports item is behind the pie?", "パイの後ろにあるスポーツ用品は何ですか？", "A baseball bat|野球のバット",
  ["A tennis racket|テニスラケット", "A golf club|ゴルフクラブ", "A hockey stick|ホッケースティック"], tags=["detail"], diff="hard")
Q("h0896", "Which planet is shown?", "どの惑星が写っていますか？", "Neptune|海王星", ["Mars|火星", "Jupiter|木星", "Saturn|土星"], tags=["classify", "space"], diff="hard")
Q("h0898", "Which animal is shown?", "どの動物が写っていますか？", "A cowrie (a sea snail)|タカラガイ（巻貝）",
  ["A crab|カニ", "A scallop|ホタテ", "A starfish|ヒトデ"], tags=["classify", "animal"], diff="hard")
Q("h0899", "Which flower is shown?", "どの花が写っていますか？", "A sunflower|ヒマワリ", ["A dandelion|タンポポ", "A tulip|チューリップ", "A rose|バラ"], tags=["classify", "plant"], diff="medium")
Q("h0900", "What are the people doing outside the station?", "宇宙ステーションの外で人々は何をしていますか？", "Working in spacesuits|宇宙服で作業している",
  ["Swimming|泳いでいる", "Walking a dog|犬を散歩させている", "Taking photographs of each other|互いを撮影している"], tags=["action"], diff="medium")
Q("h0902", "What is the title on the open book?", "開かれた本の題名は何ですか？", "A Christmas Carol|クリスマス・キャロル",
  ["Oliver Twist|オリバー・ツイスト", "David Copperfield|デイヴィッド・コパフィールド", "Great Expectations|大いなる遺産"], tags=["ocr", "book"], diff="hard")
Q("h0905", "What does the picture show?", "写真は何を写していますか？", "Sea ice|海氷", ["A salt lake|塩湖", "A glacier on land|陸上の氷河", "A frozen river|凍った川"], tags=["scene"], diff="hard")
Q("h0906", "Which islands are visible in this satellite image?", "この衛星画像に写っている島々はどれですか？", "The Channel Islands|チャンネル諸島",
  ["The Hawaiian Islands|ハワイ諸島", "The Galápagos Islands|ガラパゴス諸島", "The Orkney Islands|オークニー諸島"], tags=["geo"], diff="hard")
Q("h0907", "Which birds are illustrated?", "どの鳥が描かれていますか？", "Finches|アトリ科の鳥（フィンチ）", ["Owls|フクロウ", "Ducks|アヒル", "Penguins|ペンギン"], tags=["classify", "animal"], diff="hard")
Q("h0910", "What kind of place is this?", "ここはどんな場所ですか？", "A tropical beach|熱帯のビーチ", ["A snowy mountain|雪山", "A city street|市街地", "A desert|砂漠"], tags=["scene"], diff="medium")
Q("h0912", "Which island is shown on this relief map?", "この地形図に描かれている島はどれですか？", "Borneo|ボルネオ島",
  ["Sumatra|スマトラ島", "Madagascar|マダガスカル島", "Honshu|本州"], tags=["geo", "map"], diff="hard")
Q("h0913", "What is shown?", "何が写っていますか？", "A marble statue of a bearded god|ひげのある神の大理石像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"], diff="medium")
Q("h0915", "Which island is highlighted in red?", "赤く強調されている島はどれですか？", "Sumatra|スマトラ島",
  ["Borneo|ボルネオ島", "Java|ジャワ島", "Sulawesi|スラウェシ島"], tags=["geo", "map"], diff="hard")
Q("h0916", "What kind of ship is this?", "これはどんな船ですか？", "An aircraft carrier|空母", ["A cargo ship|貨物船", "A sailboat|ヨット", "A ferry|フェリー"], tags=["classify", "vehicle"], diff="medium")
Q("h0917", "What are the droplets resting on?", "水滴は何の上にありますか？", "A leaf|葉", ["A window|窓", "A spider web|クモの巣", "A flower petal|花びら"], tags=["detail"], diff="medium")
Q("h0920", "What natural phenomenon is shown?", "どんな自然現象が写っていますか？", "Lightning|稲妻", ["A rainbow|虹", "An aurora|オーロラ", "A tornado|竜巻"], tags=["classify", "scene"], diff="medium")
Q("h0923", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Edvard Munch|エドヴァルド・ムンク",
  ["Van Gogh|ゴッホ", "Gustav Klimt|グスタフ・クリムト", "Picasso|ピカソ"], tags=["art"], diff="medium")
Q("h0924", "Which animal is shown?", "どの動物が写っていますか？", "A crayfish|ザリガニ", ["A lobster|ロブスター", "A scorpion|サソリ", "A spider|クモ"], tags=["classify", "animal"], diff="hard")
Q("h0925", "Which peninsula is shown in this satellite image?", "この衛星画像に写っている半島はどれですか？", "The Crimean Peninsula|クリミア半島",
  ["The Kamchatka Peninsula|カムチャッカ半島", "The Yucatán Peninsula|ユカタン半島", "The Malay Peninsula|マレー半島"], tags=["geo"], diff="hard")
Q("h0928", "Which river is the green band in this satellite image?", "この衛星画像の緑の帯は何川ですか？", "The Nile|ナイル川",
  ["The Amazon|アマゾン川", "The Danube|ドナウ川", "The Yangtze|長江"], tags=["geo"], diff="hard")
Q("h0931", "Which animal is illustrated?", "どの動物が描かれていますか？", "A woolly mammoth|マンモス", ["An elephant|ゾウ", "A bison|バイソン", "A rhinoceros|サイ"], tags=["classify", "animal"], diff="hard")
Q("h0933", "Which space telescope is this?", "これはどの宇宙望遠鏡ですか？", "The Hubble Space Telescope|ハッブル宇宙望遠鏡",
  ["The James Webb Space Telescope|ジェイムズ・ウェッブ宇宙望遠鏡", "The Kepler telescope|ケプラー宇宙望遠鏡", "The International Space Station|国際宇宙ステーション"], tags=["classify", "vehicle"], diff="hard")
Q("h0937", "Which flower is shown?", "どの花が写っていますか？", "A narcissus (daffodil)|スイセン", ["A tulip|チューリップ", "A rose|バラ", "A lily|ユリ"], tags=["classify", "plant"], diff="medium")
Q("h0938", "What are these large stone figures?", "これらの大きな石像は何ですか？", "Moai on Easter Island|イースター島のモアイ",
  ["Buddha statues in Japan|日本の仏像", "Egyptian sphinxes|エジプトのスフィンクス", "Totem poles in Canada|カナダのトーテムポール"], tags=["classify", "structure"], diff="medium")
Q("h0939", "Which waterway is named in the satellite map?", "衛星地図に名前が書かれている海峡はどれですか？", "The English Channel|イギリス海峡",
  ["The Bosporus|ボスポラス海峡", "The Strait of Malacca|マラッカ海峡", "The Bering Strait|ベーリング海峡"], tags=["geo", "ocr"], diff="hard")
