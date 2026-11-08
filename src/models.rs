use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct User {
    pub user_id: i64,
    pub username: Option<String>,
    pub first_name: Option<String>,
    pub reminder_time: Option<String>,
    pub reminder_enabled: Option<bool>,
    pub timezone: Option<String>,
    pub last_reminded_date: Option<String>,
    pub language: Option<String>,
    pub created_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct HeadacheEpisode {
    pub id: i32,
    pub user_id: i64,
    pub start_time: String,
    pub end_time: Option<String>,
    pub intensity: i32,
    pub location: String,
    pub pain_type: String,
    pub symptoms: Option<serde_json::Value>,
    pub triggers: Option<serde_json::Value>,
    pub medication: Option<String>,
    pub status: Option<String>,
    pub medication_relief: Option<String>,
    pub pain_resolved: Option<bool>,
    pub med_take_delay: Option<String>,
    pub relief_delay: Option<String>,
    pub followup_due_at: Option<DateTime<Utc>>,
    pub followup_sent: Option<bool>,
    pub created_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone)]
pub struct NewEpisode {
    pub user_id: i64,
    pub start_time: String,
    pub end_time: Option<String>,
    pub intensity: i32,
    pub location: String,
    pub pain_type: String,
    pub symptoms: Vec<String>,
    pub triggers: Vec<String>,
    pub medication: String,
    pub medication_relief: Option<String>,
    pub med_take_delay: Option<String>,
    pub relief_delay: Option<String>,
    pub status: String,
    pub pain_resolved: Option<bool>,
}

#[derive(Debug, Clone)]
pub struct UserReminder {
    pub reminder_time: String,
    pub reminder_enabled: bool,
    pub timezone: String,
    pub last_reminded_date: Option<String>,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct UserMedication {
    pub id: i32,
    pub user_id: i64,
    pub name: String,
    pub last_used_at: Option<DateTime<Utc>>,
}
