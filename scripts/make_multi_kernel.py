#!/usr/bin/env python3
"""One Kaggle session, several evaluation jobs, one vLLM start-up.

Reuses make_kernel.TEMPLATE: the set-up and vLLM part runs once, the evaluation
and report part runs once per job with its own submission, task list and tag.
All jobs must declare the same model.

  python scripts/make_multi_kernel.py --user U --name night2 \
      --job p03b=dist/p03.zip:dev --job p03c=dist/p03.zip:dev \
      --job p05=dist/p05.zip:dev --job heldout-p03=dist/p03.zip:heldout
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from make_kernel import MODELS, TEMPLATE

RANK_PATCH = (
    "    calls = TOOLS_RE.findall(blob)\n",
    "    calls = TOOLS_RE.findall(blob)\n"
    "    used = re.findall(r'RANK_USED[ :=]+(1|2|fallback)\\b', blob)\n",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--name", required=True, help="output folder and tag prefix")
    ap.add_argument("--model", choices=MODELS, default="e4b")
    ap.add_argument("--job", action="append", required=True,
                    help="tag=zip_path:split  (split = dev | heldout | comma-separated ids)")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--accelerator", default="NvidiaL4X4")
    a = ap.parse_args()

    jobs = []
    for spec in a.job:
        tag, rest = spec.split("=", 1)
        zpath, split = rest.rsplit(":", 1)
        sp = Path(f"data/splits/{split}.txt")
        ids = sp.read_text().split() if sp.exists() else split.split(",")
        jobs.append({"tag": tag, "ids": ids,
                     "zip": base64.b64encode(Path(zpath).read_bytes()).decode()})

    head, tail = TEMPLATE.split("# 4. Evaluate.", 1)
    tail = "# 4. Evaluate.\n" + tail
    assert "if server is not None:\n    server.stop()\n" in tail
    tail = tail.replace("if server is not None:\n    server.stop()\n", "")
    assert RANK_PATCH[0] in tail
    tail = tail.replace(*RANK_PATCH)
    tail = tail.replace("'submitted': 'submit_patch' in blob})",
                        "'submitted': 'submit_patch' in blob, 'rank': used[-1] if used else None})")
    tail += ("\nfrom collections import Counter as _C\n"
             "print('RANKS ' + json.dumps({'all': dict(_C(r['rank'] for r in brows)), "
             "'resolved': dict(_C(r['rank'] for r in brows if r['bucket'] == 'resolved'))}))\n")

    first = jobs[0]
    all_ids = sorted({i for j in jobs for i in j["ids"]})
    src = (head.replace("__TAG__", repr(a.name))
           .replace("__MODEL__", repr(MODELS[a.model]))
           .replace("__TASK_IDS__", repr(all_ids))
           .replace("__SKIP__", "False")
           .replace("__CONC__", repr(a.concurrency))
           .replace("__ZIP__", repr(first["zip"])))
    src += (
        "\nJOBS = " + json.dumps([{k: j[k] for k in ("tag", "ids", "zip")} for j in jobs]) + "\n"
        "TAIL_SRC = " + repr(tail) + "\n"
        "ALL_TASKS = tasks\n"
        "for _job in JOBS:\n"
        "    TAG = _job['tag']\n"
        "    OUT = WORK / 'results' / TAG\n"
        "    OUT.mkdir(parents=True, exist_ok=True)\n"
        "    AGENT_DIR = WORK / f'submission_{TAG}'\n"
        "    shutil.rmtree(AGENT_DIR, ignore_errors=True)\n"
        "    zipfile.ZipFile(io.BytesIO(base64.b64decode(_job['zip']))).extractall(AGENT_DIR)\n"
        "    validate_directory(AGENT_DIR, limits=limits)\n"
        "    _keep = set(_job['ids'])\n"
        "    tasks = [t for t in ALL_TASKS if t.instance_id in _keep]\n"
        "    print(f'\\n##### JOB {TAG}: {len(tasks)} tasks', flush=True)\n"
        "    try:\n"
        "        exec(TAIL_SRC, globals())\n"
        "    except Exception as _e:\n"
        "        print(f'JOB {TAG} FAILED: {type(_e).__name__}: {_e}', flush=True)\n"
        "if server is not None:\n"
        "    server.stop()\n"
    )
    out = Path("kaggle") / a.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.py").write_text(src, encoding="utf-8")
    nb = {"cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                     "source": src.splitlines(True)}],
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
          "nbformat": 4, "nbformat_minor": 5}
    (out / f"gemma-agent-{a.name}.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    print(f"wrote {out}: jobs {[(j['tag'], len(j['ids'])) for j in jobs]}, {len(src)} chars")


if __name__ == "__main__":
    main()
