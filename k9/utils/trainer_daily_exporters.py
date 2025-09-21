"""
PDF exporter for trainer daily reports with Arabic RTL support
"""

import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from k9.utils.utils_pdf_rtl import register_arabic_fonts, rtl, get_arabic_font_name
from k9.utils.trainer_daily_constants import TRAINER_DAILY_HEADERS, SUMMARY_HEADERS
from k9.utils.report_header import create_pdf_report_header


def export_trainer_daily_pdf(report_data: Dict[str, Any]) -> str:
    """
    Export trainer daily report to PDF with Arabic RTL support
    
    Args:
        report_data: Report data from trainer_daily_services
        
    Returns:
        Relative path to generated PDF file
    """
    # Register Arabic fonts
    register_arabic_fonts()
    arabic_font = get_arabic_font_name()
    
    # Create output directory
    year = datetime.now().year
    month = datetime.now().month
    output_dir = f"uploads/reports/{year}/{month:02d}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    date_str = report_data['date'].replace('-', '')
    project_code = report_data.get('project_id', 'ALL')[:8] if report_data.get('project_id') else 'ALL'
    filename = f"trainer_daily_{project_code}_{date_str}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Story elements
    story = []
    
    # Styles needed for table sections
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'ArabicHeader',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=12,
        alignment=TA_RIGHT,
        spaceAfter=10
    )
    
    # Create standardized header
    formatted_date = datetime.strptime(report_data['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    day_name = report_data['day_name_ar']
    project_name = report_data.get('project_name', 'جميع المشاريع')
    
    additional_info = f"اليوم: {day_name}   التاريخ: {formatted_date}   المشروع: {project_name}"
    
    # Add standardized header to story
    header_elements = create_pdf_report_header(
        report_title_ar="تقرير يومي للمدرب",
        additional_info=additional_info
    )
    story.extend(header_elements)
    
    # Sessions table
    if report_data['sessions']:
        story.append(Paragraph(rtl("جدول جلسات التدريب"), header_style))
        
        # Prepare sessions table data - RTL column order (reversed)
        sessions_headers = [rtl(header) for header in reversed(TRAINER_DAILY_HEADERS)]
        sessions_data = [sessions_headers]
        
        for session in report_data['sessions']:
            row = [
                rtl(session['notes']),
                rtl(session['equipment']),
                rtl(session['weather']),
                rtl(session['location']),
                str(session['success_rating']),
                str(session['duration_min']),
                rtl(session['subject']),
                rtl(session['category_ar']),
                rtl(session['dog_name']),
                rtl(session['trainer_name']),
                session['time']
            ]
            sessions_data.append(row)
        
        # Create sessions table
        sessions_table = Table(sessions_data, repeatRows=1)
        sessions_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(sessions_table)
        story.append(Spacer(1, 30))
    
    # Summary by dog table
    if report_data['summary_by_dog']:
        story.append(Paragraph(rtl("ملخص حسب الكلب"), header_style))
        
        # Prepare summary table data - RTL column order (reversed)
        summary_headers = [rtl(header) for header in reversed(SUMMARY_HEADERS)]
        summary_data = [summary_headers]
        
        for summary in report_data['summary_by_dog']:
            # Format categories breakdown
            categories_text = ", ".join([
                f"{cat}: {count}" for cat, count in summary['categories_breakdown'].items() if count > 0
            ])
            
            row = [
                rtl(categories_text),
                f"{summary['avg_success_rating']:.1f}",
                str(summary['total_duration_min']),
                str(summary['sessions_count']),
                rtl(summary['dog_name'])
            ]
            summary_data.append(row)
        
        # Create summary table
        summary_table = Table(summary_data, repeatRows=1)
        summary_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    
    # Return relative path
    return filepath