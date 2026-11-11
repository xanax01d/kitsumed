#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register DejaVu fonts for full Cyrillic and Belarusian support
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/DejaVuSans.ttf",
    os.path.expanduser("~/.fonts/DejaVuSans.ttf"),
]

FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/DejaVuSans-Bold.ttf",
    os.path.expanduser("~/.fonts/DejaVuSans-Bold.ttf"),
]

font_name = "Helvetica"
font_bold = "Helvetica-Bold"

for p in FONT_PATHS:
    if os.path.exists(p):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", p))
            font_name = "DejaVuSans"
            break
        except Exception:
            pass

for p in FONT_BOLD_PATHS:
    if os.path.exists(p):
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", p))
            font_bold = "DejaVuSans-Bold"
            break
        except Exception:
            pass

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont(font_name, 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        
        lang = getattr(self, "lang", "ru")
        if "be" in lang or "by" in lang:
            footer_text = f"KitsuMed — Дзённік галаўнога болю  |  Старонка {self._pageNumber} з {page_count}"
        elif "en" in lang:
            footer_text = f"KitsuMed — Headache Diary  |  Page {self._pageNumber} of {page_count}"
        else:
            footer_text = f"KitsuMed — Дневник головной боли  |  Страница {self._pageNumber} из {page_count}"
        self.drawString(36, 20, footer_text)
        self.drawRightString(A4[0] - 36, 20, "t.me/KitsuMedBot")
        self.restoreState()

def generate_pdf_report(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=36,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A202C")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568")
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2D3748")
    )

    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2D3748")
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName=font_bold,
        fontSize=8,
        leading=10
    )

    cell_header = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#FFFFFF")
    )

    elements = []

    lang = data.get("lang", "ru").lower()
    is_be = "be" in lang or "by" in lang
    is_en = "en" in lang

    user_id = data.get("user_id", "—")
    date_gen = data.get("date_generated", datetime.now().strftime("%d.%m.%Y %H:%M"))

    # Title block
    if is_be:
        title_text = "🦊 KitsuMed — Дзённік галаўнога болю і мігрэні"
        sub_text = f"Справаздача для лекара-неўролага  •  ID пацыента: <code>{user_id}</code>  •  Дата выгрузкі: {date_gen}"
    elif is_en:
        title_text = "🦊 KitsuMed — Headache & Migraine Diary"
        sub_text = f"Clinical Report for Neurologist  •  Patient ID: <code>{user_id}</code>  •  Date: {date_gen}"
    else:
        title_text = "🦊 KitsuMed — Дневник головной боли и мигрени"
        sub_text = f"Отчет для врача-невролога  •  ID пациента: <code>{user_id}</code>  •  Дата выгрузки: {date_gen}"

    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(sub_text, subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=10))

    # Summary Statistics Box
    episodes = data.get("episodes", [])
    total_eps = len(episodes)
    pain_days_set = set()
    total_intensity = 0
    med_days_set = set()

    for ep in episodes:
        raw_start = ep.get("start_time", "")
        if len(raw_start) >= 10:
            pain_days_set.add(raw_start[:10])
        total_intensity += ep.get("intensity", 0)
        med = ep.get("medication", "").lower()
        if med and med != "none" and med != "—" and med != "не принимались" and med != "не прымаліся":
            if len(raw_start) >= 10:
                med_days_set.add(raw_start[:10])

    avg_intensity = (total_intensity / total_eps) if total_eps > 0 else 0
    pain_days = len(pain_days_set)
    med_days = len(med_days_set)

    if is_be:
        moh_badge = "🟢 У межах нормы (<8 дзён)"
        if med_days >= 10:
            moh_badge = "🔴 Высокая рызыка абузуснага болю (≥10 дзён)"
        elif med_days >= 8:
            moh_badge = "🟡 Увага: набліжэнне да рызыкі (8-9 дзён)"

        summary_data = [
            [
                Paragraph("<b>Усяго прыступаў:</b>", cell_style), Paragraph(str(total_eps), cell_bold),
                Paragraph("<b>Дзён з болем:</b>", cell_style), Paragraph(str(pain_days), cell_bold)
            ],
            [
                Paragraph("<b>Сярэдняя інтэнсіўнасць:</b>", cell_style), Paragraph(f"{avg_intensity:.1f} / 10", cell_bold),
                Paragraph("<b>Дзён прыёму лекаў:</b>", cell_style), Paragraph(f"{med_days} дн. ({moh_badge})", cell_bold)
            ]
        ]
        table_title = "📋 Журнал зарэгістраваных прыступаў"
        headers = [
            Paragraph("#", cell_header),
            Paragraph("Дата і час", cell_header),
            Paragraph("Боль", cell_header),
            Paragraph("Лакалізацыя і характар", cell_header),
            Paragraph("Сімптомы і трыгеры", cell_header),
            Paragraph("Прэпарат і эфект", cell_header),
            Paragraph("Статус", cell_header)
        ]
    elif is_en:
        moh_badge = "🟢 Within normal range (<8 days)"
        if med_days >= 10:
            moh_badge = "🔴 High Medication Overuse Risk (≥10 days)"
        elif med_days >= 8:
            moh_badge = "🟡 Caution: approaching threshold (8-9 days)"

        summary_data = [
            [
                Paragraph("<b>Total attacks:</b>", cell_style), Paragraph(str(total_eps), cell_bold),
                Paragraph("<b>Pain days:</b>", cell_style), Paragraph(str(pain_days), cell_bold)
            ],
            [
                Paragraph("<b>Average intensity:</b>", cell_style), Paragraph(f"{avg_intensity:.1f} / 10", cell_bold),
                Paragraph("<b>Medication days:</b>", cell_style), Paragraph(f"{med_days} d. ({moh_badge})", cell_bold)
            ]
        ]
        table_title = "📋 Log of Recorded Episodes"
        headers = [
            Paragraph("#", cell_header),
            Paragraph("Date & Time", cell_header),
            Paragraph("Pain", cell_header),
            Paragraph("Location & Type", cell_header),
            Paragraph("Symptoms & Triggers", cell_header),
            Paragraph("Medication & Relief", cell_header),
            Paragraph("Status", cell_header)
        ]
    else:
        moh_badge = "🟢 В пределах нормы (<8 дней)"
        if med_days >= 10:
            moh_badge = "🔴 Высокий риск абузусной боли (≥10 дней)"
        elif med_days >= 8:
            moh_badge = "🟡 Внимание: приближение к риску (8-9 дней)"

        summary_data = [
            [
                Paragraph("<b>Всего приступов:</b>", cell_style), Paragraph(str(total_eps), cell_bold),
                Paragraph("<b>Дней с болью:</b>", cell_style), Paragraph(str(pain_days), cell_bold)
            ],
            [
                Paragraph("<b>Средняя интенсивность:</b>", cell_style), Paragraph(f"{avg_intensity:.1f} / 10", cell_bold),
                Paragraph("<b>Дней приема лекарств:</b>", cell_style), Paragraph(f"{med_days} дн. ({moh_badge})", cell_bold)
            ]
        ]
        table_title = "📋 Журнал зарегистрированных приступов"
        headers = [
            Paragraph("#", cell_header),
            Paragraph("Дата и время", cell_header),
            Paragraph("Боль", cell_header),
            Paragraph("Локализация и характер", cell_header),
            Paragraph("Симптомы и триггеры", cell_header),
            Paragraph("Препарат и эффект", cell_header),
            Paragraph("Статус", cell_header)
        ]

    summary_table = Table(summary_data, colWidths=[130, 110, 140, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Table of Episodes
    elements.append(Paragraph(table_title, h2_style))
    elements.append(Spacer(1, 6))

    col_widths = [22, 100, 38, 95, 115, 105, 55]
    table_rows = [headers]

    for idx, ep in enumerate(episodes, 1):
        num_p = Paragraph(str(idx), cell_bold)
        
        time_text = ep.get("time_str", ep.get("start_time", ""))
        weather = ep.get("weather", "")
        if weather:
            time_text += f"<br/><font color='#718096' size='7'>{weather}</font>"
        time_p = Paragraph(time_text, cell_style)

        intensity = ep.get("intensity", 0)
        pain_text = f"<b>{intensity}/10</b>"
        if intensity >= 8:
            pain_text = f"<font color='#E53E3E'><b>{intensity}/10</b></font>"
        elif intensity >= 5:
            pain_text = f"<font color='#DD6B20'><b>{intensity}/10</b></font>"
        pain_p = Paragraph(pain_text, cell_style)

        loc = ep.get("location", "—")
        pt = ep.get("pain_type", "—")
        loc_p = Paragraph(f"<b>{loc}</b><br/>{pt}", cell_style)

        sym = ep.get("symptoms", "—")
        trig = ep.get("triggers", "—")
        lbl_sym = "Сімптомы" if is_be else ("Symptoms" if is_en else "Симп")
        lbl_trig = "Трыгеры" if is_be else ("Triggers" if is_en else "Триг")
        st_text = f"<b>{lbl_sym}:</b> {sym}<br/><b>{lbl_trig}:</b> {trig}"
        st_p = Paragraph(st_text, cell_style)

        med = ep.get("medication", "—")
        relief = ep.get("relief", "—")
        med_text = f"<b>{med}</b><br/>{relief}"
        med_p = Paragraph(med_text, cell_style)

        status = ep.get("status", "—")
        s_low = status.lower()
        if "купіраван" in s_low or "купирован" in s_low or "resolved" in s_low or "попустило" in s_low:
            status_html = f"<font color='#2E7D32'><b>{status}</b></font>"
        elif "не прайшоў" in s_low or "не прошла" in s_low or "not resolved" in s_low:
            status_html = f"<font color='#D32F2F'><b>{status}</b></font>"
        else:
            status_html = f"<font color='#C67D00'><b>{status}</b></font>"
        status_p = Paragraph(status_html, cell_style)

        table_rows.append([num_p, time_p, pain_p, loc_p, st_p, med_p, status_p])

    ep_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")), # Deep medical blue header
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    for i in range(1, len(table_rows)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F8FAFC")))

    ep_table.setStyle(TableStyle(t_style))
    elements.append(ep_table)

    class CustomCanvas(NumberedCanvas):
        pass
    CustomCanvas.lang = lang

    doc.build(elements, canvasmaker=CustomCanvas)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_pdf.py <input.json> <output.pdf>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    generate_pdf_report(data, output_file)
    print("SUCCESS")
