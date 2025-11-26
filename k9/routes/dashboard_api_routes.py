"""
Dashboard API Routes
Provides JSON endpoints for dashboard chart data
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from k9.utils.permissions_new import admin_required, has_permission
from k9.services.dashboard_service import DashboardService
from k9.routes.pm_routes import get_pm_project, require_pm_project
from functools import wraps

dashboard_api_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')


@dashboard_api_bp.route('/pm/report-status')
@login_required
@require_pm_project
def pm_report_status():
    """Get handler report status distribution for PM's project"""
    project = get_pm_project()
    if not project:
        return jsonify({'error': 'No project assigned'}), 404
    
    data = DashboardService.get_handler_report_status_distribution(project.id)
    return jsonify(data)


@dashboard_api_bp.route('/pm/attendance-trends')
@login_required
@require_pm_project
def pm_attendance_trends():
    """Get attendance trends for PM's project"""
    project = get_pm_project()
    if not project:
        return jsonify({'error': 'No project assigned'}), 404
    
    days = request.args.get('days', 30, type=int)
    data = DashboardService.get_attendance_trends(project.id, days=days)
    return jsonify(data)


@dashboard_api_bp.route('/pm/handler-activity')
@login_required
@require_pm_project
def pm_handler_activity():
    """Get dogs worked per handler for PM's project"""
    project = get_pm_project()
    if not project:
        return jsonify({'error': 'No project assigned'}), 404
    
    limit = request.args.get('limit', 10, type=int)
    data = DashboardService.get_dogs_worked_per_handler(project.id, limit=limit)
    return jsonify(data)


@dashboard_api_bp.route('/pm/monthly-trends')
@login_required
@require_pm_project
def pm_monthly_trends():
    """Get monthly report submission trends for PM's project"""
    project = get_pm_project()
    if not project:
        return jsonify({'error': 'No project assigned'}), 404
    
    months = request.args.get('months', 6, type=int)
    data = DashboardService.get_monthly_report_trends(project.id, months=months)
    return jsonify(data)


@dashboard_api_bp.route('/pm/all')
@login_required
@require_pm_project
def pm_all_data():
    """Get all dashboard data for PM in one request"""
    project = get_pm_project()
    if not project:
        return jsonify({'error': 'No project assigned'}), 404
    
    data = DashboardService.get_pm_dashboard_data(project.id)
    return jsonify(data)


@dashboard_api_bp.route('/admin/dogs-by-project')
@login_required
@admin_required
def admin_dogs_by_project():
    """Get active dogs count by project"""
    data = DashboardService.get_active_dogs_by_project()
    return jsonify(data)


@dashboard_api_bp.route('/admin/dogs-by-status')
@login_required
@admin_required
def admin_dogs_by_status():
    """Get dogs distribution by status"""
    data = DashboardService.get_dogs_by_status()
    return jsonify(data)


@dashboard_api_bp.route('/admin/employee-by-role')
@login_required
@admin_required
def admin_employee_by_role():
    """Get employee distribution by role"""
    data = DashboardService.get_employee_distribution_by_role()
    return jsonify(data)


@dashboard_api_bp.route('/admin/project-status')
@login_required
@admin_required
def admin_project_status():
    """Get project status overview"""
    data = DashboardService.get_project_status_overview()
    return jsonify(data)


@dashboard_api_bp.route('/admin/report-status')
@login_required
@admin_required
def admin_report_status():
    """Get system-wide handler report status distribution"""
    data = DashboardService.get_handler_report_status_distribution()
    return jsonify(data)


@dashboard_api_bp.route('/admin/attendance-trends')
@login_required
@admin_required
def admin_attendance_trends():
    """Get system-wide attendance trends"""
    days = request.args.get('days', 30, type=int)
    data = DashboardService.get_attendance_trends(days=days)
    return jsonify(data)


@dashboard_api_bp.route('/admin/all')
@login_required
@admin_required
def admin_all_data():
    """Get all dashboard data for Admin in one request"""
    if not has_permission("api.dashboard.access"):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = DashboardService.get_admin_dashboard_data()
    return jsonify(data)
