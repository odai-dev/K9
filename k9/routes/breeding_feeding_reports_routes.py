"""
Breeding Feeding Reports UI Routes
Handles Arabic/RTL feeding reports under Reports → Breeding
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from k9.utils.permission_decorators import require_sub_permission
from k9.models.models import PermissionType, Project
from k9.utils.utils import get_user_projects

# Create blueprint
bp = Blueprint('breeding_feeding_reports_ui', __name__)


@bp.route('/daily')
@login_required
@require_sub_permission("Reports", "Feeding Daily", PermissionType.VIEW)
def feeding_daily():
    """Arabic/RTL daily feeding reports page"""
    projects = get_user_projects(current_user)
    
    return render_template('reports/breeding/feeding_daily.html', 
                         accessible_projects=projects,
                         title='تقرير التغذية اليومي')


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Feeding Weekly", PermissionType.VIEW)
def feeding_weekly():
    """Arabic/RTL weekly feeding reports page"""
    projects = get_user_projects(current_user)
    
    return render_template('reports/breeding/feeding_weekly.html',
                         accessible_projects=projects,
                         title='تقرير التغذية الأسبوعي')