# Experiments

| Tag | Split | Change | Resolved | Delta | Regressions | Kept | Reason |
|---|---|---|---|---|---|---|---|
| smoke | rich_3676 | P1 prompts, e4b | 0/1 | n/a | n/a | n/a | Wiring check only: 7/7 brief sections, submit_patch reached, 14 calls, 69 s |
| p00-base | dev90 | P1 prompts, e4b (Kaggle v2) | 4/90 = 4.4% | baseline | n/a | baseline | wrong_fix 41, regression 27, no_patch 18. Budget never bound (mean 13.9 calls) |
