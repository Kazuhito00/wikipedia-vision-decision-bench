# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0701-h0760 (pictures used by the Japanese article only).
Camps, corpses, autopsies, trials, soldiers, spies, anatomy and photographs of children were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0702", "map", ["photo", "painting", "satellite"])
Q("h0703", "Which instrument is shown?", "どの楽器が写っていますか？", "A harpsichord|チェンバロ", ["A violin|バイオリン", "A drum|ドラム", "A flute|フルート"], tags=["classify", "object"], diff="hard")
Q("h0704", "What kind of screen is this?", "これはどんな画面ですか？", "A website login page|ウェブサイトのログイン画面",
  ["A weather map|天気図", "A calendar|カレンダー", "A shopping list|買い物リスト"], tags=["classify", "object"], diff="medium")
Q("h0704", "Which website name appears at the top left?", "左上に表示されているサイト名はどれですか？", "facebook", ["twitter", "youtube", "instagram"], tags=["ocr"])
Q("h0705", "What is the object?", "これは何ですか？", "A ruler|定規", ["A comb|くし", "A knife|ナイフ", "A spoon|スプーン"], tags=["classify", "object"])
Q("h0708", "What is shown?", "何が写っていますか？", "A marble bust|大理石の胸像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"])
Q("h0709", "In which language is the text written?", "文章はどの言語で書かれていますか？", "English|英語",
  ["French|フランス語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"])
TYPE("h0710", "painting", ["photo", "diagram", "satellite"])
TYPE("h0712", "diagram", ["photo", "painting", "satellite"])
Q("h0713", "What kind of landscape is this?", "これはどんな景色ですか？", "A layered cliff by the sea|海辺の層状の崖",
  ["A city|都市", "A farm field|畑", "A forest|森"], tags=["scene"], diff="medium")
Q("h0714", "How many men are shown?", "描かれている男性は何人ですか？", "Four|4 人", ["Two|2 人", "Three|3 人", "Six|6 人"], tags=["count"], diff="medium")
TYPE("h0715", "map", ["photo", "painting", "satellite"])
Q("h0716", "What does the sculpture show?", "この彫刻は何を表していますか？", "A melting clock|溶けた時計",
  ["A burning candle|燃えるろうそく", "A bent bicycle|曲がった自転車", "A flower pot|植木鉢"], tags=["classify", "object"], diff="medium")
TYPE("h0718", "map", ["photo", "painting", "satellite"])
Q("h0719", "Which vegetable is shown?", "どの野菜が写っていますか？", "Pumpkins|カボチャ", ["Cabbages|キャベツ", "Potatoes|じゃがいも", "Apples|りんご"], tags=["classify", "food"])
Q("h0720", "What fills the sky above the houses?", "家々の上の空を覆っているものは何ですか？", "A huge dust cloud|巨大な砂ぼこりの雲",
  ["Snow|雪", "Smoke from a factory|工場の煙", "Fog over a lake|湖の霧"], tags=["scene"], diff="medium")
N("h0720", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
TYPE("h0721", "painting", ["photo", "diagram", "satellite"], diff="medium")
TYPE("h0722", "painting", ["photo", "diagram", "satellite"], diff="medium")
Q("h0723", "Which birds are shown?", "どの鳥が描かれていますか？", "Pigeons|ハト", ["Penguins|ペンギン", "Owls|フクロウ", "Ducks|アヒル"], tags=["classify", "animal"], diff="medium")
Q("h0724", "Which writing system is on the scroll fragment?", "巻物の断片に書かれている文字は何ですか？", "Hebrew|ヘブライ文字",
  ["Chinese characters|漢字", "Latin letters|ラテン文字", "Cyrillic letters|キリル文字"], tags=["ocr", "script"], diff="hard")
Q("h0725", "What device is shown?", "これは何の装置ですか？", "A barcode scanner|バーコードリーダー",
  ["A computer mouse|マウス", "A telephone|電話機", "A hair dryer|ヘアドライヤー"], tags=["classify", "object"], diff="medium")
TYPE("h0726", "drawing", ["photo", "satellite", "map"])
Q("h0727", "Which animal is shown?", "どの動物が写っていますか？", "A damselfly|イトトンボ", ["A butterfly|チョウ", "A bee|ミツバチ", "A beetle|甲虫"], tags=["classify", "animal"], diff="medium")
Q("h0728", "What is the object?", "これは何ですか？", "Binoculars|双眼鏡", ["A microphone|マイク", "A toaster|トースター", "A teapot|ティーポット"], tags=["classify", "object"])
Q("h0729", "How many screens are on the desk?", "机の上の画面はいくつありますか？", "Two|2 つ", ["One|1 つ", "Three|3 つ", "Four|4 つ"], tags=["count"], diff="medium")
TYPE("h0730", "painting", ["photo", "diagram", "satellite"])
colour("h0731", "the flowers", "花", "pink", ["blue", "yellow", "green"], tags=("colour", "attribute"))
Q("h0732", "What measuring tool is shown?", "どんな測定器具が写っていますか？", "A tape measure|巻き尺",
  ["A thermometer|温度計", "A weighing scale|はかり", "A clock|時計"], tags=["classify", "object"])
N("h0732", "There are two coins in the picture", "写真にコインが 2 枚ある", True, tags=["count"], diff="medium")
Q("h0733", "What spans the river?", "川にかかっているものは何ですか？", "Bridges|橋", ["Dams|ダム", "Tunnels|トンネル", "Piers only|桟橋だけ"], tags=["scene"], diff="medium")
Q("h0734", "What is the hand holding?", "手に持っているものは何ですか？", "A glass of brandy|ブランデーのグラス",
  ["A cup of coffee|コーヒーカップ", "A bowl of soup|スープ皿", "A milk bottle|牛乳瓶"], tags=["detail"], diff="medium")
Q("h0737", "What is shown?", "何が写っていますか？", "A tiny electronic device|小さな電子装置", ["A flower|花", "A seashell|貝殻", "A coin|硬貨"], tags=["classify", "object"], diff="hard")
TYPE("h0738", "map", ["photo", "painting", "satellite"])
Q("h0739", "Which activity is shown?", "何をしている場面ですか？", "Tug of war|綱引き", ["Soccer|サッカー", "Rowing|ボート競技", "Golf|ゴルフ"], tags=["classify", "sport"], diff="medium")
TYPE("h0741", "drawing", ["photo", "satellite", "map"], diff="medium")
TYPE("h0742", "painting", ["photo", "diagram", "satellite"])
Q("h0743", "What is the book title?", "本の題名は何ですか？", "Little Women|若草物語",
  ["Pride and Prejudice|高慢と偏見", "Jane Eyre|ジェーン・エア", "Moby-Dick|白鯨"], tags=["ocr", "book"], diff="medium")
colour("h0743", "the book covers", "本の表紙", "green", ["red", "blue", "yellow"], tags=("colour", "attribute"))
TYPE("h0744", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0748", "Which bird is shown?", "どの鳥が写っていますか？", "An ibis|トキの仲間", ["A penguin|ペンギン", "An owl|フクロウ", "A duck|アヒル"], tags=["classify", "animal"], diff="hard")
Q("h0749", "Which insects are shown?", "どの昆虫が写っていますか？", "Bees|ミツバチ", ["Ants|アリ", "Butterflies|チョウ", "Ladybugs|てんとう虫"], tags=["classify", "animal"])
Q("h0751", "What is shown?", "何が写っていますか？", "A world map made from satellite images|衛星画像で作った世界地図",
  ["A road map of a city|市街地図", "A star chart|星図", "A floor plan|間取り図"], tags=["image-type"], diff="medium")
Q("h0754", "Which animal is shown?", "どの動物が写っていますか？", "A lizard-like reptile (tuatara)|トカゲに似た爬虫類（ムカシトカゲ）",
  ["A frog|カエル", "A snake|ヘビ", "A mouse|ネズミ"], tags=["classify", "animal"], diff="hard")
TYPE("h0755", "painting", ["photo", "diagram", "satellite"])
Q("h0756", "Which bird is shown?", "どの鳥が写っていますか？", "A condor|コンドル", ["A penguin|ペンギン", "A duck|アヒル", "An owl|フクロウ"], tags=["classify", "animal"], diff="medium")
N("h0756", "The bird's wings are spread", "鳥は翼を広げている", True, tags=["attribute"])
Q("h0758", "In which language is the title page written?", "表紙はどの言語で書かれていますか？", "German|ドイツ語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
Q("h0759", "What stands on the launch pad?", "発射台に立っているものは何ですか？", "A rocket|ロケット",
  ["A lighthouse|灯台", "A tower crane|クレーン", "A skyscraper|超高層ビル"], tags=["classify", "vehicle"])
Q("h0760", "What is the object?", "これは何ですか？", "A piece of jade (green stone)|翡翠（緑の石）",
  ["A piece of soap|石けん", "A candle|ろうそく", "A lump of butter|バター"], tags=["classify", "object"], diff="hard")
