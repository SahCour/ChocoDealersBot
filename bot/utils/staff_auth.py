"""
Staff Authentication Utilities for Inventory Management

Handles dual authentication modes:
- Mode A: Individual Telegram accounts (automatic user_id and username)
- Mode B: Shared Telegram account (manual staff name selection via buttons)

Current configuration: MODE A (Individual accounts)

Administrators:
- Sah (ID: 7699749902) - Admin, shop owner
- Ксюша (ID: 47361914) - Admin, partner

Mode B staff names (if needed for shared tablet):
- Thei, Nu, Choco
"""

from typing import Optional, Dict, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ============================================
# STAFF CONFIGURATION
# ============================================

# Known individual staff Telegram user IDs (Mode A)
# Format: {telegram_id: display_name}
INDIVIDUAL_STAFF_ACCOUNTS: Dict[int, str] = {
    7699749902: "Sah",      # Admin, shop owner
    47361914: "Ксюша",     # Admin, partner
    # Add more staff members here when they join:
    # 123456789: "Name",
}

# Admin Telegram user IDs
ADMIN_USER_IDS: List[int] = [
    7699749902,  # Sah (shop owner)
    47361914,    # Ксюша (partner)
    # Add more admins here if needed:
    # 123456789,  # Another admin
]

# Staff name options for Mode B (shared account)
STAFF_NAMES = ["Thei", "Nu", "Choco"]


# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================

def is_individual_staff_account(telegram_user_id: int) -> bool:
    """
    Check if user has an individual staff account (Mode A).

    Args:
        telegram_user_id: Telegram user ID from update.effective_user.id

    Returns:
        True if user has individual account, False otherwise
    """
    return telegram_user_id in INDIVIDUAL_STAFF_ACCOUNTS


def is_admin(telegram_user_id: int) -> bool:
    """
    Check if user is an admin.

    Args:
        telegram_user_id: Telegram user ID

    Returns:
        True if user is admin, False otherwise
    """
    return telegram_user_id in ADMIN_USER_IDS


def get_staff_name_from_telegram(telegram_user_id: int, username: Optional[str] = None) -> Optional[str]:
    """
    Get staff display name for individual account (Mode A).

    Args:
        telegram_user_id: Telegram user ID
        username: Telegram @username (fallback)

    Returns:
        Staff name or None if not found
    """
    if telegram_user_id in INDIVIDUAL_STAFF_ACCOUNTS:
        return INDIVIDUAL_STAFF_ACCOUNTS[telegram_user_id]

    # Fallback to @username if available
    if username:
        return f"@{username}"

    return None


def create_staff_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard with staff name selection buttons (Mode B).

    Returns:
        InlineKeyboardMarkup with [Thei] [Nu] [Choco] buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("👤 Thei", callback_data="staff_select:Thei"),
            InlineKeyboardButton("👤 Nu", callback_data="staff_select:Nu"),
            InlineKeyboardButton("👤 Choco", callback_data="staff_select:Choco"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def request_staff_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: str = "👤 **Please select your name:**"
) -> None:
    """
    Request staff to select their name via inline buttons (Mode B).

    Args:
        update: Telegram update object
        context: Telegram context
        message: Custom message to display
    """
    keyboard = create_staff_selection_keyboard()

    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def get_user_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> Dict[str, any]:
    """
    Get comprehensive user information for transaction logging.

    This function handles BOTH authentication modes:
    - Mode A: Automatic from Telegram API
    - Mode B: From staff selection (stored in context.user_data)

    Args:
        update: Telegram update object
        context: Telegram context

    Returns:
        Dict with:
            - telegram_user_id: int (Telegram user ID)
            - user_name: str (display name)
            - is_admin: bool
            - auth_mode: str ("individual" or "shared")
    """
    telegram_user_id = update.effective_user.id
    telegram_username = update.effective_user.username

    # Check if individual staff account (Mode A)
    if is_individual_staff_account(telegram_user_id):
        user_name = get_staff_name_from_telegram(telegram_user_id, telegram_username)
        return {
            "telegram_user_id": telegram_user_id,
            "user_name": user_name,
            "is_admin": is_admin(telegram_user_id),
            "auth_mode": "individual"
        }

    # Check if admin
    if is_admin(telegram_user_id):
        user_name = telegram_username or f"Admin_{telegram_user_id}"
        return {
            "telegram_user_id": telegram_user_id,
            "user_name": user_name,
            "is_admin": True,
            "auth_mode": "individual"
        }

    # Mode B: Check if staff name already selected (stored in context)
    selected_staff_name = context.user_data.get("selected_staff_name")
    if selected_staff_name:
        return {
            "telegram_user_id": telegram_user_id,
            "user_name": selected_staff_name,
            "is_admin": False,
            "auth_mode": "shared"
        }

    # No selection yet - return None to trigger selection prompt
    return None


async def handle_staff_selection_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> Optional[str]:
    """
    Handle callback from staff name selection buttons.

    Args:
        update: Telegram update object (callback query)
        context: Telegram context

    Returns:
        Selected staff name or None
    """
    query = update.callback_query
    await query.answer()

    # Extract staff name from callback data
    # Format: "staff_select:Thei"
    callback_data = query.data
    if callback_data.startswith("staff_select:"):
        staff_name = callback_data.split(":", 1)[1]

        # Store in context for this session
        context.user_data["selected_staff_name"] = staff_name

        # Confirm selection
        await query.edit_message_text(
            f"✅ **Selected:** {staff_name}\n\nYou can now proceed with inventory operations.",
            parse_mode="Markdown"
        )

        return staff_name

    return None


def clear_staff_selection(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Clear staff name selection from context (for logout or session end).

    Args:
        context: Telegram context
    """
    if "selected_staff_name" in context.user_data:
        del context.user_data["selected_staff_name"]


def requires_admin_check(user_info: Dict) -> bool:
    """
    Check if user has admin privileges.

    Args:
        user_info: Dict from get_user_info()

    Returns:
        True if user is admin, False otherwise
    """
    return user_info.get("is_admin", False)


# ============================================
# CATEGORY ACCESS CONTROL
# ============================================

def can_access_category(category: str, user_info: Dict) -> bool:
    """
    Check if user can access a specific product category.

    Args:
        category: ProductCategory enum value
        user_info: Dict from get_user_info()

    Returns:
        True if user can access, False otherwise
    """
    # AI_EXPENSES category is admin-only
    if category == "AI_EXPENSES":
        return user_info.get("is_admin", False)

    # All other categories accessible to all staff
    return True


# ============================================
# EXPORT
# ============================================

__all__ = [
    "is_individual_staff_account",
    "is_admin",
    "get_staff_name_from_telegram",
    "create_staff_selection_keyboard",
    "request_staff_selection",
    "get_user_info",
    "handle_staff_selection_callback",
    "clear_staff_selection",
    "requires_admin_check",
    "can_access_category",
    "STAFF_NAMES",
    "ADMIN_USER_IDS",
    "INDIVIDUAL_STAFF_ACCOUNTS",
]
