"""
Permission keys for PM Daily Report system
Extends the existing permission system with new granular permissions
"""

# PM Daily Report permission keys
PM_DAILY_PERMISSIONS = {
    "reports:attendance:pm_daily:view": "View PM Daily Reports",
    "reports:attendance:pm_daily:export": "Export PM Daily Reports to PDF",
}

# Unified Matrix permission keys
UNIFIED_MATRIX_PERMISSIONS = {
    "reports:attendance:unified:view": "View Unified Attendance Matrix",
    "reports:attendance:unified:export": "Export Unified Attendance Matrix",
}

# Excretion permission keys
EXCRETION_PERMISSIONS = {
    "excretion:view": "View Excretion Logs",
    "excretion:create": "Create Excretion Logs",
    "excretion:edit": "Edit Excretion Logs",
    "excretion:delete": "Delete Excretion Logs",
}

# Deworming permission keys
DEWORMING_PERMISSIONS = {
    "deworming:view": "View Deworming Logs",
    "deworming:create": "Create Deworming Logs",
    "deworming:edit": "Edit Deworming Logs",
    "deworming:delete": "Delete Deworming Logs",
}

# Combined permissions
ALL_PERMISSIONS = {**PM_DAILY_PERMISSIONS, **UNIFIED_MATRIX_PERMISSIONS, **EXCRETION_PERMISSIONS, **DEWORMING_PERMISSIONS}

# Default permissions for roles
DEFAULT_ROLE_PERMISSIONS = {
    "GENERAL_ADMIN": [
        "reports:attendance:pm_daily:view",
        "reports:attendance:pm_daily:export",
        "reports:attendance:unified:view",
        "reports:attendance:unified:export",
        "excretion:view",
        "excretion:create",
        "excretion:edit",
        "excretion:delete",
        "deworming:view",
        "deworming:create",
        "deworming:edit",
        "deworming:delete",
    ],
    "PROJECT_MANAGER": [
        "reports:attendance:pm_daily:view",
        "reports:attendance:unified:view",
        "excretion:view",
        "excretion:create",
        "excretion:edit",
        "deworming:view",
        "deworming:create",
        "deworming:edit",
        # Note: delete and export permissions only if explicitly granted
    ]
}

def get_pm_daily_permissions():
    """Get all PM Daily Report permission keys"""
    return PM_DAILY_PERMISSIONS

def get_default_permissions_for_role(role_name):
    """Get default PM Daily permissions for a role"""
    return DEFAULT_ROLE_PERMISSIONS.get(role_name, [])