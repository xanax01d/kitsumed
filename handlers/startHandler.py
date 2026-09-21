import json
from pathlib import Path
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from keyboards.main_menu import get_main_menu_keyboard
from keyboards.headache_kb import LOCATION_MAP, PAIN_TYPE_MAP, ALL_SYMPTOMS, MEDICATION_MAP
from db import upsert_user, get_recent_episodes

# Paths to localized Russian visual banners
BANNER_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "hero_banner.png"
FLOW_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "flow_diagram.png"
DB_PATH = Path(__file__).parent.parent / "assets" / "images" / "ru" / "db_diagram.png"

router = Router()


def _get_intensity_badge(val: int) -> tuple[str, str]:
    if val <= 3:
        return "🟢", "Слабая"
    elif val <= 6:
        return "🟡", "Умеренная"
    elif val <= 8:
        return "🟠", "Сильная"
    else:
        return "🔴", "Невыносимая"


def _format_episode_card(ep: Dict[str, Any]) -> str:
    status = ep.get("status")
    if status == "completed":
        status_badge = "🟢 <i>Завершен</i>"
    else:
        status_badge = "🔴 <b>АКТИВЕН СЕЙЧАС</b>"

    intensity = ep.get("intensity", 0)
    dot, level_name = _get_intensity_badge(intensity)
    filled = min(max(intensity, 0), 10)
    bar = "█" * filled + "░" * (10 - filled)

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

    time_line = f"<code>{ep.get('start_time')}</code>"
    if ep.get("end_time"):
        time_line += f" → <code>{ep.get('end_time')}</code>"

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"┃ <b>Приступ #{ep.get('id')}</b> • {status_badge}\n"
        f"┃ 🗓 {time_line}\n"
        f"┃ 💥 <b>Боль:</b> <b>{intensity}/10</b> {dot} <code>[{bar}]</code>\n"
        f"┃ 📍 <b>Локация:</b> {loc}\n"
        f"┃ ⚡️ <b>Характер:</b> {pt}\n"
        f"┃ 🩺 <b>Симптомы:</b> {sym_str}\n"
        f"┃ 💊 <b>Препарат:</b> <b>{med}</b>\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@router.message(Command("start"))
async def start(message: Message):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)

    greeting_name = ""
    if user:
        name_parts = []
        if user.first_name and user.first_name.strip():
            name_parts.append(user.first_name.strip())
        if user.username:
            name_parts.append(f"(@{user.username})")
        if name_parts:
            greeting_name = f", {' '.join(name_parts)}"

    welcome_text = (
        f"👋 <b>Привет{greeting_name}!</b>\n"
        "Добро пожаловать в <b>Migrebot</b> — твой умный дневник головной боли и мигрени.\n\n"
        "💡 <b>Возможности бота:</b>\n"
        "▫️ <b>Быстрая запись:</b> опрос за 30 секунд (сила боли 1–10, локализация, симптомы)\n"
        "▫️ <b>Учет лекарств:</b> точная фиксация препаратов и дозировок\n"
        "▫️ <b>Хронометраж:</b> расчет точной продолжительности каждого приступа\n"
        "▫️ <b>Медицинский экспорт:</b> отчеты в <b>PDF</b> и <b>Excel/CSV</b> для невролога\n\n"
        "<i>Нажмите <b>«🤕 Записать приступ»</b> в меню ниже, чтобы зафиксировать боль.</i>"
    )

    if BANNER_PATH.is_file():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(BANNER_PATH)),
                caption=welcome_text,
                reply_markup=get_main_menu_keyboard()
            )
            return
        except Exception:
            pass

    await message.answer(text=welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Справка")
async def help_command(message: Message):
    help_text = (
        "📖 <b>Справка и навигация по Migrebot:</b>\n\n"
        "• <b>🤕 Записать приступ</b> (<code>/log</code>) — пошаговый опрос о текущей боли.\n"
        "• <b>⏹ Завершить приступ</b> (<code>/finish</code>) — зафиксировать окончание боли и время.\n"
        "• <b>📊 Мои приступы</b> — последние записи из дневника в виде наглядных карточек.\n"
        "• <b>📥 Экспорт отчета</b> (<code>/export</code>) — скачать отчет для врача (PDF) или таблицу (CSV).\n"
        "• <b>/cancel</b> — прервать текущий опрос в любой момент.\n\n"
        "💡 <i>Дневник позволяет врачу-неврологу поставить точный диагноз (мигрень, ГБН, кластерная боль) и подобрать эффективную терапию.</i>"
    )

    if FLOW_PATH.is_file():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(FLOW_PATH)),
                caption=help_text,
                reply_markup=get_main_menu_keyboard()
            )
            return
        except Exception:
            pass

    await message.answer(text=help_text, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "📊 Мои приступы")
async def view_history(message: Message):
    user = message.from_user
    episodes = await get_recent_episodes(user.id, limit=5)

    if not episodes:
        empty_text = (
            "📭 <b>В дневнике пока нет сохраненных записей о приступах.</b>\n\n"
            "Чтобы добавить первую запись, нажмите <b>«🤕 Записать приступ»</b>."
        )
        if DB_PATH.is_file():
            try:
                await message.answer_photo(
                    photo=FSInputFile(str(DB_PATH)),
                    caption=empty_text,
                    reply_markup=get_main_menu_keyboard()
                )
                return
            except Exception:
                pass
        await message.answer(empty_text, reply_markup=get_main_menu_keyboard())
        return

    cards = [_format_episode_card(ep) for ep in episodes]
    header = "📊 <b>ПОСЛЕДНИЕ ПРИСТУПЫ В ДНЕВНИКЕ:</b>\n\n"
    footer = "\n\n📥 <i>Для выгрузки всех записей нажмите «📥 Экспорт отчета».</i>"
    full_text = header + "\n\n".join(cards) + footer

    if DB_PATH.is_file():
        try:
            if len(full_text) <= 1024:
                await message.answer_photo(
                    photo=FSInputFile(str(DB_PATH)),
                    caption=full_text,
                    reply_markup=get_main_menu_keyboard()
                )
                return
            else:
                await message.answer_photo(
                    photo=FSInputFile(str(DB_PATH)),
                    caption="📊 <b>Дневник головных болей — История приступов</b>"
                )
                await message.answer(full_text, reply_markup=get_main_menu_keyboard())
                return
        except Exception:
            pass

    await message.answer(full_text, reply_markup=get_main_menu_keyboard())
