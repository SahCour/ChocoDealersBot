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
                status=UserStatus.ACTIVE,
                is_admin=True
            )
            session.add(admin_sah)

            admin_ksenia = User(
                telegram_id=47361914,  # Ksenia's Telegram ID
                username="kseniia_kisa",
                first_name="Ksenia",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_admin=True
            )
            session.add(admin_ksenia)
            print("✅ Created admin users: Sah & Ksenia")

            # Flush to get user IDs for later use
            await session.flush()

            # ====================================
            # 2. CREATE SAMPLE PRODUCTS
            # ====================================
            products = [
                # Chocolate Bars (Our Chocolate)
                Product(
                    sku="BAR-S-01",
                    name="Dark Chocolate Bar - Small",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=50,
                    cocoa_percent="70%",
                    retail_price_thb=120.00,
                    cogs_thb=60.00,
                    is_active=True,
                    notes="70% dark chocolate bar, 50g",
                    grammovka=50,
                    unit_type="штука"
                ),
                Product(
                    sku="BAR-M-01",
                    name="Milk Chocolate Bar - Medium",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=100,
                    cocoa_percent="40%",
                    retail_price_thb=150.00,
                    cogs_thb=75.00,
                    is_active=True,
                    notes="Creamy milk chocolate bar, 100g",
                    grammovka=100,
                    unit_type="штука"
                ),
                Product(
                    sku="BAR-L-01",
                    name="Dark Chocolate Bar - Large",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=200,
                    cocoa_percent="85%",
                    retail_price_thb=250.00,
                    cogs_thb=120.00,
                    is_active=True,
                    notes="Premium 85% dark chocolate bar, 200g",
                    grammovka=200,
                    unit_type="штука"
                ),
                # Truffles (Our Chocolate)
                Product(
                    sku="TRF-001",
                    name="Classic Truffle",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20,
                    cocoa_percent="70%",
                    retail_price_thb=35.00,
                    cogs_thb=18.00,
                    is_active=True,
                    notes="Hand-rolled dark chocolate truffle",
                    grammovka=20,
                    unit_type="штука"
                ),
                Product(
                    sku="TRF-002",
                    name="Hazelnut Truffle",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=22,
                    cocoa_percent="65%",
                    retail_price_thb=40.00,
                    cogs_thb=22.00,
                    is_active=True,
                    notes="Dark chocolate truffle with hazelnut center",
                    grammovka=22,
                    unit_type="штука"
                ),
                Product(
                    sku="TRF-003",
                    name="Raspberry Truffle",
                    category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=22,
                    cocoa_percent="35%",
                    retail_price_thb=45.00,
                    cogs_thb=25.00,
                    is_active=True,
                    notes="White chocolate truffle with raspberry filling",
                    grammovka=22,
                    unit_type="штука"
                ),
            ]

            for product in products:
                session.add(product)
            print(f"✅ Created {len(products)} sample products")

            # Flush to get product IDs
            await session.flush()

            # ====================================
            # 3. CREATE SAMPLE INGREDIENTS
            # ====================================
            ingredients = [
                # Chocolate & Cocoa (CACAO_BASE)
                Ingredient(
                    code="ING-001",
                    name="Dark Chocolate (70%)",
                    category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=450.00,
                    supplier="Premium Cacao Co.",
                    is_active=True
                ),
                Ingredient(
                    code="ING-002",
                    name="Milk Chocolate",
                    category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=350.00,
                    supplier="Premium Cacao Co.",
                    is_active=True
                ),
                Ingredient(
                    code="ING-003",
                    name="Cocoa Powder",
                    category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=280.00,
                    supplier="Cocoa Suppliers Ltd.",
                    is_active=True
                ),
                # Dairy (DAIRY_ALT)
                Ingredient(
                    code="ING-011",
                    name="Heavy Cream",
                    category=IngredientCategory.DAIRY_ALT,
                    unit=IngredientUnit.L,
                    price_per_unit_thb=85.00,
                    supplier="Fresh Dairy",
                    is_active=True
                ),
                Ingredient(
                    code="ING-012",
                    name="Butter (Unsalted)",
                    category=IngredientCategory.DAIRY_ALT,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=180.00,
                    supplier="Fresh Dairy",
                    is_active=True
                ),
                # Sweeteners (OTHER)
                Ingredient(
                    code="ING-021",
                    name="Cane Sugar",
                    category=IngredientCategory.OTHER,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=35.00,
                    supplier="Sugar Mills Co.",
                    is_active=True,
                    notes="Sweetener"
                ),
                Ingredient(
                    code="ING-022",
                    name="Honey",
                    category=IngredientCategory.OTHER,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=220.00,
                    supplier="Local Honey Farm",
                    is_active=True,
                    notes="Natural sweetener"
                ),
                # Nuts (NUTS_SEEDS)
                Ingredient(
                    code="ING-031",
                    name="Hazelnuts (Roasted)",
                    category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=420.00,
                    supplier="Nut Importers Inc.",
                    is_active=True
                ),
                # Flavors & Fruits (OTHER)
                Ingredient(
                    code="ING-032",
                    name="Vanilla Extract",
                    category=IngredientCategory.OTHER,
                    unit=IngredientUnit.L,
                    price_per_unit_thb=950.00,
                    supplier="Flavor House",
                    is_active=True,
                    notes="Flavoring"
                ),
                Ingredient(
                    code="ING-033",
                    name="Raspberry Puree",
                    category=IngredientCategory.OTHER,
                    unit=IngredientUnit.KG,
                    price_per_unit_thb=180.00,
                    supplier="Fruit Suppliers",
                    is_active=True,
                    notes="Fruit filling"
                ),
            ]

            for ingredient in ingredients:
                session.add(ingredient)
            print(f"✅ Created {len(ingredients)} sample ingredients")

            # Flush to get ingredient IDs
            await session.flush()

            # ====================================
            # 4. CREATE INITIAL INVENTORY (EMPTY)
            # ====================================
            # Create inventory records with 0 quantity for all products
            for product in products:
                inventory_product = InventoryProduct(
                    product_id=product.id,
                    quantity=0,
                    min_stock_level=5,
                    max_stock_level=100,
                    location="Main Warehouse"
                )
                session.add(inventory_product)

            # Create inventory records with 0 quantity for all ingredients
            for ingredient in ingredients:
                inventory_ingredient = InventoryIngredient(
                    ingredient_id=ingredient.id,
                    quantity_kg=0.0,
                    min_stock_level_kg=1.0,
                    max_stock_level_kg=50.0,
                    location="Main Warehouse"
                )
                session.add(inventory_ingredient)

            print("✅ Created empty inventory records")

            # Commit all changes
            await session.commit()
            print("\n🎉 Database seeding completed successfully!")
            print(f"   - {len(products)} products (chocolate bars & truffles)")
            print(f"   - {len(ingredients)} ingredients")
            print("   - 2 admin users (Sah & Ksenia)")
            print("   - Empty inventory records for all products & ingredients")
            print("\n💡 You can now use the bot to add stock and start selling!")

        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("🌱 CHOCODEALERS BOT - DATABASE SEEDING")
    print("=" * 60)
    asyncio.run(seed_database())
