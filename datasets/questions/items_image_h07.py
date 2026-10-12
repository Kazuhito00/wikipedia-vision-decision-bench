# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0356-h0400. From here on every picture belongs to ONE wiki
(E = used by the English article only, J = used by the Japanese article only); the compiler keeps only the language(s)
the picture is really used in, so the question is written in both languages but published in one or both.
Pictures with soldiers in action, weapons and people in distress were left out on purpose."""
from templates import Q, N, TYPE, S, colour

TYPE("h0356", "painting", ["photo", "diagram", "satellite"])
Q("h0356", "What are the dancers wearing?", "踊り手たちは何を着ていますか？", "Tutus (ballet skirts)|チュチュ（バレエの衣装）",
  ["Kimonos|着物", "Winter coats|冬のコート", "Swimsuits|水着"], tags=["detail"], diff="medium")
Q("h0357", "What is the object made of?", "この物は何でできていますか？", "Clay|粘土", ["Metal|金属", "Paper|紙", "Glass|ガラス"], tags=["classify", "object"], diff="medium")
Q("h0358", "In which language is the title page written?", "表紙はどの言語で書かれていますか？", "Latin|ラテン語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="hard")
Q("h0360", "Which instrument is shown?", "どの楽器が写っていますか？", "A mandolin|マンドリン",
  ["A trumpet|トランペット", "A drum|ドラム", "A flute|フルート"], tags=["classify", "object"], diff="medium")
TYPE("h0361", "drawing", ["photo", "satellite", "map"])
Q("h0362", "What natural feature runs through the landscape?", "景色の中を流れている自然のものは何ですか？", "A river|川",
  ["A glacier|氷河", "A desert|砂漠", "A volcano|火山"], tags=["scene"])
TYPE("h0363", "painting", ["photo", "diagram", "satellite"])
Q("h0364", "What kind of view is this?", "これはどんな眺めですか？", "An aerial view of a city|都市の空撮",
  ["A forest|森", "A beach|ビーチ", "A mountain range|山脈"], tags=["scene"])
Q("h0366", "What is the large vehicle on the water?", "水上の大きな乗り物は何ですか？", "A ship|船",
  ["A train|電車", "A bus|バス", "A tractor|トラクター"], tags=["classify", "vehicle"])
N("h0366", "An aircraft is flying above the ship", "船の上を航空機が飛んでいる", True, tags=["scene"])
N("h0366", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0367", "What kind of picture is this?", "これはどんな種類の絵ですか？", "A theatre poster|劇場のポスター",
  ["A map|地図", "A satellite image|衛星画像", "A chart|グラフ"], tags=["image-type"], diff="medium")
Q("h0368", "What does the microscope picture show?", "顕微鏡写真には何が写っていますか？", "Pollen grains|花粉",
  ["Snowflakes|雪の結晶", "Grains of rice|米粒", "Soap bubbles|シャボン玉"], tags=["classify", "object"], diff="hard")
Q("h0369", "What kind of scene is this?", "これはどんな景色ですか？", "A city with tall buildings|高層ビルのある都市",
  ["A desert|砂漠", "A farm|農場", "A forest|森"], tags=["scene"])
N("h0369", "There is a lake or pond in the picture", "写真に池または湖がある", True, tags=["scene"], diff="medium")
Q("h0370", "What is the man doing?", "男性は何をしていますか？", "Lifting a barbell|バーベルを持ち上げている",
  ["Swimming|泳いでいる", "Playing the piano|ピアノを弾いている", "Riding a horse|馬に乗っている"], tags=["action"])
Q("h0371", "What kind of landscape is this?", "これはどんな景色ですか？", "Forested mountains|森に覆われた山",
  ["A desert|砂漠", "A city street|市街地", "A snowfield|雪原"], tags=["scene"])
Q("h0373", "What kind of products are these?", "これらはどんな製品ですか？", "Adhesives (glue)|接着剤",
  ["Toothpaste|歯みがき粉", "Paints for walls|壁用ペンキ", "Soft drinks|清涼飲料"], tags=["classify", "object"], diff="hard")
Q("h0375", "What kind of image is this?", "これはどんな種類の画像ですか？", "An old engraving|古い版画（線画）",
  ["A modern photograph|現代の写真", "A satellite image|衛星画像", "A map|地図"], tags=["image-type"], diff="medium")
Q("h0376", "What kind of building is this?", "これはどんな建物ですか？", "A large historic building with towers|塔のある歴史的な大きな建物",
  ["A wooden barn|木造の納屋", "A glass skyscraper|ガラス張りの高層ビル", "A tent|テント"], tags=["classify", "structure"], diff="medium")
Q("h0378", "Which gulf is shown on the map?", "地図に示されている湾はどれですか？", "The Gulf of Mexico|メキシコ湾",
  ["The Persian Gulf|ペルシア湾", "The Gulf of Bothnia|ボスニア湾", "The Bay of Bengal|ベンガル湾"], tags=["ocr", "map"], diff="medium")
TYPE("h0378", "map", ["photo", "painting", "satellite"])
Q("h0379", "What is the woman on the vase holding?", "壺に描かれた女性は何を持っていますか？", "A lyre|竪琴",
  ["A fan|扇","A basket|かご", "A sword|剣"], tags=["detail"], diff="hard")
Q("h0380", "Which natural feature is shown?", "どの自然の景観が写っていますか？", "A waterfall|滝",
  ["A volcano|火山", "A glacier|氷河", "A desert|砂漠"], tags=["classify", "scene"])
TYPE("h0381", "painting", ["photo", "diagram", "satellite"])
Q("h0381", "What is the man in the painting standing on?", "絵の中の男性は何の上に立っていますか？", "A rocky peak above the fog|霧の上にそびえる岩の頂",
  ["A boat|舟", "A bridge|橋", "A roof|屋根"], tags=["detail"], diff="medium")
Q("h0383", "How was this colourful picture produced?", "このカラフルな画像はどのようにして作られましたか？", "With an electron microscope and added colour|電子顕微鏡で撮影し、着色した",
  ["With a phone camera|携帯電話のカメラ", "By a satellite|人工衛星", "With a drawing pen|ペン画"], tags=["image-type"], diff="hard")
Q("h0385", "What kind of scene is this?", "これはどんな景色ですか？", "A city skyline|都市の景色", ["A forest|森", "A desert|砂漠", "A beach|ビーチ"], tags=["classify", "scene"])
N("h0386", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h0387", "What is shown?", "何が写っていますか？", "A bronze sculpture|ブロンズ像", ["A painting|絵画", "A building|建物", "A tree|木"], tags=["classify", "object"])
Q("h0388", "What is shown?", "何が写っていますか？", "A garage with two cars|車が 2 台入ったガレージ",
  ["A greenhouse|温室", "A barn with animals|動物のいる納屋", "A tent|テント"], tags=["classify", "structure"], diff="medium")
N("h0388", "There are two cars in the picture", "写真に車が 2 台ある", True, tags=["count"], diff="medium")
TYPE("h0391", "diagram", ["photo", "painting", "satellite"])
Q("h0393", "What are the men doing?", "男性たちは何をしていますか？", "Standing in formation|整列して立っている",
  ["Swimming|泳いでいる", "Cooking|料理している", "Dancing|踊っている"], tags=["action"], diff="medium")
Q("h0394", "What kind of image is this?", "これはどんな種類の画像ですか？", "A colourful painted picture|色鮮やかな彩色画",
  ["A satellite image|衛星画像", "A black-and-white photograph|白黒写真", "A map|地図"], tags=["image-type"], diff="medium")
N("h0395", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
TYPE("h0396", "diagram", ["photo", "painting", "satellite"])
Q("h0398", "Which planet is shown?", "どの惑星が写っていますか？", "Mercury|水星", ["Jupiter|木星", "Saturn|土星", "Earth|地球"], tags=["classify", "space"], diff="hard")
Q("h0400", "Which country do these islands belong to?", "この島々はどの国に属していますか？", "New Zealand|ニュージーランド",
  ["Japan|日本", "Italy|イタリア", "Ireland|アイルランド"], tags=["geo"], diff="hard")
