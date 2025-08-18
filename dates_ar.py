"""
Arabic date utilities for PM Daily Report system
Provides Arabic day names and date formatting
"""

from datetime import date
from typing import Dict

# Arabic day names mapping
ARABIC_DAY_NAMES: Dict[int, str] = {
    0: "الاثنين",      # Monday
    1: "الثلاثاء",     # Tuesday  
    2: "الأربعاء",     # Wednesday
    3: "الخميس",      # Thursday
    4: "الجمعة",       # Friday
    5: "السبت",        # Saturday
    6: "الأحد"         # Sunday
}

def get_arabic_day_name(date_obj: date) -> str:
    """
    Get Arabic day name for a given date
    
    Args:
        date_obj: Date object
        
    Returns:
        Arabic day name string
    """
    weekday = date_obj.weekday()
    return ARABIC_DAY_NAMES.get(weekday, "غير محدد")

def format_arabic_date(date_obj: date) -> str:
    """
    Format date in Arabic style (DD/MM/YYYY)
    
    Args:
        date_obj: Date object
        
    Returns:
        Formatted date string in Arabic style
    """
    return date_obj.strftime("%d/%m/%Y")