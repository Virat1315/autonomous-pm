"""
crud.py – Database operations supporting both MongoDB and SQL backends.
The router layer doesn't know or care which backend is active.
"""
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException

from .schemas import (
    TicketCreate, TicketUpdate,
    VALID_STATUSES, VALID_PRIORITIES, VALID_TYPES,
)

DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sql").lower()


def _validate(ticket_type=None, priority=None, status=None):
    if ticket_type and ticket_type not in VALID_TYPES:
        raise HTTPException(422, f"Invalid ticket_type. Must be one of: {sorted(VALID_TYPES)}")
    if priority and priority not in VALID_PRIORITIES:
        raise HTTPException(422, f"Invalid priority. Must be one of: {sorted(VALID_PRIORITIES)}")
    if status and status not in VALID_STATUSES:
        raise HTTPException(422, f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}")


# ─────────────────────────────────────────────────────────────────────────────
# MongoDB implementation
# ─────────────────────────────────────────────────────────────────────────────

def _mongo_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to the canonical response dict."""
    return {
        "id":               doc["id"],
        "ticket_id":        f"APM-{doc['id']}",
        "title":            doc["title"],
        "description":      doc.get("description"),
        "ticket_type":      doc.get("ticket_type", "task"),
        "status":           doc.get("status", "Open"),
        "priority":         doc.get("priority", "Medium"),
        "priority_score":   doc.get("priority_score"),
        "assignee":         doc.get("assignee"),
        "reported_by":      doc.get("reported_by"),
        "source":           doc.get("source"),
        "channel":          doc.get("channel"),
        "slack_message_ts": doc.get("slack_message_ts"),
        "created_at":       doc.get("created_at", datetime.now(timezone.utc)),
        "updated_at":       doc.get("updated_at", datetime.now(timezone.utc)),
    }


async def _mongo_next_id(db) -> int:
    result = await db.counters.find_one_and_update(
        {"_id": "ticket_seq"},
        {"$inc": {"seq": 1}},
        return_document=True,
    )
    return result["seq"]


async def _mongo_resolve(db, ticket_id: str):
    raw_id = _parse_id(ticket_id)
    doc = await db.tickets.find_one({"id": raw_id})
    if not doc:
        raise HTTPException(404, f"Ticket '{ticket_id}' not found")
    return doc


async def _mongo_create(db, data: TicketCreate) -> dict:
    _validate(ticket_type=data.ticket_type, priority=data.priority)
    now = datetime.now(timezone.utc)
    seq = await _mongo_next_id(db)
    doc = {
        "id":               seq,
        "title":            data.title,
        "description":      data.description,
        "ticket_type":      data.ticket_type or "task",
        "status":           "Open",
        "priority":         data.priority or "Medium",
        "priority_score":   None,
        "assignee":         data.assignee,
        "reported_by":      data.reported_by,
        "source":           data.source or "api",
        "channel":          data.channel,
        "slack_message_ts": data.slack_message_ts,
        "created_at":       now,
        "updated_at":       now,
    }
    await db.tickets.insert_one(doc)
    return _mongo_to_dict(doc)


async def _mongo_get(db, ticket_id: str) -> dict:
    return _mongo_to_dict(await _mongo_resolve(db, ticket_id))


async def _mongo_list(db, status=None, priority=None, ticket_type=None,
                       assignee=None, search=None, page=1, page_size=20) -> dict:
    query = {}
    if status:      query["status"]      = status
    if priority:    query["priority"]    = priority
    if ticket_type: query["ticket_type"] = ticket_type
    if assignee:    query["assignee"]    = assignee
    if search:
        query["$text"] = {"$search": search}

    total = await db.tickets.count_documents(query)
    cursor = db.tickets.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    docs = await cursor.to_list(length=page_size)
    return {
        "tickets":   [_mongo_to_dict(d) for d in docs],
        "total":     total,
        "page":      page,
        "page_size": page_size,
    }


async def _mongo_update(db, ticket_id: str, data: TicketUpdate) -> dict:
    doc = await _mongo_resolve(db, ticket_id)
    _validate(ticket_type=data.ticket_type, priority=data.priority, status=data.status)
    updates = {"updated_at": datetime.now(timezone.utc)}
    if data.title is not None:          updates["title"]          = data.title
    if data.description is not None:    updates["description"]    = data.description
    if data.ticket_type is not None:    updates["ticket_type"]    = data.ticket_type
    if data.status is not None:         updates["status"]         = data.status
    if data.priority is not None:       updates["priority"]       = data.priority
    if data.priority_score is not None: updates["priority_score"] = data.priority_score
    if data.assignee is not None:       updates["assignee"]       = data.assignee
    if data.reported_by is not None:    updates["reported_by"]    = data.reported_by
    await db.tickets.update_one({"id": doc["id"]}, {"$set": updates})
    updated = await db.tickets.find_one({"id": doc["id"]})
    return _mongo_to_dict(updated)


async def _mongo_assign(db, ticket_id: str, assignee: str) -> dict:
    doc = await _mongo_resolve(db, ticket_id)
    await db.tickets.update_one(
        {"id": doc["id"]},
        {"$set": {"assignee": assignee, "updated_at": datetime.now(timezone.utc)}},
    )
    updated = await db.tickets.find_one({"id": doc["id"]})
    return _mongo_to_dict(updated)


async def _mongo_delete(db, ticket_id: str) -> dict:
    doc = await _mongo_resolve(db, ticket_id)
    await db.tickets.delete_one({"id": doc["id"]})
    return {"deleted": True, "ticket_id": ticket_id}


async def _mongo_stats(db) -> dict:
    docs = await db.tickets.find({}).to_list(length=None)
    by_status: dict   = {}
    by_priority: dict = {}
    active_statuses   = {"Open", "In Progress", "In Review"}
    done_statuses     = {"Done", "Closed"}
    for d in docs:
        s = d.get("status",   "Open")
        p = d.get("priority", "Medium")
        by_status[s]   = by_status.get(s, 0)   + 1
        by_priority[p] = by_priority.get(p, 0) + 1
    total     = len(docs)
    active    = sum(v for k, v in by_status.items() if k in active_statuses)
    completed = sum(v for k, v in by_status.items() if k in done_statuses)
    blocked   = by_status.get("Blocked", 0)
    critical  = by_priority.get("Critical", 0)
    return {
        "total_tickets":     total,
        "active_tickets":    active,
        "completed_tickets": completed,
        "blocked_tickets":   blocked,
        "critical_tickets":  critical,
        "success_rate":      round(completed / total * 100, 1) if total > 0 else 0.0,
        "by_status":         by_status,
        "by_priority":       by_priority,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SQL implementation (SQLAlchemy)
# ─────────────────────────────────────────────────────────────────────────────

def _sql_to_dict(ticket) -> dict:
    return {
        "id":               ticket.id,
        "ticket_id":        ticket.ticket_id,
        "title":            ticket.title,
        "description":      ticket.description,
        "ticket_type":      ticket.ticket_type,
        "status":           ticket.status,
        "priority":         ticket.priority,
        "priority_score":   ticket.priority_score,
        "assignee":         ticket.assignee,
        "reported_by":      ticket.reported_by,
        "source":           ticket.source,
        "channel":          ticket.channel,
        "slack_message_ts": ticket.slack_message_ts,
        "created_at":       ticket.created_at,
        "updated_at":       ticket.updated_at,
    }


async def _sql_resolve(db, ticket_id: str):
    from sqlalchemy import select
    from .models import Ticket
    raw_id = _parse_id(ticket_id)
    result = await db.execute(select(Ticket).where(Ticket.id == raw_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404, f"Ticket '{ticket_id}' not found")
    return ticket


async def _sql_create(db, data: TicketCreate) -> dict:
    from .models import Ticket
    _validate(ticket_type=data.ticket_type, priority=data.priority)
    ticket = Ticket(
        title=data.title, description=data.description,
        ticket_type=data.ticket_type or "task", priority=data.priority or "Medium",
        assignee=data.assignee, reported_by=data.reported_by,
        source=data.source or "api", channel=data.channel,
        slack_message_ts=data.slack_message_ts,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)
    return _sql_to_dict(ticket)


async def _sql_get(db, ticket_id: str) -> dict:
    return _sql_to_dict(await _sql_resolve(db, ticket_id))


async def _sql_list(db, status=None, priority=None, ticket_type=None,
                     assignee=None, search=None, page=1, page_size=20) -> dict:
    from sqlalchemy import select, func, or_
    from .models import Ticket
    stmt = select(Ticket)
    if status:      stmt = stmt.where(Ticket.status == status)
    if priority:    stmt = stmt.where(Ticket.priority == priority)
    if ticket_type: stmt = stmt.where(Ticket.ticket_type == ticket_type)
    if assignee:    stmt = stmt.where(Ticket.assignee == assignee)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()
    stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    return {"tickets": [_sql_to_dict(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


async def _sql_update(db, ticket_id: str, data: TicketUpdate) -> dict:
    ticket = await _sql_resolve(db, ticket_id)
    _validate(ticket_type=data.ticket_type, priority=data.priority, status=data.status)
    if data.title is not None:          ticket.title          = data.title
    if data.description is not None:    ticket.description    = data.description
    if data.ticket_type is not None:    ticket.ticket_type    = data.ticket_type
    if data.status is not None:         ticket.status         = data.status
    if data.priority is not None:       ticket.priority       = data.priority
    if data.priority_score is not None: ticket.priority_score = data.priority_score
    if data.assignee is not None:       ticket.assignee       = data.assignee
    if data.reported_by is not None:    ticket.reported_by    = data.reported_by
    await db.flush()
    await db.refresh(ticket)
    return _sql_to_dict(ticket)


async def _sql_assign(db, ticket_id: str, assignee: str) -> dict:
    ticket = await _sql_resolve(db, ticket_id)
    ticket.assignee = assignee
    await db.flush()
    await db.refresh(ticket)
    return _sql_to_dict(ticket)


async def _sql_delete(db, ticket_id: str) -> dict:
    ticket = await _sql_resolve(db, ticket_id)
    await db.delete(ticket)
    return {"deleted": True, "ticket_id": ticket_id}


async def _sql_stats(db) -> dict:
    from sqlalchemy import select
    from .models import Ticket
    result = await db.execute(select(Ticket))
    tickets = result.scalars().all()
    by_status: dict = {}
    by_priority: dict = {}
    active_statuses = {"Open", "In Progress", "In Review"}
    done_statuses   = {"Done", "Closed"}
    for t in tickets:
        by_status[t.status]     = by_status.get(t.status, 0)     + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
    total     = len(tickets)
    active    = sum(v for k, v in by_status.items() if k in active_statuses)
    completed = sum(v for k, v in by_status.items() if k in done_statuses)
    return {
        "total_tickets": total, "active_tickets": active,
        "completed_tickets": completed, "blocked_tickets": by_status.get("Blocked", 0),
        "critical_tickets": by_priority.get("Critical", 0),
        "success_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
        "by_status": by_status, "by_priority": by_priority,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API — router calls these; backend is chosen automatically
# ─────────────────────────────────────────────────────────────────────────────

def _parse_id(ticket_id: str) -> int:
    try:
        if isinstance(ticket_id, str) and "-" in ticket_id:
            return int(ticket_id.split("-", 1)[1])
        return int(ticket_id)
    except (ValueError, IndexError):
        raise HTTPException(422, f"Invalid ticket ID format: '{ticket_id}'")


async def create_ticket(db, data: TicketCreate) -> dict:
    return await (_mongo_create if DATABASE_BACKEND == "mongo" else _sql_create)(db, data)

async def get_ticket(db, ticket_id: str) -> dict:
    return await (_mongo_get if DATABASE_BACKEND == "mongo" else _sql_get)(db, ticket_id)

async def list_tickets(db, status=None, priority=None, ticket_type=None,
                        assignee=None, search=None, page=1, page_size=20) -> dict:
    fn = _mongo_list if DATABASE_BACKEND == "mongo" else _sql_list
    return await fn(db, status, priority, ticket_type, assignee, search, page, page_size)

async def update_ticket(db, ticket_id: str, data: TicketUpdate) -> dict:
    return await (_mongo_update if DATABASE_BACKEND == "mongo" else _sql_update)(db, ticket_id, data)

async def assign_ticket(db, ticket_id: str, assignee: str) -> dict:
    return await (_mongo_assign if DATABASE_BACKEND == "mongo" else _sql_assign)(db, ticket_id, assignee)

async def delete_ticket(db, ticket_id: str) -> dict:
    return await (_mongo_delete if DATABASE_BACKEND == "mongo" else _sql_delete)(db, ticket_id)

async def get_stats(db) -> dict:
    return await (_mongo_stats if DATABASE_BACKEND == "mongo" else _sql_stats)(db)
