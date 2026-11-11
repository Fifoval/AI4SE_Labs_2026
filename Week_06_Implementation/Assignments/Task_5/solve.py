"""Solve the coding tasks in missing_code.json with the RAG pipeline from Tasks 2-4.

For every task:
    1. build a textual task from the JSON entry (solve() only gets this text and finds the
       target file/class/method in it),
    2. retrieve the top-5 chunks for it (Task 4),
    3. send the task + chunks to an LLM,
    4. write the returned method into the target source file (replacing the stub).
Then run the playground's unit tests.

Usage:
    python solve.py [--model gpt-5-mini] [--restore]
        --restore   copy the original stubbed files back before solving
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "Task_3"))
sys.path.insert(0, str(ROOT / "Task_4"))
from embed_chunks import EmbeddingStore  # noqa: E402
from match import Match, retrieve, task_to_query  # noqa: E402

REPO = ROOT / "AI4SE_Playground"
ORIGINAL = HERE / "original"  # stubbed sources, for --restore
RUNS = HERE / "runs"  # prompt + answer log per task
MISSING_CODE = ROOT / "missing_code.json"

ALLOWED_MODELS = {"gpt-6-luna", "gpt-5.6-luna", "gpt-5.4-nano", "gpt-5-nano",
                  "gpt-5-mini", "gpt-4.1-nano", "gpt-4o-mini"}
TOP_N = 5
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """You are a senior Python developer implementing one missing method in an existing code base.
Rules:
- Return ONLY the complete method definition (decorators, `def` line with the exact given signature, the given docstring, body) in a single ```python block.
- Keep the signature exactly as in the stub. Do not return the surrounding class or any other code.
- Use only names that exist in the provided context (attributes, helpers, imports). Do not add imports.
- Follow the conventions of the surrounding code (validation, exceptions, private attributes)."""


def format_chunks(matches: List[Match]) -> str:
    parts = []
    for i, m in enumerate(matches, 1):
        c = m.chunk
        parts.append(f"### Context {i}: {c['id']} (lines {c['start_line']}-{c['end_line']}, "
                     f"similarity {m.score:.3f})\n```python\n{c['code']}\n```")
    return "\n\n".join(parts)


def build_prompt(task: str, stub: str, matches: List[Match], imports: Optional[str]) -> str:
    imports_part = (f"## Imports of the target file (the only external names available there)\n"
                    f"```python\n{imports}\n```\n\n") if imports is not None else ""
    return (f"## Task\n{task}\n\n"
            f"## Stub to replace\n```python\n{stub}\n```\n\n"
            f"{imports_part}"
            f"## Relevant code from the repository (retrieved)\n{format_chunks(matches)}\n\n"
            "Write the implementation of the method now.")


def extract_code(answer: str) -> str:
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", answer, flags=re.S)
    return textwrap.dedent(blocks[0] if blocks else answer).strip("\n")


def find_method(tree: ast.Module, class_name: str, method: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == method:
                    return stmt
    raise LookupError(f"{class_name}.{method} not found")


def method_span(node: ast.FunctionDef) -> tuple[int, int]:
    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
    return start, node.end_lineno


def read_stub(path: Path, class_name: str, method: str) -> str:
    source = path.read_text(encoding="utf-8")
    start, end = method_span(find_method(ast.parse(source), class_name, method))
    return "".join(source.splitlines(keepends=True)[start - 1:end]).rstrip()


def read_imports(path: Path) -> str:
    """Import statements of the target module (names the new method may use)."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    return "".join("".join(lines[n.lineno - 1:n.end_lineno]) for n in ast.parse(source).body
                   if isinstance(n, (ast.Import, ast.ImportFrom))).rstrip()


def write_method(path: Path, class_name: str, method: str, code: str) -> None:
    """Replace the method in ``path`` with ``code``; raise if the result is not valid."""
    new_tree = ast.parse(code)  # SyntaxError if the answer is not valid Python
    defs = [n for n in new_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(defs) != 1 or defs[0].name != method:
        raise ValueError(f"answer must contain exactly one definition of {method}")

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    start, end = method_span(find_method(ast.parse(source), class_name, method))
    indent = re.match(r"\s*", lines[start - 1]).group()
    new_lines = [textwrap.indent(code, indent) + "\n"]
    updated = "".join(lines[:start - 1] + new_lines + lines[end:])
    find_method(ast.parse(updated), class_name, method)  # whole file must still parse
    path.write_text(updated, encoding="utf-8")


TARGET_RE = re.compile(r"method\s+`?(?P<method>\w+)`?\s+of\s+class\s+`?(?P<cls>\w+)`?\s+in\s+`?(?P<file>[\w./\\-]+\.py)")


def parse_target(task: str) -> tuple[str, str, str]:
    """Find (file, class, method) in a task like "Implement the method m of class C in path/x.py. ..."."""
    match = TARGET_RE.search(task)
    if not match:
        raise ValueError("task must name the target: 'method <name> of class <Class> in <file.py>'")
    return match["file"].replace("\\", "/"), match["cls"], match["method"]


def solve(task: str, store: EmbeddingStore, client: OpenAI, model: str,
          log_name: Optional[str] = None, naive: bool = False) -> dict:
    """Solve one textual task and write the result into the target file named in the task.

    ``naive`` reproduces run 1: stubs may be retrieved and the target file's imports are not shown.
    """
    file, class_name, method = parse_target(task)
    path = REPO / file
    matches = retrieve(store, task, TOP_N, skip_stubs=not naive)
    stub = read_stub(path, class_name, method)
    imports = None if naive else read_imports(path)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(task, stub, matches, imports)}]

    log = [f"# {class_name}.{method}\n\nModel: {model}\n\n## Prompt\n\n{messages[1]['content']}"]
    result = {"task": f"{class_name}.{method}", "file": file,
              "retrieved": [m.chunk["id"] for m in matches], "attempts": 0, "written": False}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = client.chat.completions.create(model=model, messages=messages)
        answer = response.choices[0].message.content or ""
        log.append(f"## Answer (attempt {attempt})\n\n{answer}")
        result["attempts"] = attempt
        try:
            write_method(path, class_name, method, extract_code(answer))
            result["written"] = True
            break
        except (SyntaxError, ValueError, LookupError) as exc:  # ask the model to fix its answer
            log.append(f"## Rejected: {exc}")
            messages += [{"role": "assistant", "content": answer},
                         {"role": "user", "content": f"Your answer was rejected: {exc}. "
                                                     "Return only the corrected method in one ```python block."}]
            result["error"] = str(exc)

    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{log_name or method}.md").write_text("\n\n".join(log) + "\n", encoding="utf-8")
    return result


def run_tests() -> str:
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                          cwd=REPO / "playground", capture_output=True, text=True)
    return proc.stdout + proc.stderr


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="gpt-5-mini", choices=sorted(ALLOWED_MODELS))
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--naive", action="store_true", help="run-1 setup (stubs retrievable, no imports)")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    if args.restore:
        for f in ORIGINAL.glob("*.py"):
            shutil.copy(f, REPO / "playground" / "playground" / f.name)

    store = EmbeddingStore.load()
    client = OpenAI(max_retries=5, timeout=300)
    tasks = json.loads(MISSING_CODE.read_text(encoding="utf-8"))
    results = []
    for t in tasks:
        res = solve(task_to_query(t), store, client, args.model,
                    log_name=f"{t['class']}.{t['method']}", naive=args.naive)
        print(f"{res['task']:<34} written={res['written']} attempts={res['attempts']}")
        results.append(res)

    (HERE / "results.json").write_text(json.dumps({"model": args.model, "naive": args.naive,
                                                   "tasks": results}, indent=2),
                                       encoding="utf-8")
    output = run_tests()
    (HERE / "tests_after.txt").write_text(output, encoding="utf-8")
    print("\n".join(output.strip().splitlines()[-3:]))


if __name__ == "__main__":
    main()
