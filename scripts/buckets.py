#!/usr/bin/env python3
"""Failure buckets and run-to-run overlap for SWE-agent runs.

Reads results/<tag>/buckets.json (rows of {id, repo, bucket, calls}) as written by
the Kaggle kernel (scripts/make_kernel.py) or scripts/score.py. Standard library only.

  python scripts/buckets.py p00-base p01 p02 p01b p03        # table + overlap
  python scripts/buckets.py --classify results/<tag>/kernel_results.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

ORDER = ["resolved", "wrong_fix", "regression", "no_patch", "apply_failed",
         "timeout", "budget_exhausted", "agent_error"]


def classify(rec: dict, patch_text: str, max_calls: int = 28) -> str:
    """Same rules as the kernel. 'regression' = test output shows both passed and FAILED."""
    if str(rec.get("resolved")).lower() == "true":
        return "resolved"
    err = " ".join(str(rec.get(k) or "") for k in ("error", "error_message", "status"))
    if "Failed to apply" in err:
        return "apply_failed"
    if not patch_text.strip():
        return "no_patch"
    if "Timeout" in err or "timed out" in err.lower():
        return "timeout"
    if (rec.get("tool_calls_used") or rec.get("tool_calls") or 0) >= max_calls:
        return "budget_exhausted"
    if rec.get("agent_error"):
        return "agent_error"
    out = str(rec.get("test_output") or "")
    if "FAILED" in out and "passed" in out:
        return "regression"
    return "wrong_fix"


def load(tag: str) -> list[dict]:
    return json.loads((Path("results") / tag / "buckets.json").read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tags", nargs="*")
    ap.add_argument("--classify", help="kernel_results.jsonl to bucket (patches/ beside it)")
    a = ap.parse_args()

    if a.classify:
        path = Path(a.classify)
        for line in path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                p = path.parent / "patches" / f"{rec['instance_id']}.patch"
                print(rec["instance_id"], classify(rec, p.read_text() if p.exists() else ""))
        return

    runs = {t: load(t) for t in a.tags}
    print(f"{'run':10}" + "".join(f"{b[:12]:>13}" for b in ORDER))
    for t, rows in runs.items():
        c = Counter(r["bucket"] for r in rows)
        print(f"{t:10}" + "".join(f"{c[b]:>13}" for b in ORDER))
    solved = {t: {r["id"] for r in rows if r["bucket"] == "resolved"} for t, rows in runs.items()}
    union = set().union(*solved.values()) if solved else set()
    every = set.intersection(*solved.values()) if solved else set()
    print(f"\nsolved at least once: {len(union)}   solved in every run: {len(every)} {sorted(every)}")
    for x, y in combinations(solved, 2):
        both, either = solved[x] & solved[y], solved[x] | solved[y]
        print(f"  {x} vs {y}: both {len(both)} of {len(either)} solved by either")


if __name__ == "__main__":
    main()
