"""
Chocodealers Warehouse Management Telegram Bot
Main entry point
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from alembic.config import Config
from alembic import command

from config.config import settings
from database.db import init_db, close_db
from bot.handlers import commands, admin, inventory
from bot.middleware.auth import AuthMiddleware
from bot.utils.logger import setup_logger
from bot.utils.staff_auth import handle_staff_selection_callback


# Setup logging
setup_logger(settings.log_level, settings.log_file)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False) -> None:
    """Show main menu with hierarchical navigation"""
    user = update.effective_user

    welcome_message = f"""🍫 **Chocodealers Warehouse Bot**

Hi, {user.first_name}!

Welcome to your warehouse management system.
Select a category below to get started:
"""

    # Main menu keyboard
    keyboard = [
        [
            InlineKeyboardButton("📦 Inventory Management", callback_data="menu_inventory"),
        ],
        [
            InlineKeyboardButton("💰 Sales & Orders", callback_data="menu_sales"),
        ],
        [
            InlineKeyboardButton("🏭 Production", callback_data="menu_production"),
            InlineKeyboardButton("📊 Reports", callback_data="menu_reports"),
        ],
        [
            InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_admin"),
            InlineKeyboardButton("ℹ️ Help & Info", callback_data="menu_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    await show_main_menu(update, context, edit=False)


async def show_inventory_submenu(query) -> None:
    """Show inventory management submenu"""
    message = """📦 **Inventory Management**

Choose an inventory operation:
"""

    keyboard = [
        [
            InlineKeyboardButton("👀 View Stock", callback_data="inv_view_stock"),
        ],
        [
            InlineKeyboardButton("➕ Add Inventory", callback_data="inv_add"),
            InlineKeyboardButton("➖ Consume Stock", callback_data="inv_consume"),
        ],
        [
            InlineKeyboardButton("🔧 Manual Correction", callback_data="inv_correction"),
            InlineKeyboardButton("📜 Transaction History", callback_data="inv_history"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def show_sales_submenu(query) -> None:
    """Show sales & orders submenu"""
    message = """💰 **Sales & Orders**

Manage your sales operations:
"""

    keyboard = [
        [
            InlineKeyboardButton("💵 Register Quick Sale", callback_data="sale_quick"),
        ],
        [
            InlineKeyboardButton("📊 View Sales Report", callback_data="sale_report"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def show_reports_submenu(query) -> None:
    """Show reports submenu"""
    message = """📊 **Reports & Analytics**

View business reports:
"""

    keyboard = [
        [
            InlineKeyboardButton("📅 Daily Report", callback_data="report_day"),
        ],
        [
            InlineKeyboardButton("📆 Weekly Report", callback_data="report_week"),
            InlineKeyboardButton("📊 Monthly Report", callback_data="report_month"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def show_admin_submenu(query) -> None:
    """Show admin panel submenu"""
    message = """⚙️ **Admin Panel**

Administrative functions:
"""

    keyboard = [
        [
            InlineKeyboardButton("👥 Manage Users", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🔄 Sync Square POS", callback_data="admin_sync_square"),
            InlineKeyboardButton("📊 Sync Google Sheets", callback_data="admin_sync_sheets"),
        ],
        [
            InlineKeyboardButton("🔄 Sync All Systems", callback_data="admin_sync_all"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def show_help_submenu(query) -> None:
    """Show help & info submenu"""
    message = """ℹ️ **Help & Information**

Get assistance and system info:
"""

    keyboard = [
        [
            InlineKeyboardButton("📖 Command Guide", callback_data="help_guide"),
            InlineKeyboardButton("📊 System Status", callback_data="help_status"),
        ],
        [
            InlineKeyboardButton("👤 My Profile", callback_data="help_profile"),
        ],
        [
            InlineKeyboardButton("◀️ Back to Main Menu", callback_data="menu_main"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all menu navigation callbacks"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Main menu navigation
    if callback_data == "menu_main":
        await show_main_menu(update, context, edit=True)

    # Submenu navigation
    elif callback_data == "menu_inventory":
        await show_inventory_submenu(query)
    elif callback_data == "menu_sales":
        await show_sales_submenu(query)
    elif callback_data == "menu_reports":
        await show_reports_submenu(query)
    elif callback_data == "menu_admin":
        await show_admin_submenu(query)
    elif callback_data == "menu_help":
        await show_help_submenu(query)

    # Inventory actions
    elif callback_data == "inv_view_stock":
        await query.edit_message_text("Use command: /view_inventory")
    elif callback_data == "inv_add":
        await query.edit_message_text("Use command: /add_inventory")
    elif callback_data == "inv_consume":
        await query.edit_message_text("Use command: /consume_inventory")
    elif callback_data == "inv_correction":
        await query.edit_message_text("Use command: /correction")
    elif callback_data == "inv_history":
        await query.edit_message_text("Use command: /view_logs")

    # Sales actions
    elif callback_data == "sale_quick":
        await query.edit_message_text(
            "💰 To register a sale, use:\n\n"
            "/sale <SKU> <quantity> [price]\n\n"
            "Example: /sale BAR-S-01 5"
        )
    elif callback_data == "sale_report":
        await query.edit_message_text("Use command: /report day")

    # Reports actions
    elif callback_data == "report_day":
        await query.edit_message_text("Use command: /report day")
    elif callback_data == "report_week":
        await query.edit_message_text("Use command: /report week")
    elif callback_data == "report_month":
        await query.edit_message_text("Use command: /report month")

    # Admin actions
    elif callback_data == "admin_users":
        await query.edit_message_text("Use command: /users")
    elif callback_data == "admin_sync_square":
        await query.edit_message_text("Use command: /sync_square")
    elif callback_data == "admin_sync_sheets":
        await query.edit_message_text("Use command: /sync_sheets")
    elif callback_data == "admin_sync_all":
        await query.edit_message_text("Use command: /sync_all")

    # Help actions
    elif callback_data == "help_guide":
        await query.edit_message_text("Use command: /help")
    elif callback_data == "help_status":
        await query.edit_message_text("Use command: /status")
    elif callback_data == "help_profile":
        await query.edit_message_text("Use command: /profile")

    # Production menu (simple for now)
    elif callback_data == "menu_production":
        await query.edit_message_text(
            "🏭 **Production**\n\n"
            "To produce items, use:\n\n"
            "/production <SKU> <quantity>\n\n"
            "Example: /production BAR-S-01 100\n\n"
            "Note: Requires MANAGER or ADMIN role."
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

    # ---------------------------------------------------------
    # Run Alembic migration programmatically from Python code
    # This avoids silent crashes from shell command execution
    # ---------------------------------------------------------
    logger.info("🚀 Starting Alembic Migration...")
    try:
        # Point to alembic.ini in project root
        alembic_cfg = Config("alembic.ini")

        # Explicitly set script location (alembic may lose path to env.py)
        alembic_cfg.set_main_option("script_location", "alembic")

        # Explicitly set database URL so alembic doesn't search for it
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        # Run migration in a thread to avoid blocking the event loop
        # (migrations are synchronous blocking operations)
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

        logger.success("✅ Alembic Migration Completed Successfully!")

    except Exception as e:
        logger.error(f"❌ Migration Failed: {e}")
        # Re-raise to prevent bot from running with incomplete database
        raise e
    # ---------------------------------------------------------

    # Original init_db (now just logs, migration handled above)
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

    # Menu navigation callback handler (for all inline keyboard buttons)
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^(menu_|inv_|sale_|report_|admin_|help_)"))

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
