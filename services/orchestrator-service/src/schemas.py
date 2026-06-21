from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

TriggerKind = Literal["slack_message", "github_event", "manual_standup", "full_pipeline"]


class SlackMessagePayload(BaseModel):
    title:            str
    description:      Optional[str] = None
    ticket_type:      str = "task"
    priority:         str = "Medium"
    reported_by:      Optional[str] = None
    source:           str = "slack"
    channel:          Optional[str] = None
    slack_message_ts: Optional[str] = None


class GitHubEventPayload(BaseModel):
    ticket_id:  str
    new_status: str
    pr_url:     Optional[str] = None


class OrchestrateRequest(BaseModel):
    trigger:               TriggerKind
    slack_payload:         Optional[SlackMessagePayload]  = None
    github_payload:        Optional[GitHubEventPayload]   = None
    post_standup_to_slack: bool          = True
    standup_channel:       Optional[str] = None


class WorkflowState(BaseModel):
    trigger:               TriggerKind
    slack_payload:         Optional[SlackMessagePayload]  = None
    github_payload:        Optional[GitHubEventPayload]   = None
    created_ticket:        Optional[Dict[str, Any]]       = None
    priority_report:       Optional[Dict[str, Any]]       = None
    standup_report:        Optional[Dict[str, Any]]       = None
    post_standup_to_slack: bool          = True
    standup_channel:       Optional[str] = None
    steps_completed:       List[str]     = Field(default_factory=list)
    errors:                List[str]     = Field(default_factory=list)
    started_at:            datetime      = Field(default_factory=datetime.utcnow)
    finished_at:           Optional[datetime] = None


class OrchestrateResponse(BaseModel):
    trigger:         TriggerKind
    steps_completed: List[str]
    errors:          List[str]
    started_at:      datetime
    finished_at:     datetime
    created_ticket:  Optional[Dict[str, Any]] = None
    priority_report: Optional[Dict[str, Any]] = None
    standup_report:  Optional[Dict[str, Any]] = None
