"""
Legacy veterinary report routes for backward compatibility
Redirects old veterinary daily/weekly routes to the new unified route
"""
from flask import Blueprint, request, redirect, url_for, flash

bp = Blueprint('veterinary_legacy_routes', __name__)


@bp.route('/daily')
def veterinary_daily():
    """Redirect legacy daily veterinary reports to unified veterinary reports with daily range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to daily
    params['range_type'] = 'daily'
    
    flash('تم الانتقال إلى التقرير البيطري الموحد', 'info')
    return redirect(url_for('veterinary_reports_ui.veterinary', **params))


@bp.route('/weekly')
def veterinary_weekly():
    """Redirect legacy weekly veterinary reports to unified veterinary reports with weekly range"""
    # Preserve all original query parameters
    params = dict(request.args)
    # Set range type to weekly
    params['range_type'] = 'weekly'
    
    flash('تم الانتقال إلى التقرير البيطري الموحد', 'info')
    return redirect(url_for('veterinary_reports_ui.veterinary', **params))