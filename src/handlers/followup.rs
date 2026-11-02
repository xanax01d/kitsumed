use std::str::FromStr;
use chrono::{Duration, Utc};
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, ParseMode};

use crate::db::{get_active_episode, get_episode_by_id, get_user_language, get_user_timezone, resolve_episode_pain, update_medication_relief};
use crate::keyboards::{get_followup_medication_keyboard, get_followup_pain_keyboard, get_followup_when_keyboard};
use crate::locales::{get_text, get_text_fmt};
use crate::session::{SessionStore, UserState};

pub fn calculate_end_time(preset: &str, tz_name: &str) -> String {
    let tz = Tz::from_str(tz_name).unwrap_or(chrono_tz::Europe::Moscow);
    let now = Utc::now().with_timezone(&tz);

    let target = match preset {
        "now" => now,
        "-30m" => now - Duration::minutes(30),
        "-1h" => now - Duration::hours(1),
        "-2h" => now - Duration::hours(2),
        _ => now,
    };
    target.format("%Y-%m-%d %H:%M").to_string()
}

pub async fn handle_status_cmd(
    bot: &Bot,
    msg: &Message,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    sessions.remove(user_id).await;
    let _ = crate::rich::send_rich_status_menu(bot.token(), msg.chat.id.0, None, user_id, pool).await;
    Ok(())
}

pub async fn handle_followup_callback(
    bot: &Bot,
    q: &CallbackQuery,
    data: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let lang = get_user_language(pool, user_id).await;
    let tz_name = get_user_timezone(pool, user_id).await;
    let _ = bot.answer_callback_query(&q.id).await;

    let mid = q.regular_message().map(|m| m.id.0 as i32);
    let chat_id = match q.regular_message() {
        Some(m) => m.chat.id,
        None => ChatId(user_id),
    };

    let parts: Vec<&str> = data.split(':').collect();
    if parts.len() < 2 {
        return Ok(());
    }

    let action = parts[1];
    match action {
        "pain_passed" => {
            if parts.len() >= 3 {
                let ep_id: i32 = parts[2].parse().unwrap_or(0);
                let _ = crate::rich::send_rich_followup_when(bot.token(), chat_id.0, mid, ep_id, user_id, pool).await;
            }
        }
        "pain_not_passed" => {
            if parts.len() >= 3 {
                let ep_id: i32 = parts[2].parse().unwrap_or(0);
                let _ = resolve_episode_pain(pool, ep_id, false, None).await;

                let ep = get_episode_by_id(pool, ep_id).await.unwrap_or(None);
                let has_meds = ep.as_ref().map(|e| {
                    let m = e.medication.as_deref().unwrap_or("none");
                    m != "none" && !m.is_empty()
                }).unwrap_or(false);

                if has_meds {
                    let med_name = ep.as_ref().and_then(|e| e.medication.clone()).unwrap_or_default();
                    let _ = crate::rich::send_rich_followup_med(bot.token(), chat_id.0, mid, ep_id, &med_name, user_id, pool).await;
                } else {
                    let text = get_text("fu_pain_not_resolved_recorded", &lang);
                    let _ = crate::rich::send_rich_followup_result(bot.token(), chat_id.0, mid, &text, user_id, pool).await;
                }
            }
        }
        "set_when" => {
            if parts.len() >= 4 {
                let ep_id: i32 = parts[2].parse().unwrap_or(0);
                let preset = parts[3];
                let end_time = calculate_end_time(preset, &tz_name);

                let _ = resolve_episode_pain(pool, ep_id, true, Some(&end_time)).await;
                let ep = get_episode_by_id(pool, ep_id).await.unwrap_or(None);
                let has_meds = ep.as_ref().map(|e| {
                    let m = e.medication.as_deref().unwrap_or("none");
                    m != "none" && !m.is_empty()
                }).unwrap_or(false);

                if has_meds {
                    let med_name = ep.as_ref().and_then(|e| e.medication.clone()).unwrap_or_default();
                    let _ = crate::rich::send_rich_followup_med(bot.token(), chat_id.0, mid, ep_id, &med_name, user_id, pool).await;
                } else {
                    let text = get_text_fmt("fu_pain_resolved_recorded", &lang, &[("end_time", &end_time)]);
                    let _ = crate::rich::send_rich_followup_result(bot.token(), chat_id.0, mid, &text, user_id, pool).await;
                }
            }
        }
        "custom_when" => {
            if parts.len() >= 3 {
                let ep_id: i32 = parts[2].parse().unwrap_or(0);
                sessions.set(user_id, UserState::WaitingFollowupTime(ep_id)).await;
                let _ = bot.send_message(chat_id, get_text("fu_when_custom_prompt", &lang)).parse_mode(ParseMode::Html).await;
            }
        }
        "med_relief" => {
            if parts.len() >= 4 {
                let ep_id: i32 = parts[2].parse().unwrap_or(0);
                let relief = parts[3];
                let _ = update_medication_relief(pool, ep_id, relief).await;

                let text = get_text("fu_med_recorded", &lang);
                let _ = crate::rich::send_rich_followup_result(bot.token(), chat_id.0, mid, &text, user_id, pool).await;
            }
        }
        _ => {}
    }

    Ok(())
}
