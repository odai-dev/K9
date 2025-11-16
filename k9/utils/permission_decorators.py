from functools import wraps
from flask import abort, request, flash, redirect, url_for, session, jsonify
from flask_login import current_user
from k9.utils.utils import check_project_access
from k9.models.models import UserRole, PermissionType
from k9.utils.permission_utils import (
    has_permission,
    has_any_permission,
    _is_admin_mode,
    get_sections_for_user
)


def require_permission(permission_key, project_id_param='project_id'):
    """
    Decorator to enforce granular permissions using the new permission system.
    
    Args:
        permission_key: Permission key in canonical format (e.g., "dogs.view", "reports.breeding.feeding.export")
        project_id_param: Name of the parameter/argument containing project_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Get project_id from various sources
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            # CRITICAL: Validate project access BEFORE checking permissions
            # This prevents users from accessing projects they're not assigned to
            if project_id and not check_project_access(current_user, project_id):
                flash('ليس لديك صلاحية للوصول لهذا المشروع', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Check specific permission using new system
            if not has_permission(current_user, permission_key, project_id=project_id):
                flash('ليس لديك صلاحية لتنفيذ هذا الإجراء', 'error')
                if project_id:
                    return redirect(url_for('main.project_detail', project_id=project_id))
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_project_access(project_id_param='project_id'):
    """
    Decorator to ensure user has access to a specific project.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Get project_id
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            if not project_id:
                flash('مشروع غير محدد', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Check project access
            if not check_project_access(current_user, project_id):
                flash('ليس لديك صلاحية للوصول لهذا المشروع', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_or_pm_required(f):
    """
    Require GENERAL_ADMIN (in admin mode) or user with any PM-level permissions.
    This checks permissions rather than just roles.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        # GENERAL_ADMIN in general admin mode always has access
        if _is_admin_mode(current_user):
            return f(*args, **kwargs)
        
        # Check if user has ANY permissions (indicating PM-level access)
        sections = get_sections_for_user(current_user)
        if sections:
            return f(*args, **kwargs)
        
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('main.index'))
        
    return decorated_function


def admin_required(f):
    """
    Decorator to restrict access to GENERAL_ADMIN in general admin mode only.
    GENERAL_ADMIN users in PM mode will be rejected.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if this is an AJAX/JSON request
        is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not current_user.is_authenticated:
            if is_ajax:
                return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'}), 401
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != UserRole.GENERAL_ADMIN:
            if is_ajax:
                return jsonify({'success': False, 'error': 'هذه الصفحة مخصصة للمدير العام فقط'}), 403
            flash('هذه الصفحة مخصصة للمدير العام فقط', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Check admin mode to prevent GENERAL_ADMIN in PM mode from accessing admin routes
        admin_mode = session.get('admin_mode', 'general_admin')
        if admin_mode != 'general_admin':
            if is_ajax:
                return jsonify({'success': False, 'error': 'هذه الصفحة متاحة في وضع المدير العام فقط'}), 403
            flash('هذه الصفحة متاحة في وضع المدير العام فقط', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin_permission(permission_key='admin.permissions.view'):
    """
    Decorator that allows access to GENERAL_ADMIN in admin mode OR users with specific admin permission.
    This enables delegating admin features to PROJECT_MANAGER users via granular permissions.
    
    Args:
        permission_key: Admin permission key (e.g., "admin.permissions.view", "admin.settings")
    
    Example:
        @require_admin_permission('admin.permissions.view')
        def permissions_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if this is an AJAX/JSON request
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
            if has_permission(current_user, permission_key):
                return f(*args, **kwargs)
            
            # Access denied
            error_msg = 'ليس لديك صلاحية للوصول إلى هذه الصفحة'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 403
            flash(error_msg, 'error')
            return redirect(url_for('main.dashboard'))
            
        return decorated_function
    return decorator


def require_role_or_permission(role, permission=None):
    """
    Decorator that allows access if user has specified role OR specified permission.
    This allows role-based users to keep access, while also allowing other users
    with equivalent permissions to access the same routes.
    
    Args:
        role: UserRole enum value (e.g., UserRole.HANDLER)
        permission: Optional permission key in canonical format (e.g., "handler.access")
                   If None, checks if user has ANY permissions (indicating PM/admin access)
    
    Examples:
        @require_role_or_permission(UserRole.HANDLER, "handler.access")
        def handler_route():
            ...
            
        @require_role_or_permission(UserRole.HANDLER)
        def handler_route_with_any_permissions():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if this is an AJAX/JSON request
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'}), 401
                flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
                return redirect(url_for('auth.login'))
            
            # GENERAL_ADMIN in admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Check if user has the required role
            if current_user.role == role:
                return f(*args, **kwargs)
            
            # Check if user has the required permission
            if permission:
                if has_permission(current_user, permission):
                    return f(*args, **kwargs)
            else:
                # If no specific permission specified, check if user has ANY permissions
                # This allows PMs/admins with granted permissions to access handler routes
                sections = get_sections_for_user(current_user)
                if sections:
                    return f(*args, **kwargs)
            
            # Access denied
            error_msg = f'هذه الصفحة متاحة لـ {role.value} فقط'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 403
            flash(error_msg, 'danger')
            return redirect(url_for('main.index'))
            
        return decorated_function
    return decorator


def handler_required(f):
    """
    Require HANDLER role or equivalent permissions.
    This allows both dedicated handlers and users with granted permissions to access.
    Implemented using require_role_or_permission for permission-based access control.
    """
    return require_role_or_permission(UserRole.HANDLER)(f)


def require_sub_permission(section, subsection, permission_type, project_id_param='project_id'):
    """
    Enhanced decorator for ultra-granular permission control.
    Uses the new has_permission() function from permission_utils.
    
    Args:
        section: Main section (e.g., "Dogs", "Employees")
        subsection: Specific subsection (e.g., "View Dog List", "Upload Medical Records")  
        permission_type: PermissionType enum value (VIEW, CREATE, EDIT, DELETE, etc.)
        project_id_param: Parameter name containing project_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Get project_id from various sources
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            # Check permission using the new permission system
            if not has_permission(current_user, section, subsection, permission_type):
                flash(f'ليس لديك صلاحية: {subsection} في قسم {section}', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_sub_permission(section, subsection, permission_types, project_id_param='project_id'):
    """
    Decorator that requires ANY of the specified permissions (OR logic).
    Uses the new has_any_permission() function from permission_utils.
    
    Args:
        section: Main section  
        subsection: Specific subsection
        permission_types: List of PermissionType enum values
        project_id_param: Parameter name containing project_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Build canonical permission keys from section/subsection/permission_types
            permission_keys = []
            for perm_type in permission_types:
                # Build canonical format
                if subsection:
                    # Format: "section.subsection.action"
                    key = f"{section}.{subsection}.{perm_type.value.lower()}"
                else:
                    # Format: "section.action"
                    key = f"{section}.{perm_type.value.lower()}"
                permission_keys.append(key)
            
            # Use new has_any_permission function
            if not has_any_permission(current_user, permission_keys):
                flash(f'ليس لديك أي صلاحية مطلوبة: {subsection} في قسم {section}', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(permission_keys):
    """
    Decorator that requires user to have ANY of the specified permissions.
    Uses the new has_any_permission() function from permission_utils.
    
    Args:
        permission_keys: List of permission keys in canonical format
                        (e.g., ["dogs.view", "dogs.edit", "employees.view"])
    
    Example:
        @require_any_permission(["reports.breeding.feeding.view", "reports.breeding.feeding.export"])
        def view_feeding_reports():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if this is an AJAX/JSON request
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if not current_user.is_authenticated:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'}), 401
                abort(401)
            
            # GENERAL_ADMIN in general admin mode always has access
            if _is_admin_mode(current_user):
                return f(*args, **kwargs)
            
            # Check if user has ANY of the required permissions using new function
            if has_any_permission(current_user, permission_keys):
                return f(*args, **kwargs)
            
            # Access denied
            error_msg = 'ليس لديك صلاحية لتنفيذ هذا الإجراء'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 403
            flash(error_msg, 'error')
            return redirect(url_for('main.dashboard'))
            
        return decorated_function
    return decorator
