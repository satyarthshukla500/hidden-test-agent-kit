# notes

Running log, newest at the bottom. The results table is EXPERIMENTS.md; the findings are PAPER.md. `v<n>` is a version of the run notebook, `cal<n>` and `night2` are batches that ran several configurations in one version.

2026-11-04
- read HARNESS_README. tools, budgets, patch stripping all as expected.
- swegemma / adk-submission / adk-eval-core not in data/wheels, not on pypi. no docker, no gpu here. local runs are out.
- scaffold written. build.py ok, 6 files in the zip.
- `{hints}` changed to `{hints?}`. all 129 tasks have empty hints and adk raises on a missing state var.
- sub_agents include paths use `../`, copied from the sample. validate_directory accepts them.

2026-11-05
- 00:10 smoke on rich_3676 (v1). brief has all 7 sections, coder reaches submit_patch. not resolved. vllm start 366s.
- 00:30 kernel now runs 4 tasks at once (evaluate_task is async). buckets computed in-kernel, no downloads needed.
- dev split: 72/90 test patches only add new tests. 1/90 reports has a traceback. 65/90 fixes touch one file.
- so "find the failing test first" has nothing to find most of the time.
- 01:50 p00-base done (v2). 4/90. wrong_fix 41, target-still-failing 27, empty 18. mean 13.9 calls of 28, max 22. budget isn't binding.
- read 32 failed briefs. NO_TEST in 26. 11 of 25 non-empty patches in a file the gold fix doesn't touch. 7 empty.
- p01: analyzer writes /tmp/repro.py, greps the package not tests/. 7/90 (v3). keeping it.
- p02: coder uses the repro + module tests as gate. 6/90 (v4). no better than p01, reverting.
- union of solved over 3 runs is 11, only 2 solved every time. noisy.
- p01b = p01 unchanged (v5). 5/90. overlap with p01 is 2 of 10. so 4..7 is all noise.
- p01 on 12B (v6): first 12 tasks all hit the turn cap or the 5 min timeout, 0 resolved. stopped it.
- ContextWindowExceeded at 24577 input tokens. 32768 - 8192 = 24576. that's the whole bug.
- p03: output 6144, thinking 2048 (v7). 7/90. overflow 12 to 0, turn cap 8 to 4, timeouts still 8. keeping.
- p04 temperature 0 started then stopped after 10 min.
- p01 vs p01b mcnemar p = 0.73. stability S = 1/13 over 5 runs.
- night2 (v9): p03 x2, rank-2 variant, 39 held-out, one vllm start. 12b probe queued after.
- night2 done, 3h40m. p03b 7, p03c 8, p05 (rank-2) 5, held-out 5/39.
- p03 x3: S = 2/14, mcnemar p = 1.00 for every pair. rank-2 fallback fired once, not worth it.
- held-out 13% vs dev 8%: no overfit. 12b probe not run.

2026-11-08
- public LB has 58 tasks. p03 = 0.06, read as 4/58 assuming the score is truncated (4/58 = 0.069).
- we never ran the official sample prompts on e4b. cal1 (v10): s01 sample exact, s02 sample with our budget, p06 edit-first coder.
- no_patch means empty diff, the harness recovers unsubmitted edits. so 17-19 of 90 tasks end with no edit at all.
- review.txt 'tool sequence' is junk, TOOLS_RE matches prompt text. real calls are in traces/. cpu notebook gemma-agent-trace-analysis reads them.
- p03b errors: 8 timeouts, 7 turn cap, 68 none. no_patch 15.
- traces (p03b, p03c, p05, heldout-p03; 309 tasks): edit_file 350 ok / 308 fail. 243 'old_string not found' (source split in the re-decode below), 25 'occurs N times', 21 wrong path.
- after a failed edit: read_file 109, new anchor 80, SAME anchor again 45, submit 23. every no_patch task = zero landed edits.
- analyzer called no tool in 33/309 tasks and wrote the brief from memory. 5 of those resolved anyway.
- anchors of 2-8 lines land 59%, 1 line 44%, 9+ lines 43%. first edit attempt lands 77%.
- time is not binding: analyzer done ~40s, first edit ~90s, submit ~115s, wall median 130s of 300.
- p07 = anchors only from read_file windows, never resend a failed anchor, line-number fallback, analyzer must use tools.
- cal1 (v10, 2h23m): s01 5/90 with 49 no_patch (1 min budget too short), s02 8/90 (np 10), p06 4/90. single-agent sample prompt + our budget ties p03's best. edit-first hurt.
- p08 = SequentialAgent [analyzer -> LoopAgent(3 x fresh attempt, temp 0.7, verify, submit only if checks pass) -> finisher]. 7 min / 40 calls. untested on the harness: loop + nudge semantics unknown.

2026-11-09
- LB: s01 (sample prompts, 1 min budget) scored 0.03 = 2/58.
- cal3 (v12): p08smoke 3/20 (edits 14 ok / 48 fail, analyzer skipped tools in 7 of 20), s04 8/90, p09 4/90. every single-pass prompt so far lands in 4..8 of 90. the recipe did not lift s04 above s02.
- cal2 (v11): p07 3/90, s03 8/90, heldout-p07 3/39. the edit rules hurt the two-agent design (p03 7/7/8 -> p07 3, p09 4). single-agent s02/s03/s04 = 8/8/8.
- the two-agent design does not beat the sample prompt on e4b; every single-pass prompt sits in 4..8 of 90.
- analysis notes: include_contents none hides the workspace layout from the analyzer (invented paths); p08 call budget 12+3x11+6=51 > 40 and last attempt reverts -> empty tree; 12 h wall: 120 x mean wall must stay < 9 h; attempt rotation via last_attempt; read the existing test file for the spec; 14 dev tasks need inline_snapshot (unsolvable locally), 5 requests tasks graded via test_requests.py -> honest denominator 70.
- verifier analysis: our attempt decision rejected on 'status error', but 7 of 8 correct p03c patches ended with an error-status check. verifier = py_compile + module test file not worse than baseline + probe; reject only on BROKEN.
- sandbox analysis: 20 of 90 dev tasks cannot be graded in our sandbox (14 import inline_snapshot, 1 dirty_equals, 5 grade through tests/test_requests.py); 5 of them had a p03b patch matching the reference fix. 8 task rules added to p08c.
- p08b smoke (v13): 5/20 (rich_4077, fastapi_14786, rich_3905, requests_6644, rich_3454), edits 30 ok / 11 fail (kernel tally; decode 28/41), mean wall 138 s -> wall rule 5.5 h, passes. loop mechanics work.
- p08c smoke (v14): 5/20 (rich_4077, fastapi_14786, rich_3905, requests_6644, rich_2725), edits 47 ok / 20 fail (kernel tally; decode 41/67), mean wall 208 s (wall rule 7.9 h, passes with less margin), 2 timeouts, 2 at 40 calls. same count as p08b, slower.

- s04 submitted to the public leaderboard.
- lb s04 = 0.03 (2/58), same as s01. dev 8/90 did not carry to the hidden set; s04 prompt also carries a broken `split` example (a raw newline inside the quotes) in the line-number fallback, fixed in the next variant. note: the sample agent.yaml includes code_analyzer as an optional agent_tool, so the s-runs are 'analyzer as optional tool', not strictly single-agent.
- re-decode (scripts/edit_decode.py, cpu notebook v11, dataset gemma-agent-results-night2 = p03b, p03c, p05, heldout-p03; the '309 traces' are these four runs, not p03 x3): 658 edit_file calls, 350 ok, 243 old_string not found, 25 occurs-N-times, 21 wrong path, 8 budget, 11 other. origin of the 243, author-aware (analyzer tool output is invisible to the coder): brief 92 (88 exact + 4 whitespace), coder's own read_file 29, coder's own earlier text 12, analyzer-only output 7, shell 1, search 1, nowhere 101. per run not_found: heldout 40, p03b 51, p03c 81, p05 71. landing by anchor lines (658 calls): 1 line 39/89, 2-8 lines 243/410, 9+ lines 68/159 (p08c excluded: 42/109, 273/446, 76/170 with it). read_file content carries no line-number prefixes, so the earlier 'old in seen' test was not prefix-biased;
- decode of cal1 traces (cpu notebook v12, dataset v2): s01 77 edit calls, 51 ok (66%), 13 not found (12 nowhere, 1 read_file), 8 occurs-N-times, 5 other; s02 187 calls, 119 ok (64%), 51 not found (40 nowhere, 9 read_file, 2 own text); p06 199 calls, 118 ok (59%), 58 not found (27 brief incl 2 whitespace, 24 nowhere, 5 own text, 2 read_file). the sample-prompt agent's missing anchors are mostly text it never read; the briefed coder's are mostly brief text. per-task buckets for s01, s02, p06 now in results/.
- decode of cal2 traces (cpu notebook v13, dataset v3): p07 172 edit calls, 93 ok (54%), 59 not found (31 brief incl 2 whitespace, 22 nowhere, 6 read_file); s03 169 calls, 117 ok (69%), 36 not found (20 nowhere, 12 read_file, 4 own text); heldout-p07 62 calls, 28 ok, 24 not found (13 nowhere, 8 brief, 3 read_file). per-task buckets for p07, s03, heldout-p07 now in results/.
- decode of cal3 traces (cpu notebook v14, dataset v4): s04 239 edit calls, 149 ok (62%), 68 not found (51 nowhere, 12 read_file, 4 own text, 1 shell); p09 152 calls, 88 ok (58%), 45 not found (23 nowhere, 15 brief, 3 shell, 3 own text, 1 analyzer-only); p08smoke 62 calls, 14 ok, 48 not found (36 brief, 7 read_file, 3 nowhere, 2 own text). anchor-length landing over the 658 night2 calls corrected: 1 line 39/89 (not 39/100). per-task buckets for s04, p09, p08smoke now in results/; every run in the paper tables has a per-task file.
- decode of cal4 traces (cpu notebook v15, dataset v5): p08bsmoke 41 edit calls, 28 ok (68%), 10 not found, all text the model had never read (no brief in this design). p08csmoke 67 calls, 41 ok (61%), 9 not found, all never-read. every run in the paper tables now has results/<tag>/buckets.json.
- landing jump is a prompt-family contrast (s02 with no edit rules landed 64%), not an edit-rule effect; pooled s02-s04 vs p03 trio: no patch 33 vs 51 of 270 (p 0.043), wrong fix 134 vs 112 (p 0.069), resolved 24 vs 22; sd at 7/90 is 2.5; 5/33 vs 20/276 p 0.16; union over all 15 full runs 16 of 90.
- edits.csv files added under results/<run>/ from the cpu notebook outputs v11-v15.

2026-11-10
- extended decode (cpu notebook v17, dataset v1 = p03b, p03c, p05, heldout-p03, plus the p08c smoke): edits.csv now carries an anchor hash and a resend flag, tasks.csv the analyzer's tool calls per task. over the four runs: 658 calls, 308 failed, 87 failures repeat the anchor of the failed edit just before them in the task (74 not found, 9 wrong path, 3 occurs-N-times, 1 budget), 105 repeat any earlier failed anchor; the 243 not-found calls are 157 distinct anchors; 524 distinct anchors in all. the earlier '45' counted only a repeat as the very next action. analyzer made no tool call in 33 of 309 tasks; 5 of those resolved, 20 of the other 276.
- p08b on the public leaderboard: 0.06 = 4/58, same as p03. a loop of single-agent attempts with no analyzer ties the best two-agent run.
