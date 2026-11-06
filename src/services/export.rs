use crate::models::HeadacheEpisode;
use crate::locales::{get_location_name, get_medication_name, get_pain_type_name, get_symptom_name, get_trigger_name, get_intensity_label, normalize_lang};
use crate::services::weather::format_weather_display_lang;
use serde::Serialize;
use std::path::Path;

#[derive(Serialize)]
struct PdfEpisodeItem {
    id: i32,
    start_time: String,
    time_str: String,
    intensity: i32,
    pain_level: String,
    location: String,
    pain_type: String,
    symptoms: String,
    triggers: String,
    medication: String,
    relief: String,
    status: String,
    weather: String,
}

#[derive(Serialize)]
struct PdfExportPayload {
    user_id: i64,
    date_generated: String,
    lang: String,
    episodes: Vec<PdfEpisodeItem>,
}

pub fn generate_csv(episodes: &[HeadacheEpisode], lang: &str) -> Vec<u8> {
    let mut wtr = csv::WriterBuilder::new().from_writer(Vec::new());

    // Write UTF-8 BOM for Excel Cyrillic compatibility
    let mut out = vec![0xEF, 0xBB, 0xBF];

    let norm = normalize_lang(lang);
    let headers = match norm {
        "en" => vec![
            "Episode ID", "Start Time", "End Time", "Intensity (1-10)", "Location",
            "Pain Type", "Symptoms", "Triggers", "Medication", "Relief", "Weather", "Status"
        ],
        "be" => vec![
            "ID прыступу", "Пачатак", "Заканчэнне", "Інтэнсіўнасць (1-10)", "Лакалізацыя",
            "Характар болю", "Сімптомы", "Трыгеры", "Прэпарат", "Эфект прэпарата", "Надвор'е", "Статус"
        ],
        _ => vec![
            "ID приступа", "Начало", "Окончание", "Интенсивность (1-10)", "Локализация",
            "Характер боли", "Симптомы", "Триггеры", "Препарат", "Эффект препарата", "Погода", "Статус"
        ],
    };

    wtr.write_record(&headers).unwrap_or(());

    for ep in episodes {
        let sym_str = if let Some(serde_json::Value::Array(arr)) = &ep.symptoms {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_symptom_name(s, lang)).collect();
            if list.is_empty() { "—".to_string() } else { list.join(", ") }
        } else {
            "—".to_string()
        };

        let trig_str = if let Some(serde_json::Value::Array(arr)) = &ep.triggers {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_trigger_name(s, lang)).collect();
            if list.is_empty() { "—".to_string() } else { list.join(", ") }
        } else {
            "—".to_string()
        };

        let med_name = ep.medication.as_deref().unwrap_or("none");
        let med_str = get_medication_name(med_name, lang);

        let relief_str = match (ep.medication_relief.as_deref(), norm) {
            (Some("helped"), "be") => "Дапамагло",
            (Some("helped"), "en") => "Helped",
            (Some("helped"), _) => "Помогло",
            (Some("partially"), "be") => "Часткова",
            (Some("partially"), "en") => "Partially",
            (Some("partially"), _) => "Частично",
            (Some("not_helped"), "be") => "Не дапамагло",
            (Some("not_helped"), "en") => "Not helped",
            (Some("not_helped"), _) => "Не помогло",
            _ => "—",
        };

        let status_str = match (ep.status.as_deref(), norm) {
            (Some("completed"), "be") => "Купіраваны",
            (Some("completed"), "en") => "Resolved",
            (Some("completed"), _) => "Купирован",
            (Some("not_resolved"), "be") => "Не прайшоў",
            (Some("not_resolved"), "en") => "Not resolved",
            (Some("not_resolved"), _) => "Не прошла",
            (_, "be") => "Актыўны",
            (_, "en") => "Active",
            _ => "Активен",
        };

        let weather_str = format_weather_display_lang(ep.pressure_hpa, ep.temperature_c, lang).unwrap_or_else(|| "—".to_string());

        let row = vec![
            ep.id.to_string(),
            ep.start_time.clone(),
            ep.end_time.clone().unwrap_or_else(|| "—".to_string()),
            ep.intensity.to_string(),
            get_location_name(&ep.location, lang),
            get_pain_type_name(&ep.pain_type, lang),
            sym_str,
            trig_str,
            med_str,
            relief_str.to_string(),
            weather_str,
            status_str.to_string(),
        ];
        wtr.write_record(&row).unwrap_or(());
    }

    let mut csv_data = wtr.into_inner().unwrap_or_default();
    out.append(&mut csv_data);
    out
}

pub async fn generate_pdf(
    episodes: &[HeadacheEpisode],
    user_id: i64,
    date_gen: &str,
    lang: &str,
) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
    let mut items = Vec::new();

    for ep in episodes {
        let sym_str = if let Some(serde_json::Value::Array(arr)) = &ep.symptoms {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_symptom_name(s, lang)).collect();
            if list.is_empty() { "—".to_string() } else { list.join(", ") }
        } else {
            "—".to_string()
        };

        let trig_str = if let Some(serde_json::Value::Array(arr)) = &ep.triggers {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_trigger_name(s, lang)).collect();
            if list.is_empty() { "—".to_string() } else { list.join(", ") }
        } else {
            "—".to_string()
        };

        let med_name = ep.medication.as_deref().unwrap_or("none");
        let med_str = get_medication_name(med_name, lang);

        let norm = normalize_lang(lang);
        let relief_str = match (ep.medication_relief.as_deref(), norm) {
            (Some("helped"), "be") => "Дапамагло",
            (Some("helped"), "en") => "Helped",
            (Some("helped"), _) => "Помогло",
            (Some("partially"), "be") => "Часткова",
            (Some("partially"), "en") => "Partially",
            (Some("partially"), _) => "Частично",
            (Some("not_helped"), "be") => "Не дапамагло",
            (Some("not_helped"), "en") => "Not helped",
            (Some("not_helped"), _) => "Не помогло",
            _ => "—",
        };

        let status_str = match (ep.status.as_deref(), norm) {
            (Some("completed"), "be") => "Купіраваны",
            (Some("completed"), "en") => "Resolved",
            (Some("completed"), _) => "Купирован",
            (Some("not_resolved"), "be") => "Не прайшоў",
            (Some("not_resolved"), "en") => "Not resolved",
            (Some("not_resolved"), _) => "Не прошла",
            (_, "be") => "Актыўны",
            (_, "en") => "Active",
            _ => "Активен",
        };

        let weather_str = format_weather_display_lang(ep.pressure_hpa, ep.temperature_c, lang).unwrap_or_default();

        let time_str = if let Some(end) = &ep.end_time {
            if ep.start_time.len() >= 10 && end.len() >= 16 && ep.start_time[..10] == end[..10] {
                format!("{} → {}", ep.start_time, &end[11..])
            } else {
                format!("{} → {}", ep.start_time, end)
            }
        } else {
            ep.start_time.clone()
        };

        items.push(PdfEpisodeItem {
            id: ep.id,
            start_time: ep.start_time.clone(),
            time_str,
            intensity: ep.intensity,
            pain_level: get_intensity_label(ep.intensity, lang),
            location: get_location_name(&ep.location, lang),
            pain_type: get_pain_type_name(&ep.pain_type, lang),
            symptoms: sym_str,
            triggers: trig_str,
            medication: med_str,
            relief: relief_str.to_string(),
            status: status_str.to_string(),
            weather: weather_str,
        });
    }

    let payload = PdfExportPayload {
        user_id,
        date_generated: date_gen.to_string(),
        lang: lang.to_string(),
        episodes: items,
    };

    let json_bytes = serde_json::to_vec(&payload)?;

    let tmp_json = format!("/tmp/kitsumed_{}_{}.json", user_id, uuid_or_timestamp());
    let tmp_pdf = format!("/tmp/kitsumed_{}_{}.pdf", user_id, uuid_or_timestamp());

    tokio::fs::write(&tmp_json, json_bytes).await?;

    let script_path = if Path::new("/opt/kitsumed/scripts/generate_pdf.py").exists() {
        "/opt/kitsumed/scripts/generate_pdf.py"
    } else {
        "scripts/generate_pdf.py"
    };

    let output = tokio::process::Command::new("python3")
        .arg(script_path)
        .arg(&tmp_json)
        .arg(&tmp_pdf)
        .output()
        .await?;

    let _ = tokio::fs::remove_file(&tmp_json).await;

    if !output.status.success() {
        let err_msg = String::from_utf8_lossy(&output.stderr);
        let _ = tokio::fs::remove_file(&tmp_pdf).await;
        return Err(format!("Python PDF script failed: {err_msg}").into());
    }

    let pdf_bytes = tokio::fs::read(&tmp_pdf).await?;
    let _ = tokio::fs::remove_file(&tmp_pdf).await;

    Ok(pdf_bytes)
}

fn uuid_or_timestamp() -> u128 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}
