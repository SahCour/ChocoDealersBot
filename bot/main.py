import asyncio
import sys
from config.config import settings
from loguru import logger
from bot.utils.logger import setup_logger

setup_logger(settings.log_level, settings.log_file)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    TypeHandler,
)

from database.db import init_db, close_db
from database.seed import seed_data  # <--- НОВЫЙ ИМПОРТ
from bot.handlers import commands, admin, inventory
from bot.middleware.auth import AuthMiddleware
from bot.utils.staff_auth import handle_staff_selection_callback


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"System Online. Welcome, {user.first_name}!")


async def post_init(application: Application) -> None:
    """Инициализация при старте"""
    logger.info("🔄 Running post-init setup...")
    try:
        await init_db()   # Создает таблицы
        await seed_data() # Заполняет рецепты
        logger.success("✅ System initialized successfully")
    except Exception as e:
        logger.exception(f"❌ CRITICAL INIT ERROR: {e}")


async def post_shutdown(application: Application) -> None:
    await close_db()


def main() -> None:
    logger.info("🚀 Starting ChocoBot v2.0 (Police Mode)...")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Middleware
    auth_middleware = AuthMiddleware()
    application.add_handler(TypeHandler(Update, auth_middleware), group=-1)

    # Handlers
    application.add_handler(CommandHandler("start", start))

    # Временно оставим старые хендлеры, позже заменим на Меню Персонала
    application.add_handler(inventory.get_add_inventory_handler())
    application.add_handler(inventory.get_consume_inventory_handler())
    application.add_handler(CommandHandler("inventory", commands.inventory_command))

    application.add_handler(CallbackQueryHandler(handle_staff_selection_callback, pattern=r"^staff_select:"))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
