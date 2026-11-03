use regex::Regex;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, ChatId, InputFile, KeyboardRemove, ParseMode};

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

pub async fn send_main_menu(
    bot: &Bot,
    chat_id: ChatId,
    mid: Option<i32>,
    user_id: i64,
    first_name: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let target_mid = match mid {
        Some(m) => Some(m),
        None => sessions.get_last_mid(user_id).await,
    };
    if let Ok(new_mid) = crate::rich::send_rich_main_menu(bot.token(), chat_id.0, target_mid, user_id, first_name, pool).await {
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
            UserState::WaitingCustomStartTime(mut form) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                form.start_time = Some(text.to_string());
                form.current_step = Some(FlowStep::Intensity);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingCustomTrigger(mut form) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                form.triggers.push(text.to_string());
                form.current_step = Some(FlowStep::Medication);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingCustomMedication(mut form) => {
                let _ = bot.delete_message(msg.chat.id, msg.id).await;
                form.medication = Some(text.to_string());
                form.current_step = Some(FlowStep::MedicationTime);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let last_mid = sessions.get_last_mid(user_id).await;
                if let Ok(new_mid) = crate::rich::render_rich_headache_step(bot.token(), msg.chat.id.0, last_mid, user_id, &form, &pool).await {
                    sessions.set_last_mid(user_id, new_mid).await;
                }
                return Ok(());
            }

            UserState::WaitingFollowupTime(ep_id) => {
                sessions.remove(user_id).await;

                let _ = resolve_episode_pain(&pool, ep_id, true, Some(text)).await;
                let ep = get_episode_by_id(&pool, ep_id).await.unwrap_or(None);
                let has_meds = ep.as_ref().map(|e| {
                    let m = e.medication.as_deref().unwrap_or("none");
                    m != "none" && !m.is_empty()
                }).unwrap_or(false);

                if has_meds {
                    let med_name = ep.as_ref().and_then(|e| e.medication.clone()).unwrap_or_default();
                    let caption = get_text_fmt("fu_med_question", &lang, &[("medication", &med_name)]);
                    let kb = get_followup_medication_keyboard(ep_id, &lang);
                    bot.send_message(msg.chat.id, caption)
                        .parse_mode(ParseMode::Html)
                        .reply_markup(kb)
                        .await?;
                } else {
                    let caption = get_text_fmt("fu_pain_resolved_recorded", &lang, &[("end_time", text)]);
                    bot.send_message(msg.chat.id, caption)
                        .parse_mode(ParseMode::Html)
                        .reply_markup(KeyboardRemove::default())
                        .await?;
                }
                return Ok(());
            }

            UserState::WaitingReminderTime => {
                let re = Regex::new(r"^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$").unwrap();
                if re.is_match(text) {
                    sessions.remove(user_id).await;
                    let _ = set_user_reminder(&pool, user_id, Some(text), None, None).await;
                    let success_text = get_text_fmt("reminder_custom_time_saved", &lang, &[
                        ("time", text),
                        ("tz_label", "Europe/Moscow"),
                    ]);
                    bot.send_message(msg.chat.id, success_text)
                        .parse_mode(ParseMode::Html)
                        .reply_markup(KeyboardRemove::default())
                        .await?;
                } else {
                    bot.send_message(msg.chat.id, get_text("reminder_custom_time_invalid", &lang))
                        .parse_mode(ParseMode::Html)
                        .await?;
                }
                return Ok(());
            }

            UserState::WaitingCustomTimezone => {
                if let Some(valid_tz) = resolve_timezone(text) {
                    sessions.remove(user_id).await;
                    let _ = set_user_reminder(&pool, user_id, None, None, Some(&valid_tz)).await;
                    let success_text = get_text_fmt("tz_custom_saved", &lang, &[
                        ("tz_label", &valid_tz),
                        ("local_time", "OK"),
                    ]);
                    bot.send_message(msg.chat.id, success_text)
                        .parse_mode(ParseMode::Html)
                        .reply_markup(KeyboardRemove::default())
                        .await?;
                } else {
                    bot.send_message(msg.chat.id, get_text("tz_custom_invalid", &lang))
                        .parse_mode(ParseMode::Html)
                        .await?;
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
                send_main_menu(&bot, msg.chat.id, last_mid, user_id, first_name, &pool, &sessions).await?;
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
