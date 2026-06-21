"""
routers/tickets.py – Ticket CRUD endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import TicketCreate, TicketUpdate, TicketAssign, TicketResponse, TicketListResponse
from .. import crud

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(payload: TicketCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_ticket(db, payload)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status:      Optional[str] = Query(None),
    priority:    Optional[str] = Query(None),
    ticket_type: Optional[str] = Query(None),
    assignee:    Optional[str] = Query(None),
    search:      Optional[str] = Query(None),
    page:        int           = Query(1,  ge=1),
    page_size:   int           = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await crud.list_tickets(db, status, priority, ticket_type, assignee, search, page, page_size)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    return await crud.get_ticket(db, ticket_id)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: str, payload: TicketUpdate, db: AsyncSession = Depends(get_db)):
    return await crud.update_ticket(db, ticket_id, payload)


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(ticket_id: str, payload: TicketAssign, db: AsyncSession = Depends(get_db)):
    return await crud.assign_ticket(db, ticket_id, payload.assignee)


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    return await crud.delete_ticket(db, ticket_id)
