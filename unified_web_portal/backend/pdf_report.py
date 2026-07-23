import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_attendance_pdf(report_title: str, summary_data: list, statistics: dict) -> io.BytesIO:
    """
    Generates a high-quality printable PDF summary using ReportLab.
    
    summary_data is a list of dicts: [
        {"label": "CSE-3A", "total_students": 5, "present_percentage": "80.0%"},
        ...
    ]
    statistics is a dict: {
        "overall_attendance": "78.5%",
        "total_classes": 14,
        "total_logs": 28
    }
    """
    buffer = io.BytesIO()
    
    # 0.5 inch margins to ensure it fits on a single page
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY_COLOR = colors.HexColor("#0f172a")  # Slate 900
    SECONDARY_COLOR = colors.HexColor("#3b82f6")  # Blue 500
    TEXT_COLOR = colors.HexColor("#334155")  # Slate 700
    LIGHT_BG = colors.HexColor("#f8fafc")  # Slate 50
    BORDER_COLOR = colors.HexColor("#e2e8f0")  # Slate 200
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=SECONDARY_COLOR,
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=10,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    # 1. Header Section
    story.append(Paragraph("PROXIMITY ATTENDANCE AUTOMATION", title_style))
    story.append(Paragraph(f"Campus Report: {report_title} | Generated on: {date_str()}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 2. Key Performance Indicators (KPI) Box
    kpi_data = [
        [
            Paragraph("<b>Overall Campus Attendance</b>", body_style),
            Paragraph("<b>Total Active Schedules</b>", body_style),
            Paragraph("<b>Total Attendance Logs</b>", body_style)
        ],
        [
            Paragraph(f"<font size=18 color='#3b82f6'><b>{statistics.get('overall_attendance', 'N/A')}</b></font>", body_style),
            Paragraph(f"<font size=18 color='#0f172a'><b>{statistics.get('total_classes', 0)}</b></font>", body_style),
            Paragraph(f"<font size=18 color='#0f172a'><b>{statistics.get('total_logs', 0)}</b></font>", body_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ]))
    
    story.append(Paragraph("System Summary Key Metrics", header_style))
    story.append(kpi_table)
    story.append(Spacer(1, 15))
    
    # 3. Detailed Data Table
    story.append(Paragraph("Breakdown Performance Analytics", header_style))
    
    table_content = [
        [
            Paragraph("Entity / Section", table_header_style), 
            Paragraph("Total Enrolled Students", table_header_style), 
            Paragraph("Attendance Ratio", table_header_style)
        ]
    ]
    
    for row in summary_data:
        table_content.append([
            Paragraph(str(row.get("label")), body_style),
            Paragraph(str(row.get("total_students")), body_style),
            Paragraph(f"<b>{row.get('present_percentage')}</b>", body_style),
        ])
        
    data_table = Table(table_content, colWidths=[3.2*inch, 2.1*inch, 2.2*inch])
    
    # Alternating row background styles
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
    ]
    for r in range(1, len(table_content)):
        bg_col = colors.white if r % 2 != 0 else LIGHT_BG
        t_style.append(('BACKGROUND', (0, r), (-1, r), bg_col))
        
    data_table.setStyle(TableStyle(t_style))
    story.append(data_table)
    
    # 4. Footer Note
    story.append(Spacer(1, 20))
    story.append(Paragraph("<font color='#64748b'><i>Note: This is an auto-generated official report. Secure verification logs are archived in PostgreSQL.</i></font>", body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def date_str() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%d %B %Y %H:%M UTC")
