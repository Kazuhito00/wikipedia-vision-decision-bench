# -*- coding: utf-8 -*-
"""Text items 01: countries and cities (written from the lead sections; see questions/dsl.py)."""
from dsl import tchoice, tnoul

# ---- Japan
tchoice("Japan", "In which part of the world is this country located?", "East Asia",
        ["Western Europe", "South America", "Central Africa"],
        "この国はどの地域に位置していますか？", "東アジア", ["西ヨーロッパ", "南アメリカ", "中央アフリカ"],
        [], [], tags=["geo-region"])
tchoice("Japan", "What is the capital of the country?", "Tokyo", ["Osaka", "Sapporo", "Nagoya"],
        "この国の首都はどこですか？", "東京", ["大阪", "札幌", "名古屋"],
        [], [], tags=["capital"])
# ---- Brazil
tchoice("Brazil", "What is the capital of Brazil?", "Brasília", ["Lima", "Buenos Aires", "Santiago"],
        "ブラジルの首都はどこですか？", "ブラジリア", ["リマ", "ブエノスアイレス", "サンティアゴ"],
        [], [], tags=["capital"])
tnoul("Brazil", "Brazil is the largest country in South America.", "ブラジルは南アメリカで最大の面積を持つ国である。", True,
      [], [], tags=["fact"])
# ---- Egypt
tchoice("Egypt", "Which sea lies to the north of the country?", "The Mediterranean Sea",
        ["The Baltic Sea", "The Black Sea", "The Caspian Sea"],
        "この国の北側に面している海はどれですか？", "地中海", ["バルト海", "黒海", "カスピ海"],
        [], [], tags=["geo-border"])
tnoul("Egypt", "Cairo is the capital of the country.", "カイロはこの国の首都である。", True,
      [], [], tags=["capital"])
# ---- Canada
tchoice("Canada", "What is the capital of Canada?", "Ottawa", ["Calgary", "Halifax", "Winnipeg"],
        "カナダの首都はどこですか？", "オタワ", ["カルガリー", "ハリファックス", "ウィニペグ"],
        [], [], tags=["capital"], diff="medium")
tnoul("Canada", "The country has ten provinces and three territories.", "この国は 10 の州と 3 つの準州からなる。", True,
      [], [], tags=["fact"])
# ---- Kenya
tchoice("Kenya", "Which city is the capital of Kenya?", "Nairobi", ["Kampala", "Dodoma", "Addis Ababa"],
        "ケニアの首都はどこですか？", "ナイロビ", ["カンパラ", "ドドマ", "アディスアベバ"],
        [], [], tags=["capital"], diff="medium")
tnoul("Kenya", "Kenya borders Tanzania.", "ケニアはタンザニアと国境を接している。", True,
      [], [], tags=["geo-border"])
# ---- Iceland
tchoice("Iceland", "What is the capital of Iceland?", "Reykjavík", ["Oslo", "Helsinki", "Copenhagen"],
        "アイスランドの首都はどこですか？", "レイキャヴィーク", ["オスロ", "ヘルシンキ", "コペンハーゲン"],
        [], [], tags=["capital"])
tnoul("Iceland", "Iceland is an island country in the North Atlantic.", "アイスランドは北大西洋にある島国である。", True,
      [], [], tags=["geo-region"])
