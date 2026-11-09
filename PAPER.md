# No Test to Anchor On

*What 15 runs of a Gemma 4 E4B bug-fixing agent show about hidden tests, failed edits and run-to-run noise*

## Abstract

In 72 of our 90 development tasks the grading patch adds a new test function, and in 55 of 90 it touches no existing test; 1 report in 90 contains a traceback. A Gemma 4 E4B agent has no failing test to run. Our best run solved 8 of 90; on the public leaderboard three submissions scored 4, 2 and 2 of 58 hidden tasks (0.06 and 0.03; 95% interval for 4 of 58, 1 to 10). Fifteen runs of 12 configurations all solved 3 to 8 of 90, and identical reruns spanned 5 to 8, so no prompt comparison here is significant. In 309 traced tasks, 243 of 308 failed edits asked to replace text not in the file.

The official sample prompt, run under our budget, was one of the 12 configurations and scored 8 of 90; our two-agent design, a read-only analyzer writing a brief for a coder, scored 7, 7 and 8. An edit lands when its edit anchor, the exact `old_string` the edit call must match, is found in the file. Edit rules that raised the share of landed edits from 53% (350 of 658, p03) to 63% and 70% (151 of 239 in s04, 119 of 169 in s03) moved tasks from the empty-patch bucket (19 to 7 of 90) into the wrong-fix bucket (37 to 47) and left the resolved count at 7 to 8. On this model an edit that lands is necessary and nowhere near sufficient: the fix is wrong before it is applied.

## 1. Introduction

Most writeups for this competition change a prompt, run once and report the new score. At a solve rate near 8% on 90 tasks, one run has a standard deviation of 2.4 tasks, so a three-task gain is not evidence of anything. This paper reports what 15 runs of Gemma 4 E4B, the smallest permitted model, show when read together.

The setting is the Gemma 4 Developer Agent competition: an agent declared only in YAML and Markdown prompts must fix real bugs in fastapi, rich, requests and httpx, offline, inside a 32,768-token window and about six minutes per task. We call a failing test or traceback the agent can run an execution anchor; we counted how often a task supplies one.

Contributions:

1. **The task condition, bounded and reproducible.** 72 of 90 development tasks add a new test function, 55 of 90 touch no existing test line, 1 report of 90 contains a traceback and 10 name an exception class; the counting rule is one sentence (Section 2) and `scripts/task_properties.py` applies it to any SWE-bench-format file.
2. **Landing versus outcome.** Of 658 `edit_file` calls in 309 traced tasks, 308 failed, 243 because the anchor was not in the file. Rules that raised the landing rate from 53% to 63-70% moved tasks from no-patch to wrong-fix and left resolved counts where they were; an author-aware decode of each missing anchor's source sits underneath.
3. **A pre-stated negative result, with its breaches.** A mandatory, history-less brief as the coder's anchor source scored 7, 7 and 8 of 90 and did not beat the official sample prompt under the same budget (8 of 90; Fisher p = 1.0); leaderboard 4, 2 and 2 of 58 (Section 7).
4. **A noise data point for small agents.** SD 2.4 tasks at p about 0.08, n = 90; identical repeats spanned 5 to 7 and 7 to 8; solve stability S = 1/13 over 5 runs, 2/14 over 3, 1/14 over 8; a local 8 versus 7 became a hidden 2 versus 4.

## 2. Setting

An agent here never sees the test that grades it, and it almost never sees a traceback. The agent works on the repository at the pre-fix commit with nine tools (shell, file read, edit, write, patch submission, a budget query, three code-graph tools). Its diff is applied to a fresh copy, the hidden test patch is added, and pytest decides; edits to tests are stripped first.

We split the 129 public tasks by repository into 90 development and 39 held-out tasks (seed 1234). Counting rule: a test patch "adds a new test function" when it contains a `+def test_` line and no `-def test_` line, and "touches no existing test" when every changed test line is an addition.

| Property of the 90 development tasks | Count |
| --- | --- |
| Test patch adds a new test function | 72 of 90 |
| Adds new tests and touches no existing test line | 55 of 90 |
| Also edits an existing test / creates a new test file | 17 / 0 of 90 |
| Report contains "Traceback" (any case: 5) | 1 of 90 |
| Report names an *Error or *Exception class | 10 of 90 |
| Reference fix touches one file / three or more | 65 / 13 of 90 |

*The hidden test always lands in a file that exists at the base commit, but in 72 of 90 tasks the function that grades the fix is new.*

At least 20 of the 90 development tasks are ungradable in the offline sandbox (14 import `inline_snapshot`, 1 `dirty_equals`, 5 grade through `tests/test_requests.py`, which errors at collection); none of the 20 was ever solved, 4 had patches identical or equivalent to the reference (fastapi_14303, requests_6592, requests_7433, requests_6589), the local denominator for rates is 70, and the host states that private scoring is unaffected [10].

**Budget.** About 120 hidden tasks must finish inside a 12-hour wall that includes model start-up (366 s on our first run, 4 L4 GPUs) and grading. We set 5 minutes, 28 tool calls, 24 turns and a 150-second command timeout per task.

## 3. Method

We bet that an agent with no test to run should write its own, so we split the work between two Gemma 4 E4B instances. The **analyzer** is a read-only sub-agent (shell, file read, code-graph tools) with 12 tool calls and no conversation history: it greps the package for identifiers in the report, writes and runs `/tmp/repro.py`, and answers with a seven-section **brief** whose `CODE` section quotes the code and whose `EDIT_SITES` section gives an exact `old_string` per site. The **coder** calls the analyzer once, applies the top edit with `edit_file`, re-runs the check, repairs at most twice, runs the module's tests and always submits. The analyzer runs with `include_contents: none`, the harness setting that hides the conversation so far from a sub-agent; the repository layout is given only in the first user message, so the analyzer never sees it.

Sampling: temperature 0.2, top_p 0.9, top_k 40, seed 7; 6,144 output tokens and a 2,048-token thinking budget from p03 on (8,192 and 3,072 before). The comparison is the official sample agent (`variants/sample-e4b`): its `agent.yaml` includes `code_analyzer` as an optional agent tool, so we call the s-runs "analyzer as an optional tool"; its `sampling.yaml` reserves 16,384 output tokens.

## 4. Results

No configuration left the band of 3 to 8 solved tasks out of 90. p-runs are the two-agent design, s-runs the official sample prompt.

| Run | Change | Resolved of 90 |
| --- | --- | --- |
| p00-base | spec prompts, 8,192 / 3,072 tokens | 4 |
| p01, p01b | analyzer writes a repro; p01b is p01 unchanged | 7, 5 |
| p03, p03b, p03c | 6,144 / 2,048 tokens; three identical runs | 7, 7, 8 |
| p07 | anchors only from `read_file`, never resend a failed anchor | 3 |
| p09 | p07 plus a public prompt recipe | 4 |
| s01 | sample prompt, sample budget (1 min, 10 calls) | 5 |
| s02 | sample prompt, our budget (5 min, 28 calls) | 8 |
| s03, s04 | s02 plus edit rules; s04 adds a prompt recipe | 8, 8 |

![Resolved tasks per run](figures/fig1_runs.png)

*Figure 1. Resolved tasks for every full run (of 90), two held-out runs (of 39) and three 20-task smokes.*

The headline score: the best local run solved 8 of 90 (8 of the 70 gradable tasks); on the public leaderboard of 58 hidden tasks p03 scored 0.06 (4 of 58), s01 0.03 (2 of 58) and s04 0.03 (2 of 58). s02, s03 and s04 each scored 8 and the three p03 repeats 7, 7 and 8 (Fisher p = 1.0). p07 scored 3 of 90 against the pooled p03 repeats' 22 of 270 (p = 0.15), unproven by the Section 5.1 rule. s03 and s04 carried a broken `split("\n")` example (a raw newline inside the quotes), so they did not carry exactly p07's edit rules.

Unresolved tasks fall into three buckets: wrong fix (patch applied, graded tests fail), target still failing (patch applied, other tests pass, graded test fails) and no patch (empty diff).

| Run | resolved | wrong fix | target still failing | no patch |
| --- | --- | --- | --- | --- |
| p00-base | 4 | 41 | 27 | 18 |
| p03 | 7 | 37 | 27 | 19 |
| p07 | 3 | 46 | 28 | 13 |
| s02, s03 | 8, 8 | 44, 43 | 28, 23 | 10, 16 |
| s04 | 8 | 47 | 28 | 7 |

![Failure buckets per run](figures/fig3_funnel.png)

*Figure 2. The same three buckets in every run; the no-patch share moves, the resolved share does not.*

The one-minute sample budget (s01) left 49 of 90 tasks with no patch against 10 of 90 under our budget (s02; p = 5e-10) and resolved 5 against 8 (p = 0.57).

## 5. Analysis

### 5.1 The noise floor

At 7 solved of 90 (p about 0.08) the binomial standard deviation of one run is 2.4 tasks, so the 95% interval around one run spans about 4.7 tasks either way. Temperature 0.2 and a fixed seed do not remove the variance: four tasks share one vLLM instance.

Identical configurations repeated: p01 and p01b scored 7 and 5 and disagreed on 8 tasks (McNemar p = 0.73); the p03 trio scored 7, 7 and 8. Solve stability S, the tasks solved in every run over the tasks solved in any, was 1/13 over the first 5 runs, 2/14 over the 3 p03 repeats and 1/14 over 8 runs. Only 14 of 90 tasks were ever solved in 8 runs; the 3 p03 repeats alone reached all 14.

![Per-task solve matrix](figures/fig4_consistency.png)

*Figure 3. Times solved per task across 8 two-agent runs: 14 of 90 ever solved, 9 in three or more runs, 1 in all eight.*

Rule: state a difference as two counts with a p-value, and treat anything inside the repeat spread (5 to 8 of 90) as unproven. The leaderboard applied it for us: local 8 (s04) versus 7 (p03) became hidden 2 versus 4 of 58.

### 5.2 Where edit anchors come from

`scripts/edit_decode.py` reads the traces of p03b, p03c, p05 and held-out p03 (309 tasks). The coder called `edit_file` 658 times: 350 landed, 308 failed, the failures being 243 "old_string not found", 26 "occurs N times", 21 wrong path, 8 budget and 10 other. For the 243 the script asks where the anchor text had appeared before, counting only what the coder itself had seen (the analyzer's own tool output is invisible to it): 92 were verbatim in the brief (88 exact, 4 differing only in whitespace), 29 in a file window the coder had read, 12 in the coder's own earlier text, 7 only in analyzer output the coder never saw, 2 in shell or search output, and 101 in nothing the coder had read. `read_file` output carries no line-number prefixes, so the match is a plain substring. Landing rate by anchor length over all 658 calls: 1 line 39 of 89 (44%), 2 to 8 lines 243 of 410 (59%), 9 or more lines 68 of 159 (43%).

The brief's `CODE` section is the analyzer's paraphrase, and the design relies on it as the anchor source: 92 of 243 missing anchors came from it verbatim and 101 from memory. The analyzer wrote 33 of 309 briefs without any tool call; 5 of those tasks still resolved (15% against 8%, p = 0.19), so a brief from memory is not a failure mechanism.

### 5.3 What landed edits became

Landing rates: p03 350 of 658 (53%), p07 93 of 172 (54%), s03 119 of 169 (70%), s04 151 of 239 (63%). The buckets show where the extra landed edits went: from p03 to s04, no-patch fell from 19 to 7 of 90 and wrong-fix rose from 37 to 47, while resolved stayed at 7 to 8. Zha found the same shape at 31B [7]. Each s-run is one run, so this is a bucket-level observation; the per-task files for s01 to s04 are in `results/`.

### 5.4 The output reservation

The window is 32,768 tokens, so reserved output sets a hard prompt ceiling: 32,768 minus 8,192 is 24,576, and the run log shows the rejection at exactly 24,577 input tokens. Counted in the run log, context-window overflows went from 12 of 90 tasks (p01b, 8,192 reserved) to 0 of 90 (p03, 6,144; p = 0.0003); turn-cap hits went 8 to 4 (p = 0.37, unproven) and timeouts stayed at 8. The official sample reserves 16,384 output tokens, a 16,384-token prompt ceiling.

![Ungradable tasks](figures/fig5_sandbox.png)

*Figure 4. The 20 of 90 development tasks the offline sandbox never grades, with the 4 whose patch matched the reference marked.*

## 6. What to do differently

Three rules follow from the counts above.

1. **Repeat before you compare.** Run the unchanged configuration at least twice (our repeats spanned 5 to 7 and 7 to 8 of 90) and treat anything inside that spread as unproven.
2. **Reserve less output.** In a 32,768-token window, 6,144 reserved tokens removed all 12 overflows counted at 8,192.
3. **Count landed edits and wrong fixes together.** A rule that raises the landing rate can move tasks from no-patch to wrong-fix and leave resolved unchanged; report all three buckets.

## 7. What we wrote down before the runs, and what happened

Before the repeats ran we wrote (commit a0fa0c9, 2026-11-05) that p03 repeats outside 5 to 7 would mean the noise floor was an artifact of one pair of runs; the third repeat scored 8, one task outside, and the pooled spread of identical configurations is 5 to 8. We also wrote that a traceback-anchored baseline matching reproduce-first over repeated runs would void the redesign; the baseline we could afford was the official sample prompt, run once (8 of 90), which matched, so the design claim falls on weaker evidence than we specified.

## 8. Limitations

Ninety public tasks in three repositories, one to three runs per configuration, one model, one harness. The bucket shift in Section 5.3 compares single runs of different prompts. The anchor decode covers four two-agent runs and does not judge whether a landed edit was the right edit. A 12-task probe of Gemma 4 12B at the 8,192 / 3,072 budget ended every task on a limit. Held-out 5 of 39 and leaderboard 4 of 58 are consistent with the development rate.

## 9. Related work

The format is SWE-bench's [1]. SWE-agent [2] showed that the tool interface shapes success; Agentless [3] made reproduction tests a ranking signal for strong models. "On Randomness in Agentic Evals" [4] reports single-run pass@1 moving 2.2 to 6.0 points between identical runs on SWE-bench Verified. Sweep [5] found 77% of `str_replace` failures were text not in the file; our 243 of 308 (79%) replicates that on E4B and adds the source split. Toeda's pre-registered study [6] (3 sizes, 2 scaffolds, 5 seeds) is the best-powered E4B result we know of. Zha [7] found no loop-breaking lever moved resolution at 31B (71, 73 and 72 of 218). Gluzdov [8] reports E4B editing the wrong file in 13 of 31 tasks; Thakur [9] reports one 31B configuration scoring 55 then 48. New here is the count of the task condition itself: nobody we read counted whether the grading test pre-exists.

## 10. Reproducibility

Code, prompts, configs, the experiment log and per-task files are at [github.com/satyarthshukla500/hidden-test-agent-kit](https://github.com/satyarthshukla500/hidden-test-agent-kit) (MIT). Runs are versions of the Kaggle notebook [voidwalkers123/getting-started-gemma-4-developer-agent](https://www.kaggle.com/code/voidwalkers123/getting-started-gemma-4-developer-agent); the traces behind Section 5.2 are in the Kaggle dataset `voidwalkers123/gemma-agent-results-night2`. Scripts (Python 3.10, standard library; matplotlib for figures): `make_splits.py`, `task_properties.py`, `buckets.py`, `noise_floor.py`, `edit_decode.py`, `make_figures.py`. Per-task bucket files exist for every run in the tables (p00-base, p01, p01b, p02, p03, p03b, p03c, p05, p06, p07, p09, s01 to s04, both held-out runs and the three 20-task smokes); notebook versions and commands, see EXPERIMENTS.md.

## References

1. C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, K. Narasimhan. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024. https://arxiv.org/abs/2310.06770
2. J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, O. Press. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. NeurIPS 2024. https://arxiv.org/abs/2405.15793
3. C. S. Xia, Y. Deng, S. Dunn, L. Zhang. Agentless: Demystifying LLM-based Software Engineering Agents. arXiv:2407.01489, 2024. https://arxiv.org/abs/2407.01489
4. On Randomness in Agentic Evals. arXiv:2602.07150, 2026. https://arxiv.org/abs/2602.07150
5. Sweep. Lessons from building a coding agent for JetBrains. https://blog.sweep.dev/posts/jetbrains-coding-agent
6. T. Toeda. Scaffolding Helps the Smallest Gemma 4 Agent, Not the Larger Ones. Zenodo, 2026. https://zenodo.org/records/23834104
7. J. Zha. When Coding Agents Repeat: Persistence, Selection, and the Limits of Loop Breaking. 2026. https://github.com/usp787/Gemma4_paper_track
8. D. Gluzdov. 31B vs 12B vs E4B with the same agent files. Kaggle discussion, 2026. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/750974
9. A. Thakur. Gemma 4 agent experiments: sampling, thinking, time limits, and tool ablations. Kaggle discussion, 2026. https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/746250
10. J. Wold. 27 fastapi tasks that fail at collection in the provided sandbox (host reply: private scoring excludes these tasks). Kaggle discussion, 2026. https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/discussion/753370
