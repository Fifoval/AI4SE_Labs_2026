"""Match an input embedding against the chunk store and return the n most relevant chunks.

Similarity is cosine similarity. Both the stored vectors and the query vector are
L2-normalised, so it is a single matrix-vector product. Top-n selection uses
``np.argpartition`` (O(N)) followed by sorting only the n winners.

Usage:
    python match.py "Return True when the amount is non-zero." [-n 5] [--kind source]
    python match.py --eval        # rank of the target method for every task in missing_code.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "Task_3"))
from embed_chunks import EmbeddingStore, embed_query  # noqa: E402

MISSING_CODE = HERE.parent / "missing_code.json"


@dataclass
class Match:
    score: float  # cosine similarity in [-1, 1]
    chunk: dict


def top_n(store: EmbeddingStore, query_vec: np.ndarray, n: int = 5,
          kinds: Optional[Sequence[str]] = None, skip_stubs: bool = False) -> List[Match]:
    """Return the ``n`` chunks most similar to ``query_vec``, best first.

    ``kinds`` optionally restricts the candidates, e.g. ``["source"]``;
    ``skip_stubs`` drops methods whose body is only ``pass``.
    """
    query_vec = query_vec / np.linalg.norm(query_vec)  # no-op for our vectors, safe for others
    scores = store.embeddings @ query_vec
    if kinds is not None or skip_stubs:
        mask = np.array([(kinds is None or c["kind"] in kinds) and not (skip_stubs and c["is_stub"])
                         for c in store.chunks])
        scores = np.where(mask, scores, -np.inf)
    n = min(n, int(np.isfinite(scores).sum()))
    if n <= 0:
        return []
    best = np.argpartition(-scores, n - 1)[:n]
    best = best[np.argsort(-scores[best])]
    return [Match(float(scores[i]), store.chunks[i]) for i in best]


def retrieve(store: EmbeddingStore, task: str, n: int = 5,
             kinds: Optional[Sequence[str]] = None, skip_stubs: bool = False) -> List[Match]:
    """Convenience: embed a textual task and return its top-n chunks."""
    return top_n(store, embed_query(task), n, kinds, skip_stubs)


def task_to_query(task: dict) -> str:
    """Textual query for one entry of missing_code.json (also used in Task 5)."""
    return (f"Implement the method {task['method']} of class {task['class']} "
            f"in {task['file']}. {task['docstring'].strip()}")


def evaluate(store: EmbeddingStore, n: int) -> None:
    """For each task, report where the target (stub) chunk ranks."""
    tasks = json.loads(MISSING_CODE.read_text(encoding="utf-8"))
    hits = 0
    for task in tasks:
        target = f"{task['file']}::{task['class']}.{task['method']}"
        ranked = top_n(store, embed_query(task_to_query(task)), len(store))
        rank = next(i for i, m in enumerate(ranked, 1) if m.chunk["id"] == target)
        class_rank = next(i for i, m in enumerate(ranked, 1)
                          if m.chunk["class_name"] == task["class"] and m.chunk["kind"] == "source")
        hits += rank <= n
        print(f"{task['class'] + '.' + task['method']:<34} method rank {rank:>3}   "
              f"first chunk of class rank {class_rank:>2}")
    print(f"\nTarget method in top {n}: {hits}/{len(tasks)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("task", nargs="?", help="textual task / query")
    parser.add_argument("-n", type=int, default=5)
    parser.add_argument("--kind", action="append", choices=["source", "test"])
    parser.add_argument("--eval", action="store_true")
    args = parser.parse_args()

    store = EmbeddingStore.load()
    if args.eval:
        evaluate(store, args.n)
        return
    if not args.task:
        parser.error("provide a task or --eval")
    for m in retrieve(store, args.task, args.n, args.kind):
        print(f"{m.score:.3f}  {m.chunk['id']}")


if __name__ == "__main__":
    main()
