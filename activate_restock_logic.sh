#!/bin/bash
set -e
echo "📦 Activating Restock Logic..."

# 1. APPEND NEW FUNCTIONS TO database/operations.py
cat >> database/operations.py << 'EOF'


async def get_all_ingredients(session: AsyncSession):
    """Fetch all ingredients (Raw + Packaging) ordered by name"""
    result = await session.execute(select(Ingredient).order_by(Ingredient.name))
    return result.scalars().all()


async def process_restock(session: AsyncSession, ingredient_id: int, quantity: float, user_name: str):
    """
    1. Increase ingredient stock
    2. Log the purchase in AuditLog
    """
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        return {"success": False, "error": "Ingredient not found"}

    # Update Stock
    old_stock = ingredient.current_stock
    ingredient.current_stock += quantity

    # Audit Log
    log_entry = AuditLog(
        event_type="RESTOCK",
        staff_name=user_name,
        details=f"Restocked {ingredient.name}. {old_stock} -> {ingredient.current_stock} ({ingredient.unit.value})"
    )
    session.add(log_entry)
    await session.commit()

    return {
        "success": True,
        "name": ingredient.name,
        "new_stock": ingredient.current_stock,
        "unit": ingredient.unit.value
    }
EOF
echo "✅ database/operations.py updated."

# 2. CREATE RESTOCK HANDLER
cat > bot/handlers/restock.py << 'EOF'
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database.db import get_db_session
from database.operations import get_all_ingredients, process_restock
from bot.keyboards import get_main_menu_keyboard
from loguru import logger

# Conversation States
SELECT_INGREDIENT, ENTER_QTY = range(2)


async def restock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Show list of ingredients"""
    user = update.effective_user
    logger.info(f"Restock started by {user.first_name}")

    async for session in get_db_session():
        ingredients = await get_all_ingredients(session)

        if not ingredients:
            await update.message.reply_text("⚠️ No ingredients found in database.")
            return ConversationHandler.END

        # Build Inline Keyboard (2 columns)
        keyboard = []
        row = []
        for i in ingredients:
            btn_text = f"{i.name} ({i.unit.value})"
            row.append(InlineKeyboardButton(btn_text, callback_data=str(i.id)))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await update.message.reply_text(
            "📦 **Restock Mode**\nWhat did you buy?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    return SELECT_INGREDIENT


async def restock_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save ingredient ID and ask for quantity"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END

    context.user_data['ing_id'] = int(query.data)

    await query.edit_message_text(
        "✅ Selected.\n\n**Enter quantity added:**\n(e.g. 5000 for 5kg, or 50 for 50 boxes)",
        parse_mode="Markdown"
    )
    return ENTER_QTY


async def restock_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Update DB"""
    text = update.message.text
    user = update.effective_user
    ing_id = context.user_data.get('ing_id')

    try:
        qty = float(text.replace(",", ""))
        if qty <= 0:
            raise ValueError

        async for session in get_db_session():
            result = await process_restock(session, ing_id, qty, user.first_name)

            if result['success']:
                await update.message.reply_text(
                    f"✅ **Stock Updated!**\n"
                    f"Item: {result['name']}\n"
                    f"Added: +{qty:g}\n"
                    f"New Total: {result['new_stock']:g} {result['unit']}",
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
        await update.message.reply_text("⚠️ Numbers only please (e.g. 2000).")
        return ENTER_QTY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END
EOF
echo "✅ bot/handlers/restock.py created."

# 3. REWRITE MAIN.PY — wire all 3 ConversationHandlers
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
EOF
echo "✅ bot/main.py updated."

echo "🚀 RESTOCK LOGIC ACTIVE."
