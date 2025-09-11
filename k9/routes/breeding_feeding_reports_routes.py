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
    """Redirect legacy daily feeding reports to unified feeding reports with daily range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to daily
    params['range_type'] = 'daily'
    
    flash('تم الانتقال إلى تقرير التغذية الموحد', 'info')
    return redirect(url_for('unified_feeding_reports_ui.feeding', **params))


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Feeding Weekly", PermissionType.VIEW)
def feeding_weekly():
    """Redirect legacy weekly feeding reports to unified feeding reports with weekly range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to weekly
    params['range_type'] = 'weekly'
    
    flash('تم الانتقال إلى تقرير التغذية الموحد', 'info')
    return redirect(url_for('unified_feeding_reports_ui.feeding', **params))