import json
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from keyboards.main_menu import get_main_menu_keyboard
from keyboards.headache_kb import LOCATION_MAP, PAIN_TYPE_MAP, ALL_SYMPTOMS, MEDICATION_MAP
from db import upsert_user, get_recent_episodes

# Creating the Router instance to connect this handler to bot instance
router = Router()


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
        f"👋 <b>Привет{greeting_name}! Я твой личный дневник головных болей</b>, чтобы ты не пришел как его создатель к неврологу как долбоеб!\n\n"
        "💡 <b>Что я умею:</b>\n"
        "• Фиксировать начало, интенсивность, локализацию и характер боли\n"
        "• Отслеживать сопутствующие симптомы (ауру, светобоязнь, тошноту)\n"
        "• Записывать принятые препараты и их эффективность\n"
        "• Вести историю твоих приступов\n"
        "• 📥 <b>Экспортировать готовый медицинский отчет в PDF и таблицу CSV</b> для врача\n\n"
        "Нажми <b>«🤕 Записать приступ»</b>, чтобы сделать первую запись."
    )
    await message.answer(text=welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Справка")
async def help_command(message: Message):
    help_text = (
        "📖 <b>Справка по боту:</b>\n\n"
        "• <b>🤕 Записать приступ</b> (/log) — пошаговый опрос о текущем приступе боли.\n"
        "• <b>⏹ Завершить приступ</b> (/finish) — отметить, что боль утихла, и рассчитать продолжительность.\n"
        "• <b>📊 Мои приступы</b> — просмотреть последние записи из дневника.\n"
        "• <b>📥 Экспорт отчета</b> (/export) — скачать дневник в виде PDF-отчета или CSV-таблицы (Excel).\n"
        "• <b>/cancel</b> — прервать текущий опрос в любой момент.\n\n"
        "<i>Дневник помогает врачу-неврологу поставить точный диагноз (мигрень, ГБН, кластерная боль и т.д.) и подобрать правильную терапию.</i>"
    )
    await message.answer(text=help_text, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "📊 Мои приступы")
async def view_history(message: Message):
    user = message.from_user
    episodes = await get_recent_episodes(user.id, limit=5)

    if not episodes:
        await message.answer(
            "📭 У вас пока нет сохраненных записей о приступах.\n\n"
            "Чтобы добавить первую запись, нажмите «🤕 Записать приступ».",
            reply_markup=get_main_menu_keyboard()
        )
        return

    lines = ["<b>📊 Последние приступы:</b>\n"]
    for i, ep in enumerate(episodes, 1):
        status_icon = "🟢 (завершен)" if ep.get("status") == "completed" else "🔴 (активен)"
        intensity = ep.get("intensity", 0)
        loc = LOCATION_MAP.get(ep.get("location"), ep.get("location"))
        pt = PAIN_TYPE_MAP.get(ep.get("pain_type"), ep.get("pain_type"))

        symptoms_raw = ep.get("symptoms", [])
        if isinstance(symptoms_raw, str):
            try:
                symptoms_raw = json.loads(symptoms_raw)
            except Exception:
                symptoms_raw = [symptoms_raw]
        if not symptoms_raw or "none" in symptoms_raw:
            sym_str = "нет"
        else:
            sym_str = ", ".join(ALL_SYMPTOMS.get(s, s) for s in symptoms_raw)

        med = MEDICATION_MAP.get(ep.get("medication"), ep.get("medication"))

        lines.append(
            f"<b>#{ep.get('id')} — {ep.get('start_time')}</b> {status_icon}\n"
            f"• Сила: <b>{intensity}/10</b> | Локация: {loc}\n"
            f"• Тип: {pt} | Симптомы: {sym_str}\n"
            f"• Препарат: {med}\n"
        )

    lines.append("<i>Для выгрузки всех записей нажмите «📥 Экспорт отчета».</i>")
    await message.answer("\n".join(lines), reply_markup=get_main_menu_keyboard())
