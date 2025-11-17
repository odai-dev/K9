"""
Minimal Elegant PDF Template for K9 Operations Management System
Provides consistent, clean, and professional PDF design across all reports
"""

import os
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    Table, TableStyle, Paragraph, Spacer, Image,
    PageBreak, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from k9.utils.utils_pdf_rtl import rtl, register_arabic_fonts, get_arabic_font_name

logger = logging.getLogger(__name__)

# ==================== COLOR SCHEME ====================
# Minimal Elegant Color Palette
class MinimalColors:
    """Minimal Elegant color scheme - clean and professional"""
    
    # Primary colors
    DARK_GRAY = colors.HexColor('#333333')      # Main text
    CALM_BLUE = colors.HexColor('#3A6EA5')      # Headings and accents
    LIGHT_GRAY = colors.HexColor('#DDDDDD')     # Borders and dividers
    VERY_LIGHT_GRAY = colors.HexColor('#F5F5F5') # Table headers background
    PALE_GRAY = colors.HexColor('#EEEEEE')      # Section backgrounds (subtle)
    
    # Text colors
    TEXT_PRIMARY = DARK_GRAY
    TEXT_SECONDARY = colors.HexColor('#666666')
    TEXT_LIGHT = colors.HexColor('#999999')
    
    # Background
    WHITE = colors.white
    
    # Status colors (subtle versions)
    SUCCESS = colors.HexColor('#10B981')        # Green
    WARNING = colors.HexColor('#F59E0B')        # Orange
    DANGER = colors.HexColor('#EF4444')         # Red
    INFO = colors.HexColor('#3B82F6')           # Blue


# ==================== STYLES ====================
def get_minimal_styles():
    """
    Get consistent Minimal Elegant styles for all reports
    
    Returns:
        Dictionary of ParagraphStyle objects
    """
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    styles = {
        # Report title - 18px bold, calm blue
        'ReportTitle': ParagraphStyle(
            'ReportTitle',
            fontName=font_name,
            fontSize=18,
            textColor=MinimalColors.CALM_BLUE,
            alignment=TA_RIGHT,
            spaceAfter=6,
            spaceBefore=0,
            leading=22
        ),
        
        # Report subtitle - 14px, dark gray
        'ReportSubtitle': ParagraphStyle(
            'ReportSubtitle',
            fontName=font_name,
            fontSize=14,
            textColor=MinimalColors.DARK_GRAY,
            alignment=TA_RIGHT,
            spaceAfter=12,
            leading=18
        ),
        
        # Section heading - 16px bold, calm blue
        'SectionHeading': ParagraphStyle(
            'SectionHeading',
            fontName=font_name,
            fontSize=16,
            textColor=MinimalColors.CALM_BLUE,
            alignment=TA_RIGHT,
            spaceAfter=8,
            spaceBefore=12,
            leading=20
        ),
        
        # Subsection heading - 13px bold, dark gray
        'SubsectionHeading': ParagraphStyle(
            'SubsectionHeading',
            fontName=font_name,
            fontSize=13,
            textColor=MinimalColors.DARK_GRAY,
            alignment=TA_RIGHT,
            spaceAfter=6,
            spaceBefore=8,
            leading=16
        ),
        
        # Normal text - 11px, dark gray
        'Normal': ParagraphStyle(
            'Normal',
            fontName=font_name,
            fontSize=11,
            textColor=MinimalColors.TEXT_PRIMARY,
            alignment=TA_RIGHT,
            spaceAfter=4,
            leading=14,
            rightIndent=0,
            leftIndent=0
        ),
        
        # Small text - 10px, gray
        'Small': ParagraphStyle(
            'Small',
            fontName=font_name,
            fontSize=10,
            textColor=MinimalColors.TEXT_SECONDARY,
            alignment=TA_RIGHT,
            spaceAfter=3,
            leading=12
        ),
        
        # Footer text - 9px, light gray
        'Footer': ParagraphStyle(
            'Footer',
            fontName=font_name,
            fontSize=9,
            textColor=MinimalColors.TEXT_LIGHT,
            alignment=TA_CENTER,
            leading=11
        ),
        
        # Label (for field names) - 11px, medium gray
        'Label': ParagraphStyle(
            'Label',
            fontName=font_name,
            fontSize=11,
            textColor=MinimalColors.TEXT_SECONDARY,
            alignment=TA_RIGHT,
            spaceAfter=2,
            leading=14
        ),
        
        # Value (for field values) - 11px, dark gray, slightly bold
        'Value': ParagraphStyle(
            'Value',
            fontName=font_name,
            fontSize=11,
            textColor=MinimalColors.TEXT_PRIMARY,
            alignment=TA_RIGHT,
            spaceAfter=4,
            leading=14
        ),
    }
    
    return styles


# ==================== HEADER ====================
def create_minimal_header(report_title, metadata=None, logo_path=None):
    """
    Create minimal elegant header for PDF reports
    
    Args:
        report_title: Main title of the report (Arabic)
        metadata: Dict with optional fields:
            - subtitle: Report subtitle
            - date: Report date
            - project: Project name
            - location: Location name
            - handler: Handler name
            - period: Time period
        logo_path: Optional path to logo image
        
    Returns:
        List of ReportLab elements
    """
    styles = get_minimal_styles()
    elements = []
    
    # Logo and title row
    if logo_path and os.path.exists(logo_path):
        # Create table with logo and title
        logo_img = Image(logo_path, width=2*cm, height=2*cm)
        title_para = Paragraph(rtl(report_title), styles['ReportTitle'])
        
        header_data = [[title_para, logo_img]]
        header_table = Table(header_data, colWidths=[15*cm, 2.5*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
    else:
        # Title only
        elements.append(Paragraph(rtl(report_title), styles['ReportTitle']))
    
    # Subtitle if provided
    if metadata and metadata.get('subtitle'):
        elements.append(Paragraph(rtl(metadata['subtitle']), styles['ReportSubtitle']))
    
    # Metadata section (date, project, etc.)
    if metadata:
        meta_data = []
        
        # Build metadata rows (2 columns per row)
        row = []
        fields = []
        
        if metadata.get('date'):
            fields.append(('التاريخ', metadata['date']))
        if metadata.get('project'):
            fields.append(('المشروع', metadata['project']))
        if metadata.get('location'):
            fields.append(('الموقع', metadata['location']))
        if metadata.get('handler'):
            fields.append(('السائس', metadata['handler']))
        if metadata.get('period'):
            fields.append(('الفترة', metadata['period']))
        
        # Create 2-column layout for metadata
        for i, (label, value) in enumerate(fields):
            cell_content = Paragraph(
                rtl(f"<b>{label}:</b> {value}"),
                styles['Small']
            )
            row.append(cell_content)
            
            if len(row) == 2 or i == len(fields) - 1:
                # Pad row if needed
                while len(row) < 2:
                    row.append('')
                meta_data.append(row)
                row = []
        
        if meta_data:
            meta_table = Table(meta_data, colWidths=[8.5*cm, 8.5*cm])
            meta_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(Spacer(1, 4))
            elements.append(meta_table)
    
    # Thin divider line below header
    divider_data = [['']]
    divider_table = Table(divider_data, colWidths=[17*cm])
    divider_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, MinimalColors.LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(divider_table)
    elements.append(Spacer(1, 12))
    
    return elements


# ==================== SECTIONS ====================
def create_info_section(title, data_dict):
    """
    Create a clean information section with key-value pairs
    
    Args:
        title: Section title (Arabic)
        data_dict: Dictionary of {label: value} pairs
        
    Returns:
        List of ReportLab elements
    """
    styles = get_minimal_styles()
    elements = []
    
    # Section title
    elements.append(Paragraph(rtl(title), styles['SectionHeading']))
    
    # Data rows
    data = []
    for label, value in data_dict.items():
        if value is not None and value != '':
            cell = Paragraph(
                rtl(f"<b>{label}:</b> {value}"),
                styles['Normal']
            )
            data.append([cell])
    
    if data:
        info_table = Table(data, colWidths=[17*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), MinimalColors.WHITE),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 8))
    
    return elements


def create_text_section(title, text_content):
    """
    Create a section with title and text content
    
    Args:
        title: Section title (Arabic)
        text_content: Text content (Arabic)
        
    Returns:
        List of ReportLab elements
    """
    styles = get_minimal_styles()
    elements = []
    
    # Section title
    elements.append(Paragraph(rtl(title), styles['SectionHeading']))
    
    # Text content in a subtle box
    if text_content:
        content_para = Paragraph(rtl(text_content), styles['Normal'])
        content_table = Table([[content_para]], colWidths=[17*cm])
        content_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 0.5, MinimalColors.PALE_GRAY),
            ('BACKGROUND', (0, 0), (-1, -1), MinimalColors.WHITE),
        ]))
        elements.append(content_table)
        elements.append(Spacer(1, 8))
    
    return elements


# ==================== TABLES ====================
def get_minimal_table_style():
    """
    Get consistent table style for data tables
    
    Returns:
        TableStyle object
    """
    return TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), MinimalColors.VERY_LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), MinimalColors.DARK_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Borders - very light
        ('GRID', (0, 0), (-1, -1), 0.5, MinimalColors.LIGHT_GRAY),
        ('LINEBELOW', (0, 0), (-1, 0), 1, MinimalColors.LIGHT_GRAY),
        
        # Body rows
        ('BACKGROUND', (0, 1), (-1, -1), MinimalColors.WHITE),
        ('TEXTCOLOR', (0, 1), (-1, -1), MinimalColors.TEXT_PRIMARY),
    ])


def create_data_table(headers, rows, col_widths=None):
    """
    Create a clean data table
    
    Args:
        headers: List of header labels (Arabic)
        rows: List of row data (list of lists)
        col_widths: Optional list of column widths
        
    Returns:
        Table object
    """
    styles = get_minimal_styles()
    
    # Format headers
    header_cells = [Paragraph(rtl(h), styles['SubsectionHeading']) for h in headers]
    
    # Format data rows
    data = [header_cells]
    for row in rows:
        row_cells = []
        for cell in row:
            if isinstance(cell, str):
                row_cells.append(Paragraph(rtl(cell), styles['Small']))
            else:
                row_cells.append(cell)
        data.append(row_cells)
    
    # Create table
    if not col_widths:
        # Auto-calculate widths
        num_cols = len(headers)
        col_width = 17*cm / num_cols
        col_widths = [col_width] * num_cols
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(get_minimal_table_style())
    
    return table


# ==================== FOOTER ====================
def add_page_number(canvas_obj, doc):
    """
    Add minimal page footer with page number
    
    Args:
        canvas_obj: ReportLab canvas object
        doc: Document object
    """
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    page_num = canvas_obj.getPageNumber()
    text = rtl(f"صفحة {page_num}")
    
    canvas_obj.saveState()
    canvas_obj.setFont(font_name, 9)
    canvas_obj.setFillColor(MinimalColors.TEXT_LIGHT)
    
    # Center footer
    canvas_obj.drawCentredString(
        A4[0] / 2,
        1.5*cm,
        text
    )
    
    # Optional: Add system name on the right
    canvas_obj.drawRightString(
        A4[0] - 2*cm,
        1.5*cm,
        rtl("نظام إدارة عمليات الكلاب البوليسية K9")
    )
    
    canvas_obj.restoreState()


# ==================== UTILITIES ====================
def create_divider():
    """Create a simple horizontal divider"""
    divider_data = [['']]
    divider_table = Table(divider_data, colWidths=[17*cm])
    divider_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, MinimalColors.LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return divider_table


def create_spacer(height_cm=0.5):
    """Create a vertical spacer"""
    return Spacer(1, height_cm*cm)


def format_status_badge(status_text, status_type='default'):
    """
    Format status text with appropriate color
    
    Args:
        status_text: Status text (Arabic)
        status_type: 'success', 'warning', 'danger', 'info', or 'default'
        
    Returns:
        Formatted HTML string
    """
    color_map = {
        'success': '#10B981',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#3B82F6',
        'default': '#666666'
    }
    
    color = color_map.get(status_type, color_map['default'])
    return f'<font color="{color}"><b>{status_text}</b></font>'
