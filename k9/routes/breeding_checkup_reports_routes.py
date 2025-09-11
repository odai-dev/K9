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
    """Redirect legacy daily checkup reports to unified checkup reports with daily range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to daily
    params['range_type'] = 'daily'
    
    flash('تم الانتقال إلى تقرير الفحص الظاهري الموحد', 'info')
    return redirect(url_for('unified_checkup_reports_ui.checkup', **params))


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Checkup Weekly", PermissionType.VIEW)
def checkup_weekly():
    """Redirect legacy weekly checkup reports to unified checkup reports with weekly range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to weekly
    params['range_type'] = 'weekly'
    
    flash('تم الانتقال إلى تقرير الفحص الظاهري الموحد', 'info')
    return redirect(url_for('unified_checkup_reports_ui.checkup', **params))