"""
Constants and enums for attendance reporting
Defines mapping and labels for the daily sheet report
"""

# Arabic day names mapping
ARABIC_DAY_NAMES = {
    0: "الاثنين",    # Monday
    1: "الثلاثاء",   # Tuesday  
    2: "الأربعاء",   # Wednesday
    3: "الخميس",     # Thursday
    4: "الجمعة",     # Friday
    5: "السبت",      # Saturday
    6: "الأحد"       # Sunday
}

# Group 1 (Left block) column headers - 8 columns (RTL order)
GROUP_1_HEADERS = [
    "التوقيع",              # Signature
    "وقت الانصراف",         # Check-out time
    "التوقيع",              # Signature
    "وقت الحضور",           # Check-in time
    "اسم الكلب",            # Dog name
    "اسم الموظف البديل",    # Substitute employee name
    "اسم الموظف",           # Employee name
    "م"                     # Serial number
]

# Group 2 (Right block) column headers - 7 columns  
GROUP_2_HEADERS = [
    "م",                    # Serial number
    "اسم الموظف / البديل",  # Employee/Substitute name
    "اسم الكلب",            # Dog name
    "وقت الحضور",           # Check-in time
    "التوقيع",              # Signature
    "وقت الانصراف",         # Check-out time
    "التوقيع"               # Signature
]

# Leave table headers - 4 columns (RTL order)
LEAVE_TABLE_HEADERS = [
    "ملاحظة",                # Note
    "نوع الإجازة",          # Leave type
    "اسم الفرد المأجز",     # Name of person on leave
    "#"                     # Serial number
]

# Leave type Arabic mapping
LEAVE_TYPE_ARABIC = {
    "ANNUAL": "إجازة سنوية",
    "SICK": "إجازة مرضية", 
    "EMERGENCY": "إجازة طارئة",
    "OTHER": "أخرى"
}

# Report titles and labels
REPORT_LABELS = {
    "main_title": "كشف التحضير اليومي",
    "day_label": "اليوم:",
    "date_label": "التاريخ:",
    "leave_section_title": "أسماء المجازين ونوع الإجازة"
}

# Permission constants for this module
PERMISSION_KEYS = {
    "view": "reports:attendance:view",
    "export": "reports:attendance:export"
}