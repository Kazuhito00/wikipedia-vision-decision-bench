# -*- coding: utf-8 -*-
"""Text items 04: scientists and inventors (articles 23-31)."""
from dsl import tchoice, tnoul

# ---- Isaac Newton
tchoice("Isaac Newton", "Which country was Isaac Newton from?", "England", ["France", "Italy", "Spain"],
        "アイザック・ニュートンはどの国の人物ですか？", "イングランド", ["フランス", "イタリア", "スペイン"],
        [], [], tags=["person-fact"])
tnoul("Isaac Newton", "Newton helped establish classical mechanics.", "ニュートンは古典力学の確立に貢献した。", True,
      [], [], tags=["person-fact"])
# ---- Charles Darwin
tchoice("Charles Darwin", "What did Darwin call the process by which species evolve?", "Natural selection",
        ["Plate tectonics", "The Big Bang", "Germ theory"],
        "ダーウィンは、生物が進化する過程を何と呼びましたか？", "自然選択", ["プレートテクトニクス", "ビッグバン", "病原菌説"],
        [], [], tags=["concept"], diff="medium")
tnoul("Charles Darwin", "Charles Darwin was a composer.", "チャールズ・ダーウィンは作曲家だった。", False,
      [], [], absent_en=["composer"], absent_ja=["作曲家"], tags=["person-fact"])
# ---- Nikola Tesla
tchoice("Nikola Tesla", "What was Nikola Tesla's profession?", "Engineer and inventor", ["Painter", "Poet", "Chef"],
        "ニコラ・テスラの職業は何でしたか？", "発明家・電気技師", ["画家", "詩人", "料理人"],
        [], [], tags=["person-fact"])
tnoul("Nikola Tesla", "Tesla is known for his work on alternating current electricity.", "テスラは交流電気に関する業績で知られる。", True,
      [], [], tags=["person-fact"])
# ---- Alan Turing
tchoice("Alan Turing", "Which concept did Alan Turing formalise?", "The Turing machine",
        ["The steam engine", "The telegraph", "The printing press"],
        "アラン・チューリングが定式化した概念はどれですか？", "チューリングマシン", ["蒸気機関", "電信", "活版印刷"],
        [], [], tags=["concept"])
tnoul("Alan Turing", "Alan Turing is regarded as an important figure in computer science.", "アラン・チューリングは計算機科学の重要人物とされる。", True,
      [], [], tags=["person-fact"])
# ---- Ada Lovelace
tchoice("Ada Lovelace", "Whose proposed machine did Ada Lovelace write about?", "Charles Babbage's",
        ["Alan Turing's", "Isaac Newton's", "Thomas Edison's"],
        "エイダ・ラブレースはだれが考案した機械について書きましたか？", "チャールズ・バベッジ", ["アラン・チューリング", "アイザック・ニュートン", "トーマス・エジソン"],
        [], [], tags=["person-fact"], diff="medium")
tnoul("Ada Lovelace", "Ada Lovelace is often considered the first computer programmer.", "エイダ・ラブレースは世界初のプログラマーとされる。", True,
      [], [], tags=["person-fact"])
# ---- Galileo Galilei
tchoice("Galileo Galilei", "Galileo is often called the father of what?", "Modern science",
        ["Modern medicine", "The printing press", "Classical music"],
        "ガリレオは何の父と呼ばれていますか？", "近代科学", ["近代医学", "印刷術", "クラシック音楽"],
        [], [], tags=["person-fact"])
tnoul("Galileo Galilei", "Galileo was an Italian astronomer.", "ガリレオはイタリアの天文学者だった。", True,
      [], [], tags=["person-fact"])
# ---- Louis Pasteur
tchoice("Louis Pasteur", "Which process was named after Louis Pasteur?", "Pasteurization (low-temperature sterilisation)",
        ["Photosynthesis", "Evaporation", "Electrolysis"],
        "ルイ・パスツールの名前に由来する処理はどれですか？", "パスチャライゼーション（低温殺菌法）", ["光合成", "蒸発", "電気分解"],
        [], [], tags=["concept"], diff="medium")
tnoul("Louis Pasteur", "Pasteur developed a vaccine against rabies.", "パスツールは狂犬病ワクチンを開発した。", True,
      [], [], tags=["person-fact"])
# ---- Thomas Edison
tchoice("Thomas Edison", "Which invention is Thomas Edison known for?", "The incandescent light bulb",
        ["The telephone", "The steam locomotive", "The radio"],
        "トーマス・エジソンの発明として知られるものはどれですか？", "白熱電球", ["電話", "蒸気機関車", "ラジオ"],
        [], [], tags=["person-fact"])
tnoul("Thomas Edison", "Thomas Edison was an American inventor.", "トーマス・エジソンはアメリカの発明家だった。", True,
      [], [], tags=["person-fact"])
# ---- Wright brothers
tchoice("Wright brothers", "What are the Wright brothers credited with?", "Inventing the airplane",
        ["Inventing the telephone", "Inventing the radio", "Inventing the camera"],
        "ライト兄弟の功績として知られるものはどれですか？", "飛行機の発明", ["電話の発明", "ラジオの発明", "カメラの発明"],
        [], [], tags=["person-fact"])
tnoul("Wright brothers", "The Wright brothers were British.", "ライト兄弟はイギリス人だった。", False,
      [], [], absent_en=["British"], absent_ja=["イギリス人"], tags=["person-fact"])
