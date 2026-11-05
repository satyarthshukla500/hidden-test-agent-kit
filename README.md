# hidden-test-agent-kit

This repo holds a two-agent bug fixer for the Kaggle Gemma 4 Developer Agent competition (Gemma 4 E4B) and the small kit used to measure it. It goes with the paper "No Test to Anchor On".

Every experiment, prompt and decision is logged in `EXPERIMENTS.md` and `NOTES.md`.

## What is in it

- `submission/` the agent as submitted: `agent.yaml`, `sub_agents/code_analyzer.yaml`, prompts, sampling and budget config
- `prompts/reproduce_first.md` the analyzer prompt on its own
- `variants/` the rank-2 and 12B probe configs that differ from `submission/`
- `scripts/` split, bucketing, noise floor, task properties, build and kaggle kernel generators
- `results/<tag>/buckets.json` per-task outcome of each run

## Running it

Needs the competition files in `data/` (not redistributed). Python 3.10+, no dependencies.

```bash
python scripts/make_splits.py
python scripts/task_properties.py data/tasks.jsonl --split data/splits/dev.txt
python scripts/buckets.py p00-base p01 p02 p01b p03
python scripts/noise_floor.py --p 0.07 --n 90 --target 0.14
```

`make_splits.py` is seed 1234, 30% held out per repo, which gives 90 dev and 39 held-out.

To re-run a config, fork the official "Getting Started - Gemma 4 Developer Agent" notebook (it has the wheelhouse, models and L4 x4 attached), then

```bash
python scripts/build.py --model e4b
python scripts/make_kernel.py --user <kaggle-user> --tag p03 --split dev
```

and import `kaggle/p03/gemma-agent-p03.ipynb` into the fork. The log ends with a bucket table.

## Bucket labels

- `resolved` all required tests pass
- `wrong_fix` a patch was applied and the target test fails
- `regression` test output has both passed and FAILED. mostly the target still failing, not a true regression
- `no_patch` empty diff
- `apply_failed`, `timeout`, `budget_exhausted`, `agent_error` as named. none of these showed up in our runs

## Notebook versions

Runs are versions of the kaggle notebook `voidwalkers123/getting-started-gemma-4-developer-agent`. The scriptVersionId for each run is in `EXPERIMENTS.md`.

MIT license.
