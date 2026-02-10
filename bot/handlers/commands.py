"""
Main command handlers for Chocodealers Bot
Handles inventory, sales, production, purchases, and reports
"""

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional

from database.db import get_db
from database.models import (
    User, Product, Ingredient, InventoryProduct, InventoryIngredient,
    Sale, Production, Purchase, UserRole, SaleSource, PaymentMethod,
    ProductionStatus, PurchaseStatus
)
from bot.middleware.auth import require_role
from bot.utils.formatters import (
    format_inventory_list, format_product_info, format_ingredient_info,
    format_sale_receipt, format_low_stock_alert
)


# ============================================
# INVENTORY COMMANDS
# ============================================

async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show inventory levels
    Usage: /inventory [SKU or name]
    """
    user_id = update.effective_user.id
    args = context.args

    async with get_db() as db:
        # Check if searching for specific product
        if args:
            search_term = " ".join(args).strip()

            # Search by SKU or name
            stmt = select(Product).join(InventoryProduct).where(
                or_(
                    Product.sku.ilike(f"%{search_term}%"),
                    Product.name.ilike(f"%{search_term}%")
                )
            ).options(joinedload(Product.inventory))

            result = await db.execute(stmt)
            products = result.scalars().all()

            if not products:
                await update.message.reply_text(
                    f"❌ Product '{search_term}' not found.\n"
                    f"Use /inventory to view all products."
                )
                return

            # Show detailed info for found products
            response = f"🔍 Search results for '{search_term}':\n\n"
            for product in products[:10]:  # Limit to 10 results
                inv = product.inventory
                margin = ((product.retail_price_thb - product.cogs_thb) / product.retail_price_thb * 100)

                response += f"**{product.name}** ({product.sku})\n"
                response += f"📦 Stock: **{inv.quantity}** pcs"

                if inv.quantity < inv.min_stock_level:
                    response += f" ⚠️ LOW"
                response += f"\n💰 Price: {product.retail_price_thb}฿ (margin {margin:.1f}%)\n"
                response += f"📊 Category: {product.category.value}\n\n"

        else:
            # Show all products grouped by category
            stmt = select(Product).join(InventoryProduct).order_by(
                Product.category, Product.sku
            ).options(joinedload(Product.inventory))

            result = await db.execute(stmt)
            products = result.scalars().all()

            if not products:
                await update.message.reply_text("❌ No products found in database.")
                return

            # Group by category
            from collections import defaultdict
            categories = defaultdict(list)

            for product in products:
                categories[product.category].append(product)

            response = "📦 **INVENTORY**\n\n"

            for category, items in categories.items():
                response += f"**{category.value}**\n"
                for product in items:
                    inv = product.inventory
                    status = "⚠️" if inv.quantity < inv.min_stock_level else "✅"
                    response += f"{status} {product.sku}: {inv.quantity} pcs\n"
                response += "\n"

            response += f"_Total products: {len(products)}_\n"
            response += "Use `/inventory <SKU>` for details"

    await update.message.reply_text(response, parse_mode="Markdown")
    logger.info(f"User {user_id} checked inventory")


async def ingredients_inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show ingredients inventory"""
    async with get_db() as db:
        stmt = select(Ingredient).join(InventoryIngredient).order_by(
            Ingredient.category, Ingredient.code
        ).options(joinedload(Ingredient.inventory))

        result = await db.execute(stmt)
        ingredients = result.scalars().all()

        if not ingredients:
            await update.message.reply_text("❌ No ingredients found.")
            return

        from collections import defaultdict
        categories = defaultdict(list)

        for ing in ingredients:
            categories[ing.category].append(ing)

        response = "🥜 **INGREDIENTS INVENTORY**\n\n"

        for category, items in categories.items():
            response += f"**{category.value}**\n"
            for ing in items:
                inv = ing.inventory
                status = "⚠️" if inv.quantity_kg < inv.min_stock_level_kg else "✅"
                response += f"{status} {ing.code}: {inv.quantity_kg:.2f} kg\n"
            response += "\n"

        response += f"_Total ingredients: {len(ingredients)}_"

    await update.message.reply_text(response, parse_mode="Markdown")


async def low_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show products with low stock"""
    async with get_db() as db:
        # Products with low stock
        stmt = select(Product, InventoryProduct).join(InventoryProduct).where(
            InventoryProduct.quantity < InventoryProduct.min_stock_level
        ).order_by(InventoryProduct.quantity)

        result = await db.execute(stmt)
        low_stock_products = result.all()

        # Ingredients with low stock
        stmt_ing = select(Ingredient, InventoryIngredient).join(InventoryIngredient).where(
            InventoryIngredient.quantity_kg < InventoryIngredient.min_stock_level_kg
        ).order_by(InventoryIngredient.quantity_kg)

        result_ing = await db.execute(stmt_ing)
        low_stock_ingredients = result_ing.all()

        if not low_stock_products and not low_stock_ingredients:
            await update.message.reply_text("✅ All products and ingredients are sufficiently stocked!")
            return

        response = "⚠️ **LOW STOCK ITEMS**\n\n"

        if low_stock_products:
            response += "**PRODUCTS:**\n"
            for product, inv in low_stock_products:
                shortage = inv.min_stock_level - inv.quantity
                response += f"• {product.sku} ({product.name})\n"
                response += f"  Stock: {inv.quantity} / Min: {inv.min_stock_level} (need: {shortage})\n\n"

        if low_stock_ingredients:
            response += "**INGREDIENTS:**\n"
            for ing, inv in low_stock_ingredients:
                shortage = inv.min_stock_level_kg - inv.quantity_kg
                response += f"• {ing.code} ({ing.name})\n"
                response += f"  Stock: {inv.quantity_kg:.2f} kg / Min: {inv.min_stock_level_kg:.2f} kg\n\n"

    await update.message.reply_text(response, parse_mode="Markdown")


# ============================================
# SALES COMMANDS
# ============================================

@require_role([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN])
async def sale_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Register a sale
    Usage: /sale <SKU> <quantity> [price]
    """
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "❌ Invalid format.\n"
            "Usage: `/sale <SKU> <quantity> [price]`\n"
            "Example: `/sale BAR-S-01 5` or `/sale TRF-002 3 180`",
            parse_mode="Markdown"
        )
        return

    sku = args[0].upper()
    try:
        quantity = int(args[1])
        custom_price = float(args[2]) if len(args) > 2 else None
    except ValueError:
        await update.message.reply_text("❌ Quantity and price must be numbers.")
        return

    if quantity <= 0:
        await update.message.reply_text("❌ Quantity must be greater than 0.")
        return

    async with get_db() as db:
        # Find product with row-level lock to prevent race conditions
        stmt = (
            select(Product)
            .where(Product.sku == sku)
            .options(joinedload(Product.inventory))
            .with_for_update()  # Lock row until transaction commits
        )
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            await update.message.reply_text(f"❌ Product with SKU '{sku}' not found.")
            return

        inv = product.inventory

        # Check inventory
        if inv.quantity < quantity:
            await update.message.reply_text(
                f"❌ Insufficient stock!\n"
                f"Available: {inv.quantity} pcs\n"
                f"Requested: {quantity} pcs"
            )
            return

        # Get user
        stmt_user = select(User).where(User.telegram_id == user_id)
        result_user = await db.execute(stmt_user)
        user = result_user.scalar_one_or_none()

        # Calculate price
        unit_price = custom_price if custom_price else product.retail_price_thb
        total_price = quantity * unit_price

        # Create sale
        sale = Sale(
            product_id=product.id,
            quantity=quantity,
            unit_price_thb=unit_price,
            final_price_thb=total_price,
            source=SaleSource.TELEGRAM_BOT,
            payment_method=PaymentMethod.CASH,
            created_by=user.id if user else None
        )
        db.add(sale)

        # Update inventory
        inv.quantity -= quantity

        await db.commit()

        # Send receipt
        margin = ((unit_price - product.cogs_thb) / unit_price * 100) if unit_price > 0 else 0
        profit = (unit_price - product.cogs_thb) * quantity

        receipt = f"""
✅ **SALE REGISTERED**

🍫 Product: {product.name} ({sku})
📦 Quantity: {quantity} pcs
💰 Price per unit: {unit_price:.2f}฿
💵 Total: {total_price:.2f}฿

📊 Margin: {margin:.1f}%
💎 Profit: {profit:.2f}฿

📦 Stock remaining: {inv.quantity} pcs
"""

        await update.message.reply_text(receipt, parse_mode="Markdown")
        logger.info(f"Sale registered: {sku} x{quantity} by user {user_id}")


# ============================================
# PRODUCTION COMMANDS (MANAGER+)
# ============================================

@require_role([UserRole.MANAGER, UserRole.ADMIN])
async def production_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Register production
    Usage: /production <SKU> <quantity>
    """
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/production <SKU> <quantity>`\n"
            "Example: `/production BAR-S-01 100`",
            parse_mode="Markdown"
        )
        return

    sku = args[0].upper()
    try:
        quantity = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Quantity must be a number.")
        return

    # Implementation here (similar structure to sale_command)
    await update.message.reply_text(f"🏭 Production of {quantity} pcs of {sku} (in development)")


# ============================================
# PURCHASE COMMANDS (MANAGER+)
# ============================================

@require_role([UserRole.MANAGER, UserRole.ADMIN])
async def purchase_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register ingredient purchase"""
    await update.message.reply_text("🛒 Ingredient purchase (in development)")


# ============================================
# REPORT COMMANDS (MANAGER+)
# ============================================

@require_role([UserRole.MANAGER, UserRole.ADMIN])
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate reports"""
    await update.message.reply_text("📊 Report generation (in development)")


# ============================================
# USER PROFILE
# ============================================

async def my_profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile"""
    user_id = update.effective_user.id

    async with get_db() as db:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await update.message.reply_text("❌ You are not registered in the system.")
            return

        profile = f"""
👤 **YOUR PROFILE**

Name: {user.first_name} {user.last_name or ''}
Username: @{update.effective_user.username or 'N/A'}
Telegram ID: `{user.telegram_id}`

🔐 Role: **{user.role.value}**
📊 Status: {user.status.value}

📅 Registered: {user.created_at.strftime('%d.%m.%Y')}
🕐 Last login: {user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else 'N/A'}
"""

        await update.message.reply_text(profile, parse_mode="Markdown")


# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred while processing the command. Please try again later."
        )
