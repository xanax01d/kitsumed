from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from db import get_user_language, set_user_language, upsert_user
from keyboards.headache_kb import LanguageCallback, get_language_keyboard
from keyboards.main_menu import get_main_menu_keyboard, LANGUAGE_BUTTONS
from locales import get_text, SUPPORTED_LANGUAGES

router = Router()


@router.message(Command("language"))
@router.message(Command("lang"))
@router.message(F.text.in_(LANGUAGE_BUTTONS))
async def cmd_select_language(message: Message):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
        lang = await get_user_language(user.id)
    else:
        lang = "ru"

    text = get_text("lang_menu_title", lang)
    keyboard = get_language_keyboard(current_lang=lang)
    await message.answer(text=text, reply_markup=keyboard)


@router.callback_query(LanguageCallback.filter())
async def process_language_choice(callback: CallbackQuery, callback_data: LanguageCallback):
    new_lang = callback_data.code
    user = callback.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name, language=new_lang)
        await set_user_language(user.id, new_lang)

    success_text = get_text("lang_changed", new_lang)
    await callback.answer(f"Language: {new_lang.upper()}")

    try:
        await callback.message.edit_text(
            text=success_text,
            reply_markup=None
        )
    except Exception:
        try:
            await callback.message.edit_caption(
                caption=success_text,
                reply_markup=None
            )
        except Exception:
            await callback.message.answer(text=success_text)

    # Send updated main menu in new language
    await callback.message.answer(
        text=get_text("main_menu_title", new_lang),
        reply_markup=get_main_menu_keyboard(new_lang)
    )
