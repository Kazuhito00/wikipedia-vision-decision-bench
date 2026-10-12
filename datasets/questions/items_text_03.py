# -*- coding: utf-8 -*-
"""Text items 03: cities and first scientists (articles 15-22)."""
from dsl import tchoice, tnoul

# ---- Cairo
tchoice("Cairo", "Cairo is the capital of which country?", "Egypt", ["Jordan", "Libya", "Sudan"],
        "カイロはどの国の首都ですか？", "エジプト", ["ヨルダン", "リビア", "スーダン"],
        [], [], tags=["capital"])
tnoul("Cairo", "Cairo is the capital of Libya.", "カイロはリビアの首都である。", False,
      [], [], absent_en=["capital of Libya"], absent_ja=["リビアの首都"], tags=["capital"])
# ---- Reykjavík
tnoul("Reykjavík", "Reykjavík is the capital of Iceland.", "レイキャヴィークはアイスランドの首都である。", True,
      [], [], tags=["capital"])
tnoul("Reykjavík", "Reykjavík is the capital of Norway.", "レイキャヴィークはノルウェーの首都である。", False,
      [], [], absent_en=["capital of Norway"], absent_ja=["ノルウェーの首都"], tags=["capital"])
# ---- Singapore
tchoice("Singapore", "In which region of the world is Singapore located?", "Southeast Asia",
        ["Western Europe", "Central America", "Northern Africa"],
        "シンガポールは世界のどの地域にありますか？", "東南アジア", ["西ヨーロッパ", "中央アメリカ", "北アフリカ"],
        [], [], tags=["geo-region"])
tnoul("Singapore", "Singapore consists of a main island and dozens of smaller islands.", "シンガポールは本島と数十の小さな島々からなる。", True,
      [], [], tags=["fact"])
# ---- Nairobi
tchoice("Nairobi", "Nairobi is the capital of which country?", "Kenya", ["Uganda", "Tanzania", "Ethiopia"],
        "ナイロビはどの国の首都ですか？", "ケニア", ["ウガンダ", "タンザニア", "エチオピア"],
        [], [], tags=["capital"])
tnoul("Nairobi", "Nairobi is the capital of Tanzania.", "ナイロビはタンザニアの首都である。", False,
      [], [], absent_en=["capital of Tanzania"], absent_ja=["タンザニアの首都"], tags=["capital"])
# ---- Osaka
tchoice("Osaka", "In which region of Japan is Osaka located?", "Kansai", ["Kanto", "Tohoku", "Kyushu"],
        "大阪市は日本のどの地方にありますか？", "近畿地方", ["関東地方", "東北地方", "九州地方"],
        [], [], tags=["geo-region"])
tnoul("Osaka", "Osaka is part of the Keihanshin metropolitan area.", "大阪市は京阪神大都市圏の一部である。", True,
      [], [], tags=["fact"])
# ---- Florence
tchoice("Florence", "Florence is the capital of which Italian region?", "Tuscany", ["Lombardy", "Sicily", "Piedmont"],
        "フィレンツェはイタリアのどの州の州都ですか？", "トスカーナ州", ["ロンバルディア州", "シチリア州", "ピエモンテ州"],
        [], [], tags=["geo-admin"])
tnoul("Florence", "Florence is the capital of Sicily.", "フィレンツェはシチリア州の州都である。", False,
      [], [], absent_en=["capital of Sicily"], absent_ja=["シチリア州の州都"], tags=["geo-admin"])
# ---- Albert Einstein
tchoice("Albert Einstein", "In which year was Albert Einstein born?", "1879", ["1859", "1889", "1901"],
        "アルベルト・アインシュタインが生まれた年はいつですか？", "1879年", ["1859年", "1889年", "1901年"],
        [], [], tags=["date"], diff="medium")
tnoul("Albert Einstein", "Einstein was born in Germany.", "アインシュタインはドイツで生まれた。", True,
      [], [], tags=["fact"])
# ---- Marie Curie
tchoice("Marie Curie", "In which year did Marie Curie win the Nobel Prize in Chemistry?", "1911", ["1905", "1921", "1928"],
        "マリ・キュリーがノーベル化学賞を受賞した年はいつですか？", "1911年", ["1905年", "1921年", "1928年"],
        [], [], tags=["date"], diff="medium")
tnoul("Marie Curie", "Marie Curie was a painter.", "マリ・キュリーは画家だった。", False,
      [], [], absent_en=["painter"], absent_ja=["画家"], tags=["fact"])
tnoul("Marie Curie", "Marie Curie was a physicist and chemist.", "マリ・キュリーは物理学者であり化学者だった。", True,
      [], [], tags=["fact"])
