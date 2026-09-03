"""
Telegram Bot Application Lifecycle and Runner.
Runs alongside the FastAPI server.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.quant_brain_config import settings
from telegram_bot.handlers import (
    cmd_start,
    cmd_help,
    cmd_market,
    cmd_nifty,
    cmd_banknifty,
    cmd_gold,
    cmd_setup,
    cmd_watchlist,
    cmd_status,
    handle_natural_language,
)

logger = logging.getLogger(__name__)


class TelegramBotRunner:
    """Manages the lifecycle of the Telegram bot."""

    def __init__(self) -> None:
        self.app: Optional[Application] = None
        self._is_running = False

    def build_application(self) -> Optional[Application]:
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.info("No TELEGRAM_BOT_TOKEN configured in settings. Telegram bot will remain idle.")
            return None

        app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Register Commands
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("market", cmd_market))
        app.add_handler(CommandHandler("briefing", cmd_market))
        app.add_handler(CommandHandler("nifty", cmd_nifty))
        app.add_handler(CommandHandler("banknifty", cmd_banknifty))
        app.add_handler(CommandHandler("gold", cmd_gold))
        app.add_handler(CommandHandler("setup", cmd_setup))
        app.add_handler(CommandHandler("watchlist", cmd_watchlist))
        app.add_handler(CommandHandler("status", cmd_status))

        # Register Natural Language Message Handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_language))

        self.app = app
        return app

    async def start(self) -> None:
        """Starts the telegram polling loop asynchronously."""
        if not self.app:
            self.build_application()
        if not self.app:
            return

        logger.info("Starting Telegram Bot long-polling...")
        self._is_running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram Bot successfully listening for messages.")

    async def stop(self) -> None:
        """Gracefully stops the Telegram bot."""
        if self.app and self._is_running:
            logger.info("Stopping Telegram Bot...")
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self._is_running = False
            logger.info("Telegram Bot stopped.")


# Global singleton bot runner
telegram_bot_runner = TelegramBotRunner()
