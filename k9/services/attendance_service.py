"""
Attendance Service - Unified Global Attendance System
Handles attendance tracking with strict project ownership rules.
"""

from datetime import datetime, date
from sqlalchemy import and_, or_
from app import db
from k9.models.models import (Employee, Project, ProjectAssignment, AttendanceDay, AttendanceStatus,
                   ProjectStatus, AuditAction)
from k9.utils.utils import log_audit
from flask_login import current_user
from flask import request


class ProjectOwnershipError(Exception):
    """Raised when trying to modify attendance for project-owned employee"""
    pass


def resolve_project_control(employee_id, target_date):
    """
    Determine if an employee is owned by a project on a specific date.
    Returns dict with project ownership information.
    """
    try:
        # Convert string dates to date objects if needed
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        employee = Employee.query.get(employee_id)
        if not employee:
            return {"is_owned": False, "project_id": None, "project_name": None}
        
        # Check if employee has any active assignments that cover the target date
        assignment_query = db.session.query(ProjectAssignment, Project).join(
            Project, ProjectAssignment.project_id == Project.id
        ).filter(
            and_(
                ProjectAssignment.employee_id == employee_id,
                ProjectAssignment.is_active == True,
                or_(
                    Project.status == ProjectStatus.ACTIVE,
                    Project.status == ProjectStatus.PLANNED
                ),
                or_(
                    # Assignment has no end date (open-ended)
                    ProjectAssignment.assigned_to.is_(None),
                    # Or target date is within assignment period
                    and_(
                        ProjectAssignment.assigned_from <= target_date,
                        ProjectAssignment.assigned_to >= target_date
                    )
                ),
                or_(
                    # Project has no end date (open-ended)
                    Project.end_date.is_(None),
                    # Or target date is within project period  
                    and_(
                        Project.start_date <= target_date,
                        Project.end_date >= target_date
                    )
                )
            )
        )
        
        # Get the first matching assignment (deterministic - earliest created)
        result = assignment_query.order_by(ProjectAssignment.created_at.asc()).first()
        
        if result:
            assignment, project = result
            return {
                "is_owned": True,
                "project_id": str(project.id),
                "project_name": project.name,
                "assignment": assignment
            }
        else:
            return {"is_owned": False, "project_id": None, "project_name": None}
            
    except Exception as e:
        # Log the error but don't expose it to users
        print(f"Error in resolve_project_control: {e}")
        return {"is_owned": False, "project_id": None, "project_name": None}


def get_attendance_day(employee_id, target_date):
    """Get attendance record for an employee on a specific date"""
    try:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        return AttendanceDay.query.filter_by(
            employee_id=employee_id, 
            date=target_date
        ).first()
    except Exception as e:
        print(f"Error in get_attendance_day: {e}")
        return None


def set_attendance_global(employee_id, target_date, status, note=None):
    """
    Set global attendance for an employee on a specific date.
    Raises ProjectOwnershipError if employee is project-owned on that date.
    """
    try:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        # Check project ownership
        ownership = resolve_project_control(employee_id, target_date)
        if ownership["is_owned"]:
            raise ProjectOwnershipError(
                f"Employee is assigned to active project '{ownership['project_name']}' on this date. "
                "Edit attendance in the project dashboard."
            )
        
        # Convert string status to enum if needed
        if isinstance(status, str):
            status = AttendanceStatus(status)
            
        employee = Employee.query.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
            
        # Get existing record or create new one
        attendance = get_attendance_day(employee_id, target_date)
        old_status = attendance.status.value if attendance else None
        
        if attendance:
            # Update existing record
            attendance.status = status
            attendance.note = note
            attendance.updated_at = datetime.utcnow()
        else:
            # Create new record
            attendance = AttendanceDay(
                employee_id=employee_id,
                date=target_date,
                status=status,
                note=note,
                source='global',
                locked=False
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        # Audit log
        if current_user and current_user.is_authenticated:
            log_audit(
                user_id=current_user.id,
                action=AuditAction.UPDATE if old_status else AuditAction.CREATE,
                target_type='AttendanceDay',
                target_id=str(attendance.id),
                target_name=f"{employee.name} - {target_date}",
                description=f"Set attendance status from '{old_status or 'None'}' to '{status.value}'",
                old_values={'status': old_status} if old_status else {},
                new_values={'status': status.value, 'note': note},
                ip_address=request.remote_addr if request else None
            )
        
        return attendance
        
    except ProjectOwnershipError:
        # Re-raise project ownership errors
        raise
    except Exception as e:
        print(f"Error in set_attendance_global: {e}")
        db.session.rollback()
        raise ValueError(f"Failed to set attendance: {str(e)}")


def get_globally_editable_employees(target_date, search=None, status_filter=None, page=1, per_page=50):
    """
    Get employees that can be edited in the global attendance system on a specific date.
    Excludes employees assigned to active projects on that date.
    """
    try:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        # Start with all active employees
        query = Employee.query.filter(Employee.is_active == True)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.name.ilike(search_term),
                    Employee.employee_id.ilike(search_term)
                )
            )
        
        # Get employee IDs that are project-owned on the target date (need to exclude these)
        project_owned_subquery = db.session.query(ProjectAssignment.employee_id).join(
            Project, ProjectAssignment.project_id == Project.id
        ).filter(
            and_(
                ProjectAssignment.employee_id.isnot(None),  # Only assignments with employee_id
                ProjectAssignment.is_active == True,
                or_(
                    Project.status == ProjectStatus.ACTIVE,
                    Project.status == ProjectStatus.PLANNED
                ),
                or_(
                    # Assignment has no end date (open-ended)
                    ProjectAssignment.assigned_to.is_(None),
                    # Or target date is within assignment period
                    and_(
                        ProjectAssignment.assigned_from <= target_date,
                        ProjectAssignment.assigned_to >= target_date
                    )
                ),
                or_(
                    # Project has no end date (open-ended)
                    Project.end_date.is_(None),
                    # Or target date is within project period
                    and_(
                        Project.start_date <= target_date,
                        Project.end_date >= target_date
                    )
                )
            )
        )
        
        # Convert subquery to list to avoid SQLAlchemy issues
        project_owned_employee_ids = [row[0] for row in project_owned_subquery.all() if row[0] is not None]
        
        # Exclude project-owned employees
        if project_owned_employee_ids:
            query = query.filter(~Employee.id.in_(project_owned_employee_ids))
        
        # Get employees with their attendance for the date
        employees = query.order_by(Employee.name).all()
        
        # Get attendance records for these employees on the target date
        employee_ids = [emp.id for emp in employees]
        attendance_records = {}
        if employee_ids:
            records = AttendanceDay.query.filter(
                and_(
                    AttendanceDay.employee_id.in_(employee_ids),
                    AttendanceDay.date == target_date
                )
            ).all()
            attendance_records = {rec.employee_id: rec for rec in records}
        
        # Build result with attendance info
        result = []
        for employee in employees:
            attendance = attendance_records.get(employee.id)
            employee_data = {
                'id': str(employee.id),
                'name': employee.name,
                'employee_id': employee.employee_id,
                'role': employee.role.value,
                'status': attendance.status.value if attendance else AttendanceStatus.ABSENT.value,
                'note': attendance.note if attendance else '',
                'has_attendance': attendance is not None
            }
            
            # Apply status filter
            if status_filter and employee_data['status'] != status_filter:
                continue
                
            result.append(employee_data)
        
        # Manual pagination
        total = len(result)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_result = result[start_idx:end_idx]
        
        return {
            'employees': paginated_result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
    except Exception as e:
        print(f"Error in get_globally_editable_employees: {e}")
        return {
            'employees': [],
            'total': 0,
            'page': 1,
            'per_page': per_page,
            'pages': 0
        }


def get_attendance_stats(target_date):
    """Get attendance statistics for globally editable employees on a specific date"""
    try:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        # Get all globally editable employees (unlimited)
        editable_data = get_globally_editable_employees(target_date, per_page=1000)
        employees = editable_data['employees']
        
        # Count by status
        stats = {}
        for status in AttendanceStatus:
            stats[status.value] = 0
            
        for emp in employees:
            stats[emp['status']] += 1
            
        stats['total_editable'] = len(employees)
        
        return stats
        
    except Exception as e:
        print(f"Error in get_attendance_stats: {e}")
        return {status.value: 0 for status in AttendanceStatus} | {'total_editable': 0}


def create_project_attendance_record(employee_id, target_date, status, project_id, note=None):
    """
    Create attendance record from project system.
    This creates a locked record that excludes the employee from global attendance.
    """
    try:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
            
        if isinstance(status, str):
            status = AttendanceStatus(status)
            
        # Get or create attendance record
        attendance = get_attendance_day(employee_id, target_date)
        
        if attendance:
            # Update existing record to project source
            attendance.status = status
            attendance.note = note
            attendance.source = 'project'
            attendance.project_id = project_id
            attendance.locked = True
            attendance.updated_at = datetime.utcnow()
        else:
            # Create new project-sourced record
            attendance = AttendanceDay(
                employee_id=employee_id,
                date=target_date,
                status=status,
                note=note,
                source='project',
                project_id=project_id,
                locked=True
            )
            db.session.add(attendance)
        
        db.session.commit()
        return attendance
        
    except Exception as e:
        print(f"Error in create_project_attendance_record: {e}")
        db.session.rollback()
        return None