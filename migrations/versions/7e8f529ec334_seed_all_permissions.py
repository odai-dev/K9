"""Seed all permissions - single source of truth for permission definitions.

This replaces the startup seeder (ensure_permissions_exist).
All future permissions should be added here as new data migrations.

Revision ID: 7e8f529ec334
Revises: f49070afbb99
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '7e8f529ec334'
down_revision = '88452249e856'
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Complete list of all permissions in the system.
# Add new permissions at the bottom of this list or in a new migration.
# Format: ('permission.key', 'Arabic Name', 'category')
# ---------------------------------------------------------------------------
PERMISSIONS = [
    # ── Admin ──────────────────────────────────────────────────────────────
    ('admin.users.view',               'لوحة الإدارة - عرض المستخدمين',           'admin'),
    ('admin.users.create',             'لوحة الإدارة - إضافة مستخدم',             'admin'),
    ('admin.users.edit',               'لوحة الإدارة - تعديل مستخدم',             'admin'),
    ('admin.users.delete',             'لوحة الإدارة - حذف مستخدم',               'admin'),
    ('admin.users.reset_password',     'لوحة الإدارة - إعادة تعيين كلمة المرور', 'admin'),
    ('admin.settings.view',            'لوحة الإدارة - عرض الإعدادات',            'admin'),
    ('admin.settings.edit',            'لوحة الإدارة - تعديل الإعدادات',          'admin'),
    ('admin.audit.view',               'لوحة الإدارة - عرض سجل التدقيق',         'admin'),
    ('admin.accounts.view',            'لوحة الإدارة - الحسابات - عرض',          'admin'),
    ('admin.accounts.create',          'لوحة الإدارة - الحسابات - إضافة',         'admin'),
    ('admin.accounts.edit',            'لوحة الإدارة - الحسابات - تعديل',         'admin'),
    ('admin.accounts.delete',          'لوحة الإدارة - الحسابات - حذف',           'admin'),
    ('admin.reports.approve',          'لوحة الإدارة - التقارير - موافقة',         'admin'),
    ('admin.reports.reject',           'لوحة الإدارة - التقارير - رفض',            'admin'),
    ('admin.cloud.manage',             'لوحة الإدارة - السحابة - إدارة',           'admin'),
    ('admin.system.manage',            'لوحة الإدارة - النظام - إدارة',            'admin'),
    ('admin.api.access',               'لوحة الإدارة - واجهة البرمجة - وصول',     'admin'),
    ('admin.backup.manage',            'لوحة الإدارة - النسخ الاحتياطي - إدارة',  'admin'),
    ('admin.permissions.view',         'لوحة الإدارة - الصلاحيات - عرض',          'admin'),
    ('admin.permissions.manage',       'لوحة الإدارة - الصلاحيات - إدارة',         'admin'),

    # ── Authentication ─────────────────────────────────────────────────────
    ('auth.login.access',              'المصادقة - تسجيل الدخول',                  'auth'),
    ('auth.logout.access',             'المصادقة - تسجيل الخروج',                  'auth'),
    ('auth.setup.access',              'المصادقة - الإعداد الأولي',                'auth'),
    ('auth.create_manager.access',     'المصادقة - إنشاء مدير',                    'auth'),

    # ── MFA ────────────────────────────────────────────────────────────────
    ('mfa.setup.access',               'المصادقة الثنائية - إعداد',                'mfa'),
    ('mfa.backup_codes.view',          'المصادقة الثنائية - رموز النسخ الاحتياطي - عرض', 'mfa'),
    ('mfa.backup_codes.regenerate',    'المصادقة الثنائية - رموز النسخ الاحتياطي - إعادة توليد', 'mfa'),
    ('mfa.disable.access',             'المصادقة الثنائية - تعطيل',                'mfa'),
    ('mfa.status.view',                'المصادقة الثنائية - حالة',                  'mfa'),

    # ── Password Reset ─────────────────────────────────────────────────────
    ('password_reset.request.access',  'إعادة تعيين كلمة المرور - طلب',            'password_reset'),
    ('password_reset.reset.access',    'إعادة تعيين كلمة المرور - إعادة تعيين',    'password_reset'),

    # ── Account / Profile ──────────────────────────────────────────────────
    ('account.profile.view',           'الحساب - عرض الملف الشخصي',               'account'),
    ('account.profile.edit',           'الحساب - تعديل الملف الشخصي',              'account'),
    ('account.password.change',        'الحساب - تغيير كلمة المرور',               'account'),
    ('account.mfa.manage',             'الحساب - إدارة المصادقة الثنائية',         'account'),
    ('profile.view',                   'الملف الشخصي - عرض',                        'profile'),
    ('profile.edit',                   'الملف الشخصي - تعديل',                      'profile'),

    # ── Dashboard ──────────────────────────────────────────────────────────
    ('dashboard.general.access',       'لوحة التحكم - وصول عام',                   'dashboard'),
    ('dashboard.admin.access',         'لوحة التحكم - مشرف عام',                   'dashboard'),
    ('dashboard.api.access',           'لوحة التحكم - واجهة البرمجة',              'dashboard'),
    ('home.main.access',               'الصفحة الرئيسية - وصول',                   'home'),

    # ── Dogs ───────────────────────────────────────────────────────────────
    ('dogs.management.view',           'إدارة الكلاب - عرض',                        'dogs'),
    ('dogs.management.create',         'إدارة الكلاب - إضافة',                      'dogs'),
    ('dogs.management.edit',           'إدارة الكلاب - تعديل',                      'dogs'),
    ('dogs.management.delete',         'إدارة الكلاب - حذف',                        'dogs'),
    ('dogs.management.transfer',       'إدارة الكلاب - نقل',                        'dogs'),
    ('dogs.management.assign_handler', 'إدارة الكلاب - تعيين سائس',                 'dogs'),
    ('dogs.details.view',              'إدارة الكلاب - عرض التفاصيل',               'dogs'),

    # ── Employees ──────────────────────────────────────────────────────────
    ('employees.management.view',      'إدارة الموظفين - عرض',                      'employees'),
    ('employees.management.create',    'إدارة الموظفين - إضافة',                    'employees'),
    ('employees.management.edit',      'إدارة الموظفين - تعديل',                    'employees'),
    ('employees.management.delete',    'إدارة الموظفين - حذف',                      'employees'),
    ('employees.details.view',         'إدارة الموظفين - عرض التفاصيل',             'employees'),
    ('employees.assignments.manage',   'إدارة الموظفين - إدارة التعيينات',           'employees'),

    # ── Projects ───────────────────────────────────────────────────────────
    ('projects.management.view',       'إدارة المشاريع - عرض',                      'projects'),
    ('projects.management.create',     'إدارة المشاريع - إضافة',                    'projects'),
    ('projects.management.edit',       'إدارة المشاريع - تعديل',                    'projects'),
    ('projects.management.delete',     'إدارة المشاريع - حذف',                      'projects'),
    ('projects.details.view',          'إدارة المشاريع - عرض التفاصيل',             'projects'),
    ('projects.assignments.manage',    'إدارة المشاريع - إدارة التعيينات',           'projects'),
    ('projects.locations.manage',      'إدارة المشاريع - إدارة المواقع',             'projects'),
    ('projects.incidents.view',        'إدارة المشاريع - عرض الحوادث',              'projects'),
    ('projects.incidents.create',      'إدارة المشاريع - إضافة حادث',               'projects'),
    ('projects.incidents.edit',        'إدارة المشاريع - تعديل حادث',               'projects'),
    ('projects.suspicions.view',       'إدارة المشاريع - عرض الشبهات',              'projects'),
    ('projects.suspicions.create',     'إدارة المشاريع - إضافة شبهة',               'projects'),
    ('projects.evaluations.view',      'إدارة المشاريع - عرض التقييمات',            'projects'),
    ('projects.evaluations.create',    'إدارة المشاريع - إضافة تقييم',              'projects'),

    # ── Incidents ──────────────────────────────────────────────────────────
    ('incidents.management.view',      'الحوادث - عرض',                             'incidents'),
    ('incidents.management.create',    'الحوادث - إضافة',                           'incidents'),
    ('incidents.management.edit',      'الحوادث - تعديل',                           'incidents'),
    ('incidents.management.delete',    'الحوادث - حذف',                             'incidents'),
    ('incidents.management.approve',   'الحوادث - موافقة',                          'incidents'),

    # ── Shifts ─────────────────────────────────────────────────────────────
    ('shifts.management.view',         'الورديات - عرض',                            'shifts'),
    ('shifts.management.create',       'الورديات - إضافة',                          'shifts'),
    ('shifts.management.edit',         'الورديات - تعديل',                          'shifts'),
    ('shifts.management.delete',       'الورديات - حذف',                            'shifts'),
    ('shifts.assignments.manage',      'الورديات - إدارة التعيينات',                 'shifts'),
    ('shifts.api.view',                'الورديات - واجهة البرمجة - عرض',            'shifts'),

    # ── Schedule ───────────────────────────────────────────────────────────
    ('schedule.management.view',       'الجداول - عرض',                             'schedule'),
    ('schedule.management.create',     'الجداول - إضافة',                           'schedule'),
    ('schedule.management.edit',       'الجداول - تعديل',                           'schedule'),
    ('schedule.management.delete',     'الجداول - حذف',                             'schedule'),
    ('schedule.items.view',            'الجداول - البنود - عرض',                    'schedule'),
    ('schedule.items.create',          'الجداول - البنود - إضافة',                  'schedule'),
    ('schedule.items.delete',          'الجداول - البنود - حذف',                    'schedule'),
    ('schedule.lock.manage',           'الجداول - القفل - إدارة',                   'schedule'),

    # ── Training ───────────────────────────────────────────────────────────
    ('training.management.view',       'التدريب - عرض',                             'training'),
    ('training.management.create',     'التدريب - إضافة جلسة',                      'training'),
    ('training.management.edit',       'التدريب - تعديل جلسة',                      'training'),
    ('training.management.delete',     'التدريب - حذف جلسة',                        'training'),
    ('training.programs.manage',       'التدريب - إدارة البرامج',                   'training'),

    # ── Veterinary ─────────────────────────────────────────────────────────
    ('veterinary.management.view',     'الرعاية البيطرية - عرض',                    'veterinary'),
    ('veterinary.management.create',   'الرعاية البيطرية - إضافة زيارة',            'veterinary'),
    ('veterinary.management.edit',     'الرعاية البيطرية - تعديل زيارة',            'veterinary'),
    ('veterinary.management.delete',   'الرعاية البيطرية - حذف زيارة',              'veterinary'),

    # ── Breeding & Care ────────────────────────────────────────────────────
    ('breeding.activities.view',       'التربية - عرض الأنشطة',                     'breeding'),
    ('breeding.activities.create',     'التربية - إضافة نشاط',                      'breeding'),
    ('breeding.activities.edit',       'التربية - تعديل نشاط',                      'breeding'),
    ('breeding.activities.delete',     'التربية - حذف نشاط',                        'breeding'),
    ('breeding.feeding.view',          'التربية - التغذية - عرض',                   'breeding'),
    ('breeding.feeding.create',        'التربية - التغذية - إضافة',                 'breeding'),
    ('breeding.feeding.edit',          'التربية - التغذية - تعديل',                 'breeding'),
    ('breeding.feeding.delete',        'التربية - التغذية - حذف',                   'breeding'),
    ('breeding.checkup.view',          'التربية - الفحص الظاهري - عرض',             'breeding'),
    ('breeding.checkup.create',        'التربية - الفحص الظاهري - إضافة',           'breeding'),
    ('breeding.checkup.edit',          'التربية - الفحص الظاهري - تعديل',           'breeding'),
    ('breeding.checkup.delete',        'التربية - الفحص الظاهري - حذف',             'breeding'),
    ('breeding.grooming.view',         'التربية - العناية - عرض',                   'breeding'),
    ('breeding.grooming.create',       'التربية - العناية - إضافة',                 'breeding'),
    ('breeding.grooming.edit',         'التربية - العناية - تعديل',                 'breeding'),
    ('breeding.grooming.delete',       'التربية - العناية - حذف',                   'breeding'),
    ('breeding.cleaning.view',         'التربية - التنظيف - عرض',                   'breeding'),
    ('breeding.cleaning.create',       'التربية - التنظيف - إضافة',                 'breeding'),
    ('breeding.cleaning.edit',         'التربية - التنظيف - تعديل',                 'breeding'),
    ('breeding.cleaning.delete',       'التربية - التنظيف - حذف',                   'breeding'),
    ('breeding.excretion.view',        'التربية - الإخراج - عرض',                   'breeding'),
    ('breeding.excretion.create',      'التربية - الإخراج - إضافة',                 'breeding'),
    ('breeding.excretion.edit',        'التربية - الإخراج - تعديل',                 'breeding'),
    ('breeding.excretion.delete',      'التربية - الإخراج - حذف',                   'breeding'),
    ('breeding.deworming.view',        'التربية - مكافحة الديدان - عرض',            'breeding'),
    ('breeding.deworming.create',      'التربية - مكافحة الديدان - إضافة',          'breeding'),
    ('breeding.deworming.edit',        'التربية - مكافحة الديدان - تعديل',          'breeding'),
    ('breeding.deworming.delete',      'التربية - مكافحة الديدان - حذف',            'breeding'),

    # ── Production & Breeding ──────────────────────────────────────────────
    ('production.management.view',     'الإنتاج - عرض',                             'production'),
    ('production.management.create',   'الإنتاج - إضافة',                           'production'),
    ('production.management.edit',     'الإنتاج - تعديل',                           'production'),
    ('production.management.delete',   'الإنتاج - حذف',                             'production'),
    ('production.heat_cycles.view',    'الإنتاج - دورات الحرارة - عرض',             'production'),
    ('production.heat_cycles.create',  'الإنتاج - دورات الحرارة - إضافة',           'production'),
    ('production.heat_cycles.edit',    'الإنتاج - دورات الحرارة - تعديل',           'production'),
    ('production.heat_cycles.delete',  'الإنتاج - دورات الحرارة - حذف',             'production'),
    ('production.mating.view',         'الإنتاج - التزاوج - عرض',                   'production'),
    ('production.mating.create',       'الإنتاج - التزاوج - إضافة',                 'production'),
    ('production.mating.edit',         'الإنتاج - التزاوج - تعديل',                 'production'),
    ('production.mating.delete',       'الإنتاج - التزاوج - حذف',                   'production'),
    ('production.pregnancy.view',      'الإنتاج - الحمل - عرض',                     'production'),
    ('production.pregnancy.create',    'الإنتاج - الحمل - إضافة',                   'production'),
    ('production.pregnancy.edit',      'الإنتاج - الحمل - تعديل',                   'production'),
    ('production.pregnancy.delete',    'الإنتاج - الحمل - حذف',                     'production'),
    ('production.delivery.view',       'الإنتاج - الولادة - عرض',                   'production'),
    ('production.delivery.edit',       'الإنتاج - الولادة - تعديل',                 'production'),
    ('production.delivery.delete',     'الإنتاج - الولادة - حذف',                   'production'),
    ('production.puppies.view',        'الإنتاج - الجراء - عرض',                    'production'),
    ('production.puppies.edit',        'الإنتاج - الجراء - تعديل',                  'production'),
    ('production.puppies.delete',      'الإنتاج - الجراء - حذف',                    'production'),
    ('production.puppy_training.view', 'الإنتاج - تدريب الجراء - عرض',              'production'),
    ('production.puppy_training.edit', 'الإنتاج - تدريب الجراء - تعديل',            'production'),
    ('production.puppy_training.delete','الإنتاج - تدريب الجراء - حذف',             'production'),
    ('production.maturity.view',       'الإنتاج - البلوغ - عرض',                    'production'),
    ('production.maturity.edit',       'الإنتاج - البلوغ - تعديل',                  'production'),
    ('production.maturity.delete',     'الإنتاج - البلوغ - حذف',                    'production'),

    # ── Reports ────────────────────────────────────────────────────────────
    ('reports.all.view',               'التقارير - عرض الكل',                        'reports'),
    ('reports.all.export',             'التقارير - تصدير الكل',                      'reports'),
    ('reports.handler.view',           'التقارير - تقارير السائس',                   'reports'),
    ('reports.handler.export',         'التقارير - تصدير تقارير السائس',             'reports'),
    ('reports.daily.view',             'التقارير - التقارير اليومية',                'reports'),
    ('reports.daily.export',           'التقارير - تصدير التقارير اليومية',          'reports'),
    ('reports.weekly.view',            'التقارير - التقارير الأسبوعية',              'reports'),
    ('reports.weekly.export',          'التقارير - تصدير التقارير الأسبوعية',        'reports'),
    ('reports.attendance.view',        'التقارير - الحضور - عرض',                   'reports'),
    ('reports.attendance.create',      'التقارير - الحضور - إضافة',                 'reports'),
    ('reports.attendance.export',      'التقارير - الحضور - تصدير',                 'reports'),
    ('reports.training.view',          'التقارير - التدريب - عرض',                  'reports'),
    ('reports.training.create',        'التقارير - التدريب - إضافة',                'reports'),
    ('reports.training.edit',          'التقارير - التدريب - تعديل',                'reports'),
    ('reports.training.approve',       'التقارير - التدريب - موافقة',               'reports'),
    ('reports.breeding.feeding.view',  'التقارير - التغذية - عرض',                  'reports'),
    ('reports.breeding.feeding.create','التقارير - التغذية - إضافة',                'reports'),
    ('reports.breeding.feeding.export','التقارير - التغذية - تصدير',                'reports'),
    ('reports.breeding.checkup.view',  'التقارير - الفحص الظاهري - عرض',            'reports'),
    ('reports.breeding.checkup.create','التقارير - الفحص الظاهري - إضافة',          'reports'),
    ('reports.breeding.checkup.export','التقارير - الفحص الظاهري - تصدير',          'reports'),
    ('reports.veterinary.view',        'التقارير - البيطرية - عرض',                  'reports'),
    ('reports.veterinary.create',      'التقارير - البيطرية - إضافة',                'reports'),
    ('reports.veterinary.export',      'التقارير - البيطرية - تصدير',                'reports'),
    ('reports.caretaker.view',         'التقارير - مقدم الرعاية - عرض',              'reports'),
    ('reports.caretaker.create',       'التقارير - مقدم الرعاية - إضافة',            'reports'),
    ('reports.caretaker.export',       'التقارير - مقدم الرعاية - تصدير',            'reports'),

    # ── Handler Daily ──────────────────────────────────────────────────────
    ('handler_daily.schedules.view',   'يومي السائس - الجداول - عرض',               'handler_daily'),
    ('handler_daily.reports.view',     'يومي السائس - التقارير - عرض',               'handler_daily'),
    ('handler_daily.reports.create',   'يومي السائس - التقارير - إضافة',             'handler_daily'),
    ('handler_daily.reports.edit',     'يومي السائس - التقارير - تعديل',             'handler_daily'),
    ('handler_daily.reports.delete',   'يومي السائس - التقارير - حذف',               'handler_daily'),
    ('handler_daily.reports.submit',   'يومي السائس - التقارير - إرسال',             'handler_daily'),

    # ── Handlers ───────────────────────────────────────────────────────────
    ('handlers.daily_reports.view',    'السائسين - عرض التقارير اليومية',            'handlers'),
    ('handlers.daily_reports.create',  'السائسين - إضافة تقرير يومي',               'handlers'),
    ('handlers.daily_reports.edit',    'السائسين - تعديل تقرير يومي',               'handlers'),
    ('handlers.daily_reports.approve', 'السائسين - الموافقة على التقارير',           'handlers'),
    ('handlers.schedule.view',         'السائسين - عرض الجدول',                      'handlers'),
    ('handlers.assignments.view',      'السائسين - عرض التعيينات',                   'handlers'),

    # ── Project Manager ────────────────────────────────────────────────────
    ('pm.general.access',              'مدير المشروع - وصول عام',                   'pm'),
    ('pm.reports.view',                'مدير المشروع - عرض التقارير',               'pm'),
    ('pm.reports.create',              'مدير المشروع - إضافة تقرير',                'pm'),
    ('pm.schedule.view',               'مدير المشروع - عرض الجدول',                 'pm'),
    ('pm.schedule.create',             'مدير المشروع - إنشاء جدول',                 'pm'),
    ('pm.schedule.edit',               'مدير المشروع - تعديل الجدول',               'pm'),
    ('pm.assignments.view',            'مدير المشروع - عرض التعيينات',              'pm'),
    ('pm.assignments.manage',          'مدير المشروع - إدارة التعيينات',            'pm'),
    ('pm.notifications.view',          'مدير المشروع - الإشعارات - عرض',            'pm'),
    ('pm.profile.view',                'مدير المشروع - الملف الشخصي - عرض',         'pm'),
    ('pm.approvals.manage',            'مدير المشروع - الموافقات - إدارة',           'pm'),
    ('pm.breeding.approve',            'مدير المشروع - التربية - موافقة',            'pm'),
    ('pm.breeding.reject',             'مدير المشروع - التربية - رفض',               'pm'),
    ('pm.select_project.access',       'مدير المشروع - اختيار المشروع - وصول',       'pm'),
    ('pm.daily_reports.view',          'مدير المشروع - التقارير اليومية - عرض',      'pm'),
    ('pm.daily_reports.create',        'مدير المشروع - التقارير اليومية - إضافة',    'pm'),
    ('pm.weekly_reports.view',         'مدير المشروع - التقارير الأسبوعية - عرض',    'pm'),
    ('pm.weekly_reports.create',       'مدير المشروع - التقارير الأسبوعية - إضافة',  'pm'),
    ('pm.team.view',                   'مدير المشروع - الفريق - عرض',                'pm'),
    ('pm.dogs.view',                   'مدير المشروع - الكلاب - عرض',                'pm'),

    # ── Supervisor ─────────────────────────────────────────────────────────
    ('supervisor.general.access',      'المشرف - وصول عام',                          'supervisor'),
    ('supervisor.reports.view',        'المشرف - عرض التقارير',                      'supervisor'),
    ('supervisor.reports.approve',     'المشرف - التقارير - موافقة',                 'supervisor'),
    ('supervisor.reports.reject',      'المشرف - التقارير - رفض',                    'supervisor'),
    ('supervisor.schedules.view',      'المشرف - عرض الجداول',                       'supervisor'),
    ('supervisor.schedules.create',    'المشرف - الجداول - إضافة',                   'supervisor'),
    ('supervisor.schedules.edit',      'المشرف - الجداول - تعديل',                   'supervisor'),
    ('supervisor.schedules.delete',    'المشرف - الجداول - حذف',                     'supervisor'),
    ('supervisor.schedules.lock',      'المشرف - الجداول - قفل',                     'supervisor'),
    ('supervisor.handlers.replace',    'المشرف - السائسين - استبدال',                 'supervisor'),
    ('supervisor.api.access',          'المشرف - واجهة البرمجة - وصول',             'supervisor'),

    # ── Tasks ──────────────────────────────────────────────────────────────
    ('tasks.management.view',          'المهام - عرض',                               'tasks'),
    ('tasks.management.create',        'المهام - إضافة',                             'tasks'),
    ('tasks.management.edit',          'المهام - تعديل',                             'tasks'),
    ('tasks.management.delete',        'المهام - حذف',                               'tasks'),
    ('tasks.management.assign',        'المهام - تعيين',                             'tasks'),
    ('tasks.my_tasks.view',            'المهام - مهامي - عرض',                       'tasks'),
    ('tasks.my_tasks.complete',        'المهام - مهامي - إكمال',                     'tasks'),
    ('tasks.my_tasks.start',           'المهام - مهامي - بدء',                       'tasks'),

    # ── Search ─────────────────────────────────────────────────────────────
    ('search.global.access',           'البحث العام - وصول',                          'search'),

    # ── Notifications ──────────────────────────────────────────────────────
    ('notifications.view',             'الإشعارات - عرض',                            'notifications'),
    ('notifications.mark_read',        'الإشعارات - وضع علامة مقروء',               'notifications'),
    ('notifications.settings.manage',  'الإشعارات - الإعدادات - إدارة',              'notifications'),

    # ── Backup ─────────────────────────────────────────────────────────────
    ('backup.system.manage',           'النسخ الاحتياطي - النظام - إدارة',           'backup'),
    ('backup.google_drive.manage',     'النسخ الاحتياطي - جوجل درايف - إدارة',       'backup'),
    ('backup.cloud.access',            'النسخ الاحتياطي - السحابة - وصول',           'backup'),

    # ── Settings ───────────────────────────────────────────────────────────
    ('settings.general.view',          'الإعدادات - عرض',                            'settings'),
    ('settings.general.edit',          'الإعدادات - تعديل',                          'settings'),

    # ── Audit ──────────────────────────────────────────────────────────────
    ('audit.log.view',                 'سجل التدقيق - عرض',                          'audit'),
    ('audit.log.export',               'سجل التدقيق - تصدير',                       'audit'),

    # ── API (general) ──────────────────────────────────────────────────────
    ('api.general.access',             'واجهة البرمجة - وصول عام',                  'api'),

    # ── Evaluations ────────────────────────────────────────────────────────
    ('evaluations.management.view',    'التقييمات - عرض',                            'evaluations'),
    ('evaluations.management.create',  'التقييمات - إضافة',                          'evaluations'),
    ('evaluations.management.edit',    'التقييمات - تعديل',                          'evaluations'),
    ('evaluations.management.delete',  'التقييمات - حذف',                            'evaluations'),

    # ── Locations ──────────────────────────────────────────────────────────
    ('locations.management.view',      'المواقع - عرض',                              'locations'),
    ('locations.management.create',    'المواقع - إضافة',                            'locations'),
    ('locations.management.edit',      'المواقع - تعديل',                            'locations'),
    ('locations.management.delete',    'المواقع - حذف',                              'locations'),

    # ── Suspicions ─────────────────────────────────────────────────────────
    ('suspicions.management.view',     'الشبهات - عرض',                              'suspicions'),
    ('suspicions.management.create',   'الشبهات - إضافة',                            'suspicions'),
    ('suspicions.management.edit',     'الشبهات - تعديل',                            'suspicions'),
    ('suspicions.management.delete',   'الشبهات - حذف',                              'suspicions'),

    # ── Assignments ────────────────────────────────────────────────────────
    ('assignments.management.view',    'التعيينات - عرض',                            'assignments'),
    ('assignments.management.create',  'التعيينات - إضافة',                          'assignments'),
    ('assignments.management.edit',    'التعيينات - تعديل',                          'assignments'),
    ('assignments.management.delete',  'التعيينات - حذف',                            'assignments'),

    # ── Dictionaries ───────────────────────────────────────────────────────
    ('dictionaries.management.view',   'القوائم المرجعية - عرض',                     'dictionaries'),
    ('dictionaries.management.edit',   'القوائم المرجعية - تعديل',                   'dictionaries'),
]


def upgrade():
    conn = op.get_bind()
    for i, (key, name_ar, category) in enumerate(PERMISSIONS):
        conn.execute(
            text("""
                INSERT INTO permissions (id, key, name, name_ar, category, sort_order, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), :key, :name_ar, :name_ar, :category, :sort_order, true, now(), now())
                ON CONFLICT (key) DO NOTHING
            """),
            {"key": key, "name_ar": name_ar, "category": category, "sort_order": i}
        )


def downgrade():
    conn = op.get_bind()
    keys = [p[0] for p in PERMISSIONS]
    for key in keys:
        conn.execute(
            text("DELETE FROM permissions WHERE key = :key"),
            {"key": key}
        )
