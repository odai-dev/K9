"""
PM Daily Report Data Services
Provides data retrieval and processing for PM Daily Reports
"""

from datetime import date
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import joinedload
from flask import current_app

from app import db
from models import Project, Employee, Dog, UserRole
from models_attendance_reporting import PMDailyEvaluation, ProjectAttendanceReporting, LeaveType
from dates_ar import get_arabic_day_name
from utils import check_project_access, get_project_manager_permissions


def get_pm_daily(project_id: str, date_str: str, user) -> Dict[str, Any]:
    """
    Get PM Daily Report data for a specific project and date
    
    Args:
        project_id: Project UUID string
        date_str: Date string in YYYY-MM-DD format
        user: Current user object
        
    Returns:
        Dictionary with PM daily report data following the JSON contract
        
    Raises:
        ValueError: If project_id or date_str are invalid
        PermissionError: If user lacks permission
        NotFoundError: If project not found or not accessible
    """
    try:
        # Parse inputs
        project_uuid = UUID(project_id)
        report_date = date.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid project_id or date format: {e}")
    
    # Validate user permission + project visibility
    if user.role == UserRole.PROJECT_MANAGER:
        if not check_project_access(user, project_id):
            raise PermissionError("User does not have access to this project")
        
        permissions = get_project_manager_permissions(user, project_id)
        if not permissions.get("reports:attendance:pm_daily:view", False):
            raise PermissionError("User lacks PM daily view permission")
    
    # Verify project exists
    project = Project.query.get(project_uuid)
    if not project:
        raise ValueError("Project not found")
    
    # Load existing PM daily evaluations for this project/date
    pm_evaluations = PMDailyEvaluation.query.filter_by(
        project_id=project_uuid,
        date=report_date
    ).options(
        joinedload(PMDailyEvaluation.employee),
        joinedload(PMDailyEvaluation.dog),
        joinedload(PMDailyEvaluation.on_leave_employee),
        joinedload(PMDailyEvaluation.on_leave_dog),
        joinedload(PMDailyEvaluation.replacement_employee),
        joinedload(PMDailyEvaluation.replacement_dog)
    ).order_by(PMDailyEvaluation.group_no, PMDailyEvaluation.seq_no).all()
    
    # If no evaluations exist, synthesize from ProjectAttendanceReporting
    if not pm_evaluations:
        pm_evaluations = _synthesize_from_attendance(project_uuid, report_date)
    
    # Build response groups
    groups = _build_response_groups(pm_evaluations)
    
    # Get Arabic day name
    day_name_ar = get_arabic_day_name(report_date)
    
    return {
        "project_id": str(project_uuid),
        "date": date_str,
        "day_name_ar": day_name_ar,
        "groups": groups
    }


def _synthesize_from_attendance(project_id: UUID, report_date: date) -> List[PMDailyEvaluation]:
    """
    Synthesize PM daily evaluations from ProjectAttendanceReporting data
    Creates placeholder PMDailyEvaluation objects when none exist
    
    Args:
        project_id: Project UUID
        report_date: Report date
        
    Returns:
        List of synthesized PMDailyEvaluation objects
    """
    # Get attendance records for this project/date
    attendance_records = ProjectAttendanceReporting.query.filter_by(
        project_id=project_id,
        date=report_date
    ).options(
        joinedload(ProjectAttendanceReporting.employee),
        joinedload(ProjectAttendanceReporting.dog),
        joinedload(ProjectAttendanceReporting.shift)
    ).order_by(
        ProjectAttendanceReporting.group_no,
        ProjectAttendanceReporting.seq_no
    ).all()
    
    synthesized = []
    
    for attendance in attendance_records:
        # Create placeholder PM evaluation from attendance data
        pm_eval = PMDailyEvaluation()
        pm_eval.project_id = project_id
        pm_eval.date = report_date
        pm_eval.group_no = attendance.group_no
        pm_eval.seq_no = attendance.seq_no
        pm_eval.employee_id = attendance.employee_id
        pm_eval.dog_id = attendance.dog_id
        
        # Set basic site/shift info
        if attendance.shift:
            pm_eval.shift_name = attendance.shift.name
            pm_eval.site_name = getattr(attendance.shift, 'site_name', 'غير محدد')
        else:
            pm_eval.shift_name = 'غير محدد'
            pm_eval.site_name = 'غير محدد'
        
        # All evaluation flags default to False (as per model defaults)
        # Performance fields remain None (empty)
        # Violations remain None (empty)
        
        # Populate relationships for name access
        pm_eval.employee = attendance.employee
        pm_eval.dog = attendance.dog
        
        synthesized.append(pm_eval)
    
    # Add special bottom rows if none exist
    if synthesized:
        # Add on-leave row (Group 1)
        on_leave_row = PMDailyEvaluation()
        on_leave_row.project_id = project_id
        on_leave_row.date = report_date
        on_leave_row.group_no = 1
        on_leave_row.seq_no = len([e for e in synthesized if e.group_no == 1]) + 1
        on_leave_row.is_on_leave_row = True
        synthesized.append(on_leave_row)
        
        # Add replacement row (Group 2 or Group 1 if no Group 2)
        replacement_row = PMDailyEvaluation()
        replacement_row.project_id = project_id
        replacement_row.date = report_date
        group_2_count = len([e for e in synthesized if e.group_no == 2 and not e.is_on_leave_row])
        if group_2_count > 0:
            replacement_row.group_no = 2
            replacement_row.seq_no = group_2_count + 1
        else:
            replacement_row.group_no = 1
            replacement_row.seq_no = len([e for e in synthesized if e.group_no == 1]) + 1
        replacement_row.is_replacement_row = True
        synthesized.append(replacement_row)
    
    return synthesized


def _build_response_groups(pm_evaluations: List[PMDailyEvaluation]) -> List[Dict[str, Any]]:
    """
    Build response groups from PM daily evaluations
    
    Args:
        pm_evaluations: List of PMDailyEvaluation objects
        
    Returns:
        List of group dictionaries with rows
    """
    groups_dict = {}
    
    for pm_eval in pm_evaluations:
        group_no = pm_eval.group_no
        
        if group_no not in groups_dict:
            groups_dict[group_no] = {
                "group_no": group_no,
                "rows": []
            }
        
        # Build row data
        row_data = {
            "seq_no": pm_eval.seq_no,
            "employee_name": pm_eval.employee.full_name if pm_eval.employee else "",
            "dog_name": pm_eval.dog.name if pm_eval.dog else "",
            "site_name": pm_eval.site_name or "",
            "shift_name": pm_eval.shift_name or "",
            
            # Personal evaluation checkboxes
            "uniform_ok": pm_eval.uniform_ok,
            "card_ok": pm_eval.card_ok,
            "appearance_ok": pm_eval.appearance_ok,
            "cleanliness_ok": pm_eval.cleanliness_ok,
            
            # Dog care checkboxes
            "dog_exam_done": pm_eval.dog_exam_done,
            "dog_fed": pm_eval.dog_fed,
            "dog_watered": pm_eval.dog_watered,
            
            # Training checkboxes
            "training_tansheti": pm_eval.training_tansheti,
            "training_other": pm_eval.training_other,
            
            # Field deployment
            "field_deployment_done": pm_eval.field_deployment_done,
            
            # Performance evaluations
            "perf_sais": pm_eval.perf_sais or "",
            "perf_dog": pm_eval.perf_dog or "",
            "perf_murabbi": pm_eval.perf_murabbi or "",
            "perf_sehi": pm_eval.perf_sehi or "",
            "perf_mudarrib": pm_eval.perf_mudarrib or "",
            
            # Violations
            "violations": pm_eval.violations or "",
            
            # Special row flags and data
            "is_on_leave_row": pm_eval.is_on_leave_row,
            "on_leave_employee_name": pm_eval.on_leave_employee.full_name if pm_eval.on_leave_employee else None,
            "on_leave_dog_name": pm_eval.on_leave_dog.name if pm_eval.on_leave_dog else None,
            "on_leave_type": pm_eval.on_leave_type.value if pm_eval.on_leave_type else None,
            "on_leave_note": pm_eval.on_leave_note,
            
            "is_replacement_row": pm_eval.is_replacement_row,
            "replacement_employee_name": pm_eval.replacement_employee.full_name if pm_eval.replacement_employee else None,
            "replacement_dog_name": pm_eval.replacement_dog.name if pm_eval.replacement_dog else None
        }
        
        groups_dict[group_no]["rows"].append(row_data)
    
    # Convert to list sorted by group number
    return [groups_dict[key] for key in sorted(groups_dict.keys())]