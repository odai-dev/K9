"""
API endpoints for breeding excretion logs management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_, or_
from datetime import datetime, date
from k9.models.models import db, ExcretionLog, Project, Dog, Employee, UserRole
from k9.utils.permission_decorators import require_sub_permission
from k9.utils.utils import get_user_assigned_projects

bp = Blueprint('api_excretion', __name__)

@bp.route('/api/breeding/excretion/list')
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', 'VIEW')
def list_excretion_logs():
    """List excretion logs with filters and KPIs"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        project_id = request.args.get('project_id')
        dog_id = request.args.get('dog_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Base query with optional joins (since project_id is nullable)
        query = ExcretionLog.query.outerjoin(Project).join(Dog, ExcretionLog.dog_id == Dog.id)
        
        # Apply user access restrictions
        if current_user.role == UserRole.GENERAL_ADMIN:
            # Admin can see all logs
            pass
        else:
            # PROJECT_MANAGER can see logs from assigned projects + logs without projects
            assigned_projects = get_user_assigned_projects(current_user)
            if not assigned_projects:
                # If no assigned projects, only show logs without projects
                query = query.filter(ExcretionLog.project_id.is_(None))
            else:
                # Show logs from assigned projects OR logs without projects
                project_ids = [p.id for p in assigned_projects]
                query = query.filter(
                    or_(
                        ExcretionLog.project_id.in_(project_ids),
                        ExcretionLog.project_id.is_(None)
                    )
                )
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(ExcretionLog.project_id.is_(None))
            else:
                query = query.filter(ExcretionLog.project_id == project_id)
        
        if dog_id:
            query = query.filter(ExcretionLog.dog_id == dog_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(ExcretionLog.date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(ExcretionLog.date <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        
        # Calculate KPIs on filtered data
        kpis = calculate_excretion_kpis(query)
        
        # Order by date and time descending
        query = query.order_by(ExcretionLog.date.desc(), ExcretionLog.time.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format items for response
        items = []
        for log in pagination.items:
            items.append({
                'id': str(log.id),
                'date': log.date.isoformat(),
                'time': log.time.strftime('%H:%M'),
                'project_name': log.project.name if log.project else None,
                'project_id': str(log.project_id) if log.project_id else None,
                'dog_name': log.dog.name,
                'dog_code': log.dog.code,
                'dog_id': str(log.dog_id),
                'recorder_employee_name': log.recorder_employee.name if log.recorder_employee else None,
                'stool_color': log.stool_color,
                'stool_consistency': log.stool_consistency,
                'stool_content': log.stool_content,
                'constipation': log.constipation,
                'stool_place': log.stool_place,
                'stool_notes': log.stool_notes,
                'urine_color': log.urine_color,
                'urine_notes': log.urine_notes,
                'vomit_color': log.vomit_color,
                'vomit_count': log.vomit_count,
                'vomit_notes': log.vomit_notes,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return jsonify({
            'items': items,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            },
            'kpis': kpis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/breeding/excretion', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', 'CREATE')
def create_excretion_log():
    """Create new excretion log"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if data.get('project_id'):
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(data['project_id']) not in project_ids:
                    return jsonify({'error': 'Access denied to this project'}), 403
        
        # Verify project and dog exist with better error handling
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
        
        # Validate at least one observation
        has_stool = any([
            data.get('stool_color'), data.get('stool_consistency'), data.get('stool_content'),
            data.get('constipation'), data.get('stool_place'), data.get('stool_notes')
        ])
        has_urine = any([data.get('urine_color'), data.get('urine_notes')])
        has_vomit = any([data.get('vomit_color'), data.get('vomit_count'), data.get('vomit_notes')])
        
        if not (has_stool or has_urine or has_vomit):
            return jsonify({'error': 'At least one observation (stool, urine, or vomit) must be provided'}), 400
        
        # Check for duplicate entry
        project_id_value = data.get('project_id') if data.get('project_id') else None
        existing = ExcretionLog.query.filter(
            and_(
                ExcretionLog.project_id == project_id_value,
                ExcretionLog.dog_id == data['dog_id'],
                ExcretionLog.date == log_date,
                ExcretionLog.time == log_time
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'An excretion log already exists for this dog, project, date, and time'}), 400
        
        # Create new log with comprehensive safety checks
        excretion_log = ExcretionLog()
        # CRITICAL: Ensure project_id is properly handled for nullable constraint
        project_id_value = data.get('project_id')
        if project_id_value is None or project_id_value == '' or project_id_value == 'null':
            excretion_log.project_id = None
        else:
            excretion_log.project_id = project_id_value
        excretion_log.dog_id = data['dog_id']
        excretion_log.recorder_employee_id = data.get('recorder_employee_id')
        excretion_log.date = log_date
        excretion_log.time = log_time
        excretion_log.stool_color = data.get('stool_color')
        excretion_log.stool_consistency = data.get('stool_consistency')
        excretion_log.stool_content = data.get('stool_content')
        excretion_log.constipation = data.get('constipation', False)
        excretion_log.stool_place = data.get('stool_place')
        excretion_log.stool_notes = data.get('stool_notes')
        excretion_log.urine_color = data.get('urine_color')
        excretion_log.urine_notes = data.get('urine_notes')
        excretion_log.vomit_color = data.get('vomit_color')
        excretion_log.vomit_count = data.get('vomit_count')
        excretion_log.vomit_notes = data.get('vomit_notes')
        excretion_log.created_by_user_id = current_user.id
        
        db.session.add(excretion_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء سجل الإفراز بنجاح',
            'id': str(excretion_log.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        # Log detailed error for debugging
        print(f"ERROR creating excretion log: {error_msg}")
        print(f"Data received: {data}")
        return jsonify({'error': 'حدث خطأ في حفظ سجل الإفراز'}), 500


@bp.route('/api/breeding/excretion/<log_id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', 'EDIT')
def update_excretion_log(log_id):
    """Update existing excretion log"""
    try:
        excretion_log = ExcretionLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if excretion_log.project not in assigned_projects:
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
        existing = ExcretionLog.query.filter(
            and_(
                ExcretionLog.project_id == project_id_value,
                ExcretionLog.dog_id == data['dog_id'],
                ExcretionLog.date == log_date,
                ExcretionLog.time == log_time,
                ExcretionLog.id != log_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'An excretion log already exists for this dog, project, date, and time'}), 400
        
        # Update log
        excretion_log.project_id = data.get('project_id')
        excretion_log.dog_id = data['dog_id']
        excretion_log.recorder_employee_id = data.get('recorder_employee_id')
        excretion_log.date = log_date
        excretion_log.time = log_time
        excretion_log.stool_color = data.get('stool_color')
        excretion_log.stool_consistency = data.get('stool_consistency')
        excretion_log.stool_content = data.get('stool_content')
        excretion_log.constipation = data.get('constipation', False)
        excretion_log.stool_place = data.get('stool_place')
        excretion_log.stool_notes = data.get('stool_notes')
        excretion_log.urine_color = data.get('urine_color')
        excretion_log.urine_notes = data.get('urine_notes')
        excretion_log.vomit_color = data.get('vomit_color')
        excretion_log.vomit_count = data.get('vomit_count')
        excretion_log.vomit_notes = data.get('vomit_notes')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث سجل الإفراز بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/breeding/excretion/<log_id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', 'DELETE')
def delete_excretion_log(log_id):
    """Delete excretion log"""
    try:
        excretion_log = ExcretionLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if excretion_log.project not in assigned_projects:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        dog_name = excretion_log.dog.name if excretion_log.dog else 'Unknown'
        
        db.session.delete(excretion_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم حذف سجل الإفراز للكلب {dog_name} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def calculate_excretion_kpis(query):
    """Calculate KPIs for excretion logs"""
    try:
        # Basic counts
        total = query.count()
        
        # Stool KPIs
        constipation_count = query.filter(ExcretionLog.constipation == True).count()
        abnormal_consistency_count = query.filter(
            and_(
                ExcretionLog.stool_consistency.isnot(None),
                or_(
                    ExcretionLog.stool_consistency.like('%سائل%'),
                    ExcretionLog.stool_consistency.like('%صلب%'),
                    ExcretionLog.stool_consistency.like('%دموي%')
                )
            )
        ).count()
        
        # Urine KPIs
        abnormal_urine_count = query.filter(
            and_(
                ExcretionLog.urine_color.isnot(None),
                or_(
                    ExcretionLog.urine_color.like('%بني%'),
                    ExcretionLog.urine_color.like('%دموي%'),
                    ExcretionLog.urine_color.like('%وردي%')
                )
            )
        ).count()
        
        # Vomit KPIs
        vomit_events = query.filter(
            or_(
                ExcretionLog.vomit_color.isnot(None),
                ExcretionLog.vomit_count > 0,
                ExcretionLog.vomit_notes.isnot(None)
            )
        ).count()
        
        return {
            'total': total,
            'stool': {
                'constipation': constipation_count,
                'abnormal_consistency': abnormal_consistency_count
            },
            'urine': {
                'abnormal_color': abnormal_urine_count
            },
            'vomit': {
                'total_events': vomit_events
            }
        }
        
    except Exception as e:
        print(f"Error calculating KPIs: {e}")
        return {
            'total': 0,
            'stool': {
                'constipation': 0,
                'abnormal_consistency': 0
            },
            'urine': {
                'abnormal_color': 0
            },
            'vomit': {
                'total_events': 0
            }
        }