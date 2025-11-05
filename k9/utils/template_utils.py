"""
Template utilities for handling PM vs Admin views
"""
from flask import session
from flask_login import current_user
from k9.models.models import UserRole


def get_base_template():
    """
    Automatically determine which base template to use based on user role and mode.
    
    Returns:
        str: 'pm/base_pm.html' for PROJECT_MANAGERs or GENERAL_ADMINs in PM mode,
             'base.html' for GENERAL_ADMINs in admin mode or other roles
    """
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return 'base.html'
    
    # PROJECT_MANAGER users always get PM template
    if current_user.role == UserRole.PROJECT_MANAGER:
        return 'pm/base_pm.html'
    
    # GENERAL_ADMIN users check their mode
    if current_user.role == UserRole.GENERAL_ADMIN:
        admin_mode = session.get('admin_mode', 'general_admin')
        if admin_mode == 'project_manager':
            return 'pm/base_pm.html'
        else:
            return 'base.html'
    
    # All other roles use default template
    return 'base.html'


def is_pm_view():
    """
    Check if the current view should be rendered as PM view.
    
    Returns:
        bool: True if user is PM or GENERAL_ADMIN in PM mode
    """
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return False
    
    if current_user.role == UserRole.PROJECT_MANAGER:
        return True
    
    if current_user.role == UserRole.GENERAL_ADMIN:
        admin_mode = session.get('admin_mode', 'general_admin')
        return admin_mode == 'project_manager'
    
    return False
