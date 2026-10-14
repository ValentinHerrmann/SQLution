import io
import re
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _cell_font_size(column_count):
    """Shrink the font for wide tables so they still fit on portrait A4."""
    if column_count <= 5:
        return 9
    if column_count <= 8:
        return 8
    if column_count <= 12:
        return 7
    return 6


def build_result_pdf(title, columns, rows):
    """Render a query result as an A4 PDF document and return its bytes."""
    buffer = io.BytesIO()
    margin = 15 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=title,
    )

    styles = getSampleStyleSheet()
    font_size = _cell_font_size(len(columns))
    cell_style = ParagraphStyle('cell', parent=styles['Normal'], fontSize=font_size, leading=font_size * 1.2)
    header_style = ParagraphStyle('header', parent=cell_style, fontName='Helvetica-Bold')

    def para(value, style):
        text = '' if value is None else str(value)
        return Paragraph(escape(text).replace('\n', '<br/>'), style)

    data = [[para(col, header_style) for col in columns]]
    data += [[para(cell, cell_style) for cell in row] for row in rows]

    col_width = doc.width / max(len(columns), 1)
    table = Table(data, colWidths=[col_width] * len(columns), repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))

    info = f"{len(rows)} Zeilen · exportiert am {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story = [
        Paragraph(escape(title), styles['Title']),
        table,
        Spacer(1, 4 * mm),
        Paragraph(escape(info), styles['Italic']),
    ]
    doc.build(story)
    return buffer.getvalue()


def pdf_filename(title):
    """Build a safe download filename for a query title."""
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', title).strip('_') or 'abfrage'
    return f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
