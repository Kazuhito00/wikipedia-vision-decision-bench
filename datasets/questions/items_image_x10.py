# -*- coding: utf-8 -*-
"""Expansion set: x0258-x0277 -- field "sci" (3D printers, power pylons) and the start of field "life" (a supermarket shelf,
restaurants). Pictures with a person as the subject were not used."""
from templates import Q, N, TYPE

Q("x0258", "What machine is this?", "これは何の機械ですか？", "A 3D printer|3D プリンター", ["A microwave oven|電子レンジ", "A coffee machine|コーヒーメーカー", "A washing machine|洗濯機"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0259", "What colour is the frame of this machine?", "この機械の枠は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Black|黒"], tags=["colour", "sci"], diff="medium")
Q("x0263", "Which brand name is printed on the machine?", "機械に印刷されているブランド名はどれですか？", "Ultimaker", ["MakerBot", "Prusa", "Creality"], tags=["ocr", "sci"], diff="hard")
Q("x0266", "What is the tall steel structure seen from below?", "下から見上げている背の高い鉄の構造物は何ですか？", "An electricity pylon|送電鉄塔",
  ["A radio mast|電波塔", "A crane|クレーン", "An oil derrick|油井やぐら"], tags=["classify", "structure", "sci"], diff="hard")
Q("x0268", "What stands near the high-rise buildings?", "高層ビルの近くに立っているものは何ですか？", "A power pylon|送電鉄塔", ["A lighthouse|灯台", "A windmill|風車", "A ferris wheel|観覧車"],
  tags=["classify", "structure", "sci"], diff="medium")
Q("x0269", "What are the grey elements hanging along the cross-arms?", "腕木に沿って下がっている灰色の部品は何ですか？", "Insulators|碍子", ["Chains|鎖", "Bananas|バナナ", "Lanterns|提灯"],
  tags=["detail", "sci"], diff="hard")
Q("x0274", "What colour are most of the lids on the shelf?", "棚の瓶のふたはほとんどが何色ですか？", "Orange|オレンジ", ["Blue|青", "Green|緑", "White|白"], tags=["colour", "life"], diff="medium")
N("x0274", "The shelf is in a shop", "この棚は店の中にある", True, tags=["scene", "life"])
N("x0275", "The restaurant entrance is lit up at night", "夜のレストランの入り口に明かりがともっている", True, tags=["scene", "life"])
Q("x0276", "What colour is the facade of the building?", "建物の外壁は何色ですか？", "Dark grey|濃い灰色", ["Red|赤", "Yellow|黄色", "White|白"], tags=["colour", "life"], diff="medium")
N("x0277", "Cars are parked in front of the building", "建物の前に自動車が止まっている", True, tags=["scene", "life"])
