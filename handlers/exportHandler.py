from datetime import datetime
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile
from aiogram.filters import Command

from db import get_all_episodes, get_user_language, get_user_timezone
from keyboards.headache_kb import get_export_keyboard, ExportCallback
from keyboards.main_menu import get_main_menu_keyboard, EXPORT_BUTTONS
from services import generate_csv, generate_pdf, get_tz_now
from services.media_cache import get_localized_asset, get_photo_source, extract_and_record
from locales import get_text

IMG_EXPORT = get_localized_asset("export.png", "ru")

router = Router()


@router.message(Command("export"))
@router.message(F.text.in_(EXPORT_BUTTONS))
async def cmd_export(message: Message):
    user = message.from_user
    lang = await get_user_language(user.id) if user else "ru"
    episodes = await get_all_episodes(user.id)

    if not episodes:
        await message.answer(
            get_text("export_empty", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return

    text = get_text("export_title", lang, count=len(episodes))
    kb = get_export_keyboard(lang)
    export_img = get_localized_asset("export.png", lang)

    if export_img.is_file():
        photo_src = get_photo_source(export_img)
        try:
            res = await message.answer_photo(
                photo=photo_src,
                caption=text,
                reply_markup=kb
            )
            extract_and_record(export_img, res)
            return
        except Exception:
            if isinstance(photo_src, str):
                try:
                    res = await message.answer_photo(
                        photo=FSInputFile(str(export_img)),
                        caption=text,
                        reply_markup=kb
                    )
                    extract_and_record(export_img, res)
                    return
                except Exception:
                    pass

    await message.answer(text, reply_markup=kb)


@router.callback_query(ExportCallback.filter())
async def process_export_callback(callback: CallbackQuery, callback_data: ExportCallback):
    user = callback.from_user
    lang = await get_user_language(user.id) if user else "ru"
    episodes = await get_all_episodes(user.id)

    if not episodes:
        await callback.message.answer(
            get_text("export_empty", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await callback.answer()
        return

    fmt = callback_data.format
    user_tz = await get_user_timezone(user.id) if user else "Europe/Moscow"
    user_now = get_tz_now(user_tz)
    date_str = user_now.strftime("%Y%m%d_%H%M")
    formatted_now = user_now.strftime("%d.%m.%Y %H:%M")
    name_parts = []
    if user.full_name and user.full_name.strip():
        name_parts.append(user.full_name.strip())
    if user.username:
        name_parts.append(f"(@{user.username})")
    user_name = " ".join(name_parts) if name_parts else f"User {user.id}"

    await callback.answer("Формирую отчет...")

    if fmt in ("csv", "both"):
        csv_bytes = generate_csv(episodes)
        csv_filename = f"migrebot_diary_{date_str}.csv"
        csv_file = BufferedInputFile(csv_bytes, filename=csv_filename)
        await callback.message.answer_document(
            document=csv_file,
            caption=get_text("export_caption_csv", lang, count=len(episodes), date=formatted_now)
        )

    if fmt in ("pdf", "both"):
        pdf_bytes = generate_pdf(episodes, user_title=user_name, tz_name=user_tz)
        pdf_filename = f"migrebot_report_{date_str}.pdf"
        pdf_file = BufferedInputFile(pdf_bytes, filename=pdf_filename)
        await callback.message.answer_document(
            document=pdf_file,
            caption=get_text("export_caption_pdf", lang, count=len(episodes), date=formatted_now)
        )
