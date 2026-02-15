from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    # Main menu for staff (Bottom of screen)
    keyboard = [
        [KeyboardButton("💰 Cash Drop"), KeyboardButton("🕵️ Spot Check")],
        [KeyboardButton("🏭 Production"), KeyboardButton("📦 Restock")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_production_keyboard(products):
    # Inline buttons for selecting product to produce
    keyboard = []
    for p in products:
        keyboard.append([InlineKeyboardButton(f"Make {p.name}", callback_data=f"prod_{p.id}")])
    return InlineKeyboardMarkup(keyboard)
