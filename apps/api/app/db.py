from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import asyncpg_connect_args, settings


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=asyncpg_connect_args(),
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def _migrate_sqlite(conn) -> None:
    """Add columns introduced after initial SQLite create_all."""
    if not str(settings.database_url).startswith("sqlite"):
        return
    result = await conn.execute(text("PRAGMA table_info(campaigns)"))
    cols = {row[1] for row in result.fetchall()}
    if not cols:
        return
    if "workspace_id" not in cols:
        await conn.execute(
            text("ALTER TABLE campaigns ADD COLUMN workspace_id VARCHAR(36) DEFAULT ''")
        )
    migrations = [
        ("product_description", "TEXT DEFAULT ''"),
        ("product_url", "VARCHAR(500)"),
        ("objective", "VARCHAR(40) DEFAULT 'sales'"),
        ("daily_budget", "FLOAT DEFAULT 50.0"),
        ("duration_days", "INTEGER DEFAULT 14"),
        ("target_country", "VARCHAR(120) DEFAULT ''"),
        ("target_location", "VARCHAR(200) DEFAULT ''"),
        ("age_min", "INTEGER DEFAULT 18"),
        ("age_max", "INTEGER DEFAULT 65"),
        ("gender", "VARCHAR(20) DEFAULT 'all'"),
        ("language", "VARCHAR(40) DEFAULT 'en'"),
        ("meta_structure_json", "TEXT DEFAULT '{}'"),
        ("audiences_json", "TEXT DEFAULT '{}'"),
        ("optimization_json", "TEXT DEFAULT '{}'"),
        ("publish_status", "VARCHAR(40) DEFAULT 'none'"),
        ("auto_pause_enabled", "BOOLEAN DEFAULT 1"),
    ]
    for name, ddl in migrations:
        if name not in cols:
            await conn.execute(text(f"ALTER TABLE campaigns ADD COLUMN {name} {ddl}"))
    await conn.execute(
        text(
            "UPDATE campaigns SET workspace_id = :wid "
            "WHERE workspace_id IS NULL OR workspace_id = ''"
        ),
        {"wid": settings.demo_workspace_id},
    )


async def init_db() -> None:
    from app import models  # noqa: F401

    if str(settings.database_url).startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _migrate_sqlite(conn)
    # PostgreSQL schema is managed by Alembic (`alembic upgrade head` on deploy).
