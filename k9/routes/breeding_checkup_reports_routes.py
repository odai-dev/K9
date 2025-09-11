"""
Breeding Checkup Reports UI Routes
Handles Arabic/RTL checkup reports under Reports → Breeding
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from k9.utils.permission_decorators import require_sub_permission
from k9.models.models import PermissionType, Project
from k9.utils.utils import get_user_projects

# Create blueprint
bp = Blueprint('breeding_checkup_reports_ui', __name__)


@bp.route('/daily')
@login_required
@require_sub_permission("Reports", "Checkup Daily", PermissionType.VIEW)
def checkup_daily():
    """Arabic/RTL daily checkup reports page"""
    projects = get_user_projects(current_user)
    
    return render_template('reports/breeding/checkup_daily.html', 
                         accessible_projects=projects,
                         title='تقرير الفحص الظاهري اليومي')


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Checkup Weekly", PermissionType.VIEW)
def checkup_weekly():
    """Arabic/RTL weekly checkup reports page"""
    projects = get_user_projects(current_user)
    
    return render_template('reports/breeding/checkup_weekly.html',
                         accessible_projects=projects,
                         title='تقرير الفحص الظاهري الأسبوعي')