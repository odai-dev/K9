"""
Seed All Permissions Script
This script populates the permissions table with ALL screens and actions from the system.
It reads from permissions_map.json and creates comprehensive permission entries.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.permissions_new import Permission

CATEGORY_NAMES = {
    'admin': {'ar': 'لوحة الإدارة', 'en': 'Admin Panel', 'icon': 'fa-cogs'},
    'api': {'ar': 'واجهة البرمجة', 'en': 'API', 'icon': 'fa-code'},
    'auth': {'ar': 'المصادقة', 'en': 'Authentication', 'icon': 'fa-key'},
    'breeding': {'ar': 'التربية والعناية', 'en': 'Breeding & Care', 'icon': 'fa-paw'},
    'dashboard': {'ar': 'لوحة التحكم', 'en': 'Dashboard', 'icon': 'fa-tachometer-alt'},
    'dogs': {'ar': 'إدارة الكلاب', 'en': 'Dogs Management', 'icon': 'fa-dog'},
    'employees': {'ar': 'إدارة الموظفين', 'en': 'Employees Management', 'icon': 'fa-users'},
    'general': {'ar': 'عام', 'en': 'General', 'icon': 'fa-globe'},
    'handlers': {'ar': 'السائسين', 'en': 'Handlers', 'icon': 'fa-user-tie'},
    'home': {'ar': 'الصفحة الرئيسية', 'en': 'Home', 'icon': 'fa-home'},
    'mfa': {'ar': 'المصادقة الثنائية', 'en': 'Two-Factor Auth', 'icon': 'fa-shield-alt'},
    'password_reset': {'ar': 'إعادة تعيين كلمة المرور', 'en': 'Password Reset', 'icon': 'fa-lock'},
    'pm': {'ar': 'مدير المشروع', 'en': 'Project Manager', 'icon': 'fa-user-cog'},
    'production': {'ar': 'الإنتاج والتكاثر', 'en': 'Production & Breeding', 'icon': 'fa-baby'},
    'projects': {'ar': 'إدارة المشاريع', 'en': 'Projects Management', 'icon': 'fa-project-diagram'},
    'reports': {'ar': 'التقارير', 'en': 'Reports', 'icon': 'fa-chart-bar'},
    'schedule': {'ar': 'الجداول', 'en': 'Schedules', 'icon': 'fa-calendar-alt'},
    'search': {'ar': 'البحث', 'en': 'Search', 'icon': 'fa-search'},
    'supervisor': {'ar': 'المشرف', 'en': 'Supervisor', 'icon': 'fa-user-shield'},
    'tasks': {'ar': 'المهام', 'en': 'Tasks', 'icon': 'fa-tasks'},
    'training': {'ar': 'التدريب', 'en': 'Training', 'icon': 'fa-dumbbell'},
    'veterinary': {'ar': 'الرعاية البيطرية', 'en': 'Veterinary Care', 'icon': 'fa-stethoscope'},
    'incidents': {'ar': 'الحوادث والبلاغات', 'en': 'Incidents', 'icon': 'fa-exclamation-triangle'},
    'shifts': {'ar': 'الورديات', 'en': 'Shifts', 'icon': 'fa-clock'},
    'evaluations': {'ar': 'التقييمات', 'en': 'Evaluations', 'icon': 'fa-star'},
    'locations': {'ar': 'المواقع', 'en': 'Locations', 'icon': 'fa-map-marker-alt'},
    'assignments': {'ar': 'التعيينات', 'en': 'Assignments', 'icon': 'fa-user-check'},
    'suspicions': {'ar': 'الشبهات', 'en': 'Suspicions', 'icon': 'fa-search-plus'},
    'account': {'ar': 'إدارة الحسابات', 'en': 'Account Management', 'icon': 'fa-user-circle'},
    'notifications': {'ar': 'الإشعارات', 'en': 'Notifications', 'icon': 'fa-bell'},
    'backup': {'ar': 'النسخ الاحتياطي', 'en': 'Backup', 'icon': 'fa-database'},
}

ACTION_NAMES = {
    'view': {'ar': 'عرض', 'en': 'View'},
    'create': {'ar': 'إضافة', 'en': 'Create'},
    'edit': {'ar': 'تعديل', 'en': 'Edit'},
    'delete': {'ar': 'حذف', 'en': 'Delete'},
    'export': {'ar': 'تصدير', 'en': 'Export'},
    'approve': {'ar': 'موافقة', 'en': 'Approve'},
    'reject': {'ar': 'رفض', 'en': 'Reject'},
    'manage': {'ar': 'إدارة', 'en': 'Manage'},
    'access': {'ar': 'وصول', 'en': 'Access'},
    'submit': {'ar': 'إرسال', 'en': 'Submit'},
    'assign': {'ar': 'تعيين', 'en': 'Assign'},
    'list': {'ar': 'عرض القائمة', 'en': 'List'},
    'switch': {'ar': 'تبديل', 'en': 'Switch'},
    'regenerate': {'ar': 'إعادة توليد', 'en': 'Regenerate'},
    'change': {'ar': 'تغيير', 'en': 'Change'},
    'disable': {'ar': 'تعطيل', 'en': 'Disable'},
    'complete': {'ar': 'إكمال', 'en': 'Complete'},
    'start': {'ar': 'بدء', 'en': 'Start'},
}

def get_action_type(key):
    """Extract the action type from a permission key."""
    parts = key.split('.')
    last_part = parts[-1].lower()
    for action in ACTION_NAMES.keys():
        if action in last_part:
            return action.upper()
    return 'ACCESS'

def get_category(key):
    """Extract the category from a permission key."""
    parts = key.split('.')
    return parts[0] if parts else 'general'

def generate_arabic_name(key, page_name):
    """Generate a proper Arabic name for the permission."""
    parts = key.split('.')
    category = parts[0] if parts else 'general'
    
    cat_info = CATEGORY_NAMES.get(category, {'ar': category, 'en': category})
    cat_ar = cat_info['ar']
    
    action = parts[-1].lower() if len(parts) > 1 else 'access'
    action_info = ACTION_NAMES.get(action, {'ar': action, 'en': action})
    action_ar = action_info['ar']
    
    if len(parts) > 2:
        subsection = '.'.join(parts[1:-1])
        subsection_ar = page_name if page_name else subsection
        return f"{cat_ar} - {subsection_ar} - {action_ar}"
    else:
        return f"{cat_ar} - {action_ar}"

def seed_permissions():
    """Seed all permissions from permissions_map.json."""
    print("=" * 60)
    print("SEEDING ALL PERMISSIONS")
    print("=" * 60)
    
    permissions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'permissions_map.json')
    
    if not os.path.exists(permissions_file):
        print(f"ERROR: permissions_map.json not found at {permissions_file}")
        return False
    
    with open(permissions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    permissions_list = data.get('permissions', [])
    print(f"Found {len(permissions_list)} permissions in permissions_map.json")
    
    with app.app_context():
        existing_count = Permission.query.count()
        print(f"Existing permissions in database: {existing_count}")
        
        added = 0
        updated = 0
        
        for idx, perm_data in enumerate(permissions_list):
            key = perm_data.get('permission_key')
            page_name = perm_data.get('page_name', '')
            
            if not key:
                continue
            
            category = get_category(key)
            cat_info = CATEGORY_NAMES.get(category, {'ar': category, 'en': category, 'icon': 'fa-circle'})
            
            name_ar = generate_arabic_name(key, page_name)
            name_en = key.replace('.', ' - ').replace('_', ' ').title()
            action_type = get_action_type(key)
            
            description = f"صلاحية: {page_name}\nالمسار: {perm_data.get('route_path', '')}\nالملف: {perm_data.get('source_file', '')}"
            
            existing = Permission.query.filter_by(key=key).first()
            
            if existing:
                existing.name = name_ar
                existing.name_ar = name_ar
                existing.name_en = name_en
                existing.category = category
                existing.description = description
                existing.sort_order = idx
                existing.is_active = True
                updated += 1
            else:
                perm = Permission(
                    key=key,
                    name=name_ar,
                    name_ar=name_ar,
                    name_en=name_en,
                    description=description,
                    category=category,
                    sort_order=idx,
                    is_active=True
                )
                db.session.add(perm)
                added += 1
            
            if (idx + 1) % 20 == 0:
                print(f"Processed {idx + 1}/{len(permissions_list)} permissions...")
        
        additional_permissions = [
            {'key': 'dogs.management.delete', 'name_ar': 'إدارة الكلاب - حذف', 'category': 'dogs'},
            {'key': 'dogs.management.transfer', 'name_ar': 'إدارة الكلاب - نقل', 'category': 'dogs'},
            {'key': 'dogs.management.assign_handler', 'name_ar': 'إدارة الكلاب - تعيين سائس', 'category': 'dogs'},
            {'key': 'dogs.details.view', 'name_ar': 'إدارة الكلاب - عرض التفاصيل', 'category': 'dogs'},
            
            {'key': 'employees.details.view', 'name_ar': 'إدارة الموظفين - عرض التفاصيل', 'category': 'employees'},
            {'key': 'employees.assignments.manage', 'name_ar': 'إدارة الموظفين - إدارة التعيينات', 'category': 'employees'},
            
            {'key': 'projects.management.create', 'name_ar': 'إدارة المشاريع - إضافة', 'category': 'projects'},
            {'key': 'projects.management.edit', 'name_ar': 'إدارة المشاريع - تعديل', 'category': 'projects'},
            {'key': 'projects.management.delete', 'name_ar': 'إدارة المشاريع - حذف', 'category': 'projects'},
            {'key': 'projects.management.view', 'name_ar': 'إدارة المشاريع - عرض', 'category': 'projects'},
            {'key': 'projects.details.view', 'name_ar': 'إدارة المشاريع - عرض التفاصيل', 'category': 'projects'},
            {'key': 'projects.assignments.manage', 'name_ar': 'إدارة المشاريع - إدارة التعيينات', 'category': 'projects'},
            {'key': 'projects.locations.manage', 'name_ar': 'إدارة المشاريع - إدارة المواقع', 'category': 'projects'},
            {'key': 'projects.incidents.view', 'name_ar': 'إدارة المشاريع - عرض الحوادث', 'category': 'projects'},
            {'key': 'projects.incidents.create', 'name_ar': 'إدارة المشاريع - إضافة حادث', 'category': 'projects'},
            {'key': 'projects.incidents.edit', 'name_ar': 'إدارة المشاريع - تعديل حادث', 'category': 'projects'},
            {'key': 'projects.suspicions.view', 'name_ar': 'إدارة المشاريع - عرض الشبهات', 'category': 'projects'},
            {'key': 'projects.suspicions.create', 'name_ar': 'إدارة المشاريع - إضافة شبهة', 'category': 'projects'},
            {'key': 'projects.evaluations.view', 'name_ar': 'إدارة المشاريع - عرض التقييمات', 'category': 'projects'},
            {'key': 'projects.evaluations.create', 'name_ar': 'إدارة المشاريع - إضافة تقييم', 'category': 'projects'},
            
            {'key': 'incidents.management.view', 'name_ar': 'الحوادث - عرض', 'category': 'incidents'},
            {'key': 'incidents.management.create', 'name_ar': 'الحوادث - إضافة', 'category': 'incidents'},
            {'key': 'incidents.management.edit', 'name_ar': 'الحوادث - تعديل', 'category': 'incidents'},
            {'key': 'incidents.management.delete', 'name_ar': 'الحوادث - حذف', 'category': 'incidents'},
            {'key': 'incidents.management.approve', 'name_ar': 'الحوادث - موافقة', 'category': 'incidents'},
            
            {'key': 'shifts.management.view', 'name_ar': 'الورديات - عرض', 'category': 'shifts'},
            {'key': 'shifts.management.create', 'name_ar': 'الورديات - إضافة', 'category': 'shifts'},
            {'key': 'shifts.management.edit', 'name_ar': 'الورديات - تعديل', 'category': 'shifts'},
            {'key': 'shifts.management.delete', 'name_ar': 'الورديات - حذف', 'category': 'shifts'},
            {'key': 'shifts.assignments.manage', 'name_ar': 'الورديات - إدارة التعيينات', 'category': 'shifts'},
            
            {'key': 'training.management.view', 'name_ar': 'التدريب - عرض', 'category': 'training'},
            {'key': 'training.management.create', 'name_ar': 'التدريب - إضافة جلسة', 'category': 'training'},
            {'key': 'training.management.edit', 'name_ar': 'التدريب - تعديل جلسة', 'category': 'training'},
            {'key': 'training.management.delete', 'name_ar': 'التدريب - حذف جلسة', 'category': 'training'},
            {'key': 'training.programs.manage', 'name_ar': 'التدريب - إدارة البرامج', 'category': 'training'},
            
            {'key': 'veterinary.management.view', 'name_ar': 'الرعاية البيطرية - عرض', 'category': 'veterinary'},
            {'key': 'veterinary.management.create', 'name_ar': 'الرعاية البيطرية - إضافة زيارة', 'category': 'veterinary'},
            {'key': 'veterinary.management.edit', 'name_ar': 'الرعاية البيطرية - تعديل زيارة', 'category': 'veterinary'},
            {'key': 'veterinary.management.delete', 'name_ar': 'الرعاية البيطرية - حذف زيارة', 'category': 'veterinary'},
            
            {'key': 'reports.all.view', 'name_ar': 'التقارير - عرض الكل', 'category': 'reports'},
            {'key': 'reports.all.export', 'name_ar': 'التقارير - تصدير الكل', 'category': 'reports'},
            {'key': 'reports.handler.view', 'name_ar': 'التقارير - تقارير السائس', 'category': 'reports'},
            {'key': 'reports.handler.export', 'name_ar': 'التقارير - تصدير تقارير السائس', 'category': 'reports'},
            {'key': 'reports.daily.view', 'name_ar': 'التقارير - التقارير اليومية', 'category': 'reports'},
            {'key': 'reports.daily.export', 'name_ar': 'التقارير - تصدير التقارير اليومية', 'category': 'reports'},
            {'key': 'reports.weekly.view', 'name_ar': 'التقارير - التقارير الأسبوعية', 'category': 'reports'},
            {'key': 'reports.weekly.export', 'name_ar': 'التقارير - تصدير التقارير الأسبوعية', 'category': 'reports'},
            
            {'key': 'admin.users.view', 'name_ar': 'لوحة الإدارة - عرض المستخدمين', 'category': 'admin'},
            {'key': 'admin.users.create', 'name_ar': 'لوحة الإدارة - إضافة مستخدم', 'category': 'admin'},
            {'key': 'admin.users.edit', 'name_ar': 'لوحة الإدارة - تعديل مستخدم', 'category': 'admin'},
            {'key': 'admin.users.delete', 'name_ar': 'لوحة الإدارة - حذف مستخدم', 'category': 'admin'},
            {'key': 'admin.users.reset_password', 'name_ar': 'لوحة الإدارة - إعادة تعيين كلمة المرور', 'category': 'admin'},
            {'key': 'admin.settings.view', 'name_ar': 'لوحة الإدارة - عرض الإعدادات', 'category': 'admin'},
            {'key': 'admin.settings.edit', 'name_ar': 'لوحة الإدارة - تعديل الإعدادات', 'category': 'admin'},
            {'key': 'admin.audit.view', 'name_ar': 'لوحة الإدارة - عرض سجل التدقيق', 'category': 'admin'},
            
            {'key': 'account.profile.view', 'name_ar': 'الحساب - عرض الملف الشخصي', 'category': 'account'},
            {'key': 'account.profile.edit', 'name_ar': 'الحساب - تعديل الملف الشخصي', 'category': 'account'},
            {'key': 'account.password.change', 'name_ar': 'الحساب - تغيير كلمة المرور', 'category': 'account'},
            {'key': 'account.mfa.manage', 'name_ar': 'الحساب - إدارة المصادقة الثنائية', 'category': 'account'},
            
            {'key': 'handlers.daily_reports.view', 'name_ar': 'السائسين - عرض التقارير اليومية', 'category': 'handlers'},
            {'key': 'handlers.daily_reports.create', 'name_ar': 'السائسين - إضافة تقرير يومي', 'category': 'handlers'},
            {'key': 'handlers.daily_reports.edit', 'name_ar': 'السائسين - تعديل تقرير يومي', 'category': 'handlers'},
            {'key': 'handlers.daily_reports.approve', 'name_ar': 'السائسين - الموافقة على التقارير', 'category': 'handlers'},
            {'key': 'handlers.schedule.view', 'name_ar': 'السائسين - عرض الجدول', 'category': 'handlers'},
            {'key': 'handlers.assignments.view', 'name_ar': 'السائسين - عرض التعيينات', 'category': 'handlers'},
            
            {'key': 'pm.reports.view', 'name_ar': 'مدير المشروع - عرض التقارير', 'category': 'pm'},
            {'key': 'pm.reports.create', 'name_ar': 'مدير المشروع - إضافة تقرير', 'category': 'pm'},
            {'key': 'pm.schedule.view', 'name_ar': 'مدير المشروع - عرض الجدول', 'category': 'pm'},
            {'key': 'pm.schedule.create', 'name_ar': 'مدير المشروع - إنشاء جدول', 'category': 'pm'},
            {'key': 'pm.schedule.edit', 'name_ar': 'مدير المشروع - تعديل الجدول', 'category': 'pm'},
            {'key': 'pm.assignments.view', 'name_ar': 'مدير المشروع - عرض التعيينات', 'category': 'pm'},
            {'key': 'pm.assignments.manage', 'name_ar': 'مدير المشروع - إدارة التعيينات', 'category': 'pm'},
            
            {'key': 'breeding.activities.view', 'name_ar': 'التربية - عرض الأنشطة', 'category': 'breeding'},
            {'key': 'breeding.activities.create', 'name_ar': 'التربية - إضافة نشاط', 'category': 'breeding'},
            {'key': 'breeding.activities.edit', 'name_ar': 'التربية - تعديل نشاط', 'category': 'breeding'},
            {'key': 'breeding.activities.delete', 'name_ar': 'التربية - حذف نشاط', 'category': 'breeding'},
            {'key': 'breeding.feeding.delete', 'name_ar': 'التربية - التغذية - حذف', 'category': 'breeding'},
            {'key': 'breeding.checkup.delete', 'name_ar': 'التربية - الفحص الظاهري - حذف', 'category': 'breeding'},
            {'key': 'breeding.grooming.delete', 'name_ar': 'التربية - العناية - حذف', 'category': 'breeding'},
            {'key': 'breeding.cleaning.delete', 'name_ar': 'التربية - التنظيف - حذف', 'category': 'breeding'},
            {'key': 'breeding.excretion.delete', 'name_ar': 'التربية - الإخراج - حذف', 'category': 'breeding'},
            {'key': 'breeding.deworming.delete', 'name_ar': 'التربية - مكافحة الديدان - حذف', 'category': 'breeding'},
            
            {'key': 'production.management.view', 'name_ar': 'الإنتاج - عرض', 'category': 'production'},
            {'key': 'production.management.create', 'name_ar': 'الإنتاج - إضافة', 'category': 'production'},
            {'key': 'production.management.edit', 'name_ar': 'الإنتاج - تعديل', 'category': 'production'},
            {'key': 'production.management.delete', 'name_ar': 'الإنتاج - حذف', 'category': 'production'},
            {'key': 'production.heat_cycles.view', 'name_ar': 'الإنتاج - دورات الحرارة - عرض', 'category': 'production'},
            {'key': 'production.heat_cycles.create', 'name_ar': 'الإنتاج - دورات الحرارة - إضافة', 'category': 'production'},
            {'key': 'production.heat_cycles.edit', 'name_ar': 'الإنتاج - دورات الحرارة - تعديل', 'category': 'production'},
            {'key': 'production.heat_cycles.delete', 'name_ar': 'الإنتاج - دورات الحرارة - حذف', 'category': 'production'},
            {'key': 'production.mating.view', 'name_ar': 'الإنتاج - التزاوج - عرض', 'category': 'production'},
            {'key': 'production.mating.create', 'name_ar': 'الإنتاج - التزاوج - إضافة', 'category': 'production'},
            {'key': 'production.mating.edit', 'name_ar': 'الإنتاج - التزاوج - تعديل', 'category': 'production'},
            {'key': 'production.mating.delete', 'name_ar': 'الإنتاج - التزاوج - حذف', 'category': 'production'},
            {'key': 'production.pregnancy.view', 'name_ar': 'الإنتاج - الحمل - عرض', 'category': 'production'},
            {'key': 'production.pregnancy.create', 'name_ar': 'الإنتاج - الحمل - إضافة', 'category': 'production'},
            {'key': 'production.pregnancy.edit', 'name_ar': 'الإنتاج - الحمل - تعديل', 'category': 'production'},
            {'key': 'production.pregnancy.delete', 'name_ar': 'الإنتاج - الحمل - حذف', 'category': 'production'},
            {'key': 'production.delivery.edit', 'name_ar': 'الإنتاج - الولادة - تعديل', 'category': 'production'},
            {'key': 'production.delivery.delete', 'name_ar': 'الإنتاج - الولادة - حذف', 'category': 'production'},
            {'key': 'production.puppies.view', 'name_ar': 'الإنتاج - الجراء - عرض', 'category': 'production'},
            {'key': 'production.puppies.create', 'name_ar': 'الإنتاج - الجراء - إضافة', 'category': 'production'},
            {'key': 'production.puppies.edit', 'name_ar': 'الإنتاج - الجراء - تعديل', 'category': 'production'},
            {'key': 'production.puppies.delete', 'name_ar': 'الإنتاج - الجراء - حذف', 'category': 'production'},
            {'key': 'production.puppy_training.view', 'name_ar': 'الإنتاج - تدريب الجراء - عرض', 'category': 'production'},
            {'key': 'production.puppy_training.create', 'name_ar': 'الإنتاج - تدريب الجراء - إضافة', 'category': 'production'},
            {'key': 'production.puppy_training.edit', 'name_ar': 'الإنتاج - تدريب الجراء - تعديل', 'category': 'production'},
            {'key': 'production.puppy_training.delete', 'name_ar': 'الإنتاج - تدريب الجراء - حذف', 'category': 'production'},
            {'key': 'production.maturity.edit', 'name_ar': 'الإنتاج - البلوغ - تعديل', 'category': 'production'},
            {'key': 'production.maturity.delete', 'name_ar': 'الإنتاج - البلوغ - حذف', 'category': 'production'},
            
            {'key': 'schedule.daily.approve', 'name_ar': 'الجداول - الموافقة على الجدول', 'category': 'schedule'},
            
            {'key': 'supervisor.dashboard.view', 'name_ar': 'المشرف - لوحة التحكم', 'category': 'supervisor'},
            {'key': 'supervisor.reports.create', 'name_ar': 'المشرف - إضافة تقرير', 'category': 'supervisor'},
            {'key': 'supervisor.reports.approve', 'name_ar': 'المشرف - الموافقة على التقارير', 'category': 'supervisor'},
            {'key': 'supervisor.schedules.create', 'name_ar': 'المشرف - إنشاء جدول', 'category': 'supervisor'},
            {'key': 'supervisor.schedules.edit', 'name_ar': 'المشرف - تعديل جدول', 'category': 'supervisor'},
            
            {'key': 'notifications.view', 'name_ar': 'الإشعارات - عرض', 'category': 'notifications'},
            {'key': 'notifications.mark_read', 'name_ar': 'الإشعارات - تحديد كمقروء', 'category': 'notifications'},
            {'key': 'notifications.manage', 'name_ar': 'الإشعارات - إدارة', 'category': 'notifications'},
        ]
        
        for idx, perm_data in enumerate(additional_permissions):
            key = perm_data['key']
            category = perm_data['category']
            name_ar = perm_data['name_ar']
            
            existing = Permission.query.filter_by(key=key).first()
            if existing:
                continue
            
            cat_info = CATEGORY_NAMES.get(category, {'ar': category, 'en': category, 'icon': 'fa-circle'})
            name_en = key.replace('.', ' - ').replace('_', ' ').title()
            
            perm = Permission(
                key=key,
                name=name_ar,
                name_ar=name_ar,
                name_en=name_en,
                description=f"صلاحية: {name_ar}",
                category=category,
                sort_order=len(permissions_list) + idx,
                is_active=True
            )
            db.session.add(perm)
            added += 1
        
        db.session.commit()
        
        final_count = Permission.query.count()
        print(f"\n" + "=" * 60)
        print(f"DONE! Added: {added}, Updated: {updated}")
        print(f"Total permissions in database: {final_count}")
        print("=" * 60)
        
        categories = db.session.query(Permission.category).distinct().all()
        print(f"\nCategories: {len(categories)}")
        for cat in sorted([c[0] for c in categories]):
            count = Permission.query.filter_by(category=cat).count()
            print(f"  - {cat}: {count} permissions")
        
        return True


if __name__ == '__main__':
    seed_permissions()
