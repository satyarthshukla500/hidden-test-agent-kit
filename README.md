# Gemma 4 Developer Agent: offline Python bug fixer

This is an offline autonomous agent for the Kaggle Gemma 4 Developer Agent
competition. Given a bug report and a real GitHub repo at `/workspace`, it
produces a source patch. Grading runs the repo's pytest suite, and a task scores
only if every required test passes. The submission is pure YAML and prompts,
compiled by `adk-submission`. `submission/` is the only directory that ships.

## Design

Two agents, isolated from each other's context and joined by a typed artifact.
The read-only `code_analyzer` sub-agent (an `agent_tool` with
`include_contents: none` and `output_key: bug_brief`) finds the failing test,
captures its traceback, pulls verbatim code with `search_similar_code`, and
emits a seven-section brief (see `docs/BRIEF_SCHEMA.md`). The root `bugfixer`
coder starts from that brief, applies small `edit_file` patches, re-runs the
failing node, runs a regression gate, and always calls `submit_patch`. The two
agents share one tool budget, so the split buys context isolation, not extra
calls.

## Budget

| Item | Value |
|---|---|
| Wall clock per task | 5 min (`max_time_minutes`) |
| Tool calls per task | 28 (`max_tool_calls`): analyzer 12, coder 12, slack 4 |
| Turns | 24 (`max_turns`) |
| Single command timeout | 150 s (`timeout_seconds`) |
| Context | 32,768 tokens; `max_output_tokens` 8192, thinking 3072 |
| Fleet | ~120 tasks x 5 min = 10 h inside the 12 h wall |

## Run order

```bash
python scripts/build.py --model e4b         # validate and pack dist/e4b.zip
python scripts/make_splits.py               # data/splits/{dev,heldout}.txt
python scripts/score.py --split dev --tag p00-base
python scripts/score.py --compare p00-base p01
python scripts/review.py p00-base <instance_id>
```

`make build-e4b`, `make build-12b`, `make split`, `make base`,
`make dev TAG=..`, `make heldout TAG=..` and `make review TAG=.. ID=..` wrap the
same commands.

## Finals

