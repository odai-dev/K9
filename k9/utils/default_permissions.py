"""
Default base permissions for each user role.
These permissions are automatically granted when a new account is created.
"""

from k9.models.models import PermissionType

# Base permissions that are automatically granted to each role upon account creation
ROLE_BASE_PERMISSIONS = {
    "GENERAL_ADMIN": [
        # GENERAL_ADMIN gets ALL permissions automatically via is_admin() check
        # No need to create SubPermission records - handled by _is_admin_mode()
    ],
    
    "PROJECT_MANAGER": [
        # Dashboard access
        ("dashboard", None, PermissionType.VIEW),
        
        # Projects - view and manage assigned projects
        ("projects", None, PermissionType.VIEW),
        
        # Dogs - view and manage
        ("dogs", None, PermissionType.VIEW),
        ("dogs", None, PermissionType.EDIT),
        
        # Employees - view
        ("employees", None, PermissionType.VIEW),
        
        # Daily Schedules - full management
        ("schedule", "daily", PermissionType.VIEW),
        ("schedule", "daily", PermissionType.CREATE),
        ("schedule", "daily", PermissionType.EDIT),
        ("schedule", "daily", PermissionType.DELETE),
        
        # Legacy schedules support
        ("schedules", None, PermissionType.VIEW),
        ("schedules", None, PermissionType.CREATE),
        ("schedules", None, PermissionType.EDIT),
        ("schedules", None, PermissionType.DELETE),
        
        # Attendance - view and manage
        ("attendance", None, PermissionType.VIEW),
        ("attendance", None, PermissionType.CREATE),
        ("attendance", None, PermissionType.EDIT),
        
        # Handler reports - view and approve
        ("handler", "shift_reports", PermissionType.VIEW),
        ("handler", "daily_reports", PermissionType.VIEW),
        ("handler", "shift_reports.review", PermissionType.APPROVE),
        ("handler", "daily_reports.review", PermissionType.APPROVE),
        
        # Reports - view and approve
        ("reports", "handler.daily", PermissionType.VIEW),
        ("reports", "handler.shift", PermissionType.VIEW),
        ("reports", "handler.daily", PermissionType.APPROVE),
        ("reports", "handler.shift", PermissionType.APPROVE),
        
        # Training - view
        ("training", None, PermissionType.VIEW),
        
        # Veterinary - view
        ("veterinary", None, PermissionType.VIEW),
        
        # Breeding - view
        ("breeding", None, PermissionType.VIEW),
        
        # Tasks - manage
        ("tasks", None, PermissionType.VIEW),
        ("tasks", None, PermissionType.CREATE),
        ("tasks", None, PermissionType.EDIT),
        
        # Incidents - manage
        ("incidents", None, PermissionType.VIEW),
        ("incidents", None, PermissionType.CREATE),
        ("incidents", None, PermissionType.EDIT),
        
        # Performance - view and edit
        ("performance", None, PermissionType.VIEW),
        ("performance", None, PermissionType.EDIT),
    ],
    
    "HANDLER": [
        # Dashboard - view
        ("dashboard", None, PermissionType.VIEW),
        
        # Schedule - view only
        ("handler", "schedule.view", PermissionType.VIEW),
        
        # Daily reports - create and view
        ("handler", "reports.daily.create", PermissionType.CREATE),
        ("handler", "reports.daily.view", PermissionType.VIEW),
        
        # Shift reports - create and view
        ("handler", "reports.shift.create", PermissionType.CREATE),
        ("handler", "reports.shift.view", PermissionType.VIEW),
        
        # Dogs - view assigned dog
        ("handler", "dog.view", PermissionType.VIEW),
        
        # Notifications - view
        ("handler", "notifications.view", PermissionType.VIEW),
    ],
    
    "TRAINER": [
        # Dashboard - view
        ("dashboard", None, PermissionType.VIEW),
        
        # Training - full management
        ("training", None, PermissionType.VIEW),
        ("training", None, PermissionType.CREATE),
        ("training", None, PermissionType.EDIT),
        
        # Dogs - view
        ("dogs", None, PermissionType.VIEW),
        
        # Training reports
        ("reports", "training.trainer_daily", PermissionType.VIEW),
        ("reports", "training.trainer_daily", PermissionType.CREATE),
        ("reports", "training.trainer_daily", PermissionType.EDIT),
    ],
    
    "BREEDER": [
        # Dashboard - view
        ("dashboard", None, PermissionType.VIEW),
        
        # Breeding - full management
        ("breeding", None, PermissionType.VIEW),
        ("breeding", None, PermissionType.CREATE),
        ("breeding", None, PermissionType.EDIT),
        
        # Dogs - view and edit breeding info
        ("dogs", None, PermissionType.VIEW),
        ("dogs", None, PermissionType.EDIT),
        
        # Breeding reports
        ("reports", "breeding.feeding", PermissionType.VIEW),
        ("reports", "breeding.feeding", PermissionType.CREATE),
        ("reports", "breeding.checkup", PermissionType.VIEW),
        ("reports", "breeding.checkup", PermissionType.CREATE),
        ("reports", "breeding.caretaker_daily", PermissionType.VIEW),
        ("reports", "breeding.caretaker_daily", PermissionType.CREATE),
    ],
    
    "VET": [
        # Dashboard - view
        ("dashboard", None, PermissionType.VIEW),
        
        # Veterinary - full management
        ("veterinary", None, PermissionType.VIEW),
        ("veterinary", None, PermissionType.CREATE),
        ("veterinary", None, PermissionType.EDIT),
        
        # Dogs - view and edit medical info
        ("dogs", None, PermissionType.VIEW),
        ("dogs", None, PermissionType.EDIT),
        
        # Veterinary reports
        ("reports", "veterinary.daily", PermissionType.VIEW),
        ("reports", "veterinary.daily", PermissionType.CREATE),
        ("reports", "veterinary.daily", PermissionType.EDIT),
    ],
}


def get_base_permissions_for_role(role_name):
    """
    Get base permissions for a specific role.
    
    Args:
        role_name: Role name (e.g., "GENERAL_ADMIN", "PROJECT_MANAGER", "HANDLER")
        
    Returns:
        List of tuples (section, subsection, permission_type)
    """
    if isinstance(role_name, str):
        role_key = role_name.upper()
    else:
        # Handle UserRole enum
        role_key = role_name.value if hasattr(role_name, 'value') else str(role_name).upper()
    
    return ROLE_BASE_PERMISSIONS.get(role_key, [])


def create_base_permissions_for_user(user, db_session, project_id=None):
    """
    Create base permissions for a user based on their role.
    This should be called when a new user account is created.
    
    Args:
        user: User object
        db_session: Database session
        project_id: Optional project ID for project-specific permissions
        
    Returns:
        Number of permissions created
    """
    from k9.models.models import SubPermission, UserRole
    
    # GENERAL_ADMIN gets all permissions automatically via is_admin() check
    # No need to create SubPermission records
    if user.role == UserRole.GENERAL_ADMIN:
        return 0
    
    base_perms = get_base_permissions_for_role(user.role)
    created_count = 0
    
    for section, subsection, perm_type in base_perms:
        # Normalize subsection for storage: use "" for None to maintain compatibility
        # with existing permission-matrix code that expects empty strings
        subsection_for_db = subsection if subsection else ""
        
        # Check if permission already exists
        existing = SubPermission.query.filter_by(
            user_id=user.id,
            section=section,
            subsection=subsection_for_db,
            permission_type=perm_type,
            project_id=project_id
        ).first()
        
        if not existing:
            new_perm = SubPermission(
                user_id=user.id,
                section=section,
                subsection=subsection_for_db,  # Store as "" for compatibility
                permission_type=perm_type,
                project_id=project_id,
                is_granted=True
            )
            db_session.add(new_perm)
            created_count += 1
    
    return created_count


def is_base_permission(user, section, subsection, permission_type):
    """
    Check if a permission is a base permission for the user's role.
    Base permissions cannot be removed by admins.
    
    Args:
        user: User object
        section: Permission section
        subsection: Permission subsection (None or string, normalized for comparison)
        permission_type: PermissionType enum
        
    Returns:
        True if this is a base permission for the user's role
    """
    base_perms = get_base_permissions_for_role(user.role)
    
    # Normalize subsection: treat None and "" equivalently to handle legacy data
    subsection_normalized = subsection if subsection else None
    
    for base_section, base_subsection, base_type in base_perms:
        base_subsection_normalized = base_subsection if base_subsection else None
        
        if (base_section == section and 
            base_subsection_normalized == subsection_normalized and 
            base_type == permission_type):
            return True
    
    return False
