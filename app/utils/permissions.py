"""
Permission management utilities
"""

# Training report permissions
TRAINING_PERMISSIONS = {
    "reports:training:trainer_daily:view": "View trainer daily reports",
    "reports:training:trainer_daily:export": "Export trainer daily reports to PDF"
}

# Veterinary report permissions
VETERINARY_PERMISSIONS = {
    "reports:veterinary:daily:view": "View veterinary daily reports",
    "reports:veterinary:daily:export": "Export veterinary daily reports to PDF"
}

# Default permissions for roles
DEFAULT_PERMISSIONS = {
    "GENERAL_ADMIN": [
        "reports:training:trainer_daily:view",
        "reports:training:trainer_daily:export",
        "reports:veterinary:daily:view",
        "reports:veterinary:daily:export"
    ],
    "PROJECT_MANAGER": [
        "reports:training:trainer_daily:view",
        "reports:veterinary:daily:view"
        # export permission granted explicitly if needed
    ]
}

def has_permission(user, permission_key: str) -> bool:
    """
    Check if user has specific permission
    
    Args:
        user: User object
        permission_key: Permission string key
        
    Returns:
        Boolean indicating if user has permission
    """
    if not user or not user.role:
        return False
        
    # GENERAL_ADMIN has all permissions
    if user.role.value == "GENERAL_ADMIN":
        return True
        
    # Check default permissions for role
    role_permissions = DEFAULT_PERMISSIONS.get(user.role.value, [])
    return permission_key in role_permissions