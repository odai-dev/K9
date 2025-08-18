"""
Unified Attendance Matrix API Routes
RESTful API for unified attendance matrix operations
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import logging

from functools import wraps
from flask import abort
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

from unified_services import get_unified_matrix
from unified_exporters import export_pdf, export_excel, export_csv

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('reports_attendance_unified_api', __name__)


@bp.route('/run/unified', methods=['POST'])
@login_required
@require_perm('reports:attendance:unified:view')
def run_unified_matrix():
    """
    Run unified attendance matrix report
    POST /api/reports/attendance/run/unified
    """
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON payload required'}), 400
        
        # Validate required fields
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate date format
        try:
            datetime.strptime(data['date_from'], '%Y-%m-%d')
            datetime.strptime(data['date_to'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Set defaults for optional fields
        filters = {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'employee_ids': data.get('employee_ids', []),
            'project_ids': data.get('project_ids', []),
            'shift_ids': data.get('shift_ids', []),
            'include_dogs': data.get('include_dogs', False),
            'status_in': data.get('status_in', []),
            'page': data.get('page', 1),
            'per_page': min(data.get('per_page', 50), 100)  # Cap at 100
        }
        
        # Get matrix data
        result = get_unified_matrix(filters, current_user)
        
        logger.info(f"Unified matrix generated for user {current_user.username} "
                   f"from {filters['date_from']} to {filters['date_to']}")
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating unified matrix: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/export/pdf/unified', methods=['POST'])
@login_required
@require_perm('reports:attendance:unified:export')
def export_pdf_unified():
    """
    Export unified attendance matrix to PDF
    POST /api/reports/attendance/export/pdf/unified
    """
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON payload required'}), 400
        
        # Validate required fields
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Set defaults for optional fields
        filters = {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'employee_ids': data.get('employee_ids', []),
            'project_ids': data.get('project_ids', []),
            'shift_ids': data.get('shift_ids', []),
            'include_dogs': data.get('include_dogs', False),
            'status_in': data.get('status_in', []),
            'page': 1,  # Export all pages
            'per_page': 1000  # Large number to get all employees
        }
        
        # Generate PDF
        file_path = export_pdf(filters, current_user)
        
        logger.info(f"Unified matrix PDF exported for user {current_user.username}")
        
        return jsonify({'path': file_path}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error exporting unified matrix PDF: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/export/excel/unified', methods=['POST'])
@login_required
@require_perm('reports:attendance:unified:export')
def export_excel_unified():
    """
    Export unified attendance matrix to Excel
    POST /api/reports/attendance/export/excel/unified
    """
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON payload required'}), 400
        
        # Validate required fields
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Set defaults for optional fields
        filters = {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'employee_ids': data.get('employee_ids', []),
            'project_ids': data.get('project_ids', []),
            'shift_ids': data.get('shift_ids', []),
            'include_dogs': data.get('include_dogs', False),
            'status_in': data.get('status_in', []),
            'page': 1,  # Export all pages
            'per_page': 1000  # Large number to get all employees
        }
        
        # Generate Excel
        file_path = export_excel(filters, current_user)
        
        logger.info(f"Unified matrix Excel exported for user {current_user.username}")
        
        return jsonify({'path': file_path}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error exporting unified matrix Excel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/export/csv/unified', methods=['POST'])
@login_required
@require_perm('reports:attendance:unified:export')
def export_csv_unified():
    """
    Export unified attendance matrix to CSV
    POST /api/reports/attendance/export/csv/unified
    """
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON payload required'}), 400
        
        # Validate required fields
        required_fields = ['date_from', 'date_to']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Set defaults for optional fields
        filters = {
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'employee_ids': data.get('employee_ids', []),
            'project_ids': data.get('project_ids', []),
            'shift_ids': data.get('shift_ids', []),
            'include_dogs': data.get('include_dogs', False),
            'status_in': data.get('status_in', []),
            'page': 1,  # Export all pages
            'per_page': 1000  # Large number to get all employees
        }
        
        # Generate CSV
        file_path = export_csv(filters, current_user)
        
        logger.info(f"Unified matrix CSV exported for user {current_user.username}")
        
        return jsonify({'path': file_path}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error exporting unified matrix CSV: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500