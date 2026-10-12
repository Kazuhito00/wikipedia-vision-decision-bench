# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0221-h0280 (pictures used by both wikis). Pictures of victims, riots,
massacres, disasters' aftermath and medical close-ups were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0221", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0223", "What objects are shown?", "何が描かれていますか？", "Eggs|卵", ["Seeds|種", "Stones|石", "Buttons|ボタン"], tags=["classify", "object"])
Q("h0224", "What objects are drawn?", "何が描かれていますか？", "Shields|盾", ["Flags|旗", "Keys|鍵", "Hats|帽子"], tags=["classify", "object"], diff="medium")
TYPE("h0226", "map", ["photo", "painting", "satellite"])
Q("h0227", "What is this instrument used for?", "この器具は何に使いますか？", "Navigation at sea|航海での位置の測定",
  ["Cooking|料理", "Gardening|園芸", "Playing music|演奏"], tags=["detail"], diff="hard")
Q("h0228", "What is sinking in the picture?", "絵の中で沈んでいるのは何ですか？", "A ship|船", ["An airplane|飛行機", "A train|電車", "A house|家"], tags=["classify", "vehicle"])
Q("h0230", "What is the name of the newspaper?", "新聞の題号は何ですか？", "Le Monde|ル・モンド",
  ["Asahi Shimbun|朝日新聞", "The Times|タイムズ", "Pravda|プラウダ"], tags=["ocr"], diff="medium")
Q("h0231", "In which language is the cover written?", "表紙はどの言語で書かれていますか？", "English|英語",
  ["French|フランス語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0232", "What shape is the island?", "この島はどんな形ですか？", "Oval|楕円形", ["Star-shaped|星形", "Square|四角形", "Ring-shaped|輪の形"], tags=["shape"], diff="medium")
Q("h0233", "What does the sign list?", "看板には何が書かれていますか？", "Interest rates|金利",
  ["Train times|列車の時刻", "Menu prices|メニューの価格", "Weather forecast|天気予報"], tags=["ocr", "sign"], diff="medium")
colour("h0233", "the sign's background", "看板の背景", "red", ["blue", "green", "yellow"], tags=("colour", "attribute"))
Q("h0234", "What is in the round case?", "丸いケースに入っているものは何ですか？", "Tablets|錠剤", ["Candies|飴", "Coins|硬貨", "Buttons|ボタン"], tags=["classify", "object"], diff="hard")
TYPE("h0236", "space", ["photo", "painting", "map"], diff="medium")
Q("h0238", "What kind of facility is this?", "これはどんな施設ですか？", "An industrial plant|工場（工業地帯）",
  ["A farm|農場", "A school|学校", "A beach resort|ビーチリゾート"], tags=["scene"])
Q("h0239", "Which animal is shown?", "どの動物が写っていますか？", "Killer whale|シャチ", ["Shark|サメ", "Seal|アザラシ", "Penguin|ペンギン"], tags=["classify", "animal"], diff="medium")
Q("h0239", "What colours is the animal?", "動物は何色ですか？", "Black and white|白と黒", ["Red and blue|赤と青", "All green|緑一色", "Brown|茶色"], tags=["colour", "attribute"])
TYPE("h0240", "painting", ["photo", "diagram", "satellite"])
Q("h0241", "Which language is the printed text?", "印刷されている文章はどの言語ですか？", "Japanese|日本語",
  ["Korean|韓国語", "Arabic|アラビア語", "Russian|ロシア語"], tags=["ocr", "language"], diff="medium")
Q("h0242", "Which continent is shown?", "写っている大陸はどれですか？", "Antarctica|南極大陸",
  ["Africa|アフリカ", "Australia|オーストラリア", "Europe|ヨーロッパ"], tags=["geo"])
Q("h0243", "What shape does the large galaxy have?", "大きな銀河はどんな形をしていますか？", "A spiral|渦巻き",
  ["A ring|輪", "A cross|十字", "A square|四角形"], tags=["shape"])
TYPE("h0244", "space", ["photo", "painting", "map"], diff="medium")
Q("h0245", "Which animals are on the wood?", "木の上にいる動物はどれですか？", "Ants|アリ", ["Bees|ミツバチ", "Beetles|甲虫", "Flies|ハエ"], tags=["classify", "animal"], diff="medium")
Q("h0246", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Middlemarch|ミドルマーチ",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Dracula|吸血鬼ドラキュラ"], tags=["ocr", "book"])
Q("h0248", "In which language is the document written?", "文書はどの言語で書かれていますか？", "English|英語",
  ["French|フランス語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0249", "Which painting is this?", "これはどの絵画ですか？", "The Starry Night|星月夜",
  ["Mona Lisa|モナ・リザ", "The Scream|叫び", "Girl with a Pearl Earring|真珠の耳飾りの少女"], tags=["classify", "art"], diff="medium")
Q("h0250", "In which script is the text written?", "文章はどの文字で書かれていますか？", "Chinese characters|漢字",
  ["Latin letters|ラテン文字", "Arabic script|アラビア文字", "Cyrillic letters|キリル文字"], tags=["ocr", "script"])
Q("h0251", "Which drink is in the tall glass?", "背の高いグラスに入っている飲み物はどれですか？", "Milk|牛乳",
  ["Beer|ビール", "Red wine|赤ワイン", "Orange juice|オレンジジュース"], tags=["classify", "food"], diff="medium")
N("h0251", "There is meat in the picture", "写真に肉が写っている", False, tags=["presence"])
Q("h0253", "What is shown?", "何が写っていますか？", "A lump of metal|金属の塊",
  ["A loaf of bread|パン", "A piece of wood|木片", "A bag of salt|塩の袋"], tags=["classify", "object"], diff="medium")
Q("h0254", "What is the man doing?", "男性は何をしていますか？", "Posing to show his muscles|筋肉を見せるポーズをとっている",
  ["Swimming|泳いでいる", "Playing the piano|ピアノを弾いている", "Riding a bicycle|自転車に乗っている"], tags=["action"], diff="medium")
N("h0254", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
S("h0255", "sheep", "animal")
Q("h0256", "What are the hands wearing?", "手は何を身につけていますか？", "Gloves|手袋", ["Rings|指輪", "Watches|腕時計", "Bracelets|ブレスレット"], tags=["detail"], diff="medium")
colour("h0256", "the gloves", "手袋", "orange", ["blue", "green", "white"], tags=("colour", "attribute"))
Q("h0257", "What is the title printed on this page?", "このページに印刷されている題名は何ですか？", "On the Origin of Species|種の起源",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Das Kapital|資本論"], tags=["ocr", "book"], diff="medium")
TYPE("h0258", "painting", ["photo", "diagram", "satellite"], diff="medium")
TYPE("h0260", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0261", "Where is this?", "ここはどこですか？", "A library reading room|図書館の閲覧室",
  ["A swimming pool|プール", "A kitchen|台所", "A train station|駅"], tags=["scene"])
Q("h0264", "Which sport is shown?", "どのスポーツですか？", "American football|アメリカンフットボール",
  ["Soccer|サッカー", "Tennis|テニス", "Swimming|水泳"], tags=["classify", "sport"])
TYPE("h0265", "diagram", ["photo", "painting", "satellite"], diff="medium")
Q("h0271", "In which language is the letter written?", "手紙はどの言語で書かれていますか？", "English|英語",
  ["French|フランス語", "German|ドイツ語", "Japanese|日本語"], tags=["ocr", "language"])
Q("h0272", "Where is this?", "ここはどこですか？", "A lecture hall|講義室", ["A swimming pool|プール", "A kitchen|台所", "A train station|駅"], tags=["scene"])
N("h0272", "There is a blackboard in the picture", "写真に黒板がある", True, tags=["presence"])
Q("h0274", "Which fruit is shown?", "どの果物が写っていますか？", "Pears|洋なし", ["Apples|りんご", "Bananas|バナナ", "Grapes|ぶどう"], tags=["classify", "food"], diff="medium")
Q("h0275", "What are the small round objects?", "小さな丸い物は何ですか？", "Tablets|錠剤", ["Coins|硬貨", "Cookies|クッキー", "Buttons|ボタン"], tags=["classify", "object"], diff="hard")
TYPE("h0277", "map", ["photo", "painting", "satellite"])
Q("h0279", "What instrument stands on the tripod?", "三脚の上の機器は何ですか？", "A surveying instrument|測量機器",
  ["A camera|カメラ", "A star telescope|天体望遠鏡", "A microphone|マイク"], tags=["detail"], diff="hard")
