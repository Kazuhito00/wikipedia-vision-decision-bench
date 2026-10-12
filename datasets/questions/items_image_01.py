# -*- coding: utf-8 -*-
"""Image items 01: animals and a few vehicles/scenes from the first candidate batch (c0001-c0100).
Every answer was fixed by looking at the picture (contact sheet, then the picture itself when in doubt)."""
from templates import animal, vehicle, place, colour, count, present, claim, what

# c0001 kitten with blue eyes
animal("c0001", "cat", ["dog", "rabbit", "fox"])
colour("c0001", "the animal's eyes", "動物の目", "blue", ["green", "brown", "yellow"], tags=("colour", "attribute"))
claim("c0001", "The animal has blue eyes", "動物の目は青い", True, tags=("attribute",))
# c0002 cat lying on the ground
animal("c0002", "cat", ["dog", "tiger", "rabbit"])
present("c0002", "a dog", "犬", False)
# c0003 black-and-white cat on grass
animal("c0003", "cat", ["bird", "squirrel", "rabbit"])
place("c0003", "meadow", ["snow", "beach", "city"])
# c0006 reddish-brown dog
animal("c0006", "dog", ["cat", "horse", "deer"])
colour("c0006", "the dog's fur", "犬の毛", "brown", ["white", "black", "grey"], tags=("colour", "attribute"))
# c0007 dog lying beside the sea
animal("c0007", "dog", ["cat", "wolf", "sheep"], diff="medium")
claim("c0007", "There is water behind the animal", "動物の後ろに水面（海）がある", True, tags=("scene",))
# c0010 two horses pulling a sleigh in snow
count("c0010", "horse", 2, options=("one", "two", "three"))
claim("c0010", "There is snow on the ground", "地面に雪がある", True, tags=("scene",))
# c0011 horse standing in shallow water
animal("c0011", "horse", ["cow", "deer", "dog"])
# c0013 brown cow with horns
animal("c0013", "cow", ["horse", "goat", "sheep"], diff="medium")
# c0015 sheep on grass
animal("c0015", "sheep", ["goat", "pig", "rabbit"])
# c0019, c0020 goats
animal("c0019", "goat", ["sheep", "deer", "dog"], diff="medium")
animal("c0020", "goat", ["sheep", "cow", "horse"], diff="medium")
# c0025 white chicken behind wire
animal("c0025", "chicken", ["duck", "eagle", "rabbit"])
# c0032 aerial view of a sailing yacht
vehicle("c0032", "sailboat", ["train", "truck", "airplane"])
# c0033 black-and-white waterfall
place("c0033", "waterfall", ["desert", "beach", "city"])
claim("c0033", "The photograph is in colour", "この写真はカラーである", False, tags=("attribute",))
# c0034 F-15 fighter jet in flight
vehicle("c0034", "airplane", ["ship", "train", "bicycle"])
colour("c0034", "the aircraft", "機体", "grey", ["red", "yellow", "green"], tags=("colour", "attribute"))
# c0036 bald eagle
animal("c0036", "eagle", ["owl", "penguin", "duck"], diff="medium")
# c0046 penguins on snow (old photograph)
animal("c0046", "penguin", ["duck", "eagle", "owl"])
claim("c0046", "The photograph is in colour", "この写真はカラーである", False, tags=("attribute",))
# c0053 giraffe
animal("c0053", "giraffe", ["zebra", "elephant", "horse"])
# c0060 tiger eye
animal("c0060", "tiger", ["zebra", "giraffe", "horse"], diff="medium")
# c0062 two tigers
count("c0062", "tiger", 2, options=("one", "two", "three"))
# c0068 macaque
animal("c0068", "monkey", ["bear", "dog", "cat"])
# c0074 white rabbit
animal("c0074", "rabbit", ["cat", "dog", "sheep"])
colour("c0074", "the animal's fur", "動物の毛", "white", ["black", "brown", "grey"], tags=("colour", "attribute"))
# c0082 wolf face
animal("c0082", "wolf", ["rabbit", "horse", "cat"], diff="medium")
# c0086 butterfly
animal("c0086", "butterfly", ["bee", "frog", "bird"])
# c0087, c0089 honeybees on flowers
animal("c0087", "bee", ["butterfly", "frog", "bird"], diff="medium")
claim("c0087", "The insect is sitting on a flower", "昆虫が花にとまっている", True, tags=("scene",))
colour("c0089", "the flower", "花", "purple", ["red", "white", "green"], tags=("colour", "attribute"))
# c0092 red-eyed tree frog
animal("c0092", "frog", ["snake", "turtle", "fish"])
colour("c0092", "the animal's eyes", "動物の目", "red", ["blue", "yellow", "black"], tags=("colour", "attribute"))
# c0093 green frog on a leaf
animal("c0093", "frog", ["snake", "turtle", "butterfly"])
# c0096 cat on a table next to a person
animal("c0096", "cat", ["dog", "rabbit", "bird"])
present("c0096", "a person", "人", True)
# c0097 two kittens in a shopping cart
count("c0097", "cat", 2, options=("one", "two", "three"))
# c0100 dog running toward the camera, people in uniform behind
animal("c0100", "dog", ["horse", "deer", "cow"])
present("c0100", "a person", "人", True)
