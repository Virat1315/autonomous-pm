from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PrioritizeRequest(BaseModel):
    project_key: Optional[str] = None


class TicketPriority(BaseModel):
    ticket_id:         str
    title:             str
    current_status:    str
    assigned_priority: str
    priority_score:    int = Field(..., ge=1, le=100)
    reasoning:         str
    updated:           bool = False


class PriorityReport(BaseModel):
    generated_at:       datetime = Field(default_factory=datetime.utcnow)
    total_tickets:      int
    tickets:            List[TicketPriority]
    summary:            str
    high_priority_count: int
    model_used:         str
