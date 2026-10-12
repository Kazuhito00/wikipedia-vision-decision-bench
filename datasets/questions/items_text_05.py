# -*- coding: utf-8 -*-
"""Text items 05: artists, writers, composers, scientists (articles 32-40)."""
from dsl import tchoice, tnoul

# ---- Leonardo da Vinci
tchoice("Leonardo da Vinci", "Leonardo da Vinci was an artist of which period?", "The Renaissance",
        ["The Baroque", "The Romantic era", "The Middle Ages"],
        "レオナルド・ダ・ヴィンチはどの時代を代表する芸術家ですか？", "ルネサンス期", ["バロック期", "ロマン主義の時代", "中世"],
        [], [], tags=["person-fact"])
tnoul("Leonardo da Vinci", "Leonardo da Vinci was Italian.", "レオナルド・ダ・ヴィンチはイタリア出身である。", True,
      [], [], tags=["person-fact"])
# ---- William Shakespeare
tchoice("William Shakespeare", "What was William Shakespeare's main occupation?", "Playwright and poet",
        ["Painter", "Architect", "Physicist"],
        "ウィリアム・シェイクスピアの主な職業は何でしたか？", "劇作家・詩人", ["画家", "建築家", "物理学者"],
        [], [], tags=["person-fact"])
tnoul("William Shakespeare", "William Shakespeare was born in 1564.", "ウィリアム・シェイクスピアは 1564 年に生まれた。", True,
      [], [], tags=["date"])
# ---- Natsume Sōseki
tchoice("Natsume Sōseki", "Which of these is a major work of Natsume Sōseki?", "I Am a Cat",
        ["The Tale of Genji", "Snow Country", "The Makioka Sisters"],
        "次のうち、夏目漱石の代表作はどれですか？", "吾輩は猫である", ["源氏物語", "雪国", "細雪"],
        [], [], tags=["work"])
tnoul("Natsume Sōseki", "Natsume Sōseki wrote Botchan.", "夏目漱石は『坊っちゃん』を書いた。", True,
      [], [], tags=["work"])
# ---- Beethoven
tchoice("Ludwig van Beethoven", "What was Ludwig van Beethoven's profession?", "Composer",
        ["Painter", "Explorer", "Chemist"],
        "ルートヴィヒ・ヴァン・ベートーヴェンの職業は何でしたか？", "作曲家", ["画家", "探検家", "化学者"],
        [], [], tags=["person-fact"])
tnoul("Ludwig van Beethoven", "Beethoven was a Spanish painter.", "ベートーヴェンはスペインの画家だった。", False,
      [], [], absent_en=["Spanish painter"], absent_ja=["スペインの画家"], tags=["person-fact"])
# ---- Mozart
tchoice("Wolfgang Amadeus Mozart", "Mozart is a composer of which period?", "The Classical period",
        ["The Baroque period", "The Romantic period", "The modern period"],
        "モーツァルトはどの時代を代表する作曲家ですか？", "古典派", ["バロック", "ロマン派", "現代音楽"],
        [], [], tags=["person-fact"])
tnoul("Wolfgang Amadeus Mozart", "Mozart lived from 1756 to 1791.", "モーツァルトは 1756 年から 1791 年まで生きた。", True,
      [], [], tags=["date"])
# ---- Hokusai
tchoice("Hokusai", "Which print by Hokusai is the most iconic one mentioned?", "The Great Wave off Kanagawa",
        ["The Starry Night", "The Scream", "Girl with a Pearl Earring"],
        "（ヒント：浮世絵師の代表作）北斎の時代区分はどれですか？", "江戸時代", ["平安時代", "明治時代", "室町時代"],
        [], [], tags=["work"], diff="medium", only=None)
tnoul("Hokusai", "Hokusai was an ukiyo-e artist.", "葛飾北斎は浮世絵師だった。", True,
      [], [], tags=["person-fact"])
# ---- Florence Nightingale
tchoice("Florence Nightingale", "Florence Nightingale is known as the founder of what?", "Modern nursing",
        ["Modern aviation", "Modern banking", "Modern architecture"],
        "フローレンス・ナイチンゲールは何の母と呼ばれていますか？", "近代看護教育", ["近代航空", "近代銀行", "近代建築"],
        [], [], tags=["person-fact"])
tnoul("Florence Nightingale", "Florence Nightingale is called the Lady with the Lamp.", "ナイチンゲールは「ランプの貴婦人」と呼ばれた。", True,
      [], [], tags=["person-fact"])
# ---- Rosalind Franklin
tchoice("Rosalind Franklin", "Franklin's work was central to understanding the structure of which molecule?", "DNA",
        ["Water", "Salt", "Glucose"],
        "ロザリンド・フランクリンが構造解明に貢献した物質はどれですか？", "DNA", ["水", "食塩", "ブドウ糖"],
        [], [], tags=["concept"])
tnoul("Rosalind Franklin", "Rosalind Franklin was a chemist.", "ロザリンド・フランクリンは化学者だった。", True,
      [], [], tags=["person-fact"])
# ---- Dmitri Mendeleev
tchoice("Dmitri Mendeleev", "What did Mendeleev create a version of?", "The periodic table of elements",
        ["The map of the stars", "The globe", "The alphabet"],
        "メンデレーエフが作成したものはどれですか？", "元素周期表", ["星座表", "地球儀", "アルファベット"],
        [], [], tags=["concept"])
tnoul("Dmitri Mendeleev", "Mendeleev was a Russian chemist.", "メンデレーエフはロシアの化学者だった。", True,
      [], [], tags=["person-fact"])
