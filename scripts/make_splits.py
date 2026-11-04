#!/usr/bin/env python3
"""Deterministic 90/39 dev-heldout split, stratified by repo."""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

SEED = 1234
HELDOUT_FRAC = 0.3


def main() -> None:
    tasks = Path("data/tasks.jsonl")
    recs = [json.loads(l) for l in tasks.read_text().splitlines() if l.strip()]
    by_repo = defaultdict(list)
    for r in recs:
        by_repo[r.get("repo", "?")].append(r["instance_id"])

    rng = random.Random(SEED)
    dev, held = [], []
    for repo, ids in sorted(by_repo.items()):
        ids = sorted(ids)
        rng.shuffle(ids)
        n = max(1, round(len(ids) * HELDOUT_FRAC))
        held += ids[:n]
        dev += ids[n:]

    Path("data/splits").mkdir(parents=True, exist_ok=True)
    Path("data/splits/dev.txt").write_text("\n".join(sorted(dev)) + "\n")
    Path("data/splits/heldout.txt").write_text("\n".join(sorted(held)) + "\n")
    print(f"dev {len(dev)}  heldout {len(held)}  over {len(by_repo)} repos")


if __name__ == "__main__":
    main()
