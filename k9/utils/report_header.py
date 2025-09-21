"""
Standardized report header utilities for K9 Operations Management System
Provides consistent header design across all PDF and Excel reports
"""

import os
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from k9.utils.utils_pdf_rtl import rtl, register_arabic_fonts, get_arabic_font_name


def get_company_header_data():
    """
    Get standardized company information for reports
    
    Returns:
        Dict containing English and Arabic company information
    """
    return {
        'english': {
            'company_name': 'Peregrine Security and Safety Services',
            'service_type': 'Security guard service',
            'address': 'Haddah, West of the German Embassy, Sana\'a, Yemen'
        },
        'arabic': {
            'company_name': 'نشاط خدمات الأمن والسلامة',
            'service_type': 'خدمة حراسة الأمن',
            'address_1': 'حدة غرب السفارة الألمانية صنعاء',
            'address_2': 'الجمهورية اليمنية'
        }
    }


def create_pdf_report_header(report_title_ar, report_subtitle_ar="", additional_info=""):
    """
    Create standardized PDF report header with company logo and information
    
    Args:
        report_title_ar: Arabic title of the report
        report_subtitle_ar: Optional Arabic subtitle  
        additional_info: Optional additional information (date, project, etc.)
        
    Returns:
        List of ReportLab elements to add to story
    """
    # Register Arabic fonts
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    # Get company data
    company_data = get_company_header_data()
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Company info styles
    company_style_en = ParagraphStyle(
        'CompanyEnglish',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        alignment=TA_LEFT,
        leftIndent=0,
        spaceAfter=2
    )
    
    company_style_ar = ParagraphStyle(
        'CompanyArabic', 
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        alignment=TA_RIGHT,
        rightIndent=0,
        spaceAfter=2
    )
    
    # Report title styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    info_style = ParagraphStyle(
        'AdditionalInfo',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    # Build header elements
    header_elements = []
    
    # Company header table with logo
    try:
        # Try to load the logo
        # Try the new company header template first, fallback to old logo
        company_template_path = os.path.join('k9', 'static', 'img', 'company_header.png')
        old_logo_path = os.path.join('k9', 'static', 'img', 'peregrine_header.png')
        
        # Use company template if available, otherwise fallback
        logo_path = company_template_path if os.path.exists(company_template_path) else old_logo_path
        if os.path.exists(logo_path):
            # Create company information sections
            english_info = Paragraph(f"""
                <b>{company_data['english']['company_name']}</b><br/>
                {company_data['english']['service_type']}<br/>
                {company_data['english']['address']}
            """, company_style_en)
            
            arabic_info = Paragraph(rtl(f"""
                <b>{company_data['arabic']['company_name']}</b><br/>
                {company_data['arabic']['service_type']}<br/>
                {company_data['arabic']['address_1']}<br/>
                {company_data['arabic']['address_2']}
            """), company_style_ar)
            
            # Load and scale logo
            logo = Image(logo_path)
            # Scale logo to fit header - adjust size as needed
            logo.drawWidth = 2*inch
            logo.drawHeight = 0.8*inch
            
            # Create header table: English | Logo | Arabic
            header_table_data = [
                [english_info, logo, arabic_info]
            ]
            
            header_table = Table(header_table_data, colWidths=[2.5*inch, 2*inch, 2.5*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),     # English left
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),   # Logo center  
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),    # Arabic right
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            header_elements.append(header_table)
            
        else:
            # Fallback: text-only header if logo not found
            company_header_text = f"""
                {company_data['english']['company_name']} - {rtl(company_data['arabic']['company_name'])}<br/>
                {company_data['english']['service_type']} - {rtl(company_data['arabic']['service_type'])}
            """
            company_header = Paragraph(company_header_text, company_style_en)
            header_elements.append(company_header)
            
    except Exception as e:
        # Fallback in case of any error
        print(f"Warning: Could not create company header with logo: {e}")
        company_header_text = f"{company_data['english']['company_name']} - {rtl(company_data['arabic']['company_name'])}"
        company_header = Paragraph(company_header_text, company_style_en)
        header_elements.append(company_header)
    
    # Add separator line
    header_elements.append(Spacer(1, 10))
    separator_table = Table([[""] * 5], colWidths=[1.5*inch] * 5)
    separator_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.black)
    ]))
    header_elements.append(separator_table)
    header_elements.append(Spacer(1, 15))
    
    # Add report title
    if report_title_ar:
        title = Paragraph(rtl(report_title_ar), title_style)
        header_elements.append(title)
    
    # Add report subtitle if provided
    if report_subtitle_ar:
        subtitle = Paragraph(rtl(report_subtitle_ar), subtitle_style)
        header_elements.append(subtitle)
    
    # Add additional info if provided
    if additional_info:
        info = Paragraph(rtl(additional_info), info_style)
        header_elements.append(info)
    
    # Add final spacer
    header_elements.append(Spacer(1, 20))
    
    return header_elements


def create_excel_header_data():
    """
    Create standardized header data for Excel reports
    
    Returns:
        Dict with header information formatted for Excel export
    """
    company_data = get_company_header_data()
    
    return {
        'company_logo_path': os.path.join('k9', 'static', 'img', 'company_header.png') if os.path.exists(os.path.join('k9', 'static', 'img', 'company_header.png')) else os.path.join('k9', 'static', 'img', 'peregrine_header.png'),
        'english_info': [
            company_data['english']['company_name'],
            company_data['english']['service_type'], 
            company_data['english']['address']
        ],
        'arabic_info': [
            company_data['arabic']['company_name'],
            company_data['arabic']['service_type'],
            company_data['arabic']['address_1'],
            company_data['arabic']['address_2']
        ]
    }