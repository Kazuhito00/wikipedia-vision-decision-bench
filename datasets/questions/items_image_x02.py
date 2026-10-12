# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0021-x0040 (laboratory glassware, oscilloscopes, circuit boards)."""
from templates import Q, N, TYPE

Q("x0021", "What is the main object on the bench?", "作業台の上の主な被写体は何ですか？", "A glass jar with a lid|蓋付きのガラス瓶",
  ["A teapot|急須", "A vase|花瓶", "A tin can|缶"], tags=["classify", "object", "sci"], diff="medium")
N("x0021", "The jar contains a red liquid", "瓶には赤い液体が入っている", False, tags=["attribute", "sci"], diff="medium")
Q("x0023", "What colour range is the liquid in the vial?", "小瓶の中の液体はどの色の範囲ですか？", "Red to orange|赤〜オレンジ",
  ["Blue|青", "Green|緑", "Colourless|無色"], tags=["colour", "sci"], diff="medium")
N("x0024", "The figure number printed below the drawing is 2", "図の下に印刷されている図番号は 2 である", True, tags=["ocr", "sci"], diff="hard")
Q("x0025", "What instrument is this control panel part of?", "この操作パネルはどの機器のものですか？", "An oscilloscope|オシロスコープ",
  ["A washing machine|洗濯機", "A car dashboard|車のダッシュボード", "A piano|ピアノ"], tags=["classify", "object", "sci"], diff="hard")
Q("x0025", "Which word is printed above the middle group of knobs?", "中央のつまみのグループの上に印刷されている語はどれですか？", "VERTICAL",
  ["HORIZONTAL", "TRIGGER", "VOLUME"], tags=["ocr", "sci"], diff="hard")
Q("x0026", "What waveform is displayed on the oscilloscope screen?", "オシロスコープの画面に表示されている波形は何ですか？", "A sine wave|正弦波",
  ["A square wave|矩形波", "A flat line|直線", "A sawtooth wave|のこぎり波"], tags=["detail", "sci"], diff="hard")
Q("x0028", "What is the device in the picture?", "写っている機器は何ですか？", "An oscilloscope|オシロスコープ",
  ["A microwave oven|電子レンジ", "A radio|ラジオ", "A television|テレビ"], tags=["classify", "object", "sci"], diff="medium")
Q("x0029", "What does the screen show?", "画面には何が表示されていますか？", "A jagged blue waveform|ぎざぎざした青い波形",
  ["A flat line|直線", "A circle|円", "A page of text|文章"], tags=["detail", "sci"], diff="medium")
N("x0029", "The instrument has an orange front frame", "この機器の前面の枠はオレンジ色である", True, tags=["attribute", "sci"], diff="medium")
N("x0030", "This oscilloscope shows its trace on a flat colour display rather than a round tube", "このオシロスコープは丸い管ではなく平らなカラー画面に波形を表示する", True,
  tags=["detail", "sci"], diff="hard")
Q("x0031", "What colour is the front panel of this older oscilloscope?", "この古いオシロスコープの前面パネルは何色ですか？", "Beige|ベージュ",
  ["Black|黒", "Red|赤", "Blue|青"], tags=["colour", "sci"], diff="medium")
Q("x0032", "What are the tall cabinets in the room?", "部屋にある背の高い箱は何ですか？", "Racks of electronic test equipment|電子計測機器のラック",
  ["Refrigerators|冷蔵庫", "Wardrobes|洋服だんす", "Bookshelves|本棚"], tags=["classify", "object", "sci"], diff="hard")
Q("x0033", "What is shown?", "何が写っていますか？", "A printed circuit board|プリント基板", ["A piece of fabric|布", "A keyboard|キーボード", "A map|地図"],
  tags=["classify", "object", "sci"])
Q("x0034", "What is inside the clear plastic case?", "透明なプラスチックケースの中には何がありますか？", "A circuit board with printed traces|配線パターンのある基板",
  ["A sandwich|サンドイッチ", "A wristwatch|腕時計", "Coins|硬貨"], tags=["classify", "object", "sci"], diff="medium")
N("x0035", "A cable is attached to the small circuit board", "小さな基板にケーブルが付いている", True, tags=["detail", "sci"])
Q("x0036", "What shape is the circuit-board badge?", "基板でできたバッジはどんな形ですか？", "A skull|ドクロ", ["A heart|ハート", "A star|星", "A cat|猫"],
  tags=["classify", "object", "sci"], diff="medium")
Q("x0037", "Which text is printed on the chip at the lower left of the board?", "基板の左下のチップに印刷されている文字はどれですか？", "ESMT",
  ["INTEL", "SONY", "AMD"], tags=["ocr", "sci"], diff="hard")
Q("x0039", "What stage of making a circuit board does this show?", "これは基板づくりのどの段階を示していますか？",
  "An etched board without components|部品のないエッチング済みの基板", ["A finished board with chips|チップが載った完成基板", "A blank sheet of paper|白紙", "A battery|電池"],
  tags=["detail", "sci"], diff="hard")
Q("x0040", "What is the main subject?", "主な被写体は何ですか？", "An integrated circuit chip on a circuit board|基板上の集積回路（IC）",
  ["A beetle|甲虫", "A cracker|クラッカー", "A postage stamp|切手"], tags=["classify", "object", "sci"], diff="medium")
N("x0040", "The chip has pins along its sides", "チップの側面にはピンが並んでいる", True, tags=["detail", "sci"])
