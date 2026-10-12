# -*- coding: utf-8 -*-
"""Image items from the Wikipedia harvest, h0101-h0160 (pictures used by both wikis)."""
from templates import Q, N, TYPE, S, colour

Q("h0102", "What kind of landscape is this?", "これはどんな景色ですか？", "A mountain lake|山の湖",
  ["A desert|砂漠", "A city|都市", "A farm field|畑"], tags=["scene"])
N("h0102", "There is snow on the mountains", "山に雪がある", True, tags=["scene"])
TYPE("h0104", "painting", ["photo", "diagram", "satellite"])
Q("h0105", "What is shown on the screen?", "画面には何が表示されていますか？", "Source code|ソースコード",
  ["A map|地図", "A menu|メニュー", "A sales table|売上表"], tags=["classify", "object"], diff="medium")
TYPE("h0108", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0110", "What is the film title on the poster?", "ポスターの映画の題名は何ですか？", "Lawrence of Arabia|アラビアのロレンス",
  ["Ben-Hur|ベン・ハー", "Casablanca|カサブランカ", "Gladiator|グラディエーター"], tags=["ocr", "poster"])
Q("h0111", "With what kind of device was this picture taken?", "この画像は何を使って撮影されましたか？", "A microscope|顕微鏡",
  ["A telescope|望遠鏡", "A satellite|人工衛星", "A drone|ドローン"], tags=["image-type"], diff="medium")
colour("h0112", "the liquid in the jar", "瓶の中の液体", "yellow", ["red", "blue", "white"], tags=("colour", "attribute"))
Q("h0113", "What kind of building is the tall one in the centre?", "中央の高い建物はどんな建物ですか？", "A skyscraper|超高層ビル",
  ["A castle|城", "A barn|納屋", "A church|教会"], tags=["classify", "structure"])
S("h0116", "ship", "vehicle")
N("h0116", "Smoke or fire is visible", "煙または炎が見える", True)
TYPE("h0118", "diagram", ["photo", "painting", "satellite"], diff="medium")
Q("h0119", "What is shown?", "何が写っていますか？", "A circuit board|電子回路基板",
  ["A map|地図", "A carpet|絨毯", "A keyboard|キーボード"], tags=["classify", "object"])
TYPE("h0120", "map", ["photo", "painting", "satellite"])
TYPE("h0122", "drawing", ["photo", "satellite", "map"], diff="medium")
Q("h0123", "Which animals are shown in the painting?", "絵に描かれている動物はどれですか？", "Monkeys|サル",
  ["Dogs|犬", "Horses|馬", "Cats|猫"], tags=["classify", "animal"])
TYPE("h0124", "satellite", ["photo", "painting", "diagram"], diff="medium")
Q("h0125", "Which food is mainly shown?", "主に写っている食べ物はどれですか？", "Bread and grains|パンと穀物",
  ["Fish|魚", "Fruit|果物", "Meat|肉"], tags=["classify", "food"])
Q("h0126", "What kind of device produced this image?", "この画像は何の装置で撮影されましたか？", "An electron microscope|電子顕微鏡",
  ["A phone camera|携帯電話のカメラ", "A telescope|望遠鏡", "A satellite|人工衛星"], tags=["image-type"], diff="hard")
Q("h0127", "What is shown?", "何が写っていますか？", "A spacecraft in orbit|軌道上の宇宙船",
  ["An airplane|飛行機", "A ship|船", "A train|電車"], tags=["classify", "vehicle"])
Q("h0128", "What is the object made of?", "この物は何でできていますか？", "Clay|粘土",
  ["Metal|金属", "Paper|紙", "Glass|ガラス"], tags=["classify", "object"], diff="medium")
N("h0129", "People are sitting in a circle", "人々が輪になって座っている", True, tags=["scene"])
Q("h0130", "What activity produces the sparks?", "火花を出しているのは何の作業ですか？", "Welding|溶接",
  ["Baking|パン焼き", "Painting|塗装", "Sewing|裁縫"], tags=["action"])
Q("h0131", "What is the winding feature in the landscape?", "景色の中の曲がりくねったものは何ですか？", "A river|川",
  ["A road|道路", "A railway|鉄道", "A fence|柵"], tags=["scene"], diff="medium")
TYPE("h0132", "satellite", ["photo", "painting", "map"], diff="medium")
TYPE("h0133", "painting", ["photo", "diagram", "satellite"])
TYPE("h0137", "diagram", ["photo", "painting", "satellite"], diff="medium")
Q("h0139", "Which two lines are labelled on the map?", "地図に名前が書かれている 2 本の線はどれですか？", "Equator and Prime Meridian|赤道と本初子午線",
  ["Arctic Circle and Tropic of Cancer|北極圏と北回帰線", "Date Line and Tropic of Capricorn|日付変更線と南回帰線",
   "Equator and Date Line|赤道と日付変更線"], tags=["ocr", "diagram"], diff="hard")
Q("h0142", "In which language is the title page written?", "この表紙はどの言語で書かれていますか？", "French|フランス語",
  ["English|英語", "Russian|ロシア語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
TYPE("h0144", "painting", ["photo", "diagram", "satellite"])
N("h0146", "There are palm trees in the picture", "写真にヤシの木がある", True, tags=["scene"], diff="medium")
Q("h0147", "In which language is the title page written?", "この表紙はどの言語で書かれていますか？", "German|ドイツ語",
  ["English|英語", "French|フランス語", "Japanese|日本語"], tags=["ocr", "language"], diff="medium")
Q("h0148", "What kind of writing is carved on the wall?", "壁に彫られている文字はどれですか？", "Hieroglyphs|ヒエログリフ",
  ["Latin letters|ラテン文字", "Chinese characters|漢字", "Arabic script|アラビア文字"], tags=["ocr", "script"])
TYPE("h0149", "space", ["photo", "painting", "map"], diff="medium")
TYPE("h0150", "satellite", ["photo", "painting", "diagram"], diff="medium")
TYPE("h0151", "painting", ["photo", "diagram", "satellite"], diff="medium")
Q("h0153", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Das Kapital|資本論",
  ["Moby-Dick|白鯨", "Hamlet|ハムレット", "Faust|ファウスト"], tags=["ocr", "book"], diff="medium")
N("h0154", "The photograph is in colour", "この写真はカラーである", False, tags=["attribute"])
TYPE("h0155", "satellite", ["photo", "painting", "map"], diff="medium")
TYPE("h0156", "satellite", ["photo", "painting", "diagram"], diff="medium")
TYPE("h0157", "drawing", ["photo", "satellite", "map"], diff="medium")
TYPE("h0158", "space", ["photo", "painting", "map"], diff="medium")
TYPE("h0159", "map", ["photo", "painting", "satellite"])
