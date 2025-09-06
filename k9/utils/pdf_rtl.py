"""
RTL PDF utilities for Arabic text
"""

import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text_for_pdf(text):
    """Fix Arabic text for proper display in PDFs"""
    if not text:
        return text
    
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except:
        return str(text)

def format_arabic_date(date_obj):
    """Format date in Arabic"""
    from k9.utils.dates_ar import get_arabic_day_name, get_arabic_month_name
    
    day_name = get_arabic_day_name(date_obj)
    month_name = get_arabic_month_name(date_obj)
    
    return f"{day_name} {date_obj.day} {month_name} {date_obj.year}"

def register_arabic_fonts():
    """Register Arabic fonts for PDF generation"""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        # Try to register Amiri font if available
        font_path = os.path.join("static", "fonts", "Amiri-Regular.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Amiri', font_path))
        
        # Try to register Noto Sans Arabic if available
        font_path = os.path.join("static", "fonts", "NotoSansArabic-Regular.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('NotoSansArabic', font_path))
            
        return True
    except Exception as e:
        print(f"Warning: Could not register Arabic fonts: {e}")
        return False

def rtl(text):
    """Alias for fix_arabic_text_for_pdf for backwards compatibility"""
    return fix_arabic_text_for_pdf(text)

def get_arabic_font():
    """Get the default Arabic font name"""
    return 'Amiri'  # Default Arabic font