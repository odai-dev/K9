"""
Arabic date utilities
"""

from datetime import datetime, date

def get_arabic_day_name(date_obj):
    """Get Arabic name for day of week"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
    
    arabic_days = [
        "الاثنين",   # Monday
        "الثلاثاء",  # Tuesday  
        "الأربعاء",  # Wednesday
        "الخميس",    # Thursday
        "الجمعة",    # Friday
        "السبت",     # Saturday
        "الأحد"      # Sunday
    ]
    
    return arabic_days[date_obj.weekday()]

def get_arabic_month_name(date_obj):
    """Get Arabic name for month"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
    
    arabic_months = [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    
    return arabic_months[date_obj.month - 1]

def format_arabic_date(date_obj):
    """Format date in DD/MM/YYYY format"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
    
    return f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"