# Label check: questions both models missed in every language, with the same wrong answer (2026-10-11)

44 candidates (list in summary_v1.md). 12 were compared with the 224 px picture (work/px224_v1). In none of them is the label wrong.

| id | question | expected | finding |
|---|---|---|---|
| photo-0320 | "There are two whales in the picture" (yes) | True | A mother and a calf, the calf half hidden behind: True is defensible but borderline (candidate for rewording or dropping) |
| photo-1019 | which word is on the signs | Pharmacy | The sign reads "Chinese Medicine Pharmacy / Western Medicine Pharmacy": correct; the text is hard to read at 224 px |
| photo-1059 | what the red tin likely contains | first-aid supplies | "Toeristen Verbanddoos" (Dutch: first-aid box): correct; both models guessed cigarettes |
| biz-0033 | how many bars rise above the red dashed line | 5 | All 5 bars are above the line, bars 1 and 5 only by a few pixels at 224 px: correct but hard (hard is right) |
| biz-0046 | which line ends higher at the right edge | red | Red ends a little higher than blue: correct; close at 224 px |
| biz-0097 | how many tiles are red | 3 | 3 red tiles: correct; both models said 4 |
| rsn-0001 | sum of bars D and E | 39 | 30 + 9 = 39: correct; both said 21 |
| rsn-0005 | sum of bars D and E | 67 | 33 + 34 = 67: correct |
| rsn-0015 | payable after the discount | 850 | 600 + 250 + 100 - 100 = 850: correct; both said 550 |
| rsn-0038 | earliest train you can catch | 13:45 | arrival 13:43, trains 13:20 / 13:40 / 13:45 / 13:55: correct |
| biz-3083 | "The 'Cancel' button is disabled" (yes) | True | The Cancel label is drawn lighter than Retry, but the disabled look is weak at 224 px: the answer follows the configuration (true), but this is the one worth re-checking with the picture at full size |
| rsn-0066 | which side the front faces after turn right, right | left | Red tip points right; two right turns give left: correct; both said "right" (no rotation) |

Reading: the shared misses are model weaknesses (counting, arithmetic over read numbers, rotation, small differences at 224 px), not wrong labels.
Two items to look at again as questions (not as labels): photo-0320 (ambiguous count) and biz-3083 (weak visual cue).
