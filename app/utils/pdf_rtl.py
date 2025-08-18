"""
Arabic RTL PDF generation utilities for PM Daily Report
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
        return text or ""
    
    try:
        # Reshape Arabic text (connects letters properly)
        reshaped_text = arabic_reshaper.reshape(text)
        
        # Apply bidirectional algorithm for RTL display
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    except Exception as e:
        print(f"Error processing RTL text '{text}': {e}")
        return text or ""

def get_arabic_font():
    """
    Get the name of the registered Arabic font
    
    Returns:
        Font name string or 'Helvetica' as fallback
    """
    register_arabic_fonts()
    return 'DejaVuSans' if _FONTS_REGISTERED else 'Helvetica'