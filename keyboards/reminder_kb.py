from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ReminderCallback(CallbackData, prefix="rem", sep="|"):
    action: str  # "set_time", "custom", "toggle", "close"
    value: str = ""


class ReminderPromptCallback(CallbackData, prefix="rem_p", sep="|"):
    action: str  # "headache", "healthy", "settings"


def get_reminder_settings_keyboard(current_time: str, enabled: bool) -> InlineKeyboardMarkup:
    """Builds the reminder configuration keyboard with presets and controls."""
    builder = InlineKeyboardBuilder()

    presets = [
        ("🌅 09:00", "09:00"),
        ("☀️ 14:00", "14:00"),
        ("🌇 19:00", "19:00"),
        ("🌙 21:00", "21:00"),
        ("🌃 22:00", "22:00"),
        ("🌌 23:00", "23:00"),
    ]

    for label, val in presets:
        btn_text = f"✅ {label}" if (enabled and current_time == val) else label
        builder.button(
            text=btn_text,
            callback_data=ReminderCallback(action="set_time", value=val).pack()
        )
    builder.adjust(2, 2, 2)

    builder.row(
        InlineKeyboardButton(
            text="✍️ Указать своё время (ЧЧ:ММ)",
            callback_data=ReminderCallback(action="custom").pack()
        )
    )

    toggle_text = "🔕 Отключить напоминания" if enabled else "🔔 Включить напоминания"
    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data=ReminderCallback(action="toggle").pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data=ReminderCallback(action="close").pack()
        )
    )

    return builder.as_markup()


def get_reminder_custom_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel button for text input of custom reminder time."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=ReminderCallback(action="close").pack()
        )
    )
    return builder.as_markup()


def get_reminder_prompt_keyboard() -> InlineKeyboardMarkup:
    """Interactive buttons sent during daily check-in inquiry."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🤕 Да, болела",
            callback_data=ReminderPromptCallback(action="headache").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👌 Нет, всё отлично",
            callback_data=ReminderPromptCallback(action="healthy").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏰ Настроить время",
            callback_data=ReminderPromptCallback(action="settings").pack()
        )
    )
    return builder.as_markup()
