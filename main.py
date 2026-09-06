import asyncio
from aiogram import Bot,Dispatcher,html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
import logging
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from os import getenv

from handlers import startHandler

#Get a token of bot from .env file
load_dotenv()
token = str(getenv('TOKEN'))
#Creating a dispatcher instance
dp = Dispatcher()
dp.include_router(startHandler.router)

async def main() -> None:
    bot = Bot(token=token,default = DefaultBotProperties(parse_mode = ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
