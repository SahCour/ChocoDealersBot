import sys
import asyncio
from config.config import settings
from loguru import logger
from bot.utils.logger import setup_logger

setup_logger(settings.log_level, settings.log_file)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    TypeHandler
)

from database.db import init_db, close_db
from database.seed import seed_data
from bot.middleware.auth import AuthMiddleware
from bot.handlers.actions import (
    start,
    cash_check_start,
    cash_check_complete,
    production_start,
    restock_start,
    cancel,
    CASH_COUNT
)


async def post_init(application: Application) -> None:
    logger.info("🔄 Post-init setup...")
    await init_db()
    await seed_data()
    logger.success("✅ System initialized")


async def post_shutdown(application: Application) -> None:
    await close_db()


def main() -> None:
    logger.info("🚀 Starting ChocoBot (English Version)...")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Middleware
    application.add_handler(TypeHandler(Update, AuthMiddleware()), group=-1)

    # Cash Drop Conversation
    cash_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Cash Drop$"), cash_check_start)],
        states={
            CASH_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_check_complete)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Main Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(cash_handler)

    # Simple Buttons
    application.add_handler(MessageHandler(filters.Regex("^🏭 Production$"), production_start))
    application.add_handler(MessageHandler(filters.Regex("^📦 Restock$"), restock_start))

    # Spot Check (Stub)
    application.add_handler(MessageHandler(
        filters.Regex("^🕵️ Spot Check$"),
        lambda u, c: u.message.reply_text("🕵️ Random check coming soon!")
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
