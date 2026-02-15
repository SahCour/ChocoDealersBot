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
)

from database.db import init_db, close_db
from database.seed import seed_data
from bot.middleware.auth import AuthMiddleware
from bot.handlers.actions import (
    start, cash_check_start, cash_check_complete,
    production_start, cancel, CASH_COUNT
)


async def post_init(application: Application) -> None:
    logger.info("🔄 Post-init setup...")
    await init_db()
    await seed_data()
    logger.success("✅ System initialized")


async def post_shutdown(application: Application) -> None:
    await close_db()


def main() -> None:
    logger.info("🚀 Starting ChocoBot (Clean Build)...")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Диалог сдачи кассы
    cash_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Сдать кассу$"), cash_check_start)],
        states={
            CASH_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_check_complete)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(cash_handler)
    application.add_handler(MessageHandler(filters.Regex("^🏭 Производство$"), production_start))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
