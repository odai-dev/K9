"""
Veterinary reports UI routes - unified veterinary reports with range selector
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from k9.utils.permission_utils import has_permission
from k9.utils.utils import get_user_projects, get_user_accessible_dogs

bp = Blueprint('veterinary_reports_ui', __name__)


@bp.route('/')
@login_required
def veterinary():
    """Unified Arabic/RTL veterinary reports page with range selector"""
    
    # Check unified permission
    if not has_permission(current_user, "reports.veterinary.view"):
        flash('ليس لديك صلاحية لعرض التقارير البيطرية', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get accessible projects and dogs for current user
    projects = get_user_projects(current_user)
    dogs = get_user_accessible_dogs(current_user)
    
    # Get any URL parameters for state preservation
    initial_params = {
        'project_id': request.args.get('project_id', ''),
        'range_type': request.args.get('range_type', 'daily'),
        'date': request.args.get('date', ''),
        'week_start': request.args.get('week_start', ''),
        'year_month': request.args.get('year_month', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'dog_id': request.args.get('dog_id', ''),
        'show_kpis': request.args.get('show_kpis', '1')
    }
    
    return render_template('reports/breeding/veterinary.html', 
                         accessible_projects=projects,
                         accessible_dogs=dogs,
                         initial_params=initial_params,
                         title='التقرير البيطري (موحّد)')