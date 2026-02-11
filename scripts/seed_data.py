"""
Seed database with initial data for Chocodealers Bot
Run this once after migration to populate the database
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import AsyncSessionLocal
from database.models import (
    User, UserRole, UserStatus,
    Product, ProductCategory,
    Ingredient, IngredientCategory, IngredientUnit,
    InventoryProduct, InventoryIngredient
)
from sqlalchemy import select


async def seed_database():
    """Add initial data to database"""
    async with AsyncSessionLocal() as session:
        try:
            print("🌱 Starting database seeding...")

            # Check if data already exists
            result = await session.execute(select(User))
            if result.scalars().first():
                print("⚠️  Database already has data. Skipping seeding.")
                return

            # ====================================
            # 1. CREATE ADMIN USERS (Both Owners)
            # ====================================
            admin_sah = User(
                telegram_id=7699749902,  # Sah's Telegram ID
                username="Sah",
                first_name="Sah",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE
            )
            session.add(admin_sah)

            admin_ksenia = User(
                telegram_id=47361914,  # Ksenia's Telegram ID
                username="kseniia_kisa",
                first_name="Ksenia",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE
            )
            session.add(admin_ksenia)
            print("✅ Created admin users: Sah & Ksenia")

            # ====================================
            # 2. CREATE SAMPLE PRODUCTS
            # ====================================
            products = [
                # Chocolate Bars
                Product(
                    sku="BAR-S-01",
                    name="Dark Chocolate Bar - Small",
                    category=ProductCategory.CHOCOLATE_BAR,
                    unit_price=120.00,
                    description="70% dark chocolate bar, 50g"
                ),
                Product(
                    sku="BAR-M-01",
                    name="Milk Chocolate Bar - Medium",
                    category=ProductCategory.CHOCOLATE_BAR,
                    unit_price=150.00,
                    description="Creamy milk chocolate bar, 100g"
                ),
                Product(
                    sku="BAR-L-01",
                    name="Dark Chocolate Bar - Large",
                    category=ProductCategory.CHOCOLATE_BAR,
                    unit_price=250.00,
                    description="Premium 85% dark chocolate bar, 200g"
                ),
                # Truffles
                Product(
                    sku="TRF-001",
                    name="Classic Truffle",
                    category=ProductCategory.TRUFFLE,
                    unit_price=35.00,
                    description="Hand-rolled dark chocolate truffle"
                ),
                Product(
                    sku="TRF-002",
                    name="Hazelnut Truffle",
                    category=ProductCategory.TRUFFLE,
                    unit_price=40.00,
                    description="Dark chocolate truffle with hazelnut center"
                ),
                Product(
                    sku="TRF-003",
                    name="Raspberry Truffle",
                    category=ProductCategory.TRUFFLE,
                    unit_price=45.00,
                    description="White chocolate truffle with raspberry filling"
                ),
            ]

            for product in products:
                session.add(product)
            print(f"✅ Created {len(products)} sample products")

            # ====================================
            # 3. CREATE SAMPLE INGREDIENTS
            # ====================================
            ingredients = [
                # Chocolate & Cocoa
                Ingredient(
                    code="ING-001",
                    name="Dark Chocolate (70%)",
                    category=IngredientCategory.CHOCOLATE,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=450.00,
                    supplier="Premium Cacao Co."
                ),
                Ingredient(
                    code="ING-002",
                    name="Milk Chocolate",
                    category=IngredientCategory.CHOCOLATE,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=350.00,
                    supplier="Premium Cacao Co."
                ),
                Ingredient(
                    code="ING-003",
                    name="Cocoa Powder",
                    category=IngredientCategory.CHOCOLATE,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=280.00,
                    supplier="Cocoa Suppliers Ltd."
                ),
                # Dairy
                Ingredient(
                    code="ING-011",
                    name="Heavy Cream",
                    category=IngredientCategory.DAIRY,
                    unit=IngredientUnit.LITER,
                    unit_cost=85.00,
                    supplier="Fresh Dairy"
                ),
                Ingredient(
                    code="ING-012",
                    name="Butter (Unsalted)",
                    category=IngredientCategory.DAIRY,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=180.00,
                    supplier="Fresh Dairy"
                ),
                # Sweeteners
                Ingredient(
                    code="ING-021",
                    name="Cane Sugar",
                    category=IngredientCategory.SWEETENER,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=35.00,
                    supplier="Sugar Mills Co."
                ),
                Ingredient(
                    code="ING-022",
                    name="Honey",
                    category=IngredientCategory.SWEETENER,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=220.00,
                    supplier="Local Honey Farm"
                ),
                # Nuts & Flavors
                Ingredient(
                    code="ING-031",
                    name="Hazelnuts (Roasted)",
                    category=IngredientCategory.NUT,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=420.00,
                    supplier="Nut Importers Inc."
                ),
                Ingredient(
                    code="ING-032",
                    name="Vanilla Extract",
                    category=IngredientCategory.FLAVORING,
                    unit=IngredientUnit.LITER,
                    unit_cost=950.00,
                    supplier="Flavor House"
                ),
                Ingredient(
                    code="ING-033",
                    name="Raspberry Puree",
                    category=IngredientCategory.FRUIT,
                    unit=IngredientUnit.KILOGRAM,
                    unit_cost=180.00,
                    supplier="Fruit Suppliers"
                ),
            ]

            for ingredient in ingredients:
                session.add(ingredient)
            print(f"✅ Created {len(ingredients)} sample ingredients")

            # ====================================
            # 4. CREATE INITIAL INVENTORY (EMPTY)
            # ====================================
            # Create inventory records with 0 quantity for all products
            for product in products:
                inventory_product = InventoryProduct(
                    sku=product.sku,
                    quantity_in_stock=0
                )
                session.add(inventory_product)

            # Create inventory records with 0 quantity for all ingredients
            for ingredient in ingredients:
                inventory_ingredient = InventoryIngredient(
                    ingredient_code=ingredient.code,
                    quantity_in_stock=0.0
                )
                session.add(inventory_ingredient)

            print("✅ Created empty inventory records")

            # Commit all changes
            await session.commit()
            print("\n🎉 Database seeding completed successfully!")
            print(f"   - {len(products)} products")
            print(f"   - {len(ingredients)} ingredients")
            print("   - 2 admin users (Sah & Ksenia)")
            print("\n💡 You can now use the bot to add stock and start selling!")

        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("🌱 CHOCODEALERS BOT - DATABASE SEEDING")
    print("=" * 60)
    asyncio.run(seed_database())
