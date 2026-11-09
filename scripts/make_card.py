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

ax.text(28, 262, "No Test to Anchor On", fontsize=11, fontweight="bold", color=FG, ha="left", va="center")
ax.text(532, 262, "Gemma 4 E4B  |  15 runs  |  309 traced tasks  |  MIT kit", fontsize=7.5, color=DIM, ha="right", va="center")

ax.text(26, 196, "72", fontsize=46, fontweight="bold", color=ACC, ha="left", va="center", family="DejaVu Sans")
ax.text(126, 208, "of 90 tasks hide the test", fontsize=15, color=FG, ha="left", va="center", fontweight="bold")
ax.text(126, 184, "the agent would need to run.", fontsize=15, color=FG, ha="left", va="center", fontweight="bold")
ax.text(28, 150, "A Gemma 4 E4B agent has no failing test to run. We measured the result:", fontsize=10, color=DIM, ha="left", va="center")
ax.text(28, 131, "15 runs, 12 designs, all solved 3 to 8 of 90. The differences are noise.", fontsize=10, color=DIM, ha="left", va="center")

# strip of 15 runs
x0, x1, y0, k = 28, 532, 40, 7.2
w = (x1 - x0) / len(solved)
ax.add_patch(FancyBboxPatch((x0 - 4, y0 + 3 * k - 2), x1 - x0 + 8, 5 * k + 4, boxstyle="round,pad=0,rounding_size=3",
                            fc="#1a2440", ec="none", alpha=0.9, zorder=1))
for i, s in enumerate(solved):
    col = ACC2 if RUNS[i].startswith("s") else "#8b9bd1"
    ax.add_patch(plt.Rectangle((x0 + i * w + 4, y0), w - 8, s * k, fc=col, ec="none", zorder=2))
    ax.text(x0 + i * w + w / 2, y0 + s * k + 2, str(s), fontsize=7, color=FG, ha="center", va="bottom", zorder=3)
ax.text(x0, y0 - 14, "resolved of 90 per run   |   shaded band = the 3 to 8 noise floor   |   blue = official sample prompt", fontsize=7, color=DIM, ha="left", va="center")

out = Path("assets/card.png"); out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=200, facecolor=BG)
print("wrote", out, solved)
