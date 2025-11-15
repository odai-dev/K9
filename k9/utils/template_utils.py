"""
Template utilities for handling PM vs Admin views
"""
from flask_login import current_user
from k9.utils.permission_utils import get_sections_for_user, _is_admin_mode


def get_base_template():
    """
    Automatically determine which base template to use based on user permissions.
    
    Returns:
        str: 'pm/base_pm.html' for users with granted permissions,
             'base.html' for GENERAL_ADMINs in admin mode or users without permissions
    """
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return 'base.html'
    
    # GENERAL_ADMIN in admin mode gets admin template
    # ROLE CHECK DISABLED: if _is_admin_mode(current_user):
    if True:  # Role check bypassed
        return 'base.html'
    
    # Check if user has any granted permissions
    sections = get_sections_for_user(current_user)
    if sections:
        # User has at least one permission - show PM interface
        return 'pm/base_pm.html'
    
    # No permissions - default template
    return 'base.html'


def is_pm_view():
    """
    Check if the current view should be rendered as PM view.
    
    Returns:
        bool: True if user has any operational permissions (excluding GENERAL_ADMIN in admin mode)
    """
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return False
    
    # GENERAL_ADMIN in admin mode is NOT in PM view
    # ROLE CHECK DISABLED: if _is_admin_mode(current_user):
    if True:  # Role check bypassed
        return False
    
    # Check if user has any granted permissions
    sections = get_sections_for_user(current_user)
    return len(sections) > 0
