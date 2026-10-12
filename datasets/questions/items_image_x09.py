# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0218-x0257 (greenhouses, radio telescopes, engines, cranes, engineering works). Pictures
where a person is the subject were not used."""
from templates import Q, N, TYPE

Q("x0218", "What is the title printed on the book cover?", "本の表紙に印刷されている題名はどれですか？", "The House of Orchids", ["The Garden of Roses", "The Book of Birds", "The House of Cards"],
  tags=["ocr", "record", "sci"], diff="hard")
Q("x0218", "Who is named as the author on the cover?", "表紙に著者として書かれている名前は誰ですか？", "George Sterling", ["Mark Twain", "Jack London", "Oscar Wilde"],
  tags=["ocr", "record", "sci"], diff="hard")
Q("x0220", "By what does the caption say the interior is heated?", "キャプションによると、内部は何で暖められていますか？", "A slow combustion stove|低速燃焼ストーブ",
  ["Solar mirrors|太陽光の反射鏡", "Electric heaters|電気ヒーター", "Steam pipes from a boiler|ボイラーの蒸気管"], tags=["ocr", "sci"], diff="hard")
Q("x0221", "What does the caption under the drawing say?", "図の下のキャプションには何と書かれていますか？", "REMOVABLE GREENHOUSE", ["FIXED PAVILION", "WINTER GARDEN", "COLD FRAME"],
  tags=["ocr", "sci"], diff="hard")
Q("x0223", "Which season does the picture suggest?", "写真はどの季節を思わせますか？", "Winter|冬", ["Summer|夏", "Spring|春", "Autumn|秋"], tags=["scene", "sci"], diff="easy")
N("x0223", "The long low structure is covered with snow", "細長い低い構造物は雪に覆われている", True, tags=["scene", "sci"])
Q("x0224", "What is growing inside the greenhouse?", "温室の中で育っているものは何ですか？", "Leafy vegetables|葉物野菜", ["Cacti|サボテン", "Rice plants|稲", "Cotton|綿"],
  tags=["classify", "sci"], diff="medium")
Q("x0225", "What kind of building is this?", "これはどんな建物ですか？", "A glass conservatory or greenhouse|ガラスの温室", ["A swimming pool|プール", "A bus station|バスターミナル", "A parking garage|立体駐車場"],
  tags=["classify", "structure", "sci"], diff="medium")
Q("x0226", "What is the large dish in the picture?", "写真の大きな皿状のものは何ですか？", "A radio telescope|電波望遠鏡", ["A water tank|貯水槽", "A lamp shade|ランプの傘", "A solar cooker|ソーラークッカー"],
  tags=["classify", "object", "sci"], diff="medium")
N("x0227", "The big dish is made of a wire mesh", "大きな皿状のアンテナは金網でできている", True, tags=["attribute", "sci"], diff="hard")
Q("x0230", "Which instrument is drawn on the stamp?", "切手に描かれている器具は何ですか？", "A microscope|顕微鏡", ["A telescope|望遠鏡", "A camera|カメラ", "A typewriter|タイプライター"],
  tags=["classify", "record", "sci"], diff="medium")
Q("x0230", "Which number is printed at the right edge of the stamp?", "切手の右端に印刷されている数字はどれですか？", "4", ["5", "10", "20"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0232", "What is named in the title at the top?", "上部のタイトルに書かれているものは何ですか？", "Lunar Crater Radio Telescope", ["Mars Orbiter Camera", "Solar Wind Probe", "Deep Sea Sonar"],
  tags=["ocr", "sci"], diff="hard")
Q("x0236", "Which country is named in the caption?", "キャプションに書かれている国はどれですか？", "Egypt|エジプト", ["Italy|イタリア", "Spain|スペイン", "Morocco|モロッコ"],
  tags=["ocr", "record", "sci"], diff="hard")
Q("x0236", "Which year is given in the caption?", "キャプションに書かれている年はどれですか？", "1915", ["1913", "1925", "1895"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0239", "What large round part is at the top right of the engine drawing?", "エンジンの図の右上にある大きな丸い部品は何ですか？", "A flywheel|はずみ車",
  ["A bicycle wheel|自転車の車輪", "A pizza|ピザ", "A clock face|時計の文字盤"], tags=["detail", "sci"], diff="hard")
Q("x0241", "What is the title of the magazine at the top?", "上部の雑誌名はどれですか？", "Aeronautics", ["Automobile", "Astronomy", "Architecture"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0241", "Which company's name appears in large letters?", "大きな文字で書かれている会社名はどれですか？", "Roberts", ["Wright", "Ford", "Boeing"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0242", "What stands on the barge by the water?", "水辺のはしけの上に立っているものは何ですか？", "A crane|クレーン", ["A windmill|風車", "A lighthouse|灯台", "A radio mast|電波塔"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0247", "What equipment stands in a row along the quay?", "岸壁に並んで立っている設備は何ですか？", "Dock cranes|港湾クレーン", ["Wind turbines|風車", "Street lamps|街灯", "Church towers|教会の塔"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0250", "Which place name is printed at the top of the plate?", "図版の上部に印刷されている地名はどれですか？", "LOURENÇO MARQUES", ["LISBON", "MADRID", "ROTTERDAM"],
  tags=["ocr", "record", "sci"], diff="hard")
Q("x0251", "What crosses the road far ahead?", "道路の遠くを横切っているものは何ですか？", "A viaduct (bridge)|高架橋", ["A railway tunnel|鉄道のトンネル", "A river|川", "A castle wall|城壁"],
  tags=["detail", "scene", "sci"], diff="medium")
Q("x0254", "What are the people standing on?", "人々は何の上に立っていますか？", "A wooden pier|木の桟橋", ["A glacier|氷河", "A rooftop|屋上", "A frozen lake|凍った湖"],
  tags=["scene", "sci"], diff="medium")
