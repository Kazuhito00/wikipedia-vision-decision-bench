# v1 trial measurement: JEVision 0.8B and OpenAI Decisions API

Cases: 5364 (id x language; en 2596 + ja 2768 = 5364 when complete). Accuracy = correct / asked, NA counted wrong. JEVision CPU is the main result; JEVision GPU is the agreement check and the time comparison.

## (a) Accuracy

| model | all | en | ja |
|---|---|---|---|
| JEVision CPU | 76.8% (4120/5364) | 80.7% (2095/2596) | 73.2% (2025/2768) |
| JEVision GPU | 76.8% (4120/5364) | 80.7% (2095/2596) | 73.2% (2025/2768) |
| OpenAI | 92.8% (4978/5364) | 93.4% (2425/2596) | 92.2% (2553/2768) |

#### language

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| ja | 2768 | 73.2% (2025/2768) | 92.2% (2553/2768) |
| en | 2596 | 80.7% (2095/2596) | 93.4% (2425/2596) |

#### group

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| photo | 2952 | 86.2% (2545/2952) | 97.6% (2880/2952) |
| biz | 1145 | 66.0% (756/1145) | 85.9% (983/1145) |
| rsn | 920 | 60.3% (555/920) | 84.7% (779/920) |
| txt | 347 | 76.1% (264/347) | 96.8% (336/347) |

#### origin (base = first set, new = added later)

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| base | 3682 | 82.8% (3047/3682) | 94.6% (3482/3682) |
| new | 1682 | 63.8% (1073/1682) | 88.9% (1496/1682) |

#### format

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| choice | 4056 | 77.3% (3135/4056) | 93.1% (3776/4056) |
| yes/no | 1045 | 81.0% (846/1045) | 93.3% (975/1045) |
| score | 263 | 52.9% (139/263) | 86.3% (227/263) |

#### options

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| choice 2 | 139 | 86.3% (120/139) | 100.0% (139/139) |
| choice 3 | 237 | 64.6% (153/237) | 85.7% (203/237) |
| choice 4 | 2934 | 80.3% (2355/2934) | 94.1% (2762/2934) |
| choice 5 | 259 | 62.5% (162/259) | 84.6% (219/259) |
| choice 6 | 141 | 62.4% (88/141) | 87.9% (124/141) |
| choice 7 | 120 | 74.2% (89/120) | 97.5% (117/120) |
| choice 8 | 114 | 69.3% (79/114) | 95.6% (109/114) |
| choice 9 | 48 | 68.8% (33/48) | 95.8% (46/48) |
| choice 10 | 22 | 100.0% (22/22) | 95.5% (21/22) |
| choice 11 | 12 | 83.3% (10/12) | 100.0% (12/12) |
| choice 12 | 16 | 75.0% (12/16) | 87.5% (14/16) |
| choice 13 | 8 | 75.0% (6/8) | 75.0% (6/8) |
| choice 16 | 6 | 100.0% (6/6) | 66.7% (4/6) |
| score 3 | 64 | 45.3% (29/64) | 96.9% (62/64) |
| score 5 | 86 | 54.7% (47/86) | 91.9% (79/86) |
| score 7 | 63 | 49.2% (31/63) | 76.2% (48/63) |
| score 10 | 50 | 64.0% (32/50) | 76.0% (38/50) |
| yes/no | 1045 | 81.0% (846/1045) | 93.3% (975/1045) |

#### difficulty

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| easy | 1851 | 88.9% (1646/1851) | 98.5% (1824/1851) |
| medium | 2589 | 75.5% (1955/2589) | 94.3% (2442/2589) |
| hard | 924 | 56.2% (519/924) | 77.1% (712/924) |

#### modality

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| picture | 5017 | 76.9% (3856/5017) | 92.5% (4642/5017) |
| text only | 347 | 76.1% (264/347) | 96.8% (336/347) |

#### image_type

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| figure | 680 | 66.9% (455/680) | 88.1% (599/680) |
| ui | 651 | 59.1% (385/651) | 84.3% (549/651) |
| document | 537 | 77.1% (414/537) | 91.4% (491/537) |
| photo-scene | 516 | 88.4% (456/516) | 97.5% (503/516) |
| photo-object | 456 | 86.6% (395/456) | 98.5% (449/456) |
| chart | 408 | 66.9% (273/408) | 83.1% (339/408) |
| none | 347 | 76.1% (264/347) | 96.8% (336/347) |
| photo-animal | 264 | 74.6% (197/264) | 97.7% (258/264) |
| art | 210 | 76.7% (161/210) | 96.7% (203/210) |
| photo-vehicle | 158 | 84.2% (133/158) | 97.5% (154/158) |
| diagram-map | 157 | 79.0% (124/157) | 92.4% (145/157) |
| mixed | 152 | 93.4% (142/152) | 100.0% (152/152) |
| text-in-image | 140 | 82.9% (116/140) | 93.6% (131/140) |
| photo-food | 128 | 83.6% (107/128) | 97.7% (125/128) |
| photo-structure | 122 | 97.5% (119/122) | 100.0% (122/122) |
| sign | 108 | 89.8% (97/108) | 95.4% (103/108) |
| photo-person | 90 | 94.4% (85/90) | 95.6% (86/90) |
| astronomical | 76 | 86.8% (66/76) | 100.0% (76/76) |
| photo-plant | 72 | 81.9% (59/72) | 100.0% (72/72) |
| satellite | 50 | 62.0% (31/50) | 86.0% (43/50) |
| photo-other | 42 | 97.6% (41/42) | 100.0% (42/42) |

#### skill

| category | n | JEVision CPU | OpenAI |
|---|---|---|---|
| recognition | 2576 | 86.5% (2228/2576) | 97.9% (2523/2576) |
| ocr | 656 | 90.1% (591/656) | 96.5% (633/656) |
| compare | 401 | 79.6% (319/401) | 90.5% (363/401) |
| count | 400 | 53.0% (212/400) | 79.5% (318/400) |
| text-comprehension | 347 | 76.1% (264/347) | 96.8% (336/347) |
| quantity | 317 | 45.1% (143/317) | 76.3% (242/317) |
| spatial | 253 | 77.1% (195/253) | 89.3% (226/253) |
| negation | 163 | 28.8% (47/163) | 98.2% (160/163) |
| rules | 145 | 40.7% (59/145) | 69.7% (101/145) |
| uncertainty | 66 | 66.7% (44/66) | 72.7% (48/66) |
| contradiction | 40 | 45.0% (18/40) | 70.0% (28/40) |

## (b) Text-only controls (99) vs the picture questions they were made from

Caution: the control puts the exact numbers (bar heights, amounts, times) into the `state`, so the text version can be EASIER than the picture version. The difference is 'answer from text that gives the information' vs 'read it from a 224 px picture', not a pure 'does the picture matter' effect.

| lang | model | pairs | picture question | text-only control | text - picture | both right | only text right | only picture right |
|---|---|---|---|---|---|---|---|---|
| all | JEVision CPU | 173 | 55.5% (96/173) | 56.1% (97/173) | +0.6 pt | 68 | 29 | 28 |
| all | OpenAI | 173 | 82.1% (142/173) | 93.6% (162/173) | +11.6 pt | 138 | 24 | 4 |
| en | JEVision CPU | 74 | 58.1% (43/74) | 63.5% (47/74) | +5.4 pt | 34 | 13 | 9 |
| en | OpenAI | 74 | 83.8% (62/74) | 95.9% (71/74) | +12.2 pt | 61 | 10 | 1 |
| ja | JEVision CPU | 99 | 53.5% (53/99) | 50.5% (50/99) | -3.0 pt | 34 | 16 | 19 |
| ja | OpenAI | 99 | 80.8% (80/99) | 91.9% (91/99) | +11.1 pt | 77 | 14 | 3 |

## (c) Questions both models missed / only one missed

Per question id over its languages: wrong in every language by both models: **103**; wrong only by JEVision (OpenAI right in every language): **372**; wrong only by OpenAI (JEVision right in every language): **40**.

Both wrong by group/origin: biz/base 6, biz/new 47, photo/base 9, photo/new 1, rsn/base 29, rsn/new 6, txt/new 5

#### Both models wrong in every language (first 40 of 103, by id)

| id | group | origin | kind | options | difficulty | image_type | expected | JEVision got | OpenAI got |
|---|---|---|---|---|---|---|---|---|---|
| biz-0033 | biz | base | choice | choice 4 | hard | chart | 0 | en:2/ja:2 | en:2/ja:2 |
| biz-0036 | biz | base | choice | choice 4 | hard | chart | 0 | en:3/ja:3 | en:2/ja:2 |
| biz-0046 | biz | base | choice | choice 3 | medium | chart | 1 | en:2/ja:2 | en:2/ja:2 |
| biz-0097 | biz | base | choice | choice 4 | hard | ui | 1 | en:0/ja:0 | en:0/ja:0 |
| biz-0098 | biz | base | choice | choice 4 | hard | ui | 3 | en:0/ja:0 | en:2/ja:2 |
| biz-0103 | biz | base | choice | choice 4 | hard | ui | 1 | en:0/ja:0 | en:2/ja:2 |
| biz-1037 | biz | new | score | score 7 | medium | chart | 5 | en:2/ja:2 | en:6/ja:3 |
| biz-1038 | biz | new | score | score 7 | medium | chart | 2 | en:1/ja:1 | en:1/ja:1 |
| biz-1039 | biz | new | score | score 7 | medium | chart | 3 | en:2/ja:2 | en:2/ja:2 |
| biz-1040 | biz | new | score | score 10 | hard | chart | 4 | en:3/ja:3 | en:3/ja:3 |
| biz-1041 | biz | new | score | score 10 | hard | chart | 2 | en:1/ja:1 | en:1/ja:1 |
| biz-1042 | biz | new | score | score 10 | hard | chart | 8 | en:4/ja:4 | en:0/ja:0 |
| biz-1060 | biz | new | choice | choice 12 | medium | chart | 5 | en:8/ja:8 | en:3/ja:3 |
| biz-1090 | biz | new | choice | choice 3 | medium | chart | 2 | en:0/ja:0 | en:0/ja:0 |
| biz-1091 | biz | new | choice | choice 3 | medium | chart | 2 | en:1/ja:1 | en:1/ja:1 |
| biz-1092 | biz | new | choice | choice 3 | medium | chart | 2 | en:0/ja:0 | en:0/ja:0 |
| biz-1093 | biz | new | choice | choice 3 | medium | chart | 2 | en:0/ja:0 | en:0/ja:0 |
| biz-2039 | biz | new | choice | choice 5 | hard | sign | 3 | ja:1 | ja:0 |
| biz-2048 | biz | new | choice | choice 5 | medium | document | 2 | ja:1 | ja:1 |
| biz-2051 | biz | new | choice | choice 4 | medium | document | 1 | ja:2 | ja:0 |
| biz-2055 | biz | new | choice | choice 6 | medium | document | 1 | ja:5 | ja:2 |
| biz-2056 | biz | new | choice | choice 5 | hard | document | 2 | ja:3 | ja:0 |
| biz-2057 | biz | new | choice | choice 4 | hard | document | 3 | ja:0 | ja:1 |
| biz-2064 | biz | new | choice | choice 4 | medium | document | 2 | ja:0 | ja:1 |
| biz-2075 | biz | new | choice | choice 3 | medium | document | 2 | ja:1 | ja:0 |
| biz-2079 | biz | new | choice | choice 5 | easy | document | 4 | ja:2 | ja:1 |
| biz-2089 | biz | new | choice | choice 5 | hard | text-in-image | 3 | ja:0 | ja:4 |
| biz-3080 | biz | new | choice | choice 5 | medium | ui | 2 | en:0/ja:0 | en:0/ja:0 |
| biz-3081 | biz | new | choice | choice 3 | medium | ui | 0 | en:1/ja:1 | en:1/ja:1 |
| biz-3083 | biz | new | noul | yes/no | easy | ui | True | en:False/ja:False | en:False/ja:False |
| biz-3095 | biz | new | choice | choice 4 | medium | ui | 3 | en:0/ja:0 | en:0/ja:0 |
| biz-3097 | biz | new | choice | choice 6 | hard | ui | 2 | en:1/ja:5 | en:5/ja:5 |
| biz-3111 | biz | new | choice | choice 3 | easy | ui | 1 | en:0/ja:2 | en:2/ja:2 |
| biz-3147 | biz | new | choice | choice 4 | medium | ui | 3 | ja:1 | ja:2 |
| biz-3155 | biz | new | choice | choice 6 | medium | ui | 2 | en:5/ja:5 | en:1/ja:0 |
| biz-3159 | biz | new | noul | yes/no | hard | ui | False | en:True/ja:True | en:True/ja:True |
| biz-3161 | biz | new | choice | choice 6 | hard | ui | 2 | ja:1 | ja:0 |
| biz-3168 | biz | new | choice | choice 5 | hard | ui | 4 | en:0/ja:2 | en:0/ja:0 |
| biz-3172 | biz | new | choice | choice 3 | hard | ui | 1 | en:0/ja:0 | en:0/ja:0 |
| biz-3174 | biz | new | choice | choice 4 | medium | ui | 2 | en:1/ja:3 | en:1/ja:0 |

#### Only JEVision wrong (first 25 of 372, by id)

| id | group | origin | kind | options | difficulty | image_type | expected | JEVision got | OpenAI got |
|---|---|---|---|---|---|---|---|---|---|
| biz-0031 | biz | base | choice | choice 4 | hard | chart | 0 | en:2/ja:2 | en:0/ja:0 |
| biz-0032 | biz | base | choice | choice 4 | hard | chart | 2 | en:0/ja:3 | en:2/ja:2 |
| biz-0034 | biz | base | choice | choice 4 | hard | chart | 1 | en:2/ja:2 | en:1/ja:1 |
| biz-0035 | biz | base | choice | choice 4 | hard | chart | 3 | en:1/ja:1 | en:3/ja:3 |
| biz-0039 | biz | base | choice | choice 4 | hard | chart | 3 | en:2/ja:1 | en:3/ja:3 |
| biz-0040 | biz | base | choice | choice 4 | hard | chart | 1 | en:2/ja:2 | en:1/ja:1 |
| biz-0041 | biz | base | choice | choice 3 | medium | chart | 1 | en:2/ja:2 | en:1/ja:1 |
| biz-0047 | biz | base | choice | choice 3 | medium | chart | 0 | en:2/ja:2 | en:0/ja:0 |
| biz-0080 | biz | base | score | score 5 | medium | ui | 3 | en:1/ja:1 | en:3/ja:3 |
| biz-0082 | biz | base | score | score 5 | medium | ui | 0 | en:1/ja:1 | en:0/ja:0 |
| biz-0084 | biz | base | score | score 5 | medium | ui | 2 | en:1/ja:1 | en:2/ja:2 |
| biz-0085 | biz | base | score | score 5 | medium | ui | 3 | en:1/ja:1 | en:3/ja:3 |
| biz-0086 | biz | base | score | score 5 | medium | ui | 4 | en:0/ja:0 | en:4/ja:4 |
| biz-0090 | biz | base | score | score 5 | medium | ui | 3 | en:1/ja:1 | en:3/ja:3 |
| biz-0091 | biz | base | score | score 5 | medium | ui | 4 | en:0/ja:0 | en:4/ja:4 |
| biz-0096 | biz | base | choice | choice 4 | hard | ui | 1 | en:0/ja:3 | en:1/ja:1 |
| biz-0099 | biz | base | choice | choice 4 | hard | ui | 1 | en:0/ja:0 | en:1/ja:1 |
| biz-0106 | biz | base | choice | choice 4 | hard | ui | 2 | en:0/ja:0 | en:2/ja:2 |
| biz-0124 | biz | base | choice | choice 3 | medium | ui | 2 | en:1/ja:0 | en:2/ja:2 |
| biz-0133 | biz | base | choice | choice 3 | medium | ui | 2 | en:1/ja:1 | en:2/ja:2 |
| biz-0155 | biz | base | noul | yes/no | medium | ui | False | en:True/ja:True | en:False/ja:False |
| biz-0173 | biz | base | choice | choice 5 | medium | ui | 1 | en:3/ja:3 | en:1/ja:1 |
| biz-0174 | biz | base | choice | choice 5 | medium | ui | 2 | en:1/ja:1 | en:2/ja:2 |
| biz-0175 | biz | base | choice | choice 4 | medium | ui | 3 | en:2/ja:2 | en:3/ja:3 |
| biz-0219 | biz | base | choice | choice 4 | medium | document | 0 | en:1/ja:1 | en:0/ja:0 |

#### Only OpenAI wrong (first 25 of 40, by id)

| id | group | origin | kind | options | difficulty | image_type | expected | JEVision got | OpenAI got |
|---|---|---|---|---|---|---|---|---|---|
| biz-1015 | biz | new | score | score 7 | medium | chart | 5 | en:5/ja:5 | en:4/ja:4 |
| biz-1086 | biz | new | noul | yes/no | medium | chart | True | en:True/ja:True | en:False/ja:False |
| biz-1088 | biz | new | noul | yes/no | medium | chart | True | en:True/ja:True | en:False/ja:False |
| biz-1096 | biz | new | choice | choice 3 | medium | chart | 1 | en:1/ja:1 | en:0/ja:0 |
| biz-2019 | biz | new | choice | choice 4 | easy | document | 1 | ja:1 | ja:0 |
| biz-2035 | biz | new | noul | yes/no | easy | sign | True | ja:True | ja:False |
| biz-2041 | biz | new | score | score 3 | medium | sign | 1 | ja:1 | ja:0 |
| biz-2065 | biz | new | choice | choice 4 | hard | document | 0 | ja:0 | ja:3 |
| biz-3099 | biz | new | choice | choice 5 | hard | ui | 1 | en:1/ja:1 | en:0/ja:0 |
| biz-3110 | biz | new | noul | yes/no | easy | ui | True | en:True/ja:True | en:False/ja:False |
| biz-3143 | biz | new | choice | choice 4 | medium | ui | 0 | ja:0 | ja:2 |
| biz-3160 | biz | new | choice | choice 6 | medium | ui | 4 | en:4/ja:4 | en:5/ja:5 |
| biz-3163 | biz | new | choice | choice 6 | hard | ui | 5 | en:5/ja:5 | en:1/ja:3 |
| biz-3171 | biz | new | choice | choice 3 | hard | ui | 0 | en:0/ja:0 | en:2/ja:2 |
| biz-3185 | biz | new | noul | yes/no | hard | ui | False | ja:False | ja:True |
| biz-3199 | biz | new | choice | choice 7 | medium | ui | 3 | en:3/ja:3 | en:1/ja:1 |
| biz-3214 | biz | new | choice | choice 5 | medium | ui | 0 | en:0/ja:0 | en:3/ja:3 |
| biz-3225 | biz | new | noul | yes/no | hard | ui | True | ja:True | ja:False |
| photo-0042 | photo | base | choice | choice 4 | hard | document | 3 | en:3/ja:3 | en:0/ja:0 |
| photo-0461 | photo | base | noul | yes/no | medium | photo-scene | True | en:True/ja:True | en:False/ja:False |
| photo-0550 | photo | base | choice | choice 4 | easy | photo-person | 1 | en:1/ja:1 | en:0/ja:0 |
| photo-0635 | photo | base | noul | yes/no | easy | photo-person | True | en:True/ja:True | en:False/ja:False |
| photo-0878 | photo | base | choice | choice 4 | hard | chart | 1 | en:1/ja:1 | en:0/ja:0 |
| photo-1089 | photo | base | choice | choice 4 | medium | photo-scene | 1 | en:1/ja:1 | en:0/ja:0 |
| photo-1144 | photo | base | choice | choice 4 | hard | document | 1 | en:1/ja:1 | en:2/ja:2 |

#### Label-check candidates: both models wrong, giving the SAME wrong answer in every language (44)

biz-0033, biz-0046, biz-0097, biz-1038, biz-1039, biz-1040, biz-1041, biz-1090, biz-1091, biz-1092, biz-1093, biz-2048, biz-3080, biz-3081, biz-3083, biz-3095, biz-3159, biz-3172, biz-3175, biz-3182, biz-3192, biz-3206, biz-3210, biz-3215, photo-0320, photo-1019, photo-1059, rsn-0001, rsn-0005, rsn-0015, rsn-0038, rsn-0040, rsn-0066, rsn-0114, rsn-0116, rsn-0152, rsn-0201, rsn-0203, rsn-0210, rsn-1116, rsn-1120, rsn-1124, txt-1067, txt-1102

## (f) NA, time and cost

| model | asked (id x lang) | NA | NA ids (first 12) |
|---|---|---|---|
| JEVision CPU | 5364 | 0 |  |
| JEVision GPU | 5364 | 0 |  |
| OpenAI | 5364 | 0 |  |

OpenAI (model gpt-6-luna, endpoint https://api.openai.com/v1/decisions): 5364 requests, 1019702 input tokens, 2 retries, summed round trip 2283 s. Estimated cost at an ASSUMED $0.10 per 1M input tokens (GPT-6 Luna input rate; the Decisions API has no published price): **$0.102**. Output tokens were not billed in the assumption (they are reported as 0).

## JEVision CPU vs GPU

Same answer on 5360 of 5364 (id x lang); different on 4. Correctness differs on 0.

| id | lang | kind | expected | CPU | GPU |
|---|---|---|---|---|---|
| biz-3123 | en | choice | 0 | 1 | 3 |
| photo-0367 | ja | choice | 1 | 3 | 0 |
| rsn-1055 | en | choice | 1 | 6 | 4 |
| rsn-1093 | ja | choice | 7 | 5 | 6 |

Median ms per question (wall time of the ask call; GPU first-call warm-up outliers do not move a median). The CPU times count only for blocks whose calibration was valid (see below).

| subset | n | CPU ms | GPU ms | CPU/GPU |
|---|---|---|---|---|
| all | 5364 | 785 | 71 | 11.1x |
| group photo | 2952 | 786 | 71 | 11.1x |
| group biz | 1145 | 800 | 70 | 11.4x |
| group rsn | 920 | 776 | 70 | 11.1x |
| group txt | 347 | 622 | 402 | 1.5x |
| format choice | 4056 | 798 | 71 | 11.2x |
| format noul | 1045 | 703 | 67 | 10.5x |
| format score | 263 | 834 | 73 | 11.4x |
| picture | 5017 | 787 | 71 | 11.1x |
| text only | 347 | 622 | 402 | 1.5x |
| lang en | 2596 | 778 | 69 | 11.3x |
| lang ja | 2768 | 792 | 72 | 11.0x |

CPU calibration (GLiNER fixed job before/after each block, limit 600 ms): 2 of 2 blocks valid. jevision_v1all_en_224_cpu before=250 after=202 valid; jevision_v1all_ja_224_cpu before=203 after=202 valid

## Conditions recorded

- jevision_v1all_en_224_cpu: model=jevision repo=<OWNER>/JEVision-0.8B-ONNX-CPU tag=local-untagged variant=fp16 device=cpu providers_requested=['CPUExecutionProvider'] providers_used=['CPUExecutionProvider'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T12:47:57+09:00 finished=2026-10-11T13:21:31+09:00
- jevision_v1all_ja_224_cpu: model=jevision repo=<OWNER>/JEVision-0.8B-ONNX-CPU tag=local-untagged variant=fp16 device=cpu providers_requested=['CPUExecutionProvider'] providers_used=['CPUExecutionProvider'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T13:21:46+09:00 finished=2026-10-11T13:58:29+09:00
- jevision_v1all_en_224_cuda: model=jevision repo=<OWNER>/JEVision-0.8B-ONNX-CPU tag=local-untagged variant=fp16 device=cuda providers_requested=['CUDAExecutionProvider', 'CPUExecutionProvider'] providers_used=['CUDAExecutionProvider'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T12:38:41+09:00 finished=2026-10-11T12:41:46+09:00
- jevision_v1all_ja_224_cuda: model=jevision repo=<OWNER>/JEVision-0.8B-ONNX-CPU tag=local-untagged variant=fp16 device=cuda providers_requested=['CUDAExecutionProvider', 'CPUExecutionProvider'] providers_used=['CUDAExecutionProvider'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T12:41:48+09:00 finished=2026-10-11T12:47:18+09:00
- openai_v1all_en_224: model=openai repo=https://api.openai.com/v1/decisions (remote API) tag=api variant=gpt-6-luna device=remote providers_requested=['remote'] providers_used=['remote:https://api.openai.com/v1/decisions'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T12:38:26+09:00 finished=2026-10-11T12:38:27+09:00
- openai_v1all_ja_224: model=openai repo=https://api.openai.com/v1/decisions (remote API) tag=api variant=gpt-6-luna device=remote providers_requested=['remote'] providers_used=['remote:https://api.openai.com/v1/decisions'] threads=8 dataset_version=v1 question_list sha256=b14ec1a246e4d2527f5cffad488a64a186e67000afd1af0e376558e0bbd40394 started=2026-10-11T12:29:36+09:00 finished=2026-10-11T12:36:20+09:00
