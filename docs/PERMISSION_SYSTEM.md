# K9 Permission System Documentation

## Overview

The K9 system uses a **Hybrid Permission Model** that combines:
1. Role-Based Access Control (RBAC) - baseline permissions per role
2. Permission Keys - granular control per screen/action
3. User-Specific Overrides - individual grants/revokes beyond role baseline

## Permission Formula

```
effective_permissions(user) = role_baseline_permissions + user_granted_overrides - user_revoked_overrides
```

## Database Models

### Location: `k9/models/permissions_v2.py`

| Model | Purpose |
|-------|---------|
| `Role` | System roles (SUPER_ADMIN, GENERAL_ADMIN, PROJECT_MANAGER, HANDLER, etc.) |
| `UserRoleAssignment` | Assigns roles to users, optionally scoped to a project |
| `PermissionOverride` | Individual permission grants/revokes per user |
| `PermissionAuditLog` | Audit trail for all permission changes |

### Permission Keys Format
```
module.action
```

Examples:
- `dogs.view`, `dogs.create`, `dogs.edit`, `dogs.delete`
- `schedule.view`, `schedule.create`, `schedule.approve`
- `reports.view`, `reports.approve`, `reports.export`

## Role Baseline Permissions

### GENERAL_ADMIN
Full access via wildcards: `dogs.*`, `employees.*`, `projects.*`, etc.

### PROJECT_MANAGER
Full access to dogs, employees, projects, training, veterinary, breeding, reports, schedules, and PM operations within their assigned project.

### HANDLER
Limited access: `dogs.view`, `training.view`, `training.create`, `schedule.view`, `reports.view`, `reports.create`, `handler_daily.*`

## Key Files Modified

| File | Purpose |
|------|---------|
| `k9/services/permission_service.py` | Core permission checking service with caching |
| `k9/routes/account_management_routes.py` | User edit and permission override routes |
| `k9/templates/admin/account_management/edit.html` | Permission management UI |
| `k9/routes/handler_routes.py` | Handler routes with shift report enforcement |
| `app.py` | Application-level shift report enforcement |

## How UI Reacts to Permission Changes

1. Template context processor `can()` function checks effective permissions
2. Menu items, buttons, and links are conditionally rendered using `{% if can('permission.key') %}`
3. Permission cache is cleared immediately when overrides are saved
4. Changes reflect on next page load without server restart

## Shift Report Enforcement (Hard Block)

### How It Works
1. `before_request` handler checks if user is HANDLER
2. Queries for completed shifts (status = PRESENT/REPLACED) where shift end time has passed
3. Checks if ShiftReport exists for each completed shift
4. If pending reports exist, redirects to `/handler/pending-reports` page

### Allowed Routes When Blocked
- `handler.new_shift_report` - Submit new report
- `handler.submit_shift_report` - POST action
- `handler.my_shift_reports` - View reports
- `handler.view_shift_report` - View specific report
- `handler.pending_reports_required` - Blocking page
- `auth.logout` - Logout
- Static files

### Blocked Routes
Everything else in the system.

---

## Manual Testing Steps

### Test 1: Granting Permissions to a Handler

1. **Login as GENERAL_ADMIN**
2. Go to **Account Management** (`/admin/accounts`)
3. Find a HANDLER user and click **Edit**
4. In the "صلاحيات إضافية للمستخدم (Overrides)" section:
   - Expand a module (e.g., "الموظفين" / Employees)
   - Change a permission from "افتراضي" to "منح إضافي"
   - Click **Save**
5. **Expected**: Success message appears
6. **Logout and login as that HANDLER**
7. **Expected**: Handler can now access the granted feature

### Test 2: Revoking Permissions

1. **Login as GENERAL_ADMIN**
2. Go to **Account Management** → Edit a user
3. Find a permission in their role baseline (shown with "الدور" badge)
4. Change it to "حجب" (Revoke)
5. Click **Save**
6. **Expected**: That user can no longer access the revoked feature

### Test 3: UI Reflection

1. After granting `employees.view` to a HANDLER
2. Login as that HANDLER
3. **Expected**: "Employees" menu item now appears in navigation
4. After revoking the permission
5. **Expected**: "Employees" menu item disappears

### Test 4: Backend Protection

1. Grant a HANDLER the `dogs.create` permission
2. Login as HANDLER, verify "Add Dog" button appears
3. Revoke the permission
4. Login as HANDLER, try to access `/dogs/add` directly
5. **Expected**: 403 Forbidden error

### Test 5: Schedule Restriction

1. Login as HANDLER
2. Try to access `/schedules/create`
3. **Expected**: 403 Forbidden (HANDLERs cannot create schedules)
4. Login as PROJECT_MANAGER
5. Access `/schedules/create`
6. **Expected**: Success (PMs can create schedules)

### Test 6: Shift Report Blocking

1. Create a completed shift for a HANDLER (status = PRESENT, end time in past)
2. Ensure no ShiftReport exists for that shift
3. Login as that HANDLER
4. **Expected**: Redirected to `/handler/pending-reports` blocking page
5. Submit a shift report for the pending shift
6. **Expected**: After submission, redirected to dashboard (if no more pending reports)

### Test 7: Real-Time Permission Updates

1. Login as GENERAL_ADMIN in one browser
2. Login as a test HANDLER in another browser
3. As ADMIN, grant a new permission to the HANDLER
4. As HANDLER, refresh the page
5. **Expected**: New permission is active immediately (no server restart)

---

## API Endpoints

### Permission Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/accounts/<user_id>/edit` | GET | View user with permission overrides |
| `/admin/accounts/<user_id>/permissions` | POST | Save permission overrides |

### Request Format (Save Permissions)
```json
{
  "grants": ["dogs.create", "employees.view"],
  "revokes": ["schedule.create"]
}
```

### Response Format
```json
{
  "success": true,
  "message": "تم حفظ 2 صلاحية ممنوحة و 1 صلاحية محجوبة"
}
```

---

## Troubleshooting

### Permission Not Taking Effect
1. Check if permission override was saved (check `permission_overrides_v2` table)
2. Clear browser cache and refresh
3. Verify cache was cleared (`PermissionService.clear_cache()` is called on save)

### Handler Still Blocked After Submitting Report
1. Check if ShiftReport was created in database
2. Verify the report is linked to the correct DailySchedule entry
3. Check if there are other pending shifts

### Admin Cannot Access Feature
1. GENERAL_ADMIN has wildcards - should have access to everything
2. Check if the permission key matches the decorator (e.g., `@require_permission('dogs.view')`)
3. Verify user role is correctly set to GENERAL_ADMIN
