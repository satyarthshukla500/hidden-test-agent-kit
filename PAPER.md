# No Test to Anchor On

*A measured account of small-model SWE agents under hidden tests, with a reusable evaluation kit*

## Abstract

In 72 of 90 development tasks (80%), the test that grades a fix does not exist in the agent's workspace, and only 1 bug report in 90 contains a traceback. Two runs of one unchanged submission resolved 7 and 5 tasks and agreed on only 2 of the 10 tasks either solved. We report three findings, ordered by how far they transfer. Protocol: at a solve rate near 7% on 90 tasks, one run has a standard deviation of 2.4 tasks, so prompt changes worth fewer than about five tasks cannot be ranked from single runs, and detecting a doubling needs about 300 tasks per arm. Design: when grading tests are hidden, a read-only analyzer that writes its own reproduction script and hands a typed seven-field brief to an isolated coder matches the condition; traceback-first localization has nothing to anchor on. Budget: with 8,192 output tokens reserved in a 32,768-token window, long trajectories overflow, and reserving 6,144 removed all 12 overflow events. We release the kit: a stratified split, a failure bucketer, a noise-floor calculator and per-task outcomes for every run.

## 1. Introduction

Small local models put coding agents on hardware a developer already owns, but they leave little margin. The Gemma 4 Developer Agent competition makes the constraint concrete: an agent declared only in YAML and prompts must fix real bugs in fastapi, rich, requests and httpx offline, inside a 32,768-token window and about six minutes per task. A task counts only if every required test passes.

We built a two-agent fixer on the smallest permitted model, Gemma 4 E4B, and logged every run. The solve rate stayed between 4 and 8 of 90, and that is context, not the result. The results are about measurement: where a small agent can anchor when the grading test is hidden, and how much of an observed change is noise. The budget turned out to cause failures of its own.

Who is blocked without this: anyone evaluating a small agent without the GPU budget to run it hundreds of times. A team with one run per change on 90 tasks will keep changes that did nothing and revert changes that helped, and will not know it.

Contributions, each checkable against a file in the released kit:

1. **A noise-floor protocol for small-agent evaluation.** A measured same-configuration spread (5 to 7 of 90, 2 of 10 solved tasks shared) and the binomial arithmetic that turns any solve rate and task count into a minimum detectable effect (`noise_floor.py`).
2. **A measurement of the hidden-test condition.** 72 of 90 tasks grade the fix with test functions that do not exist before it; 1 of 90 reports carries a traceback.
3. **A reproduce-first, two-agent design.** A read-only analyzer writes `/tmp/repro.py`, localizes in the source package, and hands a seven-field verbatim brief to a coder that starts with a fresh context.
4. **A budget failure mechanism and its fix.** Reserving 8,192 output tokens caps the prompt at 24,576 tokens; long trajectories cross it. Reserving 6,144 removed every overflow (12 to 0).
5. **A reusable kit.** Split, bucketer, noise-floor calculator, prompts and per-task outcomes for every run, one commit per experiment.

## 2. Setting

Each task runs in two sandboxes. In the first, the agent works on the repository at the pre-fix commit with nine tools: shell, file read, edit and write, patch submission, a budget query, and three code-graph tools over precomputed call graphs and symbol embeddings. Its diff is applied to a fresh copy, the hidden test patch is added, and pytest decides. Edits to tests and runner configuration are stripped before grading.

We split the 129 public tasks by repository into 90 development and 39 held-out tasks (seed 1234) and measured the development set before writing any prompt.

| Property of the 90 dev tasks | Count | Share |
| --- | --- | --- |
| Grading test patch only adds new test functions | 72 | 80% |
| Bug report contains a Python traceback | 1 | 1% |
| Bug report contains a code block | 15 | 17% |
| Reference fix touches one file | 65 | 72% |
| Reference fix touches three or more files | 13 | 14% |

*Most graded tests are new and almost no report shows where the code fails: an agent must create its own evidence.*

**Budget arithmetic.** About 120 hidden tasks must finish inside a 12-hour wall that includes model start-up (330 to 366 s for E4B on 4x L4) and verification. That leaves about 6 minutes per task, so we set 5 minutes of agent time, 28 tool calls, 24 turns and a 150-second command timeout. The model sees at most 32,768 tokens; every token reserved for output is a token the prompt cannot use.

**Why the setting generalizes.** The task format follows SWE-bench [1]: an issue text, a repository at the pre-fix commit, and fail-to-pass tests that arrive with the fix and are withheld from the agent. Any benchmark built this way shares the hidden-test condition; what varies is how often the issue text itself supplies an execution anchor. We measured that rate only for this task set, and the measurement script runs unchanged on any task file in the same format.

## 3. Method

The agent is two Gemma 4 E4B instances joined by a typed artifact, declared entirely in YAML and Markdown prompts.

**Analyzer.** Read-only (shell, file read, code-graph tools; no edit or write), no conversation history, 12 tool calls. Its plan:

1. Grep the source package, never `tests/`, for two or three identifiers copied from the report.
2. Write `/tmp/repro.py`: import the library, do what the report describes, assert the behaviour it asks for; run it. Its output is the anchor.
3. `search_similar_code` on the two or three most relevant functions (up to 5,000 characters of ranked code per call).
4. Confirm each line it will name exists verbatim; find call sites of the function to change.

It answers with exactly seven sections, written to session state as `bug_brief`:

| Field | Content |
| --- | --- |
| FAILING_TEST | the repro command, or NO_TEST |
| TRACEBACK | innermost 3 non-test frames, verbatim |
| FILES | path:start-end, 1 to 3 entries |
| CODE | 5 to 20 verbatim lines per site, 2 lines of context |
| DIAGNOSIS | two sentences naming the wrong value or missing branch |
| EDIT_SITES | exact `old_string` per site, best first |
| RISK | call sites a signature change would break, or NONE |

**Coder.** Calls the analyzer once, applies the top edit with `edit_file`, re-runs the check, repairs at most twice, runs the module's tests, and always submits. Scratch files go to `/tmp`; tests and runner configuration are never edited, since the grader strips them.

**The hand-off.** Both agents share one tool budget, so the split buys context isolation, not calls: the analyzer's file dumps never enter the coder's window. Verbatim matters because `edit_file` matches `old_string` literally; a paraphrase fails the edit and costs a re-read.

```yaml
# sub_agents/code_analyzer.yaml (excerpt)
instruction: !include ../prompts/analyzer.md
output_key: bug_brief
include_contents: none
tools: [run_command, search_similar_code, get_code_neighbors, get_code_subgraph, read_file]
# agent.yaml (excerpt)
tools:
  - agent_tool:
      config_path: sub_agents/code_analyzer.yaml
      skip_summarization: true
```

| Parameter | Value |
| --- | --- |
| Model | gemma-4-e4b-it-qat-w4a16-ct, both agents |
| temperature / top_p / top_k / seed | 0.2 / 0.9 / 40 / 7 |
| max_output_tokens | 6,144 (was 8,192 before p03) |
| thinking_budget | 2,048 (was 3,072), include_thoughts true |
| Per task | 5 min, 28 tool calls, 24 turns, 150 s per command |

## 4. Experiments and results

Every E4B configuration we ran resolves between 4 and 8 of 90 development tasks. We changed one thing per run; p01 was run twice and p03 three times to measure noise. Resolve counts are reported as context. The claims in this section are the spread, the failure distribution and the overflow mechanism.

Resolved, of 90 dev tasks (Gemma 4 E4B, Kaggle notebook versions 2, 3, 4, 5 and 7): p00-base 4, p01 7, p02 6, p01b 5, p03 7.

*The two identical runs span 5 to 7, which covers every configuration after the baseline: no prompt change here is distinguishable from noise. 13 tasks were solved at least once, 1 (requests_6644) in every run.*

| Run | wrong fix | target still failing | empty patch |
| --- | --- | --- | --- |
| p00-base | 41 | 27 | 18 |
| p01 | 34 | 31 | 18 |
| p02 | 41 | 30 | 13 |
| p01b | 39 | 30 | 16 |
| p03 | 37 | 27 | 19 |

*Failures stay in the same three buckets whatever the prompt; the tool budget is not the constraint (baseline: 13.9 of 28 calls on average, maximum 22, a complete brief and a submit call on every task).*

| Limit hit, 90 tasks | p01b (8,192 output) | p03 (6,144 output) |
| --- | --- | --- |
| Context-window overflow errors | 12 | 0 |
| Turn cap (24) reached | 8 | 4 |
| Session timeout (5 min) | 8 | 8 |

*Overflow is a mechanism, not a sample: the request fails once the prompt exceeds the window minus the reserved output (24,576 tokens at 8,192; 26,624 at 6,144), and no p03 trajectory reached the higher line. Turn-cap hits halve; timeouts do not move.*

**Repeats, rank-2 and held-out (version 365852417).** Two unchanged p03 repeats resolved 7 and 8; over the three p03 runs 14 tasks were solved at least once, 2 every time. A rank-2 variant (the coder falls back to a second edit site) resolved 5 and used the fallback once. On the 39 held-out tasks p03 resolved 5 (13%): no sign of overfitting, and not distinguishable from 8% at n = 39.

## 5. Analysis

### 5.1 The noise floor

With a solve rate of 7 of 90 (p ≈ 0.07), the binomial standard deviation of a single run is 2.4 tasks, so the 95% interval around one run spans about ±4.7 tasks. A single-run change below about five tasks is not individually significant. Detecting a doubling of the solve rate (0.07 to 0.14) at 80% power needs about 300 tasks per arm, 3.3 times our development set; at n = 90 the power to detect that doubling is 33%. Temperature 0.2 and seed 7 do not remove the variance. Four tasks share one vLLM instance, so batch composition, and with it floating-point results, likely differs between runs, and wall-clock limits cut slow trajectories at different points.

Runs share their tasks, so the sharper test is paired. p01 and p01b disagree on 8 tasks (5 solved only by p01, 3 only by p01b); an exact McNemar test gives p = 0.73, which is consistent with no difference, as it should be for identical submissions. We also report solve stability, S = |solved in every run| / |solved in any run| over k runs: here S = 1/13 at k = 5. S near 1 means the agent's successes are repeatable; S near 0 means a leaderboard score mostly reflects which tasks happened to land.

Rule: run the unchanged configuration at least twice before the first comparison, and treat any change inside the observed spread as unproven. For our task set that spread is 5 to 8. The 13 tasks solved at least once, about double any single run, also name a target: consistency on tasks the agent can already solve is worth as much as new capability.

### 5.2 Where the 44% wrong-file rate comes from

In 32 failed baseline traces, 26 briefs said NO_TEST (81%), 7 patches were empty (22%), and 11 of the 25 non-empty patches edited no file the reference fix touches (44%). The 11 decompose as follows:

| Wrong-file case | Count |
| --- | --- |
| Fix is in the Pydantic compatibility module (`_compat`); no report names it | 6 |
| Agent edited `utils.py` or `applications.py`; the fix is in `dependencies/utils.py` | 2 |
| Reference fix spans several files; agent edited one that is not among them | 2 |
| Reference fix is in documentation examples only | 1 |

*Six of eleven wrong-file cases share one cause: the fix sits in a compatibility layer the report never mentions, and a small model reading a 400-character report edits the module that matches its words.*

### 5.3 The budget fails before the model does

The window is fixed at 32,768 tokens, so reserved output sets a hard prompt ceiling: 32,768 − 8,192 = 24,576. The harness rejects the call above it; we saw the rejection at exactly 24,577 input tokens. Long coder trajectories (analyzer brief, file reads, test output) cross that line late in the task, when a fix may be one call away. At 6,144 reserved, the ceiling rises to 26,624 and the 2,048-token thinking budget still fits inside the output. Overflow events fell from 12 to 0 and turn-cap hits from 8 to 4, at no cost in resolved tasks. Timeouts stayed at 8, so the wall clock, not the window, is now the binding limit.

A larger model is not automatically better under a fixed wall clock. With the 8,192/3,072 budget, Gemma 4 12B ended each of its first 12 tasks on a limit (6 on the turn cap, 6 on the timeout) without a tested fix. A 12B probe with its own budget (3,072 output tokens, a 16-turn cap, a forced submit after 12 tool calls) is configured in the repository but has not been run.

## 6. Limitations and future work

- **Scale.** 90 public development tasks in three repositories, one to three runs per configuration. The hidden test set comes from private repositories we cannot inspect.
- **Keep or revert decisions on prompts are calibrated, not measured.** By Section 5.1 no change here exceeds the noise floor; "kept" means no evidence of harm plus a mechanism we can name, never "better".
- **Coarse bucket.** "Target still failing" is any failing run whose test output shows both passed and failed tests; it is not a strict regression measure.
- **One model family, one harness.** The noise floor depends on our concurrency and sampling settings; the hidden-test rate depends on how this task set was mined.

**What would falsify the thesis.** If a traceback-anchored baseline matched reproduce-first on this task set over repeated runs, the hidden-test measurement would not justify the redesign. If repeated runs of p03 fell outside 5 to 7, the noise floor would be an artifact of one pair of runs or of our concurrency setting rather than a property of small-agent evaluation at n = 90. If overflow events reappeared at 6,144 reserved tokens, the mechanism in Section 5.3 would be incomplete. The p03 repeats reached 8, so the spread widens to 5 to 8.

## 7. Related work

**Benchmarks.** SWE-bench [1] defined repository-level issue resolution graded by fail-to-pass tests withheld from the agent; this competition follows that format. We do not claim the hidden-test condition is new.

**Borrowed.** From Agentless [4], the idea of generating a reproduction test before patching. From SWE-agent [2], the view that the tool interface shapes success, though our nine tools are fixed by the harness. From AutoCodeRover [3], code search over program structure for localization, which the harness exposes as embedding and call-graph tools.

**New here.** (1) Reproduction placed inside a read-only sub-agent with a 12-call budget and no shared history, joined to the coder only by a verbatim seven-field brief, all declared in YAML with no orchestration code. (2) A measured noise floor for a small model at a small task count, with the arithmetic to carry it to other solve rates. (3) A context-budget failure mechanism specific to small windows, with its fix. Agentless uses reproduction tests to rank many candidate patches; under a 28-call budget we generate one reproduction and one to three ranked edit sites. OpenHands [5] is a general agent platform; our setting forbids custom orchestration code.

**Evaluation variance.** Run-to-run variance of agent benchmarks is increasingly reported; we add a small-model, small-budget data point and a minimum-detectable-effect calculator.

**References**

1. C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, K. Narasimhan. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024.
2. J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, O. Press. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. NeurIPS 2024.
3. Y. Zhang, H. Ruan, Z. Fan, A. Roychoudhury. AutoCodeRover: Autonomous Program Improvement. ISSTA 2024.
4. C. S. Xia, Y. Deng, S. Dunn, L. Zhang. Agentless: Demystifying LLM-based Software Engineering Agents. arXiv:2407.01489, 2024.
5. X. Wang et al. OpenHands: An Open Platform for AI Software Developers as Generalist Agents. arXiv:2407.16741, 2024.

## 8. Reproducibility

Code, prompts, per-task outcomes and the full experiment log: [github.com/satyarthshukla500/hidden-test-agent-kit](https://github.com/satyarthshukla500/hidden-test-agent-kit), MIT license. Runs are versions of the Kaggle notebook [voidwalkers123/getting-started-gemma-4-developer-agent](https://www.kaggle.com/code/voidwalkers123/getting-started-gemma-4-developer-agent), forked from the official starter. The evaluated models are Gemma 4 E4B and 12B (QAT, w4a16), and the repository holds every prompt and config used.

| Run | Kaggle scriptVersionId | Config |
| --- | --- | --- |
| p00-base | 365724503 | spec prompts, 8,192/3,072 |
| p01 | 365777266 | reproduce-first analyzer |
| p02 | 365790405 | coder check change (reverted) |
| p01b | 365803916 | p01 unchanged |
| p01-12b | 365819874 | p01 on 12B, 12 tasks |
| p03 | 365825150 | p01 + 6,144/2,048 |
| night2 | 365852417 | p03 x2, rank-2, held-out |

Commands (Python 3.10+, standard library):

```bash
python scripts/task_properties.py data/tasks.jsonl --split data/splits/dev.txt
python scripts/buckets.py p00-base p01 p02 p01b p03
python scripts/noise_floor.py --p 0.07 --n 90 --target 0.14
python scripts/make_splits.py   # seed 1234, 30% held out per repository
```
