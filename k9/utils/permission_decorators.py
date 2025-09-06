from functools import wraps
from flask import abort, request, flash, redirect, url_for
from flask_login import current_user
from k9.utils.utils import get_project_manager_permissions, check_project_access
from k9.models.models import UserRole, PermissionType
from k9.utils.permission_utils import has_permission

def require_permission(permission_type, project_id_param='project_id'):
    """
    Decorator to enforce granular permissions for PROJECT_MANAGER users.
    
    Args:
        permission_type: String key for the permission to check
        project_id_param: Name of the parameter/argument containing project_id
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # GENERAL_ADMIN always has access
            if current_user.role == UserRole.GENERAL_ADMIN:
                return f(*args, **kwargs)
            
            # Get project_id from various sources
            project_id = None
            
            # Try to get from URL parameters
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            if not project_id:
                flash('مشروع غير محدد', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Check if user has access to this project
            if not check_project_access(current_user, project_id):
                flash('ليس لديك صلاحية للوصول لهذا المشروع', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Check specific permission
            permissions = get_project_manager_permissions(current_user, project_id)
            if not permissions.get(permission_type, False):
                flash('ليس لديك صلاحية لتنفيذ هذا الإجراء', 'error')
                return redirect(url_for('main.project_detail', project_id=project_id))
            
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
            
            # GENERAL_ADMIN always has access
            if current_user.role == UserRole.GENERAL_ADMIN:
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

def admin_required(f):
    """
    Decorator to restrict access to GENERAL_ADMIN only.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if current_user.role != UserRole.GENERAL_ADMIN:
            flash('هذه الصفحة مخصصة للمدير العام فقط', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_sub_permission(section, subsection, permission_type, project_id_param='project_id'):
    """
    Enhanced decorator for ultra-granular permission control
    
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
            
            # GENERAL_ADMIN always has access
            if current_user.role == UserRole.GENERAL_ADMIN:
                return f(*args, **kwargs)
            
            # Get project_id from various sources
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            # Check permission using the enhanced system
            if not has_permission(current_user, section, subsection, permission_type, project_id):
                flash(f'ليس لديك صلاحية: {subsection} في قسم {section}', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_sub_permission(section, subsection, permission_types, project_id_param='project_id'):
    """
    Decorator that requires ANY of the specified permissions (OR logic)
    
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
            
            # GENERAL_ADMIN always has access
            if current_user.role == UserRole.GENERAL_ADMIN:
                return f(*args, **kwargs)
            
            # Get project_id
            project_id = None
            if project_id_param in kwargs:
                project_id = kwargs[project_id_param]
            elif project_id_param in request.args:
                project_id = request.args.get(project_id_param)
            elif project_id_param in request.form:
                project_id = request.form.get(project_id_param)
            
            # Check if user has ANY of the required permissions
            has_any_permission = False
            for perm_type in permission_types:
                if has_permission(current_user, section, subsection, perm_type, project_id):
                    has_any_permission = True
                    break
            
            if not has_any_permission:
                flash(f'ليس لديك أي صلاحية مطلوبة: {subsection} في قسم {section}', 'error')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator