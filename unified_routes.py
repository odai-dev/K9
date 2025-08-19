"""
Unified Attendance Matrix UI Routes
Web interface for unified attendance matrix reports
"""

from flask import Blueprint, render_template, request
from flask_login import login_required
from functools import wraps
from flask import abort
from flask_login import current_user
from models import UserRole

def require_perm(permission_key):
    """Simple permission decorator for unified matrix"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            # For now, allow all authenticated users (will implement proper RBAC later)
            if current_user.role not in [UserRole.GENERAL_ADMIN, UserRole.PROJECT_MANAGER]:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Create blueprint
bp = Blueprint('reports_attendance_unified_ui', __name__)


@bp.route('/unified')
@login_required
@require_perm('reports:attendance:unified:view')
def unified_matrix():
    """Display the new clean unified matrix page"""
    return render_template('reports/attendance/unified_matrix_new.html')

@bp.route('/unified_old')
@login_required
@require_perm('reports:attendance:unified:view')
def unified_matrix_old():
    """
    Display unified attendance matrix page
    GET /reports/attendance/unified
    """
    # Get optional query parameters for prefilling filters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    employee_ids = request.args.getlist('employee_ids')
    project_ids = request.args.getlist('project_ids')
    include_dogs = request.args.get('include_dogs', 'false').lower() == 'true'
    
    prefill_data = {
        'date_from': date_from,
        'date_to': date_to,
        'employee_ids': employee_ids,
        'project_ids': project_ids,
        'include_dogs': include_dogs
    }
    
    return render_template(
        'reports/attendance/unified_matrix.html',
        prefill_data=prefill_data
    )