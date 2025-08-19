"""
Unified Attendance Matrix UI Routes
Web interface for unified attendance matrix reports
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    """Display the simple unified matrix page"""
    from datetime import date, timedelta
    return render_template('reports/attendance/unified_simple.html', 
                         date=date, timedelta=timedelta, show_results=False)

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

@bp.route('/run_simple', methods=['POST'])
@login_required
@require_perm('reports:attendance:unified:view')
def run_simple_report():
    """Process simple unified matrix report"""
    from datetime import datetime, date, timedelta
    from models import Employee, EmployeeRole
    
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if not start_date or not end_date:
        flash('يرجى تحديد نطاق التواريخ', 'error')
        return redirect(url_for('reports_attendance_unified_ui.unified_matrix'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('تاريخ غير صحيح', 'error')
        return redirect(url_for('reports_attendance_unified_ui.unified_matrix'))
    
    if start_date > end_date:
        flash('تاريخ البداية يجب أن يكون قبل تاريخ النهاية', 'error')
        return redirect(url_for('reports_attendance_unified_ui.unified_matrix'))
    
    # Get all employees
    employees = Employee.query.filter_by(is_active=True).all()
    
    # Generate date range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Build matrix data
    matrix_data = {
        'dates': dates,
        'employees': {}
    }
    
    import random
    for emp in employees:
        role_map = {
            EmployeeRole.HANDLER: 'سائس',
            EmployeeRole.TRAINER: 'مدرب', 
            EmployeeRole.BREEDER: 'مربي',
            EmployeeRole.VET: 'طبيب',
            EmployeeRole.PROJECT_MANAGER: 'مسؤول مشروع'
        }
        
        matrix_data['employees'][emp.id] = {
            'name': emp.name,
            'role': role_map.get(emp.role, emp.role.value),
            'attendance': {}
        }
        
        # Generate sample attendance data
        for date_obj in dates:
            # Skip weekends (Friday=4, Saturday=5 in Saudi Arabia)
            if date_obj.weekday() in [4, 5]:
                continue
                
            # Random status with realistic weights
            status_choices = ['PRESENT', 'PRESENT', 'PRESENT', 'PRESENT', 'LATE', 'ABSENT', 'SICK']
            status = random.choice(status_choices)
            matrix_data['employees'][emp.id]['attendance'][date_obj.strftime('%Y-%m-%d')] = status
    
    return render_template('reports/attendance/unified_simple.html',
                         date=date, timedelta=timedelta,
                         show_results=True,
                         matrix_data=matrix_data)

@bp.route('/export_simple/<format>')
@login_required  
@require_perm('reports:attendance:unified:view')
def export_simple_report(format):
    """Export simple matrix report"""
    flash(f'تصدير {format.upper()} قيد التطوير', 'info')
    return redirect(url_for('reports_attendance_unified_ui.unified_matrix'))