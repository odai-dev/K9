"""
Veterinary daily report PDF exporters
"""
import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from k9.utils.utils_pdf_rtl import rtl
from k9.utils.veterinary_daily_constants import PDF_HEADERS
from k9.utils.report_header import create_pdf_report_header


def register_arabic_fonts():
    """Register Arabic fonts for PDF generation"""
    try:
        font_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'static', 'fonts', 'NotoSansArabic-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arabic', font_path))
            return True
    except:
        pass
    return False


def export_vet_daily_pdf(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Export veterinary daily report to PDF
    
    Args:
        data: Report data from daily_services.get_vet_daily()
        
    Returns:
        Dictionary with file path
    """
    # Ensure upload directory exists
    upload_dir = os.path.join('uploads', 'reports', datetime.now().strftime('%Y'), datetime.now().strftime('%m'))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate filename
    date_str = data['date'].replace('-', '')
    project_name = data.get('project_name', 'unknown').replace(' ', '-')
    filename = f"vet_daily_{project_name}_{date_str}.pdf"
    filepath = os.path.join(upload_dir, filename)
    
    # Register Arabic font
    has_arabic_font = register_arabic_fonts()
    font_name = 'Arabic' if has_arabic_font else 'Helvetica'
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40,
                          topMargin=40, bottomMargin=40)
    
    # Build content
    story = []
    
    # Create standardized header
    additional_info = f"اليوم: {data['day_name_ar']}   التاريخ: {data['date_ar']}   المشروع: {data.get('project_name', 'غير محدد')}"
    
    # Add standardized header to story
    header_elements = create_pdf_report_header(
        report_title_ar="التقرير اليومي الصحي",
        additional_info=additional_info
    )
    story.extend(header_elements)
    
    # Keep header style for section headers
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=getSampleStyleSheet()['Normal'],
        fontName=font_name,
        fontSize=12,
        spaceAfter=10,
        alignment=2  # Right alignment
    )
    
    # KPIs Summary
    kpis_style = ParagraphStyle(
        'KPIsStyle',
        parent=getSampleStyleSheet()['Normal'],
        fontName=font_name,
        fontSize=10,
        spaceAfter=15,
        alignment=2
    )
    
    kpis = data['kpis']
    kpis_text = [
        f"إجمالي الزيارات: {kpis['total_visits']}",
        f"عدد الكلاب: {kpis['unique_dogs']}",
        f"التكلفة الإجمالية: {kpis['total_cost']} ر.س",
        f"الحالات الطارئة: {kpis['emergencies']}",
        f"التحصينات: {kpis['vaccinations']}"
    ]
    
    for kpi in kpis_text:
        story.append(Paragraph(rtl(kpi), kpis_style))
    
    story.append(Spacer(1, 20))
    
    # Visits table
    if data['visits']:
        # Prepare table data - headers first, then visits
        table_data = [PDF_HEADERS]  # Headers are already in RTL order
        
        for visit in data['visits']:
            row = [
                visit['time'],
                visit['dog_name'],
                visit['breed'],
                visit['vet_name'],
                visit['visit_type_ar'],
                visit['diagnosis'][:50] + '...' if len(visit['diagnosis']) > 50 else visit['diagnosis'],
                visit['treatment'][:50] + '...' if len(visit['treatment']) > 50 else visit['treatment'],
                visit['medications'][:40] + '...' if len(visit['medications']) > 40 else visit['medications'],
                f"{visit['cost']:.2f}" if visit['cost'] else '',
                visit['location'],
                visit['weather'],
                visit['vital_signs'][:30] + '...' if len(visit['vital_signs']) > 30 else visit['vital_signs'],
                visit['notes'][:40] + '...' if len(visit['notes']) > 40 else visit['notes']
            ]
            table_data.append(row)
        
        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(table)
    else:
        # No visits message
        no_data_style = ParagraphStyle(
            'NoDataStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=14,
            alignment=1,  # Center alignment
            spaceAfter=20
        )
        story.append(Paragraph(rtl("لا توجد زيارات بيطرية في هذا التاريخ"), no_data_style))
    
    # Build PDF
    doc.build(story)
    
    return {"path": filepath, "filename": filename}