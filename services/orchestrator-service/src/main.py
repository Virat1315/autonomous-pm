"""
main.py – Orchestrator Service
"""
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import OrchestrateRequest, OrchestrateResponse, WorkflowState
from .workflows import get_graph
from . import clients

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Orchestrator Service starting – checking downstream services…")
    statuses = await clients.check_all_services()
    for name, ok in statuses.items():
        logger.log(logging.INFO if ok else logging.WARNING, f"  {'✓' if ok else '✗'} {name}: {'up' if ok else 'DOWN'}")
    yield
    logger.info("Orchestrator Service shutting down")


app = FastAPI(
    title="Autonomous PM – Orchestrator Service",
    description="LangGraph coordinator. Routes triggers through agent workflows.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/orchestrate/start", response_model=OrchestrateResponse)
async def orchestrate_start(request: OrchestrateRequest):
    logger.info(f"Workflow requested: trigger={request.trigger}")

    if request.trigger in ("slack_message", "full_pipeline") and not request.slack_payload:
        raise HTTPException(422, f"trigger='{request.trigger}' requires slack_payload")

    # github_event – pass-through (status already updated by Unit 3)
    if request.trigger == "github_event":
        if not request.github_payload:
            raise HTTPException(422, "trigger='github_event' requires github_payload")
        now = datetime.utcnow()
        return OrchestrateResponse(
            trigger=request.trigger,
            steps_completed=[f"github_event_recorded:ticket={request.github_payload.ticket_id}"],
            errors=[],
            started_at=now,
            finished_at=now,
        )

    graph = get_graph(request.trigger)
    if graph is None:
        raise HTTPException(400, f"No workflow for trigger='{request.trigger}'")

    initial_state = WorkflowState(
        trigger=request.trigger,
        slack_payload=request.slack_payload,
        github_payload=request.github_payload,
        post_standup_to_slack=request.post_standup_to_slack,
        standup_channel=request.standup_channel,
    )

    try:
        result_dict  = await graph.ainvoke(initial_state.model_dump())
        final_state  = WorkflowState(**result_dict)
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        raise HTTPException(500, f"Workflow failed: {e}")

    final_state.finished_at = datetime.utcnow()
    logger.info(f"Workflow complete: {final_state.steps_completed} errors={final_state.errors}")

    return OrchestrateResponse(
        trigger=final_state.trigger,
        steps_completed=final_state.steps_completed,
        errors=final_state.errors,
        started_at=final_state.started_at,
        finished_at=final_state.finished_at,
        created_ticket=final_state.created_ticket,
        priority_report=final_state.priority_report,
        standup_report=final_state.standup_report,
    )


@app.get("/orchestrate/workflows")
async def list_workflows():
    return {"workflows": [
        {"trigger": "slack_message",  "nodes": ["create_ticket", "prioritize"]},
        {"trigger": "github_event",   "nodes": ["pass-through"]},
        {"trigger": "manual_standup", "nodes": ["standup"]},
        {"trigger": "full_pipeline",  "nodes": ["create_ticket", "prioritize", "standup"]},
    ]}


@app.get("/health")
async def health():
    statuses = await clients.check_all_services()
    return {"status": "ok" if all(statuses.values()) else "degraded", "downstream": statuses}
