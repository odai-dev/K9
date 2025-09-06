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
    Tries to find and register DejaVu Sans or falls back to default fonts
    """
    global _FONTS_REGISTERED
    
    if _FONTS_REGISTERED:
        return True
    
    try:
        # Try to find DejaVu Sans fonts (commonly available)
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/DejaVuSans.ttf',
            'C:\\Windows\\Fonts\\DejaVuSans.ttf'
        ]
        
        dejavu_path = None
        for path in font_paths:
            if os.path.exists(path):
                dejavu_path = path
                break
        
        if dejavu_path:
            # Register DejaVu Sans font
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))
            addMapping('DejaVuSans', 0, 0, 'DejaVuSans')  # normal
            print(f"Successfully registered DejaVu Sans font from: {dejavu_path}")
            _FONTS_REGISTERED = True
            return True
        else:
            print("DejaVu Sans font not found. Using default fonts (Arabic may not display correctly)")
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
        return 'DejaVuSans'
    else:
        # Fallback to Helvetica (may not display Arabic correctly)
        return 'Helvetica'

def format_arabic_date(date_obj) -> str:
    """
    Format a date object into Arabic numerals and format
    
    Args:
        date_obj: Python date object
        
    Returns:
        Formatted date string in Arabic style (dd/mm/yyyy)
    """
    if not date_obj:
        return ""
    
    # Convert to Arabic numerals
    arabic_numerals = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
    
    # Format as dd/mm/yyyy
    formatted_date = date_obj.strftime("%d/%m/%Y")
    
    # Convert to Arabic numerals
    arabic_date = formatted_date.translate(arabic_numerals)
    
    return arabic_date

def format_arabic_time(time_obj) -> str:
    """
    Format a time object into Arabic numerals
    
    Args:
        time_obj: Python time object
        
    Returns:
        Formatted time string in Arabic numerals (HH:MM)
    """
    if not time_obj:
        return ""
    
    # Convert to Arabic numerals
    arabic_numerals = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
    
    # Format as HH:MM
    formatted_time = time_obj.strftime("%H:%M")
    
    # Convert to Arabic numerals
    arabic_time = formatted_time.translate(arabic_numerals)
    
    return arabic_time

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