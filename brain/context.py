"""
Conversation context manager for Quant Brain.
Maintains session state, active instrument, active timeframe, and conversation memory.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple
from live_data.instruments import INSTRUMENTS, ALIAS_MAP, resolve_symbol
from storage.repository import QuantBrainRepository
from storage.models import ActiveContext


TIMEFRAME_PATTERN = re.compile(r"\b(1m|5m|15m|30m|1h|60m|4h|daily|1d|weekly|1wk)\b", re.IGNORECASE)


def extract_symbol_and_timeframe(
    text: str,
    current_context: Optional[ActiveContext] = None,
) -> Tuple[str, str, bool]:
    """
    Extracts symbol and timeframe from text.
    If not explicitly mentioned, infers from current context.
    Returns: (symbol, timeframe, was_explicitly_mentioned)
    """
    explicit_symbol = resolve_symbol(text)
    
    # Check for timeframe
    tf_match = TIMEFRAME_PATTERN.search(text)
    explicit_tf = None
    if tf_match:
        raw_tf = tf_match.group(1).lower()
        if raw_tf in ("daily", "1d"):
            explicit_tf = "1d"
        elif raw_tf in ("weekly", "1wk"):
            explicit_tf = "1wk"
        elif raw_tf in ("60m", "1h"):
            explicit_tf = "1h"
        else:
            explicit_tf = raw_tf

    # Determine symbol
    if explicit_symbol:
        symbol = explicit_symbol
        was_symbol_explicit = True
    elif current_context and current_context.active_symbol:
        symbol = current_context.active_symbol
        was_symbol_explicit = False
    else:
        symbol = "NIFTY"
        was_symbol_explicit = False

    # Determine timeframe
    if explicit_tf:
        timeframe = explicit_tf
    elif current_context and current_context.active_timeframe:
        timeframe = current_context.active_timeframe
    else:
        timeframe = "15m"

    return symbol, timeframe, was_symbol_explicit
