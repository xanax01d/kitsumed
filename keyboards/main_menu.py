from typing import List, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from locales import get_text, SUPPORTED_LANGUAGES


def _collect_buttons(btn_key: str, extra: Optional[List[str]] = None) -> List[str]:
    buttons = set(extra or [])
    for lang in SUPPORTED_LANGUAGES:
        txt = get_text(btn_key, lang)
        if txt and not txt.startswith("["):
            buttons.add(txt)
    return sorted(list(buttons))


LOG_BUTTONS = _collect_buttons("btn_log", [
    "🤕 Записать приступ",
    "🤕 Log Episode",
    "🤕 Записать суету",
    "⚡️ Зафиксировать сбой нейросети",
])

STATUS_BUTTONS = _collect_buttons("btn_status", [
    "⏹ Прошла ли боль?",
    "⏹ Did Pain Pass?",
    "⏹ Че с болью?",
    "⏹ Статус биочипа",
    "⏹ Завершить приступ",
    "⏹ End Episode",
    "⏹ Завершить",
])

HISTORY_BUTTONS = _collect_buttons("btn_history", [
    "📊 Мои приступы",
    "📊 My Episodes",
    "📊 Архив кринжа",
    "📊 Логи киберпсихоза",
])

EXPORT_BUTTONS = _collect_buttons("btn_export", [
    "📥 Экспорт отчета",
    "📥 Export Report",
    "📥 Слить инфу доку",
    "📥 Слить датапак рипердоку",
])

REMINDER_BUTTONS = _collect_buttons("btn_reminder", [
    "⏰ Напоминания",
    "⏰ Reminders",
    "⏰ Будильник",
    "⏰ Калибровка биомонитора",
])

LANGUAGE_BUTTONS = _collect_buttons("btn_language", [
    "🌐 Язык",
    "🌐 Language",
    "🌐 Базар / Язык",
    "🌐 Протокол / Язык",
])

HELP_BUTTONS = _collect_buttons("btn_help", [
    "ℹ️ Справка",
    "ℹ️ Help",
    "ℹ️ Поясни за бота",
    "ℹ️ Мануал нетраннера",
])

CANCEL_BUTTONS = _collect_buttons("btn_cancel", [
    "отмена",
    "❌ отмена",
    "cancel",
    "❌ cancel",
    "❌ отмена суеты",
    "❌ аварийный сброс",
])


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
