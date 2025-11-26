"""
Caretaker Daily Report UI Routes
Handles Arabic/RTL caretaker daily reports under Reports → Breeding
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from k9.utils.permissions_new import has_permission
from k9.utils.pm_scoping import get_scoped_projects
from k9.utils.template_utils import get_base_template

# Create blueprint
bp = Blueprint('caretaker_daily_reports_ui', __name__)


@bp.route('/')
@login_required
def caretaker_daily():
    """Unified Arabic/RTL caretaker daily reports page with range selector"""
    
    # Check unified permission
    if not has_permission("reports.general.view"):
        return redirect("/unauthorized")
    
    # Get accessible projects for current user using PM scoping
    projects = get_scoped_projects()
    
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
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('reports/breeding/caretaker_daily.html', 
                         accessible_projects=projects,
                         initial_params=initial_params,
                         title='تقرير الرعاية اليومية',
                         base_template=base_template)