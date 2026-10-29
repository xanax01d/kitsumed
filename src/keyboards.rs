use std::collections::HashSet;
use chrono::{Datelike, NaiveDate};
use teloxide::types::{InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, KeyboardMarkup};
use crate::locales::{get_text, normalize_lang};

pub fn get_main_menu(lang: &str) -> KeyboardMarkup {
    let code = normalize_lang(lang);
    let row1 = vec![
        KeyboardButton::new(get_text("btn_log", code)),
        KeyboardButton::new(get_text("btn_status", code)),
    ];
    let row2 = vec![
        KeyboardButton::new(get_text("btn_history", code)),
        KeyboardButton::new(get_text("btn_export", code)),
    ];
    let row3 = vec![
        KeyboardButton::new(get_text("btn_reminder", code)),
        KeyboardButton::new(get_text("btn_language", code)),
        KeyboardButton::new(get_text("btn_help", code)),
    ];

    KeyboardMarkup::new(vec![row1, row2, row3])
        .resize_keyboard()
        .input_field_placeholder("KitsuMed...")
}

pub fn is_log_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Записать приступ")
        || t.contains("Запісаць прыступ")
        || t.contains("Log Episode")
        || t.contains("Записать суету")
        || t.contains("сбой нейросети")
}

pub fn is_status_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Прошла ли боль")
        || t.contains("Ці прайшоў боль")
        || t.contains("Did Pain Pass")
        || t.contains("Че с болью")
        || t.contains("Статус биочипа")
        || t.contains("Завершить приступ")
}

pub fn is_history_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Мои приступы")
        || t.contains("Мае прыступы")
        || t.contains("My Episodes")
        || t.contains("Архив кринжа")
        || t.contains("Логи киберпсихоза")
}

pub fn is_export_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Экспорт отчета")
        || t.contains("Экспарт справаздачы")
        || t.contains("Export Report")
        || t.contains("Слить инфу доку")
        || t.contains("Слить датапак")
}

pub fn is_reminder_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Напоминания")
        || t.contains("Напаміны")
        || t.contains("Reminders")
        || t.contains("Будильник")
        || t.contains("биомонитора")
}

pub fn is_language_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Язык")
        || t.contains("Мова")
        || t.contains("Language")
        || t.contains("Базар")
        || t.contains("Протокол")
}

pub fn is_help_btn(text: &str) -> bool {
    let t = text.trim();
    t.contains("Справка")
        || t.contains("Даведка")
        || t.contains("Help")
        || t.contains("Поясни за бота")
        || t.contains("Мануал")
}

pub fn is_cancel_btn(text: &str) -> bool {
    let t = text.trim().to_lowercase();
    t == "отмена"
        || t == "cancel"
        || t == "адмена"
        || t.contains("отмена")
        || t.contains("адмена")
        || t.contains("cancel")
        || t.contains("сброс")
}

pub fn get_start_time_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let (t_now, t_30m, t_1h, t_2h, t_custom) = match code {
        "meme" => ("⚡️ Щас (свежий завоз)", "⏱ Полчаса назад", "🕰 Час назад", "💀 Давно уже (2ч)", "✍️ Ввести время"),
        "cyberpunk" => ("⚡️ Сейчас // 00m", "⏱ 30 мин назад", "🕰 1 час назад", "💀 2 часа назад", "✍️ Ручной таймкод"),
        "en" => ("⚡️ Just now", "⏱ 30 min ago", "🕰 1 hour ago", "💀 2 hours ago", "✍️ Custom time"),
        _ => ("⚡️ Только что", "⏱ 30 минут назад", "🕰 1 час назад", "💀 2 часа назад", "✍️ Ввести время"),
    };

    let rows = vec![
        vec![
            InlineKeyboardButton::callback(t_now, "hdt:now"),
            InlineKeyboardButton::callback(t_30m, "hdt:-30m"),
        ],
        vec![
            InlineKeyboardButton::callback(t_1h, "hdt:-1h"),
            InlineKeyboardButton::callback(t_2h, "hdt:-2h"),
        ],
        vec![
            InlineKeyboardButton::callback(t_custom, "hdt:custom"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_intensity_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let mut row1 = Vec::new();
    for i in 1..=5 {
        row1.push(InlineKeyboardButton::callback(format!("{i}"), format!("hdi:{i}")));
    }
    let mut row2 = Vec::new();
    for i in 6..=10 {
        row2.push(InlineKeyboardButton::callback(format!("{i}"), format!("hdi:{i}")));
    }
    let nav_row = vec![
        InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
        InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
    ];
    InlineKeyboardMarkup::new(vec![row1, row2, nav_row])
}

pub fn get_location_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(crate::locales::get_location_name("left", code), "hdl:left"),
            InlineKeyboardButton::callback(crate::locales::get_location_name("right", code), "hdl:right"),
        ],
        vec![
            InlineKeyboardButton::callback(crate::locales::get_location_name("both", code), "hdl:both"),
        ],
        vec![
            InlineKeyboardButton::callback(crate::locales::get_location_name("forehead_temples", code), "hdl:forehead_temples"),
            InlineKeyboardButton::callback(crate::locales::get_location_name("back_head", code), "hdl:back_head"),
        ],
        vec![
            InlineKeyboardButton::callback(crate::locales::get_location_name("diffuse", code), "hdl:diffuse"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_pain_type_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("throbbing", code), "hdp:throbbing"),
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("pressing", code), "hdp:pressing"),
        ],
        vec![
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("stabbing", code), "hdp:stabbing"),
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("dull", code), "hdp:dull"),
        ],
        vec![
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("bursting", code), "hdp:bursting"),
            InlineKeyboardButton::callback(crate::locales::get_pain_type_name("burning", code), "hdp:burning"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_symptoms_keyboard(selected: &[String], lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let syms = [
        ("nausea", "vomiting"),
        ("photophobia", "phonophobia"),
        ("aura", "dizziness"),
        ("odor", ""),
    ];

    let mut rows = Vec::new();
    for (s1, s2) in syms {
        let mut row = Vec::new();
        let mark1 = if selected.contains(&s1.to_string()) { "✅ " } else { "◻️ " };
        let name1 = format!("{mark1}{}", crate::locales::get_symptom_name(s1, code));
        row.push(InlineKeyboardButton::callback(name1, format!("hds:toggle:{s1}")));

        if !s2.is_empty() {
            let mark2 = if selected.contains(&s2.to_string()) { "✅ " } else { "◻️ " };
            let name2 = format!("{mark2}{}", crate::locales::get_symptom_name(s2, code));
            row.push(InlineKeyboardButton::callback(name2, format!("hds:toggle:{s2}")));
        }
        rows.push(row);
    }

    let no_sym_text = match code {
        "en" => "❌ No symptoms",
        "meme" => "❌ Без допов (чисто боль)",
        "cyberpunk" => "❌ Без побочных глитчей",
        _ => "❌ Без сопутствующих симптомов",
    };
    rows.push(vec![InlineKeyboardButton::callback(no_sym_text, "hds:none")]);

    let done_text = match code {
        "en" => "➡️ Continue",
        "meme" => "➡️ Погнали дальше",
        "cyberpunk" => "➡️ Подтвердить данные",
        _ => "➡️ Далее",
    };
    rows.push(vec![InlineKeyboardButton::callback(done_text, "hds:done")]);

    rows.push(vec![
        InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
        InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
    ]);

    InlineKeyboardMarkup::new(rows)
}

pub fn get_triggers_keyboard(selected: &[String], lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let triggers = [
        ("stress", "sleep"),
        ("oversleep", "weather"),
        ("food", "alcohol"),
        ("caffeine", "sensory"),
        ("physical", ""),
    ];

    let mut rows = Vec::new();
    for (t1, t2) in triggers {
        let mut row = Vec::new();
        let mark1 = if selected.contains(&t1.to_string()) { "✅ " } else { "◻️ " };
        let name1 = format!("{mark1}{}", crate::locales::get_trigger_name(t1, code));
        row.push(InlineKeyboardButton::callback(name1, format!("hdtr:toggle:{t1}")));

        if !t2.is_empty() {
            let mark2 = if selected.contains(&t2.to_string()) { "✅ " } else { "◻️ " };
            let name2 = format!("{mark2}{}", crate::locales::get_trigger_name(t2, code));
            row.push(InlineKeyboardButton::callback(name2, format!("hdtr:toggle:{t2}")));
        }
        rows.push(row);
    }

    let custom_trig_text = get_text("btn_custom_trigger", code);
    rows.push(vec![InlineKeyboardButton::callback(custom_trig_text, "hdtr:custom")]);

    let no_trig_text = get_text("btn_no_triggers", code);
    rows.push(vec![InlineKeyboardButton::callback(no_trig_text, "hdtr:none")]);

    let done_text = match code {
        "en" => "➡️ Continue",
        "meme" => "➡️ Погнали дальше",
        "cyberpunk" => "➡️ Подтвердить данные",
        _ => "➡️ Далее",
    };
    rows.push(vec![InlineKeyboardButton::callback(done_text, "hdtr:done")]);

    rows.push(vec![
        InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
        InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
    ]);

    InlineKeyboardMarkup::new(rows)
}

pub fn get_medication_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let (t_triptan, t_nsaid, t_para, t_analgesic, t_citramon, t_custom, t_none) = match code {
        "meme" => ("💊 Триптаны (тяжелая арта)", "💊 Ибупрофен (база)", "💊 Парацетамол", "💊 Спазмалгон / Анальгин", "💊 Цитрамон", "✍️ Свои колеса", "❌ Без колес (терпим)"),
        "cyberpunk" => ("💊 Триптаны // Боевой нейростим", "💊 НПВП // Обезбол", "💊 Парацетамол // Очиститель", "💊 Спазмалгон // Иммуноблокатор", "💊 Цитрамон", "✍️ Кастомный стим", "❌ Без препаратов (хром терпит)"),
        "en" => ("💊 Triptans (Sumatriptan)", "💊 NSAIDs (Ibuprofen)", "💊 Paracetamol", "💊 Analgesic / Spasmolytics", "💊 Citramon", "✍️ Custom Medication", "❌ No Medication"),
        _ => ("💊 Триптаны (Суматриптан)", "💊 Ибупрофен / НПВП", "💊 Парацетамол", "💊 Спазмалгон / Анальгин", "💊 Цитрамон", "✍️ Свой препарат", "❌ Не принимались"),
    };

    let rows = vec![
        vec![
            InlineKeyboardButton::callback(t_triptan, "hdm:triptan"),
            InlineKeyboardButton::callback(t_nsaid, "hdm:nsaid"),
        ],
        vec![
            InlineKeyboardButton::callback(t_para, "hdm:paracetamol"),
            InlineKeyboardButton::callback(t_analgesic, "hdm:analgesic"),
        ],
        vec![
            InlineKeyboardButton::callback(t_citramon, "hdm:citramon"),
            InlineKeyboardButton::callback(t_custom, "hdm:custom"),
        ],
        vec![
            InlineKeyboardButton::callback(t_none, "hdm:none"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_medication_time_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let (t_0m, t_30m, t_60m, t_120m) = match code {
        "meme" => ("⚡️ Сразу вкинул", "⏱ Минут через 30", "🕰 Через часок", "💀 Спустя 2+ часа"),
        "cyberpunk" => ("⚡️ Инъекция сразу // 00m", "⏱ Спустя 30 мин", "🕰 Спустя 1 час", "💀 Через 2+ часа"),
        "en" => ("⚡️ Immediately", "⏱ After 30 min", "🕰 After 1 hour", "💀 After 2+ hours"),
        _ => ("⚡️ Сразу при начале", "⏱ Через 30 минут", "🕰 Через 1 час", "💀 Через 2+ часа"),
    };

    let rows = vec![
        vec![
            InlineKeyboardButton::callback(t_0m, "hdmt:0m"),
            InlineKeyboardButton::callback(t_30m, "hdmt:30m"),
        ],
        vec![
            InlineKeyboardButton::callback(t_60m, "hdmt:60m"),
            InlineKeyboardButton::callback(t_120m, "hdmt:120m"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_medication_relief_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let (t_helped, t_part, t_not) = match code {
        "meme" => ("✅ Попустило (помогло)", "⚡️ Немного сняло", "❌ Ваще ноль эффекта"),
        "cyberpunk" => ("✅ Нейросбой купирован", "⚡️ Частичная стабилизация", "❌ Эффект нулевой"),
        "en" => ("✅ Helped", "⚡️ Partially helped", "❌ Did not help"),
        _ => ("✅ Да, помогло", "⚡️ Частично", "❌ Не помогло"),
    };

    let rows = vec![
        vec![
            InlineKeyboardButton::callback(t_helped, "hdmr:helped"),
            InlineKeyboardButton::callback(t_part, "hdmr:partially"),
        ],
        vec![
            InlineKeyboardButton::callback(t_not, "hdmr:not_helped"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_relief_time_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback("⚡️ 15–30 мин", "hdmrt:15m"),
            InlineKeyboardButton::callback("⏱ 30–60 мин", "hdmrt:30m"),
        ],
        vec![
            InlineKeyboardButton::callback("🕰 1–2 часа", "hdmrt:60m"),
            InlineKeyboardButton::callback("⏳ 2–3 часа", "hdmrt:120m"),
        ],
        vec![
            InlineKeyboardButton::callback("🐢 Больше 3 часов", "hdmrt:180m"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_confirm_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(get_text("btn_save", code), "hdc:save"),
            InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdc:cancel"),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("btn_back", code), "hdn:back"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_cancel_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    InlineKeyboardMarkup::new(vec![vec![
        InlineKeyboardButton::callback(get_text("btn_cancel", code), "hdn:cancel"),
    ]])
}

pub fn get_followup_pain_keyboard(ep_id: i32, lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(get_text("fu_btn_passed", code), format!("fu:pain_passed:{ep_id}")),
            InlineKeyboardButton::callback(get_text("fu_btn_not_passed", code), format!("fu:pain_not_passed:{ep_id}")),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_followup_when_keyboard(ep_id: i32, lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(get_text("fu_when_now", code), format!("fu:set_when:{ep_id}:now")),
            InlineKeyboardButton::callback(get_text("fu_when_30m", code), format!("fu:set_when:{ep_id}:-30m")),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("fu_when_1h", code), format!("fu:set_when:{ep_id}:-1h")),
            InlineKeyboardButton::callback(get_text("fu_when_2h", code), format!("fu:set_when:{ep_id}:-2h")),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("fu_when_custom", code), format!("fu:custom_when:{ep_id}")),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_followup_medication_keyboard(ep_id: i32, lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(get_text("fu_med_helped", code), format!("fu:med_relief:{ep_id}:helped")),
            InlineKeyboardButton::callback(get_text("fu_med_partially", code), format!("fu:med_relief:{ep_id}:partially")),
        ],
        vec![
            InlineKeyboardButton::callback(get_text("fu_med_not_helped", code), format!("fu:med_relief:{ep_id}:not_helped")),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_reminder_settings_keyboard(enabled: bool, lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let toggle_text = if enabled {
        match code {
            "en" => "🔕 Disable Reminders",
            "meme" => "🔕 Вырубить будильник",
            "cyberpunk" => "🔕 Отключить биомонитор",
            _ => "🔕 Отключить опрос",
        }
    } else {
        match code {
            "en" => "🔔 Enable Reminders",
            "meme" => "🔔 Врубить будильник",
            "cyberpunk" => "🔔 Активировать биомонитор",
            _ => "🔔 Включить опрос",
        }
    };

    let change_time_text = match code {
        "en" => "⏰ Change Time",
        "meme" => "⏰ Сменить время",
        "cyberpunk" => "⏰ Таймер калибровки",
        _ => "⏰ Изменить время",
    };

    let change_tz_text = match code {
        "en" => "🌐 Timezone",
        "meme" => "🌐 Часовой пояс",
        "cyberpunk" => "🌐 Сектор / Пояс",
        _ => "🌐 Часовой пояс",
    };

    let rows = vec![
        vec![InlineKeyboardButton::callback(toggle_text, "rem:toggle")],
        vec![InlineKeyboardButton::callback(change_time_text, "rem:time")],
        vec![InlineKeyboardButton::callback(change_tz_text, "rem:tz")],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_timezone_keyboard() -> InlineKeyboardMarkup {
    let presets = [
        ("Калининград (UTC+2)", "Europe/Kaliningrad"),
        ("Москва / СПб (UTC+3)", "Europe/Moscow"),
        ("Самара (UTC+4)", "Europe/Samara"),
        ("Екатеринбург (UTC+5)", "Asia/Yekaterinburg"),
        ("Омск (UTC+6)", "Asia/Omsk"),
        ("Красноярск (UTC+7)", "Asia/Krasnoyarsk"),
        ("Иркутск (UTC+8)", "Asia/Irkutsk"),
        ("Владивосток (UTC+10)", "Asia/Vladivostok"),
        ("Минск (UTC+3)", "Europe/Minsk"),
        ("Киев (UTC+2)", "Europe/Kyiv"),
        ("Алматы (UTC+5)", "Asia/Almaty"),
        ("Ташкент (UTC+5)", "Asia/Tashkent"),
        ("Тбилиси (UTC+4)", "Asia/Tbilisi"),
        ("Ереван (UTC+4)", "Asia/Yerevan"),
        ("Баку (UTC+4)", "Asia/Baku"),
        ("Лондон (UTC+0)", "Europe/London"),
        ("Берлин (UTC+1)", "Europe/Berlin"),
        ("Нью-Йорк (UTC-5)", "America/New_York"),
    ];

    let mut rows = Vec::new();
    for chunk in presets.chunks(2) {
        let mut row = Vec::new();
        for (label, tz_id) in chunk {
            row.push(InlineKeyboardButton::callback(*label, format!("tz:set:{tz_id}")));
        }
        rows.push(row);
    }
    rows.push(vec![InlineKeyboardButton::callback("✍️ Ввести пояс / смещение", "tz:custom")]);
    rows.push(vec![InlineKeyboardButton::callback("⬅️ Назад", "rem:back")]);
    InlineKeyboardMarkup::new(rows)
}

pub fn get_reminder_prompt_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let (t_ok, t_log) = match code {
        "en" => ("🟢 No, I'm fine", "🤕 Yes, log headache"),
        "meme" => ("🟢 Чилим, голова ок", "🤕 Да, голова бо-бо"),
        "cyberpunk" => ("🟢 Хром в норме", "🤕 Зафиксировать сбой"),
        _ => ("🟢 Нет, не болела", "🤕 Да, записать приступ"),
    };

    let rows = vec![
        vec![
            InlineKeyboardButton::callback(t_ok, "remp:ok"),
            InlineKeyboardButton::callback(t_log, "remp:log"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_language_keyboard(current: &str) -> InlineKeyboardMarkup {
    let mark = |code: &str| if code == current { " ✅" } else { "" };
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(format!("🇷🇺 Русский{}", mark("ru")), "lang:ru"),
            InlineKeyboardButton::callback(format!("🇬🇧 English{}", mark("en")), "lang:en"),
        ],
        vec![
            InlineKeyboardButton::callback(format!("🎭 Мемный (Рунет){}", mark("meme")), "lang:meme"),
            InlineKeyboardButton::callback(format!("🦾 Киберпанк{}", mark("cyberpunk")), "lang:cyberpunk"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_export_keyboard(lang: &str) -> InlineKeyboardMarkup {
    let code = normalize_lang(lang);
    let rows = vec![
        vec![
            InlineKeyboardButton::callback(get_text("export_btn_csv", code), "hde:csv"),
        ],
    ];
    InlineKeyboardMarkup::new(rows)
}

pub fn get_month_name(_year: i32, month: u32, lang: &str) -> &'static str {
    let code = normalize_lang(lang);
    match (code, month) {
        ("be", 1) => "Студзень", ("be", 2) => "Люты", ("be", 3) => "Сакавік", ("be", 4) => "Красавік",
        ("be", 5) => "Май", ("be", 6) => "Чэрвень", ("be", 7) => "Ліпень", ("be", 8) => "Жнівень",
        ("be", 9) => "Верасень", ("be", 10) => "Кастрычнік", ("be", 11) => "Лістапад", ("be", 12) => "Снежань",
        ("en", 1) => "January", ("en", 2) => "February", ("en", 3) => "March", ("en", 4) => "April",
        ("en", 5) => "May", ("en", 6) => "June", ("en", 7) => "July", ("en", 8) => "August",
        ("en", 9) => "September", ("en", 10) => "October", ("en", 11) => "November", ("en", 12) => "December",
        _ => match month {
            1 => "Январь", 2 => "Февраль", 3 => "Март", 4 => "Апрель",
            5 => "Май", 6 => "Июнь", 7 => "Июль", 8 => "Август",
            9 => "Сентябрь", 10 => "Октябрь", 11 => "Ноябрь", 12 => "Декабрь",
            _ => "Месяц",
        }
    }
}

pub fn build_calendar_keyboard(
    year: i32,
    month: u32,
    pain_days: &HashSet<u32>,
    today: NaiveDate,
    lang: &str,
) -> (InlineKeyboardMarkup, usize, usize) {
    let code = normalize_lang(lang);
    let mut rows = Vec::new();

    let (prev_y, prev_m) = if month == 1 { (year - 1, 12) } else { (year, month - 1) };
    let (next_y, next_m) = if month == 12 { (year + 1, 1) } else { (year, month + 1) };

    let m_name = get_month_name(year, month, code);
    let header_row = vec![
        InlineKeyboardButton::callback("◀️", format!("cal:nav:{prev_y}:{prev_m}")),
        InlineKeyboardButton::callback(format!("{m_name} {year}"), "cal:ignore"),
        InlineKeyboardButton::callback("▶️", format!("cal:nav:{next_y}:{next_m}")),
    ];
    rows.push(header_row);

    let days_header = match code {
        "en" => vec!["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        _ => vec!["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    };
    let dow_row = days_header
        .into_iter()
        .map(|d| InlineKeyboardButton::callback(d, "cal:ignore"))
        .collect();
    rows.push(dow_row);

    let first_day = NaiveDate::from_ymd_opt(year, month, 1).unwrap_or(today);
    let next_month_first = if month == 12 {
        NaiveDate::from_ymd_opt(year + 1, 1, 1).unwrap_or(today)
    } else {
        NaiveDate::from_ymd_opt(year, month + 1, 1).unwrap_or(today)
    };
    let total_days = (next_month_first - first_day).num_days() as u32;

    let start_weekday = first_day.weekday().number_from_monday();

    let mut current_row = Vec::new();
    for _ in 1..start_weekday {
        current_row.push(InlineKeyboardButton::callback(" ", "cal:ignore"));
    }

    let mut pain_count = 0;
    let mut healthy_count = 0;

    for day in 1..=total_days {
        let date = NaiveDate::from_ymd_opt(year, month, day).unwrap_or(today);
        let is_future = date > today;
        let is_pain = pain_days.contains(&day);

        let (btn_text, callback) = if is_future {
            (format!("{day}"), "cal:future".to_string())
        } else if is_pain {
            pain_count += 1;
            (format!("🔴{day}"), format!("cal:day:{year}:{month}:{day}"))
        } else {
            healthy_count += 1;
            (format!("🟢{day}"), format!("cal:day:{year}:{month}:{day}"))
        };

        current_row.push(InlineKeyboardButton::callback(btn_text, callback));

        if current_row.len() == 7 {
            rows.push(current_row);
            current_row = Vec::new();
        }
    }

    if !current_row.is_empty() {
        while current_row.len() < 7 {
            current_row.push(InlineKeyboardButton::callback(" ", "cal:ignore"));
        }
        rows.push(current_row);
    }

    rows.push(vec![
        InlineKeyboardButton::callback(get_text("calendar_btn_today", code), "cal:today"),
    ]);

    (InlineKeyboardMarkup::new(rows), pain_count, healthy_count)
}
