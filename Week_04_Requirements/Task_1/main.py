"""Run the requirements-refinement network.

Usage:
    python main.py --input data/corpus [--output output]
    python main.py --diagram            # print the graph as Mermaid and exit
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from req_network import llm
from req_network.config import CACHE_DIR_NAME, MAX_CONCURRENCY
from req_network.graph import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", help="directory with the input corpus (searched recursively)")
    parser.add_argument("--output", default="output", help="output directory (default: output)")
    parser.add_argument("--diagram", action="store_true", help="print Mermaid diagram and exit")
    parser.add_argument("--no-cache", action="store_true", help="ignore cached LLM answers")
    args = parser.parse_args()
    if not args.no_cache:
        llm.CACHE_DIR = Path(args.output) / CACHE_DIR_NAME

    graph = build_graph()
    if args.diagram:
        print(graph.get_graph().draw_mermaid())
        return
    if not args.input or not Path(args.input).is_dir():
        parser.error("--input must be an existing directory")

    load_dotenv(Path(__file__).parent / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set (put it into .env, see .env.example)")

    graph.invoke({"input_dir": args.input, "output_dir": args.output},
                 config={"max_concurrency": MAX_CONCURRENCY, "recursion_limit": 100})


if __name__ == "__main__":
    main()
