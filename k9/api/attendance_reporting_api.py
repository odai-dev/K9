"""
API routes for attendance reporting
Handles JSON API endpoints for running and exporting daily sheet reports
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
import os

from k9.services.attendance_reporting_services import get_daily_sheet, validate_project_date_access
from k9.utils.attendance_reporting_exporters import export_daily_attendance_pdf
from k9.utils.attendance_reporting_constants import PERMISSION_KEYS
from k9.utils.permission_decorators import require_sub_permission
from k9.models.models import PermissionType
from k9.utils.utils import log_audit
from k9.models.models import AuditAction

# Create blueprint
bp = Blueprint('reports_attendance_api', __name__)


@bp.route('/run/daily-sheet', methods=['POST'])
@login_required
@require_sub_permission("Reports", "Attendance Daily Sheet", PermissionType.VIEW)
def run_daily_sheet():
    """
    API endpoint to run daily sheet report
    
    Expected JSON body:
    {
        "project_id": "uuid-string",
        "date": "YYYY-MM-DD"
    }
    
    Returns JSON contract as specified in requirements
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        project_id = data.get('project_id')
        date_str = data.get('date')
        
        # Validate required parameters
        if not project_id:
            return jsonify({"error": "project_id is required"}), 400
        
        if not date_str:
            return jsonify({"error": "date is required"}), 400
        
        # Parse and validate date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400
        
        # Validate user access to project and date
        if not validate_project_date_access(project_id, target_date, current_user):
            return jsonify({"error": "Access denied for this project"}), 403
        
        # Get daily sheet data
        result = get_daily_sheet(project_id, target_date, current_user)
        
        # Log audit trail
        log_audit(
            user_id=current_user.id,
            action=AuditAction.EXPORT,
            target_type='AttendanceReport',
            target_id=project_id,
            description=f"Generated daily attendance sheet for project {project_id} on {date_str}",
            old_values={},
            new_values={"report_type": "daily_sheet", "date": date_str}
        )
        
        return jsonify(result), 200
        
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error in run_daily_sheet: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route('/export/pdf/daily-sheet', methods=['POST'])
@login_required
@require_sub_permission("Reports", "Attendance Daily Sheet", PermissionType.EXPORT)
def export_pdf_daily_sheet():
    """
    API endpoint to export daily sheet report as PDF
    
    Expected JSON body:
    {
        "project_id": "uuid-string", 
        "date": "YYYY-MM-DD"
    }
    
    Returns:
    {
        "path": "uploads/reports/YYYY/MM/daily_sheet_PROJECT_YYYYMMDD.pdf"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        project_id = data.get('project_id')
        date_str = data.get('date')
        
        # Validate required parameters
        if not project_id:
            return jsonify({"error": "project_id is required"}), 400
        
        if not date_str:
            return jsonify({"error": "date is required"}), 400
        
        # Parse and validate date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400
        
        # Validate user access to project and date
        if not validate_project_date_access(project_id, target_date, current_user):
            return jsonify({"error": "Access denied for this project"}), 403
        
        # Get daily sheet data first
        sheet_data = get_daily_sheet(project_id, target_date, current_user)
        
        # Export to PDF
        pdf_path = export_daily_attendance_pdf(sheet_data)
        
        # Verify file was created
        if not os.path.exists(pdf_path):
            return jsonify({"error": "Failed to generate PDF file"}), 500
        
        # Log audit trail
        log_audit(
            user_id=current_user.id,
            action=AuditAction.EXPORT,
            target_type='AttendanceReport',
            target_id=project_id,
            description=f"Exported daily attendance sheet PDF for project {project_id} on {date_str}",
            old_values={},
            new_values={"report_type": "daily_sheet_pdf", "date": date_str, "file_path": pdf_path}
        )
        
        return jsonify({"path": pdf_path}), 200
        
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error in export_pdf_daily_sheet: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route('/projects', methods=['GET'])
@login_required
@require_sub_permission("Reports", "Attendance Daily Sheet", PermissionType.VIEW)
def get_accessible_projects():
    """
    API endpoint to get list of projects accessible to current user for attendance reporting
    
    Returns:
    {
        "projects": [
            {
                "id": "uuid-string",
                "name": "Project Name",
                "code": "PROJECT_CODE"
            }
        ]
    }
    """
    try:
        from k9.services.attendance_reporting_services import get_user_accessible_projects
        
        projects = get_user_accessible_projects(current_user)
        
        return jsonify({"projects": projects}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_accessible_projects: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Error handlers for the blueprint
@bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400


@bp.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Access denied"}), 403


@bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500