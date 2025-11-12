"""
Permission management utilities for K9 Operations Management System
"""

from functools import wraps
from flask import abort, request, flash, redirect, url_for, session
from flask_login import current_user
from k9.models.models import User, Project, SubPermission, PermissionAuditLog, PermissionType, UserRole
from app import db
import json
from datetime import datetime


def _is_admin_mode(user):
    """Helper to check if user is GENERAL_ADMIN in general admin mode (not PM mode)
    
    Only GENERAL_ADMIN users in general admin mode have full administrative access.
    PROJECT_MANAGER users should NOT have full admin access and must use granular permissions.
    """
    if not user or not hasattr(user, 'role'):
        return False
    # Only GENERAL_ADMIN in general admin mode has full access
    if user.role != UserRole.GENERAL_ADMIN and user.role.value != "GENERAL_ADMIN":
        return False
    admin_mode = session.get('admin_mode', 'general_admin')
    return admin_mode == 'general_admin'


def _is_pm_mode(user):
    """Helper to check if user should be treated as PM (regular PM or GENERAL_ADMIN in PM mode)"""
    if not user or not hasattr(user, 'role'):
        return False
    # Regular PROJECT_MANAGER
    if user.role == UserRole.PROJECT_MANAGER or user.role.value == "PROJECT_MANAGER":
        return True
    # GENERAL_ADMIN in PM mode
    if user.role == UserRole.GENERAL_ADMIN or user.role.value == "GENERAL_ADMIN":
        admin_mode = session.get('admin_mode', 'general_admin')
        return admin_mode == 'project_manager'
    return False

# Permission structure - comprehensive permission system
PERMISSION_STRUCTURE = {
    "projects": {
        "view": "View projects",
        "create": "Create projects", 
        "edit": "Edit projects",
        "delete": "Delete projects"
    },
    "employees": {
        "view": "View employees",
        "create": "Create employees",
        "edit": "Edit employees", 
        "delete": "Delete employees"
    },
    "dogs": {
        "view": "View dogs",
        "create": "Create dogs",
        "edit": "Edit dogs",
        "delete": "Delete dogs"
    },
    "attendance": {
        "view": "View daily schedules and attendance",
        "record": "Create and record daily schedules",
        "edit": "Edit daily schedules",
        "reports": "Access daily schedule reports"
    },
    "training": {
        "view": "View training records",
        "create": "Create training records", 
        "edit": "Edit training records",
        "reports": "Access training reports"
    },
    "veterinary": {
        "view": "View veterinary records",
        "create": "Create veterinary records",
        "edit": "Edit veterinary records", 
        "reports": "Access veterinary reports"
    },
    "breeding": {
        "view": "View breeding records",
        "create": "Create breeding records",
        "edit": "Edit breeding records",
        "reports": "Access breeding reports"
    },
    "production": {
        "view": "View production records",
        "create": "Create production records",
        "edit": "Edit production records",
        "reports": "Access production records"
    },
    "reports": {
        "training": {
            "trainer_daily": {
                "view": "View trainer daily reports",
                "export": "Export trainer daily reports"
            }
        },
        "veterinary": {
            "daily": {
                "view": "View veterinary daily reports", 
                "export": "Export veterinary daily reports"
            },
            "view": "View veterinary reports (unified)",
            "export": "Export veterinary reports (unified)"
        },
        "attendance": {
            "daily": {
                "view": "View attendance daily reports",
                "export": "Export attendance daily reports"
            }
        },
        "breeding": {
            "feeding": {
                "view": "View feeding reports (all ranges)",
                "export": "Export feeding reports (all ranges)"
            },
            "checkup": {
                "view": "View checkup reports (all ranges)",
                "export": "Export checkup reports (all ranges)"
            },
            "caretaker_daily": {
                "view": "View caretaker daily reports",
                "export": "Export caretaker daily reports"
            }
        }
    }
}

def has_permission(user, permission_key: str, sub_permission=None, action=None) -> bool:
    """
    Check if user has specific permission
    
    Args:
        user: User object
        permission_key: Permission string key (or category for backward compatibility)
        sub_permission: Sub-permission (for backward compatibility)
        action: Action type (for backward compatibility)
        
    Returns:
        Boolean indicating if user has permission
    """
    if not user or not user.role:
        return False
        
    # GENERAL_ADMIN in general admin mode has all permissions
    # GENERAL_ADMIN in PM mode will be treated like PROJECT_MANAGER
    if _is_admin_mode(user):
        return True
        
    # Handle backward compatibility with old 4-argument format
    if sub_permission is not None and action is not None:
        # Old format: has_permission(user, "Breeding", "التغذية - السجل اليومي", "VIEW")
        # New format: has_permission(user, "Reports", "Feeding Daily", "VIEW")
        category = permission_key.lower()
        if category in ["breeding", "تربية"]:
            return _is_admin_mode(user)  # Only admin can access breeding for now
        elif category in ["training", "تدريب"]:
            return True  # Allow project managers to access training
        elif category in ["veterinary", "طبي"]:
            return True  # Allow project managers to access veterinary
        elif category == "reports":
            # Handle reports permissions - check against the new structure
            if _is_pm_mode(user):
                # Map subsection names to permission keys
                subsection_lower = sub_permission.lower()
                action_lower = action.value.lower() if hasattr(action, 'value') else str(action).lower()
                
                # Map common report subsections - support both legacy and unified
                if "attendance daily sheet" in subsection_lower:
                    perm_key = f"reports.attendance.daily.{action_lower}"
                elif any(x in subsection_lower for x in ["feeding daily", "feeding weekly", "feeding"]):
                    perm_key = f"reports.breeding.feeding.{action_lower}"
                elif any(x in subsection_lower for x in ["checkup daily", "checkup weekly", "checkup"]):
                    perm_key = f"reports.breeding.checkup.{action_lower}"
                elif any(x in subsection_lower for x in ["caretaker daily", "caretaker"]):
                    perm_key = f"reports.breeding.caretaker_daily.{action_lower}"
                elif "trainer daily" in subsection_lower:
                    perm_key = f"reports.training.trainer_daily.{action_lower}"
                elif "veterinary daily" in subsection_lower:
                    perm_key = f"reports.veterinary.daily.{action_lower}"
                elif any(x in subsection_lower for x in ["veterinary", "veterinary unified"]):
                    perm_key = f"reports.veterinary.{action_lower}"
                else:
                    return False  # Unknown report type
                
                # Check against allowed permissions
                allowed_permissions = [
                    "reports.training.trainer_daily.view",
                    "reports.training.trainer_daily.export",
                    "reports.veterinary.daily.view",
                    "reports.veterinary.daily.export",
                    "reports.veterinary.view",
                    "reports.veterinary.export",
                    "reports.attendance.daily.view",
                    "reports.attendance.daily.export",
                    "reports.breeding.feeding.view",
                    "reports.breeding.feeding.export",
                    "reports.breeding.checkup.view",
                    "reports.breeding.checkup.export",
                    "reports.breeding.caretaker_daily.view",
                    "reports.breeding.caretaker_daily.export"
                ]
                return perm_key in allowed_permissions
            else:
                return _is_admin_mode(user)
        else:
            return _is_admin_mode(user)
    
    # PROJECT_MANAGER permissions are more limited (includes GENERAL_ADMIN in PM mode)
    if _is_pm_mode(user):
        # Define allowed permissions for project managers
        allowed_permissions = [
            "projects.view",
            "employees.view", 
            "dogs.view",
            "attendance.view",
            "attendance.record",
            "attendance.edit",
            "training.view",
            "training.create",
            "veterinary.view",
            "breeding.view",
            "production.view",
            "reports.training.trainer_daily.view",
            "reports.training.trainer_daily.export",
            "reports.veterinary.daily.view",
            "reports.veterinary.daily.export",
            "reports.veterinary.view",
            "reports.veterinary.export",
            "reports.attendance.daily.view",
            "reports.attendance.daily.export",
            "reports.breeding.feeding.view",
            "reports.breeding.feeding.export",
            "reports.breeding.checkup.view",
            "reports.breeding.checkup.export",
            "reports.breeding.caretaker_daily.view",
            "reports.breeding.caretaker_daily.export"
        ]
        return permission_key in allowed_permissions
        
    return False

def get_user_permissions_matrix(user_id, project_id=None):
    """Get comprehensive permissions matrix for a user"""
    user = User.query.get_or_404(user_id)
    
    # GENERAL_ADMIN in general admin mode has all permissions
    # GENERAL_ADMIN in PM mode will be treated like PROJECT_MANAGER
    if _is_admin_mode(user):
        # General admin has all permissions
        matrix = {}
        for section, subsections in PERMISSION_STRUCTURE.items():
            if isinstance(subsections, dict):
                matrix[section] = {}
                for subsection, permissions in subsections.items():
                    if isinstance(permissions, dict):
                        matrix[section][subsection] = {perm: True for perm in permissions.keys()}
                    else:
                        matrix[section][subsection] = True
            else:
                matrix[section] = True
        return matrix
    
    # For project managers, return limited permissions based on project_id
    matrix = {}
    for section, subsections in PERMISSION_STRUCTURE.items():
        if isinstance(subsections, dict):
            matrix[section] = {}
            for subsection, permissions in subsections.items():
                if isinstance(permissions, dict):
                    matrix[section][subsection] = {perm: False for perm in permissions.keys()}
                else:
                    matrix[section][subsection] = False
        else:
            matrix[section] = False
            
    return matrix

def update_permission(user_id, section, subsection, permission_type, granted, updated_by, project_id=None):
    """
    Update a specific permission for a user
    
    Args:
        user_id: ID of the user to update permissions for
        section: Permission section (e.g., "dogs", "employees")
        subsection: Permission subsection (can be empty string for main section)
        permission_type: PermissionType enum value
        granted: Boolean indicating if permission is granted
        updated_by: ID of the user making the change
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        Boolean indicating success
    """
    try:
        from flask import request
        
        existing = SubPermission.query.filter_by(
            user_id=user_id,
            section=section,
            subsection=subsection if subsection else "",
            permission_type=permission_type,
            project_id=project_id
        ).first()
        
        old_value = existing.is_granted if existing else False
        
        if existing:
            existing.is_granted = granted
            existing.updated_at = datetime.utcnow()
        else:
            new_perm = SubPermission(
                user_id=user_id,
                section=section,
                subsection=subsection if subsection else "",
                permission_type=permission_type,
                project_id=project_id,
                is_granted=granted
            )
            db.session.add(new_perm)
        
        audit_log = PermissionAuditLog(
            changed_by_user_id=updated_by,
            target_user_id=user_id,
            section=section,
            subsection=subsection if subsection else "",
            permission_type=permission_type,
            project_id=project_id,
            old_value=old_value,
            new_value=granted,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(audit_log)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error updating permission: {e}")
        return False

def bulk_update_permissions(user_id, permissions_list, updated_by, project_id=None):
    """
    Bulk update permissions for a user
    
    Args:
        user_id: ID of the user to update permissions for
        permissions_list: List of dicts with keys: section, subsection, permission_type, granted
        updated_by: ID of the user making the changes
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        Boolean indicating success
    """
    try:
        for perm_data in permissions_list:
            update_permission(
                user_id=user_id,
                section=perm_data['section'],
                subsection=perm_data.get('subsection', ''),
                permission_type=perm_data['permission_type'],
                granted=perm_data['granted'],
                updated_by=updated_by,
                project_id=project_id
            )
        return True
    except Exception as e:
        print(f"Error in bulk update: {e}")
        return False

def get_project_managers():
    """Get all project manager users"""
    return User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()

def get_all_projects():
    """Get all projects"""
    return Project.query.all()

def get_users_by_project(project_id):
    """
    Get all users (with their employee info) assigned to a specific project
    
    Args:
        project_id: ID of the project
        
    Returns:
        List of User objects with employee relationship loaded
    """
    from k9.models.models import Employee, project_employee_assignment
    
    project = Project.query.get(project_id)
    if not project:
        return []
    
    assigned_employee_ids = db.session.query(project_employee_assignment.c.employee_id).filter(
        project_employee_assignment.c.project_id == project_id
    ).all()
    
    employee_ids = [emp_id[0] for emp_id in assigned_employee_ids]
    
    users = User.query.filter(User.employee_id.in_(employee_ids)).all()
    
    if project.manager:
        if project.manager not in users:
            users.append(project.manager)
    
    return users

def get_user_permissions_by_project(user_id, project_id):
    """
    Get all permissions for a user within a specific project
    
    Args:
        user_id: ID of the user
        project_id: ID of the project
        
    Returns:
        Dict of permissions with structure: {section: {subsection: {permission_type: is_granted}}}
    """
    user = User.query.get(user_id)
    if not user:
        return {}
    
    if _is_admin_mode(user):
        from k9.utils.permission_registry import PERMISSION_REGISTRY
        permissions = {}
        for section_key, section_data in PERMISSION_REGISTRY.items():
            permissions[section_key] = {}
            def extract_perms(data, path=""):
                result = {}
                if "permissions" in data:
                    for perm_key, perm_data in data["permissions"].items():
                        result[perm_key] = {
                            "granted": True,
                            "permission_type": perm_data["permission_type"].value if hasattr(perm_data["permission_type"], 'value') else str(perm_data["permission_type"])
                        }
                return result
            permissions[section_key] = extract_perms(section_data)
        return permissions
    
    db_permissions = SubPermission.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).all()
    
    permissions = {}
    for perm in db_permissions:
        if perm.section not in permissions:
            permissions[perm.section] = {}
        
        key = f"{perm.subsection}.{perm.permission_type.value}" if perm.subsection else perm.permission_type.value
        permissions[perm.section][key] = {
            "granted": perm.is_granted,
            "permission_type": perm.permission_type.value
        }
    
    return permissions

def initialize_default_permissions(user):
    """Initialize default permissions for a user"""
    # This is a placeholder - permissions are handled by role
    pass

def export_permissions_matrix(users, project_id=None):
    """Export permissions matrix to CSV format"""
    # This is a placeholder for export functionality
    # The project_id parameter allows filtering permissions by project
    return "permissions_export.csv"

def get_user_permissions_for_project(user, project_id):
    """Get user permissions for a specific project"""
    if user.role == UserRole.GENERAL_ADMIN:
        return list(PERMISSION_STRUCTURE.keys())
    
    # Project managers have limited permissions
    return ["view", "record"]

def get_project_manager_permissions(user, permissions):
    """Get permissions for project manager users"""
    return permissions if user.role == UserRole.GENERAL_ADMIN else []

def check_project_access(user, project_id):
    """Check if user has access to a specific project"""
    if user.role == UserRole.GENERAL_ADMIN:
        return True
        
    # For project managers, you might want to implement project-specific access control
    return True  # Simplified for now