"""
Storage models and schemas for Quant Brain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: Optional[int] = None
    session_id: str
    channel: str = Field(default="web", description="'web', 'telegram', or 'api'")
    role: str = Field(description="'user', 'assistant', or 'system'")
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActiveContext(BaseModel):
    session_id: str
    active_symbol: str = "NIFTY"
    active_timeframe: str = "15m"
    last_topic: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TradingViewAlertRecord(BaseModel):
    id: Optional[int] = None
    alert_name: str
    symbol: str
    timeframe: str = "15m"
    signal: str
    price: float
    indicator: Optional[str] = None
    payload_json: Dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(default_factory=datetime.utcnow)


class MarketSnapshotRecord(BaseModel):
    id: Optional[int] = None
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    price: float
    change_pct: float
    regime: str
    structure: str
    momentum: str
    volatility: str
    raw_analysis: Dict[str, Any] = Field(default_factory=dict)


class AuditLogRecord(BaseModel):
    id: Optional[int] = None
    event_type: str
    actor: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
