"""
Chocodealers Warehouse Management Telegram Bot
Main entry point
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    TypeHandler,
)
from loguru import logger
import sys

from config.config import settings
from database.db import init_db, close_db
from bot.handlers import commands, admin, inventory
from bot.middleware.auth import AuthMiddleware
from bot.utils.logger import setup_logger
from bot.utils.staff_auth import handle_staff_selection_callback


# Setup logging
setup_logger(settings.log_level, settings.log_file)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")

    welcome_message = f"""
🍫 **Welcome to Chocodealers Warehouse Bot!**

Hi, {user.first_name}!

This bot helps you manage inventory and sales for Chocodealers chocolate shop.

**📋 MAIN COMMANDS:**

**🆕 Inventory Management:**
• `/add_inventory` - Add incoming goods
• `/consume_inventory` - Record consumption/sales
• `/view_inventory` - View current stock levels
• `/view_logs` - View transaction history
• `/correction` - Manual inventory correction (ADMIN)

**Inventory (Legacy):**
• `/inventory` - Show all inventory
• `/inventory <SKU>` - Specific product stock

**Sales:**
• `/sale <SKU> <quantity> [price]` - Register a sale

**Production (MANAGER+):**
• `/production <SKU> <quantity>` - Produce items

**Purchases (MANAGER+):**
• `/purchase <code> <quantity>` - Buy ingredients

**Reports (MANAGER+):**
• `/report day` - Today's report
• `/report week` - Weekly report
• `/report month` - Monthly report

**Sync (ADMIN):**
• `/sync_square` - Sync with Square POS
• `/sync_sheets` - Sync with Google Sheets

**Help:**
• `/help` - Show all commands
• `/status` - Bot and system status

Use `/help` for detailed information about each command.
"""

    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = """
🆘 **Chocodealers Bot Help**

**📦 INVENTORY**
`/inventory` - Show all product stock
`/inventory_ingredients` - Show ingredient stock
`/inventory <name/SKU>` - Specific product stock
Example: `/inventory TRF-001`

**💰 SALES**
`/sale <SKU> <qty> [price]` - Register a sale
Examples:
  • `/sale BAR-S-01 5` - Sell 5 bars at standard price
  • `/sale TRF-002 3 180` - Sell 3 truffles at 180฿

**🏭 PRODUCTION** (MANAGER or ADMIN required)
`/production <SKU> <qty>` - Produce items
Example: `/production BAR-S-01 100`

**🛒 PURCHASES** (MANAGER or ADMIN required)
`/purchase <code> <qty kg> [supplier]` - Buy ingredients
Examples:
  • `/purchase ING-001 10` - Buy 10kg cocoa butter
  • `/purchase ING-013 5 Heritage` - Buy 5kg pistachios from Heritage

**📊 REPORTS** (MANAGER or ADMIN required)
`/report day` - Today's report
`/report week` - Last 7 days
`/report month` - Last 30 days
`/report <date>` - Specific date (YYYY-MM-DD)

**🔄 SYNC** (ADMIN only)
`/sync_square` - Sync with Square POS
`/sync_sheets` - Sync with Google Sheets
`/sync_all` - Full sync all systems

**⚙️ SYSTEM**
`/status` - System status and last syncs
`/profile` - Your profile info
`/low_stock` - Products with low stock

**👥 USER MANAGEMENT** (ADMIN only)
`/users` - List all users
`/add_user <telegram_id> <role>` - Add user
`/change_role <telegram_id> <role>` - Change user role

**Roles:**
• `ADMIN` - Full access
• `MANAGER` - Production, purchases, reports
• `STAFF` - View inventory, sales

Questions? Contact the administrator.
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status"""
    from database.models import User, Product, Ingredient
    from database.db import get_db
    from sqlalchemy import select, func

    async with get_db() as db:
        # Count stats
        total_users = await db.scalar(select(func.count(User.id)))
        total_products = await db.scalar(select(func.count(Product.id)))
        total_ingredients = await db.scalar(select(func.count(Ingredient.id)))

    status_text = f"""
🤖 **Chocodealers Bot Status**

✅ Bot is running normally

**📊 Statistics:**
• Users: {total_users}
• Products in catalog: {total_products}
• Ingredients: {total_ingredients}

**🔧 Settings:**
• Environment: {settings.environment}
• Timezone: {settings.timezone}
• Auto-sync Square: {"✅" if settings.enable_auto_sync_square else "❌"}
• Auto-sync Sheets: {"✅" if settings.enable_auto_sync_sheets else "❌"}

**🔗 Integrations:**
• Square POS: {'✅ Connected' if settings.square_access_token else '❌ Not configured'}
• Google Sheets: {'✅ Connected' if settings.google_sheet_id else '❌ Not configured'}

Use `/help` for list of all commands.
"""

    await update.message.reply_text(status_text, parse_mode="Markdown")


async def post_init(application: Application) -> None:
    """Initialize database and other services after bot starts"""
    logger.info("Initializing database...")
    await init_db()
    logger.success("Database initialized")


async def post_shutdown(application: Application) -> None:
    """Cleanup after bot stops"""
    logger.info("Shutting down...")
    await close_db()
    logger.success("Bot shut down successfully")


def main() -> None:
    """Run the bot"""
    logger.info("Starting Chocodealers Warehouse Bot...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log level: {settings.log_level}")

    # Create application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Add middleware (runs before all commands with group=-1)
    auth_middleware = AuthMiddleware()
    application.add_handler(TypeHandler(Update, auth_middleware), group=-1)

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))

    # Inventory commands (legacy)
    application.add_handler(CommandHandler("inventory", commands.inventory_command))
    application.add_handler(CommandHandler("inventory_ingredients", commands.ingredients_inventory_command))
    application.add_handler(CommandHandler("low_stock", commands.low_stock_command))

    # NEW: Inventory Management System
    # Conversation handlers for multi-step flows
    application.add_handler(inventory.get_add_inventory_handler())
    application.add_handler(inventory.get_consume_inventory_handler())
    application.add_handler(inventory.get_correction_handler())

    # Simple command handlers
    application.add_handler(CommandHandler("view_logs", inventory.view_logs_command))
    application.add_handler(CommandHandler("view_inventory", inventory.view_inventory_command))

    # Staff selection callback handler (for Mode B authentication)
    application.add_handler(CallbackQueryHandler(handle_staff_selection_callback, pattern=r"^staff_select:"))

    # Sales commands
    application.add_handler(CommandHandler("sale", commands.sale_command))

    # Production commands (MANAGER+)
    application.add_handler(CommandHandler("production", commands.production_command))

    # Purchase commands (MANAGER+)
    application.add_handler(CommandHandler("purchase", commands.purchase_command))

    # Report commands (MANAGER+)
    application.add_handler(CommandHandler("report", commands.report_command))

    # Sync commands (ADMIN)
    application.add_handler(CommandHandler("sync_square", admin.sync_square_command))
    application.add_handler(CommandHandler("sync_sheets", admin.sync_sheets_command))
    application.add_handler(CommandHandler("sync_all", admin.sync_all_command))

    # User management (ADMIN)
    application.add_handler(CommandHandler("users", admin.list_users_command))
    application.add_handler(CommandHandler("add_user", admin.add_user_command))
    application.add_handler(CommandHandler("change_role", admin.change_role_command))
    application.add_handler(CommandHandler("profile", commands.my_profile_command))

    # Error handler
    application.add_error_handler(commands.error_handler)

    # Start bot
    logger.success("Bot started successfully!")
    logger.info("Press Ctrl+C to stop")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
