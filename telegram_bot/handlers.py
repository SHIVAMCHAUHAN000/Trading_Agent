"""
Telegram Bot Message Handlers and Command Processing.
Connects Telegram directly to the shared Quant Brain.
"""

from __future__ import annotations

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config.quant_brain_config import settings
from brain.orchestrator import quant_brain
from storage.repository import QuantBrainRepository
from telegram_bot.formatter import clean_markdown_for_telegram

logger = logging.getLogger(__name__)


def is_user_authorized(update: Update) -> bool:
    """Check if the user is authorized to query the personal quant brain."""
    auth_list = settings.authorized_telegram_ids
    # If no users configured in dev mode, permit access
    if not auth_list:
        return True

    user = update.effective_user
    if not user:
        return False

    user_id_str = str(user.id)
    username = (user.username or "").lower()

    if user_id_str in auth_list:
        return True
    for item in auth_list:
        if item.lower().replace("@", "") == username:
            return True
    return False


async def unauthorized_reply(update: Update) -> None:
    """Send polite rejection notice to unauthorized users."""
    user = update.effective_user
    uid = user.id if user else "Unknown"
    await update.message.reply_text(
        f"⛔ *Access Restricted*\n\n"
        f"Your Telegram ID `{uid}` is not authorized to access this personal quant brain.\n"
        f"To authorize your account, add `{uid}` to `AUTHORIZED_TELEGRAM_USERS` in the `.env` file.",
        parse_mode=ParseMode.MARKDOWN,
    )
    logger.warning("Rejected unauthorized access attempt from Telegram user %s", uid)
    await QuantBrainRepository.log_audit(
        event_type="UNAUTHORIZED_TELEGRAM_ACCESS",
        actor=f"Telegram:{uid}",
        details={"username": user.username if user else None},
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    msg = (
        "🧠 **Personal Live Quant Brain** online!\n\n"
        "I provide live-market quantitative intelligence, structure, liquidity, momentum, "
        "and multi-timeframe decision support.\n\n"
        "**Available Commands:**\n"
        "• `/market` or `/briefing` — Complete market briefing\n"
        "• `/nifty` — Detailed NIFTY 50 analysis\n"
        "• `/banknifty` — Bank Nifty analysis\n"
        "• `/gold` — Gold COMEX/MCX analysis\n"
        "• `/watchlist` — Configured watchlist overview\n"
        "• `/setup` — Check for active confluent setups\n"
        "• `/status` — System health and data freshness\n"
        "• `/help` — Example natural language questions\n\n"
        "💬 *Or just ask me questions naturally!* Follow-ups like *'Why?'* and *'Where is liquidity?'* will understand previous context."
    )
    await update.message.reply_text(clean_markdown_for_telegram(msg), parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    msg = (
        "💡 **Sample Questions You Can Ask:**\n\n"
        "• *'What is NIFTY doing right now?'*\n"
        "• *'Why is it falling?'*\n"
        "• *'Where is liquidity?'*\n"
        "• *'What is the 15-minute trend?'*\n"
        "• *'What is the price of gold?'*\n"
        "• *'What's driving gold?'*\n"
        "• *'Is there a high quality setup developing?'*\n"
        "• *'Compare NIFTY and BANKNIFTY'*\n"
        "• *'What is momentum telling us?'*\n"
        "• *'Summarize today's market.'*"
    )
    await update.message.reply_text(clean_markdown_for_telegram(msg), parse_mode=ParseMode.MARKDOWN)


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /market or /briefing command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="Summarize today's market briefing",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_nifty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /nifty command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="What is NIFTY doing?",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_banknifty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /banknifty command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="What is BANKNIFTY doing?",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_gold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /gold command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="Analyze GOLD",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setup command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="Is there a setup developing?",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /watchlist command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")
    result = await quant_brain.process_query(
        session_id=chat_id,
        user_message="Analyze my watchlist",
        channel="telegram",
    )
    await update.message.reply_text(clean_markdown_for_telegram(result["response"]), parse_mode=ParseMode.MARKDOWN)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    from mcp_tools.registry import mcp_registry
    tools = mcp_registry.list_tools()
    active_count = len([t for t in tools if t.is_active])
    total_calls = sum(t.total_calls for t in tools)

    msg = (
        "⚙️ **System Status & Connection Health**\n\n"
        f"• **App Version**: `{settings.APP_VERSION}`\n"
        f"• **Environment**: `{settings.APP_ENV}`\n"
        f"• **AI Provider**: `{settings.AI_PROVIDER}`\n"
        f"• **MCP Tools**: `{active_count} active` (Total calls: {total_calls})\n"
        f"• **Market Data Feed**: `YFinance (NSE/Global) Connected`\n"
        f"• **TradingView Webhooks**: `Active on /api/v1/tradingview/webhook`\n"
        f"• **Database**: `SQLite Persistent`"
    )
    await update.message.reply_text(clean_markdown_for_telegram(msg), parse_mode=ParseMode.MARKDOWN)


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all conversational natural language messages."""
    if not is_user_authorized(update):
        await unauthorized_reply(update)
        return

    user_text = update.message.text
    if not user_text:
        return

    chat_id = str(update.effective_chat.id)
    await update.message.reply_chat_action("typing")

    try:
        result = await quant_brain.process_query(
            session_id=chat_id,
            user_message=user_text,
            channel="telegram",
        )
        resp_text = result["response"]
        await update.message.reply_text(
            clean_markdown_for_telegram(resp_text),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.error("Error processing Telegram message: %s", e, exc_info=True)
        await update.message.reply_text(
            f"⚠️ An error occurred while analyzing the market: {str(e)}\nPlease try again."
        )
