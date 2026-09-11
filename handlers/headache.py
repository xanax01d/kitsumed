from datetime import datetime, timedelta
from typing import Set, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.headache import HeadacheLogSG
from keyboards.headache_kb import (
    get_start_time_keyboard,
    get_intensity_keyboard,
    get_location_keyboard,
    get_pain_type_keyboard,
    get_symptoms_keyboard,
    get_medication_keyboard,
    get_confirm_keyboard,
    get_cancel_keyboard,
    LOCATION_MAP,
    PAIN_TYPE_MAP,
    ALL_SYMPTOMS,
    MEDICATION_MAP,
    TimeCallback,
    IntensityCallback,
    LocationCallback,
    PainTypeCallback,
    SymptomCallback,
    MedicationCallback,
    ConfirmCallback,
    NavCallback,
)
from keyboards.main_menu import get_main_menu_keyboard
from db import create_episode, get_active_episode, finish_episode, upsert_user

router = Router()


# --- Helper to format summary ---
def format_summary(data: Dict[str, Any]) -> str:
    intensity = data.get("intensity", 0)
    int_emoji = "🟢" if intensity <= 3 else ("🟡" if intensity <= 6 else "🔴")

    loc_key = data.get("location", "")
    loc_text = LOCATION_MAP.get(loc_key, loc_key)

    pt_key = data.get("pain_type", "")
    pt_text = PAIN_TYPE_MAP.get(pt_key, pt_key)

    symptoms_list = data.get("symptoms", [])
    if not symptoms_list or "none" in symptoms_list:
        symptoms_str = "Нет"
    else:
        symptoms_str = ", ".join(ALL_SYMPTOMS.get(s, s) for s in symptoms_list)

    med_val = data.get("medication", "none")
    med_text = MEDICATION_MAP.get(med_val, med_val)

    return (
        "<b>📋 Проверьте данные о приступе:</b>\n\n"
        f"⏰ <b>Начало:</b> {data.get('start_time', 'Не указано')}\n"
        f"📊 <b>Интенсивность:</b> {intensity}/10 {int_emoji}\n"
        f"📍 <b>Локализация:</b> {loc_text}\n"
        f"⚡️ <b>Характер:</b> {pt_text}\n"
        f"🩺 <b>Симптомы:</b> {symptoms_str}\n"
        f"💊 <b>Препарат:</b> {med_text}\n"
    )


# --- Cancel Command & Handlers ---
@router.message(Command("cancel"))
@router.message(F.text.casefold().in_(["отмена", "❌ отмена"]))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного процесса для отмены.", reply_markup=get_main_menu_keyboard())
        return

    await state.clear()
    await message.answer("❌ Запись приступа отменена.", reply_markup=get_main_menu_keyboard())


@router.callback_query(NavCallback.filter(F.action == "cancel"))
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Запись приступа отменена.")
    await callback.message.answer("Вы вернулись в главное меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()


# --- Navigation Back Handler ---
@router.callback_query(NavCallback.filter(F.action == "back"))
async def callback_back(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state == HeadacheLogSG.intensity.state:
        await state.set_state(HeadacheLogSG.start_time)
        await callback.message.edit_text(
            "⏰ <b>Когда началась головная боль?</b>",
            reply_markup=get_start_time_keyboard()
        )
    elif current_state == HeadacheLogSG.location.state:
        await state.set_state(HeadacheLogSG.intensity)
        await callback.message.edit_text(
            "📊 <b>Оцените интенсивность боли по шкале от 1 до 10:</b>\n"
            "<i>(1 — еле заметная, 10 — невыносимая)</i>",
            reply_markup=get_intensity_keyboard()
        )
    elif current_state == HeadacheLogSG.pain_type.state:
        await state.set_state(HeadacheLogSG.location)
        await callback.message.edit_text(
            "📍 <b>Где именно локализуется боль?</b>",
            reply_markup=get_location_keyboard()
        )
    elif current_state == HeadacheLogSG.symptoms.state:
        await state.set_state(HeadacheLogSG.pain_type)
        await callback.message.edit_text(
            "⚡️ <b>Каков характер головной боли?</b>",
            reply_markup=get_pain_type_keyboard()
        )
    elif current_state == HeadacheLogSG.medication.state:
        data = await state.get_data()
        selected = set(data.get("symptoms", []))
        await state.set_state(HeadacheLogSG.symptoms)
        await callback.message.edit_text(
            "🩺 <b>Есть ли сопутствующие симптомы?</b>\n"
            "<i>(Отметьте нужные пункты и нажмите «➡️ Продолжить»)</i>",
            reply_markup=get_symptoms_keyboard(selected)
        )
    elif current_state == HeadacheLogSG.confirm.state:
        await state.set_state(HeadacheLogSG.medication)
        await callback.message.edit_text(
            "💊 <b>Принимали ли вы лекарство?</b>",
            reply_markup=get_medication_keyboard()
        )

    await callback.answer()


# --- Entry Point: Start Logging ---
@router.message(Command("log"))
@router.message(Command("headache"))
@router.message(F.text == "🤕 Записать приступ")
async def start_headache_log(message: Message, state: FSMContext):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)

        # Check if there is an active episode
        active = await get_active_episode(user.id)
        if active:
            await message.answer(
                "⚠️ <b>У вас уже есть незавершенный приступ</b>, начатый: "
                f"<code>{active.get('start_time')}</code>.\n\n"
                "Вы можете сначала завершить его кнопкой «⏹ Завершить приступ» или начать новую запись.",
            )

    await state.clear()
    await state.set_state(HeadacheLogSG.start_time)
    await message.answer(
        "🤕 <b>Запись нового приступа</b>\n\n"
        "⏰ <b>Когда началась головная боль?</b>",
        reply_markup=get_start_time_keyboard()
    )


# --- Step 1: Start Time ---
@router.callback_query(HeadacheLogSG.start_time, TimeCallback.filter())
async def process_start_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext):
    now = datetime.now()
    preset = callback_data.preset

    if preset == "now":
        time_str = now.strftime("%Y-%m-%d %H:%M")
    elif preset == "-30m":
        time_str = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    elif preset == "-1h":
        time_str = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    elif preset == "-2h":
        time_str = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    elif preset == "custom":
        await state.set_state(HeadacheLogSG.custom_start_time)
        await callback.message.edit_text(
            "✍️ <b>Введите время начала приступа</b> текстом\n"
            "<i>(Например: <code>15:40</code> или <code>вчера в 21:00</code>)</i>:",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        return
    else:
        time_str = now.strftime("%Y-%m-%d %H:%M")

    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await callback.message.edit_text(
        f"⏰ Время начала: <b>{time_str}</b>\n\n"
        "📊 <b>Оцените интенсивность боли по шкале от 1 до 10:</b>\n"
        "<i>(1 — едва ощутимая, 5 — умеренная, 10 — невыносимая)</i>",
        reply_markup=get_intensity_keyboard()
    )
    await callback.answer()


@router.message(HeadacheLogSG.custom_start_time, F.text)
async def process_custom_start_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await message.answer(
        f"⏰ Время начала: <b>{time_str}</b>\n\n"
        "📊 <b>Оцените интенсивность боли по шкале от 1 до 10:</b>\n"
        "<i>(1 — едва ощутимая, 5 — умеренная, 10 — невыносимая)</i>",
        reply_markup=get_intensity_keyboard()
    )


# --- Step 2: Intensity ---
@router.callback_query(HeadacheLogSG.intensity, IntensityCallback.filter())
async def process_intensity(callback: CallbackQuery, callback_data: IntensityCallback, state: FSMContext):
    intensity = callback_data.value
    await state.update_data(intensity=intensity)
    await state.set_state(HeadacheLogSG.location)
    await callback.message.edit_text(
        f"📊 Интенсивность: <b>{intensity}/10</b>\n\n"
        "📍 <b>Где локализуется боль?</b>",
        reply_markup=get_location_keyboard()
    )
    await callback.answer()


# --- Step 3: Location ---
@router.callback_query(HeadacheLogSG.location, LocationCallback.filter())
async def process_location(callback: CallbackQuery, callback_data: LocationCallback, state: FSMContext):
    loc_key = callback_data.value
    await state.update_data(location=loc_key)
    await state.set_state(HeadacheLogSG.pain_type)
    await callback.message.edit_text(
        f"📍 Локализация: <b>{LOCATION_MAP.get(loc_key, loc_key)}</b>\n\n"
        "⚡️ <b>Каков характер боли?</b>",
        reply_markup=get_pain_type_keyboard()
    )
    await callback.answer()


# --- Step 4: Pain Type ---
@router.callback_query(HeadacheLogSG.pain_type, PainTypeCallback.filter())
async def process_pain_type(callback: CallbackQuery, callback_data: PainTypeCallback, state: FSMContext):
    pt_key = callback_data.value
    await state.update_data(pain_type=pt_key, symptoms=[])
    await state.set_state(HeadacheLogSG.symptoms)
    await callback.message.edit_text(
        f"⚡️ Характер: <b>{PAIN_TYPE_MAP.get(pt_key, pt_key)}</b>\n\n"
        "🩺 <b>Есть ли сопутствующие симптомы?</b>\n"
        "<i>(Отметьте нужные пункты и нажмите «➡️ Продолжить»)</i>",
        reply_markup=get_symptoms_keyboard(set())
    )
    await callback.answer()


# --- Step 5: Symptoms (Multi-select) ---
@router.callback_query(HeadacheLogSG.symptoms, SymptomCallback.filter())
async def process_symptoms(callback: CallbackQuery, callback_data: SymptomCallback, state: FSMContext):
    data = await state.get_data()
    selected: Set[str] = set(data.get("symptoms", []))
    action = callback_data.action
    val = callback_data.value

    if action == "toggle":
        if "none" in selected:
            selected.remove("none")
        if val in selected:
            selected.remove(val)
        else:
            selected.add(val)
        await state.update_data(symptoms=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_symptoms_keyboard(selected))

    elif action == "none":
        selected = {"none"}
        await state.update_data(symptoms=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_symptoms_keyboard(selected))

    elif action == "done":
        await state.set_state(HeadacheLogSG.medication)
        await callback.message.edit_text(
            "💊 <b>Принимали ли вы лекарство?</b>",
            reply_markup=get_medication_keyboard()
        )

    await callback.answer()


# --- Step 6: Medication ---
@router.callback_query(HeadacheLogSG.medication, MedicationCallback.filter())
async def process_medication(callback: CallbackQuery, callback_data: MedicationCallback, state: FSMContext):
    med_val = callback_data.value

    if med_val == "custom":
        await state.set_state(HeadacheLogSG.custom_medication)
        await callback.message.edit_text(
            "✍️ <b>Введите название лекарства и дозировку</b> текстом:\n"
            "<i>(Например: <code>Ибупрофен 400 мг</code> или <code>Суматриптан 50 мг</code>)</i>",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        return

    await state.update_data(medication=med_val)
    data = await state.get_data()
    await state.set_state(HeadacheLogSG.confirm)
    await callback.message.edit_text(
        format_summary(data),
        reply_markup=get_confirm_keyboard()
    )
    await callback.answer()


@router.message(HeadacheLogSG.custom_medication, F.text)
async def process_custom_medication(message: Message, state: FSMContext):
    med_name = message.text.strip()
    await state.update_data(medication=med_name)
    data = await state.get_data()
    await state.set_state(HeadacheLogSG.confirm)
    await message.answer(
        format_summary(data),
        reply_markup=get_confirm_keyboard()
    )


# --- Step 7: Confirmation ---
@router.callback_query(HeadacheLogSG.confirm, ConfirmCallback.filter())
async def process_confirmation(callback: CallbackQuery, callback_data: ConfirmCallback, state: FSMContext):
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Запись приступа отменена.")
        await callback.message.answer("Вы вернулись в главное меню:", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    # Save to database
    data = await state.get_data()
    user = callback.from_user
    episode_id = await create_episode(user.id, data)
    await state.clear()

    await callback.message.edit_text(
        "✅ <b>Приступ успешно записан!</b> (№" + str(episode_id) + ")\n\n"
        "💡 <i>Рекомендации:</i>\n"
        "• Выпейте стакан чистой воды\n"
        "• Отдохните в затемненной и тихой комнате\n"
        "• Положите прохладный компресс на лоб или шею\n\n"
        "Когда головная боль стихнет, нажмите кнопку <b>«⏹ Завершить приступ»</b>, чтобы зафиксировать продолжительность.",
        reply_markup=None
    )
    await callback.message.answer(
        "Вы можете в любой момент посмотреть историю или зафиксировать окончание боли через меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


# --- Finish Episode Button ---
@router.message(F.text == "⏹ Завершить приступ")
@router.message(Command("finish"))
async def cmd_finish_episode(message: Message):
    user = message.from_user
    active = await get_active_episode(user.id)

    if not active:
        await message.answer(
            "ℹ️ У вас сейчас нет активного незавершенного приступа.\n\n"
            "Чтобы зафиксировать новый приступ, нажмите кнопку «🤕 Записать приступ».",
            reply_markup=get_main_menu_keyboard()
        )
        return

    end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    await finish_episode(user.id, end_time_str)

    start_str = active.get("start_time", "")
    duration_str = ""
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        now_dt = datetime.now()
        diff = now_dt - start_dt
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        duration_str = f"\n⏱ <b>Длительность приступа:</b> {hours} ч {minutes} мин"
    except Exception:
        pass

    await message.answer(
        f"🎉 <b>Приступ завершен!</b>\n\n"
        f"Начало: <code>{start_str}</code>\n"
        f"Окончание: <code>{end_time_str}</code>"
        f"{duration_str}\n\n"
        "Данные сохранены в ваш дневник. Рады, что вам стало легче!",
        reply_markup=get_main_menu_keyboard()
    )
