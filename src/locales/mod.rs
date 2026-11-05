use std::collections::HashMap;
use std::sync::LazyLock;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct LocaleData {
    pub messages: HashMap<String, String>,
    pub location_map: HashMap<String, String>,
    pub pain_type_map: HashMap<String, String>,
    pub symptoms_map: HashMap<String, String>,
    pub medication_map: HashMap<String, String>,
    pub triggers_map: HashMap<String, String>,
}

static RU_JSON: &str = include_str!("../../locales/ru.json");
static BE_JSON: &str = include_str!("../../locales/be.json");
static EN_JSON: &str = include_str!("../../locales/en.json");
static MEME_JSON: &str = include_str!("../../locales/meme.json");
static CYBERPUNK_JSON: &str = include_str!("../../locales/cyberpunk.json");

static LOCALES: LazyLock<HashMap<&'static str, LocaleData>> = LazyLock::new(|| {
    let mut map = HashMap::new();
    map.insert("ru", serde_json::from_str(RU_JSON).expect("ru locale"));
    map.insert("be", serde_json::from_str(BE_JSON).expect("be locale"));
    map.insert("en", serde_json::from_str(EN_JSON).expect("en locale"));
    map.insert("meme", serde_json::from_str(MEME_JSON).expect("meme locale"));
    map.insert("cyberpunk", serde_json::from_str(CYBERPUNK_JSON).expect("cyberpunk locale"));
    map
});

pub fn normalize_lang(lang: &str) -> &'static str {
    let cleaned = lang.trim().to_lowercase();
    if cleaned == "be" || cleaned.starts_with("be") || cleaned == "by" || cleaned == "bel" {
        "be"
    } else if cleaned == "ru" || cleaned.starts_with("ru") {
        "ru"
    } else if cleaned == "en" || cleaned.starts_with("en") {
        "en"
    } else if cleaned.contains("mem") {
        "meme"
    } else if cleaned.contains("cyber") || cleaned == "cp" {
        "cyberpunk"
    } else {
        "ru"
    }
}

pub fn get_text(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.messages.get(key) {
            return val.clone();
        }
    }
    // Fallback to RU
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.messages.get(key) {
            return val.clone();
        }
    }
    format!("[{key}]")
}

pub fn get_text_fmt(key: &str, lang: &str, replacements: &[(&str, &str)]) -> String {
    let mut text = get_text(key, lang);
    for (k, v) in replacements {
        let pattern = format!("{{{k}}}");
        text = text.replace(&pattern, v);
    }
    text
}

pub fn get_location_name(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.location_map.get(key) {
            return val.clone();
        }
    }
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.location_map.get(key) {
            return val.clone();
        }
    }
    key.to_string()
}

pub fn get_pain_type_name(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.pain_type_map.get(key) {
            return val.clone();
        }
    }
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.pain_type_map.get(key) {
            return val.clone();
        }
    }
    key.to_string()
}

pub fn get_symptom_name(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.symptoms_map.get(key) {
            return val.clone();
        }
    }
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.symptoms_map.get(key) {
            return val.clone();
        }
    }
    key.to_string()
}

pub fn get_trigger_name(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.triggers_map.get(key) {
            return val.clone();
        }
        let alias = match key {
            "skip_food" => "food",
            "fatigue" => "stress",
            "lack_of_sleep" => "sleep",
            _ => "",
        };
        if !alias.is_empty() {
            if let Some(val) = loc.triggers_map.get(alias) {
                return val.clone();
            }
        }
    }
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.triggers_map.get(key) {
            return val.clone();
        }
        let alias = match key {
            "skip_food" => "food",
            "fatigue" => "stress",
            "lack_of_sleep" => "sleep",
            _ => "",
        };
        if !alias.is_empty() {
            if let Some(val) = loc.triggers_map.get(alias) {
                return val.clone();
            }
        }
    }
    key.to_string()
}

pub fn get_medication_name(key: &str, lang: &str) -> String {
    let code = normalize_lang(lang);
    if let Some(loc) = LOCALES.get(code) {
        if let Some(val) = loc.medication_map.get(key) {
            return val.clone();
        }
    }
    if let Some(loc) = LOCALES.get("ru") {
        if let Some(val) = loc.medication_map.get(key) {
            return val.clone();
        }
    }
    key.to_string()
}

pub fn get_intensity_label(val: i32, lang: &str) -> String {
    let code = normalize_lang(lang);
    if val <= 3 {
        get_text("intensity_mild", code)
    } else if val <= 6 {
        get_text("intensity_moderate", code)
    } else if val <= 8 {
        get_text("intensity_severe", code)
    } else {
        get_text("intensity_unbearable", code)
    }
}
