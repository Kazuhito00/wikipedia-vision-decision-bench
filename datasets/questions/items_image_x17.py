# -*- coding: utf-8 -*-
"""Expansion set, field "record" (records and documents): x0532-x0574 -- newspapers, tickets, timetables, banknotes and
emergency money, stamps, certificates. Reading names, numbers, years and languages off a document is the task."""
from templates import Q, N, TYPE

Q("x0532", "Which script is the newspaper's title written in?", "新聞の題字はどの文字で書かれていますか？", "Georgian|ジョージア文字", ["Cyrillic|キリル文字", "Arabic|アラビア文字", "Armenian|アルメニア文字"],
  tags=["language", "ocr", "record"], diff="hard")
Q("x0533", "What does the rack hold?", "ラックに置かれているものは何ですか？", "Magazines|雑誌", ["Shoes|靴", "Umbrellas|傘", "Bottles|瓶"], tags=["classify", "object", "record"], diff="easy")
Q("x0534", "Whose name is printed in large letters at the top?", "上部に大きな文字で印刷されている名前は誰のものですか？", "BOLESŁAW WASYLEWSKI",
  ["STANISŁAW WYSPIAŃSKI", "JAN KOWALSKI", "ADAM MICKIEWICZ"], tags=["ocr", "record"], diff="hard")
Q("x0535", "What is the title of the newspaper?", "新聞の題字は何ですか？", "L'ECHO", ["LE FIGARO", "LE MONDE", "LA PRESSE"], tags=["ocr", "record"], diff="hard")
Q("x0536", "Which country is named at the top of the page?", "ページの上部に書かれている国はどれですか？", "Malta|マルタ", ["Monaco|モナコ", "Cyprus|キプロス", "Iceland|アイスランド"],
  tags=["ocr", "record"], diff="medium")
Q("x0538", "Which language is the newspaper written in?", "新聞は何語で書かれていますか？", "Spanish|スペイン語", ["Portuguese|ポルトガル語", "Italian|イタリア語", "French|フランス語"],
  tags=["language", "record"], diff="hard")
Q("x0539", "Which word is printed at the top of the ticket?", "切符の上部に印刷されている語はどれですか？", "METROPOLITAIN", ["TÉLÉGRAPHE", "AUTOBUS", "TRAMWAY"], tags=["ocr", "record"], diff="hard")
Q("x0540", "Which society's name is at the top of the certificate?", "賞状の上部に書かれている団体名はどれですか？", "Society of the Army of the Tennessee",
  ["Society of the Cincinnati", "Army of the Potomac", "Grand Army of the Republic"], tags=["ocr", "record"], diff="hard")
Q("x0542", "Which number is printed large on the ticket?", "切符に大きく印刷されている番号はどれですか？", "10373", ["10378", "10573", "13073"], tags=["ocr", "record"], diff="hard")
Q("x0542", "Which city is named on the ticket?", "切符に書かれている都市はどれですか？", "Hamburg|ハンブルク", ["Berlin|ベルリン", "Munich|ミュンヘン", "Vienna|ウィーン"], tags=["ocr", "record"], diff="medium")
Q("x0544", "Which city is named on the invitation?", "招待状に書かれている都市はどれですか？", "Seattle|シアトル", ["Portland|ポートランド", "Boston|ボストン", "Denver|デンバー"], tags=["ocr", "record"], diff="hard")
Q("x0544", "What kind of document is this?", "これはどんな書類ですか？", "A printed invitation card|印刷された招待状", ["A tax form|納税書類", "A train ticket|列車の切符", "A passport|パスポート"],
  tags=["image-type", "record"], diff="medium")
Q("x0545", "Which subject is named on the card?", "カードに書かれている科目はどれですか？", "Chemistry|化学", ["Anatomy|解剖学", "Law|法学", "Music|音楽"], tags=["ocr", "record"], diff="hard")
Q("x0545", "Which city is named on the card?", "カードに書かれている都市はどれですか？", "Philadelphia|フィラデルフィア", ["Boston|ボストン", "Chicago|シカゴ", "Baltimore|ボルチモア"],
  tags=["ocr", "record"], diff="hard")
Q("x0548", "What does the heading of the table concern?", "表の見出しは何に関するものですか？", "Hours of fog|霧の時間", ["Hours of sunshine|日照時間", "Rainfall|降水量", "Wind speed|風速"],
  tags=["ocr", "record"], diff="hard")
Q("x0549", "What number is in the title of the notice?", "掲示の題名に書かれている番号はどれですか？", "2", ["1", "3", "4"], tags=["ocr", "record"], diff="hard")
Q("x0552", "Which year is in the heading of the diagram?", "図の見出しに書かれている年はどれですか？", "1961", ["1951", "1971", "1941"], tags=["ocr", "record"], diff="hard")
Q("x0552", "Which region is named in the heading?", "見出しに書かれている地域はどれですか？", "South Australian Murraylands|南オーストラリアのマレーランド",
  ["Tasmanian Highlands|タスマニアの高地", "Welsh Marches|ウェールズ境界地方", "Scottish Lowlands|スコットランド低地"], tags=["ocr", "record"], diff="hard")
Q("x0553", "Which days are the column headings?", "列の見出しは何曜日ですか？", "Monday to Friday|月曜から金曜", ["Saturday and Sunday|土曜と日曜", "Monday to Sunday|月曜から日曜", "Tuesday to Saturday|火曜から土曜"],
  tags=["ocr", "record"], diff="medium")
N("x0553", "The schedule grid has been filled in with times", "時間割の表には時刻が書き込まれている", False, tags=["detail", "record"], diff="medium")
Q("x0554", "Which language is the announcement written in?", "お知らせは何語で書かれていますか？", "Turkish|トルコ語", ["Greek|ギリシャ語", "Hungarian|ハンガリー語", "Finnish|フィンランド語"],
  tags=["language", "record"], diff="hard")
Q("x0554", "Which word is the heading in red?", "赤い見出しの語はどれですか？", "DUYURU!", ["ACHTUNG!", "ATTENTION!", "AVISO!"], tags=["ocr", "record"], diff="hard")
Q("x0555", "What amount does the note state in words?", "紙幣に文字で書かれている金額はどれですか？", "Fifty million marks|5000 万マルク",
  ["Fifty marks|50 マルク", "Five hundred marks|500 マルク", "Fifty thousand marks|5 万マルク"], tags=["ocr", "record"], diff="hard")
Q("x0556", "Which city is named on the emergency note?", "この緊急紙幣に書かれている都市はどれですか？", "Cologne (Köln)|ケルン", ["Berlin|ベルリン", "Hamburg|ハンブルク", "Munich|ミュンヘン"],
  tags=["ocr", "record"], diff="hard")
Q("x0556", "What value is shown on the note?", "紙幣に示されている額面はどれですか？", "50 Pfennig", ["10 Pfennig", "1 Mark", "5 Mark"], tags=["ocr", "record"], diff="medium")
Q("x0557", "What value is written in words at the top?", "上部に文字で書かれている額面はどれですか？", "Ten Pfennig|10 ペニヒ", ["Five Pfennig|5 ペニヒ", "Fifty Pfennig|50 ペニヒ", "One Mark|1 マルク"],
  tags=["ocr", "record"], diff="hard")
Q("x0558", "Which place is named at the top of the voucher?", "引換券の上部に書かれている地名はどれですか？", "Apenrade", ["Flensburg", "Kiel", "Lübeck"], tags=["ocr", "record"], diff="hard")
Q("x0559", "Which year is printed on the voucher?", "引換券に印刷されている年はどれですか？", "1920", ["1910", "1930", "1923"], tags=["ocr", "record"], diff="hard")
Q("x0561", "Which spa town is named on the note?", "紙幣に書かれている温泉地はどれですか？", "Bad Oeynhausen", ["Bad Homburg", "Baden-Baden", "Bad Ems"], tags=["ocr", "record"], diff="hard")
Q("x0562", "What value is written in words?", "文字で書かれている額面はどれですか？", "One Mark|1 マルク", ["Five Marks|5 マルク", "Ten Marks|10 マルク", "One Pfennig|1 ペニヒ"], tags=["ocr", "record"], diff="hard")
Q("x0563", "Which event is printed on the cover?", "封筒に印刷されている出来事はどれですか？", "The first round-the-world flight|初の世界一周飛行",
  ["The first Olympic Games|初のオリンピック", "A royal wedding|王室の結婚式", "A world fair|万国博覧会"], tags=["ocr", "record"], diff="hard")
Q("x0564", "What plant does the stamp show?", "切手に描かれている植物は何ですか？", "A cucumber|きゅうり", ["A tomato|トマト", "A pumpkin|カボチャ", "A carrot|にんじん"],
  tags=["classify", "language", "record"], diff="hard")
Q("x0564", "What value is printed on the stamp?", "切手に印刷されている額面はどれですか？", "3.00", ["1.00", "5.00", "30.00"], tags=["ocr", "record"], diff="medium")
Q("x0566", "Which place name is printed at the top of the stamp?", "切手の上部に印刷されている地名はどれですか？", "Fiume", ["Trieste", "Venice", "Zara"], tags=["ocr", "record"], diff="hard")
Q("x0566", "Which year is printed in Roman numerals?", "ローマ数字で印刷されている年はどれですか？", "1919", ["1909", "1929", "1991"], tags=["ocr", "record"], diff="hard")
Q("x0569", "Which country does the stamp come from (the Latin name on it)?", "切手に書かれたラテン語名から、どの国の切手ですか？", "Switzerland (Helvetia)|スイス（ヘルヴェティア）",
  ["Austria|オーストリア", "Belgium|ベルギー", "Sweden|スウェーデン"], tags=["ocr", "record"], diff="hard")
Q("x0569", "Which year is printed on the stamp?", "切手に印刷されている年はどれですか？", "1922", ["1912", "1932", "1942"], tags=["ocr", "record"], diff="hard")
Q("x0570", "What is the magnifying glass held over?", "虫眼鏡は何の上にかざされていますか？", "A postage stamp|切手", ["A coin|硬貨", "A map|地図", "A leaf|葉"], tags=["classify", "object", "record"], diff="medium")
Q("x0572", "Which institution is named at the top of the certificate?", "証書の上部に書かれている機関はどれですか？", "Royal Bavarian Academy of Fine Arts|バイエルン王立美術アカデミー",
  ["Royal Bavarian Academy of Sciences|バイエルン王立科学アカデミー", "Royal Prussian Academy of Music|プロイセン王立音楽アカデミー", "Imperial Library|帝国図書館"], tags=["ocr", "record"], diff="hard")
Q("x0574", "What kind of document is this?", "これはどんな書類ですか？", "A certificate of recognition|表彰状", ["A birth certificate|出生証明書", "A tax invoice|請求書", "A passport|パスポート"],
  tags=["image-type", "record"], diff="medium")
Q("x0574", "Which legislative body is named in the header?", "上部に書かれている議会はどれですか？", "Assembly", ["Senate", "Parliament", "Congress"], tags=["ocr", "record"], diff="hard")
