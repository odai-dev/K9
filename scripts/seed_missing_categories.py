"""
Missing Categories Permissions Seed Script
Adds permissions for categories that were missing: auth, password_reset, dashboard_api, and production sub-categories.

Run with: python scripts/seed_missing_categories.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission


MISSING_PERMISSIONS = [
    # ============ AUTH CATEGORY ============
    {
        "key": "auth.login",
        "name": "Login Access",
        "name_ar": "الوصول لتسجيل الدخول",
        "name_en": "Login Access",
        "category": "auth",
        "description": "Access to login page",
        "sort_order": 1
    },
    {
        "key": "auth.logout",
        "name": "Logout Access",
        "name_ar": "الوصول لتسجيل الخروج",
        "name_en": "Logout Access",
        "category": "auth",
        "description": "Access to logout functionality",
        "sort_order": 2
    },
    {
        "key": "auth.session.view",
        "name": "View Session Info",
        "name_ar": "عرض معلومات الجلسة",
        "name_en": "View Session Info",
        "category": "auth",
        "description": "View current session information",
        "sort_order": 3
    },
    {
        "key": "auth.session.manage",
        "name": "Manage Sessions",
        "name_ar": "إدارة الجلسات",
        "name_en": "Manage Sessions",
        "category": "auth",
        "description": "Manage user sessions (terminate, refresh)",
        "sort_order": 4
    },
    {
        "key": "auth.force_logout",
        "name": "Force Logout Users",
        "name_ar": "إجبار تسجيل الخروج",
        "name_en": "Force Logout Users",
        "category": "auth",
        "description": "Force logout other users from their sessions",
        "sort_order": 5
    },

    # ============ PASSWORD RESET CATEGORY ============
    {
        "key": "password_reset.request",
        "name": "Request Password Reset",
        "name_ar": "طلب إعادة تعيين كلمة المرور",
        "name_en": "Request Password Reset",
        "category": "password_reset",
        "description": "Request a password reset link",
        "sort_order": 1
    },
    {
        "key": "password_reset.verify",
        "name": "Verify Reset Token",
        "name_ar": "التحقق من رمز إعادة التعيين",
        "name_en": "Verify Reset Token",
        "category": "password_reset",
        "description": "Verify password reset token",
        "sort_order": 2
    },
    {
        "key": "password_reset.complete",
        "name": "Complete Password Reset",
        "name_ar": "إكمال إعادة تعيين كلمة المرور",
        "name_en": "Complete Password Reset",
        "category": "password_reset",
        "description": "Complete the password reset process",
        "sort_order": 3
    },
    {
        "key": "password_reset.admin_reset",
        "name": "Admin Password Reset",
        "name_ar": "إعادة تعيين كلمة المرور من المسؤول",
        "name_en": "Admin Password Reset",
        "category": "password_reset",
        "description": "Admin can reset any user password",
        "sort_order": 4
    },
    {
        "key": "password_reset.view_requests",
        "name": "View Reset Requests",
        "name_ar": "عرض طلبات إعادة التعيين",
        "name_en": "View Reset Requests",
        "category": "password_reset",
        "description": "View password reset request history",
        "sort_order": 5
    },

    # ============ DASHBOARD API CATEGORY ============
    {
        "key": "dashboard_api.charts",
        "name": "Dashboard Charts",
        "name_ar": "رسوم لوحة التحكم البيانية",
        "name_en": "Dashboard Charts",
        "category": "dashboard_api",
        "description": "Access to dashboard chart data",
        "sort_order": 1
    },
    {
        "key": "dashboard_api.statistics",
        "name": "Dashboard Statistics",
        "name_ar": "إحصائيات لوحة التحكم",
        "name_en": "Dashboard Statistics",
        "category": "dashboard_api",
        "description": "Access to dashboard statistics",
        "sort_order": 2
    },
    {
        "key": "dashboard_api.analytics",
        "name": "Dashboard Analytics",
        "name_ar": "تحليلات لوحة التحكم",
        "name_en": "Dashboard Analytics",
        "category": "dashboard_api",
        "description": "Access to advanced analytics data",
        "sort_order": 3
    },
    {
        "key": "dashboard_api.reports_summary",
        "name": "Reports Summary",
        "name_ar": "ملخص التقارير",
        "name_en": "Reports Summary",
        "category": "dashboard_api",
        "description": "Access to reports summary data",
        "sort_order": 4
    },
    {
        "key": "dashboard_api.dogs_status",
        "name": "Dogs Status Overview",
        "name_ar": "نظرة عامة على حالة الكلاب",
        "name_en": "Dogs Status Overview",
        "category": "dashboard_api",
        "description": "Access to dogs status overview data",
        "sort_order": 5
    },
    {
        "key": "dashboard_api.projects_status",
        "name": "Projects Status Overview",
        "name_ar": "نظرة عامة على حالة المشاريع",
        "name_en": "Projects Status Overview",
        "category": "dashboard_api",
        "description": "Access to projects status overview data",
        "sort_order": 6
    },
    {
        "key": "dashboard_api.employees_status",
        "name": "Employees Status Overview",
        "name_ar": "نظرة عامة على حالة الموظفين",
        "name_en": "Employees Status Overview",
        "category": "dashboard_api",
        "description": "Access to employees status overview data",
        "sort_order": 7
    },
    {
        "key": "dashboard_api.breeding_status",
        "name": "Breeding Status Overview",
        "name_ar": "نظرة عامة على حالة التربية",
        "name_en": "Breeding Status Overview",
        "category": "dashboard_api",
        "description": "Access to breeding status overview data",
        "sort_order": 8
    },

    # ============ MATURITY CATEGORY ============
    {
        "key": "maturity.view",
        "name": "View Maturity Records",
        "name_ar": "عرض سجلات النضوج",
        "name_en": "View Maturity Records",
        "category": "maturity",
        "description": "View dog maturity records",
        "sort_order": 1
    },
    {
        "key": "maturity.create",
        "name": "Create Maturity Record",
        "name_ar": "إنشاء سجل نضوج",
        "name_en": "Create Maturity Record",
        "category": "maturity",
        "description": "Create new maturity record",
        "sort_order": 2
    },
    {
        "key": "maturity.edit",
        "name": "Edit Maturity Record",
        "name_ar": "تعديل سجل النضوج",
        "name_en": "Edit Maturity Record",
        "category": "maturity",
        "description": "Edit existing maturity record",
        "sort_order": 3
    },
    {
        "key": "maturity.delete",
        "name": "Delete Maturity Record",
        "name_ar": "حذف سجل النضوج",
        "name_en": "Delete Maturity Record",
        "category": "maturity",
        "description": "Delete maturity record",
        "sort_order": 4
    },

    # ============ HEAT CYCLES CATEGORY ============
    {
        "key": "heat_cycles.view",
        "name": "View Heat Cycles",
        "name_ar": "عرض دورات الحرارة",
        "name_en": "View Heat Cycles",
        "category": "heat_cycles",
        "description": "View heat cycle records",
        "sort_order": 1
    },
    {
        "key": "heat_cycles.create",
        "name": "Create Heat Cycle",
        "name_ar": "إنشاء دورة حرارة",
        "name_en": "Create Heat Cycle",
        "category": "heat_cycles",
        "description": "Create new heat cycle record",
        "sort_order": 2
    },
    {
        "key": "heat_cycles.edit",
        "name": "Edit Heat Cycle",
        "name_ar": "تعديل دورة الحرارة",
        "name_en": "Edit Heat Cycle",
        "category": "heat_cycles",
        "description": "Edit existing heat cycle record",
        "sort_order": 3
    },
    {
        "key": "heat_cycles.delete",
        "name": "Delete Heat Cycle",
        "name_ar": "حذف دورة الحرارة",
        "name_en": "Delete Heat Cycle",
        "category": "heat_cycles",
        "description": "Delete heat cycle record",
        "sort_order": 4
    },

    # ============ MATING CATEGORY ============
    {
        "key": "mating.view",
        "name": "View Mating Records",
        "name_ar": "عرض سجلات التزاوج",
        "name_en": "View Mating Records",
        "category": "mating",
        "description": "View mating records",
        "sort_order": 1
    },
    {
        "key": "mating.create",
        "name": "Create Mating Record",
        "name_ar": "إنشاء سجل تزاوج",
        "name_en": "Create Mating Record",
        "category": "mating",
        "description": "Create new mating record",
        "sort_order": 2
    },
    {
        "key": "mating.edit",
        "name": "Edit Mating Record",
        "name_ar": "تعديل سجل التزاوج",
        "name_en": "Edit Mating Record",
        "category": "mating",
        "description": "Edit existing mating record",
        "sort_order": 3
    },
    {
        "key": "mating.delete",
        "name": "Delete Mating Record",
        "name_ar": "حذف سجل التزاوج",
        "name_en": "Delete Mating Record",
        "category": "mating",
        "description": "Delete mating record",
        "sort_order": 4
    },

    # ============ PREGNANCY CATEGORY ============
    {
        "key": "pregnancy.view",
        "name": "View Pregnancy Records",
        "name_ar": "عرض سجلات الحمل",
        "name_en": "View Pregnancy Records",
        "category": "pregnancy",
        "description": "View pregnancy records",
        "sort_order": 1
    },
    {
        "key": "pregnancy.create",
        "name": "Create Pregnancy Record",
        "name_ar": "إنشاء سجل حمل",
        "name_en": "Create Pregnancy Record",
        "category": "pregnancy",
        "description": "Create new pregnancy record",
        "sort_order": 2
    },
    {
        "key": "pregnancy.edit",
        "name": "Edit Pregnancy Record",
        "name_ar": "تعديل سجل الحمل",
        "name_en": "Edit Pregnancy Record",
        "category": "pregnancy",
        "description": "Edit existing pregnancy record",
        "sort_order": 3
    },
    {
        "key": "pregnancy.delete",
        "name": "Delete Pregnancy Record",
        "name_ar": "حذف سجل الحمل",
        "name_en": "Delete Pregnancy Record",
        "category": "pregnancy",
        "description": "Delete pregnancy record",
        "sort_order": 4
    },
    {
        "key": "pregnancy.track",
        "name": "Track Pregnancy Progress",
        "name_ar": "تتبع تقدم الحمل",
        "name_en": "Track Pregnancy Progress",
        "category": "pregnancy",
        "description": "Track pregnancy milestones and progress",
        "sort_order": 5
    },

    # ============ DELIVERY CATEGORY ============
    {
        "key": "delivery.view",
        "name": "View Delivery Records",
        "name_ar": "عرض سجلات الولادة",
        "name_en": "View Delivery Records",
        "category": "delivery",
        "description": "View delivery/birth records",
        "sort_order": 1
    },
    {
        "key": "delivery.create",
        "name": "Create Delivery Record",
        "name_ar": "إنشاء سجل ولادة",
        "name_en": "Create Delivery Record",
        "category": "delivery",
        "description": "Create new delivery record",
        "sort_order": 2
    },
    {
        "key": "delivery.edit",
        "name": "Edit Delivery Record",
        "name_ar": "تعديل سجل الولادة",
        "name_en": "Edit Delivery Record",
        "category": "delivery",
        "description": "Edit existing delivery record",
        "sort_order": 3
    },
    {
        "key": "delivery.delete",
        "name": "Delete Delivery Record",
        "name_ar": "حذف سجل الولادة",
        "name_en": "Delete Delivery Record",
        "category": "delivery",
        "description": "Delete delivery record",
        "sort_order": 4
    },

    # ============ PUPPIES CATEGORY ============
    {
        "key": "puppies.view",
        "name": "View Puppies",
        "name_ar": "عرض الجراء",
        "name_en": "View Puppies",
        "category": "puppies",
        "description": "View puppy records",
        "sort_order": 1
    },
    {
        "key": "puppies.create",
        "name": "Create Puppy Record",
        "name_ar": "إنشاء سجل جرو",
        "name_en": "Create Puppy Record",
        "category": "puppies",
        "description": "Create new puppy record",
        "sort_order": 2
    },
    {
        "key": "puppies.edit",
        "name": "Edit Puppy Record",
        "name_ar": "تعديل سجل الجرو",
        "name_en": "Edit Puppy Record",
        "category": "puppies",
        "description": "Edit existing puppy record",
        "sort_order": 3
    },
    {
        "key": "puppies.delete",
        "name": "Delete Puppy Record",
        "name_ar": "حذف سجل الجرو",
        "name_en": "Delete Puppy Record",
        "category": "puppies",
        "description": "Delete puppy record",
        "sort_order": 4
    },
    {
        "key": "puppies.transfer",
        "name": "Transfer Puppy",
        "name_ar": "نقل الجرو",
        "name_en": "Transfer Puppy",
        "category": "puppies",
        "description": "Transfer puppy to another project or handler",
        "sort_order": 5
    },
    {
        "key": "puppies.graduate",
        "name": "Graduate Puppy to Dog",
        "name_ar": "تخريج الجرو إلى كلب",
        "name_en": "Graduate Puppy to Dog",
        "category": "puppies",
        "description": "Graduate puppy to adult dog status",
        "sort_order": 6
    },

    # ============ PUPPY TRAINING CATEGORY ============
    {
        "key": "puppy_training.view",
        "name": "View Puppy Training",
        "name_ar": "عرض تدريب الجراء",
        "name_en": "View Puppy Training",
        "category": "puppy_training",
        "description": "View puppy training records",
        "sort_order": 1
    },
    {
        "key": "puppy_training.create",
        "name": "Create Puppy Training",
        "name_ar": "إنشاء تدريب جرو",
        "name_en": "Create Puppy Training",
        "category": "puppy_training",
        "description": "Create new puppy training record",
        "sort_order": 2
    },
    {
        "key": "puppy_training.edit",
        "name": "Edit Puppy Training",
        "name_ar": "تعديل تدريب الجرو",
        "name_en": "Edit Puppy Training",
        "category": "puppy_training",
        "description": "Edit existing puppy training record",
        "sort_order": 3
    },
    {
        "key": "puppy_training.delete",
        "name": "Delete Puppy Training",
        "name_ar": "حذف تدريب الجرو",
        "name_en": "Delete Puppy Training",
        "category": "puppy_training",
        "description": "Delete puppy training record",
        "sort_order": 4
    },
    {
        "key": "puppy_training.evaluate",
        "name": "Evaluate Puppy Training",
        "name_ar": "تقييم تدريب الجرو",
        "name_en": "Evaluate Puppy Training",
        "category": "puppy_training",
        "description": "Evaluate puppy training progress",
        "sort_order": 5
    },

    # ============ DEWORMING CATEGORY ============
    {
        "key": "deworming.view",
        "name": "View Deworming Records",
        "name_ar": "عرض سجلات التطعيم",
        "name_en": "View Deworming Records",
        "category": "deworming",
        "description": "View deworming records",
        "sort_order": 1
    },
    {
        "key": "deworming.create",
        "name": "Create Deworming Record",
        "name_ar": "إنشاء سجل تطعيم",
        "name_en": "Create Deworming Record",
        "category": "deworming",
        "description": "Create new deworming record",
        "sort_order": 2
    },
    {
        "key": "deworming.edit",
        "name": "Edit Deworming Record",
        "name_ar": "تعديل سجل التطعيم",
        "name_en": "Edit Deworming Record",
        "category": "deworming",
        "description": "Edit existing deworming record",
        "sort_order": 3
    },
    {
        "key": "deworming.delete",
        "name": "Delete Deworming Record",
        "name_ar": "حذف سجل التطعيم",
        "name_en": "Delete Deworming Record",
        "category": "deworming",
        "description": "Delete deworming record",
        "sort_order": 4
    },

    # ============ ATTENDANCE CATEGORY ============
    {
        "key": "attendance.view",
        "name": "View Attendance",
        "name_ar": "عرض الحضور",
        "name_en": "View Attendance",
        "category": "attendance",
        "description": "View attendance records",
        "sort_order": 1
    },
    {
        "key": "attendance.create",
        "name": "Create Attendance",
        "name_ar": "إنشاء سجل حضور",
        "name_en": "Create Attendance",
        "category": "attendance",
        "description": "Create attendance record",
        "sort_order": 2
    },
    {
        "key": "attendance.edit",
        "name": "Edit Attendance",
        "name_ar": "تعديل الحضور",
        "name_en": "Edit Attendance",
        "category": "attendance",
        "description": "Edit attendance record",
        "sort_order": 3
    },
    {
        "key": "attendance.delete",
        "name": "Delete Attendance",
        "name_ar": "حذف الحضور",
        "name_en": "Delete Attendance",
        "category": "attendance",
        "description": "Delete attendance record",
        "sort_order": 4
    },
    {
        "key": "attendance.report",
        "name": "Attendance Report",
        "name_ar": "تقرير الحضور",
        "name_en": "Attendance Report",
        "category": "attendance",
        "description": "Generate attendance reports",
        "sort_order": 5
    },

    # ============ SETTINGS CATEGORY ============
    {
        "key": "settings.view",
        "name": "View Settings",
        "name_ar": "عرض الإعدادات",
        "name_en": "View Settings",
        "category": "settings",
        "description": "View system settings",
        "sort_order": 1
    },
    {
        "key": "settings.edit",
        "name": "Edit Settings",
        "name_ar": "تعديل الإعدادات",
        "name_en": "Edit Settings",
        "category": "settings",
        "description": "Edit system settings",
        "sort_order": 2
    },
    {
        "key": "settings.backup",
        "name": "Backup Settings",
        "name_ar": "إعدادات النسخ الاحتياطي",
        "name_en": "Backup Settings",
        "category": "settings",
        "description": "Configure backup settings",
        "sort_order": 3
    },
    {
        "key": "settings.notifications",
        "name": "Notification Settings",
        "name_ar": "إعدادات الإشعارات",
        "name_en": "Notification Settings",
        "category": "settings",
        "description": "Configure notification settings",
        "sort_order": 4
    },
    {
        "key": "settings.security",
        "name": "Security Settings",
        "name_ar": "إعدادات الأمان",
        "name_en": "Security Settings",
        "category": "settings",
        "description": "Configure security settings",
        "sort_order": 5
    },

    # ============ AUDIT LOG CATEGORY ============
    {
        "key": "audit_log.view",
        "name": "View Audit Log",
        "name_ar": "عرض سجل التدقيق",
        "name_en": "View Audit Log",
        "category": "audit_log",
        "description": "View system audit log",
        "sort_order": 1
    },
    {
        "key": "audit_log.export",
        "name": "Export Audit Log",
        "name_ar": "تصدير سجل التدقيق",
        "name_en": "Export Audit Log",
        "category": "audit_log",
        "description": "Export audit log data",
        "sort_order": 2
    },
    {
        "key": "audit_log.filter",
        "name": "Filter Audit Log",
        "name_ar": "تصفية سجل التدقيق",
        "name_en": "Filter Audit Log",
        "category": "audit_log",
        "description": "Filter audit log by criteria",
        "sort_order": 3
    },

    # ============ SYSTEM CATEGORY ============
    {
        "key": "system.health",
        "name": "System Health",
        "name_ar": "صحة النظام",
        "name_en": "System Health",
        "category": "system",
        "description": "View system health status",
        "sort_order": 1
    },
    {
        "key": "system.logs",
        "name": "System Logs",
        "name_ar": "سجلات النظام",
        "name_en": "System Logs",
        "category": "system",
        "description": "View system logs",
        "sort_order": 2
    },
    {
        "key": "system.maintenance",
        "name": "System Maintenance",
        "name_ar": "صيانة النظام",
        "name_en": "System Maintenance",
        "category": "system",
        "description": "Perform system maintenance tasks",
        "sort_order": 3
    },
    {
        "key": "system.cache",
        "name": "Cache Management",
        "name_ar": "إدارة التخزين المؤقت",
        "name_en": "Cache Management",
        "category": "system",
        "description": "Manage system cache",
        "sort_order": 4
    },
]


def seed_missing_permissions():
    """Seed all missing category permissions into the database"""
    with app.app_context():
        print("=" * 60)
        print("Missing Categories Permissions Seeding")
        print("=" * 60)
        print(f"\nProcessing {len(MISSING_PERMISSIONS)} new permissions...\n")
        
        created = 0
        updated = 0
        skipped = 0
        
        for perm_data in MISSING_PERMISSIONS:
            existing = Permission.query.filter_by(key=perm_data['key']).first()
            
            if existing:
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
        print(f"  Total:   {len(MISSING_PERMISSIONS)} permissions processed")
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
    seed_missing_permissions()
