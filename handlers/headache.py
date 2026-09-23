from datetime import datetime, timedelta
from typing import Set, Dict, Any
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardMarkup
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
from services.media_cache import (
    get_input_media,
    get_photo_source,
    extract_and_record,
    get_cached_file_id,
)

router = Router()

# Paths to localized Russian images for every step
BASE_IMG_DIR = Path(__file__).parent.parent / "assets" / "images" / "ru"
IMG_HERO = BASE_IMG_DIR / "hero_banner.png"
IMG_FLOW = BASE_IMG_DIR / "flow_diagram.png"
IMG_PAIN_SCALE = BASE_IMG_DIR / "steps" / "pain_scale.png"
IMG_LOCATION = BASE_IMG_DIR / "steps" / "location.png"
IMG_PAIN_TYPE = BASE_IMG_DIR / "steps" / "pain_type.png"
IMG_SYMPTOMS = BASE_IMG_DIR / "steps" / "symptoms.png"
IMG_MEDICATION = BASE_IMG_DIR / "steps" / "medication.png"


async def show_or_edit_step(
    target: Message | CallbackQuery,
    image_path: Path,
    caption: str,
    reply_markup: InlineKeyboardMarkup | None = None
):
    """Seamlessly updates or sends a step with cached image file_id, caption and inline keyboard."""
    if isinstance(target, CallbackQuery):
        msg = target.message
        if image_path.is_file():
            # 1. Try fast path with cached file_id or InputMedia
            media_obj = get_input_media(image_path, caption)
            try:
                res = await msg.edit_media(media=media_obj, reply_markup=reply_markup)
                extract_and_record(image_path, res)
                return
            except Exception:
                # If cached file_id failed, retry once with raw file upload
                if get_cached_file_id(image_path):
                    try:
                        res = await msg.edit_media(
                            media=InputMediaPhoto(media=FSInputFile(str(image_path)), caption=caption),
                            reply_markup=reply_markup
                        )
                        extract_and_record(image_path, res)
                        return
                    except Exception:
                        pass
                try:
                    await msg.edit_caption(caption=caption, reply_markup=reply_markup)
                    return
                except Exception:
                    pass
        try:
            await msg.edit_text(text=caption, reply_markup=reply_markup)
        except Exception:
            await msg.answer(text=caption, reply_markup=reply_markup)
    else:
        if image_path.is_file():
            photo_src = get_photo_source(image_path)
            try:
                res = await target.answer_photo(
                    photo=photo_src,
                    caption=caption,
                    reply_markup=reply_markup
                )
                extract_and_record(image_path, res)
                return
            except Exception:
                # Fallback to FSInputFile if cached file_id failed
                if isinstance(photo_src, str):
                    try:
                        res = await target.answer_photo(
                            photo=FSInputFile(str(image_path)),
                            caption=caption,
                            reply_markup=reply_markup
                        )
                        extract_and_record(image_path, res)
                        return
                    except Exception:
                        pass
        await target.answer(text=caption, reply_markup=reply_markup)


# --- Helpers for Visual Badges & Summary ---
def _get_intensity_badge(val: int) -> tuple[str, str]:
    if val <= 3:
        return "🟢", "Слабая"
    elif val <= 6:
        return "🟡", "Умеренная"
    elif val <= 8:
        return "🟠", "Сильная"
    else:
        return "🔴", "Невыносимая"


def _get_progress_bar(val: int, max_val: int = 10) -> str:
    filled = min(max(val, 0), max_val)
    return "█" * filled + "░" * (max_val - filled)


def step_1_text() -> str:
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 1 из 6 • Время ]  ▰▱▱▱▱▱ 17%</code>\n\n"
        "⏰ <b>Когда началась головная боль?</b>\n"
        "<i>Выберите быстрый вариант или укажите точное время:</i>"
    )


def step_2_text(time_str: str) -> str:
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 2 из 6 • Сила боли ]  ▰▰▱▱▱▱ 33%</code>\n\n"
        f"⏰ Начало: <code>{time_str}</code>\n\n"
        "📊 <b>Оцените интенсивность боли по шкале от 1 до 10:</b>\n"
        "🟢 <b>1–3</b> — Слабая <i>(фоновая, работоспособность сохранена)</i>\n"
        "🟡 <b>4–6</b> — Умеренная <i>(снижает концентрацию)</i>\n"
        "🟠 <b>7–8</b> — Сильная <i>(тяжело выполнять обычные дела)</i>\n"
        "🔴 <b>9–10</b> — Невыносимая <i>(сильнейшая боль, постельный режим)</i>"
    )


def step_3_text(intensity: int) -> str:
    dot, level_name = _get_intensity_badge(intensity)
    bar = _get_progress_bar(intensity, 10)
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 3 из 6 • Локализация ]  ▰▰▰▱▱▱ 50%</code>\n\n"
        f"📊 Интенсивность: <b>{intensity}/10</b> {dot} <i>({level_name})</i>\n"
        f"    <code>[{bar}]</code>\n\n"
        "📍 <b>Где именно локализуется боль?</b>\n"
        "<i>Выберите зону сосредоточения боли:</i>"
    )


def step_4_text(loc_key: str) -> str:
    loc_text = LOCATION_MAP.get(loc_key, loc_key)
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 4 из 6 • Характер ]  ▰▰▰▰▱▱ 67%</code>\n\n"
        f"📍 Зона: <b>{loc_text}</b>\n\n"
        "⚡️ <b>Каков характер головной боли?</b>\n"
        "<i>Выберите тип ощущений (важно для клинической дифференциации):</i>"
    )


def step_5_text(pt_key: str) -> str:
    pt_text = PAIN_TYPE_MAP.get(pt_key, pt_key)
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 5 из 6 • Симптомы ]  ▰▰▰▰▰▱ 83%</code>\n\n"
        f"⚡️ Характер: <b>{pt_text}</b>\n\n"
        "🩺 <b>Есть ли сопутствующие симптомы?</b>\n"
        "<i>Отметьте нужные симптомы и нажмите «➡️ Продолжить»:</i>"
    )


def step_6_text() -> str:
    return (
        "🤕 <b>ЗАПИСЬ ПРИСТУПА</b>\n"
        "<code>[ Шаг 6 из 6 • Препарат ]  ▰▰▰▰▰▰ 100%</code>\n\n"
        "💊 <b>Укажите принятый препарат и дозировку</b> сообщением в чат:\n\n"
        "<i>(Например: <code>Суматриптан 50 мг</code>, <code>Ибупрофен 400 мг</code>, "
        "<code>Цитрамон 1 таб</code>)</i>\n\n"
        "Если вы ничего не принимали, нажмите кнопку ниже:"
    )


def format_summary(data: Dict[str, Any]) -> str:
    intensity = data.get("intensity", 0)
    dot, level_name = _get_intensity_badge(intensity)
    bar = _get_progress_bar(intensity, 10)

    loc_key = data.get("location", "")
    loc_text = LOCATION_MAP.get(loc_key, loc_key)

    pt_key = data.get("pain_type", "")
    pt_text = PAIN_TYPE_MAP.get(pt_key, pt_key)

    symptoms_list = data.get("symptoms", [])
    if not symptoms_list or "none" in symptoms_list:
        symptoms_str = "<i>Не отмечено</i>"
    else:
        symptoms_str = ", ".join(ALL_SYMPTOMS.get(s, s) for s in symptoms_list)

    med_val = data.get("medication", "Не принимались")
    if med_val == "none":
        med_val = "Не принимались"
    med_text = MEDICATION_MAP.get(med_val, med_val)

    return (
        "╔═══════════════════════════════════╗\n"
        "║   📋 <b>ИТОГОВАЯ КАРТОЧКА ПРИСТУПА</b>     ║\n"
        "╚═══════════════════════════════════╝\n\n"
        f"⏰ <b>Начало:</b> <code>{data.get('start_time', 'Не указано')}</code>\n"
        f"📊 <b>Интенсивность:</b> <b>{intensity}/10</b> {dot} <i>({level_name})</i>\n"
        f"    <code>[{bar}]</code>\n"
        f"📍 <b>Локализация:</b> {loc_text}\n"
        f"⚡️ <b>Характер:</b> {pt_text}\n"
        f"🩺 <b>Симптомы:</b> {symptoms_str}\n"
        f"💊 <b>Препарат:</b> <b>{med_text}</b>\n\n"
        "───────────────────────────────────\n"
        "<i>Все данные указаны верно? Сохранить запись в дневник?</i>"
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
    await message.answer("❌ <b>Запись приступа отменена.</b>", reply_markup=get_main_menu_keyboard())


@router.callback_query(NavCallback.filter(F.action == "cancel"))
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    try:
        await callback.message.edit_caption(
            caption="❌ <b>Запись приступа отменена.</b>",
            reply_markup=None
        )
    except Exception:
        try:
            await callback.message.edit_text(
                text="❌ <b>Запись приступа отменена.</b>",
                reply_markup=None
            )
        except Exception:
            pass
    await callback.message.answer("Вы вернулись в главное меню:", reply_markup=get_main_menu_keyboard())


# --- Navigation Back Handler ---
@router.callback_query(NavCallback.filter(F.action == "back"))
async def callback_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    current_state = await state.get_state()

    if current_state == HeadacheLogSG.custom_start_time.state:
        await state.set_state(HeadacheLogSG.start_time)
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            step_1_text(),
            get_start_time_keyboard()
        )
    elif current_state == HeadacheLogSG.intensity.state:
        await state.set_state(HeadacheLogSG.start_time)
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            step_1_text(),
            get_start_time_keyboard()
        )
    elif current_state == HeadacheLogSG.location.state:
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.intensity)
        await show_or_edit_step(
            callback,
            IMG_PAIN_SCALE,
            step_2_text(data.get("start_time", "")),
            get_intensity_keyboard()
        )
    elif current_state == HeadacheLogSG.pain_type.state:
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.location)
        await show_or_edit_step(
            callback,
            IMG_LOCATION,
            step_3_text(data.get("intensity", 0)),
            get_location_keyboard()
        )
    elif current_state == HeadacheLogSG.symptoms.state:
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.pain_type)
        await show_or_edit_step(
            callback,
            IMG_PAIN_TYPE,
            step_4_text(data.get("location", "")),
            get_pain_type_keyboard()
        )
    elif current_state == HeadacheLogSG.medication.state:
        data = await state.get_data()
        selected = set(data.get("symptoms", []))
        await state.set_state(HeadacheLogSG.symptoms)
        await show_or_edit_step(
            callback,
            IMG_SYMPTOMS,
            step_5_text(data.get("pain_type", "")),
            get_symptoms_keyboard(selected)
        )
    elif current_state == HeadacheLogSG.confirm.state:
        await state.set_state(HeadacheLogSG.medication)
        await show_or_edit_step(
            callback,
            IMG_MEDICATION,
            step_6_text(),
            get_medication_keyboard()
        )


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
                "⚠️ <b>У вас уже есть незавершенный приступ!</b>\n"
                f"🗓 Начало: <code>{active.get('start_time')}</code>\n\n"
                "Вы можете завершить его кнопкой <b>«⏹ Завершить приступ»</b> или начать новую запись.",
            )

    await state.clear()
    await state.set_state(HeadacheLogSG.start_time)
    await show_or_edit_step(
        message,
        IMG_FLOW,
        step_1_text(),
        get_start_time_keyboard()
    )


# --- Step 1: Start Time ---
@router.callback_query(HeadacheLogSG.start_time, TimeCallback.filter())
async def process_start_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext):
    await callback.answer()
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
        custom_prompt = (
            "✍️ <b>Введите время начала приступа</b> текстом в чат:\n\n"
            "<i>(Например: <code>15:40</code> или <code>вчера в 21:00</code>)</i>"
        )
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            custom_prompt,
            get_cancel_keyboard(show_back=True)
        )
        return
    else:
        time_str = now.strftime("%Y-%m-%d %H:%M")

    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await show_or_edit_step(
        callback,
        IMG_PAIN_SCALE,
        step_2_text(time_str),
        get_intensity_keyboard()
    )


@router.message(HeadacheLogSG.custom_start_time, F.text)
async def process_custom_start_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await show_or_edit_step(
        message,
        IMG_PAIN_SCALE,
        step_2_text(time_str),
        get_intensity_keyboard()
    )


# --- Step 2: Intensity ---
@router.callback_query(HeadacheLogSG.intensity, IntensityCallback.filter())
async def process_intensity(callback: CallbackQuery, callback_data: IntensityCallback, state: FSMContext):
    await callback.answer()
    intensity = callback_data.value
    await state.update_data(intensity=intensity)
    await state.set_state(HeadacheLogSG.location)
    await show_or_edit_step(
        callback,
        IMG_LOCATION,
        step_3_text(intensity),
        get_location_keyboard()
    )


# --- Step 3: Location ---
@router.callback_query(HeadacheLogSG.location, LocationCallback.filter())
async def process_location(callback: CallbackQuery, callback_data: LocationCallback, state: FSMContext):
    await callback.answer()
    loc_key = callback_data.value
    await state.update_data(location=loc_key)
    await state.set_state(HeadacheLogSG.pain_type)
    await show_or_edit_step(
        callback,
        IMG_PAIN_TYPE,
        step_4_text(loc_key),
        get_pain_type_keyboard()
    )


# --- Step 4: Pain Type ---
@router.callback_query(HeadacheLogSG.pain_type, PainTypeCallback.filter())
async def process_pain_type(callback: CallbackQuery, callback_data: PainTypeCallback, state: FSMContext):
    await callback.answer()
    pt_key = callback_data.value
    await state.update_data(pain_type=pt_key, symptoms=[])
    await state.set_state(HeadacheLogSG.symptoms)
    await show_or_edit_step(
        callback,
        IMG_SYMPTOMS,
        step_5_text(pt_key),
        get_symptoms_keyboard(set())
    )


# --- Step 5: Symptoms (Multi-select) ---
@router.callback_query(HeadacheLogSG.symptoms, SymptomCallback.filter())
async def process_symptoms(callback: CallbackQuery, callback_data: SymptomCallback, state: FSMContext):
    await callback.answer()
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
        await show_or_edit_step(
            callback,
            IMG_MEDICATION,
            step_6_text(),
            get_medication_keyboard()
        )


# --- Step 6: Medication (Manual entry + skip button) ---
@router.callback_query(HeadacheLogSG.medication, MedicationCallback.filter())
async def process_medication_skip(callback: CallbackQuery, callback_data: MedicationCallback, state: FSMContext):
    await callback.answer()
    if callback_data.value == "none":
        await state.update_data(medication="Не принимались")
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.confirm)
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            format_summary(data),
            get_confirm_keyboard()
        )


@router.message(HeadacheLogSG.medication, F.text)
async def process_medication_input(message: Message, state: FSMContext):
    med_name = message.text.strip()
    await state.update_data(medication=med_name)
    data = await state.get_data()
    await state.set_state(HeadacheLogSG.confirm)
    await show_or_edit_step(
        message,
        IMG_FLOW,
        format_summary(data),
        get_confirm_keyboard()
    )


# --- Step 7: Confirmation ---
@router.callback_query(HeadacheLogSG.confirm, ConfirmCallback.filter())
async def process_confirmation(callback: CallbackQuery, callback_data: ConfirmCallback, state: FSMContext):
    await callback.answer()
    if callback_data.action == "cancel":
        await state.clear()
        try:
            await callback.message.edit_caption(
                caption="❌ <b>Запись приступа отменена.</b>",
                reply_markup=None
            )
        except Exception:
            try:
                await callback.message.edit_text(
                    text="❌ <b>Запись приступа отменена.</b>",
                    reply_markup=None
                )
            except Exception:
                pass
        await callback.message.answer("Вы вернулись в главное меню:", reply_markup=get_main_menu_keyboard())
        return

    # Save to database
    data = await state.get_data()
    user = callback.from_user
    episode_id = await create_episode(user.id, data)
    await state.clear()

    saved_text = (
        f"✅ <b>Приступ успешно сохранен в дневник!</b> (Запись #{episode_id})\n\n"
        "🧘‍♂️ <b>Рекомендации первой помощи:</b>\n"
        "💧 Выпейте стакан чистой воды\n"
        "🌑 Отдохните в затемненной и тихой комнате\n"
        "❄️ Приложите прохладный компресс на лоб или шею\n\n"
        "Когда боль стихнет, нажмите кнопку <b>«⏹ Завершить приступ»</b>, чтобы зафиксировать продолжительность."
    )

    await show_or_edit_step(
        callback,
        IMG_HERO,
        saved_text,
        None
    )
    await callback.message.answer(
        "Вы можете в любой момент посмотреть историю или зафиксировать окончание боли через меню ниже:",
        reply_markup=get_main_menu_keyboard()
    )


# --- Finish Episode Button ---
@router.message(F.text == "⏹ Завершить приступ")
@router.message(Command("finish"))
async def cmd_finish_episode(message: Message):
    user = message.from_user
    active = await get_active_episode(user.id)

    if not active:
        await message.answer(
            "ℹ️ <b>У вас сейчас нет активного незавершенного приступа.</b>\n\n"
            "Чтобы зафиксировать новый приступ, нажмите кнопку <b>«🤕 Записать приступ»</b>.",
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
        duration_str = f"{hours} ч {minutes} мин"
    except Exception:
        duration_str = "не рассчитана"

    finish_text = (
        "🎉 <b>Приступ успешно завершен!</b>\n\n"
        f"⏱ <b>Длительность:</b> <b>{duration_str}</b>\n"
        f"🗓 <b>Начало:</b> <code>{start_str}</code>\n"
        f"🏁 <b>Окончание:</b> <code>{end_time_str}</code>\n\n"
        "<i>Данные зафиксированы в истории. Рады, что вам стало лучше! 💚</i>"
    )

    await show_or_edit_step(
        message,
        IMG_HERO,
        finish_text,
        None
    )
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
