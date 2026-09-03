"""
TradingView Alert webhook payload models.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TradingViewWebhookPayload(BaseModel):
    secret: Optional[str] = Field(default=None, description="Webhook authorization secret")
    symbol: str = Field(description="Instrument symbol e.g. NIFTY, BANKNIFTY, GOLD")
    timeframe: str = Field(default="15m", description="Chart timeframe e.g. 5m, 15m, 1h")
    signal: str = Field(description="Alert signal e.g. BUY, SELL, BOS_BULLISH, SWEEP_LOW")
    price: float = Field(description="Price level when alert was triggered")
    indicator: Optional[str] = Field(default=None, description="Name of the TradingView indicator")
    message: Optional[str] = Field(default=None, description="Optional custom text message from alert")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional custom fields")
