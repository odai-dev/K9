"""
Permission management utilities for K9 Operations Management System
"""

from functools import wraps
from flask import abort, request, flash, redirect, url_for, session, g
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


def canonical_permission_key(permission_key, sub_permission=None, action=None):
    """
    Normalize permission checks to canonical format: "section.subsection.action"
    Handles backward compatibility for legacy 4-argument format.
    
    Args:
        permission_key: Either canonical key (e.g., "dogs.view") or legacy category
        sub_permission: Legacy subsection name (optional)
        action: Legacy action (optional, can be string or PermissionType enum)
        
    Returns:
        Tuple of (section, subsection, permission_type) for database queries
        
    Examples:
        canonical_permission_key("dogs.view") -> ("dogs", None, PermissionType.VIEW)
        canonical_permission_key("admin.permissions") -> ("admin", "permissions", PermissionType.EDIT)
        canonical_permission_key("admin.permissions.edit") -> ("admin", "permissions", PermissionType.EDIT)
        canonical_permission_key("reports.breeding.feeding.export") -> ("reports", "breeding.feeding", PermissionType.EXPORT)
        canonical_permission_key("Reports", "Feeding Daily", "VIEW") -> ("reports", "breeding.feeding", PermissionType.VIEW)
    """
    # Handle new canonical format (e.g., "dogs.view", "reports.training.trainer_daily.view")
    if sub_permission is None and action is None:
        parts = permission_key.split('.')
        
        # Special mappings for admin permissions that use permission name as subsection
        admin_permission_mappings = {
            "admin.permissions.view": ("admin", "permissions", PermissionType.VIEW),
            "admin.permissions.edit": ("admin", "permissions", PermissionType.EDIT),
            "admin.permissions": ("admin", "permissions", PermissionType.VIEW),  # Legacy fallback
            "admin.backup": ("admin", "backup", PermissionType.VIEW),
            "admin.settings": ("admin", "settings", PermissionType.EDIT),
            "admin.audit": ("admin", "audit", PermissionType.VIEW),
        }
        
        permission_key_lower = permission_key.lower()
        if permission_key_lower in admin_permission_mappings:
            return admin_permission_mappings[permission_key_lower]
        
        if len(parts) == 2:
            # Simple format: "dogs.view"
            section, action_str = parts
            return (section.lower(), None, getattr(PermissionType, action_str.upper(), None))
        
        elif len(parts) >= 3:
            # Complex format: "reports.training.trainer_daily.view"
            section = parts[0].lower()
            action_str = parts[-1]
            subsection = '.'.join(parts[1:-1])
            return (section, subsection, getattr(PermissionType, action_str.upper(), None))
        
        else:
            # Invalid format
            return (permission_key.lower(), None, None)
    
    # Handle legacy 4-argument format
    category = permission_key.lower()
    action_lower = action.value.lower() if hasattr(action, 'value') else str(action).lower()
    action_enum = getattr(PermissionType, action_lower.upper(), None)
    
    # Map legacy categories
    legacy_mappings = {
        "breeding": ("breeding", None, action_enum),
        "تربية": ("breeding", None, action_enum),
        "training": ("training", None, action_enum),
        "تدريب": ("training", None, action_enum),
        "veterinary": ("veterinary", None, action_enum),
        "طبي": ("veterinary", None, action_enum),
    }
    
    if category in legacy_mappings and not sub_permission:
        return legacy_mappings[category]
    
    # Handle legacy report format
    if category == "reports":
        subsection_lower = sub_permission.lower() if sub_permission else ""
        
        # Map common report subsections to canonical format
        report_mappings = {
            "attendance daily sheet": ("reports", "attendance.daily", action_enum),
            "feeding daily": ("reports", "breeding.feeding", action_enum),
            "feeding weekly": ("reports", "breeding.feeding", action_enum),
            "feeding": ("reports", "breeding.feeding", action_enum),
            "checkup daily": ("reports", "breeding.checkup", action_enum),
            "checkup weekly": ("reports", "breeding.checkup", action_enum),
            "checkup": ("reports", "breeding.checkup", action_enum),
            "caretaker daily": ("reports", "breeding.caretaker_daily", action_enum),
            "caretaker": ("reports", "breeding.caretaker_daily", action_enum),
            "trainer daily": ("reports", "training.trainer_daily", action_enum),
            "veterinary daily": ("reports", "veterinary.daily", action_enum),
            "veterinary": ("reports", "veterinary", action_enum),
            "veterinary unified": ("reports", "veterinary", action_enum),
        }
        
        for key, mapping in report_mappings.items():
            if key in subsection_lower:
                return mapping
    
    # Default fallback - return None for empty subsection to match NULL in database
    return (category, sub_permission or None, action_enum)


# Permission structure - comprehensive permission system
PERMISSION_STRUCTURE = {
    "admin": {
        "permissions": "Manage user permissions",
        "settings": "Access system settings",
        "backups": "Manage backups",
        "audit": "View audit logs"
    },
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

PM_DEFAULT_PERMISSIONS = {
    "projects": ["view", "create", "edit", "delete"],
    "dogs": ["view", "create", "edit", "delete"],
    "employees": ["view", "create", "edit"],
    "attendance": ["view", "record", "edit", "reports"],
    "training": ["view", "create", "edit", "reports"],
    "veterinary": ["view", "create", "edit", "reports"],
    "breeding": ["view", "create", "edit", "reports"],
    "production": ["view", "create", "edit", "reports"],
    "reports": {
        "training": {
            "trainer_daily": ["view", "export"]
        },
        "veterinary": {
            "daily": ["view", "export"],
            "view": True,
            "export": True
        },
        "attendance": {
            "daily": ["view", "export"]
        },
        "breeding": {
            "feeding": ["view", "export"],
            "checkup": ["view", "export"],
            "caretaker_daily": ["view", "export"]
        }
    }
}

def has_permission(user, permission_key: str, sub_permission=None, action=None, project_id=None) -> bool:
    """
    Check if user has specific permission by querying SubPermission table.
    
    Args:
        user: User object
        permission_key: Permission string key (e.g., "dogs.view") or legacy category
        sub_permission: Sub-permission (for backward compatibility)
        action: Action type (for backward compatibility)
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        Boolean indicating if user has permission
    """
    if not user or not user.role:
        return False
        
    # GENERAL_ADMIN in general admin mode has ALL permissions (bypass database check)
    if _is_admin_mode(user):
        return True
    
    # Normalize permission to canonical format
    section, subsection, permission_type = canonical_permission_key(permission_key, sub_permission, action)
    
    if not permission_type:
        # Invalid permission format
        return False
    
    # Initialize request-level cache if not exists
    if not hasattr(g, 'permission_cache'):
        g.permission_cache = {}
    
    # Create cache key
    cache_key = f"{user.id}:{section}:{subsection}:{permission_type.value}:{project_id}"
    
    # Check cache first
    if cache_key in g.permission_cache:
        return g.permission_cache[cache_key]
    
    # Query SubPermission table for this specific permission
    # Handle NULL vs empty string subsection compatibility
    permission_query = SubPermission.query.filter_by(
        user_id=user.id,
        section=section,
        permission_type=permission_type,
        is_granted=True
    )
    
    # Handle subsection matching - match both NULL and empty string for compatibility
    if subsection is None or subsection == "":
        permission_query = permission_query.filter(
            (SubPermission.subsection.is_(None)) | (SubPermission.subsection == "")
        )
    else:
        permission_query = permission_query.filter_by(subsection=subsection)
    
    # Add project_id filter if specified
    if project_id is not None:
        permission_query = permission_query.filter_by(project_id=project_id)
    else:
        # For global permissions, check both project_id=None and any project-specific permissions
        permission_query = permission_query.filter(
            (SubPermission.project_id.is_(None)) | (SubPermission.project_id.isnot(None))
        )
    
    # Check if permission exists and is granted
    has_perm = permission_query.first() is not None
    
    # Cache the result
    g.permission_cache[cache_key] = has_perm
    
    return has_perm


def get_user_permissions(user_id, project_id=None):
    """
    Get all granted permissions for a user from SubPermission table.
    
    Args:
        user_id: ID of the user
        project_id: Optional project ID to filter permissions
        
    Returns:
        List of dicts with permission details:
        [{"section": "dogs", "subsection": "", "permission_type": "VIEW", "project_id": None}, ...]
    """
    user = User.query.get(user_id)
    if not user:
        return []
    
    # GENERAL_ADMIN in admin mode has all permissions
    if _is_admin_mode(user):
        # Return all possible permissions from PERMISSION_STRUCTURE
        all_perms = []
        for section, subsections in PERMISSION_STRUCTURE.items():
            if isinstance(subsections, dict):
                for subsection, permissions in subsections.items():
                    if isinstance(permissions, dict):
                        for perm_key in permissions.keys():
                            try:
                                perm_type = getattr(PermissionType, perm_key.upper())
                                all_perms.append({
                                    "section": section,
                                    "subsection": "",
                                    "permission_type": perm_type.value,
                                    "project_id": project_id
                                })
                            except AttributeError:
                                pass
        return all_perms
    
    # Query SubPermission table
    query = SubPermission.query.filter_by(user_id=user_id, is_granted=True)
    
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    
    permissions = query.all()
    
    return [
        {
            "section": p.section,
            "subsection": p.subsection,
            "permission_type": p.permission_type.value,
            "project_id": p.project_id
        }
        for p in permissions
    ]


def has_any_permission(user, permission_keys):
    """
    Check if user has ANY of the listed permissions.
    
    Args:
        user: User object
        permission_keys: List of permission keys (e.g., ["dogs.view", "dogs.edit"])
        
    Returns:
        Boolean indicating if user has at least one of the permissions
    """
    if not user or not permission_keys:
        return False
    
    # GENERAL_ADMIN in admin mode has all permissions
    if _is_admin_mode(user):
        return True
    
    # Check each permission
    for perm_key in permission_keys:
        if has_permission(user, perm_key):
            return True
    
    return False


def has_all_permissions(user, permission_keys):
    """
    Check if user has ALL listed permissions.
    
    Args:
        user: User object
        permission_keys: List of permission keys (e.g., ["dogs.view", "dogs.edit"])
        
    Returns:
        Boolean indicating if user has all of the permissions
    """
    if not user or not permission_keys:
        return False
    
    # GENERAL_ADMIN in admin mode has all permissions
    if _is_admin_mode(user):
        return True
    
    # Check each permission
    for perm_key in permission_keys:
        if not has_permission(user, perm_key):
            return False
    
    return True


def get_sections_for_user(user):
    """
    Get list of sections user has access to.
    
    Args:
        user: User object
        
    Returns:
        List of section names the user has any permission in
        (e.g., ["dogs", "employees", "reports"])
    """
    if not user:
        return []
    
    # GENERAL_ADMIN in admin mode has access to all sections
    if _is_admin_mode(user):
        return list(PERMISSION_STRUCTURE.keys())
    
    # Query unique sections from SubPermission table
    sections = db.session.query(SubPermission.section).filter_by(
        user_id=user.id,
        is_granted=True
    ).distinct().all()
    
    return [section[0] for section in sections]


def get_user_permissions_matrix(user_id, project_id=None):
    """
    Get comprehensive permissions matrix for a user by querying SubPermission table.
    For PROJECT_MANAGER users, includes default permissions overlaid with database permissions.
    
    Args:
        user_id: ID of the user
        project_id: Optional project ID to filter permissions
        
    Returns:
        Nested dict structure showing all permissions and their granted status
    """
    user = User.query.get_or_404(user_id)
    
    # GENERAL_ADMIN in general admin mode has all permissions
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
    
    # Query ALL SubPermission records from database (including revocations)
    query = SubPermission.query.filter_by(user_id=user_id)
    
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    
    permissions = query.all()
    
    # Build matrix from database permissions
    matrix = {}
    
    # Initialize matrix with False values - recursively handle nested structures
    def init_matrix_recursive(structure):
        """Recursively initialize matrix structure"""
        result = {}
        for key, value in structure.items():
            if isinstance(value, dict):
                has_permission_keys = any(k in ['view', 'create', 'edit', 'delete', 'export', 'record', 'reports', 'assign', 'approve'] for k in value.keys())
                if has_permission_keys:
                    sub_result = {}
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            sub_result[sub_key] = init_matrix_recursive(sub_value)
                        else:
                            sub_result[sub_key] = False
                    result[key] = sub_result
                else:
                    result[key] = init_matrix_recursive(value)
            else:
                result[key] = False
        return result
    
    for section, subsections in PERMISSION_STRUCTURE.items():
        if isinstance(subsections, dict):
            matrix[section] = init_matrix_recursive(subsections)
        else:
            matrix[section] = False
    
    # Overlay PM default permissions if user is PROJECT_MANAGER
    if _is_pm_mode(user):
        def apply_pm_defaults(matrix_section, defaults_section):
            """Recursively apply PM default permissions to matrix"""
            if isinstance(defaults_section, dict):
                for key, value in defaults_section.items():
                    if isinstance(value, list):
                        for perm in value:
                            if key in matrix_section and isinstance(matrix_section[key], dict):
                                if perm in matrix_section[key]:
                                    matrix_section[key][perm] = True
                    elif isinstance(value, dict):
                        if key in matrix_section and isinstance(matrix_section[key], dict):
                            apply_pm_defaults(matrix_section[key], value)
                    elif isinstance(value, bool):
                        if key in matrix_section:
                            matrix_section[key] = value
        
        for section, defaults in PM_DEFAULT_PERMISSIONS.items():
            if section in matrix:
                if isinstance(defaults, list):
                    for perm in defaults:
                        if isinstance(matrix[section], dict) and perm in matrix[section]:
                            matrix[section][perm] = True
                elif isinstance(defaults, dict):
                    if isinstance(matrix[section], dict):
                        apply_pm_defaults(matrix[section], defaults)
    
    # Populate with actual permissions from database (both grants and revocations)
    # This overrides defaults - explicit grants set to True, explicit revocations set to False
    for perm in permissions:
        section = perm.section
        subsection = perm.subsection
        perm_type = perm.permission_type.value.lower()
        granted = perm.is_granted
        
        if section not in matrix:
            continue
            
        # Handle simple section permissions (e.g., dogs.view)
        if not subsection or subsection == "":
            if isinstance(matrix[section], dict) and perm_type in matrix[section]:
                matrix[section][perm_type] = granted
        else:
            # Handle nested subsections (e.g., reports.breeding.feeding.view)
            # Navigate through nested structure to find the correct location
            current = matrix[section]
            subsection_parts = subsection.split('.')
            
            # Navigate to the target location
            for part in subsection_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            
            # Set the permission at the final location
            if isinstance(current, dict) and perm_type in current:
                current[perm_type] = granted
            
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

def bulk_update_permissions(user_id, permissions_data, updated_by, project_id=None):
    """
    Bulk update permissions for a user
    
    Can handle two modes:
    1. List mode: permissions_data is a list of dicts with keys: section, subsection, permission_type, granted
    2. Section mode: permissions_data is a dict with keys: section, is_granted (updates all permissions in that section)
    
    Args:
        user_id: ID of the user to update permissions for
        permissions_data: Either a list of permission dicts OR a dict with section and is_granted
        updated_by: ID of the user making the changes
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        Integer count of permissions updated
    """
    from k9.utils.permission_registry import PERMISSION_REGISTRY, get_section_permissions
    
    count = 0
    
    try:
        # Handle dict mode (section-wide update)
        if isinstance(permissions_data, dict) and 'section' in permissions_data and 'is_granted' in permissions_data:
            section = permissions_data['section']
            is_granted = permissions_data['is_granted']
            
            # Get all permissions for this section from the registry
            try:
                section_perms = get_section_permissions(section)
            except Exception as e:
                # Fallback if permission registry is not available
                print(f"Could not get section permissions: {e}")
                section_perms = []
            
            # Update each permission in the section
            for perm in section_perms:
                success = update_permission(
                    user_id=user_id,
                    section=section,  # Use the section passed in, not from perm dict
                    subsection=perm.get('subsection', ''),
                    permission_type=perm['permission_type'],
                    granted=is_granted,
                    updated_by=updated_by,
                    project_id=project_id
                )
                if success:
                    count += 1
        
        # Handle list mode (individual permissions)
        elif isinstance(permissions_data, list):
            for perm_data in permissions_data:
                success = update_permission(
                    user_id=user_id,
                    section=perm_data['section'],
                    subsection=perm_data.get('subsection', ''),
                    permission_type=perm_data['permission_type'],
                    granted=perm_data['granted'],
                    updated_by=updated_by,
                    project_id=project_id
                )
                if success:
                    count += 1
        else:
            print(f"Invalid permissions_data format: {type(permissions_data)}")
            return 0
        
        return count
    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk update: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_project_managers():
    """Get all project manager users"""
    return User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()

def get_all_projects():
    """Get all projects"""
    return Project.query.all()

def get_users_by_project(project_id):
    """
    Get all users assigned to a specific project regardless of role
    
    This includes:
    - Users whose employees are assigned via project_employee_assignment
    - Users whose employees are assigned via ProjectAssignment
    - The project manager
    - Users who have any permissions set for this project
    
    Args:
        project_id: ID of the project
        
    Returns:
        List of User objects (deduplicated)
    """
    from k9.models.models import Employee, project_employee_assignment, ProjectAssignment
    
    project = Project.query.get(project_id)
    if not project:
        return []
    
    users_dict = {}  # Use dict to deduplicate by user.id
    
    # 1. Get users via project_employee_assignment table
    assigned_employee_ids = db.session.query(project_employee_assignment.c.employee_id).filter(
        project_employee_assignment.c.project_id == project_id
    ).all()
    
    if assigned_employee_ids:
        employee_ids = [emp_id[0] for emp_id in assigned_employee_ids]
        employee_users = User.query.filter(User.employee_id.in_(employee_ids)).all()
        for user in employee_users:
            users_dict[user.id] = user
    
    # 2. Get users via ProjectAssignment table (handlers, vets, etc.)
    project_assignments = ProjectAssignment.query.filter_by(
        project_id=project_id,
        is_active=True
    ).filter(ProjectAssignment.employee_id.isnot(None)).all()
    
    for assignment in project_assignments:
        if assignment.employee:
            employee_users = User.query.filter_by(employee_id=assignment.employee.id).all()
            for user in employee_users:
                users_dict[user.id] = user
    
    # 3. Add project manager
    if project.manager:
        users_dict[project.manager.id] = project.manager
    
    # 4. Get users who have permissions specifically set for this project
    users_with_permissions = db.session.query(SubPermission.user_id).filter(
        SubPermission.project_id == project_id
    ).distinct().all()
    
    if users_with_permissions:
        permission_user_ids = [user_id[0] for user_id in users_with_permissions]
        permission_users = User.query.filter(User.id.in_(permission_user_ids)).all()
        for user in permission_users:
            users_dict[user.id] = user
    
    return list(users_dict.values())

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