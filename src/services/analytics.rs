use chrono::{Datelike, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use std::collections::HashMap;

use crate::db::get_all_episodes;
use crate::locales::{get_symptom_name, get_trigger_name, normalize_lang};
use crate::models::HeadacheEpisode;
use crate::services::weather::hpa_to_mmhg;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MohRisk {
    Safe,    // 0-7 days
    Caution, // 8-9 days
    Alert,   // 10+ days
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalyticsReport {
    pub total_episodes_30d: usize,
    pub pain_days_30d: usize,
    pub avg_intensity: f32,
    pub medication_days_30d: i64,
    pub moh_risk: MohRisk,
    pub medication_efficacy_pct: Option<i32>,
    pub top_triggers: Vec<(String, usize, i32)>, // (display_name, count, pct)
    pub top_symptoms: Vec<(String, usize, i32)>, // (display_name, count, pct)
    pub peak_weekday: Option<(String, usize)>,   // (weekday_name, count)
    pub avg_pressure_mmhg: Option<i32>,
}

pub async fn generate_analytics_report(
    pool: &PgPool,
    user_id: i64,
    lang: &str,
) -> Result<AnalyticsReport, sqlx::Error> {
    let norm = normalize_lang(lang);
    let all_episodes = get_all_episodes(pool, user_id).await?;

    let now = Utc::now();
    let thirty_days_ago = now - chrono::Duration::days(30);

    // Фильтруем приступы за последние 30 дней
    let eps_30d: Vec<&HeadacheEpisode> = all_episodes
        .iter()
        .filter(|e| {
            if let Some(created) = e.created_at {
                created >= thirty_days_ago
            } else {
                false
            }
        })
        .collect();

    let total_episodes = eps_30d.len();

    // Подсчет уникальных дней боли
    let mut pain_dates = std::collections::HashSet::new();
    let mut weekday_counts: HashMap<u32, usize> = HashMap::new();
    let mut total_intensity = 0;
    let mut intensity_count = 0;

    let mut pressure_sum = 0.0f32;
    let mut pressure_count = 0;

    let mut med_episodes_count = 0;
    let mut med_helped_count = 0;

    let mut trigger_counts: HashMap<String, usize> = HashMap::new();
    let mut symptom_counts: HashMap<String, usize> = HashMap::new();

    for ep in &eps_30d {
        if let Some(created) = ep.created_at {
            pain_dates.insert(created.date_naive());
            let wd = created.weekday().number_from_monday();
            *weekday_counts.entry(wd).or_insert(0) += 1;
        }

        total_intensity += ep.intensity;
        intensity_count += 1;

        if let Some(p) = ep.pressure_hpa {
            pressure_sum += p;
            pressure_count += 1;
        }

        // Эффективность лекарств
        if let Some(ref med) = ep.medication {
            if !med.is_empty() && med != "none" {
                med_episodes_count += 1;
                if ep.medication_relief.as_deref() == Some("helped") {
                    med_helped_count += 1;
                }
            }
        }

        // Триггеры
        if let Some(ref tr_val) = ep.triggers {
            if let Some(arr) = tr_val.as_array() {
                for item in arr {
                    if let Some(s) = item.as_str() {
                        if s != "none" && !s.is_empty() {
                            *trigger_counts.entry(s.to_string()).or_insert(0) += 1;
                        }
                    }
                }
            }
        }

        // Симптомы
        if let Some(ref sym_val) = ep.symptoms {
            if let Some(arr) = sym_val.as_array() {
                for item in arr {
                    if let Some(s) = item.as_str() {
                        if s != "none" && !s.is_empty() {
                            *symptom_counts.entry(s.to_string()).or_insert(0) += 1;
                        }
                    }
                }
            }
        }
    }

    let pain_days = pain_dates.len();
    let avg_intensity = if intensity_count > 0 {
        (total_intensity as f32) / (intensity_count as f32)
    } else {
        0.0
    };

    let avg_pressure_mmhg = if pressure_count > 0 {
        Some(hpa_to_mmhg(pressure_sum / (pressure_count as f32)))
    } else {
        None
    };

    let medication_days = crate::db::get_monthly_medication_days(pool, user_id).await.unwrap_or(0);

    let moh_risk = if medication_days >= 10 {
        MohRisk::Alert
    } else if medication_days >= 8 {
        MohRisk::Caution
    } else {
        MohRisk::Safe
    };

    let medication_efficacy_pct = if med_episodes_count > 0 {
        Some(((med_helped_count as f32 / med_episodes_count as f32) * 100.0).round() as i32)
    } else {
        None
    };

    // Топ триггеров
    let mut top_triggers_vec: Vec<(String, usize)> = trigger_counts.into_iter().collect();
    top_triggers_vec.sort_by(|a, b| b.1.cmp(&a.1));
    let top_triggers: Vec<(String, usize, i32)> = top_triggers_vec
        .into_iter()
        .take(3)
        .map(|(key, count)| {
            let name = get_trigger_name(&key, norm);
            let pct = if total_episodes > 0 {
                ((count as f32 / total_episodes as f32) * 100.0).round() as i32
            } else {
                0
            };
            (name, count, pct)
        })
        .collect();

    // Топ симптомов
    let mut top_symptoms_vec: Vec<(String, usize)> = symptom_counts.into_iter().collect();
    top_symptoms_vec.sort_by(|a, b| b.1.cmp(&a.1));
    let top_symptoms: Vec<(String, usize, i32)> = top_symptoms_vec
        .into_iter()
        .take(3)
        .map(|(key, count)| {
            let name = get_symptom_name(&key, norm);
            let pct = if total_episodes > 0 {
                ((count as f32 / total_episodes as f32) * 100.0).round() as i32
            } else {
                0
            };
            (name, count, pct)
        })
        .collect();

    // Пиковый день недели
    let peak_weekday = weekday_counts
        .into_iter()
        .max_by_key(|&(_, count)| count)
        .map(|(wd, count)| {
            let name = match (wd, norm) {
                (1, "en") => "Monday",
                (1, "be") => "Панядзелак",
                (1, _) => "Понедельник",
                (2, "en") => "Tuesday",
                (2, "be") => "Аўторак",
                (2, _) => "Вторник",
                (3, "en") => "Wednesday",
                (3, "be") => "Серада",
                (3, _) => "Среда",
                (4, "en") => "Thursday",
                (4, "be") => "Чацвер",
                (4, _) => "Четверг",
                (5, "en") => "Friday",
                (5, "be") => "Пятніца",
                (5, _) => "Пятница",
                (6, "en") => "Saturday",
                (6, "be") => "Субота",
                (6, _) => "Суббота",
                (7, "en") => "Sunday",
                (7, "be") => "Нядзеля",
                (7, _) => "Воскресенье",
                _ => "Неизвестно",
            };
            (name.to_string(), count)
        });

    Ok(AnalyticsReport {
        total_episodes_30d: total_episodes,
        pain_days_30d: pain_days,
        avg_intensity,
        medication_days_30d: medication_days,
        moh_risk,
        medication_efficacy_pct,
        top_triggers,
        top_symptoms,
        peak_weekday,
        avg_pressure_mmhg,
    })
}
