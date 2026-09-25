from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db import (
    get_active_episode,
    get_episode_by_id,
    resolve_episode_pain,
    update_medication_relief,
    get_user_language,
)
from keyboards.headache_kb import (
    FollowUpCallback,
    get_followup_pain_keyboard,
    get_followup_when_keyboard,
    get_followup_medication_keyboard,
    get_cancel_keyboard,
)
from keyboards.main_menu import get_main_menu_keyboard, STATUS_BUTTONS
from states.followup import FollowUpSG
from locales import get_text

router = Router()


def _calculate_end_time(preset: str) -> str:
    now = datetime.now()
    if preset == "now":
        return now.strftime("%Y-%m-%d %H:%M")
    elif preset == "-30m":
        return (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
    elif preset == "-1h":
        return (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    elif preset == "-2h":
        return (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    return now.strftime("%Y-%m-%d %H:%M")


@router.message(Command("status"))
@router.message(Command("finish"))
@router.message(F.text.in_(STATUS_BUTTONS))
async def cmd_check_pain_status(message: Message, state: FSMContext):
    """Initiates inquiry about whether pain resolved and medication efficacy."""
    await state.clear()
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    active = await get_active_episode(user_id)

    if not active:
        await message.answer(
            get_text("fu_no_active", lang),
            reply_markup=get_main_menu_keyboard(lang),
        )
        return

    ep_id = active["id"]
    text = get_text("fu_pain_question", lang)
    keyboard = get_followup_pain_keyboard(ep_id, lang)
    await message.answer(text=text, reply_markup=keyboard)


@router.callback_query(FollowUpCallback.filter(F.action == "pain_passed"))
async def process_pain_passed(callback: CallbackQuery, callback_data: FollowUpCallback):
    """User states the pain passed: ask when it stopped."""
    await callback.answer()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    ep_id = callback_data.episode_id

    text = get_text("fu_when_question", lang)
    keyboard = get_followup_when_keyboard(ep_id, lang)

    try:
        await callback.message.edit_text(text=text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        except Exception:
            await callback.message.answer(text=text, reply_markup=keyboard)


@router.callback_query(FollowUpCallback.filter(F.action == "pain_not_passed"))
async def process_pain_not_passed(callback: CallbackQuery, callback_data: FollowUpCallback):
    """User states pain did not pass: record as not resolved and inquire about medication if taken."""
    await callback.answer()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    ep_id = callback_data.episode_id

    # Record in database that pain has NOT passed
    await resolve_episode_pain(ep_id, pain_passed=False)

    ep = await get_episode_by_id(ep_id)
    has_meds = ep and ep.get("medication") and ep["medication"] not in ("none", "Не принимались", "")
    relief_recorded = ep and ep.get("medication_relief") is not None

    if has_meds and not relief_recorded:
        # Inquire if medication helped
        med_text = ep["medication"]
        prompt = get_text("fu_med_question", lang, medication=med_text)
        kb = get_followup_medication_keyboard(ep_id, lang)
        try:
            await callback.message.edit_text(text=prompt, reply_markup=kb)
        except Exception:
            await callback.message.answer(text=prompt, reply_markup=kb)
    else:
        text = get_text("fu_pain_not_resolved_recorded", lang)
        try:
            await callback.message.edit_text(text=text, reply_markup=None)
        except Exception:
            await callback.message.answer(text=text)
        await callback.message.answer(
            get_text("main_menu_title", lang),
            reply_markup=get_main_menu_keyboard(lang),
        )


@router.callback_query(FollowUpCallback.filter(F.action == "set_when"))
async def process_set_when(callback: CallbackQuery, callback_data: FollowUpCallback):
    """User selected a preset time when pain stopped."""
    await callback.answer()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    ep_id = callback_data.episode_id
    end_time = _calculate_end_time(callback_data.value)

    # Save resolution in database
    await resolve_episode_pain(ep_id, pain_passed=True, end_time=end_time)

    ep = await get_episode_by_id(ep_id)
    has_meds = ep and ep.get("medication") and ep["medication"] not in ("none", "Не принимались", "")
    relief_recorded = ep and ep.get("medication_relief") is not None

    resolved_msg = get_text("fu_pain_resolved_recorded", lang, end_time=end_time)

    if has_meds and not relief_recorded:
        med_text = ep["medication"]
        med_prompt = get_text("fu_med_question", lang, medication=med_text)
        full_text = f"{resolved_msg}\n\n{med_prompt}"
        kb = get_followup_medication_keyboard(ep_id, lang)
        try:
            await callback.message.edit_text(text=full_text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text=full_text, reply_markup=kb)
    else:
        try:
            await callback.message.edit_text(text=resolved_msg, reply_markup=None)
        except Exception:
            await callback.message.answer(text=resolved_msg)
        await callback.message.answer(
            get_text("main_menu_title", lang),
            reply_markup=get_main_menu_keyboard(lang),
        )


@router.callback_query(FollowUpCallback.filter(F.action == "custom_when"))
async def process_custom_when(callback: CallbackQuery, callback_data: FollowUpCallback, state: FSMContext):
    """User wants to enter custom end time as text."""
    await callback.answer()
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    ep_id = callback_data.episode_id

    await state.set_state(FollowUpSG.custom_end_time)
    await state.update_data(followup_episode_id=ep_id)

    prompt = get_text("fu_when_custom_prompt", lang)
    kb = get_cancel_keyboard(show_back=False, lang=lang)

    try:
        await callback.message.edit_text(text=prompt, reply_markup=kb)
    except Exception:
        await callback.message.answer(text=prompt, reply_markup=kb)


@router.message(FollowUpSG.custom_end_time, F.text)
async def process_custom_end_time_input(message: Message, state: FSMContext):
    """Receives user text input for when pain stopped."""
    end_time_text = message.text.strip()
    data = await state.get_data()
    ep_id = data.get("followup_episode_id")
    await state.clear()

    user_id = message.from_user.id
    lang = await get_user_language(user_id)

    if not ep_id:
        active = await get_active_episode(user_id)
        if active:
            ep_id = active["id"]

    if ep_id:
        await resolve_episode_pain(ep_id, pain_passed=True, end_time=end_time_text)
        ep = await get_episode_by_id(ep_id)
        has_meds = ep and ep.get("medication") and ep["medication"] not in ("none", "Не принимались", "")
        relief_recorded = ep and ep.get("medication_relief") is not None

        resolved_msg = get_text("fu_pain_resolved_recorded", lang, end_time=end_time_text)

        if has_meds and not relief_recorded:
            med_text = ep["medication"]
            med_prompt = get_text("fu_med_question", lang, medication=med_text)
            full_text = f"{resolved_msg}\n\n{med_prompt}"
            kb = get_followup_medication_keyboard(ep_id, lang)
            await message.answer(text=full_text, reply_markup=kb)
            return

        await message.answer(resolved_msg)

    await message.answer(
        get_text("main_menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang),
    )


@router.callback_query(FollowUpCallback.filter(F.action == "med_relief"))
async def process_medication_relief(callback: CallbackQuery, callback_data: FollowUpCallback):
    """User records whether medication helped ('helped', 'partially', 'not_helped')."""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    ep_id = callback_data.episode_id
    relief = callback_data.value

    # Store in database
    await update_medication_relief(ep_id, relief)
    await callback.answer(get_text("fu_med_recorded", lang))

    msg_text = get_text("fu_med_recorded", lang)
    try:
        await callback.message.edit_text(text=msg_text, reply_markup=None)
    except Exception:
        try:
            await callback.message.edit_caption(caption=msg_text, reply_markup=None)
        except Exception:
            await callback.message.answer(text=msg_text)

    await callback.message.answer(
        get_text("main_menu_title", lang),
        reply_markup=get_main_menu_keyboard(lang),
    )
