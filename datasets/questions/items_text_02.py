# -*- coding: utf-8 -*-
"""Text items 02: countries and cities (articles 7-14), plus the false statements for items 01."""
from dsl import tchoice, tnoul

# ---- false statements for the first six articles (balance the true/false ratio)
tnoul("Japan", "Japan is a landlocked country in Europe.", "日本はヨーロッパにある内陸国である。", False,
      [], [], absent_en=["landlocked"], absent_ja=["内陸国"], tags=["geo-region"])
tnoul("Brazil", "Brazil is the largest country in Europe.", "ブラジルはヨーロッパで最大の面積を持つ国である。", False,
      [], [], absent_en=["largest country in Europe"],
      absent_ja=["ヨーロッパで最大"], tags=["fact"])
tnoul("Egypt", "Egypt is a landlocked country with no sea coast.", "エジプトは海に面していない内陸国である。", False,
      [], [], absent_en=["landlocked"], absent_ja=["内陸国"], tags=["geo-border"])
tnoul("Canada", "The capital of Canada is Toronto.", "カナダの首都はトロントである。", False,
      [], [], absent_en=["capital is Toronto"], absent_ja=["首都はトロント"], tags=["capital"])
tnoul("Kenya", "Kenya has a coast on the Atlantic Ocean.", "ケニアは大西洋に面している。", False,
      [], [], absent_en=["Atlantic Ocean"], absent_ja=["大西洋"], tags=["geo-border"])
tnoul("Iceland", "The capital of Iceland is Oslo.", "アイスランドの首都はオスロである。", False,
      [], [], absent_en=["capital of Iceland is Oslo"],
      absent_ja=["首都はオスロ"], tags=["capital"])

# ---- Thailand
tchoice("Thailand", "What is the capital of Thailand?", "Bangkok", ["Hanoi", "Manila", "Jakarta"],
        "タイの首都はどこですか？", "バンコク", ["ハノイ", "マニラ", "ジャカルタ"],
        [], [], tags=["capital"])
tnoul("Thailand", "Thailand is located in South America.", "タイは南アメリカに位置している。", False,
      [], [], absent_en=["South America"], absent_ja=["南アメリカ"], tags=["geo-region"])
# ---- Peru
tchoice("Peru", "Which ocean lies to the west of Peru?", "The Pacific Ocean",
        ["The Atlantic Ocean", "The Indian Ocean", "The Arctic Ocean"],
        "ペルーの西側に広がる海洋はどれですか？", "太平洋", ["大西洋", "インド洋", "北極海"],
        [], [], tags=["geo-border"])
tnoul("Peru", "Lima is the capital of Peru.", "リマはペルーの首都である。", True,
      [], [], tags=["capital"])
# ---- Norway
tchoice("Norway", "What is the capital of Norway?", "Oslo", ["Stockholm", "Helsinki", "Copenhagen"],
        "ノルウェーの首都はどこですか？", "オスロ", ["ストックホルム", "ヘルシンキ", "コペンハーゲン"],
        [], [], tags=["capital"])
tnoul("Norway", "Norway has no coastline.", "ノルウェーには海岸線がない。", False,
      [], [], absent_en=["no coastline"], absent_ja=["海岸線がない"], tags=["fact"])
# ---- New Zealand
tchoice("New Zealand", "What is the capital city of New Zealand?", "Wellington", ["Canberra", "Sydney", "Suva"],
        "ニュージーランドの首都はどこですか？", "ウェリントン", ["キャンベラ", "シドニー", "スバ"],
        [], [], tags=["capital"], diff="medium")
tnoul("New Zealand", "New Zealand is an island country in the Pacific Ocean.", "ニュージーランドは太平洋にある島国である。", True,
      [], [], tags=["geo-region"])
# ---- Kyoto
tchoice("Kyoto", "Kyoto is the capital city of which prefecture?", "Kyoto Prefecture",
        ["Nara Prefecture", "Shiga Prefecture", "Hyogo Prefecture"],
        "京都市は、どの府県の県庁（府庁）所在地ですか？", "京都府", ["奈良県", "滋賀県", "兵庫県"],
        [], [], tags=["geo-admin"])
tnoul("Kyoto", "Kyoto is in the Kanto region.", "京都は関東地方にある。", False,
      [], [], absent_en=["Kanto"], absent_ja=["関東"], tags=["geo-region"])
# ---- Venice
tchoice("Venice", "In which country is Venice?", "Italy", ["France", "Spain", "Greece"],
        "ヴェネツィアはどの国にありますか？", "イタリア", ["フランス", "スペイン", "ギリシャ"],
        [], [], tags=["geo-country"])
tnoul("Venice", "Venice is the capital of the Veneto region.", "ヴェネツィアはヴェネト州の州都である。", True,
      [], [], tags=["geo-admin"])
# ---- Istanbul
tchoice("Istanbul", "In which country is Istanbul the largest city?", "Turkey", ["Greece", "Egypt", "Iran"],
        "イスタンブールはどの国で最大の都市ですか？", "トルコ", ["ギリシャ", "エジプト", "イラン"],
        [], [], tags=["geo-country"])
tnoul("Istanbul", "Istanbul is a small village.", "イスタンブールは小さな村である。", False,
      [], [], absent_en=["small village"], absent_ja=["小さな村"], tags=["fact"])
# ---- Sydney
tchoice("Sydney", "Sydney is the capital of which Australian state?", "New South Wales",
        ["Victoria", "Queensland", "Tasmania"],
        "シドニーはオーストラリアのどの州の州都ですか？", "ニューサウスウェールズ州", ["ビクトリア州", "クイーンズランド州", "タスマニア州"],
        [], [], tags=["geo-admin"])
tnoul("Sydney", "Sydney is the capital of the state of Victoria.", "シドニーはビクトリア州の州都である。", False,
      [], [], absent_en=["Victoria"],
      absent_ja=["ビクトリア州"], tags=["geo-admin"])
