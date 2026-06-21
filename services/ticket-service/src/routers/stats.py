"""
routers/stats.py – Dashboard statistics endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import DashboardStats
from .. import crud

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate statistics for the dashboard."""
    return await crud.get_stats(db)
