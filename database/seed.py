import logging
from sqlalchemy import select
from .db import AsyncSessionLocal
from .models import Ingredient, Product, RecipeItem, IngredientType, UnitType

logger = logging.getLogger(__name__)


async def seed_data():
    """Заполняет базу начальными данными (Рецепт Эскимо)"""
    async with AsyncSessionLocal() as db:
        # Проверка дубликатов
        result = await db.execute(select(Product).where(Product.name == "Eskimo Coconut"))
        if result.scalar():
            return

        logger.info("🌱 Seeding database with initial recipe...")

        # 1. Сырье
        coconut = Ingredient(name="Coconut Meat (Nam Hom)", unit=UnitType.GRAMS, current_stock=5000)
        water = Ingredient(name="Coconut Water", unit=UnitType.GRAMS, current_stock=2000)
        sugar = Ingredient(name="Sugar", unit=UnitType.GRAMS, current_stock=5000)
        vanilla = Ingredient(name="Vanilla Extract", unit=UnitType.GRAMS, current_stock=500)
        stick = Ingredient(name="Ice Cream Stick", unit=UnitType.PCS, type=IngredientType.PACKAGING, current_stock=100)

        db.add_all([coconut, water, sugar, vanilla, stick])
        await db.flush()

        # 2. Продукт
        eskimo = Product(name="Eskimo Coconut", price=160.0, square_id="sq_eskimo_mock")
        db.add(eskimo)
        await db.flush()

        # 3. Рецепт (на 1 шт)
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
