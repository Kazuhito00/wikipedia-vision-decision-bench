# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0101-x0120 (gravitational lenses, space station, robots). Pictures of identifiable people
were not used as subjects of questions."""
from templates import Q, N, TYPE

Q("x0101", "What surrounds the bright orange galaxy at the centre?", "中央の明るいオレンジ色の銀河を取り囲んでいるものは何ですか？",
  "A bluish ring of light|青みがかった光の輪", ["A cross of light|十字の光", "A long tail|長い尾", "A row of dark spots|並んだ暗い斑点"], tags=["detail", "sci"], diff="hard")
Q("x0102", "Which telescope is named in the caption?", "キャプションに書かれている望遠鏡はどれですか？", "Hubble Space Telescope|ハッブル宇宙望遠鏡",
  ["Spitzer Space Telescope|スピッツァー宇宙望遠鏡", "Kepler|ケプラー", "James Webb|ジェームズ・ウェッブ"], tags=["ocr", "sci"], diff="hard")
N("x0102", "The picture is divided into six panels", "画像は 6 つのパネルに分かれている", True, tags=["count", "sci"], diff="medium")
Q("x0103", "How many stages does the diagram show side by side?", "図は段階をいくつ並べて示していますか？", "Four|4 つ", ["Two|2 つ", "Three|3 つ", "Five|5 つ"],
  tags=["count", "sci"], diff="medium")
Q("x0107", "What floats in the middle of the module?", "モジュールの中央に浮かんでいるものは何ですか？", "A ball|ボール", ["A pillow|枕", "A cat|猫", "A lamp|ランプ"],
  tags=["classify", "object", "sci"], diff="medium")
N("x0107", "Many national flags hang along the top of the wall", "壁の上部にたくさんの国旗が掲げられている", True, tags=["detail", "sci"], diff="medium")
Q("x0109", "What is shown against the Earth?", "地球を背景に写っているものは何ですか？", "The International Space Station|国際宇宙ステーション",
  ["A bridge|橋", "An oil rig|石油掘削施設", "A radio telescope array|電波望遠鏡群"], tags=["classify", "sci"], diff="medium")
N("x0109", "Large solar panels extend from the structure", "構造物から大きな太陽電池パネルが伸びている", True, tags=["detail", "sci"])
Q("x0110", "Which system does the text describe?", "文章はどのシステムについて説明していますか？", "Thermal Control System|熱制御システム",
  ["Power system|電力システム", "Communication system|通信システム", "Life-support system|生命維持システム"], tags=["ocr", "sci"], diff="hard")
N("x0112", "Letters label the parts of the structure in the picture", "図には構造物の各部を示す文字が付いている", True, tags=["detail", "sci"], diff="medium")
Q("x0113", "What kind of document is this?", "これはどんな資料ですか？", "An old printed newspaper notice|古い新聞の記事・広告",
  ["A restaurant receipt|レストランのレシート", "A road map|道路地図", "A bank cheque|小切手"], tags=["image-type", "record", "sci"], diff="medium")
Q("x0114", "Whose name appears in the heading of the notice?", "広告の見出しに書かれている名前は誰のものですか？", "Jaquet Droz", ["Maillardet", "Edison", "Babbage"],
  tags=["ocr", "record", "sci"], diff="hard")
Q("x0115", "What kind of machine is on the ground?", "地面にある機械はどんな種類ですか？", "A tracked robot|無限軌道（クローラー）式のロボット",
  ["A farm tractor|農業用トラクター", "A snowmobile|スノーモービル", "A forklift|フォークリフト"], tags=["classify", "vehicle", "sci"], diff="hard")
Q("x0116", "What machine stands in front of the wooden wall?", "木の壁の前に立っている機械は何ですか？", "A robot with mechanical arms|機械の腕を持つロボット",
  ["A washing machine|洗濯機", "A piano|ピアノ", "A bicycle|自転車"], tags=["classify", "object", "sci"], diff="medium")
Q("x0118", "What number is printed on the yellow robot?", "黄色いロボットに印刷されている数字は何ですか？", "2", ["5", "7", "9"], tags=["ocr", "sci"], diff="medium")
Q("x0119", "What colour is the large robot in the exhibition?", "展示会の大きなロボットは何色ですか？", "Orange|オレンジ", ["Blue|青", "Green|緑", "Black|黒"],
  tags=["colour", "sci"], diff="medium")
