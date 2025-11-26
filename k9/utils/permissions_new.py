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
    Load all permission keys for a user into the session.
    Called during login to cache permissions for fast checking.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Set of permission keys (strings)
    """
    from k9.models.permissions_new import UserPermission, Permission
    
    # Query all permissions granted to this user
    user_perms = UserPermission.query.filter_by(user_id=user_id).all()
    
    # Extract permission keys
    permission_keys = set()
    for up in user_perms:
        if up.permission:
            permission_keys.add(up.permission.key)
    
    # Store in session for fast access
    session['user_permissions'] = list(permission_keys)
    session.modified = True
    
    return permission_keys


def get_user_permissions():
    """
    Get current user's permissions from session.
    
    Returns:
        Set of permission keys (strings)
    """
    if not current_user.is_authenticated:
        return set()
    
    # Load from session
    perms = session.get('user_permissions', [])
    return set(perms)


def has_permission(permission_key, user=None):
    """
    Check if current user has a specific permission.
    
    Args:
        permission_key: The permission key to check (e.g., 'dogs.view')
        user: Optional user object (defaults to current_user)
        
    Returns:
        True if user has the permission, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # GENERAL_ADMIN in admin mode has ALL permissions
    if _is_admin_mode(user):
        return True
    
    user_perms = get_user_permissions()
    return permission_key in user_perms


def has_any_permission(*permission_keys, user=None):
    """
    Check if current user has ANY of the specified permissions.
    
    Args:
        *permission_keys: Variable number of permission keys
        user: Optional user object (defaults to current_user)
        
    Returns:
        True if user has at least one permission, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # GENERAL_ADMIN in admin mode has ALL permissions
    if _is_admin_mode(user):
        return True
    
    user_perms = get_user_permissions()
    return any(key in user_perms for key in permission_keys)


def has_all_permissions(*permission_keys, user=None):
    """
    Check if current user has ALL of the specified permissions.
    
    Args:
        *permission_keys: Variable number of permission keys
        user: Optional user object (defaults to current_user)
        
    Returns:
        True if user has all permissions, False otherwise
    """
    if user is None:
        user = current_user
    
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # GENERAL_ADMIN in admin mode has ALL permissions
    if _is_admin_mode(user):
        return True
    
    user_perms = get_user_permissions()
    return all(key in user_perms for key in permission_keys)


def require_permission(permission_key):
    """
    Decorator to enforce permission on a route.
    If user doesn't have the permission, redirect to dashboard with error.
    Handles both regular requests and AJAX/API requests.
    
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
            
            if not has_permission(permission_key):
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
            
            if not has_any_permission(*permission_keys):
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
            
            if not has_all_permissions(*permission_keys):
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذه الصفحة'}), 403
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to GENERAL_ADMIN in admin mode only.
    Also allows access if user has admin.permissions.view or admin.permissions.edit.
    
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
        
        # GENERAL_ADMIN in admin mode always has access
        if _is_admin_mode(current_user):
            return f(*args, **kwargs)
        
        # Check if user has admin permissions
        if has_permission('admin.permissions.view') or has_permission('admin.permissions.edit'):
            return f(*args, **kwargs)
        
        # Access denied
        if is_ajax:
            return jsonify({'success': False, 'error': 'هذه الصفحة مخصصة للمدير العام فقط'}), 403
        flash('هذه الصفحة مخصصة للمدير العام فقط', 'error')
        return redirect(url_for('main.dashboard'))
    
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


def grant_permission(user_id, permission_key, granted_by_user_id=None):
    """
    Grant a permission to a user.
    
    Args:
        user_id: User to grant permission to
        permission_key: Permission key to grant
        granted_by_user_id: User granting the permission (for audit)
        
    Returns:
        True if successful, False otherwise
    """
    from app import db
    from k9.models.permissions_new import Permission, UserPermission, PermissionChangeLog
    
    # Find the permission
    permission = Permission.query.filter_by(key=permission_key).first()
    if not permission:
        return False
    
    # Check if already granted
    existing = UserPermission.query.filter_by(
        user_id=user_id,
        permission_id=permission.id
    ).first()
    
    if existing:
        return True  # Already granted
    
    # Create grant
    user_perm = UserPermission(
        user_id=user_id,
        permission_id=permission.id,
        granted_by_user_id=granted_by_user_id
    )
    db.session.add(user_perm)
    
    # Log the change
    log = PermissionChangeLog(
        user_id=user_id,
        permission_id=permission.id,
        action='granted',
        changed_by_user_id=granted_by_user_id,
        ip_address=request.remote_addr if has_request_context() else None
    )
    db.session.add(log)
    
    db.session.commit()
    
    # Reload permissions if this user is currently logged in
    if current_user.is_authenticated and str(current_user.id) == str(user_id):
        load_user_permissions(user_id)
    
    return True


def revoke_permission(user_id, permission_key, revoked_by_user_id=None):
    """
    Revoke a permission from a user.
    
    Args:
        user_id: User to revoke permission from
        permission_key: Permission key to revoke
        revoked_by_user_id: User revoking the permission (for audit)
        
    Returns:
        True if successful, False otherwise
    """
    from app import db
    from k9.models.permissions_new import Permission, UserPermission, PermissionChangeLog
    
    # Find the permission
    permission = Permission.query.filter_by(key=permission_key).first()
    if not permission:
        return False
    
    # Find the grant
    user_perm = UserPermission.query.filter_by(
        user_id=user_id,
        permission_id=permission.id
    ).first()
    
    if not user_perm:
        return True  # Already revoked
    
    # Remove grant
    db.session.delete(user_perm)
    
    # Log the change
    log = PermissionChangeLog(
        user_id=user_id,
        permission_id=permission.id,
        action='revoked',
        changed_by_user_id=revoked_by_user_id,
        ip_address=request.remote_addr if has_request_context() else None
    )
    db.session.add(log)
    
    db.session.commit()
    
    # Reload permissions if this user is currently logged in
    if current_user.is_authenticated and str(current_user.id) == str(user_id):
        load_user_permissions(user_id)
    
    return True


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
