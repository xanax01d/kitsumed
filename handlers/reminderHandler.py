import re
import zoneinfo
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.reminder_kb import (
    ReminderCallback,
    ReminderPromptCallback,
    TIMEZONE_PRESETS,
    get_reminder_settings_keyboard,
    get_reminder_custom_cancel_keyboard,
    get_timezone_keyboard,
    get_timezone_cancel_keyboard,
    get_tz_label,
    get_tz_local_time,
)
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.headache_kb import get_start_time_keyboard
from states.reminder import ReminderSG
from states.headache import HeadacheLogSG
from handlers.headache import show_or_edit_step, IMG_FLOW, step_1_text
from db import get_user_reminder, set_user_reminder, upsert_user

router = Router()

TIME_REGEX = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$")


def resolve_timezone(input_str: str) -> Optional[str]:
    """
    Parses and validates user timezone input.
    Supports IANA names (e.g. Europe/Minsk, Asia/Almaty),
    city/preset matching, and UTC offset formats (e.g. UTC+4, +5, -3, GMT+2).
    """
    cleaned = input_str.strip()

    # 1. Try directly as IANA timezone
    try:
        zoneinfo.ZoneInfo(cleaned)
        return cleaned
    except Exception:
        pass

    # 2. Try match in known presets
    for label, tz_id in TIMEZONE_PRESETS:
        if cleaned.lower() in label.lower() or cleaned.lower() == tz_id.lower():
            return tz_id

    # 3. Match UTC±X or GMT±X or just ±X
    m = re.match(r"^(?:UTC|GMT)?\s*([+-]?\d{1,2})(?::?(\d{2}))?$", cleaned.upper())
    if m:
        hours = int(m.group(1))
        mins = int(m.group(2) or 0)
        if -12 <= hours <= 14 and mins == 0:
            # Format as Etc/GMT-X (POSIX sign convention is inverted)
            posix_sign = "-" if hours > 0 else "+"
            etc_name = f"Etc/GMT{posix_sign}{abs(hours)}"
            try:
                zoneinfo.ZoneInfo(etc_name)
                return etc_name
            except Exception:
                pass

    return None


def _format_reminder_text(reminder_time: str, enabled: bool, tz_name: str = "Europe/Moscow") -> str:
    status_str = "Включен" if enabled else "Отключен"
    tz_label = get_tz_label(tz_name)
    local_time = get_tz_local_time(tz_name)
    return (
        "<b>Ежедневный опрос</b>\n\n"
        f"• Статус: <b>{status_str}</b>\n"
        f"• Время: <b>{reminder_time}</b>\n"
        f"• Пояс: {tz_label} (сейчас {local_time})"
    )


def _format_timezone_text(tz_name: str) -> str:
    tz_label = get_tz_label(tz_name)
    local_time = get_tz_local_time(tz_name)
    return (
        "<b>Часовой пояс</b>\n\n"
        f"• Пояс: <b>{tz_label}</b>\n"
        f"• Местное время: <b>{local_time}</b>"
    )


@router.message(Command("reminder"))
@router.message(Command("remind"))
@router.message(Command("settings"))
@router.message(F.text == "⏰ Напоминания")
async def show_reminder_settings(message: Message):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        rem = await get_user_reminder(user.id)
    else:
        rem = {"reminder_time": "21:00", "reminder_enabled": True, "timezone": "Europe/Moscow"}

    r_time = rem.get("reminder_time", "21:00")
    r_enabled = rem.get("reminder_enabled", True)
    r_tz = rem.get("timezone", "Europe/Moscow")

    text = _format_reminder_text(r_time, r_enabled, r_tz)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled, r_tz)
    await message.answer(text=text, reply_markup=keyboard)


@router.callback_query(ReminderCallback.filter(F.action == "set_time"))
async def process_preset_time(callback: CallbackQuery, callback_data: ReminderCallback):
    user_id = callback.from_user.id
    new_time = callback_data.value
    await set_user_reminder(user_id, reminder_time=new_time, enabled=True)

    rem = await get_user_reminder(user_id)
    r_tz = rem.get("timezone", "Europe/Moscow")

    text = _format_reminder_text(new_time, True, r_tz)
    keyboard = get_reminder_settings_keyboard(new_time, True, r_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            pass

    await callback.answer(f"Время: {new_time}")


@router.callback_query(ReminderCallback.filter(F.action == "toggle"))
async def process_toggle_reminder(callback: CallbackQuery):
    user_id = callback.from_user.id
    rem = await get_user_reminder(user_id)
    new_enabled = not rem.get("reminder_enabled", True)
    r_time = rem.get("reminder_time", "21:00")
    r_tz = rem.get("timezone", "Europe/Moscow")

    await set_user_reminder(user_id, enabled=new_enabled)

    text = _format_reminder_text(r_time, new_enabled, r_tz)
    keyboard = get_reminder_settings_keyboard(r_time, new_enabled, r_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            pass

    status_msg = "Включен" if new_enabled else "Отключен"
    await callback.answer(f"Опрос: {status_msg}")


@router.callback_query(ReminderCallback.filter(F.action == "custom"))
async def process_custom_time_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReminderSG.custom_time)
    prompt = (
        "<b>Время опроса</b>\n"
        "Введите время в формате <code>ЧЧ:ММ</code> (например: <code>20:30</code>):"
    )
    try:
        await callback.message.edit_text(text=prompt, reply_markup=get_reminder_custom_cancel_keyboard())
    except Exception:
        try:
            await callback.message.edit_caption(caption=prompt, reply_markup=get_reminder_custom_cancel_keyboard())
        except Exception:
            await callback.message.answer(text=prompt, reply_markup=get_reminder_custom_cancel_keyboard())
    await callback.answer()


@router.message(ReminderSG.custom_time, F.text)
async def process_custom_time_input(message: Message, state: FSMContext):
    text = message.text.strip()
    match = TIME_REGEX.match(text)
    if not match:
        await message.answer(
            "<b>Неверный формат времени</b>\n"
            "Введите время в формате <code>ЧЧ:ММ</code> (например: <code>21:30</code>):",
            reply_markup=get_reminder_custom_cancel_keyboard()
        )
        return

    hour, minute = match.group(1), match.group(2)
    normalized_time = f"{int(hour):02d}:{int(minute):02d}"

    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        await set_user_reminder(user.id, reminder_time=normalized_time, enabled=True)
        rem = await get_user_reminder(user.id)
        tz_label = get_tz_label(rem.get("timezone", "Europe/Moscow"))
    else:
        tz_label = "Москва (UTC+3)"

    await state.clear()
    await message.answer(
        f"Время опроса установлено: <b>{normalized_time}</b> ({tz_label}).",
        reply_markup=get_main_menu_keyboard()
    )


# --- Timezone Settings Handlers ---
@router.callback_query(ReminderCallback.filter(F.action == "tz_menu"))
async def process_open_tz_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    rem = await get_user_reminder(user_id)
    current_tz = rem.get("timezone", "Europe/Moscow")

    text = _format_timezone_text(current_tz)
    keyboard = get_timezone_keyboard(current_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await callback.message.answer(text=text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "set_tz"))
async def process_set_timezone(callback: CallbackQuery, callback_data: ReminderCallback):
    user_id = callback.from_user.id
    new_tz = callback_data.value
    await set_user_reminder(user_id, timezone=new_tz)

    rem = await get_user_reminder(user_id)
    r_time = rem.get("reminder_time", "21:00")
    r_enabled = rem.get("reminder_enabled", True)

    text = _format_reminder_text(r_time, r_enabled, new_tz)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled, new_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            pass

    tz_label = get_tz_label(new_tz)
    await callback.answer(f"Пояс: {tz_label}")


@router.callback_query(ReminderCallback.filter(F.action == "custom_tz"))
async def process_custom_tz_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReminderSG.custom_timezone)
    prompt = (
        "<b>Часовой пояс</b>\n"
        "Введите смещение или город (например: <code>UTC+5</code>, <code>+4</code> или <code>Asia/Almaty</code>):"
    )
    try:
        await callback.message.edit_text(text=prompt, reply_markup=get_timezone_cancel_keyboard())
    except Exception:
        try:
            await callback.message.edit_caption(caption=prompt, reply_markup=get_timezone_cancel_keyboard())
        except Exception:
            await callback.message.answer(text=prompt, reply_markup=get_timezone_cancel_keyboard())
    await callback.answer()


@router.message(ReminderSG.custom_timezone, F.text)
async def process_custom_timezone_input(message: Message, state: FSMContext):
    text = message.text.strip()
    resolved_tz = resolve_timezone(text)
    if not resolved_tz:
        await message.answer(
            "<b>Пояс не распознан</b>\n"
            "Укажите смещение (например <code>UTC+4</code>) или название (<code>Europe/Minsk</code>):",
            reply_markup=get_timezone_cancel_keyboard()
        )
        return

    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        await set_user_reminder(user.id, timezone=resolved_tz)

    await state.clear()
    tz_label = get_tz_label(resolved_tz)
    local_time = get_tz_local_time(resolved_tz)

    await message.answer(
        f"Часовой пояс сохранен: <b>{tz_label}</b> (сейчас {local_time})",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(ReminderCallback.filter(F.action == "back_settings"))
async def process_back_to_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    rem = await get_user_reminder(user_id)
    r_time = rem.get("reminder_time", "21:00")
    r_enabled = rem.get("reminder_enabled", True)
    r_tz = rem.get("timezone", "Europe/Moscow")

    text = _format_reminder_text(r_time, r_enabled, r_tz)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled, r_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await callback.message.answer(text=text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(ReminderCallback.filter(F.action == "close"))
async def process_close_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    await callback.answer("Закрыто")


# --- Handlers for Daily Check-in Prompt ---
@router.callback_query(ReminderPromptCallback.filter(F.action == "healthy"))
async def process_daily_healthy(callback: CallbackQuery):
    response_text = "Отметка сохранена: день без головной боли."
    try:
        await callback.message.edit_text(text=response_text, reply_markup=None)
    except Exception:
        try:
            await callback.message.edit_caption(caption=response_text, reply_markup=None)
        except Exception:
            await callback.message.answer(text=response_text)
    await callback.answer("Здорово!")


@router.callback_query(ReminderPromptCallback.filter(F.action == "headache"))
async def process_daily_headache(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(HeadacheLogSG.start_time)
    await show_or_edit_step(
        callback,
        IMG_FLOW,
        step_1_text(),
        get_start_time_keyboard()
    )
    await callback.answer()


@router.callback_query(ReminderPromptCallback.filter(F.action == "settings"))
async def process_daily_open_settings(callback: CallbackQuery):
    user_id = callback.from_user.id
    rem = await get_user_reminder(user_id)
    r_time = rem.get("reminder_time", "21:00")
    r_enabled = rem.get("reminder_enabled", True)
    r_tz = rem.get("timezone", "Europe/Moscow")

    text = _format_reminder_text(r_time, r_enabled, r_tz)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled, r_tz)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await callback.message.answer(text=text, reply_markup=keyboard)
    await callback.answer()
