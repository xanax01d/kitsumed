from datetime import datetime
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from aiogram.filters import Command

from db import get_all_episodes
from keyboards.headache_kb import get_export_keyboard, ExportCallback
from keyboards.main_menu import get_main_menu_keyboard
from services import generate_csv, generate_pdf

IMG_EXPORT = Path(__file__).parent.parent / "assets" / "images" / "ru" / "architecture_diagram.png"

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
        "📥 <b>ЭКСПОРТ ДНЕВНИКА ДЛЯ ВРАЧА</b>\n\n"
        f"Всего зафиксировано приступов: <b>{len(episodes)}</b>.\n"
        "Выберите желаемый формат для выгрузки:\n\n"
        "📄 <b>Медицинский отчет (PDF)</b>\n"
        "• Альбомный формат A4 со сводной клинической таблицей\n"
        "• Включает силу боли, локализацию, тип, симптомы и препараты\n"
        "• Готов для печати или отправки лечащему неврологу\n\n"
        "📊 <b>Таблица данных (Excel / CSV)</b>\n"
        "• Структурированная таблица (кодировка UTF-8 BOM, разделитель «;»)\n"
        "• Удобно открывать в Excel, Numbers и Google Таблицах"
    )

    if IMG_EXPORT.is_file():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(IMG_EXPORT)),
                caption=text,
                reply_markup=get_export_keyboard()
            )
            return
        except Exception:
            pass

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
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    formatted_now = datetime.now().strftime("%d.%m.%Y %H:%M")
    name_parts = []
    if user.full_name and user.full_name.strip():
        name_parts.append(user.full_name.strip())
    if user.username:
        name_parts.append(f"(@{user.username})")
    user_name = " ".join(name_parts) if name_parts else f"User {user.id}"

    await callback.answer("⏳ Формирую отчет...")

    if fmt in ("csv", "both"):
        csv_bytes = generate_csv(episodes)
        csv_filename = f"migrebot_diary_{date_str}.csv"
        csv_file = BufferedInputFile(csv_bytes, filename=csv_filename)
        await callback.message.answer_document(
            document=csv_file,
            caption=f"📊 <b>Дневник головных болей (Excel / CSV)</b>\n\n"
                    f"▫️ Пациент: <b>{user_name}</b>\n"
                    f"▫️ Записей в таблице: <b>{len(episodes)}</b>\n"
                    f"▫️ Дата выгрузки: <code>{formatted_now}</code>\n\n"
                    "<i>Разделитель «;», поддержка кириллицы (UTF-8 with BOM).</i>"
        )

    if fmt in ("pdf", "both"):
        pdf_bytes = generate_pdf(episodes, user_title=user_name)
        pdf_filename = f"migrebot_report_{date_str}.pdf"
        pdf_file = BufferedInputFile(pdf_bytes, filename=pdf_filename)
        await callback.message.answer_document(
            document=pdf_file,
            caption=f"📄 <b>Медицинский отчет по приступам (PDF)</b>\n\n"
                    f"▫️ Пациент: <b>{user_name}</b>\n"
                    f"▫️ Записей в отчете: <b>{len(episodes)}</b>\n"
                    f"▫️ Дата выгрузки: <code>{formatted_now}</code>\n\n"
                    "<i>Формат A4 (альбомная ориентация), готов для показа врачу.</i>"
        )
