# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0505-h0548 (pictures used by the Japanese article only; the compiler
publishes them in Japanese). The English text is written anyway so that the same item can be reused if the English
article starts to use the picture."""
from templates import Q, N, TYPE, S, colour

TYPE("h0505", "painting", ["photo", "diagram", "satellite"])
S("h0507", "tiger", "animal")
Q("h0509", "What is the child eating?", "子どもは何を食べていますか？", "Soup|スープ", ["Pizza|ピザ", "Sushi|寿司", "Ice cream|アイスクリーム"], tags=["detail"], diff="medium")
TYPE("h0509", "painting", ["photo", "diagram", "satellite"])
Q("h0510", "What flows through the city?", "都市を流れているものは何ですか？", "A river|川", ["A glacier|氷河", "A highway|高速道路", "A railway|鉄道"], tags=["scene"])
Q("h0514", "Which vegetable is shown?", "どの野菜が写っていますか？", "Green peppers|ピーマン",
  ["Cucumbers|キュウリ", "Apples|りんご", "Pears|洋なし"], tags=["classify", "food"], diff="medium")
Q("h0533", "What is shown?", "何が写っていますか？", "A knight in armour on a horse|馬上の甲冑の騎士",
  ["A farmer plowing|耕す農夫", "A ship captain|船長", "A sumo wrestler|力士"], tags=["classify", "object"])
Q("h0534", "What time of day does the sky suggest?", "空の様子から、いつごろの景色だと考えられますか？", "Dusk or night|夕暮れから夜",
  ["Bright midday|明るい真昼"], tags=["scene"], diff="medium")
TYPE("h0538", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0547", "What kind of landscape is this?", "これはどんな景色ですか？", "A savanna with a lone tree|一本の木が立つサバンナ",
  ["A snowy forest|雪の森", "A city street|市街地", "A coral reef|サンゴ礁"], tags=["scene"])
N("h0547", "There is a snow-capped mountain in the picture", "写真に雪をかぶった山がある", True, tags=["scene"])
TYPE("h0548", "painting", ["photo", "diagram", "satellite"])
