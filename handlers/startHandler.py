from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command
#Creating the Router instance to connect this handler to bot instance
router = Router()

@router.message(Command("start"))
async def start(message:Message):
    reply_markup = ReplyKeyboardRemove()
    await message.reply(text = "Привет! Я твой личный дневник головных болей, что бы ты не пришел как его создатель к неврологу как долбоеб!")
