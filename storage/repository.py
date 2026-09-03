"""
Database repository for CRUD operations in Quant Brain.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from storage.db import get_db_connection
from storage.models import (
    ChatMessage,
    ActiveContext,
    TradingViewAlertRecord,
    MarketSnapshotRecord,
    AuditLogRecord,
)

logger = logging.getLogger(__name__)


class QuantBrainRepository:
    """Repository handling all persistent database operations."""

    @staticmethod
    async def save_message(
        session_id: str,
        role: str,
        content: str,
        channel: str = "web",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        metadata_json = json.dumps(metadata or {})
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO messages (session_id, channel, role, content, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, channel, role, content, metadata_json),
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_messages(session_id: str, limit: int = 20) -> List[ChatMessage]:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT id, session_id, channel, role, content, metadata_json, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            messages = []
            for row in reversed(rows):
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    meta = {}
                messages.append(
                    ChatMessage(
                        id=row["id"],
                        session_id=row["session_id"],
                        channel=row["channel"],
                        role=row["role"],
                        content=row["content"],
                        metadata=meta,
                        created_at=datetime.fromisoformat(str(row["created_at"])),
                    )
                )
            return messages

    @staticmethod
    async def get_active_context(session_id: str) -> ActiveContext:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT session_id, active_symbol, active_timeframe, last_topic, updated_at
                FROM active_contexts
                WHERE session_id = ?
                """,
                (session_id,),
            )
            row = await cursor.fetchone()
            if row:
                return ActiveContext(
                    session_id=row["session_id"],
                    active_symbol=row["active_symbol"],
                    active_timeframe=row["active_timeframe"],
                    last_topic=row["last_topic"],
                    updated_at=datetime.fromisoformat(str(row["updated_at"])),
                )
            # Default context
            default_ctx = ActiveContext(session_id=session_id)
            await db.execute(
                """
                INSERT INTO active_contexts (session_id, active_symbol, active_timeframe)
                VALUES (?, ?, ?)
                """,
                (session_id, default_ctx.active_symbol, default_ctx.active_timeframe),
            )
            await db.commit()
            return default_ctx

    @staticmethod
    async def update_active_context(
        session_id: str,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> ActiveContext:
        current = await QuantBrainRepository.get_active_context(session_id)
        new_symbol = (symbol.upper() if symbol else current.active_symbol)
        new_tf = (timeframe if timeframe else current.active_timeframe)
        new_topic = (topic if topic is not None else current.last_topic)

        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO active_contexts (session_id, active_symbol, active_timeframe, last_topic, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    active_symbol = excluded.active_symbol,
                    active_timeframe = excluded.active_timeframe,
                    last_topic = excluded.last_topic,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (session_id, new_symbol, new_tf, new_topic),
            )
            await db.commit()

        return ActiveContext(
            session_id=session_id,
            active_symbol=new_symbol,
            active_timeframe=new_tf,
            last_topic=new_topic,
            updated_at=datetime.utcnow(),
        )

    @staticmethod
    async def save_tv_alert(alert: TradingViewAlertRecord) -> int:
        payload_str = json.dumps(alert.payload_json)
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO tradingview_alerts (alert_name, symbol, timeframe, signal, price, indicator, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_name,
                    alert.symbol.upper(),
                    alert.timeframe,
                    alert.signal,
                    alert.price,
                    alert.indicator,
                    payload_str,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_recent_tv_alerts(symbol: Optional[str] = None, limit: int = 10) -> List[TradingViewAlertRecord]:
        async with get_db_connection() as db:
            if symbol:
                cursor = await db.execute(
                    """
                    SELECT id, alert_name, symbol, timeframe, signal, price, indicator, payload_json, received_at
                    FROM tradingview_alerts
                    WHERE symbol = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (symbol.upper(), limit),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT id, alert_name, symbol, timeframe, signal, price, indicator, payload_json, received_at
                    FROM tradingview_alerts
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            rows = await cursor.fetchall()
            alerts = []
            for r in rows:
                try:
                    payload = json.loads(r["payload_json"])
                except Exception:
                    payload = {}
                alerts.append(
                    TradingViewAlertRecord(
                        id=r["id"],
                        alert_name=r["alert_name"],
                        symbol=r["symbol"],
                        timeframe=r["timeframe"],
                        signal=r["signal"],
                        price=r["price"],
                        indicator=r["indicator"],
                        payload_json=payload,
                        received_at=datetime.fromisoformat(str(r["received_at"])),
                    )
                )
            return alerts

    @staticmethod
    async def log_audit(event_type: str, actor: str, details: Dict[str, Any]) -> None:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO audit_logs (event_type, actor, details_json)
                VALUES (?, ?, ?)
                """,
                (event_type, actor, json.dumps(details)),
            )
            await db.commit()

    @staticmethod
    async def get_watchlist() -> List[str]:
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT symbol FROM watchlist ORDER BY id ASC")
            rows = await cursor.fetchall()
            if not rows:
                from config.quant_brain_config import settings
                for sym in settings.watchlist_symbols:
                    await db.execute("INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)", (sym,))
                await db.commit()
                return settings.watchlist_symbols
            return [r["symbol"] for r in rows]

    @staticmethod
    async def add_to_watchlist(symbol: str) -> bool:
        async with get_db_connection() as db:
            await db.execute("INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)", (symbol.upper(),))
            await db.commit()
            return True

    @staticmethod
    async def remove_from_watchlist(symbol: str) -> bool:
        async with get_db_connection() as db:
            await db.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
            await db.commit()
            return True
