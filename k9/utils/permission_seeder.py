"""
Automatic Permission Seeder
This module automatically seeds all permissions when the app starts.
Permissions are NEVER allowed to be empty - they are the foundation of the system.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

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
    'cleaning': {'ar': 'التنظيف', 'en': 'Cleaning', 'icon': 'fa-broom'},
    'settings': {'ar': 'الإعدادات', 'en': 'Settings', 'icon': 'fa-cog'},
    'dictionaries': {'ar': 'القوائم المرجعية', 'en': 'Dictionaries', 'icon': 'fa-book'},
    'audit': {'ar': 'سجل التدقيق', 'en': 'Audit Log', 'icon': 'fa-history'},
    'users': {'ar': 'إدارة المستخدمين', 'en': 'User Management', 'icon': 'fa-users-cog'},
    'grooming': {'ar': 'العناية', 'en': 'Grooming', 'icon': 'fa-cut'},
    'excretion': {'ar': 'الإخراج', 'en': 'Excretion', 'icon': 'fa-toilet'},
    'deworming': {'ar': 'مكافحة الديدان', 'en': 'Deworming', 'icon': 'fa-bug'},
    'handler_daily': {'ar': 'يومي السائس', 'en': 'Handler Daily', 'icon': 'fa-clipboard-list'},
    'profile': {'ar': 'الملف الشخصي', 'en': 'Profile', 'icon': 'fa-user'},
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
    'replace': {'ar': 'استبدال', 'en': 'Replace'},
    'lock': {'ar': 'قفل', 'en': 'Lock'},
}

SUBSECTION_NAMES = {
    'management': 'الإدارة',
    'details': 'التفاصيل',
    'assignments': 'التعيينات',
    'daily': 'اليومي',
    'weekly': 'الأسبوعي',
    'unified': 'الموحد',
    'dashboard': 'لوحة التحكم',
    'general': 'عام',
    'profile': 'الملف الشخصي',
    'schedule': 'الجدول',
    'reports': 'التقارير',
    'daily_reports': 'التقارير اليومية',
    'my_tasks': 'مهامي',
    'admin': 'إدارة',
    'users': 'المستخدمين',
    'settings': 'الإعدادات',
    'permissions': 'الصلاحيات',
    'backup': 'النسخ الاحتياطي',
    'audit': 'سجل التدقيق',
    'sessions': 'الجلسات',
    'visits': 'الزيارات',
    'programs': 'البرامج',
    'activities': 'الأنشطة',
    'feeding': 'التغذية',
    'checkup': 'الفحص الظاهري',
    'cleaning': 'التنظيف',
    'grooming': 'العناية',
    'excretion': 'الإخراج',
    'deworming': 'مكافحة الديدان',
    'feeding_log': 'سجل التغذية',
    'heat_cycles': 'دورات الحرارة',
    'mating': 'التزاوج',
    'pregnancy': 'الحمل',
    'delivery': 'الولادة',
    'puppies': 'الجراء',
    'puppy_training': 'تدريب الجراء',
    'maturity': 'البلوغ',
    'notifications': 'الإشعارات',
    'approvals': 'الموافقات',
    'team': 'الفريق',
    'dogs': 'الكلاب',
    'project': 'المشروع',
    'schedules': 'الجداول',
    'incidents': 'الحوادث',
    'suspicions': 'الشبهات',
    'evaluations': 'التقييمات',
    'locations': 'المواقع',
    'main': 'الرئيسية',
    'index': 'الرئيسية',
    'login': 'تسجيل الدخول',
    'logout': 'تسجيل الخروج',
    'mode': 'الوضع',
    'setup': 'الإعداد',
    'create_manager': 'إنشاء مدير',
    'status': 'الحالة',
    'backup_codes': 'رموز النسخ الاحتياطي',
    'password': 'كلمة المرور',
    'request': 'طلب',
    'reset': 'إعادة تعيين',
    'mfa': 'المصادقة الثنائية',
    'global': 'البحث العام',
    'google_drive': 'جوجل درايف',
    'handler': 'السائس',
    'all': 'الكل',
    'attendance': 'الحضور',
    'training': 'التدريب',
    'breeding': 'التربية',
    'veterinary': 'البيطرية',
    'caretaker': 'مقدم الرعاية',
    'trainer_daily': 'يومي المدرب',
    'pm_daily': 'يومي مدير المشروع',
    'pm_weekly': 'أسبوعي مدير المشروع',
    'handler_daily': 'يومي السائس',
    'monthly': 'الشهري',
    'veterinary_daily': 'يومي البيطرية',
    'items': 'البنود',
    'lock': 'القفل',
    'accounts': 'الحسابات',
    'cloud': 'السحابة',
    'system': 'النظام',
    'select_project': 'اختيار المشروع',
    'api': 'واجهة البرمجة',
    'mark_read': 'وضع علامة مقروء',
    'handlers': 'السائسين',
}

ADDITIONAL_PERMISSIONS = [
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
    {'key': 'production.delivery.view', 'name_ar': 'الإنتاج - الولادة - عرض', 'category': 'production'},
    {'key': 'production.delivery.edit', 'name_ar': 'الإنتاج - الولادة - تعديل', 'category': 'production'},
    {'key': 'production.delivery.delete', 'name_ar': 'الإنتاج - الولادة - حذف', 'category': 'production'},
    {'key': 'production.puppies.edit', 'name_ar': 'الإنتاج - الجراء - تعديل', 'category': 'production'},
    {'key': 'production.puppies.delete', 'name_ar': 'الإنتاج - الجراء - حذف', 'category': 'production'},
    {'key': 'production.puppy_training.edit', 'name_ar': 'الإنتاج - تدريب الجراء - تعديل', 'category': 'production'},
    {'key': 'production.puppy_training.delete', 'name_ar': 'الإنتاج - تدريب الجراء - حذف', 'category': 'production'},
    {'key': 'production.maturity.edit', 'name_ar': 'الإنتاج - البلوغ - تعديل', 'category': 'production'},
    {'key': 'production.maturity.delete', 'name_ar': 'الإنتاج - البلوغ - حذف', 'category': 'production'},
    {'key': 'schedule.management.delete', 'name_ar': 'الجداول - حذف', 'category': 'schedule'},
    {'key': 'tasks.management.view', 'name_ar': 'المهام - عرض', 'category': 'tasks'},
    {'key': 'tasks.management.create', 'name_ar': 'المهام - إضافة', 'category': 'tasks'},
    {'key': 'tasks.management.edit', 'name_ar': 'المهام - تعديل', 'category': 'tasks'},
    {'key': 'tasks.management.delete', 'name_ar': 'المهام - حذف', 'category': 'tasks'},
    {'key': 'tasks.management.assign', 'name_ar': 'المهام - تعيين', 'category': 'tasks'},
    {'key': 'supervisor.general.access', 'name_ar': 'المشرف - وصول عام', 'category': 'supervisor'},
    {'key': 'supervisor.reports.view', 'name_ar': 'المشرف - عرض التقارير', 'category': 'supervisor'},
    {'key': 'supervisor.schedules.view', 'name_ar': 'المشرف - عرض الجداول', 'category': 'supervisor'},
    {'key': 'search.global.access', 'name_ar': 'البحث العام - وصول', 'category': 'search'},
    
    # Tasks - My Tasks permissions
    {'key': 'tasks.my_tasks.view', 'name_ar': 'المهام - مهامي - عرض', 'category': 'tasks'},
    {'key': 'tasks.my_tasks.complete', 'name_ar': 'المهام - مهامي - إكمال', 'category': 'tasks'},
    {'key': 'tasks.my_tasks.start', 'name_ar': 'المهام - مهامي - بدء', 'category': 'tasks'},
    
    # Schedule permissions
    {'key': 'schedule.management.view', 'name_ar': 'الجداول - عرض', 'category': 'schedule'},
    {'key': 'schedule.management.create', 'name_ar': 'الجداول - إضافة', 'category': 'schedule'},
    {'key': 'schedule.management.edit', 'name_ar': 'الجداول - تعديل', 'category': 'schedule'},
    {'key': 'schedule.items.view', 'name_ar': 'الجداول - البنود - عرض', 'category': 'schedule'},
    {'key': 'schedule.items.create', 'name_ar': 'الجداول - البنود - إضافة', 'category': 'schedule'},
    {'key': 'schedule.items.delete', 'name_ar': 'الجداول - البنود - حذف', 'category': 'schedule'},
    {'key': 'schedule.lock.manage', 'name_ar': 'الجداول - القفل - إدارة', 'category': 'schedule'},
    
    # Shifts - API permissions
    {'key': 'shifts.api.view', 'name_ar': 'الورديات - واجهة البرمجة - عرض', 'category': 'shifts'},
    
    # Supervisor additional permissions
    {'key': 'supervisor.schedules.create', 'name_ar': 'المشرف - الجداول - إضافة', 'category': 'supervisor'},
    {'key': 'supervisor.schedules.edit', 'name_ar': 'المشرف - الجداول - تعديل', 'category': 'supervisor'},
    {'key': 'supervisor.schedules.delete', 'name_ar': 'المشرف - الجداول - حذف', 'category': 'supervisor'},
    {'key': 'supervisor.schedules.lock', 'name_ar': 'المشرف - الجداول - قفل', 'category': 'supervisor'},
    {'key': 'supervisor.reports.approve', 'name_ar': 'المشرف - التقارير - موافقة', 'category': 'supervisor'},
    {'key': 'supervisor.reports.reject', 'name_ar': 'المشرف - التقارير - رفض', 'category': 'supervisor'},
    {'key': 'supervisor.handlers.replace', 'name_ar': 'المشرف - السائسين - استبدال', 'category': 'supervisor'},
    {'key': 'supervisor.api.access', 'name_ar': 'المشرف - واجهة البرمجة - وصول', 'category': 'supervisor'},
    
    # Reports - Attendance permissions
    {'key': 'reports.attendance.view', 'name_ar': 'التقارير - الحضور - عرض', 'category': 'reports'},
    {'key': 'reports.attendance.create', 'name_ar': 'التقارير - الحضور - إضافة', 'category': 'reports'},
    {'key': 'reports.attendance.export', 'name_ar': 'التقارير - الحضور - تصدير', 'category': 'reports'},
    
    # Reports - Training permissions
    {'key': 'reports.training.view', 'name_ar': 'التقارير - التدريب - عرض', 'category': 'reports'},
    {'key': 'reports.training.create', 'name_ar': 'التقارير - التدريب - إضافة', 'category': 'reports'},
    {'key': 'reports.training.edit', 'name_ar': 'التقارير - التدريب - تعديل', 'category': 'reports'},
    {'key': 'reports.training.approve', 'name_ar': 'التقارير - التدريب - موافقة', 'category': 'reports'},
    
    # Reports - Breeding Feeding permissions
    {'key': 'reports.breeding.feeding.view', 'name_ar': 'التقارير - التغذية - عرض', 'category': 'reports'},
    {'key': 'reports.breeding.feeding.create', 'name_ar': 'التقارير - التغذية - إضافة', 'category': 'reports'},
    {'key': 'reports.breeding.feeding.export', 'name_ar': 'التقارير - التغذية - تصدير', 'category': 'reports'},
    
    # Reports - Breeding Checkup permissions
    {'key': 'reports.breeding.checkup.view', 'name_ar': 'التقارير - الفحص الظاهري - عرض', 'category': 'reports'},
    {'key': 'reports.breeding.checkup.create', 'name_ar': 'التقارير - الفحص الظاهري - إضافة', 'category': 'reports'},
    {'key': 'reports.breeding.checkup.export', 'name_ar': 'التقارير - الفحص الظاهري - تصدير', 'category': 'reports'},
    
    # Reports - Veterinary permissions
    {'key': 'reports.veterinary.view', 'name_ar': 'التقارير - البيطرية - عرض', 'category': 'reports'},
    {'key': 'reports.veterinary.create', 'name_ar': 'التقارير - البيطرية - إضافة', 'category': 'reports'},
    {'key': 'reports.veterinary.export', 'name_ar': 'التقارير - البيطرية - تصدير', 'category': 'reports'},
    
    # Reports - Caretaker permissions
    {'key': 'reports.caretaker.view', 'name_ar': 'التقارير - مقدم الرعاية - عرض', 'category': 'reports'},
    {'key': 'reports.caretaker.create', 'name_ar': 'التقارير - مقدم الرعاية - إضافة', 'category': 'reports'},
    {'key': 'reports.caretaker.export', 'name_ar': 'التقارير - مقدم الرعاية - تصدير', 'category': 'reports'},
    
    # Handler Daily permissions
    {'key': 'handler_daily.schedules.view', 'name_ar': 'يومي السائس - الجداول - عرض', 'category': 'handler_daily'},
    {'key': 'handler_daily.reports.view', 'name_ar': 'يومي السائس - التقارير - عرض', 'category': 'handler_daily'},
    {'key': 'handler_daily.reports.create', 'name_ar': 'يومي السائس - التقارير - إضافة', 'category': 'handler_daily'},
    {'key': 'handler_daily.reports.edit', 'name_ar': 'يومي السائس - التقارير - تعديل', 'category': 'handler_daily'},
    
    # PM additional permissions
    {'key': 'pm.general.access', 'name_ar': 'مدير المشروع - وصول عام', 'category': 'pm'},
    {'key': 'pm.notifications.view', 'name_ar': 'مدير المشروع - الإشعارات - عرض', 'category': 'pm'},
    {'key': 'pm.profile.view', 'name_ar': 'مدير المشروع - الملف الشخصي - عرض', 'category': 'pm'},
    {'key': 'pm.approvals.manage', 'name_ar': 'مدير المشروع - الموافقات - إدارة', 'category': 'pm'},
    {'key': 'pm.breeding.approve', 'name_ar': 'مدير المشروع - التربية - موافقة', 'category': 'pm'},
    {'key': 'pm.breeding.reject', 'name_ar': 'مدير المشروع - التربية - رفض', 'category': 'pm'},
    {'key': 'pm.select_project.access', 'name_ar': 'مدير المشروع - اختيار المشروع - وصول', 'category': 'pm'},
    
    # Admin additional permissions
    {'key': 'admin.accounts.view', 'name_ar': 'لوحة الإدارة - الحسابات - عرض', 'category': 'admin'},
    {'key': 'admin.accounts.create', 'name_ar': 'لوحة الإدارة - الحسابات - إضافة', 'category': 'admin'},
    {'key': 'admin.accounts.edit', 'name_ar': 'لوحة الإدارة - الحسابات - تعديل', 'category': 'admin'},
    {'key': 'admin.accounts.delete', 'name_ar': 'لوحة الإدارة - الحسابات - حذف', 'category': 'admin'},
    {'key': 'admin.reports.approve', 'name_ar': 'لوحة الإدارة - التقارير - موافقة', 'category': 'admin'},
    {'key': 'admin.reports.reject', 'name_ar': 'لوحة الإدارة - التقارير - رفض', 'category': 'admin'},
    {'key': 'admin.cloud.manage', 'name_ar': 'لوحة الإدارة - السحابة - إدارة', 'category': 'admin'},
    {'key': 'admin.system.manage', 'name_ar': 'لوحة الإدارة - النظام - إدارة', 'category': 'admin'},
    {'key': 'admin.api.access', 'name_ar': 'لوحة الإدارة - واجهة البرمجة - وصول', 'category': 'admin'},
    
    # Notifications permissions
    {'key': 'notifications.view', 'name_ar': 'الإشعارات - عرض', 'category': 'notifications'},
    {'key': 'notifications.mark_read', 'name_ar': 'الإشعارات - وضع علامة مقروء', 'category': 'notifications'},
    {'key': 'notifications.settings.manage', 'name_ar': 'الإشعارات - الإعدادات - إدارة', 'category': 'notifications'},
    
    # Profile permissions
    {'key': 'profile.view', 'name_ar': 'الملف الشخصي - عرض', 'category': 'profile'},
    {'key': 'profile.edit', 'name_ar': 'الملف الشخصي - تعديل', 'category': 'profile'},
]


def _translate_subsection(subsection):
    """Translate a subsection name to Arabic."""
    parts = subsection.split('.')
    translated_parts = []
    for part in parts:
        ar_name = SUBSECTION_NAMES.get(part.lower())
        if ar_name:
            translated_parts.append(ar_name)
        else:
            translated_parts.append(SUBSECTION_NAMES.get(part.lower().replace('_', ' '), part))
    return ' - '.join(translated_parts) if translated_parts else subsection


def _generate_arabic_name(key, page_name=''):
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
        subsection_ar = _translate_subsection(subsection)
        return f"{cat_ar} - {subsection_ar} - {action_ar}"
    elif len(parts) == 2:
        return f"{cat_ar} - {action_ar}"
    else:
        return f"{cat_ar} - {action_ar}"


def _get_category(key):
    """Extract the category from a permission key."""
    parts = key.split('.')
    return parts[0] if parts else 'general'


def seed_permissions_from_map(db, Permission):
    """
    Automatically seed ONLY MISSING permissions from permissions_map.json.
    This function is idempotent and conservative - it only adds new permissions,
    never overwrites existing curated metadata.
    
    Args:
        db: SQLAlchemy database instance
        Permission: Permission model class
    
    Returns:
        tuple: (added_count, skipped_count, total_count)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    permissions_file = os.path.join(base_dir, 'permissions_map.json')
    
    if not os.path.exists(permissions_file):
        logger.warning(f"permissions_map.json not found at {permissions_file}")
        return (0, 0, 0)
    
    try:
        with open(permissions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load permissions_map.json: {e}")
        return (0, 0, 0)
    
    permissions_list = data.get('permissions', [])
    
    existing_keys = {p.key for p in Permission.query.all()}
    
    added = 0
    skipped = 0
    sort_order = len(existing_keys)
    
    for perm_data in permissions_list:
        key = perm_data.get('permission_key')
        page_name = perm_data.get('page_name', '')
        
        if not key:
            continue
        
        if key in existing_keys:
            skipped += 1
            continue
        
        category = _get_category(key)
        name_ar = _generate_arabic_name(key, page_name)
        description = f"صلاحية: {page_name}\nالمسار: {perm_data.get('route_path', '')}"
        
        perm = Permission(
            key=key,
            name=name_ar,
            name_ar=name_ar,
            description=description,
            category=category,
            sort_order=sort_order,
            is_active=True
        )
        db.session.add(perm)
        existing_keys.add(key)
        added += 1
        sort_order += 1
    
    for extra_perm in ADDITIONAL_PERMISSIONS:
        key = extra_perm['key']
        if key in existing_keys:
            skipped += 1
            continue
            
        perm = Permission(
            key=key,
            name=extra_perm['name_ar'],
            name_ar=extra_perm['name_ar'],
            category=extra_perm['category'],
            sort_order=sort_order,
            is_active=True
        )
        db.session.add(perm)
        existing_keys.add(key)
        added += 1
        sort_order += 1
    
    try:
        db.session.commit()
        total = Permission.query.count()
        if added > 0:
            print(f"✓ Permissions auto-seeded: {added} new permissions added (total: {total})")
        return (added, skipped, total)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to commit permissions: {e}")
        return (0, 0, 0)


def ensure_permissions_exist(db, Permission):
    """
    Ensure permissions table is never empty.
    Called during app initialization - this is CRITICAL for the system to function.
    
    Args:
        db: SQLAlchemy database instance
        Permission: Permission model class
    """
    try:
        count = Permission.query.count()
        if count == 0:
            print("⚠ Permissions table is empty! Auto-seeding permissions...")
            added, updated, total = seed_permissions_from_map(db, Permission)
            if total == 0:
                print("✗ CRITICAL: Failed to seed permissions!")
            else:
                print(f"✓ Permissions seeded successfully: {total} permissions available")
        else:
            added, updated, total = seed_permissions_from_map(db, Permission)
            if added > 0:
                print(f"✓ Added {added} new permissions (total: {total})")
    except Exception as e:
        logger.error(f"Error ensuring permissions exist: {e}")
        print(f"⚠ Warning: Could not verify permissions: {e}")
