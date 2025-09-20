"""
PDF and Excel exporters for attendance reports
Implements export functionality for daily sheet reports
"""

import os
from datetime import datetime, date
from typing import Dict, Any
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from k9.utils.utils_pdf_rtl import rtl, register_arabic_fonts, get_arabic_font_name, format_arabic_date
from k9.utils.attendance_reporting_constants import (
    GROUP_1_HEADERS, GROUP_2_HEADERS, LEAVE_TABLE_HEADERS, REPORT_LABELS
)
from k9.models.models import Project
from k9.utils.report_header import create_pdf_report_header


def ensure_reports_directory() -> str:
    """
    Ensure the reports directory structure exists
    Creates uploads/reports/YYYY/MM/ structure
    
    Returns:
        Path to the current month's directory
    """
    now = datetime.now()
    year_str = now.strftime("%Y")
    month_str = now.strftime("%m")
    
    base_path = os.path.join("uploads", "reports", year_str, month_str)
    os.makedirs(base_path, exist_ok=True)
    
    return base_path


def get_project_code(project_id: str) -> str:
    """
    Get project code from database, fallback to project_id if not found
    
    Args:
        project_id: UUID string of the project
        
    Returns:
        Project code or project_id as fallback
    """
    try:
        project = Project.query.get(project_id)
        return project.code if project and project.code else str(project_id)[:8]
    except Exception:
        return str(project_id)[:8]


def export_daily_attendance_pdf(data: Dict[str, Any]) -> str:
    """
    Export daily attendance data to PDF format
    
    Args:
        data: Dictionary containing the attendance data in the JSON contract format
        
    Returns:
        Relative path to the generated PDF file
    """
    try:
        # Register Arabic fonts
        register_arabic_fonts()
        font_name = get_arabic_font_name()
        
        # Prepare file path
        reports_dir = ensure_reports_directory()
        project_code = get_project_code(data.get("project_id", "unknown"))
        date_str = data.get("date", datetime.now().strftime("%Y%m%d")).replace("-", "")
        filename = f"daily_sheet_{project_code}_{date_str}.pdf"
        file_path = os.path.join(reports_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build story (content)
        story = []
        
        # Create styles
        styles = getSampleStyleSheet()
        
        # Arabic title style
        title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Arabic normal style
        arabic_style = ParagraphStyle(
            'ArabicNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=TA_RIGHT
        )
        
        # Add date and day information for header
        date_string = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        target_date = datetime.strptime(date_string, "%Y-%m-%d").date()
        formatted_date = format_arabic_date(target_date)
        day_name = data.get("day_name_ar", "")
        project_name = data.get("project_name", "جميع المشاريع")
        
        additional_info = f"{REPORT_LABELS['day_label']} {day_name}   {REPORT_LABELS['date_label']} {formatted_date}   المشروع: {project_name}"
        
        # Add standardized header to story
        header_elements = create_pdf_report_header(
            report_title_ar=REPORT_LABELS["main_title"],
            additional_info=additional_info
        )
        story.extend(header_elements)
        
        # Process groups data
        groups = data.get("groups", [])
        group_1_data = []
        group_2_data = []
        
        for group in groups:
            if group.get("group_no") == 1:
                group_1_data = group.get("rows", [])
            elif group.get("group_no") == 2:
                group_2_data = group.get("rows", [])
        
        # Standardize table structure - both groups use same 8-column layout
        # Group 1 Table
        group_1_table_data = [
            [rtl(header) for header in GROUP_1_HEADERS]
        ]
        
        # Add Group 1 rows (RTL column order)
        for row in group_1_data:
            table_row = [
                "",  # Signature box (empty)
                row.get("check_out_time", ""),
                "",  # Signature box (empty)
                row.get("check_in_time", ""),
                rtl(row.get("dog_name", "")),
                rtl(row.get("substitute_name", "")),
                rtl(row.get("employee_name", "")),
                str(row.get("seq_no", ""))
            ]
            group_1_table_data.append(table_row)
        
        # Ensure minimum 10 rows for Group 1
        while len(group_1_table_data) < 11:  # 1 header + 10 data rows
            group_1_table_data.append(["", "", "", "", "", "", "", ""])
        
        # Group 2 Table - using same 8-column structure as Group 1
        group_2_table_data = [
            [rtl(header) for header in GROUP_1_HEADERS]  # Use same headers as Group 1
        ]
        
        # Add Group 2 rows - adapt data to match Group 1 RTL structure
        for row in group_2_data:
            table_row = [
                "",  # Signature box (empty)
                row.get("check_out_time", ""),
                "",  # Signature box (empty)
                row.get("check_in_time", ""),
                rtl(row.get("dog_name", "")),
                "",  # Empty substitute column since Group 2 combines employee/substitute
                rtl(row.get("employee_or_substitute_name", "")),  # Map to employee_name column
                str(row.get("seq_no", ""))
            ]
            group_2_table_data.append(table_row)
        
        # Ensure minimum 8 rows for Group 2
        while len(group_2_table_data) < 9:  # 1 header + 8 data rows
            group_2_table_data.append(["", "", "", "", "", "", "", ""])
        
        # Create Group 1 table (RTL column widths)
        group_1_table = Table(group_1_table_data, colWidths=[
            0.8*inch,  # التوقيع
            1.0*inch,  # وقت الانصراف
            0.8*inch,  # التوقيع
            1.0*inch,  # وقت الحضور
            1.2*inch,  # اسم الكلب
            1.4*inch,  # اسم الموظف البديل
            1.4*inch,  # اسم الموظف
            0.4*inch   # م
        ])
        
        group_1_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue])
        ]))
        
        # Create Group 2 table (same RTL structure as Group 1)
        group_2_table = Table(group_2_table_data, colWidths=[
            0.8*inch,  # التوقيع
            1.0*inch,  # وقت الانصراف
            0.8*inch,  # التوقيع
            1.0*inch,  # وقت الحضور
            1.2*inch,  # اسم الكلب
            1.4*inch,  # اسم الموظف البديل
            1.4*inch,  # اسم الموظف
            0.4*inch   # م
        ])
        
        group_2_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgreen])
        ]))
        
        # Add Group 1 title and table
        group_1_title = Paragraph(rtl("المجموعة الأولى"), arabic_style)
        story.append(group_1_title)
        story.append(Spacer(1, 8))
        story.append(group_1_table)
        story.append(Spacer(1, 15))
        
        # Add Group 2 title and table
        group_2_title = Paragraph(rtl("المجموعة الثانية"), arabic_style)
        story.append(group_2_title)
        story.append(Spacer(1, 8))
        story.append(group_2_table)
        story.append(Spacer(1, 20))
        
        # Add leave table at the bottom
        leave_title = Paragraph(rtl(REPORT_LABELS["leave_section_title"]), arabic_style)
        story.append(leave_title)
        story.append(Spacer(1, 10))
        
        # Leave table
        leave_table_data = [
            [rtl(header) for header in LEAVE_TABLE_HEADERS]
        ]
        
        # Add leave rows (RTL order)
        leaves = data.get("leaves", [])
        for leave in leaves:
            leave_row = [
                rtl(leave.get("note", "")),
                rtl(leave.get("leave_type", "")),
                rtl(leave.get("employee_name", "")),
                str(leave.get("seq_no", ""))
            ]
            leave_table_data.append(leave_row)
        
        # Ensure minimum 3 rows for leaves
        while len(leave_table_data) < 4:  # 1 header + 3 data rows
            leave_table_data.append(["", "", "", ""])
        
        leave_table = Table(leave_table_data, colWidths=[
            2.5*inch,  # ملاحظة
            1.5*inch,  # نوع الإجازة
            2.0*inch,  # اسم الفرد المأجز
            0.5*inch   # #
        ])
        
        leave_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightyellow])
        ]))
        
        story.append(leave_table)
        
        # Build PDF
        doc.build(story)
        
        # Return relative path
        return file_path
        
    except Exception as e:
        print(f"Error exporting daily attendance PDF: {e}")
        raise