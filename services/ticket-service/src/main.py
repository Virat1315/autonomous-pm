"""
main.py – Autonomous PM Ticket Service
Canonical ticket store for the entire platform.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import tickets, stats

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("ticket-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ticket Service starting – initialising database…")
    await init_db()
    logger.info("Database ready")
    yield
    logger.info("Ticket Service shutting down")


app = FastAPI(
    title="Autonomous PM – Ticket Service",
    description="Canonical ticket store. Source of truth for all tickets in the platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(stats.router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "ticket-service", "version": "1.0.0"}
