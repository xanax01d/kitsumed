"""
Meme Russian locale dictionary for Migrebot.
Packed with viral, iconic Runet memes (Меллстрой, Скуфы/Альтушки, Чиназес, Сигма, Бархатные тяги, База, Кринж, Тильт).
"""

MESSAGES = {
    # Main Menu & General
    "main_menu_title": "Главная поляна (движ):",
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
        "<b>Расклад по командам (база):</b>\n\n"
        "• <b>/log</b> — зафиксировать приступ и суету\n"
        "• <b>/status</b> — проверить: попустило или плаки-плаки\n"
        "• <b>/export</b> — слить данные для доктора (PDF / CSV)\n"
        "• <b>/reminder</b> — настроить ежедневный пинг\n"
        "• <b>/language</b> — сменить базар (язык)\n"
        "• <b>/cancel</b> — отмена операции"
    ),

    # History
    "history_empty": "В архиве пусто, голова не болела — чиназес, чистый кайф!",
    "history_title": "<b>Архив кринжа (последние приступы):</b>\n\n",
    "history_card_status_completed": "Попустило (сюдааа)",
    "history_card_status_active": "На суете (болит)",
    "history_card_status_not_resolved": "Плаки-плаки (не прошло)",
    "history_card_header": "Суета #{id} ({status})",
    "history_card_time": "• Время: <code>{time}</code>\n",
    "history_card_pain": "• Урон: <b>{intensity}/10</b> ({level})\n",
    "history_card_loc": "• Локация: {loc} | {pt}\n",
    "history_card_sym": "• Допы: {sym}\n",
    "history_card_med": "• Колеса: {med}",

    # Headache Log Steps
    "step_1_title": "<b>Когда начался этот кринж?</b>",
    "step_2_title": "<b>Шкала разъеба (1–10)</b>\nНачало: <code>{time_str}</code>",
    "step_3_title": "<b>Куда прилетело?</b>\nУрон: <b>{intensity}/10</b> ({level})",
    "step_4_title": "<b>Какой вайб у боли?</b>\nЗона: <b>{loc_text}</b>",
    "step_5_title": "<b>Что еще завезли? (Симптомы)</b>\nВайб: <b>{pt_text}</b>",
    "step_6_title": "<b>Закинулся колесами?</b>\nВведи название и дозу или тыкни кнопку ниже:",

    # Intensity labels
    "intensity_mild": "Нормалдаки (понедельник)",
    "intensity_moderate": "Словил тильт (уже не чиназес)",
    "intensity_severe": "Шеф, это тотал (скуф помянул)",
    "intensity_unbearable": "Это фиаско, братан (Press F, мозг вышел из чата)",

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
    "no_active_action": "Тут ничего не происходит, отдыхай, нормис.",
    "saved_success": "<b>Суета зафиксирована!</b> (#{episode_id})\n\nПозже бот сам спросит, попустило или суета продолжается. Думайте.",

    # Follow-up Flow (Pain resolution & Medication efficacy)
    "fu_no_active": "Активной боли нет, живем! Сюдааа!",
    "fu_pain_question": "<b>Боль отпустила или суета продолжается?</b>",
    "fu_btn_passed": "✅ Сюдааа, попустило! (Чиназес)",
    "fu_btn_not_passed": "❌ Плаки-плаки, не отпустило",
    "fu_when_question": "<b>Когда именно попустило?</b>",
    "fu_when_now": "Только что (свежак)",
    "fu_when_30m": "Полчаса назад",
    "fu_when_1h": "Час назад",
    "fu_when_2h": "2 часа назад",
    "fu_when_custom": "Вбить время",
    "fu_when_custom_prompt": "<b>Когда отпустило?</b>\nВведи время (например: <code>18:30</code> или <code>полчаса назад</code>):",
    "fu_pain_resolved_recorded": "<b>Сюдааа, попустило! Чиназес.</b>\nВремя финиша: <code>{end_time}</code>.",
    "fu_pain_not_resolved_recorded": "<b>Зафиксировано: боль пока не прошла. Плаки-плаки.</b>\nДержись, скуф, запись обновлена.",

    # Medication Relief Question
    "fu_med_question": "<b>Таблетка ({medication}) зарешала?</b>",
    "fu_med_helped": "✅ Чиназес, имба! (Помогло)",
    "fu_med_partially": "⚡️ 50/50, так себе",
    "fu_med_not_helped": "❌ Скам века, ноль эффекта",
    "fu_med_recorded": "Статистика по колесам записана в базу. Думайте.",

    # Reminders
    "reminder_title": (
        "<b>Ежедневный пинг</b>\n\n"
        "• Статус: <b>{status_str}</b>\n"
        "• Время: <b>{reminder_time}</b>\n"
        "• Часовой пояс: {tz_label} (сейчас {local_time})"
    ),
    "reminder_status_enabled": "Врублен (на суете)",
    "reminder_status_disabled": "Вырублен (в тильте)",
    "reminder_daily_prompt": "<b>Болела ли башка сегодня?</b>",
    "reminder_healthy_saved": "Красава, день без боли! Сигма мув, чистый кайф.",
    "reminder_custom_time_prompt": "<b>Когда пинговать?</b>\nВведи время <code>ЧЧ:ММ</code> (например: <code>20:30</code>):",
    "reminder_custom_time_invalid": "<b>Кринж формат!</b>\nНадо <code>ЧЧ:ММ</code> (например: <code>21:30</code>):",
    "reminder_custom_time_saved": "Будильник заряжен на <b>{time}</b> ({tz_label}). Сюдааа!",

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
    "export_empty": "Сливать нечего, записей ноль, гуляй.",
    "export_title": "<b>Слить инфу доку</b> (всего приступов: <b>{count}</b>)\n\nВ каком виде упаковать суету:",
    "export_btn_pdf": "📄 Отчет доку (PDF)",
    "export_btn_csv": "📊 Табличка (CSV)",
    "export_btn_both": "📦 Все сразу (тотал)",
    "export_caption_csv": "<b>Табличка для дока (CSV)</b>\n\n• Приступов: <b>{count}</b>\n• Дата: <code>{date}</code>",
    "export_caption_pdf": "<b>Медотчет для невролога (PDF)</b>\n\n• Приступов: <b>{count}</b>\n• Дата: <code>{date}</code>",

    # Language Switcher
    "lang_menu_title": "<b>Выбор базара / Language</b>\n\nВыбирай, на каком языке двигаться дальше:",
    "lang_changed": "Базар переключен на <b>Мемный русский</b> 🎭 Чиназес, сюдааа! Зацени вайб.",
}

LOCATION_MAP = {
    "left": "👈 Слева (полбашки)",
    "right": "Справа (полбашки) 👉",
    "both": "↔️ Бархатные тяги (с 2 сторон)",
    "forehead_temples": "🎯 Лоб (facepalm)",
    "back_head": "🔙 Затылок (база)",
    "diffuse": "🌐 Вся башка (шеф, это тотал)",
    # Granular aliases
    "forehead": "Лоб (facepalm)",
    "temple_right": "Висок справа",
    "temple_left": "Висок слева",
    "temple_both": "Виски (бархатные тяги с двух сторон)",
    "one_half": "Полбашки (классика)",
    "all_head": "Вся башка (шеф, это тотал)",
    "crown": "Макушка (крыша поехала)",
    "eyes": "Глаза (минус зрение)",
    "neck": "Шея (заклинило на суете)",
}

PAIN_TYPE_MAP = {
    "throbbing": "💓 Фонк долбит в череп (пульсирует)",
    "pulsating": "💓 Фонк долбит в череп (пульсирует)",
    "pressing": "🗜 Давит как дедлайн и долги",
    "stabbing": "🎯 Стреляет как пулемет",
    "dull": "🌧 Тупая как диалог с тюбиком",
    "bursting": "💥 Башка щас сделает бум",
    "burning": "Горит как пукан после слива",
}

SYMPTOMS_MAP = {
    "nausea": "Тошнота (кринж поймал)",
    "vomiting": "Рвота (полный тотал)",
    "photophobia": "Свет слепит (вырубите солнце)",
    "phonophobia": "Звуки бесят (осуждаю на максимум)",
    "aura": "Мультики (глитчи матрицы)",
    "dizziness": "Вертолеты (шатает как после вписки)",
    "odor": "Запахи душат",
    "osmophobia": "Запахи душат",
    "none": "Без допов (чистый вайб)",
}

MEDICATION_MAP = {
    "none": "Терплю без колес (терпила)",
    "triptan": "Суматриптан (тяжелая артиллерия / имба)",
    "nsaid": "Ибупрофен (база кормит)",
    "paracetamol": "Парацетамол (мел с сахаром)",
    "analgesic": "Анальгин / Спазмалгон",
    "citramon": "Цитрамончик (бабушкин рецепт)",
}
