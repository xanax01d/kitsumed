use std::str::FromStr;
use chrono::Utc;
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, InputFile, ParseMode};

use crate::db::{get_all_episodes, get_user_language, get_user_timezone};
use crate::locales::{get_text, get_text_fmt};
use crate::services::export::{generate_csv, generate_pdf};
use crate::session::SessionStore;

pub async fn handle_export_cmd(
    bot: &Bot,
    msg: &Message,
    pool: &PgPool,
    sessions: &SessionStore,
    mid: Option<i32>,
) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    let target_mid = match mid {
        Some(m) => Some(m),
        None => sessions.get_last_mid(user_id).await,
    };
    if let Ok(new_mid) = crate::rich::send_rich_export_menu(bot.token(), msg.chat.id.0, target_mid, user_id, pool).await {
        sessions.set_last_mid(user_id, new_mid).await;
    }
    Ok(())
}

pub async fn handle_export_callback(
    bot: &Bot,
    q: &CallbackQuery,
    format_type: &str,
    pool: &PgPool,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let lang = get_user_language(pool, user_id).await;
    let episodes = get_all_episodes(pool, user_id).await.unwrap_or_default();

    if episodes.is_empty() {
        let _ = bot.answer_callback_query(&q.id)
            .text(get_text("export_empty", &lang))
            .await;
        return Ok(());
    }

    let _ = bot.answer_callback_query(&q.id)
        .text("Формирую отчет...")
        .await;

    let tz_str = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_str).unwrap_or(chrono_tz::Europe::Moscow);
    let now = Utc::now().with_timezone(&tz);
    let date_str = now.format("%Y%m%d_%H%M").to_string();
    let formatted_now = now.format("%d.%m.%Y %H:%M").to_string();

    if format_type == "pdf" {
        match generate_pdf(&episodes, user_id, &formatted_now, &lang).await {
            Ok(pdf_bytes) => {
                let filename = format!("kitsumed_diary_{date_str}.pdf");
                let doc = InputFile::memory(pdf_bytes).file_name(filename);
                let caption = get_text_fmt(
                    "export_caption_pdf",
                    &lang,
                    &[
                        ("count", &episodes.len().to_string()),
                        ("date", &formatted_now),
                    ],
                );
                if let Some(msg) = q.regular_message() {
                    let _ = bot.send_document(msg.chat.id, doc)
                        .caption(caption)
                        .parse_mode(ParseMode::Html)
                        .await;
                }
            }
            Err(e) => {
                log::error!("Failed to generate PDF for user {user_id}: {e}");
                if let Some(msg) = q.regular_message() {
                    let _ = bot.send_message(msg.chat.id, "⚠️ Ошибка при формировании PDF отчета. Попробуйте CSV.").await;
                }
            }
        }
    } else {
        let csv_bytes = generate_csv(&episodes, &lang);
        let filename = format!("kitsumed_diary_{date_str}.csv");
        let doc = InputFile::memory(csv_bytes).file_name(filename);

        let caption = get_text_fmt(
            "export_caption_csv",
            &lang,
            &[
                ("count", &episodes.len().to_string()),
                ("date", &formatted_now),
            ],
        );

        if let Some(msg) = q.regular_message() {
            let _ = bot.send_document(msg.chat.id, doc)
                .caption(caption)
                .parse_mode(ParseMode::Html)
                .await;
        }
    }

    Ok(())
}
