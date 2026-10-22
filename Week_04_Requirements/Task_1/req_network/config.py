"""Central configuration: models per role, limits, priority scale, source authority."""
import os

# One model per agent role (ANS4: at least 3 different models).
# Cheap model for many parallel calls, strong models for few judgement calls.
MODELS = {
    "extractor": os.getenv("MODEL_EXTRACTOR", "gpt-5-nano"),
    "structurer": os.getenv("MODEL_STRUCTURER", "gpt-5-mini"),
    "consolidator": os.getenv("MODEL_CONSOLIDATOR", "gpt-5-mini"),
    "conflict": os.getenv("MODEL_CONFLICT", "gpt-6-luna"),
    "verifier": os.getenv("MODEL_VERIFIER", "gpt-5.6-luna"),   # independent check of conflicts
    "critic": os.getenv("MODEL_CRITIC", "gpt-5.6-luna"),
}

MAX_CHUNK_CHARS = 12_000      # chunk size for extraction
ASSIGN_BATCH = 100            # candidates per area-assignment call
MAX_AREA_SHARE = 0.2          # areas holding more candidates than this get split
PAIR_NEIGHBORS = 6            # most similar requirements checked per requirement
PAIR_BATCH = 40               # requirement pairs per conflict-judge call
MAX_REVISIONS = 2             # max critic -> consolidator feedback rounds
MAX_CONCURRENCY = 8           # parallel LLM calls (rate-limit friendly)
CACHE_DIR_NAME = ".cache"     # extraction cache inside the output directory
INPUT_EXTENSIONS = {".txt", ".eml", ".md"}

# OS6: priority scale, rendered into the output document.
PRIORITY_SCALE = {
    "Must": "Essential for the system to be accepted. A source marks it as high priority, "
            "or states it as mandatory (\"must\", \"shall\", \"critical\", \"essential\", "
            "legal obligation).",
    "Should": "Important and expected in the first release, but a workaround exists; a source "
              "marks it as medium priority or phrases it as \"should\", \"need\" or "
              "\"highly desirable\".",
    "Could": "Nice to have; phrased as a wish (\"would be helpful\", \"it would be nice\") "
             "or requested by a single stakeholder without supporting sources. Can be postponed.",
}
PRIORITIES = list(PRIORITY_SCALE)

# Deterministic priority evidence in source text, checked in this order.
PRIORITY_MARKER = r"\[\*\s*(high|medium|low)\s+priority\]"
PRIORITY_KEYWORDS = [
    ("Must", r"\b(must|shall|mandatory|critical|essential|required|legal requirement|non-negotiable)\b"),
    ("Should", r"\b(should|needs?|important|highly desirable|want)\b"),
    ("Could", r"\b(would be (nice|helpful|great|useful)|nice[- ]to[- ]have|could|maybe|might|wish)\b"),
]

# Source authority tiers used by deterministic conflict resolution.
# Formal decisions beat elicitation inputs, which beat drafts/background material.
AUTHORITY = {
    "meeting_minutes": 3,
    "interview": 2,
    "survey": 2,
    "email": 2,
    "draft_spec": 1,
    "reference": 1,
    "other": 1,
}
