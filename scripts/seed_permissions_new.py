"""
Seed script for new permission system
Creates all permission keys in the system
"""
from app import app, db
from k9.models.permissions_new import Permission


def create_permissions():
    """Create all permission keys in the system"""
    
    permissions = [
        # Dashboard & General
        {"key": "view_dashboard", "name": "عرض لوحة التحكم", "description": "الوصول إلى لوحة التحكم الرئيسية", "category": "عام"},
        
        # Dogs Management
        {"key": "view_dogs", "name": "عرض الكلاب", "description": "عرض قائمة الكلاب ومعلوماتهم", "category": "الكلاب"},
        {"key": "add_dog", "name": "إضافة كلب", "description": "إضافة كلب جديد للنظام", "category": "الكلاب"},
        {"key": "edit_dog", "name": "تعديل كلب", "description": "تعديل معلومات الكلب", "category": "الكلاب"},
        {"key": "delete_dog", "name": "حذف كلب", "description": "حذف كلب من النظام", "category": "الكلاب"},
        {"key": "view_dog_details", "name": "عرض تفاصيل الكلب", "description": "عرض التفاصيل الكاملة للكلب", "category": "الكلاب"},
        
        # Employees Management
        {"key": "view_employees", "name": "عرض الموظفين", "description": "عرض قائمة الموظفين", "category": "الموظفين"},
        {"key": "add_employee", "name": "إضافة موظف", "description": "إضافة موظف جديد", "category": "الموظفين"},
        {"key": "edit_employee", "name": "تعديل موظف", "description": "تعديل معلومات الموظف", "category": "الموظفين"},
        {"key": "delete_employee", "name": "حذف موظف", "description": "حذف موظف من النظام", "category": "الموظفين"},
        {"key": "view_employee_details", "name": "عرض تفاصيل الموظف", "description": "عرض التفاصيل الكاملة للموظف", "category": "الموظفين"},
        
        # Projects Management
        {"key": "view_projects", "name": "عرض المشاريع", "description": "عرض قائمة المشاريع", "category": "المشاريع"},
        {"key": "add_project", "name": "إضافة مشروع", "description": "إضافة مشروع جديد", "category": "المشاريع"},
        {"key": "edit_project", "name": "تعديل مشروع", "description": "تعديل معلومات المشروع", "category": "المشاريع"},
        {"key": "delete_project", "name": "حذف مشروع", "description": "حذف مشروع من النظام", "category": "المشاريع"},
        {"key": "view_project_details", "name": "عرض تفاصيل المشروع", "description": "عرض التفاصيل الكاملة للمشروع", "category": "المشاريع"},
        
        # Schedules Management
        {"key": "view_schedules", "name": "عرض الجداول", "description": "عرض جداول العمل اليومية", "category": "الجداول"},
        {"key": "create_schedule", "name": "إنشاء جدول", "description": "إنشاء جدول عمل جديد", "category": "الجداول"},
        {"key": "edit_schedule", "name": "تعديل جدول", "description": "تعديل جدول العمل", "category": "الجداول"},
        {"key": "delete_schedule", "name": "حذف جدول", "description": "حذف جدول العمل", "category": "الجداول"},
        {"key": "lock_schedule", "name": "قفل الجدول", "description": "قفل جدول العمل من التعديل", "category": "الجداول"},
        {"key": "unlock_schedule", "name": "فتح الجدول", "description": "فتح جدول مقفل للتعديل", "category": "الجداول"},
        
        # Shifts Management
        {"key": "view_shifts", "name": "عرض الورديات", "description": "عرض الورديات والمناوبات", "category": "الورديات"},
        {"key": "manage_shifts", "name": "إدارة الورديات", "description": "إدارة وتعديل الورديات", "category": "الورديات"},
        
        # Handler Reports
        {"key": "view_handler_reports", "name": "عرض تقارير السياس", "description": "عرض تقارير السياس اليومية", "category": "تقارير السياس"},
        {"key": "review_handler_reports", "name": "مراجعة تقارير السياس", "description": "مراجعة واعتماد تقارير السياس", "category": "تقارير السياس"},
        {"key": "approve_handler_report", "name": "اعتماد تقرير سائس", "description": "اعتماد تقرير سائس", "category": "تقارير السياس"},
        {"key": "reject_handler_report", "name": "رفض تقرير سائس", "description": "رفض تقرير سائس", "category": "تقارير السياس"},
        
        # Training Reports
        {"key": "view_training_reports", "name": "عرض تقارير التدريب", "description": "عرض تقارير التدريب", "category": "التدريب"},
        {"key": "create_training_report", "name": "إنشاء تقرير تدريب", "description": "إنشاء تقرير تدريب جديد", "category": "التدريب"},
        {"key": "edit_training_report", "name": "تعديل تقرير تدريب", "description": "تعديل تقرير تدريب", "category": "التدريب"},
        {"key": "delete_training_report", "name": "حذف تقرير تدريب", "description": "حذف تقرير تدريب", "category": "التدريب"},
        {"key": "export_training_reports", "name": "تصدير تقارير التدريب", "description": "تصدير تقارير التدريب لملف", "category": "التدريب"},
        
        # Veterinary Reports
        {"key": "view_vet_reports", "name": "عرض التقارير البيطرية", "description": "عرض التقارير البيطرية", "category": "البيطرة"},
        {"key": "create_vet_report", "name": "إنشاء تقرير بيطري", "description": "إنشاء تقرير بيطري جديد", "category": "البيطرة"},
        {"key": "edit_vet_report", "name": "تعديل تقرير بيطري", "description": "تعديل تقرير بيطري", "category": "البيطرة"},
        {"key": "delete_vet_report", "name": "حذف تقرير بيطري", "description": "حذف تقرير بيطري", "category": "البيطرة"},
        {"key": "approve_vet_report", "name": "اعتماد تقرير بيطري", "description": "اعتماد تقرير بيطري", "category": "البيطرة"},
        
        # Breeding Reports
        {"key": "view_breeding_reports", "name": "عرض تقارير التربية", "description": "عرض تقارير التربية", "category": "التربية"},
        {"key": "create_breeding_report", "name": "إنشاء تقرير تربية", "description": "إنشاء تقرير تربية جديد", "category": "التربية"},
        {"key": "edit_breeding_report", "name": "تعديل تقرير تربية", "description": "تعديل تقرير تربية", "category": "التربية"},
        {"key": "delete_breeding_report", "name": "حذف تقرير تربية", "description": "حذف تقرير تربية", "category": "التربية"},
        {"key": "approve_breeding_report", "name": "اعتماد تقرير تربية", "description": "اعتماد تقرير تربية", "category": "التربية"},
        
        # Feeding Reports
        {"key": "view_feeding_reports", "name": "عرض تقارير التغذية", "description": "عرض تقارير التغذية", "category": "التغذية"},
        {"key": "create_feeding_report", "name": "إنشاء تقرير تغذية", "description": "إنشاء تقرير تغذية جديد", "category": "التغذية"},
        {"key": "edit_feeding_report", "name": "تعديل تقرير تغذية", "description": "تعديل تقرير تغذية", "category": "التغذية"},
        
        # Checkup Reports
        {"key": "view_checkup_reports", "name": "عرض تقارير الفحص", "description": "عرض تقارير الفحص اليومي", "category": "الفحص اليومي"},
        {"key": "create_checkup_report", "name": "إنشاء تقرير فحص", "description": "إنشاء تقرير فحص جديد", "category": "الفحص اليومي"},
        {"key": "edit_checkup_report", "name": "تعديل تقرير فحص", "description": "تعديل تقرير فحص", "category": "الفحص اليومي"},
        
        # Caretaker Reports
        {"key": "view_caretaker_reports", "name": "عرض تقارير العناية", "description": "عرض تقارير العناية اليومية", "category": "العناية"},
        {"key": "create_caretaker_report", "name": "إنشاء تقرير عناية", "description": "إنشاء تقرير عناية جديد", "category": "العناية"},
        {"key": "approve_caretaker_report", "name": "اعتماد تقرير عناية", "description": "اعتماد تقرير عناية", "category": "العناية"},
        
        # Attendance
        {"key": "view_attendance", "name": "عرض الحضور", "description": "عرض سجلات الحضور", "category": "الحضور"},
        {"key": "manage_attendance", "name": "إدارة الحضور", "description": "إدارة وتعديل سجلات الحضور", "category": "الحضور"},
        
        # Tasks Management
        {"key": "view_tasks", "name": "عرض المهام", "description": "عرض قائمة المهام", "category": "المهام"},
        {"key": "create_task", "name": "إنشاء مهمة", "description": "إنشاء مهمة جديدة", "category": "المهام"},
        {"key": "edit_task", "name": "تعديل مهمة", "description": "تعديل مهمة موجودة", "category": "المهام"},
        {"key": "delete_task", "name": "حذف مهمة", "description": "حذف مهمة", "category": "المهام"},
        {"key": "complete_task", "name": "إكمال مهمة", "description": "وضع علامة اكتمال على مهمة", "category": "المهام"},
        
        # Users & Permissions Management
        {"key": "view_users", "name": "عرض المستخدمين", "description": "عرض قائمة المستخدمين", "category": "المستخدمين"},
        {"key": "add_user", "name": "إضافة مستخدم", "description": "إضافة مستخدم جديد", "category": "المستخدمين"},
        {"key": "edit_user", "name": "تعديل مستخدم", "description": "تعديل بيانات المستخدم", "category": "المستخدمين"},
        {"key": "delete_user", "name": "حذف مستخدم", "description": "حذف مستخدم من النظام", "category": "المستخدمين"},
        {"key": "manage_permissions", "name": "إدارة الصلاحيات", "description": "إدارة صلاحيات المستخدمين", "category": "المستخدمين"},
        
        # System Administration
        {"key": "view_audit_logs", "name": "عرض سجلات المراجعة", "description": "عرض سجلات النشاطات والتعديلات", "category": "النظام"},
        {"key": "manage_backups", "name": "إدارة النسخ الاحتياطية", "description": "إدارة النسخ الاحتياطية للنظام", "category": "النظام"},
        {"key": "export_data", "name": "تصدير البيانات", "description": "تصدير البيانات لملفات خارجية", "category": "النظام"},
        {"key": "view_system_settings", "name": "عرض إعدادات النظام", "description": "عرض إعدادات النظام", "category": "النظام"},
        {"key": "edit_system_settings", "name": "تعديل إعدادات النظام", "description": "تعديل إعدادات النظام", "category": "النظام"},
        
        # PM Dashboard
        {"key": "view_pm_dashboard", "name": "عرض لوحة مدير المشروع", "description": "الوصول إلى لوحة تحكم مدير المشروع", "category": "مدير المشروع"},
        {"key": "manage_project_assignments", "name": "إدارة تعيينات المشروع", "description": "إدارة تعيينات الموظفين والكلاب للمشاريع", "category": "مدير المشروع"},
        
        # Handler Dashboard  
        {"key": "view_handler_dashboard", "name": "عرض لوحة السائس", "description": "الوصول إلى لوحة تحكم السائس", "category": "السياس"},
        {"key": "submit_handler_report", "name": "تقديم تقرير سائس", "description": "تقديم تقرير عمل يومي", "category": "السياس"},
    ]
    
    created_count = 0
    updated_count = 0
    
    for perm_data in permissions:
        existing = Permission.query.filter_by(key=perm_data['key']).first()
        if existing:
            # Update existing
            existing.name = perm_data['name']
            existing.description = perm_data['description']
            existing.category = perm_data['category']
            updated_count += 1
        else:
            # Create new
            perm = Permission(
                key=perm_data['key'],
                name=perm_data['name'],
                description=perm_data['description'],
                category=perm_data['category']
            )
            db.session.add(perm)
            created_count += 1
    
    db.session.commit()
    
    print(f"✓ Permissions seeded successfully!")
    print(f"  - Created: {created_count} new permissions")
    print(f"  - Updated: {updated_count} existing permissions")
    print(f"  - Total: {len(permissions)} permissions in system")


if __name__ == '__main__':
    with app.app_context():
        create_permissions()
