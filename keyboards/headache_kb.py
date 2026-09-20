from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Set, List

# Callback data classes
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

class MedicationCallback(CallbackData, prefix="hdm"):
    value: str

class ConfirmCallback(CallbackData, prefix="hdc"):
    action: str  # "save", "cancel"

class NavCallback(CallbackData, prefix="hdn"):
    action: str  # "back", "cancel"


# Navigation helper
def add_navigation_buttons(builder: InlineKeyboardBuilder, show_back: bool = True, show_cancel: bool = True):
    nav_row = []
    if show_back:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=NavCallback(action="back").pack()))
    if show_cancel:
        nav_row.append(InlineKeyboardButton(text="❌ Отмена", callback_data=NavCallback(action="cancel").pack()))
    if nav_row:
        builder.row(*nav_row)


# 1. Start Time Keyboard
def get_start_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
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
    add_navigation_buttons(builder, show_back=False, show_cancel=True)
    return builder.as_markup()


# 2. Intensity Keyboard (1-10)
def get_intensity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Row 1: 1-5 (Mild to moderate)
    builder.row(*[
        InlineKeyboardButton(text=str(i), callback_data=IntensityCallback(value=i).pack())
        for i in range(1, 6)
    ])
    # Row 2: 6-10 (Severe)
    builder.row(*[
        InlineKeyboardButton(text=str(i), callback_data=IntensityCallback(value=i).pack())
        for i in range(6, 11)
    ])
    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()


# 3. Location Keyboard
LOCATION_MAP = {
    "left": "Слева 👈",
    "right": "Справа 👉",
    "both": "С обеих сторон ↔️",
    "forehead_temples": "Лоб и виски 🎯",
    "back_head": "Затылок 🔙",
    "diffuse": "Вся голова 🌐"
}

def get_location_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
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
    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()


# 4. Pain Type Keyboard
PAIN_TYPE_MAP = {
    "throbbing": "Пульсирующая ⚡️",
    "pressing": "Давящая / сжимающая 🗜",
    "bursting": "Распирающая 💥",
    "stabbing": "Колющая / прострелы 🎯",
    "dull": "Тупая / ноющая 🌧"
}

def get_pain_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, text in PAIN_TYPE_MAP.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=PainTypeCallback(value=key).pack()))
    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()


# 5. Symptoms Keyboard (Multi-select)
ALL_SYMPTOMS = {
    "nausea": "🤢 Тошнота",
    "vomiting": "🤮 Рвота",
    "photophobia": "💡 Светобоязнь",
    "phonophobia": "🔊 Звукобоязнь",
    "aura": "✨ Зрительная аура",
    "dizziness": "🌀 Головокружение",
    "odor": "👃 Чувствительность к запахам"
}

def get_symptoms_keyboard(selected: Set[str] = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    builder = InlineKeyboardBuilder()

    for key, label in ALL_SYMPTOMS.items():
        mark = "✅ " if key in selected else "▫️ "
        builder.row(
            InlineKeyboardButton(
                text=f"{mark}{label}",
                callback_data=SymptomCallback(action="toggle", value=key).pack()
            )
        )

    # Option for no symptoms
    no_sym_mark = "✅ " if "none" in selected else "▫️ "
    builder.row(
        InlineKeyboardButton(
            text=f"{no_sym_mark}❌ Нет сопутствующих симптомов",
            callback_data=SymptomCallback(action="none", value="none").pack()
        )
    )

    # Done button
    builder.row(
        InlineKeyboardButton(
            text="➡️ Продолжить",
            callback_data=SymptomCallback(action="done", value="done").pack()
        )
    )

    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()


# 6. Medication Keyboard (Manual text input with skip option)
MEDICATION_MAP = {
    "none": "Не принимались",
}

def get_medication_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for manual medication entry step (optionally skip if no meds taken)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Не принимал(а) препараты",
            callback_data=MedicationCallback(value="none").pack()
        )
    )
    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()

get_manual_medication_keyboard = get_medication_keyboard


# 7. Confirmation Keyboard
def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💾 Сохранить приступ", callback_data=ConfirmCallback(action="save").pack())
    )
    add_navigation_buttons(builder, show_back=True, show_cancel=True)
    return builder.as_markup()


# Cancel only keyboard for text input steps
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data=NavCallback(action="cancel").pack())
    )
    return builder.as_markup()


# 8. Export Keyboard
class ExportCallback(CallbackData, prefix="hde"):
    format: str  # "pdf", "csv", "both"

def get_export_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 Экспорт в PDF", callback_data=ExportCallback(format="pdf").pack()),
        InlineKeyboardButton(text="📊 Экспорт в CSV (Excel)", callback_data=ExportCallback(format="csv").pack())
    )
    builder.row(
        InlineKeyboardButton(text="📦 Скачать оба формата (PDF + CSV)", callback_data=ExportCallback(format="both").pack())
    )
    return builder.as_markup()

