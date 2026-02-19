import sys
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
    CallbackQueryHandler,
    TypeHandler
)

from database.db import init_db, close_db
from database.seed import seed_data
from bot.middleware.auth import AuthMiddleware
from bot.handlers.actions import (
    start,
    cash_check_start,
    cash_check_complete,
    cancel as action_cancel,
    CASH_COUNT
)
from bot.handlers.production import (
    production_start,
    production_select,
    production_confirm,
    cancel as prod_cancel,
    SELECT_PRODUCT,
    ENTER_QUANTITY
)
from bot.handlers.restock import (
    restock_start,
    restock_select,
    restock_confirm,
    cancel as restock_cancel,
    SELECT_INGREDIENT,
    ENTER_QTY
)


async def post_init(application: Application) -> None:
    logger.info("🔄 Post-init setup...")
    await init_db()
    await seed_data()
    logger.success("✅ System initialized")


async def post_shutdown(application: Application) -> None:
    await close_db()


def main() -> None:
    logger.info("🚀 Starting ChocoBot (Full Ops)...")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Middleware
    application.add_handler(TypeHandler(Update, AuthMiddleware()), group=-1)

    # 1. Cash Drop
    cash_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Cash Drop$"), cash_check_start)],
        states={
            CASH_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_check_complete)]
        },
        fallbacks=[CommandHandler("cancel", action_cancel)]
    )

    # 2. Production
    prod_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏭 Production$"), production_start)],
        states={
            SELECT_PRODUCT: [CallbackQueryHandler(production_select)],
            ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, production_confirm)]
        },
        fallbacks=[
            CommandHandler("cancel", prod_cancel),
            CallbackQueryHandler(prod_cancel, pattern="^cancel$")
        ]
    )

    # 3. Restock
    restock_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Restock$"), restock_start)],
        states={
            SELECT_INGREDIENT: [CallbackQueryHandler(restock_select)],
            ENTER_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, restock_confirm)]
        },
        fallbacks=[
            CommandHandler("cancel", restock_cancel),
            CallbackQueryHandler(restock_cancel, pattern="^cancel$")
        ]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(cash_handler)
    application.add_handler(prod_handler)
    application.add_handler(restock_handler)
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
