# Experiments

| Tag | Split | Change | Resolved | Delta | Regressions | Kept | Reason |
|---|---|---|---|---|---|---|---|
| smoke | rich_3676 | P1 prompts, e4b | 0/1 | n/a | n/a | n/a | Wiring check only: 7/7 brief sections, submit_patch reached, 14 calls, 69 s |
| p00-base | dev90 | P1 prompts, e4b (Kaggle v2) | 4/90 = 4.4% | baseline | n/a | baseline | wrong_fix 41, regression 27, no_patch 18. Budget never bound (mean 13.9 calls) |
| p01 | dev90 | analyzer call plan: reproduce-first, source-first localization (Kaggle v3, 4252 s) | 7/90 = 7.8% | +3 (+3.3 pts) | 2 (fastapi_14372, rich_3454) | yes | New: fastapi_14463/14616/14794, rich_2725/4077. wrong_fix 41->34, regression 27->31, no_patch 18->18 |
