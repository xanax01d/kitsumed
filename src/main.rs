pub mod rich;
mod models;
mod db;
mod locales;
mod keyboards;
mod session;
mod services;
mod handlers;

use std::env;
use sqlx::postgres::PgPoolOptions;
use teloxide::prelude::*;
use teloxide::types::{BotCommand, LabeledPrice, PreCheckoutQuery, Update};

use crate::db::init_db;
use crate::handlers::calendar::handle_calendar_callback;
use crate::handlers::commands::{handle_message, handle_menu_callback};
use crate::handlers::export::handle_export_callback;
use crate::handlers::followup::handle_followup_callback;
use crate::handlers::headache::{handle_headache_callback, handle_sos_callback};
use crate::handlers::language::handle_language_callback;
use crate::handlers::reminder::{handle_reminder_callback, handle_reminder_prompt_callback, handle_timezone_callback};
use crate::services::schedulers::{run_followup_scheduler, run_reminder_scheduler};
use crate::session::{create_session_store, SessionStore};

async fn handle_callback_query(
    bot: Bot,
    q: CallbackQuery,
    pool: sqlx::PgPool,
    sessions: SessionStore,
) -> ResponseResult<()> {
    if let Some(msg) = q.regular_message() {
        sessions.set_last_mid(q.from.id.0 as i64, msg.id.0 as i32).await;
    }

    let data = q.data.as_deref().unwrap_or("");

    if let Some(code) = data.strip_prefix("lang:") {
        handle_language_callback(&bot, &q, code, &pool).await?;
    } else if let Some(action) = data.strip_prefix("menu:") {
        handle_menu_callback(&bot, &q, action, &pool, &sessions).await?;
    } else if data.starts_with("cal:") {
        handle_calendar_callback(&bot, &q, data, &pool, &sessions).await?;
    } else if let Some(fmt) = data.strip_prefix("hde:") {
        handle_export_callback(&bot, &q, fmt, &pool).await?;
    } else if let Some(act) = data.strip_prefix("rem:") {
        handle_reminder_callback(&bot, &q, act, &pool, &sessions).await?;
    } else if let Some(tz_val) = data.strip_prefix("tz:") {
        handle_timezone_callback(&bot, &q, tz_val, &pool, &sessions).await?;
    } else if let Some(act) = data.strip_prefix("remp:") {
        handle_reminder_prompt_callback(&bot, &q, act, &pool, &sessions).await?;
    } else if data.starts_with("fu:") {
        handle_followup_callback(&bot, &q, data, &pool, &sessions).await?;
    } else if data.starts_with("sosm:") {
        handle_sos_callback(&bot, &q, data, &pool, &sessions).await?;
    } else if let Some(stars_str) = data.strip_prefix("stars:") {
        let stars_amount: u32 = stars_str.parse().unwrap_or(50);
        let lang = crate::db::get_user_language(&pool, q.from.id.0 as i64).await;
        let norm = crate::locales::normalize_lang(&lang);

        let (title_key, desc_key) = match stars_amount {
            100 => ("donate_stars_100_title", "donate_stars_100_desc"),
            250 => ("donate_stars_250_title", "donate_stars_250_desc"),
            _ => ("donate_stars_50_title", "donate_stars_50_desc"),
        };
        let title = crate::locales::get_text(title_key, norm);
        let desc = crate::locales::get_text(desc_key, norm);

        let _ = bot.answer_callback_query(q.id.clone()).await;

        let chat_id = q.message.as_ref().map(|m| m.chat().id).unwrap_or(teloxide::types::ChatId(q.from.id.0 as i64));
        let _ = bot.send_invoice(
            chat_id,
            title,
            desc,
            format!("stars_donate_{}", stars_amount),
            "",
            "XTR",
            vec![LabeledPrice::new(format!("{} Stars", stars_amount), stars_amount)],
        ).await;
        return Ok(());
    } else {
        // Headache flow callbacks
        for prefix in ["hdt", "hdi", "hdl", "hdp", "hds", "hdtr", "hdm", "hdmt", "hdmr", "hdmrt", "hdc", "hdn"] {
            if data.starts_with(&format!("{prefix}:")) {
                handle_headache_callback(&bot, &q, prefix, data, &pool, &sessions).await?;
                break;
            }
        }
    }

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenvy::dotenv().ok();
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    log::info!("Starting KitsuMed Rust...");

    let database_url = env::var("DATABASE_URL").unwrap_or_else(|_| {
        let host = env::var("POSTGRES_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
        let port = env::var("POSTGRES_PORT").unwrap_or_else(|_| "5432".to_string());
        let user = env::var("POSTGRES_USER").unwrap_or_else(|_| "kitsumed".to_string());
        let password = env::var("POSTGRES_PASSWORD").unwrap_or_else(|_| "kitsumed_secure_pass".to_string());
        let db = env::var("POSTGRES_DB").unwrap_or_else(|_| "kitsumed".to_string());

        if password.is_empty() {
            format!("postgresql://{user}@{host}:{port}/{db}")
        } else {
            format!("postgresql://{user}:{password}@{host}:{port}/{db}")
        }
    });

    log::info!("Connecting to PostgreSQL at {database_url}...");
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await?;

    init_db(&pool).await?;

    let token = env::var("TELOXIDE_TOKEN")
        .or_else(|_| env::var("TOKEN"))
        .expect("Neither TELOXIDE_TOKEN nor TOKEN environment variable is set");

    let bot = Bot::new(token);
    let _ = bot.delete_webhook().drop_pending_updates(true).await;

    let redis_url = env::var("REDIS_URL").unwrap_or_else(|_| {
        let host = env::var("REDIS_HOST")
            .or_else(|_| env::var("RedisIP"))
            .unwrap_or_else(|_| "127.0.0.1".to_string());
        let port = env::var("REDIS_PORT")
            .or_else(|_| env::var("RedisPort"))
            .unwrap_or_else(|_| "6379".to_string());
        let pass = env::var("REDIS_PASSWORD")
            .or_else(|_| env::var("RedisPassword"))
            .ok()
            .filter(|p| !p.is_empty());
        match pass {
            Some(p) => format!("redis://:{p}@{host}:{port}"),
            None => format!("redis://{host}:{port}"),
        }
    });

    let sessions = create_session_store(Some(&redis_url)).await;

    // Spawn background schedulers
    tokio::spawn(run_followup_scheduler(bot.clone(), pool.clone()));
    tokio::spawn(run_reminder_scheduler(bot.clone(), pool.clone()));

    let commands = vec![
        BotCommand::new("menu", "🦊 Главное меню"),
        BotCommand::new("sos", "🆘 Быстрый SOS"),
        BotCommand::new("log", "🤕 Записать приступ"),
        BotCommand::new("status", "⏹ Прошла ли боль?"),
        BotCommand::new("stats", "📊 Аналитика и радар"),
        BotCommand::new("history", "📅 Календарь приступов"),
        BotCommand::new("export", "📥 Экспорт отчета (PDF/CSV)"),
        BotCommand::new("reminder", "⏰ Напоминания"),
        BotCommand::new("language", "🌐 Язык и стиль"),
        BotCommand::new("help", "ℹ️ Справка"),
    ];
    let _ = bot.set_my_commands(commands).await;

    log::info!("Bot started successfully and is polling for updates...");

    let handler = dptree::entry()
        .branch(
            Update::filter_message()
                .endpoint(|bot: Bot, msg: Message, pool: sqlx::PgPool, sessions: SessionStore| async move {
                    handle_message(bot, msg, pool, sessions).await
                }),
        )
        .branch(
            Update::filter_callback_query()
                .endpoint(|bot: Bot, q: CallbackQuery, pool: sqlx::PgPool, sessions: SessionStore| async move {
                    handle_callback_query(bot, q, pool, sessions).await
                }),
        )
        .branch(
            Update::filter_pre_checkout_query()
                .endpoint(|bot: Bot, q: PreCheckoutQuery| async move {
                    let _ = bot.answer_pre_checkout_query(q.id, true).await;
                    ResponseResult::Ok(())
                }),
        );

    Dispatcher::builder(bot, handler)
        .dependencies(dptree::deps![pool, sessions])
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;

    log::info!("KitsuMed Rust stopped.");
    Ok(())
}
