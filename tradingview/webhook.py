"""
TradingView Webhook Handler and Ingestion Logic.
Authenticates webhook tokens, sanitizes signals, and saves records to the database.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple
from config.quant_brain_config import settings
from storage.repository import QuantBrainRepository
from storage.models import TradingViewAlertRecord
from tradingview.models import TradingViewWebhookPayload
from live_data.instruments import resolve_symbol

logger = logging.getLogger(__name__)


async def process_tradingview_alert(
    payload: TradingViewWebhookPayload,
    header_secret: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates and stores incoming TradingView alert.
    Returns (success, message, alert_data).
    """
    provided_secret = header_secret or payload.secret
    expected_secret = settings.TRADINGVIEW_WEBHOOK_SECRET

    if expected_secret and provided_secret != expected_secret:
        logger.warning("Unauthorized TradingView webhook attempt with invalid secret.")
        return False, "Unauthorized: Invalid webhook secret token.", {}

    canonical_symbol = resolve_symbol(payload.symbol) or payload.symbol.upper()

    alert_record = TradingViewAlertRecord(
        alert_name=payload.indicator or f"{payload.signal}_{payload.timeframe}",
        symbol=canonical_symbol,
        timeframe=payload.timeframe,
        signal=payload.signal.upper(),
        price=payload.price,
        indicator=payload.indicator,
        payload_json=payload.model_dump(),
    )

    alert_id = await QuantBrainRepository.save_tv_alert(alert_record)
    logger.info("Ingested TradingView alert #%s for %s (%s at %s)", alert_id, canonical_symbol, payload.signal, payload.price)

    await QuantBrainRepository.log_audit(
        event_type="TRADINGVIEW_ALERT_INGESTED",
        actor="TradingViewWebhook",
        details={"alert_id": alert_id, "symbol": canonical_symbol, "signal": payload.signal, "price": payload.price},
    )

    return True, f"Alert ingested successfully with ID {alert_id}", {
        "alert_id": alert_id,
        "symbol": canonical_symbol,
        "signal": payload.signal,
        "price": payload.price,
    }
