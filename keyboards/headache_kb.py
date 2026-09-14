from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Set, List, Optional

from locales import (
    get_text,
    get_location_map,
    get_pain_type_map,
    get_symptoms_map,
    get_medication_map,
    get_triggers_map,
    SUPPORTED_LANGUAGES,
)

# --- Callback Data Classes ---
class TimeCallback(CallbackData, prefix="hdt"):
    preset: str

class IntensityCallback(CallbackData, prefix="hdi"):
    value: int

class LocationCallback(CallbackData, prefix="hdl"):
    value: str

class PainTypeCallback(CallbackData, prefix="hdp"):
    value: str

class SymptomCallback(CallbackData, prefix="hds"):
    action: str  # "toggle", "none", "done"
    value: str

class TriggerCallback(CallbackData, prefix="hdtr", sep="|"):
    action: str  # "toggle", "none", "custom", "done"
    value: str

class MedicationCallback(CallbackData, prefix="hdm"):
    value: str

class MedicationTimeCallback(CallbackData, prefix="hdmt"):
    value: str  # "0m", "30m", "60m", "120m"

class MedicationReliefCallback(CallbackData, prefix="hdmr"):
    value: str  # "helped", "partially", "not_helped"

class ReliefTimeCallback(CallbackData, prefix="hdmrt"):
    value: str  # "15m", "30m", "60m", "120m", "180m"

class ConfirmCallback(CallbackData, prefix="hdc"):
    action: str  # "save", "cancel"

class NavCallback(CallbackData, prefix="hdn"):
    action: str  # "back", "cancel"

class ExportCallback(CallbackData, prefix="hde"):
    format: str  # "pdf", "csv", "both"

class FollowUpCallback(CallbackData, prefix="fu", sep="|"):
    action: str  # "pain_passed", "pain_not_passed", "set_when", "custom_when", "med_relief", "close"
    episode_id: int
    value: str = ""

class LanguageCallback(CallbackData, prefix="lang", sep="|"):
    code: str  # "ru", "en", "meme"


# --- Navigation Helper ---
def add_navigation_buttons(
    builder: InlineKeyboardBuilder,
    show_back: bool = True,
    show_cancel: bool = True,
    lang: str = "ru",
):
    nav_row = []
    if show_back:
        nav_row.append(
            InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data=NavCallback(action="back").pack()
            )
        )
    if show_cancel:
        nav_row.append(
            InlineKeyboardButton(
                text=get_text("btn_cancel", lang),
                callback_data=NavCallback(action="cancel").pack()
            )
        )
    if nav_row:
        builder.row(*nav_row)


# --- 1. Start Time Keyboard ---
def get_start_time_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        builder.row(
            InlineKeyboardButton(text="⚡️ Щас (свежий завоз)", callback_data=TimeCallback(preset="now").pack()),
            InlineKeyboardButton(text="⏱ Полчаса назад", callback_data=TimeCallback(preset="-30m").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🕐 Час назад", callback_data=TimeCallback(preset="-1h").pack()),
            InlineKeyboardButton(text="🕑 2 часа назад", callback_data=TimeCallback(preset="-2h").pack())
        )
        builder.row(
            InlineKeyboardButton(text="✍️ Свое время (вручную)", callback_data=TimeCallback(preset="custom").pack())
        )
    elif lang == "cyberpunk":
        builder.row(
            InlineKeyboardButton(text="⚡️ Прямо сейчас (онлайн)", callback_data=TimeCallback(preset="now").pack()),
            InlineKeyboardButton(text="⏱ 30 мин назад", callback_data=TimeCallback(preset="-30m").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🕐 1 час назад", callback_data=TimeCallback(preset="-1h").pack()),
            InlineKeyboardButton(text="🕑 2 часа назад", callback_data=TimeCallback(preset="-2h").pack())
        )
        builder.row(
            InlineKeyboardButton(text="✍️ Ввести таймкод вручную", callback_data=TimeCallback(preset="custom").pack())
        )
    elif lang == "en":
        builder.row(
            InlineKeyboardButton(text="⚡️ Right now", callback_data=TimeCallback(preset="now").pack()),
            InlineKeyboardButton(text="⏱ 30m ago", callback_data=TimeCallback(preset="-30m").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🕐 1h ago", callback_data=TimeCallback(preset="-1h").pack()),
            InlineKeyboardButton(text="🕑 2h ago", callback_data=TimeCallback(preset="-2h").pack())
        )
        builder.row(
            InlineKeyboardButton(text="✍️ Custom time", callback_data=TimeCallback(preset="custom").pack())
        )
    else:
        builder.row(
            InlineKeyboardButton(text="⚡️ Прямо сейчас", callback_data=TimeCallback(preset="now").pack()),
            InlineKeyboardButton(text="⏱ 30 мин назад", callback_data=TimeCallback(preset="-30m").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🕐 1 час назад", callback_data=TimeCallback(preset="-1h").pack()),
            InlineKeyboardButton(text="🕑 2 часа назад", callback_data=TimeCallback(preset="-2h").pack())
        )
        builder.row(
            InlineKeyboardButton(text="✍️ Указать другое время", callback_data=TimeCallback(preset="custom").pack())
        )
    add_navigation_buttons(builder, show_back=False, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 2. Intensity Keyboard (1-10) ---
def get_intensity_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row_1 = [
        InlineKeyboardButton(
            text=f"{i} 🟢" if i <= 3 else f"{i} 🟡",
            callback_data=IntensityCallback(value=i).pack()
        )
        for i in range(1, 6)
    ]
    builder.row(*row_1)

    row_2 = [
        InlineKeyboardButton(
            text=f"{i} 🟡" if i == 6 else (f"{i} 🟠" if i <= 8 else f"{i} 🔴"),
            callback_data=IntensityCallback(value=i).pack()
        )
        for i in range(6, 11)
    ]
    builder.row(*row_2)

    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 3. Location Keyboard ---
LOCATION_MAP = {
    "left": "👈 Слева (односторонняя)",
    "right": "Справа (односторонняя) 👉",
    "both": "↔️ С обеих сторон",
    "forehead_temples": "🎯 Лоб и виски",
    "back_head": "🔙 Затылок и шея",
    "diffuse": "🌐 Вся голова (диффузная)"
}

def get_location_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        builder.row(
            InlineKeyboardButton(text="👈 Слева (полбашки)", callback_data=LocationCallback(value="left").pack()),
            InlineKeyboardButton(text="Справа (полбашки) 👉", callback_data=LocationCallback(value="right").pack())
        )
        builder.row(
            InlineKeyboardButton(text="↔️ Бархатные тяги (с 2 сторон)", callback_data=LocationCallback(value="both").pack()),
            InlineKeyboardButton(text="🎯 Лоб (facepalm)", callback_data=LocationCallback(value="forehead_temples").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Затылок (база)", callback_data=LocationCallback(value="back_head").pack()),
            InlineKeyboardButton(text="🌐 Вся башка (шеф, это тотал)", callback_data=LocationCallback(value="diffuse").pack())
        )
    elif lang == "cyberpunk":
        builder.row(
            InlineKeyboardButton(text="👈 Левый височный имплант", callback_data=LocationCallback(value="left").pack()),
            InlineKeyboardButton(text="Правый височный имплант 👉", callback_data=LocationCallback(value="right").pack())
        )
        builder.row(
            InlineKeyboardButton(text="↔️ Оба полушария (КЗ)", callback_data=LocationCallback(value="both").pack()),
            InlineKeyboardButton(text="🎯 Лобовая кора (нейропорт)", callback_data=LocationCallback(value="forehead_temples").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Чип Релик / Шея", callback_data=LocationCallback(value="back_head").pack()),
            InlineKeyboardButton(text="🌐 Тотальный перегрев CPU", callback_data=LocationCallback(value="diffuse").pack())
        )
    elif lang == "en":
        builder.row(
            InlineKeyboardButton(text="👈 Left side", callback_data=LocationCallback(value="left").pack()),
            InlineKeyboardButton(text="Right side 👉", callback_data=LocationCallback(value="right").pack())
        )
        builder.row(
            InlineKeyboardButton(text="↔️ Both sides", callback_data=LocationCallback(value="both").pack()),
            InlineKeyboardButton(text="🎯 Forehead & temples", callback_data=LocationCallback(value="forehead_temples").pack())
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Back of head & neck", callback_data=LocationCallback(value="back_head").pack()),
            InlineKeyboardButton(text="🌐 Whole head (diffuse)", callback_data=LocationCallback(value="diffuse").pack())
        )
    else:
        builder.row(
            InlineKeyboardButton(text=LOCATION_MAP["left"], callback_data=LocationCallback(value="left").pack()),
            InlineKeyboardButton(text=LOCATION_MAP["right"], callback_data=LocationCallback(value="right").pack())
        )
        builder.row(
            InlineKeyboardButton(text=LOCATION_MAP["both"], callback_data=LocationCallback(value="both").pack()),
            InlineKeyboardButton(text=LOCATION_MAP["forehead_temples"], callback_data=LocationCallback(value="forehead_temples").pack())
        )
        builder.row(
            InlineKeyboardButton(text=LOCATION_MAP["back_head"], callback_data=LocationCallback(value="back_head").pack()),
            InlineKeyboardButton(text=LOCATION_MAP["diffuse"], callback_data=LocationCallback(value="diffuse").pack())
        )
    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 4. Pain Type Keyboard ---
PAIN_TYPE_MAP = {
    "throbbing": "💓 Пульсирующая (мигренозная)",
    "pressing": "🗜 Сжимающая / как обруч (ГБН)",
    "bursting": "💥 Распирающая",
    "stabbing": "🎯 Колющая / прострелы",
    "dull": "🌧 Тупая / ноющая"
}

def get_pain_type_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        m_types = [
            ("throbbing", "💓 Фонк долбит (пульсирует)"),
            ("pressing", "🗜 Давит как дедлайн и долги"),
            ("bursting", "💥 Башка щас сделает бум"),
            ("stabbing", "🎯 Стреляет как пулемет"),
            ("dull", "🌧 Тупая как диалог с тюбиком"),
        ]
        for key, text in m_types:
            builder.row(InlineKeyboardButton(text=text, callback_data=PainTypeCallback(value=key).pack()))
    elif lang == "cyberpunk":
        cp_types = [
            ("throbbing", "💓 Пульсирующий импульс (шина)"),
            ("pressing", "🗜 Давление гидравлики (тиски)"),
            ("bursting", "💥 Риск разрыва сосудов"),
            ("stabbing", "🎯 Прострел Черного льда"),
            ("dull", "🌧 Фоновый нейрошум"),
        ]
        for key, text in cp_types:
            builder.row(InlineKeyboardButton(text=text, callback_data=PainTypeCallback(value=key).pack()))
    elif lang == "en":
        en_types = [
            ("throbbing", "💓 Throbbing / Pulsating"),
            ("pressing", "🗜 Pressing / Tight band"),
            ("bursting", "💥 Bursting / Splitting"),
            ("stabbing", "🎯 Stabbing / Sharp"),
            ("dull", "🌧 Dull ache"),
        ]
        for key, text in en_types:
            builder.row(InlineKeyboardButton(text=text, callback_data=PainTypeCallback(value=key).pack()))
    else:
        for key, text in PAIN_TYPE_MAP.items():
            builder.row(InlineKeyboardButton(text=text, callback_data=PainTypeCallback(value=key).pack()))
    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()



# --- 5. Symptoms Keyboard ---
ALL_SYMPTOMS = {
    "photophobia": "💡 Светобоязнь (фотофобия)",
    "phonophobia": "🔊 Звукобоязнь (фонофобия)",
    "nausea": "🤢 Тошнота",
    "vomiting": "🤮 Рвота",
    "aura": "✨ Зрительная аура (мерцание)",
    "dizziness": "🌀 Головокружение",
    "odor": "👃 Чувствительность к запахам"
}

def get_symptoms_keyboard(selected: Set[str] = None, lang: str = "ru") -> InlineKeyboardMarkup:
    selected = selected or set()
    builder = InlineKeyboardBuilder()

    if lang == "meme":
        sym_dict = {
            "photophobia": "💡 Свет режет глаза (вампир)",
            "phonophobia": "🔊 Звуки бесят (осуждаю)",
            "nausea": "🤢 Тошнота (кринж)",
            "vomiting": "🤮 Рвота",
            "aura": "✨ Мультики перед глазами (аура)",
            "dizziness": "🌀 Вертолеты (шатает)",
            "odor": "👃 Запахи убивают",
        }
        no_sym_text = "❌ Без допов (чистый кайф)"
        done_text = "➡️ Далее"
    elif lang == "cyberpunk":
        sym_dict = {
            "photophobia": "💡 Перегрузка оптики Kiroshi (свет)",
            "phonophobia": "🔊 Глитч аудиопроцессора (звук)",
            "nausea": "🤢 Сбой вестибулярного модуля",
            "vomiting": "🤮 Выброс биомассы (рвота)",
            "aura": "✨ Глитчи матрицы / Аура",
            "dizziness": "🌀 Дрифт гироскопа",
            "odor": "👃 Перегрузка ольфакторного чипа",
        }
        no_sym_text = "❌ Без аномалий (чистый хром)"
        done_text = "➡️ Подтвердить"
    elif lang == "en":
        sym_dict = {
            "photophobia": "💡 Light sensitivity",
            "phonophobia": "🔊 Sound sensitivity",
            "nausea": "🤢 Nausea",
            "vomiting": "🤮 Vomiting",
            "aura": "✨ Visual aura",
            "dizziness": "🌀 Dizziness",
            "odor": "👃 Smell sensitivity",
        }
        no_sym_text = "❌ No associated symptoms"
        done_text = "➡️ Continue"
    else:
        sym_dict = ALL_SYMPTOMS
        no_sym_text = "❌ Нет сопутствующих симптомов"
        done_text = "➡️ Продолжить"

    for key, label in sym_dict.items():
        mark = "✅ " if key in selected else "◻️ "
        builder.row(
            InlineKeyboardButton(
                text=f"{mark}{label}",
                callback_data=SymptomCallback(action="toggle", value=key).pack()
            )
        )

    no_sym_mark = "✅ " if "none" in selected else "◻️ "
    builder.row(
        InlineKeyboardButton(
            text=f"{no_sym_mark}{no_sym_text}",
            callback_data=SymptomCallback(action="none", value="none").pack()
        )
    )

    real_selected = [s for s in selected if s != "none"]
    count_label = f" ({len(real_selected)})" if real_selected else ""
    builder.row(
        InlineKeyboardButton(
            text=f"{done_text}{count_label}",
            callback_data=SymptomCallback(action="done", value="done").pack()
        )
    )

    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 5b. Triggers Keyboard ---
TRIGGERS_ORDER = [
    ("stress", "weather"),
    ("sleep", "oversleep"),
    ("food", "alcohol"),
    ("caffeine", "sensory"),
    ("physical",),
]

def get_triggers_keyboard(selected: Optional[Set[str]] = None, lang: str = "ru") -> InlineKeyboardMarkup:
    selected = selected or set()
    builder = InlineKeyboardBuilder()
    trig_map = get_triggers_map(lang)

    for row in TRIGGERS_ORDER:
        row_btns = []
        for key in row:
            label = trig_map.get(key, key)
            mark = "✅ " if key in selected else "◻️ "
            row_btns.append(
                InlineKeyboardButton(
                    text=f"{mark}{label}",
                    callback_data=TriggerCallback(action="toggle", value=key).pack()
                )
            )
        builder.row(*row_btns)

    # Custom trigger option
    custom_text = get_text("btn_custom_trigger", lang)
    builder.row(
        InlineKeyboardButton(
            text=custom_text,
            callback_data=TriggerCallback(action="custom", value="custom").pack()
        )
    )

    # None option
    no_trig_mark = "✅ " if "none" in selected else "◻️ "
    no_trig_text = get_text("btn_no_triggers", lang)
    builder.row(
        InlineKeyboardButton(
            text=f"{no_trig_mark}{no_trig_text}",
            callback_data=TriggerCallback(action="none", value="none").pack()
        )
    )

    # Done / continue
    real_selected = [s for s in selected if s != "none"]
    count_label = f" ({len(real_selected)})" if real_selected else ""
    if lang == "meme":
        done_text = "➡️ Далее"
    elif lang == "cyberpunk":
        done_text = "➡️ Подтвердить"
    elif lang == "en":
        done_text = "➡️ Continue"
    else:
        done_text = "➡️ Продолжить"

    builder.row(
        InlineKeyboardButton(
            text=f"{done_text}{count_label}",
            callback_data=TriggerCallback(action="done", value="done").pack()
        )
    )

    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 6. Medication Keyboard ---
MEDICATION_MAP = {
    "none": "Не принимались",
}

def get_medication_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        skip_text = "❌ Терплю без колес (терпила)"
    elif lang == "cyberpunk":
        skip_text = "❌ Без химии (чистый хром)"
    elif lang == "en":
        skip_text = "❌ No medication taken"
    else:
        skip_text = "❌ Не принимал(а) препараты"

    builder.row(
        InlineKeyboardButton(
            text=skip_text,
            callback_data=MedicationCallback(value="none").pack()
        )
    )
    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()

get_manual_medication_keyboard = get_medication_keyboard


# --- 6a. Medication Time Taken Keyboard ---
def get_medication_time_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        labels = [
            ("⚡️ Сразу вкинул(а)", "0m"),
            ("⏱ Через 30 мин", "30m"),
            ("⏱ Через 1 час", "60m"),
            ("⏱ Спустя 2+ часа", "120m"),
        ]
    elif lang == "cyberpunk":
        labels = [
            ("⚡️ Мгновенный инжект (<15м)", "0m"),
            ("⏱ Через 30 мин", "30m"),
            ("⏱ Через 1 час", "60m"),
            ("⏱ Через 2+ часа", "120m"),
        ]
    elif lang == "en":
        labels = [
            ("⚡️ Immediately / <15m", "0m"),
            ("⏱ After 30 min", "30m"),
            ("⏱ After 1 hour", "60m"),
            ("⏱ After 2+ hours", "120m"),
        ]
    else:
        labels = [
            ("⚡️ Сразу / до 15 мин", "0m"),
            ("⏱ Через 30 минут", "30m"),
            ("⏱ Через 1 час", "60m"),
            ("⏱ Через 2+ часа", "120m"),
        ]

    for i in range(0, len(labels), 2):
        row_btns = [
            InlineKeyboardButton(text=lbl, callback_data=MedicationTimeCallback(value=val).pack())
            for lbl, val in labels[i:i+2]
        ]
        builder.row(*row_btns)

    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 6b. Medication Relief Keyboard ---
def get_medication_relief_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_med_helped", lang),
            callback_data=MedicationReliefCallback(value="helped").pack()
        ),
        InlineKeyboardButton(
            text=get_text("fu_med_partially", lang),
            callback_data=MedicationReliefCallback(value="partially").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_med_not_helped", lang),
            callback_data=MedicationReliefCallback(value="not_helped").pack()
        )
    )
    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 6c. Relief Duration Keyboard ---
def get_relief_time_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lang == "meme":
        labels = [
            ("⏱ За 30 мин (имба)", "30m"),
            ("⏱ За 1 час (норм)", "60m"),
            ("⏱ За 2 часа (потно)", "120m"),
            ("⏱ За 3+ часа (еле выжил)", "180m"),
        ]
    elif lang == "cyberpunk":
        labels = [
            ("⏱ Стабилизация за 30 мин", "30m"),
            ("⏱ Стабилизация за 1 час", "60m"),
            ("⏱ Стабилизация за 2 часа", "120m"),
            ("⏱ Стабилизация за 3+ часа", "180m"),
        ]
    elif lang == "en":
        labels = [
            ("⏱ Within 30 min", "30m"),
            ("⏱ Within 1 hour", "60m"),
            ("⏱ Within 2 hours", "120m"),
            ("⏱ After 3+ hours", "180m"),
        ]
    else:
        labels = [
            ("⏱ Через 30 минут", "30m"),
            ("⏱ Через 1 час", "60m"),
            ("⏱ Через 2 часа", "120m"),
            ("⏱ Через 3+ часа", "180m"),
        ]

    for i in range(0, len(labels), 2):
        row_btns = [
            InlineKeyboardButton(text=lbl, callback_data=ReliefTimeCallback(value=val).pack())
            for lbl, val in labels[i:i+2]
        ]
        builder.row(*row_btns)

    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 7. Confirmation Keyboard ---
def get_confirm_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_save", lang),
            callback_data=ConfirmCallback(action="save").pack()
        )
    )
    add_navigation_buttons(builder, show_back=True, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 8. Cancel & Navigation Keyboard ---
def get_cancel_keyboard(show_back: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    add_navigation_buttons(builder, show_back=show_back, show_cancel=True, lang=lang)
    return builder.as_markup()


# --- 9. Export Keyboard ---
def get_export_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("export_btn_pdf", lang),
            callback_data=ExportCallback(format="pdf").pack()
        ),
        InlineKeyboardButton(
            text=get_text("export_btn_csv", lang),
            callback_data=ExportCallback(format="csv").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("export_btn_both", lang),
            callback_data=ExportCallback(format="both").pack()
        )
    )
    return builder.as_markup()


# --- 10. Follow-Up Keyboards (Pain Resolution & Medication Relief) ---
def get_followup_pain_keyboard(episode_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_btn_passed", lang),
            callback_data=FollowUpCallback(action="pain_passed", episode_id=episode_id).pack()
        ),
        InlineKeyboardButton(
            text=get_text("fu_btn_not_passed", lang),
            callback_data=FollowUpCallback(action="pain_not_passed", episode_id=episode_id).pack()
        )
    )
    return builder.as_markup()


def get_followup_when_keyboard(episode_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_when_now", lang),
            callback_data=FollowUpCallback(action="set_when", episode_id=episode_id, value="now").pack()
        ),
        InlineKeyboardButton(
            text=get_text("fu_when_30m", lang),
            callback_data=FollowUpCallback(action="set_when", episode_id=episode_id, value="-30m").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_when_1h", lang),
            callback_data=FollowUpCallback(action="set_when", episode_id=episode_id, value="-1h").pack()
        ),
        InlineKeyboardButton(
            text=get_text("fu_when_2h", lang),
            callback_data=FollowUpCallback(action="set_when", episode_id=episode_id, value="-2h").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_when_custom", lang),
            callback_data=FollowUpCallback(action="custom_when", episode_id=episode_id).pack()
        )
    )
    return builder.as_markup()


def get_followup_medication_keyboard(episode_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_med_helped", lang),
            callback_data=FollowUpCallback(action="med_relief", episode_id=episode_id, value="helped").pack()
        ),
        InlineKeyboardButton(
            text=get_text("fu_med_partially", lang),
            callback_data=FollowUpCallback(action="med_relief", episode_id=episode_id, value="partially").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("fu_med_not_helped", lang),
            callback_data=FollowUpCallback(action="med_relief", episode_id=episode_id, value="not_helped").pack()
        )
    )
    return builder.as_markup()


# --- 11. Language Selection Keyboard ---
def get_language_keyboard(current_lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in SUPPORTED_LANGUAGES.items():
        mark = "✅ " if code == current_lang else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{mark}{label}",
                callback_data=LanguageCallback(code=code).pack()
            )
        )
    return builder.as_markup()
