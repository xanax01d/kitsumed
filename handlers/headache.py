import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.headache import HeadacheLogSG
from keyboards.headache_kb import (
    TimeCallback, IntensityCallback, LocationCallback, PainTypeCallback,
    SymptomCallback, TriggerCallback, MedicationCallback, MedicationReliefCallback,
    MedicationTimeCallback, ReliefTimeCallback,
    ConfirmCallback, NavCallback,
    get_start_time_keyboard, get_intensity_keyboard, get_location_keyboard,
    get_pain_type_keyboard, get_symptoms_keyboard, get_triggers_keyboard,
    get_medication_keyboard, get_medication_time_keyboard,
    get_medication_relief_keyboard, get_relief_time_keyboard,
    get_confirm_keyboard, get_cancel_keyboard,
    LOCATION_MAP, PAIN_TYPE_MAP, ALL_SYMPTOMS, MEDICATION_MAP
)
from keyboards.main_menu import get_main_menu_keyboard, LOG_BUTTONS, CANCEL_BUTTONS
from db import create_episode, get_active_episode, upsert_user, get_user_language, get_user_timezone
from services.media_cache import get_photo_source, extract_and_record, get_localized_asset, get_input_media
from services import get_tz_now
from locales import (
    get_text,
    get_intensity_label,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
    get_triggers_map,
)

router = Router()

# Paths to localized step illustration cards
BASE_ASSETS = Path(__file__).parent.parent / "assets" / "images" / "ru"


def get_step_asset(step_name: str, lang: str = "ru") -> Path:
    mapping = {
        "flow": "flow_diagram.png",
        "hero": "hero_banner.png",
        "start_time": "steps/start_time.png",
        "pain_scale": "steps/pain_scale.png",
        "location": "steps/location.png",
        "pain_type": "steps/pain_type.png",
        "symptoms": "steps/symptoms.png",
        "triggers": "steps/symptoms.png",
        "medication": "steps/medication.png",
        "medication_time": "steps/medication.png",
        "relief_time": "steps/saved.png",
        "confirm": "steps/confirm.png",
        "saved": "steps/saved.png",
    }
    rel = mapping.get(step_name, f"steps/{step_name}.png")
    return get_localized_asset(rel, lang)


IMG_FLOW = get_step_asset("flow", "ru")
IMG_HERO = get_step_asset("hero", "ru")
IMG_START_TIME = get_step_asset("start_time", "ru")
IMG_PAIN_SCALE = get_step_asset("pain_scale", "ru")
IMG_LOCATION = get_step_asset("location", "ru")
IMG_PAIN_TYPE = get_step_asset("pain_type", "ru")
IMG_SYMPTOMS = get_step_asset("symptoms", "ru")
IMG_MEDICATION = get_step_asset("medication", "ru")
IMG_CONFIRM = get_step_asset("confirm", "ru")
IMG_SAVED = get_step_asset("saved", "ru")


# --- Navigation History Helper ---
STEP_ORDER = [
    HeadacheLogSG.start_time,
    HeadacheLogSG.intensity,
    HeadacheLogSG.location,
    HeadacheLogSG.pain_type,
    HeadacheLogSG.symptoms,
    HeadacheLogSG.triggers,
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
        if msg and msg.photo and photo_path and photo_path.is_file():
            # Dynamically edit the photo to match the new step's illustration!
            try:
                media = get_input_media(photo_path, caption=text)
                res = await msg.edit_media(media=media, reply_markup=reply_markup)
                extract_and_record(photo_path, res)
                return
            except Exception:
                try:
                    fallback_media = InputMediaPhoto(media=FSInputFile(str(photo_path)), caption=text)
                    res = await msg.edit_media(media=fallback_media, reply_markup=reply_markup)
                    extract_and_record(photo_path, res)
                    return
                except Exception:
                    pass
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


def step_triggers_text(lang: str = "ru") -> str:
    return get_text("step_triggers_title", lang)


def step_6_text(lang: str = "ru") -> str:
    return get_text("step_6_title", lang)


def step_med_time_text(med_name: str, lang: str = "ru") -> str:
    med_map = get_medication_map(lang)
    display_name = med_map.get(med_name, med_name)
    return get_text("med_time_question", lang, medication=display_name)


def step_med_relief_text(med_name: str, lang: str = "ru") -> str:
    med_map = get_medication_map(lang)
    display_name = med_map.get(med_name, med_name)
    return get_text("fu_med_question", lang, medication=display_name)


def step_relief_time_text(lang: str = "ru") -> str:
    return get_text("relief_time_question", lang)


def _parse_delay_minutes(delay_val: Optional[str]) -> int:
    if not delay_val:
        return 0
    val = str(delay_val).strip().lower()
    if val.endswith("m"):
        try:
            return int(val[:-1])
        except ValueError:
            return 0
    elif val.endswith("h"):
        try:
            return int(val[:-1]) * 60
        except ValueError:
            return 0
    try:
        return int(val)
    except ValueError:
        return 0


def _calculate_end_time_and_duration(start_time_str: str, total_minutes: int, lang: str = "ru", tz_name: str = "Europe/Moscow") -> tuple[str, str]:
    try:
        dt_start = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
    except Exception:
        try:
            today = get_tz_now(tz_name).date()
            t = datetime.strptime(start_time_str, "%H:%M").time()
            dt_start = datetime.combine(today, t)
        except Exception:
            dt_start = get_tz_now(tz_name) - timedelta(minutes=total_minutes)

    dt_end = dt_start + timedelta(minutes=total_minutes)
    end_time_str = dt_end.strftime("%Y-%m-%d %H:%M")

    hours = total_minutes // 60
    mins = total_minutes % 60
    if lang == "en":
        if hours > 0 and mins > 0:
            duration_str = f"{hours}h {mins}m"
        elif hours > 0:
            duration_str = f"{hours}h"
        else:
            duration_str = f"{mins}m"
    else:
        if hours > 0 and mins > 0:
            duration_str = f"{hours} ч {mins} мин"
        elif hours > 0:
            duration_str = f"{hours} ч"
        else:
            duration_str = f"{mins} мин"

    return end_time_str, duration_str


def format_summary(data: Dict[str, Any], lang: str = "ru") -> str:
    intensity = data.get("intensity", 0)
    level = _get_intensity_label(intensity, lang)

    loc_map = get_location_map(lang)
    pt_map = get_pain_type_map(lang)
    sym_map = get_symptoms_map(lang)
    med_map = get_medication_map(lang)
    trig_map = get_triggers_map(lang)

    loc_key = data.get("location", "")
    loc_text = loc_map.get(loc_key, loc_key)

    pt_key = data.get("pain_type", "")
    pt_text = pt_map.get(pt_key, pt_key)

    symptoms_list = data.get("symptoms", [])
    if not symptoms_list or "none" in symptoms_list:
        symptoms_str = "—"
    else:
        symptoms_str = ", ".join(sym_map.get(s, s) for s in symptoms_list)

    triggers_list = data.get("triggers", [])
    if not triggers_list or "none" in triggers_list:
        triggers_str = "—"
    else:
        triggers_str = ", ".join(trig_map.get(t, t) for t in triggers_list)

    med_val = data.get("medication", "none")
    if med_val == "none":
        med_text = med_map.get("none", "Не принимались")
    else:
        med_text = med_map.get(med_val, med_val)
        med_relief = data.get("medication_relief")
        if med_relief:
            if med_relief == "helped":
                med_text += f" ({get_text('fu_med_helped', lang)})"
            elif med_relief == "partially":
                med_text += f" ({get_text('fu_med_partially', lang)})"
            elif med_relief == "not_helped":
                med_text += f" ({get_text('fu_med_not_helped', lang)})"

    is_completed = data.get("status") == "completed"
    if is_completed and data.get("end_time"):
        time_section = get_text(
            "summary_time_resolved",
            lang,
            start_time=data.get('start_time', '—'),
            end_time=data.get('end_time', '—'),
            duration=data.get('duration', '—')
        )
        status_section = get_text("summary_status_completed", lang)
    else:
        time_section = get_text("summary_time", lang, start_time=data.get('start_time', '—'))
        status_section = get_text("summary_status_active", lang)

    return (
        get_text("summary_title", lang) +
        status_section +
        time_section +
        get_text("summary_pain", lang, intensity=intensity, level=level) +
        get_text("summary_location", lang, loc_text=loc_text) +
        get_text("summary_pain_type", lang, pt_text=pt_text) +
        get_text("summary_symptoms", lang, symptoms_str=symptoms_str) +
        get_text("summary_triggers", lang, triggers_str=triggers_str) +
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
            get_step_asset("start_time", lang),
            step_1_text(lang),
            get_start_time_keyboard(lang)
        )
        return

    if current_state_str == HeadacheLogSG.custom_trigger.state:
        await state.set_state(HeadacheLogSG.triggers)
        selected_trigs = set(data.get("triggers", []))
        await show_or_edit_step(
            callback,
            get_step_asset("triggers", lang),
            step_triggers_text(lang),
            get_triggers_keyboard(selected_trigs, lang)
        )
        return

    # Special handling for confirm step: check if medication was taken
    if current_state_str == HeadacheLogSG.confirm.state:
        med_val = data.get("medication", "none")
        if med_val and med_val != "none":
            if data.get("status") == "completed" or data.get("medication_relief") == "helped":
                await state.set_state(HeadacheLogSG.relief_time)
                await show_or_edit_step(
                    callback,
                    get_step_asset("relief_time", lang),
                    step_relief_time_text(lang),
                    get_relief_time_keyboard(lang)
                )
                return
            else:
                await state.set_state(HeadacheLogSG.medication_relief)
                await show_or_edit_step(
                    callback,
                    get_step_asset("medication", lang),
                    step_med_relief_text(med_val, lang),
                    get_medication_relief_keyboard(lang)
                )
                return
        else:
            await state.set_state(HeadacheLogSG.medication)
            await show_or_edit_step(
                callback,
                get_step_asset("medication", lang),
                step_6_text(lang),
                get_medication_keyboard(lang)
            )
            return

    # Special handling for relief_time step: go back to medication_relief
    if current_state_str == HeadacheLogSG.relief_time.state:
        med_val = data.get("medication", "")
        await state.set_state(HeadacheLogSG.medication_relief)
        await show_or_edit_step(
            callback,
            get_step_asset("medication", lang),
            step_med_relief_text(med_val, lang),
            get_medication_relief_keyboard(lang)
        )
        return

    # Special handling for medication_relief step: go back to medication_time
    if current_state_str == HeadacheLogSG.medication_relief.state:
        med_val = data.get("medication", "")
        await state.set_state(HeadacheLogSG.medication_time)
        await show_or_edit_step(
            callback,
            get_step_asset("medication_time", lang),
            step_med_time_text(med_val, lang),
            get_medication_time_keyboard(lang)
        )
        return

    # Special handling for medication_time step: go back to medication
    if current_state_str == HeadacheLogSG.medication_time.state:
        await state.set_state(HeadacheLogSG.medication)
        await show_or_edit_step(
            callback,
            get_step_asset("medication", lang),
            step_6_text(lang),
            get_medication_keyboard(lang)
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
            get_step_asset("start_time", lang),
            step_1_text(lang),
            get_start_time_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.intensity:
        time_str = data.get("start_time", datetime.now().strftime("%Y-%m-%d %H:%M"))
        await show_or_edit_step(
            callback,
            get_step_asset("pain_scale", lang),
            step_2_text(time_str, lang),
            get_intensity_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.location:
        intensity = data.get("intensity", 5)
        await show_or_edit_step(
            callback,
            get_step_asset("location", lang),
            step_3_text(intensity, lang),
            get_location_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.pain_type:
        loc_key = data.get("location", "left")
        await show_or_edit_step(
            callback,
            get_step_asset("pain_type", lang),
            step_4_text(loc_key, lang),
            get_pain_type_keyboard(lang)
        )
    elif prev_state == HeadacheLogSG.symptoms:
        pt_key = data.get("pain_type", "throbbing")
        selected_syms = set(data.get("symptoms", []))
        await show_or_edit_step(
            callback,
            get_step_asset("symptoms", lang),
            step_5_text(pt_key, lang),
            get_symptoms_keyboard(selected_syms, lang)
        )
    elif prev_state == HeadacheLogSG.triggers:
        selected_trigs = set(data.get("triggers", []))
        await show_or_edit_step(
            callback,
            get_step_asset("triggers", lang),
            step_triggers_text(lang),
            get_triggers_keyboard(selected_trigs, lang)
        )
    elif prev_state == HeadacheLogSG.medication:
        await show_or_edit_step(
            callback,
            get_step_asset("medication", lang),
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
        get_step_asset("start_time", lang),
        step_1_text(lang),
        get_start_time_keyboard(lang)
    )


# --- Step 1: Start Time ---
@router.callback_query(HeadacheLogSG.start_time, TimeCallback.filter())
async def process_start_time(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext):
    await callback.answer()
    user_tz = await get_user_timezone(callback.from_user.id)
    now = get_tz_now(user_tz)
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
            get_step_asset("start_time", lang),
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
        get_step_asset("pain_scale", lang),
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
        get_step_asset("pain_scale", lang),
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
        get_step_asset("location", lang),
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
        get_step_asset("pain_type", lang),
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
        get_step_asset("symptoms", lang),
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
        await state.set_state(HeadacheLogSG.triggers)
        await state.update_data(triggers=[])
        await show_or_edit_step(
            callback,
            get_step_asset("triggers", lang),
            step_triggers_text(lang),
            get_triggers_keyboard(set(), lang)
        )


# --- Step 5b: Triggers (Multi-select) ---
@router.callback_query(HeadacheLogSG.triggers, TriggerCallback.filter())
async def process_triggers(callback: CallbackQuery, callback_data: TriggerCallback, state: FSMContext):
    await callback.answer()
    action = callback_data.action
    val = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)
    selected = set(data.get("triggers", []))

    if action == "toggle":
        if "none" in selected:
            selected.remove("none")
        if val in selected:
            selected.remove(val)
        else:
            selected.add(val)
            # Mutual exclusion for sleep / oversleep
            if val == "sleep" and "oversleep" in selected:
                selected.remove("oversleep")
            elif val == "oversleep" and "sleep" in selected:
                selected.remove("sleep")
        await state.update_data(triggers=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_triggers_keyboard(selected, lang))

    elif action == "none":
        selected = {"none"}
        await state.update_data(triggers=list(selected))
        await callback.message.edit_reply_markup(reply_markup=get_triggers_keyboard(selected, lang))

    elif action == "custom":
        await state.set_state(HeadacheLogSG.custom_trigger)
        prompt = get_text("custom_trigger_prompt", lang)
        await show_or_edit_step(
            callback,
            get_step_asset("triggers", lang),
            prompt,
            get_cancel_keyboard(show_back=True, lang=lang)
        )

    elif action == "done":
        if not selected:
            selected = {"none"}
        await state.update_data(triggers=list(selected))
        await state.set_state(HeadacheLogSG.medication)
        await show_or_edit_step(
            callback,
            get_step_asset("medication", lang),
            step_6_text(lang),
            get_medication_keyboard(lang)
        )


@router.message(HeadacheLogSG.triggers, F.text)
async def process_trigger_direct_input(message: Message, state: FSMContext):
    trigger_text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(message.from_user.id)
    current_trigs = [t for t in data.get("triggers", []) if t != "none"]
    if trigger_text not in current_trigs:
        current_trigs.append(trigger_text)
    await state.update_data(triggers=current_trigs)
    await state.set_state(HeadacheLogSG.medication)
    await show_or_edit_step(
        message,
        get_step_asset("medication", lang),
        step_6_text(lang),
        get_medication_keyboard(lang)
    )


@router.message(HeadacheLogSG.custom_trigger, F.text)
async def process_custom_trigger_input(message: Message, state: FSMContext):
    trigger_text = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(message.from_user.id)
    current_trigs = [t for t in data.get("triggers", []) if t != "none"]
    if trigger_text not in current_trigs:
        current_trigs.append(trigger_text)
    await state.update_data(triggers=current_trigs)
    await state.set_state(HeadacheLogSG.medication)
    await show_or_edit_step(
        message,
        get_step_asset("medication", lang),
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
        # None taken -> advance straight to confirmation
        await state.update_data(
            medication="none",
            medication_relief=None,
            med_take_delay=None,
            relief_delay=None,
            status="active",
            pain_resolved=False,
            end_time=None,
            duration=None,
        )
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.confirm)
        await show_or_edit_step(
            callback,
            get_step_asset("confirm", lang),
            format_summary(data, lang),
            get_confirm_keyboard(lang)
        )
    else:
        # A medication was selected -> ask when it was taken relative to pain onset!
        med_val = callback_data.value
        await state.update_data(medication=med_val)
        await state.set_state(HeadacheLogSG.medication_time)
        await show_or_edit_step(
            callback,
            get_step_asset("medication_time", lang),
            step_med_time_text(med_val, lang),
            get_medication_time_keyboard(lang)
        )


@router.message(HeadacheLogSG.medication, F.text)
async def process_medication_input(message: Message, state: FSMContext):
    med_name = message.text.strip()
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(message.from_user.id)

    await state.update_data(medication=med_name)
    await state.set_state(HeadacheLogSG.medication_time)
    await show_or_edit_step(
        message,
        get_step_asset("medication_time", lang),
        step_med_time_text(med_name, lang),
        get_medication_time_keyboard(lang)
    )


# --- Step 6b: Medication Intake Time ---
@router.callback_query(HeadacheLogSG.medication_time, MedicationTimeCallback.filter())
async def process_medication_time(callback: CallbackQuery, callback_data: MedicationTimeCallback, state: FSMContext):
    await callback.answer()
    delay_val = callback_data.value
    await state.update_data(med_take_delay=delay_val)
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)
    med_name = data.get("medication", "")

    await state.set_state(HeadacheLogSG.medication_relief)
    await show_or_edit_step(
        callback,
        get_step_asset("medication", lang),
        step_med_relief_text(med_name, lang),
        get_medication_relief_keyboard(lang)
    )


# --- Step 6c: Medication Relief ---
@router.callback_query(HeadacheLogSG.medication_relief, MedicationReliefCallback.filter())
async def process_medication_relief(callback: CallbackQuery, callback_data: MedicationReliefCallback, state: FSMContext):
    await callback.answer()
    relief_val = callback_data.value
    await state.update_data(medication_relief=relief_val)
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)

    if relief_val == "helped":
        # Pain relieved -> ask how long after taking medication
        await state.set_state(HeadacheLogSG.relief_time)
        await show_or_edit_step(
            callback,
            get_step_asset("relief_time", lang),
            step_relief_time_text(lang),
            get_relief_time_keyboard(lang)
        )
    else:
        # Not helped / partially helped -> remains active episode
        await state.update_data(
            status="active",
            pain_resolved=False,
            relief_delay=None,
            end_time=None,
            duration=None,
        )
        data = await state.get_data()
        await state.set_state(HeadacheLogSG.confirm)
        await show_or_edit_step(
            callback,
            get_step_asset("confirm", lang),
            format_summary(data, lang),
            get_confirm_keyboard(lang)
        )


# --- Step 6d: Relief Duration & Calculation ---
@router.callback_query(HeadacheLogSG.relief_time, ReliefTimeCallback.filter())
async def process_relief_time(callback: CallbackQuery, callback_data: ReliefTimeCallback, state: FSMContext):
    await callback.answer()
    relief_delay = callback_data.value
    data = await state.get_data()
    lang = data.get("lang") or await get_user_language(callback.from_user.id)
    user_tz = await get_user_timezone(callback.from_user.id)
    med_take_delay = data.get("med_take_delay", "0m")
    total_minutes = _parse_delay_minutes(med_take_delay) + _parse_delay_minutes(relief_delay)
    start_time_str = data.get("start_time", get_tz_now(user_tz).strftime("%Y-%m-%d %H:%M"))
    end_time_str, duration_str = _calculate_end_time_and_duration(start_time_str, total_minutes, lang, user_tz)

    await state.update_data(
        relief_delay=relief_delay,
        status="completed",
        pain_resolved=True,
        end_time=end_time_str,
        duration=duration_str,
    )
    data = await state.get_data()
    await state.set_state(HeadacheLogSG.confirm)
    await show_or_edit_step(
        callback,
        get_step_asset("confirm", lang),
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

    if data.get("status") == "completed":
        saved_text = get_text(
            "saved_completed_success",
            lang,
            episode_id=episode_id,
            duration=data.get("duration", "—")
        )
    else:
        saved_text = get_text("saved_success", lang, episode_id=episode_id)

    await show_or_edit_step(
        callback,
        get_step_asset("saved", lang),
        saved_text,
        None
    )
    await callback.message.answer(
        get_text("main_menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
