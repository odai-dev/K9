"""
Decorators for K9 System
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from k9.models.models import UserRole


def admin_or_pm_required(f):
    """Require GENERAL_ADMIN or PROJECT_MANAGER role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in [UserRole.GENERAL_ADMIN, UserRole.PROJECT_MANAGER]:
            flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require GENERAL_ADMIN role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != UserRole.GENERAL_ADMIN:
            flash('هذه الصفحة متاحة لمدير النظام فقط', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def handler_required(f):
    """Require HANDLER role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != UserRole.HANDLER:
            flash('هذه الصفحة متاحة للسائسين فقط', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def supervisor_required(f):
    """Require supervisor-level privileges (GENERAL_ADMIN, PROJECT_MANAGER, SUPERVISOR, or PROJECT_ADMIN)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('auth.login'))
        
        # Allow GENERAL_ADMIN, PROJECT_MANAGER, and legacy SUPERVISOR/PROJECT_ADMIN roles
        allowed_roles = [UserRole.GENERAL_ADMIN, UserRole.PROJECT_MANAGER]
        
        # Check for SUPERVISOR and PROJECT_ADMIN if they exist
        if hasattr(UserRole, 'SUPERVISOR'):
            allowed_roles.append(UserRole.SUPERVISOR)
        if hasattr(UserRole, 'PROJECT_ADMIN'):
            allowed_roles.append(UserRole.PROJECT_ADMIN)
        
        if current_user.role not in allowed_roles:
            flash('هذه الصفحة متاحة للمشرفين فقط', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function
