"""
UI routes for attendance reporting
Handles HTML page rendering for daily sheet reports
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date

from k9.services.attendance_reporting_services import get_user_accessible_projects, validate_project_date_access
from k9.utils.permission_decorators import require_sub_permission
from k9.models.models import PermissionType, UserRole

# Create blueprint
bp = Blueprint('reports_attendance_ui', __name__)


@bp.route('/daily-sheet')
@login_required
@require_sub_permission("Reports", "Attendance Daily Sheet", PermissionType.VIEW)
def daily_sheet():
    """
    Render the daily sheet report page
    
    Query parameters:
    - project_id (optional): UUID of project to pre-select
    - date (optional): Date in YYYY-MM-DD format to pre-select
    """
    try:
        # Get query parameters for pre-selection
        selected_project_id = request.args.get('project_id')
        selected_date = request.args.get('date')
        
        # Validate selected_date format if provided
        if selected_date:
            try:
                datetime.strptime(selected_date, '%Y-%m-%d')
            except ValueError:
                flash('تنسيق التاريخ غير صحيح', 'error')
                selected_date = None
        
        # Validate project access if project_id provided
        if selected_project_id:
            target_date = datetime.strptime(selected_date, '%Y-%m-%d').date() if selected_date else date.today()
            if not validate_project_date_access(selected_project_id, target_date, current_user):
                flash('ليس لديك صلاحية للوصول لهذا المشروع', 'error')
                selected_project_id = None
        
        # Get accessible projects for the dropdown
        accessible_projects = get_user_accessible_projects(current_user)
        
        # If no projects accessible, show message
        if not accessible_projects:
            if current_user.role == UserRole.PROJECT_MANAGER:
                flash('لا توجد مشاريع مخصصة لك. يرجى التواصل مع المدير العام.', 'warning')
            else:
                flash('لا توجد مشاريع نشطة حالياً.', 'info')
        
        return render_template(
            'reports/attendance/daily_sheet.html',
            accessible_projects=accessible_projects,
            selected_project_id=selected_project_id,
            selected_date=selected_date or date.today().strftime('%Y-%m-%d'),
            page_title='كشف التحضير اليومي'
        )
        
    except Exception as e:
        flash('حدث خطأ في تحميل الصفحة', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/daily-sheet/help')
@login_required 
@require_sub_permission("Reports", "Attendance Daily Sheet", PermissionType.VIEW)
def daily_sheet_help():
    """
    Render help page for daily sheet functionality
    """
    return render_template(
        'reports/attendance/daily_sheet_help.html',
        page_title='مساعدة - كشف التحضير اليومي'
    )