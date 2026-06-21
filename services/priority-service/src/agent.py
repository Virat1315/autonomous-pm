"""
agent.py – LLM-powered ticket prioritisation agent.
Uses shared llm_client package.
"""
import os
import sys
import logging
import httpx
from typing import List, Dict, Optional

# Add packages directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../packages/llm-client"))
from llm_client import call_llm, parse_json_response, active_model

from .models import TicketPriority, PriorityReport

logger = logging.getLogger("priority-agent")

TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://localhost:3001")
REQUEST_TIMEOUT    = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

SYSTEM_PROMPT = """You are a senior engineering project manager and expert ticket prioritization agent.

Analyze the list of open software tickets and assign each a priority level and numeric score.

Priority levels (use EXACTLY one of these): Critical, High, Medium, Low
Score: integer from 1 (lowest urgency) to 100 (most critical)

Scoring criteria:
- Production impact or customer-facing severity (highest weight)
- Number of users/teams affected
- Security or data integrity implications
- Business criticality / deadlines implied in title/description
- Dependencies (blocking other work)
- Age of unresolved ticket

Return ONLY valid JSON matching this schema (no markdown, no explanation):
{
  "summary": "<one paragraph overall health summary>",
  "tickets": [
    {
      "ticket_id": "<id>",
      "assigned_priority": "<Critical|High|Medium|Low>",
      "priority_score": <1-100>,
      "reasoning": "<1-2 sentence explanation>"
    }
  ]
}"""


def _build_prompt(tickets: List[Dict]) -> str:
    lines = [f"Prioritize these {len(tickets)} open tickets:\n"]
    for t in tickets:
        lines.append(f"---")
        lines.append(f"ID: {t.get('ticket_id') or t.get('id')}")
        lines.append(f"Title: {t.get('title', 'N/A')}")
        lines.append(f"Description: {t.get('description', 'N/A')}")
        lines.append(f"Status: {t.get('status', 'open')}")
        lines.append(f"Current Priority: {t.get('priority', 'unset')}")
        lines.append(f"Created: {t.get('created_at', 'unknown')}")
        lines.append("")
    return "\n".join(lines)


class PriorityAgent:
    async def fetch_open_tickets(self, project_key: Optional[str] = None) -> List[Dict]:
        params = {"status": "Open", "page_size": 100}
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                resp = await client.get(f"{TICKET_SERVICE_URL}/tickets", params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("tickets", []) if isinstance(data, dict) else data
            except httpx.ConnectError:
                raise RuntimeError(f"Cannot connect to Ticket Service at {TICKET_SERVICE_URL}")

    async def update_ticket_priority(self, ticket_id: str, priority: str, score: int) -> bool:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                resp = await client.put(
                    f"{TICKET_SERVICE_URL}/tickets/{ticket_id}",
                    json={"priority": priority, "priority_score": score},
                )
                return resp.status_code in (200, 204)
            except Exception as e:
                logger.warning(f"Failed to update ticket {ticket_id}: {e}")
                return False

    async def run(self, filter_project: Optional[str] = None) -> PriorityReport:
        logger.info(f"PriorityAgent starting (project: {filter_project or 'all'})")
        raw_tickets = await self.fetch_open_tickets(filter_project)

        if not raw_tickets:
            return PriorityReport(
                total_tickets=0,
                tickets=[],
                summary="No open tickets found.",
                high_priority_count=0,
                model_used=active_model(),
            )

        logger.info(f"Fetched {len(raw_tickets)} tickets")
        prompt = _build_prompt(raw_tickets)

        try:
            raw = await call_llm(prompt, SYSTEM_PROMPT, temperature=0.2)
            data = parse_json_response(raw)
        except Exception as e:
            raise RuntimeError(f"LLM analysis failed: {e}")

        summary     = data.get("summary", "No summary.")
        prioritized = data.get("tickets", [])

        ticket_map = {str(t.get("ticket_id") or t.get("id", "")): t for t in raw_tickets}
        results: List[TicketPriority] = []
        high_count = 0

        for p in prioritized:
            tid = str(p.get("ticket_id", ""))
            source = ticket_map.get(tid, {})
            pl = p.get("assigned_priority", "Medium")
            score = int(p.get("priority_score", 50))
            updated = await self.update_ticket_priority(tid, pl, score)

            results.append(TicketPriority(
                ticket_id=tid,
                title=source.get("title", "Unknown"),
                current_status=source.get("status", "Open"),
                assigned_priority=pl,
                priority_score=score,
                reasoning=p.get("reasoning", ""),
                updated=updated,
            ))
            if pl in ("Critical", "High"):
                high_count += 1

        results.sort(key=lambda x: x.priority_score, reverse=True)
        logger.info(f"PriorityAgent done: {len(results)} tickets, {high_count} high/critical")

        return PriorityReport(
            total_tickets=len(results),
            tickets=results,
            summary=summary,
            high_priority_count=high_count,
            model_used=active_model(),
        )
