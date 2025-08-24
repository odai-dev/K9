"""
Veterinary report constants and labels
"""

# Arabic labels for visit types
VISIT_TYPE_LABELS = {
    "ROUTINE": "روتينية",
    "EMERGENCY": "طارئة", 
    "VACCINATION": "تحصين"
}

# Arabic day names
DAY_NAMES = {
    0: "الاثنين",   # Monday
    1: "الثلاثاء",   # Tuesday
    2: "الأربعاء",   # Wednesday
    3: "الخميس",    # Thursday
    4: "الجمعة",    # Friday
    5: "السبت",     # Saturday
    6: "الأحد"      # Sunday
}

# PDF Table headers (RTL order - rightmost to leftmost)
PDF_HEADERS = [
    "الوقت",
    "اسم الكلب", 
    "السلالة",
    "الطبيب",
    "نوع الزيارة",
    "التشخيص",
    "العلاج", 
    "الأدوية",
    "التكلفة",
    "الموقع",
    "الطقس",
    "العلامات الحيوية",
    "ملاحظات"
]

# HTML Table headers (same order for RTL display)
HTML_HEADERS = PDF_HEADERS.copy()

# CSS classes for styling
TABLE_CLASSES = "table table-bordered table-striped table-hover"
CARD_CLASSES = "card shadow-sm"
FILTER_CLASSES = "row g-3 mb-4"