"""
Caretaker Daily Report UI Routes
Handles Arabic/RTL caretaker daily reports under Reports → Breeding
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from k9.utils.permission_utils import has_permission
from k9.utils.utils import get_user_projects

# Create blueprint
bp = Blueprint('caretaker_daily_reports_ui', __name__)


@bp.route('/')
@login_required
def caretaker_daily():
    """Unified Arabic/RTL caretaker daily reports page with range selector"""
    
    # Check unified permission
    if not has_permission(current_user, "reports.breeding.caretaker_daily.view"):
        flash('ليس لديك صلاحية لعرض تقارير الرعاية اليومية', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get accessible projects for current user
    projects = get_user_projects(current_user)
    
    # Get any URL parameters for state preservation
    initial_params = {
        'project_id': request.args.get('project_id', ''),
        'range_type': request.args.get('range_type', 'daily'),
        'date': request.args.get('date', ''),
        'week_start': request.args.get('week_start', ''),
        'year_month': request.args.get('year_month', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'dog_id': request.args.get('dog_id', '')
    }
    
    return render_template('reports/breeding/caretaker_daily.html', 
                         accessible_projects=projects,
                         initial_params=initial_params,
                         title='تقرير الرعاية اليومية')