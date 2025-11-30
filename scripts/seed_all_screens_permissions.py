"""
Comprehensive Permissions Seed Script
Adds ALL screen-level and action-level permissions for EVERY page in the K9 system.

Run with: python scripts/seed_all_screens_permissions.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission


COMPREHENSIVE_PERMISSIONS = [
    # ============ HANDLER SCREENS ============
    {
        "key": "handlers.dashboard",
        "name": "Handler Dashboard",
        "name_ar": "لوحة تحكم السائس",
        "name_en": "Handler Dashboard",
        "category": "handlers",
        "description": "Access the handler's main dashboard",
        "sort_order": 1
    },
    {
        "key": "handlers.daily_report.view",
        "name": "View Daily Reports",
        "name_ar": "عرض التقارير اليومية",
        "name_en": "View Daily Reports",
        "category": "handlers",
        "description": "View handler daily reports",
        "sort_order": 2
    },
    {
        "key": "handlers.daily_report.create",
        "name": "Create Daily Report",
        "name_ar": "إنشاء تقرير يومي",
        "name_en": "Create Daily Report",
        "category": "handlers",
        "description": "Create a new handler daily report",
        "sort_order": 3
    },
    {
        "key": "handlers.daily_report.edit",
        "name": "Edit Daily Report",
        "name_ar": "تعديل التقرير اليومي",
        "name_en": "Edit Daily Report",
        "category": "handlers",
        "description": "Edit handler daily reports",
        "sort_order": 4
    },
    {
        "key": "handlers.daily_report.submit",
        "name": "Submit Daily Report",
        "name_ar": "إرسال التقرير اليومي",
        "name_en": "Submit Daily Report",
        "category": "handlers",
        "description": "Submit handler daily report for approval",
        "sort_order": 5
    },
    {
        "key": "handlers.shift_report.view",
        "name": "View Shift Reports",
        "name_ar": "عرض تقارير الوردية",
        "name_en": "View Shift Reports",
        "category": "handlers",
        "description": "View handler shift reports",
        "sort_order": 6
    },
    {
        "key": "handlers.shift_report.create",
        "name": "Create Shift Report",
        "name_ar": "إنشاء تقرير وردية",
        "name_en": "Create Shift Report",
        "category": "handlers",
        "description": "Create a new shift report",
        "sort_order": 7
    },
    {
        "key": "handlers.shift_report.edit",
        "name": "Edit Shift Report",
        "name_ar": "تعديل تقرير الوردية",
        "name_en": "Edit Shift Report",
        "category": "handlers",
        "description": "Edit handler shift reports",
        "sort_order": 8
    },
    {
        "key": "handlers.shift_report.submit",
        "name": "Submit Shift Report",
        "name_ar": "إرسال تقرير الوردية",
        "name_en": "Submit Shift Report",
        "category": "handlers",
        "description": "Submit shift report for approval",
        "sort_order": 9
    },
    {
        "key": "handlers.tasks.view",
        "name": "View My Tasks",
        "name_ar": "عرض مهامي",
        "name_en": "View My Tasks",
        "category": "handlers",
        "description": "View assigned tasks",
        "sort_order": 10
    },
    {
        "key": "handlers.tasks.complete",
        "name": "Complete Task",
        "name_ar": "إكمال المهمة",
        "name_en": "Complete Task",
        "category": "handlers",
        "description": "Mark a task as completed",
        "sort_order": 11
    },
    {
        "key": "handlers.schedule.view",
        "name": "View My Schedule",
        "name_ar": "عرض جدولي",
        "name_en": "View My Schedule",
        "category": "handlers",
        "description": "View personal work schedule",
        "sort_order": 12
    },
    {
        "key": "handlers.notifications.view",
        "name": "View Notifications",
        "name_ar": "عرض الإشعارات",
        "name_en": "View Notifications",
        "category": "handlers",
        "description": "View handler notifications",
        "sort_order": 13
    },

    # ============ PM SCREENS ============
    {
        "key": "pm.team.manage",
        "name": "Manage Team",
        "name_ar": "إدارة الفريق",
        "name_en": "Manage Team",
        "category": "pm",
        "description": "Manage project team members and assignments",
        "sort_order": 16
    },
    {
        "key": "pm.dogs.view",
        "name": "View Project Dogs",
        "name_ar": "عرض كلاب المشروع",
        "name_en": "View Project Dogs",
        "category": "pm",
        "description": "View dogs assigned to project",
        "sort_order": 17
    },
    {
        "key": "pm.dogs.assign",
        "name": "Assign Dogs to Project",
        "name_ar": "تعيين الكلاب للمشروع",
        "name_en": "Assign Dogs to Project",
        "category": "pm",
        "description": "Assign dogs to the project",
        "sort_order": 18
    },
    {
        "key": "pm.schedules.view",
        "name": "View PM Schedules",
        "name_ar": "عرض جداول مدير المشروع",
        "name_en": "View PM Schedules",
        "category": "pm",
        "description": "View project schedules",
        "sort_order": 19
    },
    {
        "key": "pm.schedules.create",
        "name": "Create PM Schedule",
        "name_ar": "إنشاء جدول مدير المشروع",
        "name_en": "Create PM Schedule",
        "category": "pm",
        "description": "Create project schedules",
        "sort_order": 20
    },
    {
        "key": "pm.schedules.edit",
        "name": "Edit PM Schedule",
        "name_ar": "تعديل جدول مدير المشروع",
        "name_en": "Edit PM Schedule",
        "category": "pm",
        "description": "Edit project schedules",
        "sort_order": 21
    },
    {
        "key": "pm.schedules.lock",
        "name": "Lock PM Schedule",
        "name_ar": "قفل جدول مدير المشروع",
        "name_en": "Lock PM Schedule",
        "category": "pm",
        "description": "Lock project schedules",
        "sort_order": 22
    },
    {
        "key": "pm.incidents.view",
        "name": "View PM Incidents",
        "name_ar": "عرض حوادث المشروع",
        "name_en": "View PM Incidents",
        "category": "pm",
        "description": "View project incidents",
        "sort_order": 23
    },
    {
        "key": "pm.incidents.create",
        "name": "Create PM Incident",
        "name_ar": "إنشاء حادثة المشروع",
        "name_en": "Create PM Incident",
        "category": "pm",
        "description": "Create project incidents",
        "sort_order": 24
    },
    {
        "key": "pm.incidents.resolve",
        "name": "Resolve PM Incident",
        "name_ar": "حل حادثة المشروع",
        "name_en": "Resolve PM Incident",
        "category": "pm",
        "description": "Resolve project incidents",
        "sort_order": 25
    },
    {
        "key": "pm.suspicions.view",
        "name": "View PM Suspicions",
        "name_ar": "عرض اشتباهات المشروع",
        "name_en": "View PM Suspicions",
        "category": "pm",
        "description": "View project suspicions",
        "sort_order": 26
    },
    {
        "key": "pm.suspicions.create",
        "name": "Create PM Suspicion",
        "name_ar": "إنشاء اشتباه المشروع",
        "name_en": "Create PM Suspicion",
        "category": "pm",
        "description": "Create project suspicions",
        "sort_order": 27
    },
    {
        "key": "pm.evaluations.view",
        "name": "View PM Evaluations",
        "name_ar": "عرض تقييمات المشروع",
        "name_en": "View PM Evaluations",
        "category": "pm",
        "description": "View project evaluations",
        "sort_order": 28
    },
    {
        "key": "pm.evaluations.create",
        "name": "Create PM Evaluation",
        "name_ar": "إنشاء تقييم المشروع",
        "name_en": "Create PM Evaluation",
        "category": "pm",
        "description": "Create project evaluations",
        "sort_order": 29
    },
    {
        "key": "pm.statistics",
        "name": "View PM Statistics",
        "name_ar": "عرض إحصائيات المشروع",
        "name_en": "View PM Statistics",
        "category": "pm",
        "description": "View project statistics and analytics",
        "sort_order": 30
    },

    # ============ SUPERVISOR SCREENS ============
    {
        "key": "supervisor.schedules.view",
        "name": "View Supervisor Schedules",
        "name_ar": "عرض جداول المشرف",
        "name_en": "View Supervisor Schedules",
        "category": "supervisor",
        "description": "View supervisor schedules list",
        "sort_order": 6
    },
    {
        "key": "supervisor.schedules.create",
        "name": "Create Supervisor Schedule",
        "name_ar": "إنشاء جدول المشرف",
        "name_en": "Create Supervisor Schedule",
        "category": "supervisor",
        "description": "Create new supervisor schedules",
        "sort_order": 7
    },
    {
        "key": "supervisor.schedules.edit",
        "name": "Edit Supervisor Schedule",
        "name_ar": "تعديل جدول المشرف",
        "name_en": "Edit Supervisor Schedule",
        "category": "supervisor",
        "description": "Edit supervisor schedules",
        "sort_order": 8
    },
    {
        "key": "supervisor.schedules.lock",
        "name": "Lock Supervisor Schedule",
        "name_ar": "قفل جدول المشرف",
        "name_en": "Lock Supervisor Schedule",
        "category": "supervisor",
        "description": "Lock supervisor schedules",
        "sort_order": 9
    },
    {
        "key": "supervisor.schedules.unlock",
        "name": "Unlock Supervisor Schedule",
        "name_ar": "فتح قفل جدول المشرف",
        "name_en": "Unlock Supervisor Schedule",
        "category": "supervisor",
        "description": "Unlock supervisor schedules",
        "sort_order": 10
    },
    {
        "key": "supervisor.schedules.delete",
        "name": "Delete Supervisor Schedule",
        "name_ar": "حذف جدول المشرف",
        "name_en": "Delete Supervisor Schedule",
        "category": "supervisor",
        "description": "Delete supervisor schedules",
        "sort_order": 11
    },
    {
        "key": "supervisor.replace_handler",
        "name": "Replace Handler in Schedule",
        "name_ar": "استبدال سائس في الجدول",
        "name_en": "Replace Handler in Schedule",
        "category": "supervisor",
        "description": "Replace handler in schedule item",
        "sort_order": 12
    },
    {
        "key": "supervisor.reports.approve",
        "name": "Approve Reports (Supervisor)",
        "name_ar": "اعتماد التقارير (مشرف)",
        "name_en": "Approve Reports (Supervisor)",
        "category": "supervisor",
        "description": "Approve handler reports as supervisor",
        "sort_order": 13
    },
    {
        "key": "supervisor.reports.reject",
        "name": "Reject Reports (Supervisor)",
        "name_ar": "رفض التقارير (مشرف)",
        "name_en": "Reject Reports (Supervisor)",
        "category": "supervisor",
        "description": "Reject handler reports as supervisor",
        "sort_order": 14
    },

    # ============ ADMIN SCREENS ============
    {
        "key": "admin.permissions.advanced",
        "name": "Advanced Permissions",
        "name_ar": "الصلاحيات المتقدمة",
        "name_en": "Advanced Permissions",
        "category": "admin",
        "description": "Access advanced permissions management",
        "sort_order": 7
    },
    {
        "key": "admin.permissions.templates",
        "name": "Permission Templates",
        "name_ar": "قوالب الصلاحيات",
        "name_en": "Permission Templates",
        "category": "admin",
        "description": "Manage permission templates",
        "sort_order": 8
    },
    {
        "key": "admin.reports.pending",
        "name": "Pending Reports",
        "name_ar": "التقارير المعلقة",
        "name_en": "Pending Reports",
        "category": "admin",
        "description": "View pending reports for approval",
        "sort_order": 9
    },
    {
        "key": "admin.reports.approve",
        "name": "Approve Admin Reports",
        "name_ar": "اعتماد تقارير المسؤول",
        "name_en": "Approve Admin Reports",
        "category": "admin",
        "description": "Approve reports as admin",
        "sort_order": 10
    },
    {
        "key": "admin.reports.reject",
        "name": "Reject Admin Reports",
        "name_ar": "رفض تقارير المسؤول",
        "name_en": "Reject Admin Reports",
        "category": "admin",
        "description": "Reject reports as admin",
        "sort_order": 11
    },
    {
        "key": "admin.backup.create",
        "name": "Create Backup",
        "name_ar": "إنشاء نسخة احتياطية",
        "name_en": "Create Backup",
        "category": "admin",
        "description": "Create system backups",
        "sort_order": 12
    },
    {
        "key": "admin.backup.restore",
        "name": "Restore Backup",
        "name_ar": "استعادة النسخة الاحتياطية",
        "name_en": "Restore Backup",
        "category": "admin",
        "description": "Restore system from backup",
        "sort_order": 13
    },
    {
        "key": "admin.backup.download",
        "name": "Download Backup",
        "name_ar": "تحميل النسخة الاحتياطية",
        "name_en": "Download Backup",
        "category": "admin",
        "description": "Download backup files",
        "sort_order": 14
    },
    {
        "key": "admin.backup.delete",
        "name": "Delete Backup",
        "name_ar": "حذف النسخة الاحتياطية",
        "name_en": "Delete Backup",
        "category": "admin",
        "description": "Delete backup files",
        "sort_order": 15
    },
    {
        "key": "admin.notifications.view",
        "name": "View Admin Notifications",
        "name_ar": "عرض إشعارات المسؤول",
        "name_en": "View Admin Notifications",
        "category": "admin",
        "description": "View admin notifications",
        "sort_order": 16
    },
    {
        "key": "admin.google_drive",
        "name": "Google Drive Integration",
        "name_ar": "تكامل Google Drive",
        "name_en": "Google Drive Integration",
        "category": "admin",
        "description": "Manage Google Drive integration",
        "sort_order": 17
    },
    {
        "key": "admin.cloud_backup",
        "name": "Cloud Backup",
        "name_ar": "النسخ الاحتياطي السحابي",
        "name_en": "Cloud Backup",
        "category": "admin",
        "description": "Manage cloud backup settings",
        "sort_order": 18
    },
    {
        "key": "admin.users.view",
        "name": "View Users",
        "name_ar": "عرض المستخدمين",
        "name_en": "View Users",
        "category": "admin",
        "description": "View all system users",
        "sort_order": 19
    },
    {
        "key": "admin.users.create",
        "name": "Create User",
        "name_ar": "إنشاء مستخدم",
        "name_en": "Create User",
        "category": "admin",
        "description": "Create new system users",
        "sort_order": 20
    },
    {
        "key": "admin.users.edit",
        "name": "Edit User",
        "name_ar": "تعديل مستخدم",
        "name_en": "Edit User",
        "category": "admin",
        "description": "Edit user accounts",
        "sort_order": 21
    },
    {
        "key": "admin.users.delete",
        "name": "Delete User",
        "name_ar": "حذف مستخدم",
        "name_en": "Delete User",
        "category": "admin",
        "description": "Delete user accounts",
        "sort_order": 22
    },
    {
        "key": "admin.users.reset_password",
        "name": "Reset User Password",
        "name_ar": "إعادة تعيين كلمة مرور المستخدم",
        "name_en": "Reset User Password",
        "category": "admin",
        "description": "Reset user passwords",
        "sort_order": 23
    },
    {
        "key": "admin.users.toggle_status",
        "name": "Toggle User Status",
        "name_ar": "تبديل حالة المستخدم",
        "name_en": "Toggle User Status",
        "category": "admin",
        "description": "Activate/deactivate user accounts",
        "sort_order": 24
    },
    
    # ============ ACCOUNT MANAGEMENT SCREENS ============
    {
        "key": "account_management.index",
        "name": "Account Management List",
        "name_ar": "قائمة إدارة الحسابات",
        "name_en": "Account Management List",
        "category": "account_management",
        "description": "View list of user accounts",
        "sort_order": 1
    },
    {
        "key": "account_management.create",
        "name": "Create Account",
        "name_ar": "إنشاء حساب",
        "name_en": "Create Account",
        "category": "account_management",
        "description": "Create new user accounts",
        "sort_order": 2
    },
    {
        "key": "account_management.toggle_status",
        "name": "Toggle Account Status",
        "name_ar": "تبديل حالة الحساب",
        "name_en": "Toggle Account Status",
        "category": "account_management",
        "description": "Activate/deactivate accounts",
        "sort_order": 3
    },
    {
        "key": "account_management.reset_password",
        "name": "Reset Account Password",
        "name_ar": "إعادة تعيين كلمة مرور الحساب",
        "name_en": "Reset Account Password",
        "category": "account_management",
        "description": "Reset account passwords",
        "sort_order": 4
    },

    # ============ DOG SCREENS ============
    {
        "key": "dogs.list",
        "name": "Dogs List",
        "name_ar": "قائمة الكلاب",
        "name_en": "Dogs List",
        "category": "dogs",
        "description": "View the list of all dogs",
        "sort_order": 6
    },
    {
        "key": "dogs.details",
        "name": "Dog Details",
        "name_ar": "تفاصيل الكلب",
        "name_en": "Dog Details",
        "category": "dogs",
        "description": "View detailed dog information",
        "sort_order": 7
    },
    {
        "key": "dogs.transfer",
        "name": "Transfer Dog",
        "name_ar": "نقل الكلب",
        "name_en": "Transfer Dog",
        "category": "dogs",
        "description": "Transfer dog between projects",
        "sort_order": 8
    },
    {
        "key": "dogs.status_change",
        "name": "Change Dog Status",
        "name_ar": "تغيير حالة الكلب",
        "name_en": "Change Dog Status",
        "category": "dogs",
        "description": "Change dog status (active, retired, etc)",
        "sort_order": 9
    },
    {
        "key": "dogs.medical_history",
        "name": "Dog Medical History",
        "name_ar": "السجل الطبي للكلب",
        "name_en": "Dog Medical History",
        "category": "dogs",
        "description": "View dog medical history",
        "sort_order": 10
    },
    {
        "key": "dogs.training_history",
        "name": "Dog Training History",
        "name_ar": "سجل تدريب الكلب",
        "name_en": "Dog Training History",
        "category": "dogs",
        "description": "View dog training history",
        "sort_order": 11
    },

    # ============ EMPLOYEE SCREENS ============
    {
        "key": "employees.list",
        "name": "Employees List",
        "name_ar": "قائمة الموظفين",
        "name_en": "Employees List",
        "category": "employees",
        "description": "View the list of all employees",
        "sort_order": 6
    },
    {
        "key": "employees.details",
        "name": "Employee Details",
        "name_ar": "تفاصيل الموظف",
        "name_en": "Employee Details",
        "category": "employees",
        "description": "View detailed employee information",
        "sort_order": 7
    },
    {
        "key": "employees.transfer",
        "name": "Transfer Employee",
        "name_ar": "نقل الموظف",
        "name_en": "Transfer Employee",
        "category": "employees",
        "description": "Transfer employee between projects",
        "sort_order": 8
    },
    {
        "key": "employees.link_user",
        "name": "Link Employee to User",
        "name_ar": "ربط الموظف بمستخدم",
        "name_en": "Link Employee to User",
        "category": "employees",
        "description": "Link employee record to user account",
        "sort_order": 9
    },
    {
        "key": "employees.unlink_user",
        "name": "Unlink Employee from User",
        "name_ar": "فك ربط الموظف من المستخدم",
        "name_en": "Unlink Employee from User",
        "category": "employees",
        "description": "Unlink employee record from user account",
        "sort_order": 10
    },

    # ============ PROJECT SCREENS ============
    {
        "key": "projects.list",
        "name": "Projects List",
        "name_ar": "قائمة المشاريع",
        "name_en": "Projects List",
        "category": "projects",
        "description": "View the list of all projects",
        "sort_order": 5
    },
    {
        "key": "projects.dashboard",
        "name": "Project Dashboard",
        "name_ar": "لوحة تحكم المشروع",
        "name_en": "Project Dashboard",
        "category": "projects",
        "description": "View project dashboard with statistics",
        "sort_order": 6
    },
    {
        "key": "projects.assignments.view",
        "name": "View Project Assignments",
        "name_ar": "عرض تعيينات المشروع",
        "name_en": "View Project Assignments",
        "category": "projects",
        "description": "View project employee/dog assignments",
        "sort_order": 7
    },
    {
        "key": "projects.assignments.add",
        "name": "Add Project Assignment",
        "name_ar": "إضافة تعيين للمشروع",
        "name_en": "Add Project Assignment",
        "category": "projects",
        "description": "Add new assignment to project",
        "sort_order": 8
    },
    {
        "key": "projects.assignments.edit",
        "name": "Edit Project Assignment",
        "name_ar": "تعديل تعيين المشروع",
        "name_en": "Edit Project Assignment",
        "category": "projects",
        "description": "Edit project assignment",
        "sort_order": 9
    },
    {
        "key": "projects.assignments.remove",
        "name": "Remove Project Assignment",
        "name_ar": "إزالة تعيين المشروع",
        "name_en": "Remove Project Assignment",
        "category": "projects",
        "description": "Remove assignment from project",
        "sort_order": 10
    },
    {
        "key": "projects.incidents.view",
        "name": "View Project Incidents",
        "name_ar": "عرض حوادث المشروع",
        "name_en": "View Project Incidents",
        "category": "projects",
        "description": "View project incidents",
        "sort_order": 11
    },
    {
        "key": "projects.incidents.add",
        "name": "Add Project Incident",
        "name_ar": "إضافة حادثة للمشروع",
        "name_en": "Add Project Incident",
        "category": "projects",
        "description": "Add incident to project",
        "sort_order": 12
    },
    {
        "key": "projects.incidents.resolve",
        "name": "Resolve Project Incident",
        "name_ar": "حل حادثة المشروع",
        "name_en": "Resolve Project Incident",
        "category": "projects",
        "description": "Resolve project incident",
        "sort_order": 13
    },
    {
        "key": "projects.suspicions.view",
        "name": "View Project Suspicions",
        "name_ar": "عرض اشتباهات المشروع",
        "name_en": "View Project Suspicions",
        "category": "projects",
        "description": "View project suspicions",
        "sort_order": 14
    },
    {
        "key": "projects.suspicions.add",
        "name": "Add Project Suspicion",
        "name_ar": "إضافة اشتباه للمشروع",
        "name_en": "Add Project Suspicion",
        "category": "projects",
        "description": "Add suspicion to project",
        "sort_order": 15
    },
    {
        "key": "projects.evaluations.view",
        "name": "View Project Evaluations",
        "name_ar": "عرض تقييمات المشروع",
        "name_en": "View Project Evaluations",
        "category": "projects",
        "description": "View project evaluations",
        "sort_order": 16
    },
    {
        "key": "projects.evaluations.add",
        "name": "Add Project Evaluation",
        "name_ar": "إضافة تقييم للمشروع",
        "name_en": "Add Project Evaluation",
        "category": "projects",
        "description": "Add evaluation to project",
        "sort_order": 17
    },
    {
        "key": "projects.status_change",
        "name": "Change Project Status",
        "name_ar": "تغيير حالة المشروع",
        "name_en": "Change Project Status",
        "category": "projects",
        "description": "Change project status",
        "sort_order": 18
    },
    {
        "key": "projects.manager_update",
        "name": "Update Project Manager",
        "name_ar": "تحديث مدير المشروع",
        "name_en": "Update Project Manager",
        "category": "projects",
        "description": "Update project manager assignment",
        "sort_order": 19
    },

    # ============ SCHEDULE SCREENS ============
    {
        "key": "schedule.list",
        "name": "Schedule List",
        "name_ar": "قائمة الجداول",
        "name_en": "Schedule List",
        "category": "schedule",
        "description": "View list of schedules",
        "sort_order": 6
    },
    {
        "key": "schedule.details",
        "name": "Schedule Details",
        "name_ar": "تفاصيل الجدول",
        "name_en": "Schedule Details",
        "category": "schedule",
        "description": "View schedule details",
        "sort_order": 7
    },
    {
        "key": "schedule.item.delete",
        "name": "Delete Schedule Item",
        "name_ar": "حذف عنصر الجدول",
        "name_en": "Delete Schedule Item",
        "category": "schedule",
        "description": "Delete individual schedule items",
        "sort_order": 8
    },
    {
        "key": "schedule.lock",
        "name": "Lock Schedule",
        "name_ar": "قفل الجدول",
        "name_en": "Lock Schedule",
        "category": "schedule",
        "description": "Lock schedule to prevent changes",
        "sort_order": 9
    },
    {
        "key": "schedule.unlock",
        "name": "Unlock Schedule",
        "name_ar": "فتح قفل الجدول",
        "name_en": "Unlock Schedule",
        "category": "schedule",
        "description": "Unlock schedule to allow changes",
        "sort_order": 10
    },

    # ============ TRAINING SCREENS ============
    {
        "key": "training.list",
        "name": "Training List",
        "name_ar": "قائمة التدريب",
        "name_en": "Training List",
        "category": "training",
        "description": "View list of training sessions",
        "sort_order": 6
    },
    {
        "key": "training.details",
        "name": "Training Details",
        "name_ar": "تفاصيل التدريب",
        "name_en": "Training Details",
        "category": "training",
        "description": "View training session details",
        "sort_order": 7
    },
    {
        "key": "training.approve",
        "name": "Approve Training",
        "name_ar": "اعتماد التدريب",
        "name_en": "Approve Training",
        "category": "training",
        "description": "Approve training records",
        "sort_order": 8
    },

    # ============ VETERINARY SCREENS ============
    {
        "key": "veterinary.list",
        "name": "Veterinary List",
        "name_ar": "قائمة البيطرة",
        "name_en": "Veterinary List",
        "category": "veterinary",
        "description": "View list of veterinary visits",
        "sort_order": 6
    },
    {
        "key": "veterinary.details",
        "name": "Veterinary Details",
        "name_ar": "تفاصيل البيطرة",
        "name_en": "Veterinary Details",
        "category": "veterinary",
        "description": "View veterinary visit details",
        "sort_order": 7
    },
    {
        "key": "veterinary.daily",
        "name": "Daily Veterinary Reports",
        "name_ar": "التقارير البيطرية اليومية",
        "name_en": "Daily Veterinary Reports",
        "category": "veterinary",
        "description": "View daily veterinary reports",
        "sort_order": 8
    },
    {
        "key": "veterinary.weekly",
        "name": "Weekly Veterinary Reports",
        "name_ar": "التقارير البيطرية الأسبوعية",
        "name_en": "Weekly Veterinary Reports",
        "category": "veterinary",
        "description": "View weekly veterinary reports",
        "sort_order": 9
    },
    {
        "key": "veterinary.approve",
        "name": "Approve Veterinary",
        "name_ar": "اعتماد البيطرة",
        "name_en": "Approve Veterinary",
        "category": "veterinary",
        "description": "Approve veterinary records",
        "sort_order": 10
    },

    # ============ BREEDING SCREENS ============
    {
        "key": "breeding.list",
        "name": "Breeding List",
        "name_ar": "قائمة التربية",
        "name_en": "Breeding List",
        "category": "breeding",
        "description": "View list of breeding records",
        "sort_order": 12
    },
    {
        "key": "breeding.details",
        "name": "Breeding Details",
        "name_ar": "تفاصيل التربية",
        "name_en": "Breeding Details",
        "category": "breeding",
        "description": "View breeding record details",
        "sort_order": 13
    },
    {
        "key": "breeding.feeding.list",
        "name": "Feeding Log List",
        "name_ar": "قائمة سجل التغذية",
        "name_en": "Feeding Log List",
        "category": "breeding",
        "description": "View feeding logs list",
        "sort_order": 14
    },
    {
        "key": "breeding.feeding.create",
        "name": "Create Feeding Log",
        "name_ar": "إنشاء سجل التغذية",
        "name_en": "Create Feeding Log",
        "category": "breeding",
        "description": "Create new feeding log",
        "sort_order": 15
    },
    {
        "key": "breeding.feeding.edit",
        "name": "Edit Feeding Log",
        "name_ar": "تعديل سجل التغذية",
        "name_en": "Edit Feeding Log",
        "category": "breeding",
        "description": "Edit feeding log",
        "sort_order": 16
    },
    {
        "key": "breeding.checkup.list",
        "name": "Checkup List",
        "name_ar": "قائمة الفحوصات",
        "name_en": "Checkup List",
        "category": "breeding",
        "description": "View checkup list",
        "sort_order": 17
    },
    {
        "key": "breeding.checkup.create",
        "name": "Create Checkup",
        "name_ar": "إنشاء فحص",
        "name_en": "Create Checkup",
        "category": "breeding",
        "description": "Create new checkup record",
        "sort_order": 18
    },
    {
        "key": "breeding.checkup.edit",
        "name": "Edit Checkup",
        "name_ar": "تعديل الفحص",
        "name_en": "Edit Checkup",
        "category": "breeding",
        "description": "Edit checkup record",
        "sort_order": 19
    },
    {
        "key": "breeding.excretion.list",
        "name": "Excretion List",
        "name_ar": "قائمة الإخراج",
        "name_en": "Excretion List",
        "category": "breeding",
        "description": "View excretion records list",
        "sort_order": 20
    },
    {
        "key": "breeding.excretion.create",
        "name": "Create Excretion",
        "name_ar": "إنشاء سجل إخراج",
        "name_en": "Create Excretion",
        "category": "breeding",
        "description": "Create new excretion record",
        "sort_order": 21
    },
    {
        "key": "breeding.excretion.edit",
        "name": "Edit Excretion",
        "name_ar": "تعديل سجل الإخراج",
        "name_en": "Edit Excretion",
        "category": "breeding",
        "description": "Edit excretion record",
        "sort_order": 22
    },
    {
        "key": "breeding.puppies.list",
        "name": "Puppies List",
        "name_ar": "قائمة الجراء",
        "name_en": "Puppies List",
        "category": "breeding",
        "description": "View puppies list",
        "sort_order": 23
    },
    {
        "key": "breeding.puppies.view",
        "name": "View Puppy",
        "name_ar": "عرض الجرو",
        "name_en": "View Puppy",
        "category": "breeding",
        "description": "View puppy details",
        "sort_order": 24
    },
    {
        "key": "breeding.puppy_training.list",
        "name": "Puppy Training List",
        "name_ar": "قائمة تدريب الجراء",
        "name_en": "Puppy Training List",
        "category": "breeding",
        "description": "View puppy training list",
        "sort_order": 25
    },
    {
        "key": "breeding.puppy_training.create",
        "name": "Create Puppy Training",
        "name_ar": "إنشاء تدريب جرو",
        "name_en": "Create Puppy Training",
        "category": "breeding",
        "description": "Create puppy training record",
        "sort_order": 26
    },
    {
        "key": "breeding.deliveries.view",
        "name": "View Deliveries",
        "name_ar": "عرض الولادات",
        "name_en": "View Deliveries",
        "category": "breeding",
        "description": "View breeding deliveries",
        "sort_order": 27
    },

    # ============ PRODUCTION SCREENS ============
    {
        "key": "production.list",
        "name": "Production List",
        "name_ar": "قائمة الإنتاج",
        "name_en": "Production List",
        "category": "production",
        "description": "View production records list",
        "sort_order": 1
    },
    {
        "key": "production.view",
        "name": "View Production",
        "name_ar": "عرض الإنتاج",
        "name_en": "View Production",
        "category": "production",
        "description": "View production record details",
        "sort_order": 2
    },
    {
        "key": "production.create",
        "name": "Create Production",
        "name_ar": "إنشاء سجل إنتاج",
        "name_en": "Create Production",
        "category": "production",
        "description": "Create new production record",
        "sort_order": 3
    },
    {
        "key": "production.edit",
        "name": "Edit Production",
        "name_ar": "تعديل سجل الإنتاج",
        "name_en": "Edit Production",
        "category": "production",
        "description": "Edit production record",
        "sort_order": 4
    },
    {
        "key": "production.delete",
        "name": "Delete Production",
        "name_ar": "حذف سجل الإنتاج",
        "name_en": "Delete Production",
        "category": "production",
        "description": "Delete production record",
        "sort_order": 5
    },

    # ============ TASK SCREENS ============
    {
        "key": "tasks.admin.list",
        "name": "Admin Tasks List",
        "name_ar": "قائمة مهام المسؤول",
        "name_en": "Admin Tasks List",
        "category": "tasks",
        "description": "View all tasks (admin)",
        "sort_order": 7
    },
    {
        "key": "tasks.admin.create",
        "name": "Create Admin Task",
        "name_ar": "إنشاء مهمة المسؤول",
        "name_en": "Create Admin Task",
        "category": "tasks",
        "description": "Create new task (admin)",
        "sort_order": 8
    },
    {
        "key": "tasks.admin.edit",
        "name": "Edit Admin Task",
        "name_ar": "تعديل مهمة المسؤول",
        "name_en": "Edit Admin Task",
        "category": "tasks",
        "description": "Edit task (admin)",
        "sort_order": 9
    },
    {
        "key": "tasks.admin.delete",
        "name": "Delete Admin Task",
        "name_ar": "حذف مهمة المسؤول",
        "name_en": "Delete Admin Task",
        "category": "tasks",
        "description": "Delete task (admin)",
        "sort_order": 10
    },
    {
        "key": "tasks.my_tasks.list",
        "name": "My Tasks List",
        "name_ar": "قائمة مهامي",
        "name_en": "My Tasks List",
        "category": "tasks",
        "description": "View my assigned tasks",
        "sort_order": 11
    },
    {
        "key": "tasks.my_tasks.complete",
        "name": "Complete My Task",
        "name_ar": "إكمال مهمتي",
        "name_en": "Complete My Task",
        "category": "tasks",
        "description": "Mark my task as complete",
        "sort_order": 12
    },
    {
        "key": "tasks.my_tasks.start",
        "name": "Start My Task",
        "name_ar": "بدء مهمتي",
        "name_en": "Start My Task",
        "category": "tasks",
        "description": "Start working on my task",
        "sort_order": 13
    },

    # ============ REPORTS SCREENS ============
    {
        "key": "reports.hub",
        "name": "Reports Hub",
        "name_ar": "مركز التقارير",
        "name_en": "Reports Hub",
        "category": "reports.general",
        "description": "Access reports hub",
        "sort_order": 2
    },
    {
        "key": "reports.simple",
        "name": "Simple Reports",
        "name_ar": "التقارير البسيطة",
        "name_en": "Simple Reports",
        "category": "reports.general",
        "description": "Access simple reports",
        "sort_order": 3
    },
    {
        "key": "reports.generate",
        "name": "Generate Reports",
        "name_ar": "إنشاء التقارير",
        "name_en": "Generate Reports",
        "category": "reports.general",
        "description": "Generate new reports",
        "sort_order": 4
    },
    {
        "key": "reports.preview",
        "name": "Preview Reports",
        "name_ar": "معاينة التقارير",
        "name_en": "Preview Reports",
        "category": "reports.general",
        "description": "Preview reports before export",
        "sort_order": 5
    },
    {
        "key": "reports.preview_pdf",
        "name": "Preview Reports PDF",
        "name_ar": "معاينة PDF للتقارير",
        "name_en": "Preview Reports PDF",
        "category": "reports.general",
        "description": "Preview reports as PDF",
        "sort_order": 6
    },

    # ============ MFA SCREENS ============
    {
        "key": "mfa.setup",
        "name": "Setup MFA",
        "name_ar": "إعداد المصادقة الثنائية",
        "name_en": "Setup MFA",
        "category": "mfa",
        "description": "Setup multi-factor authentication",
        "sort_order": 1
    },
    {
        "key": "mfa.verify",
        "name": "Verify MFA",
        "name_ar": "التحقق من المصادقة الثنائية",
        "name_en": "Verify MFA",
        "category": "mfa",
        "description": "Verify MFA code",
        "sort_order": 2
    },
    {
        "key": "mfa.disable",
        "name": "Disable MFA",
        "name_ar": "تعطيل المصادقة الثنائية",
        "name_en": "Disable MFA",
        "category": "mfa",
        "description": "Disable multi-factor authentication",
        "sort_order": 3
    },
    {
        "key": "mfa.backup_codes",
        "name": "MFA Backup Codes",
        "name_ar": "أكواد الاحتياط للمصادقة",
        "name_en": "MFA Backup Codes",
        "category": "mfa",
        "description": "View/regenerate MFA backup codes",
        "sort_order": 4
    },
    {
        "key": "mfa.admin_reset",
        "name": "Admin Reset MFA",
        "name_ar": "إعادة تعيين المصادقة من المسؤول",
        "name_en": "Admin Reset MFA",
        "category": "mfa",
        "description": "Admin can reset user MFA",
        "sort_order": 5
    },

    # ============ CARETAKER SCREENS ============
    {
        "key": "caretaker.daily_log.list",
        "name": "Caretaker Daily Logs List",
        "name_ar": "قائمة سجلات العناية اليومية",
        "name_en": "Caretaker Daily Logs List",
        "category": "reports.caretaker",
        "description": "View caretaker daily logs list",
        "sort_order": 3
    },
    {
        "key": "caretaker.daily_log.create",
        "name": "Create Caretaker Log",
        "name_ar": "إنشاء سجل العناية",
        "name_en": "Create Caretaker Log",
        "category": "reports.caretaker",
        "description": "Create new caretaker daily log",
        "sort_order": 4
    },
    {
        "key": "caretaker.daily_log.edit",
        "name": "Edit Caretaker Log",
        "name_ar": "تعديل سجل العناية",
        "name_en": "Edit Caretaker Log",
        "category": "reports.caretaker",
        "description": "Edit caretaker daily log",
        "sort_order": 5
    },
    {
        "key": "caretaker.daily_log.submit",
        "name": "Submit Caretaker Log",
        "name_ar": "إرسال سجل العناية",
        "name_en": "Submit Caretaker Log",
        "category": "reports.caretaker",
        "description": "Submit caretaker log for approval",
        "sort_order": 6
    },

    # ============ TRAINER SCREENS ============
    {
        "key": "trainer.daily.list",
        "name": "Trainer Daily List",
        "name_ar": "قائمة المدرب اليومية",
        "name_en": "Trainer Daily List",
        "category": "reports.training",
        "description": "View trainer daily reports list",
        "sort_order": 5
    },
    {
        "key": "trainer.daily.create",
        "name": "Create Trainer Daily",
        "name_ar": "إنشاء تقرير المدرب اليومي",
        "name_en": "Create Trainer Daily",
        "category": "reports.training",
        "description": "Create trainer daily report",
        "sort_order": 6
    },
    {
        "key": "trainer.daily.edit",
        "name": "Edit Trainer Daily",
        "name_ar": "تعديل تقرير المدرب اليومي",
        "name_en": "Edit Trainer Daily",
        "category": "reports.training",
        "description": "Edit trainer daily report",
        "sort_order": 7
    },
    {
        "key": "trainer.daily.submit",
        "name": "Submit Trainer Daily",
        "name_ar": "إرسال تقرير المدرب اليومي",
        "name_en": "Submit Trainer Daily",
        "category": "reports.training",
        "description": "Submit trainer daily report for approval",
        "sort_order": 8
    },

    # ============ GENERAL SCREENS ============
    {
        "key": "general.home",
        "name": "Home Page",
        "name_ar": "الصفحة الرئيسية",
        "name_en": "Home Page",
        "category": "general",
        "description": "Access home page",
        "sort_order": 1
    },
    {
        "key": "general.dashboard",
        "name": "Main Dashboard",
        "name_ar": "لوحة التحكم الرئيسية",
        "name_en": "Main Dashboard",
        "category": "general",
        "description": "Access main dashboard",
        "sort_order": 2
    },
    {
        "key": "general.profile",
        "name": "User Profile",
        "name_ar": "الملف الشخصي",
        "name_en": "User Profile",
        "category": "general",
        "description": "View and edit user profile",
        "sort_order": 3
    },
    {
        "key": "general.change_password",
        "name": "Change Password",
        "name_ar": "تغيير كلمة المرور",
        "name_en": "Change Password",
        "category": "general",
        "description": "Change user password",
        "sort_order": 4
    },

    # ============ CLEANING SCREENS ============
    {
        "key": "cleaning.list",
        "name": "Cleaning List",
        "name_ar": "قائمة التنظيف",
        "name_en": "Cleaning List",
        "category": "cleaning",
        "description": "View cleaning records list",
        "sort_order": 5
    },
    {
        "key": "cleaning.details",
        "name": "Cleaning Details",
        "name_ar": "تفاصيل التنظيف",
        "name_en": "Cleaning Details",
        "category": "cleaning",
        "description": "View cleaning record details",
        "sort_order": 6
    },

    # ============ UNIFIED REPORTS SCREENS ============
    {
        "key": "reports.breeding.unified_feeding",
        "name": "Unified Feeding Reports",
        "name_ar": "تقارير التغذية الموحدة",
        "name_en": "Unified Feeding Reports",
        "category": "reports.breeding",
        "description": "View unified breeding feeding reports",
        "sort_order": 14
    },
    {
        "key": "reports.breeding.unified_checkup",
        "name": "Unified Checkup Reports",
        "name_ar": "تقارير الفحص الموحدة",
        "name_en": "Unified Checkup Reports",
        "category": "reports.breeding",
        "description": "View unified breeding checkup reports",
        "sort_order": 15
    },
    {
        "key": "reports.veterinary.unified",
        "name": "Unified Veterinary Reports",
        "name_ar": "التقارير البيطرية الموحدة",
        "name_en": "Unified Veterinary Reports",
        "category": "reports.veterinary",
        "description": "View unified veterinary reports",
        "sort_order": 4
    },
]


def seed_comprehensive_permissions():
    """Seed all comprehensive permissions into the database"""
    with app.app_context():
        print("=" * 60)
        print("Comprehensive Permissions Seeding")
        print("=" * 60)
        print(f"\nProcessing {len(COMPREHENSIVE_PERMISSIONS)} additional permissions...\n")
        
        created = 0
        updated = 0
        skipped = 0
        
        for perm_data in COMPREHENSIVE_PERMISSIONS:
            existing = Permission.query.filter_by(key=perm_data['key']).first()
            
            if existing:
                # Check if any field needs updating
                needs_update = False
                for field in ['name', 'name_ar', 'name_en', 'description', 'category', 'sort_order']:
                    if getattr(existing, field, None) != perm_data.get(field):
                        needs_update = True
                        setattr(existing, field, perm_data.get(field))
                
                if needs_update:
                    updated += 1
                    print(f"  Updated: {perm_data['key']}")
                else:
                    skipped += 1
            else:
                new_perm = Permission(
                    key=perm_data['key'],
                    name=perm_data['name'],
                    name_ar=perm_data.get('name_ar'),
                    name_en=perm_data.get('name_en'),
                    description=perm_data.get('description'),
                    category=perm_data['category'],
                    sort_order=perm_data.get('sort_order', 0),
                    is_active=True
                )
                db.session.add(new_perm)
                created += 1
                print(f"  Created: {perm_data['key']}")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Created: {created} new permissions")
        print(f"  Updated: {updated} existing permissions")
        print(f"  Skipped: {skipped} unchanged permissions")
        print(f"  Total:   {len(COMPREHENSIVE_PERMISSIONS)} permissions processed")
        print("=" * 60)
        
        # Show total count
        total = Permission.query.count()
        print(f"\nTotal permissions in database: {total}")
        
        # Show categories
        from sqlalchemy import func
        categories = db.session.query(
            Permission.category,
            func.count(Permission.id)
        ).group_by(Permission.category).order_by(Permission.category).all()
        
        print(f"\nCategories ({len(categories)}):")
        for cat, count in categories:
            print(f"  - {cat}: {count} permissions")


if __name__ == '__main__':
    seed_comprehensive_permissions()
