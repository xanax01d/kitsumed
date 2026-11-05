use std::str::FromStr;
use chrono::{Duration, Utc};
use chrono_tz::Tz;
use sqlx::PgPool;
use teloxide::prelude::*;
use teloxide::types::{CallbackQuery, InputFile};

use crate::db::{create_episode, get_user_language, get_user_timezone};
use crate::keyboards::*;
use crate::locales::*;
use crate::models::NewEpisode;
use crate::session::{FlowStep, HeadacheForm, SessionStore, UserState};

pub fn parse_delay_to_minutes(delay: Option<&str>) -> i64 {
    match delay {
        Some("0m") | Some("now") | Some("0") => 0,
        Some("15m") => 15,
        Some("30m") => 30,
        Some("1h") | Some("60m") => 60,
        Some("2h") | Some("120m") => 120,
        Some("3h") | Some("180m") => 180,
        Some("4h") | Some("240m") => 240,
        Some(s) => {
            if let Some(num) = s.strip_suffix('m').and_then(|v| v.parse::<i64>().ok()) {
                num
            } else if let Some(num) = s.strip_suffix('h').and_then(|v| v.parse::<i64>().ok()) {
                num * 60
            } else {
                s.parse::<i64>().unwrap_or(0)
            }
        }
        None => 0,
    }
}

pub fn calculate_headache_end_time(
    start_time_str: Option<&str>,
    med_take_delay: Option<&str>,
    relief_delay: Option<&str>,
    tz: &Tz,
) -> String {
    let now = Utc::now().with_timezone(tz);
    let med_mins = parse_delay_to_minutes(med_take_delay);
    let relief_mins = parse_delay_to_minutes(relief_delay);
    let total_mins = med_mins + relief_mins;

    if let Some(st) = start_time_str {
        if let Ok(dt) = chrono::NaiveDateTime::parse_from_str(st, "%Y-%m-%d %H:%M") {
            let calc = dt + Duration::minutes(total_mins);
            return calc.format("%Y-%m-%d %H:%M").to_string();
        }
        if let Ok(t) = chrono::NaiveTime::parse_from_str(st, "%H:%M") {
            let today = now.date_naive();
            let dt = today.and_time(t);
            let calc = dt + Duration::minutes(total_mins);
            return calc.format("%Y-%m-%d %H:%M").to_string();
        }
    }

    if total_mins > 0 {
        let calc = now + Duration::minutes(total_mins);
        calc.format("%Y-%m-%d %H:%M").to_string()
    } else {
        now.format("%Y-%m-%d %H:%M").to_string()
    }
}

pub fn get_step_image_path(step: &str, lang: &str) -> String {
    let norm = normalize_lang(lang);
    let filename = match step {
        "start_time" => "steps/start_time.png",
        "intensity" => "steps/pain_scale.png",
        "location" => "steps/location.png",
        "pain_type" => "steps/pain_type.png",
        "symptoms" => "steps/symptoms.png",
        "triggers" => "steps/triggers.png",
        "medication" | "medication_time" => "steps/medication.png",
        "relief_time" | "saved" => "steps/saved.png",
        "confirm" => "steps/confirm.png",
        _ => "steps/start_time.png",
    };
    format!("assets/images/{norm}/{filename}")
}

pub async fn start_headache_flow(
    bot: &Bot,
    chat_id: ChatId,
    message_id: Option<i32>,
    user_id: i64,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let mut form = HeadacheForm::default();
    form.current_step = Some(FlowStep::StartTime);

    sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

    let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id.0, message_id, user_id, &form, pool).await;
    Ok(())
}

pub fn format_summary(form: &HeadacheForm, lang: &str) -> String {
    let start_time = form.start_time.clone().unwrap_or_else(|| "—".to_string());
    let intensity = form.intensity.unwrap_or(5);
    let level = get_intensity_label(intensity, lang);

    let loc = form.location.as_deref().unwrap_or("diffuse");
    let loc_text = get_location_name(loc, lang);

    let pt = form.pain_type.as_deref().unwrap_or("throbbing");
    let pt_text = get_pain_type_name(pt, lang);

    let symptoms_str = if form.symptoms.is_empty() || form.symptoms.contains(&"none".to_string()) {
        "—".to_string()
    } else {
        let list: Vec<String> = form.symptoms.iter().map(|s| get_symptom_name(s, lang)).collect();
        list.join(", ")
    };

    let triggers_str = if form.triggers.is_empty() || form.triggers.contains(&"none".to_string()) {
        "—".to_string()
    } else {
        let list: Vec<String> = form.triggers.iter().map(|t| get_trigger_name(t, lang)).collect();
        list.join(", ")
    };

    let med = form.medication.as_deref().unwrap_or("none");
    let mut med_text = get_medication_name(med, lang);
    if let Some(relief) = form.medication_relief.as_deref() {
        let r_txt = match relief {
            "helped" => get_text("fu_med_helped", lang),
            "partially" => get_text("fu_med_partially", lang),
            "not_helped" => get_text("fu_med_not_helped", lang),
            _ => "".to_string(),
        };
        if !r_txt.is_empty() {
            med_text = format!("{med_text} ({r_txt})");
        }
    }

    let is_resolved = form.medication_relief.as_deref() == Some("helped");

    let mut out = String::new();
    out.push_str(&get_text("summary_title", lang));
    if is_resolved {
        let duration = form.relief_delay.as_deref().unwrap_or("1h");
        out.push_str(&get_text_fmt("summary_status_completed", lang, &[]));
        out.push_str(&get_text_fmt("summary_time_resolved", lang, &[
            ("start_time", &start_time),
            ("end_time", "Купирован"),
            ("duration", duration),
        ]));
    } else {
        out.push_str(&get_text_fmt("summary_status_active", lang, &[]));
        out.push_str(&get_text_fmt("summary_time", lang, &[("start_time", &start_time)]));
    }

    out.push_str(&get_text_fmt("summary_pain", lang, &[
        ("intensity", &intensity.to_string()),
        ("level", &level),
    ]));
    out.push_str(&get_text_fmt("summary_location", lang, &[("loc_text", &loc_text)]));
    out.push_str(&get_text_fmt("summary_pain_type", lang, &[("pt_text", &pt_text)]));
    out.push_str(&get_text_fmt("summary_symptoms", lang, &[("symptoms_str", &symptoms_str)]));
    out.push_str(&get_text_fmt("summary_triggers", lang, &[("triggers_str", &triggers_str)]));
    out.push_str(&get_text_fmt("summary_medication", lang, &[("med_text", &med_text)]));
    out.push_str(&get_text("summary_confirm", lang));
    out
}

pub async fn handle_headache_callback(
    bot: &Bot,
    q: &CallbackQuery,
    prefix: &str,
    data: &str,
    pool: &PgPool,
    sessions: &SessionStore,
) -> ResponseResult<()> {
    let user_id = q.from.id.0 as i64;
    let _ = bot.answer_callback_query(&q.id).await;

    let tz_name = get_user_timezone(pool, user_id).await;
    let tz = Tz::from_str(&tz_name).unwrap_or(chrono_tz::Europe::Moscow);
    let lang = get_user_language(pool, user_id).await;
    let norm = normalize_lang(&lang);

    let mid = q.regular_message().map(|m| m.id.0 as i32);
    let chat_id = match q.regular_message() {
        Some(m) => m.chat.id.0,
        None => user_id,
    };

    let mut form = match sessions.get(user_id).await {
        Some(UserState::LoggingHeadache(f)) => f,
        _ => HeadacheForm::default(),
    };

    match prefix {
        "hdt" => {
            let preset = data.strip_prefix("hdt:").unwrap_or("now");
            let now = Utc::now().with_timezone(&tz);

            if preset == "custom" {
                let prompt = get_text("step1_custom_prompt", &norm);
                let pmid = if let Ok(sent) = bot.send_message(teloxide::types::ChatId(chat_id), prompt)
                    .parse_mode(teloxide::types::ParseMode::Html)
                    .reply_markup(teloxide::types::KeyboardRemove::new())
                    .await {
                    Some(sent.id.0 as i32)
                } else {
                    None
                };
                sessions.set(user_id, UserState::WaitingCustomStartTime(form.clone(), pmid)).await;
                return Ok(());
            }

            if preset == "yesterday" {
                let yesterday_str = (now - Duration::days(1)).format("%Y-%m-%d 12:00").to_string();
                form.start_time = Some(yesterday_str);
                form.current_step = Some(FlowStep::Intensity);
                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;
                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
                return Ok(());
            }

            let time_str = match preset {
                "-30m" => (now - Duration::minutes(30)).format("%Y-%m-%d %H:%M").to_string(),
                "-1h" => (now - Duration::hours(1)).format("%Y-%m-%d %H:%M").to_string(),
                "-2h" => (now - Duration::hours(2)).format("%Y-%m-%d %H:%M").to_string(),
                _ => now.format("%Y-%m-%d %H:%M").to_string(),
            };

            form.start_time = Some(time_str);
            form.current_step = Some(FlowStep::Intensity);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdi" => {
            let val_str = data.strip_prefix("hdi:").unwrap_or("5");
            let intensity: i32 = val_str.parse().unwrap_or(5);

            form.intensity = Some(intensity);
            form.current_step = Some(FlowStep::Location);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdl" => {
            let loc = data.strip_prefix("hdl:").unwrap_or("both");

            form.location = Some(loc.to_string());
            form.current_step = Some(FlowStep::PainType);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdp" => {
            let pt = data.strip_prefix("hdp:").unwrap_or("throbbing");

            form.pain_type = Some(pt.to_string());
            form.current_step = Some(FlowStep::Symptoms);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hds" => {
            let sub = data.strip_prefix("hds:").unwrap_or("");
            if sub.starts_with("toggle:") {
                let sym = sub.strip_prefix("toggle:").unwrap_or("");
                if let Some(pos) = form.symptoms.iter().position(|x| x == sym) {
                    form.symptoms.remove(pos);
                } else {
                    form.symptoms.retain(|x| x != "none");
                    form.symptoms.push(sym.to_string());
                }

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            } else if sub == "none" {
                form.symptoms = vec!["none".to_string()];
                form.current_step = Some(FlowStep::Triggers);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            } else if sub == "done" {
                form.current_step = Some(FlowStep::Triggers);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            }
        }

        "hdtr" => {
            let sub = data.strip_prefix("hdtr:").unwrap_or("");
            if sub.starts_with("toggle:") {
                let trig = sub.strip_prefix("toggle:").unwrap_or("");
                if let Some(pos) = form.triggers.iter().position(|x| x == trig) {
                    form.triggers.remove(pos);
                } else {
                    form.triggers.retain(|x| x != "none");
                    form.triggers.push(trig.to_string());
                }

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            } else if sub == "none" {
                form.triggers = vec!["none".to_string()];
                form.current_step = Some(FlowStep::Medication);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            } else if sub == "done" {
                form.current_step = Some(FlowStep::Medication);

                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            }
        }

        "hdm" => {
            let med = data.strip_prefix("hdm:").unwrap_or("none");

            if med == "custom" {
                let lang = crate::db::get_user_language(pool, user_id).await;
                let norm = crate::locales::normalize_lang(&lang);
                let prompt = match norm {
                    "be" => "<b>Назва лекаў і дазіроўка</b>\n\nНапішыце ў адказ назву прэпарата і дазіроўку (напрыклад: <code>Элетрыптан 40 мг</code> ці <code>Налгезін 550 мг</code>):",
                    "en" => "<b>Medication Name & Dosage</b>\n\nPlease type the name of the medicine and dosage in reply (e.g. <code>Eletriptan 40 mg</code> or <code>Naproxen 500 mg</code>):",
                    "meme" => "<b>Название колёс и дозировка</b>\n\nЧеркани в ответ, чем закинулся и сколько (например: <code>Элетриптан 40 мг</code> или <code>Ибупрофен 400 мг</code>):",
                    "cyberpunk" => "<b>Фарм-препарат и дозировка</b>\n\nВведите идентификатор препарата и дозу (напр.: <code>Элетриптан 40 мг</code>):",
                    _ => "<b>Название препарата и дозировка</b>\n\nНапишите в ответном сообщении название лекарства и дозировку (например: <code>Элетриптан 40 мг</code> или <code>Налгезин 550 мг</code>):",
                };
                let pmid = if let Ok(sent) = bot.send_message(teloxide::types::ChatId(chat_id), prompt)
                    .parse_mode(teloxide::types::ParseMode::Html)
                    .reply_markup(teloxide::types::KeyboardRemove::new())
                    .await {
                    Some(sent.id.0 as i32)
                } else {
                    None
                };
                sessions.set(user_id, UserState::WaitingCustomMedication(form.clone(), pmid)).await;
                return Ok(());
            }

            form.medication = Some(med.to_string());

            if med == "none" {
                form.current_step = Some(FlowStep::Confirm);
            } else {
                form.current_step = Some(FlowStep::MedicationTime);
            }

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdmt" => {
            let delay = data.strip_prefix("hdmt:").unwrap_or("0m");
            form.med_take_delay = Some(delay.to_string());
            form.current_step = Some(FlowStep::MedicationRelief);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdmr" => {
            let relief = data.strip_prefix("hdmr:").unwrap_or("helped");
            form.medication_relief = Some(relief.to_string());

            if relief == "helped" {
                form.current_step = Some(FlowStep::ReliefTime);
            } else {
                form.current_step = Some(FlowStep::Confirm);
            }

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdmrt" => {
            let r_time = data.strip_prefix("hdmrt:").unwrap_or("30m");
            form.relief_delay = Some(r_time.to_string());
            form.current_step = Some(FlowStep::Confirm);

            sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

            let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
        }

        "hdc" => {
            let act = data.strip_prefix("hdc:").unwrap_or("cancel");

            if act == "save" {
                let is_completed = form.medication_relief.as_deref() == Some("helped");
                let status = if is_completed { "completed" } else { "active" };

                let end_time = if is_completed {
                    Some(calculate_headache_end_time(
                        form.start_time.as_deref(),
                        form.med_take_delay.as_deref(),
                        form.relief_delay.as_deref(),
                        &tz,
                    ))
                } else {
                    None
                };

                let new_ep = NewEpisode {
                    user_id,
                    start_time: form.start_time.clone().unwrap_or_else(|| Utc::now().with_timezone(&tz).format("%Y-%m-%d %H:%M").to_string()),
                    end_time,
                    intensity: form.intensity.unwrap_or(5),
                    location: form.location.clone().unwrap_or_else(|| "both".to_string()),
                    pain_type: form.pain_type.clone().unwrap_or_else(|| "throbbing".to_string()),
                    symptoms: form.symptoms.clone(),
                    triggers: form.triggers.clone(),
                    medication: form.medication.clone().unwrap_or_else(|| "none".to_string()),
                    medication_relief: form.medication_relief.clone(),
                    med_take_delay: form.med_take_delay.clone(),
                    relief_delay: form.relief_delay.clone(),
                    status: status.to_string(),
                    pain_resolved: if is_completed { Some(true) } else { Some(false) },
                };

                let ep_id = create_episode(pool, &new_ep).await.unwrap_or(0);

                sessions.remove(user_id).await;

                let _ = crate::rich::send_rich_headache_saved(bot.token(), chat_id, mid, ep_id, &form, user_id, pool).await;
            } else {
                sessions.remove(user_id).await;
                let _ = crate::rich::send_rich_headache_cancelled(bot.token(), chat_id, mid, user_id, pool).await;
            }
        }

        "hdn" => {
            let act = data.strip_prefix("hdn:").unwrap_or("cancel");
            if act == "cancel" {
                sessions.remove(user_id).await;
                let _ = crate::rich::send_rich_headache_cancelled(bot.token(), chat_id, mid, user_id, pool).await;
            } else if act == "back" {
                let current = form.current_step.clone().unwrap_or(FlowStep::StartTime);
                let prev_step = match current {
                    FlowStep::Intensity => FlowStep::StartTime,
                    FlowStep::Location => FlowStep::Intensity,
                    FlowStep::PainType => FlowStep::Location,
                    FlowStep::Symptoms => FlowStep::PainType,
                    FlowStep::Triggers => FlowStep::Symptoms,
                    FlowStep::Medication => FlowStep::Triggers,
                    FlowStep::MedicationTime => FlowStep::Medication,
                    FlowStep::MedicationRelief => FlowStep::MedicationTime,
                    FlowStep::ReliefTime => FlowStep::MedicationRelief,
                    FlowStep::Confirm => {
                        let med = form.medication.as_deref().unwrap_or("none");
                        if med == "none" {
                            FlowStep::Medication
                        } else if form.medication_relief.as_deref() == Some("helped") {
                            FlowStep::ReliefTime
                        } else {
                            FlowStep::MedicationRelief
                        }
                    }
                    _ => FlowStep::StartTime,
                };

                form.current_step = Some(prev_step);
                sessions.set(user_id, UserState::LoggingHeadache(form.clone())).await;

                let _ = crate::rich::render_rich_headache_step(bot.token(), chat_id, mid, user_id, &form, pool).await;
            }
        }

        _ => {}
    }

    Ok(())
}
