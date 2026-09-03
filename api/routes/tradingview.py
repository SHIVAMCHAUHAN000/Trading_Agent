"""
TradingView Webhook API Route.
Receives, authenticates, and serves TradingView alerts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from tradingview.models import TradingViewWebhookPayload
from tradingview.webhook import process_tradingview_alert
from storage.repository import QuantBrainRepository

router = APIRouter(prefix="/api/v1/tradingview", tags=["TradingView"])


@router.post("/webhook")
async def receive_tv_webhook(
    payload: TradingViewWebhookPayload,
    x_tradingview_secret: Optional[str] = Header(default=None, alias="X-TradingView-Secret"),
):
    """
    Receives alerts and signals sent by TradingView Webhooks.
    Validates secret and stores signal in database.
    """
    success, message, data = await process_tradingview_alert(
        payload=payload,
        header_secret=x_tradingview_secret,
    )
    if not success:
        raise HTTPException(status_code=401, detail=message)
    return {"status": "success", "message": message, "data": data}


@router.get("/alerts")
async def list_recent_alerts(
    symbol: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=100),
):
    """List recent TradingView alerts from the database."""
    alerts = await QuantBrainRepository.get_recent_tv_alerts(symbol=symbol, limit=limit)
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "alert_name": a.alert_name,
                "symbol": a.symbol,
                "timeframe": a.timeframe,
                "signal": a.signal,
                "price": a.price,
                "indicator": a.indicator,
                "received_at": a.received_at.isoformat(),
            }
            for a in alerts
        ],
    }
