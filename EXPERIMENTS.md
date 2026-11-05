# Experiments

| Tag | Split | Change | Resolved | Delta | Regressions | Kept | Reason |
|---|---|---|---|---|---|---|---|
| smoke | rich_3676 | P1 prompts, e4b | 0/1 | n/a | n/a | n/a | Wiring check only: 7/7 brief sections, submit_patch reached, 14 calls, 69 s |
| p00-base | dev90 | P1 prompts, e4b (Kaggle v2) | 4/90 = 4.4% | baseline | n/a | baseline | wrong_fix 41, regression 27, no_patch 18. Budget never bound (mean 13.9 calls) |
| p01 | dev90 | analyzer call plan: reproduce-first, source-first localization (Kaggle v3, 4252 s) | 7/90 = 7.8% | +3 (+3.3 pts) | 2 (fastapi_14372, rich_3454) | yes | New: fastapi_14463/14616/14794, rich_2725/4077. wrong_fix 41->34, regression 27->31, no_patch 18->18 |
| p02 | dev90 | coder Sequence: repro-driven check + module test-file regression gate (Kaggle v4, 3677 s) | 6/90 = 6.7% | -1 vs p01 | 3 (fastapi_14463, fastapi_14616, rich_2725) | no, reverted | no_patch 18->13 but wrong_fix 34->41. Union of solved over 3 runs = 11, only 2 solved in all 3: high run-to-run noise |
| p01b | dev90 | p01 rerun, unchanged (Kaggle v5, 4458 s) | 5/90 = 5.6% | -2 vs p01 (same config) | n/a | noise run | p01 vs p01b solved sets overlap 2 of 10. Same-config spread is 5-7, so baseline 4, p01 7 and p02 6 are within noise |
| p03 | dev90 | sampling: max_output_tokens 8192->6144, thinking_budget 3072->2048 (Kaggle v7, ~4340 s) | 7/90 = 7.8% | +2 vs p01b, =p01 | n/a (noise) | yes | ContextWindowExceeded 12->0, turn-cap hits 8->4, timeouts 8->8. Removes a hard failure source at no cost |
