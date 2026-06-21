"""
schemas.py – Pydantic v2 models.
These are the CANONICAL enum values. ALL services must use these exact strings.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ── Canonical enumerations ────────────────────────────────────────────────────
VALID_STATUSES   = {"Open", "In Progress", "In Review", "Done", "Closed", "Blocked"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_TYPES      = {"bug", "feature", "task", "incident", "code_review", "epic", "story", "spike"}
VALID_SOURCES    = {"slack", "slack-command", "github", "api", "orchestrator", "agent"}


class TicketCreate(BaseModel):
    title:            str           = Field(..., min_length=1, max_length=200)
    description:      Optional[str] = None
    ticket_type:      Optional[str] = Field("task")
    priority:         Optional[str] = Field("Medium")
    assignee:         Optional[str] = None
    reported_by:      Optional[str] = None
    source:           Optional[str] = Field("api")
    channel:          Optional[str] = None
    slack_message_ts: Optional[str] = None


class TicketUpdate(BaseModel):
    title:            Optional[str] = Field(None, min_length=1, max_length=200)
    description:      Optional[str] = None
    ticket_type:      Optional[str] = None
    status:           Optional[str] = None
    priority:         Optional[str] = None
    priority_score:   Optional[int] = Field(None, ge=1, le=100)
    assignee:         Optional[str] = None
    reported_by:      Optional[str] = None


class TicketAssign(BaseModel):
    assignee: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    id:               int
    ticket_id:        str
    title:            str
    description:      Optional[str]
    ticket_type:      str
    status:           str
    priority:         str
    priority_score:   Optional[int]
    assignee:         Optional[str]
    reported_by:      Optional[str]
    source:           Optional[str]
    channel:          Optional[str]
    slack_message_ts: Optional[str]
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    tickets:   List[TicketResponse]
    total:     int
    page:      int
    page_size: int


class DashboardStats(BaseModel):
    total_tickets:     int
    active_tickets:    int
    completed_tickets: int
    blocked_tickets:   int
    critical_tickets:  int
    success_rate:      float
    by_status:         Dict[str, int]
    by_priority:       Dict[str, int]
