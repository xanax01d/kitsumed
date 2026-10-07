use crate::models::HeadacheEpisode;
use crate::locales::{get_location_name, get_medication_name, get_pain_type_name, get_symptom_name, get_trigger_name};

pub fn generate_csv(episodes: &[HeadacheEpisode], lang: &str) -> Vec<u8> {
    let mut wtr = csv::WriterBuilder::new().from_writer(Vec::new());

    // Write UTF-8 BOM for Excel Cyrillic compatibility
    let mut out = vec![0xEF, 0xBB, 0xBF];

    let headers = match lang {
        "en" => vec![
            "Episode ID", "Start Time", "End Time", "Intensity (1-10)", "Location",
            "Pain Type", "Symptoms", "Triggers", "Medication", "Relief", "Status"
        ],
        _ => vec![
            "ID приступа", "Начало", "Окончание", "Интенсивность (1-10)", "Локализация",
            "Характер боли", "Симптомы", "Триггеры", "Препарат", "Эффект препарата", "Статус"
        ],
    };

    wtr.write_record(&headers).unwrap_or(());

    for ep in episodes {
        let sym_str = if let Some(serde_json::Value::Array(arr)) = &ep.symptoms {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_symptom_name(s, lang)).collect();
            list.join(", ")
        } else {
            "—".to_string()
        };

        let trig_str = if let Some(serde_json::Value::Array(arr)) = &ep.triggers {
            let list: Vec<String> = arr.iter().filter_map(|v| v.as_str()).map(|s| get_trigger_name(s, lang)).collect();
            list.join(", ")
        } else {
            "—".to_string()
        };

        let med_name = ep.medication.as_deref().unwrap_or("none");
        let med_str = get_medication_name(med_name, lang);

        let relief_str = match ep.medication_relief.as_deref() {
            Some("helped") => "Помогло",
            Some("partially") => "Частично",
            Some("not_helped") => "Не помогло",
            _ => "—",
        };

        let status_str = match ep.status.as_deref() {
            Some("completed") => "Купирован",
            Some("not_resolved") => "Не прошла",
            _ => "Активен",
        };

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
            status_str.to_string(),
        ];
        wtr.write_record(&row).unwrap_or(());
    }

    let mut csv_data = wtr.into_inner().unwrap_or_default();
    out.append(&mut csv_data);
    out
}
