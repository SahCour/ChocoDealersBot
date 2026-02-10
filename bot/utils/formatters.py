"""
Message formatters for beautiful Telegram outputs
"""

from typing import List
from database.models import Product, Ingredient, Sale


def format_product_info(product: Product, inventory_quantity: int) -> str:
    """Format product information"""
    margin = ((product.retail_price_thb - product.cogs_thb) / product.retail_price_thb * 100)

    return f"""
🍫 **{product.name}**
SKU: `{product.sku}`
Category: {product.category.value}
Weight: {product.weight_g}g | Cocoa: {product.cocoa_percent}

💰 Price: {product.retail_price_thb}฿
📊 COGS: {product.cogs_thb}฿
📈 Margin: {margin:.1f}%

📦 Stock: **{inventory_quantity}** pcs
"""


def format_ingredient_info(ingredient: Ingredient, inventory_quantity: float) -> str:
    """Format ingredient information"""
    return f"""
🥜 **{ingredient.name}**
Code: `{ingredient.code}`
Category: {ingredient.category.value}

💰 Price: {ingredient.price_per_unit_thb}฿/{ingredient.unit.value}
🏭 Supplier: {ingredient.supplier or 'N/A'}

📦 Stock: **{inventory_quantity:.2f}** {ingredient.unit.value}
"""


def format_inventory_list(products: List[tuple], show_low_stock: bool = False) -> str:
    """Format list of products with inventory"""
    if not products:
        return "❌ No products found"

    response = "📦 **INVENTORY**\n\n"

    for product, inventory in products:
        status = "⚠️" if inventory.quantity < inventory.min_stock_level else "✅"

        if show_low_stock and inventory.quantity >= inventory.min_stock_level:
            continue

        response += f"{status} **{product.sku}**: {inventory.quantity} pcs\n"
        response += f"   {product.name} ({product.retail_price_thb}฿)\n\n"

    return response


def format_sale_receipt(sale: Sale, product: Product) -> str:
    """Format sale receipt"""
    total = sale.quantity * sale.unit_price_thb
    profit = (sale.unit_price_thb - product.cogs_thb) * sale.quantity

    return f"""
✅ **SALE REGISTERED**

🍫 Product: {product.name}
📦 Quantity: {sale.quantity} pcs
💰 Price: {sale.unit_price_thb}฿/pc
💵 Total: {total:.2f}฿

💎 Profit: {profit:.2f}฿
📊 Payment method: {sale.payment_method.value if sale.payment_method else 'N/A'}

🕐 Time: {sale.created_at.strftime('%d.%m.%Y %H:%M')}
"""


def format_low_stock_alert(products: List[tuple]) -> str:
    """Format low stock alert"""
    if not products:
        return "✅ All products sufficiently stocked"

    response = "⚠️ **LOW STOCK ITEMS**\n\n"

    for product, inventory in products:
        shortage = inventory.min_stock_level - inventory.quantity
        response += f"• **{product.sku}** - {product.name}\n"
        response += f"  Stock: {inventory.quantity} / Min: {inventory.min_stock_level}\n"
        response += f"  Need to order: {shortage} pcs\n\n"

    return response


def format_report_summary(period: str, stats: dict) -> str:
    """Format sales report summary"""
    return f"""
📊 **REPORT FOR {period.upper()}**

💰 Revenue: {stats.get('revenue', 0):.2f}฿
💎 Profit: {stats.get('profit', 0):.2f}฿
📦 Units sold: {stats.get('units_sold', 0)}
🧾 Number of sales: {stats.get('sales_count', 0)}

📈 Average sale: {stats.get('avg_sale', 0):.2f}฿
🔝 Top product: {stats.get('top_product', 'N/A')}
"""
