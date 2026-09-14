"""
Cyberpunk 2077 / Dark Future locale dictionary for Migrebot.
Atmospheric, immersive Night City netrunner & chrome lore.
"""

MESSAGES = {
    # Main Menu & General
    "main_menu_title": "<b>Терминал Киберпространства // Night City Net:</b>",
    "btn_log": "⚡️ Зафиксировать сбой нейросети",
    "btn_status": "⏹ Статус биочипа",
    "btn_history": "📊 Логи киберпсихоза",
    "btn_export": "📥 Слить датапак рипердоку",
    "btn_reminder": "⏰ Калибровка биомонитора",
    "btn_language": "🌐 Протокол / Язык",
    "btn_help": "ℹ️ Мануал нетраннера",

    # Start & Help
    "start_welcome": (
        "<b>Migrebot v2.077</b> — кибернетический биомонитор головных болей и глитчей нейрочипа.\n\n"
        "Слышишь шум в имплантах или словил Черный лед? Жми <b>«⚡️ Зафиксировать сбой нейросети»</b>, чумба, пока не вызвали Макс-так."
    ),
    "help_text": (
        "<b>Командная строка деки:</b>\n\n"
        "• <b>/log</b> — инициализировать запись перегрузки нейросети\n"
        "• <b>/status</b> — диагностика: отпустил ли глитч или система горит\n"
        "• <b>/export</b> — компиляция логов для рипердока (PDF / CSV)\n"
        "• <b>/reminder</b> — цикл ежедневной калибровки биомонитора\n"
        "• <b>/language</b> — конфигурация протокола локализации\n"
        "• <b>/cancel</b> — прерывание протокола (SIGKILL)"
    ),

    # History
    "history_empty": "В буфере чисто. Никаких перегрузок и сбоев биочипа. Хром чист, чумба!",
    "history_title": "<b>Логи нейросбоев (последние дампы памяти):</b>\n\n",
    "history_card_status_completed": "Купирован (система стабильна)",
    "history_card_status_active": "КРИТИЧЕСКИЙ СБОЙ (в процессе)",
    "history_card_status_not_resolved": "Перегрузка не снята",
    "history_card_header": "Инцидент #{id} ({status})",
    "history_card_time": "• Таймкод: <code>{time}</code>\n",
    "history_card_pain": "• Урон нейросети: <b>{intensity}/10</b> ({level})\n",
    "history_card_loc": "• Сектор: {loc} | {pt}\n",
    "history_card_sym": "• Аномалии: {sym}\n",
    "history_card_med": "• Стимы/Фарма: {med}",

    # Headache Log Steps
    "step_1_title": "<b>Таймкод: когда начался сбой нейросети?</b>",
    "step_2_title": "<b>Уровень перегрузки синапсов (1–10)</b>\nИнициация: <code>{time_str}</code>",
    "step_3_title": "<b>Сектор поражения имплантов</b>\nНагрузка: <b>{intensity}/10</b> ({level})",
    "step_4_title": "<b>Характер нейрошума и спазма</b>\nСектор: <b>{loc_text}</b>",
    "step_5_title": "<b>Сопутствующие аномалии биосистемы</b>\nШум: <b>{pt_text}</b>",
    "step_6_title": "<b>Инъекция стимуляторов / Блокаторы</b>\nУкажи химсостав или нажми клавишу на деке:",

    # Intensity labels
    "intensity_mild": "Минорный глитч интерфейса",
    "intensity_moderate": "Перегрев кибердеки",
    "intensity_severe": "Критический сбой биочипа",
    "intensity_unbearable": "Угроза киберпсихоза // Вызывайте Травма Тим",

    # Summary
    "summary_title": "<b>Дамп отчета биомонитора:</b>\n\n",
    "summary_time": "• Таймкод: <code>{start_time}</code>\n",
    "summary_pain": "• Урон нейросети: <b>{intensity}/10</b> ({level})\n",
    "summary_location": "• Сектор: {loc_text}\n",
    "summary_pain_type": "• Характер сбоя: {pt_text}\n",
    "summary_symptoms": "• Аномалии: {symptoms_str}\n",
    "summary_medication": "• Стимы/Фарма: {med_text}\n\n",
    "summary_confirm": "Загрузить пакет данных в память деки?",

    # Navigation & Action Buttons
    "btn_cancel": "❌ Аварийный сброс",
    "btn_back": "⬅️ Назад по стеку",
    "btn_save": "💾 Записать в ядро",
    "btn_edit": "🔄 Перекалибровать",
    "action_cancelled": "Операция прервана. Буфер очищен.",
    "no_active_action": "Нет активных потоков выполнения.",
    "saved_success": "<b>Сбой залогирован!</b> (#{episode_id})\n\nБиомонитор проведет контрольный пинг узлов через заданный интервал.",

    # Follow-up Flow (Pain resolution & Medication efficacy)
    "fu_no_active": "Активных сигнатур боли в нейроинтерфейсе не обнаружено. Ты в строю, самурай.",
    "fu_pain_question": "<b>Биомонитор запрашивает статус: спазм отпустил или синапсы все еще горят?</b>",
    "fu_btn_passed": "✅ Система стабилизирована (отпустило)",
    "fu_btn_not_passed": "❌ Критический перегрев (не прошло)",
    "fu_when_question": "<b>Таймкод стабилизации нейросистемы:</b>",
    "fu_when_now": "Прямо сейчас (онлайн)",
    "fu_when_30m": "30 минут назад",
    "fu_when_1h": "1 час назад",
    "fu_when_2h": "2 часа назад",
    "fu_when_custom": "Ввести таймкод",
    "fu_when_custom_prompt": "<b>Таймкод купирования</b>\nВведи время стабилизации (например: <code>18:30</code> или <code>полчаса назад</code>):",
    "fu_pain_resolved_recorded": "<b>Система в норме. Биомонитор зафиксировал стабилизацию.</b>\nВремя купирования: <code>{end_time}</code>.",
    "fu_pain_not_resolved_recorded": "<b>Внимание: перегрузка не спала. Статус обновлен.</b>\nВключи охлаждение имплантов, чумба, держись.",

    # Medication Relief Question
    "fu_med_question": "<b>Введенный препарат ({medication}) снизил перегрузку?</b>",
    "fu_med_helped": "✅ Эффективно (хром остыл)",
    "fu_med_partially": "⚡️ Частично (слабый дебафф)",
    "fu_med_not_helped": "❌ Паленый стим (ноль эффекта)",
    "fu_med_recorded": "Телеметрия фармакологического отклика внесена в реестр.",

    # Reminders
    "reminder_title": (
        "<b>Калибровка биомонитора</b>\n\n"
        "• Подсистема: <b>{status_str}</b>\n"
        "• Время пинга: <b>{reminder_time}</b>\n"
        "• Временная зона: {tz_label} (местное: {local_time})"
    ),
    "reminder_status_enabled": "АКТИВНА [ОНЛАЙН]",
    "reminder_status_disabled": "ОФФЛАЙН [ОТКЛЮЧЕНА]",
    "reminder_daily_prompt": "<b>Диагностика биомонитора: фиксировался ли сбой синапсов сегодня?</b>",
    "reminder_healthy_saved": "Телеметрия чиста: 24 часа без сбоев нейросети. Хром в порядке!",
    "reminder_custom_time_prompt": "<b>Таймер опроса биомонитора</b>\nВведи время в формате <code>ЧЧ:ММ</code> (например: <code>20:30</code>):",
    "reminder_custom_time_invalid": "<b>Ошибка синтаксиса таймера</b>\nТребуется формат <code>ЧЧ:ММ</code> (например: <code>21:30</code>):",
    "reminder_custom_time_saved": "Цикл опроса синхронизирован: <b>{time}</b> ({tz_label}).",

    # Timezones
    "tz_menu_title": (
        "<b>Конфигурация временного кластера</b>\n\n"
        "• Кластер: <b>{tz_label}</b>\n"
        "• Бортовое время: <b>{local_time}</b>"
    ),
    "tz_custom_prompt": "<b>Ввод координат кластера</b>\nВведи смещение или ноду (например: <code>UTC+3</code>, <code>+4</code> или <code>Asia/Tokyo</code>):",
    "tz_custom_invalid": "<b>Нода времени не найдена</b>\nУкажи валидное смещение (<code>UTC+4</code>) или ноду (<code>Europe/Moscow</code>):",
    "tz_custom_saved": "Временной кластер привязан: <b>{tz_label}</b> (бортовое: {local_time})",

    # Export
    "export_empty": "Буфер логов пуст. Экспортировать нечего, чумба.",
    "export_title": "<b>Компиляция датапака для рипердока</b> (записей: <b>{count}</b>)\n\nВыбери формат шифрования:",
    "export_btn_pdf": "📄 Зашифрованный протокол (PDF)",
    "export_btn_csv": "📊 Сырой дамп матрицы (CSV)",
    "export_btn_both": "📦 Полный датапак (тотал)",
    "export_caption_csv": "<b>Дамп телеметрии для рипердока (CSV)</b>\n\n• Инцидентов: <b>{count}</b>\n• Дата компиляции: <code>{date}</code>",
    "export_caption_pdf": "<b>Клинический отчет нейрохирурга (PDF)</b>\n\n• Инцидентов: <b>{count}</b>\n• Дата компиляции: <code>{date}</code>",

    # Language Switcher
    "lang_menu_title": "<b>Выбор сетевого протокола / Language</b>\n\nВыбери интерфейс коммуникации:",
    "lang_changed": "Интерфейс перепрошит на <b>Киберпанк // Night City Net</b> 🦾 Добро пожаловать в темное будущее, чумба!",
}

LOCATION_MAP = {
    "left": "👈 Левый височный имплант",
    "right": "Правый височный имплант 👉",
    "both": "↔️ Оба полушария (короткое замыкание)",
    "forehead_temples": "🎯 Лобовая кора (разъем нейропорта)",
    "back_head": "🔙 Основание черепа (чип Релик)",
    "diffuse": "🌐 Тотальный перегрев CPU",
    # Granular aliases
    "forehead": "Лобовая кора (разъем нейропорта)",
    "temple_right": "Правый височный имплант",
    "temple_left": "Левый височный имплант",
    "temple_both": "Оба полушария (короткое замыкание)",
    "one_half": "Гемикрания / Половина черепной коробки",
    "all_head": "Тотальный перегрев центрального процессора",
    "crown": "Теменной узел (макушка)",
    "eyes": "Оптические киберимпланты Kiroshi",
    "neck": "Шейные сервоприводы и нейроразъемы",
}

PAIN_TYPE_MAP = {
    "throbbing": "💓 Пульсирующий импульс (перегрузка шины)",
    "pressing": "🗜 Давление гидравлики (тиски)",
    "stabbing": "🎯 Прострел Черного льда (высоковольтный спайк)",
    "dull": "🌧 Фоновый нейрошум / Глухой откат",
    "bursting": "💥 Критическое расширение (риск разрыва сосудов)",
    "pulsating": "💓 Пульсирующий импульс (перегрузка шины)",
    "burning": "Термический ожог синапсов (сварка мозгов)",
}

SYMPTOMS_MAP = {
    "nausea": "Сбой вестибулярного модуля (тошнота)",
    "vomiting": "Выброс биомассы (рвота)",
    "photophobia": "Перегрузка оптики Kiroshi (светобоязнь)",
    "phonophobia": "Глитч аудиопроцессора (звукобоязнь)",
    "aura": "Глитчи интерфейса / Зрительная аура",
    "dizziness": "Дрифт гироскопа (головокружение)",
    "odor": "Перегрузка ольфакторного чипа (запахи)",
    "osmophobia": "Перегрузка ольфакторного чипа (запахи)",
    "none": "Побочных аномалий нет (чистый хром)",
}

MEDICATION_MAP = {
    "none": "Без химии (вывожу на чистом хроме)",
    "triptan": "Суматриптан / Трамадол (тяжелый нейроблокатор)",
    "nsaid": "Ибупрофен / МаксДок (MaxDoc / базовый дебафф)",
    "paracetamol": "Парацетамол (слабый стимулятор)",
    "analgesic": "Анальгин / Спазмалгон (анальгетик)",
    "citramon": "Цитрамон (олдскульный бустер)",
}
