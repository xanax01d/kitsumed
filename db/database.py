import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

import asyncpg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


def get_postgres_dsn() -> str:
    """Constructs the PostgreSQL DSN from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    db_name = os.getenv("POSTGRES_DB", "migrebot")

    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return f"postgresql://{user}@{host}:{port}/{db_name}"


def get_ssl_config() -> Union[str, bool, None]:
    """Returns SSL parameter configuration for asyncpg connection to external servers."""
    ssl_env = os.getenv("POSTGRES_SSL", "").strip().lower()
    if ssl_env in ("require", "required", "true", "1", "yes"):
        return "require"
    elif ssl_env in ("disable", "false", "0", "no"):
        return False
    return None


async def init_db(dsn: Optional[str] = None):
    """Initializes the connection pool for external PostgreSQL and creates tables."""
    global _pool
    target_dsn = dsn or get_postgres_dsn()
    ssl_config = get_ssl_config()
    timeout = float(os.getenv("POSTGRES_TIMEOUT", "10.0"))
    command_timeout = float(os.getenv("POSTGRES_COMMAND_TIMEOUT", "15.0"))

    logger.info(f"Connecting to external PostgreSQL (timeout={timeout}s, ssl={ssl_config})...")

    pool_kwargs = {
        "dsn": target_dsn,
        "min_size": 1,
        "max_size": 10,
        "timeout": timeout,
        "command_timeout": command_timeout,
        "max_inactive_connection_lifetime": 300.0,
    }
    if ssl_config is not None:
        pool_kwargs["ssl"] = ssl_config

    try:
        _pool = await asyncpg.create_pool(**pool_kwargs)
    except Exception as exc:
        logger.error(f"Failed to connect to PostgreSQL at {target_dsn}: {exc}")
        raise

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                reminder_time VARCHAR(8) DEFAULT '21:00',
                reminder_enabled BOOLEAN DEFAULT TRUE,
                timezone VARCHAR(64) DEFAULT 'Europe/Moscow',
                last_reminded_date VARCHAR(16) DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );

            -- Migrations for existing deployments
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
        """)
    logger.info("PostgreSQL database initialized successfully.")


async def close_db():
    """Closes the PostgreSQL connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed.")


def _get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db() first.")
    return _pool


async def upsert_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    language: Optional[str] = None,
):
    """Inserts or updates Telegram user info."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        if language:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, language)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    language = EXCLUDED.language;
            """, user_id, username, first_name, language)
        else:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name;
            """, user_id, username, first_name)


async def get_user_language(user_id: int) -> str:
    """Retrieves the preferred language for a user (default: 'ru')."""
    try:
        pool = _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT language FROM users WHERE user_id = $1;", user_id)
            if row and row["language"]:
                return row["language"]
    except Exception:
        pass
    return "ru"


async def set_user_language(user_id: int, language: str) -> bool:
    """Updates user preferred language."""
    try:
        pool = _get_pool()
        async with pool.acquire() as conn:
            res = await conn.execute("""
                UPDATE users SET language = $2 WHERE user_id = $1;
            """, user_id, language)
            return res.endswith("1")
    except Exception:
        return False


async def create_episode(user_id: int, data: Dict[str, Any]) -> int:
    """Inserts a new headache episode and returns its generated ID."""
    pool = _get_pool()
    symptoms_list = list(data.get("symptoms", []))
    symptoms_json = json.dumps(symptoms_list, ensure_ascii=False)
    triggers_list = list(data.get("triggers", []))
    triggers_json = json.dumps(triggers_list, ensure_ascii=False)
    start_time = data.get("start_time", datetime.now().strftime("%Y-%m-%d %H:%M"))
    end_time = data.get("end_time")
    intensity = int(data.get("intensity", 5))
    location = str(data.get("location", ""))
    pain_type = str(data.get("pain_type", ""))
    medication = str(data.get("medication", "none"))
    medication_relief = data.get("medication_relief")
    med_take_delay = data.get("med_take_delay")
    relief_delay = data.get("relief_delay")
    status = data.get("status", "active")
    pain_resolved = data.get("pain_resolved")

    async with pool.acquire() as conn:
        if status == "completed":
            row = await conn.fetchrow("""
                INSERT INTO headache_episodes (
                    user_id, start_time, end_time, intensity, location, pain_type, symptoms, triggers,
                    medication, medication_relief, med_take_delay, relief_delay, status,
                    pain_resolved, followup_due_at, followup_sent
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb,
                    $9, $10, $11, $12, 'completed',
                    $13, NULL, TRUE
                )
                RETURNING id;
            """, user_id, start_time, end_time, intensity, location, pain_type, symptoms_json, triggers_json,
                medication, medication_relief, med_take_delay, relief_delay,
                True if pain_resolved is None else pain_resolved)
        else:
            row = await conn.fetchrow("""
                INSERT INTO headache_episodes (
                    user_id, start_time, end_time, intensity, location, pain_type, symptoms, triggers,
                    medication, medication_relief, med_take_delay, relief_delay, status,
                    pain_resolved, followup_due_at, followup_sent
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb,
                    $9, $10, $11, $12, 'active',
                    $13, NOW() + INTERVAL '2 hours', FALSE
                )
                RETURNING id;
            """, user_id, start_time, end_time, intensity, location, pain_type, symptoms_json, triggers_json,
                medication, medication_relief, med_take_delay, relief_delay,
                False if pain_resolved is None else pain_resolved)
        return row["id"]


def _format_episode_row(row: asyncpg.Record) -> Dict[str, Any]:
    item = dict(row)
    syms = item.get("symptoms")
    if isinstance(syms, str):
        try:
            item["symptoms"] = json.loads(syms)
        except Exception:
            pass
    elif syms is None:
        item["symptoms"] = []

    trigs = item.get("triggers")
    if isinstance(trigs, str):
        try:
            item["triggers"] = json.loads(trigs)
        except Exception:
            item["triggers"] = [trigs]
    elif trigs is None:
        item["triggers"] = []

    return item


async def get_active_episode(user_id: int) -> Optional[Dict[str, Any]]:
    """Returns the latest active episode for the user if any."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay,
                   followup_due_at, followup_sent, created_at
            FROM headache_episodes
            WHERE user_id = $1 AND status = 'active'
            ORDER BY id DESC LIMIT 1;
        """, user_id)
        if row:
            return _format_episode_row(row)
        return None


async def get_episode_by_id(episode_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves an episode by its primary key ID."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay,
                   followup_due_at, followup_sent, created_at
            FROM headache_episodes
            WHERE id = $1;
        """, episode_id)
        if row:
            return _format_episode_row(row)
        return None


async def finish_episode(user_id: int, end_time: Optional[str] = None) -> bool:
    """Marks the active headache episode as completed with the end timestamp."""
    pool = _get_pool()
    finish_time = end_time or datetime.now().strftime("%Y-%m-%d %H:%M")
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE headache_episodes
            SET status = 'completed', end_time = $2, pain_resolved = TRUE, followup_sent = TRUE
            WHERE id = (
                SELECT id FROM headache_episodes
                WHERE user_id = $1 AND status = 'active'
                ORDER BY id DESC LIMIT 1
            );
        """, user_id, finish_time)
        return result.endswith("1")


async def resolve_episode_pain(episode_id: int, pain_passed: bool, end_time: Optional[str] = None) -> bool:
    """
    Updates the episode status when checking if pain passed:
    - If pain_passed is True: sets status = 'completed', pain_resolved = TRUE, end_time.
    - If pain_passed is False: sets status = 'not_resolved', pain_resolved = FALSE, end_time = NULL.
    """
    pool = _get_pool()
    async with pool.acquire() as conn:
        if pain_passed:
            finish_time = end_time or datetime.now().strftime("%Y-%m-%d %H:%M")
            res = await conn.execute("""
                UPDATE headache_episodes
                SET status = 'completed', pain_resolved = TRUE, end_time = $2, followup_sent = TRUE
                WHERE id = $1;
            """, episode_id, finish_time)
            return res.endswith("1")
        else:
            res = await conn.execute("""
                UPDATE headache_episodes
                SET status = 'not_resolved', pain_resolved = FALSE, end_time = NULL, followup_sent = TRUE
                WHERE id = $1;
            """, episode_id)
            return res.endswith("1")


async def update_medication_relief(episode_id: int, relief: str) -> bool:
    """Records whether medication helped ('helped', 'partially', 'not_helped')."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("""
            UPDATE headache_episodes
            SET medication_relief = $2
            WHERE id = $1;
        """, episode_id, relief)
        return res.endswith("1")


async def get_pending_followup_episodes() -> List[Dict[str, Any]]:
    """Retrieves active episodes ready for automated follow-up inquiry."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT e.id, e.user_id, e.start_time, e.intensity, e.location,
                   e.pain_type, e.symptoms, e.medication, e.status, e.medication_relief,
                   e.pain_resolved, u.language
            FROM headache_episodes e
            JOIN users u ON e.user_id = u.user_id
            WHERE e.status = 'active'
              AND e.followup_sent = FALSE
              AND (e.followup_due_at IS NULL OR e.followup_due_at <= NOW())
            ORDER BY e.id ASC;
        """)
        return [_format_episode_row(r) for r in rows]


async def mark_followup_sent(episode_id: int) -> bool:
    """Marks that the follow-up prompt was delivered for this episode."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("""
            UPDATE headache_episodes
            SET followup_sent = TRUE
            WHERE id = $1;
        """, episode_id)
        return res.endswith("1")


async def get_recent_episodes(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches the latest recorded episodes for a user."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay, created_at
            FROM headache_episodes
            WHERE user_id = $1
            ORDER BY id DESC LIMIT $2;
        """, user_id, limit)
        return [_format_episode_row(r) for r in rows]


async def get_all_episodes(user_id: int) -> List[Dict[str, Any]]:
    """Fetches all recorded episodes for a user for exporting (ordered chronologically)."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay, created_at
            FROM headache_episodes
            WHERE user_id = $1
            ORDER BY id ASC;
        """, user_id)
        return [_format_episode_row(r) for r in rows]


async def get_user_reminder(user_id: int) -> Dict[str, Any]:
    """Retrieves user reminder settings or defaults if not configured."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT reminder_time, reminder_enabled, timezone, last_reminded_date
            FROM users
            WHERE user_id = $1;
        """, user_id)
        if row:
            return {
                "reminder_time": row["reminder_time"] or "21:00",
                "reminder_enabled": bool(row["reminder_enabled"]) if row["reminder_enabled"] is not None else True,
                "timezone": row["timezone"] or "Europe/Moscow",
                "last_reminded_date": row["last_reminded_date"],
            }
        return {
            "reminder_time": "21:00",
            "reminder_enabled": True,
            "timezone": "Europe/Moscow",
            "last_reminded_date": None,
        }


async def set_user_reminder(
    user_id: int,
    reminder_time: Optional[str] = None,
    enabled: Optional[bool] = None,
    timezone: Optional[str] = None,
) -> bool:
    """Updates user reminder configuration."""
    pool = _get_pool()
    updates = []
    params: List[Any] = [user_id]

    if reminder_time is not None:
        params.append(reminder_time)
        updates.append(f"reminder_time = ${len(params)}")
    if enabled is not None:
        params.append(enabled)
        updates.append(f"reminder_enabled = ${len(params)}")
    if timezone is not None:
        params.append(timezone)
        updates.append(f"timezone = ${len(params)}")

    if not updates:
        return False

    async with pool.acquire() as conn:
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = $1;"
        res = await conn.execute(query, *params)
        return res.endswith("1")


async def get_users_due_for_reminder(current_time_str: str, current_date_str: str) -> List[Dict[str, Any]]:
    """Returns all users who need to be reminded at the specified time and have not been reminded today."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, username, first_name, reminder_time, timezone
            FROM users
            WHERE reminder_enabled = TRUE
              AND reminder_time = $1
              AND (last_reminded_date IS NULL OR last_reminded_date < $2);
        """, current_time_str, current_date_str)
        return [dict(r) for r in rows]


async def mark_user_reminded(user_id: int, reminder_date_str: str) -> bool:
    """Updates the last_reminded_date to prevent duplicate reminders on the same day."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("""
            UPDATE users
            SET last_reminded_date = $2
            WHERE user_id = $1;
        """, user_id, reminder_date_str)
        return res.endswith("1")


async def get_enabled_reminder_users() -> List[Dict[str, Any]]:
    """Returns all users with active reminders for timezone-aware evaluation."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, username, first_name, reminder_time, timezone, last_reminded_date, language
            FROM users
            WHERE reminder_enabled = TRUE;
        """)
        return [dict(r) for r in rows]


def extract_episode_date(ep: Dict[str, Any]) -> Optional[datetime.date]:
    """Extracts date object from an episode dict using start_time or created_at."""
    st = ep.get("start_time", "")
    if isinstance(st, str) and len(st) >= 10:
        try:
            return datetime.strptime(st[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    ca = ep.get("created_at")
    if isinstance(ca, datetime):
        return ca.date()
    elif isinstance(ca, str) and len(ca) >= 10:
        try:
            return datetime.strptime(ca[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


async def get_episodes_for_month(user_id: int, year: int, month: int) -> List[Dict[str, Any]]:
    """Fetches all episodes recorded for a user in the given year and month."""
    pool = _get_pool()
    month_prefix = f"{year:04d}-{month:02d}%"
    month_exact = f"{year:04d}-{month:02d}"
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay, created_at
            FROM headache_episodes
            WHERE user_id = $1
              AND (
                  start_time LIKE $2
                  OR TO_CHAR(created_at, 'YYYY-MM') = $3
              )
            ORDER BY id ASC;
        """, user_id, month_prefix, month_exact)
        return [_format_episode_row(r) for r in rows]


async def get_episodes_for_date(user_id: int, year: int, month: int, day: int) -> List[Dict[str, Any]]:
    """Fetches all episodes recorded for a user on a specific date (YYYY-MM-DD)."""
    pool = _get_pool()
    date_prefix = f"{year:04d}-{month:02d}-{day:02d}%"
    date_exact = f"{year:04d}-{month:02d}-{day:02d}"
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, user_id, start_time, end_time, intensity, location,
                   pain_type, symptoms, triggers, medication, status, medication_relief,
                   pain_resolved, med_take_delay, relief_delay, created_at
            FROM headache_episodes
            WHERE user_id = $1
              AND (
                  start_time LIKE $2
                  OR TO_CHAR(created_at, 'YYYY-MM-DD') = $3
              )
            ORDER BY id ASC;
        """, user_id, date_prefix, date_exact)
        return [_format_episode_row(r) for r in rows]


async def clear_all_episodes(user_id: Optional[int] = None) -> int:
    """Clears headache episodes. If user_id is provided, deletes episodes for that user; otherwise truncates table."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        if user_id is not None:
            res = await conn.execute("DELETE FROM headache_episodes WHERE user_id = $1;", user_id)
        else:
            res = await conn.execute("TRUNCATE TABLE headache_episodes RESTART IDENTITY CASCADE;")
        try:
            return int(res.split()[-1])
        except Exception:
            return 0




