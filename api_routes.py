from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from models import (
    db, Project, Employee, Dog, UserRole, AttendanceStatus
)
from utils import get_user_permissions
import uuid
from attendance_service import (
    resolve_project_control, get_attendance_day, set_attendance_global,
    get_globally_editable_employees, get_attendance_stats, ProjectOwnershipError
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

# UNIFIED GLOBAL ATTENDANCE API ENDPOINTS
# Only accessible to GENERAL_ADMIN users

@api_bp.route('/attendance', methods=['GET'])
@login_required
def get_attendance():
    """Get globally editable employees for a specific date with attendance status"""
    # Only GENERAL_ADMIN can access unified attendance
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'error': 'Unauthorized. Only General Admin can access unified attendance.'}), 403
    
    try:
        # Get parameters
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Validate date format
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Validate status filter
        if status_filter and status_filter not in [s.value for s in AttendanceStatus]:
            return jsonify({'error': 'Invalid status filter'}), 400
            
        # Get globally editable employees
        result = get_globally_editable_employees(
            target_date=parsed_date,
            search=search if search else None,
            status_filter=status_filter if status_filter else None,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'date': target_date,
            'employees': result['employees'],
            'pagination': {
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_attendance API: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/attendance/<employee_id>', methods=['PUT'])
@login_required
def update_attendance(employee_id):
    """Update attendance for a specific employee on a specific date"""
    # Only GENERAL_ADMIN can access unified attendance
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'error': 'Unauthorized. Only General Admin can access unified attendance.'}), 403
    
    try:
        # Get parameters
        target_date = request.args.get('date')
        if not target_date:
            return jsonify({'error': 'Date parameter is required'}), 400
            
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
            
        status = data.get('status')
        note = data.get('note', '').strip()
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
            
        # Validate status
        try:
            status_enum = AttendanceStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in AttendanceStatus]
            return jsonify({'error': f'Invalid status. Valid options: {valid_statuses}'}), 400
        
        # Validate employee exists
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        if not employee.is_active:
            return jsonify({'error': 'Employee is not active'}), 400
        
        # Set attendance (this will check project ownership)
        attendance = set_attendance_global(
            employee_id=employee_id,
            target_date=parsed_date,
            status=status_enum,
            note=note if note else None
        )
        
        return jsonify({
            'success': True,
            'message': 'Attendance updated successfully',
            'employee': {
                'id': str(employee.id),
                'name': employee.name,
                'employee_id': employee.employee_id
            },
            'attendance': {
                'date': target_date,
                'status': attendance.status.value,
                'note': attendance.note
            }
        })
        
    except ProjectOwnershipError as e:
        return jsonify({
            'error': str(e)
        }), 409
        
    except Exception as e:
        current_app.logger.error(f"Error in update_attendance API: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/attendance/stats', methods=['GET'])
@login_required
def get_attendance_statistics():
    """Get attendance statistics for globally editable employees on a specific date"""
    # Only GENERAL_ADMIN can access unified attendance
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'error': 'Unauthorized. Only General Admin can access unified attendance.'}), 403
    
    try:
        # Get parameters
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validate date format
        try:
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Get statistics
        stats = get_attendance_stats(parsed_date)
        
        return jsonify({
            'success': True,
            'date': target_date,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_attendance_statistics API: {e}")
        return jsonify({'error': 'Internal server error'}), 500