"""
Veterinary daily report UI routes
"""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.utils.permissions import has_permission
from models import Project

bp = Blueprint('veterinary_daily_ui', __name__)


@bp.route('/daily')
@login_required
def daily_report():
    """
    Veterinary daily report page
    """
    # Check permission
    if not has_permission(current_user, "reports:veterinary:daily:view"):
        from flask import abort
        abort(403)
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