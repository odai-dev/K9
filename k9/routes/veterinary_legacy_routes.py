"""
Legacy veterinary report routes for backward compatibility
Redirects old veterinary daily/weekly routes to the new unified route
"""
from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from k9.utils.permission_utils import has_permission

bp = Blueprint('veterinary_legacy_routes', __name__)


@bp.route('/daily')
@login_required
def veterinary_daily():
    """Redirect legacy daily veterinary reports to unified veterinary reports with daily range"""
    if not has_permission(current_user, "reports.veterinary.legacy.access"):
        return redirect("/unauthorized")
    
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to daily
    params['range_type'] = 'daily'
    
    flash('تم الانتقال إلى التقرير البيطري الموحد', 'info')
    return redirect(url_for('veterinary_reports_ui.veterinary', **params))


@bp.route('/weekly')
@login_required
def veterinary_weekly():
    """Redirect legacy weekly veterinary reports to unified veterinary reports with weekly range"""
    if not has_permission(current_user, "reports.veterinary.legacy.access"):
        return redirect("/unauthorized")
    
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to weekly
    params['range_type'] = 'weekly'
    
    flash('تم الانتقال إلى التقرير البيطري الموحد', 'info')
    return redirect(url_for('veterinary_reports_ui.veterinary', **params))