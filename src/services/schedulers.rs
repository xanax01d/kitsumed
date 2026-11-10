use std::str::FromStr;
use std::time::Duration;
use chrono::Utc;
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;

use crate::db::{get_enabled_reminder_users, get_pending_followup_episodes, mark_followup_sent, mark_user_reminded};

pub async fn run_followup_scheduler(bot: Bot, pool: PgPool) {
    log::info!("Follow-up background scheduler started.");
    loop {
        tokio::time::sleep(Duration::from_secs(60)).await;

        match get_pending_followup_episodes(&pool).await {
            Ok(episodes) => {
                for (ep, _) in episodes {
                    match crate::rich::send_rich_followup_prompt(bot.token(), ep.user_id, None, ep.id, ep.user_id, &pool).await {
                        Ok(_) => {
                            let _ = mark_followup_sent(&pool, ep.id).await;
                            log::info!("Delivered rich follow-up check for episode #{} to user {}", ep.id, ep.user_id);
                        }
                        Err(e) => {
                            log::warn!("Could not send rich follow-up to user {}: {}", ep.user_id, e);
                            let _ = mark_followup_sent(&pool, ep.id).await;
                        }
                    }
                }
            }
            Err(e) => {
                log::error!("Error in followup scheduler: {}", e);
            }
        }
    }
}

pub async fn run_reminder_scheduler(bot: Bot, pool: PgPool) {
    log::info!("Daily reminder background scheduler started.");
    loop {
        tokio::time::sleep(Duration::from_secs(60)).await;

        let now_utc = Utc::now();

        match get_enabled_reminder_users(&pool).await {
            Ok(users) => {
                for u in users {
                    let target_time = u.reminder_time.as_deref().unwrap_or("21:00");
                    let tz_str = u.timezone.as_deref().unwrap_or("Europe/Moscow");

                    let tz = match Tz::from_str(tz_str) {
                        Ok(t) => t,
                        Err(_) => chrono_tz::Europe::Moscow,
                    };

                    let user_now = now_utc.with_timezone(&tz);
                    let user_time_str = user_now.format("%H:%M").to_string();
                    let user_date_str = user_now.format("%Y-%m-%d").to_string();

                    if user_time_str == target_time {
                        let already_reminded = u.last_reminded_date.as_deref() == Some(&user_date_str);
                        if !already_reminded {
                            match crate::rich::send_rich_daily_reminder(bot.token(), u.user_id, None, u.user_id, &pool).await {
                                Ok(_) => {
                                    let _ = mark_user_reminded(&pool, u.user_id, &user_date_str).await;
                                    log::info!("Delivered rich daily reminder to user {}", u.user_id);
                                }
                                Err(e) => {
                                    log::warn!("Could not send rich daily reminder to user {}: {}", u.user_id, e);
                                }
                            }
                        }
                    }
                }
            }
            Err(e) => {
                log::error!("Error in reminder scheduler: {}", e);
            }
        }
    }
}
