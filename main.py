import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio import Redis

from handlers import startHandler, headache, exportHandler
from db import init_db, close_db

# Load environment variables
load_dotenv()
token = str(os.getenv("TOKEN"))


def get_redis_client() -> Redis:
    """Creates an async Redis client from environment variables."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return Redis.from_url(redis_url)

    host = os.getenv("RedisIP") or os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("RedisPort") or os.getenv("REDIS_PORT", 6379))
    password = os.getenv("RedisPassword") or os.getenv("REDIS_PASSWORD") or None

    return Redis(host=host, port=port, password=password)


def get_fsm_storage(redis_client: Redis) -> RedisStorage:
    """Configures Redis FSM storage for aiogram."""
    return RedisStorage(
        redis=redis_client,
        key_builder=DefaultKeyBuilder(with_bot_id=True)
    )


async def main() -> None:
    # 1. Initialize PostgreSQL database
    logging.info("Initializing PostgreSQL database...")
    await init_db()

    # 2. Setup Redis FSM storage
    logging.info("Connecting to Redis for FSM storage...")
    redis_client = get_redis_client()
    try:
        await redis_client.ping()
        logging.info("Connected to Redis successfully.")
    except Exception as e:
        logging.warning(f"Could not ping Redis ({e}). Please verify Redis connection settings.")

    storage = get_fsm_storage(redis_client)

    # 3. Create Dispatcher with Redis storage
    dp = Dispatcher(storage=storage)
    dp.include_router(startHandler.router)
    dp.include_router(headache.router)
    dp.include_router(exportHandler.router)

    # 4. Create Bot instance
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("Bot started successfully and is polling for updates...")
    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Shutting down resources...")
        await close_db()
        await redis_client.aclose()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
