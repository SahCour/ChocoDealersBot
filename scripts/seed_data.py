"""
Seed database with initial data for Chocodealers Bot
Full product and ingredient catalog from seed_data.sql
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
            # 1. CREATE ADMIN USERS
            # ====================================
            admin_sah = User(
                telegram_id=7699749902,
                username="Sah",
                first_name="Sah",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_admin=True
            )
            session.add(admin_sah)

            admin_ksenia = User(
                telegram_id=47361914,
                username="kseniia_kisa",
                first_name="Ksenia",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_admin=True
            )
            session.add(admin_ksenia)
            print("✅ Created admin users: Sah & Ksenia")

            await session.flush()

            # ====================================
            # 2. CREATE INGREDIENTS (from seed_data.sql)
            # ====================================
            ingredients = [
                # === Cacao & Base ===
                Ingredient(
                    code='ING-001', name='Cocoa Butter', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=900, supplier='Mark Rin', notes='Base fat'
                ),
                Ingredient(
                    code='ING-002', name='Cocoa Powder', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=550, supplier='Mark Rin', notes='Base dry'
                ),
                Ingredient(
                    code='ING-003', name='Coconut Sugar (Granulated)', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=110, supplier='Wholesale', notes='Main sweetener'
                ),
                Ingredient(
                    code='ING-004', name='Monk Fruit Mix (Erythritol)', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=550, supplier='Specialty', notes='For Keto/No Sugar'
                ),
                Ingredient(
                    code='ING-005', name='MCT Oil', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=660, supplier='Specialty', notes='For Bulletproof/Keto'
                ),
                Ingredient(
                    code='ING-006', name='Coconut Meat (Nam Hom)', category=IngredientCategory.CACAO_BASE,
                    unit=IngredientUnit.kg, price_per_unit_thb=159, supplier='Makro/Local', notes='Frozen Flesh (Escimo)'
                ),

                # === Nuts & Seeds ===
                Ingredient(
                    code='ING-010', name='Cashew Nut (Broken)', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=225, supplier='Makro/Aro/Heritage', notes='For Milk Base & Truffles'
                ),
                Ingredient(
                    code='ING-011', name='Almond (Sliced/Petal)', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=225, supplier='Makro/Aro/Heritage', notes='For Marzipan (No skin)'
                ),
                Ingredient(
                    code='ING-012', name='Pecan Nut (Heritage)', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=840, supplier='Heritage', notes='Premium (420฿/500g)'
                ),
                Ingredient(
                    code='ING-013', name='Pistachio (Shelled)', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=1320, supplier='Heritage', notes='Premium (330฿/250g)'
                ),
                Ingredient(
                    code='ING-014', name='Macadamia (Local)', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=900, supplier='Local Thai', notes='Thai Local'
                ),
                Ingredient(
                    code='ING-015', name='Hazelnut', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=600, supplier='Heritage', notes='Dynamic price'
                ),
                Ingredient(
                    code='ING-016', name='Walnut', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=550, supplier='Aro', notes='Aro Vacuum'
                ),
                Ingredient(
                    code='ING-017', name='Pumpkin Seeds', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=310, supplier='Wholesale', notes='155฿/500g'
                ),
                Ingredient(
                    code='ING-018', name='Sesame White', category=IngredientCategory.NUTS_SEEDS,
                    unit=IngredientUnit.kg, price_per_unit_thb=120, supplier='Wholesale', notes='For Halva/Symphony'
                ),

                # === Dairy Alternatives & Liquids ===
                Ingredient(
                    code='ING-020', name='Almond Milk (137 Degrees)', category=IngredientCategory.DAIRY_ALT,
                    unit=IngredientUnit.L, price_per_unit_thb=130, supplier='137 Degrees', notes='For Coffee/Bar'
                ),
                Ingredient(
                    code='ING-021', name='Cashew Cream Base (Homemade)', category=IngredientCategory.DAIRY_ALT,
                    unit=IngredientUnit.kg, price_per_unit_thb=73, supplier='Homemade',
                    notes='Calc: 120g Cashew + 100g Sugar + 300g Water'
                ),
                Ingredient(
                    code='ING-022', name='Coconut Water (Namhom)', category=IngredientCategory.DAIRY_ALT,
                    unit=IngredientUnit.L, price_per_unit_thb=40, supplier='Local', notes='Est. price for juice'
                ),

                # === Spices ===
                Ingredient(
                    code='ING-023', name='Vanilla Extract (Imition)', category=IngredientCategory.SPICES,
                    unit=IngredientUnit.btl, price_per_unit_thb=100, supplier='Wholesale', notes='~100ml Bottle'
                ),

                # === Coffee Beans ===
                Ingredient(
                    code='ING-030', name='Ben Coffee (Medium)', category=IngredientCategory.COFFEE,
                    unit=IngredientUnit.kg, price_per_unit_thb=460, supplier='China Import', notes='China Import'
                ),
                Ingredient(
                    code='ING-031', name='Brazil Roast', category=IngredientCategory.COFFEE,
                    unit=IngredientUnit.kg, price_per_unit_thb=800, supplier='Chiang Mai', notes='Chiang Mai'
                ),
                Ingredient(
                    code='ING-032', name='Ethiopia / Thai Premium', category=IngredientCategory.COFFEE,
                    unit=IngredientUnit.kg, price_per_unit_thb=1500, supplier='Specialty', notes='Specialty / Bulletproof'
                ),

                # === Chinese Tea ===
                Ingredient(
                    code='ING-040', name='Pu-erh (Old Stock)', category=IngredientCategory.TEA,
                    unit=IngredientUnit.kg, price_per_unit_thb=1000, supplier='Direct Sourcing', notes='Price will increase'
                ),
                Ingredient(
                    code='ING-041', name='White Tea', category=IngredientCategory.TEA,
                    unit=IngredientUnit.kg, price_per_unit_thb=2000, supplier='Direct Sourcing', notes=''
                ),
                Ingredient(
                    code='ING-042', name='Da Hong Pao', category=IngredientCategory.TEA,
                    unit=IngredientUnit.kg, price_per_unit_thb=2000, supplier='Direct Sourcing', notes=''
                ),
                Ingredient(
                    code='ING-043', name='Gaba Tea (Avg)', category=IngredientCategory.TEA,
                    unit=IngredientUnit.kg, price_per_unit_thb=6000, supplier='Direct Sourcing', notes='Range 4000-8000฿'
                ),

                # === Packaging ===
                Ingredient(
                    code='PKG-001', name='Wrapper Small (31g)', category=IngredientCategory.PACKAGING,
                    unit=IngredientUnit.pc, price_per_unit_thb=5.5, supplier='Supplier', notes=''
                ),
                Ingredient(
                    code='PKG-002', name='Wrapper Large (75g)', category=IngredientCategory.PACKAGING,
                    unit=IngredientUnit.pc, price_per_unit_thb=12.5, supplier='Supplier', notes=''
                ),
                Ingredient(
                    code='PKG-003', name='Popsicle Stick', category=IngredientCategory.PACKAGING,
                    unit=IngredientUnit.pc, price_per_unit_thb=0.5, supplier='Supplier', notes='Est.'
                ),
            ]

            for ing in ingredients:
                session.add(ing)
            print(f"✅ Created {len(ingredients)} ingredients")

            await session.flush()

            # ====================================
            # 3. CREATE PRODUCTS (from seed_data.sql)
            # All products are OUR_CHOCOLATE category
            # ====================================
            products = [
                # === Ice Cream ===
                Product(
                    sku='ICE-001', name='Eskimo Coconut (Vegan)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=85, cocoa_percent='0%', retail_price_thb=160, cogs_thb=20.50,
                    notes='Кокос мякоть 159 THB/kg. Ваниль учтена.',
                    grammovka=85, unit_type='штука', is_active=True
                ),

                # === Truffles (20-25g) ===
                Product(
                    sku='TRF-001', name='Classic Truffle Ball', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20, cocoa_percent='75%', retail_price_thb=80, cogs_thb=10.20,
                    notes='Кешью дробленый (225 THB)',
                    grammovka=20, unit_type='штука', is_active=True
                ),
                Product(
                    sku='TRF-002', name='Pistachio Kiss', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20, cocoa_percent='80%', retail_price_thb=200, cogs_thb=26.10,
                    notes='Фисташка дорогая но цена продажи перекрывает',
                    grammovka=20, unit_type='штука', is_active=True
                ),
                Product(
                    sku='TRF-003', name='Truffle Pecan Cream', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20, cocoa_percent='75%', retail_price_thb=160, cogs_thb=16.50,
                    notes='Пекан Heritage (840 THB/kg)',
                    grammovka=20, unit_type='штука', is_active=True
                ),
                Product(
                    sku='TRF-004', name='Truffle Erotic/Coconut', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20, cocoa_percent='75%', retail_price_thb=170, cogs_thb=14.00,
                    notes='Кокос/Карамель - выгодные начинки',
                    grammovka=20, unit_type='штука', is_active=True
                ),
                Product(
                    sku='TRF-005', name='Macadamia Flower', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=25, cocoa_percent='80%', retail_price_thb=220, cogs_thb=28.50,
                    notes='Сложная сборка: Макадамия+Фисташка+Матча',
                    grammovka=25, unit_type='штука', is_active=True
                ),

                # === Bars Small (31g) ===
                Product(
                    sku='BAR-S-01', name='Classic Bar 31g (Milky/Dark)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=31, cocoa_percent='65-100%', retail_price_thb=160, cogs_thb=26.20,
                    notes='Цена Shop (минимум)',
                    grammovka=31, unit_type='штука', is_active=True
                ),
                Product(
                    sku='BAR-S-02', name='Flavor Bar 31g (Mint/Orange/Love)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=31, cocoa_percent='75%', retail_price_thb=200, cogs_thb=27.00,
                    notes='Высокая маржа (масла дешевые на порцию)',
                    grammovka=31, unit_type='штука', is_active=True
                ),
                Product(
                    sku='BAR-S-03', name='Keto/No Sugar Bar 31g', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=31, cocoa_percent='90%', retail_price_thb=220, cogs_thb=29.45,
                    notes='Премиум (Monk fruit)',
                    grammovka=31, unit_type='штука', is_active=True
                ),

                # === Bars Large (75g) ===
                Product(
                    sku='BAR-L-01', name='Classic Bar 75g (Milky/Dark)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=75, cocoa_percent='65-100%', retail_price_thb=280, cogs_thb=62.58,
                    notes='Базовая позиция',
                    grammovka=75, unit_type='штука', is_active=True
                ),
                Product(
                    sku='BAR-L-02', name='Flavor Bar 75g (Mint/Orange/Love)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=75, cocoa_percent='75%', retail_price_thb=320, cogs_thb=64.00,
                    notes='Лидер по прибыли в батах',
                    grammovka=75, unit_type='штука', is_active=True
                ),
                Product(
                    sku='BAR-L-03', name='Keto/No Sugar Bar 75g', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=75, cocoa_percent='90%', retail_price_thb=340, cogs_thb=70.44,
                    notes='Премиум (Monk fruit)',
                    grammovka=75, unit_type='штука', is_active=True
                ),

                # === Bean-to-Bar ===
                Product(
                    sku='BAR-BTB-01', name='Bean-to-Bar Origin 30g', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=30, cocoa_percent='90%', retail_price_thb=260, cogs_thb=28.67,
                    notes='Самая высокая ценность бренда',
                    grammovka=30, unit_type='штука', is_active=True
                ),

                # === Symphony ===
                Product(
                    sku='SYM-001', name='Symphony Classic (Fruits & Seeds)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=50, cocoa_percent='90%', retail_price_thb=250, cogs_thb=36.50,
                    notes='Весовой товар (цена за 50г)',
                    grammovka=50, unit_type='штука', is_active=True
                ),
                Product(
                    sku='SYM-002', name='Symphony Elite FRUIT (No Sugar)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=40, cocoa_percent='100%', retail_price_thb=300, cogs_thb=38.00,
                    notes='Только 5 фруктов + 100% шоколад',
                    grammovka=40, unit_type='штука', is_active=True
                ),
                Product(
                    sku='SYM-003', name='Symphony Elite NUTS (No Sugar)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=40, cocoa_percent='100%', retail_price_thb=300, cogs_thb=42.50,
                    notes='Дорогие орехи (Пекан/Фисташка/Макадамия)',
                    grammovka=40, unit_type='штука', is_active=True
                ),

                # === Desserts ===
                Product(
                    sku='DES-001', name='Dessert (Banana)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=60, cocoa_percent='100%', retail_price_thb=160, cogs_thb=24.10,
                    notes='Банан + Крем + Шоколад',
                    grammovka=60, unit_type='штука', is_active=True
                ),

                # === Halva ===
                Product(
                    sku='HAL-001', name='Halva Pecan', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=25, cocoa_percent='80%', retail_price_thb=130, cogs_thb=17.80,
                    notes='Самая дорогая халва по сырью',
                    grammovka=25, unit_type='штука', is_active=True
                ),
                Product(
                    sku='HAL-002', name='Halva Hazelnut/Walnut', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=25, cocoa_percent='80%', retail_price_thb=130, cogs_thb=14.20,
                    notes='Фундук/Грецкий (~550 THB)',
                    grammovka=25, unit_type='штука', is_active=True
                ),

                # === Bonbons ===
                Product(
                    sku='BON-001', name='Marzipan Ball', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=20, cocoa_percent='80%', retail_price_thb=100, cogs_thb=10.80,
                    notes='Миндаль лепестки (225 THB)',
                    grammovka=20, unit_type='штука', is_active=True
                ),
                Product(
                    sku='BON-002', name='Chocolate Bonbons (Molded)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=12, cocoa_percent='75%', retail_price_thb=50, cogs_thb=6.50,
                    notes='Корпусная конфета',
                    grammovka=12, unit_type='штука', is_active=True
                ),

                # === Other ===
                Product(
                    sku='OTH-001', name='Tropical Fruit Mix Roll', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=50, cocoa_percent='100%', retail_price_thb=250, cogs_thb=32.00,
                    notes='Сушеные фрукты в шоколаде',
                    grammovka=50, unit_type='штука', is_active=True
                ),
                Product(
                    sku='OTH-002', name='Fruits in 100% Chocolate', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=50, cocoa_percent='100%', retail_price_thb=200, cogs_thb=28.00,
                    notes='Манго/Ананас/Банан (весовое)',
                    grammovka=50, unit_type='штука', is_active=True
                ),

                # === Sets ===
                Product(
                    sku='SET-001', name='Halva Set (3 pcs)', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=75, cocoa_percent='80%', retail_price_thb=390, cogs_thb=46.20,
                    notes='Набор из 3 видов',
                    grammovka=75, unit_type='набор', is_active=True
                ),
                Product(
                    sku='SET-002', name='Sample Box', category=ProductCategory.OUR_CHOCOLATE,
                    weight_g=120, cocoa_percent='Mix', retail_price_thb=350, cogs_thb=65.00,
                    notes='Промо-набор (Symphony+Marzipan+Truffle+Bars)',
                    grammovka=120, unit_type='набор', is_active=True
                ),
            ]

            for prod in products:
                session.add(prod)
            print(f"✅ Created {len(products)} products")

            await session.flush()

            # ====================================
            # 4. CREATE INITIAL INVENTORY (EMPTY)
            # ====================================
            for product in products:
                inventory_product = InventoryProduct(
                    product_id=product.id,
                    quantity=0,
                    min_stock_level=10,
                    max_stock_level=100,
                    location="Main Warehouse"
                )
                session.add(inventory_product)

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
            print("\n" + "=" * 60)
            print("🎉 DATABASE SEEDING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   • {len(products)} products (ice cream, truffles, bars, desserts, halva, sets)")
            print(f"   • {len(ingredients)} ingredients (cacao, nuts, dairy, coffee, tea, packaging)")
            print(f"   • 2 admin users (Sah & Ksenia)")
            print(f"   • {len(products)} product inventory records (empty)")
            print(f"   • {len(ingredients)} ingredient inventory records (empty)")
            print("=" * 60)
            print("💡 Next Steps:")
            print("   1. Use bot to add initial stock quantities")
            print("   2. Start recording sales and production")
            print("   3. Monitor inventory levels")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ ERROR SEEDING DATABASE: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌱 CHOCODEALERS BOT - DATABASE SEEDING")
    print("=" * 60)
    asyncio.run(seed_database())
