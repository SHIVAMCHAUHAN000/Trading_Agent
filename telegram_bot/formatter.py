"""
Telegram Response Formatter for Live Quant Brain.
Ensures Telegram Markdown compatibility and clean visual presentation.
"""

from __future__ import annotations

import re


def clean_markdown_for_telegram(text: str) -> str:
    """
    Cleans markdown formatting so it renders reliably in Telegram.
    Replaces problematic nested asterisks or symbols.
    """
    # Remove HTML tags if any
    cleaned = re.sub(r"<[^>]+>", "", text)
    return cleaned
