"""
Permission management utilities for K9 Operations Management System
"""

from functools import wraps
from flask import abort, request, flash, redirect, url_for
from flask_login import current_user
from k9.models.models import User, Project, SubPermission, PermissionAuditLog, PermissionType, UserRole
from app import db
import json
from datetime import datetime

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
        "view": "View attendance",
        "record": "Record attendance",
        "edit": "Edit attendance",
        "reports": "Access attendance reports"
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
        
    # GENERAL_ADMIN has all permissions
    if user.role.value == "GENERAL_ADMIN":
        return True
        
    # Handle backward compatibility with old 4-argument format
    if sub_permission is not None and action is not None:
        # Old format: has_permission(user, "Breeding", "التغذية - السجل اليومي", "VIEW")
        # New format: has_permission(user, "Reports", "Feeding Daily", "VIEW")
        category = permission_key.lower()
        if category in ["breeding", "تربية"]:
            return user.role.value == "GENERAL_ADMIN"  # Only admin can access breeding for now
        elif category in ["training", "تدريب"]:
            return True  # Allow project managers to access training
        elif category in ["veterinary", "طبي"]:
            return True  # Allow project managers to access veterinary
        elif category == "reports":
            # Handle reports permissions - check against the new structure
            if user.role.value == "PROJECT_MANAGER":
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
                return user.role.value == "GENERAL_ADMIN"
        else:
            return user.role.value == "GENERAL_ADMIN"
    
    # PROJECT_MANAGER permissions are more limited
    if user.role.value == "PROJECT_MANAGER":
        # Define allowed permissions for project managers
        allowed_permissions = [
            "projects.view",
            "employees.view", 
            "dogs.view",
            "attendance.view",
            "attendance.record",
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
    
    if user.role == UserRole.GENERAL_ADMIN:
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

def update_permission(user_id, permission_key, granted, updated_by, project_id=None):
    """Update a specific permission for a user"""
    # This is a placeholder - in a real system, you'd store permissions in the database
    # The project_id parameter allows for project-scoped permissions
    return True

def bulk_update_permissions(user_id, permissions_dict, updated_by, project_id=None):
    """Bulk update permissions for a user"""
    # This is a placeholder - in a real system, you'd bulk update permissions
    # Extract project_id from permissions_dict if not provided directly
    if project_id is None and 'project_id' in permissions_dict:
        project_id = permissions_dict['project_id']
    # The project_id parameter allows for project-scoped permissions
    return True

def get_project_managers():
    """Get all project manager users"""
    return User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()

def get_all_projects():
    """Get all projects"""
    return Project.query.all()

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