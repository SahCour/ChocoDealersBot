from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    # Простое меню для персонала внизу экрана (Reply Keyboard)
    keyboard = [
        [KeyboardButton("💰 Сдать кассу"), KeyboardButton("🕵️ Ревизия")],
        [KeyboardButton("🏭 Производство"), KeyboardButton("📦 Закупка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_production_keyboard(products):
    # Инлайн кнопки с выбором продукта для производства
    keyboard = []
    for p in products:
        keyboard.append([InlineKeyboardButton(f"Make {p.name}", callback_data=f"prod_{p.id}")])
    return InlineKeyboardMarkup(keyboard)
