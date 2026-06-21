from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class TicketSnapshot(BaseModel):
    ticket_id:   str
    title:       str
    status:      str
    priority:    str
    assignee:    Optional[str]
    ticket_type: str
    updated_at:  datetime


class AssigneeSummary(BaseModel):
    assignee:     str
    ticket_count: int
    tickets:      List[TicketSnapshot]
    blurb:        str


class StandupReport(BaseModel):
    report_date:       date
    generated_at:      datetime
    channel_posted:    bool = False
    total_tickets:     int
    open_count:        int
    in_progress_count: int
    blocked_count:     int
    done_today_count:  int
    critical_count:    int
    by_assignee:       List[AssigneeSummary]
    summary:           str
    model_used:        str


class StandupTriggerRequest(BaseModel):
    post_to_slack: bool          = Field(True)
    channel:       Optional[str] = None
    date_filter:   Optional[date] = None
