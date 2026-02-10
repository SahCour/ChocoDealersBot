"""
Unit Conversion Utilities for Inventory Management

All quantities are stored in GRAMS as the base unit in the database.
This module handles conversion from various input units to grams and back.
"""

from typing import Optional, Tuple, Dict
from decimal import Decimal


# ============================================
# UNIT CONVERSION MAPPINGS
# ============================================

# Weight conversions to grams
WEIGHT_CONVERSIONS: Dict[str, float] = {
    # Grams
    "г": 1.0,
    "грамм": 1.0,
    "граммы": 1.0,
    "граммов": 1.0,
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,

    # Kilograms
    "кг": 1000.0,
    "килограмм": 1000.0,
    "килограммы": 1000.0,
    "килограммов": 1000.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,

    # Milliliters (approximate 1:1 for liquids)
    "мл": 1.0,
    "миллилитр": 1.0,
    "миллилитры": 1.0,
    "миллилитров": 1.0,
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,

    # Liters
    "л": 1000.0,
    "литр": 1000.0,
    "литры": 1000.0,
    "литров": 1000.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
}


# ============================================
# CONVERSION FUNCTIONS
# ============================================

def convert_to_grams(
    value: float,
    unit: str,
    product_info: Optional[Dict] = None
) -> Tuple[int, str]:
    """
    Convert input quantity to grams (base unit for storage).

    Args:
        value: Numeric value from user input
        unit: Unit string (e.g., "kg", "pieces", "г")
        product_info: Optional dict with product details (grammovka, unit_type, etc.)

    Returns:
        Tuple of (grams_as_int, display_string)
        - grams_as_int: Total quantity in grams (for database storage)
        - display_string: Human-readable format (e.g., "5000g (5 pieces)")

    Examples:
        >>> convert_to_grams(5, "kg")
        (5000, "5000g (5kg)")

        >>> convert_to_grams(3, "pieces", {"grammovka": 100})
        (300, "300g (3 pieces)")
    """
    unit_lower = unit.lower().strip()

    # Case 1: Weight-based units (direct conversion)
    if unit_lower in WEIGHT_CONVERSIONS:
        multiplier = WEIGHT_CONVERSIONS[unit_lower]
        grams = int(value * multiplier)

        # Format display string
        if unit_lower in ["кг", "kg", "килограмм", "килограммы", "килограммов", "kilogram", "kilograms"]:
            display = f"{grams}g ({value}kg)"
        elif unit_lower in ["л", "l", "литр", "литры", "литров", "liter", "liters"]:
            display = f"{grams}g ({value}L)"
        else:
            display = f"{grams}g"

        return (grams, display)

    # Case 2: Piece-based units (штуки, pieces) - requires grammovka
    piece_units = ["штука", "штуки", "штук", "шт", "piece", "pieces", "pc", "pcs"]
    if unit_lower in piece_units:
        if product_info and product_info.get("grammovka"):
            grammovka = product_info["grammovka"]
            grams = int(value * grammovka)
            display = f"{grams}g ({int(value)} pieces)"
            return (grams, display)
        else:
            # No grammovka - assume piece-based product, store as units
            # For piece-based products, we store the count directly
            return (int(value), f"{int(value)} pieces")

    # Case 3: Package-based units (коробки, пачки, упаковки)
    package_units = ["коробка", "коробки", "коробок", "box", "boxes"]
    pack_units = ["пачка", "пачки", "пачек", "pack", "packs"]
    package_units_all = package_units + pack_units

    if unit_lower in package_units_all:
        if product_info and product_info.get("quantity_per_package"):
            qty_per_package = product_info["quantity_per_package"]
            total_pieces = int(value * qty_per_package)

            # If product also has grammovka, convert to grams
            if product_info.get("grammovka"):
                grammovka = product_info["grammovka"]
                grams = total_pieces * grammovka
                display = f"{grams}g ({int(value)} packages, {total_pieces} pieces)"
                return (grams, display)
            else:
                # Store as pieces
                display = f"{total_pieces} pieces ({int(value)} packages)"
                return (total_pieces, display)
        else:
            # No package breakdown defined - treat as 1:1
            return (int(value), f"{int(value)} packages")

    # Case 4: Unknown unit - store value as-is and log warning
    # This is a fallback for safety
    print(f"⚠️ WARNING: Unknown unit '{unit}'. Storing value as-is: {value}")
    return (int(value), f"{int(value)} {unit}")


def format_quantity(
    grams: int,
    display_unit: Optional[str] = None,
    product_info: Optional[Dict] = None
) -> str:
    """
    Format grams into human-readable display string.

    Args:
        grams: Quantity in grams (from database)
        display_unit: Preferred display unit (kg, g, pieces, etc.)
        product_info: Optional dict with product details

    Returns:
        Human-readable string (e.g., "5kg", "300g (3 pieces)", "100 pieces")

    Examples:
        >>> format_quantity(5000, "kg")
        "5kg"

        >>> format_quantity(300, "pieces", {"grammovka": 100})
        "300g (3 pieces)"
    """
    # Case 1: Piece-based display with grammovka
    if display_unit in ["pieces", "штуки", "шт"] and product_info and product_info.get("grammovka"):
        grammovka = product_info["grammovka"]
        pieces = grams // grammovka
        return f"{grams}g ({pieces} pieces)"

    # Case 2: Kilogram display
    if display_unit in ["kg", "кг"] or grams >= 1000:
        kg = grams / 1000
        if kg == int(kg):
            return f"{int(kg)}kg"
        else:
            return f"{kg:.2f}kg"

    # Case 3: Default gram display
    return f"{grams}g"


def parse_quantity_input(input_str: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse user input string into (value, unit) tuple.

    Args:
        input_str: User input like "5 kg", "100g", "3 pieces"

    Returns:
        Tuple of (value, unit) or (None, None) if parsing fails

    Examples:
        >>> parse_quantity_input("5 kg")
        (5.0, "kg")

        >>> parse_quantity_input("100г")
        (100.0, "г")

        >>> parse_quantity_input("3 pieces")
        (3.0, "pieces")
    """
    input_str = input_str.strip()

    # Try to split by space
    parts = input_str.split(maxsplit=1)

    if len(parts) == 2:
        # Format: "5 kg"
        try:
            value = float(parts[0])
            unit = parts[1].strip()
            return (value, unit)
        except ValueError:
            return (None, None)

    elif len(parts) == 1:
        # Format: "5kg" or "100g" - need to separate number from unit
        import re
        match = re.match(r'^([\d.]+)\s*([a-zA-Zа-яА-Я]+)$', input_str)
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2)
                return (value, unit)
            except ValueError:
                return (None, None)

    return (None, None)


def get_base_unit_for_category(category: str) -> str:
    """
    Get the base storage unit for a product category.

    Args:
        category: Product category enum value

    Returns:
        Base unit ("grams" or "pieces")
    """
    # Weight-based categories (stored in grams)
    weight_based = [
        "OUR_CHOCOLATE",  # With grammovka conversion
        "CHOCOLATE_INGREDIENTS",
        "CHINESE_TEA",
        "BEVERAGES_COFFEE",
    ]

    # Piece-based categories (stored as units)
    piece_based = [
        "SHOP_MERCHANDISE",
        "HOUSEHOLD_ITEMS",  # Can vary by product
        "CHOCOLATE_PACKAGING",
        "OTHER_PACKAGING",
        "PRINTING_MATERIALS",
        "AI_EXPENSES",
        "EQUIPMENT_MATERIALS",
    ]

    if category in weight_based:
        return "grams"
    elif category in piece_based:
        return "pieces"
    else:
        # Default to grams
        return "grams"


# ============================================
# EXPORT
# ============================================

__all__ = [
    "convert_to_grams",
    "format_quantity",
    "parse_quantity_input",
    "get_base_unit_for_category",
    "WEIGHT_CONVERSIONS",
]
