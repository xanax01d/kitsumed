use sqlx::{Executor, PgPool};
use crate::models::{HeadacheEpisode, NewEpisode, User, UserReminder};
use chrono::Utc;

pub async fn init_db(pool: &PgPool) -> Result<(), sqlx::Error> {
    pool.execute(
        r#"
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            reminder_time VARCHAR(8) DEFAULT '21:00',
            reminder_enabled BOOLEAN DEFAULT TRUE,
            timezone VARCHAR(64) DEFAULT 'Europe/Moscow',
            last_reminded_date VARCHAR(16) DEFAULT NULL,
            language VARCHAR(16) DEFAULT 'ru',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        ALTER TABLE users ADD COLUMN IF NOT EXISTS reminder_time VARCHAR(8) DEFAULT '21:00';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS reminder_enabled BOOLEAN DEFAULT TRUE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) DEFAULT 'Europe/Moscow';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_reminded_date VARCHAR(16) DEFAULT NULL;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(16) DEFAULT 'ru';

        CREATE TABLE IF NOT EXISTS headache_episodes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            start_time VARCHAR(64) NOT NULL,
            end_time VARCHAR(64),
            intensity INTEGER NOT NULL,
            location VARCHAR(128) NOT NULL,
            pain_type VARCHAR(128) NOT NULL,
            symptoms JSONB,
            triggers JSONB,
            medication TEXT,
            status VARCHAR(32) DEFAULT 'active',
            medication_relief VARCHAR(32) DEFAULT NULL,
            pain_resolved BOOLEAN DEFAULT NULL,
            med_take_delay VARCHAR(32) DEFAULT NULL,
            relief_delay VARCHAR(32) DEFAULT NULL,
            followup_due_at TIMESTAMPTZ DEFAULT NULL,
            followup_sent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS triggers JSONB;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS medication_relief VARCHAR(32) DEFAULT NULL;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS pain_resolved BOOLEAN DEFAULT NULL;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS med_take_delay VARCHAR(32) DEFAULT NULL;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS relief_delay VARCHAR(32) DEFAULT NULL;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS followup_due_at TIMESTAMPTZ DEFAULT NULL;
        ALTER TABLE headache_episodes ADD COLUMN IF NOT EXISTS followup_sent BOOLEAN DEFAULT FALSE;

        CREATE INDEX IF NOT EXISTS idx_headache_episodes_user_status
        ON headache_episodes(user_id, status);
        "#,
    )
    .await?;

    log::info!("PostgreSQL database initialized successfully.");
    Ok(())
}

pub async fn upsert_user(
    pool: &PgPool,
    user_id: i64,
    username: Option<&str>,
    first_name: Option<&str>,
    language: Option<&str>,
) -> Result<(), sqlx::Error> {
    if let Some(lang) = language {
        sqlx::query(
            r#"
            INSERT INTO users (user_id, username, first_name, language)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                language = EXCLUDED.language;
            "#,
        )
        .bind(user_id)
        .bind(username)
        .bind(first_name)
        .bind(lang)
        .execute(pool)
        .await?;
    } else {
        sqlx::query(
            r#"
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name;
            "#,
        )
        .bind(user_id)
        .bind(username)
        .bind(first_name)
        .execute(pool)
        .await?;
    }
    Ok(())
}

pub async fn get_user_language(pool: &PgPool, user_id: i64) -> String {
    let row: Result<Option<(Option<String>,)>, _> = sqlx::query_as(
        "SELECT language FROM users WHERE user_id = $1;"
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await;

    if let Ok(Some((Some(lang),))) = row {
        if !lang.trim().is_empty() {
            return lang;
        }
    }
    "ru".to_string()
}

pub async fn set_user_language(pool: &PgPool, user_id: i64, lang: &str) -> Result<bool, sqlx::Error> {
    let res = sqlx::query("UPDATE users SET language = $2 WHERE user_id = $1;")
        .bind(user_id)
        .bind(lang)
        .execute(pool)
        .await?;
    Ok(res.rows_affected() > 0)
}

pub async fn create_episode(pool: &PgPool, ep: &NewEpisode) -> Result<i32, sqlx::Error> {
    let symptoms_json = serde_json::to_value(&ep.symptoms).unwrap_or(serde_json::json!([]));
    let triggers_json = serde_json::to_value(&ep.triggers).unwrap_or(serde_json::json!([]));

    let row: (i32,) = if ep.status == "completed" {
        sqlx::query_as(
            r#"
            INSERT INTO headache_episodes (
                user_id, start_time, end_time, intensity, location, pain_type, symptoms, triggers,
                medication, medication_relief, med_take_delay, relief_delay, status,
                pain_resolved, followup_due_at, followup_sent
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, 'completed',
                $13, NULL, TRUE
            )
            RETURNING id;
            "#,
        )
        .bind(ep.user_id)
        .bind(&ep.start_time)
        .bind(&ep.end_time)
        .bind(ep.intensity)
        .bind(&ep.location)
        .bind(&ep.pain_type)
        .bind(symptoms_json)
        .bind(triggers_json)
        .bind(&ep.medication)
        .bind(&ep.medication_relief)
        .bind(&ep.med_take_delay)
        .bind(&ep.relief_delay)
        .bind(ep.pain_resolved.unwrap_or(true))
        .fetch_one(pool)
        .await?
    } else {
        sqlx::query_as(
            r#"
            INSERT INTO headache_episodes (
                user_id, start_time, end_time, intensity, location, pain_type, symptoms, triggers,
                medication, medication_relief, med_take_delay, relief_delay, status,
                pain_resolved, followup_due_at, followup_sent
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, 'active',
                $13, NOW() + INTERVAL '2 hours', FALSE
            )
            RETURNING id;
            "#,
        )
        .bind(ep.user_id)
        .bind(&ep.start_time)
        .bind(&ep.end_time)
        .bind(ep.intensity)
        .bind(&ep.location)
        .bind(&ep.pain_type)
        .bind(symptoms_json)
        .bind(triggers_json)
        .bind(&ep.medication)
        .bind(&ep.medication_relief)
        .bind(&ep.med_take_delay)
        .bind(&ep.relief_delay)
        .bind(ep.pain_resolved.unwrap_or(false))
        .fetch_one(pool)
        .await?
    };

    Ok(row.0)
}

pub async fn get_active_episode(pool: &PgPool, user_id: i64) -> Result<Option<HeadacheEpisode>, sqlx::Error> {
    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE user_id = $1 AND status = 'active'
        ORDER BY id DESC LIMIT 1;
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await
}

pub async fn get_episode_by_id(pool: &PgPool, id: i32) -> Result<Option<HeadacheEpisode>, sqlx::Error> {
    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE id = $1;
        "#,
    )
    .bind(id)
    .fetch_optional(pool)
    .await
}

pub async fn finish_episode(pool: &PgPool, user_id: i64, end_time: Option<&str>) -> Result<bool, sqlx::Error> {
    let now_str = Utc::now().format("%Y-%m-%d %H:%M").to_string();
    let finish_time = end_time.unwrap_or(&now_str);
    let res = sqlx::query(
        r#"
        UPDATE headache_episodes
        SET status = 'completed', end_time = $2, pain_resolved = TRUE, followup_sent = TRUE
        WHERE id = (
            SELECT id FROM headache_episodes
            WHERE user_id = $1 AND status = 'active'
            ORDER BY id DESC LIMIT 1
        );
        "#,
    )
    .bind(user_id)
    .bind(finish_time)
    .execute(pool)
    .await?;
    Ok(res.rows_affected() > 0)
}

pub async fn resolve_episode_pain(
    pool: &PgPool,
    episode_id: i32,
    pain_passed: bool,
    end_time: Option<&str>,
) -> Result<bool, sqlx::Error> {
    if pain_passed {
        let now_str = Utc::now().format("%Y-%m-%d %H:%M").to_string();
        let finish_time = end_time.unwrap_or(&now_str);
        let res = sqlx::query(
            r#"
            UPDATE headache_episodes
            SET status = 'completed', pain_resolved = TRUE, end_time = $2, followup_sent = TRUE
            WHERE id = $1;
            "#,
        )
        .bind(episode_id)
        .bind(finish_time)
        .execute(pool)
        .await?;
        Ok(res.rows_affected() > 0)
    } else {
        let res = sqlx::query(
            r#"
            UPDATE headache_episodes
            SET status = 'not_resolved', pain_resolved = FALSE, end_time = NULL, followup_sent = TRUE
            WHERE id = $1;
            "#,
        )
        .bind(episode_id)
        .execute(pool)
        .await?;
        Ok(res.rows_affected() > 0)
    }
}

pub async fn update_medication_relief(
    pool: &PgPool,
    episode_id: i32,
    relief: &str,
) -> Result<bool, sqlx::Error> {
    let res = sqlx::query(
        "UPDATE headache_episodes SET medication_relief = $2 WHERE id = $1;"
    )
    .bind(episode_id)
    .bind(relief)
    .execute(pool)
    .await?;
    Ok(res.rows_affected() > 0)
}

pub async fn get_pending_followup_episodes(
    pool: &PgPool,
) -> Result<Vec<(HeadacheEpisode, String)>, sqlx::Error> {
    let rows = sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT e.id, e.user_id, e.start_time, e.end_time, e.intensity, e.location,
               e.pain_type, e.symptoms, e.triggers, e.medication, e.status, e.medication_relief,
               e.pain_resolved, e.med_take_delay, e.relief_delay,
               e.followup_due_at, e.followup_sent, e.created_at
        FROM headache_episodes e
        WHERE e.status = 'active'
          AND e.followup_sent = FALSE
          AND (e.followup_due_at IS NULL OR e.followup_due_at <= NOW())
        ORDER BY e.id ASC;
        "#,
    )
    .fetch_all(pool)
    .await?;

    let mut result = Vec::new();
    for ep in rows {
        let lang = get_user_language(pool, ep.user_id).await;
        result.push((ep, lang));
    }
    Ok(result)
}

pub async fn mark_followup_sent(pool: &PgPool, episode_id: i32) -> Result<bool, sqlx::Error> {
    let res = sqlx::query("UPDATE headache_episodes SET followup_sent = TRUE WHERE id = $1;")
        .bind(episode_id)
        .execute(pool)
        .await?;
    Ok(res.rows_affected() > 0)
}

pub async fn get_recent_episodes(
    pool: &PgPool,
    user_id: i64,
    limit: i64,
) -> Result<Vec<HeadacheEpisode>, sqlx::Error> {
    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE user_id = $1
        ORDER BY id DESC LIMIT $2;
        "#,
    )
    .bind(user_id)
    .bind(limit)
    .fetch_all(pool)
    .await
}

pub async fn get_all_episodes(
    pool: &PgPool,
    user_id: i64,
) -> Result<Vec<HeadacheEpisode>, sqlx::Error> {
    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE user_id = $1
        ORDER BY id ASC;
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
}

pub async fn get_user_reminder(pool: &PgPool, user_id: i64) -> Result<UserReminder, sqlx::Error> {
    let row: Option<(Option<String>, Option<bool>, Option<String>, Option<String>)> = sqlx::query_as(
        r#"
        SELECT reminder_time, reminder_enabled, timezone, last_reminded_date
        FROM users
        WHERE user_id = $1;
        "#,
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await?;

    if let Some((rem_time, rem_en, tz, last_date)) = row {
        Ok(UserReminder {
            reminder_time: rem_time.unwrap_or_else(|| "21:00".to_string()),
            reminder_enabled: rem_en.unwrap_or(true),
            timezone: tz.unwrap_or_else(|| "Europe/Moscow".to_string()),
            last_reminded_date: last_date,
        })
    } else {
        Ok(UserReminder {
            reminder_time: "21:00".to_string(),
            reminder_enabled: true,
            timezone: "Europe/Moscow".to_string(),
            last_reminded_date: None,
        })
    }
}

pub async fn get_user_timezone(pool: &PgPool, user_id: i64) -> String {
    let row: Result<Option<(Option<String>,)>, _> = sqlx::query_as(
        "SELECT timezone FROM users WHERE user_id = $1;"
    )
    .bind(user_id)
    .fetch_optional(pool)
    .await;

    if let Ok(Some((Some(tz),))) = row {
        if !tz.trim().is_empty() {
            return tz;
        }
    }
    "Europe/Moscow".to_string()
}

pub async fn set_user_reminder(
    pool: &PgPool,
    user_id: i64,
    reminder_time: Option<&str>,
    enabled: Option<bool>,
    timezone: Option<&str>,
) -> Result<bool, sqlx::Error> {
    let mut clauses = Vec::new();
    let mut param_idx = 2;

    if reminder_time.is_some() {
        clauses.push(format!("reminder_time = ${param_idx}"));
        param_idx += 1;
    }
    if enabled.is_some() {
        clauses.push(format!("reminder_enabled = ${param_idx}"));
        param_idx += 1;
    }
    if timezone.is_some() {
        clauses.push(format!("timezone = ${param_idx}"));
    }

    if clauses.is_empty() {
        return Ok(false);
    }

    let query_str = format!("UPDATE users SET {} WHERE user_id = $1;", clauses.join(", "));
    let mut q = sqlx::query(&query_str).bind(user_id);

    if let Some(rt) = reminder_time {
        q = q.bind(rt);
    }
    if let Some(en) = enabled {
        q = q.bind(en);
    }
    if let Some(tz) = timezone {
        q = q.bind(tz);
    }

    let res = q.execute(pool).await?;
    Ok(res.rows_affected() > 0)
}

pub async fn get_enabled_reminder_users(pool: &PgPool) -> Result<Vec<User>, sqlx::Error> {
    sqlx::query_as::<_, User>(
        r#"
        SELECT user_id, username, first_name, reminder_time, reminder_enabled,
               timezone, last_reminded_date, language, created_at
        FROM users
        WHERE reminder_enabled = TRUE;
        "#,
    )
    .fetch_all(pool)
    .await
}

pub async fn mark_user_reminded(
    pool: &PgPool,
    user_id: i64,
    reminder_date_str: &str,
) -> Result<bool, sqlx::Error> {
    let res = sqlx::query(
        "UPDATE users SET last_reminded_date = $2 WHERE user_id = $1;"
    )
    .bind(user_id)
    .bind(reminder_date_str)
    .execute(pool)
    .await?;
    Ok(res.rows_affected() > 0)
}

pub async fn get_episodes_for_month(
    pool: &PgPool,
    user_id: i64,
    year: i32,
    month: u32,
) -> Result<Vec<HeadacheEpisode>, sqlx::Error> {
    let month_prefix = format!("{year:04}-{month:02}%");
    let month_exact = format!("{year:04}-{month:02}");

    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE user_id = $1
          AND (
              start_time LIKE $2
              OR TO_CHAR(created_at, 'YYYY-MM') = $3
          )
        ORDER BY id ASC;
        "#,
    )
    .bind(user_id)
    .bind(month_prefix)
    .bind(month_exact)
    .fetch_all(pool)
    .await
}

pub async fn get_episodes_for_date(
    pool: &PgPool,
    user_id: i64,
    year: i32,
    month: u32,
    day: u32,
) -> Result<Vec<HeadacheEpisode>, sqlx::Error> {
    let date_prefix = format!("{year:04}-{month:02}-{day:02}%");
    let date_exact = format!("{year:04}-{month:02}-{day:02}");

    sqlx::query_as::<_, HeadacheEpisode>(
        r#"
        SELECT id, user_id, start_time, end_time, intensity, location,
               pain_type, symptoms, triggers, medication, status, medication_relief,
               pain_resolved, med_take_delay, relief_delay,
               followup_due_at, followup_sent, created_at
        FROM headache_episodes
        WHERE user_id = $1
          AND (
              start_time LIKE $2
              OR TO_CHAR(created_at, 'YYYY-MM-DD') = $3
          )
        ORDER BY id ASC;
        "#,
    )
    .bind(user_id)
    .bind(date_prefix)
    .bind(date_exact)
    .fetch_all(pool)
    .await
}
