#!/usr/bin/env python3
"""Where did a failed edit_file anchor come from?

Reads ATIF traces (trace_<id>.json) under one or more results folders and, for every
edit_file call made by the main agent, records whether it landed and, when the error
was "old_string not found", where the anchor text had appeared before: in the analyzer
brief, in a read_file window, in a shell or search output, in the coder's own earlier
text, only in analyzer tool output the coder never saw, or nowhere. Writes edits.csv and prints a summary. Standard library only.

  python scripts/edit_decode.py results/p03b results/p03c results/p05 results/heldout-p03
  (on Kaggle: python edit_decode.py /kaggle/input/<notebook-output>/results/*)

Matching order for a missing anchor: read_file first (the text was in a file window the
model had seen), then brief, shell, search, the coder's own text, analyzer-only output;
a hit in an earlier source wins. Whitespace
is normalised (runs of spaces/tabs collapse, CRLF dropped) in a second pass.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PREFIX = re.compile(r"^\s*\d+[:|]\s?", re.M)  # defensive: read_file content carries no prefixes in this harness
SOURCES = ["read_file", "brief", "shell", "search", "self", "analyzer_tool", "other"]


def raw_content(step: dict) -> str:
    o = step.get("observation") or {}
    c = o.get("content") if isinstance(o, dict) else o
    return c if isinstance(c, str) else json.dumps(c or "")


def decode(c: str):
    """Human text inside a tool observation (JSON strings unescaped), plus the parsed dict."""
    try:
        d = json.loads(c)
    except Exception:
        return c, None
    out: list[str] = []

    def walk(v):
        if isinstance(v, str):
            if v.startswith("{") and '"' in v[:3]:
                try:
                    walk(json.loads(v))
                    return
                except Exception:
                    pass
            out.append(v)
        elif isinstance(v, dict):
            for vv in v.values():
                walk(vv)
        elif isinstance(v, list):
            for vv in v:
                walk(vv)

    walk(d)
    return "\n".join(out), (d if isinstance(d, dict) else None)


def norm_ws(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s.replace("\r", "")).strip()


def source_of(tool: str) -> str:
    if tool == "read_file":
        return "read_file"
    if tool == "code_analyzer":
        return "brief"
    if tool == "run_command":
        return "shell"
    if tool in ("search_similar_code", "get_code_neighbors", "get_code_subgraph"):
        return "search"
    return "other"


def locate(old: str, seen: dict[str, str]) -> str:
    for src in SOURCES:
        if old in seen[src]:
            return src
    n = norm_ws(old)
    for src in SOURCES:
        if n in norm_ws(seen[src]):
            return src + "_ws"
    return "none"


def main(argv: list[str]) -> None:
    roots = [Path(a) for a in argv] or [Path("results")]
    traces = sorted(p for r in roots for p in r.rglob("trace_*.json"))
    if not traces:
        sys.exit("no trace_*.json under " + ", ".join(map(str, roots)))
    rows: list[dict] = []
    tasks: list[dict] = []
    for p in traces:
        tid = p.name[len("trace_"):-5]
        run = p.parent.parent.name if p.parent.name == "traces" else p.parent.name
        try:
            steps = json.loads(p.read_text(errors="replace")).get("steps", [])
        except Exception:
            continue
        seen = {s: "" for s in SOURCES}
        an_calls = 0
        last_failed_anchor = None  # sha1 of the previous failed edit's old_string in this task
        for s in steps:
            text, od = decode(raw_content(s))
            calls = s.get("tool_calls") or []
            tools = [tc.get("function_name") or "?" for tc in calls]
            authors = [str((tc.get("extra") or {}).get("author") or "") for tc in calls]
            an_calls += sum(1 for a in authors if a == "code_analyzer")
            for tc, tool, author in zip(calls, tools, authors):
                if tool != "edit_file" or author == "code_analyzer":
                    continue
                args = tc.get("arguments") or {}
                old = str(args.get("old_string") or "")
                ok = bool(od) and od.get("status") == "ok"
                em = (od or {}).get("error_message", "") if od else text[:80]
                kind = ("ok" if ok else "not_found" if "not found. Ensure" in em
                        else "multiple" if ("ultiple" in em or "occurs" in em)
                        else "identical" if "identical" in em
                        else "bad_args" if "mandatory input parameters" in em
                        else "no_such_file" if "not found in sandbox" in em
                        else "budget" if "udget" in em else "other:" + em[:40])
                origin = locate(old, seen) if kind == "not_found" and old.strip() else ("" if ok else "n/a")
                h = hashlib.sha1(old.encode("utf-8", "replace")).hexdigest()[:10]
                resend = int(not ok and last_failed_anchor == h)  # same anchor as the previous failed edit
                rows.append({"run": run, "task": tid, "lines": old.count("\n") + 1, "result": kind,
                             "origin": origin, "file": str(args.get("filepath") or ""),
                             "anchor": h, "resend": resend})
                last_failed_anchor = None if ok else h
            # what the coder could have seen after this step. Steps authored by the analyzer
            # sub-agent are invisible to the coder except its final answer, the brief.
            step_author = str((s.get("extra") or {}).get("author") or "")
            msg = s.get("message") if isinstance(s.get("message"), str) else ""
            if step_author == "code_analyzer":
                src = "analyzer_tool" if tools else "brief"
                blob = (text or "") + "\n" + (msg or "")
            else:
                src = source_of(tools[0]) if tools else "self"
                blob = (text or "") if tools else (msg or "")
            if blob.strip():
                seen[src] += "\n" + blob
        mine = [r for r in rows if r["run"] == run and r["task"] == tid]
        tasks.append({"run": run, "task": tid, "analyzer_tool_calls": an_calls,
                      "edit_calls": len(mine), "landed": sum(r["result"] == "ok" for r in mine),
                      "distinct_anchors": len({r["anchor"] for r in mine})})
    with Path("tasks.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["run", "task", "analyzer_tool_calls", "edit_calls", "landed", "distinct_anchors"])
        w.writeheader()
        w.writerows(tasks)
    print("tasks", len(tasks), "| analyzer made no tool call in",
          sum(t["analyzer_tool_calls"] == 0 for t in tasks), "tasks |",
          "resends among failed edits:", sum(r["resend"] for r in rows),
          "| distinct anchors:", len({(r["run"], r["task"], r["anchor"]) for r in rows}),
          "| distinct missing anchors:", len({(r["run"], r["task"], r["anchor"]) for r in rows if r["result"] == "not_found"}))
    out = Path("edits.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    res = Counter(r["result"] for r in rows)
    print(f"edit_file calls {len(rows)} in {len(traces)} traces:", dict(res))
    nf = [r for r in rows if r["result"] == "not_found"]
    print(f"not_found {len(nf)} by origin:", dict(Counter(r["origin"] for r in nf).most_common()))
    by = defaultdict(lambda: [0, 0])
    for r in rows:
        k = "1" if r["lines"] == 1 else "2-8" if r["lines"] <= 8 else "9+"
        by[k][r["result"] == "ok"] += 1
    print("landing rate by anchor lines:", {k: f"{v[1]}/{v[0] + v[1]} = {v[1] / (v[0] + v[1]):.0%}" for k, v in sorted(by.items())})
    for r in [r for r in nf if r["origin"] == "none"][:6]:
        print("  none-origin sample:", r["run"], r["task"], r["file"], "lines", r["lines"])
    for run in sorted({r["run"] for r in nf}):
        print("  origin", run, dict(Counter(r["origin"] for r in nf if r["run"] == run).most_common()))
    print("per run:", {run: dict(Counter(r["result"] for r in rows if r["run"] == run)) for run in sorted({r["run"] for r in rows})})
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1:])
