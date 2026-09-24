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

from db import get_enabled_reminder_users, mark_user_reminded
from keyboards.reminder_kb import get_reminder_prompt_keyboard

logger = logging.getLogger(__name__)


async def reminder_scheduler(bot: Bot) -> None:
    """
    Background worker that runs continuously and dispatches daily check-in
    inquiries to users based on their individual preferred reminder time and timezone.
    """
    logger.info("Reminder background scheduler started (per-user timezone aware).")
    try:
        while True:
            # Sleep until the start of the next minute
            now_utc = datetime.now(timezone.utc)
            seconds_to_next_minute = 60 - now_utc.second
            if seconds_to_next_minute <= 0:
                seconds_to_next_minute = 60
            await asyncio.sleep(seconds_to_next_minute)

            now_utc = datetime.now(timezone.utc)

            try:
                users = await get_enabled_reminder_users()
            except Exception as db_err:
                logger.error(f"Error querying enabled reminder users: {db_err}")
                await asyncio.sleep(2)
                continue

            for user in users:
                user_id = user["user_id"]
                target_time = user.get("reminder_time") or "21:00"
                tz_name = user.get("timezone") or "Europe/Moscow"
                last_date = user.get("last_reminded_date")

                try:
                    user_tz = zoneinfo.ZoneInfo(tz_name)
                except Exception:
                    user_tz = MSK_TZ

                user_now = now_utc.astimezone(user_tz)
                user_time_str = user_now.strftime("%H:%M")
                user_date_str = user_now.strftime("%Y-%m-%d")

                if user_time_str == target_time:
                    if last_date is None or str(last_date) < user_date_str:
                        prompt_text = "<b>Болела ли голова сегодня?</b>"

                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=prompt_text,
                                reply_markup=get_reminder_prompt_keyboard()
                            )
                            await mark_user_reminded(user_id, user_date_str)
                            logger.info(
                                f"Daily reminder dispatched to user {user_id} at {user_time_str} ({tz_name})."
                            )
                        except Exception as send_err:
                            logger.warning(f"Could not send reminder to user {user_id}: {send_err}")
                            try:
                                await mark_user_reminded(user_id, user_date_str)
                            except Exception:
                                pass

            # Small cushion to ensure we don't double-trigger the same minute
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        logger.info("Reminder background scheduler received cancellation. Exiting cleanly.")
    except Exception as exc:
        logger.error(f"Unexpected error in reminder scheduler: {exc}", exc_info=True)
