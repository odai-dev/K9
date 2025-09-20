"""
PM Daily Report PDF Exporter
Generates Arabic RTL PDF reports exactly matching the DOCX form structure
"""

import os
from datetime import date
from typing import Dict, Any, List
from uuid import UUID

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from k9.utils.utils_pdf_rtl import register_arabic_fonts, rtl, get_arabic_font_name
from k9.utils.dates_ar import format_arabic_date
from k9.services.pm_daily_services import get_pm_daily
from k9.utils.report_header import create_pdf_report_header


def export_pm_daily_pdf(project_id: str, date_str: str, user, project_code: str | None = None) -> Dict[str, str]:
    """
    Export PM Daily Report to PDF
    
    Args:
        project_id: Project UUID string
        date_str: Date string in YYYY-MM-DD format  
        user: Current user object
        project_code: Optional project code for filename
        
    Returns:
        Dictionary with PDF file path
        
    Raises:
        Exception: If data retrieval or PDF generation fails
    """
    # Get report data
    data = get_pm_daily(project_id, date_str, user)
    
    # Generate filename
    report_date = date.fromisoformat(date_str)
    year = report_date.strftime('%Y')
    month = report_date.strftime('%m')
    date_code = report_date.strftime('%Y%m%d')
    
    if not project_code:
        project_code = project_id[:8]  # Use first 8 chars of UUID as fallback
    
    filename = f"pm_daily_{project_code}_{date_code}.pdf"
    
    # Ensure directory exists
    save_dir = os.path.join('uploads', 'reports', year, month)
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, filename)
    
    # Generate PDF
    _generate_pdf(data, file_path)
    
    return {"path": file_path}


def _generate_pdf(data: Dict[str, Any], file_path: str):
    """
    Generate the actual PDF document
    
    Args:
        data: PM daily report data
        file_path: Output PDF file path
    """
    # Register Arabic fonts
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    # Create document with landscape A4 for wide tables stacked vertically
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    # Build document content
    story = []
    
    # Add header
    story.extend(_build_header(data, font_name))
    
    # Add main content table
    story.extend(_build_main_table(data, font_name))
    
    # Add special bottom rows
    story.extend(_build_special_rows(data, font_name))
    
    # Build PDF
    doc.build(story)


def _build_header(data: Dict[str, Any], font_name: str) -> List[Any]:
    """Build standardized PDF header with company logo and information"""
    # Date formatting
    report_date = date.fromisoformat(data['date'])
    formatted_date = format_arabic_date(report_date)
    day_name = data['day_name_ar']
    project_name = data.get('project_name', 'غير محدد')
    
    # Create additional info
    additional_info = f"اليوم: {day_name}   التاريخ: {formatted_date}   المشروع: {project_name}"
    
    # Create standardized header
    return create_pdf_report_header(
        report_title_ar="التقرير اليومي لرئيس الميدان",
        additional_info=additional_info
    )


def _build_main_table(data: Dict[str, Any], font_name: str) -> List[Any]:
    """Build separate tables for each group stacked vertically"""
    story = []
    
    # Arabic column headers (reversed order)
    headers = [
        "المخالفات",
        "تقييم الأداء: المدرب", "الصحي", "المربي", "الكلب", "السائس",
        "نزول ميداني",
        "التدريب: أخرى", "التدريب: تنشيطي",
        "سقاية الكلب", "تغذية الكلب", "فحص الكلب",
        "النظافة", "المظهر", "البطاقة", "الزي",
        "الفترة", "موقع الدوام", "اسم الكلب", "اسم الموظف"
    ]
    
    # Process RTL headers
    rtl_headers = [rtl(header) for header in headers]
    
    # Process groups data
    groups = data.get('groups', [])
    
    # Create a separate table for each group
    for group in sorted(groups, key=lambda g: g.get('group_no', 0)):
        group_no = group.get('group_no', 0)
        
        # Add group title/header
        styles = getSampleStyleSheet()
        group_title_style = styles['Normal'].clone('GroupTitleStyle')
        group_title_style.fontName = font_name
        group_title_style.fontSize = 12
        group_title_style.alignment = TA_CENTER
        
        group_title = rtl(f"المجموعة {group_no}")
        group_title_para = Paragraph(group_title, group_title_style)
        story.append(group_title_para)
        story.append(Spacer(1, 5*mm))
        
        # Build table data for this group
        table_data = []
        
        # Add headers row
        table_data.append(rtl_headers)
        
        # Add data rows for this group
        for row in group.get('rows', []):
            row_data = _build_row_data(row)
            table_data.append(row_data)
        
        # Add empty rows if group has no data
        if not group.get('rows'):
            empty_row = [''] * len(headers)
            table_data.append(empty_row)
        
        # Create table for this group
        if table_data:
            # Compact column widths for better screen fit
            col_widths = [
                25*mm,  # المخالفات
                14*mm,  # تقييم الأداء: المدرب
                12*mm,  # الصحي
                14*mm,  # المربي
                12*mm,  # الكلب
                16*mm,  # السائس (kept relatively bigger)
                12*mm,  # نزول ميداني
                12*mm,  # التدريب: أخرى
                12*mm,  # التدريب: تنشيطي
                12*mm,  # سقاية الكلب
                12*mm,  # تغذية الكلب
                12*mm,  # فحص الكلب
                10*mm,  # النظافة
                10*mm,  # المظهر
                10*mm,  # البطاقة
                10*mm,  # الزي
                16*mm,  # الفترة
                20*mm,  # موقع الدوام
                24*mm,  # اسم الكلب
                28*mm,  # اسم الموظف
            ]
            
            table = Table(table_data, colWidths=col_widths)
            
            # Table styling with optimized font sizes
            table_style = [
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 6),   # Header font - reduced for compact view
                ('FONTSIZE', (0, 1), (-1, -1), 5), # Data font - reduced for compact view
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),  # Enable text wrapping
            ]
            
            table.setStyle(TableStyle(table_style))
            story.append(table)
            
            # Add space between groups
            story.append(Spacer(1, 10*mm))
    
    return story


def _build_row_data(row: Dict[str, Any]) -> List[str]:
    """
    Build table row data from row dictionary
    
    Args:
        row: Row data dictionary
        
    Returns:
        List of cell values for the table
    """
    # Handle special rows (reversed order)
    if row.get('is_on_leave_row'):
        employee_name = rtl(row.get('on_leave_employee_name') or 'اسم الفرد المأجز')
        dog_name = rtl(row.get('on_leave_dog_name') or 'اسم الكلب')
        leave_type = rtl(row.get('on_leave_type') or '')
        note = rtl(row.get('on_leave_note') or '')
        # Reversed: note, leave_type, dog_name, employee_name + 16 empty
        return [note, leave_type] + [''] * 14 + [dog_name, employee_name]
    
    if row.get('is_replacement_row'):
        employee_name = rtl(row.get('replacement_employee_name') or 'اسم الفرد البديل')
        dog_name = rtl(row.get('replacement_dog_name') or 'اسم الكلب البديل')
        # Reversed: 18 empty + dog_name, employee_name
        return [''] * 18 + [dog_name, employee_name]
    
    # Normal row data (reversed order to match headers)
    return [
        rtl(row.get('violations', '')),
        
        # Performance evaluations (reversed)
        rtl(row.get('perf_mudarrib', '')),
        rtl(row.get('perf_sehi', '')),
        rtl(row.get('perf_murabbi', '')),
        rtl(row.get('perf_dog', '')),
        rtl(row.get('perf_sais', '')),
        
        '■' if row.get('field_deployment_done') else '□',
        
        '■' if row.get('training_other') else '□',
        '■' if row.get('training_tansheti') else '□',
        
        '■' if row.get('dog_watered') else '□',
        '■' if row.get('dog_fed') else '□',
        '■' if row.get('dog_exam_done') else '□',
        
        # Checkboxes: ■ for True, □ for False (reversed)
        '■' if row.get('cleanliness_ok') else '□',
        '■' if row.get('appearance_ok') else '□',
        '■' if row.get('card_ok') else '□',
        '■' if row.get('uniform_ok') else '□',
        
        rtl(row.get('shift_name', '')),
        rtl(row.get('site_name', '')),
        rtl(row.get('dog_name', '')),
        rtl(row.get('employee_name', ''))
    ]


def _build_special_rows(data: Dict[str, Any], font_name: str) -> List[Any]:
    """Build special bottom rows for on-leave and replacement employees"""
    story = []
    
    # Add some space
    story.append(Spacer(1, 10*mm))
    
    # Find special rows from the data
    groups = data.get('groups', [])
    special_rows = []
    
    for group in groups:
        for row in group.get('rows', []):
            if row.get('is_on_leave_row') or row.get('is_replacement_row'):
                special_rows.append(row)
    
    if special_rows:
        # Build special rows table
        special_table_data = []
        
        # Headers for special rows
        special_headers = [
            "النوع", "اسم الموظف", "اسم الكلب", "نوع الإجازة", "ملاحظة"
        ]
        rtl_special_headers = [rtl(header) for header in special_headers]
        special_table_data.append(rtl_special_headers)
        
        # Add special row data
        for row in special_rows:
            if row.get('is_on_leave_row'):
                special_row = [
                    rtl("الفرد المأجز"),
                    rtl(row.get('on_leave_employee_name', '')),
                    rtl(row.get('on_leave_dog_name', '')),
                    rtl(row.get('on_leave_type', '')),
                    rtl(row.get('on_leave_note', ''))
                ]
            elif row.get('is_replacement_row'):
                special_row = [
                    rtl("الفرد البديل"),
                    rtl(row.get('replacement_employee_name', '')),
                    rtl(row.get('replacement_dog_name', '')),
                    '',
                    ''
                ]
            else:
                continue
                
            special_table_data.append(special_row)
        
        # Create special table
        special_table = Table(special_table_data)
        
        special_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
        
        special_table.setStyle(TableStyle(special_style))
        story.append(special_table)
    
    return story