"""
main.py – Priority Service
LLM-powered ticket prioritisation agent.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .agent import PriorityAgent
from .models import PrioritizeRequest, PriorityReport

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("priority-service")

_last_report: Optional[PriorityReport] = None
_is_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Priority Service starting…")
    yield
    logger.info("Priority Service shutting down")


app = FastAPI(
    title="Autonomous PM – Priority Service",
    description="LLM-powered ticket priority agent. Reads from and writes to the Ticket Service.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "priority-service"}


@app.post("/tickets/prioritize", response_model=PriorityReport)
async def prioritize_tickets(request: PrioritizeRequest = PrioritizeRequest()):
    global _is_running, _last_report
    if _is_running:
        raise HTTPException(409, "Prioritisation already in progress. Try GET /tickets/priorities for cached result.")
    _is_running = True
    try:
        agent = PriorityAgent()
        report = await agent.run(filter_project=request.project_key)
        _last_report = report
        return report
    except Exception as e:
        logger.error(f"Prioritisation failed: {e}")
        raise HTTPException(500, str(e))
    finally:
        _is_running = False


@app.get("/tickets/priorities", response_model=PriorityReport)
async def get_latest_priorities():
    if _last_report is None:
        raise HTTPException(404, "No report yet. POST /tickets/prioritize first.")
    return _last_report
