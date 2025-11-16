# Admin Permissions Bug Fix Summary

## Issue
The admin permissions module had a critical bug where the permission key `"admin.permissions"` didn't follow the canonical format `"section.subsection.action"`, preventing project managers from accessing the permissions dashboard even when granted the permission.

## Changes Made

### 1. Updated Permission Mapping (k9/utils/permission_utils.py)
**File:** `k9/utils/permission_utils.py`

Added proper canonical permission key mappings:
- `admin.permissions.view` → (admin, permissions, PermissionType.VIEW) - for viewing permissions dashboard
- `admin.permissions.edit` → (admin, permissions, PermissionType.EDIT) - for editing permissions
- `admin.permissions` → (admin, permissions, PermissionType.VIEW) - legacy fallback for compatibility

### 2. Updated Admin Routes (k9/routes/admin_routes.py)
**File:** `k9/routes/admin_routes.py`

Updated all admin permission routes to use canonical keys:

#### Read-only routes (using `admin.permissions.view`):
- `/admin/permissions` - permissions dashboard
- `/admin/permissions/user/<user_id>` - get user permissions
- `/admin/permissions/comprehensive` - comprehensive permissions interface
- `/admin/permissions/projects` - get projects list
- `/admin/permissions/users/<project_id>` - get project users
- `/admin/permissions/matrix/<user_id>/<project_id>` - get permissions matrix
- `/admin/permissions/audit` - view audit log
- `/admin/permissions/export/<user_id>` - export as JSON
- `/admin/permissions/export-pdf/<user_id>` - export as PDF
- `/admin/permissions/export-excel` - export all as Excel
- `/admin/permissions/preview/<user_id>` - preview PM view

#### Write routes (using `admin.permissions.edit`):
- `/admin/permissions/update` - update single permission
- `/admin/permissions/bulk-update` - bulk update permissions
- `/admin/permissions/initialize/<user_id>` - initialize default permissions

### 3. Updated Templates
**Files:** 
- `k9/templates/pm/base_pm.html`

Changed permission check from:
```jinja2
{% if has_permission(current_user, 'admin.permissions') %}
```

To:
```jinja2
{% if has_permission(current_user, 'admin.permissions.view') %}
```

**Note:** `k9/templates/base.html` already had the correct canonical format.

## Result

Now when a GENERAL_ADMIN grants the following permissions to a PROJECT_MANAGER:
- **admin.permissions.view** - Allows viewing the permissions dashboard and audit logs
- **admin.permissions.edit** - Allows modifying user permissions

The PROJECT_MANAGER can successfully:
1. Access the permissions dashboard via the navbar link
2. View user permissions and audit logs
3. Edit permissions (if granted admin.permissions.edit)
4. Export permissions data

## Testing

The application has been restarted and is running successfully with these changes. All blueprints registered correctly without errors.

## Backward Compatibility

The legacy `"admin.permissions"` key is maintained as a fallback that maps to VIEW permission, ensuring existing permission grants continue to work.
