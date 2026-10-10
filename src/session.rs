use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum FlowStep {
    StartTime,
    Intensity,
    Location,
    PainType,
    Symptoms,
    Triggers,
    Medication,
    MedicationTime,
    MedicationRelief,
    ReliefTime,
    Confirm,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct HeadacheForm {
    pub start_time: Option<String>,
    pub intensity: Option<i32>,
    pub location: Option<String>,
    pub pain_type: Option<String>,
    pub symptoms: Vec<String>,
    pub triggers: Vec<String>,
    pub medication: Option<String>,
    pub med_take_delay: Option<String>,
    pub medication_relief: Option<String>,
    pub relief_delay: Option<String>,
    pub current_step: Option<FlowStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserState {
    Idle,
    LoggingHeadache(HeadacheForm),
    WaitingCustomStartTime(HeadacheForm),
    WaitingCustomTrigger(HeadacheForm),
    WaitingCustomMedication(HeadacheForm),
    WaitingFollowupTime(i32),
    WaitingReminderTime,
    WaitingCustomTimezone,
}

impl Default for UserState {
    fn default() -> Self {
        UserState::Idle
    }
}

pub struct SessionStoreInner {
    redis: Option<tokio::sync::Mutex<redis::aio::ConnectionManager>>,
    memory: RwLock<HashMap<i64, UserState>>,
}

#[derive(Clone)]
pub struct SessionStore {
    inner: Arc<SessionStoreInner>,
}

impl SessionStore {
    pub async fn get(&self, user_id: i64) -> Option<UserState> {
        if let Some(ref r_mutex) = self.inner.redis {
            let mut conn = r_mutex.lock().await;
            let key = format!("migrebot:session:{}", user_id);
            if let Ok(Some(json)) = redis::cmd("GET").arg(&key).query_async::<Option<String>>(&mut *conn).await {
                if let Ok(state) = serde_json::from_str::<UserState>(&json) {
                    return Some(state);
                }
            }
        }
        let lock = self.inner.memory.read().await;
        lock.get(&user_id).cloned()
    }

    pub async fn set(&self, user_id: i64, state: UserState) {
        if let Some(ref r_mutex) = self.inner.redis {
            if let Ok(json) = serde_json::to_string(&state) {
                let mut conn = r_mutex.lock().await;
                let key = format!("migrebot:session:{}", user_id);
                let _ = redis::cmd("SETEX").arg(&key).arg(7200).arg(&json).query_async::<()>(&mut *conn).await;
            }
        }
        let mut lock = self.inner.memory.write().await;
        lock.insert(user_id, state);
    }

    pub async fn remove(&self, user_id: i64) {
        if let Some(ref r_mutex) = self.inner.redis {
            let mut conn = r_mutex.lock().await;
            let key = format!("migrebot:session:{}", user_id);
            let _ = redis::cmd("DEL").arg(&key).query_async::<()>(&mut *conn).await;
        }
        let mut lock = self.inner.memory.write().await;
        lock.remove(&user_id);
    }
}

pub async fn create_session_store(redis_url: Option<&str>) -> SessionStore {
    let mut redis_mgr = None;
    if let Some(url) = redis_url {
        match redis::Client::open(url) {
            Ok(client) => match client.get_connection_manager().await {
                Ok(mgr) => {
                    log::info!("Connected to Redis at {url} for persistent sessions");
                    redis_mgr = Some(tokio::sync::Mutex::new(mgr));
                }
                Err(e) => {
                    log::warn!("Failed to connect to Redis connection manager at {url}: {e}");
                }
            },
            Err(e) => {
                log::warn!("Invalid Redis URL '{url}': {e}");
            }
        }
    }
    SessionStore {
        inner: Arc::new(SessionStoreInner {
            redis: redis_mgr,
            memory: RwLock::new(HashMap::new()),
        }),
    }
}
