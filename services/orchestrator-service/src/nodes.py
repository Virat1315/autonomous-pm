"""
nodes.py – LangGraph node functions.
"""
import logging
from datetime import datetime
from .schemas import WorkflowState
from . import clients

logger = logging.getLogger("orchestrator.nodes")


async def create_ticket_node(state: WorkflowState) -> WorkflowState:
    logger.info("[create_ticket_node] starting")
    if state.slack_payload is None:
        state.errors.append("create_ticket_node: no slack_payload")
        return state
    p = state.slack_payload
    try:
        ticket = await clients.create_ticket(
            title=p.title, description=p.description,
            ticket_type=p.ticket_type, priority=p.priority,
            reported_by=p.reported_by, source=p.source,
            channel=p.channel, slack_message_ts=p.slack_message_ts,
        )
        state.created_ticket = ticket
        state.steps_completed.append(f"create_ticket:{ticket.get('ticket_id')}")
        logger.info(f"[create_ticket_node] created {ticket.get('ticket_id')}")
    except Exception as e:
        err = f"create_ticket_node failed: {e}"
        logger.error(err)
        state.errors.append(err)
    return state


async def prioritize_node(state: WorkflowState) -> WorkflowState:
    logger.info("[prioritize_node] starting")
    try:
        report = await clients.run_prioritization()
        state.priority_report = report
        state.steps_completed.append(f"prioritize:total={report.get('total_tickets','?')}")
    except Exception as e:
        err = f"prioritize_node failed: {e}"
        logger.error(err)
        state.errors.append(err)
    return state


async def standup_node(state: WorkflowState) -> WorkflowState:
    logger.info("[standup_node] starting")
    try:
        report = await clients.generate_standup(
            post_to_slack=state.post_standup_to_slack,
            channel=state.standup_channel,
        )
        state.standup_report = report
        state.steps_completed.append(f"standup:posted={report.get('channel_posted')}")
    except Exception as e:
        err = f"standup_node failed: {e}"
        logger.error(err)
        state.errors.append(err)
    return state
