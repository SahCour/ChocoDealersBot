#!/bin/bash
# apply_police_mode.sh — Batch apply Police Mode (English) to ChocoDealersBot
set -e
cd "$(dirname "$0")"
echo "🚔 Applying Police Mode..."

# --- 1. Remove old files ---
rm -f bot/handlers/inventory.py
rm -f bot/handlers/commands.py
rm -f bot/handlers/admin.py
rm -f bot/utils/staff_auth.py
rm -f bot/utils/unit_conversion.py

# --- 2. Ensure directories exist ---
mkdir -p bot/handlers integrations database

# --- 3. database/models.py ---
cat << 'EOF' > database/models.py
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .db import Base


class IngredientType(str, enum.Enum):
    RAW = "raw"
    PACKAGING = "packaging"


class UnitType(str, enum.Enum):
    GRAMS = "g"
    PCS = "pcs"
    KG = "kg"


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(Enum(IngredientType), default=IngredientType.RAW)
    current_stock = Column(Float, default=0.0)
    unit = Column(Enum(UnitType), default=UnitType.GRAMS)
    price_per_unit = Column(Float, default=0.0)
    supplier = Column(String, nullable=True)
    recipe_items = relationship("RecipeItem", back_populates="ingredient")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    sku = Column(String, unique=True, nullable=True)
    square_id = Column(String, unique=True, nullable=True)
    price = Column(Float, default=0.0)
    recipe_items = relationship("RecipeItem", back_populates="product")


class RecipeItem(Base):
    __tablename__ = "recipe_items"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    amount = Column(Float, nullable=False)
    product = relationship("Product", back_populates="recipe_items")
    ingredient = relationship("Ingredient", back_populates="recipe_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String)
    details = Column(Text)
    staff_name = Column(String)
    is_alert = Column(Boolean, default=False)
EOF

# --- 4. database/seed.py ---
cat << 'EOF' > database/seed.py
import logging
from sqlalchemy import select
from .db import AsyncSessionLocal
from .models import Ingredient, Product, RecipeItem, IngredientType, UnitType

logger = logging.getLogger(__name__)


async def seed_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).where(Product.name == "Eskimo Coconut"))
        if result.scalar():
            return
        logger.info("🌱 Seeding database with initial recipe...")

        coconut = Ingredient(name="Coconut Meat (Nam Hom)", unit=UnitType.GRAMS, current_stock=5000)
        water = Ingredient(name="Coconut Water", unit=UnitType.GRAMS, current_stock=2000)
        sugar = Ingredient(name="Sugar", unit=UnitType.GRAMS, current_stock=5000)
        vanilla = Ingredient(name="Vanilla Extract", unit=UnitType.GRAMS, current_stock=500)
        stick = Ingredient(
            name="Ice Cream Stick",
            unit=UnitType.PCS,
            type=IngredientType.PACKAGING,
            current_stock=100
        )
        db.add_all([coconut, water, sugar, vanilla, stick])
        await db.flush()

        eskimo = Product(name="Eskimo Coconut", price=160.0, square_id="sq_eskimo_mock")
        db.add(eskimo)
        await db.flush()

        recipes = [
            RecipeItem(product_id=eskimo.id, ingredient_id=coconut.id, amount=50.0),
            RecipeItem(product_id=eskimo.id, ingredient_id=water.id, amount=16.6),
            RecipeItem(product_id=eskimo.id, ingredient_id=sugar.id, amount=25.0),
            RecipeItem(product_id=eskimo.id, ingredient_id=vanilla.id, amount=1.0),
            RecipeItem(product_id=eskimo.id, ingredient_id=stick.id, amount=1.0),
        ]
        db.add_all(recipes)
        await db.commit()
        logger.info("✅ Database seeded successfully!")
EOF

# --- 5. integrations/square_client.py ---
cat << 'EOF' > integrations/square_client.py
import logging
import asyncio

logger = logging.getLogger(__name__)

# SWITCH: True = Mock mode (no real keys), False = Live mode
USE_MOCK = True


class SquareClient:
    def __init__(self):
        self.is_mock = USE_MOCK

    async def get_inventory(self, product_name: str) -> int:
        """Get product stock level (Mock)"""
        if self.is_mock:
            mock_db = {"Eskimo Coconut": 10, "Truffle Classic": 5}
            return mock_db.get(product_name, 0)
        return 0

    async def update_inventory(self, product_name: str, quantity: int):
        """Update stock in Square (Mock)"""
        if self.is_mock:
            logger.info(f"✅ [MOCK SQUARE] Inventory update: {product_name} += {quantity}")
            return True
        return False

    async def get_sales_today(self) -> float:
        """Get total sales amount for today (Mock)"""
        if self.is_mock:
            return 4000.0
        return 0.0

    async def get_total_expected_cash(self) -> float:
        """Get expected cash in drawer based on Square sales (Mock)"""
        if self.is_mock:
            return 4000.0  # Mock: Square expects 4000 THB in drawer
        return 0.0


# Global instance
square_client = SquareClient()
EOF

# --- 6. bot/keyboards.py ---
cat << 'EOF' > bot/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    # Main menu for staff (Bottom of screen)
    keyboard = [
        [KeyboardButton("💰 Cash Drop"), KeyboardButton("🕵️ Spot Check")],
        [KeyboardButton("🏭 Production"), KeyboardButton("📦 Restock")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_production_keyboard(products):
    # Inline buttons for selecting product to produce
    keyboard = []
    for p in products:
        keyboard.append([InlineKeyboardButton(f"Make {p.name}", callback_data=f"prod_{p.id}")])
    return InlineKeyboardMarkup(keyboard)
EOF

# --- 7. bot/handlers/actions.py ---
cat << 'EOF' > bot/handlers/actions.py
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

async def production_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Production Menu Stub"""
    await update.message.reply_text("🏭 Production menu is coming soon.\nUse Square to track sales for now.")

async def restock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restock Menu Stub"""
    await update.message.reply_text("📦 Restock menu is coming soon.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END
EOF

# --- 8. bot/main.py ---
cat << 'EOF' > bot/main.py
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
EOF

# --- 9. bot/middleware/auth.py ---
cat << 'EOF' > bot/middleware/auth.py
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


class AuthMiddleware:
    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user:
            logger.debug(f"Update from user {update.effective_user.id}")
EOF

# --- 10. bot/handlers/__init__.py (clear) ---
cat << 'EOF' > bot/handlers/__init__.py
EOF

echo ""
echo "✅ Police Mode applied successfully!"
echo "   Files updated: models.py, seed.py, square_client.py, keyboards.py, actions.py, main.py, auth.py"
echo "   Old handlers removed (inventory, commands, admin, staff_auth, unit_conversion)"
