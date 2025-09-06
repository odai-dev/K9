"""
Veterinary daily report UI routes
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from k9.utils.permission_decorators import admin_required
from k9.models.models import Project

bp = Blueprint('veterinary_daily_ui', __name__)


@bp.route('/daily')
@login_required
@admin_required
def daily_report():
    """
    Veterinary daily report page
    """
    # Get available projects based on user role
    if current_user.role.value == "GENERAL_ADMIN":
        projects = Project.query.filter(
            Project.status.in_(["ACTIVE", "PLANNED"])
        ).order_by(Project.name).all()
    else:
        # PROJECT_MANAGER - only assigned projects
        projects = [p for p in current_user.managed_projects 
                   if p.status in ["ACTIVE", "PLANNED"]]
    
    return render_template(
        'reports/veterinary/daily.html',
        projects=projects,
        page_title="التقرير اليومي الصحي"
    )