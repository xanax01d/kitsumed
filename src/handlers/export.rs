use std::str::FromStr;
use chrono::Utc;
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, InputFile, ParseMode};

use crate::db::{get_all_episodes, get_user_language, get_user_timezone};
use crate::locales::{get_text, get_text_fmt};
use crate::services::export::generate_csv;

pub async fn handle_export_cmd(bot: &Bot, msg: &Message, pool: &PgPool) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    let _ = crate::rich::send_rich_export_menu(bot.token(), msg.chat.id.0, None, user_id, pool).await;
    Ok(())
}

pub async fn handle_export_callback(
    bot: &Bot,
    q: &CallbackQuery,
    _format: &str,
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

    let csv_bytes = generate_csv(&episodes, &lang);
    let filename = format!("migrebot_diary_{date_str}.csv");
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
            .caption(caption).parse_mode(ParseMode::Html)
            .await;
    }

    Ok(())
}
