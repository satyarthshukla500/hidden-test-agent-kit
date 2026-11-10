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
| s01 | 366917009 | official sample prompts on e4b, no adapters, sample budget (1 min, 10 calls) | 5/90 | no_patch 49. eval 1454 s |
| s02 | 366917009 | sample prompts, our budget and sampling | 8/90 | wf 44, rg 28, np 10. eval 3250 s |
| p06 | 366917009 | p03, coder applies the edit before any test run | 4/90 | wf 36, rg 35, np 15. worse: edits from the brief, not from the file |
| p07 | 366966580 | anchors only from read_file, never resend a failed anchor, line-number fallback, analyzer must use tools | 3/90 | wf 46, rg 28, np 13. edits 93 ok / 79 fail, no edit 23, analyzer no tools 21. worse than p03 |
| s03 | 366966580 | sample prompts, our budget, same edit rules as p07 | 8/90 | wf 43, rg 23, np 16. edits 119 ok / 50 fail (kernel tally; decode 117/169) |
| heldout-p07 | 366966580 | p07 on the 39 held-out tasks | 3/39 | |
| p08smoke | 366973438 | best-of-3 verified attempts (SequentialAgent + LoopAgent), 7 min, 40 calls, 20 tasks | 3/20 | edits ok 14 / fail 48, no edit 8, analyzer no tools 7 of 20. eval 767 s |
| s04 | 366973438 | s03 + spec contract, sibling coverage, registration, no graph tools, edit by call 12 | 8/90 | wf 47, rg 28, np 7. edits ok 151 / fail 88 (kernel tally; decode 149/239). eval 3512 s |
| p09 | 366973438 | p07 + the same five rules | 4/90 | wf 44, rg 34, np 8. edits ok 88 / fail 64, no edit 20. eval 4046 s |
| p08bsmoke | 367059960 | loop of 3 single-agent attempts (no analyzer), layout listing first, site rotation, 6 min, 40 calls, 60 turns, no new attempt after 150 s, last attempt keeps its edit, finisher never resets | 5/20 | edits 30 ok / 11 fail (kernel tally; decode 28/41), no edit 2, mean wall 138 s, 1 timeout. eval 760 s |
| p08csmoke | 367063648 | p08b + baseline-aware verifier (compile, test file not worse, probe) + task rules from the trace decode | 5/20 | edits 47 ok / 20 fail (kernel tally; decode 41/67), no edit 1, mean wall 208 s, 2 timeouts, 2 call-budget exhausted. eval 1157 s |
| p08b | not run | p08b on the 90 dev tasks | - | not run yet; public leaderboard 0.06 (4/58) |

wf = wrong fix, tsf / rg = target test still failing (the `regression` bucket), empty / np = no patch. "kernel tally" is the count printed by the run notebook; "decode" is the count from the traces (results/<tag>/edits.csv). cal1..cal4 and night2 are the overnight batches that ran several tags in one notebook version; the batch has no meaning beyond that.
