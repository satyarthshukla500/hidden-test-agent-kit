#!/usr/bin/env python3
"""Run a split and bucket every failure by phase.

Each bucket maps to one prompt section you can change:
  no_patch         -> coder stop conditions and submit discipline
  apply_failed     -> edit_file old_string quality in the analyzer brief
  wrong_fix        -> diagnosis and edit-site ranking
  regression       -> the regression gate step
  timeout          -> budget caps, per-call cost
  budget_exhausted -> phase call caps
  agent_error      -> tool misuse, hallucinated tools

  python scripts/score.py --split dev --tag p07
  python scripts/score.py --compare p06 p07
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

BUCKETS = ["resolved", "no_patch", "apply_failed", "wrong_fix", "regression",
           "timeout", "budget_exhausted", "agent_error"]
MAX_CALLS = 28


def load_ids(split: str, tasks: Path) -> list[str]:
    ids = [json.loads(l)["instance_id"] for l in tasks.read_text().splitlines() if l.strip()]
    sp = Path(f"data/splits/{split}.txt")
    if sp.exists():
        keep = set(sp.read_text().split())
        ids = [i for i in ids if i in keep]
    return ids


def classify(rec: dict, out: Path) -> str:
    tid = rec["instance_id"]
    if rec.get("resolved"):
        return "resolved"
    err = " ".join(str(rec.get(k) or "") for k in ("error", "error_message", "status"))
    if "Failed to apply" in err:
        return "apply_failed"
    patch = out / "patches" / f"{tid}.patch"
    if not patch.exists() or not patch.read_text(errors="replace").strip():
        return "no_patch"
    if "Timeout" in err:
        return "timeout"
    if rec.get("tool_calls_used", 0) >= MAX_CALLS:
        return "budget_exhausted"
    if rec.get("agent_error"):
        return "agent_error"
    log = out / "test_outputs" / f"{tid}.log"
    if log.exists() and "FAILED" in log.read_text(errors="replace"):
        return "regression"
    return "wrong_fix"


def run(ids: list[str], tag: str, sub: Path, tasks: Path, snaps: Path, sandbox: str) -> None:
    out = Path("results") / tag
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["swegemma", "eval", "--tasks", str(tasks), "--snapshots-dir", str(snaps),
           "--submission-dir", str(sub), "--results-dir", str(out),
           "--sandbox", sandbox, "--concurrency", "2", "--task-ids", *ids]
    subprocess.run(cmd, check=False)


def summarise(tag: str) -> dict:
    out = Path("results") / tag
    counts: Counter[str] = Counter()
    per_repo: defaultdict[str, Counter[str]] = defaultdict(Counter)
    rows = []
    for line in (out / "task_results.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        b = classify(rec, out)
        counts[b] += 1
        per_repo[rec.get("repo", "?")][b] += 1
        rows.append({"id": rec["instance_id"], "repo": rec.get("repo"),
                     "bucket": b, "calls": rec.get("tool_calls_used")})
    total = sum(counts.values()) or 1
    print(f"\n== {tag}  ({total} tasks)  resolved {counts['resolved']}/{total} "
          f"= {counts['resolved'] / total:.1%}")
    for b in BUCKETS:
        if counts[b]:
            print(f"   {b:18} {counts[b]:4}  {counts[b] / total:5.1%}")
    print("\n   by repo:")
    for repo, c in sorted(per_repo.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"     {repo:24} {dict(c)}")
    (out / "buckets.json").write_text(json.dumps(rows, indent=2))
    return {"counts": dict(counts), "total": total}


def compare(a: str, b: str) -> None:
    sa = json.loads((Path("results") / a / "buckets.json").read_text())
    sb = json.loads((Path("results") / b / "buckets.json").read_text())
    ca = Counter(r["bucket"] for r in sa)
    cb = Counter(r["bucket"] for r in sb)
    print(f"\n{a} -> {b}")
    for k in BUCKETS:
        d = cb[k] - ca[k]
        if d:
            print(f"   {k:18} {ca[k]:4} -> {cb[k]:4}  {d:+d}")
    ra = ca["resolved"] / max(sum(ca.values()), 1)
    rb = cb["resolved"] / max(sum(cb.values()), 1)
    print(f"   RESOLVED {ra:.1%} -> {rb:.1%}  ({rb - ra:+.1%})")
    regressed = ({r["id"] for r in sa if r["bucket"] == "resolved"}
                 - {r["id"] for r in sb if r["bucket"] == "resolved"})
    if regressed:
        print(f"   regressed on {len(regressed)} previously-passing tasks:")
        for t in sorted(regressed):
            print(f"     {t}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--tag")
    ap.add_argument("--sub", default="submission")
    ap.add_argument("--tasks", default="data/tasks.jsonl")
    ap.add_argument("--snapshots", default="data/snapshots")
    ap.add_argument("--sandbox", default="docker")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    a = ap.parse_args()

    if a.compare:
        compare(*a.compare)
        return
    if not a.tag:
        ap.error("--tag required unless --compare")
    ids = load_ids(a.split, Path(a.tasks))
    print(f"running {len(ids)} tasks on split {a.split} as {a.tag}")
    run(ids, a.tag, Path(a.sub), Path(a.tasks), Path(a.snapshots), a.sandbox)
    summarise(a.tag)


if __name__ == "__main__":
    main()
