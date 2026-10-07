use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::CallbackQuery;

use crate::db::{set_user_language, upsert_user};

pub async fn handle_language_cmd(bot: &Bot, msg: &Message, pool: &PgPool) -> ResponseResult<()> {
    let user_id = msg.from.as_ref().map(|u| u.id.0 as i64).unwrap_or(0);
    if let Some(user) = msg.from.as_ref() {
        let _ = upsert_user(pool, user_id, user.username.as_deref(), Some(&user.first_name), None).await;
    }
    let _ = crate::rich::send_rich_language_menu(bot.token(), msg.chat.id.0, None, user_id, pool).await;
    Ok(())
}

pub async fn handle_language_callback(
    bot: &Bot,
    q: &CallbackQuery,
    code: &str,
    pool: &PgPool,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let _ = upsert_user(pool, user_id, q.from.username.as_deref(), Some(&q.from.first_name), Some(code)).await;
    let _ = set_user_language(pool, user_id, code).await;

    let _ = bot.answer_callback_query(&q.id)
        .text(format!("Language: {}", code.to_uppercase()))
        .await;

    if let Some(msg) = q.regular_message() {
        let mid = Some(msg.id.0 as i32);
        let _ = crate::rich::send_rich_main_menu(bot.token(), msg.chat.id.0, mid, user_id, &q.from.first_name, pool).await;
    }

    Ok(())
}
