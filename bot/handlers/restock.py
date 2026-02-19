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
