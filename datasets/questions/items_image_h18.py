# -*- coding: utf-8 -*-
"""Image items, h0801-h0860 (pictures used by the Japanese article only), written for a somewhat demanding set:
look-alike distractors, artist / work / place identification, printed words, counts.
War and nuclear photographs, crowds, anatomy, nudity, portraits of private people and religious parody were left out."""
from templates import Q, N, TYPE, S, colour

Q("h0801", "Which animal is shown?", "どの動物が写っていますか？", "A weevil (a beetle)|ゾウムシ",
  ["A spider|クモ", "A bee|ミツバチ", "A tick|マダニ"], tags=["classify", "animal"], diff="hard")
Q("h0803", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Pieter Bruegel the Elder|ピーテル・ブリューゲル（父）",
  ["Rembrandt|レンブラント", "Vermeer|フェルメール", "Hieronymus Bosch|ヒエロニムス・ボス"], tags=["art"], diff="hard")
Q("h0804", "Which Japanese artist made this print?", "この版画を作った日本の絵師は誰ですか？", "Hokusai|葛飾北斎",
  ["Hiroshige|歌川広重", "Utamaro|喜多川歌麿", "Kuniyoshi|歌川国芳"], tags=["art"], diff="hard")
Q("h0809", "Which island lies off the coast of China on this map?", "この地図で中国の沿岸の沖にある島はどれですか？", "Taiwan|台湾",
  ["Hainan|海南島", "Japan|日本", "Sri Lanka|スリランカ"], tags=["ocr", "map"], diff="medium")
Q("h0812", "Which animals carry the travellers?", "旅人たちを運んでいる動物はどれですか？", "Camels|ラクダ",
  ["Horses|馬", "Elephants|ゾウ", "Donkeys|ロバ"], tags=["classify", "animal"], diff="medium")
Q("h0814", "What is the title printed on this book?", "この本に印刷されている題名は何ですか？", "Wuthering Heights|嵐が丘",
  ["Jane Eyre|ジェーン・エア", "Emma|エマ", "Middlemarch|ミドルマーチ"], tags=["ocr", "book"], diff="medium")
Q("h0816", "Which famous painting is this?", "これはどの有名な絵画ですか？", "Black Square|黒の正方形",
  ["The Scream|叫び", "The Starry Night|星月夜", "Guernica|ゲルニカ"], tags=["art"], diff="hard")
Q("h0817", "What is happening in the picture?", "絵では何が行われていますか？", "A lecture to students|学生への講義",
  ["A battle|戦い", "A harvest|収穫", "A feast|宴会"], tags=["scene"], diff="medium")
Q("h0818", "Which mountain range is shown?", "写っている山脈はどれですか？", "The Pyrenees|ピレネー山脈",
  ["The Alps|アルプス山脈", "The Urals|ウラル山脈", "The Andes|アンデス山脈"], tags=["geo"], diff="hard")
Q("h0819", "Which monument is this?", "これはどの遺跡ですか？", "Abu Simbel|アブ・シンベル神殿",
  ["The Parthenon|パルテノン神殿", "The Taj Mahal|タージ・マハル", "Angkor Wat|アンコール・ワット"], tags=["classify", "structure"], diff="hard")
Q("h0820", "Which country is highlighted in dark green?", "濃い緑で強調されている国はどれですか？", "China|中国",
  ["Japan|日本", "India|インド", "Russia|ロシア"], tags=["geo", "map"], diff="medium")
Q("h0821", "What natural feature is this?", "これはどんな自然の地形ですか？", "A slot canyon with a beam of light|光の筋が差し込むスロットキャニオン",
  ["A cave with a waterfall|滝のある洞窟", "A glacier|氷河", "A railway tunnel|鉄道トンネル"], tags=["scene"], diff="hard")
Q("h0823", "What is shown close up?", "接写されているものは何ですか？", "A leaf with visible veins|葉脈の見える葉",
  ["A feather|羽根", "A fish fin|魚のひれ", "A bat wing|コウモリの翼"], tags=["classify", "object"], diff="medium")
Q("h0824", "Which currency is shown?", "写っているのはどの通貨ですか？", "US dollars|米ドル",
  ["Japanese yen|日本円", "Euros|ユーロ", "British pounds|英ポンド"], tags=["classify", "object"], diff="medium")
Q("h0826", "Which animal is illustrated?", "どの動物が描かれていますか？", "A caecilian (a limbless amphibian)|アシナシイモリ（足のない両生類）",
  ["A snake|ヘビ", "An earthworm|ミミズ", "An eel|ウナギ"], tags=["classify", "animal"], diff="hard")
Q("h0827", "How many jets are in the formation?", "編隊の飛行機は何機ですか？", "Four|4 機", ["Three|3 機", "Five|5 機", "Two|2 機"], tags=["count"], diff="medium")
Q("h0828", "Which stage is labelled at the left end of the diagram?", "図の左端に書かれている段階はどれですか？", "Inflation|インフレーション",
  ["The Dark Ages|暗黒時代", "Reionization|再電離", "The Big Crunch|ビッグクランチ"], tags=["ocr", "diagram"], diff="hard")
Q("h0833", "What are the white branching shapes?", "白い枝分かれした形は何ですか？", "Frost crystals|霜の結晶",
  ["Tree roots|木の根", "Coral|サンゴ", "Cotton threads|綿糸"], tags=["classify", "object"], diff="hard")
Q("h0834", "How many helmets are on the table?", "テーブルの上のヘルメットはいくつですか？", "Five|5 つ", ["Three|3 つ", "Four|4 つ", "Six|6 つ"], tags=["count"], diff="medium")
Q("h0835", "Which kind of drink do the bottles contain?", "瓶に入っているのはどんな酒ですか？", "Tequila|テキーラ",
  ["Sake|日本酒", "Beer|ビール", "Wine|ワイン"], tags=["classify", "food"], diff="hard")
Q("h0838", "Which lake is shown in this satellite image?", "この衛星画像に写っている湖はどれですか？", "Lake Superior|スペリオル湖",
  ["Lake Baikal|バイカル湖", "Lake Victoria|ヴィクトリア湖", "Lake Biwa|琵琶湖"], tags=["geo"], diff="hard")
Q("h0842", "Which museum has this skylight above its spiral rotunda?", "らせん状の吹き抜けの上にこの天窓があるのはどの美術館ですか？",
  "The Guggenheim Museum, New York|グッゲンハイム美術館（ニューヨーク）",
  ["The Louvre|ルーブル美術館", "Tate Modern|テート・モダン", "The British Museum|大英博物館"], tags=["classify", "structure"], diff="hard")
Q("h0843", "Which crop is being held?", "手に持っている作物はどれですか？", "Sorghum|モロコシ（ソルガム）",
  ["Rice|稲", "Wheat|小麦", "Soybeans|大豆"], tags=["classify", "plant"], diff="hard")
Q("h0845", "What kind of landscape is this?", "これはどんな景色ですか？", "A grassland steppe|草原",
  ["A desert|砂漠", "A snowfield|雪原", "A rainforest|熱帯雨林"], tags=["scene"], diff="medium")
N("h0845", "A person is standing in the distance", "遠くに人が立っている", True, tags=["presence"], diff="medium")
Q("h0847", "Which mountain is this?", "これはどの山ですか？", "Mount Fuji|富士山",
  ["Mount Aso|阿蘇山", "Kilimanjaro|キリマンジャロ", "Mount Rainier|レーニア山"], tags=["geo"], diff="medium")
Q("h0849", "What is the table made of?", "テーブルは何でできていますか？", "Wood|木", ["Glass|ガラス", "Metal|金属", "Plastic|プラスチック"], tags=["classify", "object"], diff="medium")
Q("h0850", "What is rising from the volcano?", "火山から立ちのぼっているものは何ですか？", "An ash cloud|火山灰の雲",
  ["Smoke from a factory|工場の煙", "A swarm of locusts|イナゴの群れ", "Morning fog|朝霧"], tags=["scene"], diff="medium")
Q("h0854", "What is launching?", "打ち上げられているのは何ですか？", "The Space Shuttle|スペースシャトル",
  ["A Soyuz rocket|ソユーズロケット", "An airliner|旅客機", "A missile|ミサイル"], tags=["classify", "vehicle"], diff="hard")
Q("h0855", "What shape is the artificial island?", "人工島はどんな形をしていますか？", "A palm tree|ヤシの木",
  ["A star|星", "A heart|ハート", "A circle|円"], tags=["shape"], diff="medium")
Q("h0857", "Which birds are shown?", "どの鳥が写っていますか？", "Boobies (seabirds)|カツオドリの仲間",
  ["Penguins|ペンギン", "Swans|白鳥", "Owls|フクロウ"], tags=["classify", "animal"], diff="hard")
Q("h0858", "Which bird is shown?", "どの鳥が写っていますか？", "An American robin|コマツグミ（ロビン）",
  ["A blue jay|アオカケス", "An owl|フクロウ", "A pigeon|ハト"], tags=["classify", "animal"], diff="hard")
N("h0858", "The bird has an orange-red breast", "鳥の胸はオレンジがかった赤色である", True, tags=["attribute"])
