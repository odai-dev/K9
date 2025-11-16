"""
API endpoints for breeding deworming logs management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_
from datetime import datetime
from k9.models.models import db, DewormingLog, Project, Dog, Employee, UserRole
from k9.utils.permission_decorators import require_sub_permission
from k9.utils.utils import get_user_assigned_projects

bp = Blueprint('api_deworming', __name__)

@bp.route('/api/breeding/deworming', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'جرعة الديدان', 'CREATE')
def create_deworming_log():
    """Create new deworming log"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Handle optional project_id (allow "No Project" entries)
        project_id = data.get('project_id')
        if not project_id or project_id == '' or project_id == 'null':
            project_id = None
            data['project_id'] = None
            print('Deworming log created without project assignment')
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if data.get('project_id'):  # Only check if project is assigned
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
        # Set project_id (can be None for "No Project" entries)
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
@require_sub_permission('Breeding', 'جرعة الديدان', 'EDIT')
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

@bp.route('/api/breeding/deworming/<log_id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'جرعة الديدان', 'DELETE')
def delete_deworming_log(log_id):
    """Delete deworming log"""
    try:
        deworming_log = DewormingLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if deworming_log.project not in assigned_projects:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        db.session.delete(deworming_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف سجل جرعة الديدان بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/breeding/deworming/list', methods=['GET'])
@login_required
@require_sub_permission('Breeding', 'جرعة الديدان', 'VIEW')
def api_deworming_list():
    """Get paginated list of deworming logs with KPIs"""
    try:
        from sqlalchemy import func
        
        # Query parameters
        project_id = request.args.get('project_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dog_id = request.args.get('dog_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Base query with necessary joins (left join for project since it can be null)
        query = DewormingLog.query.join(Dog).outerjoin(Project)
        
        # Apply project scoping for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            # Include both assigned projects AND records without project assignment
            from sqlalchemy import or_
            query = query.filter(or_(
                DewormingLog.project_id.in_(assigned_project_ids),
                DewormingLog.project_id.is_(None)
            ))
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(DewormingLog.project_id.is_(None))
            else:
                query = query.filter(DewormingLog.project_id == project_id)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(DewormingLog.date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(DewormingLog.date <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        if dog_id:
            query = query.filter(DewormingLog.dog_id == dog_id)
        
        # Order by date and time (newest first)
        query = query.order_by(DewormingLog.date.desc(), DewormingLog.time.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items
        
        # Build items list with joined data
        items_data = []
        for log in items:
            specialist_name = log.specialist_employee.name if log.specialist_employee else None
            
            item_data = {
                'id': str(log.id),
                'project_id': str(log.project_id) if log.project_id else None,
                'project_name': log.project.name if log.project else 'بدون مشروع',
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M'),
                'dog_id': str(log.dog_id),
                'dog_name': log.dog.name,
                'dog_code': log.dog.code,
                'specialist_employee_id': str(log.specialist_employee_id) if log.specialist_employee_id else None,
                'specialist_name': specialist_name,
                'dog_weight_kg': log.dog_weight_kg,
                'product_name': log.product_name,
                'active_ingredient': log.active_ingredient,
                'standard_dose_mg_per_kg': log.standard_dose_mg_per_kg,
                'calculated_dose_mg': log.calculated_dose_mg,
                'administered_amount': log.administered_amount,
                'amount_unit': log.amount_unit,
                'administration_route': log.administration_route,
                'batch_number': log.batch_number,
                'expiry_date': log.expiry_date.strftime('%Y-%m-%d') if log.expiry_date else None,
                'adverse_reaction': log.adverse_reaction,
                'next_due_date': log.next_due_date.strftime('%Y-%m-%d') if log.next_due_date else None,
                'notes': log.notes
            }
            items_data.append(item_data)
        
        # Calculate KPIs
        total_query = DewormingLog.query
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            # Include both assigned projects AND records without project assignment
            from sqlalchemy import or_
            total_query = total_query.filter(or_(
                DewormingLog.project_id.in_(assigned_project_ids),
                DewormingLog.project_id.is_(None)
            ))
        
        # Apply same filters to KPI calculations
        if project_id:
            total_query = total_query.filter(DewormingLog.project_id == project_id)
        if date_from:
            total_query = total_query.filter(DewormingLog.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            total_query = total_query.filter(DewormingLog.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if dog_id:
            total_query = total_query.filter(DewormingLog.dog_id == dog_id)
        
        total_count = total_query.count()
        avg_mg_per_kg = total_query.filter(DewormingLog.standard_dose_mg_per_kg.isnot(None)).with_entities(func.avg(DewormingLog.standard_dose_mg_per_kg)).scalar()
        with_next_due = total_query.filter(DewormingLog.next_due_date.isnot(None)).count()
        
        # Route distribution
        route_distribution = {}
        route_counts = total_query.filter(DewormingLog.administration_route.isnot(None)).with_entities(
            DewormingLog.administration_route, func.count(DewormingLog.administration_route)
        ).group_by(DewormingLog.administration_route).all()
        
        for route, count in route_counts:
            route_distribution[route] = count
        
        kpis = {
            'total': total_count,
            'avg_mg_per_kg': round(float(avg_mg_per_kg), 2) if avg_mg_per_kg else 0,
            'with_next_due': with_next_due,
            'by_route': route_distribution
        }
        
        return jsonify({
            'items': items_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            },
            'kpis': kpis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500