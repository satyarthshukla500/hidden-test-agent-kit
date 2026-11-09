#!/usr/bin/env python3
"""Publication figures for the paper.

Reads EXPERIMENTS.md (run table), results/*/buckets.json (per-task buckets)
and data/tasks.jsonl + data/splits/dev.txt (test-patch imports), and writes
figures/fig*.png (200 dpi) and figures/fig*.svg.

Numbers that exist in no machine-readable file are hard-coded below, each with
a comment naming the NOTES.md line (or the trace re-decode) it comes from.

  python scripts/make_figures.py
"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

# Okabe-Ito, colorblind-safe.
BLUE, ORANGE, GREEN, SKY, YELLOW, VERMILION, PURPLE, GREY = (
    "#0072B2", "#E69F00", "#009E73", "#56B4E9", "#F0E442", "#D55E00", "#CC79A7", "#999999",
)
LIGHT = "#D9D9D9"
FAM_SAMPLE = "sample prompt (analyzer optional)"
FAM_BRIEF = "mandatory brief (analyzer then coder)"
FAM_RETRY = "retry loop"
FAMILY_COLOR = {FAM_SAMPLE: BLUE, FAM_BRIEF: ORANGE, FAM_RETRY: GREEN}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.size": 11,
    "axes.titlesize": 12.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "legend.frameon": False,
    "svg.fonttype": "none",
    "hatch.linewidth": 0.8,
})


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)
    print("wrote", OUT / f"{name}.png")


# --------------------------------------------------------------------------
# Data: EXPERIMENTS.md run table
# --------------------------------------------------------------------------
def parse_experiments():
    rows = []
    for line in (ROOT / "EXPERIMENTS.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in ("tag", "---"):
            continue
        tag, kaggle, change, resolved, note = cells
        m = re.fullmatch(r"(\d+)/(\d+)", resolved)
        if not m:
            continue  # stopped / blocked runs
        rows.append({"tag": tag, "kaggle": kaggle, "change": change, "note": note,
                     "resolved": int(m.group(1)), "n": int(m.group(2))})
    return rows


def family(tag):
    if tag.startswith("s"):
        return FAM_SAMPLE
    if tag.startswith("p08"):
        return FAM_RETRY
    return FAM_BRIEF


def load_buckets(run):
    p = ROOT / "results" / run / "buckets.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def dev_tasks():
    """The 90 dev tasks from data/tasks.jsonl, keyed by instance_id."""
    dev_ids = set(open(ROOT / "data/splits/dev.txt", encoding="utf-8").read().split())
    tasks = {}
    with open(ROOT / "data/tasks.jsonl", encoding="utf-8") as fh:
        for line in fh:
            t = json.loads(line)
            if t["instance_id"] in dev_ids:
                tasks[t["instance_id"]] = t
    assert len(tasks) == 90
    return tasks


def ungradable_sets(tasks):
    """Dev tasks the offline sandbox does not grade (NOTES.md 2026-11-09, analysis):
    the wheels cache lacks inline_snapshot and dirty_equals, and tests/test_requests.py
    errors at collection. Derived from the test_patch text."""
    inline, dirty, treq = set(), set(), set()
    for tid, t in tasks.items():
        tp = t["test_patch"]
        files = re.findall(r"^\+\+\+ b/(\S+)", tp, re.M)
        if "inline_snapshot" in tp:
            inline.add(tid)
        if "dirty_equals" in tp:
            dirty.add(tid)
        if "tests/test_requests.py" in files:
            treq.add(tid)
    return inline, dirty - inline, treq


EXP = parse_experiments()
DEV_RUNS = ["p00-base", "p01", "p02", "p01b", "p03", "p03b", "p03c", "p05"]  # the 8 dev runs used for fig4


# --------------------------------------------------------------------------
# Figure 1: resolved count per run, by design family
# --------------------------------------------------------------------------
def fig1():
    dev = [r for r in EXP if r["n"] == 90]
    held = [r for r in EXP if r["n"] == 39]
    smoke = [r for r in EXP if r["n"] == 20]
    dev.sort(key=lambda r: (family(r["tag"]) == FAM_SAMPLE, EXP.index(r)))

    fig, axes = plt.subplots(
        1, 3, figsize=(11, 4.6),
        gridspec_kw={"width_ratios": [len(dev), len(held) + 0.6, len(smoke) + 0.6], "wspace": 0.25},
    )
    panels = [(axes[0], dev, "90 dev tasks"), (axes[1], held, "39 held-out"), (axes[2], smoke, "20-task smokes")]
    for ax, rows, title in panels:
        xs = range(len(rows))
        cols = [FAMILY_COLOR[family(r["tag"])] for r in rows]
        bars = ax.bar(xs, [r["resolved"] for r in rows], color=cols, width=0.72)
        for b, r in zip(bars, rows):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.15, str(r["resolved"]),
                    ha="center", va="bottom", fontsize=10)
        labels = [r["tag"].replace("heldout-", "").replace("smoke", "") for r in rows]
        ax.set_xticks(list(xs))
        ax.set_xticklabels(labels, rotation=45, ha="right", rotation_mode="anchor")
        ax.set_title(title, fontsize=10.5, fontweight="normal", loc="center", pad=4)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_ylim(0, max(r["resolved"] for r in rows) * 1.3)
        ax.set_xlabel(f"resolved of {rows[0]['n']}", labelpad=6)
    ax = axes[0]
    best = max(r["resolved"] for r in dev)
    ax.axhline(best, color="black", lw=0.8, ls=(0, (4, 3)))
    ax.text(-0.4, best + 0.15, f"{best} of 90", ha="left", va="bottom", fontsize=9.5)
    handles = [Patch(color=c, label=f) for f, c in FAMILY_COLOR.items()]
    fig.legend(handles=handles, loc="upper left", ncol=3, bbox_to_anchor=(0.01, 0.93))
    fig.text(0.01, 0.99, "Every configuration solved 3 to 8 of 90 dev tasks",
             ha="left", va="top", fontsize=12.5, fontweight="bold")
    fig.subplots_adjust(top=0.78, bottom=0.22)
    save(fig, "fig1_runs")


# --------------------------------------------------------------------------
# Figure 2: why edit_file failed (trace re-decode)
# --------------------------------------------------------------------------
def fig2():
    # Trace re-decode over 309 traced tasks (p03b, p03c, p05, held-out p03):
    # 658 edit_file calls = 350 landed + 308 failed.
    ok, failed = 350, 308
    assert ok + failed == 658
    # 308 failures by cause.
    not_found, nonunique, wrong_path, budget, other = 243, 26, 21, 8, 10
    assert not_found + nonunique + wrong_path + budget + other == failed
    # 243 "old_string not found", by where the text had appeared (author-aware).
    where = [
        ("in the brief", 92, VERMILION),  # 88 exact + 4 whitespace-only
        ("in a file window\nthe coder read", 29, SKY),
        ("in the coder's\nown earlier text", 12, PURPLE),
        ("only in analyzer tool output\nthe coder never saw", 7, GREY),
        ("shell / search output", 2, YELLOW),
        ("nowhere", 101, ORANGE),
    ]
    assert sum(v for _, v, _ in where) == not_found
    # Landing by anchor length over the 658 calls (re-decode): landed / attempted.
    by_len = [("1 line", 39, 89), ("2 to 8 lines", 243, 410), ("9 or more lines", 68, 159)]
    assert sum(a for _, a, _ in by_len) == ok
    assert sum(n for _, _, n in by_len) == ok + failed

    rows = [
        ("658 edit_file calls", [("landed", ok, GREEN), ("failed", failed, VERMILION)]),
        ("308 failures, by cause", [
            ("old_string not found", not_found, VERMILION),
            ("occurs N times", nonunique, PURPLE),
            ("wrong path", wrong_path, SKY),
            ("budget", budget, GREY),
            ("other", other, LIGHT),
        ]),
        ("243 not found, where the\ntext had appeared", where),
    ]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.8), gridspec_kw={"width_ratios": [4.2, 1], "wspace": 0.35})
    ys = [2.6, 1.3, 0.0]
    h = 0.7
    for y, (label, segs) in zip(ys, rows):
        left = 0
        small = []
        for name, v, c in segs:
            ax.barh(y, v, left=left, height=h, color=c, edgecolor="white", linewidth=0.8)
            if v >= 60:
                ax.text(left + v / 2, y, f"{name}\n{v}", ha="center", va="center", fontsize=9.5,
                        color="white" if c in (VERMILION, BLUE, PURPLE, GREEN) else "black")
            else:
                small.append((left + v / 2, name.replace("\n", " "), v))
            left += v
        n = len(small)
        for i, (x, name, v) in enumerate(small):
            ty = y + (n - 1) / 2 * 0.2 - i * 0.2
            ax.annotate(f"{name}  {v}", xy=(x, y + h / 2 if ty >= y else y - h / 2), xytext=(left + 40, ty),
                        ha="left", va="center", fontsize=9,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color="#555555",
                                        connectionstyle="angle,angleA=0,angleB=90,rad=0"))
        ax.text(-8, y, label, ha="right", va="center", fontsize=10.5)
    ax.set_xlim(0, 660)
    ax.set_ylim(-0.6, 3.1)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("edit_file calls (309 traced tasks: p03b, p03c, p05 and held-out p03)\n"
                  "\"in the brief\" = 88 exact + 4 whitespace-only", fontsize=10)

    # right panel: landing rate by anchor length
    xs = range(len(by_len))
    rates = [a / n for _, a, n in by_len]
    ax2.bar(xs, rates, color=BLUE, width=0.65)
    for x, (name, a, n) in zip(xs, by_len):
        ax2.text(x, a / n + 0.02, f"{a}/{n}\n{a / n:.0%}", ha="center", va="bottom", fontsize=9.5)
    ax2.set_xticks(list(xs))
    ax2.set_xticklabels([n for n, _, _ in by_len], rotation=30, ha="right", rotation_mode="anchor")
    ax2.set_ylim(0, 1)
    ax2.set_yticks([])
    ax2.spines["left"].set_visible(False)
    ax2.set_title("landed, by anchor length", fontsize=10.5, fontweight="normal", loc="center")

    fig.text(0.01, 0.99, "Of 243 missing edit anchors, 92 matched text in the brief and 101 matched nothing the coder had received",
             ha="left", va="top", fontsize=12.5, fontweight="bold")
    fig.subplots_adjust(left=0.2, top=0.86)
    save(fig, "fig2_edit_failures")


# --------------------------------------------------------------------------
# Figure 3: bucket breakdown per dev run, ungradable tasks hatched
# --------------------------------------------------------------------------
def fig3():
    order = ["resolved", "wrong_fix", "regression", "no_patch", "other"]
    names = {"resolved": "resolved", "wrong_fix": "wrong fix", "regression": "target still failing",
             "no_patch": "no patch", "other": "other (budget, timeout, error)"}
    colors = {"resolved": BLUE, "wrong_fix": VERMILION, "regression": ORANGE, "no_patch": LIGHT, "other": GREY}
    wanted = ["p00-base", "p01", "p01b", "p02", "p03", "p03b", "p03c", "p05", "p06", "p07",
              "s01", "s02", "s03", "s04", "p09"]
    runs = [r for r in wanted if load_buckets(r) is not None]
    # Edit landing rate (landed / edit_file calls) per run, from the trace re-decode.
    # p03 figure is pooled over p03b, p03c, p05 and held-out p03 (350/658).
    landing = {"p03": (350, 658), "p03b": (350, 658), "p03c": (350, 658), "p05": (350, 658),
               "p06": (118, 199), "p07": (93, 172), "s01": (51, 77), "s02": (119, 187),
               "s03": (117, 169), "s04": (149, 239)}
    pooled = {"p03", "p03b", "p03c", "p05"}

    tasks = dev_tasks()
    inline, dirty_only, treq = ungradable_sets(tasks)
    ungradable = inline | dirty_only | treq
    assert len(ungradable) == 20

    fig, ax = plt.subplots(figsize=(11, 0.48 * len(runs) + 2.6))
    ylabels = []
    for i, run in enumerate(reversed(runs)):
        rows = load_buckets(run)
        assert len(rows) == 90, run
        counts = collections.Counter(x["bucket"] if x["bucket"] in order else "other" for x in rows)
        ung = collections.Counter((x["bucket"] if x["bucket"] in order else "other")
                                  for x in rows if x["id"] in ungradable)
        left = 0
        for k in order:
            v = counts[k]
            if not v:
                continue
            plain, hatched = v - ung[k], ung[k]
            ax.barh(i, plain, left=left, height=0.68, color=colors[k], edgecolor="white", linewidth=0.8)
            if hatched:
                ax.barh(i, hatched, left=left + plain, height=0.68, color=colors[k], edgecolor="white",
                        linewidth=0.8, hatch="////")
            if v >= 3:
                ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=9.5,
                        color="white" if k in ("resolved", "wrong_fix") else "black")
            left += v
        lab = run
        if run in landing:
            a, n = landing[run]
            lab += f"\nedits landed {a / n:.0%}" + ("*" if run in pooled else "")
        ylabels.append(lab)
    ax.set_yticks(range(len(runs)))
    ax.set_yticklabels(ylabels, fontsize=9.5)
    ax.set_xlim(0, 90)
    ax.set_xticks([0, 30, 60, 90])
    ax.set_xlabel("tasks of 90")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles = [Patch(color=colors[k], label=names[k]) for k in order]
    handles.append(Patch(facecolor="white", edgecolor="black", hatch="////",
                         label=f"hatched: {len(ungradable)} tasks the sandbox does not grade"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3)
    ax.text(0, -0.2, "* pooled over p03b, p03c, p05 and held-out p03 (350 of 658 edit_file calls)",
            transform=ax.transAxes, fontsize=8.5, color="#555555", va="top")
    ax.set_title("Sample-prompt runs landed 62-69% of edits, briefed runs 53-59%; "
                 "resolved stayed at 3 to 8 of 90", wrap=True)
    save(fig, "fig3_funnel")


# --------------------------------------------------------------------------
# Figure 4: per-task consistency across the 8 dev runs
# --------------------------------------------------------------------------
def fig4():
    counts = collections.Counter()
    for run in DEV_RUNS:
        for x in load_buckets(run):
            if x["bucket"] == "resolved":
                counts[x["id"]] += 1
    tasks = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    core = sum(1 for _, v in tasks if v >= 3)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ys = range(len(tasks))[::-1]
    for y, (tid, v) in zip(ys, tasks):
        c = BLUE if v >= 3 else GREY
        ax.hlines(y, 0, v, color=c, lw=1.2, alpha=0.6)
        ax.plot(range(1, v + 1), [y] * v, "o", color=c, ms=7)
        ax.text(v + 0.25, y, f"{v} / {len(DEV_RUNS)}", va="center", fontsize=9.5, color="black")
    ax.set_yticks(list(ys))
    ax.set_yticklabels([t for t, _ in tasks], fontfamily="monospace", fontsize=9.5)
    ax.set_xlim(0, len(DEV_RUNS) + 1.2)
    ax.set_xticks(range(0, len(DEV_RUNS) + 1))
    ax.set_xlabel(f"runs that solved the task (of {len(DEV_RUNS)}: {', '.join(DEV_RUNS)})")
    sep = len(tasks) - core - 0.5
    ax.axhline(sep, color="black", lw=0.8, ls=(0, (4, 3)))
    ax.text(len(DEV_RUNS) + 1.1, sep + 0.25, f"{core} tasks solved in 3 or more runs", fontsize=9.5,
            ha="right", va="bottom", color=BLUE)
    ax.text(len(DEV_RUNS) + 1.1, sep - 0.25, f"{len(tasks) - core} tasks solved once or twice", fontsize=9.5,
            ha="right", va="top", color="#555555")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_title(f"Only {len(tasks)} of 90 tasks were solved in any of {len(DEV_RUNS)} runs; "
                 f"{core} of them in 3 or more runs", wrap=True)
    save(fig, "fig4_consistency")


# --------------------------------------------------------------------------
# Figure 5: sandbox gradability of the 90 dev tasks
# --------------------------------------------------------------------------
def fig5():
    tasks = dev_tasks()
    inline, dirty_only, treq = ungradable_sets(tasks)
    ungradable = inline | dirty_only | treq
    # Union over every 90-task run with a buckets.json in results/ (15 runs).
    full_runs = sorted(p.parent.name for p in (ROOT / "results").glob("*/buckets.json")
                       if len(json.loads(p.read_text(encoding="utf-8"))) == 90)
    ever_solved = set()
    for run in full_runs:
        ever_solved |= {x["id"] for x in load_buckets(run) if x["bucket"] == "resolved"}
    assert not (ever_solved & ungradable)

    cats = [
        (f"gradable, solved in at least one of {len(full_runs)} runs", sorted(ever_solved), BLUE),
        ("gradable, never solved", sorted(set(tasks) - ungradable - ever_solved), LIGHT),
        ("test imports inline_snapshot (missing wheel)", sorted(inline), VERMILION),
        ("test imports dirty_equals only (missing wheel)", sorted(dirty_only), ORANGE),
        ("graded via tests/test_requests.py (errors at collection)", sorted(treq), PURPLE),
    ]
    assert sum(len(ids) for _, ids, _ in cats) == 90

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ncol = 15
    i = 0
    for label, ids, c in cats:
        for tid in ids:
            r, col = divmod(i, ncol)
            ax.add_patch(Rectangle((col, -r), 0.9, 0.9, color=c))
            i += 1
    nrow = -(-90 // ncol)
    ax.set_xlim(-0.2, ncol + 0.1)
    ax.set_ylim(-nrow + 0.7, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    gradable = 90 - len(ungradable)
    handles = [Patch(color=c, label=f"{label}: {len(ids)}") for label, ids, c in cats]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=9.5)
    ax.set_title(f"{len(ungradable)} of 90 dev tasks are not graded in the offline sandbox; "
                 f"{gradable} are gradable", wrap=True, pad=14)
    save(fig, "fig5_sandbox")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
