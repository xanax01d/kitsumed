import json
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from keyboards.main_menu import (
    get_main_menu_keyboard,
    HISTORY_BUTTONS,
    HELP_BUTTONS,
)
from db import upsert_user, get_recent_episodes, get_user_language
from services.media_cache import get_photo_source, extract_and_record, get_localized_asset
from locales import (
    get_text,
    get_intensity_label,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
)

BANNER_PATH = get_localized_asset("hero_banner.png", "ru")
FLOW_PATH = get_localized_asset("flow_diagram.png", "ru")
DB_PATH = get_localized_asset("db_diagram.png", "ru")

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


@router.message(F.text.in_(HISTORY_BUTTONS))
async def view_history(message: Message):
    user = message.from_user
    lang = await get_user_language(user.id) if user else "ru"
    main_kb = get_main_menu_keyboard(lang)
    episodes = await get_recent_episodes(user.id, limit=5)

    if not episodes:
        empty_text = get_text("history_empty", lang)
        if DB_PATH.is_file():
            photo_src = get_photo_source(DB_PATH)
            try:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption=empty_text,
                    reply_markup=main_kb
                )
                extract_and_record(DB_PATH, res)
                return
            except Exception:
                if isinstance(photo_src, str):
                    try:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption=empty_text,
                            reply_markup=main_kb
                        )
                        extract_and_record(DB_PATH, res)
                        return
                    except Exception:
                        pass
        await message.answer(empty_text, reply_markup=main_kb)
        return

    cards = [_format_episode_card(ep, lang) for ep in episodes]
    header = get_text("history_title", lang)
    full_text = header + "\n\n".join(cards)

    if DB_PATH.is_file():
        photo_src = get_photo_source(DB_PATH)
        try:
            if len(full_text) <= 1024:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption=full_text,
                    reply_markup=main_kb
                )
                extract_and_record(DB_PATH, res)
                return
            else:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption=header.strip()
                )
                extract_and_record(DB_PATH, res)
                await message.answer(full_text, reply_markup=main_kb)
                return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    if len(full_text) <= 1024:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption=full_text,
                            reply_markup=main_kb
                        )
                        extract_and_record(DB_PATH, res)
                        return
                    else:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption=header.strip()
                        )
                        extract_and_record(DB_PATH, res)
                        await message.answer(full_text, reply_markup=main_kb)
                        return
                except Exception:
                    pass

    await message.answer(full_text, reply_markup=main_kb)
