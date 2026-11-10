# figures

Built by `python scripts/make_figures.py` (matplotlib; PNG at 200 dpi and SVG). Every number is parsed from a repo file or hard-coded with a comment naming its source.

Paper figure numbers: Figure 1 = fig5_sandbox, Figure 2 = fig1_runs, Figure 3 = fig3_funnel, Figure 4 = fig4_consistency, Figure 5 = fig2_edit_failures.

| figure | data | title |
| --- | --- | --- |
| fig1_runs | EXPERIMENTS.md run table (resolved/90, /39, /20); family from the tag: s* = sample prompt (analyzer optional), p00..p09 = mandatory brief (analyzer then coder), p08* = retry loop. Excludes the 1-task smoke, the 12B probe and stopped/blocked runs. | Every configuration solved 3 to 8 of 90 dev tasks. |
| fig2_edit_failures | Trace re-decode over 309 traced tasks (p03b, p03c, p05, held-out p03): 658 edit_file calls = 350 landed + 308 failed; failed by cause 243 not found / 25 occurs N times / 21 wrong path / 8 budget / 11 other; the 243 by where the text had appeared: 92 in the brief (88 exact + 4 whitespace), 29 in a file window the coder read, 12 in the coder's own earlier text, 7 only in analyzer tool output, 2 shell/search, 101 nowhere. Right panel: landed by anchor length 39/89, 243/410, 68/159 (the attempted counts sum to 658). | Of 243 missing edit anchors, 92 matched text in the brief and 101 matched no brief, file window or tool output. |
| fig3_funnel | results/<run>/buckets.json for every 90-task dev run present (p00-base, p01, p01b, p02, p03, p03b, p03c, p05, p06, p07, p09, s01, s02, s03, s04). `regression` is drawn as "target still failing"; `budget_exhausted` etc. as "other". Hatched: the 20 tasks the sandbox does not grade, derived from data/tasks.jsonl test patches. Edit-landing labels from the trace re-decode (p03 pooled 350/658; p06 118/199; p07 93/172; s01 51/77; s02 119/187; s03 117/169; s04 149/239). | Dev runs: sample prompt landed 62-69% of edits, briefed 49-60%; resolved stayed at 3 to 8 of 90. |
| fig4_consistency | results/{p00-base,p01,p02,p01b,p03,p03b,p03c,p05}/buckets.json, per-task count of runs with bucket resolved. | Only 14 of 90 tasks were solved in any of 8 runs; 9 of them in 3 or more runs. |
| fig5_sandbox | data/tasks.jsonl test_patch text for the 90 ids in data/splits/dev.txt: imports inline_snapshot (14), dirty_equals only (1, fastapi_14303), file tests/test_requests.py (5) = 20 ungradable; ever-solved is the union over all fifteen 90-task buckets.json files (16 tasks; none of the 20). | 20 of 90 dev tasks are not graded in the offline sandbox; at most 70 are gradable. |
