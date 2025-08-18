"""
Unified Attendance Matrix Services
Data provider for unified attendance matrix reports
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_, func
from flask_login import current_user

from app import db
from models import Employee, Dog, Project, User, UserRole
from models_attendance_reporting import ProjectAttendanceReporting, AttendanceStatus
from permission_utils import has_permission


def get_unified_matrix(filters: dict, user: User) -> dict:
    """
    Get unified attendance matrix data with ownership rule enforcement
    
    Args:
        filters: Dictionary containing filter parameters
        user: Current user object
        
    Returns:
        Dictionary with matrix data following the API contract
    """
    # Parse and validate date range
    try:
        date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
        date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        raise ValueError("date_from and date_to are required in YYYY-MM-DD format")
    
    # Validate date range (max 62 days)
    if (date_to - date_from).days > 62:
        raise ValueError("Date range cannot exceed 62 days")
    
    if date_from > date_to:
        raise ValueError("date_from cannot be after date_to")
    
    # Generate ordered list of days
    days = []
    current_date = date_from
    while current_date <= date_to:
        days.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Determine visible employees based on user role
    visible_employees = _get_visible_employees(user, filters)
    
    # Apply ownership rule: get project-controlled attendance pairs to exclude
    excluded_pairs = _get_project_controlled_pairs(visible_employees, date_from, date_to)
    
    # Get attendance data for remaining pairs
    attendance_data = _get_attendance_data(visible_employees, date_from, date_to, excluded_pairs)
    
    # Get dog assignments if requested
    dog_assignments = {}
    if filters.get('include_dogs', False):
        dog_assignments = _get_dog_assignments(visible_employees, date_from, date_to)
    
    # Build matrix rows
    rows = []
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 50)
    
    # Apply pagination to employees
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_employees = visible_employees[start_idx:end_idx]
    
    for employee in paginated_employees:
        row = {
            'employee_id': str(employee.id),
            'employee_name': employee.name,
            'cells': []
        }
        
        # Add dog name if requested
        if filters.get('include_dogs', False):
            row['dog_name'] = dog_assignments.get(str(employee.id))
        
        # Build cells for each day
        for day in days:
            day_date = datetime.strptime(day, '%Y-%m-%d').date()
            employee_day_key = (str(employee.id), day_date)
            
            if employee_day_key in excluded_pairs:
                # Project-controlled - exclude entirely from unified matrix
                cell = {
                    'date': day,
                    'status': None,
                    'project_controlled': True,
                    'check_in_time': None,
                    'check_out_time': None,
                    'tooltip': 'مستبعد من المصفوفة الموحدة'
                }
            else:
                # Get attendance data for this employee/day
                attendance = attendance_data.get(employee_day_key)
                cell = _build_cell_data(day, attendance, filters.get('status_in'))
            
            row['cells'].append(cell)
        
        rows.append(row)
    
    # Build pagination info
    total_rows = len(visible_employees)
    total_pages = (total_rows + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_rows': total_rows,
        'pages': total_pages
    }
    
    # Build legend
    legend = [
        {'key': 'PRESENT', 'label_ar': 'حاضر'},
        {'key': 'ABSENT', 'label_ar': 'غائب'},
        {'key': 'LATE', 'label_ar': 'متأخر'},
        {'key': 'SICK', 'label_ar': 'مرضية'},
        {'key': 'LEAVE', 'label_ar': 'إجازة'},
        {'key': 'REMOTE', 'label_ar': 'عن بُعد'},
        {'key': 'OVERTIME', 'label_ar': 'عمل إضافي'}
    ]
    
    return {
        'date_from': filters['date_from'],
        'date_to': filters['date_to'],
        'days': days,
        'rows': rows,
        'pagination': pagination,
        'legend': legend
    }


def _get_visible_employees(user: User, filters: dict) -> List[Employee]:
    """Get list of employees visible to the user based on role and filters"""
    query = Employee.query.filter(Employee.is_active == True)
    
    if user.role == UserRole.GENERAL_ADMIN:
        # Admin sees all active employees
        if filters.get('employee_ids'):
            query = query.filter(Employee.id.in_(filters['employee_ids']))
    
    elif user.role == UserRole.PROJECT_MANAGER:
        # PM sees employees assigned to their projects
        assigned_projects = Project.query.filter(
            and_(
                Project.manager_id == user.id,
                Project.status.in_(['ACTIVE', 'PLANNED'])
            )
        ).all()
        
        project_ids = [p.id for p in assigned_projects]
        if not project_ids:
            return []
        
        # Get employees assigned to these projects (this would need proper relationship)
        # For now, return all employees but could be refined with project assignments
        if filters.get('employee_ids'):
            query = query.filter(Employee.id.in_(filters['employee_ids']))
    
    return query.all()


def _get_project_controlled_pairs(employees: List[Employee], date_from: date, date_to: date) -> set:
    """
    Get (employee_id, date) pairs that have project-controlled attendance
    These pairs must be excluded from the unified matrix per ownership rule
    """
    if not employees:
        return set()
    
    employee_ids = [e.id for e in employees]
    
    # Query for project-controlled attendance in date range
    controlled_attendance = db.session.query(
        ProjectAttendanceReporting.employee_id,
        ProjectAttendanceReporting.date
    ).filter(
        and_(
            ProjectAttendanceReporting.is_project_controlled == True,
            ProjectAttendanceReporting.employee_id.in_(employee_ids),
            ProjectAttendanceReporting.date >= date_from,
            ProjectAttendanceReporting.date <= date_to
        )
    ).distinct().all()
    
    # Convert to set of (employee_id_str, date) tuples
    excluded_pairs = set()
    for emp_id, att_date in controlled_attendance:
        excluded_pairs.add((str(emp_id), att_date))
    
    return excluded_pairs


def _get_attendance_data(employees: List[Employee], date_from: date, date_to: date, excluded_pairs: set) -> dict:
    """
    Get attendance data for employees in date range, excluding project-controlled pairs
    """
    if not employees:
        return {}
    
    employee_ids = [e.id for e in employees]
    
    # Query non-project-controlled attendance
    attendance_records = ProjectAttendanceReporting.query.filter(
        and_(
            ProjectAttendanceReporting.is_project_controlled == False,
            ProjectAttendanceReporting.employee_id.in_(employee_ids),
            ProjectAttendanceReporting.date >= date_from,
            ProjectAttendanceReporting.date <= date_to
        )
    ).all()
    
    # Build dictionary keyed by (employee_id_str, date)
    attendance_data = {}
    for record in attendance_records:
        key = (str(record.employee_id), record.date)
        if key not in excluded_pairs:  # Double-check exclusion
            attendance_data[key] = record
    
    return attendance_data


def _get_dog_assignments(employees: List[Employee], date_from: date, date_to: date) -> dict:
    """Get latest dog assignments for employees in the date range"""
    # This would need proper dog assignment tracking
    # For now, return empty assignments
    # TODO: Implement based on actual dog assignment model
    return {}


def _build_cell_data(day: str, attendance: Optional[ProjectAttendanceReporting], status_filter: Optional[List[str]]) -> dict:
    """Build cell data for a specific day"""
    if not attendance:
        return {
            'date': day,
            'status': None,
            'project_controlled': False,
            'check_in_time': None,
            'check_out_time': None,
            'tooltip': 'لا توجد بيانات'
        }
    
    status = attendance.status.value if attendance.status else None
    
    # Apply status filter if provided
    if status_filter and status not in status_filter:
        status = None
    
    # Build tooltip
    tooltip = _build_tooltip(attendance)
    
    return {
        'date': day,
        'status': status,
        'project_controlled': False,
        'check_in_time': attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time is not None else None,
        'check_out_time': attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time is not None else None,
        'tooltip': tooltip
    }


def _build_tooltip(attendance: ProjectAttendanceReporting) -> str:
    """Build Arabic tooltip for attendance record"""
    if not attendance.status:
        return 'لا توجد بيانات'
    
    status_labels = {
        'PRESENT': 'حاضر',
        'ABSENT': 'غائب',
        'LATE': 'متأخر',
        'SICK': 'مرضية',
        'LEAVE': 'إجازة',
        'REMOTE': 'عن بُعد',
        'OVERTIME': 'عمل إضافي'
    }
    
    status_text = status_labels.get(attendance.status.value, attendance.status.value)
    
    if attendance.check_in_time is not None and attendance.check_out_time is not None:
        return f"{status_text} {attendance.check_in_time.strftime('%H:%M')} → {attendance.check_out_time.strftime('%H:%M')}"
    elif attendance.check_in_time is not None:
        return f"{status_text} {attendance.check_in_time.strftime('%H:%M')}"
    else:
        return status_text