from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, Ingredient, RecipeItem, AuditLog
from integrations.square_client import square_client
import logging

logger = logging.getLogger(__name__)


async def get_products_with_recipes(session: AsyncSession):
    """Fetch all products that have recipes defined"""
    result = await session.execute(select(Product))
    return result.scalars().all()


async def process_production(session: AsyncSession, product_id: int, quantity: int, user_name: str):
    """
    1. Deduct ingredients from stock
    2. Update Square inventory (Mock/Real)
    3. Log the event
    """
    # 1. Get Product
    product = await session.get(Product, product_id)
    if not product:
        return {"success": False, "error": "Product not found"}

    # 2. Load recipe items
    result = await session.execute(
        select(RecipeItem).where(RecipeItem.product_id == product_id)
    )
    recipe_items = result.scalars().all()

    if not recipe_items:
        return {"success": False, "error": "No recipe defined for this product"}

    # 3. Deduct Ingredients
    report = []
    for item in recipe_items:
        ingredient = await session.get(Ingredient, item.ingredient_id)
        if ingredient:
            required_amount = item.amount * quantity
            ingredient.current_stock -= required_amount
            report.append(f"- {ingredient.name}: {required_amount:.1f} {ingredient.unit}")

    # 4. Update Square (Add finished goods)
    if product.square_id:
        await square_client.update_inventory(product.square_id, quantity)

    # 5. Audit Log
    log_entry = AuditLog(
        event_type="PRODUCTION",
        staff_name=user_name,
        details=f"Produced {quantity} x {product.name}. Ingredients used: {', '.join(report)}"
    )
    session.add(log_entry)

    await session.commit()

    return {
        "success": True,
        "product_name": product.name,
        "report": "\n".join(report)
    }


async def get_all_ingredients(session: AsyncSession):
    """Fetch all ingredients (Raw + Packaging) ordered by name"""
    result = await session.execute(select(Ingredient).order_by(Ingredient.name))
    return result.scalars().all()


async def process_restock(session: AsyncSession, ingredient_id: int, quantity: float, user_name: str):
    """
    1. Increase ingredient stock
    2. Log the purchase in AuditLog
    """
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        return {"success": False, "error": "Ingredient not found"}

    # Update Stock
    old_stock = ingredient.current_stock
    ingredient.current_stock += quantity

    # Audit Log
    log_entry = AuditLog(
        event_type="RESTOCK",
        staff_name=user_name,
        details=f"Restocked {ingredient.name}. {old_stock} -> {ingredient.current_stock} ({ingredient.unit.value})"
    )
    session.add(log_entry)
    await session.commit()

    return {
        "success": True,
        "name": ingredient.name,
        "new_stock": ingredient.current_stock,
        "unit": ingredient.unit.value
    }
