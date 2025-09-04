"""
API endpoints for breeding deworming logs management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_
from datetime import datetime
from models import db, DewormingLog, Project, Dog, Employee, UserRole
from permission_decorators import require_sub_permission
from utils import get_user_assigned_projects

bp = Blueprint('api_deworming', __name__)

@bp.route('/api/breeding/deworming', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'عرض الفحص الظاهري اليومي', 'CREATE')
def create_deworming_log():
    """Create new deworming log"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate required project_id field
        if not data.get('project_id') or data.get('project_id') == '' or data.get('project_id') == 'null':
            if current_user.role == UserRole.GENERAL_ADMIN:
                default_project = Project.query.first()
            else:
                assigned_projects = get_user_assigned_projects(current_user)
                default_project = assigned_projects[0] if assigned_projects else None
            
            if not default_project:
                return jsonify({'error': 'لا يوجد مشروع متاح. يجب إنشاء مشروع أولاً أو تعيين المستخدم لمشروع'}), 400
            
            data['project_id'] = str(default_project.id)
            print(f'Auto-assigned project: {default_project.id} to deworming log')
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if data.get('project_id'):
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(data['project_id']) not in project_ids:
                    return jsonify({'error': 'Access denied to this project'}), 403
        
        # Verify project and dog exist
        if data.get('project_id'):
            try:
                project = Project.query.get(data['project_id'])
                if not project:
                    return jsonify({'error': 'المشروع المحدد غير موجود'}), 404
            except Exception as e:
                return jsonify({'error': 'معرف المشروع غير صالح'}), 400
        
        try:
            dog = Dog.query.get(data['dog_id'])
            if not dog:
                return jsonify({'error': 'الكلب المحدد غير موجود'}), 404
        except Exception as e:
            return jsonify({'error': 'معرف الكلب غير صالح - يرجى إختيار كلب من القائمة'}), 400
        
        # Parse date and time
        try:
            log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            log_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
        
        # Check for duplicate entry
        project_id_value = data.get('project_id') if data.get('project_id') else None
        existing = DewormingLog.query.filter(
            and_(
                DewormingLog.project_id == project_id_value,
                DewormingLog.dog_id == data['dog_id'],
                DewormingLog.date == log_date,
                DewormingLog.time == log_time
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'A deworming log already exists for this dog, project, date, and time'}), 400
        
        # Create new deworming log
        deworming_log = DewormingLog()
        # Ensure project_id is not None (required field)
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'error': 'معرف المشروع مطلوب'}), 400
        deworming_log.project_id = project_id
        deworming_log.dog_id = data['dog_id']
        deworming_log.specialist_employee_id = data.get('specialist_employee_id')
        deworming_log.date = log_date
        deworming_log.time = log_time
        deworming_log.dog_weight_kg = float(data['dog_weight_kg']) if data.get('dog_weight_kg') else None
        deworming_log.product_name = data.get('product_name')
        deworming_log.active_ingredient = data.get('active_ingredient')
        deworming_log.standard_dose_mg_per_kg = float(data['standard_dose_mg_per_kg']) if data.get('standard_dose_mg_per_kg') else None
        deworming_log.calculated_dose_mg = float(data['calculated_dose_mg']) if data.get('calculated_dose_mg') else None
        deworming_log.administered_amount = float(data['administered_amount']) if data.get('administered_amount') else None
        deworming_log.amount_unit = data.get('amount_unit')
        deworming_log.administration_route = data.get('administration_route')
        deworming_log.batch_number = data.get('batch_number')
        deworming_log.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None
        deworming_log.adverse_reaction = data.get('adverse_reaction')
        deworming_log.next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date() if data.get('next_due_date') else None
        deworming_log.notes = data.get('notes')
        deworming_log.created_by_user_id = current_user.id
        deworming_log.created_at = datetime.utcnow()
        deworming_log.updated_at = datetime.utcnow()
        
        db.session.add(deworming_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إضافة سجل جرعة الديدان بنجاح',
            'id': str(deworming_log.id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/breeding/deworming/<log_id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'عرض الفحص الظاهري اليومي', 'EDIT')
def update_deworming_log(log_id):
    """Update existing deworming log"""
    try:
        deworming_log = DewormingLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if deworming_log.project not in assigned_projects:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse date and time
        try:
            log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            log_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
        
        # Check for duplicate entry (excluding current record)
        project_id_value = data.get('project_id') if data.get('project_id') else None
        existing = DewormingLog.query.filter(
            and_(
                DewormingLog.project_id == project_id_value,
                DewormingLog.dog_id == data['dog_id'],
                DewormingLog.date == log_date,
                DewormingLog.time == log_time,
                DewormingLog.id != log_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'A deworming log already exists for this dog, project, date, and time'}), 400
        
        # Update log
        deworming_log.project_id = data.get('project_id')
        deworming_log.dog_id = data['dog_id']
        deworming_log.specialist_employee_id = data.get('specialist_employee_id')
        deworming_log.date = log_date
        deworming_log.time = log_time
        deworming_log.dog_weight_kg = float(data['dog_weight_kg']) if data.get('dog_weight_kg') else None
        deworming_log.product_name = data.get('product_name')
        deworming_log.active_ingredient = data.get('active_ingredient')
        deworming_log.standard_dose_mg_per_kg = float(data['standard_dose_mg_per_kg']) if data.get('standard_dose_mg_per_kg') else None
        deworming_log.calculated_dose_mg = float(data['calculated_dose_mg']) if data.get('calculated_dose_mg') else None
        deworming_log.administered_amount = float(data['administered_amount']) if data.get('administered_amount') else None
        deworming_log.amount_unit = data.get('amount_unit')
        deworming_log.administration_route = data.get('administration_route')
        deworming_log.batch_number = data.get('batch_number')
        deworming_log.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None
        deworming_log.adverse_reaction = data.get('adverse_reaction')
        deworming_log.next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date() if data.get('next_due_date') else None
        deworming_log.notes = data.get('notes')
        deworming_log.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث سجل جرعة الديدان بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500