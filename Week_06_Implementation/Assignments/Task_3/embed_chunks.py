"""Turn the chunks from Task 2 into embeddings and store them.

Model: BAAI/bge-small-en-v1.5 (sentence-transformers, 384 dimensions, runs on CPU).
We embed each chunk's ``text`` (context header + code). Vectors are L2-normalised,
so cosine similarity is a plain dot product.

Storage (in this folder):
    embeddings.npy   float32 matrix, shape (n_chunks, 384); row i = chunk i
    store.json       model name, dimension and the chunk list (same order as rows)

Usage:
    python embed_chunks.py [--chunks PATH]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).resolve().parent
DEFAULT_CHUNKS = HERE.parent / "Task_2" / "chunks.json"
EMBEDDINGS_PATH = HERE / "embeddings.npy"
STORE_PATH = HERE / "store.json"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
# BGE models expect this prefix on short queries (not on the stored passages).
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once (downloaded from Hugging Face on first use)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


def embed_texts(texts: Sequence[str]) -> np.ndarray:
    """Embed passages (chunks). Returns a normalised float32 matrix."""
    vectors = get_model().encode(list(texts), batch_size=32, normalize_embeddings=True,
                                 show_progress_bar=len(texts) > 64)
    return np.asarray(vectors, dtype=np.float32)


def embed_chunk(chunk: dict) -> np.ndarray:
    """Embed a single chunk (as stored in chunks.json)."""
    return embed_texts([chunk["text"]])[0]


def embed_query(query: str) -> np.ndarray:
    """Embed a task description so it can be compared with chunk embeddings."""
    return embed_texts([QUERY_INSTRUCTION + query])[0]


class EmbeddingStore:
    """Chunks and their embeddings, aligned by row index."""

    def __init__(self, chunks: List[dict], embeddings: np.ndarray, model: str) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks and embeddings are not aligned")
        self.chunks = chunks
        self.embeddings = embeddings
        self.model = model
        self._index = {c["id"]: i for i, c in enumerate(chunks)}

    def __len__(self) -> int:
        return len(self.chunks)

    def get(self, chunk_id: str) -> tuple[dict, np.ndarray]:
        """Return the chunk and its embedding by chunk id."""
        i = self._index[chunk_id]
        return self.chunks[i], self.embeddings[i]

    def save(self, embeddings_path: Path = EMBEDDINGS_PATH, store_path: Path = STORE_PATH) -> None:
        np.save(embeddings_path, self.embeddings)
        meta = {"model": self.model, "dim": int(self.embeddings.shape[1]), "chunks": self.chunks}
        store_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, embeddings_path: Path = EMBEDDINGS_PATH, store_path: Path = STORE_PATH) -> "EmbeddingStore":
        meta = json.loads(store_path.read_text(encoding="utf-8"))
        return cls(meta["chunks"], np.load(embeddings_path), meta["model"])


def build_store(chunks_path: Path) -> EmbeddingStore:
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    embeddings = embed_texts([c["text"] for c in chunks])
    return EmbeddingStore(chunks, embeddings, MODEL_NAME)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    args = parser.parse_args()

    store = build_store(args.chunks)
    store.save()
    print(f"Embedded {len(store)} chunks with {store.model} -> {store.embeddings.shape}")
    print(f"Saved {EMBEDDINGS_PATH.name} ({EMBEDDINGS_PATH.stat().st_size // 1024} KB) and {STORE_PATH.name}")


if __name__ == "__main__":
    main()
