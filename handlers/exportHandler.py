from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from db import get_all_episodes
from keyboards.headache_kb import get_export_keyboard, ExportCallback
from keyboards.main_menu import get_main_menu_keyboard
from services import generate_csv, generate_pdf

router = Router()


@router.message(Command("export"))
@router.message(F.text == "📥 Экспорт отчета")
async def cmd_export(message: Message):
    user = message.from_user
    episodes = await get_all_episodes(user.id)

    if not episodes:
        await message.answer(
            "📭 <b>У вас пока нет записей о приступах для экспорта.</b>\n\n"
            "Сделайте хотя бы одну запись с помощью кнопки «🤕 Записать приступ», "
            "после чего вы сможете выгрузить дневник.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    text = (
        f"📊 <b>Экспорт дневника приступов</b>\n\n"
        f"Всего найдено записей: <b>{len(episodes)}</b>.\n"
        "Выберите желаемый формат для выгрузки:\n\n"
        "• <b>PDF</b> — готовый медицинский отчет в виде таблицы (удобно распечатать или показать неврологу).\n"
        "• <b>CSV</b> — таблица для Excel / Google Таблиц для самостоятельного анализа."
    )
    await message.answer(text, reply_markup=get_export_keyboard())


@router.callback_query(ExportCallback.filter())
async def process_export_callback(callback: CallbackQuery, callback_data: ExportCallback):
    user = callback.from_user
    episodes = await get_all_episodes(user.id)

    if not episodes:
        await callback.message.answer(
            "📭 Записей для экспорта не найдено.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    fmt = callback_data.format
    name_parts = []
    if user.full_name and user.full_name.strip():
        name_parts.append(user.full_name.strip())
    if user.username:
        name_parts.append(f"(@{user.username})")
    user_name = " ".join(name_parts) if name_parts else f"User {user.id}"

    await callback.answer("⏳ Формирую файл...")

    if fmt in ("csv", "both"):
        csv_bytes = generate_csv(episodes)
        csv_filename = f"migrebot_diary_{date_str}.csv"
        csv_file = BufferedInputFile(csv_bytes, filename=csv_filename)
        await callback.message.answer_document(
            document=csv_file,
            caption="📊 <b>Ваш дневник головных болей (CSV / Excel)</b>\n"
                    "<i>Кодировка UTF-8 с BOM, разделитель «;» для корректного открытия в Excel.</i>"
        )

    if fmt in ("pdf", "both"):
        pdf_bytes = generate_pdf(episodes, user_title=user_name)
        pdf_filename = f"migrebot_report_{date_str}.pdf"
        pdf_file = BufferedInputFile(pdf_bytes, filename=pdf_filename)
        await callback.message.answer_document(
            document=pdf_file,
            caption="📄 <b>Медицинский отчет по приступам (PDF)</b>\n"
                    "<i>Формат A4 (альбомная ориентация), готов для показа врачу-неврологу.</i>"
        )
