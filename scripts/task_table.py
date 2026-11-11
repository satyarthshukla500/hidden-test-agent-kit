#!/usr/bin/env python3
"""Per-task table of the hidden-test condition for a SWE-bench-format task file.

One row per task: does the grading test patch add a new test function, does it also edit an existing
test, does it create a new test file, what the bug report carries (traceback, named error, code block),
how many files the reference fix touches, and whether the offline sandbox can grade it. The rules are
those of task_properties.py; only ids and derived values are written, never task text.

  python scripts/task_table.py data/tasks.jsonl --out results/task_table.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ADD = re.compile(r"^\+[ \t]*(?:async[ \t]+)?def (test_\w+)", re.M)
DEL = re.compile(r"^-[ \t]*(?:async[ \t]+)?def (test_\w+)", re.M)
FILES = re.compile(r"^\+\+\+ b/(\S+)", re.M)
# a test file created by the patch: "--- /dev/null", or a file whose first hunk starts from line 0 ("@@ -0,0")
NEWFILE = re.compile(r"^--- /dev/null|^\+\+\+ b/\S+\n@@ -0,0 ", re.M)
REMOVED = re.compile(r"^-(?!--)[ \t]*\S", re.M)
ERRNAME = re.compile(r"\b[A-Z]\w+(?:Error|Exception)\b")
ROOT = Path(__file__).resolve().parent.parent
RUNS = ["p00-base", "p01", "p01b", "p02", "p03", "p03b", "p03c", "p05", "p06", "p07", "p09",
        "s01", "s02", "s03", "s04", "heldout-p03", "heldout-p07"]


def sandbox_blocker(test_patch: str) -> str:
    """Why the offline sandbox cannot grade the task, or '' (same rule as make_figures.ungradable_sets)."""
    if "inline_snapshot" in test_patch:
        return "inline_snapshot"
    if "dirty_equals" in test_patch:
        return "dirty_equals"
    if "tests/test_requests.py" in FILES.findall(test_patch):
        return "tests/test_requests.py"
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("--out", default=str(ROOT / "results" / "task_table.csv"))
    ap.add_argument("--splits", default=str(ROOT / "data" / "splits"), help="folder with dev.txt and heldout.txt")
    a = ap.parse_args()

    split = {}
    for name in ("dev", "heldout"):
        p = Path(a.splits) / f"{name}.txt"
        if p.exists():
            split.update({i: name for i in p.read_text().split()})
    recs = [json.loads(l) for l in Path(a.tasks).read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = []
    for r in sorted(recs, key=lambda r: r["instance_id"]):
        tp, ps = r["test_patch"], r["problem_statement"]
        adds = bool(ADD.search(tp)) and not DEL.search(tp)
        rows.append({
            "instance_id": r["instance_id"],
            "repo": r["instance_id"].rsplit("_", 1)[0],
            "split": split.get(r["instance_id"], ""),
            "adds_new_test": int(adds),
            "removes_test_line": int(adds and bool(REMOVED.search(tp))),
            "creates_new_test_file": int(bool(NEWFILE.search(tp))),
            "report_has_traceback": int("Traceback" in ps),
            "report_names_error": int(bool(ERRNAME.search(ps))),
            "report_has_code_block": int("```" in ps),
            "fix_files": len(set(FILES.findall(r["patch"]))),
            "sandbox_blocker": sandbox_blocker(tp),
        })
    # how many of our runs covered and solved each task: the 15 full dev runs and the 2 held-out runs
    # (one model, Gemma 4 E4B, one agent family); smokes are left out
    runs, solved = {}, {}
    for run in RUNS:
        b = ROOT / "results" / run / "buckets.json"
        if not b.exists():
            print("missing", b, "- run columns left at 0")
            continue
        for x in json.loads(b.read_text(encoding="utf-8")):
            runs[x["id"]] = runs.get(x["id"], 0) + 1
            solved[x["id"]] = solved.get(x["id"], 0) + (x["bucket"] == "resolved")
    for row in rows:
        row["our_runs"] = runs.get(row["instance_id"], 0)
        row["our_runs_resolved"] = solved.get(row["instance_id"], 0)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    dev = [x for x in rows if x["split"] == "dev"]
    for label, sub in (("all", rows), ("dev", dev)):
        n = len(sub)
        new = sum(x["adds_new_test"] for x in sub)
        print(f"{label}: {n} tasks, adds new test {new}, of those touches no existing test "
              f"{new - sum(x['removes_test_line'] for x in sub)}, traceback {sum(x['report_has_traceback'] for x in sub)}, "
              f"sandbox-blocked {sum(1 for x in sub if x['sandbox_blocker'])}")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
