-- ============================================
-- CHOCODEALERS INITIAL DATA SEEDING
-- Import all products and ingredients from business data
-- Date: 2026-02-10
-- ============================================

-- ============================================
-- 1. INGREDIENTS (from Business Data MD)
-- ============================================

-- Cacao & Base
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('ING-001', 'Cocoa Butter', 'CACAO_BASE', 900, 'kg', 'Mark Rin', 'Base fat'),
('ING-002', 'Cocoa Powder', 'CACAO_BASE', 550, 'kg', 'Mark Rin', 'Base dry'),
('ING-003', 'Coconut Sugar (Granulated)', 'CACAO_BASE', 110, 'kg', 'Wholesale', 'Main sweetener'),
('ING-004', 'Monk Fruit Mix (Erythritol)', 'CACAO_BASE', 550, 'kg', 'Specialty', 'For Keto/No Sugar'),
('ING-005', 'MCT Oil', 'CACAO_BASE', 660, 'kg', 'Specialty', 'For Bulletproof/Keto'),
('ING-006', 'Coconut Meat (Nam Hom)', 'CACAO_BASE', 159, 'kg', 'Makro/Local', 'Frozen Flesh (Escimo)');

-- Nuts & Seeds
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('ING-010', 'Cashew Nut (Broken)', 'NUTS_SEEDS', 225, 'kg', 'Makro/Aro/Heritage', 'For Milk Base & Truffles'),
('ING-011', 'Almond (Sliced/Petal)', 'NUTS_SEEDS', 225, 'kg', 'Makro/Aro/Heritage', 'For Marzipan (No skin)'),
('ING-012', 'Pecan Nut (Heritage)', 'NUTS_SEEDS', 840, 'kg', 'Heritage', 'Premium (420฿/500g)'),
('ING-013', 'Pistachio (Shelled)', 'NUTS_SEEDS', 1320, 'kg', 'Heritage', 'Premium (330฿/250g)'),
('ING-014', 'Macadamia (Local)', 'NUTS_SEEDS', 900, 'kg', 'Local Thai', 'Thai Local'),
('ING-015', 'Hazelnut', 'NUTS_SEEDS', 600, 'kg', 'Heritage', 'Dynamic price'),
('ING-016', 'Walnut', 'NUTS_SEEDS', 550, 'kg', 'Aro', 'Aro Vacuum'),
('ING-017', 'Pumpkin Seeds', 'NUTS_SEEDS', 310, 'kg', 'Wholesale', '155฿/500g'),
('ING-018', 'Sesame White', 'NUTS_SEEDS', 120, 'kg', 'Wholesale', 'For Halva/Symphony');

-- Dairy Alternatives & Liquids
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('ING-020', 'Almond Milk (137 Degrees)', 'DAIRY_ALT', 130, 'L', '137 Degrees', 'For Coffee/Bar'),
('ING-021', 'Cashew Cream Base (Homemade)', 'DAIRY_ALT', 73, 'kg', 'Homemade', 'Calc: 120g Cashew + 100g Sugar + 300g Water'),
('ING-022', 'Coconut Water (Namhom)', 'DAIRY_ALT', 40, 'L', 'Local', 'Est. price for juice'),
('ING-023', 'Vanilla Extract (Imition)', 'SPICES', 100, 'btl', 'Wholesale', '~100ml Bottle');

-- Coffee Beans
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('ING-030', 'Ben Coffee (Medium)', 'COFFEE', 460, 'kg', 'China Import', 'China Import'),
('ING-031', 'Brazil Roast', 'COFFEE', 800, 'kg', 'Chiang Mai', 'Chiang Mai'),
('ING-032', 'Ethiopia / Thai Premium', 'COFFEE', 1500, 'kg', 'Specialty', 'Specialty / Bulletproof');

-- Chinese Tea
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('ING-040', 'Pu-erh (Old Stock)', 'TEA', 1000, 'kg', 'Direct Sourcing', 'Price will increase'),
('ING-041', 'White Tea', 'TEA', 2000, 'kg', 'Direct Sourcing', ''),
('ING-042', 'Da Hong Pao', 'TEA', 2000, 'kg', 'Direct Sourcing', ''),
('ING-043', 'Gaba Tea (Avg)', 'TEA', 6000, 'kg', 'Direct Sourcing', 'Range 4000-8000฿');

-- Packaging
INSERT INTO ingredients (code, name, category, price_per_unit_thb, unit, supplier, notes) VALUES
('PKG-001', 'Wrapper Small (31g)', 'PACKAGING', 5.5, 'pc', 'Supplier', ''),
('PKG-002', 'Wrapper Large (75g)', 'PACKAGING', 12.5, 'pc', 'Supplier', ''),
('PKG-003', 'Popsicle Stick', 'PACKAGING', 0.5, 'pc', 'Supplier', 'Est.');

-- ============================================
-- 2. PRODUCTS (from Master_SKU_Final.csv)
-- ============================================

-- Ice Cream
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('ICE-001', 'Eskimo Coconut (Vegan)', 'ICE_CREAM', 85, '0%', 160, 20.50, 'Кокос мякоть 159 THB/kg. Ваниль учтена.');

-- Truffles (20-25g)
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('TRF-001', 'Classic Truffle Ball', 'TRUFFLE', 20, '75%', 80, 10.20, 'Кешью дробленый (225 THB)'),
('TRF-002', 'Pistachio Kiss', 'TRUFFLE', 20, '80%', 200, 26.10, 'Фисташка дорогая но цена продажи перекрывает'),
('TRF-003', 'Truffle Pecan Cream', 'TRUFFLE', 20, '75%', 160, 16.50, 'Пекан Heritage (840 THB/kg)'),
('TRF-004', 'Truffle Erotic/Coconut', 'TRUFFLE', 20, '75%', 170, 14.00, 'Кокос/Карамель - выгодные начинки'),
('TRF-005', 'Macadamia Flower', 'TRUFFLE', 25, '80%', 220, 28.50, 'Сложная сборка: Макадамия+Фисташка+Матча');

-- Bars Small (31g)
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('BAR-S-01', 'Classic Bar 31g (Milky/Dark)', 'BAR_SMALL', 31, '65-100%', 160, 26.20, 'Цена Shop (минимум)'),
('BAR-S-02', 'Flavor Bar 31g (Mint/Orange/Love)', 'BAR_SMALL', 31, '75%', 200, 27.00, 'Высокая маржа (масла дешевые на порцию)'),
('BAR-S-03', 'Keto/No Sugar Bar 31g', 'BAR_SMALL', 31, '90%', 220, 29.45, 'Премиум (Monk fruit)');

-- Bars Large (75g)
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('BAR-L-01', 'Classic Bar 75g (Milky/Dark)', 'BAR_LARGE', 75, '65-100%', 280, 62.58, 'Базовая позиция'),
('BAR-L-02', 'Flavor Bar 75g (Mint/Orange/Love)', 'BAR_LARGE', 75, '75%', 320, 64.00, 'Лидер по прибыли в батах'),
('BAR-L-03', 'Keto/No Sugar Bar 75g', 'BAR_LARGE', 75, '90%', 340, 70.44, 'Премиум (Monk fruit)');

-- Bean-to-Bar
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('BAR-BTB-01', 'Bean-to-Bar Origin 30g', 'BEAN_TO_BAR', 30, '90%', 260, 28.67, 'Самая высокая ценность бренда');

-- Symphony
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('SYM-001', 'Symphony Classic (Fruits & Seeds)', 'SYMPHONY', 50, '90%', 250, 36.50, 'Весовой товар (цена за 50г)'),
('SYM-002', 'Symphony Elite FRUIT (No Sugar)', 'SYMPHONY', 40, '100%', 300, 38.00, 'Только 5 фруктов + 100% шоколад'),
('SYM-003', 'Symphony Elite NUTS (No Sugar)', 'SYMPHONY', 40, '100%', 300, 42.50, 'Дорогие орехи (Пекан/Фисташка/Макадамия)');

-- Desserts
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('DES-001', 'Dessert (Banana)', 'DESSERT', 60, '100%', 160, 24.10, 'Банан + Крем + Шоколад');

-- Halva
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('HAL-001', 'Halva Pecan', 'HALVA', 25, '80%', 130, 17.80, 'Самая дорогая халва по сырью'),
('HAL-002', 'Halva Hazelnut/Walnut', 'HALVA', 25, '80%', 130, 14.20, 'Фундук/Грецкий (~550 THB)');

-- Bonbons
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('BON-001', 'Marzipan Ball', 'BONBON', 20, '80%', 100, 10.80, 'Миндаль лепестки (225 THB)'),
('BON-002', 'Chocolate Bonbons (Molded)', 'BONBON', 12, '75%', 50, 6.50, 'Корпусная конфета');

-- Other
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('OTH-001', 'Tropical Fruit Mix Roll', 'OTHER', 50, '100%', 250, 32.00, 'Сушеные фрукты в шоколаде'),
('OTH-002', 'Fruits in 100% Chocolate', 'OTHER', 50, '100%', 200, 28.00, 'Манго/Ананас/Банан (весовое)');

-- Sets
INSERT INTO products (sku, name, category, weight_g, cocoa_percent, retail_price_thb, cogs_thb, notes) VALUES
('SET-001', 'Halva Set (3 pcs)', 'SET', 75, '80%', 390, 46.20, 'Набор из 3 видов'),
('SET-002', 'Sample Box', 'SET', 120, 'Mix', 350, 65.00, 'Промо-набор (Symphony+Marzipan+Truffle+Bars)');

-- ============================================
-- 3. INITIALIZE INVENTORY (Zero Stock)
-- ============================================

-- Initialize product inventory (all products start with 0 stock)
INSERT INTO inventory_products (product_id, quantity, min_stock_level, max_stock_level)
SELECT id, 0, 10, 100 FROM products;

-- Initialize ingredient inventory (all ingredients start with 0 stock)
INSERT INTO inventory_ingredients (ingredient_id, quantity_kg, min_stock_level_kg, max_stock_level_kg)
SELECT id, 0, 1, 50 FROM ingredients;

-- Update specific inventory levels if you have initial stock
-- UPDATE inventory_products SET quantity = 50 WHERE product_id = (SELECT id FROM products WHERE sku = 'BAR-S-01');

-- ============================================
-- 4. CREATE ADMIN USER (UPDATE WITH YOUR TELEGRAM ID!)
-- ============================================

-- IMPORTANT: Replace 123456789 with your actual Telegram ID
-- To find your Telegram ID, message @userinfobot on Telegram

-- INSERT INTO users (telegram_id, username, first_name, role)
-- VALUES (123456789, 'your_username', 'Your Name', 'ADMIN');

-- Example: Add 5 users
-- INSERT INTO users (telegram_id, username, first_name, role) VALUES
-- (111111111, 'admin_user', 'Admin', 'ADMIN'),
-- (222222222, 'manager1', 'Manager One', 'MANAGER'),
-- (333333333, 'manager2', 'Manager Two', 'MANAGER'),
-- (444444444, 'staff1', 'Staff Member 1', 'STAFF'),
-- (555555555, 'staff2', 'Staff Member 2', 'STAFF');

COMMENT ON TABLE products IS 'All SKU data loaded from Master_SKU_Final.csv';
COMMENT ON TABLE ingredients IS 'All ingredient data loaded from Chocodealers_Business_Data.md';
