# -*- coding: utf-8 -*-
"""Expansion set, field "sci": x0161-x0177 (seismograph drum, lenses, magnets)."""
from templates import Q, N, TYPE

Q("x0161", "What is wrapped around the drum?", "ドラムに巻き付けられているものは何ですか？", "Recording paper|記録紙", ["A blanket|毛布", "A flag|旗", "A towel|タオル"],
  tags=["detail", "sci"], diff="hard")
Q("x0162", "What colour are the beams of light?", "光線は何色ですか？", "Green|緑", ["Red|赤", "Blue|青", "Yellow|黄色"], tags=["colour", "sci"], diff="easy")
N("x0162", "A hand holds the lens in the upper beam", "上の光線の中でレンズを手で持っている", True, tags=["detail", "sci"], diff="medium")
Q("x0166", "What shape is the glowing object?", "光っている物体はどんな形ですか？", "A lens shape, a pointed oval|レンズの形（先のとがった楕円）",
  ["A star|星形", "A square|正方形", "A cross|十字"], tags=["detail", "sci"], diff="medium")
Q("x0167", "What instrument is the person using at the desk?", "机で人物が使っている器具は何ですか？", "A microscope|顕微鏡", ["A typewriter|タイプライター", "A sewing machine|ミシン", "A telephone|電話機"],
  tags=["action", "sci"], diff="medium")
Q("x0170", "What kind of object is this?", "これはどんなものですか？", "A page from a medieval manuscript|中世の写本のページ",
  ["A modern newspaper|現代の新聞", "A road sign|道路標識", "A food label|食品のラベル"], tags=["image-type", "record", "sci"], diff="medium")
Q("x0171", "What do the curved lines around the central sphere show?", "中心の球の周りの曲線は何を表していますか？", "Magnetic field lines|磁力線",
  ["Roads|道路", "Wind currents of a storm|嵐の風の流れ", "Tree rings|年輪"], tags=["detail", "sci"], diff="hard")
Q("x0176", "What colour is the triangle at the upper right?", "右上の三角形は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Yellow|黄色"], tags=["colour", "sci"], diff="medium")
Q("x0177", "What sticks to the magnet in large numbers?", "磁石にたくさんくっついているものは何ですか？", "Metal washers|金属のワッシャー", ["Coins|硬貨", "Buttons|ボタン", "Pebbles|小石"],
  tags=["classify", "object", "sci"], diff="medium")
N("x0177", "The objects on the magnet are made of plastic", "磁石にくっついているものはプラスチックでできている", False, tags=["attribute", "sci"], diff="medium")
