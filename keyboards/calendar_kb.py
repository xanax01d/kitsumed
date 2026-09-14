import calendar
from datetime import date
from typing import Set, Tuple
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from locales import get_text


class CalendarCallback(CallbackData, prefix="cal", sep="|"):
    action: str  # "prev", "next", "today", "day", "back", "ignore", "future"
    year: int = 0
    month: int = 0
    day: int = 0


MONTH_NAMES_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]
MONTH_NAMES_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEKDAYS_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def get_month_name(year: int, month: int, lang: str = "ru") -> str:
    if lang == "en":
        return MONTH_NAMES_EN[month]
    return MONTH_NAMES_RU[month]


def build_calendar_keyboard(
    year: int,
    month: int,
    pain_days: Set[int],
    today: date,
    lang: str = "ru",
) -> Tuple[InlineKeyboardMarkup, int, int]:
    """
    Builds an interactive 7-column calendar keyboard for the specified month.
    Marks days with headache as 🔴{day} and pain-free days (up to today) as 🟢{day}.
    Returns (keyboard_markup, pain_days_count, healthy_days_count).
    """
    builder = InlineKeyboardBuilder()
    month_name = get_month_name(year, month, lang)

    # 1. Navigation header row: [ ◀️ ] [ Month Year ] [ ▶️ ]
    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)

    builder.row(
        InlineKeyboardButton(
            text="◀️",
            callback_data=CalendarCallback(action="prev", year=prev_y, month=prev_m).pack()
        ),
        InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data=CalendarCallback(action="today", year=today.year, month=today.month).pack()
        ),
        InlineKeyboardButton(
            text="▶️",
            callback_data=CalendarCallback(action="next", year=next_y, month=next_m).pack()
        ),
    )

    # 2. Weekday abbreviation headers
    weekdays = WEEKDAYS_EN if lang == "en" else WEEKDAYS_RU
    builder.row(*[
        InlineKeyboardButton(
            text=wd,
            callback_data=CalendarCallback(action="ignore").pack()
        )
        for wd in weekdays
    ])

    # 3. Calendar day grid
    cal = calendar.monthcalendar(year, month)
    healthy_days_count = 0
    pain_days_count = 0

    for week in cal:
        row_btns = []
        for day in week:
            if day == 0:
                row_btns.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data=CalendarCallback(action="ignore").pack()
                    )
                )
            else:
                cur_date = date(year, month, day)
                if day in pain_days:
                    pain_days_count += 1
                    btn_text = f"🔴{day}"
                    cb = CalendarCallback(action="day", year=year, month=month, day=day).pack()
                elif cur_date <= today:
                    healthy_days_count += 1
                    btn_text = f"🟢{day}"
                    cb = CalendarCallback(action="day", year=year, month=month, day=day).pack()
                else:
                    btn_text = f"{day}"
                    cb = CalendarCallback(action="future", year=year, month=month, day=day).pack()

                row_btns.append(InlineKeyboardButton(text=btn_text, callback_data=cb))
        builder.row(*row_btns)

    # 4. Controls row: [ 📅 Текущий месяц ]
    builder.row(
        InlineKeyboardButton(
            text=get_text("calendar_btn_today", lang),
            callback_data=CalendarCallback(action="today", year=today.year, month=today.month).pack()
        )
    )

    return builder.as_markup(), pain_days_count, healthy_days_count
