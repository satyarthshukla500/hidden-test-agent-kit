# No Test to Anchor On

*A measured account of small-model SWE agents under hidden tests, with a reusable evaluation kit*

## Abstract

In 72 of 90 development tasks (80%), the test that grades a fix does not exist in the agent's workspace, and only 1 bug report in 90 contains a traceback. We ran 15 configurations of Gemma 4 E4B agents on the same 90 tasks and report what the traces show. Protocol: at a solve rate near 8%, one run has a standard deviation of 2.4 tasks, so single runs cannot rank prompt changes; across 8 runs of 5 prompts only 14 tasks were ever solved and no run solved more than 8. Design: a read-only analyzer that writes its own reproduction script and hands a verbatim brief to a coder did not beat a single-agent prompt with the same budget (7 to 8 versus 8 of 90), and stricter edit rules made it worse (3 to 4). Mechanism: in 309 traced tasks, 308 of 658 edit attempts failed, 253 because the text to replace was not in the file, copied from the paraphrased brief or written from memory; 11% of briefs were written without a tool call. Budget: reserving 8,192 output tokens in a 32,768-token window overflowed 12 trajectories and 6,144 removed all of them; the official one-minute budget halves the solve rate. We release the kit: split, bucketer, trace analyzer, noise-floor calculator and per-task outcomes for every run.

## 1. Introduction

Small local models put coding agents on hardware a developer already owns, but they leave little margin. The Gemma 4 Developer Agent competition makes the constraint concrete: an agent declared only in YAML and prompts must fix real bugs in fastapi, rich, requests and httpx offline, inside a 32,768-token window and about six minutes per task. A task counts only if every required test passes.

We built a two-agent fixer on the smallest permitted model, Gemma 4 E4B, then compared it with the official single-agent prompt, and logged every run. No configuration left the 3 to 8 of 90 band. The results are about measurement: where a small agent can anchor when the grading test is hidden, why its edits fail, and how much of an observed change is noise.

Who is blocked without this: anyone evaluating a small agent on one run per change, who will keep changes that did nothing and revert changes that helped without knowing it.

Contributions, each checkable against a file in the released kit:

1. **A noise-floor protocol for small-agent evaluation.** A measured same-configuration spread (5 to 7 of 90, 2 of 10 solved tasks shared) and the binomial arithmetic that turns any solve rate and task count into a minimum detectable effect (`noise_floor.py`).
2. **A measurement of the hidden-test condition.** 72 of 90 tasks grade the fix with test functions that do not exist before it; 1 of 90 reports carries a traceback.
3. **A measured negative result on reproduce-first.** A read-only analyzer that writes `/tmp/repro.py` and hands a seven-field brief to a fresh-context coder did not beat a single-agent prompt with the same budget, and every edit rule added to it cost tasks.
4. **An edit-anchor failure mechanism.** Of 308 failed edits, 253 asked to replace text that was not in the file: 125 copied from the brief, 114 from memory, 4 whitespace; 45 were identical retries. A history-less sub-agent never sees the repository layout, so 11% of briefs invent paths.
5. **A budget failure mechanism and its fix.** Reserving 8,192 output tokens caps the prompt at 24,576 tokens; long trajectories cross it. Reserving 6,144 removed every overflow (12 to 0).
6. **A reusable kit.** Split, bucketer, trace analyzer, noise-floor calculator, prompts and per-task outcomes for every run.

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

**Why the setting generalizes.** The format follows SWE-bench [1]: issue text, repository at the pre-fix commit, fail-to-pass tests withheld from the agent. Every benchmark built this way shares the hidden-test condition; what varies is how often the issue supplies an execution anchor, and the measurement script runs on any task file in the format.

## 3. Method

The agent is two Gemma 4 E4B instances joined by a typed artifact, declared entirely in YAML and Markdown prompts.

**Analyzer.** Read-only (shell, file read, code-graph tools), no conversation history, 12 tool calls: grep the source package for identifiers from the report, write and run `/tmp/repro.py` asserting the behaviour the report asks for, confirm the lines it will name, find call sites. It answers with seven sections written to session state (`FAILING_TEST`, `TRACEBACK`, `FILES`, `CODE`, `DIAGNOSIS`, `EDIT_SITES` with exact `old_string` per site, `RISK`).

**Coder.** Calls the analyzer once, applies the top edit with `edit_file`, re-runs the check, repairs at most twice, runs the module's tests, and always submits. Scratch files go to `/tmp`; tests and runner configuration are never edited, since the grader strips them.

**The hand-off.** Both agents share one tool budget, so the split buys context isolation, not calls. Verbatim matters because `edit_file` matches `old_string` literally; Section 5.2 shows this is where the design breaks.


| Parameter | Value |
| --- | --- |
| Model | gemma-4-e4b-it-qat-w4a16-ct |
| temperature / top_p / top_k / seed | 0.2 / 0.9 / 40 / 7 |
| max_output_tokens | 6,144 (was 8,192 before p03) |
| thinking_budget | 2,048 (was 3,072), include_thoughts true |
| Per task | 5 min, 28 tool calls, 24 turns, 150 s per command |

## 4. Experiments and results

One change per run on the same 90 tasks; p01 was run twice and p03 three times to measure noise. p-runs are the two-agent design, s-runs the official single-agent sample prompt.

| Run | Change | Resolved / 90 |
| --- | --- | --- |
| p00-base | spec prompts, two agents, 8,192/3,072 tokens | 4 |
| p01 | analyzer writes a repro, greps source not tests | 7 |
| p02 | coder gates on repro and module tests | 6 |
| p01b | p01 unchanged | 5 |
| p03, p03b, p03c | 6,144 output / 2,048 thinking | 7, 7, 8 |
| p05 | second edit site as fallback | 5 |
| p06 | coder edits before any test | 4 |
| p07 | anchors only from read_file, line-number fallback | 3 |
| p09 | p07 plus the public "Budget-Fit" recipe | 4 |
| s01 | sample prompt, sample budget (1 min, 10 calls) | 5 |
| s02 | sample prompt, our budget (5 min, 28 calls) | 8 |
| s03 | s02 plus the p07 edit rules | 8 |
| s04 | s03 plus the Budget-Fit recipe | 8 |

*Held-out 39 tasks: p03 5, p07 3. Public leaderboard, 58 hidden tasks from private repositories: p03 0.06 (4 tasks), s01 0.03 (2). The single-agent prompt matches the best two-agent run and never falls below it; every rule added to the two-agent coder cost tasks.*

| Run | wrong fix | target still failing | empty patch |
| --- | --- | --- | --- |
| p00-base | 41 | 27 | 18 |
| p03 | 37 | 27 | 19 |
| p07 | 46 | 28 | 13 |
| s04 | 47 | 28 | 7 |

*Failures stay in the same three buckets whatever the prompt; the tool budget is not the constraint (median 11 of 28 calls, median wall 130 of 300 s).*

| Limit hit, 90 tasks | p01b (8,192 output) | p03 (6,144 output) |
| --- | --- | --- |
| Context-window overflow errors | 12 | 0 |
| Turn cap (24) reached | 8 | 4 |
| Session timeout (5 min) | 8 | 8 |

*Overflow is a mechanism, not a sample: the request fails once the prompt exceeds the window minus the reserved output (24,576 tokens at 8,192; 26,624 at 6,144), and no p03 trajectory reached the higher line.*

## 5. Analysis

### 5.1 The noise floor

With a solve rate of 7 of 90 (p ≈ 0.07), the binomial standard deviation of a single run is 2.4 tasks, so the 95% interval around one run spans about ±4.7 tasks. A single-run change below about five tasks is not individually significant. Detecting a doubling of the solve rate (0.07 to 0.14) at 80% power needs about 300 tasks per arm, 3.3 times our development set; at n = 90 the power to detect that doubling is 33%. Temperature 0.2 and seed 7 do not remove the variance: four tasks share one vLLM instance, so batch composition differs between runs, and wall-clock limits cut slow trajectories at different points.

Runs share their tasks, so the sharper test is paired. p01 and p01b disagree on 8 tasks (5 solved only by p01, 3 only by p01b); an exact McNemar test gives p = 0.73, which is consistent with no difference, as it should be for identical submissions. We also report solve stability, S = |solved in every run| / |solved in any run| over k runs: here S = 1/14 at k = 8. S near 1 means the agent's successes are repeatable; S near 0 means a leaderboard score mostly reflects which tasks happened to land.

Rule: run the unchanged configuration at least twice before the first comparison, and treat any change inside the observed spread as unproven. For our task set that spread is 5 to 8.

### 5.2 Why edits fail

The kit's trace analyzer parsed every tool call of three p03 runs and the held-out run (309 tasks). The coder called `edit_file` 658 times: 350 succeeded, 308 failed. Of the failures, 243 were "old_string not found", 26 "occurs N times", 21 a wrong path and 8 budget. Decoding every tool output the model had seen, 125 of the 243 missing anchors appeared verbatim in something it had read, almost always the brief, whose CODE section is paraphrased; 114 appeared nowhere; 4 differed only in whitespace. The next action after a failed edit was `read_file` 109 times, a new anchor 80 times, the identical anchor 45 times and `submit_patch` 23 times. Every task that ended with no patch is a task where no edit landed. Anchors of 2 to 8 lines landed 62% of the time, one-line anchors 44%, nine or more lines 43%.

The analyzer wrote 33 of 309 briefs (11%) without calling a tool. The mechanism is in the harness: the repository layout is given only in the initial user message, and a sub-agent with `include_contents: none` never sees it, so it invents paths such as `fastapi/fastapi/utils/model_validation.py`. In the 83 failed p03b tasks the brief named the reference file in 44 and a wrong file in 36; patches that touched the right file still failed 37 times. Localization and edit content each explain about half of the failures, which is why fixing anchors alone (p07) did not help, and 6 of 11 wrong-file baseline patches missed a fix that sits in a Pydantic compatibility module no report names.

### 5.3 The budget fails before the model does

The window is fixed at 32,768 tokens, so reserved output sets a hard prompt ceiling: 32,768 − 8,192 = 24,576; we saw the rejection at exactly 24,577 input tokens. Long coder trajectories cross that line late in the task, when a fix may be one call away. At 6,144 reserved, the ceiling rises to 26,624 and the 2,048-token thinking budget still fits inside the output. Overflow events fell from 12 to 0 and turn-cap hits from 8 to 4, at no cost in resolved tasks. Timeouts stayed at 8, so the wall clock, not the window, is now the binding limit.

A larger model is not automatically better under a fixed wall clock: with the 8,192/3,072 budget, Gemma 4 12B ended each of its first 12 tasks on a limit without a tested fix.

### 5.4 What a retry can and cannot buy

Across 8 runs only 14 of 90 tasks were ever solved, 9 of them in three or more runs, and each run found 4 to 8 of them. The ever-solved tasks have a median issue of 174 words with 4.5 backticked identifiers and a 3-line reference fix; the never-solved, 40 words, 0.5 identifiers and 12 lines, and they include 10 documentation-example fixes and 16 title-only reports. The union is the ceiling for best-of-N retries with a perfect verifier (15.6%), so the realistic target is consistency on those 14, not new capability. Budget matters as much as prompt: the sample's one-minute, ten-call budget scored 5 of 90 and 2 of 58 on the leaderboard; the same prompt with five minutes scored 8 of 90.

## 6. Limitations and future work

- **Scale.** 90 public development tasks in three repositories, one to three runs per configuration. The hidden test set comes from private repositories we cannot inspect.
- **Keep or revert decisions on prompts are calibrated, not measured.** By Section 5.1 no change here exceeds the noise floor; "kept" means no evidence of harm plus a mechanism we can name, never "better".
- **One model family, one harness.** The noise floor depends on our concurrency and sampling settings; the hidden-test rate depends on how this task set was mined.
- **Sandbox gaps.** 14 dev tasks grade through test files that import `inline_snapshot`, absent from the offline wheels, and 5 requests tasks grade through `tests/test_requests.py`, which errors at collection here. None of the 19 was ever solved; the honest local denominator is 71.

**What was falsified.** We wrote in advance that a baseline matching reproduce-first over repeated runs would mean the hidden-test measurement does not justify the redesign. The single-agent prompt matched it (8 versus 7 to 8), so the design claim falls on this task set. The measurement claims stand: p03 repeats stayed inside 5 to 8, and no overflow reappeared at 6,144 reserved tokens.

## 7. Related work

**Benchmarks.** SWE-bench [1] defined repository-level issue resolution graded by fail-to-pass tests withheld from the agent; this competition follows that format. We do not claim the hidden-test condition is new.

**New here.** Agentless [4] generates reproduction tests to rank candidate patches; SWE-agent [2] shows the tool interface shapes success; AutoCodeRover [3] localizes over program structure; OpenHands [5] is a general platform. We add (1) a measured noise floor for a small model at a small task count, with the arithmetic to carry it elsewhere, (2) a trace-level account of why a small model's edits fail, and (3) a context-budget failure mechanism with its fix, all under a harness that forbids orchestration code.

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
| cal1 | 366917009 | s01, s02, p06 |
| cal2 | 366966580 | p07, s03, held-out p07 |
| cal3 | 366973438 | s04, p09 |

Commands (Python 3.10+, standard library):

```bash
python scripts/task_properties.py data/tasks.jsonl --split data/splits/dev.txt
python scripts/buckets.py p00-base p01 p02 p01b p03 p03b p03c s02 s04
python scripts/noise_floor.py --p 0.07 --n 90 --target 0.14
python scripts/make_splits.py   # seed 1234, 30% held out per repository
```
