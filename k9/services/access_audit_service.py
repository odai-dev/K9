"""
Access Audit Service
Provides comprehensive access logging for GENERAL_ADMIN mode switching and data access
"""

import uuid
import logging
from datetime import datetime
from flask import request, session
from flask_login import current_user
from k9.models.models import AccessAuditLog, AccessActionType, AccessOutcome
from app import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def log_access(
    action_type,
    target_type=None,
    target_id=None,
    target_name=None,
    outcome=AccessOutcome.SUCCESS,
    extra_metadata=None,
    user=None
):
    """
    Core function to log an access action using an isolated session
    
    Args:
        action_type: AccessActionType enum value
        target_type: Type of target (e.g., 'project', 'dog', 'report')
        target_id: ID of target resource
        target_name: Human-readable name of target
        outcome: AccessOutcome enum value (SUCCESS, FAILURE, BLOCKED)
        extra_metadata: Dict of additional context data
        user: User object (defaults to current_user)
    """
    if user is None:
        user = current_user
    
    if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return
    
    Session = None
    try:
        log_entry = AccessAuditLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            request_path=request.path if request else None,
            http_method=request.method if request else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            session_id=session.get('_id') if session else None,
            admin_mode=session.get('admin_mode') if session else None,
            outcome=outcome,
            extra_metadata=extra_metadata,
            created_at=datetime.utcnow()
        )
        
        # Use isolated session to avoid committing in-flight business transactions
        Session = sessionmaker(bind=db.engine)
        with Session.begin() as audit_session:
            audit_session.add(log_entry)
        
    except Exception as e:
        logger.error(f"Error logging access: {e}", exc_info=True)
        # Fallback: try using main session if isolated session fails
        try:
            db.session.add(log_entry)
            db.session.flush()
        except Exception as fallback_error:
            logger.error(f"Fallback audit logging also failed: {fallback_error}", exc_info=True)


def log_page_access(page_name, project_id=None, project_name=None, outcome=AccessOutcome.SUCCESS):
    """
    Log access to a page/route
    
    Args:
        page_name: Name of the page/route accessed
        project_id: Project ID if page is project-scoped
        project_name: Project name for display
        outcome: AccessOutcome enum value
    """
    metadata = {
        'page_name': page_name
    }
    
    if project_id:
        metadata['project_id'] = str(project_id)
    
    log_access(
        action_type=AccessActionType.PAGE_ACCESS,
        target_type='page',
        target_id=project_id,
        target_name=project_name or page_name,
        outcome=outcome,
        extra_metadata=metadata
    )


def log_project_access(project_id, project_name, action='view', outcome=AccessOutcome.SUCCESS):
    """
    Log access to a project
    
    Args:
        project_id: Project ID
        project_name: Project name
        action: Type of action ('view', 'edit', 'create', 'delete')
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.PROJECT_ACCESS,
        target_type='project',
        target_id=str(project_id),
        target_name=project_name,
        outcome=outcome,
        extra_metadata={'action': action}
    )


def log_data_export(export_type, record_count=None, filters=None, outcome=AccessOutcome.SUCCESS):
    """
    Log data export action
    
    Args:
        export_type: Type of data exported (e.g., 'training_report', 'vet_records')
        record_count: Number of records exported
        filters: Dict of filters applied
        outcome: AccessOutcome enum value
    """
    metadata = {
        'export_type': export_type
    }
    
    if record_count is not None:
        metadata['record_count'] = record_count
    
    if filters:
        metadata['filters'] = filters
    
    log_access(
        action_type=AccessActionType.DATA_EXPORT,
        target_type='export',
        target_name=export_type,
        outcome=outcome,
        extra_metadata=metadata
    )


def log_file_download(file_type, file_name, file_id=None, outcome=AccessOutcome.SUCCESS):
    """
    Log file download action
    
    Args:
        file_type: Type of file (e.g., 'pdf_report', 'excel_export')
        file_name: Name of the file
        file_id: ID of file record if applicable
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.FILE_DOWNLOAD,
        target_type=file_type,
        target_id=file_id,
        target_name=file_name,
        outcome=outcome,
        extra_metadata={'file_type': file_type}
    )


def log_schedule_access(schedule_id, schedule_name, action='view', outcome=AccessOutcome.SUCCESS):
    """
    Log access to schedules
    
    Args:
        schedule_id: Schedule ID
        schedule_name: Schedule description
        action: Type of action
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.SCHEDULE_ACCESS,
        target_type='schedule',
        target_id=str(schedule_id),
        target_name=schedule_name,
        outcome=outcome,
        extra_metadata={'action': action}
    )


def log_shift_access(shift_id, shift_name, action='view', outcome=AccessOutcome.SUCCESS):
    """
    Log access to shift reports
    
    Args:
        shift_id: Shift report ID
        shift_name: Shift description
        action: Type of action
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.SHIFT_ACCESS,
        target_type='shift_report',
        target_id=str(shift_id),
        target_name=shift_name,
        outcome=outcome,
        extra_metadata={'action': action}
    )


def log_report_approval(report_type, report_id, report_name, outcome=AccessOutcome.SUCCESS):
    """
    Log report approval action
    
    Args:
        report_type: Type of report (e.g., 'shift_report', 'training_report')
        report_id: Report ID
        report_name: Report description
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.REPORT_APPROVAL,
        target_type=report_type,
        target_id=str(report_id),
        target_name=report_name,
        outcome=outcome
    )


def log_report_rejection(report_type, report_id, report_name, reason=None, outcome=AccessOutcome.SUCCESS):
    """
    Log report rejection action
    
    Args:
        report_type: Type of report
        report_id: Report ID
        report_name: Report description
        reason: Rejection reason
        outcome: AccessOutcome enum value
    """
    metadata = {}
    if reason:
        metadata['rejection_reason'] = reason
    
    log_access(
        action_type=AccessActionType.REPORT_REJECTION,
        target_type=report_type,
        target_id=str(report_id),
        target_name=report_name,
        outcome=outcome,
        extra_metadata=metadata if metadata else None
    )


def log_mode_switch(from_mode, to_mode, outcome=AccessOutcome.SUCCESS):
    """
    Log GENERAL_ADMIN mode switching
    
    Args:
        from_mode: Previous mode ('general_admin' or 'project_manager')
        to_mode: New mode ('general_admin' or 'project_manager')
        outcome: AccessOutcome enum value
    """
    log_access(
        action_type=AccessActionType.PAGE_ACCESS,
        target_type='mode_switch',
        target_name=f"Mode switch: {from_mode} -> {to_mode}",
        outcome=outcome,
        extra_metadata={
            'from_mode': from_mode,
            'to_mode': to_mode,
            'action': 'mode_switch'
        }
    )


def get_audit_logs(user_id=None, action_type=None, start_date=None, end_date=None, limit=100):
    """
    Query access audit logs with filters
    
    Args:
        user_id: Filter by user ID
        action_type: Filter by AccessActionType
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        limit: Maximum number of logs to return
        
    Returns:
        List of AccessAuditLog objects
    """
    query = AccessAuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if action_type:
        query = query.filter_by(action_type=action_type)
    
    if start_date:
        query = query.filter(AccessAuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AccessAuditLog.created_at <= end_date)
    
    query = query.order_by(AccessAuditLog.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_user_recent_activity(user_id, limit=50):
    """
    Get recent activity for a specific user
    
    Args:
        user_id: User ID
        limit: Maximum number of logs
        
    Returns:
        List of AccessAuditLog objects
    """
    return get_audit_logs(user_id=user_id, limit=limit)


def get_admin_mode_switches(user_id=None, limit=50):
    """
    Get mode switch history for GENERAL_ADMIN users
    
    Args:
        user_id: Optional user ID filter
        limit: Maximum number of logs
        
    Returns:
        List of AccessAuditLog objects representing mode switches
    """
    query = AccessAuditLog.query.filter_by(target_type='mode_switch')
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    query = query.order_by(AccessAuditLog.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()
