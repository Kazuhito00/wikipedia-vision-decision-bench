# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0001-h0040 (pictures used by BOTH the English and the Japanese article).
Every answer was fixed by looking at the picture."""
from templates import Q, N, TYPE, S, colour

Q("h0001", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Moby-Dick|白鯨",
  ["Pride and Prejudice|高慢と偏見", "Hamlet|ハムレット", "Dracula|吸血鬼ドラキュラ"], tags=["ocr", "book"])
Q("h0002", "Which food is shown?", "写っている食べ物はどれですか？", "Meat|肉", ["Bread|パン", "Cheese|チーズ", "Fruit|果物"], tags=["classify", "food"], diff="easy")
TYPE("h0004", "painting", ["photo", "diagram", "satellite"])
TYPE("h0005", "satellite", ["painting", "diagram", "map"], diff="medium")
Q("h0006", "In which language is this title page written?", "この表紙はどの言語で書かれていますか？", "Russian|ロシア語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0007", "What does the sign say?", "プラカードには何と書かれていますか？", "VOTES FOR WOMEN",
  ["STOP THE WAR", "FREE SPEECH", "WORKERS UNITE"], tags=["ocr", "sign"])
N("h0007", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0008", "Which animal is shown?", "どの動物が写っていますか？", "Dolphin|イルカ", ["Shark|サメ", "Seal|アザラシ", "Penguin|ペンギン"], tags=["classify", "animal"])
TYPE("h0009", "space", ["photo", "painting", "map"], diff="medium")
Q("h0010", "Which plant is shown?", "どの植物が写っていますか？", "Cotton|綿（コットン）", ["Wheat|小麦", "Rice|稲", "Corn|トウモロコシ"], tags=["classify", "plant"])
Q("h0011", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Pride and Prejudice|高慢と偏見",
  ["Moby-Dick|白鯨", "Gulliver's Travels|ガリバー旅行記", "Jane Eyre|ジェーン・エア"], tags=["ocr", "book"])
TYPE("h0012", "diagram", ["photo", "painting", "map"])
TYPE("h0013", "painting", ["photo", "diagram", "satellite"])
TYPE("h0014", "space", ["photo", "painting", "map"], diff="medium")
Q("h0015", "What is the overall shape of the large facility?", "この大きな施設の全体の形はどれですか？", "A ring|輪（円形）",
  ["A square|正方形", "A triangle|三角形", "A straight line|直線"], tags=["shape"], diff="medium")
Q("h0016", "What kind of structure crosses the water in this satellite view?", "この衛星画像で、水面をまたいでいる構造物は何ですか？", "A dam|ダム",
  ["A tower|塔", "A lighthouse|灯台", "A tunnel entrance|トンネルの入口"], tags=["classify", "structure"], diff="hard")
Q("h0017", "What kind of building is this?", "これはどんな建物ですか？", "An office building|オフィスビル",
  ["A castle|城", "A barn|納屋", "A church|教会"], tags=["classify", "structure"])
Q("h0018", "Which board game is shown?", "どのボードゲームが写っていますか？", "Backgammon|バックギャモン",
  ["Chess|チェス", "Go|囲碁", "Checkers|チェッカー"], tags=["classify", "game"], diff="medium")
Q("h0019", "Which ocean is named in the diagram?", "図に名前が書かれている海洋はどれですか？", "The Pacific Ocean|太平洋",
  ["The Atlantic Ocean|大西洋", "The Indian Ocean|インド洋", "The Arctic Ocean|北極海"], tags=["ocr", "diagram"])
Q("h0021", "What is the woman doing?", "女性は何をしていますか？", "Singing|歌っている",
  ["Reading|読書している", "Cooking|料理している", "Swimming|泳いでいる"], tags=["action"])
N("h0021", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0023", "Which country does this island belong to?", "この島はどの国に属していますか？", "Japan|日本",
  ["Italy|イタリア", "New Zealand|ニュージーランド", "Ireland|アイルランド"], tags=["geo"], diff="hard")
TYPE("h0024", "space", ["photo", "painting", "satellite"], diff="medium")
N("h0025", "A baby is in the picture", "写真に赤ちゃんが写っている", True)
S("h0027", "ship", "vehicle")
TYPE("h0028", "satellite", ["photo", "map", "painting"], diff="medium")
Q("h0029", "Which animal is shown?", "どの動物が写っていますか？", "Bison|バイソン", ["Horse|馬", "Deer|シカ", "Pig|豚"], tags=["classify", "animal"], diff="medium")
S("h0030", "tower", "structure")
TYPE("h0031", "page", ["photo", "map", "satellite"])
Q("h0032", "Which sport is being played?", "どのスポーツをしていますか？", "Golf|ゴルフ", ["Tennis|テニス", "Baseball|野球", "Soccer|サッカー"], tags=["classify", "sport"])
Q("h0033", "What objects are shown on the plate?", "図版には何が描かれていますか？", "Feathers|羽根", ["Leaves|葉", "Shells|貝殻", "Flowers|花"], tags=["classify", "object"], diff="medium")
colour("h0035", "the flowers", "花", "white", ["red", "yellow", "blue"], tags=("colour", "attribute"))
Q("h0040", "What is this object?", "これは何ですか？", "A truffle|トリュフ", ["An apple|りんご", "An egg|卵", "A tomato|トマト"], tags=["classify", "food"], diff="medium")
