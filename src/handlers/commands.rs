use std::str::FromStr;
use chrono::{Datelike, Duration, Utc};
use chrono_tz::Tz;
use regex::Regex;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, ChatId, InputFile, KeyboardRemove, MessageId, ParseMode};

use crate::db::{get_episode_by_id, get_user_language, resolve_episode_pain, set_user_reminder, upsert_user};
use crate::handlers::calendar::handle_calendar_cmd;
use crate::handlers::export::handle_export_cmd;
use crate::handlers::followup::handle_status_cmd;
use crate::handlers::headache::{get_step_image_path, start_headache_flow};
use crate::handlers::language::handle_language_cmd;
use crate::handlers::reminder::{handle_reminder_cmd, resolve_timezone};
use crate::keyboards::*;
use crate::locales::{get_text, get_text_fmt};
use crate::session::{FlowStep, SessionStore, UserState};

pub fn parse_custom_datetime_input(text: &str, tz_name: &str) -> String {
    let tz = Tz::from_str(tz_name).unwrap_or(chrono_tz::Europe::Moscow);
    let now = Utc::now().with_timezone(&tz);
    let t = text.trim();

    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(t, "%Y-%m-%d %H:%M") {
        return dt.format("%Y-%m-%d %H:%M").to_string();
    }
    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(t, "%d.%m.%Y %H:%M") {
        return dt.format("%Y-%m-%d %H:%M").to_string();
    }
    let curr_year = now.year();
    let with_year = format!("{curr_year}.{t}");
    if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(&with_year, "%Y.%d.%m %H:%M") {
        return dt.format("%Y-%m-%d %H:%M").to_string();
    }
    let lower = t.to_lowercase();
    if lower.contains("вчера") || lower.contains("учора") || lower.contains("yesterday") {
        let yesterday = now.date_naive() - Duration::days(1);
        let re = Regex::new(r"([0-1]?[0-9]|2[0-3]):([0-5][0-9])").unwrap();
        if let Some(caps) = re.captures(t) {
            let h: u32 = caps[1].parse().unwrap_or(12);
            let m: u32 = caps[2].parse().unwrap_or(0);
            if let Some(dt) = yesterday.and_hms_opt(h, m, 0) {
                return dt.format("%Y-%m-%d %H:%M").to_string();
            }
        }
        return format!("{} 12:00", yesterday.format("%Y-%m-%d"));
    }
    if let Ok(time) = chrono::NaiveTime::parse_from_str(t, "%H:%M") {
        let dt = now.date_naive().and_time(time);
        return dt.format("%Y-%m-%d %H:%M").to_string();
    }
    let re_h_ago = Regex::new(r"(\d+)\s*(?:ч|час|часа|часов|h|hour|hours|гадз|гадзіны)?\s*(?:назад|ago|таму)").unwrap();
    if let Some(caps) = re_h_ago.captures(&lower) {
        let h: i64 = caps[1].parse().unwrap_or(1);
        let dt = now - Duration::hours(h);
        return dt.format("%Y-%m-%d %H:%M").to_string();
    }
    now.format("%Y-%m-%d %H:%M").to_string()
}

pub async fn send_main_menu(
    bot: &Bot,
    chat_id: ChatId,
    mid: Option<i32>,
    user_id: i64,
    first_name: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    if let Ok(new_mid) = crate::rich::send_rich_main_menu(bot.token(), chat_id.0, mid, user_id, first_name, pool).await {
        sessions.set_last_mid(user_id, new_mid).await;
    }
    Ok(())
}

pub async fn handle_menu_callback(
    bot: &Bot,
    q: &CallbackQuery,
    action: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let _ = bot.answer_callback_query(&q.id).await;

    let chat_id = match q.regular_message() {
        Some(m) => m.chat.id,
        None => return Ok(()),
    };

    let mid = q.regular_message().map(|m| m.id.0 as i32);
    if let Some(m) = mid {
        sessions.set_last_mid(user_id, m).await;
    }

    match action {
        "log" => {
            start_headache_flow(bot, chat_id, mid, user_id, pool, sessions).await?;
        }
        "status" => {
            sessions.remove(user_id).await;
            if let Ok(new_mid) = crate::rich::send_rich_status_menu(bot.token(), chat_id.0, mid, user_id, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "history" | "calendar" => {
            use std::str::FromStr;
            let tz_str = crate::db::get_user_timezone(pool, user_id).await;
            let tz = chrono_tz::Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
            let today = chrono::Utc::now().with_timezone(&tz).date_naive();
            if let Ok(new_mid) = crate::rich::send_rich_calendar_menu(
                bot.token(),
                chat_id.0,
                mid,
                user_id,
                chrono::Datelike::year(&today),
                chrono::Datelike::month(&today),
                None,
                pool,
            ).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "export" => {
            if let Ok(new_mid) = crate::rich::send_rich_export_menu(bot.token(), chat_id.0, mid, user_id, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "reminder" => {
            if let Ok(new_mid) = crate::rich::send_rich_reminder_menu(bot.token(), chat_id.0, mid, user_id, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "language" => {
            if let Ok(new_mid) = crate::rich::send_rich_language_menu(bot.token(), chat_id.0, mid, user_id, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "help" => {
            if let Ok(new_mid) = crate::rich::send_rich_help_menu(bot.token(), chat_id.0, mid, user_id, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        "home" | "main" => {
            let first_name = &q.from.first_name;
            if let Ok(new_mid) = crate::rich::send_rich_main_menu(bot.token(), chat_id.0, mid, user_id, first_name, pool).await {
                sessions.set_last_mid(user_id, new_mid).await;
            }
        }
        _ => {}
    }

    Ok(())
}

pub async fn handle_message(
    bot: Bot,
    msg: Message,
    pool: PgPool,
    sessions: SessionStore,
) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    let text = msg.text().unwrap_or("").trim();

    if let Some(u) = msg.from.as_ref() {
        let _ = upsert_user(&pool, user_id, u.username.as_deref(), Some(&u.first_name), None).await;
    }
    let lang = get_user_language(&pool, user_id).await;

    // Check cancel command or button
    if text == "/cancel" || is_cancel_btn(text) {
        sessions.remove(user_id).await;
        let _ = bot.delete_message(msg.chat.id, msg.id).await;
        let first_name = msg.from.as_ref().map(|u| u.first_name.as_str()).unwrap_or("друг");
        let last_mid = sessions.get_last_mid(user_id).await;
        send_main_menu(&bot, msg.chat.id, last_mid, user_id, first_name, &pool, &sessions).await?;
        return Ok(());
    }

    // Check user waiting state for text inputs
    let current_state = sessions.get(user_id).await;

    if let Some(state) = current_state {
        match state {
            UserState::WaitingCustomStartTime(mut form, pmid) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                let tz_str = crate::db::get_user_timezone(&pool, user_id).await;
                form.start_time = Some(parse_custom_datetime_input(text, &tz_str));
                form.current_step = Some(FlowStep::Intensity);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingCustomTrigger(mut form, pmid) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                form.triggers.retain(|x| x != "none");
                form.triggers.push(text.to_string());
                form.current_step = Some(FlowStep::Medication);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingCustomMedication(mut form, pmid) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                let trimmed = text.trim();
                if !trimmed.is_empty() && trimmed != "none" {
                    let _ = crate::db::save_user_medication(&pool, user_id, trimmed).await;
                    form.medication = Some(trimmed.to_string());
                    form.current_step = Some(FlowStep::MedicationTime);
                } else {
                    form.medication = Some("none".to_string());
                    form.current_step = Some(FlowStep::Confirm);
                }

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingFollowupTime(ep_id, pmid) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                sessions.remove(user_id).await;

                let tz_str = crate::db::get_user_timezone(&pool, user_id).await;
                let end_time = parse_custom_datetime_input(text, &tz_str);
                let _ = resolve_episode_pain(&pool, ep_id, true, Some(&end_time)).await;
                let ep = get_episode_by_id(&pool, ep_id).await.unwrap_or(None);
                let has_meds = ep.as_ref().map(|e| {
                    let m = e.medication.as_deref().unwrap_or("none");
                    m != "none" && !m.is_empty()
                }).unwrap_or(false);

                let last_mid = sessions.get_last_mid(user_id).await;
                if has_meds {
                    let med_name = ep.as_ref().and_then(|e| e.medication.clone()).unwrap_or_default();
                    let _ = crate::rich::send_rich_followup_med(bot.token(), msg.chat.id.0, last_mid, ep_id, &med_name, user_id, &pool).await;
                } else {
                    let caption = get_text_fmt("fu_pain_resolved_recorded", &lang, &[("end_time", &end_time)]);
                    let _ = crate::rich::send_rich_followup_result(bot.token(), msg.chat.id.0, last_mid, &caption, user_id, &pool).await;
                }
                return Ok(());
            }

            UserState::WaitingReminderTime(pmid) => {
                let re = Regex::new(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$").unwrap();
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                if re.is_match(text) {
                    sessions.remove(user_id).await;
                    let _ = set_user_reminder(&pool, user_id, Some(text), None, None).await;
                    let last_mid = sessions.get_last_mid(user_id).await;
                    if let Ok(new_mid) = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, last_mid, user_id, &pool).await {
                        sessions.set_last_mid(user_id, new_mid).await;
                    }
                } else {
                    let err = bot.send_message(msg.chat.id, get_text("reminder_custom_time_invalid", &lang))
                        .parse_mode(ParseMode::Html)
                        .await?;
                    tokio::time::sleep(std::time::Duration::from_secs(3)).await;
                    let _ = bot.delete_message(msg.chat.id, err.id).await;
                }
                return Ok(());
            }

            UserState::WaitingCustomTimezone(pmid) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                if let Some(p) = pmid {
                    let _ = bot.delete_message(msg.chat.id, MessageId(p)).await;
                }
                if let Some(valid_tz) = resolve_timezone(text) {
                    sessions.remove(user_id).await;
                    let _ = set_user_reminder(&pool, user_id, None, None, Some(&valid_tz)).await;
                    let last_mid = sessions.get_last_mid(user_id).await;
                    if let Ok(new_mid) = crate::rich::send_rich_reminder_menu(bot.token(), msg.chat.id.0, last_mid, user_id, &pool).await {
                        sessions.set_last_mid(user_id, new_mid).await;
                    }
                } else {
                    let err = bot.send_message(msg.chat.id, get_text("tz_custom_invalid", &lang))
                        .parse_mode(ParseMode::Html)
                        .await?;
                    tokio::time::sleep(std::time::Duration::from_secs(3)).await;
                    let _ = bot.delete_message(msg.chat.id, err.id).await;
                }
                return Ok(());
            }

            _ => {}
        }
    }

    // Command dispatching
    let is_cmd = text.starts_with('/') 
        || is_log_btn(text)
        || is_status_btn(text)
        || is_history_btn(text)
        || is_export_btn(text)
        || is_reminder_btn(text)
        || is_language_btn(text)
        || is_help_btn(text);

    if is_cmd {
        let _ = bot.delete_message(msg.chat.id, msg.id).await;
        if let Ok(temp) = bot.send_message(msg.chat.id, "🦊")
            .reply_markup(KeyboardRemove::default())
            .await 
        {
            let _ = bot.delete_message(msg.chat.id, temp.id).await;
        }
    }

    let last_mid = sessions.get_last_mid(user_id).await;

    if text.starts_with("/start") {
        let args = text.strip_prefix("/start").unwrap_or("").trim();

        match args {
            "log" => {
                start_headache_flow(&bot, msg.chat.id, last_mid, user_id, &pool, &sessions).await?;
                return Ok(());
            }
            "status" => {
                handle_status_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
                return Ok(());
            }
            "history" => {
                handle_calendar_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
                return Ok(());
            }
            "export" => {
                handle_export_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
                return Ok(());
            }
            "reminder" => {
                handle_reminder_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
                return Ok(());
            }
            "language" => {
                handle_language_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
                return Ok(());
            }
            "help" => {
                if let Ok(new_mid) = crate::rich::send_rich_help_menu(bot.token(), msg.chat.id.0, last_mid, user_id, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }
            _ => {
                let first_name = msg.from.as_ref().map(|u| u.first_name.as_str()).unwrap_or("друг");
                send_main_menu(&bot, msg.chat.id, None, user_id, first_name, &pool, &sessions).await?;
                return Ok(());
            }
        }
    }

    if text == "/help" || is_help_btn(text) {
        if let Ok(new_mid) = crate::rich::send_rich_help_menu(bot.token(), msg.chat.id.0, last_mid, user_id, &pool).await {
            sessions.set_last_mid(user_id, new_mid).await;
        }
        return Ok(());
    }

    if text == "/log" || is_log_btn(text) {
        start_headache_flow(&bot, msg.chat.id, last_mid, user_id, &pool, &sessions).await?;
        return Ok(());
    }

    if text == "/status" || text == "/finish" || is_status_btn(text) {
        handle_status_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
        return Ok(());
    }

    if text == "/history" || is_history_btn(text) {
        handle_calendar_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
        return Ok(());
    }

    if text == "/export" || is_export_btn(text) {
        handle_export_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
        return Ok(());
    }

    if text == "/reminder" || text == "/remind" || text == "/settings" || is_reminder_btn(text) {
        handle_reminder_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
        return Ok(());
    }

    if text == "/language" || text == "/lang" || is_language_btn(text) {
        handle_language_cmd(&bot, &msg, &pool, &sessions, last_mid).await?;
        return Ok(());
    }

    // Default reply: show main menu
    let first_name = msg.from.as_ref().map(|u| u.first_name.as_str()).unwrap_or("друг");
    send_main_menu(&bot, msg.chat.id, last_mid, user_id, first_name, &pool, &sessions).await?;

    Ok(())
}
