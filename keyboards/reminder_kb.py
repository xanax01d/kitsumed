import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ReminderCallback(CallbackData, prefix="rem", sep="|"):
    action: str  # "set_time", "custom", "toggle", "close", "tz_menu", "set_tz", "custom_tz", "back_settings"
    value: str = ""


class ReminderPromptCallback(CallbackData, prefix="rem_p", sep="|"):
    action: str  # "headache", "healthy", "settings"


TIMEZONE_PRESETS = [
    ("Калининград (UTC+2)", "Europe/Kaliningrad"),
    ("Москва, СПб (UTC+3)", "Europe/Moscow"),
    ("Самара, Баку (UTC+4)", "Europe/Samara"),
    ("Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
    ("Омск, Астана (UTC+6)", "Asia/Omsk"),
    ("Новосибирск (UTC+7)", "Asia/Novosibirsk"),
    ("Иркутск (UTC+8)", "Asia/Irkutsk"),
    ("Якутск (UTC+9)", "Asia/Yakutsk"),
    ("Владивосток (UTC+10)", "Asia/Vladivostok"),
    ("Магадан (UTC+11)", "Asia/Magadan"),
    ("Камчатка (UTC+12)", "Asia/Kamchatka"),
    ("Берлин, Варшава (UTC+1)", "Europe/Berlin"),
    ("Лондон (UTC+0)", "Europe/London"),
    ("Нью-Йорк (UTC-5)", "America/New_York"),
]

TIMEZONE_LABELS = {tz: label for label, tz in TIMEZONE_PRESETS}


def get_tz_label(tz_key: str) -> str:
    """Returns a friendly label for the given timezone identifier."""
    if tz_key in TIMEZONE_LABELS:
        return TIMEZONE_LABELS[tz_key]
    if tz_key.startswith("Etc/GMT"):
        # Format Etc/GMT-3 as UTC+3
        try:
            offset_part = tz_key.replace("Etc/GMT", "")
            if offset_part.startswith("-"):
                return f"UTC+{offset_part[1:]}"
            elif offset_part.startswith("+"):
                return f"UTC-{offset_part[1:]}"
            return "UTC+0"
        except Exception:
            pass
    return tz_key


def get_tz_local_time(tz_key: str) -> str:
    """Returns the current formatted local time (HH:MM) in the given timezone."""
    try:
        tz = zoneinfo.ZoneInfo(tz_key)
    except Exception:
        tz = timezone(timedelta(hours=3))
    return datetime.now(tz).strftime("%H:%M")


def get_reminder_settings_keyboard(
    current_time: str,
    enabled: bool,
    current_tz: str = "Europe/Moscow"
) -> InlineKeyboardMarkup:
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

    tz_label = get_tz_label(current_tz)
    builder.row(
        InlineKeyboardButton(
            text=f"🌍 Пояс: {tz_label}",
            callback_data=ReminderCallback(action="tz_menu").pack()
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


def get_timezone_keyboard(current_tz: str) -> InlineKeyboardMarkup:
    """Builds the timezone selection keyboard with city presets."""
    builder = InlineKeyboardBuilder()

    for label, tz_id in TIMEZONE_PRESETS:
        is_current = (current_tz == tz_id)
        btn_text = f"✅ {label}" if is_current else label
        builder.button(
            text=btn_text,
            callback_data=ReminderCallback(action="set_tz", value=tz_id).pack()
        )
    builder.adjust(2, 2, 2, 2, 2, 1, 2, 1)

    builder.row(
        InlineKeyboardButton(
            text="✍️ Ввести вручную (UTC±X или город)",
            callback_data=ReminderCallback(action="custom_tz").pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к напоминаниям",
            callback_data=ReminderCallback(action="back_settings").pack()
        )
    )

    return builder.as_markup()


def get_timezone_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel button for manual timezone input."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=ReminderCallback(action="back_settings").pack()
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


def get_reminder_prompt_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Interactive buttons sent during daily check-in inquiry."""
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        b_yes = "🤕 Да, был кринж"
        b_no = "👌 Не, я гигачад"
        b_set = "⚙️ Настроить будильник"
    elif lang == "cyberpunk":
        b_yes = "🤕 Да, был сбой имплантов"
        b_no = "👌 Биомонитор в норме"
        b_set = "⚙️ Калибровка таймера"
    elif lang == "en":
        b_yes = "🤕 Yes, it did"
        b_no = "👌 No, felt great"
        b_set = "⚙️ Adjust time"
    else:
        b_yes = "🤕 Да, болела"
        b_no = "👌 Нет, всё отлично"
        b_set = "⚙️ Настроить время"

    builder.row(
        InlineKeyboardButton(
            text=b_yes,
            callback_data=ReminderPromptCallback(action="headache").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=b_no,
            callback_data=ReminderPromptCallback(action="healthy").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=b_set,
            callback_data=ReminderPromptCallback(action="settings").pack()
        )
    )
    return builder.as_markup()
