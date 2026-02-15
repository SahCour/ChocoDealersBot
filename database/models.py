from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .db import Base

# --- ENUMS ---
class IngredientType(str, enum.Enum):
    RAW = "raw"
    PACKAGING = "packaging"

class UnitType(str, enum.Enum):
    GRAMS = "g"
    PCS = "pcs"
    KG = "kg"

class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(Enum(IngredientType), default=IngredientType.RAW)
    current_stock = Column(Float, default=0.0)
    unit = Column(Enum(UnitType), default=UnitType.GRAMS)
    price_per_unit = Column(Float, default=0.0)
    supplier = Column(String, nullable=True)
    recipe_items = relationship("RecipeItem", back_populates="ingredient")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    sku = Column(String, unique=True, nullable=True)
    square_id = Column(String, unique=True, nullable=True)
    price = Column(Float, default=0.0)
    recipe_items = relationship("RecipeItem", back_populates="product")

class RecipeItem(Base):
    __tablename__ = "recipe_items"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    amount = Column(Float, nullable=False)
    product = relationship("Product", back_populates="recipe_items")
    ingredient = relationship("Ingredient", back_populates="recipe_items")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String)
    details = Column(Text)
    staff_name = Column(String)
    is_alert = Column(Boolean, default=False)
