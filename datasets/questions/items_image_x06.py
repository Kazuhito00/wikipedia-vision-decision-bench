# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0121-x0160 (drones, scanners, stethoscopes, weather stations, seismographs). Pictures of
military personnel, politicians and speakers were not used as the subject of any question."""
from templates import Q, N, TYPE

Q("x0121", "How many rotors does the drone have?", "このドローンのローターはいくつありますか？", "Four|4 つ", ["Two|2 つ", "Three|3 つ", "Eight|8 つ"],
  tags=["count", "sci"], diff="hard")
Q("x0122", "What stands on the round display platform?", "丸い展示台の上に置かれているものは何ですか？", "A model of a drone|ドローンの模型・機体",
  ["A cake|ケーキ", "A fountain|噴水", "A lamp|ランプ"], tags=["classify", "object", "sci"], diff="medium")
Q("x0123", "What kind of aircraft is flying in the blue sky?", "青空を飛んでいるのはどんな航空機ですか？", "A small unmanned aircraft with fixed wings|固定翼の小型無人機",
  ["A passenger jet|旅客機", "A helicopter|ヘリコプター", "A hot-air balloon|熱気球"], tags=["classify", "vehicle", "sci"], diff="hard")
Q("x0126", "What is shown in the aerial picture?", "空撮の写真に写っているのは何ですか？", "An island in the sea|海に浮かぶ島",
  ["A desert|砂漠", "A lake in a city|都市の湖", "A glacier|氷河"], tags=["classify", "scene", "sci"], diff="medium")
Q("x0128", "What does the drone photograph show?", "ドローンで撮った写真には何が写っていますか？", "A forest with a grassy clearing and a path|草地と小道のある森",
  ["A harbour|港", "A snowfield|雪原", "A shopping street|商店街"], tags=["classify", "scene", "sci"], diff="medium")
Q("x0129", "What kind of images are these?", "これはどんな画像ですか？", "Brain scans in several slices|いくつもの断面の脳のスキャン画像",
  ["Photographs of food|料理の写真", "Maps of a city|都市の地図", "Pictures of insects|昆虫の写真"], tags=["image-type", "sci"], diff="medium")
N("x0129", "The scans are arranged in a grid of panels", "スキャン画像はパネルの格子状に並んでいる", True, tags=["detail", "sci"])
Q("x0130", "What kind of medical machine is drawn?", "描かれているのはどんな医療機器ですか？", "An MRI scanner|MRI 装置", ["A dental chair|歯科の椅子", "A wheelchair|車椅子", "An incubator|保育器"],
  tags=["classify", "object", "sci"], diff="hard")
Q("x0134", "What kind of machine is shown?", "描かれている機械は何ですか？", "A scanner with a round tunnel and a patient table|円形のトンネルと寝台を持つスキャナー",
  ["A washing machine|洗濯機", "A kiln|窯", "A treadmill|ルームランナー"], tags=["classify", "object", "sci"], diff="hard")
Q("x0132", "What are the two images at the bottom of the figure?", "図の下にある 2 つの画像は何ですか？", "A face and a house|顔と家",
  ["A cat and a dog|猫と犬", "A car and a bicycle|車と自転車", "A tree and a flower|木と花"], tags=["detail", "sci"], diff="hard")
Q("x0137", "What kind of equipment is drawn?", "描かれているのはどんな装置ですか？", "A mobile medical imaging machine on wheels|車輪付きの移動式医用画像装置",
  ["A vending machine|自動販売機", "A shopping cart|ショッピングカート", "A barbecue grill|バーベキューグリル"], tags=["classify", "object", "sci"], diff="hard")
Q("x0138", "What colour are the tubes of the stethoscope?", "聴診器のチューブは何色ですか？", "Pink|ピンク", ["Black|黒", "Blue|青", "Green|緑"], tags=["colour", "sci"])
Q("x0139", "Whose name is carved on the plaque?", "プレートに刻まれている名前は誰のものですか？", "Laennec", ["Pasteur", "Curie", "Koch"], tags=["ocr", "record", "sci"], diff="hard")
N("x0139", "The plaque shows the years 1781 and 1826", "プレートには 1781 年と 1826 年が刻まれている", True, tags=["ocr", "record", "sci"], diff="hard")
Q("x0140", "What material does this old stethoscope appear to be made of?", "この古い聴診器は何でできているように見えますか？", "Metal|金属", ["Wood|木", "Glass|ガラス", "Paper|紙"],
  tags=["attribute", "sci"], diff="medium")
Q("x0141", "What is the dark horn-shaped object in the case?", "ケースの中の黒いラッパ形の物体は何ですか？", "An early listening horn (stethoscope)|初期の聴診用ラッパ（聴診器）",
  ["A trumpet for a band|楽団のトランペット", "A gramophone|蓄音機", "A shoehorn|くつべら"], tags=["classify", "object", "sci"], diff="hard")
N("x0142", "The picture is a close-up of a stethoscope", "写真は聴診器のクローズアップである", True, tags=["detail", "sci"])
Q("x0144", "What lies beside the stethoscope on the cloth?", "布の上で聴診器の隣にあるものは何ですか？", "Scissors|はさみ", ["A key|鍵", "A spoon|スプーン", "A pen|ペン"],
  tags=["classify", "object", "sci"], diff="hard")
Q("x0148", "What kind of station is on the pole by the roof?", "屋根のそばの支柱にあるのはどんな観測装置ですか？", "A weather station with wind sensors|風向風速計などの気象観測装置",
  ["A satellite dish|衛星アンテナ", "A street lamp|街灯", "A bird feeder|餌台"], tags=["classify", "object", "sci"], diff="hard")
N("x0148", "A small solar panel can be seen near the railing", "手すりの近くに小さなソーラーパネルが見える", True, tags=["detail", "sci"], diff="hard")
Q("x0149", "What is shown on the map?", "地図には何が描かれていますか？", "Japan|日本", ["Italy|イタリア", "Chile|チリ", "Greece|ギリシャ"], tags=["geo", "sci"], diff="medium")
Q("x0151", "What kind of display is this?", "これはどんな表示ですか？", "A weather-station display with temperature and humidity|気温と湿度を表示する気象観測の表示器",
  ["A car speedometer|車の速度計", "A clock radio|時計付きラジオ", "A pocket calculator|電卓"], tags=["classify", "object", "sci"], diff="hard")
Q("x0152", "What kind of room is shown in this old photograph?", "この古い写真に写っているのはどんな部屋ですか？", "A room with cabinets of weather instruments|気象測器の棚が並ぶ部屋",
  ["A bakery|パン屋", "A classroom|教室", "A railway ticket office|切符売り場"], tags=["classify", "scene", "sci"], diff="hard")
Q("x0153", "What tall thin object stands in the dry grass?", "乾いた草の中に立っている細長いものは何ですか？", "A mast of a weather station|気象観測の支柱",
  ["A lighthouse|灯台", "A flagpole with a flag|旗の付いた旗竿", "A telescope|望遠鏡"], tags=["detail", "scene", "sci"], diff="hard")
Q("x0154", "Which newspaper's front page is shown?", "どの新聞の 1 面ですか？", "The New York Times", ["The Washington Post", "The Times of London", "Le Monde"],
  tags=["ocr", "record", "sci"], diff="medium")
N("x0154", "The front page reports an earthquake", "1 面には地震が報じられている", True, tags=["ocr", "record", "sci"], diff="hard")
Q("x0155", "What kind of record is shown?", "これはどんな記録ですか？", "Traces recorded by several seismograph channels|複数の地震計チャンネルの波形記録",
  ["A timetable of trains|列車の時刻表", "A heart-rate monitor in a hospital|病院の心拍モニター", "A stock exchange board|株価ボード"], tags=["image-type", "record", "sci"], diff="hard")
Q("x0156", "What instrument is shown in this old photograph?", "この古い写真に写っている装置は何ですか？", "An early seismograph|初期の地震計",
  ["A printing press|印刷機", "A sewing machine|ミシン", "A telescope|望遠鏡"], tags=["classify", "object", "sci"], diff="hard")
Q("x0158", "What shape is the large part in the middle of the instrument?", "装置の中央にある大きな部品はどんな形ですか？", "A drum (cylinder)|ドラム（円筒）",
  ["A cube|立方体", "A cone|円錐", "A star|星形"], tags=["detail", "sci"], diff="medium")
Q("x0160", "Which words label the long tube in the diagram?", "図の長い管に付けられた語はどれですか？", "FUSED - QUARTZ TUBE", ["COPPER WIRE", "STEEL BEAM", "WATER PIPE"],
  tags=["ocr", "sci"], diff="hard")
N("x0160", "The diagram labels the ground beneath as BEDROCK", "図では地面が BEDROCK と記されている", True, tags=["ocr", "sci"], diff="hard")
