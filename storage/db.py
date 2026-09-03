"""
Database connection and schema initialization for Live Quant Brain.
Supports local SQLite, Vercel Serverless ephemeral /tmp SQLite, and Supabase Postgres.
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
import aiosqlite
from config.quant_brain_config import settings

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id, created_at);

CREATE TABLE IF NOT EXISTS active_contexts (
    session_id TEXT PRIMARY KEY,
    active_symbol TEXT NOT NULL DEFAULT 'NIFTY',
    active_timeframe TEXT NOT NULL DEFAULT '15m',
    last_topic TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tradingview_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT DEFAULT '15m',
    signal TEXT NOT NULL,
    price REAL NOT NULL,
    indicator TEXT,
    payload_json TEXT DEFAULT '{}',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tv_alerts_symbol ON tradingview_alerts (symbol, received_at DESC);

CREATE TABLE IF NOT EXISTS market_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price REAL NOT NULL,
    change_pct REAL NOT NULL,
    regime TEXT,
    structure TEXT,
    momentum TEXT,
    volatility TEXT,
    raw_analysis_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_snapshots_symbol ON market_snapshots (symbol, timestamp DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details_json TEXT DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_effective_sqlite_path() -> Path:
    """Returns /tmp on Vercel/serverless environments where local directory is read-only."""
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = Path("/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir / "quant_brain.db"
    return Path(settings.SQLITE_PATH)


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager for SQLite database connection."""
    db_path = get_effective_sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Initialize database tables."""
    db_path = get_effective_sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(db_path)) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    logger.info("Database schema initialized successfully at %s", db_path)
