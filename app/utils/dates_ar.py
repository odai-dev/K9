"""
Arabic date utilities
"""
from datetime import date

DAY_NAMES_AR = {
    0: "الاثنين",
    1: "الثلاثاء", 
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد"
}

def get_arabic_day_name(date_obj: date) -> str:
    """
    Get Arabic day name for a given date
    
    Args:
        date_obj: Date object
        
    Returns:
        Arabic day name
    """
    return DAY_NAMES_AR.get(date_obj.weekday(), "")