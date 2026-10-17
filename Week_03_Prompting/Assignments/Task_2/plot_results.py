# Draws results/comparison.png from results/summary.csv (run evaluate_all.py first).
# One panel per measure (accuracy, inference time) - no shared or dual axis.

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
SURFACE, INK, MUTED, GRID, BAR = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"

with (RESULTS_DIR / "summary.csv").open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
labels = [r["prompt_id"].replace("_", " ") for r in rows][::-1]

panels = [
    ("Accuracy (%)", [float(r["accuracy"]) * 100 for r in rows][::-1], "{:.2f} %", (90, 101)),
    ("Inference time (s)", [float(r["inference_time_s"]) for r in rows][::-1], "{:.0f} s", None),
]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK})
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), facecolor=SURFACE)
fig.suptitle("Prompt comparison on 155 text-to-SQL questions",
             x=0.01, ha="left", fontsize=12, fontweight="bold")

for ax, (title, values, fmt, xlim) in zip(axes, panels):
    ax.set_facecolor(SURFACE)
    ax.barh(labels, values, height=0.45, color=BAR)
    upper = xlim[1] if xlim else max(values) * 1.25
    ax.set_xlim(xlim[0] if xlim else 0, upper)
    for y, v in enumerate(values):
        ax.text(v + (upper - (xlim[0] if xlim else 0)) * 0.015, y, fmt.format(v),
                va="center", color=INK, fontsize=9)
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(GRID)

axes[0].text(0, -0.3, "Axis starts at 90 %", transform=axes[0].transAxes, color=MUTED, fontsize=8)
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig(RESULTS_DIR / "comparison.png", dpi=160, facecolor=SURFACE)
print("saved", RESULTS_DIR / "comparison.png")
