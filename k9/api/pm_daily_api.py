"""
PM Daily Report API Endpoints
JSON API for running reports and exporting PDFs
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import logging

from k9.services.pm_daily_services import get_pm_daily
from k9.utils.pm_daily_exporters import export_pm_daily_pdf
from k9.utils.permission_decorators import require_permission
from k9.models.models import Project

# Create blueprint
bp = Blueprint('reports_attendance_pm_daily_api', __name__)

logger = logging.getLogger(__name__)


@bp.route('/run/pm-daily', methods=['POST'])
@login_required
@require_permission('reports:attendance:pm_daily:view')
def run_pm_daily():
    """
    Run PM Daily Report and return JSON data
    
    Expected JSON body:
    {
        "project_id": "<uuid>",
        "date": "YYYY-MM-DD"
    }
    
    Returns:
    JSON response with PM daily report data following the contract
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        
        project_id = data.get('project_id')
        date_str = data.get('date')
        
        # Validate inputs
        if not project_id or not date_str:
            return jsonify({"error": "project_id and date are required"}), 400
        
        # Get report data
        result = get_pm_daily(project_id, date_str, current_user)
        
        logger.info(f"PM Daily report generated for project {project_id} date {date_str} by user {current_user.username}")
        
        return jsonify(result)
        
    except ValueError as e:
        logger.warning(f"Invalid input for PM Daily report: {e}")
        return jsonify({"error": str(e)}), 400
        
    except PermissionError as e:
        logger.warning(f"Permission denied for PM Daily report: {e}")
        return jsonify({"error": "Permission denied"}), 403
        
    except Exception as e:
        logger.error(f"Error generating PM Daily report: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route('/export/pdf/pm-daily', methods=['POST'])
@login_required
@require_permission('reports:attendance:pm_daily:export')
def export_pm_daily_pdf_api():
    """
    Export PM Daily Report to PDF
    
    Expected JSON body:
    {
        "project_id": "<uuid>",
        "date": "YYYY-MM-DD"
    }
    
    Returns:
    JSON response with PDF file path:
    {
        "path": "uploads/reports/2025/08/pm_daily_{project_code}_{YYYYMMDD}.pdf"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
        
        project_id = data.get('project_id')
        date_str = data.get('date')
        
        # Validate inputs
        if not project_id or not date_str:
            return jsonify({"error": "project_id and date are required"}), 400
        
        # Get project code for filename
        project = Project.query.get(project_id)
        project_code = project.code if project and hasattr(project, 'code') else project_id[:8]
        
        # Export PDF
        result = export_pm_daily_pdf(project_id, date_str, current_user, project_code)
        
        logger.info(f"PM Daily PDF exported for project {project_id} date {date_str} by user {current_user.username}")
        
        return jsonify(result)
        
    except ValueError as e:
        logger.warning(f"Invalid input for PM Daily PDF export: {e}")
        return jsonify({"error": str(e)}), 400
        
    except PermissionError as e:
        logger.warning(f"Permission denied for PM Daily PDF export: {e}")
        return jsonify({"error": "Permission denied"}), 403
        
    except Exception as e:
        logger.error(f"Error exporting PM Daily PDF: {e}")
        return jsonify({"error": "Internal server error"}), 500