"""
PM Daily Report UI Routes
HTML page routes for PM Daily Reports
"""

from flask import Blueprint, render_template, request, current_app
from flask_login import login_required, current_user
from datetime import date

from k9.utils.permission_decorators import require_permission
from k9.models.models import Project, UserRole, ProjectStatus
from k9.utils.utils import get_user_permissions

# Create blueprint
bp = Blueprint('reports_attendance_pm_daily_ui', __name__)


@bp.route('/pm-daily')
@login_required
@require_permission('reports:attendance:pm_daily:view')
def pm_daily():
    """
    PM Daily Report page
    
    Query parameters:
        project_id (optional): UUID to prefill project filter
        date (optional): YYYY-MM-DD to prefill date filter
    """
    # Get query parameters for prefilling filters
    prefill_project_id = request.args.get('project_id')
    prefill_date = request.args.get('date', date.today().isoformat())
    
    # Get accessible projects for filter dropdown
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(
            Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])
        ).order_by(Project.name).all()
    else:
        # PROJECT_MANAGER sees only managed projects
        projects = Project.query.filter(
            Project.manager_id == current_user.id,
            Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])
        ).order_by(Project.name).all()
    
    return render_template(
        'reports/attendance/pm_daily.html',
        projects=projects,
        prefill_project_id=prefill_project_id,
        prefill_date=prefill_date,
        page_title="التقرير اليومي لمسؤول المشروع"
    )