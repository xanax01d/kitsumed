import io
import csv
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from keyboards.headache_kb import (
    LOCATION_MAP,
    PAIN_TYPE_MAP,
    ALL_SYMPTOMS,
    MEDICATION_MAP,
)

# Clean maps for professional medical PDF and CSV exports without broken emoji glyphs
LOCATION_MAP_CLEAN = {
    "left": "Слева",
    "right": "Справа",
    "both": "С обеих сторон",
    "forehead_temples": "Лоб и виски",
    "back_head": "Затылок",
    "diffuse": "Вся голова",
}

PAIN_TYPE_MAP_CLEAN = {
    "throbbing": "Пульсирующая",
    "pressing": "Давящая / сжимающая",
    "bursting": "Распирающая",
    "stabbing": "Колющая / прострелы",
    "dull": "Тупая / ноющая",
}

ALL_SYMPTOMS_CLEAN = {
    "nausea": "Тошнота",
    "vomiting": "Рвота",
    "photophobia": "Светобоязнь",
    "phonophobia": "Звукобоязнь",
    "aura": "Зрительная аура",
    "dizziness": "Головокружение",
    "odor": "Чувствительность к запахам",
}

MEDICATION_MAP_CLEAN = {
    "triptan": "Триптан (Суматриптан, Зомиг)",
    "nsaid": "НПВП (Ибупрофен, Напроксен, Нурофен)",
    "analgesic": "Анальгетик / Спазмолитик",
    "custom": "Другое",
    "none": "Не принимались",
}

import re

EMOJI_PATTERN = re.compile(
    r'[\U00010000-\U0010ffff]'
    r'|[\u2600-\u26FF]'
    r'|[\u2700-\u27BF]'
    r'|[\uFE00-\uFE0F]'
    r'|[\u20D0-\u20FF]'
    r'|[\u2190-\u21FF]'
    , flags=re.UNICODE
)

def clean_text_for_pdf(text: Any) -> str:
    """Removes unsupported emoji codepoints while preserving Latin, Cyrillic, and CJK characters."""
    if text is None:
        return ""
    s = str(text)
    cleaned = EMOJI_PATTERN.sub('', s)
    return re.sub(r'\s+', ' ', cleaned).strip()

# Register TrueType fonts (VLGothic for CJK/Japanese + Cyrillic + Latin, DejaVuSans as fallback)
FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))
VL_GOTHIC_PATH = os.path.join(FONTS_DIR, "VL-Gothic-Regular.ttf")
SYSTEM_VL_GOTHIC = "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf"
REGULAR_FONT_PATH = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
BOLD_FONT_PATH = os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf")

vl_gothic_target = VL_GOTHIC_PATH if os.path.exists(VL_GOTHIC_PATH) else (SYSTEM_VL_GOTHIC if os.path.exists(SYSTEM_VL_GOTHIC) else None)

if vl_gothic_target:
    try:
        pdfmetrics.registerFont(TTFont("VLGothic", vl_gothic_target))
        pdfmetrics.registerFontFamily(
            "VLGothic",
            normal="VLGothic",
            bold="VLGothic",
            italic="VLGothic",
            boldItalic="VLGothic"
        )
    except Exception:
        pass

try:
    if os.path.exists(REGULAR_FONT_PATH):
        pdfmetrics.registerFont(TTFont("DejaVuSans", REGULAR_FONT_PATH))
    if os.path.exists(BOLD_FONT_PATH):
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", BOLD_FONT_PATH))
        pdfmetrics.registerFontFamily(
            "DejaVuSans",
            normal="DejaVuSans",
            bold="DejaVuSans-Bold"
        )
except Exception:
    pass


def _calculate_duration(start_str: str, end_str: Optional[str]) -> str:
    if not end_str:
        return "В процессе"
    try:
        dt_start = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
        diff = dt_end - dt_start
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        return f"{hours}ч {minutes}м"
    except Exception:
        return "-"


def _format_symptoms(symptoms_raw: Any, clean: bool = False) -> str:
    if isinstance(symptoms_raw, str):
        try:
            symptoms_raw = json.loads(symptoms_raw)
        except Exception:
            symptoms_raw = [symptoms_raw]
    if not symptoms_raw or "none" in symptoms_raw:
        return "Нет"
    lookup = ALL_SYMPTOMS_CLEAN if clean else ALL_SYMPTOMS
    return ", ".join(lookup.get(s, clean_text_for_pdf(s) if clean else s) for s in symptoms_raw)


def generate_csv(episodes: List[Dict[str, Any]]) -> bytes:
    """Generates a CSV file with BOM for Microsoft Excel compatibility."""
    output = io.StringIO()
    # Write UTF-8 BOM so Excel opens Cyrillic automatically
    output.write('\ufeff')

    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    headers = [
        "№",
        "Время начала",
        "Время окончания",
        "Длительность",
        "Интенсивность (1-10)",
        "Локализация",
        "Характер боли",
        "Симптомы",
        "Принятые медикаменты",
        "Статус"
    ]
    writer.writerow(headers)

    for i, ep in enumerate(episodes, 1):
        loc = LOCATION_MAP_CLEAN.get(ep.get("location"), clean_text_for_pdf(ep.get("location") or "-"))
        pt = PAIN_TYPE_MAP_CLEAN.get(ep.get("pain_type"), clean_text_for_pdf(ep.get("pain_type") or "-"))
        sym = _format_symptoms(ep.get("symptoms"), clean=True)
        med = MEDICATION_MAP_CLEAN.get(ep.get("medication"), clean_text_for_pdf(ep.get("medication") or "-"))
        dur = _calculate_duration(ep.get("start_time", ""), ep.get("end_time"))
        status_str = "Завершен" if ep.get("status") == "completed" else "Активен"

        writer.writerow([
            i,
            ep.get("start_time", ""),
            ep.get("end_time") or "-",
            dur,
            ep.get("intensity", ""),
            loc,
            pt,
            sym,
            med,
            status_str
        ])

    return output.getvalue().encode('utf-8-sig')


def generate_pdf(episodes: List[Dict[str, Any]], user_title: str = "Пациент") -> bytes:
    """Generates a landscape A4 medical report table in PDF."""
    buffer = io.BytesIO()

    # Document setup: A4 Landscape with 20pt margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    registered = pdfmetrics.getRegisteredFontNames()
    if "VLGothic" in registered:
        font_regular = "VLGothic"
        font_bold = "VLGothic"
    elif "DejaVuSans" in registered:
        font_regular = "DejaVuSans"
        font_bold = "DejaVuSans-Bold" if "DejaVuSans-Bold" in registered else "DejaVuSans"
    else:
        font_regular = "Helvetica"
        font_bold = "Helvetica-Bold"

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4,
    )

    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15,
    )

    th_style = ParagraphStyle(
        "THStyle",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1,  # Center
    )

    td_style = ParagraphStyle(
        "TDStyle",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2D3748"),
    )

    td_center = ParagraphStyle(
        "TDCenter",
        parent=td_style,
        alignment=1,  # Center
    )

    elements = []

    # Title & Metadata (Clean text without emoji glyph drop)
    elements.append(Paragraph("Дневник головных болей (Мигрень)", title_style))
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    total_count = len(episodes)
    avg_intensity = (
        round(sum(e.get("intensity", 0) for e in episodes) / total_count, 1)
        if total_count > 0 else 0
    )

    clean_user_title = clean_text_for_pdf(user_title) or "Пациент"
    meta_text = (
        f"<b>Пациент:</b> {clean_user_title}  |  "
        f"<b>Дата формирования:</b> {now_str}  |  "
        f"<b>Всего записей:</b> {total_count}  |  "
        f"<b>Средняя интенсивность:</b> {avg_intensity}/10"
    )
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 8))

    # Table Header
    headers = [
        Paragraph("<b>№</b>", th_style),
        Paragraph("<b>Начало</b>", th_style),
        Paragraph("<b>Конец</b>", th_style),
        Paragraph("<b>Длит.</b>", th_style),
        Paragraph("<b>Сила</b>", th_style),
        Paragraph("<b>Локализация</b>", th_style),
        Paragraph("<b>Характер</b>", th_style),
        Paragraph("<b>Симптомы</b>", th_style),
        Paragraph("<b>Препарат</b>", th_style),
    ]

    data = [headers]

    for i, ep in enumerate(episodes, 1):
        loc = LOCATION_MAP_CLEAN.get(ep.get("location"), clean_text_for_pdf(ep.get("location") or "-"))
        pt = PAIN_TYPE_MAP_CLEAN.get(ep.get("pain_type"), clean_text_for_pdf(ep.get("pain_type") or "-"))
        sym = _format_symptoms(ep.get("symptoms"), clean=True)
        med = MEDICATION_MAP_CLEAN.get(ep.get("medication"), clean_text_for_pdf(ep.get("medication") or "-"))
        dur = _calculate_duration(ep.get("start_time", ""), ep.get("end_time"))
        intensity = ep.get("intensity", "")

        row = [
            Paragraph(str(i), td_center),
            Paragraph(ep.get("start_time", ""), td_center),
            Paragraph(ep.get("end_time") or "-", td_center),
            Paragraph(dur, td_center),
            Paragraph(f"<b>{intensity}</b>/10", td_center),
            Paragraph(loc, td_style),
            Paragraph(pt, td_style),
            Paragraph(sym, td_style),
            Paragraph(med, td_style),
        ]
        data.append(row)

    # Column widths for Landscape A4 (total usable width ≈ 792pt)
    # Total width = 30 + 90 + 90 + 55 + 45 + 115 + 115 + 140 + 110 = 790pt
    col_widths = [30, 85, 85, 55, 45, 115, 115, 140, 120]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))

    elements.append(table)
    doc.build(elements)

    return buffer.getvalue()
