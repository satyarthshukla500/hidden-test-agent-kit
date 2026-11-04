#!/usr/bin/env python3
"""Print one task's trajectory compactly for review.

  python scripts/review.py p00-base <instance_id>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LIMIT = 700


def main() -> None:
    tag, tid = sys.argv[1], sys.argv[2]
    base = Path("results") / tag
    trace = base / "traces" / f"trace_{tid}.json"
    if trace.exists():
        for step in json.loads(trace.read_text()).get("steps", []):
            for part in step.get("parts", []):
                kind = part.get("kind") or ("thought" if part.get("thought") else "text")
                body = (part.get("text") or json.dumps(part.get("tool_call", {})))[:LIMIT]
                print(f"[{kind}] {body}\n")
    patch = base / "patches" / f"{tid}.patch"
    print("=== PATCH ===")
    print(patch.read_text()[:3000] if patch.exists() else "(none)")
    log = base / "test_outputs" / f"{tid}.log"
    print("\n=== TEST TAIL ===")
    print(log.read_text()[-2000:] if log.exists() else "(none)")


if __name__ == "__main__":
    main()
