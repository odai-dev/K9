"""
Fix Missing Code Permissions
This script adds ONLY permissions that are actually used in @require_permission decorators
but are missing from the database.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission

PERMISSIONS_USED_IN_CODE = [
    {'key': 'breeding.checkup', 'name_ar': 'التربية - الفحص الظاهري', 'category': 'breeding'},
    {'key': 'breeding.deworming', 'name_ar': 'التربية - مكافحة الديدان', 'category': 'breeding'},
    {'key': 'breeding.excretion', 'name_ar': 'التربية - الإخراج', 'category': 'breeding'},
    {'key': 'breeding.grooming', 'name_ar': 'التربية - العناية', 'category': 'breeding'},
    {'key': 'breeding.view', 'name_ar': 'التربية - عرض', 'category': 'breeding'},
    {'key': 'breeding.create', 'name_ar': 'التربية - إضافة', 'category': 'breeding'},
    {'key': 'breeding.edit', 'name_ar': 'التربية - تعديل', 'category': 'breeding'},
    {'key': 'dogs.create', 'name_ar': 'الكلاب - إضافة', 'category': 'dogs'},
    {'key': 'dogs.edit', 'name_ar': 'الكلاب - تعديل', 'category': 'dogs'},
    {'key': 'dogs.view', 'name_ar': 'الكلاب - عرض', 'category': 'dogs'},
    {'key': 'dogs.assign', 'name_ar': 'الكلاب - تعيين', 'category': 'dogs'},
    {'key': 'employees.create', 'name_ar': 'الموظفين - إضافة', 'category': 'employees'},
    {'key': 'employees.delete', 'name_ar': 'الموظفين - حذف', 'category': 'employees'},
    {'key': 'employees.edit', 'name_ar': 'الموظفين - تعديل', 'category': 'employees'},
    {'key': 'employees.view', 'name_ar': 'الموظفين - عرض', 'category': 'employees'},
    {'key': 'incidents.create', 'name_ar': 'الحوادث - إضافة', 'category': 'incidents'},
    {'key': 'incidents.resolve', 'name_ar': 'الحوادث - حل', 'category': 'incidents'},
    {'key': 'incidents.view', 'name_ar': 'الحوادث - عرض', 'category': 'incidents'},
    {'key': 'incidents.edit', 'name_ar': 'الحوادث - تعديل', 'category': 'incidents'},
    {'key': 'projects.create', 'name_ar': 'المشاريع - إضافة', 'category': 'projects'},
    {'key': 'projects.delete', 'name_ar': 'المشاريع - حذف', 'category': 'projects'},
    {'key': 'projects.edit', 'name_ar': 'المشاريع - تعديل', 'category': 'projects'},
    {'key': 'projects.view', 'name_ar': 'المشاريع - عرض', 'category': 'projects'},
    {'key': 'reports.attendance.view', 'name_ar': 'تقارير الحضور - عرض', 'category': 'reports'},
    {'key': 'reports.attendance.export', 'name_ar': 'تقارير الحضور - تصدير', 'category': 'reports'},
    {'key': 'reports.breeding.caretaker_daily.export', 'name_ar': 'تقارير العناية اليومية - تصدير', 'category': 'reports'},
    {'key': 'reports.breeding.caretaker_daily.view', 'name_ar': 'تقارير العناية اليومية - عرض', 'category': 'reports'},
    {'key': 'reports.breeding.checkup.export', 'name_ar': 'تقارير الفحص - تصدير', 'category': 'reports'},
    {'key': 'reports.breeding.checkup.view', 'name_ar': 'تقارير الفحص - عرض', 'category': 'reports'},
    {'key': 'reports.breeding.feeding.export', 'name_ar': 'تقارير التغذية - تصدير', 'category': 'reports'},
    {'key': 'reports.breeding.feeding.view', 'name_ar': 'تقارير التغذية - عرض', 'category': 'reports'},
    {'key': 'reports.veterinary.export', 'name_ar': 'التقارير البيطرية - تصدير', 'category': 'reports'},
    {'key': 'reports.veterinary.view', 'name_ar': 'التقارير البيطرية - عرض', 'category': 'reports'},
    {'key': 'reports.caretaker.view', 'name_ar': 'تقارير العناية - عرض', 'category': 'reports'},
    {'key': 'reports.caretaker_daily.view', 'name_ar': 'التقارير اليومية للعناية - عرض', 'category': 'reports'},
    {'key': 'reports.hub.view', 'name_ar': 'مركز التقارير - عرض', 'category': 'reports'},
    {'key': 'reports.training.view', 'name_ar': 'تقارير التدريب - عرض', 'category': 'reports'},
    {'key': 'reports.veterinary.legacy.access', 'name_ar': 'التقارير البيطرية القديمة - وصول', 'category': 'reports'},
    {'key': 'reports.veterinary.unified.view', 'name_ar': 'التقارير البيطرية الموحدة - عرض', 'category': 'reports'},
    {'key': 'schedule.create', 'name_ar': 'الجداول - إضافة', 'category': 'schedule'},
    {'key': 'schedule.edit', 'name_ar': 'الجداول - تعديل', 'category': 'schedule'},
    {'key': 'schedule.view', 'name_ar': 'الجداول - عرض', 'category': 'schedule'},
    {'key': 'schedule.management.create', 'name_ar': 'إدارة الجداول - إضافة', 'category': 'schedule'},
    {'key': 'shifts.create', 'name_ar': 'الورديات - إضافة', 'category': 'shifts'},
    {'key': 'shifts.edit', 'name_ar': 'الورديات - تعديل', 'category': 'shifts'},
    {'key': 'shifts.view', 'name_ar': 'الورديات - عرض', 'category': 'shifts'},
    {'key': 'tasks.approve', 'name_ar': 'المهام - موافقة', 'category': 'tasks'},
    {'key': 'tasks.create', 'name_ar': 'المهام - إضافة', 'category': 'tasks'},
    {'key': 'tasks.delete', 'name_ar': 'المهام - حذف', 'category': 'tasks'},
    {'key': 'tasks.edit', 'name_ar': 'المهام - تعديل', 'category': 'tasks'},
    {'key': 'tasks.view', 'name_ar': 'المهام - عرض', 'category': 'tasks'},
    {'key': 'tasks.assign', 'name_ar': 'المهام - تعيين', 'category': 'tasks'},
    {'key': 'training.create', 'name_ar': 'التدريب - إضافة', 'category': 'training'},
    {'key': 'training.delete', 'name_ar': 'التدريب - حذف', 'category': 'training'},
    {'key': 'training.edit', 'name_ar': 'التدريب - تعديل', 'category': 'training'},
    {'key': 'training.view', 'name_ar': 'التدريب - عرض', 'category': 'training'},
    {'key': 'training.add_session.create', 'name_ar': 'جلسات التدريب - إضافة', 'category': 'training'},
    {'key': 'training.view_sessions.view', 'name_ar': 'جلسات التدريب - عرض', 'category': 'training'},
    {'key': 'veterinary.create', 'name_ar': 'الرعاية البيطرية - إضافة', 'category': 'veterinary'},
    {'key': 'veterinary.view', 'name_ar': 'الرعاية البيطرية - عرض', 'category': 'veterinary'},
    {'key': 'veterinary.edit', 'name_ar': 'الرعاية البيطرية - تعديل', 'category': 'veterinary'},
    {'key': 'account_management.api.access', 'name_ar': 'إدارة الحسابات - وصول API', 'category': 'account'},
    {'key': 'account_management.create.access', 'name_ar': 'إدارة الحسابات - إنشاء', 'category': 'account'},
    {'key': 'account_management.index.view', 'name_ar': 'إدارة الحسابات - عرض القائمة', 'category': 'account'},
    {'key': 'account_management.reset_password.access', 'name_ar': 'إدارة الحسابات - إعادة تعيين كلمة المرور', 'category': 'account'},
    {'key': 'account_management.toggle_status.access', 'name_ar': 'إدارة الحسابات - تبديل الحالة', 'category': 'account'},
    {'key': 'admin.audit', 'name_ar': 'الإدارة - سجلات المراجعة', 'category': 'admin'},
    {'key': 'admin.backup', 'name_ar': 'الإدارة - النسخ الاحتياطي', 'category': 'admin'},
    {'key': 'admin.tasks.send', 'name_ar': 'الإدارة - إرسال المهام', 'category': 'admin'},
    {'key': 'handler_reports.approve', 'name_ar': 'تقارير المدربين - موافقة', 'category': 'handlers'},
    {'key': 'handler_reports.export', 'name_ar': 'تقارير المدربين - تصدير', 'category': 'handlers'},
    {'key': 'handler_reports.view', 'name_ar': 'تقارير المدربين - عرض', 'category': 'handlers'},
    {'key': 'pm.approvals', 'name_ar': 'مدير المشروع - الموافقات', 'category': 'pm'},
    {'key': 'pm.dogs', 'name_ar': 'مدير المشروع - الكلاب', 'category': 'pm'},
    {'key': 'pm.team', 'name_ar': 'مدير المشروع - الفريق', 'category': 'pm'},
    {'key': 'production.create', 'name_ar': 'الإنتاج - إضافة', 'category': 'production'},
    {'key': 'production.edit', 'name_ar': 'الإنتاج - تعديل', 'category': 'production'},
    {'key': 'production.heat_cycle.view', 'name_ar': 'دورة الحرارة - عرض', 'category': 'production'},
    {'key': 'production.overview.view', 'name_ar': 'نظرة عامة على الإنتاج - عرض', 'category': 'production'},
    {'key': 'production.view', 'name_ar': 'الإنتاج - عرض', 'category': 'production'},
    {'key': 'supervisor.approve', 'name_ar': 'المشرف - موافقة', 'category': 'supervisor'},
    {'key': 'supervisor.reports', 'name_ar': 'المشرف - التقارير', 'category': 'supervisor'},
    {'key': 'supervisor.schedules', 'name_ar': 'المشرف - الجداول', 'category': 'supervisor'},
]

def fix_missing_permissions():
    """Add missing permissions that are used in code."""
    print("=" * 60)
    print("FIXING MISSING CODE PERMISSIONS")
    print("=" * 60)
    
    with app.app_context():
        existing_keys = set(p.key for p in Permission.query.all())
        print(f"Existing permissions in database: {len(existing_keys)}")
        
        added = 0
        skipped = 0
        
        for perm_data in PERMISSIONS_USED_IN_CODE:
            key = perm_data['key']
            
            if key in existing_keys:
                skipped += 1
                continue
            
            perm = Permission(
                key=key,
                name=perm_data['name_ar'],
                name_ar=perm_data['name_ar'],
                name_en=key.replace('.', ' - ').replace('_', ' ').title(),
                category=perm_data['category'],
                is_active=True
            )
            db.session.add(perm)
            added += 1
            print(f"  + Added: {key}")
        
        db.session.commit()
        
        print(f"\n{'=' * 60}")
        print(f"Added: {added} new permissions")
        print(f"Skipped: {skipped} (already exist)")
        print(f"Total permissions in database: {Permission.query.count()}")
        print("=" * 60)

if __name__ == '__main__':
    fix_missing_permissions()
