"""
Add Missing Permissions Script
This script adds permissions for categories that were missed during initial seeding.
These categories are used in the code but were not included in permissions_map.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission

MISSING_PERMISSIONS = [
    # Cleaning category - used in api_cleaning.py
    {'key': 'cleaning.view', 'name_ar': 'التنظيف - عرض', 'name_en': 'Cleaning - View', 'category': 'cleaning', 'description': 'عرض سجلات التنظيف'},
    {'key': 'cleaning.create', 'name_ar': 'التنظيف - إضافة', 'name_en': 'Cleaning - Create', 'category': 'cleaning', 'description': 'إضافة سجل تنظيف جديد'},
    {'key': 'cleaning.edit', 'name_ar': 'التنظيف - تعديل', 'name_en': 'Cleaning - Edit', 'category': 'cleaning', 'description': 'تعديل سجلات التنظيف'},
    {'key': 'cleaning.delete', 'name_ar': 'التنظيف - حذف', 'name_en': 'Cleaning - Delete', 'category': 'cleaning', 'description': 'حذف سجلات التنظيف'},
    {'key': 'cleaning.export', 'name_ar': 'التنظيف - تصدير', 'name_en': 'Cleaning - Export', 'category': 'cleaning', 'description': 'تصدير سجلات التنظيف'},
    
    # Suspicions category - used in main.py
    {'key': 'suspicions.view', 'name_ar': 'الشبهات - عرض', 'name_en': 'Suspicions - View', 'category': 'suspicions', 'description': 'عرض حالات الاشتباه'},
    {'key': 'suspicions.create', 'name_ar': 'الشبهات - إضافة', 'name_en': 'Suspicions - Create', 'category': 'suspicions', 'description': 'إضافة حالة اشتباه جديدة'},
    {'key': 'suspicions.edit', 'name_ar': 'الشبهات - تعديل', 'name_en': 'Suspicions - Edit', 'category': 'suspicions', 'description': 'تعديل حالات الاشتباه'},
    {'key': 'suspicions.delete', 'name_ar': 'الشبهات - حذف', 'name_en': 'Suspicions - Delete', 'category': 'suspicions', 'description': 'حذف حالات الاشتباه'},
    {'key': 'suspicions.export', 'name_ar': 'الشبهات - تصدير', 'name_en': 'Suspicions - Export', 'category': 'suspicions', 'description': 'تصدير تقارير الاشتباه'},
    {'key': 'suspicions.confirm', 'name_ar': 'الشبهات - تأكيد', 'name_en': 'Suspicions - Confirm', 'category': 'suspicions', 'description': 'تأكيد حالة اشتباه'},
    
    # Evaluations category - used in main.py
    {'key': 'evaluations.view', 'name_ar': 'التقييمات - عرض', 'name_en': 'Evaluations - View', 'category': 'evaluations', 'description': 'عرض التقييمات'},
    {'key': 'evaluations.create', 'name_ar': 'التقييمات - إضافة', 'name_en': 'Evaluations - Create', 'category': 'evaluations', 'description': 'إضافة تقييم جديد'},
    {'key': 'evaluations.edit', 'name_ar': 'التقييمات - تعديل', 'name_en': 'Evaluations - Edit', 'category': 'evaluations', 'description': 'تعديل التقييمات'},
    {'key': 'evaluations.delete', 'name_ar': 'التقييمات - حذف', 'name_en': 'Evaluations - Delete', 'category': 'evaluations', 'description': 'حذف التقييمات'},
    {'key': 'evaluations.export', 'name_ar': 'التقييمات - تصدير', 'name_en': 'Evaluations - Export', 'category': 'evaluations', 'description': 'تصدير التقييمات'},
    {'key': 'evaluations.approve', 'name_ar': 'التقييمات - اعتماد', 'name_en': 'Evaluations - Approve', 'category': 'evaluations', 'description': 'اعتماد التقييمات'},
    
    # Locations category - for project locations
    {'key': 'locations.view', 'name_ar': 'المواقع - عرض', 'name_en': 'Locations - View', 'category': 'locations', 'description': 'عرض المواقع'},
    {'key': 'locations.create', 'name_ar': 'المواقع - إضافة', 'name_en': 'Locations - Create', 'category': 'locations', 'description': 'إضافة موقع جديد'},
    {'key': 'locations.edit', 'name_ar': 'المواقع - تعديل', 'name_en': 'Locations - Edit', 'category': 'locations', 'description': 'تعديل المواقع'},
    {'key': 'locations.delete', 'name_ar': 'المواقع - حذف', 'name_en': 'Locations - Delete', 'category': 'locations', 'description': 'حذف المواقع'},
    {'key': 'locations.assign', 'name_ar': 'المواقع - تعيين', 'name_en': 'Locations - Assign', 'category': 'locations', 'description': 'تعيين الموظفين للمواقع'},
    
    # Assignments category - for project assignments
    {'key': 'assignments.view', 'name_ar': 'التعيينات - عرض', 'name_en': 'Assignments - View', 'category': 'assignments', 'description': 'عرض التعيينات'},
    {'key': 'assignments.create', 'name_ar': 'التعيينات - إضافة', 'name_en': 'Assignments - Create', 'category': 'assignments', 'description': 'إضافة تعيين جديد'},
    {'key': 'assignments.edit', 'name_ar': 'التعيينات - تعديل', 'name_en': 'Assignments - Edit', 'category': 'assignments', 'description': 'تعديل التعيينات'},
    {'key': 'assignments.delete', 'name_ar': 'التعيينات - حذف', 'name_en': 'Assignments - Delete', 'category': 'assignments', 'description': 'حذف التعيينات'},
    {'key': 'assignments.dogs.manage', 'name_ar': 'التعيينات - إدارة الكلاب', 'name_en': 'Assignments - Manage Dogs', 'category': 'assignments', 'description': 'إدارة تعيينات الكلاب للمشاريع'},
    {'key': 'assignments.employees.manage', 'name_ar': 'التعيينات - إدارة الموظفين', 'name_en': 'Assignments - Manage Employees', 'category': 'assignments', 'description': 'إدارة تعيينات الموظفين للمشاريع'},
    
    # Backup category - admin backup functionality
    {'key': 'backup.view', 'name_ar': 'النسخ الاحتياطي - عرض', 'name_en': 'Backup - View', 'category': 'backup', 'description': 'عرض النسخ الاحتياطية'},
    {'key': 'backup.create', 'name_ar': 'النسخ الاحتياطي - إنشاء', 'name_en': 'Backup - Create', 'category': 'backup', 'description': 'إنشاء نسخة احتياطية'},
    {'key': 'backup.restore', 'name_ar': 'النسخ الاحتياطي - استعادة', 'name_en': 'Backup - Restore', 'category': 'backup', 'description': 'استعادة نسخة احتياطية'},
    {'key': 'backup.delete', 'name_ar': 'النسخ الاحتياطي - حذف', 'name_en': 'Backup - Delete', 'category': 'backup', 'description': 'حذف النسخ الاحتياطية'},
    {'key': 'backup.settings', 'name_ar': 'النسخ الاحتياطي - إعدادات', 'name_en': 'Backup - Settings', 'category': 'backup', 'description': 'إعدادات النسخ الاحتياطي التلقائي'},
    {'key': 'backup.google_drive', 'name_ar': 'النسخ الاحتياطي - جوجل درايف', 'name_en': 'Backup - Google Drive', 'category': 'backup', 'description': 'ربط النسخ الاحتياطي بجوجل درايف'},
    
    # Settings category - system settings
    {'key': 'settings.view', 'name_ar': 'الإعدادات - عرض', 'name_en': 'Settings - View', 'category': 'settings', 'description': 'عرض إعدادات النظام'},
    {'key': 'settings.edit', 'name_ar': 'الإعدادات - تعديل', 'name_en': 'Settings - Edit', 'category': 'settings', 'description': 'تعديل إعدادات النظام'},
    {'key': 'settings.security', 'name_ar': 'الإعدادات - الأمان', 'name_en': 'Settings - Security', 'category': 'settings', 'description': 'إعدادات الأمان'},
    {'key': 'settings.notifications', 'name_ar': 'الإعدادات - الإشعارات', 'name_en': 'Settings - Notifications', 'category': 'settings', 'description': 'إعدادات الإشعارات'},
    
    # Dictionaries/Lookups category - data dictionaries
    {'key': 'dictionaries.view', 'name_ar': 'القوائم المرجعية - عرض', 'name_en': 'Dictionaries - View', 'category': 'dictionaries', 'description': 'عرض القوائم المرجعية'},
    {'key': 'dictionaries.edit', 'name_ar': 'القوائم المرجعية - تعديل', 'name_en': 'Dictionaries - Edit', 'category': 'dictionaries', 'description': 'تعديل القوائم المرجعية'},
    {'key': 'dictionaries.breeds', 'name_ar': 'القوائم المرجعية - السلالات', 'name_en': 'Dictionaries - Breeds', 'category': 'dictionaries', 'description': 'إدارة قائمة السلالات'},
    {'key': 'dictionaries.colors', 'name_ar': 'القوائم المرجعية - الألوان', 'name_en': 'Dictionaries - Colors', 'category': 'dictionaries', 'description': 'إدارة قائمة الألوان'},
    {'key': 'dictionaries.specializations', 'name_ar': 'القوائم المرجعية - التخصصات', 'name_en': 'Dictionaries - Specializations', 'category': 'dictionaries', 'description': 'إدارة قائمة التخصصات'},
    
    # Audit category - audit logs
    {'key': 'audit.view', 'name_ar': 'سجل التدقيق - عرض', 'name_en': 'Audit - View', 'category': 'audit', 'description': 'عرض سجل التدقيق'},
    {'key': 'audit.export', 'name_ar': 'سجل التدقيق - تصدير', 'name_en': 'Audit - Export', 'category': 'audit', 'description': 'تصدير سجل التدقيق'},
    {'key': 'audit.filter', 'name_ar': 'سجل التدقيق - تصفية', 'name_en': 'Audit - Filter', 'category': 'audit', 'description': 'تصفية سجل التدقيق'},
    
    # User Management category
    {'key': 'users.view', 'name_ar': 'المستخدمين - عرض', 'name_en': 'Users - View', 'category': 'users', 'description': 'عرض المستخدمين'},
    {'key': 'users.create', 'name_ar': 'المستخدمين - إضافة', 'name_en': 'Users - Create', 'category': 'users', 'description': 'إضافة مستخدم جديد'},
    {'key': 'users.edit', 'name_ar': 'المستخدمين - تعديل', 'name_en': 'Users - Edit', 'category': 'users', 'description': 'تعديل بيانات المستخدمين'},
    {'key': 'users.delete', 'name_ar': 'المستخدمين - حذف', 'name_en': 'Users - Delete', 'category': 'users', 'description': 'حذف المستخدمين'},
    {'key': 'users.reset_password', 'name_ar': 'المستخدمين - إعادة تعيين كلمة المرور', 'name_en': 'Users - Reset Password', 'category': 'users', 'description': 'إعادة تعيين كلمة مرور المستخدم'},
    {'key': 'users.permissions', 'name_ar': 'المستخدمين - إدارة الصلاحيات', 'name_en': 'Users - Manage Permissions', 'category': 'users', 'description': 'إدارة صلاحيات المستخدمين'},
    {'key': 'users.activate', 'name_ar': 'المستخدمين - تفعيل/تعطيل', 'name_en': 'Users - Activate/Deactivate', 'category': 'users', 'description': 'تفعيل وتعطيل حسابات المستخدمين'},
    
    # Grooming category - dog grooming
    {'key': 'grooming.view', 'name_ar': 'العناية - عرض', 'name_en': 'Grooming - View', 'category': 'grooming', 'description': 'عرض سجلات العناية'},
    {'key': 'grooming.create', 'name_ar': 'العناية - إضافة', 'name_en': 'Grooming - Create', 'category': 'grooming', 'description': 'إضافة سجل عناية جديد'},
    {'key': 'grooming.edit', 'name_ar': 'العناية - تعديل', 'name_en': 'Grooming - Edit', 'category': 'grooming', 'description': 'تعديل سجلات العناية'},
    {'key': 'grooming.delete', 'name_ar': 'العناية - حذف', 'name_en': 'Grooming - Delete', 'category': 'grooming', 'description': 'حذف سجلات العناية'},
    
    # Excretion category - dog excretion logs
    {'key': 'excretion.view', 'name_ar': 'الإخراج - عرض', 'name_en': 'Excretion - View', 'category': 'excretion', 'description': 'عرض سجلات الإخراج'},
    {'key': 'excretion.create', 'name_ar': 'الإخراج - إضافة', 'name_en': 'Excretion - Create', 'category': 'excretion', 'description': 'إضافة سجل إخراج جديد'},
    {'key': 'excretion.edit', 'name_ar': 'الإخراج - تعديل', 'name_en': 'Excretion - Edit', 'category': 'excretion', 'description': 'تعديل سجلات الإخراج'},
    {'key': 'excretion.delete', 'name_ar': 'الإخراج - حذف', 'name_en': 'Excretion - Delete', 'category': 'excretion', 'description': 'حذف سجلات الإخراج'},
    
    # Deworming category
    {'key': 'deworming.view', 'name_ar': 'مكافحة الديدان - عرض', 'name_en': 'Deworming - View', 'category': 'deworming', 'description': 'عرض سجلات مكافحة الديدان'},
    {'key': 'deworming.create', 'name_ar': 'مكافحة الديدان - إضافة', 'name_en': 'Deworming - Create', 'category': 'deworming', 'description': 'إضافة سجل مكافحة ديدان جديد'},
    {'key': 'deworming.edit', 'name_ar': 'مكافحة الديدان - تعديل', 'name_en': 'Deworming - Edit', 'category': 'deworming', 'description': 'تعديل سجلات مكافحة الديدان'},
    {'key': 'deworming.delete', 'name_ar': 'مكافحة الديدان - حذف', 'name_en': 'Deworming - Delete', 'category': 'deworming', 'description': 'حذف سجلات مكافحة الديدان'},
]

CATEGORY_METADATA = {
    'cleaning': {'ar': 'التنظيف', 'en': 'Cleaning', 'icon': 'fa-broom'},
    'suspicions': {'ar': 'الشبهات', 'en': 'Suspicions', 'icon': 'fa-search-plus'},
    'evaluations': {'ar': 'التقييمات', 'en': 'Evaluations', 'icon': 'fa-star'},
    'locations': {'ar': 'المواقع', 'en': 'Locations', 'icon': 'fa-map-marker-alt'},
    'assignments': {'ar': 'التعيينات', 'en': 'Assignments', 'icon': 'fa-user-check'},
    'backup': {'ar': 'النسخ الاحتياطي', 'en': 'Backup', 'icon': 'fa-database'},
    'settings': {'ar': 'الإعدادات', 'en': 'Settings', 'icon': 'fa-cog'},
    'dictionaries': {'ar': 'القوائم المرجعية', 'en': 'Dictionaries', 'icon': 'fa-book'},
    'audit': {'ar': 'سجل التدقيق', 'en': 'Audit Log', 'icon': 'fa-history'},
    'users': {'ar': 'إدارة المستخدمين', 'en': 'User Management', 'icon': 'fa-users-cog'},
    'grooming': {'ar': 'العناية', 'en': 'Grooming', 'icon': 'fa-cut'},
    'excretion': {'ar': 'الإخراج', 'en': 'Excretion', 'icon': 'fa-toilet'},
    'deworming': {'ar': 'مكافحة الديدان', 'en': 'Deworming', 'icon': 'fa-bug'},
}

def add_missing_permissions():
    """Add all missing permissions to the database."""
    print("=" * 60)
    print("ADDING MISSING PERMISSIONS")
    print("=" * 60)
    
    with app.app_context():
        existing_count = Permission.query.count()
        print(f"Existing permissions in database: {existing_count}")
        
        added = 0
        skipped = 0
        
        for idx, perm_data in enumerate(MISSING_PERMISSIONS):
            key = perm_data['key']
            
            existing = Permission.query.filter_by(key=key).first()
            
            if existing:
                skipped += 1
                continue
            
            perm = Permission(
                key=key,
                name=perm_data['name_ar'],
                name_ar=perm_data['name_ar'],
                name_en=perm_data['name_en'],
                description=perm_data.get('description', ''),
                category=perm_data['category'],
                sort_order=existing_count + idx,
                is_active=True
            )
            db.session.add(perm)
            added += 1
        
        db.session.commit()
        
        print(f"\nAdded: {added} new permissions")
        print(f"Skipped: {skipped} (already exist)")
        
        final_count = Permission.query.count()
        print(f"Total permissions in database: {final_count}")
        
        print("\n" + "=" * 60)
        print("PERMISSION CATEGORIES SUMMARY")
        print("=" * 60)
        
        from sqlalchemy import func
        categories = db.session.query(
            Permission.category, 
            func.count(Permission.id).label('count')
        ).group_by(Permission.category).order_by(Permission.category).all()
        
        for cat, count in categories:
            meta = CATEGORY_METADATA.get(cat, {'ar': cat, 'en': cat})
            print(f"  - {cat}: {count} permissions ({meta.get('ar', cat)})")
        
        print(f"\nTotal categories: {len(categories)}")
        print("=" * 60)

if __name__ == '__main__':
    add_missing_permissions()
