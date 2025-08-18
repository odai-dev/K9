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

from utils_pdf_rtl import register_arabic_fonts, rtl, get_arabic_font_name
from dates_ar import format_arabic_date
from pm_daily_services import get_pm_daily


def export_pm_daily_pdf(project_id: str, date_str: str, user, project_code: str = None) -> Dict[str, str]:
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
    
    # Create document with landscape A4 to fit side-by-side blocks
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
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
    """Build PDF header with date and day information"""
    story = []
    
    # Header style
    styles = getSampleStyleSheet()
    header_style = styles['Normal'].clone('HeaderStyle')
    header_style.fontName = font_name
    header_style.fontSize = 14
    header_style.alignment = TA_CENTER
    
    # Date formatting
    report_date = date.fromisoformat(data['date'])
    formatted_date = format_arabic_date(report_date)
    day_name = data['day_name_ar']
    
    # Header text
    header_text = rtl(f"اليوم: {day_name} - التاريخ: {formatted_date}")
    header_para = Paragraph(header_text, header_style)
    
    story.append(header_para)
    story.append(Spacer(1, 10*mm))
    
    return story


def _build_main_table(data: Dict[str, Any], font_name: str) -> List[Any]:
    """Build the main side-by-side groups table"""
    story = []
    
    # Arabic column headers
    headers = [
        "اسم الموظف", "اسم الكلب", "موقع الدوام", "الفترة",
        "الزي", "البطاقة", "المظهر", "النظافة",
        "فحص الكلب", "تغذية الكلب", "سقاية الكلب",
        "التدريب: تنشيطي", "التدريب: أخرى",
        "نزول ميداني",
        "تقييم الأداء: السائس", "الكلب", "المربي", "الصحي", "المدرب",
        "المخالفات"
    ]
    
    # Process RTL headers
    rtl_headers = [rtl(header) for header in headers]
    
    # Build table data
    table_data = []
    
    # Add headers row
    table_data.append(rtl_headers)
    
    # Process groups data
    groups = data.get('groups', [])
    
    # Find max rows needed
    max_rows = 0
    if groups:
        max_rows = max(len(group.get('rows', [])) for group in groups)
    
    # Build rows for both groups side by side
    for row_idx in range(max_rows):
        left_row_data = []
        right_row_data = []
        
        # Group 1 (left side)
        group_1 = next((g for g in groups if g['group_no'] == 1), None)
        if group_1 and row_idx < len(group_1.get('rows', [])):
            left_row_data = _build_row_data(group_1['rows'][row_idx])
        else:
            left_row_data = [''] * len(headers)
        
        # Group 2 (right side)
        group_2 = next((g for g in groups if g['group_no'] == 2), None)
        if group_2 and row_idx < len(group_2.get('rows', [])):
            right_row_data = _build_row_data(group_2['rows'][row_idx])
        else:
            right_row_data = [''] * len(headers)
        
        # Combine left and right (RTL: right group first, then left group)
        combined_row = right_row_data + left_row_data
        table_data.append(combined_row)
    
    # Create table with double width for side-by-side groups
    if table_data:
        table = Table(table_data)
        
        # Table styling
        table_style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Group separation (vertical line between groups)
            ('LINEAFTER', (len(headers)-1, 0), (len(headers)-1, -1), 2, colors.black),
        ]
        
        table.setStyle(TableStyle(table_style))
        story.append(table)
    
    return story


def _build_row_data(row: Dict[str, Any]) -> List[str]:
    """
    Build table row data from row dictionary
    
    Args:
        row: Row data dictionary
        
    Returns:
        List of cell values for the table
    """
    # Handle special rows
    if row.get('is_on_leave_row'):
        employee_name = rtl(row.get('on_leave_employee_name') or 'اسم الفرد المأجز')
        dog_name = rtl(row.get('on_leave_dog_name') or 'اسم الكلب')
        leave_type = rtl(row.get('on_leave_type') or '')
        note = rtl(row.get('on_leave_note') or '')
        return [employee_name, dog_name, leave_type, note] + [''] * 16
    
    if row.get('is_replacement_row'):
        employee_name = rtl(row.get('replacement_employee_name') or 'اسم الفرد البديل')
        dog_name = rtl(row.get('replacement_dog_name') or 'اسم الكلب البديل')
        return [employee_name, dog_name] + [''] * 18
    
    # Normal row data
    return [
        rtl(row.get('employee_name', '')),
        rtl(row.get('dog_name', '')),
        rtl(row.get('site_name', '')),
        rtl(row.get('shift_name', '')),
        
        # Checkboxes: ■ for True, □ for False
        '■' if row.get('uniform_ok') else '□',
        '■' if row.get('card_ok') else '□',
        '■' if row.get('appearance_ok') else '□',
        '■' if row.get('cleanliness_ok') else '□',
        
        '■' if row.get('dog_exam_done') else '□',
        '■' if row.get('dog_fed') else '□',
        '■' if row.get('dog_watered') else '□',
        
        '■' if row.get('training_tansheti') else '□',
        '■' if row.get('training_other') else '□',
        
        '■' if row.get('field_deployment_done') else '□',
        
        # Performance evaluations
        rtl(row.get('perf_sais', '')),
        rtl(row.get('perf_dog', '')),
        rtl(row.get('perf_murabbi', '')),
        rtl(row.get('perf_sehi', '')),
        rtl(row.get('perf_mudarrib', '')),
        
        rtl(row.get('violations', ''))
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