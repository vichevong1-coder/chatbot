"""Builds the LangGraph state machine — the tutor's brain (architecture.md §2).

Phase 1 wires exactly five nodes: input_normalizer, safety_gate, intent_router,
solve, explain. clarify / check_answer / recommend_next arrive in Phase 2 and
their modules stay empty stubs until then.

Service clients are bound into the node callables here (functools.partial), so
the node functions themselves stay pure ``(state, clients) -> update`` and tests
can drive them with fakes through the app factory.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph

from app.core.graph import edges
from app.core.graph.nodes.explain import explain
from app.core.graph.nodes.input_normalizer import input_normalizer
from app.core.graph.nodes.intent_router import intent_router
from app.core.graph.nodes.safety_gate import safety_gate
from app.core.graph.nodes.solve import solve
from app.core.graph.nodes.check_answer import check_answer
from app.core.graph.state import GraphState
from app.infrastructure.service_clients import ServiceClients


def build_graph(clients: ServiceClients):
    """Compile the Phase-1 graph with the given clients bound in."""
    graph = StateGraph(GraphState)

    graph.add_node("input_normalizer", input_normalizer)
    graph.add_node("safety_gate", partial(safety_gate, clients=clients))
    graph.add_node("intent_router", intent_router)
    graph.add_node("solve", partial(solve, clients=clients))
    graph.add_node("explain", partial(explain, clients=clients))
    graph.add_node("check_answer", partial(check_answer, clients=clients))

    graph.add_edge(START, "input_normalizer")
    graph.add_conditional_edges(
        "input_normalizer", edges.after_input_normalizer, ["safety_gate", END]
    )
    graph.add_conditional_edges(
        "safety_gate", edges.after_safety_gate, ["intent_router", END]
    )
    graph.add_conditional_edges(
        "intent_router", edges.after_intent_router, ["solve", "explain", "check_answer"]
    )
    graph.add_conditional_edges(
        "check_answer", edges.after_check_answer, ["explain", END]
    )
    graph.add_conditional_edges("solve", edges.after_solve, ["explain", END])
    graph.add_edge("explain", END)

    return graph.compile()
