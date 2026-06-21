"""
workflows.py – LangGraph StateGraph definitions.
"""
import logging
from langgraph.graph import StateGraph, END
from .schemas import WorkflowState, TriggerKind
from .nodes import create_ticket_node, prioritize_node, standup_node

logger = logging.getLogger("orchestrator.workflows")


def _wrap(node_fn):
    async def wrapped(state: dict) -> dict:
        ws = WorkflowState(**state)
        updated = await node_fn(ws)
        return updated.model_dump()
    wrapped.__name__ = node_fn.__name__
    return wrapped


def build_slack_graph():
    g = StateGraph(dict)
    g.add_node("create_ticket", _wrap(create_ticket_node))
    g.add_node("prioritize",    _wrap(prioritize_node))
    g.set_entry_point("create_ticket")
    g.add_edge("create_ticket", "prioritize")
    g.add_edge("prioritize",    END)
    return g.compile()


def build_standup_graph():
    g = StateGraph(dict)
    g.add_node("standup", _wrap(standup_node))
    g.set_entry_point("standup")
    g.add_edge("standup", END)
    return g.compile()


def build_full_pipeline_graph():
    g = StateGraph(dict)
    g.add_node("create_ticket", _wrap(create_ticket_node))
    g.add_node("prioritize",    _wrap(prioritize_node))
    g.add_node("standup",       _wrap(standup_node))
    g.set_entry_point("create_ticket")
    g.add_edge("create_ticket", "prioritize")
    g.add_edge("prioritize",    "standup")
    g.add_edge("standup",       END)
    return g.compile()


_REGISTRY = {
    "slack_message":  build_slack_graph,
    "manual_standup": build_standup_graph,
    "full_pipeline":  build_full_pipeline_graph,
}


def get_graph(trigger: TriggerKind):
    builder = _REGISTRY.get(trigger)
    return builder() if builder else None
