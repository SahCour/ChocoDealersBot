from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database.db import AsyncSessionLocal
from database.models import Product, Ingredient, AuditLog
from bot.keyboards import get_main_menu_keyboard
from sqlalchemy import select
from loguru import logger

# Состояния для диалогов
CASH_COUNT = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт смены"""
    await update.message.reply_text(
        "👮‍♂️ **ChocoBot Police Mode**\n\n"
        "Смена открыта. Работайте через Square POS.\n"
        "В конце смены нажмите '💰 Сдать кассу'.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def cash_check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало проверки кассы"""
    await update.message.reply_text(
        "💵 **СЛЕПОЙ ПОДСЧЕТ**\n\n"
        "Посчитайте наличные в ящике.\n"
        "Напишите сумму цифрами (например: 3500):",
        reply_markup=ReplyKeyboardRemove()
    )
    return CASH_COUNT

async def cash_check_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенной суммы"""
    text = update.message.text
    try:
        amount = float(text)
        # ТУТ ПОЗЖЕ БУДЕТ СВЕРКА СО SQUARE
        expected = 4000.0  # Mock
        diff = amount - expected

        status = "✅ OK" if abs(diff) < 50 else f"🚨 РАСХОЖДЕНИЕ: {diff}"

        await update.message.reply_text(
            f"Принято: {amount} THB.\n"
            f"Статус: {status}\n\n"
            "Меню возвращено.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите только цифры.")
        return CASH_COUNT

async def production_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню производства"""
    await update.message.reply_text("Эта функция в разработке 🏭")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END
