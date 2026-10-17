# Correct-Answer Throughput (CAT) for the Task 2 predictions.
#
#   F1_i  = row-level F1 between predicted and expected rows of question i (multisets, so
#           duplicate rows count); 1.0 when both are empty, 0.0 when exactly one is empty
#   CAT   = sum_i F1_i / T, where T is the inference time of the prompt in minutes
#
# CAT says how much correct output a prompt produces per minute. Partial answers earn
# partial credit, and a slow prompt is penalised even when it is just as accurate.
#
# Writes results/per_question_f1.csv and results/metric_summary.csv, and draws results/cat.png.

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TASK3_DIR = Path(__file__).resolve().parent
TASK2_DIR = TASK3_DIR.parent / "Task_2"
RESULTS_DIR = TASK3_DIR / "results"
PROMPTS = ["P1_RTF", "P2_FewShot", "P3_CoT"]

sys.path.insert(0, str(TASK2_DIR / "data"))
from evaluate_retrieval_predictions import load_database  # noqa: E402


def row_f1(predicted, expected):
    if not predicted and not expected:
        return 1.0, 1.0, 1.0
    if not predicted or not expected:
        return 0.0, 0.0, 0.0
    p, e = Counter(map(tuple, predicted)), Counter(map(tuple, expected))
    overlap = sum((p & e).values())
    precision = overlap / sum(p.values())
    recall = overlap / sum(e.values())
    f1 = 2 * precision * recall / (precision + recall) if overlap else 0.0
    return precision, recall, f1


def main():
    csv.field_size_limit(1_000_000_000)
    with (TASK2_DIR / "data" / "restaurants_dataset.csv").open(encoding="utf-8", newline="") as f:
        labels = [(r["question"], json.loads(r["result"])) for r in csv.DictReader(f)]
    with (TASK2_DIR / "results" / "summary.csv").open(encoding="utf-8", newline="") as f:
        times = {r["prompt_id"]: float(r["inference_time_s"]) for r in csv.DictReader(f)}

    connection = load_database()
    RESULTS_DIR.mkdir(exist_ok=True)
    per_question, summary = [], []

    for prompt_id in PROMPTS:
        with (TASK2_DIR / "predictions" / f"{prompt_id}.csv").open(encoding="utf-8", newline="") as f:
            predictions = list(csv.DictReader(f))

        f1_sum = exact = 0
        for index, (prediction, (question, expected)) in enumerate(zip(predictions, labels)):
            predicted = connection.execute(prediction["predicted_sql"]).fetchall()
            precision, recall, f1 = row_f1(predicted, expected)
            f1_sum += f1
            exact += Counter(map(tuple, predicted)) == Counter(map(tuple, expected))
            per_question.append({
                "prompt_id": prompt_id, "question_index": index, "question": question,
                "expected_rows": len(expected), "predicted_rows": len(predicted),
                "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            })

        minutes = times[prompt_id] / 60
        summary.append({
            "prompt_id": prompt_id,
            "exact_match_accuracy": round(exact / len(labels), 4),
            "mean_f1": round(f1_sum / len(labels), 4),
            "inference_time_min": round(minutes, 2),
            "cat_per_min": round(f1_sum / minutes, 2),
        })

    connection.close()
    for name, rows in [("per_question_f1.csv", per_question), ("metric_summary.csv", summary)]:
        with (RESULTS_DIR / name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    plot(summary)
    for s in summary:
        print(s)


def plot(summary):
    surface, ink, muted, grid, bar = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"
    labels = [s["prompt_id"].replace("_", " ") for s in summary][::-1]
    values = [s["cat_per_min"] for s in summary][::-1]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": ink})
    fig, ax = plt.subplots(figsize=(7, 2.8), facecolor=surface)
    ax.set_facecolor(surface)
    ax.barh(labels, values, height=0.45, color=bar)
    upper = max(values) * 1.2
    ax.set_xlim(0, upper)
    for y, v in enumerate(values):
        ax.text(v + upper * 0.015, y, f"{v:.1f}", va="center", color=ink, fontsize=9)
    ax.set_title("Correct-Answer Throughput (correct answers per minute)", loc="left", fontsize=11)
    ax.tick_params(colors=muted, length=0)
    ax.grid(axis="x", color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(grid)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "cat.png", dpi=160, facecolor=surface)


if __name__ == "__main__":
    main()
