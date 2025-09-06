"""
Data provider services for attendance reporting
Handles data retrieval and processing for daily sheet reports
"""

from datetime import datetime, date
from uuid import UUID
from typing import Dict, List, Optional
from sqlalchemy import and_, or_
from flask_login import current_user

from app import db
from k9.models.models import Project, Employee, Dog, ProjectShift, UserRole
from k9.models.models_attendance_reporting import ProjectAttendanceReporting, AttendanceDayLeave
from k9.utils.attendance_reporting_constants import ARABIC_DAY_NAMES, LEAVE_TYPE_ARABIC
from k9.utils.utils import check_project_access


def get_daily_sheet(project_id: str, target_date: date, user) -> Dict:
    """
    Get daily attendance sheet data for a specific project and date
    
    Args:
        project_id: UUID of the project
        target_date: Date for the report
        user: Current user for permission checking
        
    Returns:
        Dictionary containing the daily sheet data in the specified JSON contract format
    """
    try:
        # Handle UUID compatibility - use string for SQLite
        import os
        database_url = os.environ.get("DATABASE_URL", "")
        use_string_uuid = database_url.startswith("sqlite") or not database_url
        
        if use_string_uuid:
            # For SQLite, keep as string and validate format
            try:
                UUID(project_id)  # Validate format
                project_search_id = project_id
            except:
                raise ValueError("Invalid project ID format")
        else:
            # For PostgreSQL, convert to UUID
            project_search_id = UUID(project_id) if isinstance(project_id, str) else project_id
        
        # Convert string to date if needed
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        elif isinstance(target_date, datetime):
            target_date = target_date.date()
        
        # Check user permissions - PROJECT_MANAGER can only see assigned projects
        if user.role == UserRole.PROJECT_MANAGER:
            if not check_project_access(user, project_id):
                raise PermissionError("User does not have access to this project")
        
        # Get project information
        project = Project.query.get(project_search_id)
        if not project:
            raise ValueError("Project not found")
        
        # Get attendance records for the date, split by groups
        group_1_query = ProjectAttendanceReporting.query.filter(
            and_(
                ProjectAttendanceReporting.project_id == project_search_id,
                ProjectAttendanceReporting.date == target_date,
                ProjectAttendanceReporting.group_no == 1
            )
        ).order_by(ProjectAttendanceReporting.seq_no.asc())
        
        group_2_query = ProjectAttendanceReporting.query.filter(
            and_(
                ProjectAttendanceReporting.project_id == project_search_id,
                ProjectAttendanceReporting.date == target_date,
                ProjectAttendanceReporting.group_no == 2
            )
        ).order_by(ProjectAttendanceReporting.seq_no.asc())
        
        # Process Group 1 records (with substitute employee)
        group_1_rows = []
        for record in group_1_query:
            row_data = {
                "seq_no": record.seq_no,
                "employee_name": record.employee.name if record.employee else "",
                "substitute_name": record.substitute_employee.name if record.substitute_employee else "",
                "dog_name": record.dog.name if record.dog else "",
                "check_in_time": record.check_in_time.strftime("%H:%M") if record.check_in_time else "",
                "check_in_signed": False,  # Always false as per spec - for signature boxes
                "check_out_time": record.check_out_time.strftime("%H:%M") if record.check_out_time else "",
                "check_out_signed": False  # Always false as per spec - for signature boxes
            }
            group_1_rows.append(row_data)
        
        # Process Group 2 records (combined employee/substitute name)
        group_2_rows = []
        for record in group_2_query:
            # For group 2, use either employee or substitute name
            employee_or_substitute_name = ""
            if record.employee:
                employee_or_substitute_name = record.employee.name
            elif record.substitute_employee:
                employee_or_substitute_name = record.substitute_employee.name
            
            row_data = {
                "seq_no": record.seq_no,
                "employee_or_substitute_name": employee_or_substitute_name,
                "dog_name": record.dog.name if record.dog else "",
                "check_in_time": record.check_in_time.strftime("%H:%M") if record.check_in_time else "",
                "check_in_signed": False,  # Always false as per spec - for signature boxes
                "check_out_time": record.check_out_time.strftime("%H:%M") if record.check_out_time else "",
                "check_out_signed": False  # Always false as per spec - for signature boxes
            }
            group_2_rows.append(row_data)
        
        # Get leave records for the bottom table
        leave_query = AttendanceDayLeave.query.filter(
            and_(
                AttendanceDayLeave.project_id == project_search_id,
                AttendanceDayLeave.date == target_date
            )
        ).order_by(AttendanceDayLeave.seq_no.asc())
        
        leave_rows = []
        for leave_record in leave_query:
            leave_data = {
                "seq_no": leave_record.seq_no,
                "employee_name": leave_record.employee.name if leave_record.employee else "",
                "leave_type": LEAVE_TYPE_ARABIC.get(leave_record.leave_type.value, leave_record.leave_type.value),
                "note": leave_record.note or ""
            }
            leave_rows.append(leave_data)
        
        # Get Arabic day name
        day_name_ar = ARABIC_DAY_NAMES.get(target_date.weekday(), "غير محدد")
        
        # Build response according to JSON contract
        response = {
            "project_id": project_id,
            "date": target_date.strftime("%Y-%m-%d"),
            "day_name_ar": day_name_ar,
            "groups": [
                {
                    "group_no": 1,
                    "rows": group_1_rows
                },
                {
                    "group_no": 2,
                    "rows": group_2_rows
                }
            ],
            "leaves": leave_rows
        }
        
        return response
        
    except Exception as e:
        print(f"Error in get_daily_sheet: {e}")
        raise


def get_user_accessible_projects(user) -> List[Dict]:
    """
    Get list of projects accessible to the user for the attendance reports
    
    Args:
        user: Current user
        
    Returns:
        List of project dictionaries with id, name, and code
    """
    try:
        if user.role == UserRole.GENERAL_ADMIN:
            # Admin can see all projects
            projects = Project.query.filter(
                or_(
                    Project.status == "ACTIVE",
                    Project.status == "PLANNED"
                )
            ).order_by(Project.name).all()
        else:
            # PROJECT_MANAGER can only see assigned projects
            from k9.utils.permission_utils import get_user_accessible_projects as get_accessible
            accessible_project_ids = get_accessible(user)
            
            if accessible_project_ids:
                projects = Project.query.filter(
                    and_(
                        Project.id.in_(accessible_project_ids),
                        or_(
                            Project.status == "ACTIVE",
                            Project.status == "PLANNED"
                        )
                    )
                ).order_by(Project.name).all()
            else:
                projects = []
        
        # Convert to list of dictionaries
        project_list = []
        for project in projects:
            project_data = {
                "id": str(project.id),
                "name": project.name,
                "code": project.code
            }
            project_list.append(project_data)
        
        return project_list
        
    except Exception as e:
        print(f"Error in get_user_accessible_projects: {e}")
        return []


def validate_project_date_access(project_id: str, target_date: date, user) -> bool:
    """
    Validate that user has access to view attendance for given project and date
    
    Args:
        project_id: UUID of the project
        target_date: Date to check
        user: Current user
        
    Returns:
        True if access is allowed, False otherwise
    """
    try:
        # Keep project_id as string for validation but create UUID for DB queries
        project_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            
        # GENERAL_ADMIN always has access
        if user.role == UserRole.GENERAL_ADMIN:
            return True
        
        # Check if PROJECT_MANAGER has access to this project
        if user.role == UserRole.PROJECT_MANAGER:
            return check_project_access(user, project_id)
        
        return False
        
    except Exception as e:
        print(f"Error in validate_project_date_access: {e}")
        return False