use serde::Deserialize;
use std::time::Duration;

#[derive(Debug, Deserialize)]
struct CurrentWeather {
    pub surface_pressure: Option<f32>,
    pub temperature_2m: Option<f32>,
}

#[derive(Debug, Deserialize)]
struct OpenMeteoResponse {
    pub current: Option<CurrentWeather>,
}

/// Маппинг часового пояса в координаты центра региона (широта, долгота)
pub fn timezone_to_coordinates(tz: &str) -> (f64, f64) {
    match tz {
        "Europe/Moscow" => (55.7558, 37.6176),
        "Europe/Minsk" => (53.9045, 27.5615),
        "Europe/Kyiv" => (50.4501, 30.5234),
        "Europe/Warsaw" => (52.2297, 21.0122),
        "Europe/Vilnius" => (54.6872, 25.2797),
        "Europe/Riga" => (56.9496, 24.1052),
        "Europe/Tallinn" => (59.4370, 24.7536),
        "Europe/Berlin" => (52.5200, 13.4050),
        "Europe/London" => (51.5074, -0.1278),
        "Europe/Paris" => (48.8566, 2.3522),
        "Europe/Prague" => (50.0755, 14.4378),
        "Europe/Rome" => (41.9028, 12.4964),
        "Europe/Madrid" => (40.4168, -3.7038),
        "Asia/Tbilisi" => (41.7151, 44.8271),
        "Asia/Yerevan" => (40.1792, 44.4991),
        "Asia/Baku" => (40.4093, 49.8671),
        "Asia/Almaty" => (43.2220, 76.8512),
        "Asia/Tashkent" => (41.2995, 69.2401),
        "Asia/Bishkek" => (42.8746, 74.5698),
        "Asia/Dushanbe" => (38.5598, 68.7870),
        "Asia/Yekaterinburg" => (56.8389, 60.6057),
        "Asia/Omsk" => (54.9885, 73.3242),
        "Asia/Novosibirsk" => (55.0084, 82.9357),
        "Asia/Krasnoyarsk" => (56.0153, 92.8932),
        "Asia/Irkutsk" => (52.2870, 104.3050),
        "Asia/Yakutsk" => (62.0355, 129.6755),
        "Asia/Vladivostok" => (43.1198, 131.8869),
        _ => (55.7558, 37.6176), // По умолчанию Москва
    }
}

/// Перевод гектопаскалей (hPa) в миллиметры ртутного столба (мм рт. ст.)
pub fn hpa_to_mmhg(hpa: f32) -> i32 {
    (hpa * 0.750062).round() as i32
}

/// Получение текущей погоды (давление в hPa и температура в °C) через Open-Meteo API
pub async fn fetch_current_weather(tz: &str) -> Option<(f32, f32)> {
    let (lat, lon) = timezone_to_coordinates(tz);
    let url = format!(
        "https://api.open-meteo.com/v1/forecast?latitude={:.4}&longitude={:.4}&current=surface_pressure,temperature_2m",
        lat, lon
    );

    let client = reqwest::Client::builder()
        .timeout(Duration::from_millis(2500))
        .build()
        .ok()?;

    let res = client.get(&url).send().await.ok()?;
    if !res.status().is_success() {
        return None;
    }

    let body: OpenMeteoResponse = res.json().await.ok()?;
    let curr = body.current?;

    Some((curr.surface_pressure?, curr.temperature_2m?))
}

/// Форматирование строки погоды для карточки приступа
pub fn format_weather_display(pressure_hpa: Option<f32>, temp_c: Option<f32>) -> Option<String> {
    match (pressure_hpa, temp_c) {
        (Some(p), Some(t)) => {
            let mmhg = hpa_to_mmhg(p);
            let sign = if t > 0.0 { "+" } else { "" };
            Some(format!("{}{}°C, {} мм рт. ст.", sign, t.round() as i32, mmhg))
        }
        (Some(p), None) => {
            let mmhg = hpa_to_mmhg(p);
            Some(format!("{} мм рт. ст.", mmhg))
        }
        (None, Some(t)) => {
            let sign = if t > 0.0 { "+" } else { "" };
            Some(format!("{}{}°C", sign, t.round() as i32))
        }
        (None, None) => None,
    }
}
