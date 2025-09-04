"""
Enhanced Permission Management System for K9 Operations
Ultra-granular permissions with full admin control over PROJECT_MANAGER access
"""

from app import db
from models import SubPermission, PermissionAuditLog, PermissionType, UserRole, User, Project
from flask import request
from datetime import datetime
import json

# Define the complete permission hierarchy structure
PERMISSION_STRUCTURE = {
    "Dogs": {
        "عرض قائمة الكلاب": ["VIEW"],
        "عرض تفاصيل الكلب": ["VIEW"],
        "تعديل معلومات الكلب": ["EDIT"],
        "رفع السجلات الطبية": ["CREATE", "EDIT"],
        "تسجيل كلب جديد": ["CREATE"],
        "حذف كلب": ["DELETE"],
        "تعيين إلى مشروع": ["ASSIGN"],
        "تصدير بيانات الكلاب": ["EXPORT"],
    },
    "Employees": {
        "عرض قائمة الموظفين": ["VIEW"],
        "عرض تفاصيل الموظف": ["VIEW"],
        "تعديل معلومات الموظف": ["EDIT"],
        "إضافة موظف جديد": ["CREATE"],
        "حذف موظف": ["DELETE"],
        "تعيين إلى مشاريع": ["ASSIGN"],
        "تتبع الشهادات": ["VIEW", "EDIT"],
        "تصدير بيانات الموظفين": ["EXPORT"],
    },
    "Production": {
        "الوصول لدورات الحرارة": ["VIEW", "EDIT"],
        "سجلات التزاوج": ["VIEW", "CREATE", "EDIT"],
        "متتبع الحمل": ["VIEW", "CREATE", "EDIT"],
        "إدارة الجراء": ["VIEW", "CREATE", "EDIT"],
        "تعيين الجراء للتدريب": ["ASSIGN"],
        "تصدير سجلات الإنتاج": ["EXPORT"],
    },
    "Breeding": {
        "عرض الفحص الظاهري اليومي": ["VIEW"],
        "إضافة فحص ظاهري يومي": ["CREATE"],
        "تعديل الفحص الظاهري": ["EDIT"],
        "حذف الفحص الظاهري": ["DELETE"],
        "تصدير تقارير الفحص": ["EXPORT"],
        "العناية (الاستحمام)": ["VIEW", "CREATE", "EDIT", "DELETE"],
        "النظافة (البيئة/القفص)": ["VIEW", "CREATE", "EDIT", "DELETE"],
    },
    "Projects": {
        "إنشاء مشروع": ["CREATE"],
        "عرض تفاصيل المشروع": ["VIEW"],
        "تعديل المشروع": ["EDIT"],
        "حذف مشروع": ["DELETE"],
        "تعيين الكلاب": ["ASSIGN"],
        "تعيين الموظفين": ["ASSIGN"],
        "تسجيل الحوادث": ["CREATE", "EDIT"],
        "تقييم الأداء": ["CREATE", "EDIT", "APPROVE"],
        "اعتماد المشروع": ["APPROVE"],
        "تصدير تقارير المشروع": ["EXPORT"],
    },
    "Training": {
        "عرض جلسات التدريب": ["VIEW"],
        "إنشاء جلسة تدريب": ["CREATE"],
        "تعديل جلسة تدريب": ["EDIT"],
        "حذف جلسة تدريب": ["DELETE"],
        "تعيين مدربين": ["ASSIGN"],
        "اعتماد نتائج التدريب": ["APPROVE"],
        "تصدير تقارير التدريب": ["EXPORT"],
    },
    "Veterinary": {
        "عرض السجلات الطبية": ["VIEW"],
        "إضافة زيارة طبية": ["CREATE"],
        "تعديل زيارة طبية": ["EDIT"],
        "حذف زيارة طبية": ["DELETE"],
        "اعتماد التشخيص": ["APPROVE"],
        "تصدير التقارير الطبية": ["EXPORT"],
    },
    "Attendance": {
        "تعريف المناوبات": ["CREATE", "EDIT"],
        "تعيين المناوبات": ["ASSIGN"],
        "تسجيل الحضور": ["CREATE", "EDIT"],
        "عرض سجلات الحضور": ["VIEW"],
        "حذف سجل حضور": ["DELETE"],
        "اعتماد الحضور": ["APPROVE"],
        "تصدير تقارير الحضور": ["EXPORT"],
    },
    "Reports": {
        "إنشاء تقارير PDF": ["CREATE", "EXPORT"],
        "تصدير CSV": ["EXPORT"],
        "الوصول للإحصائيات": ["VIEW"],
        "تصفية حسب التاريخ": ["VIEW"],
        "تصفية حسب المشروع": ["VIEW"],
        "اعتماد التقارير": ["APPROVE"],
    },
    "Analytics": {
        "الوصول للإحصائيات": ["VIEW"],
        "تحليل الأداء": ["VIEW"],
        "إحصائيات الحضور": ["VIEW"],
        "تقارير المشاريع": ["VIEW"],
        "تحليل البيانات المتقدم": ["VIEW"],
        "تصدير التحليلات": ["EXPORT"],
    },
    "Breeding": {
        "الوصول لقائمة التربية": ["VIEW"],
        "التغذية - السجل اليومي": ["VIEW", "CREATE", "EDIT", "DELETE"],
        "الفحص الظاهري اليومي": ["VIEW", "CREATE", "EDIT"],
        "البراز والبول والقيء": ["VIEW", "CREATE", "EDIT"],
        "العناية والاستحمام": ["VIEW", "CREATE", "EDIT"],
        "جرعة الديدان": ["VIEW", "CREATE", "EDIT", "DELETE"],
        "تدريب الأنشطة اليومية": ["VIEW", "CREATE", "EDIT"],
        "النظافة والبيئة": ["VIEW", "CREATE", "EDIT"],
    }
}

def has_permission(user, section, subsection, permission_type, project_id=None):
    """
    Check if user has specific granular permission
    
    Args:
        user: User object
        section: Main section (e.g., "Dogs")
        subsection: Specific subsection (e.g., "View Dog List")
        permission_type: PermissionType enum value
        project_id: Optional project ID for project-specific permissions
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    # GENERAL_ADMIN always has full access
    if user.role == UserRole.GENERAL_ADMIN:
        return True
    
    # PROJECT_MANAGER needs explicit permission grants
    if user.role == UserRole.PROJECT_MANAGER:
        permission = SubPermission.query.filter_by(
            user_id=user.id,
            section=section,
            subsection=subsection,
            permission_type=permission_type,
            project_id=project_id
        ).first()
        
        if permission:
            return permission.is_granted
        
        # Check for global permission if no project-specific permission found
        if project_id:
            global_permission = SubPermission.query.filter_by(
                user_id=user.id,
                section=section,
                subsection=subsection,
                permission_type=permission_type,
                project_id=None
            ).first()
            
            if global_permission:
                return global_permission.is_granted
        
        # Default deny for PROJECT_MANAGER
        return False
    
    # Default deny for unknown roles
    return False

def update_permission(admin_user, target_user, section, subsection, permission_type, project_id, is_granted):
    """
    Update a specific permission for a user
    
    Args:
        admin_user: Admin user making the change
        target_user: User whose permission is being changed
        section: Main section
        subsection: Specific subsection  
        permission_type: PermissionType enum value
        project_id: Project ID (can be None for global)
        is_granted: Boolean - whether to grant or revoke permission
    
    Returns:
        bool: Success status
    """
    if admin_user.role != UserRole.GENERAL_ADMIN:
        return False
    
    try:
        # Find existing permission or create new one
        permission = SubPermission.query.filter_by(
            user_id=target_user.id,
            section=section,
            subsection=subsection,
            permission_type=permission_type,
            project_id=project_id
        ).first()
        
        old_value = permission.is_granted if permission else False
        
        if permission:
            permission.is_granted = is_granted
            permission.updated_at = datetime.utcnow()
        else:
            permission = SubPermission()
            permission.user_id = target_user.id
            permission.section = section
            permission.subsection = subsection
            permission.permission_type = permission_type
            permission.project_id = project_id
            permission.is_granted = is_granted
            db.session.add(permission)
        
        # Log the permission change
        audit_log = PermissionAuditLog()
        audit_log.changed_by_user_id = admin_user.id
        audit_log.target_user_id = target_user.id
        audit_log.section = section
        audit_log.subsection = subsection
        audit_log.permission_type = permission_type
        audit_log.project_id = project_id
        audit_log.old_value = old_value
        audit_log.new_value = is_granted
        audit_log.ip_address = request.remote_addr if request else None
        audit_log.user_agent = request.headers.get('User-Agent') if request and request.headers else None
        db.session.add(audit_log)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating permission: {str(e)}")
        return False

def get_user_permissions_matrix(user, project_id=None):
    """
    Get complete permissions matrix for a user
    
    Args:
        user: User object
        project_id: Optional project ID to filter permissions
    
    Returns:
        dict: Nested dictionary with permission status
    """
    if user.role == UserRole.GENERAL_ADMIN:
        # Admin has all permissions
        matrix = {}
        for section, subsections in PERMISSION_STRUCTURE.items():
            matrix[section] = {}
            for subsection, permission_types in subsections.items():
                matrix[section][subsection] = {}
                for perm_type in permission_types:
                    matrix[section][subsection][perm_type] = True
        return matrix
    
    # Get user's actual permissions from database
    query = SubPermission.query.filter_by(user_id=user.id)
    if project_id:
        query = query.filter(
            (SubPermission.project_id == project_id) | 
            (SubPermission.project_id.is_(None))
        )
    
    user_permissions = query.all()
    
    # Build matrix
    matrix = {}
    for section, subsections in PERMISSION_STRUCTURE.items():
        matrix[section] = {}
        for subsection, permission_types in subsections.items():
            matrix[section][subsection] = {}
            for perm_type in permission_types:
                # Look for specific permission
                perm = next((p for p in user_permissions 
                           if p.section == section and 
                              p.subsection == subsection and 
                              p.permission_type.value == perm_type and
                              (p.project_id == project_id or 
                               (project_id and p.project_id is None))), None)
                
                matrix[section][subsection][perm_type] = perm.is_granted if perm else False
    
    return matrix

def get_project_managers():
    """Get all PROJECT_MANAGER users"""
    return User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()

def get_all_projects():
    """Get all projects for permission management"""
    return Project.query.all()

def initialize_default_permissions(user):
    """
    Initialize default permissions for a new PROJECT_MANAGER user
    Generally starts with minimal permissions for security
    """
    if user.role != UserRole.PROJECT_MANAGER:
        return
    
    # Give minimal default permissions - viewing only
    default_grants = [
        ("Dogs", "عرض قائمة الكلاب", PermissionType.VIEW),
        ("Employees", "عرض قائمة الموظفين", PermissionType.VIEW),
        ("Projects", "عرض تفاصيل المشروع", PermissionType.VIEW),
        ("Attendance", "عرض سجلات الحضور", PermissionType.VIEW),
    ]
    
    for section, subsection, perm_type in default_grants:
        existing = SubPermission.query.filter_by(
            user_id=user.id,
            section=section,
            subsection=subsection,
            permission_type=perm_type,
            project_id=None  # Global permissions
        ).first()
        
        if not existing:
            permission = SubPermission()
            permission.user_id = user.id
            permission.section = section
            permission.subsection = subsection
            permission.permission_type = perm_type
            permission.project_id = None
            permission.is_granted = True
            db.session.add(permission)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing default permissions: {str(e)}")

def bulk_update_permissions(admin_user, target_user, section, is_granted, project_id=None):
    """
    Grant or revoke all permissions in a section for a user
    
    Args:
        admin_user: Admin making the change
        target_user: Target user
        section: Section name (e.g., "Dogs")
        is_granted: Boolean - grant or revoke all
        project_id: Optional project ID
    
    Returns:
        int: Number of permissions updated
    """
    if admin_user.role != UserRole.GENERAL_ADMIN:
        return 0
    
    if section not in PERMISSION_STRUCTURE:
        return 0
    
    count = 0
    subsections = PERMISSION_STRUCTURE[section]
    
    for subsection, permission_types in subsections.items():
        for perm_type_str in permission_types:
            perm_type = PermissionType(perm_type_str)
            if update_permission(admin_user, target_user, section, subsection, perm_type, project_id, is_granted):
                count += 1
    
    return count

def export_permissions_matrix(user, project_id=None):
    """
    Export user permissions as JSON for reporting/backup
    
    Args:
        user: User object
        project_id: Optional project ID
    
    Returns:
        dict: Complete permissions data
    """
    matrix = get_user_permissions_matrix(user, project_id)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value
        },
        "project_id": project_id,
        "permissions": matrix,
        "exported_at": datetime.utcnow().isoformat()
    }

def get_user_permissions_for_project(user_id, project_id):
    """Get all permissions for a user in a specific project (or global if project_id is None)"""
    permissions = SubPermission.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).all()
    
    # Build permission matrix
    matrix = {}
    for section, subsections in PERMISSION_STRUCTURE.items():
        matrix[section] = {}
        for subsection, permission_types in subsections.items():
            matrix[section][subsection] = {}
            for perm_type in permission_types:
                # Find the specific permission
                specific_perm = next(
                    (p for p in permissions if p.section == section 
                     and p.subsection == subsection 
                     and p.permission_type.value == perm_type), 
                    None
                )
                matrix[section][subsection][perm_type] = specific_perm.is_granted if specific_perm else False
    
    return matrix