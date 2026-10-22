"""LangGraph wiring of the requirements-refinement network."""
from langgraph.graph import END, START, StateGraph

from . import agents, preprocess
from .render import render
from .state import GraphState


def build_graph():
    g = StateGraph(GraphState)

    # deterministic nodes
    g.add_node("load_corpus", preprocess.load_corpus)
    g.add_node("annotate_metadata", preprocess.annotate_metadata)
    g.add_node("chunk", preprocess.chunk_documents)
    g.add_node("collect_candidates", agents.collect_candidates)
    g.add_node("number_and_trace", agents.number_and_trace)
    g.add_node("render", render)
    # LLM nodes (resolve_conflicts is deterministic with an LLM arbiter for ties)
    g.add_node("extract", agents.extract)
    g.add_node("plan_structure", agents.plan_structure)
    g.add_node("consolidate", agents.consolidate)
    g.add_node("detect_conflicts", agents.detect_conflicts)
    g.add_node("resolve_conflicts", agents.resolve_conflicts)
    g.add_node("critic", agents.critic)

    g.add_edge(START, "load_corpus")
    g.add_edge("load_corpus", "annotate_metadata")
    g.add_edge("annotate_metadata", "chunk")
    g.add_conditional_edges("chunk", agents.fan_out_extraction, ["extract"])
    g.add_edge("extract", "collect_candidates")
    g.add_edge("collect_candidates", "plan_structure")
    g.add_conditional_edges("plan_structure", agents.fan_out_consolidation, ["consolidate"])
    g.add_edge("consolidate", "number_and_trace")
    g.add_edge("number_and_trace", "detect_conflicts")
    g.add_edge("detect_conflicts", "resolve_conflicts")
    g.add_edge("resolve_conflicts", "critic")
    # feedback loop: critic -> consolidate (flagged areas only), -> number_and_trace
    # (only new duplicate/conflict pairs to apply) or -> render
    g.add_conditional_edges("critic", agents.route_after_critic,
                            ["consolidate", "number_and_trace", "render"])
    g.add_edge("render", END)
    return g.compile()
