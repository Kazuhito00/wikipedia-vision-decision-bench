# -*- coding: utf-8 -*-
"""Expansion set, field "sci" (science and technology): x0001-x0020 (microscopes, laboratories, laboratory glassware).
Pictures are CC0 / public domain Commons files picked by category (tools/collect_expansion.py); every question was written
after looking at the picture. Pictures where the answer could not be read with confidence were left out."""
from templates import Q, N, TYPE

SCI = ("sci",)

Q("x0001", "What instruments are drawn on this book page?", "この本のページに描かれている器具は何ですか？", "Microscopes|顕微鏡",
  ["Telescopes|望遠鏡", "Cameras|カメラ", "Stethoscopes|聴診器"], tags=["classify", "object", "sci"], diff="medium")
N("x0001", "The picture is a scanned page of a printed book", "この画像は印刷された本のページをスキャンしたものである", True, tags=["detail", "sci"], diff="medium")
TYPE("x0002", "page", ["photo", "map", "satellite"], diff="medium")
N("x0002", "The page shows a drawing of an optical instrument built from lenses", "このページにはレンズでできた光学機器の図が載っている", True,
  tags=["detail", "sci"], diff="medium")
Q("x0004", "What lies on the stage under the microscope?", "顕微鏡の下に置かれているものは何ですか？", "A coin or medal|硬貨またはメダル",
  ["A leaf|葉", "A drop of water|水滴", "A circuit chip|電子回路のチップ"], tags=["classify", "object", "sci"], diff="hard")
Q("x0005", "What instrument is shown?", "写っている器具は何ですか？", "A microscope|顕微鏡", ["A telescope|望遠鏡", "A camera|カメラ", "A lamp|ランプ"],
  tags=["classify", "object", "sci"])
Q("x0005", "What colour is the surface the instrument stands on?", "器具が置かれている面は何色ですか？", "Purple|紫", ["Green|緑", "Red|赤", "Yellow|黄色"],
  tags=["colour", "sci"], diff="medium")
N("x0006", "The photograph is in black and white", "この写真は白黒である", True, tags=["attribute", "sci"], diff="medium")
Q("x0006", "What is the person in the picture looking through?", "写真の人物は何をのぞき込んでいますか？", "A microscope|顕微鏡",
  ["A telescope|望遠鏡", "A keyhole|鍵穴", "A camera viewfinder|カメラのファインダー"], tags=["action", "sci"], diff="medium")
Q("x0007", "What do the cross-section drawings show?", "断面の図は何を表していますか？", "The lens elements of an objective|対物レンズのレンズ構成",
  ["Teeth of a gear|歯車の歯", "Pipes inside a wall|壁の中の配管", "Layers of a cake|ケーキの層"], tags=["detail", "sci"], diff="hard")
N("x0008", "One of the people is looking into a microscope", "人物の 1 人が顕微鏡をのぞいている", True, tags=["action", "sci"], diff="medium")
Q("x0009", "What kind of room is this?", "ここはどんな部屋ですか？", "A study or library with bookcases|本棚のある書斎・図書室",
  ["A kitchen|台所", "A garage|車庫", "A swimming pool|プール"], tags=["classify", "scene", "sci"], diff="medium")
N("x0009", "The window has red curtains", "窓に赤いカーテンがかかっている", True, tags=["attribute", "sci"], diff="medium")
Q("x0010", "What kind of place is shown in this old photograph?", "この古い写真に写っているのはどんな場所ですか？",
  "A laboratory with long work benches|長い作業台のある実験室", ["A restaurant kitchen|レストランの厨房", "A railway waiting room|鉄道の待合室", "A church|教会"],
  tags=["classify", "scene", "sci"], diff="medium")
Q("x0011", "What kind of equipment is this?", "これはどんな設備ですか？", "Laboratory glassware held on stands|スタンドに固定された実験用ガラス器具",
  ["Musical instruments|楽器", "Kitchen pots|調理用の鍋", "Bicycle parts|自転車の部品"], tags=["classify", "object", "sci"], diff="medium")
Q("x0013", "How many microscopes stand on the table?", "テーブルの上に顕微鏡はいくつありますか？", "Two|2 台", ["One|1 台", "Three|3 台", "Four|4 台"],
  tags=["count", "sci"], diff="medium")
Q("x0015", "What are the yellow boxes with the symbol used for?", "記号の付いた黄色い箱は何に使いますか？",
  "Disposing of sharp or hazardous waste|鋭利な物や危険な廃棄物の廃棄", ["Storing food|食品の保管", "Carrying tools|工具の持ち運び", "Posting letters|郵便の投函"],
  tags=["detail", "safety", "sci"], diff="hard")
Q("x0016", "What glassware stands on the white bench?", "白い作業台の上に立っているガラス器具は何ですか？", "Graduated cylinders|メスシリンダー",
  ["Wine glasses|ワイングラス", "Vases|花瓶", "Teapots|急須"], tags=["classify", "object", "sci"], diff="medium")
N("x0016", "The bench is made of dark wood", "作業台は濃い色の木でできている", False, tags=["attribute", "sci"])
Q("x0017", "What kind of laboratory glassware is this?", "これはどんな実験用ガラス器具ですか？", "Erlenmeyer flasks|三角フラスコ",
  ["Beakers|ビーカー", "Test tubes|試験管", "Funnels|漏斗"], tags=["classify", "object", "sci"], diff="medium")
Q("x0017", "What volume is printed on the left flask?", "左のフラスコに印刷されている容量はどれですか？", "50 ml", ["25 ml", "100 ml", "250 ml"],
  tags=["ocr", "sci"], diff="hard")
N("x0018", "The figure number printed below the drawing is 40", "図の下に印刷されている図番号は 40 である", True, tags=["ocr", "sci"], diff="hard")
Q("x0019", "Which volume is written on the round flask?", "丸いフラスコに書かれている容量はどれですか？", "1 litre|1 リットル",
  ["5 litres|5 リットル", "10 litres|10 リットル", "1 pint|1 パイント"], tags=["ocr", "sci"], diff="hard")
Q("x0020", "What are the hands holding in the drawings?", "図の中の手は何を持っていますか？", "Pipettes|ピペット", ["Pencils|鉛筆", "Scissors|はさみ", "Sewing needles|縫い針"],
  tags=["detail", "sci"], diff="hard")
