# Evaluates every prompt's predictions with the same logic as data/evaluate_retrieval_predictions.py
# (multiset comparison of executed rows), but per question and without stopping on a SQL error.
# Writes:
#   results/all_predictions.csv  - all predictions with prompt/model metadata and per-question correctness
#   results/summary.csv          - accuracy and inference time per prompt

import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
PRED_DIR = TASK_DIR / "predictions"
RESULTS_DIR = TASK_DIR / "results"
PROMPTS = ["P1_RTF", "P2_FewShot", "P3_CoT"]

sys.path.insert(0, str(DATA_DIR))
from evaluate_retrieval_predictions import load_database, row_multiset  # noqa: E402


def main():
    csv.field_size_limit(1_000_000_000)
    with (DATA_DIR / "restaurants_dataset.csv").open(encoding="utf-8", newline="") as f:
        labels = [(r["question"], json.loads(r["result"])) for r in csv.DictReader(f)]

    connection = load_database()
    RESULTS_DIR.mkdir(exist_ok=True)
    all_rows, summary = [], []

    for prompt_id in PROMPTS:
        run = json.loads((PRED_DIR / f".run_{prompt_id}.json").read_text(encoding="utf-8"))
        with (PRED_DIR / f"{prompt_id}.csv").open(encoding="utf-8", newline="") as f:
            predictions = list(csv.DictReader(f))
        if len(predictions) != len(labels):
            raise ValueError(f"{prompt_id}: {len(predictions)} predictions, {len(labels)} labels")

        correct = errors = 0
        exec_start = time.perf_counter()
        for index, (prediction, (question, expected)) in enumerate(zip(predictions, labels)):
            if prediction["question"] != question:
                raise ValueError(f"{prompt_id}: question mismatch on row {index + 2}")
            error = ""
            try:
                predicted = connection.execute(prediction["predicted_sql"]).fetchall()
                is_correct = row_multiset(predicted) == row_multiset(expected)
            except sqlite3.Error as exc:
                predicted, is_correct, error = [], False, str(exc)
                errors += 1
            correct += is_correct
            all_rows.append({
                "prompt_id": prompt_id,
                "framework": prompt_id.split("_", 1)[1],
                "model": run["model"],
                "question_index": index,
                "question": question,
                "predicted_sql": prediction["predicted_sql"],
                "analysis": prediction.get("analysis", ""),
                "expected_rows": len(expected),
                "predicted_rows": len(predicted),
                "correct": int(is_correct),
                "sql_error": error,
            })
        exec_seconds = time.perf_counter() - exec_start

        total = len(labels)
        summary.append({
            "prompt_id": prompt_id,
            "model": run["model"],
            "correct": correct,
            "total": total,
            "accuracy": round(correct / total, 4),
            "sql_errors": errors,
            "inference_time_s": round(run["duration_ms"] / 1000, 1),
            "time_per_question_s": round(run["duration_ms"] / 1000 / total, 2),
            "tokens": run["subagent_tokens"],
            "tool_uses": run["tool_uses"],
            "sql_execution_time_s": round(exec_seconds, 3),
        })

    connection.close()
    for name, rows in [("all_predictions.csv", all_rows), ("summary.csv", summary)]:
        with (RESULTS_DIR / name).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    for s in summary:
        print(f"{s['prompt_id']:<11} accuracy {s['accuracy']:.2%} ({s['correct']}/{s['total']}), "
              f"errors {s['sql_errors']}, inference {s['inference_time_s']} s")


if __name__ == "__main__":
    main()
