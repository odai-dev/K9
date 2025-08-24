"""
Constants and Arabic labels for training reports
"""

# Arabic labels for training categories
CATEGORY_LABELS_AR = {
    "OBEDIENCE": "الطاعة",
    "DETECTION": "الكشف", 
    "AGILITY": "الرشاقة",
    "ATTACK": "الهجوم",
    "FITNESS": "اللياقة"
}

# Arabic day names
DAY_NAMES_AR = {
    0: "الاثنين",
    1: "الثلاثاء", 
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد"
}

# Table headers for trainer daily report
TRAINER_DAILY_HEADERS = [
    "الوقت",
    "اسم المدرب", 
    "اسم الكلب",
    "الفئة",
    "الموضوع",
    "المدة (دقائق)",
    "تقييم النجاح /10",
    "الموقع",
    "الطقس", 
    "المعدات",
    "الملاحظات"
]

# Summary table headers
SUMMARY_HEADERS = [
    "اسم الكلب",
    "عدد الجلسات", 
    "إجمالي المدة (دقائق)",
    "متوسط التقييم",
    "تفصيل الفئات"
]