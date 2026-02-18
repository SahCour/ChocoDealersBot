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
