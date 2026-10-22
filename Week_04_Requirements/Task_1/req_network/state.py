"""Shared graph state. Records are plain dicts so the state stays JSON-serialisable."""
import operator
from typing import Annotated, TypedDict


def merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}


class GraphState(TypedDict, total=False):
    input_dir: str
    output_dir: str

    # deterministic preprocessing
    documents: list[dict]          # {doc_id, path, doc_type, date, authority, text, warnings}
    chunks: list[dict]             # {chunk_id, doc_id, text}

    # extraction (fan-out, merged by reducer)
    raw_items: Annotated[list[dict], operator.add]
    candidates: list[dict]         # valid items with cid
    rejected: list[dict]           # items flagged nonsensical / out of scope by extractor

    # structure
    areas: list[dict]
    glossary: list[dict]
    assignments: dict              # cid -> area code

    # consolidation (fan-out per area, merged by reducer)
    area_results: Annotated[dict, merge_dicts]   # area code -> ConsolidationResult dict

    # numbered, traced requirements and checks
    requirements: list[dict]
    coverage_gaps: dict            # area code -> [cid, ...]
    fidelity_gaps: dict            # area code -> [candidate absorbed without its content, ...]
    issues: list[dict]
    conflict_blacklist: list[dict]
    merged_duplicates: list[dict]
    tensions: list[dict]           # open issues: both requirements kept, need clarification

    # feedback loop
    revision: int
    feedback: dict                 # area code -> [instruction, ...]
    known_issues: list[dict]       # duplicate/conflict pairs keyed by area+name (persist across rounds)
    pending_pairs: int             # new pairs reported by the critic in the last round
    critic_summary: str
    critic_history: list[dict]

    errors: Annotated[list[str], operator.add]   # non-fatal processing errors
