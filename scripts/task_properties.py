#!/usr/bin/env python3
"""Measure the hidden-test condition on any SWE-bench-format task file.

For each task: does the grading test patch add a new test function (a +def test_ line and no -def test_ line, so the graded
test does not exist before the fix)? Does the issue text carry a traceback or a code
block? How many files does the reference fix touch? Standard library only.

  python scripts/task_properties.py data/tasks.jsonl --split data/splits/dev.txt
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ADD = re.compile(r"^\+[ \t]*(?:async[ \t]+)?def (test_\w+)", re.M)
DEL = re.compile(r"^-[ \t]*(?:async[ \t]+)?def (test_\w+)", re.M)
FILES = re.compile(r"^\+\+\+ b/(\S+)", re.M)
# a test file created by the patch: "--- /dev/null", or a file whose first hunk starts from line 0 ("@@ -0,0")
NEWFILE = re.compile(r"^--- /dev/null|^\+\+\+ b/\S+\n@@ -0,0 ", re.M)
# a removed, non-blank line inside a test file: the grading patch edits a test that exists
REMOVED = re.compile(r"^-(?!--)[ \t]*\S", re.M)
ERRNAME = re.compile(r"\b[A-Z]\w+(?:Error|Exception)\b")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("--split", help="file of instance ids to keep")
    a = ap.parse_args()

    recs = [json.loads(l) for l in Path(a.tasks).read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.split:
        keep = set(Path(a.split).read_text().split())
        recs = [r for r in recs if r["instance_id"] in keep]
    n = len(recs)
    # counting rule: "adds a new test function" = the test patch has a "+def test_" line and no "-def test_" line
    adds_new = [r for r in recs if ADD.search(r["test_patch"]) and not DEL.search(r["test_patch"])]
    new_only = len(adds_new)
    # of those, how many also remove an existing non-blank line (edit a test that already exists)?
    also_edits = sum(1 for r in adds_new if REMOVED.search(r["test_patch"]))
    new_file = sum(1 for r in recs if NEWFILE.search(r["test_patch"]))
    tb = sum(1 for r in recs if "Traceback" in r["problem_statement"])
    tb_ci = sum(1 for r in recs if "traceback" in r["problem_statement"].lower())
    errname = sum(1 for r in recs if ERRNAME.search(r["problem_statement"]))
    code = sum(1 for r in recs if "```" in r["problem_statement"])
    nfiles = [len(set(FILES.findall(r["patch"]))) for r in recs]
    one = sum(1 for k in nfiles if k == 1)
    three = sum(1 for k in nfiles if k >= 3)
    lens = sorted(len(r["problem_statement"]) for r in recs)
    rows = [("grading test patch adds a new test function", new_only),
            ("  ... and touches no existing test line", new_only - also_edits),
            ("  ... and also edits an existing test", also_edits),
            ("grading test patch creates a new test file", new_file),
            ("bug report contains 'Traceback' (case-sensitive)", tb),
            ("bug report mentions a traceback (any case)", tb_ci),
            ("bug report names an *Error/*Exception", errname),
            ("bug report contains a code block", code),
            ("reference fix touches one file", one),
            ("reference fix touches three or more files", three)]
    print(f"{n} tasks, median report length {lens[n // 2]} chars")
    for label, k in rows:
        print(f"  {label:50} {k:4}  {k / n:5.0%}")


if __name__ == "__main__":
    main()
