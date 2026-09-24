import json
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from keyboards.main_menu import get_main_menu_keyboard
from keyboards.headache_kb import LOCATION_MAP, PAIN_TYPE_MAP, ALL_SYMPTOMS, MEDICATION_MAP
from db import upsert_user, get_recent_episodes
from services.media_cache import get_photo_source, extract_and_record

# Paths to localized Russian visual banners
BANNER_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "hero_banner.png"
FLOW_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "flow_diagram.png"
DB_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "db_diagram.png"

router = Router()




def _format_episode_card(ep: Dict[str, Any]) -> str:
    status = ep.get("status")
    status_str = "Завершен" if status == "completed" else "Активен"

    intensity = ep.get("intensity", 0)
    level_name = "Слабая" if intensity <= 3 else ("Умеренная" if intensity <= 6 else ("Сильная" if intensity <= 8 else "Невыносимая"))

    loc = LOCATION_MAP.get(ep.get("location"), ep.get("location"))
    pt = PAIN_TYPE_MAP.get(ep.get("pain_type"), ep.get("pain_type"))

    symptoms_raw = ep.get("symptoms", [])
    if isinstance(symptoms_raw, str):
        try:
            symptoms_raw = json.loads(symptoms_raw)
        except Exception:
            symptoms_raw = [symptoms_raw]
    if not symptoms_raw or "none" in symptoms_raw:
        sym_str = "—"
    else:
        sym_str = ", ".join(ALL_SYMPTOMS.get(s, s) for s in symptoms_raw)

    med = ep.get("medication") or "Не принимались"
    if med == "none":
        med = "Не принимались"
    med = MEDICATION_MAP.get(med, med)

    time_line = f"{ep.get('start_time')}"
    if ep.get("end_time"):
        time_line += f" → {ep.get('end_time')}"

    return (
        f"<b>Приступ #{ep.get('id')}</b> ({status_str})\n"
        f"• Время: <code>{time_line}</code>\n"
        f"• Боль: <b>{intensity}/10</b> ({level_name})\n"
        f"• Локация: {loc} | {pt}\n"
        f"• Симптомы: {sym_str}\n"
        f"• Препарат: {med}"
    )


@router.message(Command("start"))
async def start(message: Message):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)

    welcome_text = (
        "<b>Migrebot</b> — дневник головной боли и мигрени.\n\n"
        "Нажмите <b>«🤕 Записать приступ»</b>, чтобы зафиксировать боль."
    )

    if BANNER_PATH.is_file():
        photo_src = get_photo_source(BANNER_PATH)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=welcome_text,
                reply_markup=get_main_menu_keyboard()
            )
            extract_and_record(BANNER_PATH, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(BANNER_PATH)),
                        caption=welcome_text,
                        reply_markup=get_main_menu_keyboard()
                    )
                    extract_and_record(BANNER_PATH, res)
                    return
                except Exception:
                    pass

    await message.answer(text=welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Справка")
async def help_command(message: Message):
    help_text = (
        "<b>Команды бота:</b>\n\n"
        "• <b>/log</b> — записать приступ\n"
        "• <b>/finish</b> — завершить активный приступ\n"
        "• <b>/export</b> — выгрузить отчет (PDF / CSV)\n"
        "• <b>/reminder</b> — настроить ежедневный опрос\n"
        "• <b>/cancel</b> — отмена действия"
    )

    if FLOW_PATH.is_file():
        photo_src = get_photo_source(FLOW_PATH)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=help_text,
                reply_markup=get_main_menu_keyboard()
            )
            extract_and_record(FLOW_PATH, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(FLOW_PATH)),
                        caption=help_text,
                        reply_markup=get_main_menu_keyboard()
                    )
                    extract_and_record(FLOW_PATH, res)
                    return
                except Exception:
                    pass

    await message.answer(text=help_text, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "📊 Мои приступы")
async def view_history(message: Message):
    user = message.from_user
    episodes = await get_recent_episodes(user.id, limit=5)

    if not episodes:
        empty_text = "В дневнике пока нет сохраненных записей."
        if DB_PATH.is_file():
            photo_src = get_photo_source(DB_PATH)
            try:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption=empty_text,
                    reply_markup=get_main_menu_keyboard()
                )
                extract_and_record(DB_PATH, res)
                return
            except Exception:
                if isinstance(photo_src, str):
                    try:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption=empty_text,
                            reply_markup=get_main_menu_keyboard()
                        )
                        extract_and_record(DB_PATH, res)
                        return
                    except Exception:
                        pass
        await message.answer(empty_text, reply_markup=get_main_menu_keyboard())
        return

    cards = [_format_episode_card(ep) for ep in episodes]
    header = "<b>История приступов:</b>\n\n"
    full_text = header + "\n\n".join(cards)

    if DB_PATH.is_file():
        photo_src = get_photo_source(DB_PATH)
        try:
            if len(full_text) <= 1024:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption=full_text,
                    reply_markup=get_main_menu_keyboard()
                )
                extract_and_record(DB_PATH, res)
                return
            else:
                res = await message.answer_photo(
                    photo=photo_src,
                    caption="📊 <b>Дневник головных болей — История приступов</b>"
                )
                extract_and_record(DB_PATH, res)
                await message.answer(full_text, reply_markup=get_main_menu_keyboard())
                return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    if len(full_text) <= 1024:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption=full_text,
                            reply_markup=get_main_menu_keyboard()
                        )
                        extract_and_record(DB_PATH, res)
                        return
                    else:
                        res = await message.answer_photo(
                            photo=FSInputFile(str(DB_PATH)),
                            caption="📊 <b>Дневник головных болей — История приступов</b>"
                        )
                        extract_and_record(DB_PATH, res)
                        await message.answer(full_text, reply_markup=get_main_menu_keyboard())
                        return
                except Exception:
                    pass

    await message.answer(full_text, reply_markup=get_main_menu_keyboard())
