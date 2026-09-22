import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import zoneinfo
    MSK_TZ = zoneinfo.ZoneInfo("Europe/Moscow")
except Exception:
    MSK_TZ = timezone(timedelta(hours=3))

from aiogram import Bot

from db import get_users_due_for_reminder, mark_user_reminded
from keyboards.reminder_kb import get_reminder_prompt_keyboard

logger = logging.getLogger(__name__)


async def reminder_scheduler(bot: Bot) -> None:
    """
    Background worker that runs continuously and dispatches daily check-in
    inquiries to users based on their individual preferred reminder time (MSK).
    """
    logger.info("Reminder background scheduler started.")
    try:
        while True:
            # Sleep until the start of the next minute
            now_utc = datetime.now(timezone.utc)
            seconds_to_next_minute = 60 - now_utc.second
            if seconds_to_next_minute <= 0:
                seconds_to_next_minute = 60
            await asyncio.sleep(seconds_to_next_minute)

            # Current time and date in Moscow timezone (UTC+3)
            now_msk = datetime.now(MSK_TZ)
            time_str = now_msk.strftime("%H:%M")
            date_str = now_msk.strftime("%Y-%m-%d")

            try:
                due_users = await get_users_due_for_reminder(time_str, date_str)
            except Exception as db_err:
                logger.error(f"Error querying users due for reminder: {db_err}")
                await asyncio.sleep(2)
                continue

            if due_users:
                logger.info(f"Found {len(due_users)} user(s) due for daily reminder at {time_str} MSK.")

            for user in due_users:
                user_id = user["user_id"]
                first_name = user.get("first_name") or ""
                greeting = (
                    "Добрый день"
                    if 12 <= now_msk.hour < 18
                    else ("Добрый вечер" if 18 <= now_msk.hour < 23 else "Привет")
                )
                name_str = f", {first_name}" if first_name else ""

                prompt_text = (
                    f"👋 <b>{greeting}{name_str}!</b>\n\n"
                    "Время ежедневной отметки в дневнике:\n"
                    "❓ <b>Болела ли голова сегодня?</b>"
                )

                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=prompt_text,
                        reply_markup=get_reminder_prompt_keyboard()
                    )
                    await mark_user_reminded(user_id, date_str)
                    logger.info(f"Successfully sent daily reminder to user {user_id}.")
                except Exception as send_err:
                    logger.warning(f"Could not send reminder to user {user_id}: {send_err}")
                    # Mark as reminded to avoid repetitive errors if bot is blocked
                    try:
                        await mark_user_reminded(user_id, date_str)
                    except Exception:
                        pass

            # Small cushion to ensure we don't double-trigger the same minute
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        logger.info("Reminder background scheduler received cancellation. Exiting cleanly.")
    except Exception as exc:
        logger.error(f"Unexpected error in reminder scheduler: {exc}", exc_info=True)
