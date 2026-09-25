"""
Meme Russian locale dictionary for Migrebot (Iconic Runet memes: old & new).
"""

MESSAGES = {
    # Main Menu & General
    "main_menu_title": "Главная поляна:",
    "btn_log": "🤕 Записать суету",
    "btn_status": "⏹ Че с болью?",
    "btn_history": "📊 Архив кринжа",
    "btn_export": "📥 Слить инфу доку",
    "btn_reminder": "⏰ Будильник",
    "btn_language": "🌐 Базар / Язык",
    "btn_help": "ℹ️ Поясни за бота",

    # Start & Help
    "start_welcome": (
        "<b>Migrebot</b> — дневник головной боли.\n\n"
        "Голова бо-бо? Не лезь, она тебя сожрет! Жми <b>«🤕 Записать суету»</b> и фиксируй приступ."
    ),
    "help_text": (
        "<b>Расклад по командам:</b>\n\n"
        "• <b>/log</b> — зафиксировать суету и боль\n"
        "• <b>/status</b> — спросить: попустило или еще нет\n"
        "• <b>/export</b> — слить данные для доктора (PDF / CSV)\n"
        "• <b>/reminder</b> — настроить ежедневный пинг\n"
        "• <b>/language</b> — сменить базар (язык)\n"
        "• <b>/cancel</b> — отмена операции"
    ),

    # History
    "history_empty": "В архиве пусто, голова не болела — кайф!",
    "history_title": "<b>Архив кринжа (последние приступы):</b>\n\n",
    "history_card_status_completed": "Попустило",
    "history_card_status_active": "В процессе",
    "history_card_status_not_resolved": "Не отпустило",

    # Headache Log Steps
    "step_1_title": "<b>Когда начался этот кринж?</b>",
    "step_2_title": "<b>Шкала разъеба (1–10)</b>\nНачало: <code>{time_str}</code>",
    "step_3_title": "<b>Куда прилетело?</b>\nУрон: <b>{intensity}/10</b> ({level})",
    "step_4_title": "<b>Какой вайб у боли?</b>\nЗона: <b>{loc_text}</b>",
    "step_5_title": "<b>Что еще завезли? (Симптомы)</b>\nВайб: <b>{pt_text}</b>",
    "step_6_title": "<b>Закинулся таблетками?</b>\nНапиши колеса и дозу или тыкни кнопку ниже:",

    # Intensity labels
    "intensity_mild": "Терпимо (понедельник)",
    "intensity_moderate": "Уже не смешно",
    "intensity_severe": "Помянем",
    "intensity_unbearable": "Это фиаско, братан (Press F)",

    # Summary
    "summary_title": "<b>Итог суеты:</b>\n\n",
    "summary_time": "• Время: <code>{start_time}</code>\n",
    "summary_pain": "• Урон: <b>{intensity}/10</b> ({level})\n",
    "summary_location": "• Локация: {loc_text}\n",
    "summary_pain_type": "• Вайб: {pt_text}\n",
    "summary_symptoms": "• Допы: {symptoms_str}\n",
    "summary_medication": "• Колеса: {med_text}\n\n",
    "summary_confirm": "Сохраняем этот кринж в базу?",

    # Navigation & Action Buttons
    "btn_cancel": "❌ Отмена суеты",
    "btn_back": "⬅️ Назад",
    "btn_save": "✅ Засейвить",
    "btn_edit": "🔄 Переделать",
    "action_cancelled": "Суета отменена, расходимся.",
    "no_active_action": "Тут ничего не происходит, отдыхай.",
    "saved_success": "<b>Суета зафиксирована!</b> (#{episode_id})\n\nПозже бот сам спросит, попустило ли или суета продолжается.",

    # Follow-up Flow (Pain resolution & Medication efficacy)
    "fu_no_active": "Активной боли нет, живем!",
    "fu_pain_question": "<b>Боль отпустила или суета продолжается?</b>",
    "fu_btn_passed": "✅ Попустило (кайф)",
    "fu_btn_not_passed": "❌ Не отпустило (жиза)",
    "fu_when_question": "<b>Когда именно попустило?</b>",
    "fu_when_now": "Только что",
    "fu_when_30m": "Полчаса назад",
    "fu_when_1h": "Час назад",
    "fu_when_2h": "2 часа назад",
    "fu_when_custom": "Вбить время",
    "fu_when_custom_prompt": "<b>Когда отпустило?</b>\nВведи время (например: <code>18:30</code> или <code>полчаса назад</code>):",
    "fu_pain_resolved_recorded": "<b>Попустило — и слава богу!</b>\nВремя финиша: <code>{end_time}</code>.",
    "fu_pain_not_resolved_recorded": "<b>Зафиксировано: боль пока не прошла, жиза.</b>\nДержись, братан, запись обновлена.",

    # Medication Relief Question
    "fu_med_question": "<b>Таблетка ({medication}) зарешала?</b>",
    "fu_med_helped": "✅ Да, имба (помогло)",
    "fu_med_partially": "⚡️ 50/50, так себе",
    "fu_med_not_helped": "❌ Скам, вообще ноль эффекта",
    "fu_med_recorded": "Оценка колес сохранена в базу!",

    # Reminders
    "reminder_title": (
        "<b>Ежедневный пинг</b>\n\n"
        "• Статус: <b>{status_str}</b>\n"
        "• Время: <b>{reminder_time}</b>\n"
        "• Часовой пояс: {tz_label} (сейчас {local_time})"
    ),
    "reminder_status_enabled": "Врублен",
    "reminder_status_disabled": "Вырублен",
    "reminder_daily_prompt": "<b>Болела ли башка сегодня?</b>",
    "reminder_healthy_saved": "Красава, день без боли зафиксирован! Чистый кайф.",
    "reminder_custom_time_prompt": "<b>Когда пинговать?</b>\nВведи время <code>ЧЧ:ММ</code> (например: <code>20:30</code>):",
    "reminder_custom_time_invalid": "<b>Кринж формат!</b>\nНадо <code>ЧЧ:ММ</code> (например: <code>21:30</code>):",
    "reminder_custom_time_saved": "Будильник заряжен на <b>{time}</b> ({tz_label}).",

    # Timezones
    "tz_menu_title": (
        "<b>Часовой пояс</b>\n\n"
        "• Пояс: <b>{tz_label}</b>\n"
        "• Местное время: <b>{local_time}</b>"
    ),
    "tz_custom_prompt": "<b>Введи пояс или город</b> (например: <code>UTC+5</code>, <code>+4</code> или <code>Asia/Almaty</code>):",
    "tz_custom_invalid": "<b>Не вкурил пояс!</b>\nНапиши смещение (<code>UTC+4</code>) или город (<code>Europe/Minsk</code>):",
    "tz_custom_saved": "Пояс зафиксирован: <b>{tz_label}</b> (сейчас {local_time})",

    # Export
    "export_empty": "Сливать нечего, записей ноль.",
    "export_title": "<b>Слить инфу доку</b> (всего приступов: <b>{count}</b>)\n\nВ каком виде упаковать:",
    "export_btn_pdf": "📄 Отчет (PDF)",
    "export_btn_csv": "📊 Табличка (CSV)",
    "export_btn_both": "📦 Все сразу",
    "export_caption_csv": "<b>Табличка для дока (CSV)</b>\n\n• Приступов: <b>{count}</b>\n• Дата: <code>{date}</code>",
    "export_caption_pdf": "<b>Медотчет для невролога (PDF)</b>\n\n• Приступов: <b>{count}</b>\n• Дата: <code>{date}</code>",

    # Language Switcher
    "lang_menu_title": "<b>Выбор базара / Language</b>\n\nВыбирай, на каком языке общаться:",
    "lang_changed": "Базар переключен на <b>Мемный русский</b> 🎭 Зацени вайб!",
}

LOCATION_MAP = {
    "forehead": "Лоб (facepalm)",
    "temple_right": "Висок справа",
    "temple_left": "Висок слева",
    "temple_both": "Виски с двух сторон (тиски)",
    "back_head": "Затылок (база)",
    "one_half": "Полбашки (классика)",
    "all_head": "Вся башка (полный джигурда)",
    "crown": "Макушка (крыша едет)",
    "eyes": "Глаза (вытекают)",
    "neck": "Шея (заклинило)",
}

PAIN_TYPE_MAP = {
    "pulsating": "Пульсирует как жесткий бас",
    "pressing": "Давит как дедлайн",
    "stabbing": "Стреляет как из пулемета",
    "dull": "Тупая как пробка",
    "bursting": "Башка щас лопнет",
    "burning": "Горит как пукан",
}

SYMPTOMS_MAP = {
    "nausea": "Тошнота (кринж)",
    "photophobia": "Свет режет глаза (я вампир)",
    "phonophobia": "Звуки бесят (осуждаю)",
    "aura": "Мультики перед глазами (аура)",
    "dizziness": "Вертолеты (шатает)",
    "osmophobia": "Запахи убивают",
    "none": "Без допов (чистый кайф)",
}

MEDICATION_MAP = {
    "none": "Терплю без колес (терпила)",
    "triptan": "Суматриптан (тяжелая артиллерия)",
    "nsaid": "Ибупрофен (база)",
    "paracetamol": "Парацетамол (плацебо)",
    "analgesic": "Анальгин / Спазмалгон",
    "citramon": "Цитрамончик",
}
