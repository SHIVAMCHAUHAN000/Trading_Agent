"""
Unified Production Service Launcher for Personal Live Quant Brain.
Runs the FastAPI Web Server + Telegram Bot concurrently with graceful shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn
from config.quant_brain_config import settings
from storage.db import init_db
from telegram_bot.bot import telegram_bot_runner
from server.app import app

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("quant_brain.production")


async def run_services():
    """Starts persistent services concurrently."""
    logger.info("==================================================")
    logger.info("  Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("  Environment: %s | Host: %s:%s", settings.APP_ENV, settings.HOST, settings.PORT)
    logger.info("==================================================")

    # 1. Initialize Database
    await init_db()
    logger.info("Database initialized at %s", settings.SQLITE_PATH)

    # 2. Prepare Uvicorn web server
    config = uvicorn.Config(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False,
    )
    server = uvicorn.Server(config)

    # 3. Start Telegram Bot if token provided
    bot_task = None
    if settings.TELEGRAM_BOT_TOKEN:
        logger.info("Telegram Bot token detected. Initializing bot...")
        telegram_bot_runner.build_application()
        bot_task = asyncio.create_task(telegram_bot_runner.start())
    else:
        logger.info("💡 Telegram bot is in standby (Add TELEGRAM_BOT_TOKEN to .env to activate).")
        logger.info("   Web dashboard and API remain fully operational!")

    # 4. Start Web Server
    server_task = asyncio.create_task(server.serve())

    tasks = [server_task]
    if bot_task:
        tasks.append(bot_task)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Services received cancellation signal.")
    finally:
        if settings.TELEGRAM_BOT_TOKEN:
            await telegram_bot_runner.stop()
        logger.info("All services shut down cleanly.")


def main():
    try:
        asyncio.run(run_services())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated by user.")


if __name__ == "__main__":
    main()
