"""
SQLAlchemy ORM Models for Chocodealers Database
These models match the PostgreSQL schema defined in schema.sql
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Enum as SQLEnum, Text, DECIMAL, BigInteger, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import uuid


Base = declarative_base()


# ============================================
# ENUMS
# ============================================

class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"


class UserStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ProductCategory(str, PyEnum):
    """Product categories for Chocodealers inventory system"""
    OUR_CHOCOLATE = "OUR_CHOCOLATE"  # 🍫 Шоколад (наше производство)
    CHOCOLATE_INGREDIENTS = "CHOCOLATE_INGREDIENTS"  # 🥘 Ингредиенты для шоколада
    CHINESE_TEA = "CHINESE_TEA"  # 🍵 Китайский чай
    BEVERAGES_COFFEE = "BEVERAGES_COFFEE"  # ☕ Напитки/кофе
    SHOP_MERCHANDISE = "SHOP_MERCHANDISE"  # 🛍️ Товары магазина
    HOUSEHOLD_ITEMS = "HOUSEHOLD_ITEMS"  # 🧹 Хозяйственные товары
    CHOCOLATE_PACKAGING = "CHOCOLATE_PACKAGING"  # 📦 Упаковка для шоколада
    OTHER_PACKAGING = "OTHER_PACKAGING"  # 📦 Упаковка для всего остального
    PRINTING_MATERIALS = "PRINTING_MATERIALS"  # 🖨️ Печать
    AI_EXPENSES = "AI_EXPENSES"  # 💻 Расходы на AI [ADMIN ONLY]
    EQUIPMENT_MATERIALS = "EQUIPMENT_MATERIALS"  # ⚙️ Оборудование и сопутствующие материалы


class IngredientCategory(str, PyEnum):
    CACAO_BASE = "CACAO_BASE"
    NUTS_SEEDS = "NUTS_SEEDS"
    DAIRY_ALT = "DAIRY_ALT"
    COFFEE = "COFFEE"
    TEA = "TEA"
    PACKAGING = "PACKAGING"
    SPICES = "SPICES"
    OTHER = "OTHER"


class IngredientUnit(str, PyEnum):
    kg = "kg"  # FIXED: lowercase to match PostgreSQL enum
    L = "L"
    pc = "pc"  # FIXED: lowercase to match PostgreSQL enum
    btl = "btl"  # FIXED: lowercase to match PostgreSQL enum


class SaleSource(str, PyEnum):
    TELEGRAM_BOT = "TELEGRAM_BOT"
    SQUARE_POS = "SQUARE_POS"
    MANUAL = "MANUAL"


class PaymentMethod(str, PyEnum):
    CASH = "CASH"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    CRYPTO = "CRYPTO"
    OTHER = "OTHER"


class ProductionStatus(str, PyEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PurchaseStatus(str, PyEnum):
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class SyncType(str, PyEnum):
    INVENTORY = "INVENTORY"
    SALES = "SALES"
    PRODUCTS = "PRODUCTS"
    FULL = "FULL"


class SyncStatus(str, PyEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"


class ActionType(str, PyEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SALE = "SALE"
    PRODUCTION = "PRODUCTION"
    PURCHASE = "PURCHASE"
    INVENTORY_ADJUST = "INVENTORY_ADJUST"
    SYNC = "SYNC"


class TransactionActionType(str, PyEnum):
    """Transaction types for inventory management"""
    ADD = "ADD"  # Incoming goods (приход)
    CONSUME = "CONSUME"  # Consumption/Sales (расход)
    CORRECTION = "CORRECTION"  # Manual inventory correction


# ============================================
# MODELS
# ============================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STAFF)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    is_admin = Column(Boolean, default=False)  # Admin flag for special permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    sales = relationship("Sale", back_populates="creator")
    productions = relationship("Production", back_populates="creator")
    purchases = relationship("Purchase", back_populates="creator")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role = Column(SQLEnum(UserRole), primary_key=True)
    permissions = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SQLEnum(ProductCategory), nullable=False, index=True)
    weight_g = Column(DECIMAL(8, 2))
    cocoa_percent = Column(String(20))
    retail_price_thb = Column(DECIMAL(10, 2), nullable=False)
    cogs_thb = Column(DECIMAL(10, 2), nullable=False)
    square_item_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    # Inventory management fields
    grammovka = Column(Integer)  # Weight in grams per unit (for chocolate products)
    unit_type = Column(String(50))  # штука, package, etc.
    quantity_per_package = Column(Integer)  # For packaging breakdown (e.g., 1 box = 20 pieces)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    inventory = relationship("InventoryProduct", back_populates="product", uselist=False)
    sales = relationship("Sale", back_populates="product")
    productions = relationship("Production", back_populates="product")
    transaction_logs = relationship("TransactionLog", back_populates="product")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SQLEnum(IngredientCategory), nullable=False)
    price_per_unit_thb = Column(DECIMAL(10, 2), nullable=False)
    unit = Column(SQLEnum(IngredientUnit), nullable=False)
    supplier = Column(String(255))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    inventory = relationship("InventoryIngredient", back_populates="ingredient", uselist=False)
    purchases = relationship("Purchase", back_populates="ingredient")
    production_usages = relationship("ProductionIngredientUsed", back_populates="ingredient")


class InventoryProduct(Base):
    __tablename__ = "inventory_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False, default=0)
    min_stock_level = Column(Integer, default=10)
    max_stock_level = Column(Integer, default=100)
    location = Column(String(255), default="Main Warehouse")
    last_count_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("quantity >= 0", name="positive_quantity"),)

    # Relationships
    product = relationship("Product", back_populates="inventory")


class InventoryIngredient(Base):
    __tablename__ = "inventory_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="CASCADE"))
    quantity_kg = Column(DECIMAL(12, 3), nullable=False, default=0)
    min_stock_level_kg = Column(DECIMAL(12, 3), default=1)
    max_stock_level_kg = Column(DECIMAL(12, 3), default=50)
    location = Column(String(255), default="Main Warehouse")
    expiry_date = Column(Date)
    last_count_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("quantity_kg >= 0", name="positive_quantity_ing"),)

    # Relationships
    ingredient = relationship("Ingredient", back_populates="inventory")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    quantity = Column(Integer, nullable=False)
    unit_price_thb = Column(DECIMAL(10, 2), nullable=False)
    discount_thb = Column(DECIMAL(10, 2), default=0)
    final_price_thb = Column(DECIMAL(10, 2))
    source = Column(SQLEnum(SaleSource), nullable=False, default=SaleSource.TELEGRAM_BOT)
    payment_method = Column(SQLEnum(PaymentMethod))
    square_transaction_id = Column(String(255))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    customer_name = Column(String(255))
    customer_telegram_id = Column(BigInteger)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (CheckConstraint("quantity > 0", name="positive_quantity_sale"),)

    # Relationships
    product = relationship("Product", back_populates="sales")
    creator = relationship("User", back_populates="sales")


class Production(Base):
    __tablename__ = "production"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"))
    batch_number = Column(String(100), unique=True)
    quantity_produced = Column(Integer, nullable=False)
    production_date = Column(Date, nullable=False, server_default=func.current_date())
    status = Column(SQLEnum(ProductionStatus), nullable=False, default=ProductionStatus.PLANNED, index=True)
    cost_materials_thb = Column(DECIMAL(10, 2))
    cost_labor_thb = Column(DECIMAL(10, 2))
    total_cost_thb = Column(DECIMAL(10, 2))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (CheckConstraint("quantity_produced > 0", name="positive_quantity_prod"),)

    # Relationships
    product = relationship("Product", back_populates="productions")
    creator = relationship("User", back_populates="productions")
    ingredients_used = relationship("ProductionIngredientUsed", back_populates="production")


class ProductionIngredientUsed(Base):
    __tablename__ = "production_ingredients_used"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_id = Column(UUID(as_uuid=True), ForeignKey("production.id", ondelete="CASCADE"))
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="RESTRICT"))
    quantity_used_kg = Column(DECIMAL(12, 3), nullable=False)
    cost_thb = Column(DECIMAL(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    production = relationship("Production", back_populates="ingredients_used")
    ingredient = relationship("Ingredient", back_populates="production_usages")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredients.id", ondelete="RESTRICT"))
    quantity_kg = Column(DECIMAL(12, 3), nullable=False)
    unit_price_thb = Column(DECIMAL(10, 2), nullable=False)
    supplier = Column(String(255))
    purchase_date = Column(Date, nullable=False, server_default=func.current_date())
    expected_delivery_date = Column(Date)
    status = Column(SQLEnum(PurchaseStatus), nullable=False, default=PurchaseStatus.ORDERED, index=True)
    invoice_number = Column(String(100))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    received_at = Column(DateTime(timezone=True))

    __table_args__ = (CheckConstraint("quantity_kg > 0", name="positive_quantity_purch"),)

    # Relationships
    ingredient = relationship("Ingredient", back_populates="purchases")
    creator = relationship("User", back_populates="purchases")


class SquareSyncLog(Base):
    __tablename__ = "square_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_type = Column(SQLEnum(SyncType), nullable=False)
    sync_status = Column(SQLEnum(SyncStatus), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    records_synced = Column(Integer)
    error_message = Column(Text)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class SheetsSyncLog(Base):
    __tablename__ = "sheets_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sheet_name = Column(String(255), nullable=False)
    sync_direction = Column(String(20))
    sync_status = Column(SQLEnum(SyncStatus), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    records_synced = Column(Integer)
    error_message = Column(Text)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action = Column(SQLEnum(ActionType), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(UUID(as_uuid=True))
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    ip_address = Column(INET)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class TransactionLog(Base):
    """
    Comprehensive transaction logging for inventory management.
    Records all ADD, CONSUME, and CORRECTION actions with full audit trail.
    """
    __tablename__ = "transaction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User information (from Telegram)
    telegram_user_id = Column(BigInteger, nullable=False, index=True)  # Telegram user ID
    user_name = Column(String(255), nullable=False)  # @username or selected name [Thei][Nu][Choco]

    # Product information
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)  # Denormalized for historical record
    category = Column(SQLEnum(ProductCategory), nullable=False)  # Denormalized for historical record

    # Transaction details
    action_type = Column(SQLEnum(TransactionActionType), nullable=False, index=True)

    # Quantity tracking (all quantities stored in GRAMS as base unit)
    quantity_original = Column(Float, nullable=False)  # User input value (e.g., 5.0 for "5 kg")
    quantity_unit = Column(String(50), nullable=False)  # Original unit (e.g., "kg", "pieces", "г")
    quantity_grams = Column(Integer, nullable=False)  # Stored quantity in grams (base unit)
    quantity_display = Column(String(100))  # Human-readable format (e.g., "5000g" or "5kg" or "100 pieces")

    # Additional information
    notes = Column(Text)  # Optional user notes
    source = Column(String(50), default="telegram_bot")  # Source of transaction (telegram_bot, google_sheets, etc.)
    admin_flag = Column(Boolean, default=False)  # Whether this was recorded by admin user

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="transaction_logs")
