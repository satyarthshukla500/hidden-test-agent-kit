#!/usr/bin/env python3
"""How many tasks do you need before a solve-rate change means anything?

Standard library only. Two-proportion normal approximation, two-sided test.

  python scripts/noise_floor.py --p 0.078 --n 90
  python scripts/noise_floor.py --p 0.07 --n 90 --target 0.14
  python scripts/noise_floor.py --runs 7 5 --n 90   # spread of repeated identical runs
"""
from __future__ import annotations

import argparse
import math
from statistics import NormalDist

Z = NormalDist()


def single_run(p: float, n: int, alpha: float) -> dict:
    sd = math.sqrt(n * p * (1 - p))
    half = Z.inv_cdf(1 - alpha / 2) * sd
    return {"sd_tasks": sd, "ci_half_width_tasks": half}


def n_per_arm(p1: float, p2: float, alpha: float, power: float) -> float:
    pbar = (p1 + p2) / 2
    za, zb = Z.inv_cdf(1 - alpha / 2), Z.inv_cdf(power)
    num = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return (num / (p2 - p1)) ** 2


def power_at(p1: float, p2: float, n: int, alpha: float) -> float:
    pbar = (p1 + p2) / 2
    za = Z.inv_cdf(1 - alpha / 2)
    se0 = math.sqrt(2 * pbar * (1 - pbar) / n)
    se1 = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n)
    return Z.cdf((abs(p2 - p1) - za * se0) / se1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=float, help="observed solve rate, e.g. 0.078")
    ap.add_argument("--n", type=int, required=True, help="tasks per run")
    ap.add_argument("--target", type=float, help="solve rate you hope to detect")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", type=float, default=0.8)
    ap.add_argument("--runs", type=int, nargs="*", help="resolved counts of repeated identical runs")
    a = ap.parse_args()

    if a.runs:
        lo, hi = min(a.runs), max(a.runs)
        mean = sum(a.runs) / len(a.runs)
        print(f"identical runs: {a.runs}  spread {lo}-{hi} ({hi - lo} tasks)  mean {mean:.2f}/{a.n}")
        a.p = a.p or mean / a.n

    if a.p is None:
        ap.error("--p or --runs required")
    s = single_run(a.p, a.n, a.alpha)
    print(f"p={a.p:.3f} n={a.n}: one run SD = {s['sd_tasks']:.2f} tasks, "
          f"{1 - a.alpha:.0%} interval = +/-{s['ci_half_width_tasks']:.1f} tasks")
    target = a.target or 2 * a.p
    need = n_per_arm(a.p, target, a.alpha, a.power)
    pw = power_at(a.p, target, a.n, a.alpha)
    print(f"to detect {a.p:.3f} -> {target:.3f} at {a.power:.0%} power: {need:.0f} tasks per arm "
          f"({need / a.n:.1f}x your n); power at n={a.n}: {pw:.0%}")


if __name__ == "__main__":
    main()
