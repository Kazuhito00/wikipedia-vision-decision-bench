# -*- coding: utf-8 -*-
"""Expansion set, field "life": x0475-x0514 -- bus stations, ferries, tools, gardens, fire engines. Foreign-language signs
(Cyrillic, French) are included on purpose: reading a sign in another script is an everyday task."""
from templates import Q, N, TYPE

Q("x0476", "What vehicles stand next to the white building?", "白い建物のそばに止まっている乗り物は何ですか？", "Buses|バス", ["Trams|路面電車", "Ferries|フェリー", "Tractors|トラクター"],
  tags=["classify", "vehicle", "life"], diff="medium")
Q("x0480", "Which alphabet is the sign on the building written in?", "建物の看板はどの文字で書かれていますか？", "Cyrillic|キリル文字", ["Greek|ギリシャ文字", "Arabic|アラビア文字", "Hangul|ハングル"],
  tags=["language", "ocr", "life"], diff="hard")
Q("x0481", "What kind of shop does the red sign advertise?", "赤い看板はどんな店を示していますか？", "A pharmacy|薬局", ["A bakery|パン屋", "A bank|銀行", "A bookshop|書店"],
  tags=["language", "ocr", "life"], diff="hard")
Q("x0485", "Which game name is printed on the board?", "盤に印刷されているゲーム名はどれですか？", "GAME OF DEER STALKING", ["GAME OF GOOSE", "GAME OF CHESS", "GAME OF FOX HUNTING"],
  tags=["ocr", "record", "life"], diff="hard")
Q("x0487", "Which language is the title written in?", "題名は何語で書かれていますか？", "French|フランス語", ["Spanish|スペイン語", "Italian|イタリア語", "English|英語"],
  tags=["language", "ocr", "record", "life"], diff="hard")
Q("x0487", "Whose name is printed at the bottom of the title?", "題名の下に印刷されている名前は誰のものですか？", "Daubigny", ["Monet", "Manet", "Millet"],
  tags=["ocr", "record", "life"], diff="hard")
Q("x0490", "What kind of vessel is this?", "これはどんな船ですか？", "A river ferry|川の渡し船", ["A submarine|潜水艦", "A sailing yacht|ヨット", "An airship|飛行船"],
  tags=["classify", "vehicle", "life"], diff="medium")
Q("x0493", "What name is written at the top?", "上部に書かれている名前は何ですか？", "Leatherman Leap", ["Swiss Champion", "Victorinox Spartan", "Gerber Dime"], tags=["ocr", "life"], diff="hard")
Q("x0493", "What colour is the handle of the multitool?", "マルチツールの持ち手は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Black|黒"], tags=["colour", "life"], diff="easy")
Q("x0494", "Which model name is written at the top?", "上部に書かれているモデル名はどれですか？", "Leatherman Squirt P4", ["Leatherman Wave", "Leatherman Leap", "Leatherman Charge"],
  tags=["ocr", "life"], diff="hard")
Q("x0499", "Which word is at the top of the plaque?", "プレートの上部の語はどれですか？", "UNCONQUERED", ["UNDEFEATED", "UNITED", "UNKNOWN"], tags=["ocr", "record", "life"], diff="hard")
N("x0499", "The plaque is mounted on a boulder", "プレートは大きな岩に取り付けられている", True, tags=["detail", "life"])
Q("x0501", "What stands in the middle of the garden?", "庭の中央に立っているものは何ですか？", "A fountain|噴水", ["A statue of a horse|馬の像", "A windmill|風車", "A tent|テント"],
  tags=["classify", "scene", "life"], diff="medium")
Q("x0506", "What kind of garden is shown from above?", "上から見たのはどんな庭ですか？", "A formal garden with geometric paths|幾何学模様の小道がある整形庭園",
  ["A rice field|田んぼ", "A forest|森", "A desert|砂漠"], tags=["classify", "scene", "life"], diff="hard")
Q("x0509", "What kind of vehicle is the large red truck?", "大きな赤いトラックはどんな車ですか？", "A fire engine|消防車", ["An ambulance|救急車", "A bus|バス", "A garbage truck|ごみ収集車"],
  tags=["classify", "vehicle", "life"], diff="easy")
