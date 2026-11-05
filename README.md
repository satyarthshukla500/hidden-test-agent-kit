# No Test to Anchor On: a small-model SWE agent and evaluation kit

This repository holds a Gemma 4 E4B bug-fixing agent for the Kaggle Gemma 4 Developer
Agent competition, plus the kit used to measure it: a repo-stratified split, a failure
bucketer, a noise-floor calculator, and one commit per experiment. The accompanying
Paper Track writeup is "No Test to Anchor On".

## Reproduce the paper's numbers (no GPU)

```bash
python scripts/buckets.py p00-base p01 p02 p01b p03
python scripts/noise_floor.py --runs 7 5 --n 90
python scripts/noise_floor.py --p 0.07 --n 90 --target 0.14
```

The first prints the failure-bucket table and the run-to-run overlap (13 tasks solved at
least once, 1 solved in every run). The other two print the single-run SD (2.4 tasks),
the 95% interval (about +/-4.7 tasks) and the tasks per arm needed to detect a doubling
of the solve rate (about 300). Python 3.10+, standard library only.

## Kit

| Artifact | Enables a reader to |
|---|---|
| `scripts/task_properties.py` | Measure the hidden-test condition (new-only test patches, tracebacks, files per fix) on any SWE-bench-format task file |
| `scripts/make_splits.py` (seed 1234, repo-stratified) | Recreate the 90/39 dev/held-out split exactly from `tasks.jsonl` |
| `scripts/buckets.py` | Classify any run into failure buckets and measure overlap between runs |
| `scripts/noise_floor.py` | Compute the SD, interval and required n for a target effect on their own solve rate |
| `prompts/reproduce_first.md` | Drop the reproduce-first analyzer prompt into their own harness |
| `submission/` | The exact agent: `agent.yaml`, `sub_agents/code_analyzer.yaml`, prompts, sampling and budget config |
| `scripts/build.py` | Validate and pack the submission for any of the four Gemma 4 QAT models |
| `scripts/make_kernel.py` | Generate a self-contained Kaggle notebook that runs any configuration on any task list |
| `results/<tag>/buckets.json` | Per-task outcome of every run reported in the paper |
| `EXPERIMENTS.md` | Audit every decision: one row and one commit per experiment |

## Re-run a configuration on Kaggle

1. Fork the official notebook "Getting Started - Gemma 4 Developer Agent" (it attaches the
   competition data, the `metric/gemma-4-developer-agent-wheelhouse` dataset, the Gemma 4
   models and GPU L4 x4).
2. Build and generate the notebook:
   ```bash
   python scripts/build.py --model e4b
   python scripts/make_kernel.py --user <kaggle-user> --tag p03 --split dev
   ```
3. In the fork, File > Import Notebook > `kaggle/p03/gemma-agent-p03.ipynb`, then
   Save Version > Save & Run All. The log ends with the bucket table and a `BUCKETS` line.

`data/` (competition files) is not redistributed; download it from the competition page
and run `python scripts/make_splits.py` to recreate `data/splits/`.

## Design in four sentences

A read-only analyzer (Gemma 4 E4B, 12 tool calls, no conversation history) writes a
reproduction script in `/tmp`, localizes the bug in the source package, and returns a
seven-field brief with verbatim code and exact edit strings. The brief lands in session
state; the coder starts from it in a fresh context, edits, re-runs the check, runs the
module's tests, and always submits. The split buys context isolation, not extra calls.
Output is capped at 6,144 tokens with a 2,048-token thinking budget so that long
trajectories stay inside the 32,768-token window.

## Budget

| Item | Value |
|---|---|
| Wall clock per task | 5 min |
| Tool calls / turns per task | 28 / 24 |
| Command timeout | 150 s |
| Output / thinking tokens | 6,144 / 2,048 |
| Sampling | temperature 0.2, top-p 0.9, top-k 40, seed 7 |

## License

MIT, see `LICENSE`.
