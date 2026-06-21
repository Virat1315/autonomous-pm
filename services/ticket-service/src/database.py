"""
database.py
Supports both MongoDB (via Motor) and PostgreSQL/SQLite (via SQLAlchemy).
Set DATABASE_BACKEND=mongo or DATABASE_BACKEND=sql (default: sql).

MongoDB:  set MONGODB_URI=mongodb+srv://...
SQL:      set DATABASE_URL=postgresql://...  (or sqlite for local dev)
"""
import os

DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sql").lower()  # "sql" | "mongo"

# ── MongoDB setup ─────────────────────────────────────────────────────────────
_mongo_client = None
_mongo_db     = None

MONGODB_URI    = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "autonomous_pm")


def get_mongo_db():
    """Return the Motor async database handle. Call once at startup."""
    global _mongo_client, _mongo_db
    if _mongo_db is None:
        from motor.motor_asyncio import AsyncIOMotorClient
        _mongo_client = AsyncIOMotorClient(MONGODB_URI)
        _mongo_db     = _mongo_client[MONGODB_DBNAME]
    return _mongo_db


async def close_mongo():
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()


# ── SQL setup (SQLAlchemy) ────────────────────────────────────────────────────
Base = None
engine = None
AsyncSessionLocal = None

def _setup_sql():
    global Base, engine, AsyncSessionLocal
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import declarative_base

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./autonomous_pm.db")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    Base = declarative_base()
    return Base


if DATABASE_BACKEND == "sql":
    _setup_sql()


async def init_db():
    if DATABASE_BACKEND == "mongo":
        db = get_mongo_db()
        # Create indexes
        await db.tickets.create_index("id", unique=True)
        await db.tickets.create_index("status")
        await db.tickets.create_index("priority")
        await db.tickets.create_index("assignee")
        await db.tickets.create_index([("title", "text"), ("description", "text")])
        # Counter collection for auto-incrementing IDs
        await db.counters.update_one(
            {"_id": "ticket_seq"},
            {"$setOnInsert": {"seq": 0}},
            upsert=True,
        )
    else:
        from . import models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency. Yields either a MongoDB db handle or SQLAlchemy session."""
    if DATABASE_BACKEND == "mongo":
        yield get_mongo_db()
    else:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
