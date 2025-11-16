# Security Guidelines - K9 Operations System

## Critical Anti-Patterns - NEVER DO THESE

### ❌ 1. Bypassing Role Checks with `if True`
**WRONG:**
```python
# ROLE CHECK DISABLED: if current_user.role == UserRole.GENERAL_ADMIN:
if True:  # Role check bypassed
    # Admin-only code
```

**CORRECT:**
```python
if current_user.role == UserRole.GENERAL_ADMIN:
    # Admin-only code
```

---

### ❌ 2. Using Non-Existent Properties
**WRONG:**
```python
{% if current_user.is_general_admin %}
```

**CORRECT:**
```python
{% if is_admin() %}
```

The `User` model does NOT have an `is_general_admin` property. Always use the `is_admin()` helper function which properly checks both role AND admin_mode.

---

### ❌ 3. Forgetting @login_required Decorator
**WRONG:**
```python
@main_bp.route('/admin/sensitive-data')
def sensitive_data():
    return render_template('admin/data.html')
```

**CORRECT:**
```python
@main_bp.route('/admin/sensitive-data')
@login_required
@require_permission('admin.data.view')
def sensitive_data():
    return render_template('admin/data.html')
```

---

### ❌ 4. Hardcoding Admin Access
**WRONG:**
```python
if True:  # Always allow admin
    return redirect('/admin')
```

**CORRECT:**
```python
if is_admin(current_user):
    return redirect('/admin')
```

---

## Proper Access Control Patterns

### For Routes (Python)
```python
from flask_login import login_required
from k9.utils.permission_decorators import require_permission
from k9.utils.pm_scoping import is_admin

@main_bp.route('/dogs/add', methods=['GET', 'POST'])
@login_required
@require_permission('dogs.management.create')
def dogs_add():
    # Only accessible to users with the permission
    pass
```

### For Templates (Jinja2)
```html
<!-- Check admin status -->
{% if is_admin() %}
    <a href="{{ url_for('account_management.index') }}">إدارة الحسابات</a>
{% endif %}

<!-- Check specific permission -->
{% if has_permission(current_user, 'dogs.management.view') %}
    <a href="{{ url_for('main.dogs') }}">قائمة الكلاب</a>
{% endif %}
```

---

## Available Helper Functions

### In Templates
- `is_admin()` - Check if GENERAL_ADMIN in admin mode
- `has_permission(user, 'section.subsection.action')` - Check specific permission
- `has_any_permission(user, ['perm1', 'perm2'])` - Check if user has any of the permissions
- `has_all_permissions(user, ['perm1', 'perm2'])` - Check if user has all permissions
- `get_sections_for_user(user)` - Get all sections user has access to

### In Routes/Python
- `is_admin(user=None)` - From `k9.utils.pm_scoping`
- `@require_permission('section.subsection.action')` - Decorator
- `@require_any_permission(['perm1', 'perm2'])` - Decorator
- `@admin_required` - Decorator for GENERAL_ADMIN only

---

## Validation Script

Before deploying or committing major changes, run:
```bash
python3 scripts/validate_security.py
```

This will scan for:
- Bypassed role checks (`if True`)
- Disabled check comments
- Non-existent properties
- Missing `@login_required` decorators
- Other common security issues

---

## Role and Permission System

### User Roles
1. **GENERAL_ADMIN** - Full system access
   - Can switch between `admin_mode` and `project_manager` mode
   - In admin mode: unrestricted access
   - In PM mode: restricted to assigned projects

2. **PROJECT_MANAGER** - Project-scoped access
   - Access controlled by `SubPermission` table
   - Cannot access admin features
   - Scoped to assigned projects only

3. **HANDLER** - Handler operations only
   - Daily reports, schedules, tasks
   - No admin or management access

### Admin Mode Checking
```python
from k9.utils.pm_scoping import is_admin

# Check if user is GENERAL_ADMIN in admin mode
if is_admin(current_user):
    # Full admin access
    pass
```

The `is_admin()` function checks:
1. User role is `GENERAL_ADMIN`
2. `session['admin_mode'] == 'general_admin'` (not in PM mode)

---

## Common Mistakes to Avoid

1. **Don't check `current_user.role` directly in templates** - Use helper functions
2. **Don't assume GENERAL_ADMIN always has full access** - Check admin_mode
3. **Don't skip decorators for "quick testing"** - They prevent real vulnerabilities
4. **Don't use `if True` for debugging** - Use proper logging instead
5. **Don't create custom admin checks** - Use existing `is_admin()` function

---

## Audit and Logging

All permission changes are automatically logged to `PermissionAuditLog`. When making access control changes:
- Changes are tracked with timestamp, user, and details
- Review audit logs regularly for suspicious activity
- Use `log_audit()` for custom security events

---

## Pre-Deployment Checklist

Before deploying to production:
- [ ] Run `python3 scripts/validate_security.py`
- [ ] No `if True` bypasses in code
- [ ] All routes have `@login_required`
- [ ] All admin routes check `is_admin()` or use `@admin_required`
- [ ] Templates use helper functions, not direct property access
- [ ] No hardcoded credentials or test data in code
- [ ] Review recent audit logs for anomalies

---

## Emergency Response

If a security issue is discovered:
1. Document the issue immediately
2. Run validation script to find all instances
3. Fix all occurrences systematically
4. Test with both GENERAL_ADMIN and PROJECT_MANAGER accounts
5. Review audit logs for potential exploitation
6. Update this document with new anti-patterns if needed
