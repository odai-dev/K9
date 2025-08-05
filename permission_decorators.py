from functools import wraps
from flask import abort, request, flash, redirect, url_for
from flask_login import current_user
from utils import get_project_manager_permissions, check_project_access
from models import UserRole

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