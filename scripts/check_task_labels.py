#!/usr/bin/env python3
"""Check the adds_new_test label of results/task_table.csv against each task's pre-fix repository.

For every task, open data/snapshots/<id>.tgz (the repository at the pre-fix commit), read the test files the
grading test patch touches, and ask: do the test functions the patch adds already exist there? A task is
"graded test absent before the fix" when none of the added test function names is defined in the pre-fix
version of its file. Writes results/task_label_check.csv and prints the agreement with the patch-only label.

  python scripts/check_task_labels.py data/tasks.jsonl data/snapshots
"""
from __future__ import annotations

import csv
import json
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUS_FILE = re.compile(r"^\+\+\+ b/(\S+)", re.M)
ADD = re.compile(r"^\+[ \t]*(?:async[ \t]+)?def (test_\w+)", re.M)


def added_tests_by_file(test_patch: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    parts = re.split(r"(?m)^(?=--- (?:a/|/dev/null))", test_patch)
    for part in parts:
        m = PLUS_FILE.search(part)
        if not m:
            continue
        names = set(ADD.findall(part))
        if names:
            out.setdefault(m.group(1), set()).update(names)
    return out


def base_files(tgz: Path, wanted: set[str]) -> dict[str, str | None]:
    """Contents of the wanted repo-relative paths in the snapshot (None if absent)."""
    found: dict[str, str | None] = {w: None for w in wanted}
    with tarfile.open(tgz, "r:gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            name = m.name.lstrip("./")
            for w in wanted:
                if found[w] is None and (name == w or name.endswith("/" + w)):
                    f = tf.extractfile(m)
                    found[w] = f.read().decode("utf-8", "replace") if f else ""
            if all(v is not None for v in found.values()):
                break
    return found


def main() -> None:
    tasks_path, snap_dir = Path(sys.argv[1]), Path(sys.argv[2])
    table = {r["instance_id"]: r for r in csv.DictReader(open(ROOT / "results" / "task_table.csv", encoding="utf-8"))}
    recs = [json.loads(l) for l in tasks_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = []
    for i, r in enumerate(sorted(recs, key=lambda r: r["instance_id"])):
        tid = r["instance_id"]
        by_file = added_tests_by_file(r["test_patch"])
        files = base_files(snap_dir / f"{tid}.tgz", set(by_file)) if by_file else {}
        added = sum(len(v) for v in by_file.values())
        preexisting = sorted(f"{p}::{n}" for p, names in by_file.items() for n in names
                             if files.get(p) and re.search(rf"^\s*(?:async\s+)?def {n}\b", files[p], re.M))
        absent = int(added > 0 and not preexisting)
        rows.append({"instance_id": tid, "added_test_functions": added,
                     "files_missing_before_fix": sum(1 for v in files.values() if v is None),
                     "added_names_already_defined": ";".join(preexisting),
                     "graded_test_absent_before_fix": absent,
                     "adds_new_test_label": int(table[tid]["adds_new_test"])})
        print(i + 1, tid, "added", added, "pre-existing", len(preexisting), "label", table[tid]["adds_new_test"], flush=True)
    out = ROOT / "results" / "task_label_check.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    agree = sum(1 for x in rows if x["graded_test_absent_before_fix"] == x["adds_new_test_label"])
    print(f"agreement {agree} of {len(rows)}; label 1 and absent before fix: "
          f"{sum(1 for x in rows if x['adds_new_test_label'] and x['graded_test_absent_before_fix'])} of "
          f"{sum(x['adds_new_test_label'] for x in rows)}; wrote {out}")


if __name__ == "__main__":
    main()
