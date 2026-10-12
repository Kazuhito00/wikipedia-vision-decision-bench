# -*- coding: utf-8 -*-
"""Expansion set, field "record": x0615-x0654 -- handwriting, typewriters, telegrams, posters, and charts / graphs. Reading
a heading, a name or an axis label, and saying what a chart is about, are the everyday document tasks."""
from templates import Q, N, TYPE

Q("x0619", "Which phrase is written in the lower part?", "下の部分に書かれている言葉はどれですか？", "In God we trust", ["In God we hope", "Under God we stand", "God save the King"],
  tags=["ocr", "record"], diff="hard")
Q("x0619", "Which tongue-twister is written at the top?", "上部に書かれている早口言葉はどれですか？", "Round the rugged rocks the ragged rascal ran",
  ["Peter Piper picked a peck of pickled peppers", "She sells sea shells on the sea shore", "How much wood would a woodchuck chuck"], tags=["ocr", "record"], diff="medium")
Q("x0623", "What machine is shown?", "写っている機械は何ですか？", "A typewriter|タイプライター", ["A piano|ピアノ", "A sewing machine|ミシン", "A cash register|レジスター"],
  tags=["classify", "object", "record"], diff="medium")
Q("x0624", "What is in the open case?", "開いたケースの中には何が入っていますか？", "A portable typewriter|携帯用タイプライター", ["A radio|ラジオ", "A camera|カメラ", "A microscope|顕微鏡"],
  tags=["classify", "object", "record"], diff="medium")
Q("x0625", "Who is named at the bottom of the sheet-music cover?", "楽譜の表紙の下に書かれている名前は誰ですか？", "DAVE REED JR.", ["IRVING BERLIN", "GEORGE COHAN", "JOHN SOUSA"],
  tags=["ocr", "record"], diff="hard")
Q("x0627", "Which machines does the German plate show?", "ドイツ語の図版は何の機械を示していますか？", "Typewriters|タイプライター", ["Sewing machines|ミシン", "Printing presses|印刷機", "Cameras|カメラ"],
  tags=["language", "ocr", "record"], diff="hard")
Q("x0628", "Which company's name is on the postcard?", "絵はがきに書かれている会社名はどれですか？", "Smith Premier Typewriter Co.", ["Remington Arms Co.", "Singer Sewing Co.", "Kodak Co."],
  tags=["ocr", "record"], diff="hard")
Q("x0628", "Which city is named on the postcard?", "絵はがきに書かれている都市はどれですか？", "Syracuse|シラキュース", ["Buffalo|バッファロー", "Albany|オールバニー", "Rochester|ロチェスター"],
  tags=["ocr", "record"], diff="hard")
Q("x0630", "Which company's name is at the top of the document?", "書類の上部に書かれている会社名はどれですか？", "WESTERN UNION", ["AT&T", "ATLANTIC CABLE", "POSTAL TELEGRAPH"], tags=["ocr", "record"], diff="medium")
Q("x0633", "Which country's name is at the top of the telegram?", "電報の上部に書かれている国名はどれですか？", "Cuba|キューバ", ["Mexico|メキシコ", "Chile|チリ", "Peru|ペルー"], tags=["ocr", "record"], diff="hard")
Q("x0633", "Which language is the telegram written in?", "電報は何語で書かれていますか？", "Spanish|スペイン語", ["Portuguese|ポルトガル語", "Italian|イタリア語", "French|フランス語"],
  tags=["language", "record"], diff="medium")
Q("x0636", "Which script is the telegram written in?", "電報はどの文字で書かれていますか？", "Greek|ギリシャ文字", ["Cyrillic|キリル文字", "Arabic|アラビア文字", "Hebrew|ヘブライ文字"],
  tags=["language", "record"], diff="hard")
Q("x0637", "Which number appears in big letters on the poster?", "ポスターに大きく書かれている数字はどれですか？", "30", ["20", "25", "40"], tags=["ocr", "record"], diff="medium")
Q("x0637", "Which software project is named on the poster?", "ポスターに書かれているソフトウェアプロジェクトはどれですか？", "Debian", ["Ubuntu", "Fedora", "Arch Linux"], tags=["ocr", "record"], diff="medium")
Q("x0639", "Whose name is in large letters on the poster?", "ポスターに大きな文字で書かれている名前は誰のものですか？", "CLYDE SIMPSON", ["JOHN SMITH", "HARRY TRUMAN", "JIM BROWN"], tags=["ocr", "record"], diff="hard")
Q("x0639", "Where will the event be held, according to the bottom line?", "最下行によると、催しはどこで開かれますか？", "At the Roosevelt Hotel|ルーズベルト・ホテル", ["At the Hilton|ヒルトン", "At the Ritz|リッツ", "At the Plaza|プラザ"],
  tags=["ocr", "record"], diff="hard")
Q("x0641", "Which country's name appears in the poster title?", "ポスターの題名に書かれている国名はどれですか？", "Belgium|ベルギー", ["Switzerland|スイス", "Austria|オーストリア", "Denmark|デンマーク"],
  tags=["ocr", "language", "record"], diff="hard")
Q("x0643", "What vehicle is drawn on the poster?", "ポスターに描かれている乗り物は何ですか？", "A steam train|蒸気機関車", ["A ship|船", "An airplane|飛行機", "A bus|バス"], tags=["classify", "vehicle", "record"], diff="medium")
Q("x0644", "What product is advertised?", "何の製品の広告ですか？", "An anise liquor|アニス酒", ["Chocolate|チョコレート", "Soap|石鹸", "Coffee|コーヒー"], tags=["classify", "ocr", "record"], diff="hard")
Q("x0645", "Which constellation is the chart centred on?", "星図はどの星座を中心にしていますか？", "Cancer|かに座", ["Leo|しし座", "Gemini|ふたご座", "Orion|オリオン座"], tags=["ocr", "sci", "record"], diff="hard")
Q("x0645", "Which cluster code is labelled near the centre?", "中央付近に書かれている星団の記号はどれですか？", "M44", ["M31", "M45", "M42"], tags=["ocr", "sci", "record"], diff="hard")
Q("x0646", "What does the chart title say?", "グラフの題名には何と書かれていますか？", "Average annual growth in GDP", ["Unemployment rate", "Annual inflation", "Federal debt"], tags=["ocr", "record"], diff="medium")
Q("x0646", "Which name labels the first bar on the left?", "左端の棒に付いている名前はどれですか？", "Harry S. Truman", ["Joe Biden", "Ronald Reagan", "Richard Nixon"], tags=["ocr", "record"], diff="hard")
Q("x0648", "What shape does the curve have?", "曲線はどんな形をしていますか？", "It rises to a peak and then falls|ピークまで上がってから下がる",
  ["It rises steadily without falling|下がらずに上がり続ける", "It is a flat line|水平線", "It zigzags evenly up and down|規則的にぎざぎざする"], tags=["detail", "record"], diff="medium")
Q("x0649", "What is counted per year in this chart?", "このグラフは 1 年ごとに何を数えていますか？", "Entries|項目数", ["Visitors|来場者", "Votes|票", "Sales|売上"], tags=["ocr", "record"], diff="hard")
Q("x0650", "What is counted per year in this chart?", "このグラフは 1 年ごとに何を数えていますか？", "References|参照数", ["Photographs|写真", "Lawsuits|訴訟", "Goals|ゴール"], tags=["ocr", "record"], diff="hard")
Q("x0652", "What does the chart count?", "グラフは何を数えていますか？", "Tornado reports|竜巻の報告", ["Earthquakes|地震", "Hurricanes|ハリケーン", "Wildfires|山火事"], tags=["ocr", "sci", "record"], diff="hard")
Q("x0652", "Which agency's logo is in the lower right corner?", "右下のロゴはどの機関のものですか？", "NOAA", ["NASA", "FEMA", "CDC"], tags=["ocr", "record"], diff="hard")
Q("x0654", "What kind of graph is this?", "これはどんなグラフですか？", "A function graph on a coordinate grid|座標のグリッド上の関数のグラフ", ["A weather map|天気図", "A floor plan|間取り図", "A family tree|家系図"],
  tags=["image-type", "record"], diff="medium")
