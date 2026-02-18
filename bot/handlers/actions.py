from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.keyboards import get_main_menu_keyboard
from integrations.square_client import square_client
from loguru import logger

# Conversation States
CASH_COUNT = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shift Start - Main Entry Point"""
    user = update.effective_user
    await update.message.reply_text(
        f"👮‍♂️ **System Online**\n"
        f"User: {user.first_name}\n\n"
        "**INSTRUCTIONS:**\n"
        "1. Work via Square POS on iPad.\n"
        "2. Only use this bot for Cash Drops and Checks.\n"
        "3. If you see 'Spot Check', count the items immediately.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def cash_check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Blind Cash Count"""
    await update.message.reply_text(
        "💵 **BLIND CASH COUNT**\n\n"
        "1. Open the cash drawer.\n"
        "2. Count ALL cash (bills + coins).\n"
        "3. Do NOT look at Square report.\n\n"
        "👇 **Type the total amount below (numbers only):**",
        reply_markup=ReplyKeyboardRemove()
    )
    return CASH_COUNT

async def cash_check_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process Cash Amount"""
    text = update.message.text
    user = update.effective_user

    try:
        # 1. Parse Input
        amount = float(text.replace(",", ""))

        # 2. Compare with Square (Mock for now)
        expected = await square_client.get_total_expected_cash()
        diff = amount - expected

        # 3. Determine Status
        if abs(diff) < 50:
            status = "✅ MATCHED"
            msg = "Great job! Numbers match."
        else:
            status = f"🚨 MISMATCH ({diff:+.2f} THB)"
            msg = "⚠️ Manager has been notified."

        # 4. Log (Audit Trail)
        logger.info(f"CASH CHECK: User={user.first_name}, Counted={amount}, Expected={expected}, Diff={diff}")

        # 5. Reply to Staff
        await update.message.reply_text(
            f"📥 **Cash Drop Accepted**\n"
            f"Amount: {amount:,.2f} THB\n"
            f"Status: {status}\n"
            f"{msg}\n\n"
            "Returning to menu...",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ Error: Please enter numbers only (e.g. 3500)")
        return CASH_COUNT

async def restock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restock Menu Stub"""
    await update.message.reply_text("📦 Restock menu is coming soon.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END
