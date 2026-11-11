"""Split the AI4SE_Playground repository into chunks for RAG.

Chunking is syntax-aware (Python ``ast``): every function/method becomes its own
chunk, each class gets a "header" chunk (signature, docstring, class attributes,
list of method signatures) and each module gets a "module" chunk (docstring,
imports, top-level constants). Chunks longer than MAX_LINES are split by lines
with a small overlap.

Usage:
    python chunk_repo.py [--repo PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = HERE.parent / "AI4SE_Playground"
DEFAULT_OUT = HERE / "chunks.json"

MAX_LINES = 60  # longer chunks are split into windows of this size
OVERLAP_LINES = 5  # lines repeated between consecutive windows


@dataclass
class Chunk:
    id: str  # unique, e.g. "playground/playground/orders.py::Order.__len__"
    file: str  # path relative to the repo root
    kind: str  # "source" | "test"
    type: str  # "module" | "class" | "function" | "method"
    class_name: Optional[str]
    symbol: Optional[str]  # function/method name
    start_line: int
    end_line: int
    is_stub: bool  # body is only ``pass`` (one of the methods to implement)
    code: str  # raw source lines of the chunk
    text: str  # code prefixed with a context header; this is what gets embedded


def _segment(lines: List[str], start: int, end: int) -> str:
    """Return source lines ``start..end`` (1-based, inclusive)."""
    return "".join(lines[start - 1 : end]).rstrip()


def _start_line(node: ast.AST) -> int:
    """First line of a definition, including its decorators."""
    decorators = getattr(node, "decorator_list", [])
    return min([node.lineno] + [d.lineno for d in decorators])


def _is_stub(node: ast.AST) -> bool:
    """True if the function body is just ``pass`` (optionally after a docstring)."""
    body = [
        stmt
        for stmt in node.body
        if not (isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant))
    ]
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def _header(file: str, class_name: Optional[str], symbol: Optional[str], kind: str) -> str:
    parts = [f"# File: {file}", f"# Kind: {kind}"]
    if class_name:
        parts.append(f"# Class: {class_name}")
    if symbol:
        parts.append(f"# Symbol: {symbol}")
    return "\n".join(parts)


def _make_chunks(
    file: str,
    kind: str,
    type_: str,
    class_name: Optional[str],
    symbol: Optional[str],
    lines: List[str],
    start: int,
    end: int,
    is_stub: bool = False,
    code: Optional[str] = None,
) -> List[Chunk]:
    """Create one chunk, or several overlapping windows if it is too long."""
    base_id = f"{file}::" + (".".join(p for p in (class_name, symbol) if p) or "<module>")
    header = _header(file, class_name, symbol, kind)

    if code is not None or end - start + 1 <= MAX_LINES:
        body = code if code is not None else _segment(lines, start, end)
        return [Chunk(base_id, file, kind, type_, class_name, symbol, start, end, is_stub, body, f"{header}\n{body}")]

    chunks = []
    step = MAX_LINES - OVERLAP_LINES
    for part, win_start in enumerate(range(start, end + 1, step), start=1):
        win_end = min(win_start + MAX_LINES - 1, end)
        body = _segment(lines, win_start, win_end)
        chunks.append(
            Chunk(f"{base_id}#part{part}", file, kind, type_, class_name, symbol,
                  win_start, win_end, is_stub, body, f"{header}\n# Part: {part}\n{body}")
        )
        if win_end == end:
            break
    return chunks


def _class_header(node: ast.ClassDef, lines: List[str]) -> str:
    """Class signature + docstring + class attributes + one-line method signatures."""
    out = [_segment(lines, _start_line(node), node.lineno)]
    for stmt in node.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig_end = stmt.body[0].lineno - 1  # signature may span several lines
            sig = " ".join(l.strip() for l in lines[_start_line(stmt) - 1 : sig_end])
            doc = ast.get_docstring(stmt)
            out.append(f"    {sig}  ...  # {doc.splitlines()[0]}" if doc else f"    {sig}  ...")
        else:
            out.append(_segment(lines, _start_line(stmt), stmt.end_lineno))
    return "\n".join(out)


def chunk_file(path: Path, repo_root: Path) -> List[Chunk]:
    source = path.read_text(encoding="utf-8")
    if not source.strip():
        return []
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    rel = path.relative_to(repo_root).as_posix()
    kind = "test" if "/tests/" in f"/{rel}" else "source"

    chunks: List[Chunk] = []
    module_parts: List[str] = []
    module_end = 1

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks += _make_chunks(rel, kind, "function", None, node.name, lines,
                                   _start_line(node), node.end_lineno, _is_stub(node))
        elif isinstance(node, ast.ClassDef):
            chunks += _make_chunks(rel, kind, "class", node.name, None, lines,
                                   _start_line(node), node.end_lineno, code=_class_header(node, lines))
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks += _make_chunks(rel, kind, "method", node.name, stmt.name, lines,
                                           _start_line(stmt), stmt.end_lineno, _is_stub(stmt))
        else:  # docstring, imports, constants, __all__ ...
            module_parts.append(_segment(lines, _start_line(node), node.end_lineno))
            module_end = node.end_lineno

    if module_parts:
        chunks = _make_chunks(rel, kind, "module", None, None, lines, 1, module_end,
                              code="\n".join(module_parts)) + chunks
    return chunks


def chunk_repo(repo_root: Path) -> List[Chunk]:
    chunks: List[Chunk] = []
    for path in sorted(repo_root.rglob("*.py")):
        chunks += chunk_file(path, repo_root)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    chunks = chunk_repo(args.repo)
    args.out.write_text(json.dumps([asdict(c) for c in chunks], indent=2), encoding="utf-8")

    sizes = sorted(len(c.text) for c in chunks)
    by_type = {}
    for c in chunks:
        by_type[f"{c.kind}/{c.type}"] = by_type.get(f"{c.kind}/{c.type}", 0) + 1
    print(f"Wrote {len(chunks)} chunks to {args.out}")
    print(f"  by kind/type: {dict(sorted(by_type.items()))}")
    print(f"  stubs: {sum(c.is_stub for c in chunks)}")
    print(f"  chars per chunk: min={sizes[0]} median={sizes[len(sizes) // 2]} max={sizes[-1]}"
          f"  (~{sizes[len(sizes) // 2] // 4} tokens median)")


if __name__ == "__main__":
    main()
