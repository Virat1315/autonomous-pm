"""
main.py – Standup Service
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import StandupReport, StandupTriggerRequest

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("standup-service")

_last_report: Optional[StandupReport] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Standup Service starting…")
    yield


app = FastAPI(
    title="Autonomous PM – Standup Service",
    description="LLM-powered daily standup generator.",
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
    return {"status": "ok", "service": "standup-service"}


@app.get("/standup/summary", response_model=StandupReport)
async def get_standup_summary():
    if _last_report is None:
        raise HTTPException(404, "No report yet. POST /standup/generate first.")
    return _last_report


@app.post("/standup/generate", response_model=StandupReport)
async def generate_standup(request: StandupTriggerRequest = StandupTriggerRequest()):
    from .agent import StandupAgent
    global _last_report
    try:
        agent  = StandupAgent()
        report = await agent.run(request)
        _last_report = report
        return report
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    except Exception as e:
        logger.error(f"Standup generation failed: {e}")
        raise HTTPException(500, f"Internal error: {e}")
