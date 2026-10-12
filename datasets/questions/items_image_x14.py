# -*- coding: utf-8 -*-
"""Expansion set, field "life": x0395-x0434 -- elevators, mailboxes and parcel lockers, benches, waste bins, laundry.
Pictures with people as the subject were not used."""
from templates import Q, N, TYPE

Q("x0398", "What kind of doors are in the stone wall?", "石の壁にあるのはどんな扉ですか？", "Elevator doors|エレベーターの扉", ["Garage doors|ガレージの扉", "Oven doors|オーブンの扉", "Cupboard doors|戸棚の扉"],
  tags=["classify", "object", "life"], diff="medium")
N("x0397", "There are two elevator doors in the wall", "壁にはエレベーターの扉が 2 つある", True, tags=["count", "life"], diff="medium")
Q("x0404", "Which word is written in red on the mailbox?", "郵便受けに赤で書かれている語はどれですか？", "Christmas", ["Easter", "Birthday", "Halloween"], tags=["ocr", "life"], diff="medium")
N("x0404", "The mailbox is covered in snow", "郵便受けは雪に覆われている", True, tags=["scene", "life"])
Q("x0406", "What kind of machine is this?", "これはどんな機械ですか？", "A parcel locker|宅配ロッカー", ["A bank vault|銀行の金庫", "A refrigerator|冷蔵庫", "A ticket gate|改札機"],
  tags=["classify", "object", "life"], diff="hard")
Q("x0406", "Which brand name is on the locker?", "ロッカーに書かれているブランド名はどれですか？", "speedy", ["DHL", "FedEx", "UPS"], tags=["ocr", "life"], diff="hard")
Q("x0407", "Which number is on the small sign?", "小さな表示板の番号はどれですか？", "13A", ["13B", "18A", "31A"], tags=["ocr", "life"], diff="hard")
Q("x0408", "What does the heading on the postcard say?", "絵はがきの見出しには何と書かれていますか？", "WHY DONT YOU WRITE?", ["WHERE ARE YOU?", "COME HOME SOON", "HAPPY NEW YEAR"],
  tags=["ocr", "record", "life"], diff="medium")
Q("x0409", "What colour is the postbox?", "ポストは何色ですか？", "Pink|ピンク", ["Red|赤", "Blue|青", "Yellow|黄色"], tags=["colour", "life"], diff="medium")
Q("x0409", "Which language is the lettering on the postbox?", "ポストの文字は何語ですか？", "French|フランス語", ["Spanish|スペイン語", "Italian|イタリア語", "German|ドイツ語"],
  tags=["language", "ocr", "life"], diff="hard")
Q("x0411", "What is the bench made of?", "ベンチは何でできていますか？", "Stone|石", ["Wood|木", "Plastic|プラスチック", "Metal|金属"], tags=["attribute", "life"], diff="medium")
Q("x0412", "What covers the ground around the bench?", "ベンチの周りの地面を覆っているものは何ですか？", "Fallen leaves|落ち葉", ["Snow|雪", "Sand|砂", "Flowers|花"], tags=["scene", "life"], diff="easy")
Q("x0416", "What lies beyond the bench?", "ベンチの向こうに広がっているものは何ですか？", "The sea|海", ["A desert|砂漠", "A city|都市", "A forest|森"], tags=["scene", "life"], diff="easy")
Q("x0421", "What colours are the two wheeled bins?", "2 つのごみ箱（車輪付き）は何色ですか？", "Green and blue|緑と青", ["Red and yellow|赤と黄", "Black and white|黒と白", "Orange and purple|オレンジと紫"],
  tags=["colour", "life"], diff="medium")
Q("x0423", "Which brand name is written on the grey bin?", "灰色のごみ箱に書かれているブランド名はどれですか？", "Huskee", ["Rubbermaid", "Tupperware", "Coleman"], tags=["ocr", "life"], diff="hard")
Q("x0425", "How many small bins are lined up?", "小さなごみ箱はいくつ並んでいますか？", "Five|5 つ", ["Three|3 つ", "Four|4 つ", "Six|6 つ"], tags=["count", "life"], diff="medium")
Q("x0426", "Which word is on the orange sign on the cage?", "かごのオレンジ色の貼り紙に書かれている語はどれですか？", "NOTICE", ["DANGER", "SALE", "EXIT"], tags=["ocr", "life"], diff="medium")
Q("x0432", "What are the white machines in the room?", "部屋にある白い機械は何ですか？", "Washing machines|洗濯機", ["Ovens|オーブン", "Printers|プリンター", "Refrigerators|冷蔵庫"],
  tags=["classify", "object", "life"], diff="medium")
Q("x0433", "What hangs from the lines across the building front?", "建物の正面に渡された紐に掛かっているものは何ですか？", "Laundry|洗濯物", ["Flags|旗", "Fishing nets|漁網", "Paper lanterns|提灯"],
  tags=["detail", "life"], diff="medium")
