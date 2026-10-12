# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0178-x0217 (crystals, minerals, fossils, DNA diagrams, periodic tables)."""
from templates import Q, N, TYPE

Q("x0178", "Which name is written on the label?", "ラベルに書かれている名前はどれですか？", "Endlichit", ["Quartz", "Pyrite", "Calcite"], tags=["ocr", "sci"], diff="hard")
Q("x0180", "Which colour range do the crystals have?", "結晶はどの色の範囲ですか？", "Yellow to amber|黄〜琥珀色", ["Blue|青", "Pink|ピンク", "Green|緑"],
  tags=["colour", "sci"], diff="medium")
Q("x0187", "What colour are the crystals inside the geode?", "晶洞（ジオード）の中の結晶は何色ですか？", "Purple|紫", ["Blue|青", "Green|緑", "Yellow|黄色"], tags=["colour", "sci"], diff="easy")
N("x0186", "The rocks are on display inside a building", "岩石は建物の中に展示されている", True, tags=["scene", "sci"], diff="medium")
Q("x0188", "Which element is named in the second column heading?", "表の 2 列目の見出しに書かれている元素はどれですか？", "Lithium", ["Copper", "Zinc", "Tin"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0188", "Which country is listed first in the table?", "表の最初に挙げられている国はどれですか？", "Argentina", ["Australia", "Brazil", "Chile"], tags=["ocr", "record", "sci"], diff="hard")
Q("x0190", "What shape do the crystals form together?", "結晶は全体としてどんな形をつくっていますか？", "A radiating star-like cluster|放射状の星のような集まり",
  ["A cube|立方体", "A flat sheet|平らな板", "A ring|輪"], tags=["detail", "sci"], diff="medium")
Q("x0194", "What do the plates in the open book show?", "開いた本の図版は何を描いていますか？", "Fossil jaws and teeth|化石の顎や歯", ["Flowers|花", "Sailing ships|帆船", "Musical instruments|楽器"],
  tags=["detail", "record", "sci"], diff="hard")
Q("x0195", "What lies on the dark surface?", "暗い面の上にあるものは何ですか？", "A small skull|小さな頭骨", ["A seashell|貝殻", "A mushroom|キノコ", "A coin|硬貨"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0196", "Which code is written near the top right of the drawing?", "図の右上に書かれているコードはどれですか？", "A.M. 19007", ["A.M. 19004", "B.M. 19007", "A.M. 70001"],
  tags=["ocr", "sci"], diff="hard")
Q("x0197", "What does the impression in the orange rock look like?", "オレンジ色の岩の跡はどんな形に見えますか？", "A circle with a spiral pattern|渦巻き模様のある円",
  ["A leaf with veins|葉脈のある葉", "A fish skeleton|魚の骨", "A bird footprint|鳥の足跡"], tags=["detail", "sci"], diff="hard")
Q("x0199", "What does the surface consist of?", "表面は何でできていますか？", "Many small shells|たくさんの小さな貝殻", ["Rice grains|米粒", "Coins|硬貨", "Leaves|葉"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0200", "Which specimen code is written next to the drawing?", "図の横に書かれている標本のコードはどれですか？", "A.M. 19004", ["A.M. 19007", "B.M. 19004", "A.M. 90004"],
  tags=["ocr", "sci"], diff="hard")
Q("x0202", "What animal stands on the leaf?", "葉の上に立っている動物は何ですか？", "An insect|昆虫", ["A frog|カエル", "A snail|カタツムリ", "A bird|鳥"], tags=["classify", "animal", "sci"], diff="medium")
N("x0202", "A DNA double helix appears in the picture", "絵の中に DNA の二重らせんが描かれている", True, tags=["detail", "sci"])
Q("x0203", "Which base is labelled in blue?", "青で示されている塩基はどれですか？", "Cytosine", ["Adenine", "Thymine", "Guanine"], tags=["ocr", "colour", "sci"], diff="hard")
Q("x0204", "What container holds the glowing pattern?", "光る模様が入っている容器は何ですか？", "A petri dish|シャーレ", ["A frying pan|フライパン", "A soup plate|スープ皿", "A cookie tin|クッキー缶"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0206", "Which name is on the lowest branch at the right?", "右側のいちばん下の枝に書かれている名前はどれですか？", "Neanderthal", ["Chimpanzee", "Gorilla", "Orangutan"],
  tags=["ocr", "sci"], diff="hard")
Q("x0208", "What is plotted on the vertical axis?", "縦軸には何が取られていますか？", "Fluorescence", ["Pressure", "Speed", "Mass"], tags=["ocr", "sci"], diff="hard")
Q("x0208", "What temperature range does the horizontal axis cover?", "横軸はどの温度の範囲ですか？", "55 to 95 °C", ["0 to 100 °C", "10 to 50 °C", "100 to 200 °C"],
  tags=["ocr", "sci"], diff="hard")
Q("x0209", "What is named in the red caption?", "赤い字のキャプションに書かれているものは何ですか？", "DNA polymerase", ["RNA ribosome", "Hemoglobin", "Insulin"], tags=["ocr", "sci"], diff="hard")
Q("x0211", "What is written on the vertical axis of the scatter plot?", "散布図の縦軸には何と書かれていますか？", "Electronegativity", ["Temperature", "Population", "Wavelength"],
  tags=["ocr", "sci"], diff="hard")
Q("x0214", "Which block is named in the heading?", "見出しに書かれているブロックはどれですか？", "p block|p ブロック", ["s block|s ブロック", "d block|d ブロック", "f block|f ブロック"],
  tags=["ocr", "sci"], diff="hard")
Q("x0214", "Which element symbol is in the top right cell?", "右上のマスの元素記号はどれですか？", "He", ["H", "Ne", "Li"], tags=["ocr", "sci"], diff="medium")
Q("x0217", "What kind of chart is this?", "これはどんな表ですか？", "A periodic table of the elements|元素周期表", ["A calendar|カレンダー", "A seating plan|座席表", "A subway map|地下鉄路線図"],
  tags=["image-type", "sci"], diff="medium")
