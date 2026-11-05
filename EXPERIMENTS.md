# experiments

all runs on the 90-task dev split, gemma-4-e4b, 4 tasks concurrent, unless noted.
"kaggle" is the scriptVersionId of the notebook version.

| tag | kaggle | change | resolved | note |
|---|---|---|---|---|
| smoke | v1 | first wiring check, rich_3676 only | 0/1 | brief + submit ok |
| p00-base | 365724503 | spec prompts | 4/90 | wf 41, tsf 27, empty 18 |
| p01 | 365777266 | analyzer: repro script, grep source not tests | 7/90 | kept |
| p02 | 365790405 | coder: repro + module tests as gate | 6/90 | reverted |
| p01b | 365803916 | p01 again, unchanged | 5/90 | noise run. 2 of 10 shared with p01 |
| p01-12b | 365819874 | p01 on 12B | 0/12 | stopped. every task hit a limit |
| p03 | 365825150 | output 6144, thinking 2048 | 7/90 | overflow 12 to 0. kept |
| p04 | 365848731 | temperature 0 | - | stopped at 10 min |
| p03b | 365852417 | p03 again, unchanged | 7/90 | night2 job 1 |
| p03c | 365852417 | p03 again, unchanged | 8/90 | night2 job 2. p03 x3: 14 solved once, 2 every time |
| p05 | 365852417 | rank-2 fallback in coder | 5/90 | rank reported on 21, fallback used once |
| heldout-p03 | 365852417 | p03 on the 39 held-out tasks | 5/39 | night2 job 4 |

wf = wrong fix, tsf = target test still failing, empty = no patch.
