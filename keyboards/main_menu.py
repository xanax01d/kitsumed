from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Returns the main bottom reply keyboard."""
    keyboard = [
        [KeyboardButton(text="🤕 Записать приступ"), KeyboardButton(text="⏹ Завершить приступ")],
        [KeyboardButton(text="📊 Мои приступы"), KeyboardButton(text="📥 Экспорт отчета")],
        [KeyboardButton(text="⏰ Напоминания"), KeyboardButton(text="ℹ️ Справка")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие в меню..."
    )
