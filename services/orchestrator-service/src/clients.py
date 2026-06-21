"""
clients.py – HTTP clients to all downstream services.
"""
import os
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("orchestrator.clients")

TICKET_SERVICE_URL   = os.getenv("TICKET_SERVICE_URL",   "http://localhost:3001")
PRIORITY_SERVICE_URL = os.getenv("PRIORITY_SERVICE_URL", "http://localhost:3003")
STANDUP_SERVICE_URL  = os.getenv("STANDUP_SERVICE_URL",  "http://localhost:3004")
TIMEOUT              = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


async def create_ticket(
    title: str,
    description: Optional[str] = None,
    ticket_type: str = "task",
    priority: str = "Medium",
    reported_by: Optional[str] = None,
    source: str = "orchestrator",
    channel: Optional[str] = None,
    slack_message_ts: Optional[str] = None,
) -> Dict[str, Any]:
    payload = {k: v for k, v in {
        "title": title, "description": description, "ticket_type": ticket_type,
        "priority": priority, "reported_by": reported_by, "source": source,
        "channel": channel, "slack_message_ts": slack_message_ts,
    }.items() if v is not None}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        resp = await c.post(f"{TICKET_SERVICE_URL}/tickets", json=payload)
        resp.raise_for_status()
        return resp.json()


async def update_ticket_status(ticket_id: str, status: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        resp = await c.put(f"{TICKET_SERVICE_URL}/tickets/{ticket_id}", json={"status": status})
        resp.raise_for_status()
        return resp.json()


async def run_prioritization(project_key: Optional[str] = None) -> Dict[str, Any]:
    body = {}
    if project_key:
        body["project_key"] = project_key
    async with httpx.AsyncClient(timeout=120) as c:
        resp = await c.post(f"{PRIORITY_SERVICE_URL}/tickets/prioritize", json=body)
        if resp.status_code == 409:
            logger.warning("Priority agent busy; fetching cached report")
            cached = await c.get(f"{PRIORITY_SERVICE_URL}/tickets/priorities")
            return cached.json() if cached.status_code == 200 else {"note": "prioritization_in_progress"}
        resp.raise_for_status()
        return resp.json()


async def generate_standup(post_to_slack: bool = True, channel: Optional[str] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"post_to_slack": post_to_slack}
    if channel:
        body["channel"] = channel
    async with httpx.AsyncClient(timeout=120) as c:
        resp = await c.post(f"{STANDUP_SERVICE_URL}/standup/generate", json=body)
        resp.raise_for_status()
        return resp.json()


async def check_health(url: str, name: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            resp = await c.get(f"{url}/health")
            ok = resp.status_code == 200
            logger.info(f"  {'✓' if ok else '✗'} {name}")
            return ok
    except Exception as e:
        logger.warning(f"  ✗ {name} unreachable: {e}")
        return False


async def check_all_services() -> Dict[str, bool]:
    return {
        "ticket_service":   await check_health(TICKET_SERVICE_URL,   "Ticket Service"),
        "priority_service": await check_health(PRIORITY_SERVICE_URL, "Priority Service"),
        "standup_service":  await check_health(STANDUP_SERVICE_URL,  "Standup Service"),
    }
