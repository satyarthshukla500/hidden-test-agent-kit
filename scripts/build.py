#!/usr/bin/env python3
"""Validate and pack a submission zip.

Checks what silently zeroes a submission: missing or duplicated root config,
disallowed extensions, path traversal, size cap, multiple declared models,
unknown placeholders. Rewrites the model alias so one source tree builds both
the E4B run and the 12B run.

  python scripts/build.py --model e4b
  python scripts/build.py --model 12b
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

MODELS = {
    "e4b": "gemma-4-e4b-it-qat-w4a16-ct",
    "e2b": "gemma-4-e2b-it-qat-w4a16-ct",
    "12b": "gemma-4-12b-it-qat-w4a16-ct",
    "31b": "gemma-4-31b-it-qat-w4a16-ct",
}
ALLOWED_EXT = {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
ROOT_NAMES = {"agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml"}
SIZE_CAP = 3 * 1024**3 - 1
PLACEHOLDERS = {"problem_description", "hints", "bug_brief"}
MODEL_RE = re.compile(r"^\s*model:\s*(\S+)\s*$", re.M)


def validate(src: Path) -> bool:
    ok = True
    roots = [p.name for p in src.iterdir() if p.name in ROOT_NAMES]
    if len(roots) != 1:
        print(f"FAIL expected exactly 1 root config, found {roots}")
        ok = False

    total = 0
    models = set()
    for p in sorted(src.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        total += p.stat().st_size
        if p.suffix not in ALLOWED_EXT:
            print(f"FAIL extension not allowed: {rel}")
            ok = False
        if p.suffix in {".yaml", ".yml"}:
            models |= set(MODEL_RE.findall(p.read_text(encoding="utf-8", errors="replace")))
        if p.suffix == ".md":
            body = p.read_text(encoding="utf-8", errors="replace")
            for ph in re.findall(r"\{([a-z_]+)\??\}", body):
                if ph not in PLACEHOLDERS:
                    print(f"FAIL unknown placeholder {{{ph}}} in {rel}")
                    ok = False

    if total > SIZE_CAP:
        print(f"FAIL unpacked size {total} exceeds 3 GiB")
        ok = False
    if len(models) != 1:
        print(f"FAIL exactly one base model required, found {sorted(models)}")
        ok = False
    elif models.pop() not in MODELS.values():
        print("FAIL declared model is not one of the four QAT variants")
        ok = False
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=MODELS, default="e4b")
    ap.add_argument("--src", default="submission")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    src = Path(a.src)
    if not validate(src):
        sys.exit(1)

    out = Path(a.out or f"dist/{a.model}.zip")
    out.parent.mkdir(parents=True, exist_ok=True)
    names = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(src).as_posix()
            if p.suffix in {".yaml", ".yml"}:
                text = MODEL_RE.sub(f"model: {MODELS[a.model]}", p.read_text(encoding="utf-8"))
                z.writestr(rel, text)
            else:
                z.write(p, rel)
            names.append(rel)

    print(f"OK {out} ({out.stat().st_size} bytes, {len(names)} entries)")
    for n in names:
        print(f"   {n}")
    print(f"   model={MODELS[a.model]}")
    print(f"   kaggle competitions submit -c gemma-4-developer-agent -f {out}")


if __name__ == "__main__":
    main()
