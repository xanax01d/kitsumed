import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from db import get_pending_followup_episodes, mark_followup_sent
from keyboards.headache_kb import get_followup_pain_keyboard
from locales import get_text

logger = logging.getLogger(__name__)


async def followup_scheduler(bot: Bot) -> None:
    """
    Background worker that checks for active headache episodes due for follow-up inquiry.
    Inquires if pain has resolved and whether medication provided relief.
    """
    logger.info("Follow-up background scheduler started.")
    try:
        while True:
            # Check every 60 seconds
            await asyncio.sleep(60)

            try:
                episodes = await get_pending_followup_episodes()
            except Exception as db_err:
                logger.error(f"Error checking pending follow-ups: {db_err}")
                continue

            for ep in episodes:
                ep_id = ep["id"]
                user_id = ep["user_id"]
                lang = ep.get("language") or "ru"

                prompt_text = get_text("fu_pain_question", lang)
                keyboard = get_followup_pain_keyboard(ep_id, lang)

                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=prompt_text,
                        reply_markup=keyboard,
                    )
                    await mark_followup_sent(ep_id)
                    logger.info(f"Delivered automated follow-up check for episode #{ep_id} to user {user_id}")
                except Exception as send_err:
                    logger.warning(f"Could not send follow-up to user {user_id}: {send_err}")
                    # Mark sent so we don't spam if blocked
                    try:
                        await mark_followup_sent(ep_id)
                    except Exception:
                        pass

    except asyncio.CancelledError:
        logger.info("Follow-up scheduler received cancellation. Exiting cleanly.")
    except Exception as exc:
        logger.error(f"Unexpected error in followup scheduler: {exc}", exc_info=True)
