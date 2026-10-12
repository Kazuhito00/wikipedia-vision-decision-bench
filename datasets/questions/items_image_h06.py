# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0281-h0355 (the last pictures used by BOTH wikis). Pictures of people in
distress (resuscitation, patients, victims, arrests, earthquake ruins) were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h0282", "Which language is the text written in?", "文章はどの言語で書かれていますか？", "Latin|ラテン語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
Q("h0284", "What are the men doing?", "男性たちは何をしていますか？", "Singing|歌っている",
  ["Cooking|料理している", "Swimming|泳いでいる", "Fishing|釣りをしている"], tags=["action"])
N("h0284", "The men are wearing white uniforms", "男性たちは白い制服を着ている", True, tags=["attribute"])
TYPE("h0287", "drawing", ["photo", "satellite", "painting"], diff="medium")
Q("h0288", "Which island is shown?", "写っている島はどれですか？", "Ireland|アイルランド",
  ["Iceland|アイスランド", "Sicily|シチリア島", "Hokkaido|北海道"], tags=["geo"], diff="hard")
TYPE("h0289", "drawing", ["photo", "satellite", "map"], diff="medium")
N("h0293", "Soldiers are standing in formation", "兵士たちが整列して立っている", True, tags=["scene"])
N("h0293", "The picture was taken on a beach", "この写真は海辺で撮影された", False, tags=["scene"])
Q("h0294", "What is shown?", "何が写っていますか？", "An aircraft engine with a propeller|プロペラ付きの航空機エンジン",
  ["A car seat|自動車の座席", "A washing machine|洗濯機", "A piano|ピアノ"], tags=["classify", "object"], diff="medium")
colour("h0294", "the propeller cap", "プロペラ先端のカバー", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
Q("h0296", "What is shown?", "何が写っていますか？", "A fish tank with plants|水草のある水槽",
  ["A greenhouse|温室", "A swimming pool|プール", "A bathtub|浴槽"], tags=["classify", "object"], diff="medium")
Q("h0297", "What is the object?", "これは何ですか？", "A folded cloth|折りたたまれた布",
  ["A sheet of paper|紙", "A plate|皿", "A pillow|枕"], tags=["classify", "object"], diff="medium")
Q("h0299", "What is the profession of the person in blue?", "青い服の人の職業は何ですか？", "A dentist|歯科医",
  ["A chef|料理人", "A pilot|パイロット", "A teacher|教師"], tags=["action"], diff="medium")
Q("h0301", "What colour are the flowers along the path?", "通路沿いの花は何色ですか？", "Red|赤",
  ["Blue|青", "Yellow|黄", "White|白"], tags=["colour", "attribute"])
Q("h0302", "Whose name is on the record label?", "レコードのラベルには誰の名前が書かれていますか？", "Bob Dylan|ボブ・ディラン",
  ["Elvis Presley|エルヴィス・プレスリー", "The Beatles|ビートルズ", "Michael Jackson|マイケル・ジャクソン"], tags=["ocr"])
TYPE("h0305", "map", ["photo", "painting", "satellite"], diff="medium")
Q("h0308", "Which sport is shown?", "どのスポーツですか？", "Kickboxing|キックボクシング", ["Swimming|水泳", "Tennis|テニス", "Skiing|スキー"], tags=["classify", "sport"])
Q("h0310", "In which language is the poster written?", "ポスターはどの言語で書かれていますか？", "Russian|ロシア語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0311", "Which sea is at the centre of the picture?", "写真の中央にある海はどれですか？", "The Mediterranean Sea|地中海",
  ["The Red Sea|紅海", "The Baltic Sea|バルト海", "The Caspian Sea|カスピ海"], tags=["geo"], diff="medium")
Q("h0312", "Which fruit is shown?", "どの果物が写っていますか？", "Cranberries|クランベリー",
  ["Bananas|バナナ", "Oranges|オレンジ", "Grapes|ぶどう"], tags=["classify", "food"], diff="medium")
Q("h0313", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Lolita|ロリータ",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Dracula|吸血鬼ドラキュラ"], tags=["ocr", "book"])
Q("h0315", "In which language is the title page written?", "この表紙はどの言語で書かれていますか？", "French|フランス語",
  ["English|英語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
TYPE("h0316", "space", ["photo", "painting", "map"], diff="medium")
Q("h0317", "Which sport is shown?", "どのスポーツですか？", "Curling|カーリング",
  ["Ice hockey|アイスホッケー", "Skiing|スキー", "Swimming|水泳"], tags=["classify", "sport"], diff="medium")
N("h0317", "The event takes place on ice", "この競技は氷の上で行われている", True, tags=["scene"], diff="medium")
Q("h0319", "Which planet is shown?", "どの惑星が写っていますか？", "Uranus|天王星", ["Mars|火星", "Jupiter|木星", "Saturn|土星"], tags=["classify", "space"], diff="hard")
Q("h0320", "What is the main subject of the picture?", "この絵の主題は何ですか？", "A huge wave|大きな波",
  ["A snowstorm|吹雪", "A forest fire|山火事", "A crowd|群衆"], tags=["classify", "scene"])
Q("h0322", "What passes through the glass block?", "ガラスのブロックを通っているのは何ですか？", "A beam of light|光線",
  ["Water|水", "Smoke|煙", "A rope|ロープ"], tags=["detail"], diff="medium")
Q("h0323", "What is the man standing next to?", "男性は何のそばに立っていますか？", "A synthesizer|シンセサイザー",
  ["A washing machine|洗濯機", "A refrigerator|冷蔵庫", "A bookshelf|本棚"], tags=["detail"], diff="medium")
N("h0323", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0324", "What is reflected in the lake?", "湖に映っているものは何ですか？", "Snowy mountains|雪山",
  ["A city|都市", "A rainbow|虹", "A ship|船"], tags=["scene"])
N("h0324", "There is snow on the mountain", "山に雪がある", True, tags=["scene"])
TYPE("h0328", "painting", ["photo", "diagram", "satellite"])
TYPE("h0330", "map", ["photo", "painting", "satellite"])
Q("h0332", "Where is the astronaut?", "宇宙飛行士はどこにいますか？", "In space above the Earth|地球の上空の宇宙空間",
  ["Under the sea|海の中", "In a cave|洞窟の中", "On a mountain|山の上"], tags=["scene"])
Q("h0333", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Jane Eyre|ジェーン・エア",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Dracula|吸血鬼ドラキュラ"], tags=["ocr", "book"])
Q("h0334", "What are the large objects standing in the grass?", "草地に立っている大きなものは何ですか？", "Stones|巨石",
  ["Trees|木", "Houses|家", "Cars|自動車"], tags=["classify", "object"])
Q("h0336", "What is shown?", "何が写っていますか？", "A satellite|人工衛星", ["A watch|腕時計", "A balloon|風船", "A lamp|ランプ"], tags=["classify", "object"], diff="medium")
TYPE("h0338", "painting", ["photo", "diagram", "satellite"])
Q("h0340", "What is the winding feature?", "曲がりくねっているものは何ですか？", "A river|川", ["A road|道路", "A railway|鉄道", "A pipeline|パイプライン"], tags=["scene"], diff="medium")
Q("h0341", "Which animal is shown?", "どの動物が写っていますか？", "Shark|サメ", ["Dolphin|イルカ", "Turtle|カメ", "Octopus|タコ"], tags=["classify", "animal"])
N("h0341", "The animal is underwater", "動物は水中にいる", True)
Q("h0343", "What kind of building is this?", "これはどんな建物ですか？", "A tall office building|高層のオフィスビル",
  ["A castle|城", "A barn|納屋", "A church|教会"], tags=["classify", "structure"])
Q("h0344", "What is the name of the magazine?", "雑誌の名前は何ですか？", "Lippincott's Monthly Magazine|リッピンコッツ月刊誌",
  ["National Geographic|ナショナル ジオグラフィック", "Time|タイム", "Vogue|ヴォーグ"], tags=["ocr"], diff="hard")
Q("h0345", "Which body of water is shown?", "写っている海域はどれですか？", "The Persian Gulf|ペルシア湾",
  ["The Gulf of Mexico|メキシコ湾", "The Baltic Sea|バルト海", "The Bay of Bengal|ベンガル湾"], tags=["geo"], diff="hard")
Q("h0347", "What shape do the clouds form?", "雲はどんな形をしていますか？", "A spiral|渦巻き", ["A square|四角形", "A straight line|直線", "A cross|十字"], tags=["shape"])
Q("h0348", "Which programming language is the code written in?", "このコードはどのプログラミング言語で書かれていますか？", "C",
  ["Python", "JavaScript", "Ruby"], tags=["ocr", "code"], diff="hard")
Q("h0349", "Which animal is shown?", "どの動物が写っていますか？", "Donkey|ロバ", ["Cow|牛", "Sheep|羊", "Dog|犬"], tags=["classify", "animal"], diff="medium")
Q("h0350", "Which region name is written in large letters in the centre?", "中央に大きな文字で書かれている地域名はどれですか？", "BACTRIA",
  ["PERSIA", "EGYPT", "ARABIA"], tags=["ocr", "map"], diff="medium")
TYPE("h0351", "drawing", ["photo", "satellite", "map"], diff="medium")
TYPE("h0353", "space", ["photo", "painting", "map"], diff="medium")
Q("h0354", "Which kind of animals are shown?", "どの種類の動物が写っていますか？", "Fish|魚", ["Birds|鳥", "Dogs|犬", "Insects|昆虫"], tags=["classify", "animal"])
