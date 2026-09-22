import re
from typing import Optional, Union

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.reminder_kb import (
    ReminderCallback,
    ReminderPromptCallback,
    get_reminder_settings_keyboard,
    get_reminder_custom_cancel_keyboard,
)
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.headache_kb import get_start_time_keyboard
from states.reminder import ReminderSG
from states.headache import HeadacheLogSG
from handlers.headache import show_or_edit_step, IMG_FLOW, step_1_text
from db import get_user_reminder, set_user_reminder, upsert_user

router = Router()

TIME_REGEX = re.compile(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$")


def _format_reminder_text(reminder_time: str, enabled: bool) -> str:
    status_str = f"🟢 <b>Включено</b> (каждый день в <b>{reminder_time}</b> МСК)" if enabled else "🔴 <b>Отключено</b>"
    return (
        "⏰ <b>Ежедневный опрос о самочувствии</b>\n\n"
        f"Текущий статус: {status_str}\n\n"
        "Каждый день в установленное время бот будет отправлять вам короткий вопрос:\n"
        "<i>«Болела ли голова сегодня?»</i> — чтобы вы не забывали фиксировать приступы и вести точную статистику для невролога.\n\n"
        "Выберите удобное время или укажите своё:"
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
        rem = {"reminder_time": "21:00", "reminder_enabled": True}

    r_time = rem.get("reminder_time", "21:00")
    r_enabled = rem.get("reminder_enabled", True)

    text = _format_reminder_text(r_time, r_enabled)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled)
    await message.answer(text=text, reply_markup=keyboard)


@router.callback_query(ReminderCallback.filter(F.action == "set_time"))
async def process_preset_time(callback: CallbackQuery, callback_data: ReminderCallback):
    user_id = callback.from_user.id
    new_time = callback_data.value
    await set_user_reminder(user_id, reminder_time=new_time, enabled=True)

    text = _format_reminder_text(new_time, True)
    keyboard = get_reminder_settings_keyboard(new_time, True)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            pass

    await callback.answer(f"✅ Время установлено на {new_time} МСК")


@router.callback_query(ReminderCallback.filter(F.action == "toggle"))
async def process_toggle_reminder(callback: CallbackQuery):
    user_id = callback.from_user.id
    rem = await get_user_reminder(user_id)
    new_enabled = not rem.get("reminder_enabled", True)
    r_time = rem.get("reminder_time", "21:00")

    await set_user_reminder(user_id, enabled=new_enabled)

    text = _format_reminder_text(r_time, new_enabled)
    keyboard = get_reminder_settings_keyboard(r_time, new_enabled)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            pass

    status_msg = "Включено" if new_enabled else "Отключено"
    await callback.answer(f"🔔 Напоминания: {status_msg}")


@router.callback_query(ReminderCallback.filter(F.action == "custom"))
async def process_custom_time_request(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReminderSG.custom_time)
    prompt = (
        "✍️ <b>Введите время ежедневного опроса</b> в формате <code>ЧЧ:ММ</code> (по московскому времени):\n\n"
        "<i>(Например: <code>20:30</code> или <code>08:15</code>)</i>"
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
            "⚠️ <b>Некорректный формат времени.</b>\n\n"
            "Пожалуйста, введите время в формате <code>ЧЧ:ММ</code> (от <code>00:00</code> до <code>23:59</code>):\n"
            "<i>(Например: <code>21:30</code> или <code>09:00</code>)</i>",
            reply_markup=get_reminder_custom_cancel_keyboard()
        )
        return

    hour, minute = match.group(1), match.group(2)
    normalized_time = f"{int(hour):02d}:{int(minute):02d}"

    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        await set_user_reminder(user.id, reminder_time=normalized_time, enabled=True)

    await state.clear()
    await message.answer(
        f"✅ <b>Время успешно сохранено!</b>\n\n"
        f"Каждый день в <b>{normalized_time}</b> МСК бот будет отправлять вопрос о самочувствии.",
        reply_markup=get_main_menu_keyboard()
    )


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
    response_text = (
        "🎉 <b>Замечательно!</b>\n\n"
        "Рады, что сегодня обошлось без головной боли. Отметка сохранена в дневнике!\n"
        "Крепкого вам здоровья и отличного вечера. ✨"
    )
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

    text = _format_reminder_text(r_time, r_enabled)
    keyboard = get_reminder_settings_keyboard(r_time, r_enabled)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await callback.message.answer(text=text, reply_markup=keyboard)
    await callback.answer()
