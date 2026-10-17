# Task 4 analysis: all runs (Opus x3, Haiku x1) of the three prompts.
# Computes accuracy, mean F1 and CAT (Task 3 metric) per run, tests whether the differences
# between prompts are statistically significant, and draws the charts.
#
# Outputs (results/):
#   runs.csv               one row per run: model, run, prompt, accuracy, F1, time, CAT, tool calls
#   summary.csv            mean and standard deviation per model and prompt
#   stat_tests.csv         every statistical test with its statistic and p-value
#   sql_consistency.csv    how many of the 155 queries are textually identical across runs/models
#   time_by_run.png, cat_by_prompt.png

import csv
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy import stats  # noqa: E402

TASK4_DIR = Path(__file__).resolve().parent
ASSIGN_DIR = TASK4_DIR.parent
RUNS_DIR = TASK4_DIR / "runs"
RESULTS_DIR = TASK4_DIR / "results"
PROMPTS = ["P1_RTF", "P2_FewShot", "P3_CoT"]
MODELS = {"opus": "Opus", "haiku": "Haiku"}

sys.path.insert(0, str(ASSIGN_DIR / "Task_2" / "data"))
sys.path.insert(0, str(ASSIGN_DIR / "Task_3"))
from evaluate_retrieval_predictions import load_database  # noqa: E402
from metric import row_f1  # noqa: E402


def load_labels():
    csv.field_size_limit(1_000_000_000)
    with (ASSIGN_DIR / "Task_2" / "data" / "restaurants_dataset.csv").open(encoding="utf-8", newline="") as f:
        return [json.loads(r["result"]) for r in csv.DictReader(f)]


def evaluate_runs(labels):
    connection = load_database()
    runs, correctness, sql = [], {}, {}
    for model in MODELS:
        for run_dir in sorted((RUNS_DIR / model).iterdir()):
            for prompt in PROMPTS:
                with (run_dir / f"{prompt}.csv").open(encoding="utf-8", newline="") as f:
                    predictions = list(csv.DictReader(f))
                meta = json.loads((run_dir / f".run_{prompt}.json").read_text(encoding="utf-8"))
                flags, f1_sum = [], 0.0
                for prediction, expected in zip(predictions, labels):
                    predicted = connection.execute(prediction["predicted_sql"]).fetchall()
                    flags.append(int(Counter(map(tuple, predicted)) == Counter(map(tuple, expected))))
                    f1_sum += row_f1(predicted, expected)[2]
                seconds = meta["duration_ms"] / 1000
                key = (model, run_dir.name, prompt)
                correctness[key] = flags
                sql[key] = [" ".join(p["predicted_sql"].split()).rstrip(";") for p in predictions]
                runs.append({
                    "model": model, "run": run_dir.name, "prompt_id": prompt,
                    "correct": sum(flags), "total": len(flags),
                    "accuracy": round(sum(flags) / len(flags), 4),
                    "mean_f1": round(f1_sum / len(flags), 4),
                    "time_s": round(seconds, 1),
                    "cat_per_min": round(f1_sum / (seconds / 60), 2),
                    "tool_calls": meta["tool_uses"],
                })
    connection.close()
    return runs, correctness, sql


def summarize(runs):
    rows = []
    for model in MODELS:
        for prompt in PROMPTS:
            group = [r for r in runs if r["model"] == model and r["prompt_id"] == prompt]
            times = [r["time_s"] for r in group]
            cats = [r["cat_per_min"] for r in group]
            rows.append({
                "model": model, "prompt_id": prompt, "runs": len(group),
                "accuracy": group[0]["accuracy"] if len({r["accuracy"] for r in group}) == 1 else "varies",
                "mean_f1": round(mean(r["mean_f1"] for r in group), 4),
                "time_mean_s": round(mean(times), 1),
                "time_sd_s": round(stdev(times), 1) if len(times) > 1 else "",
                "cat_mean": round(mean(cats), 1),
                "cat_sd": round(stdev(cats), 1) if len(cats) > 1 else "",
            })
    return rows


def mcnemar_exact(a, b):
    # exact McNemar test on paired per-question correctness
    only_a = sum(x and not y for x, y in zip(a, b))
    only_b = sum(y and not x for x, y in zip(a, b))
    n = only_a + only_b
    p = 1.0 if n == 0 else stats.binomtest(only_a, n, 0.5).pvalue
    return only_a, only_b, p


def cochran_q(columns):
    # Cochran's Q for k related binary samples (questions x prompts)
    k = len(columns)
    rows = list(zip(*columns))
    col_totals = [sum(c) for c in columns]
    row_totals = [sum(r) for r in rows]
    total = sum(row_totals)
    denominator = k * total - sum(t * t for t in row_totals)
    if denominator == 0:
        return 0.0, 1.0  # every question answered the same way by every prompt
    q = (k - 1) * (k * sum(t * t for t in col_totals) - total * total) / denominator
    return q, stats.chi2.sf(q, k - 1)


def holm(p_values):
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted, running = [0.0] * len(p_values), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def run_tests(runs, correctness):
    tests = []

    def add(factor, test, comparison, statistic, p, note=""):
        tests.append({"factor": factor, "test": test, "comparison": comparison,
                      "statistic": round(float(statistic), 3),
                      "p_value": "< 0.0001" if p < 0.0001 else round(float(p), 4), "significant_0.05": "yes" if p < 0.05 else "no", "note": note})

    # 1) accuracy: prompts compared on the same questions, separately for every run
    for (model, run) in sorted({(k[0], k[1]) for k in correctness}):
        q, p = cochran_q([correctness[(model, run, pr)] for pr in PROMPTS])
        add("prompt", "Cochran's Q (accuracy)", f"{model} {run}: P1 vs P2 vs P3", q, p)
    for a, b in itertools.combinations(PROMPTS, 2):
        only_a, only_b, p = mcnemar_exact(correctness[("opus", "run1", a)], correctness[("opus", "run1", b)])
        add("prompt", "McNemar exact (accuracy)", f"opus run1: {a} vs {b}", float(only_a + only_b), p,
            "statistic = number of discordant questions")

    # 2) accuracy: model effect (Opus run1 vs Haiku run1, same prompt)
    for prompt in PROMPTS:
        only_a, only_b, p = mcnemar_exact(correctness[("opus", "run1", prompt)], correctness[("haiku", "run1", prompt)])
        add("model", "McNemar exact (accuracy)", f"{prompt}: Opus vs Haiku", float(only_a + only_b), p,
            "statistic = number of discordant questions")

    # 3) inference time between prompts (Opus, 3 runs each); once with all runs, once without
    #    the P3 run1 outlier, where the agent's first write failed and it generated the whole CSV twice
    times = {pr: [r["time_s"] for r in runs if r["model"] == "opus" and r["prompt_id"] == pr] for pr in PROMPTS}
    cleaned = dict(times, P3_CoT=[r["time_s"] for r in runs
                                  if r["model"] == "opus" and r["prompt_id"] == "P3_CoT" and r["run"] != "run1"])
    for label, data in [("all runs", times), ("without P3 run1 outlier", cleaned)]:
        f, p = stats.f_oneway(*data.values())
        add("prompt", "one-way ANOVA (time)", f"opus, {label}: P1 vs P2 vs P3", f, p)
        h, p = stats.kruskal(*data.values())
        add("prompt", "Kruskal-Wallis (time)", f"opus, {label}: P1 vs P2 vs P3", h, p,
            "rank test; with n=3 per group its power is very low")
        pairs = list(itertools.combinations(PROMPTS, 2))
        welch = [stats.ttest_ind(data[a], data[b], equal_var=False) for a, b in pairs]
        for (a, b), result, p_holm in zip(pairs, welch, holm([w.pvalue for w in welch])):
            add("prompt", "Welch t-test (time)", f"opus, {label}: {a} vs {b}", result.statistic, p_holm,
                "p-value Holm-corrected for 3 comparisons")
    return tests


def sql_consistency(sql):
    rows = []
    for prompt in PROMPTS:
        base = sql[("opus", "run1", prompt)]
        for other in [("opus", "run2"), ("opus", "run3"), ("haiku", "run1")]:
            same = sum(x == y for x, y in zip(base, sql[(*other, prompt)]))
            rows.append({"prompt_id": prompt, "compared": f"opus run1 vs {other[0]} {other[1]}",
                         "identical_queries": same, "total": len(base)})
    return rows


SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COLORS = {"opus": "#2a78d6", "haiku": "#eb6834"}


def style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot(runs, summary):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK})
    labels = [p.replace("_", " ") for p in PROMPTS]
    ypos = {p: len(PROMPTS) - 1 - i for i, p in enumerate(PROMPTS)}

    # time of every single run
    fig, ax = plt.subplots(figsize=(8, 3.4), facecolor=SURFACE)
    for model, name in MODELS.items():
        offset = 0.12 if model == "opus" else -0.12
        xs = [r["time_s"] for r in runs if r["model"] == model]
        ys = [ypos[r["prompt_id"]] + offset for r in runs if r["model"] == model]
        ax.scatter(xs, ys, s=70, color=COLORS[model], edgecolor=SURFACE, linewidth=2, label=name, zorder=3)
    outlier = next(r for r in runs if r["model"] == "opus" and r["run"] == "run1" and r["prompt_id"] == "P3_CoT")
    ax.annotate("first write failed, output generated twice", (outlier["time_s"], ypos["P3_CoT"] + 0.12),
                xytext=(-10, 14), textcoords="offset points", ha="right", color=MUTED, fontsize=8)
    ax.set_yticks(list(ypos.values()), [labels[PROMPTS.index(p)] for p in ypos])
    ax.set_xlim(0, 620)
    ax.set_xlabel("inference time per run (s); the 3 Opus runs of P1 and P2 almost overlap", color=MUTED)
    style(ax, "Inference time of every run")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "time_by_run.png", dpi=160, facecolor=SURFACE)

    # CAT per prompt and model (mean, with the range of the Opus runs)
    fig, ax = plt.subplots(figsize=(8, 3.4), facecolor=SURFACE)
    height = 0.32
    for model, name in MODELS.items():
        offset = height / 2 + 0.02 if model == "opus" else -(height / 2 + 0.02)
        for s in [s for s in summary if s["model"] == model]:
            y = ypos[s["prompt_id"]] + offset
            values = [r["cat_per_min"] for r in runs if r["model"] == model and r["prompt_id"] == s["prompt_id"]]
            ax.barh(y, s["cat_mean"], height=height, color=COLORS[model],
                    label=name if s["prompt_id"] == "P1_RTF" else None)
            if len(values) > 1:
                ax.plot([min(values), max(values)], [y, y], color=INK, linewidth=1.2)
            ax.text(max(values) + 1.5, y, f"{s['cat_mean']:.1f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(list(ypos.values()), [labels[PROMPTS.index(p)] for p in ypos])
    ax.set_xlim(0, 95)
    ax.set_xlabel("correct answers per minute (CAT); line = range of the 3 Opus runs", color=MUTED)
    style(ax, "Correct-Answer Throughput by prompt and model")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "cat_by_prompt.png", dpi=160, facecolor=SURFACE)


def write_csv(name, rows):
    with (RESULTS_DIR / name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    runs, correctness, sql = evaluate_runs(load_labels())
    summary = summarize(runs)
    tests = run_tests(runs, correctness)
    consistency = sql_consistency(sql)
    for name, rows in [("runs.csv", runs), ("summary.csv", summary),
                       ("stat_tests.csv", tests), ("sql_consistency.csv", consistency)]:
        write_csv(name, rows)
    plot(runs, summary)
    for rows in (summary, tests, consistency):
        for r in rows:
            print(r)
        print()


if __name__ == "__main__":
    main()
