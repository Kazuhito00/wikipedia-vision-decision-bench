# -*- coding: utf-8 -*-
"""Harder questions about pictures that were already looked at (art attribution, subject identification).
These replace the easy "what kind of image is this?" items that the difficulty policy removes. The answer for each is
fixed by the picture itself together with the Wikipedia article that uses it (the article is the work's own page)."""
from templates import Q, N

Q("h0004", "Which artist painted this fresco?", "このフレスコ画を描いた画家は誰ですか？", "Michelangelo|ミケランジェロ",
  ["Raphael|ラファエロ", "Botticelli|ボッティチェリ", "Caravaggio|カラヴァッジョ"], tags=["art"], diff="hard")
Q("h0013", "Which Shakespeare play does the painting illustrate?", "この絵はシェイクスピアのどの作品を描いていますか？", "Romeo and Juliet|ロミオとジュリエット",
  ["Hamlet|ハムレット", "Macbeth|マクベス", "Othello|オセロー"], tags=["art"], diff="hard")
Q("h0104", "Who painted this portrait?", "この肖像画を描いたのは誰ですか？", "Leonardo da Vinci|レオナルド・ダ・ヴィンチ",
  ["Rembrandt|レンブラント", "Vermeer|フェルメール", "Goya|ゴヤ"], tags=["art"], diff="medium")
Q("h0133", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Velázquez|ベラスケス",
  ["Rubens|ルーベンス", "Monet|モネ", "Dalí|ダリ"], tags=["art"], diff="hard")
Q("h0144", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Delacroix|ドラクロワ",
  ["Vermeer|フェルメール", "Manet|マネ", "Michelangelo|ミケランジェロ"], tags=["art"], diff="hard")
Q("h0174", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Botticelli|ボッティチェリ",
  ["Titian|ティツィアーノ", "Goya|ゴヤ", "Renoir|ルノワール"], tags=["art"], diff="hard")
Q("h0240", "Which Renaissance painter made this fresco?", "このフレスコ画を描いたルネサンスの画家は誰ですか？", "Raphael|ラファエロ",
  ["Rembrandt|レンブラント", "Monet|モネ", "Van Gogh|ゴッホ"], tags=["art"], diff="hard")
Q("h0249", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Van Gogh|ゴッホ", ["Monet|モネ", "Munch|ムンク", "Picasso|ピカソ"], tags=["art"], diff="medium")
Q("h0483", "Who painted this wall painting?", "この壁画を描いたのは誰ですか？", "Leonardo da Vinci|レオナルド・ダ・ヴィンチ",
  ["Michelangelo|ミケランジェロ", "Raphael|ラファエロ", "Titian|ティツィアーノ"], tags=["art"], diff="medium")
Q("h0199", "Who painted this picture?", "この絵を描いたのは誰ですか？", "Caravaggio|カラヴァッジョ", ["Monet|モネ", "Goya|ゴヤ", "Rembrandt|レンブラント"], tags=["art"], diff="hard")
Q("h0185", "Which artist made this woodblock print?", "この木版画を作ったのは誰ですか？", "Hokusai|葛飾北斎",
  ["Hiroshige|歌川広重", "Utamaro|喜多川歌麿", "Sharaku|東洲斎写楽"], tags=["art"], diff="hard")
Q("h0320", "Which artist made this woodblock print?", "この木版画を作ったのは誰ですか？", "Hokusai|葛飾北斎",
  ["Hiroshige|歌川広重", "Utamaro|喜多川歌麿", "Sharaku|東洲斎写楽"], tags=["art"], diff="hard")
Q("h0328", "Which historical retreat does the painting show?", "この絵が描いている歴史上の撤退はどれですか？", "Napoleon's retreat from Moscow|ナポレオンのモスクワ撤退",
  ["Hannibal's crossing of the Alps|ハンニバルのアルプス越え", "The Long March|長征", "The retreat from Kabul|カブールからの撤退"], tags=["art", "history"], diff="hard")
Q("h0074", "Which painting technique uses many small dots of colour, as in this picture?", "この絵のように小さな色の点を並べる技法はどれですか？", "Pointillism|点描",
  ["Cubism|キュビスム", "Woodblock printing|木版画", "Fresco|フレスコ"], tags=["art"], diff="hard")
