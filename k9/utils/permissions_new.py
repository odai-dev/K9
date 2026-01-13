"""
New Simple Permission System Utilities
Clean, predictable, and stable permission checking and management.
"""
from functools import wraps
from flask import session, abort, redirect, url_for, flash, request, has_request_context, jsonify
from flask_login import current_user


def _is_admin_mode(user):
    """
    Check if user is GENERAL_ADMIN in general admin mode.
    GENERAL_ADMIN in admin mode has ALL permissions automatically.
    """
    if not user or not hasattr(user, 'role'):
        return False
    
    from k9.models.models import UserRole
    if user.role != UserRole.GENERAL_ADMIN:
        return False
    
    admin_mode = session.get('admin_mode', 'general_admin')
    return admin_mode == 'general_admin'


def load_user_permissions(user_id):
    """
    Load all permission keys for a user into the session using V2 PermissionService.
    Called during login to cache permissions for fast checking.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Set of permission keys (strings)
    """
    from k9.services.permission_service import PermissionService
    from k9.models.models import User
    from datetime import datetime
    
    # Use V2 PermissionService to get all user permissions (resolves roles + wildcards)
    permission_keys = PermissionService.get_user_permissions(user_id)
    
    # Store in session for fast access
    session['user_permissions'] = list(permission_keys)
    
    # Store the timestamp when permissions were loaded
    user = User.query.get(user_id)
    if user and user.permissions_updated_at:
        session['permissions_loaded_at'] = user.permissions_updated_at.isoformat()
    else:
        session['permissions_loaded_at'] = datetime.utcnow().isoformat()
    
    session.modified = True
    
    return permission_keys


def _should_reload_permissions():
    """
    Check if permissions should be reloaded from database.
    Returns True if the user's permissions have been updated since they were loaded.
    Uses flask.g to cache the check per request to avoid multiple DB queries.
    """
    from flask import g
    from k9.models.models import User
    from datetime import datetime
    
    if not current_user.is_authenticated:
        return False
    
    # Cache the result in flask.g to avoid multiple DB queries per request
    cache_key = '_permissions_reload_checked'
    if hasattr(g, cache_key):
        return getattr(g, cache_key)
    
    loaded_at_str = session.get('permissions_loaded_at')
    if not loaded_at_str:
        setattr(g, cache_key, True)
        return True  # Never loaded, should load
    
    user = User.query.get(current_user.id)
    if not user or not user.permissions_updated_at:
        setattr(g, cache_key, False)
        return False
    
    try:
        loaded_at = datetime.fromisoformat(loaded_at_str)
        result = user.permissions_updated_at > loaded_at
        setattr(g, cache_key, result)
        return result
    except (ValueError, TypeError):
        setattr(g, cache_key, True)
        return True  # Invalid format, reload to be safe


def get_user_permissions():
    """
    Get current user's permissions using V2 PermissionService.
    Uses session cache with automatic reload when permissions change.
    
    Returns:
        Set of permission keys (strings)
    """
    if not current_user.is_authenticated:
        return set()
    
    # Check if permissions need to be reloaded (they were updated by admin)
    if _should_reload_permissions():
        load_user_permissions(current_user.id)
    
    # Try session first for performance
    perms = session.get('user_permissions')
    if perms is not None:
        return set(perms)
    
    # Fallback: load directly from V2 PermissionService
    from k9.services.permission_service import PermissionService
    return PermissionService.get_user_permissions(current_user.id)


def has_permission(permission_key, user=None, project_id=None):
    """
    Check if current user has a specific permission.
    Uses V2 PermissionService for role-based access control.
    GENERAL_ADMIN users in admin mode have full access (admin bypass preserved).
    
    Args:
        permission_key: The permission key to check (e.g., 'dogs.view')
        user: Optional user object (defaults to current_user)
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        True if user has the permission, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Admin mode bypass: GENERAL_ADMIN in admin mode has full access
    if _is_admin_mode(user):
        return True
    
    # Use V2 PermissionService for role-based check
    from k9.services.permission_service import PermissionService
    return PermissionService.has_permission(user.id, permission_key, project_id)


def has_any_permission(*permission_keys, user=None, project_id=None):
    """
    Check if current user has ANY of the specified permissions.
    Uses V2 PermissionService for role-based access control.
    GENERAL_ADMIN users in admin mode have full access (admin bypass preserved).
    
    Args:
        *permission_keys: Variable number of permission keys
        user: Optional user object (defaults to current_user)
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        True if user has at least one permission, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Admin mode bypass: GENERAL_ADMIN in admin mode has full access
    if _is_admin_mode(user):
        return True
    
    # Use V2 PermissionService
    from k9.services.permission_service import PermissionService
    return PermissionService.has_any_permission(user.id, list(permission_keys), project_id)


def has_all_permissions(*permission_keys, user=None, project_id=None):
    """
    Check if current user has ALL of the specified permissions.
    Uses V2 PermissionService for role-based access control.
    GENERAL_ADMIN users in admin mode have full access (admin bypass preserved).
    
    Args:
        *permission_keys: Variable number of permission keys
        user: Optional user object (defaults to current_user)
        project_id: Optional project ID for project-scoped permissions
        
    Returns:
        True if user has all permissions, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Admin mode bypass: GENERAL_ADMIN in admin mode has full access
    if _is_admin_mode(user):
        return True
    
    # Use V2 PermissionService
    from k9.services.permission_service import PermissionService
    return PermissionService.has_all_permissions(user.id, list(permission_keys), project_id)


def _extract_project_id(kwargs):
    """
    Extract and normalize project_id from various request contexts.
    Checks: kwargs, query args, form data, JSON body, and session.
    Returns integer project_id or None.
    """
    project_id = None
    
    # Check kwargs first (route parameters)
    if 'project_id' in kwargs:
        project_id = kwargs.get('project_id')
    # Check query string
    elif request.args.get('project_id'):
        project_id = request.args.get('project_id')
    # Check form data
    elif request.form.get('project_id'):
        project_id = request.form.get('project_id')
    # Check JSON body
    elif request.is_json and request.json:
        project_id = request.json.get('project_id')
    # Check session
    elif session.get('current_project_id'):
        project_id = session.get('current_project_id')
    
    # Normalize to integer if present
    if project_id is not None:
        try:
            return int(project_id)
        except (ValueError, TypeError):
            return None
    return None


def require_permission(permission_key):
    """
    Decorator to enforce permission on a route.
    If user doesn't have the permission, redirect to dashboard with error.
    Handles both regular requests and AJAX/API requests.
    Automatically extracts project_id from kwargs, args, form, JSON, or session for project-scoped checks.
    
    Args:
        permission_key: The permission key required for this route (e.g., 'dogs.view')
        
    Usage:
        @app.route('/dogs')
        @require_permission('dogs.view')
        def view_dogs():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if this is an AJAX/JSON request
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
                return redirect(url_for('auth.login'))
            
            # Extract project_id from multiple sources
            project_id = _extract_project_id(kwargs)
            
            if not has_permission(permission_key, project_id=project_id):
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'}), 403
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(*permission_keys):
    """
    Decorator to enforce that user has ANY of the specified permissions.
    Automatically extracts project_id from kwargs, args, form, JSON, or session for project-scoped checks.
    
    Args:
        *permission_keys: Variable number of permission keys
        
    Usage:
        @app.route('/reports')
        @require_any_permission('reports.training.view', 'reports.veterinary.view')
        def view_reports():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
                return redirect(url_for('auth.login'))
            
            # Extract project_id from multiple sources
            project_id = _extract_project_id(kwargs)
            
            if not has_any_permission(*permission_keys, project_id=project_id):
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'}), 403
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_all_permissions(*permission_keys):
    """
    Decorator to enforce that user has ALL of the specified permissions.
    Automatically extracts project_id from kwargs, args, form, JSON, or session for project-scoped checks.
    
    Args:
        *permission_keys: Variable number of permission keys
        
    Usage:
        @app.route('/advanced-settings')
        @require_all_permissions('admin.settings', 'admin.permissions.edit')
        def advanced_settings():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
                return redirect(url_for('auth.login'))
            
            # Extract project_id from multiple sources
            project_id = _extract_project_id(kwargs)
            
            if not has_all_permissions(*permission_keys, project_id=project_id):
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'}), 403
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to admin users.
    Uses V2 PermissionService for role-based access control.
    
    The decorator allows access if:
    1. User is GENERAL_ADMIN in admin mode (legacy mode switching preserved)
    2. User has general_admin or super_admin role in V2
    3. User has any admin.* permission (delegated admin access)
    
    Usage:
        @app.route('/admin/settings')
        @admin_required
        def admin_settings():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not current_user.is_authenticated:
            if is_ajax:
                return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        # Preserve admin_mode handling for GENERAL_ADMIN users
        if _is_admin_mode(current_user):
            return f(*args, **kwargs)
        
        # Use V2 PermissionService for admin check
        from k9.services.permission_service import PermissionService
        
        # Check if user is admin
        if PermissionService.is_admin(current_user.id):
            return f(*args, **kwargs)
        
        # Check for any admin.* permission (delegated admin access)
        if PermissionService.has_permission(current_user.id, 'admin.*'):
            return f(*args, **kwargs)
        
        # Access denied
        if is_ajax:
            return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'}), 403
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    return decorated_function


def admin_or_pm_required(f):
    """
    Require GENERAL_ADMIN (in admin mode) or user with PM-level permissions.
    Uses V2 PermissionService for role-based access control.
    PM-level permissions include projects, dogs, employees, reports, schedules, etc.
    
    Usage:
        @app.route('/supervisor')
        @admin_or_pm_required
        def supervisor_page():
            ...
    """
    # PM-level permission patterns for wildcard checks
    PM_PERMISSION_PATTERNS = [
        'projects.*',
        'dogs.*',
        'employees.*',
        'reports.*',
        'schedules.*',
        'shifts.*',
        'attendance.*',
        'training.*',
        'veterinary.*',
        'breeding.*',
        'supervisor.*',
        'pm.*',
        'admin.*',
    ]
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        # GENERAL_ADMIN in general admin mode always has access
        if _is_admin_mode(current_user):
            return f(*args, **kwargs)
        
        # Use V2 PermissionService for PM-level check
        from k9.services.permission_service import PermissionService
        
        # Check if user is admin
        if PermissionService.is_admin(current_user.id):
            return f(*args, **kwargs)
        
        # Check if user has project_manager role
        if PermissionService.has_role(current_user.id, 'project_manager'):
            return f(*args, **kwargs)
        
        # Check if user has any PM-level permission via V2
        if PermissionService.has_any_permission(current_user.id, PM_PERMISSION_PATTERNS):
            return f(*args, **kwargs)
        
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
        
    return decorated_function


def require_admin_permission(permission_key='admin.permissions.view'):
    """
    Decorator that allows access to GENERAL_ADMIN in admin mode OR users with specific admin permission.
    This enables delegating admin features to PROJECT_MANAGER users via granular permissions.
    
    Args:
        permission_key: Admin permission key (e.g., "admin.permissions.view", "admin.settings")
    
    Usage:
        @require_admin_permission('admin.permissions.view')
        def comprehensive_permissions():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'}), 401
                flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('auth.login'))
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Check if user has the specific admin permission
            if has_permission(permission_key):
                return f(*args, **kwargs)
            
            # Access denied
            error_msg = 'ليس لديك صلاحية للوصول إلى هذه الصفحة'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 403
            flash(error_msg, 'error')
            return redirect(url_for('main.dashboard'))
            
        return decorated_function
    return decorator


def grant_permission(user_id, permission_key, granted_by_user_id=None, _batch_session=None, _commit=True):
    """
    Grant a permission to a user using V2 PermissionOverride.
    
    Args:
        user_id: User to grant permission to
        permission_key: Permission key to grant
        granted_by_user_id: User granting the permission (for audit)
        _batch_session: Internal - Ignored in V2 (kept for backward compatibility)
        _commit: Internal - Ignored in V2 (always commits)
        
    Returns:
        True if successful, False otherwise
    """
    from k9.services.permission_service import PermissionService
    from k9.models.models import User
    from datetime import datetime
    
    # Use V2 PermissionService to grant permission via override
    try:
        PermissionService.grant_permission(
            user_id=user_id,
            permission_key=permission_key,
            granted_by_id=granted_by_user_id
        )
        success = True
    except Exception:
        success = False
    
    if success:
        # Update the user's permissions_updated_at timestamp to invalidate their session cache
        from app import db
        target_user = User.query.get(user_id)
        if target_user:
            target_user.permissions_updated_at = datetime.utcnow()
            db.session.commit()
        
        # Reload permissions if this user is currently logged in
        if current_user.is_authenticated and str(current_user.id) == str(user_id):
            load_user_permissions(user_id)
    
    return success


def revoke_permission(user_id, permission_key, revoked_by_user_id=None, _batch_session=None, _commit=True):
    """
    Revoke a permission from a user using V2 PermissionOverride.
    
    Args:
        user_id: User to revoke permission from
        permission_key: Permission key to revoke
        revoked_by_user_id: User revoking the permission (for audit)
        _batch_session: Internal - Ignored in V2 (kept for backward compatibility)
        _commit: Internal - Ignored in V2 (always commits)
        
    Returns:
        True if successful, False otherwise
    """
    from k9.services.permission_service import PermissionService
    from k9.models.models import User
    from datetime import datetime
    
    # Use V2 PermissionService to revoke permission via override
    try:
        PermissionService.revoke_permission(
            user_id=user_id,
            permission_key=permission_key,
            revoked_by_id=revoked_by_user_id
        )
        success = True
    except Exception:
        success = False
    
    if success:
        # Update the user's permissions_updated_at timestamp to invalidate their session cache
        from app import db
        target_user = User.query.get(user_id)
        if target_user:
            target_user.permissions_updated_at = datetime.utcnow()
            db.session.commit()
        
        # Reload permissions if this user is currently logged in
        if current_user.is_authenticated and str(current_user.id) == str(user_id):
            load_user_permissions(user_id)
    
    return success


def batch_grant_permissions(user_id, permission_keys, granted_by_user_id=None):
    """
    Grant multiple permissions to a user using V2 PermissionService.
    
    Args:
        user_id: User to grant permissions to
        permission_keys: List of permission keys to grant
        granted_by_user_id: User granting the permissions (for audit)
        
    Returns:
        Number of permissions successfully granted
    """
    from k9.services.permission_service import PermissionService
    from k9.models.models import User
    from datetime import datetime
    from app import db
    
    if not permission_keys:
        return 0
    
    count = 0
    
    # Grant each permission via V2 PermissionService
    for permission_key in permission_keys:
        try:
            PermissionService.grant_permission(
                user_id=user_id,
                permission_key=permission_key,
                granted_by_id=granted_by_user_id
            )
            count += 1
        except Exception:
            continue
    
    if count > 0:
        # Update timestamp for all changes at once
        target_user = User.query.get(user_id)
        if target_user:
            target_user.permissions_updated_at = datetime.utcnow()
            db.session.commit()
        
        # Reload permissions if this user is currently logged in
        if current_user.is_authenticated and str(current_user.id) == str(user_id):
            load_user_permissions(user_id)
    
    return count


def batch_revoke_permissions(user_id, permission_keys, revoked_by_user_id=None):
    """
    Revoke multiple permissions from a user using V2 PermissionService.
    
    Args:
        user_id: User to revoke permissions from
        permission_keys: List of permission keys to revoke
        revoked_by_user_id: User revoking the permissions (for audit)
        
    Returns:
        Number of permissions successfully revoked
    """
    from k9.services.permission_service import PermissionService
    from k9.models.models import User
    from datetime import datetime
    from app import db
    
    if not permission_keys:
        return 0
    
    count = 0
    
    # Revoke each permission via V2 PermissionService
    for permission_key in permission_keys:
        try:
            PermissionService.revoke_permission(
                user_id=user_id,
                permission_key=permission_key,
                revoked_by_id=revoked_by_user_id
            )
            count += 1
        except Exception:
            continue
    
    if count > 0:
        # Update timestamp for all changes at once
        target_user = User.query.get(user_id)
        if target_user:
            target_user.permissions_updated_at = datetime.utcnow()
            db.session.commit()
        
        # Reload permissions if this user is currently logged in
        if current_user.is_authenticated and str(current_user.id) == str(user_id):
            load_user_permissions(user_id)
    
    return count


def get_all_permissions_grouped():
    """
    Get all permissions in the system, grouped by category.
    
    Returns:
        Dict of {category: [permissions]}
    """
    from k9.models.permissions_new import Permission
    
    all_perms = Permission.query.order_by(Permission.category, Permission.name).all()
    
    grouped = {}
    for perm in all_perms:
        if perm.category not in grouped:
            grouped[perm.category] = []
        grouped[perm.category].append(perm)
    
    return grouped


def get_user_permission_keys(user_id):
    """
    Get all permission keys for a specific user (from database, not session).
    
    Args:
        user_id: The user's ID
        
    Returns:
        Set of permission keys
    """
    from k9.models.permissions_new import UserPermission
    
    user_perms = UserPermission.query.filter_by(user_id=user_id).all()
    return {up.permission.key for up in user_perms if up.permission}


def _is_pm_mode(user):
    """Helper to check if user should be treated as PM (regular PM or GENERAL_ADMIN in PM mode)"""
    if not user or not hasattr(user, 'role'):
        return False
    from k9.models.models import UserRole
    if user.role == UserRole.PROJECT_MANAGER:
        return True
    if user.role == UserRole.GENERAL_ADMIN:
        admin_mode = session.get('admin_mode', 'general_admin')
        return admin_mode == 'project_manager'
    return False


def get_sections_for_user(user=None):
    """
    Get list of sections/categories the user has access to based on their V2 permissions.
    
    Args:
        user: Optional user object (defaults to current_user)
        
    Returns:
        List of section names the user has access to
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return []
    
    if _is_admin_mode(user):
        return ['admin', 'dogs', 'employees', 'projects', 'training', 'veterinary', 
                'breeding', 'reports', 'schedules', 'shifts', 'attendance', 'handlers',
                'supervisor', 'caretaker', 'security', 'audit', 'notifications', 'dashboard',
                'handler_daily', 'pm', 'users']
    
    # Use V2 PermissionService to get user permissions
    from k9.services.permission_service import PermissionService
    user_perms = PermissionService.get_user_permissions(user.id)
    
    sections = set()
    for perm in user_perms:
        if '.' in perm:
            section = perm.split('.')[0]
            sections.add(section)
        elif perm.endswith('.*'):
            # Handle wildcard patterns like "dogs.*"
            section = perm[:-2]
            sections.add(section)
    
    return list(sections)


def get_project_managers():
    """Get all PROJECT_MANAGER users"""
    from k9.models.models import User, UserRole
    return User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()


def get_all_projects():
    """Get all projects"""
    from k9.models.models import Project
    return Project.query.order_by(Project.name).all()


def get_users_by_project(project_id):
    """Get users assigned to a specific project via their employee records"""
    from k9.models.models import User, ProjectAssignment
    
    # ProjectAssignment links employees (not users) to projects
    # User.employee_id links users to employees
    # So we need to: get employee_ids from assignments -> find users with those employee_ids
    
    assignments = ProjectAssignment.query.filter_by(
        project_id=project_id, 
        is_active=True
    ).filter(ProjectAssignment.employee_id.isnot(None)).all()
    
    employee_ids = [a.employee_id for a in assignments if a.employee_id]
    
    if not employee_ids:
        return []
    
    # Find users linked to these employees
    return User.query.filter(
        User.employee_id.in_(employee_ids),
        User.active == True
    ).all()


def get_user_permissions_by_project(user_id, project_id=None):
    """Get permissions for a user, optionally filtered by project"""
    return get_user_permission_keys(user_id)
