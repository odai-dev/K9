"""
Unified PDF Report Generator Service
Provides a single entry point for generating professional PDF reports for all report types
with bilingual header (English/Arabic), company branding, and proper RTL support.
"""

import os
import logging
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfgen import canvas
from flask import current_app

from k9.utils.utils_pdf_rtl import register_arabic_fonts, get_arabic_font_name, format_pdf_text
from k9.services.report_registry import get_report_registry, ColumnDefinition

logger = logging.getLogger(__name__)

# Company information constants
COMPANY_NAME_EN = "Peregrine Security and Safety Services"
COMPANY_INFO_EN = [
    "Security guard service",
    "Haddah, West of the German Embassy, Sana'a, Yemen"
]

COMPANY_NAME_AR = "نشاط خدمات الأمن والسلامة"
COMPANY_INFO_AR = [
    "خدمة حراسة الأمن",
    "حدة غرب السفارة الألمانية صنعاء",
    "الجمهورية اليمنية"
]

# Arabic day names mapping
ARABIC_DAYS = {
    'Monday': 'الإثنين',
    'Tuesday': 'الثلاثاء',
    'Wednesday': 'الأربعاء',
    'Thursday': 'الخميس',
    'Friday': 'الجمعة',
    'Saturday': 'السبت',
    'Sunday': 'الأحد'
}

# Default header color for tables
DEFAULT_HEADER_COLOR = colors.HexColor('#603913')


class UnifiedPDFReportGenerator:
    """
    Unified PDF Report Generator that creates professional bilingual reports
    matching the HTML preview style for all report types.
    """
    
    def __init__(self):
        self.arabic_font = None
        self.styles = None
        self._init_fonts_and_styles()
    
    def _init_fonts_and_styles(self):
        """Initialize fonts and paragraph styles"""
        register_arabic_fonts()
        self.arabic_font = get_arabic_font_name()
        self.styles = getSampleStyleSheet()
        
        # Define custom styles for Arabic text
        self.style_ar_right = ParagraphStyle(
            'ArabicRight',
            fontName=self.arabic_font,
            fontSize=10,
            alignment=2,  # RIGHT
            leading=14
        )
        
        self.style_ltr = ParagraphStyle(
            'LatinLeft',
            fontName=self.arabic_font,
            fontSize=10,
            alignment=0,  # LEFT
            leading=14
        )
        
        self.style_header = ParagraphStyle(
            'TableHeader',
            fontName=self.arabic_font,
            fontSize=10,
            alignment=1,  # CENTER
            textColor=colors.whitesmoke,
            leading=12
        )
        
        self.style_title = ParagraphStyle(
            'ReportTitle',
            fontName=self.arabic_font,
            fontSize=18,
            alignment=1,  # CENTER
            textColor=colors.HexColor('#603913'),
            spaceAfter=20,
            leading=24
        )
        
        self.style_subtitle = ParagraphStyle(
            'ReportSubtitle',
            fontName=self.arabic_font,
            fontSize=12,
            alignment=1,  # CENTER
            textColor=colors.HexColor('#333333'),
            spaceAfter=15,
            leading=16
        )
        
        self.style_footer = ParagraphStyle(
            'FooterText',
            fontName=self.arabic_font,
            fontSize=9,
            alignment=1,  # CENTER
            textColor=colors.HexColor('#666666'),
            leading=12
        )
    
    def _get_logo_path(self):
        """Get the path to company logo"""
        try:
            logo_path = os.path.join(current_app.root_path, 'static/img/company_logo.png')
            if os.path.exists(logo_path):
                return logo_path
        except Exception as e:
            logger.warning(f"Could not get logo path: {e}")
        return None
    
    def _format_arabic(self, text):
        """Format text for Arabic RTL display"""
        return format_pdf_text(text)
    
    def _para_arabic(self, value):
        """Create Arabic paragraph with right alignment"""
        text = '' if value is None else str(value)
        return Paragraph(self._format_arabic(text), self.style_ar_right)
    
    def _para_latin(self, value):
        """Create Latin/number paragraph with left alignment"""
        text = '' if value is None else str(value)
        return Paragraph(text, self.style_ltr)
    
    def _para_header(self, text):
        """Create header cell paragraph"""
        return Paragraph(self._format_arabic(text), self.style_header)
    
    def _draw_header(self, canvas_obj, doc, include_date=True):
        """
        Draw the professional bilingual header on each page.
        Matches the HTML template in k9/templates/reports/_header.html
        """
        width, height = A4
        top_margin = height - 30
        
        # Get current date info
        now = datetime.now()
        current_day_name = ARABIC_DAYS.get(now.strftime('%A'), now.strftime('%A'))
        current_date = now.strftime('%d-%m-%Y')
        
        # Day and Date at very top right (Arabic)
        if include_date:
            canvas_obj.setFont(self.arabic_font, 10)
            canvas_obj.drawRightString(
                width - doc.rightMargin, 
                top_margin,
                self._format_arabic(f"اليوم: {current_day_name}")
            )
            canvas_obj.drawRightString(
                width - doc.rightMargin, 
                top_margin - 15,
                self._format_arabic(f"التاريخ: {current_date}")
            )
        
        # Header section starts below date
        header_top = top_margin - 45
        
        # English company info (Left side)
        canvas_obj.setFont('Helvetica-Bold', 9)
        canvas_obj.drawString(doc.leftMargin, header_top, COMPANY_NAME_EN)
        canvas_obj.setFont('Helvetica', 8)
        for i, line in enumerate(COMPANY_INFO_EN):
            canvas_obj.drawString(doc.leftMargin, header_top - 12 - (i * 10), line)
        
        # Company logo (Center)
        logo_path = self._get_logo_path()
        if logo_path:
            logo_width = 70
            logo_height = 70
            logo_x = (width - logo_width) / 2
            logo_y = header_top - 55
            try:
                canvas_obj.drawImage(
                    logo_path, 
                    x=logo_x, 
                    y=logo_y,
                    width=logo_width, 
                    height=logo_height,
                    preserveAspectRatio=True, 
                    mask='auto'
                )
            except Exception as e:
                logger.warning(f"Could not draw logo: {e}")
        
        # Arabic company info (Right side)
        canvas_obj.setFont(self.arabic_font, 9)
        canvas_obj.drawRightString(
            width - doc.rightMargin, 
            header_top,
            self._format_arabic(COMPANY_NAME_AR)
        )
        canvas_obj.setFont(self.arabic_font, 8)
        for i, line in enumerate(COMPANY_INFO_AR):
            canvas_obj.drawRightString(
                width - doc.rightMargin, 
                header_top - 12 - (i * 10),
                self._format_arabic(line)
            )
        
        # Horizontal line separator
        canvas_obj.setStrokeColor(colors.HexColor('#333333'))
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(
            doc.leftMargin, 
            header_top - 90,
            width - doc.rightMargin, 
            header_top - 90
        )
    
    def _draw_footer(self, canvas_obj, doc, user=None, page_num=None, total_pages=None):
        """Draw the footer on each page"""
        width, height = A4
        bottom_margin = 40
        
        # Timestamp
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        canvas_obj.setFont(self.arabic_font, 8)
        canvas_obj.setFillColor(colors.HexColor('#666666'))
        
        # Left side: Generation timestamp
        canvas_obj.drawString(
            doc.leftMargin, 
            bottom_margin,
            f"Generated: {timestamp}"
        )
        
        # Center: User info if provided
        if user:
            user_name = getattr(user, 'username', str(user)) if user else ''
            canvas_obj.drawCentredString(
                width / 2, 
                bottom_margin,
                f"By: {user_name}"
            )
        
        # Right side: Page number if provided
        if page_num and total_pages:
            canvas_obj.drawRightString(
                width - doc.rightMargin, 
                bottom_margin,
                f"Page {page_num} of {total_pages}"
            )
    
    def _build_data_table(self, data, columns, header_color=None):
        """
        Build a data table with the specified columns and data.
        
        Args:
            data: List of dictionaries or list of lists containing the data
            columns: List of tuples (key, header_text, width_mm, is_arabic)
                    or list of dictionaries with 'key', 'header', 'width', 'arabic' keys
            header_color: Color for header row (default: brown #603913)
        
        Returns:
            ReportLab Table object
        """
        if not data:
            return Paragraph(
                self._format_arabic("لا توجد بيانات"),
                self.style_ar_right
            )
        
        header_color = header_color or DEFAULT_HEADER_COLOR
        
        # Normalize column definitions
        normalized_columns = []
        for col in columns:
            if isinstance(col, dict):
                normalized_columns.append({
                    'key': col.get('key', ''),
                    'header': col.get('header', ''),
                    'width': col.get('width', 25),
                    'arabic': col.get('arabic', True)
                })
            elif isinstance(col, (list, tuple)) and len(col) >= 2:
                normalized_columns.append({
                    'key': col[0],
                    'header': col[1],
                    'width': col[2] if len(col) > 2 else 25,
                    'arabic': col[3] if len(col) > 3 else True
                })
        
        # Build header row
        header_row = [self._para_header(col['header']) for col in normalized_columns]
        
        # Build data rows
        rows = [header_row]
        for i, record in enumerate(data):
            row = []
            for col in normalized_columns:
                key = col['key']
                is_arabic = col['arabic']
                
                # Get value from record
                if isinstance(record, dict):
                    value = record.get(key, '')
                elif isinstance(record, (list, tuple)):
                    try:
                        idx = int(key) if isinstance(key, int) else list(range(len(record)))[columns.index(col)]
                        value = record[idx] if idx < len(record) else ''
                    except (ValueError, IndexError):
                        value = ''
                else:
                    value = getattr(record, key, '') if hasattr(record, key) else ''
                
                # Create paragraph based on text type
                if is_arabic:
                    row.append(self._para_arabic(value))
                else:
                    row.append(self._para_latin(value))
            
            rows.append(row)
        
        # Calculate column widths
        col_widths = [col['width'] * mm for col in normalized_columns]
        
        # Create table
        table = Table(rows, repeatRows=1, colWidths=col_widths)
        
        # Apply table style
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, header_color),
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center headers
            
            # Alternating row backgrounds
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f5f5f5')]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _build_simple_table(self, data_rows, header_color=None):
        """
        Build a simple table from raw data rows.
        First row is treated as headers.
        
        Args:
            data_rows: List of lists, first row is headers
            header_color: Color for header row
        
        Returns:
            ReportLab Table object
        """
        if not data_rows or len(data_rows) == 0:
            return Paragraph(
                self._format_arabic("لا توجد بيانات"),
                self.style_ar_right
            )
        
        header_color = header_color or DEFAULT_HEADER_COLOR
        
        # Build header row
        header_row = [self._para_header(cell) for cell in data_rows[0]]
        
        # Build data rows
        rows = [header_row]
        for row_data in data_rows[1:]:
            row = []
            for cell in row_data:
                # Auto-detect if text is Arabic
                if cell and isinstance(cell, str) and any('\u0600' <= c <= '\u06FF' for c in cell):
                    row.append(self._para_arabic(cell))
                else:
                    row.append(self._para_latin(cell))
            rows.append(row)
        
        # Calculate column widths (distribute evenly)
        num_cols = len(data_rows[0]) if data_rows else 1
        available_width = 180  # mm, accounting for margins
        col_width = available_width / num_cols
        col_widths = [col_width * mm] * num_cols
        
        # Create table
        table = Table(rows, repeatRows=1, colWidths=col_widths)
        
        # Apply table style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, header_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _build_signature_section(self, signature_labels=None):
        """
        Build signature lines section for the footer.
        
        Args:
            signature_labels: List of tuples (english_label, arabic_label)
        
        Returns:
            List of flowable elements
        """
        if not signature_labels:
            signature_labels = [
                ("Prepared by", "أعده"),
                ("Reviewed by", "راجعه"),
                ("Approved by", "اعتمده")
            ]
        
        elements = []
        elements.append(Spacer(1, 30))
        
        # Create signature table
        sig_data = []
        for en_label, ar_label in signature_labels:
            sig_data.append([
                Paragraph(f"{en_label}: _______________", self.style_ltr),
                Paragraph(self._format_arabic(f": {ar_label}"), self.style_ar_right)
            ])
        
        # Add date row
        sig_data.append([
            Paragraph("Date: _______________", self.style_ltr),
            Paragraph(self._format_arabic(": التاريخ"), self.style_ar_right)
        ])
        
        sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(sig_table)
        return elements
    
    def _build_notes_section(self, notes_text=None):
        """
        Build notes section.
        
        Args:
            notes_text: Optional notes text to include
        
        Returns:
            List of flowable elements
        """
        elements = []
        elements.append(Spacer(1, 20))
        
        # Notes header
        notes_header = Paragraph(
            self._format_arabic("ملاحظات / Notes"),
            ParagraphStyle(
                'NotesHeader',
                fontName=self.arabic_font,
                fontSize=11,
                alignment=1,
                textColor=colors.HexColor('#603913'),
                spaceAfter=10
            )
        )
        elements.append(notes_header)
        
        # Notes content or empty lines
        if notes_text:
            elements.append(Paragraph(notes_text, self.style_ar_right))
        else:
            # Empty lines for handwritten notes
            for _ in range(3):
                elements.append(Paragraph(
                    "____________________________________________________________________",
                    ParagraphStyle(
                        'NotesLine',
                        fontName='Helvetica',
                        fontSize=10,
                        alignment=1,
                        textColor=colors.HexColor('#999999'),
                        spaceBefore=15
                    )
                ))
        
        return elements
    
    def generate_pdf_report(
        self,
        report_type: str,
        data: list,
        columns: list,
        title: str,
        start_date=None,
        end_date=None,
        user=None,
        subtitle: str = None,
        header_color=None,
        include_notes: bool = True,
        include_signatures: bool = True,
        notes_text: str = None,
        signature_labels: list = None
    ) -> BytesIO:
        """
        Generate a PDF report for any report type.
        
        Args:
            report_type: Type of report (for logging/tracking)
            data: List of data records (dicts or lists)
            columns: Column definitions - list of tuples (key, header, width_mm, is_arabic)
                    or list of dicts with 'key', 'header', 'width', 'arabic' keys
            title: Report title (Arabic)
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            user: User who generated the report
            subtitle: Optional subtitle
            header_color: Optional header color (default: brown #603913)
            include_notes: Whether to include notes section
            include_signatures: Whether to include signature lines
            notes_text: Optional pre-filled notes text
            signature_labels: Optional custom signature labels
        
        Returns:
            BytesIO buffer containing the PDF
        """
        # Initialize fonts
        self._init_fonts_and_styles()
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=120,  # Leave space for header
            bottomMargin=60  # Leave space for footer
        )
        
        # Build story (content)
        story = []
        
        # Add title
        story.append(Paragraph(
            self._format_arabic(title),
            self.style_title
        ))
        
        # Add subtitle if provided
        if subtitle:
            story.append(Paragraph(
                self._format_arabic(subtitle),
                self.style_subtitle
            ))
        
        # Add date range if provided
        if start_date or end_date:
            date_range_text = ""
            if start_date and end_date:
                start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
                end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
                date_range_text = f"الفترة: {start_str} إلى {end_str}"
            elif start_date:
                start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
                date_range_text = f"من تاريخ: {start_str}"
            elif end_date:
                end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
                date_range_text = f"حتى تاريخ: {end_str}"
            
            story.append(Paragraph(
                self._format_arabic(date_range_text),
                ParagraphStyle(
                    'DateRange',
                    fontName=self.arabic_font,
                    fontSize=10,
                    alignment=1,
                    textColor=colors.HexColor('#666666'),
                    spaceAfter=15
                )
            ))
        
        story.append(Spacer(1, 10))
        
        # Build data table
        if columns:
            # Using column definitions
            table = self._build_data_table(data, columns, header_color)
        elif data and isinstance(data[0], (list, tuple)):
            # Raw data rows (first row is headers)
            table = self._build_simple_table(data, header_color)
        else:
            table = Paragraph(
                self._format_arabic("لا توجد بيانات متاحة"),
                self.style_ar_right
            )
        
        story.append(table)
        
        # Add notes section if requested
        if include_notes:
            story.extend(self._build_notes_section(notes_text))
        
        # Add signature section if requested
        if include_signatures:
            story.extend(self._build_signature_section(signature_labels))
        
        # Create header/footer callback
        def add_header_footer(canvas_obj, doc_obj):
            canvas_obj.saveState()
            self._draw_header(canvas_obj, doc_obj)
            self._draw_footer(canvas_obj, doc_obj, user)
            canvas_obj.restoreState()
        
        # Build PDF
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        # Reset buffer position
        buffer.seek(0)
        
        logger.info(f"Generated PDF report: {report_type}")
        return buffer


# Create singleton instance for easy access
_generator_instance = None

def get_pdf_generator() -> UnifiedPDFReportGenerator:
    """Get the singleton PDF generator instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = UnifiedPDFReportGenerator()
    return _generator_instance


def generate_pdf_report(
    report_type: str,
    data: list,
    columns: list,
    title: str,
    start_date=None,
    end_date=None,
    user=None,
    **kwargs
) -> BytesIO:
    """
    Convenience function to generate a PDF report.
    
    Args:
        report_type: Type of report (for logging/tracking)
        data: List of data records (dicts or lists)
        columns: Column definitions - list of tuples (key, header, width_mm, is_arabic)
        title: Report title (Arabic)
        start_date: Optional start date for date range
        end_date: Optional end date for date range
        user: User who generated the report
        **kwargs: Additional options (subtitle, header_color, include_notes, etc.)
    
    Returns:
        BytesIO buffer containing the PDF
    """
    generator = get_pdf_generator()
    return generator.generate_pdf_report(
        report_type=report_type,
        data=data,
        columns=columns,
        title=title,
        start_date=start_date,
        end_date=end_date,
        user=user,
        **kwargs
    )


def generate_simple_pdf_report(
    report_type: str,
    data_rows: list,
    title: str,
    start_date=None,
    end_date=None,
    user=None,
    **kwargs
) -> BytesIO:
    """
    Generate a simple PDF report from raw data rows.
    First row of data_rows should be headers.
    
    Args:
        report_type: Type of report
        data_rows: List of lists, first row is headers
        title: Report title
        start_date: Optional start date
        end_date: Optional end date
        user: User who generated the report
        **kwargs: Additional options
    
    Returns:
        BytesIO buffer containing the PDF
    """
    generator = get_pdf_generator()
    return generator.generate_pdf_report(
        report_type=report_type,
        data=data_rows,
        columns=None,  # Will use simple table builder
        title=title,
        start_date=start_date,
        end_date=end_date,
        user=user,
        **kwargs
    )


def generate_report_from_registry(
    report_type: str,
    records: list,
    start_date=None,
    end_date=None,
    user=None,
    **kwargs
) -> BytesIO:
    """
    Generate a PDF report using the report registry for column definitions.
    This ensures PDF output matches HTML preview exactly.
    
    Args:
        report_type: Type of report (must be registered in ReportRegistry)
        records: List of dict records with header keys (pre-formatted)
        start_date: Optional start date
        end_date: Optional end date
        user: User who generated the report
        **kwargs: Additional options
    
    Returns:
        BytesIO buffer containing the PDF
    """
    registry = get_report_registry()
    report_def = registry.get_report(report_type)
    
    if not report_def:
        logger.warning(f"Report type '{report_type}' not found in registry, using simple generator")
        # Fallback to simple generator
        if records:
            headers = list(records[0].keys())
            data_rows = [headers]
            for record in records:
                data_rows.append([str(record.get(h, '')) for h in headers])
            return generate_simple_pdf_report(
                report_type=report_type,
                data_rows=data_rows,
                title=kwargs.get('title', 'تقرير'),
                start_date=start_date,
                end_date=end_date,
                user=user
            )
        return generate_simple_pdf_report(
            report_type=report_type,
            data_rows=[],
            title=kwargs.get('title', 'تقرير'),
            start_date=start_date,
            end_date=end_date,
            user=user
        )
    
    # Convert ColumnDefinition objects to dict format for the generator
    column_defs = []
    for col in report_def.columns:
        column_defs.append({
            'key': col.header,  # Use header as key since records use headers
            'header': col.header,
            'width': col.width_mm,
            'arabic': col.is_arabic
        })
    
    generator = get_pdf_generator()
    return generator.generate_pdf_report(
        report_type=report_type,
        data=records,
        columns=column_defs,
        title=report_def.title_ar,
        start_date=start_date,
        end_date=end_date,
        user=user,
        **kwargs
    )
