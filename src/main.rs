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
use teloxide::types::Update;

use crate::db::init_db;
use crate::handlers::calendar::handle_calendar_callback;
use crate::handlers::commands::{handle_message, handle_menu_callback};
use crate::handlers::export::handle_export_callback;
use crate::handlers::followup::handle_followup_callback;
use crate::handlers::headache::handle_headache_callback;
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
    let data = q.data.as_deref().unwrap_or("");

    if let Some(code) = data.strip_prefix("lang:") {
        handle_language_callback(&bot, &q, code, &pool).await?;
    } else if let Some(action) = data.strip_prefix("menu:") {
        handle_menu_callback(&bot, &q, action, &pool, &sessions).await?;
    } else if data.starts_with("cal:") {
        handle_calendar_callback(&bot, &q, data, &pool).await?;
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

    log::info!("Starting Migrebot Rust...");

    let database_url = env::var("DATABASE_URL").unwrap_or_else(|_| {
        let host = env::var("POSTGRES_HOST").unwrap_or_else(|_| "127.0.0.1".to_string());
        let port = env::var("POSTGRES_PORT").unwrap_or_else(|_| "5432".to_string());
        let user = env::var("POSTGRES_USER").unwrap_or_else(|_| "migrebot".to_string());
        let password = env::var("POSTGRES_PASSWORD").unwrap_or_else(|_| "migrebot_secure_pass".to_string());
        let db = env::var("POSTGRES_DB").unwrap_or_else(|_| "migrebot".to_string());

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

    let sessions = create_session_store();

    // Spawn background schedulers
    tokio::spawn(run_followup_scheduler(bot.clone(), pool.clone()));
    tokio::spawn(run_reminder_scheduler(bot.clone(), pool.clone()));

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
        );

    Dispatcher::builder(bot, handler)
        .dependencies(dptree::deps![pool, sessions])
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;

    log::info!("Migrebot Rust stopped.");
    Ok(())
}
