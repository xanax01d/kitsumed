use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, PartialEq, Eq)]
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

#[derive(Debug, Clone, Default)]
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

#[derive(Debug, Clone)]
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

pub type SessionStore = Arc<RwLock<HashMap<i64, UserState>>>;

pub fn create_session_store() -> SessionStore {
    Arc::new(RwLock::new(HashMap::new()))
}
