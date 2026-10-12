# -*- coding: utf-8 -*-
"""Image items, h1468-h1547 (pictures used by the English article only), written for a somewhat demanding set.
Battle scenes, slavery, patients, burials, group portraits of private people and weapons were left out on purpose."""
from templates import Q, N, TYPE, S, colour

Q("h1468", "On which body was this photograph taken?", "この写真はどの天体で撮影されましたか？", "The Moon|月",
  ["Mars|火星", "Earth|地球", "Venus|金星"], tags=["scene"], diff="medium")
Q("h1470", "What is being assembled in the clean room?", "クリーンルームで組み立てられているのは何ですか？", "A spacecraft (probe)|宇宙探査機",
  ["An airplane|飛行機", "A car|自動車", "A submarine|潜水艦"], tags=["classify", "vehicle"], diff="medium")
N("h1470", "The people are wearing white protective suits", "人々は白い防護服を着ている", True, tags=["attribute"])
Q("h1472", "What does this symbol mean?", "このマークは何を意味しますか？", "Recycling|リサイクル", ["Biohazard|バイオハザード", "Radiation|放射線", "Fire exit|非常口"], tags=["classify", "object"], diff="medium")
colour("h1472", "the arrows", "矢印", "green", ["red", "yellow", "white"], tags=("colour", "attribute"))
Q("h1473", "What happened to the trees?", "木々に何が起きましたか？", "They were flattened in one direction|同じ向きになぎ倒された",
  ["They were burnt to ash|灰になった", "They were covered with ice|氷に覆われた", "They were cut into logs|丸太に切られた"], tags=["scene"], diff="medium")
N("h1473", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
Q("h1474", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Wuthering Heights|嵐が丘",
  ["Jane Eyre|ジェーン・エア", "Emma|エマ", "Middlemarch|ミドルマーチ"], tags=["ocr", "book"], diff="medium")
Q("h1475", "Which country is shown on this old map?", "この古い地図に描かれているのはどの国ですか？", "India|インド", ["China|中国", "Brazil|ブラジル", "Egypt|エジプト"], tags=["ocr", "map"], diff="medium")
Q("h1476", "What kind of building is this?", "これはどんな建物ですか？", "A large Victorian-style institution|大きなヴィクトリア様式の施設",
  ["A modern glass skyscraper|現代のガラス張り高層ビル", "A farm barn|農場の納屋", "A wooden cabin|丸太小屋"], tags=["classify", "structure"], diff="hard")
Q("h1478", "What is the instrument?", "これは何の計器ですか？", "A thermometer|温度計", ["A clock|時計", "A barometer|気圧計", "A speedometer|速度計"], tags=["classify", "object"], diff="medium")
Q("h1478", "Which unit appears on the lower scale?", "下の目盛りに書かれている単位はどれですか？", "°F (Fahrenheit)|°F（華氏）",
  ["°C only|°C のみ", "Kelvin|ケルビン", "Pascal|パスカル"], tags=["ocr"], diff="hard")
Q("h1479", "Which culture's art is this?", "これはどの文化の美術ですか？", "Aztec|アステカ", ["Egyptian|エジプト", "Roman|ローマ", "Japanese|日本"], tags=["art"], diff="hard")
Q("h1482", "What decorates the plate?", "皿には何が描かれていますか？", "A plant with fruit|実のなる植物",
  ["A ship|船", "A portrait of a king|王の肖像", "A map|地図"], tags=["detail"], diff="medium")
Q("h1484", "What kind of room is this?", "ここはどんな部屋ですか？", "A space mission control room|宇宙ミッションの管制室",
  ["A classroom|教室", "A courtroom|法廷", "A restaurant|レストラン"], tags=["scene"], diff="hard")
Q("h1486", "Which food is in the bowl?", "器に入っている食べ物はどれですか？", "Mustard|マスタード", ["Butter|バター", "Custard|カスタード", "Mayonnaise|マヨネーズ"], tags=["classify", "food"], diff="hard")
Q("h1487", "What is the object made of?", "この物は何でできていますか？", "Clay|粘土", ["Metal|金属", "Wood|木", "Glass|ガラス"], tags=["classify", "object"], diff="medium")
Q("h1488", "What does the sign near the monument mark?", "記念碑のそばの看板は何を示していますか？", "Sea level|海抜（海水面の高さ）",
  ["A border|国境", "A battle|戦場", "A river source|川の源流"], tags=["ocr", "sign"], diff="hard")
Q("h1490", "What are the two creatures in the medieval picture?", "中世の絵に描かれている 2 つの生き物は何ですか？", "A bird and a dragon|鳥と竜",
  ["Two horses|馬 2 頭", "A deer and a hunter|シカと狩人", "A lion and a lamb|ライオンと子羊"], tags=["detail"], diff="hard")
Q("h1491", "What electronic component is next to the ruler?", "定規のそばにある電子部品は何ですか？", "A capacitor|コンデンサ",
  ["A battery|電池", "A resistor|抵抗器", "A coin|硬貨"], tags=["classify", "object"], diff="hard")
Q("h1493", "Which spacecraft is shown?", "どの宇宙船が写っていますか？", "Soyuz|ソユーズ", ["The Space Shuttle|スペースシャトル", "Apollo|アポロ", "Dragon|ドラゴン"], tags=["classify", "vehicle"], diff="hard")
Q("h1495", "What is this scientific instrument?", "これはどんな科学機器ですか？", "An astrolabe|アストロラーベ",
  ["A compass|方位磁針", "A clock|時計", "A sextant|六分儀"], tags=["classify", "object"], diff="hard")
Q("h1496", "What can be seen through the window?", "窓から何が見えますか？", "The Earth|地球", ["The Moon|月", "A city street|市街地", "A forest|森"], tags=["scene"], diff="medium")
Q("h1498", "Which fish is shown?", "どの魚が写っていますか？", "A salmon|サケ", ["A tuna|マグロ", "A shark|サメ", "A goldfish|金魚"], tags=["classify", "animal"], diff="medium")
Q("h1500", "What kind of ancient structure is this?", "これはどんな古代の建造物ですか？", "A stepped ziggurat|階段状のジッグラト",
  ["A Roman aqueduct|ローマの水道橋", "A Greek theatre|ギリシャの劇場", "A Gothic cathedral|ゴシック大聖堂"], tags=["classify", "structure"], diff="hard")
Q("h1501", "Which church is this?", "これはどの教会ですか？", "St. Peter's Basilica|サン・ピエトロ大聖堂",
  ["Notre-Dame de Paris|ノートルダム大聖堂", "Hagia Sophia|アヤソフィア", "Sagrada Família|サグラダ・ファミリア"], tags=["classify", "structure"], diff="hard")
Q("h1503", "Which animals are shown?", "どの動物が写っていますか？", "Shrimp|エビ", ["Crabs|カニ", "Lobsters|ロブスター", "Starfish|ヒトデ"], tags=["classify", "animal"], diff="hard")
Q("h1505", "What is the machine?", "これは何の機械ですか？", "A pinball machine|ピンボール台", ["A slot machine|スロットマシン", "A jukebox|ジュークボックス", "A vending machine|自動販売機"], tags=["classify", "object"], diff="hard")
Q("h1507", "What does the flyer say at the top?", "チラシの上部には何と書かれていますか？", "Keep Our Market Alive",
  ["Save the Library", "Stop the Highway", "Open Late Tonight"], tags=["ocr", "poster"], diff="medium")
Q("h1509", "Which fish are illustrated?", "どの魚が描かれていますか？", "Carp|コイ", ["Salmon|サケ", "Trout|マス", "Eels|ウナギ"], tags=["classify", "animal"], diff="hard")
Q("h1510", "What type of ship is this?", "これはどんな船ですか？", "A tall sailing ship|大型の帆船", ["A steamship|蒸気船", "A submarine|潜水艦", "A canoe|カヌー"], tags=["classify", "vehicle"], diff="medium")
Q("h1511", "What are the two dishes?", "2 つの皿の料理は何ですか？", "A stew and mashed potatoes|シチューとマッシュポテト",
  ["Two salads|サラダ 2 皿", "Two desserts|デザート 2 皿", "Sushi and miso soup|寿司と味噌汁"], tags=["classify", "food"], diff="hard")
Q("h1513", "Which moon is shown?", "どの衛星が写っていますか？", "Io|イオ", ["Europa|エウロパ", "Titan|タイタン", "Earth's Moon|月"], tags=["classify", "space"], diff="hard")
Q("h1515", "Which script is the scroll written in?", "巻物はどの文字で書かれていますか？", "Hebrew|ヘブライ文字", ["Arabic|アラビア文字", "Greek|ギリシャ文字", "Chinese characters|漢字"], tags=["ocr", "script"], diff="hard")
Q("h1516", "What does the colour scale of the map show?", "地図の色は何を表していますか？", "Doctors per 10,000 people|人口 1 万人あたりの医師数",
  ["Rainfall|降水量", "Average temperature|平均気温", "Language spoken|使用言語"], tags=["ocr", "map"], diff="hard")
Q("h1518", "What is the aircraft?", "この航空機は何ですか？", "A stealth aircraft|ステルス機", ["A helicopter|ヘリコプター", "A glider|グライダー", "An airliner|旅客機"], tags=["classify", "vehicle"], diff="hard")
Q("h1520", "What is shown in the medieval picture?", "中世の絵には何が描かれていますか？", "A castle under attack|攻められている城",
  ["A harvest festival|収穫祭", "A royal wedding|王の結婚式", "A market day|市場の日"], tags=["scene"], diff="hard")
Q("h1522", "Which lake is shown in this satellite image?", "この衛星画像に写っている湖はどれですか？", "Lake Ontario|オンタリオ湖",
  ["Lake Superior|スペリオル湖", "Lake Victoria|ヴィクトリア湖", "Lake Baikal|バイカル湖"], tags=["geo"], diff="hard")
Q("h1525", "Which peninsula is shown?", "写っている半島はどれですか？", "Brittany|ブルターニュ半島",
  ["Cornwall|コーンウォール", "Jutland|ユトランド半島", "Kamchatka|カムチャッカ半島"], tags=["geo"], diff="hard")
Q("h1528", "Which sea is shown?", "写っている海はどれですか？", "The Sea of Okhotsk|オホーツク海",
  ["The Black Sea|黒海", "The Baltic Sea|バルト海", "The Red Sea|紅海"], tags=["geo"], diff="hard")
Q("h1529", "Which vegetable is shown?", "どの野菜が写っていますか？", "A zucchini|ズッキーニ", ["A cucumber|キュウリ", "A banana|バナナ", "A pumpkin|カボチャ"], tags=["classify", "food"], diff="medium")
Q("h1533", "Which moon is shown?", "どの衛星が写っていますか？", "Enceladus|エンケラドス", ["Earth's Moon|月", "Io|イオ", "Mars's Phobos|フォボス"], tags=["classify", "space"], diff="hard")
Q("h1534", "Which art movement does this circular painting belong to?", "この円形の絵はどの美術の流れに属しますか？", "Abstract art|抽象芸術",
  ["Realism|写実主義", "Baroque|バロック", "Impressionism|印象派"], tags=["art"], diff="hard")
Q("h1535", "What gem is shown?", "どの宝石ですか？", "A sapphire|サファイア", ["A ruby|ルビー", "An emerald|エメラルド", "A diamond|ダイヤモンド"], tags=["classify", "object"], diff="hard")
colour("h1535", "the large central stone", "中央の大きな石", "blue", ["red", "green", "yellow"], tags=("colour", "attribute"))
Q("h1537", "What are the two bright objects?", "2 つの明るい天体は何ですか？", "Colliding galaxies|衝突している銀河",
  ["Two comets|2 つの彗星", "Two stars of our galaxy|天の川の 2 つの星", "A planet and its moon|惑星と衛星"], tags=["classify", "space"], diff="hard")
Q("h1541", "What is the person holding?", "手に持っているものは何ですか？", "A clump of soil|土の塊", ["A loaf of bread|パン", "A rock|岩", "A sponge|スポンジ"], tags=["detail"], diff="medium")
Q("h1542", "Which waterway is shown in this satellite image?", "この衛星画像に写っている海峡はどれですか？", "The Bering Strait|ベーリング海峡",
  ["The Strait of Hormuz|ホルムズ海峡", "The Strait of Gibraltar|ジブラルタル海峡", "The English Channel|イギリス海峡"], tags=["geo"], diff="hard")
Q("h1545", "What are the colourful objects in the sky?", "空にある色とりどりの物は何ですか？", "Kites|凧", ["Balloons|風船", "Birds|鳥", "Parachutes|パラシュート"], tags=["classify", "object"], diff="medium")
Q("h1546", "Who painted this room?", "この部屋の壁画を描いたのは誰ですか？", "Raphael|ラファエロ", ["Michelangelo|ミケランジェロ", "Giotto|ジョット", "Titian|ティツィアーノ"], tags=["art"], diff="hard")
