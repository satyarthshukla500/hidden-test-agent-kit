# task_table.csv

One row per public task of the Gemma 4 Developer Agent competition (129: 90 dev, 39 held-out). Built by
`python scripts/task_table.py data/tasks.jsonl` from the competition's `tasks.jsonl`. Only ids and derived
values are stored, no task text. The label columns come from the task file alone and apply to any
SWE-bench-format file; `split` needs `data/splits/`, and the run columns need this repo's `results/`.

| Column | Rule |
|---|---|
| `instance_id`, `repo` | task id; repo is the id without its number |
| `split` | `dev` or `heldout` from `data/splits/` (seed 1234, by repository) |
| `adds_new_test` | 1 if the grading test patch has a `+def test_` line (or `+async def test_`) and no `-def test_` line. A renamed or replaced test counts as 0 |
| `removes_test_line` | 1 if `adds_new_test` and the test patch also removes any non-blank line (a test, import or fixture). `adds_new_test` with 0 here is the paper's "touches no existing test" |
| `creates_new_test_file` | 1 if the test patch creates a file: `--- /dev/null`, or a first hunk starting at line 0 (`@@ -0,0`) |
| `report_has_traceback` | 1 if the bug report contains `Traceback` (case-sensitive) |
| `report_names_error` | 1 if the report contains a capitalised word ending in `Error` or `Exception` (a heuristic; prose can match) |
| `report_has_code_block` | 1 if the report contains a fenced code block |
| `fix_files` | distinct `+++ b/` paths in the reference fix (deleted files are not counted) |
| `sandbox_blocker` | why the offline sandbox cannot grade the task: `inline_snapshot` or `dirty_equals` (the test patch uses a package missing from the wheel cache) or `tests/test_requests.py` (that file errors at collection); empty if none. Checked in this order, first match shown |
| `our_runs` | how many of our runs covered the task: 15 per dev task (p00-base, p01, p01b, p02, p03, p03b, p03c, p05, p06, p07, p09, s01-s04), 2 per held-out task (heldout-p03, heldout-p07) |
| `our_runs_resolved` | how many of those runs solved it |

Caveats. The test labels use the patch text, not SWE-bench's FAIL_TO_PASS lists. The run columns come from one
model (Gemma 4 E4B) and one agent family across 15 prompt configurations: 0 of 15 means these agents never
solved it, not that the task is hard in general, and held-out counts (of 2) are not comparable with dev counts
(of 15).

Counts. All 129: 98 add a new test function (77 of them remove no test line), 1 report has a traceback, 29
cannot be graded offline. The 90 dev tasks give the paper's 71, 54, 1 and 20; 34 dev test patches create a test file.

Check. `python scripts/check_task_labels.py data/tasks.jsonl data/snapshots` opens each task's pre-fix repository
snapshot and looks for every test function the grading patch adds. In all 98 tasks labelled `adds_new_test`, none
of those functions is defined in its file before the fix (`results/task_label_check.csv`). Three tasks labelled 0
also have no pre-existing graded function: their patches replace a test, so the patch-only rule is conservative.
