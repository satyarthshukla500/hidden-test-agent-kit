#!/usr/bin/env python3
"""Writeup card (560 x 280): the one finding and the 15-run strip behind it. Numbers from results/."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RUNS = ["p00-base", "p01", "p01b", "p02", "p03", "p03b", "p03c", "p05", "p06", "p07", "p09", "s01", "s02", "s03", "s04"]
solved = []
for r in RUNS:
    b = json.loads(Path(f"results/{r}/buckets.json").read_text(encoding="utf-8"))
    assert len(b) == 90, r
    solved.append(sum(x["bucket"] == "resolved" for x in b))
assert min(solved) == 3 and max(solved) == 8, solved

BG, FG, DIM, ACC, ACC2 = "#0b1020", "#f3f4f6", "#9aa3b2", "#f5b942", "#3b82f6"
fig = plt.figure(figsize=(5.6, 2.8), dpi=200)
fig.patch.set_facecolor(BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 560); ax.set_ylim(0, 280); ax.axis("off")

# top band
ax.text(28, 250, "No Test to Anchor On", fontsize=19, fontweight="bold", color=FG, ha="left", va="center")
ax.text(28, 222, "What 15 runs of a Gemma 4 E4B bug-fixing agent show: hidden tests, failed edits, noise", fontsize=8.4, color=DIM, ha="left", va="center")

# middle band, left: the hook (this is what the gallery and the thumbnail show)
ax.text(26, 156, "72", fontsize=34, fontweight="bold", color=ACC, ha="left", va="center", family="DejaVu Sans")
ax.text(92, 168, "of 90", fontsize=18, fontweight="bold", color=ACC, ha="left", va="center")
ax.text(92, 143, "tasks hide the test", fontsize=11.5, fontweight="bold", color=FG, ha="left", va="center")
ax.text(26, 114, "the agent would need to run.", fontsize=11.5, fontweight="bold", color=FG, ha="left", va="center")

# middle band, right: 15 runs
x0, x1, y0, k = 300, 532, 112, 8.6
w = (x1 - x0) / len(solved)
ax.add_patch(FancyBboxPatch((x0 - 4, y0 + 3 * k - 2), x1 - x0 + 8, 5 * k + 4, boxstyle="round,pad=0,rounding_size=3",
                            fc="#1a2440", ec="none", alpha=0.9, zorder=1))
for i, s in enumerate(solved):
    col = ACC2 if RUNS[i].startswith("s") else "#8b9bd1"
    ax.add_patch(plt.Rectangle((x0 + i * w + 2, y0), w - 4, s * k, fc=col, ec="none", zorder=2))
ax.text(x0, y0 + 8 * k + 12, "15 runs, 12 designs, all 3 to 8 of 90", fontsize=8.4, color=FG, ha="left", va="center", fontweight="bold")
ax.text(x0, y0 - 11, "resolved of 90 per run; blue = official sample prompt", fontsize=6.6, color=DIM, ha="left", va="center")

# bottom band
ax.text(28, 62, "A Gemma 4 E4B agent has no failing test to run, so the differences between", fontsize=9.5, color=DIM, ha="left", va="center")
ax.text(28, 45, "designs are noise. We measured the condition, the edits and the floor.", fontsize=9.5, color=DIM, ha="left", va="center")
ax.text(28, 20, "Gemma 4 E4B  |  15 runs  |  309 traced tasks  |  code, prompts and per-task results, MIT", fontsize=7.5, color=DIM, ha="left", va="center")

out = Path("assets/card.png"); out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=200, facecolor=BG)
print("wrote", out, solved)
