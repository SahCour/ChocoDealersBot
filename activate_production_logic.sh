#!/bin/bash
set -e
echo "🏭 Activating Production Logic..."

# 1. DATABASE OPERATIONS LAYER
cat > database/operations.py << 'EOF'
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, Ingredient, RecipeItem, AuditLog
from integrations.square_client import square_client
import logging

logger = logging.getLogger(__name__)


async def get_products_with_recipes(session: AsyncSession):
    """Fetch all products that have recipes defined"""
    result = await session.execute(select(Product))
    return result.scalars().all()


async def process_production(session: AsyncSession, product_id: int, quantity: int, user_name: str):
    """
    1. Deduct ingredients from stock
    2. Update Square inventory (Mock/Real)
    3. Log the event
    """
    # 1. Get Product
    product = await session.get(Product, product_id)
    if not product:
        return {"success": False, "error": "Product not found"}

    # 2. Load recipe items
    result = await session.execute(
        select(RecipeItem).where(RecipeItem.product_id == product_id)
    )
    recipe_items = result.scalars().all()

    if not recipe_items:
        return {"success": False, "error": "No recipe defined for this product"}

    # 3. Deduct Ingredients
    report = []
    for item in recipe_items:
        ingredient = await session.get(Ingredient, item.ingredient_id)
        if ingredient:
            required_amount = item.amount * quantity
            ingredient.current_stock -= required_amount
            report.append(f"- {ingredient.name}: {required_amount:.1f} {ingredient.unit}")

    # 4. Update Square (Add finished goods)
    if product.square_id:
        await square_client.update_inventory(product.square_id, quantity)

    # 5. Audit Log
    log_entry = AuditLog(
        event_type="PRODUCTION",
        staff_name=user_name,
        details=f"Produced {quantity} x {product.name}. Ingredients used: {', '.join(report)}"
    )
    session.add(log_entry)

    await session.commit()

    return {
        "success": True,
        "product_name": product.name,
        "report": "\n".join(report)
    }
EOF
echo "✅ database/operations.py created."

# 2. PRODUCTION CONVERSATION HANDLER
cat > bot/handlers/production.py << 'EOF'
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database.db import get_db_session
from database.operations import get_products_with_recipes, process_production
from bot.keyboards import get_main_menu_keyboard
from loguru import logger

# Conversation States
SELECT_PRODUCT, ENTER_QUANTITY = range(2)


async def production_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Show list of products"""
    user = update.effective_user
    logger.info(f"Production started by {user.first_name}")

    async for session in get_db_session():
        products = await get_products_with_recipes(session)

        if not products:
            await update.message.reply_text("⚠️ No products with recipes found in database.")
            return ConversationHandler.END

        keyboard = []
        for p in products:
            keyboard.append([InlineKeyboardButton(f"Make {p.name}", callback_data=str(p.id))])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await update.message.reply_text(
            "🏭 **Production Mode**\nSelect what you made:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return SELECT_PRODUCT


async def production_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save product ID and ask for quantity"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END

    context.user_data['prod_id'] = int(query.data)

    await query.edit_message_text(
        "✅ Selected.\n\n**How many did you make?**\n(Type a number, e.g. 12)",
        parse_mode="Markdown"
    )
    return ENTER_QUANTITY


async def production_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Process the production"""
    text = update.message.text
    user = update.effective_user
    product_id = context.user_data.get('prod_id')

    try:
        quantity = int(text)
        if quantity <= 0:
            raise ValueError

        async for session in get_db_session():
            result = await process_production(session, product_id, quantity, user.first_name)

            if result['success']:
                await update.message.reply_text(
                    f"✅ **Production Recorded!**\n\n"
                    f"Product: {result['product_name']}\n"
                    f"Quantity: +{quantity}\n"
                    f"Ingredients Deducted:\n`{result['report']}`",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ Error: {result['error']}",
                    reply_markup=get_main_menu_keyboard()
                )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number (e.g. 5, 10).")
        return ENTER_QUANTITY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END
EOF
echo "✅ bot/handlers/production.py created."

# 3. MAIN.PY — wire Production ConversationHandler
cat > bot/main.py << 'EOF'
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
    restock_start,
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


async def post_init(application: Application) -> None:
    logger.info("🔄 Post-init setup...")
    await init_db()
    await seed_data()
    logger.success("✅ System initialized")


async def post_shutdown(application: Application) -> None:
    await close_db()


def main() -> None:
    logger.info("🚀 Starting ChocoBot (Production Build)...")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Middleware
    application.add_handler(TypeHandler(Update, AuthMiddleware()), group=-1)

    # 1. Cash Drop Conversation
    cash_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Cash Drop$"), cash_check_start)],
        states={
            CASH_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_check_complete)],
        },
        fallbacks=[CommandHandler("cancel", action_cancel)]
    )

    # 2. Production Conversation
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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(cash_handler)
    application.add_handler(prod_handler)
    application.add_handler(MessageHandler(filters.Regex("^📦 Restock$"), restock_start))
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
EOF
echo "✅ bot/main.py updated."

echo "🎉 PRODUCTION LOGIC ACTIVE."
