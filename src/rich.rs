use std::collections::HashSet;
use std::path::Path;
use std::str::FromStr;
use chrono::{Datelike, NaiveDate, Utc};
use chrono_tz::Tz;
use sqlx::PgPool;

use crate::db::{
    get_active_episode, get_all_episodes, get_episodes_for_date, get_episodes_for_month,
    get_user_language, get_user_reminder, get_user_timezone,
};
use crate::locales::{
    get_intensity_label, get_location_name, get_medication_name, get_pain_type_name,
    get_symptom_name, get_trigger_name, get_text, get_text_fmt, normalize_lang,
};
use crate::models::UserReminder;
use crate::session::{FlowStep, HeadacheForm};

pub fn format_duration_label(dur: &str, norm: &str) -> String {
    match dur {
        "15m" => match norm {
            "en" => "15 min".to_string(),
            "be" => "15 хвілін".to_string(),
            _ => "15 минут".to_string(),
        },
        "30m" => match norm {
            "en" => "30 min".to_string(),
            "be" => "30 хвілін".to_string(),
            _ => "30 минут".to_string(),
        },
        "1h" | "60m" => match norm {
            "en" => "1 hour".to_string(),
            "be" => "1 гадзіна".to_string(),
            _ => "1 час".to_string(),
        },
        "2h" | "120m" => match norm {
            "en" => "2 hours".to_string(),
            "be" => "2 гадзіны".to_string(),
            _ => "2 часа".to_string(),
        },
        "4h" | "180m" | "240m" => match norm {
            "en" => "4+ hours".to_string(),
            "be" => "4+ гадзіны".to_string(),
            _ => "4+ часа".to_string(),
        },
        other => other.to_string(),
    }
}

pub fn html_escape(input: &str) -> String {
    input
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

pub fn format_rich_html(html: &str) -> String {
    let mut out = String::with_capacity(html.len() + 256);
    let mut rest = html;

    while !rest.is_empty() {
        let tags = [
            rest.find("<blockquote"),
            rest.find("<tg-button-row"),
            rest.find("<img"),
            rest.find("<p"),
        ];
        let next_tag = tags.into_iter().flatten().min();

        if let Some(tag_idx) = next_tag {
            let before = &rest[..tag_idx];
            for line in before.lines() {
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    out.push_str("<p>");
                    out.push_str(trimmed);
                    out.push_str("</p>\n");
                }
            }

            let after = &rest[tag_idx..];
            if after.starts_with("<blockquote") {
                if let Some(tag_close) = after.find('>') {
                    out.push_str("<blockquote>\n");
                    let bq_start = &after[tag_close + 1..];
                    if let Some(end_idx) = bq_start.find("</blockquote>") {
                        let bq_content = &bq_start[..end_idx];
                        for line in bq_content.lines() {
                            let trimmed = line.trim();
                            if !trimmed.is_empty() {
                                if trimmed.starts_with("<p>") && trimmed.ends_with("</p>") {
                                    out.push_str(trimmed);
                                } else {
                                    out.push_str("<p>");
                                    out.push_str(trimmed);
                                    out.push_str("</p>");
                                }
                                out.push('\n');
                            }
                        }
                        out.push_str("</blockquote>\n");
                        rest = &bq_start[end_idx + 13..];
                    } else {
                        out.push_str(after);
                        return out;
                    }
                } else {
                    out.push_str(after);
                    return out;
                }
            } else if after.starts_with("<tg-button-row") {
                if let Some(end_idx) = after.find("</tg-button-row>") {
                    let block = &after[..end_idx + 16];
                    out.push_str(block);
                    out.push('\n');
                    rest = &after[end_idx + 16..];
                } else {
                    out.push_str(after);
                    return out;
                }
            } else if after.starts_with("<img") {
                if let Some(end_idx) = after.find('>') {
                    let block = &after[..=end_idx];
                    out.push_str(block);
                    out.push('\n');
                    rest = &after[end_idx + 1..];
                } else {
                    out.push_str(after);
                    return out;
                }
            } else if after.starts_with("<p") {
                if let Some(end_idx) = after.find("</p>") {
                    let block = &after[..end_idx + 4];
                    out.push_str(block);
                    out.push('\n');
                    rest = &after[end_idx + 4..];
                } else {
                    out.push_str(after);
                    return out;
                }
            } else {
                out.push_str(after);
                break;
            }
        } else {
            for line in rest.lines() {
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    out.push_str("<p>");
                    out.push_str(trimmed);
                    out.push_str("</p>\n");
                }
            }
            break;
        }
    }

    out
}

pub async fn send_or_edit_rich_raw(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    html: &str,
    img_path: Option<&str>,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let formatted_html = format_rich_html(html);
    let html = formatted_html.as_str();
    let client = reqwest::Client::new();
    let has_image = img_path.map(|p| Path::new(p).exists()).unwrap_or(false);

    // If message_id is provided, attempt in-place edit first
    if let Some(mid) = message_id {
        let edit_url = format!("https://api.telegram.org/bot{token}/editMessageText");
        let ok = if has_image {
            let path = img_path.unwrap();
            if let Ok(bytes) = tokio::fs::read(path).await {
                let rich_message = serde_json::json!({
                    "html": html,
                    "media": [
                        {
                            "id": "hero",
                            "media": {
                                "type": "photo",
                                "media": "attach://hero"
                            }
                        }
                    ]
                });
                let file_name = Path::new(path)
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("hero_banner.png");
                let mime = if file_name.ends_with(".png") { "image/png" } else { "image/jpeg" };
                if let Ok(part) = reqwest::multipart::Part::bytes(bytes).file_name(file_name.to_string()).mime_str(mime) {
                    let form = reqwest::multipart::Form::new()
                        .text("chat_id", chat_id.to_string())
                        .text("message_id", mid.to_string())
                        .text("rich_message", rich_message.to_string())
                        .part("hero", part);
                    if let Ok(res) = client.post(&edit_url).multipart(form).send().await {
                        if let Ok(json) = res.json::<serde_json::Value>().await {
                            let is_ok = json.get("ok").and_then(|v| v.as_bool()) == Some(true);
                            let is_unmodified = json.get("description")
                                .and_then(|d| d.as_str())
                                .map(|s| s.contains("message is not modified"))
                                .unwrap_or(false);
                            if is_ok || is_unmodified {
                                true
                            } else {
                                log::warn!("editMessageText multipart returned error for mid={mid}: {:?}", json);
                                false
                            }
                        } else { false }
                    } else { false }
                } else { false }
            } else { false }
        } else {
            let payload = serde_json::json!({
                "chat_id": chat_id,
                "message_id": mid,
                "rich_message": {
                    "html": html
                }
            });
            if let Ok(res) = client.post(&edit_url).json(&payload).send().await {
                if let Ok(json) = res.json::<serde_json::Value>().await {
                    let is_ok = json.get("ok").and_then(|v| v.as_bool()) == Some(true);
                    let is_unmodified = json.get("description")
                        .and_then(|d| d.as_str())
                        .map(|s| s.contains("message is not modified"))
                        .unwrap_or(false);
                    if is_ok || is_unmodified {
                        true
                    } else {
                        log::warn!("editMessageText json returned error for mid={mid}: {:?}", json);
                        false
                    }
                } else { false }
            } else { false }
        };

        if ok {
            return Ok(mid);
        }
    }

    // Fallback or initial send
    let send_url = format!("https://api.telegram.org/bot{token}/sendRichMessage");
    if has_image {
        let path = img_path.unwrap();
        let bytes = tokio::fs::read(path).await?;
        let rich_message = serde_json::json!({
            "html": html,
            "media": [
                {
                    "id": "hero",
                    "media": {
                        "type": "photo",
                        "media": "attach://hero"
                    }
                }
            ]
        });

        let file_name = Path::new(path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("hero_banner.png");

        let mime = if file_name.ends_with(".png") {
            "image/png"
        } else {
            "image/jpeg"
        };

        let part = reqwest::multipart::Part::bytes(bytes)
            .file_name(file_name.to_string())
            .mime_str(mime)?;

        let form = reqwest::multipart::Form::new()
            .text("chat_id", chat_id.to_string())
            .text("rich_message", rich_message.to_string())
            .part("hero", part);

        let res = client.post(&send_url).multipart(form).send().await?;
        let json: serde_json::Value = res.json().await?;
        if json.get("ok").and_then(|v| v.as_bool()) == Some(true) {
            if let Some(mid) = json.pointer("/result/message_id").and_then(|v| v.as_i64()) {
                return Ok(mid as i32);
            }
            return Ok(0);
        }
        return Err(format!("Rich message API error: {:?}", json).into());
    } else {
        let payload = serde_json::json!({
            "chat_id": chat_id,
            "rich_message": {
                "html": html
            }
        });

        let res = client.post(&send_url).json(&payload).send().await?;
        let json: serde_json::Value = res.json().await?;
        if json.get("ok").and_then(|v| v.as_bool()) == Some(true) {
            if let Some(mid) = json.pointer("/result/message_id").and_then(|v| v.as_i64()) {
                return Ok(mid as i32);
            }
            return Ok(0);
        }
        return Err(format!("Rich message API error: {:?}", json).into());
    }
}

pub async fn send_rich_main_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    first_name: &str,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let tz_str = get_user_timezone(pool, user_id).await;
    let rem = get_user_reminder(pool, user_id).await.unwrap_or(UserReminder {
        reminder_time: "21:00".to_string(),
        reminder_enabled: true,
        timezone: tz_str.clone(),
        last_reminded_date: None,
    });

    let greeting = get_text_fmt("main_greeting", norm, &[("name", &html_escape(first_name))]);
    let sec_label = get_text("main_section_label", norm);
    let lang_label = get_text("main_lang_label", norm);
    let tz_label = get_text("main_tz_label", norm);
    let rem_label = get_text("main_rem_label", norm);
    let status_label = if rem.reminder_enabled {
        get_text("main_status_enabled", norm)
    } else {
        get_text("main_status_disabled", norm)
    };

    let lang_display = match norm {
        "be" => "Беларуская 🇧🇾",
        "ru" => "Русский 🇷🇺",
        "en" => "English 🇬🇧",
        "meme" => "Мемный 🎭",
        "cyberpunk" => "Киберпанк 2077 🦾",
        _ => "Русский 🇷🇺",
    };

    let btn_sos = get_text("btn_sos", norm);
    let btn_stats = get_text("btn_stats", norm);
    let btn_log = get_text("btn_log", norm);
    let btn_status = get_text("btn_status", norm);
    let btn_history = get_text("btn_history", norm);
    let btn_export = get_text("btn_export", norm);
    let btn_reminder = get_text("btn_reminder", norm);
    let btn_language = get_text("btn_language", norm);
    let btn_help = get_text("btn_help", norm);

    let html = format!(
        "<b>KitsuMed 🦊</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {greeting}\n\n\
        <blockquote><b>📋 {sec_label}</b>\n\
        • {lang_label}: <b>{lang_display}</b>\n\
        • {tz_label}: <code>{tz_str}</code>\n\
        • {rem_label}: <b>{}</b> ({status_label})</blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"danger\" data=\"menu:sos\">{btn_sos}</tg-button>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"menu:log\">{btn_log}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:status\">{btn_status}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"menu:stats\">{btn_stats}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:history\">{btn_history}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"menu:export\">{btn_export}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:reminder\">{btn_reminder}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"menu:language\">{btn_language}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:help\">{btn_help}</tg-button>\n\
        </tg-button-row>",
        rem.reminder_time
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_status_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let active = get_active_episode(pool, user_id).await.unwrap_or(None);
    let title = get_text("status_menu_title", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let (content, buttons) = if let Some(ep) = active {
        let ep_id = ep.id;
        let intensity_str = ep.intensity.to_string();
        let level = get_intensity_label(ep.intensity, norm);
        let loc = get_location_name(&ep.location, norm);
        let pt = get_pain_type_name(&ep.pain_type, norm);
        let start = ep.start_time;

        let sec_title = get_text("status_active_title", norm);
        let lbl_start = get_text("status_lbl_start", norm);
        let lbl_intensity = get_text("status_lbl_intensity", norm);
        let lbl_loc = get_text("status_lbl_loc", norm);
        let lbl_pt = get_text("status_lbl_pt", norm);
        let question = get_text("status_question", norm);
        let btn_yes = get_text("status_btn_passed", norm);
        let btn_no = get_text("status_btn_not_passed", norm);

        let block = format!(
            "<blockquote><b>{sec_title}</b>\n\
            • {lbl_start} <b>{start}</b>\n\
            • {lbl_intensity} <b>{intensity_str}/10</b> ({level})\n\
            • {lbl_loc} <b>{loc}</b>\n\
            • {lbl_pt} <b>{pt}</b></blockquote>\n\n\
            <b>{question}</b>"
        );

        let btns = format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" style=\"success\" data=\"fu:pain_passed:{ep_id}\">{btn_yes}</tg-button>\n\
              <tg-button type=\"callback_data\" style=\"danger\" data=\"fu:pain_not_passed:{ep_id}\">{btn_no}</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
            </tg-button-row>"
        );
        (block, btns)
    } else {
        let no_active_txt = get_text("fu_no_active", norm);
        let info_title = get_text("status_no_active_info_title", norm);
        let info_body = get_text("status_no_active_info_body", norm);
        let btn_log = get_text("btn_log", norm);

        let block = format!(
            "{no_active_txt}\n\n\
            <blockquote><b>{info_title}</b>\n\
            {info_body}</blockquote>"
        );
        let btns = format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" style=\"success\" data=\"menu:log\">{btn_log}</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
            </tg-button-row>"
        );
        (block, btns)
    };

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {content}\n\n\
        {buttons}"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_calendar_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    year: i32,
    month: u32,
    selected_day: Option<u32>,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let today = Utc::now().with_timezone(&tz).date_naive();

    let episodes = get_episodes_for_month(pool, user_id, year, month).await.unwrap_or_default();
    let mut pain_days = HashSet::new();
    for ep in &episodes {
        if ep.start_time.len() >= 10 {
            if let Ok(d) = NaiveDate::parse_from_str(&ep.start_time[..10], "%Y-%m-%d") {
                if d.year() == year && d.month() == month {
                    pain_days.insert(d.day());
                }
            }
        }
    }

    let first_day = NaiveDate::from_ymd_opt(year, month, 1).unwrap_or(today);
    let next_month_first = if month == 12 {
        NaiveDate::from_ymd_opt(year + 1, 1, 1).unwrap_or(today)
    } else {
        NaiveDate::from_ymd_opt(year, month + 1, 1).unwrap_or(today)
    };
    let total_days = (next_month_first - first_day).num_days() as u32;

    let (prev_y, prev_m) = if month == 1 { (year - 1, 12) } else { (year, month - 1) };
    let (next_y, next_m) = if month == 12 { (year + 1, 1) } else { (year, month + 1) };

    let month_name = crate::keyboards::get_month_name(year, month, norm);
    let pain_count = pain_days.len();
    let healthy_count = (total_days as usize).saturating_sub(pain_count);

    let mut selected_info = String::new();
    if let Some(day) = selected_day {
        let day_eps = get_episodes_for_date(pool, user_id, year, month, day).await.unwrap_or_default();
        if day_eps.is_empty() {
            let empty_text = get_text("calendar_empty_day", norm);
            selected_info = format!(
                "<blockquote><b>📋 {day:02}.{month:02}.{year}</b>\n\
                {empty_text}</blockquote>\n\n"
            );
        } else {
            let mut cards = Vec::new();
            for ep in &day_eps {
                let card = crate::handlers::calendar::format_episode_card(ep, norm);
                cards.push(card);
            }
            let joined = cards.join("\n———\n");
            let title_eps = get_text_fmt(
                "calendar_day_eps_title",
                norm,
                &[
                    ("date", &format!("{day:02}.{month:02}.{year}")),
                    ("count", &day_eps.len().to_string()),
                ],
            );
            selected_info = format!(
                "<blockquote><b>{title_eps}</b>\n\
                {joined}</blockquote>\n\n"
            );
        }
    }

    let mut grid_html = String::new();

    // Nav row
    grid_html.push_str(&format!(
        "<tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"cal:nav:{prev_y}:{prev_m}\">◀️</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"cal:ignore\">{month_name} {year}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"cal:nav:{next_y}:{next_m}\">▶️</tg-button>\n\
        </tg-button-row>\n"
    ));

    // DOW row
    let dows = match norm {
        "be" => ["Пн", "Аў", "Ср", "Чц", "Пт", "Сб", "Нд"],
        "en" => ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        _ => ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    };
    grid_html.push_str("<tg-button-row>\n");
    for dow in dows {
        grid_html.push_str(&format!("  <tg-button type=\"callback_data\" data=\"cal:ignore\">{dow}</tg-button>\n"));
    }
    grid_html.push_str("</tg-button-row>\n");

    let start_weekday = first_day.weekday().number_from_monday();
    let mut current_row_len = 0;

    grid_html.push_str("<tg-button-row>\n");

    // Leading empty days
    for _ in 1..start_weekday {
        grid_html.push_str("  <tg-button type=\"callback_data\" data=\"cal:ignore\"> </tg-button>\n");
        current_row_len += 1;
    }

    for day in 1..=total_days {
        if current_row_len == 7 {
            grid_html.push_str("</tg-button-row>\n<tg-button-row>\n");
            current_row_len = 0;
        }

        let is_pain = pain_days.contains(&day);
        let is_today = today.year() == year && today.month() == month && today.day() == day;

        if is_pain {
            grid_html.push_str(&format!(
                "  <tg-button type=\"callback_data\" style=\"danger\" data=\"cal:day:{year}:{month}:{day}\">🔴{day}</tg-button>\n"
            ));
        } else if is_today {
            grid_html.push_str(&format!(
                "  <tg-button type=\"callback_data\" style=\"primary\" data=\"cal:day:{year}:{month}:{day}\">·{day}·</tg-button>\n"
            ));
        } else {
            grid_html.push_str(&format!(
                "  <tg-button type=\"callback_data\" data=\"cal:day:{year}:{month}:{day}\">{day}</tg-button>\n"
            ));
        }
        current_row_len += 1;
    }

    if current_row_len > 0 {
        while current_row_len < 7 {
            grid_html.push_str("  <tg-button type=\"callback_data\" data=\"cal:ignore\"> </tg-button>\n");
            current_row_len += 1;
        }
        grid_html.push_str("</tg-button-row>\n");
    }

    let btn_today = get_text("calendar_btn_today_rich", norm);
    let btn_menu = get_text("btn_main_menu", norm);
    let stat_header = get_text("calendar_stat_header", norm);
    let lbl_pain = get_text("calendar_lbl_pain", norm);
    let lbl_healthy = get_text("calendar_lbl_healthy", norm);
    let cal_title = format!("{month_name} {year}");

    if let Some(day) = selected_day {
        let btn_add_day = get_text("cal_btn_add_day", norm);
        grid_html.push_str(&format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" style=\"success\" data=\"cal:add:{year}:{month}:{day}\">{btn_add_day} ({day:02}.{month:02})</tg-button>\n\
            </tg-button-row>\n"
        ));
    }

    grid_html.push_str(&format!(
        "<tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"cal:today\">{btn_today}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    ));

    let html = format!(
        "<b>{cal_title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        <blockquote><b>{stat_header}</b>\n\
        • {lbl_pain} <b>{pain_count}</b> 🔴\n\
        • {lbl_healthy} <b>{healthy_count}</b> 🟢</blockquote>\n\n\
        {selected_info}\
        {grid_html}"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_export_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let episodes = get_all_episodes(pool, user_id).await.unwrap_or_default();
    let count = episodes.len();

    let title = get_text("export_rich_title", norm);
    let desc = get_text_fmt("export_rich_desc", norm, &[("count", &count.to_string())]);
    let desc_block = get_text("export_rich_desc_block", norm);
    let btn_csv = get_text("export_rich_btn_csv", norm);
    let btn_pdf = get_text("export_rich_btn_pdf", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {desc}\n\n\
        <blockquote>{desc_block}</blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"hde:csv\">{btn_csv}</tg-button>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"hde:pdf\">{btn_pdf}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_reminder_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let local_time = Utc::now().with_timezone(&tz).format("%H:%M").to_string();

    let rem = get_user_reminder(pool, user_id).await.unwrap_or(UserReminder {
        reminder_time: "21:00".to_string(),
        reminder_enabled: true,
        timezone: tz_str.clone(),
        last_reminded_date: None,
    });

    let title = get_text("reminder_rich_title", norm);
    let sec_title = get_text("reminder_rich_sec", norm);
    let lbl_status = get_text("reminder_rich_lbl_status", norm);
    let lbl_time = get_text("reminder_rich_lbl_time", norm);
    let lbl_tz = get_text("reminder_rich_lbl_tz", norm);

    let (status_text, toggle_text, toggle_style) = if rem.reminder_enabled {
        (
            get_text("main_status_enabled", norm),
            get_text("reminder_rich_toggle_off", norm),
            "danger",
        )
    } else {
        (
            get_text("main_status_disabled", norm),
            get_text("reminder_rich_toggle_on", norm),
            "success",
        )
    };

    let btn_time = get_text("reminder_rich_btn_time", norm);
    let btn_tz = get_text("reminder_rich_btn_tz", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        <blockquote><b>{sec_title}</b>\n\
        • {lbl_status} <b>{status_text}</b>\n\
        • {lbl_time} <b>{}</b>\n\
        • {lbl_tz} <b>{tz_str}</b> ({local_time})</blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"{toggle_style}\" data=\"rem:toggle\">{toggle_text}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"rem:time\">{btn_time}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"rem:tz\">{btn_tz}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>",
        rem.reminder_time
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_reminder_time_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("reminder_time_title", norm);
    let sub = get_text("reminder_time_sub", norm);
    let btn_custom = get_text("reminder_time_btn_custom", norm);
    let btn_back = get_text("reminder_time_btn_back", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {sub}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"rem:set_time:20:00\">20:00</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"rem:set_time:21:00\">21:00</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"rem:set_time:22:00\">22:00</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"rem:time_custom\">{btn_custom}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:reminder\">{btn_back}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_timezone_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let local_time = Utc::now().with_timezone(&tz).format("%H:%M").to_string();

    let title = get_text("tz_rich_title", norm);
    let sub = get_text_fmt("tz_rich_sub", norm, &[("tz", &tz_str), ("time", &local_time)]);
    let btn_custom = get_text("tz_rich_btn_custom", norm);
    let btn_back = get_text("tz_rich_btn_back", norm);

    let tz_rows = if norm == "be" {
        format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Minsk\">Мінск (UTC+3)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Moscow\">Масква (UTC+3)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Warsaw\">Варшава (UTC+1)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Vilnius\">Вільнюс (UTC+2)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Kiev\">Кіеў (UTC+2)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Asia/Tbilisi\">Тбілісі (UTC+4)</tg-button>\n\
            </tg-button-row>\n"
        )
    } else if norm == "en" {
        format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/London\">London (UTC+0)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Berlin\">Berlin/Paris (UTC+1)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:America/New_York\">New York (UTC-5)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:America/Los_Angeles\">Los Angeles (UTC-8)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Asia/Dubai\">Dubai (UTC+4)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Asia/Tokyo\">Tokyo (UTC+9)</tg-button>\n\
            </tg-button-row>\n"
        )
    } else {
        format!(
            "<tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Moscow\">Москва (UTC+3)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Minsk\">Минск (UTC+3)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Kaliningrad\">Калининград (UTC+2)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Europe/Samara\">Самара (UTC+4)</tg-button>\n\
            </tg-button-row>\n\
            <tg-button-row>\n\
              <tg-button type=\"callback_data\" data=\"tz:Asia/Yekaterinburg\">Екатеринбург (UTC+5)</tg-button>\n\
              <tg-button type=\"callback_data\" data=\"tz:Asia/Novosibirsk\">Новосибирск (UTC+7)</tg-button>\n\
            </tg-button-row>\n"
        )
    };

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {sub}\n\n\
        {tz_rows}\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"rem:tz_custom\">{btn_custom}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:reminder\">{btn_back}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_language_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("lang_rich_title", norm);
    let block = get_text("lang_rich_block", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        <blockquote>{block}</blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"lang:ru\">🇷🇺 Русский</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"lang:be\">🇧🇾 Беларуская</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"lang:en\">🇬🇧 English</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"lang:meme\">🎭 Мемный</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"lang:cyberpunk\">🦾 Киберпанк 2077</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_help_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("help_rich_title", norm);
    let block_title = get_text("help_rich_block_title", norm);
    let help_items = get_text("help_rich_items", norm);
    let btn_log = get_text("help_rich_btn_log", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        <blockquote><b>{block_title}</b>\n\
        {help_items}</blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"menu:log\">{btn_log}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_daily_reminder(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("daily_rem_title", norm);
    let desc = get_text("daily_rem_desc", norm);
    let btn_ok = get_text("daily_rem_btn_ok", norm);
    let btn_pain = get_text("daily_rem_btn_pain", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {desc}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"remp:ok\">{btn_ok}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"danger\" data=\"remp:log\">{btn_pain}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_daily_reminder_saved(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("daily_saved_title", norm);
    let text = get_text("daily_saved_text", norm);
    let btn_menu = get_text("btn_main_menu", norm);
    let btn_cal = get_text("btn_open_calendar", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {text}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:calendar\">{btn_cal}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_followup_prompt(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    ep_id: i32,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("fu_prompt_title", norm);
    let desc = get_text("fu_prompt_desc", norm);
    let btn_yes = get_text("fu_prompt_btn_yes", norm);
    let btn_no = get_text("fu_prompt_btn_no", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {desc}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"fu:pain_passed:{ep_id}\">{btn_yes}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"danger\" data=\"fu:pain_not_passed:{ep_id}\">{btn_no}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_followup_when(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    ep_id: i32,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("fu_when_title", norm);
    let sub = get_text("fu_when_sub", norm);
    let t1 = get_text("fu_when_now_rich", norm);
    let t2 = get_text("fu_when_30m_rich", norm);
    let t3 = get_text("fu_when_1h_rich", norm);
    let t4 = get_text("fu_when_2h_rich", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {sub}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"fu:set_when:{ep_id}:now\">{t1}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"fu:set_when:{ep_id}:-30m\">{t2}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"fu:set_when:{ep_id}:-1h\">{t3}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"fu:set_when:{ep_id}:-2h\">{t4}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_followup_med(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    ep_id: i32,
    med_name: &str,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);
    let med_safe = html_escape(med_name);

    let title = get_text("fu_med_title", norm);
    let sub = get_text_fmt("fu_med_sub", norm, &[("med", &med_safe)]);
    let btn_yes = get_text("fu_med_yes_rich", norm);
    let btn_part = get_text("fu_med_part_rich", norm);
    let btn_no = get_text("fu_med_no_rich", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {sub}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"fu:med_relief:{ep_id}:helped\">{btn_yes}</tg-button>\n\
          <tg-button type=\"callback_data\" data=\"fu:med_relief:{ep_id}:partially\">{btn_part}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"danger\" data=\"fu:med_relief:{ep_id}:not_helped\">{btn_no}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_followup_result(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    text: &str,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("fu_result_title", norm);
    let btn_menu = get_text("btn_main_menu", norm);
    let btn_cal = get_text("btn_open_calendar", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {text}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:calendar\">{btn_cal}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn render_rich_headache_step(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    form: &HeadacheForm,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);
    let step = form.current_step.clone().unwrap_or(FlowStep::StartTime);

    let btn_back = get_text("btn_back", norm);
    let btn_cancel = get_text("btn_cancel", norm);

    let html = match step {
        FlowStep::StartTime => {
            let title = get_text("step1_rich_title", norm);
            let sub = get_text("step1_rich_sub", norm);
            let st1 = get_text("step1_t1", norm);
            let st2 = get_text("step1_t2", norm);
            let st3 = get_text("step1_t3", norm);
            let st4 = get_text("step1_t4", norm);
            let st_yesterday = get_text("step1_yesterday", norm);
            let st_custom = get_text("step1_custom", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {sub}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:now\">{st1}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:-30m\">{st2}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:-1h\">{st3}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:-2h\">{st4}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:yesterday\">{st_yesterday}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdt:custom\">{st_custom}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Intensity => {
            let now_default = get_text("step1_t1", norm);
            let time_str = form.start_time.as_deref().unwrap_or(&now_default);
            let title = get_text("step2_rich_title", norm);
            let lbl_start = get_text("step2_rich_lbl_start", norm);
            let prompt_txt = get_text("step2_rich_prompt", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                • {lbl_start} <code>{time_str}</code>\n\n\
                {prompt_txt}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:1\">1</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:2\">2</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:3\">3</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:4\">4</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:5\">5</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:6\">6</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:7\">7</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:8\">8</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdi:9\">9</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdi:10\">10 🔥</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Location => {
            let intensity = form.intensity.unwrap_or(5);
            let level = get_intensity_label(intensity, &lang);

            let title = get_text("step3_rich_title", norm);
            let lbl_pain = get_text("step3_rich_lbl_pain", norm);
            let prompt_txt = get_text("step3_rich_prompt", norm);

            let b_left = get_text("step3_left", norm);
            let b_right = get_text("step3_right", norm);
            let b_both = get_text("step3_both", norm);
            let b_diff = get_text("step3_diff", norm);
            let b_fore = get_text("step3_fore", norm);
            let b_back = get_text("step3_back", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                • {lbl_pain} <b>{intensity}/10</b> ({level})\n\n\
                {prompt_txt}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:left\">{b_left}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:right\">{b_right}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:both\">{b_both}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:diffuse\">{b_diff}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:forehead\">{b_fore}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdl:back_head\">{b_back}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::PainType => {
            let loc = form.location.as_deref().unwrap_or("both");
            let loc_text = get_location_name(loc, &lang);

            let title = get_text("step4_rich_title", norm);
            let lbl_loc = get_text("step4_rich_lbl_loc", norm);
            let prompt_txt = get_text("step4_rich_prompt", norm);

            let b_throb = get_text("step4_throb", norm);
            let b_press = get_text("step4_press", norm);
            let b_stab = get_text("step4_stab", norm);
            let b_dull = get_text("step4_dull", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                • {lbl_loc} <b>{loc_text}</b>\n\n\
                {prompt_txt}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdp:throbbing\">{b_throb}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdp:pressing\">{b_press}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdp:stabbing\">{b_stab}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdp:dull\">{b_dull}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Symptoms => {
            let syms = &form.symptoms;
            let is_sel = |s: &str| syms.iter().any(|x| x == s);
            let make_btn = |key: &str, label: &str| {
                if is_sel(key) {
                    format!("<tg-button type=\"callback_data\" style=\"primary\" data=\"hds:toggle:{key}\">✅ {label}</tg-button>")
                } else {
                    format!("<tg-button type=\"callback_data\" data=\"hds:toggle:{key}\">{label}</tg-button>")
                }
            };

            let pt = form.pain_type.as_deref().unwrap_or("throbbing");
            let pt_text = get_pain_type_name(pt, &lang);

            let title = get_text("step5_rich_title", norm);
            let lbl_type = get_text("step5_rich_lbl_type", norm);
            let prompt_txt = get_text("step5_rich_prompt", norm);
            let btn_none = get_text("step5_none", norm);
            let btn_next = get_text("btn_next", norm);

            let b1 = make_btn("nausea", &get_text("step5_b1", norm));
            let b2 = make_btn("vomiting", &get_text("step5_b2", norm));
            let b3 = make_btn("photophobia", &get_text("step5_b3", norm));
            let b4 = make_btn("phonophobia", &get_text("step5_b4", norm));
            let b5 = make_btn("aura", &get_text("step5_b5", norm));
            let b6 = make_btn("dizziness", &get_text("step5_b6", norm));

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                • {lbl_type} <b>{pt_text}</b>\n\n\
                {prompt_txt}\n\n\
                <tg-button-row>\n  {b1}\n  {b2}\n</tg-button-row>\n\
                <tg-button-row>\n  {b3}\n  {b4}\n</tg-button-row>\n\
                <tg-button-row>\n  {b5}\n  {b6}\n</tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hds:none\">{btn_none}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"success\" data=\"hds:done\">{btn_next}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Triggers => {
            let trigs = &form.triggers;
            let is_sel = |t: &str| trigs.iter().any(|x| x == t);
            let make_btn = |key: &str, label: &str| {
                if is_sel(key) {
                    format!("<tg-button type=\"callback_data\" style=\"primary\" data=\"hdtr:toggle:{key}\">✅ {label}</tg-button>")
                } else {
                    format!("<tg-button type=\"callback_data\" data=\"hdtr:toggle:{key}\">{label}</tg-button>")
                }
            };

            let title = get_text("step6_rich_title", norm);
            let prompt_txt = get_text("step6_rich_prompt", norm);
            let btn_none = get_text("step6_none", norm);
            let btn_next = get_text("btn_next", norm);

            let b1 = make_btn("stress", &get_text("step6_b1", norm));
            let b2 = make_btn("lack_of_sleep", &get_text("step6_b2", norm));
            let b3 = make_btn("weather", &get_text("step6_b3", norm));
            let b4 = make_btn("fatigue", &get_text("step6_b4", norm));
            let b5 = make_btn("alcohol", &get_text("step6_b5", norm));
            let b6 = make_btn("skip_food", &get_text("step6_b6", norm));

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {prompt_txt}\n\n\
                <tg-button-row>\n  {b1}\n  {b2}\n</tg-button-row>\n\
                <tg-button-row>\n  {b3}\n  {b4}\n</tg-button-row>\n\
                <tg-button-row>\n  {b5}\n  {b6}\n</tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdtr:none\">{btn_none}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"success\" data=\"hdtr:done\">{btn_next}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Medication => {
            let title = get_text("step7_rich_title", norm);
            let btn_none = get_text("step7_btn_none", norm);

            let saved_meds = crate::db::get_user_medications(pool, user_id).await;

            let (sub, btn_custom) = if saved_meds.is_empty() {
                (
                    get_text("step7_rich_sub_empty", norm),
                    get_text("step7_btn_custom", norm),
                )
            } else {
                (
                    get_text("step7_rich_sub", norm),
                    get_text("step7_btn_custom_more", norm),
                )
            };

            let mut med_rows = String::new();
            for med in saved_meds {
                let escaped_name = html_escape(&med.name);
                med_rows.push_str(&format!(
                    "<tg-button-row>\n  <tg-button type=\"callback_data\" data=\"hdm:id:{id}\">💊 {escaped_name}</tg-button>\n</tg-button-row>\n",
                    id = med.id,
                    escaped_name = escaped_name
                ));
            }

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {sub}\n\n\
                {med_rows}\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" style=\"primary\" data=\"hdm:custom\">{btn_custom}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdm:none\">{btn_none}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::MedicationTime => {
            let med_name = form.medication.as_deref().unwrap_or("none");
            let med_text = get_medication_name(med_name, &lang);

            let title = get_text_fmt("step8_time_title", norm, &[("med", &med_text)]);
            let sub = get_text("step8_time_sub", norm);
            let t1 = get_text("step8_t1", norm);
            let t2 = get_text("step8_t2", norm);
            let t3 = get_text("step8_t3", norm);
            let t4 = get_text("step8_t4", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {sub}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdmt:0m\">{t1}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdmt:30m\">{t2}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdmt:1h\">{t3}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdmt:2h\">{t4}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::MedicationRelief => {
            let med_name = form.medication.as_deref().unwrap_or("none");
            let med_text = get_medication_name(med_name, &lang);

            let title = get_text_fmt("step8_relief_title", norm, &[("med", &med_text)]);
            let sub = get_text("step8_relief_sub", norm);
            let r1 = get_text("step8_r1", norm);
            let r2 = get_text("step8_r2", norm);
            let r3 = get_text("step8_r3", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {sub}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" style=\"success\" data=\"hdmr:helped\">{r1}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdmr:partially\">{r2}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdmr:not_helped\">{r3}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::ReliefTime => {
            let title = get_text("step8_dur_title", norm);
            let sub = get_text("step8_dur_sub", norm);
            let d1 = get_text("step8_d1", norm);
            let d2 = get_text("step8_d2", norm);
            let d3 = get_text("step8_d3", norm);
            let d4 = get_text("step8_d4", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                {sub}\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdmrt:30m\">{d1}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdmrt:1h\">{d2}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdmrt:2h\">{d3}</tg-button>\n\
                  <tg-button type=\"callback_data\" data=\"hdmrt:4h\">{d4}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdn:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }

        FlowStep::Confirm => {
            let start_time = form.start_time.clone().unwrap_or_else(|| "—".to_string());
            let intensity = form.intensity.unwrap_or(5);
            let level = get_intensity_label(intensity, &lang);

            let loc = form.location.as_deref().unwrap_or("diffuse");
            let loc_text = get_location_name(loc, &lang);

            let pt = form.pain_type.as_deref().unwrap_or("throbbing");
            let pt_text = get_pain_type_name(pt, &lang);

            let sym_list = if form.symptoms.is_empty() || form.symptoms.contains(&"none".to_string()) {
                "—".to_string()
            } else {
                let v: Vec<String> = form.symptoms.iter().map(|s| get_symptom_name(s, &lang)).collect();
                v.join(", ")
            };

            let trig_list = if form.triggers.is_empty() || form.triggers.contains(&"none".to_string()) {
                "—".to_string()
            } else {
                let v: Vec<String> = form.triggers.iter().map(|t| get_trigger_name(t, &lang)).collect();
                v.join(", ")
            };

            let med = form.medication.as_deref().unwrap_or("none");
            let med_text = get_medication_name(med, &lang);

            let is_resolved = form.medication_relief.as_deref() == Some("helped");
            let dur = form.relief_delay.as_deref().unwrap_or("1h");
            let dur_str = format_duration_label(dur, norm);

            let title = get_text("confirm_rich_title", norm);
            let block_title = get_text("confirm_rich_block_title", norm);
            let status_line = if is_resolved {
                get_text_fmt("confirm_status_resolved", norm, &[("dur", &dur_str)])
            } else {
                get_text("confirm_status_active", norm)
            };

            let lbl_status = get_text("confirm_lbl_status", norm);
            let lbl_start = get_text("confirm_lbl_start", norm);
            let lbl_pain = get_text("confirm_lbl_pain", norm);
            let lbl_loc = get_text("confirm_lbl_loc", norm);
            let lbl_type = get_text("confirm_lbl_type", norm);
            let lbl_sym = get_text("confirm_lbl_sym", norm);
            let lbl_trig = get_text("confirm_lbl_trig", norm);
            let lbl_med = get_text("confirm_lbl_med", norm);
            let prompt_save = get_text("confirm_prompt", norm);
            let btn_save = get_text("confirm_btn_save", norm);

            format!(
                "<b>{title}</b>\n\n\
                <img src=\"tg://photo?id=hero\">\n\n\
                <blockquote><b>{block_title}</b>\n\
                • {lbl_status} {status_line}\n\
                • {lbl_start} <code>{start_time}</code>\n\
                • {lbl_pain} <b>{intensity}/10</b> ({level})\n\
                • {lbl_loc} <b>{loc_text}</b>\n\
                • {lbl_type} <b>{pt_text}</b>\n\
                • {lbl_sym} {sym_list}\n\
                • {lbl_trig} {trig_list}\n\
                • {lbl_med} <b>{med_text}</b></blockquote>\n\n\
                <b>{prompt_save}</b>\n\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" style=\"success\" data=\"hdc:save\">{btn_save}</tg-button>\n\
                </tg-button-row>\n\
                <tg-button-row>\n\
                  <tg-button type=\"callback_data\" data=\"hdn:back\">{btn_back}</tg-button>\n\
                  <tg-button type=\"callback_data\" style=\"danger\" data=\"hdc:cancel\">{btn_cancel}</tg-button>\n\
                </tg-button-row>"
            )
        }
    };

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_headache_saved(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    ep_id: i32,
    form: &HeadacheForm,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let is_completed = form.medication_relief.as_deref() == Some("helped");
    let dur = form.relief_delay.as_deref().unwrap_or("30m");
    let dur_str = format_duration_label(dur, norm);

    let (title, text) = if is_completed {
        (
            get_text("saved_completed_title", norm),
            get_text_fmt("saved_completed_text", norm, &[("id", &ep_id.to_string()), ("dur", &dur_str)]),
        )
    } else {
        (
            get_text("saved_active_title", norm),
            get_text_fmt("saved_active_text", norm, &[("id", &ep_id.to_string())]),
        )
    };

    let mut moh_warning = String::new();
    if let Some(ref med) = form.medication {
        if !med.is_empty() && med != "none" {
            let med_days = crate::db::get_monthly_medication_days(pool, user_id).await.unwrap_or(0);
            if med_days >= 10 {
                let warn_title = get_text("moh_alert_title", norm);
                let warn_body = get_text_fmt("moh_alert_body", norm, &[("days", &med_days.to_string())]);
                moh_warning = format!("\n\n<blockquote><b>⚠️ {warn_title}</b>\n{warn_body}</blockquote>");
            } else if med_days >= 8 {
                let warn_title = get_text("moh_caution_title", norm);
                let warn_body = get_text_fmt("moh_caution_body", norm, &[("days", &med_days.to_string())]);
                moh_warning = format!("\n\n<blockquote><b>⚡ {warn_title}</b>\n{warn_body}</blockquote>");
            }
        }
    }

    let btn_menu = get_text("btn_main_menu", norm);
    let btn_cal = get_text("btn_open_calendar", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {text}{moh_warning}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:calendar\">{btn_cal}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_sos_prompt(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("sos_prompt_title", norm);
    let desc = get_text("sos_prompt_desc", norm);
    let btn_none = get_text("step7_btn_none", norm);
    let btn_custom = get_text("step7_btn_custom", norm);
    let btn_cancel = get_text("btn_cancel", norm);

    let saved_meds = crate::db::get_user_medications(pool, user_id).await;

    let mut med_rows = String::new();
    for med in saved_meds {
        let escaped = html_escape(&med.name);
        med_rows.push_str(&format!(
            "<tg-button-row>\n  <tg-button type=\"callback_data\" data=\"sosm:id:{id}\">💊 {escaped}</tg-button>\n</tg-button-row>\n",
            id = med.id,
            escaped = escaped
        ));
    }

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {desc}\n\n\
        {med_rows}\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"sosm:custom\">{btn_custom}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"sosm:none\">{btn_none}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"danger\" data=\"menu:main\">{btn_cancel}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_sos_saved(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    ep_id: i32,
    medication: &str,
    weather_str: Option<&str>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("sos_saved_title", norm);
    let desc = get_text("sos_saved_desc", norm);
    let med_display = if medication == "none" || medication.is_empty() {
        get_text("step7_btn_none", norm)
    } else {
        html_escape(medication)
    };

    let weather_line = if let Some(w) = weather_str {
        format!("\n• Погода: <code>{}</code>", html_escape(w))
    } else {
        String::new()
    };

    let mut moh_warning = String::new();
    if medication != "none" && !medication.is_empty() {
        let med_days = crate::db::get_monthly_medication_days(pool, user_id).await.unwrap_or(0);
        if med_days >= 10 {
            let warn_title = get_text("moh_alert_title", norm);
            let warn_body = get_text_fmt("moh_alert_body", norm, &[("days", &med_days.to_string())]);
            moh_warning = format!("\n\n<blockquote><b>⚠️ {warn_title}</b>\n{warn_body}</blockquote>");
        } else if med_days >= 8 {
            let warn_title = get_text("moh_caution_title", norm);
            let warn_body = get_text_fmt("moh_caution_body", norm, &[("days", &med_days.to_string())]);
            moh_warning = format!("\n\n<blockquote><b>⚡ {warn_title}</b>\n{warn_body}</blockquote>");
        }
    }

    let btn_menu = get_text("btn_main_menu", norm);
    let btn_cal = get_text("btn_open_calendar", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        <blockquote><b>📋 SOS Приступ #{ep_id}</b>\n\
        • Статус: 🔴 <b>Активен</b>\n\
        • Интенсивность: <b>8/10 (Сильная)</b>\n\
        • Препарат: <b>{med_display}</b>{weather_line}</blockquote>\n\n\
        {desc}{moh_warning}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:calendar\">{btn_cal}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_analytics_menu(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let report = crate::services::analytics::generate_analytics_report(pool, user_id, &lang)
        .await
        .unwrap_or(crate::services::analytics::AnalyticsReport {
            total_episodes_30d: 0,
            pain_days_30d: 0,
            avg_intensity: 0.0,
            medication_days_30d: 0,
            moh_risk: crate::services::analytics::MohRisk::Safe,
            medication_efficacy_pct: None,
            top_triggers: vec![],
            top_symptoms: vec![],
            peak_weekday: None,
            avg_pressure_mmhg: None,
        });

    let title = get_text("stats_rich_title", norm);
    let sub = get_text("stats_rich_sub", norm);
    let btn_export = get_text("btn_export", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let moh_badge = match report.moh_risk {
        crate::services::analytics::MohRisk::Safe => "🟢 В норме (<8 дн.)",
        crate::services::analytics::MohRisk::Caution => "🟡 Внимание (8-9 дн.)",
        crate::services::analytics::MohRisk::Alert => "🔴 Риск абузуса (≥10 дн.)",
    };

    let triggers_text = if report.top_triggers.is_empty() {
        "• <i>Данных по триггерам пока недостаточно</i>".to_string()
    } else {
        report.top_triggers.iter()
            .map(|(name, count, pct)| format!("• ⚡ <b>{}</b>: {} раз ({}%)", html_escape(name), count, pct))
            .collect::<Vec<_>>()
            .join("\n")
    };

    let symptoms_text = if report.top_symptoms.is_empty() {
        "• <i>Симптомы пока не фиксировались</i>".to_string()
    } else {
        report.top_symptoms.iter()
            .map(|(name, count, pct)| format!("• 🔹 <b>{}</b>: {} раз ({}%)", html_escape(name), count, pct))
            .collect::<Vec<_>>()
            .join("\n")
    };

    let efficacy_str = if let Some(eff) = report.medication_efficacy_pct {
        format!("{}%", eff)
    } else {
        "—".to_string()
    };

    let peak_str = if let Some((ref wd, count)) = report.peak_weekday {
        format!("{} ({} прист.)", wd, count)
    } else {
        "—".to_string()
    };

    let pressure_str = if let Some(p) = report.avg_pressure_mmhg {
        format!("{} мм рт. ст.", p)
    } else {
        "—".to_string()
    };

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {sub}\n\n\
        <blockquote><b>📊 Сводка за последние 30 дней</b>\n\
        • Всего приступов: <b>{}</b>\n\
        • Дней с болью: <b>{}</b>\n\
        • Средняя сила боли: <b>{:.1}/10</b>\n\
        • Пиковый день: <b>{}</b></blockquote>\n\n\
        <blockquote><b>⚡ Радар провоцирующих триггеров</b>\n\
        {triggers_text}</blockquote>\n\n\
        <blockquote><b>🩺 Симптомы и течение</b>\n\
        {symptoms_text}</blockquote>\n\n\
        <blockquote><b>💊 Лекарственный контроль & MOH</b>\n\
        • Дней приема лекарств: <b>{}/10</b> ({moh_badge})\n\
        • Эффективность купирования: <b>{}</b>\n\
        • Ср. давление при боли: <b>{}</b></blockquote>\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"success\" data=\"menu:export\">{btn_export}</tg-button>\n\
        </tg-button-row>\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>",
        report.total_episodes_30d,
        report.pain_days_30d,
        report.avg_intensity,
        peak_str,
        report.medication_days_30d,
        efficacy_str,
        pressure_str
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}

pub async fn send_rich_headache_cancelled(
    token: &str,
    chat_id: i64,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
) -> Result<i32, Box<dyn std::error::Error + Send + Sync>> {
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let title = get_text("cancelled_title", norm);
    let text = get_text("cancelled_text", norm);
    let btn_menu = get_text("btn_main_menu", norm);

    let html = format!(
        "<b>{title}</b>\n\n\
        <img src=\"tg://photo?id=hero\">\n\n\
        {text}\n\n\
        <tg-button-row>\n\
          <tg-button type=\"callback_data\" style=\"primary\" data=\"menu:main\">{btn_menu}</tg-button>\n\
        </tg-button-row>"
    );

    let img_path = format!("assets/images/{norm}/hero_banner.png");
    send_or_edit_rich_raw(token, chat_id, message_id, &html, Some(&img_path)).await
}
