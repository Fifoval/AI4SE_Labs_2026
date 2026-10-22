"""Deterministic (non-AI) nodes: corpus loading, metadata annotation, chunking."""
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from .config import AUTHORITY, INPUT_EXTENSIONS, MAX_CHUNK_CHARS
from .state import GraphState

_MONTHS = ("January|February|March|April|May|June|July|August|September|"
           "October|November|December")
_DATE_HEADER = re.compile(r"^\s*date:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_DATE_LABEL = re.compile(r"^[\w ]*date:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_LONG_DATE = re.compile(rf"\b(?:{_MONTHS})\s+\d{{1,2}},\s+\d{{4}}\b")
_ISO_DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_HEAD_CHARS = 1500


def load_corpus(state: GraphState) -> dict:
    """Read every text file under input_dir (recursively); ids are stable by path order."""
    root = Path(state["input_dir"])
    files = sorted(p for p in root.rglob("*")
                   if p.is_file() and p.suffix.lower() in INPUT_EXTENSIONS)
    if not files:
        raise FileNotFoundError(f"No input documents ({INPUT_EXTENSIONS}) in {root}")
    docs = []
    for i, path in enumerate(files, 1):
        docs.append({
            "doc_id": f"D{i:02d}",
            "path": path.relative_to(root).as_posix(),
            "text": path.read_text(encoding="utf-8", errors="replace"),
        })
    print(f"[load_corpus] {len(docs)} documents")
    return {"documents": docs}


_TYPE_KEYWORDS = [  # checked in order: file name first, then document head
    ("interview", "interview"),
    ("survey", "survey"),
    ("minutes", "meeting_minutes"),
    ("meeting", "meeting_minutes"),
    ("srs", "draft_spec"),
    ("draft", "draft_spec"),
    ("requirements specification", "draft_spec"),
    ("reference", "reference"),
    ("manual", "reference"),
]


def _doc_type(path: str, text: str) -> str:
    name = path.lower()
    if name.endswith(".eml") or re.match(r"(from|to|subject):", text.lower()):
        return "email"
    for haystack in (name, text[:500].lower()):
        for keyword, doc_type in _TYPE_KEYWORDS:
            if keyword in haystack:
                return doc_type
    return "other"


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    try:
        return parsedate_to_datetime(raw).replace(tzinfo=None)
    except (TypeError, ValueError):
        pass
    if m := _LONG_DATE.search(raw):
        return datetime.strptime(m.group(0).replace("  ", " "), "%B %d, %Y")
    if m := _ISO_DATE.search(raw):
        return datetime(*map(int, m.groups()))
    return None


def _content_date(text: str, doc_type: str) -> datetime | None:
    """E-mail threads: newest 'Date:' header. Other documents: first '... Date:' line
    in the document head; fallback: latest long-form date in the head."""
    if doc_type == "email":
        dates = [d for raw in _DATE_HEADER.findall(text) if (d := _parse_date(raw))]
        if dates:
            return max(dates)
    head = text[:_HEAD_CHARS]
    for raw in _DATE_LABEL.findall(head):
        if d := _parse_date(raw):
            return d
    dates = [d for m in _LONG_DATE.findall(head) if (d := _parse_date(m))]
    return max(dates) if dates else None


def annotate_metadata(state: GraphState) -> dict:
    """Attach doc type, date, authority tier and data-quality warnings to each document."""
    out = []
    for doc in state["documents"]:
        warnings = []
        doc_type = _doc_type(doc["path"], doc["text"])
        content_date = _content_date(doc["text"], doc_type)
        m = _ISO_DATE.search(doc["path"])
        name_date = datetime(*map(int, m.groups())) if m else None
        if content_date and name_date and content_date.date() != name_date.date():
            warnings.append(f"File name date {name_date:%Y-%m-%d} differs from document "
                            f"date {content_date:%Y-%m-%d}; document date used.")
        date = content_date or name_date
        if date is None:
            warnings.append("No date found; treated as oldest in conflict resolution.")
        out.append({**doc,
                    "doc_type": doc_type,
                    "date": date.strftime("%Y-%m-%d") if date else "",
                    "authority": AUTHORITY.get(doc_type, 1),
                    "warnings": warnings})
    for d in out:
        print(f"[metadata] {d['doc_id']} {d['doc_type']:<15} {d['date'] or '?':<10} "
              f"auth={d['authority']} {d['path']}")
    return {"documents": out}


def chunk_documents(state: GraphState) -> dict:
    """Split documents into paragraph-aligned chunks no longer than MAX_CHUNK_CHARS."""
    chunks = []
    for doc in state["documents"]:
        parts, buf = [], ""
        for para in re.split(r"\n\s*\n", doc["text"]):
            if buf and len(buf) + len(para) + 2 > MAX_CHUNK_CHARS:
                parts.append(buf)
                buf = ""
            buf = f"{buf}\n\n{para}" if buf else para
        if buf.strip():
            parts.append(buf)
        for i, text in enumerate(parts, 1):
            chunks.append({"chunk_id": f"{doc['doc_id']}.{i}", "doc_id": doc["doc_id"],
                           "doc_type": doc["doc_type"], "date": doc["date"],
                           "path": doc["path"], "text": text})
    print(f"[chunk] {len(chunks)} chunks")
    return {"chunks": chunks}
