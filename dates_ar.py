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