from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from locales import get_text

LOG_BUTTONS = [
    "🤕 Записать приступ",
    "🤕 Log Episode",
    "🤕 Записать суету",
]

STATUS_BUTTONS = [
    "⏹ Прошла ли боль?",
    "⏹ Did Pain Pass?",
    "⏹ Че с болью?",
    "⏹ Завершить приступ",
    "⏹ End Episode",
    "⏹ Завершить",
]

HISTORY_BUTTONS = [
    "📊 Мои приступы",
    "📊 My Episodes",
    "📊 Архив кринжа",
]

EXPORT_BUTTONS = [
    "📥 Экспорт отчета",
    "📥 Export Report",
    "📥 Слить инфу доку",
]

REMINDER_BUTTONS = [
    "⏰ Напоминания",
    "⏰ Reminders",
    "⏰ Будильник",
]

LANGUAGE_BUTTONS = [
    "🌐 Язык",
    "🌐 Language",
    "🌐 Базар / Язык",
]

HELP_BUTTONS = [
    "ℹ️ Справка",
    "ℹ️ Help",
    "ℹ️ Поясни за бота",
]


def get_main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Returns the main bottom reply keyboard localized to the user's language."""
    keyboard = [
        [
            KeyboardButton(text=get_text("btn_log", lang)),
            KeyboardButton(text=get_text("btn_status", lang)),
        ],
        [
            KeyboardButton(text=get_text("btn_history", lang)),
            KeyboardButton(text=get_text("btn_export", lang)),
        ],
        [
            KeyboardButton(text=get_text("btn_reminder", lang)),
            KeyboardButton(text=get_text("btn_language", lang)),
            KeyboardButton(text=get_text("btn_help", lang)),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Migrebot Menu...",
    )
