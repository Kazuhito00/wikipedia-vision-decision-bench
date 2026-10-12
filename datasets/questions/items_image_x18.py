# -*- coding: utf-8 -*-
"""Expansion set, field "record": x0575-x0614 -- certificates, ledgers, menus, receipts, invoices, passport covers. Personal
documents showing a photograph of a private person were not used."""
from templates import Q, N, TYPE

Q("x0577", "Which word is the large title of the document?", "書類の大きな題字はどれですか？", "CHARTE", ["DIPLOME", "PASSEPORT", "CERTIFICAT"], tags=["ocr", "record"], diff="hard")
Q("x0577", "Which language is the main text written in?", "本文は何語で書かれていますか？", "French|フランス語", ["Spanish|スペイン語", "Italian|イタリア語", "Portuguese|ポルトガル語"],
  tags=["language", "record"], diff="hard")
Q("x0578", "Which script is the certificate written in?", "賞状はどの文字で書かれていますか？", "Bengali|ベンガル文字", ["Devanagari|デーヴァナーガリー文字", "Tamil|タミル文字", "Thai|タイ文字"],
  tags=["language", "ocr", "record"], diff="hard")
Q("x0578", "Which organisation's name appears at the bottom left?", "左下に書かれている組織名はどれですか？", "Wikimedia", ["UNESCO", "Mozilla", "Google"], tags=["ocr", "record"], diff="hard")
Q("x0581", "What kind of document is this?", "これはどんな書類ですか？", "A handwritten account ledger|手書きの帳簿", ["A music score|楽譜", "A street map|地図", "A comic page|漫画のページ"],
  tags=["image-type", "record"], diff="medium")
Q("x0588", "Which language is the menu written in?", "メニューは何語で書かれていますか？", "Portuguese|ポルトガル語", ["Spanish|スペイン語", "Italian|イタリア語", "French|フランス語"],
  tags=["language", "record"], diff="hard")
Q("x0588", "Which phrase ends the menu?", "メニューの最後の言葉はどれですか？", "BOM APETITE", ["BON APPÉTIT", "BUEN PROVECHO", "GUTEN APPETIT"], tags=["ocr", "record"], diff="hard")
Q("x0589", "Which drink is listed on the receipt?", "レシートに書かれている飲み物はどれですか？", "Water|水", ["Beer|ビール", "Wine|ワイン", "Coffee|コーヒー"], tags=["ocr", "language", "record"], diff="hard")
Q("x0589", "Which language is the receipt written in?", "レシートは何語で書かれていますか？", "German|ドイツ語", ["Dutch|オランダ語", "Swedish|スウェーデン語", "Polish|ポーランド語"],
  tags=["language", "record"], diff="hard")
Q("x0591", "What does the company on the bill do?", "請求書の会社は何をしていますか？", "Photography|写真撮影", ["Baking bread|パン作り", "Plumbing|配管工事", "Printing newspapers|新聞印刷"],
  tags=["ocr", "record"], diff="medium")
Q("x0591", "Which city is in the address?", "住所に書かれている都市はどれですか？", "New York|ニューヨーク", ["Boston|ボストン", "Chicago|シカゴ", "London|ロンドン"], tags=["ocr", "record"], diff="hard")
Q("x0592", "What kind of code is printed at the lower left of the receipt?", "レシートの左下に印刷されているコードはどれですか？", "A QR code|QR コード", ["A zip code|郵便番号", "A Morse code|モールス符号", "A colour code|カラーコード"],
  tags=["detail", "record"], diff="medium")
Q("x0596", "What colour is the receipt paper?", "レシートの紙は何色ですか？", "Yellow|黄色", ["White|白", "Blue|青", "Pink|ピンク"], tags=["colour", "record"], diff="easy")
Q("x0596", "Which organisation's name is printed at the top?", "上部に印刷されている組織名はどれですか？", "The Plains Farmers' Exchange", ["The Plains Bank", "Farmers' Insurance", "Grain Elevator Company"],
  tags=["ocr", "record"], diff="hard")
Q("x0597", "Which city is named in the date line?", "日付の行に書かれている都市はどれですか？", "Glasgow|グラスゴー", ["Edinburgh|エディンバラ", "Dundee|ダンディー", "Aberdeen|アバディーン"],
  tags=["ocr", "record"], diff="hard")
Q("x0603", "Which hotel name is printed on the bill?", "請求書に印刷されているホテル名はどれですか？", "Planters' House", ["Palmer House", "Astor House", "Grand Hotel"], tags=["ocr", "record"], diff="hard")
Q("x0603", "Which month is written in the date?", "日付に書かれている月はどれですか？", "May|5 月", ["April|4 月", "June|6 月", "July|7 月"], tags=["ocr", "record"], diff="hard")
Q("x0604", "What kind of business is named at the top?", "上部に書かれているのはどんな事業ですか？", "A hotel (Leland House)|ホテル（リーランド・ハウス）", ["A bank|銀行", "A school|学校", "A railway company|鉄道会社"],
  tags=["ocr", "record"], diff="medium")
Q("x0608", "Which country's passport is this?", "これはどの国のパスポートですか？", "Australia|オーストラリア", ["Canada|カナダ", "New Zealand|ニュージーランド", "United Kingdom|イギリス"],
  tags=["ocr", "record"], diff="medium")
Q("x0608", "What colour is the passport cover?", "パスポートの表紙は何色ですか？", "Dark blue|紺", ["Red|赤", "Green|緑", "Black|黒"], tags=["colour", "record"], diff="easy")
Q("x0609", "Which country issued this passport?", "このパスポートを発行した国はどこですか？", "Egypt|エジプト", ["Syria|シリア", "Saudi Arabia|サウジアラビア", "Libya|リビア"],
  tags=["ocr", "language", "record"], diff="hard")
Q("x0610", "Which word is at the bottom of the cover?", "表紙の下部に書かれている語はどれですか？", "REISEPASS", ["PASSPORT", "PASSEPORT", "PASAPORTE"], tags=["ocr", "language", "record"], diff="medium")
Q("x0610", "What colour is the passport cover?", "パスポートの表紙は何色ですか？", "Dark red|濃い赤", ["Blue|青", "Black|黒", "Green|緑"], tags=["colour", "record"], diff="easy")
