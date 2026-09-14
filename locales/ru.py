"""
Russian locale dictionary for Migrebot (Clean & Minimalist).
"""

MESSAGES = {
    # Main Menu & General
    "main_menu_title": "Главное меню:",
    "btn_log": "🤕 Записать приступ",
    "btn_status": "⏹ Прошла ли боль?",
    "btn_history": "📊 Мои приступы",
    "btn_export": "📥 Экспорт отчета",
    "btn_reminder": "⏰ Напоминания",
    "btn_language": "🌐 Язык",
    "btn_help": "ℹ️ Справка",

    # Start & Help
    "start_welcome": (
        "<b>Migrebot</b> — дневник головной боли и мигрени.\n\n"
        "Нажмите <b>«🤕 Записать приступ»</b>, чтобы зафиксировать боль."
    ),
    "help_text": (
        "<b>Команды бота:</b>\n\n"
        "• <b>/log</b> — записать приступ\n"
        "• <b>/status</b> — проверить, прошла ли боль\n"
        "• <b>/export</b> — выгрузить отчет (PDF / CSV)\n"
        "• <b>/reminder</b> — настроить ежедневный опрос\n"
        "• <b>/language</b> — сменить язык интерфейса\n"
        "• <b>/cancel</b> — отмена действия"
    ),

    # History
    "history_empty": "В дневнике пока нет сохраненных записей.",
    "history_title": "<b>История приступов:</b>\n\n",
    "history_card_status_completed": "Завершен",
    "history_card_status_active": "Активен",
    "history_card_status_not_resolved": "Не прошла",
    "history_card_header": "Приступ #{id} ({status})",
    "history_card_time": "• Время: <code>{time}</code>\n",
    "history_card_pain": "• Боль: <b>{intensity}/10</b> ({level})\n",
    "history_card_loc": "• Локация: {loc} | {pt}\n",
    "history_card_sym": "• Симптомы: {sym}\n",
    "history_card_triggers": "• Триггеры: {triggers}\n",
    "history_card_med": "• Препарат: {med}",

    # Headache Log Steps
    "step_1_title": "<b>Когда началась боль?</b>",
    "step_2_title": "<b>Интенсивность боли (1–10)</b>\nНачало: <code>{time_str}</code>",
    "step_3_title": "<b>Локализация боли</b>\nБоль: <b>{intensity}/10</b> ({level})",
    "step_4_title": "<b>Характер боли</b>\nЛокация: <b>{loc_text}</b>",
    "step_5_title": "<b>Сопутствующие симптомы</b>\nХарактер: <b>{pt_text}</b>",
    "step_triggers_title": "<b>Что спровоцировало приступ?</b>\nВыберите возможные триггеры или введите свой:",
    "custom_trigger_prompt": "<b>Провоцирующий фактор (триггер)</b>\nВведите, что могло вызвать боль (например: <i>кондиционер, духота, поездка, кофе</i>):",
    "btn_custom_trigger": "✍️ Свой вариант",
    "btn_no_triggers": "❌ Без явного триггера",
    "step_6_title": "<b>Принятый препарат</b>\nУкажите название и дозировку или нажмите кнопку ниже:",
    "med_time_question": "<b>Когда вы приняли препарат ({medication}) относительно начала боли?</b>",
    "relief_time_question": "<b>Через сколько времени после приема таблетки боль полностью прошла?</b>",

    # Intensity labels
    "intensity_mild": "Слабая",
    "intensity_moderate": "Умеренная",
    "intensity_severe": "Сильная",
    "intensity_unbearable": "Невыносимая",

    # Summary
    "summary_title": "<b>Итог записи</b>\n\n",
    "summary_time": "• Время: <code>{start_time}</code>\n",
    "summary_time_resolved": "• Время: <code>{start_time} → {end_time}</code> ({duration})\n",
    "summary_status_completed": "• Статус: 🟢 Купирован (боль прошла)\n",
    "summary_status_active": "• Статус: 🔴 Активен (приступ продолжается)\n",
    "summary_pain": "• Боль: <b>{intensity}/10</b> ({level})\n",
    "summary_location": "• Локация: {loc_text}\n",
    "summary_pain_type": "• Характер: {pt_text}\n",
    "summary_symptoms": "• Симптомы: {symptoms_str}\n",
    "summary_triggers": "• Триггеры: {triggers_str}\n",
    "summary_medication": "• Препарат: {med_text}\n\n",
    "summary_confirm": "Сохранить запись?",

    # Calendar
    "calendar_title": "<b>Календарь приступов</b> — {month_name} {year}\n\n🔴 Дней с болью: <b>{pain_days}</b>\n🟢 Дней без боли: <b>{healthy_days}</b>\n\n<i>Нажмите на день для просмотра подробностей:</i>",
    "calendar_btn_today": "📅 Текущий месяц",
    "calendar_day_healthy": "<b>{date_str}</b> — день без головной боли 🟢\n\nПриступов не зафиксировано.",
    "calendar_day_episodes_title": "<b>Приступы за {date_str}</b> (всего: {count}):\n\n",
    "calendar_future_alert": "Этот день еще не наступил.",
    "calendar_btn_back": "⬅️ Назад к календарю",

    # Navigation & Action Buttons
    "btn_cancel": "❌ Отмена",
    "btn_back": "⬅️ Назад",
    "btn_save": "✅ Сохранить",
    "btn_edit": "🔄 Изменить",
    "action_cancelled": "Запись отменена.",
    "no_active_action": "Нет активного действия.",
    "saved_success": "<b>Приступ сохранен</b> (#{episode_id})\n\nБот сам поинтересуется самочувствием через некоторое время.",
    "saved_completed_success": "<b>Приступ зафиксирован и завершен</b> (#{episode_id})\n\n🟢 Длительность: <code>{duration}</code>.\nРады, что вам стало лучше!",

    # Follow-up Flow (Pain resolution & Medication efficacy)
    "fu_no_active": "Нет активного приступа для проверки.",
    "fu_pain_question": "<b>Прошла ли головная боль?</b>",
    "fu_btn_passed": "✅ Да, прошла",
    "fu_btn_not_passed": "❌ Нет, не прошла",
    "fu_when_question": "<b>Когда прошла боль?</b>",
    "fu_when_now": "Только что",
    "fu_when_30m": "30 минут назад",
    "fu_when_1h": "1 час назад",
    "fu_when_2h": "2 часа назад",
    "fu_when_custom": "Ввести время",
    "fu_when_custom_prompt": "<b>Время окончания боли</b>\nВведите время (например: <code>18:30</code> или <code>30 минут назад</code>):",
    "fu_pain_resolved_recorded": "<b>Боль прошла.</b>\nВремя окончания: <code>{end_time}</code>.",
    "fu_pain_not_resolved_recorded": "<b>Зафиксировано: боль пока не прошла.</b>\nЗапись обновлена в дневнике.",

    # Medication Relief Question
    "fu_med_question": "<b>Помог ли принятый препарат ({medication})?</b>",
    "fu_med_helped": "✅ Помогло",
    "fu_med_partially": "⚡️ Частично",
    "fu_med_not_helped": "❌ Не помогло",
    "fu_med_recorded": "Оценка действия препарата сохранена.",

    # Reminders
    "reminder_title": (
        "<b>Ежедневный опрос</b>\n\n"
        "• Статус: <b>{status_str}</b>\n"
        "• Время: <b>{reminder_time}</b>\n"
        "• Пояс: {tz_label} (сейчас {local_time})"
    ),
    "reminder_status_enabled": "Включен",
    "reminder_status_disabled": "Отключен",
    "reminder_daily_prompt": "<b>Болела ли голова сегодня?</b>",
    "reminder_healthy_saved": "Отметка сохранена: день без головной боли.",
    "reminder_custom_time_prompt": "<b>Время опроса</b>\nВведите время в формате <code>ЧЧ:ММ</code> (например: <code>20:30</code>):",
    "reminder_custom_time_invalid": "<b>Неверный формат времени</b>\nВведите время в формате <code>ЧЧ:ММ</code> (например: <code>21:30</code>):",
    "reminder_custom_time_saved": "Время опроса установлено: <b>{time}</b> ({tz_label}).",

    # Timezones
    "tz_menu_title": (
        "<b>Часовой пояс</b>\n\n"
        "• Пояс: <b>{tz_label}</b>\n"
        "• Местное время: <b>{local_time}</b>"
    ),
    "tz_custom_prompt": "<b>Часовой пояс</b>\nВведите смещение или город (например: <code>UTC+5</code>, <code>+4</code> или <code>Asia/Almaty</code>):",
    "tz_custom_invalid": "<b>Пояс не распознан</b>\nУкажите смещение (например <code>UTC+4</code>) или название (<code>Europe/Minsk</code>):",
    "tz_custom_saved": "Часовой пояс сохранен: <b>{tz_label}</b> (сейчас {local_time})",

    # Export
    "export_empty": "В дневнике пока нет записей для экспорта.",
    "export_title": "<b>Экспорт дневника</b> (записей: <b>{count}</b>)\n\nВыберите формат:",
    "export_btn_pdf": "📄 Отчет (PDF)",
    "export_btn_csv": "📊 Таблица (CSV)",
    "export_btn_both": "📦 Оба формата",
    "export_caption_csv": "<b>Выгрузка данных (CSV)</b>\n\n• Записей: <b>{count}</b>\n• Дата: <code>{date}</code>",
    "export_caption_pdf": "<b>Медицинский отчет (PDF)</b>\n\n• Записей: <b>{count}</b>\n• Дата: <code>{date}</code>",

    # Language Switcher
    "lang_menu_title": "<b>Выбор языка / Language</b>\n\nВыберите предпочтительный язык интерфейса:",
    "lang_changed": "Язык изменен на <b>Русский</b> 🇷🇺",
}

LOCATION_MAP = {
    "left": "👈 Слева (односторонняя)",
    "right": "Справа (односторонняя) 👉",
    "both": "↔️ С обеих сторон",
    "forehead_temples": "🎯 Лоб и виски",
    "back_head": "🔙 Затылок и шея",
    "diffuse": "🌐 Вся голова (диффузная)",
    # Granular aliases
    "forehead": "Лоб",
    "temple_right": "Висок (справа)",
    "temple_left": "Висок (слева)",
    "temple_both": "Виски (с обеих сторон)",
    "one_half": "Вся половина головы",
    "all_head": "Вся голова",
    "crown": "Теменная зона (макушка)",
    "eyes": "Область глаз",
    "neck": "Шея и основание черепа",
}

PAIN_TYPE_MAP = {
    "throbbing": "💓 Пульсирующая (мигренозная)",
    "pulsating": "💓 Пульсирующая",
    "pressing": "🗜 Сжимающая / как обруч",
    "stabbing": "🎯 Колющая / прострелы",
    "dull": "🌧 Тупая / ноющая",
    "bursting": "💥 Распирающая",
    "burning": "Жгучая",
}

SYMPTOMS_MAP = {
    "nausea": "Тошнота",
    "vomiting": "Рвота",
    "photophobia": "Светобоязнь",
    "phonophobia": "Звукобоязнь",
    "aura": "Зрительная аура",
    "dizziness": "Головокружение",
    "odor": "Чувствительность к запахам",
    "osmophobia": "Чувствительность к запахам",
    "none": "Без сопутствующих симптомов",
}

MEDICATION_MAP = {
    "none": "Не принимались",
    "triptan": "Суматриптан / Триптаны",
    "nsaid": "Ибупрофен / НПВП",
    "paracetamol": "Парацетамол",
    "analgesic": "Анальгин / Спазмалгон",
    "citramon": "Цитрамон",
}

TRIGGERS_MAP = {
    "stress": "Стресс / переутомление",
    "sleep": "Недосып",
    "oversleep": "Много сна / пересып",
    "weather": "Погода / перепад давления",
    "food": "Голод / пропуск еды",
    "alcohol": "Алкоголь",
    "caffeine": "Кофеин",
    "sensory": "Шум / свет / духота",
    "physical": "Физическая нагрузка",
    "none": "Без явного триггера",
}

