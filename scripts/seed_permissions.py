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

    # ============ BREEDING (5) ============
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

    # ============ SUPERVISOR (3) ============
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
        "key": "supervisor.reports",
        "name": "Supervisor Reports",
        "name_ar": "تقارير المشرف",
        "name_en": "Supervisor Reports",
        "category": "supervisor",
        "description": "View and manage supervisor reports",
        "sort_order": 2
    },
    {
        "key": "supervisor.approve",
        "name": "Supervisor Approve",
        "name_ar": "اعتماد المشرف",
        "name_en": "Supervisor Approve",
        "category": "supervisor",
        "description": "Approve reports as supervisor",
        "sort_order": 3
    },

    # ============ PM DASHBOARD (5) ============
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
        "key": "pm.team",
        "name": "PM Team",
        "name_ar": "فريق المشروع",
        "name_en": "PM Team",
        "category": "pm",
        "description": "View and manage project team",
        "sort_order": 2
    },
    {
        "key": "pm.dogs",
        "name": "PM Dogs",
        "name_ar": "كلاب المشروع",
        "name_en": "PM Dogs",
        "category": "pm",
        "description": "View and manage project dogs",
        "sort_order": 3
    },
    {
        "key": "pm.approvals",
        "name": "PM Approvals",
        "name_ar": "موافقات المشروع",
        "name_en": "PM Approvals",
        "category": "pm",
        "description": "Handle project approvals",
        "sort_order": 4
    },
    {
        "key": "pm.project",
        "name": "PM Project",
        "name_ar": "إدارة المشروع",
        "name_en": "PM Project",
        "category": "pm",
        "description": "Manage project settings and details",
        "sort_order": 5
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
