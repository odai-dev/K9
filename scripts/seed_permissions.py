"""
Seed script for the new permission system - Phase 1
Creates all permission keys (~85) in the system with Arabic and English names.

Run with: python scripts/seed_permissions.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission


PERMISSIONS_DATA = [
    # ============ DOGS (5) ============
    {
        "key": "dogs.view",
        "name": "View Dogs",
        "name_ar": "عرض الكلاب",
        "name_en": "View Dogs",
        "category": "dogs",
        "description": "View the list of dogs and their basic information",
        "sort_order": 1
    },
    {
        "key": "dogs.create",
        "name": "Create Dog",
        "name_ar": "إضافة كلب",
        "name_en": "Create Dog",
        "category": "dogs",
        "description": "Add a new dog to the system",
        "sort_order": 2
    },
    {
        "key": "dogs.edit",
        "name": "Edit Dog",
        "name_ar": "تعديل كلب",
        "name_en": "Edit Dog",
        "category": "dogs",
        "description": "Edit dog information and details",
        "sort_order": 3
    },
    {
        "key": "dogs.delete",
        "name": "Delete Dog",
        "name_ar": "حذف كلب",
        "name_en": "Delete Dog",
        "category": "dogs",
        "description": "Delete a dog from the system",
        "sort_order": 4
    },
    {
        "key": "dogs.assign",
        "name": "Assign Dog",
        "name_ar": "تعيين كلب",
        "name_en": "Assign Dog",
        "category": "dogs",
        "description": "Assign a dog to a project or handler",
        "sort_order": 5
    },

    # ============ EMPLOYEES (5) ============
    {
        "key": "employees.view",
        "name": "View Employees",
        "name_ar": "عرض الموظفين",
        "name_en": "View Employees",
        "category": "employees",
        "description": "View the list of employees and their basic information",
        "sort_order": 1
    },
    {
        "key": "employees.create",
        "name": "Create Employee",
        "name_ar": "إضافة موظف",
        "name_en": "Create Employee",
        "category": "employees",
        "description": "Add a new employee to the system",
        "sort_order": 2
    },
    {
        "key": "employees.edit",
        "name": "Edit Employee",
        "name_ar": "تعديل موظف",
        "name_en": "Edit Employee",
        "category": "employees",
        "description": "Edit employee information and details",
        "sort_order": 3
    },
    {
        "key": "employees.delete",
        "name": "Delete Employee",
        "name_ar": "حذف موظف",
        "name_en": "Delete Employee",
        "category": "employees",
        "description": "Delete an employee from the system",
        "sort_order": 4
    },
    {
        "key": "employees.assign",
        "name": "Assign Employee",
        "name_ar": "تعيين موظف",
        "name_en": "Assign Employee",
        "category": "employees",
        "description": "Assign an employee to a project",
        "sort_order": 5
    },

    # ============ PROJECTS (4) ============
    {
        "key": "projects.view",
        "name": "View Projects",
        "name_ar": "عرض المشاريع",
        "name_en": "View Projects",
        "category": "projects",
        "description": "View the list of projects and their details",
        "sort_order": 1
    },
    {
        "key": "projects.create",
        "name": "Create Project",
        "name_ar": "إنشاء مشروع",
        "name_en": "Create Project",
        "category": "projects",
        "description": "Create a new project",
        "sort_order": 2
    },
    {
        "key": "projects.edit",
        "name": "Edit Project",
        "name_ar": "تعديل مشروع",
        "name_en": "Edit Project",
        "category": "projects",
        "description": "Edit project information and settings",
        "sort_order": 3
    },
    {
        "key": "projects.delete",
        "name": "Delete Project",
        "name_ar": "حذف مشروع",
        "name_en": "Delete Project",
        "category": "projects",
        "description": "Delete a project from the system",
        "sort_order": 4
    },

    # ============ SCHEDULE/ATTENDANCE (5) ============
    {
        "key": "schedule.view",
        "name": "View Schedule",
        "name_ar": "عرض الجدول",
        "name_en": "View Schedule",
        "category": "schedule",
        "description": "View daily schedules and attendance",
        "sort_order": 1
    },
    {
        "key": "schedule.create",
        "name": "Create Schedule",
        "name_ar": "إنشاء جدول",
        "name_en": "Create Schedule",
        "category": "schedule",
        "description": "Create a new daily schedule",
        "sort_order": 2
    },
    {
        "key": "schedule.edit",
        "name": "Edit Schedule",
        "name_ar": "تعديل الجدول",
        "name_en": "Edit Schedule",
        "category": "schedule",
        "description": "Edit schedule items and assignments",
        "sort_order": 3
    },
    {
        "key": "schedule.delete",
        "name": "Delete Schedule",
        "name_ar": "حذف الجدول",
        "name_en": "Delete Schedule",
        "category": "schedule",
        "description": "Delete a schedule from the system",
        "sort_order": 4
    },
    {
        "key": "schedule.export",
        "name": "Export Schedule",
        "name_ar": "تصدير الجدول",
        "name_en": "Export Schedule",
        "category": "schedule",
        "description": "Export schedule to PDF or Excel",
        "sort_order": 5
    },

    # ============ TRAINING (5) ============
    {
        "key": "training.view",
        "name": "View Training",
        "name_ar": "عرض التدريب",
        "name_en": "View Training",
        "category": "training",
        "description": "View training records and sessions",
        "sort_order": 1
    },
    {
        "key": "training.create",
        "name": "Create Training",
        "name_ar": "إضافة تدريب",
        "name_en": "Create Training",
        "category": "training",
        "description": "Create a new training record",
        "sort_order": 2
    },
    {
        "key": "training.edit",
        "name": "Edit Training",
        "name_ar": "تعديل التدريب",
        "name_en": "Edit Training",
        "category": "training",
        "description": "Edit training record details",
        "sort_order": 3
    },
    {
        "key": "training.delete",
        "name": "Delete Training",
        "name_ar": "حذف التدريب",
        "name_en": "Delete Training",
        "category": "training",
        "description": "Delete a training record",
        "sort_order": 4
    },
    {
        "key": "training.export",
        "name": "Export Training",
        "name_ar": "تصدير التدريب",
        "name_en": "Export Training",
        "category": "training",
        "description": "Export training reports to PDF or Excel",
        "sort_order": 5
    },

    # ============ VETERINARY (5) ============
    {
        "key": "veterinary.view",
        "name": "View Veterinary",
        "name_ar": "عرض البيطرة",
        "name_en": "View Veterinary",
        "category": "veterinary",
        "description": "View veterinary records and visits",
        "sort_order": 1
    },
    {
        "key": "veterinary.create",
        "name": "Create Veterinary Record",
        "name_ar": "إضافة سجل بيطري",
        "name_en": "Create Veterinary Record",
        "category": "veterinary",
        "description": "Create a new veterinary record",
        "sort_order": 2
    },
    {
        "key": "veterinary.edit",
        "name": "Edit Veterinary Record",
        "name_ar": "تعديل السجل البيطري",
        "name_en": "Edit Veterinary Record",
        "category": "veterinary",
        "description": "Edit veterinary record details",
        "sort_order": 3
    },
    {
        "key": "veterinary.delete",
        "name": "Delete Veterinary Record",
        "name_ar": "حذف السجل البيطري",
        "name_en": "Delete Veterinary Record",
        "category": "veterinary",
        "description": "Delete a veterinary record",
        "sort_order": 4
    },
    {
        "key": "veterinary.export",
        "name": "Export Veterinary",
        "name_ar": "تصدير البيطرة",
        "name_en": "Export Veterinary",
        "category": "veterinary",
        "description": "Export veterinary reports to PDF or Excel",
        "sort_order": 5
    },

    # ============ BREEDING (11) ============
    {
        "key": "breeding.view",
        "name": "View Breeding",
        "name_ar": "عرض التربية",
        "name_en": "View Breeding",
        "category": "breeding",
        "description": "View breeding records and activities",
        "sort_order": 1
    },
    {
        "key": "breeding.create",
        "name": "Create Breeding Record",
        "name_ar": "إضافة سجل تربية",
        "name_en": "Create Breeding Record",
        "category": "breeding",
        "description": "Create a new breeding record",
        "sort_order": 2
    },
    {
        "key": "breeding.edit",
        "name": "Edit Breeding Record",
        "name_ar": "تعديل سجل التربية",
        "name_en": "Edit Breeding Record",
        "category": "breeding",
        "description": "Edit breeding record details",
        "sort_order": 3
    },
    {
        "key": "breeding.delete",
        "name": "Delete Breeding Record",
        "name_ar": "حذف سجل التربية",
        "name_en": "Delete Breeding Record",
        "category": "breeding",
        "description": "Delete a breeding record",
        "sort_order": 4
    },
    {
        "key": "breeding.export",
        "name": "Export Breeding",
        "name_ar": "تصدير التربية",
        "name_en": "Export Breeding",
        "category": "breeding",
        "description": "Export breeding reports to PDF or Excel",
        "sort_order": 5
    },
    {
        "key": "breeding.checkup",
        "name": "Breeding Checkup",
        "name_ar": "فحص التربية",
        "name_en": "Breeding Checkup",
        "category": "breeding",
        "description": "Manage breeding checkup records",
        "sort_order": 6
    },
    {
        "key": "breeding.excretion",
        "name": "Breeding Excretion",
        "name_ar": "إخراج التربية",
        "name_en": "Breeding Excretion",
        "category": "breeding",
        "description": "Manage breeding excretion records",
        "sort_order": 7
    },
    {
        "key": "breeding.deworming",
        "name": "Breeding Deworming",
        "name_ar": "تطهير التربية",
        "name_en": "Breeding Deworming",
        "category": "breeding",
        "description": "Manage breeding deworming records",
        "sort_order": 8
    },
    {
        "key": "breeding.grooming",
        "name": "Breeding Grooming",
        "name_ar": "تنظيف التربية",
        "name_en": "Breeding Grooming",
        "category": "breeding",
        "description": "Manage breeding grooming records",
        "sort_order": 9
    },
    {
        "key": "breeding.feeding",
        "name": "Breeding Feeding",
        "name_ar": "تغذية التربية",
        "name_en": "Breeding Feeding",
        "category": "breeding",
        "description": "Manage breeding feeding records",
        "sort_order": 10
    },
    {
        "key": "breeding.training",
        "name": "Breeding Training",
        "name_ar": "تدريب التربية",
        "name_en": "Breeding Training",
        "category": "breeding",
        "description": "Manage breeding training activities",
        "sort_order": 11
    },

    # ============ CLEANING (4) ============
    {
        "key": "cleaning.view",
        "name": "View Cleaning",
        "name_ar": "عرض التنظيف",
        "name_en": "View Cleaning",
        "category": "cleaning",
        "description": "View cleaning records",
        "sort_order": 1
    },
    {
        "key": "cleaning.create",
        "name": "Create Cleaning Record",
        "name_ar": "إنشاء سجل تنظيف",
        "name_en": "Create Cleaning Record",
        "category": "cleaning",
        "description": "Create a new cleaning record",
        "sort_order": 2
    },
    {
        "key": "cleaning.edit",
        "name": "Edit Cleaning Record",
        "name_ar": "تعديل سجل التنظيف",
        "name_en": "Edit Cleaning Record",
        "category": "cleaning",
        "description": "Edit cleaning record details",
        "sort_order": 3
    },
    {
        "key": "cleaning.delete",
        "name": "Delete Cleaning Record",
        "name_ar": "حذف سجل التنظيف",
        "name_en": "Delete Cleaning Record",
        "category": "cleaning",
        "description": "Delete a cleaning record",
        "sort_order": 4
    },

    # ============ HANDLER REPORTS (4) ============
    {
        "key": "handler_reports.view",
        "name": "View Handler Reports",
        "name_ar": "عرض تقارير السائسين",
        "name_en": "View Handler Reports",
        "category": "handler_reports",
        "description": "View handler daily and shift reports",
        "sort_order": 1
    },
    {
        "key": "handler_reports.submit",
        "name": "Submit Handler Report",
        "name_ar": "تقديم تقرير سائس",
        "name_en": "Submit Handler Report",
        "category": "handler_reports",
        "description": "Submit a handler daily or shift report",
        "sort_order": 2
    },
    {
        "key": "handler_reports.approve",
        "name": "Approve Handler Report",
        "name_ar": "اعتماد تقرير سائس",
        "name_en": "Approve Handler Report",
        "category": "handler_reports",
        "description": "Review and approve handler reports",
        "sort_order": 3
    },
    {
        "key": "handler_reports.export",
        "name": "Export Handler Reports",
        "name_ar": "تصدير تقارير السائسين",
        "name_en": "Export Handler Reports",
        "category": "handler_reports",
        "description": "Export handler reports to PDF or Excel",
        "sort_order": 4
    },

    # ============ TASKS (6) ============
    {
        "key": "tasks.view",
        "name": "View Tasks",
        "name_ar": "عرض المهام",
        "name_en": "View Tasks",
        "category": "tasks",
        "description": "View the list of tasks",
        "sort_order": 1
    },
    {
        "key": "tasks.create",
        "name": "Create Task",
        "name_ar": "إنشاء مهمة",
        "name_en": "Create Task",
        "category": "tasks",
        "description": "Create a new task",
        "sort_order": 2
    },
    {
        "key": "tasks.edit",
        "name": "Edit Task",
        "name_ar": "تعديل مهمة",
        "name_en": "Edit Task",
        "category": "tasks",
        "description": "Edit task details",
        "sort_order": 3
    },
    {
        "key": "tasks.delete",
        "name": "Delete Task",
        "name_ar": "حذف مهمة",
        "name_en": "Delete Task",
        "category": "tasks",
        "description": "Delete a task",
        "sort_order": 4
    },
    {
        "key": "tasks.assign",
        "name": "Assign Task",
        "name_ar": "تعيين مهمة",
        "name_en": "Assign Task",
        "category": "tasks",
        "description": "Assign a task to an employee",
        "sort_order": 5
    },
    {
        "key": "tasks.approve",
        "name": "Approve Task",
        "name_ar": "اعتماد مهمة",
        "name_en": "Approve Task",
        "category": "tasks",
        "description": "Approve task completion",
        "sort_order": 6
    },

    # ============ ACCOUNTS (4) ============
    {
        "key": "accounts.view",
        "name": "View Accounts",
        "name_ar": "عرض الحسابات",
        "name_en": "View Accounts",
        "category": "accounts",
        "description": "View user accounts",
        "sort_order": 1
    },
    {
        "key": "accounts.create",
        "name": "Create Account",
        "name_ar": "إنشاء حساب",
        "name_en": "Create Account",
        "category": "accounts",
        "description": "Create a new user account",
        "sort_order": 2
    },
    {
        "key": "accounts.edit",
        "name": "Edit Account",
        "name_ar": "تعديل حساب",
        "name_en": "Edit Account",
        "category": "accounts",
        "description": "Edit user account details",
        "sort_order": 3
    },
    {
        "key": "accounts.delete",
        "name": "Delete Account",
        "name_ar": "حذف حساب",
        "name_en": "Delete Account",
        "category": "accounts",
        "description": "Delete a user account",
        "sort_order": 4
    },

    # ============ REPORTS - ATTENDANCE (2) ============
    {
        "key": "reports.attendance.view",
        "name": "View Attendance Reports",
        "name_ar": "عرض تقارير الحضور",
        "name_en": "View Attendance Reports",
        "category": "reports.attendance",
        "description": "View attendance reports",
        "sort_order": 1
    },
    {
        "key": "reports.attendance.export",
        "name": "Export Attendance Reports",
        "name_ar": "تصدير تقارير الحضور",
        "name_en": "Export Attendance Reports",
        "category": "reports.attendance",
        "description": "Export attendance reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - TRAINING (2) ============
    {
        "key": "reports.training.view",
        "name": "View Training Reports",
        "name_ar": "عرض تقارير التدريب",
        "name_en": "View Training Reports",
        "category": "reports.training",
        "description": "View training reports",
        "sort_order": 1
    },
    {
        "key": "reports.training.export",
        "name": "Export Training Reports",
        "name_ar": "تصدير تقارير التدريب",
        "name_en": "Export Training Reports",
        "category": "reports.training",
        "description": "Export training reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - VETERINARY (2) ============
    {
        "key": "reports.veterinary.view",
        "name": "View Veterinary Reports",
        "name_ar": "عرض التقارير البيطرية",
        "name_en": "View Veterinary Reports",
        "category": "reports.veterinary",
        "description": "View veterinary reports",
        "sort_order": 1
    },
    {
        "key": "reports.veterinary.export",
        "name": "Export Veterinary Reports",
        "name_ar": "تصدير التقارير البيطرية",
        "name_en": "Export Veterinary Reports",
        "category": "reports.veterinary",
        "description": "Export veterinary reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - BREEDING FEEDING (2) ============
    {
        "key": "reports.breeding.feeding.view",
        "name": "View Breeding Feeding Reports",
        "name_ar": "عرض تقارير تغذية التربية",
        "name_en": "View Breeding Feeding Reports",
        "category": "reports.breeding.feeding",
        "description": "View breeding feeding reports",
        "sort_order": 1
    },
    {
        "key": "reports.breeding.feeding.export",
        "name": "Export Breeding Feeding Reports",
        "name_ar": "تصدير تقارير تغذية التربية",
        "name_en": "Export Breeding Feeding Reports",
        "category": "reports.breeding.feeding",
        "description": "Export breeding feeding reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - BREEDING CHECKUP (2) ============
    {
        "key": "reports.breeding.checkup.view",
        "name": "View Breeding Checkup Reports",
        "name_ar": "عرض تقارير فحص التربية",
        "name_en": "View Breeding Checkup Reports",
        "category": "reports.breeding.checkup",
        "description": "View breeding checkup reports",
        "sort_order": 1
    },
    {
        "key": "reports.breeding.checkup.export",
        "name": "Export Breeding Checkup Reports",
        "name_ar": "تصدير تقارير فحص التربية",
        "name_en": "Export Breeding Checkup Reports",
        "category": "reports.breeding.checkup",
        "description": "Export breeding checkup reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - CARETAKER (2) ============
    {
        "key": "reports.caretaker.view",
        "name": "View Caretaker Reports",
        "name_ar": "عرض تقارير العناية",
        "name_en": "View Caretaker Reports",
        "category": "reports.caretaker",
        "description": "View caretaker daily reports",
        "sort_order": 1
    },
    {
        "key": "reports.caretaker.export",
        "name": "Export Caretaker Reports",
        "name_ar": "تصدير تقارير العناية",
        "name_en": "Export Caretaker Reports",
        "category": "reports.caretaker",
        "description": "Export caretaker reports to PDF or Excel",
        "sort_order": 2
    },

    # ============ REPORTS - DETAILED SUB-CATEGORIES (8) ============
    {
        "key": "reports.attendance.pm_daily.view",
        "name": "View PM Daily Attendance Reports",
        "name_ar": "عرض تقارير حضور مدير المشروع اليومية",
        "name_en": "View PM Daily Attendance Reports",
        "category": "reports.attendance",
        "description": "View PM daily attendance reports",
        "sort_order": 10
    },
    {
        "key": "reports.attendance.pm_daily.export",
        "name": "Export PM Daily Attendance Reports",
        "name_ar": "تصدير تقارير حضور مدير المشروع",
        "name_en": "Export PM Daily Attendance Reports",
        "category": "reports.attendance",
        "description": "Export PM daily attendance reports to PDF or Excel",
        "sort_order": 11
    },
    {
        "key": "reports.breeding.caretaker_daily.view",
        "name": "View Caretaker Daily Reports",
        "name_ar": "عرض تقارير العناية اليومية",
        "name_en": "View Caretaker Daily Reports",
        "category": "reports.breeding",
        "description": "View caretaker daily breeding reports",
        "sort_order": 10
    },
    {
        "key": "reports.breeding.caretaker_daily.export",
        "name": "Export Caretaker Daily Reports",
        "name_ar": "تصدير تقارير العناية اليومية",
        "name_en": "Export Caretaker Daily Reports",
        "category": "reports.breeding",
        "description": "Export caretaker daily reports to PDF or Excel",
        "sort_order": 11
    },
    {
        "key": "reports.training.trainer_daily.view",
        "name": "View Trainer Daily Reports",
        "name_ar": "عرض تقارير المدرب اليومية",
        "name_en": "View Trainer Daily Reports",
        "category": "reports.training",
        "description": "View trainer daily training reports",
        "sort_order": 10
    },
    {
        "key": "reports.training.trainer_daily.export",
        "name": "Export Trainer Daily Reports",
        "name_ar": "تصدير تقارير المدرب اليومية",
        "name_en": "Export Trainer Daily Reports",
        "category": "reports.training",
        "description": "Export trainer daily reports to PDF or Excel",
        "sort_order": 11
    },
    {
        "key": "reports.breeding.checkup.view",
        "name": "View Breeding Checkup Reports",
        "name_ar": "عرض تقارير فحص التربية",
        "name_en": "View Breeding Checkup Reports",
        "category": "reports.breeding",
        "description": "View breeding checkup reports",
        "sort_order": 12
    },
    {
        "key": "reports.breeding.checkup.export",
        "name": "Export Breeding Checkup Reports",
        "name_ar": "تصدير تقارير فحص التربية",
        "name_en": "Export Breeding Checkup Reports",
        "category": "reports.breeding",
        "description": "Export breeding checkup reports to PDF or Excel",
        "sort_order": 13
    },

    # ============ ADMIN (6) ============
    {
        "key": "admin.dashboard",
        "name": "Admin Dashboard",
        "name_ar": "لوحة تحكم المسؤول",
        "name_en": "Admin Dashboard",
        "category": "admin",
        "description": "Access the admin dashboard",
        "sort_order": 1
    },
    {
        "key": "admin.permissions.view",
        "name": "View Permissions",
        "name_ar": "عرض الصلاحيات",
        "name_en": "View Permissions",
        "category": "admin",
        "description": "View user permissions",
        "sort_order": 2
    },
    {
        "key": "admin.permissions.edit",
        "name": "Edit Permissions",
        "name_ar": "تعديل الصلاحيات",
        "name_en": "Edit Permissions",
        "category": "admin",
        "description": "Modify user permissions",
        "sort_order": 3
    },
    {
        "key": "admin.backup",
        "name": "Backup Management",
        "name_ar": "إدارة النسخ الاحتياطية",
        "name_en": "Backup Management",
        "category": "admin",
        "description": "Manage system backups",
        "sort_order": 4
    },
    {
        "key": "admin.settings",
        "name": "System Settings",
        "name_ar": "إعدادات النظام",
        "name_en": "System Settings",
        "category": "admin",
        "description": "Manage system settings",
        "sort_order": 5
    },
    {
        "key": "admin.audit",
        "name": "Audit Logs",
        "name_ar": "سجلات المراجعة",
        "name_en": "Audit Logs",
        "category": "admin",
        "description": "View system audit logs",
        "sort_order": 6
    },

    # ============ SHIFTS (4) ============
    {
        "key": "shifts.view",
        "name": "View Shifts",
        "name_ar": "عرض الورديات",
        "name_en": "View Shifts",
        "category": "shifts",
        "description": "View shift schedules",
        "sort_order": 1
    },
    {
        "key": "shifts.create",
        "name": "Create Shift",
        "name_ar": "إنشاء وردية",
        "name_en": "Create Shift",
        "category": "shifts",
        "description": "Create a new shift",
        "sort_order": 2
    },
    {
        "key": "shifts.edit",
        "name": "Edit Shift",
        "name_ar": "تعديل وردية",
        "name_en": "Edit Shift",
        "category": "shifts",
        "description": "Edit shift details",
        "sort_order": 3
    },
    {
        "key": "shifts.delete",
        "name": "Delete Shift",
        "name_ar": "حذف وردية",
        "name_en": "Delete Shift",
        "category": "shifts",
        "description": "Delete a shift",
        "sort_order": 4
    },

    # ============ INCIDENTS (4) ============
    {
        "key": "incidents.view",
        "name": "View Incidents",
        "name_ar": "عرض الحوادث",
        "name_en": "View Incidents",
        "category": "incidents",
        "description": "View incident reports",
        "sort_order": 1
    },
    {
        "key": "incidents.create",
        "name": "Create Incident",
        "name_ar": "إنشاء حادثة",
        "name_en": "Create Incident",
        "category": "incidents",
        "description": "Create a new incident report",
        "sort_order": 2
    },
    {
        "key": "incidents.edit",
        "name": "Edit Incident",
        "name_ar": "تعديل حادثة",
        "name_en": "Edit Incident",
        "category": "incidents",
        "description": "Edit incident report details",
        "sort_order": 3
    },
    {
        "key": "incidents.delete",
        "name": "Delete Incident",
        "name_ar": "حذف حادثة",
        "name_en": "Delete Incident",
        "category": "incidents",
        "description": "Delete an incident report",
        "sort_order": 4
    },
    {
        "key": "incidents.resolve",
        "name": "Resolve Incident",
        "name_ar": "حل الحادثة",
        "name_en": "Resolve Incident",
        "category": "incidents",
        "description": "Mark an incident as resolved",
        "sort_order": 5
    },

    # ============ SUSPICIONS (5) ============
    {
        "key": "suspicions.view",
        "name": "View Suspicions",
        "name_ar": "عرض الاشتباهات",
        "name_en": "View Suspicions",
        "category": "suspicions",
        "description": "View suspicion reports",
        "sort_order": 1
    },
    {
        "key": "suspicions.create",
        "name": "Create Suspicion",
        "name_ar": "إنشاء اشتباه",
        "name_en": "Create Suspicion",
        "category": "suspicions",
        "description": "Create a new suspicion report",
        "sort_order": 2
    },
    {
        "key": "suspicions.edit",
        "name": "Edit Suspicion",
        "name_ar": "تعديل اشتباه",
        "name_en": "Edit Suspicion",
        "category": "suspicions",
        "description": "Edit suspicion report details",
        "sort_order": 3
    },
    {
        "key": "suspicions.delete",
        "name": "Delete Suspicion",
        "name_ar": "حذف اشتباه",
        "name_en": "Delete Suspicion",
        "category": "suspicions",
        "description": "Delete a suspicion report",
        "sort_order": 4
    },
    {
        "key": "suspicions.close",
        "name": "Close Suspicion",
        "name_ar": "إغلاق اشتباه",
        "name_en": "Close Suspicion",
        "category": "suspicions",
        "description": "Close a suspicion case",
        "sort_order": 5
    },

    # ============ EVALUATIONS (5) ============
    {
        "key": "evaluations.view",
        "name": "View Evaluations",
        "name_ar": "عرض التقييمات",
        "name_en": "View Evaluations",
        "category": "evaluations",
        "description": "View evaluation records",
        "sort_order": 1
    },
    {
        "key": "evaluations.create",
        "name": "Create Evaluation",
        "name_ar": "إنشاء تقييم",
        "name_en": "Create Evaluation",
        "category": "evaluations",
        "description": "Create a new evaluation",
        "sort_order": 2
    },
    {
        "key": "evaluations.edit",
        "name": "Edit Evaluation",
        "name_ar": "تعديل تقييم",
        "name_en": "Edit Evaluation",
        "category": "evaluations",
        "description": "Edit evaluation details",
        "sort_order": 3
    },
    {
        "key": "evaluations.delete",
        "name": "Delete Evaluation",
        "name_ar": "حذف تقييم",
        "name_en": "Delete Evaluation",
        "category": "evaluations",
        "description": "Delete an evaluation record",
        "sort_order": 4
    },
    {
        "key": "evaluations.approve",
        "name": "Approve Evaluation",
        "name_ar": "اعتماد تقييم",
        "name_en": "Approve Evaluation",
        "category": "evaluations",
        "description": "Approve an evaluation",
        "sort_order": 5
    },

    # ============ SUPERVISOR (5) ============
    {
        "key": "supervisor.schedules",
        "name": "Supervisor Schedules",
        "name_ar": "جداول المشرف",
        "name_en": "Supervisor Schedules",
        "category": "supervisor",
        "description": "Manage supervisor schedules",
        "sort_order": 1
    },
    {
        "key": "supervisor.reports.view",
        "name": "Supervisor View Reports",
        "name_ar": "عرض تقارير المشرف",
        "name_en": "Supervisor View Reports",
        "category": "supervisor",
        "description": "View supervisor reports",
        "sort_order": 2
    },
    {
        "key": "supervisor.reports",
        "name": "Supervisor Reports",
        "name_ar": "تقارير المشرف",
        "name_en": "Supervisor Reports",
        "category": "supervisor",
        "description": "View and manage supervisor reports",
        "sort_order": 3
    },
    {
        "key": "supervisor.approve",
        "name": "Supervisor Approve",
        "name_ar": "اعتماد المشرف",
        "name_en": "Supervisor Approve",
        "category": "supervisor",
        "description": "Approve reports as supervisor",
        "sort_order": 4
    },
    {
        "key": "supervisor.dashboard",
        "name": "Supervisor Dashboard",
        "name_ar": "لوحة المشرف",
        "name_en": "Supervisor Dashboard",
        "category": "supervisor",
        "description": "Access supervisor dashboard",
        "sort_order": 5
    },

    # ============ PM - PROJECT MANAGER (15) ============
    {
        "key": "pm.dashboard",
        "name": "PM Dashboard",
        "name_ar": "لوحة مدير المشروع",
        "name_en": "PM Dashboard",
        "category": "pm",
        "description": "Access project manager dashboard",
        "sort_order": 1
    },
    {
        "key": "pm.team.view",
        "name": "PM View Team",
        "name_ar": "عرض فريق المشروع",
        "name_en": "PM View Team",
        "category": "pm",
        "description": "View project team members",
        "sort_order": 2
    },
    {
        "key": "pm.project.view",
        "name": "PM View Project",
        "name_ar": "عرض تفاصيل المشروع",
        "name_en": "PM View Project",
        "category": "pm",
        "description": "View project details and settings",
        "sort_order": 3
    },
    {
        "key": "pm.dogs",
        "name": "PM Dogs",
        "name_ar": "كلاب المشروع",
        "name_en": "PM Dogs",
        "category": "pm",
        "description": "View and manage project dogs",
        "sort_order": 4
    },
    {
        "key": "pm.approvals.view",
        "name": "PM View Approvals",
        "name_ar": "عرض الموافقات",
        "name_en": "PM View Approvals",
        "category": "pm",
        "description": "View pending reports for approval",
        "sort_order": 5
    },
    {
        "key": "pm.reports.view",
        "name": "PM View Reports",
        "name_ar": "عرض التقارير",
        "name_en": "PM View Reports",
        "category": "pm",
        "description": "View submitted reports",
        "sort_order": 6
    },
    {
        "key": "pm.reports.approve",
        "name": "PM Approve Reports",
        "name_ar": "اعتماد التقارير",
        "name_en": "PM Approve Reports",
        "category": "pm",
        "description": "Approve handler and staff reports",
        "sort_order": 7
    },
    {
        "key": "pm.reports.reject",
        "name": "PM Reject Reports",
        "name_ar": "رفض التقارير",
        "name_en": "PM Reject Reports",
        "category": "pm",
        "description": "Reject handler and staff reports",
        "sort_order": 8
    },
    {
        "key": "pm.reports.request_edit",
        "name": "PM Request Report Edits",
        "name_ar": "طلب تعديل التقارير",
        "name_en": "PM Request Report Edits",
        "category": "pm",
        "description": "Request edits on submitted reports",
        "sort_order": 9
    },
    {
        "key": "pm.reports.export",
        "name": "PM Export Reports",
        "name_ar": "تصدير التقارير",
        "name_en": "PM Export Reports",
        "category": "pm",
        "description": "Export reports to PDF or Excel",
        "sort_order": 10
    },
    {
        "key": "pm.incidents.view",
        "name": "PM View Incidents",
        "name_ar": "عرض الحوادث",
        "name_en": "PM View Incidents",
        "category": "pm",
        "description": "View project incidents",
        "sort_order": 11
    },
    {
        "key": "pm.incidents.create",
        "name": "PM Create Incidents",
        "name_ar": "إنشاء حوادث",
        "name_en": "PM Create Incidents",
        "category": "pm",
        "description": "Create incident reports",
        "sort_order": 12
    },
    {
        "key": "pm.schedules.view",
        "name": "PM View Schedules",
        "name_ar": "عرض الجداول",
        "name_en": "PM View Schedules",
        "category": "pm",
        "description": "View project schedules",
        "sort_order": 13
    },
    {
        "key": "pm.schedules.create",
        "name": "PM Create Schedules",
        "name_ar": "إنشاء جداول",
        "name_en": "PM Create Schedules",
        "category": "pm",
        "description": "Create project schedules",
        "sort_order": 14
    },
    {
        "key": "pm.schedules.edit",
        "name": "PM Edit Schedules",
        "name_ar": "تعديل الجداول",
        "name_en": "PM Edit Schedules",
        "category": "pm",
        "description": "Edit project schedules",
        "sort_order": 15
    },

    # ============ HANDLERS - السائسين (10) ============
    {
        "key": "handlers.general.access",
        "name": "Handler General Access",
        "name_ar": "وصول عام للسائس",
        "name_en": "Handler General Access",
        "category": "handlers",
        "description": "General access for handler role",
        "sort_order": 1
    },
    {
        "key": "handlers.dashboard",
        "name": "Handler Dashboard",
        "name_ar": "لوحة السائس",
        "name_en": "Handler Dashboard",
        "category": "handlers",
        "description": "Access handler dashboard",
        "sort_order": 2
    },
    {
        "key": "handlers.reports.view",
        "name": "Handler View Reports",
        "name_ar": "عرض تقارير السائس",
        "name_en": "Handler View Reports",
        "category": "handlers",
        "description": "View own reports",
        "sort_order": 3
    },
    {
        "key": "handlers.reports.create",
        "name": "Handler Create Reports",
        "name_ar": "إنشاء تقارير السائس",
        "name_en": "Handler Create Reports",
        "category": "handlers",
        "description": "Create daily and shift reports",
        "sort_order": 4
    },
    {
        "key": "handlers.reports.edit",
        "name": "Handler Edit Reports",
        "name_ar": "تعديل تقارير السائس",
        "name_en": "Handler Edit Reports",
        "category": "handlers",
        "description": "Edit own draft reports",
        "sort_order": 5
    },
    {
        "key": "handlers.reports.delete",
        "name": "Handler Delete Reports",
        "name_ar": "حذف تقارير السائس",
        "name_en": "Handler Delete Reports",
        "category": "handlers",
        "description": "Delete own draft reports",
        "sort_order": 6
    },
    {
        "key": "handlers.reports.submit",
        "name": "Handler Submit Reports",
        "name_ar": "تقديم تقارير السائس",
        "name_en": "Handler Submit Reports",
        "category": "handlers",
        "description": "Submit reports for approval",
        "sort_order": 7
    },
    {
        "key": "handlers.notifications.view",
        "name": "Handler View Notifications",
        "name_ar": "عرض إشعارات السائس",
        "name_en": "Handler View Notifications",
        "category": "handlers",
        "description": "View handler notifications",
        "sort_order": 8
    },
    {
        "key": "handlers.profile.view",
        "name": "Handler View Profile",
        "name_ar": "عرض ملف السائس",
        "name_en": "Handler View Profile",
        "category": "handlers",
        "description": "View and edit own profile",
        "sort_order": 9
    },
    {
        "key": "handlers.schedule.view",
        "name": "Handler View Schedule",
        "name_ar": "عرض جدول السائس",
        "name_en": "Handler View Schedule",
        "category": "handlers",
        "description": "View own daily schedule",
        "sort_order": 10
    },

    # ============ NOTIFICATIONS (2) ============
    {
        "key": "notifications.view",
        "name": "View Notifications",
        "name_ar": "عرض الإشعارات",
        "name_en": "View Notifications",
        "category": "notifications",
        "description": "View system notifications",
        "sort_order": 1
    },
    {
        "key": "notifications.manage",
        "name": "Manage Notifications",
        "name_ar": "إدارة الإشعارات",
        "name_en": "Manage Notifications",
        "category": "notifications",
        "description": "Manage notification settings",
        "sort_order": 2
    },

    # ============ PRODUCTION/BREEDING CYCLES (5) ============
    {
        "key": "production.view",
        "name": "View Production",
        "name_ar": "عرض الإنتاج",
        "name_en": "View Production",
        "category": "production",
        "description": "View production and breeding cycles",
        "sort_order": 1
    },
    {
        "key": "production.create",
        "name": "Create Production Record",
        "name_ar": "إنشاء سجل إنتاج",
        "name_en": "Create Production Record",
        "category": "production",
        "description": "Create a new production record",
        "sort_order": 2
    },
    {
        "key": "production.edit",
        "name": "Edit Production Record",
        "name_ar": "تعديل سجل الإنتاج",
        "name_en": "Edit Production Record",
        "category": "production",
        "description": "Edit production record details",
        "sort_order": 3
    },
    {
        "key": "production.delete",
        "name": "Delete Production Record",
        "name_ar": "حذف سجل الإنتاج",
        "name_en": "Delete Production Record",
        "category": "production",
        "description": "Delete a production record",
        "sort_order": 4
    },
    {
        "key": "production.export",
        "name": "Export Production",
        "name_ar": "تصدير الإنتاج",
        "name_en": "Export Production",
        "category": "production",
        "description": "Export production reports to PDF or Excel",
        "sort_order": 5
    },

    # ============ ACCOUNT MANAGEMENT (5) ============
    {
        "key": "account_management.index.view",
        "name": "View Account Management",
        "name_ar": "عرض إدارة الحسابات",
        "name_en": "View Account Management",
        "category": "account_management",
        "description": "View account management page",
        "sort_order": 1
    },
    {
        "key": "account_management.create.access",
        "name": "Create Account Access",
        "name_ar": "إنشاء حساب مستخدم",
        "name_en": "Create Account Access",
        "category": "account_management",
        "description": "Create new user accounts",
        "sort_order": 2
    },
    {
        "key": "account_management.reset_password.access",
        "name": "Reset Password Access",
        "name_ar": "إعادة تعيين كلمة المرور",
        "name_en": "Reset Password Access",
        "category": "account_management",
        "description": "Reset user passwords",
        "sort_order": 3
    },
    {
        "key": "account_management.toggle_status.access",
        "name": "Toggle Account Status",
        "name_ar": "تفعيل/تعطيل الحساب",
        "name_en": "Toggle Account Status",
        "category": "account_management",
        "description": "Enable or disable user accounts",
        "sort_order": 4
    },
    {
        "key": "account_management.api.access",
        "name": "Account Management API",
        "name_ar": "واجهة إدارة الحسابات",
        "name_en": "Account Management API",
        "category": "account_management",
        "description": "Access account management API endpoints",
        "sort_order": 5
    },

    # ============ MFA - Two Factor Authentication (6) ============
    {
        "key": "mfa.setup.access",
        "name": "MFA Setup Access",
        "name_ar": "إعداد المصادقة الثنائية",
        "name_en": "MFA Setup Access",
        "category": "mfa",
        "description": "Setup two-factor authentication",
        "sort_order": 1
    },
    {
        "key": "mfa.disable.access",
        "name": "MFA Disable Access",
        "name_ar": "تعطيل المصادقة الثنائية",
        "name_en": "MFA Disable Access",
        "category": "mfa",
        "description": "Disable two-factor authentication",
        "sort_order": 2
    },
    {
        "key": "mfa.status.view",
        "name": "MFA Status View",
        "name_ar": "عرض حالة المصادقة",
        "name_en": "MFA Status View",
        "category": "mfa",
        "description": "View MFA status",
        "sort_order": 3
    },
    {
        "key": "mfa.backup_codes.regenerate",
        "name": "Regenerate Backup Codes",
        "name_ar": "إعادة إنشاء أكواد الطوارئ",
        "name_en": "Regenerate Backup Codes",
        "category": "mfa",
        "description": "Regenerate MFA backup codes",
        "sort_order": 4
    },
    {
        "key": "mfa.password.change",
        "name": "Change Password",
        "name_ar": "تغيير كلمة المرور",
        "name_en": "Change Password",
        "category": "mfa",
        "description": "Change user password",
        "sort_order": 5
    },
    {
        "key": "password_reset.reset.access",
        "name": "Password Reset Access",
        "name_ar": "إعادة تعيين كلمة المرور",
        "name_en": "Password Reset Access",
        "category": "mfa",
        "description": "Access password reset functionality",
        "sort_order": 6
    },

    # ============ GENERAL & API ACCESS (4) ============
    {
        "key": "general.access",
        "name": "General Access",
        "name_ar": "الوصول العام",
        "name_en": "General Access",
        "category": "general",
        "description": "General system access",
        "sort_order": 1
    },
    {
        "key": "api.dashboard.access",
        "name": "Dashboard API Access",
        "name_ar": "وصول واجهة لوحة التحكم",
        "name_en": "Dashboard API Access",
        "category": "general",
        "description": "Access dashboard API endpoints",
        "sort_order": 2
    },
    {
        "key": "search.global.access",
        "name": "Global Search Access",
        "name_ar": "البحث الشامل",
        "name_en": "Global Search Access",
        "category": "general",
        "description": "Access global search functionality",
        "sort_order": 3
    },
    {
        "key": "auth.create_manager.access",
        "name": "Create Manager Access",
        "name_ar": "إنشاء مدير",
        "name_en": "Create Manager Access",
        "category": "general",
        "description": "Create new project managers",
        "sort_order": 4
    },

    # ============ ADMIN EXTENDED (3) ============
    {
        "key": "admin.general.access",
        "name": "Admin General Access",
        "name_ar": "وصول المسؤول العام",
        "name_en": "Admin General Access",
        "category": "admin",
        "description": "General admin access",
        "sort_order": 10
    },
    {
        "key": "admin.notifications.view",
        "name": "Admin View Notifications",
        "name_ar": "عرض إشعارات المسؤول",
        "name_en": "Admin View Notifications",
        "category": "admin",
        "description": "View admin notifications",
        "sort_order": 11
    },
    {
        "key": "admin.google_drive.manage",
        "name": "Manage Google Drive",
        "name_ar": "إدارة Google Drive",
        "name_en": "Manage Google Drive",
        "category": "admin",
        "description": "Manage Google Drive backup settings",
        "sort_order": 12
    },

    # ============ REPORTS - GENERAL & EXTENDED (5) ============
    {
        "key": "admin.reports.view_pending",
        "name": "View Pending Reports",
        "name_ar": "عرض التقارير المعلقة",
        "name_en": "View Pending Reports",
        "category": "admin",
        "description": "View pending reports for final approval",
        "sort_order": 13
    },
    {
        "key": "reports.general.view",
        "name": "View General Reports",
        "name_ar": "عرض التقارير العامة",
        "name_en": "View General Reports",
        "category": "reports.general",
        "description": "View general reports",
        "sort_order": 1
    },
    {
        "key": "reports.veterinary.legacy.access",
        "name": "Veterinary Legacy Reports",
        "name_ar": "التقارير البيطرية القديمة",
        "name_en": "Veterinary Legacy Reports",
        "category": "reports.veterinary",
        "description": "Access legacy veterinary reports",
        "sort_order": 10
    },

    # ============ TRAINING SESSIONS (1) ============
    {
        "key": "training.sessions.view",
        "name": "View Training Sessions",
        "name_ar": "عرض جلسات التدريب",
        "name_en": "View Training Sessions",
        "category": "training",
        "description": "View training sessions",
        "sort_order": 10
    },

    # ============ ADMIN BACKUP (1) ============
    {
        "key": "admin.backup.manage",
        "name": "Manage Backups",
        "name_ar": "إدارة النسخ الاحتياطية",
        "name_en": "Manage Backups",
        "category": "admin",
        "description": "Create, restore, and manage system backups",
        "sort_order": 14
    },

    # ============ BREEDING DETAILED REPORTS (4) ============
    {
        "key": "reports.breeding.feeding.daily.view",
        "name": "View Daily Feeding Reports",
        "name_ar": "عرض تقارير التغذية اليومية",
        "name_en": "View Daily Feeding Reports",
        "category": "reports.breeding",
        "description": "View daily breeding feeding reports",
        "sort_order": 20
    },
    {
        "key": "reports.breeding.feeding.weekly.view",
        "name": "View Weekly Feeding Reports",
        "name_ar": "عرض تقارير التغذية الأسبوعية",
        "name_en": "View Weekly Feeding Reports",
        "category": "reports.breeding",
        "description": "View weekly breeding feeding reports",
        "sort_order": 21
    },
    {
        "key": "reports.breeding.checkup.daily.view",
        "name": "View Daily Checkup Reports",
        "name_ar": "عرض تقارير الفحص اليومية",
        "name_en": "View Daily Checkup Reports",
        "category": "reports.breeding",
        "description": "View daily breeding checkup reports",
        "sort_order": 22
    },
    {
        "key": "reports.breeding.checkup.weekly.view",
        "name": "View Weekly Checkup Reports",
        "name_ar": "عرض تقارير الفحص الأسبوعية",
        "name_en": "View Weekly Checkup Reports",
        "category": "reports.breeding",
        "description": "View weekly breeding checkup reports",
        "sort_order": 23
    },

    # ============ BREEDING DETAILED ACTIVITY (3) ============
    {
        "key": "breeding.deworming.view",
        "name": "View Deworming Records",
        "name_ar": "عرض سجلات التطهير",
        "name_en": "View Deworming Records",
        "category": "breeding",
        "description": "View breeding deworming records",
        "sort_order": 20
    },
    {
        "key": "breeding.deworming.create",
        "name": "Create Deworming Records",
        "name_ar": "إنشاء سجلات التطهير",
        "name_en": "Create Deworming Records",
        "category": "breeding",
        "description": "Create breeding deworming records",
        "sort_order": 21
    },
    {
        "key": "breeding.deworming.edit",
        "name": "Edit Deworming Records",
        "name_ar": "تعديل سجلات التطهير",
        "name_en": "Edit Deworming Records",
        "category": "breeding",
        "description": "Edit breeding deworming records",
        "sort_order": 22
    },
]


def seed_permissions():
    """Seed all permissions into the database with upsert logic."""
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    print("=" * 60)
    print("Permission System Seeding - Phase 1")
    print("=" * 60)
    print(f"\nProcessing {len(PERMISSIONS_DATA)} permissions...\n")
    
    for perm_data in PERMISSIONS_DATA:
        existing = Permission.query.filter_by(key=perm_data['key']).first()
        
        if existing:
            changed = False
            if existing.name != perm_data['name']:
                existing.name = perm_data['name']
                changed = True
            if existing.name_ar != perm_data['name_ar']:
                existing.name_ar = perm_data['name_ar']
                changed = True
            if existing.name_en != perm_data['name_en']:
                existing.name_en = perm_data['name_en']
                changed = True
            if existing.description != perm_data['description']:
                existing.description = perm_data['description']
                changed = True
            if existing.category != perm_data['category']:
                existing.category = perm_data['category']
                changed = True
            if existing.sort_order != perm_data['sort_order']:
                existing.sort_order = perm_data['sort_order']
                changed = True
            
            if changed:
                updated_count += 1
                print(f"  Updated: {perm_data['key']}")
            else:
                skipped_count += 1
        else:
            new_perm = Permission(
                key=perm_data['key'],
                name=perm_data['name'],
                name_ar=perm_data['name_ar'],
                name_en=perm_data['name_en'],
                description=perm_data['description'],
                category=perm_data['category'],
                sort_order=perm_data['sort_order'],
                is_active=True
            )
            db.session.add(new_perm)
            created_count += 1
            print(f"  Created: {perm_data['key']}")
    
    db.session.commit()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Created: {created_count} new permissions")
    print(f"  Updated: {updated_count} existing permissions")
    print(f"  Skipped: {skipped_count} unchanged permissions")
    print(f"  Total:   {len(PERMISSIONS_DATA)} permissions processed")
    print("=" * 60)
    
    total_in_db = Permission.query.count()
    print(f"\nTotal permissions in database: {total_in_db}")
    
    categories = db.session.query(Permission.category).distinct().all()
    print(f"\nCategories ({len(categories)}):")
    for cat in sorted(categories):
        count = Permission.query.filter_by(category=cat[0]).count()
        print(f"  - {cat[0]}: {count} permissions")
    
    return created_count, updated_count, skipped_count


if __name__ == '__main__':
    with app.app_context():
        seed_permissions()
