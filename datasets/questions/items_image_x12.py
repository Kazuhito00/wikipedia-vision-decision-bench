# -*- coding: utf-8 -*-
"""Expansion set, field "life": x0318-x0357 -- schools, playgrounds, crosswalks, an airport apron, vending machines, shopping
carts. Pictures with people as the subject (children, crowds, portraits) were not used."""
from templates import Q, N, TYPE

Q("x0320", "What colour is the roof of the school building?", "校舎の屋根は何色ですか？", "Red|赤", ["Blue|青", "Green|緑", "Black|黒"], tags=["colour", "life"], diff="easy")
Q("x0321", "What language is the text written in?", "文章は何語で書かれていますか？", "Arabic|アラビア語", ["Hebrew|ヘブライ語", "Thai|タイ語", "Korean|韓国語"],
  tags=["language", "ocr", "life"], diff="hard")
Q("x0322", "What covers the lower part of the wall?", "壁の下の部分を覆っているものは何ですか？", "A colourful mural|カラフルな壁画", ["Bricks|レンガ", "Ivy|つた", "Wooden planks|木の板"],
  tags=["detail", "life"], diff="medium")
Q("x0324", "What kind of place is this?", "ここはどんな場所ですか？", "A playground|遊び場", ["A tennis court|テニスコート", "A parking lot|駐車場", "A cemetery|墓地"],
  tags=["classify", "scene", "life"], diff="easy")
Q("x0324", "What colour are the posts of the climbing frame?", "遊具の柱は何色ですか？", "Orange|オレンジ", ["Blue|青", "Green|緑", "Purple|紫"], tags=["colour", "life"], diff="medium")
Q("x0326", "What lies in patches on the steps?", "階段にところどころ残っているものは何ですか？", "Snow|雪", ["Sand|砂", "Flower petals|花びら", "Fallen leaves|落ち葉"],
  tags=["detail", "scene", "life"], diff="medium")
N("x0330", "The steps are completely covered with snow", "階段は雪に完全に覆われている", False, tags=["detail", "scene", "life"], diff="medium")
N("x0327", "The playground has a slide", "遊び場には滑り台がある", True, tags=["presence", "life"])
Q("x0329", "What colour is the play structure?", "遊具は何色ですか？", "Green|緑", ["Red|赤", "Blue|青", "Yellow|黄色"], tags=["colour", "life"], diff="easy")
Q("x0332", "What are the white striped markings on the road?", "道路の白い縞模様は何ですか？", "A pedestrian crossing|横断歩道", ["A parking space|駐車枠", "A runway|滑走路", "A staircase|階段"],
  tags=["classify", "life"], diff="medium")
Q("x0333", "Which vehicle is on the street in the distance?", "通りの遠くにいる乗り物は何ですか？", "A tram|路面電車", ["A tractor|トラクター", "A train|列車", "A bus|バス"],
  tags=["classify", "vehicle", "life"], diff="medium")
N("x0338", "Snow lies beside the road", "道路のそばに雪が積もっている", True, tags=["scene", "life"])
Q("x0339", "What colour is the airplane?", "飛行機は何色ですか？", "Blue|青", ["Red|赤", "Green|緑", "Black|黒"], tags=["colour", "life"], diff="easy")
Q("x0342", "What kind of machine is this?", "これはどんな機械ですか？", "A vending machine|自動販売機", ["An ATM|ATM", "A washing machine|洗濯機", "A jukebox|ジュークボックス"],
  tags=["classify", "object", "life"], diff="medium")
Q("x0346", "How does the sign say you can pay?", "看板によると、どうやって支払えますか？", "With a text message|テキストメッセージで", ["With coins|硬貨で", "With a credit card|クレジットカードで", "With a paper ticket|紙の切符で"],
  tags=["ocr", "life"], diff="hard")
Q("x0348", "What price is written on the round sticker?", "丸いステッカーに書かれている値段はどれですか？", "99 cents|99 セント", ["9 cents|9 セント", "19 cents|19 セント", "99 dollars|99 ドル"],
  tags=["ocr", "life"], diff="hard")
Q("x0349", "What colour is the shopping cart?", "ショッピングカートは何色ですか？", "Blue|青", ["Red|赤", "Green|緑", "Yellow|黄色"], tags=["colour", "life"], diff="easy")
Q("x0350", "Which brand name is on the box in the cart?", "カートの中の箱に書かれているブランド名はどれですか？", "Coca-Cola (Coke)|コカ・コーラ", ["Pepsi|ペプシ", "Fanta|ファンタ", "Sprite|スプライト"],
  tags=["ocr", "life"], diff="medium")
Q("x0351", "What is the shopping cart being used as?", "ショッピングカートは何として使われていますか？", "A barbecue grill|バーベキューの網", ["A bed|ベッド", "A boat|ボート", "A bicycle|自転車"],
  tags=["detail", "life"], diff="hard")
N("x0351", "Meat is being grilled on the cart", "カートの上で肉が焼かれている", True, tags=["detail", "life"], diff="medium")
Q("x0352", "What colour are the carts lined up on the right?", "右に並んでいるカートは何色ですか？", "Yellow|黄色", ["Red|赤", "Blue|青", "Green|緑"], tags=["colour", "life"], diff="easy")
Q("x0355", "What colour is the basket?", "かごは何色ですか？", "Green|緑", ["Red|赤", "Blue|青", "Grey|灰色"], tags=["colour", "life"], diff="easy")
Q("x0357", "What aircraft is on display?", "展示されている航空機は何ですか？", "A helicopter|ヘリコプター", ["A glider|グライダー", "A rocket|ロケット", "A hot-air balloon|熱気球"],
  tags=["classify", "vehicle", "life"], diff="easy")
