use std::collections::HashSet;
use std::str::FromStr;
use chrono::{Datelike, NaiveDate, Utc};
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, ChatId, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, MessageId, ParseMode};

use crate::db::{get_episodes_for_date, get_episodes_for_month, get_user_language, get_user_timezone};
use crate::keyboards::{build_calendar_keyboard, get_month_name};
use crate::locales::{get_intensity_label, get_location_name, get_medication_name, get_pain_type_name, get_symptom_name, get_text, get_text_fmt, get_trigger_name};
use crate::models::HeadacheEpisode;
use crate::session::SessionStore;

pub async fn render_calendar(
    pool: &PgPool,
    user_id: i64,
    year: i32,
    month: u32,
    lang: &str,
) -> (String, InlineKeyboardMarkup) {
    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let today = Utc::now().with_timezone(&tz).date_naive();

    let episodes = get_episodes_for_month(pool, user_id, year, month).await.unwrap_or_default();
    let mut pain_days = HashSet::new();
    for ep in &episodes {
        if let Some(d) = parse_episode_date(&ep.start_time) {
            if d.year() == year && d.month() == month {
                pain_days.insert(d.day());
            }
        }
    }

    let (kb, pain_count, healthy_count) = build_calendar_keyboard(year, month, &pain_days, today, lang);
    let month_name = get_month_name(year, month, lang);

    let caption = get_text_fmt(
        "calendar_title",
        lang,
        &[
            ("month_name", month_name),
            ("year", &year.to_string()),
            ("pain_days", &pain_count.to_string()),
            ("healthy_days", &healthy_count.to_string()),
        ],
    );

    (caption, kb)
}

fn parse_episode_date(st: &str) -> Option<NaiveDate> {
    if st.len() >= 10 {
        NaiveDate::parse_from_str(&st[..10], "%Y-%m-%d").ok()
    } else {
        None
    }
}

pub fn format_episode_card(ep: &HeadacheEpisode, lang: &str) -> String {
    let status_str = match ep.status.as_deref() {
        Some("completed") => get_text("history_card_status_completed", lang),
        Some("not_resolved") => get_text("history_card_status_not_resolved", lang),
        _ => get_text("history_card_status_active", lang),
    };

    let level_name = get_intensity_label(ep.intensity, lang);
    let loc = get_location_name(&ep.location, lang);
    let pt = get_pain_type_name(&ep.pain_type, lang);

    let sym_str = if let Some(serde_json::Value::Array(arr)) = &ep.symptoms {
        let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_symptom_name(s, lang)).collect();
        if list.is_empty() || list.contains(&"none".to_string()) { "—".to_string() } else { list.join(", ") }
    } else {
        "—".to_string()
    };

    let trig_str = if let Some(serde_json::Value::Array(arr)) = &ep.triggers {
        let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|t| get_trigger_name(t, lang)).collect();
        if list.is_empty() || list.contains(&"none".to_string()) { "—".to_string() } else { list.join(", ") }
    } else {
        "—".to_string()
    };

    let med_name = ep.medication.as_deref().unwrap_or("none");
    let mut med_str = get_medication_name(med_name, lang);
    if let Some(relief) = ep.medication_relief.as_deref() {
        let relief_txt = match relief {
            "helped" => get_text("fu_med_helped", lang),
            "partially" => get_text("fu_med_partially", lang),
            "not_helped" => get_text("fu_med_not_helped", lang),
            _ => "".to_string(),
        };
        if !relief_txt.is_empty() {
            med_str = format!("{med_str} ({relief_txt})");
        }
    }

    let time_line = if let Some(end) = &ep.end_time {
        if ep.start_time.len() >= 10 && end.len() >= 16 && ep.start_time[..10] == end[..10] {
            format!("{} → {}", ep.start_time, &end[11..])
        } else {
            format!("{} → {}", ep.start_time, end)
        }
    } else {
        ep.start_time.clone()
    };

    let mut out = String::new();
    out.push_str(&get_text_fmt("history_card_header", lang, &[("id", &ep.id.to_string()), ("status", &status_str)]));
    out.push('\n');
    out.push_str(&get_text_fmt("history_card_time", lang, &[("time", &time_line)]));
    out.push_str(&get_text_fmt("history_card_pain", lang, &[("intensity", &ep.intensity.to_string()), ("level", &level_name)]));
    out.push_str(&get_text_fmt("history_card_loc", lang, &[("loc", &loc), ("pt", &pt)]));
    out.push_str(&get_text_fmt("history_card_sym", lang, &[("sym", &sym_str)]));
    out.push_str(&get_text_fmt("history_card_triggers", lang, &[("triggers", &trig_str)]));
    out.push_str(&get_text_fmt("history_card_med", lang, &[("med", &med_str)]));
    out
}

async fn update_calendar_view(
    bot: &Bot,
    chat_id: ChatId,
    msg_id: MessageId,
    text: &str,
    kb: InlineKeyboardMarkup,
) {
    if bot.edit_message_caption(chat_id, msg_id)
        .caption(text)
        .parse_mode(ParseMode::Html)
        .reply_markup(kb.clone())
        .await
        .is_err()
    {
        let _ = bot.edit_message_text(chat_id, msg_id, text)
            .parse_mode(ParseMode::Html)
            .reply_markup(kb)
            .await;
    }
}

pub async fn handle_calendar_cmd(
    bot: &Bot,
    msg: &Message,
    pool: &PgPool,
    sessions: &SessionStore,
    mid: Option<i32>,
) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let today = Utc::now().with_timezone(&tz).date_naive();

    let target_mid = match mid {
        Some(m) => Some(m),
        None => sessions.get_last_mid(user_id).await,
    };
    if let Ok(new_mid) = crate::rich::send_rich_calendar_menu(bot.token(), msg.chat.id.0, target_mid, user_id, today.year(), today.month(), None, pool).await {
        sessions.set_last_mid(user_id, new_mid).await;
    }
    Ok(())
}

pub async fn handle_calendar_callback(
    bot: &Bot,
    q: &CallbackQuery,
    data: &str,
    pool: &PgPool,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let _ = bot.answer_callback_query(&q.id).await;

    let chat_id = match q.regular_message() {
        Some(m) => m.chat.id,
        None => return Ok(()),
    };

    let mid = q.regular_message().map(|m| m.id.0 as i32);

    let parts: Vec<&str> = data.split(':').collect();
    if parts.len() < 2 {
        return Ok(());
    }

    let action = parts[1];
    match action {
        "nav" => {
            if parts.len() >= 4 {
                let y: i32 = parts[2].parse().unwrap_or(2026);
                let m: u32 = parts[3].parse().unwrap_or(1);
                let _ = crate::rich::send_rich_calendar_menu(bot.token(), chat_id.0, mid, user_id, y, m, None, pool).await;
            }
        }
        "today" => {
            let tz_str = get_user_timezone(pool, user_id).await;
            let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
            let today = Utc::now().with_timezone(&tz).date_naive();
            let _ = crate::rich::send_rich_calendar_menu(bot.token(), chat_id.0, mid, user_id, today.year(), today.month(), Some(today.day()), pool).await;
        }
        "day" => {
            if parts.len() >= 5 {
                let y: i32 = parts[2].parse().unwrap_or(2026);
                let m: u32 = parts[3].parse().unwrap_or(1);
                let d: u32 = parts[4].parse().unwrap_or(1);
                let _ = crate::rich::send_rich_calendar_menu(bot.token(), chat_id.0, mid, user_id, y, m, Some(d), pool).await;
            }
        }
        _ => {}
    }

    Ok(())
}
