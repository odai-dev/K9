"""
Arabic RTL PDF generation utilities
Provides helper functions for generating RTL Arabic text in PDFs using ReportLab
"""

import os
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, cm

# Try to import Arabic text processing libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    print("Warning: arabic_reshaper or python-bidi not available. Arabic text may not display correctly.")
    ARABIC_SUPPORT = False

# Font registration status
_FONTS_REGISTERED = False

def register_arabic_fonts():
    """
    Register Arabic-compatible fonts for ReportLab
    Prioritizes local Arabic font files, then falls back to system fonts
    """
    global _FONTS_REGISTERED
    
    if _FONTS_REGISTERED:
        return True
    
    try:
        # First priority: Local Arabic fonts in the project
        local_font_paths = [
            ('NotoSansArabic', 'k9/static/fonts/NotoSansArabic-Regular.ttf'),
            ('Amiri', 'k9/static/fonts/Amiri-Regular.ttf'),
            ('DejaVuSans', 'k9/static/fonts/DejaVuSans.ttf'),
        ]
        
        for font_name, font_path in local_font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                addMapping(font_name, 0, 0, font_name)  # normal
                print(f"Successfully registered {font_name} font from: {font_path}")
                _FONTS_REGISTERED = True
                return True
        
        # Second priority: System DejaVu Sans fonts
        system_font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/DejaVuSans.ttf',
            'C:\\Windows\\Fonts\\DejaVuSans.ttf'
        ]
        
        for path in system_font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                addMapping('DejaVuSans', 0, 0, 'DejaVuSans')  # normal
                print(f"Successfully registered DejaVu Sans font from: {path}")
                _FONTS_REGISTERED = True
                return True
        
        print("No Arabic-compatible fonts found. Using default fonts (Arabic may not display correctly)")
        return False
            
    except Exception as e:
        print(f"Error registering Arabic fonts: {e}")
        return False

def rtl(text: str) -> str:
    """
    Process Arabic text for RTL display in PDFs
    
    Args:
        text: Arabic text string
        
    Returns:
        Processed text ready for RTL display
    """
    if not text or not ARABIC_SUPPORT:
        return text
    
    try:
        # Reshape Arabic text (connect letters properly)
        reshaped_text = arabic_reshaper.reshape(text)
        
        # Apply bidirectional algorithm for proper RTL ordering
        display_text = get_display(reshaped_text)
        
        return display_text
    except Exception as e:
        print(f"Error processing Arabic text: {e}")
        return text

def get_arabic_font_name() -> str:
    """
    Get the name of the registered Arabic font
    
    Returns:
        Font name to use in ReportLab
    """
    if _FONTS_REGISTERED:
        # Check which font was actually registered (prioritize Arabic fonts)
        try:
            from reportlab.pdfbase import pdfmetrics
            
            # Check for Noto Sans Arabic first (best Arabic support)
            if 'NotoSansArabic' in pdfmetrics._fonts:
                return 'NotoSansArabic'
            # Then check for Amiri
            elif 'Amiri' in pdfmetrics._fonts:
                return 'Amiri'
            # Then DejaVu Sans
            elif 'DejaVuSans' in pdfmetrics._fonts:
                return 'DejaVuSans'
        except:
            pass
        
        # Default fallback when fonts are registered but we can't detect which
        return 'NotoSansArabic'
    else:
        # Fallback to Helvetica (may not display Arabic correctly)
        return 'Helvetica'

def format_arabic_date(date_obj) -> str:
    """
    Format a date object into DD/MM/YYYY format with standard numerals
    
    Args:
        date_obj: Python date object
        
    Returns:
        Formatted date string in DD/MM/YYYY format
    """
    if not date_obj:
        return ""
    
    # Format as dd/mm/yyyy with standard numerals
    return date_obj.strftime("%d/%m/%Y")

def format_arabic_time(time_obj) -> str:
    """
    Format a time object with standard numerals
    
    Args:
        time_obj: Python time object
        
    Returns:
        Formatted time string with standard numerals (HH:MM)
    """
    if not time_obj:
        return ""
    
    # Format as HH:MM with standard numerals
    return time_obj.strftime("%H:%M")

def get_page_dimensions():
    """
    Get standard page dimensions for the daily sheet report
    
    Returns:
        Dictionary with page width, height, and margins
    """
    return {
        'width': 8.5 * inch,  # Letter size width
        'height': 11 * inch,  # Letter size height
        'margin_left': 0.5 * inch,
        'margin_right': 0.5 * inch,
        'margin_top': 0.5 * inch,
        'margin_bottom': 0.5 * inch
    }