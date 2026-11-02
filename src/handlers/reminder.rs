use std::str::FromStr;
use chrono::Utc;
use chrono_tz::Tz;
use regex::Regex;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, ParseMode};

use crate::db::{get_user_language, get_user_reminder, set_user_reminder, upsert_user};
use crate::keyboards::{get_reminder_settings_keyboard, get_timezone_keyboard};
use crate::locales::{get_text, get_text_fmt};
use crate::session::{SessionStore, UserState};

pub fn resolve_timezone(input_str: &str) -> Option<String> {
    let cleaned = input_str.trim();

    // 1. Try IANA name directly
    if Tz::from_str(cleaned).is_ok() {
        return Some(cleaned.to_string());
    }

    // 2. Try prefix/UTC offsets
    let upper = cleaned.to_uppercase();
    let re = Regex::new(r"^(?:UTC|GMT)?\s*([+-]?\d{1,2})(?::?(\d{2}))?$").ok()?;
    if let Some(caps) = re.captures(&upper) {
        let hours: i32 = caps.get(1)?.as_str().parse().ok()?;
        let mins: i32 = caps.get(2).map(|m| m.as_str().parse().unwrap_or(0)).unwrap_or(0);
        if (-12..=14).contains(&hours) && mins == 0 {
            let posix_sign = if hours > 0 { "-" } else { "+" };
            let etc_name = format!("Etc/GMT{}{}", posix_sign, hours.abs());
            if Tz::from_str(&etc_name).is_ok() {
                return Some(etc_name);
            }
        }
    }

    None
}

pub fn format_reminder_text(
    reminder_time: &str,
    enabled: bool,
    tz_name: &str,
    lang: &str,
) -> String {
    let status_str = if enabled {
        get_text("reminder_status_enabled", lang)
    } else {
        get_text("reminder_status_disabled", lang)
    };

    let tz = Tz::from_str(tz_name).unwrap_or(chrono_tz::Europe::Moscow);
    let local_time = Utc::now().with_timezone(&tz).format("%H:%M").to_string();

    get_text_fmt(
        "reminder_title",
        lang,
        &[
            ("status_str", &status_str),
            ("reminder_time", reminder_time),
            ("tz_label", tz_name),
            ("local_time", &local_time),
        ],
    )
}

pub async fn handle_reminder_cmd(bot: &Bot, msg: &Message, pool: &PgPool) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    if let Some(user) = msg.from.as_ref() {
        let _ = upsert_user(pool, user_id, user.username.as_deref(), Some(&user.first_name), None).await;
    }
    let _ = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, None, user_id, pool).await;
    Ok(())
}

pub async fn handle_reminder_callback(
    bot: &Bot,
    q: &CallbackQuery,
    action: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let lang = get_user_language(pool, user_id).await;
    let rem = get_user_reminder(pool, user_id).await.unwrap_or(crate::models::UserReminder {
        reminder_time: "21:00".to_string(),
        reminder_enabled: true,
        timezone: "Europe/Moscow".to_string(),
        last_reminded_date: None,
    });

    let mid = q.regular_message().map(|m| m.id.0 as i32);

    if let Some(time_str) = action.strip_prefix("set_time:") {
        let _ = set_user_reminder(pool, user_id, Some(time_str), None, None).await;
        let _ = bot.answer_callback_query(&q.id).await;
        if let Some(msg) = q.regular_message() {
            let _ = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
        }
        return Ok(());
    }

    match action {
        "toggle" => {
            let new_enabled = !rem.reminder_enabled;
            let _ = set_user_reminder(pool, user_id, None, Some(new_enabled), None).await;
            let _ = bot.answer_callback_query(&q.id).await;

            if let Some(msg) = q.regular_message() {
                let _ = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
            }
        }
        "time" => {
            let _ = bot.answer_callback_query(&q.id).await;
            if let Some(msg) = q.regular_message() {
                let _ = crate::rich::send_rich_reminder_time_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
            }
        }
        "time_custom" => {
            let _ = bot.answer_callback_query(&q.id).await;
            sessions.set(user_id, UserState::WaitingReminderTime).await;
            if let Some(msg) = q.regular_message() {
                bot.send_message(msg.chat.id, get_text("reminder_custom_time_prompt", &lang))
                    .parse_mode(ParseMode::Html)
                    .await?;
            }
        }
        "tz" => {
            let _ = bot.answer_callback_query(&q.id).await;
            if let Some(msg) = q.regular_message() {
                let _ = crate::rich::send_rich_timezone_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
            }
        }
        "tz_custom" => {
            let _ = bot.answer_callback_query(&q.id).await;
            sessions.set(user_id, UserState::WaitingCustomTimezone).await;
            if let Some(msg) = q.regular_message() {
                bot.send_message(msg.chat.id, get_text("tz_custom_prompt", &lang))
                    .parse_mode(ParseMode::Html)
                    .await?;
            }
        }
        "back" => {
            let _ = bot.answer_callback_query(&q.id).await;
            if let Some(msg) = q.regular_message() {
                let _ = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
            }
        }
        _ => {
            let _ = bot.answer_callback_query(&q.id).await;
        }
    }

    Ok(())
}

pub async fn handle_timezone_callback(
    bot: &Bot,
    q: &CallbackQuery,
    tz_val: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let lang = get_user_language(pool, user_id).await;

    if tz_val == "custom" {
        bot.answer_callback_query(&q.id).await?;
        sessions.set(user_id, UserState::WaitingCustomTimezone).await;
        if let Some(msg) = q.regular_message() {
            bot.send_message(msg.chat.id, get_text("tz_custom_prompt", &lang)).parse_mode(ParseMode::Html).await?;
        }
        return Ok(());
    }

    if let Some(valid_tz) = resolve_timezone(tz_val) {
        let _ = set_user_reminder(pool, user_id, None, None, Some(&valid_tz)).await;
        let _ = bot.answer_callback_query(&q.id).await;

        if let Some(msg) = q.regular_message() {
            let mid = Some(msg.id.0 as i32);
            let _ = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, mid, user_id, pool).await;
        }
    } else {
        bot.answer_callback_query(&q.id).text("Неизвестный часовой пояс").await?;
    }

    Ok(())
}

pub async fn handle_reminder_prompt_callback(
    bot: &Bot,
    q: &CallbackQuery,
    action: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let _ = bot.answer_callback_query(&q.id).await;

    let mid = q.regular_message().map(|m| m.id.0 as i32);
    let chat_id = match q.regular_message() {
        Some(m) => m.chat.id,
        None => ChatId(user_id),
    };

    if action == "ok" {
        let tz_name = crate::db::get_user_timezone(pool, user_id).await;
        let tz = Tz::from_str(&tz_name).unwrap_or(chrono_tz::Europe::Moscow);
        let today = Utc::now().with_timezone(&tz).format("%Y-%m-%d").to_string();
        let _ = crate::db::mark_user_reminded(pool, user_id, &today).await;

        let _ = crate::rich::send_rich_daily_reminder_saved(bot.token(), chat_id.0, mid, user_id, pool).await;
    } else if action == "log" {
        let _ = crate::handlers::headache::start_headache_flow(bot, chat_id, mid, user_id, pool, sessions).await;
    }

    Ok(())
}
