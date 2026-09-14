import json
import zoneinfo
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from keyboards.main_menu import (
    get_main_menu_keyboard,
    HISTORY_BUTTONS,
    HELP_BUTTONS,
)
from keyboards.calendar_kb import (
    CalendarCallback,
    build_calendar_keyboard,
    get_month_name,
)
from db import (
    upsert_user,
    get_recent_episodes,
    get_user_language,
    get_episodes_for_month,
    get_episodes_for_date,
    extract_episode_date,
    get_user_reminder,
)
from services.media_cache import get_photo_source, extract_and_record, get_localized_asset
from locales import (
    get_text,
    get_intensity_label,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
    get_triggers_map,
)

BANNER_PATH = get_localized_asset("hero_banner.png", "ru")
FLOW_PATH = get_localized_asset("flow_diagram.png", "ru")
HISTORY_PATH = get_localized_asset("history.png", "ru")

router = Router()


def _format_episode_card(ep: Dict[str, Any], lang: str = "ru") -> str:
    status = ep.get("status")
    if status == "completed":
        status_str = get_text("history_card_status_completed", lang)
    elif status == "not_resolved":
        status_str = get_text("history_card_status_not_resolved", lang)
    else:
        status_str = get_text("history_card_status_active", lang)

    intensity = ep.get("intensity", 0)
    level_name = get_intensity_label(intensity, lang)

    loc_map = get_location_map(lang)
    pt_map = get_pain_type_map(lang)
    sym_map = get_symptoms_map(lang)
    med_map = get_medication_map(lang)
    trig_map = get_triggers_map(lang)

    loc = loc_map.get(ep.get("location"), ep.get("location"))
    pt = pt_map.get(ep.get("pain_type"), ep.get("pain_type"))

    symptoms_raw = ep.get("symptoms", [])
    if isinstance(symptoms_raw, str):
        try:
            symptoms_raw = json.loads(symptoms_raw)
        except Exception:
            symptoms_raw = [symptoms_raw]
    if not symptoms_raw or "none" in symptoms_raw:
        sym_str = "—"
    else:
        sym_str = ", ".join(sym_map.get(s, s) for s in symptoms_raw)

    triggers_raw = ep.get("triggers", [])
    if isinstance(triggers_raw, str):
        try:
            triggers_raw = json.loads(triggers_raw)
        except Exception:
            triggers_raw = [triggers_raw]
    if not triggers_raw or "none" in triggers_raw:
        trig_str = "—"
    else:
        trig_str = ", ".join(trig_map.get(t, t) for t in triggers_raw)

    med = ep.get("medication") or "none"
    if med == "none":
        med_str = med_map.get("none", "Не принимались")
    else:
        med_str = med_map.get(med, med)

    # If medication relief was recorded, show it
    relief = ep.get("medication_relief")
    if relief:
        if relief == "helped":
            med_str += f" ({get_text('fu_med_helped', lang)})"
        elif relief == "partially":
            med_str += f" ({get_text('fu_med_partially', lang)})"
        elif relief == "not_helped":
            med_str += f" ({get_text('fu_med_not_helped', lang)})"

    time_line = f"{ep.get('start_time')}"
    if ep.get("end_time"):
        time_line += f" → {ep.get('end_time')}"

    return (
        f"<b>{get_text('history_card_header', lang, id=ep.get('id'), status=status_str)}</b>\n"
        f"{get_text('history_card_time', lang, time=time_line)}"
        f"{get_text('history_card_pain', lang, intensity=intensity, level=level_name)}"
        f"{get_text('history_card_loc', lang, loc=loc, pt=pt)}"
        f"{get_text('history_card_sym', lang, sym=sym_str)}"
        f"{get_text('history_card_triggers', lang, triggers=trig_str)}"
        f"{get_text('history_card_med', lang, med=med_str)}"
    )


@router.message(Command("start"))
async def start(message: Message):
    user = message.from_user
    lang = "ru"
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        lang = await get_user_language(user.id)

    welcome_text = get_text("start_welcome", lang)
    main_kb = get_main_menu_keyboard(lang)
    banner_img = get_localized_asset("hero_banner.png", lang)

    if banner_img.is_file():
        photo_src = get_photo_source(banner_img)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=welcome_text,
                reply_markup=main_kb
            )
            extract_and_record(banner_img, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(banner_img)),
                        caption=welcome_text,
                        reply_markup=main_kb
                    )
                    extract_and_record(banner_img, res)
                    return
                except Exception:
                    pass

    await message.answer(text=welcome_text, reply_markup=main_kb)


@router.message(Command("help"))
@router.message(F.text.in_(HELP_BUTTONS))
async def help_command(message: Message):
    user = message.from_user
    lang = await get_user_language(user.id) if user else "ru"
    help_text = get_text("help_text", lang)
    main_kb = get_main_menu_keyboard(lang)
    flow_img = get_localized_asset("flow_diagram.png", lang)

    if flow_img.is_file():
        photo_src = get_photo_source(flow_img)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=help_text,
                reply_markup=main_kb
            )
            extract_and_record(flow_img, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(flow_img)),
                        caption=help_text,
                        reply_markup=main_kb
                    )
                    extract_and_record(flow_img, res)
                    return
                except Exception:
                    pass

    await message.answer(text=help_text, reply_markup=main_kb)


async def _render_calendar_view(user_id: int, year: int, month: int, lang: str):
    user_rem = await get_user_reminder(user_id)
    tz_name = user_rem.get("timezone", "Europe/Moscow")
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
        today = datetime.now(tz).date()
    except Exception:
        today = datetime.now().date()

    episodes = await get_episodes_for_month(user_id, year, month)
    pain_days = set()
    for ep in episodes:
        ep_date = extract_episode_date(ep)
        if ep_date and ep_date.year == year and ep_date.month == month:
            pain_days.add(ep_date.day)

    kb, pain_count, healthy_count = build_calendar_keyboard(year, month, pain_days, today, lang)
    month_name = get_month_name(year, month, lang)
    caption = get_text(
        "calendar_title",
        lang,
        month_name=month_name,
        year=year,
        pain_days=pain_count,
        healthy_days=healthy_count
    )
    return caption, kb


@router.message(Command("history"))
@router.message(F.text.in_(HISTORY_BUTTONS))
async def view_history(message: Message):
    user = message.from_user
    lang = await get_user_language(user.id) if user else "ru"
    history_img = get_localized_asset("history.png", lang)

    user_rem = await get_user_reminder(user.id)
    tz_name = user_rem.get("timezone", "Europe/Moscow")
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
        today = datetime.now(tz).date()
    except Exception:
        today = datetime.now().date()

    caption, cal_kb = await _render_calendar_view(user.id, today.year, today.month, lang)

    if history_img.is_file():
        photo_src = get_photo_source(history_img)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=caption,
                reply_markup=cal_kb
            )
            extract_and_record(history_img, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(history_img)),
                        caption=caption,
                        reply_markup=cal_kb
                    )
                    extract_and_record(history_img, res)
                    return
                except Exception:
                    pass

    await message.answer(caption, reply_markup=cal_kb)


@router.callback_query(CalendarCallback.filter())
async def process_calendar_callback(callback: CallbackQuery, callback_data: CalendarCallback):
    action = callback_data.action
    user = callback.from_user
    lang = await get_user_language(user.id) if user else "ru"

    if action in ("prev", "next", "today", "back"):
        year = callback_data.year
        month = callback_data.month
        if action == "today" or year == 0 or month == 0:
            user_rem = await get_user_reminder(user.id)
            tz_name = user_rem.get("timezone", "Europe/Moscow")
            try:
                tz = zoneinfo.ZoneInfo(tz_name)
                today = datetime.now(tz).date()
            except Exception:
                today = datetime.now().date()
            year, month = today.year, today.month

        caption, cal_kb = await _render_calendar_view(user.id, year, month, lang)
        await callback.answer()
        try:
            await callback.message.edit_caption(caption=caption, reply_markup=cal_kb)
            return
        except Exception:
            try:
                await callback.message.edit_text(text=caption, reply_markup=cal_kb)
                return
            except Exception:
                pass

    elif action == "day":
        await callback.answer()
        year, month, day = callback_data.year, callback_data.month, callback_data.day
        date_str = f"{day:02d}.{month:02d}.{year}"
        episodes = await get_episodes_for_date(user.id, year, month, day)

        back_builder = InlineKeyboardBuilder()
        back_builder.row(
            InlineKeyboardButton(
                text=get_text("calendar_btn_back", lang),
                callback_data=CalendarCallback(action="back", year=year, month=month).pack()
            )
        )

        if episodes:
            cards = [_format_episode_card(ep, lang) for ep in episodes]
            header = get_text("calendar_day_episodes_title", lang, date_str=date_str, count=len(episodes))
            day_text = header + "\n\n".join(cards)
        else:
            day_text = get_text("calendar_day_healthy", lang, date_str=date_str)

        if len(day_text) > 1024:
            day_text = day_text[:1020] + "..."

        try:
            await callback.message.edit_caption(caption=day_text, reply_markup=back_builder.as_markup())
            return
        except Exception:
            try:
                await callback.message.edit_text(text=day_text, reply_markup=back_builder.as_markup())
                return
            except Exception:
                pass

    elif action == "future":
        await callback.answer(get_text("calendar_future_alert", lang), show_alert=False)

    elif action == "ignore":
        await callback.answer()
