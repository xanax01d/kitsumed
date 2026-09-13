import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.headache import HeadacheLogSG
from keyboards.headache_kb import (
    TimeCallback, IntensityCallback, LocationCallback, PainTypeCallback,
    SymptomCallback, MedicationCallback, ConfirmCallback, NavCallback,
    get_start_time_keyboard, get_intensity_keyboard, get_location_keyboard,
    get_pain_type_keyboard, get_symptoms_keyboard, get_medication_keyboard,
    get_confirm_keyboard, get_cancel_keyboard,
    LOCATION_MAP, PAIN_TYPE_MAP, ALL_SYMPTOMS, MEDICATION_MAP
)
from keyboards.main_menu import get_main_menu_keyboard, LOG_BUTTONS, CANCEL_BUTTONS
from db import create_episode, get_active_episode, upsert_user, get_user_language
from services.media_cache import get_photo_source, extract_and_record
from locales import (
    get_text,
    get_intensity_label,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
)

router = Router()

# Paths to localized Russian step illustration cards
BASE_ASSETS = Path(__file__).parent.parent / "assets" / "images" / "ru"
IMG_FLOW = BASE_ASSETS / "flow_diagram.png"
IMG_HERO = BASE_ASSETS / "hero_banner.png"
IMG_PAIN_SCALE = BASE_ASSETS / "steps" / "pain_scale.png"
IMG_LOCATION = BASE_ASSETS / "steps" / "location.png"
IMG_PAIN_TYPE = BASE_ASSETS / "steps" / "pain_type.png"
IMG_SYMPTOMS = BASE_ASSETS / "steps" / "symptoms.png"
IMG_MEDICATION = BASE_ASSETS / "steps" / "medication.png"


# --- Navigation History Helper ---
STEP_ORDER = [
    HeadacheLogSG.start_time,
    HeadacheLogSG.intensity,
    HeadacheLogSG.location,
    HeadacheLogSG.pain_type,
    HeadacheLogSG.symptoms,
    HeadacheLogSG.medication,
    HeadacheLogSG.confirm
]


async def show_or_edit_step(
    target: Any,
    photo_path: Path,
    text: str,
    reply_markup: Any = None
):
    """
    Renders an illustration with caption. Edits existing photo caption if incoming update
    is a CallbackQuery with photo; otherwise sends a new photo message or plain text.
    """
    photo_source = get_photo_source(photo_path) if (photo_path and photo_path.is_file()) else None

    if isinstance(target, CallbackQuery):
        msg = target.message
        if msg and msg.photo and photo_source:
            try:
                await msg.edit_caption(caption=text, reply_markup=reply_markup)
                return
            except Exception:
                pass
            try:
                await msg.edit_text(text=text, reply_markup=reply_markup)
                return
            except Exception:
                pass

        if photo_source:
            try:
                res = await target.message.answer_photo(
                    photo=photo_source,
                    caption=text,
                    reply_markup=reply_markup
                )
                extract_and_record(photo_path, res)
                return
            except Exception:
                if isinstance(photo_source, str) and photo_path.is_file():
                    try:
                        res = await target.message.answer_photo(
                            photo=FSInputFile(str(photo_path)),
                            caption=text,
                            reply_markup=reply_markup
                        )
                        extract_and_record(photo_path, res)
                        return
                    except Exception:
                        pass
        await target.message.answer(text=text, reply_markup=reply_markup)

    elif isinstance(target, Message):
        if photo_source:
            try:
                res = await target.answer_photo(
                    photo=photo_source,
                    caption=text,
                    reply_markup=reply_markup
                )
                extract_and_record(photo_path, res)
                return
            except Exception:
                if isinstance(photo_source, str) and photo_path.is_file():
                    try:
                        res = await target.answer_photo(
                            photo=FSInputFile(str(photo_path)),
                            caption=text,
                            reply_markup=reply_markup
                        )
                        extract_and_record(photo_path, res)
                        return
                    except Exception:
                        pass
        await target.answer(text=text, reply_markup=reply_markup)


def _get_intensity_label(val: int, lang: str = "ru") -> str:
    return get_intensity_label(val, lang)


def step_1_text(lang: str = "ru") -> str:
    return get_text("step_1_title", lang)


def step_2_text(time_str: str, lang: str = "ru") -> str:
    return get_text("step_2_title", lang, time_str=time_str)


def step_3_text(intensity: int, lang: str = "ru") -> str:
    level = _get_intensity_label(intensity, lang)
    return get_text("step_3_title", lang, intensity=intensity, level=level)


def step_4_text(loc_key: str, lang: str = "ru") -> str:
    loc_map = get_location_map(lang)
    loc_text = loc_map.get(loc_key, loc_key)
    return get_text("step_4_title", lang, loc_text=loc_text)


def step_5_text(pt_key: str, lang: str = "ru") -> str:
    pt_map = get_pain_type_map(lang)
    pt_text = pt_map.get(pt_key, pt_key)
    return get_text("step_5_title", lang, pt_text=pt_text)


def step_6_text(lang: str = "ru") -> str:
    return get_text("step_6_title", lang)


def format_summary(data: Dict[str, Any], lang: str = "ru") -> str:
    intensity = data.get("intensity", 0)
    level = _get_intensity_label(intensity, lang)

    loc_map = get_location_map(lang)
    pt_map = get_pain_type_map(lang)
    sym_map = get_symptoms_map(lang)
    med_map = get_medication_map(lang)

    loc_key = data.get("location", "")
    loc_text = loc_map.get(loc_key, loc_key)

    pt_key = data.get("pain_type", "")
    pt_text = pt_map.get(pt_key, pt_key)

    symptoms_list = data.get("symptoms", [])
    if not symptoms_list or "none" in symptoms_list:
        symptoms_str = "—"
    else:
        symptoms_str = ", ".join(sym_map.get(s, s) for s in symptoms_list)

    med_val = data.get("medication", "none")
    if med_val == "none":
        med_text = med_map.get("none", "Не принимались")
    else:
        med_text = med_map.get(med_val, med_val)

    return (
        get_text("summary_title", lang) +
        get_text("summary_time", lang, start_time=data.get('start_time', '—')) +
        get_text("summary_pain", lang, intensity=intensity, level=level) +
        get_text("summary_location", lang, loc_text=loc_text) +
        get_text("summary_pain_type", lang, pt_text=pt_text) +
        get_text("summary_symptoms", lang, symptoms_str=symptoms_str) +
        get_text("summary_medication", lang, med_text=med_text) +
        get_text("summary_confirm", lang)
    )


# --- Cancel Command & Handlers ---
@router.message(Command("cancel"))
@router.message(F.text.casefold().in_([b.casefold() for b in CANCEL_BUTTONS]))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    if current_state is None:
        await message.answer(get_text("no_active_action", lang), reply_markup=get_main_menu_keyboard(lang))
        return

    await state.clear()
    await message.answer(get_text("action_cancelled", lang), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(NavCallback.filter(F.action == "cancel"))
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    await state.clear()

    text = get_text("action_cancelled", lang)
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=None
        )
    except Exception:
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=None
            )
        except Exception:
            pass
    await callback.message.answer(get_text("main_menu_title", lang), reply_markup=get_main_menu_keyboard(lang))


# --- Navigation Back Handler ---
@router.callback_query(NavCallback.filter(F.action == "back"))
async def callback_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    current_state_str = await state.get_state()
    user_id = callback.from_user.id
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(user_id)

    if not current_state_str:
        await callback.message.answer(get_text("main_menu_title", lang), reply_markup=get_main_menu_keyboard(lang))
        return

    # Custom inputs navigation back
    if current_state_str == HeadacheLogSG.custom_start_time.state:
        await state.set_state(HeadacheLogSG.start_time)
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            step_1_text(lang),
            get_start_time_keyboard(lang)
        )
        return

    # Find position in STEP_ORDER
    current_idx = -1
    for idx, st in enumerate(STEP_ORDER):
        if st.state == current_state_str:
            current_idx = idx
            break

    if current_idx <= 0:
        await state.clear()
        await callback.message.answer(get_text("main_menu_title", lang), reply_markup=get_main_menu_keyboard(lang))
        return

    prev_state = STEP_ORDER[current_idx - 1]
    await state.set_state(prev_state)

    if prev_state == HeadacheLogSG.start_time:
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            step_1_text(lang),
            get_start_time_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.intensity:
        time_str = data.get("start_time", datetime.now().strftime("%Y-%m-%d %H:%M"))
        await show_or_edit_step(
            callback,
            IMG_PAIN_SCALE,
            step_2_text(time_str, lang),
            get_intensity_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.location:
        intensity = data.get("intensity", 5)
        await show_or_edit_step(
            callback,
            IMG_LOCATION,
            step_3_text(intensity, lang),
            get_location_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.pain_type:
        loc_key = data.get("location", "left")
        await show_or_edit_step(
            callback,
            IMG_PAIN_TYPE,
            step_4_text(loc_key, lang),
            get_pain_type_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.symptoms:
        pt_key = data.get("pain_type", "throbbing")
        selected_syms = set(data.get("symptoms", []))
        await show_or_edit_step(
            callback,
            IMG_SYMPTOMS,
            step_5_text(pt_key, lang),
            get_symptoms_keyboard(selected_syms, lang)
        )
    elif prev_state == HeadacheLogSG.medication:
        await show_or_edit_step(
            callback,
            IMG_MEDICATION,
            step_6_text(lang),
            get_medication_keyboard(lang)
        )


# --- Entry Point: Start Logging ---
@router.message(Command("log"))
@router.message(Command("headache"))
@router.message(F.text.in_(LOG_BUTTONS))
async def start_headache_log(message: Message, state: FSMContext):
    user = message.from_user
    lang = "ru"
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        lang = await get_user_language(user.id)

        active = await get_active_episode(user.id)
        if active:
            await message.answer(
                f"Есть незавершенный приступ (начало: <code>{active.get('start_time')}</code>).\n"
                "Завершите его перед началом новой записи.",
            )

    await state.clear()
    await state.update_data(lang=lang)
    await state.set_state(HeadacheLogSG.start_time)
    await show_or_edit_step(
        message,
        IMG_FLOW,
        step_1_text(lang),
        get_start_time_keyboard(lang)
    )


# --- Step 1: Start Time ---
@router.callback_query(HeadacheLogSG.start_time, TimeCallback.filter())
async def process_start_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext):
    await callback.answer()
    now = datetime.now()
    preset = callback_data.preset
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

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
            "<b>Время начала приступа</b>\n"
            "Введите время (например: <code>15:40</code> или <code>вчера в 21:00</code>):"
        )
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            custom_prompt,
            get_cancel_keyboard(show_back=True, lang=lang)
        )
        return
    else:
        time_str = now.strftime("%Y-%m-%d %H:%M")

    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await show_or_edit_step(
        callback,
        IMG_PAIN_SCALE,
        step_2_text(time_str, lang),
        get_intensity_keyboard(lang)
    )


@router.message(HeadacheLogSG.custom_start_time, F.text)
async def process_custom_start_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(message.from_user.id)

    await state.update_data(start_time=time_str)
    await state.set_state(HeadacheLogSG.intensity)
    await show_or_edit_step(
        message,
        IMG_PAIN_SCALE,
        step_2_text(time_str, lang),
        get_intensity_keyboard(lang)
    )


# --- Step 2: Intensity (1-10) ---
@router.callback_query(HeadacheLogSG.intensity, IntensityCallback.filter())
async def process_intensity(callback: CallbackQuery, callback_data: IntensityCallback, state: FSMContext):
    await callback.answer()
    intensity_val = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    await state.update_data(intensity=intensity_val)
    await state.set_state(HeadacheLogSG.location)
    await show_or_edit_step(
        callback,
        IMG_LOCATION,
        step_3_text(intensity_val, lang),
        get_location_keyboard(lang)
    )


# --- Step 3: Location ---
@router.callback_query(HeadacheLogSG.location, LocationCallback.filter())
async def process_location(callback: CallbackQuery, callback_data: LocationCallback, state: FSMContext):
    await callback.answer()
    loc_key = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    await state.update_data(location=loc_key)
    await state.set_state(HeadacheLogSG.pain_type)
    await show_or_edit_step(
        callback,
        IMG_PAIN_TYPE,
        step_4_text(loc_key, lang),
        get_pain_type_keyboard(lang)
    )


# --- Step 4: Pain Type ---
@router.callback_query(HeadacheLogSG.pain_type, PainTypeCallback.filter())
async def process_pain_type(callback: CallbackQuery, callback_data: PainTypeCallback, state: FSMContext):
    await callback.answer()
    pt_key = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    await state.update_data(pain_type=pt_key)
    await state.set_state(HeadacheLogSG.symptoms)
    await state.update_data(symptoms=[])
    await show_or_edit_step(
        callback,
        IMG_SYMPTOMS,
        step_5_text(pt_key, lang),
        get_symptoms_keyboard(set(), lang)
    )


# --- Step 5: Symptoms (Multi-select) ---
@router.callback_query(HeadacheLogSG.symptoms, SymptomCallback.filter())
async def process_symptoms(callback: CallbackQuery, callback_data: SymptomCallback, state: FSMContext):
    await callback.answer()
    action = callback_data.action
    val = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)
    selected = set(data.get("symptoms", []))

    if action == "toggle":
        if "none" in selected:
            selected.remove("none")
        if val in selected:
            selected.remove(val)
        else:
            selected.add(val)
        await state.update_data(symptoms=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_symptoms_keyboard(selected, lang))

    elif action == "none":
        selected = {"none"}
        await state.update_data(symptoms=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_symptoms_keyboard(selected, lang))

    elif action == "done":
        await state.set_state(HeadacheLogSG.medication)
        await show_or_edit_step(
            callback,
            IMG_MEDICATION,
            step_6_text(lang),
            get_medication_keyboard(lang)
        )


# --- Step 6: Medication ---
@router.callback_query(HeadacheLogSG.medication, MedicationCallback.filter())
async def process_medication_skip(callback: CallbackQuery, callback_data: MedicationCallback, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    if callback_data.value == "none":
        await state.update_data(medication="none")
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.confirm)
        await show_or_edit_step(
            callback,
            IMG_FLOW,
            format_summary(data, lang),
            get_confirm_keyboard(lang)
        )


@router.message(HeadacheLogSG.medication, F.text)
async def process_medication_input(message: Message, state: FSMContext):
    med_name = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(message.from_user.id)

    await state.update_data(medication=med_name)
    data = await state.get_data()
    await state.set_state(HeadacheLogSG.confirm)
    await show_or_edit_step(
        message,
        IMG_FLOW,
        format_summary(data, lang),
        get_confirm_keyboard(lang)
    )


# --- Step 7: Confirmation ---
@router.callback_query(HeadacheLogSG.confirm, ConfirmCallback.filter())
async def process_confirmation(callback: CallbackQuery, callback_data: ConfirmCallback, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    if callback_data.action == "cancel":
        await state.clear()
        cancel_text = get_text("action_cancelled", lang)
        try:
            await callback.message.edit_caption(
                caption=cancel_text,
                reply_markup=None
            )
        except Exception:
            try:
                await callback.message.edit_text(
                    text=cancel_text,
                    reply_markup=None
                )
            except Exception:
                pass
        await callback.message.answer(get_text("main_menu_title", lang), reply_markup=get_main_menu_keyboard(lang))
        return

    # Save to database
    episode_id = await create_episode(callback.from_user.id, data)
    await state.clear()

    saved_text = get_text("saved_success", lang, episode_id=episode_id)

    await show_or_edit_step(
        callback,
        IMG_HERO,
        saved_text,
        None
    )
    await callback.message.answer(
        get_text("main_menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
