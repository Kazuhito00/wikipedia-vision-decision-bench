# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0041-x0060 (solar panels, wind turbines, a satellite instrument). Military personnel and
close-ups of faces were not used as the subject of any question."""
from templates import Q, N, TYPE

Q("x0042", "What vehicles are parked under the solar-panel roof?", "ソーラーパネルの屋根の下に止まっている乗り物は何ですか？",
  "Golf carts|ゴルフカート", ["Tractors|トラクター", "Motorcycles|オートバイ", "Buses|バス"], tags=["classify", "vehicle", "sci"], diff="hard")
N("x0042", "The vehicles in the front are red", "手前の乗り物は赤い", True, tags=["colour", "sci"])
N("x0043", "The solar panels stand in a row in a grassy field", "ソーラーパネルが草地に列になって並んでいる", True, tags=["scene", "sci"])
Q("x0044", "What does the red-outlined symbol on the sign show?", "看板の赤い枠の記号は何を表していますか？", "A house with the letters PV|「PV」の文字が入った家",
  ["A bicycle|自転車", "A fire|炎", "A cross|十字"], tags=["ocr", "sci"], diff="hard")
Q("x0045", "What colour are the large road signs above the street?", "道路の上の大きな標識は何色ですか？", "Green|緑", ["Blue|青", "Red|赤", "Yellow|黄色"],
  tags=["colour", "scene", "sci"])
Q("x0047", "What is being installed or maintained under the blue roof?", "青い屋根の下で設置・保守されているものは何ですか？",
  "Solar panels|太陽光パネル", ["Street lamps|街灯", "Billboards|看板", "Water pipes|水道管"], tags=["classify", "action", "sci"], diff="hard")
N("x0047", "A scissor lift is being used by the workers", "作業員はシザースリフトを使っている", True, tags=["detail", "sci"], diff="hard")
Q("x0048", "What does the grid pattern on the surface consist of?", "表面の格子模様は何でできていますか？", "Solar cells|太陽電池セル",
  ["Floor tiles|床のタイル", "Window panes|窓ガラス", "Chocolate bars|板チョコ"], tags=["classify", "object", "sci"], diff="medium")
Q("x0049", "How many wind turbines can be counted in the line along the shore?", "海岸沿いに並ぶ風車はおよそいくつ数えられますか？", "More than four|4 基より多い",
  ["One|1 基", "Two|2 基", "Exactly three|ちょうど 3 基"], tags=["count", "sci"], diff="hard")
Q("x0050", "What kind of wind machines stand on the lawn?", "芝生の上に立っている風力機械はどんな種類ですか？", "Sculptural vertical-axis turbines|彫刻のような縦軸型の風車",
  ["Oil derricks|油井やぐら", "Radio masts|電波塔", "Windmills for grinding grain|穀物をひく風車小屋"], tags=["detail", "sci"], diff="hard")
Q("x0052", "What kind of wind machine is this?", "これはどんな風力機械ですか？", "A multi-blade farm windmill|多翼式の農業用風車",
  ["A modern three-blade turbine|3 枚羽根の現代の風車", "A ship's propeller|船のプロペラ", "A ceiling fan|天井扇"], tags=["classify", "object", "sci"], diff="hard")
Q("x0053", "What is shown against the blue background?", "青い背景の前に写っているものは何ですか？", "A model of a wind turbine|風力発電機の模型",
  ["A rocket|ロケット", "A street lamp|街灯", "A crane|クレーン"], tags=["classify", "object", "sci"], diff="medium")
Q("x0054", "How many blades does the wind turbine have?", "この風車の羽根は何枚ですか？", "Three|3 枚", ["Two|2 枚", "Four|4 枚", "Six|6 枚"], tags=["count", "sci"], diff="medium")
N("x0055", "The turbines stand next to a crop field", "風車は作物の畑のそばに立っている", True, tags=["scene", "sci"])
TYPE("x0057", "photo", ["diagram", "painting", "map"], diff="medium")
Q("x0060", "What kind of image is this?", "これはどんな種類の画像ですか？", "A flow diagram with boxes and arrows|箱と矢印のフロー図",
  ["A photograph of a landscape|風景写真", "A satellite image of a city|都市の衛星画像", "A painting|絵画"], tags=["image-type", "sci"], diff="medium")
