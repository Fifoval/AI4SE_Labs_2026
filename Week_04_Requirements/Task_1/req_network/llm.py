"""Thin wrapper around ChatOpenAI: one model per role, structured output, disk cache, stats."""
import hashlib
import threading
from collections import Counter
from pathlib import Path

from langchain_openai import ChatOpenAI

from .config import MODELS

CALLS: Counter = Counter()
CACHED: Counter = Counter()
CACHE_DIR: Path | None = None   # set by main.py; None disables caching
_lock = threading.Lock()


def structured_call(role: str, schema, system: str, user: str):
    """Invoke the role's model and parse the answer into `schema`.

    Answers are cached on disk by (model, schema, prompt, input), so a rerun after a
    failure resumes where it stopped and an identical rerun is reproducible."""
    key = hashlib.sha256(f"{MODELS[role]}\n{schema.__name__}\n{system}\n{user}".encode()).hexdigest()
    cache = CACHE_DIR / f"{role}_{key[:24]}.json" if CACHE_DIR else None
    if cache and cache.exists():
        with _lock:
            CACHED[role] += 1
        return schema.model_validate_json(cache.read_text(encoding="utf-8"))
    llm = ChatOpenAI(model=MODELS[role], max_retries=6, timeout=900)
    chain = llm.with_structured_output(schema)
    with _lock:
        CALLS[role] += 1
    result = chain.invoke([("system", system), ("user", user)])
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(result.model_dump_json(), encoding="utf-8")
    return result
