# -*- coding: utf-8 -*-
"""Expansion set, field "life": x0358-x0394 -- fire extinguishers, first-aid boxes, warning and parking signs, escalators.
Signs and printed text are the practical part: what a sign forbids or warns of, which words and numbers it shows."""
from templates import Q, N, TYPE

Q("x0363", "How many fire extinguishers are there?", "消火器はいくつありますか？", "Two|2 本", ["One|1 本", "Three|3 本", "Four|4 本"], tags=["count", "safety", "life"], diff="easy")
Q("x0363", "What colour are the fire extinguishers?", "消火器は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Yellow|黄色"], tags=["colour", "safety", "life"], diff="easy")
Q("x0365", "Which words are on the lid of the tin?", "缶のふたに書かれている語はどれですか？", "FIRST AID", ["FIRE ALARM", "SAFE WATER", "EMERGENCY EXIT"], tags=["ocr", "safety", "life"], diff="easy")
Q("x0365", "Which brand name is on the tin?", "缶に書かれているブランド名はどれですか？", "COMPACTOID", ["ELASTOPLAST", "BAND-AID", "DETTOL"], tags=["ocr", "safety", "life"], diff="hard")
Q("x0366", "What symbol is on the cabinet door?", "戸棚の扉に付いている記号は何ですか？", "A red cross|赤い十字", ["A blue star|青い星", "A green arrow|緑の矢印", "A yellow circle|黄色い丸"],
  tags=["detail", "safety", "life"], diff="easy")
Q("x0367", "What does the hand-made sign say?", "手作りの看板には何と書かれていますか？", "First Aid box", ["Fire exit", "Lost property", "Tool box"], tags=["ocr", "safety", "life"], diff="easy")
Q("x0368", "Which word is written on the box in marker pen?", "箱にマーカーで書かれている語はどれですか？", "Pechuck", ["Pickup", "Peacock", "Puchuk"], tags=["ocr", "life"], diff="hard")
Q("x0369", "What is stored in the open car trunk?", "開いた車のトランクには何が収められていますか？", "Neatly organised emergency equipment|きちんと整理された緊急用の装備",
  ["Groceries|食料品", "Furniture|家具", "Luggage for a holiday|旅行の荷物"], tags=["detail", "safety", "life"], diff="medium")
Q("x0370", "What is the red tin likely to contain?", "この赤い缶には何が入っていると考えられますか？", "Bandages and first-aid supplies|包帯などの救急用品",
  ["Sewing materials|裁縫道具", "Cigarettes|たばこ", "Tea leaves|茶葉"], tags=["classify", "safety", "life"], diff="hard")
Q("x0371", "Which language is the text on the lid written in?", "ふたの文字は何語で書かれていますか？", "Dutch|オランダ語", ["German|ドイツ語", "Swedish|スウェーデン語", "Danish|デンマーク語"],
  tags=["language", "ocr", "life"], diff="hard")
Q("x0374", "What does the sign warn of?", "この標識は何を警告していますか？", "Pedestrians|歩行者", ["Falling rocks|落石", "A slippery road|滑りやすい路面", "Wild animals|動物の飛び出し"],
  tags=["classify", "safety", "life"], diff="medium")
N("x0374", "The sign is a red-bordered triangle", "標識は赤い縁取りの三角形である", True, tags=["attribute", "safety", "life"])
Q("x0375", "What does the warning sign on the pole refer to?", "柱の警告標識は何について警告していますか？", "High voltage|高電圧", ["Deep water|深い水", "Falling trees|倒木", "Wild dogs|野犬"],
  tags=["ocr", "language", "safety", "life"], diff="hard")
Q("x0377", "What is written on the electronic sign?", "電光掲示板には何と書かれていますか？", "WINTAHZ COMING", ["SUMMER SALE", "ROAD CLOSED", "DETOUR AHEAD"], tags=["ocr", "life"], diff="hard")
Q("x0378", "Which word is written in white on red at the top of the sign?", "看板の上部に赤地に白で書かれている語はどれですか？", "DANGER", ["WARNING", "CAUTION", "NOTICE"],
  tags=["ocr", "safety", "life"], diff="easy")
Q("x0378", "What does the sign warn of?", "この看板は何を警告していますか？", "An unguarded waterfront|監視員のいない水辺", ["Falling from a cliff|崖からの転落", "Wild animals|野生動物", "Thin ice|薄氷"],
  tags=["classify", "safety", "life"], diff="medium")
Q("x0379", "Which organisation's name is on the upper plaque?", "上のプレートに書かれている組織名はどれですか？", "The World Bank|世界銀行", ["The United Nations|国際連合", "The Red Cross|赤十字", "UNESCO|ユネスコ"],
  tags=["ocr", "record", "life"], diff="medium")
Q("x0381", "What does the sign say?", "看板には何と書かれていますか？", "NO PARKING ON YELLOW BRICK ROAD", ["NO ENTRY ON GRASS", "RESERVED FOR GUESTS", "PARKING ALLOWED"],
  tags=["ocr", "life"], diff="easy")
Q("x0382", "What is not allowed overnight according to the small lower sign?", "下の小さな看板によると、夜間に禁止されているのは何ですか？", "Parking|駐車", ["Camping|キャンプ", "Fishing|釣り", "Swimming|水泳"],
  tags=["ocr", "life"], diff="medium")
Q("x0383", "Which letter is on the blue signs?", "青い標識に書かれている文字はどれですか？", "P", ["H", "A", "S"], tags=["ocr", "life"], diff="easy")
Q("x0384", "Since which year is the parking reserved?", "この駐車場はいつから予約専用ですか？", "1830", ["1930", "1630", "1803"], tags=["ocr", "life"], diff="hard")
Q("x0385", "What does the blue square sign mean?", "青い四角の標識は何を意味しますか？", "Parking|駐車場", ["Hospital|病院", "Bus stop|バス停", "Pedestrian zone|歩行者専用"],
  tags=["classify", "life"], diff="easy")
Q("x0386", "What does the sign say?", "看板には何と書かれていますか？", "THOU SHALT NOT PARK HERE", ["NO PARKING ANYTIME", "PARK AT YOUR OWN RISK", "VISITORS WELCOME"],
  tags=["ocr", "life"], diff="medium")
N("x0386", "The sign has a red border", "看板には赤い縁がある", True, tags=["attribute", "life"])
Q("x0388", "What is shown in this picture?", "この写真には何が写っていますか？", "The inner mechanism of an escalator|エスカレーターの内部機構",
  ["A bicycle shop|自転車店", "A kitchen|台所", "A ship's engine room|船の機関室"], tags=["classify", "object", "life"], diff="hard")
Q("x0391", "What creates the orange streaks of light?", "オレンジ色の光の筋は何によるものですか？", "Sparks|火花", ["Car headlights|車のヘッドライト", "Fireflies|ホタル", "Laser beams|レーザー光"],
  tags=["detail", "life"], diff="hard")
Q("x0392", "What colour is the wall behind the escalators?", "エスカレーターの後ろの壁は何色ですか？", "Blue|青", ["Red|赤", "Green|緑", "White|白"], tags=["colour", "life"], diff="easy")
Q("x0394", "What is the camera looking down along?", "カメラは何に沿って見下ろしていますか？", "An escalator|エスカレーター", ["A stone staircase|石の階段", "A luggage conveyor|荷物のベルトコンベア", "A ski lift|スキーのリフト"],
  tags=["classify", "scene", "life"], diff="hard")
