"""
Inventory Management Command Handlers

Handles all inventory-related commands:
- /add_inventory (приход) - Add incoming goods
- /consume_inventory (расход) - Record consumption/sales
- /correction - Manual inventory correction (ADMIN ONLY)
- /view_logs - View transaction history
- /view_inventory - View current stock levels
"""

import logging
from datetime import datetime
from typing import Optional, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload

from database.db import get_db
from database.models import (
    Product,
    ProductCategory,
    TransactionLog,
    TransactionActionType,
    InventoryProduct,
)
from bot.utils.unit_conversion import (
    convert_to_grams,
    parse_quantity_input,
    format_quantity,
    get_base_unit_for_category,
)
from bot.utils.staff_auth import (
    get_user_info,
    request_staff_selection,
    can_access_category,
    requires_admin_check,
    clear_staff_selection,
)

logger = logging.getLogger(__name__)

# Conversation states
(
    SELECT_CATEGORY,
    SELECT_PRODUCT,
    ENTER_QUANTITY,
    CONFIRM_ACTION,
    ENTER_NOTES,
) = range(5)


# ============================================
# ADD INVENTORY (/add_inventory, /приход)
# ============================================

async def add_inventory_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the add inventory flow.
    Command: /add_inventory or /приход
    """
    user_info = await get_user_info(update, context)

    # If no user info, need staff selection (Mode B)
    if not user_info:
        await request_staff_selection(
            update, context,
            "👤 **Please select your name before adding inventory:**"
        )
        # Store the action type for after selection
        context.user_data["pending_action"] = "add_inventory"
        return ConversationHandler.END

    # Show category selection
    await show_category_selection(update, context, action="add", user_info=user_info)
    return SELECT_CATEGORY


async def show_category_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_info: Dict
) -> None:
    """Show product category selection buttons"""
    # Get all categories
    categories = [
        ("🍫 Our Chocolate", ProductCategory.OUR_CHOCOLATE),
        ("🥘 Chocolate Ingredients", ProductCategory.CHOCOLATE_INGREDIENTS),
        ("🍵 Chinese Tea", ProductCategory.CHINESE_TEA),
        ("☕ Beverages/Coffee", ProductCategory.BEVERAGES_COFFEE),
        ("🛍️ Shop Merchandise", ProductCategory.SHOP_MERCHANDISE),
        ("🧹 Household Items", ProductCategory.HOUSEHOLD_ITEMS),
        ("📦 Chocolate Packaging", ProductCategory.CHOCOLATE_PACKAGING),
        ("📦 Other Packaging", ProductCategory.OTHER_PACKAGING),
        ("🖨️ Printing Materials", ProductCategory.PRINTING_MATERIALS),
        ("⚙️ Equipment/Materials", ProductCategory.EQUIPMENT_MATERIALS),
    ]

    # Add AI Expenses if user is admin
    if user_info.get("is_admin"):
        categories.append(("💻 AI Expenses", ProductCategory.AI_EXPENSES))

    # Create keyboard
    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                name, cat_value = categories[i + j]
                row.append(
                    InlineKeyboardButton(
                        name,
                        callback_data=f"inv_{action}_cat:{cat_value.value}"
                    )
                )
        keyboard.append(row)

    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="inv_cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    action_text = {
        "add": "➕ **Add Inventory** - Select Category:",
        "consume": "➖ **Consume Inventory** - Select Category:",
        "correct": "✏️ **Correct Inventory** - Select Category:",
    }.get(action, "Select Category:")

    await update.message.reply_text(action_text, reply_markup=reply_markup, parse_mode="Markdown")


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection and show products in that category"""
    query = update.callback_query
    await query.answer()

    # Extract category from callback data
    callback_data = query.data
    # Format: inv_add_cat:OUR_CHOCOLATE
    parts = callback_data.split(":")
    if len(parts) != 2:
        await query.edit_message_text("❌ Invalid selection. Please try again.")
        return ConversationHandler.END

    action = parts[0].replace("inv_", "").replace("_cat", "")
    category_value = parts[1]

    # Store in context
    context.user_data["action_type"] = action
    context.user_data["selected_category"] = category_value

    # Fetch products in this category
    async with get_db() as db:
        stmt = (
            select(Product)
            .where(Product.category == category_value)
            .where(Product.is_active == True)
            .order_by(Product.name)
        )
        result = await db.execute(stmt)
        products = result.scalars().all()

    if not products:
        await query.edit_message_text(
            f"📭 No products found in this category.\n\nUse /add_product to create one first.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # Create product selection keyboard
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                f"{product.name} ({product.sku})",
                callback_data=f"inv_{action}_prod:{product.id}"
            )
        ])

    # Add back and cancel buttons
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data=f"inv_{action}_back"),
        InlineKeyboardButton("❌ Cancel", callback_data="inv_cancel")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    category_name = ProductCategory(category_value).name.replace("_", " ").title()

    await query.edit_message_text(
        f"📦 **{category_name}** - Select Product:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return SELECT_PRODUCT


async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection and request quantity"""
    query = update.callback_query
    await query.answer()

    # Extract product ID from callback data
    callback_data = query.data
    # Format: inv_add_prod:uuid
    parts = callback_data.split(":")
    if len(parts) != 2:
        await query.edit_message_text("❌ Invalid selection. Please try again.")
        return ConversationHandler.END

    product_id = parts[1]
    action = parts[0].replace("inv_", "").replace("_prod", "")

    # Store in context
    context.user_data["selected_product_id"] = product_id

    # Fetch product details
    async with get_db() as db:
        stmt = select(Product).where(Product.id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

    if not product:
        await query.edit_message_text("❌ Product not found. Please try again.")
        return ConversationHandler.END

    # Store product info for conversion
    context.user_data["product_info"] = {
        "name": product.name,
        "sku": product.sku,
        "category": product.category.value,
        "grammovka": product.grammovka,
        "unit_type": product.unit_type,
        "quantity_per_package": product.quantity_per_package,
    }

    # Show quantity input prompt
    action_text = {
        "add": f"➕ **Adding:** {product.name}\n\n",
        "consume": f"➖ **Consuming:** {product.name}\n\n",
        "correct": f"✏️ **Correcting:** {product.name}\n\n",
    }.get(action, "")

    # Suggest appropriate units based on product category
    base_unit = get_base_unit_for_category(product.category.value)
    if base_unit == "grams":
        unit_examples = "g, kg, ml, L"
    else:
        unit_examples = "pieces, boxes, packs"

    prompt_text = (
        f"{action_text}"
        f"💬 **Enter quantity and unit:**\n\n"
        f"Examples: `5 kg`, `100 g`, `3 pieces`, `2 boxes`\n"
        f"Supported units: {unit_examples}\n\n"
        f"Type your quantity below:"
    )

    await query.edit_message_text(prompt_text, parse_mode="Markdown")

    return ENTER_QUANTITY


async def quantity_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input and show confirmation"""
    user_input = update.message.text.strip()

    # Parse quantity input
    value, unit = parse_quantity_input(user_input)

    if value is None or unit is None:
        await update.message.reply_text(
            "❌ **Invalid format!**\n\n"
            "Please enter quantity and unit, e.g.:\n"
            "• `5 kg`\n"
            "• `100 g`\n"
            "• `3 pieces`",
            parse_mode="Markdown"
        )
        return ENTER_QUANTITY

    # Validate quantity is positive
    if value <= 0:
        await update.message.reply_text(
            "❌ **Invalid quantity!**\n\n"
            f"Quantity must be greater than zero.\n"
            f"You entered: {value} {unit}\n\n"
            f"Please enter a positive number.",
            parse_mode="Markdown"
        )
        return ENTER_QUANTITY

    # Convert to grams
    product_info = context.user_data.get("product_info", {})
    try:
        grams, display_str = convert_to_grams(value, unit, product_info)
    except Exception as e:
        logger.error(f"Unit conversion error: {e}")
        await update.message.reply_text(
            f"❌ **Conversion error:** {str(e)}\n\n"
            f"Please try a different unit or contact admin.",
            parse_mode="Markdown"
        )
        return ENTER_QUANTITY

    # Store in context
    context.user_data["quantity_original"] = value
    context.user_data["quantity_unit"] = unit
    context.user_data["quantity_grams"] = grams
    context.user_data["quantity_display"] = display_str

    # Show confirmation
    action = context.user_data.get("action_type", "add")
    action_emoji = {"add": "➕", "consume": "➖", "correct": "✏️"}.get(action, "")
    action_name = {"add": "Add", "consume": "Consume", "correct": "Correct to"}.get(action, "")

    product_name = product_info.get("name", "Unknown")

    confirmation_text = (
        f"{action_emoji} **Confirm {action_name}**\n\n"
        f"📦 **Product:** {product_name}\n"
        f"📊 **Quantity:** {display_str}\n"
        f"💾 **Storage:** {grams}g (base unit)\n\n"
        f"Proceed?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="inv_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="inv_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        confirmation_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    return CONFIRM_ACTION


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation and save transaction to database"""
    query = update.callback_query
    await query.answer()

    # Get user info
    user_info = await get_user_info(update, context)
    if not user_info:
        await query.edit_message_text(
            "❌ Authentication error. Please start over with /add_inventory"
        )
        return ConversationHandler.END

    # Get stored data
    action = context.user_data.get("action_type")
    product_id = context.user_data.get("selected_product_id")
    product_info = context.user_data.get("product_info")
    quantity_grams = context.user_data.get("quantity_grams")
    quantity_original = context.user_data.get("quantity_original")
    quantity_unit = context.user_data.get("quantity_unit")
    quantity_display = context.user_data.get("quantity_display")

    # Map action to TransactionActionType
    action_type_map = {
        "add": TransactionActionType.ADD,
        "consume": TransactionActionType.CONSUME,
        "correct": TransactionActionType.CORRECTION,
    }
    transaction_action = action_type_map.get(action, TransactionActionType.ADD)

    try:
        async with get_db() as db:
            # Create transaction log
            transaction_log = TransactionLog(
                telegram_user_id=user_info["telegram_user_id"],
                user_name=user_info["user_name"],
                product_id=product_id,
                product_name=product_info["name"],
                category=ProductCategory(product_info["category"]),
                action_type=transaction_action,
                quantity_original=quantity_original,
                quantity_unit=quantity_unit,
                quantity_grams=quantity_grams,
                quantity_display=quantity_display,
                notes=context.user_data.get("notes", ""),
                source="telegram_bot",
                admin_flag=user_info.get("is_admin", False),
            )
            db.add(transaction_log)

            # Update inventory with row-level locking to prevent race conditions
            stmt = (
                select(InventoryProduct)
                .where(InventoryProduct.product_id == product_id)
                .with_for_update()  # CRITICAL: Lock row until transaction commits
            )
            result = await db.execute(stmt)
            inventory = result.scalar_one_or_none()

            # Handle different transaction types
            if transaction_action == TransactionActionType.ADD:
                # ADD: Create inventory if doesn't exist, or add to existing
                if not inventory:
                    inventory = InventoryProduct(
                        product_id=product_id,
                        quantity=quantity_grams,
                    )
                    db.add(inventory)
                else:
                    inventory.quantity += quantity_grams

            elif transaction_action == TransactionActionType.CONSUME:
                # CONSUME: Must have existing inventory with sufficient stock
                if not inventory:
                    await query.edit_message_text(
                        "❌ **Error:** Product not in inventory!\n\n"
                        f"Cannot consume {quantity_grams}g - no stock record found.\n"
                        f"Please use /add_inventory first.",
                        parse_mode="Markdown"
                    )
                    return ConversationHandler.END

                if inventory.quantity < quantity_grams:
                    await query.edit_message_text(
                        "❌ **Error:** Not enough inventory!\n\n"
                        f"Available: {inventory.quantity}g\n"
                        f"Requested: {quantity_grams}g\n"
                        f"Shortage: {quantity_grams - inventory.quantity}g",
                        parse_mode="Markdown"
                    )
                    return ConversationHandler.END

                inventory.quantity -= quantity_grams

            elif transaction_action == TransactionActionType.CORRECTION:
                # CORRECTION: Set to exact value (create if doesn't exist)
                if not inventory:
                    inventory = InventoryProduct(
                        product_id=product_id,
                        quantity=quantity_grams,
                    )
                    db.add(inventory)
                else:
                    inventory.quantity = quantity_grams

            inventory.last_count_at = datetime.utcnow()

            await db.commit()

            # CRITICAL: Clear staff selection for Mode B security
            # This prevents the next person using shared device from being logged as previous user
            clear_staff_selection(context)

            # Success message
            action_emoji = {"add": "➕", "consume": "➖", "correct": "✏️"}.get(action, "")
            action_past = {"add": "added", "consume": "consumed", "correct": "corrected"}.get(action, "")

            success_text = (
                f"{action_emoji} **Success!** Inventory {action_past}\n\n"
                f"📦 **Product:** {product_info['name']}\n"
                f"📊 **Quantity:** {quantity_display}\n"
                f"💾 **New Stock:** {inventory.quantity}g\n"
                f"👤 **Recorded by:** {user_info['user_name']}"
            )

            await query.edit_message_text(success_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error saving transaction: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ **Error saving transaction:**\n\n{str(e)}",
            parse_mode="Markdown"
        )

    return ConversationHandler.END


async def cancel_inventory_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the inventory action"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ **Cancelled.** Use /add_inventory to start again.")
    return ConversationHandler.END


# ============================================
# CONSUME INVENTORY (/consume_inventory, /расход)
# ============================================

async def consume_inventory_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the consume inventory flow"""
    user_info = await get_user_info(update, context)

    if not user_info:
        await request_staff_selection(
            update, context,
            "👤 **Please select your name before consuming inventory:**"
        )
        context.user_data["pending_action"] = "consume_inventory"
        return ConversationHandler.END

    await show_category_selection(update, context, action="consume", user_info=user_info)
    return SELECT_CATEGORY


# ============================================
# CORRECTION (/correction) - ADMIN ONLY
# ============================================

async def correction_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the correction flow (ADMIN ONLY)"""
    user_info = await get_user_info(update, context)

    if not user_info:
        await request_staff_selection(
            update, context,
            "👤 **Please select your name:**"
        )
        context.user_data["pending_action"] = "correction"
        return ConversationHandler.END

    # Check admin permission
    if not requires_admin_check(user_info):
        await update.message.reply_text(
            "❌ **Access Denied**\n\n"
            "Only admins can perform inventory corrections.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await show_category_selection(update, context, action="correct", user_info=user_info)
    return SELECT_CATEGORY


# ============================================
# VIEW LOGS (/view_logs)
# ============================================

async def view_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View recent transaction logs"""
    user_info = await get_user_info(update, context)

    if not user_info:
        await request_staff_selection(
            update, context,
            "👤 **Please select your name to view logs:**"
        )
        return

    try:
        async with get_db() as db:
            # Get last 20 transactions
            stmt = (
                select(TransactionLog)
                .options(joinedload(TransactionLog.product))
                .order_by(desc(TransactionLog.created_at))
                .limit(20)
            )
            result = await db.execute(stmt)
            logs = result.scalars().all()

        if not logs:
            await update.message.reply_text(
                "📭 **No transaction logs found.**\n\n"
                "Start recording with /add_inventory",
                parse_mode="Markdown"
            )
            return

        # Format logs
        log_text = "📋 **Recent Transaction Logs** (Last 20)\n\n"
        for log in logs:
            action_emoji = {
                TransactionActionType.ADD: "➕",
                TransactionActionType.CONSUME: "➖",
                TransactionActionType.CORRECTION: "✏️",
            }.get(log.action_type, "")

            date_str = log.created_at.strftime("%Y-%m-%d %H:%M")
            log_text += (
                f"{action_emoji} **{log.action_type.value}** | {log.product_name}\n"
                f"   📊 {log.quantity_display} | 👤 {log.user_name}\n"
                f"   🕐 {date_str}\n\n"
            )

        await update.message.reply_text(log_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error fetching logs: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Error fetching logs:** {str(e)}",
            parse_mode="Markdown"
        )


# ============================================
# VIEW INVENTORY (/view_inventory)
# ============================================

async def view_inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View current inventory levels"""
    try:
        async with get_db() as db:
            stmt = (
                select(InventoryProduct)
                .options(joinedload(InventoryProduct.product))
                .order_by(InventoryProduct.updated_at.desc())
            )
            result = await db.execute(stmt)
            inventory_items = result.scalars().all()

        if not inventory_items:
            await update.message.reply_text(
                "📭 **No inventory records found.**\n\n"
                "Start adding inventory with /add_inventory",
                parse_mode="Markdown"
            )
            return

        # Group by category
        by_category = {}
        for item in inventory_items:
            category = item.product.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(item)

        # Format inventory
        inv_text = "📦 **Current Inventory Levels**\n\n"
        for category, items in by_category.items():
            category_name = ProductCategory(category).name.replace("_", " ").title()
            inv_text += f"**{category_name}:**\n"
            for item in items:
                stock_status = "✅" if item.quantity >= item.min_stock_level else "⚠️"
                inv_text += (
                    f"  {stock_status} {item.product.name}: {item.quantity}g\n"
                )
            inv_text += "\n"

        await update.message.reply_text(inv_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error fetching inventory: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ **Error fetching inventory:** {str(e)}",
            parse_mode="Markdown"
        )


# ============================================
# CONVERSATION HANDLER SETUP
# ============================================

def get_add_inventory_handler() -> ConversationHandler:
    """Get conversation handler for add_inventory flow"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("add_inventory", add_inventory_start),
            CommandHandler("приход", add_inventory_start),  # Russian alias
        ],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern=r"^inv_(add|consume|correct)_cat:"),
            ],
            SELECT_PRODUCT: [
                CallbackQueryHandler(product_selected, pattern=r"^inv_(add|consume|correct)_prod:"),
            ],
            ENTER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_entered),
            ],
            CONFIRM_ACTION: [
                CallbackQueryHandler(confirm_action, pattern="^inv_confirm$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_inventory_action, pattern="^inv_cancel$"),
            CommandHandler("cancel", cancel_inventory_action),
        ],
    )


def get_consume_inventory_handler() -> ConversationHandler:
    """Get conversation handler for consume_inventory flow"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("consume_inventory", consume_inventory_start),
            CommandHandler("расход", consume_inventory_start),  # Russian alias
        ],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern=r"^inv_(add|consume|correct)_cat:"),
            ],
            SELECT_PRODUCT: [
                CallbackQueryHandler(product_selected, pattern=r"^inv_(add|consume|correct)_prod:"),
            ],
            ENTER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_entered),
            ],
            CONFIRM_ACTION: [
                CallbackQueryHandler(confirm_action, pattern="^inv_confirm$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_inventory_action, pattern="^inv_cancel$"),
            CommandHandler("cancel", cancel_inventory_action),
        ],
    )


def get_correction_handler() -> ConversationHandler:
    """Get conversation handler for correction flow (ADMIN ONLY)"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("correction", correction_start),
        ],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern=r"^inv_(add|consume|correct)_cat:"),
            ],
            SELECT_PRODUCT: [
                CallbackQueryHandler(product_selected, pattern=r"^inv_(add|consume|correct)_prod:"),
            ],
            ENTER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_entered),
            ],
            CONFIRM_ACTION: [
                CallbackQueryHandler(confirm_action, pattern="^inv_confirm$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_inventory_action, pattern="^inv_cancel$"),
            CommandHandler("cancel", cancel_inventory_action),
        ],
    )


# ============================================
# EXPORT
# ============================================

__all__ = [
    "get_add_inventory_handler",
    "get_consume_inventory_handler",
    "get_correction_handler",
    "view_logs_command",
    "view_inventory_command",
]
