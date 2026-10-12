# -*- coding: utf-8 -*-
"""Bilingual templates for the image questions. Each helper adds one item through dsl.* ; the answers are
whatever the author saw in the picture (nothing here derives a label automatically)."""
from dsl import ichoice, inoul, iscore

NOUN = {  # key: (en, ja)    -- used for animals, vehicles, buildings, foods, objects, scenes
    # animals
    "cat": ("cat", "猫"), "dog": ("dog", "犬"), "horse": ("horse", "馬"), "cow": ("cow", "牛"), "sheep": ("sheep", "羊"),
    "goat": ("goat", "ヤギ"), "pig": ("pig", "豚"), "chicken": ("chicken", "ニワトリ"), "duck": ("duck", "アヒル"),
    "swan": ("swan", "白鳥"), "eagle": ("eagle", "ワシ"), "owl": ("owl", "フクロウ"), "parrot": ("parrot", "オウム"),
    "penguin": ("penguin", "ペンギン"), "elephant": ("elephant", "ゾウ"), "giraffe": ("giraffe", "キリン"),
    "lion": ("lion", "ライオン"), "tiger": ("tiger", "トラ"), "bear": ("bear", "クマ"), "monkey": ("monkey", "サル"),
    "zebra": ("zebra", "シマウマ"), "deer": ("deer", "シカ"), "rabbit": ("rabbit", "ウサギ"), "fox": ("fox", "キツネ"),
    "wolf": ("wolf", "オオカミ"), "butterfly": ("butterfly", "チョウ"), "bee": ("bee", "ミツバチ"), "frog": ("frog", "カエル"),
    "snake": ("snake", "ヘビ"), "turtle": ("turtle", "カメ"), "fish": ("fish", "魚"), "shark": ("shark", "サメ"),
    "bird": ("bird", "鳥"), "jellyfish": ("jellyfish", "クラゲ"), "dolphin": ("dolphin", "イルカ"), "whale": ("whale", "クジラ"),
    "camel": ("camel", "ラクダ"), "squirrel": ("squirrel", "リス"), "crab": ("crab", "カニ"), "spider": ("spider", "クモ"),
    # vehicles
    "airplane": ("airplane", "飛行機"), "helicopter": ("helicopter", "ヘリコプター"), "ship": ("ship", "船"),
    "sailboat": ("sailboat", "ヨット"), "train": ("train", "電車"), "tram": ("tram", "路面電車"), "bus": ("bus", "バス"),
    "truck": ("truck", "トラック"), "car": ("car", "自動車"), "bicycle": ("bicycle", "自転車"),
    "motorcycle": ("motorcycle", "オートバイ"), "tractor": ("tractor", "トラクター"), "ambulance": ("ambulance", "救急車"),
    "firetruck": ("fire engine", "消防車"), "rocket": ("rocket", "ロケット"),
    # structures / places
    "bridge": ("bridge", "橋"), "lighthouse": ("lighthouse", "灯台"), "castle": ("castle", "城"), "church": ("church", "教会"),
    "windmill": ("windmill", "風車"), "tower": ("tower", "塔"), "pyramid": ("pyramid", "ピラミッド"),
    "skyscraper": ("skyscraper", "高層ビル"), "dam": ("dam", "ダム"), "temple": ("temple", "寺院"),
    "stadium": ("stadium", "スタジアム"), "house": ("house", "住宅"), "barn": ("barn", "納屋"),
    # nature scenes
    "mountain": ("mountain", "山"), "beach": ("beach", "ビーチ"), "forest": ("forest", "森"), "desert": ("desert", "砂漠"),
    "waterfall": ("waterfall", "滝"), "river": ("river", "川"), "lake": ("lake", "湖"), "snow": ("snowy landscape", "雪景色"),
    "sunset": ("sunset", "夕焼け"), "volcano": ("volcano", "火山"), "field": ("farm field", "畑"), "island": ("island", "島"),
    "city": ("city street", "市街地の通り"), "sea": ("open sea", "海"), "meadow": ("meadow", "草原"), "cave": ("cave", "洞窟"),
    # food
    "pizza": ("pizza", "ピザ"), "bread": ("bread", "パン"), "cake": ("cake", "ケーキ"), "apple": ("apples", "りんご"),
    "banana": ("bananas", "バナナ"), "orange": ("oranges", "オレンジ"), "tomato": ("tomatoes", "トマト"),
    "grapes": ("grapes", "ぶどう"), "soup": ("soup", "スープ"), "egg": ("eggs", "卵"), "cheese": ("cheese", "チーズ"),
    "sushi": ("sushi", "寿司"), "salad": ("salad", "サラダ"), "coffee": ("coffee", "コーヒー"), "burger": ("hamburger", "ハンバーガー"),
    "rice": ("rice", "ご飯"), "pasta": ("pasta", "パスタ"), "cookie": ("cookies", "クッキー"), "pie": ("pie", "パイ"),
    # objects
    "clock": ("clock", "時計"), "chair": ("chair", "椅子"), "guitar": ("guitar", "ギター"), "piano": ("piano", "ピアノ"),
    "book": ("books", "本"), "laptop": ("laptop computer", "ノートパソコン"), "telescope": ("telescope", "望遠鏡"),
    "camera": ("camera", "カメラ"), "umbrella": ("umbrella", "傘"), "keyboard": ("computer keyboard", "キーボード"),
    "bottle": ("bottle", "瓶"), "lamp": ("lamp", "ランプ"), "key": ("key", "鍵"), "phone": ("telephone", "電話機"),
    "flower": ("flower", "花"), "tree": ("tree", "木"),
    # signs / documents
    "sign": ("road sign", "道路標識"), "chart": ("chart", "グラフ"), "map": ("map", "地図"), "poster": ("poster", "ポスター"),
}
COLOUR = {"red": ("red", "赤"), "blue": ("blue", "青"), "green": ("green", "緑"), "yellow": ("yellow", "黄色"),
          "purple": ("purple", "紫"), "white": ("white", "白"), "black": ("black", "黒"), "brown": ("brown", "茶色"),
          "grey": ("grey", "灰色"), "orange": ("orange", "オレンジ"), "pink": ("pink", "ピンク")}
COUNT = ["one", "two", "three", "four", "five"]
COUNT_JA = {"one": ("1", "つ"), "two": ("2", "つ"), "three": ("3", "つ"), "four": ("4", "つ"), "five": ("5", "つ")}
# counter words per noun for the Japanese question ("何匹", "何頭" ...) -- natural, and avoids "exactly N things"
UNIT = {"cat": "匹", "dog": "匹", "horse": "頭", "cow": "頭", "sheep": "頭", "goat": "頭", "tiger": "頭", "lion": "頭",
        "elephant": "頭", "giraffe": "頭", "zebra": "頭", "deer": "頭", "bear": "頭", "rabbit": "匹", "bird": "羽",
        "duck": "羽", "swan": "羽", "eagle": "羽", "penguin": "羽", "chicken": "羽", "butterfly": "匹", "bee": "匹",
        "airplane": "機", "helicopter": "機", "ship": "隻", "sailboat": "隻", "train": "両", "bus": "台", "car": "台",
        "truck": "台", "bicycle": "台", "motorcycle": "台", "person": "人", "tree": "本", "umbrella": "本", "book": "冊",
        "flower": "輪", "clock": "個", "chair": "脚", "house": "軒", "bridge": "本", "tower": "本", "boat": "隻"}


def _en(k):
    return NOUN[k][0]


def _ja(k):
    return NOUN[k][1]


def what(cid, right, wrong, q=("Which animal is mainly shown?", "主に写っている動物はどれですか？"), tags=("classify",),
         diff="easy", imgs=None):
    """4-way classification. right/wrong are NOUN keys."""
    return ichoice(imgs or cid, q[0], _en(right), [_en(w) for w in wrong], q[1], _ja(right), [_ja(w) for w in wrong],
                   tags=tags, diff=diff)


def animal(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, tags=("classify", "animal"), diff=diff)


def vehicle(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, q=("What kind of vehicle is this?", "これはどんな乗り物ですか？"), tags=("classify", "vehicle"), diff=diff)


def place(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, q=("What kind of place or scene is this?", "ここはどんな場所・景色ですか？"), tags=("classify", "scene"), diff=diff)


def structure(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, q=("What structure is this?", "これは何の構造物ですか？"), tags=("classify", "structure"), diff=diff)


def food(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, q=("Which food is shown?", "写っている食べ物はどれですか？"), tags=("classify", "food"), diff=diff)


def thing(cid, right, wrong, diff="easy"):
    return what(cid, right, wrong, q=("What is the main object?", "主な被写体は何ですか？"), tags=("classify", "object"), diff=diff)


def colour(cid, what_en, what_ja, right, wrong, diff="easy", tags=("colour",)):
    """What colour is <what>?  right/wrong are COLOUR keys."""
    verb = "are" if what_en.endswith(("eyes", "wings", "flowers")) else "is"
    return ichoice(cid, "What colour %s %s?" % (verb, what_en), COLOUR[right][0], [COLOUR[w][0] for w in wrong],
                   "%sは何色ですか？" % what_ja, COLOUR[right][1], [COLOUR[w][1] for w in wrong], tags=tags, diff=diff)


def count(cid, noun, n, diff="medium", where_en="", where_ja="", options=("one", "two", "three")):
    """How many <noun> are there?  n is the true count (1..5); options are the offered counts (3 or 4 of them)."""
    en_opts = [o for o in options]
    idx = COUNT.index
    ok = COUNT[n - 1]
    assert ok in en_opts, (cid, n, options)
    wrong = [o for o in en_opts if o != ok]
    unit = UNIT.get(noun, "つ")
    ja_ok = "%d%s" % (n, unit)
    ja_wrong = ["%d%s" % (idx(o) + 1, unit) for o in wrong]
    q_en = "How many %s are there%s?" % (_en(noun) if _en(noun).endswith("s") else _en(noun) + "s", where_en)
    q_ja = "%s%sは何%sいますか？" % (where_ja, _ja(noun), unit) if noun in ("cat", "dog", "horse", "cow", "sheep", "goat", "tiger",
            "lion", "elephant", "giraffe", "zebra", "deer", "bear", "rabbit", "bird", "duck", "swan", "eagle", "penguin",
            "chicken", "butterfly", "bee") else "%s%sは何%sありますか？" % (where_ja, _ja(noun), unit)
    return ichoice(cid, q_en, ok, wrong, q_ja, ja_ok, ja_wrong, tags=("count",), diff=diff)


def present(cid, noun_en, noun_ja, answer, tags=("presence",), diff="easy"):
    """noul: 'There is <noun> in the picture' (answer True/False)."""
    return inoul(cid, "There is %s in the picture" % noun_en, "写真に%sが写っている" % noun_ja, answer, tags=tags, diff=diff)


def claim(cid, en_stmt, ja_stmt, answer, tags=("presence",), diff="easy"):
    return inoul(cid, en_stmt, ja_stmt, answer, tags=tags, diff=diff)


def score3(cid, en_q, ja_q, en_levels, ja_levels, answer, tags=("score",), diff="medium"):
    return iscore(cid, en_q, en_levels, ja_q, ja_levels, answer, tags=tags, diff=diff)


# ---------------------------------------------------------------------------------------------------
# Bulk helper: the author names WHAT the picture shows (looked at, not derived); the three wrong options are
# drawn with a fixed seed from the same domain, skipping look-alikes (a tiger is never offered next to a lion).
import hashlib
import random

DOMAIN = {
    "animal": ["cat", "dog", "horse", "cow", "sheep", "goat", "pig", "chicken", "duck", "swan", "eagle", "owl", "parrot",
               "penguin", "elephant", "giraffe", "lion", "tiger", "bear", "monkey", "zebra", "deer", "rabbit", "fox",
               "wolf", "butterfly", "bee", "frog", "snake", "turtle", "fish", "shark", "jellyfish", "dolphin", "whale",
               "camel", "squirrel", "crab", "spider", "bird"],
    "vehicle": ["airplane", "helicopter", "ship", "sailboat", "train", "tram", "bus", "truck", "car", "bicycle",
                "motorcycle", "tractor", "ambulance", "firetruck", "rocket"],
    "structure": ["bridge", "lighthouse", "castle", "church", "windmill", "tower", "pyramid", "skyscraper", "dam", "temple",
                  "stadium", "house", "barn"],
    "scene": ["mountain", "beach", "forest", "desert", "waterfall", "river", "lake", "snow", "sunset", "volcano", "field",
              "island", "city", "sea", "meadow", "cave"],
    "food": ["pizza", "bread", "cake", "apple", "banana", "orange", "tomato", "grapes", "soup", "egg", "cheese", "sushi",
             "salad", "coffee", "burger", "rice", "pasta", "cookie", "pie"],
    "object": ["clock", "chair", "guitar", "piano", "book", "laptop", "telescope", "camera", "umbrella", "keyboard",
               "bottle", "lamp", "key", "phone"],
}
LOOKALIKE = [{"cat", "tiger", "lion", "fox"}, {"dog", "wolf", "fox"}, {"bird", "eagle", "owl", "duck", "swan", "parrot",
             "penguin", "chicken"}, {"horse", "zebra", "deer"}, {"cow", "sheep", "goat", "deer", "pig"}, {"whale", "dolphin", "shark", "fish"},
             {"car", "bus", "truck", "ambulance", "firetruck"}, {"ship", "sailboat"}, {"airplane", "helicopter", "rocket"},
             {"train", "tram"}, {"bicycle", "motorcycle"}, {"castle", "tower", "church", "temple"}, {"lake", "sea", "river", "beach"},
             {"mountain", "volcano"}, {"bread", "cake", "cookie", "pie"}, {"orange", "apple", "tomato"}, {"house", "barn"}]
QUESTION = {
    "animal": ("Which animal is mainly shown?", "主に写っている動物はどれですか？"),
    "vehicle": ("What kind of vehicle is this?", "これはどんな乗り物ですか？"),
    "structure": ("What kind of building or structure is this?", "これはどんな建物・構造物ですか？"),
    "scene": ("What kind of place or scenery is this?", "ここはどんな場所・景色ですか？"),
    "food": ("Which food is shown?", "写っている食べ物はどれですか？"),
    "object": ("What is the main object?", "主な被写体は何ですか？"),
}


def _pick_wrong(cid, right, domain, extra=()):
    rng = random.Random(int(hashlib.sha1((cid + right).encode()).hexdigest()[:10], 16))
    pool = [k for k in DOMAIN[domain] if k != right]
    for grp in LOOKALIKE:
        if right in grp:
            pool = [k for k in pool if k not in grp]
    for k in extra:                                  # author-specified exclusions
        pool = [p for p in pool if p != k]
    return rng.sample(pool, 3)


def S(cid, right, domain, diff="easy", wrong=None, tags=()):
    """The picture shows `right` (a NOUN key). Domain picks the question wording and the distractor pool."""
    wrong = wrong or _pick_wrong(cid, right, domain)
    q = QUESTION[domain]
    return what(cid, right, wrong, q=q, tags=("classify", domain) + tuple(tags), diff=diff)


# ---------------------------------------------------------------------------------------------------
# Free-form helpers for the Wikipedia pictures: options are written once as "english|日本語" (or a single string
# when the words are the same in both languages, e.g. text that is printed in the picture).
def _pair(x):
    en, _, ja = x.partition("|")
    return en.strip(), (ja.strip() or en.strip())


def Q(cid, en_q, ja_q, right, wrong, tags=(), diff="medium"):
    """Multiple choice. right / wrong items: 'english|日本語'."""
    r_en, r_ja = _pair(right)
    w = [_pair(x) for x in wrong]
    return ichoice(cid, en_q, r_en, [a for a, _ in w], ja_q, r_ja, [b for _, b in w], tags=tuple(tags), diff=diff)


def N(cid, en_stmt, ja_stmt, answer, tags=("presence",), diff="easy"):
    """Yes/no statement about the picture."""
    return inoul(cid, en_stmt, ja_stmt, answer, tags=tags, diff=diff)


KIND = {"photo": "a photograph|写真", "painting": "a painting|絵画", "diagram": "a diagram or chart|図・グラフ",
        "satellite": "a satellite image|衛星画像", "map": "a map|地図", "page": "a page of a book|本の紙面",
        "drawing": "a drawing or illustration|線画・イラスト", "space": "an astronomical image|天体画像"}


def TYPE(cid, right, others, diff="easy"):
    """What kind of image is this?  right/others are KIND keys."""
    return Q(cid, "What kind of image is this?", "これはどんな種類の画像ですか？", KIND[right], [KIND[o] for o in others],
             tags=("image-type",), diff=diff)
