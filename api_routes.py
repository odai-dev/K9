from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from models import (
    db, Project, Employee, Dog, UserRole, AttendanceStatus,
    FeedingLog, PrepMethod, BodyConditionScale, DailyCheckupLog, PermissionType, DogStatus
)
from utils import get_user_permissions, get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
from permission_decorators import require_sub_permission
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
        note = data.get('note', '')
        if note:
            note = note.strip()
        
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


# =============================================
# BREEDING FEEDING LOG API ENDPOINTS
# =============================================

from permission_utils import has_permission
from utils import get_user_assigned_projects, get_user_accessible_dogs
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func
import json

@api_bp.route('/breeding/feeding/log/list', methods=['GET'])
@login_required
def feeding_log_list():
    """Get feeding log entries with filters and pagination"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "VIEW"):
        return jsonify({'error': 'غير مصرح لك بعرض سجلات التغذية'}), 403
    
    try:
        # Get parameters
        project_id = request.args.get('project_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dog_id = request.args.get('dog_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Build base query with eager loading
        query = FeedingLog.query.options(
            joinedload(FeedingLog.project),
            joinedload(FeedingLog.dog),
            joinedload(FeedingLog.recorder_employee)
        )
        
        # Apply PROJECT_MANAGER scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if not project_ids:
                return jsonify({'items': [], 'pagination': {}, 'kpis': {}})
            query = query.filter(FeedingLog.project_id.in_(project_ids))
        
        # Apply filters
        if project_id:
            query = query.filter(FeedingLog.project_id == project_id)
        if date_from:
            query = query.filter(FeedingLog.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(FeedingLog.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if dog_id:
            query = query.filter(FeedingLog.dog_id == dog_id)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(FeedingLog.date.desc(), FeedingLog.time.desc())\
                    .offset((page - 1) * per_page)\
                    .limit(per_page)\
                    .all()
        
        # Calculate KPIs
        kpi_query = query.with_entities(
            func.count(FeedingLog.id).label('total'),
            func.sum(FeedingLog.grams).label('grams_sum'),
            func.sum(FeedingLog.water_ml).label('water_sum')
        ).first()
        
        # Count supplements
        supplements_count = 0
        for item in query.all():
            if item.supplements:
                supplements_count += len(item.supplements)
        
        # Serialize items
        items_data = []
        for item in items:
            items_data.append({
                'id': str(item.id),
                'project_id': str(item.project_id),
                'project_name': item.project.name if item.project else "",
                'date': item.date.isoformat(),
                'time': item.time.strftime('%H:%M'),
                'dog_id': str(item.dog_id),
                'dog_name': item.dog.name if item.dog else "",
                'dog_code': item.dog.code if item.dog else "",
                'recorder_employee_name': item.recorder_employee.name if item.recorder_employee else "",
                'meal_type_fresh': item.meal_type_fresh,
                'meal_type_dry': item.meal_type_dry,
                'meal_name': item.meal_name or "",
                'prep_method': item.prep_method.value if item.prep_method else "",
                'grams': item.grams or 0,
                'water_ml': item.water_ml or 0,
                'supplements': item.supplements or [],
                'body_condition': item.body_condition.value if item.body_condition else "",
                'notes': item.notes or "",
                'created_at': item.created_at.isoformat()
            })
        
        return jsonify({
            'items': items_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            },
            'kpis': {
                'total': kpi_query.total or 0,
                'grams_sum': int(kpi_query.grams_sum or 0),
                'water_sum': int(kpi_query.water_sum or 0),
                'supplements_count': supplements_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in feeding_log_list: {e}")
        return jsonify({'error': 'خطأ في استرجاع البيانات'}), 500

@api_bp.route('/breeding/feeding/log', methods=['POST'])
@login_required  
def feeding_log_create():
    """Create new feeding log entry"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "CREATE"):
        return jsonify({'error': 'غير مصرح لك بإنشاء سجلات التغذية'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'بيانات JSON مطلوبة'}), 400
        
        # Validate required fields
        required_fields = ['project_id', 'date', 'time', 'dog_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # Check PROJECT_MANAGER scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if data['project_id'] not in project_ids:
                return jsonify({'error': 'غير مصرح لك بالعمل على هذا المشروع'}), 403
        
        # Validate meal type (at least one must be True)
        if not data.get('meal_type_fresh', False) and not data.get('meal_type_dry', False):
            return jsonify({'error': 'يجب اختيار نوع وجبة واحد على الأقل'}), 400
        
        # Validate numeric fields
        grams = data.get('grams')
        if grams is not None and (not isinstance(grams, int) or grams < 0):
            return jsonify({'error': 'الكمية بالجرام يجب أن تكون رقم صحيح موجب'}), 400
            
        water_ml = data.get('water_ml')
        if water_ml is not None and (not isinstance(water_ml, int) or water_ml < 0):
            return jsonify({'error': 'ماء الشرب بالمللي يجب أن تكون رقم صحيح موجب'}), 400
        
        # Validate supplements format
        supplements = data.get('supplements', [])
        if supplements and not isinstance(supplements, list):
            return jsonify({'error': 'المكملات الغذائية يجب أن تكون قائمة'}), 400
        
        for supp in supplements:
            if not isinstance(supp, dict) or 'name' not in supp or 'qty' not in supp:
                return jsonify({'error': 'كل مكمل غذائي يجب أن يحتوي على اسم وكمية'}), 400
        
        # Normalize time format (add seconds if missing)
        time_str = data['time']
        if len(time_str.split(':')) == 2:
            time_str += ':00'
        
        # Parse and validate date/time
        try:
            parsed_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            parsed_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError as e:
            return jsonify({'error': f'تنسيق التاريخ أو الوقت غير صحيح: {str(e)}'}), 400
        
        # Validate enums
        prep_method = None
        if data.get('prep_method'):
            try:
                prep_method = PrepMethod(data['prep_method'])
            except ValueError:
                return jsonify({'error': 'طريقة التحضير غير صحيحة'}), 400
        
        body_condition = None
        if data.get('body_condition'):
            try:
                body_condition = BodyConditionScale(data['body_condition'])
            except ValueError:
                return jsonify({'error': 'كتلة الجسم غير صحيحة'}), 400
        
        # Create new feeding log entry
        feeding_log = FeedingLog(
            project_id=data['project_id'],
            date=parsed_date,
            time=parsed_time,
            dog_id=data['dog_id'],
            recorder_employee_id=data.get('recorder_employee_id'),
            meal_type_fresh=data.get('meal_type_fresh', False),
            meal_type_dry=data.get('meal_type_dry', False),
            meal_name=data.get('meal_name'),
            prep_method=prep_method,
            grams=grams,
            water_ml=water_ml,
            supplements=supplements if supplements else None,
            body_condition=body_condition,
            notes=data.get('notes'),
            created_by_user_id=current_user.id
        )
        
        db.session.add(feeding_log)
        db.session.commit()
        
        # Load relationships for response
        db.session.refresh(feeding_log)
        feeding_log = FeedingLog.query.options(
            joinedload(FeedingLog.project),
            joinedload(FeedingLog.dog)
        ).get(feeding_log.id)
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء سجل التغذية بنجاح',
            'id': str(feeding_log.id),
            'item': {
                'id': str(feeding_log.id),
                'project_name': feeding_log.project.name,
                'dog_name': feeding_log.dog.name,
                'date': feeding_log.date.isoformat(),
                'time': feeding_log.time.strftime('%H:%M'),
                'meal_type_fresh': feeding_log.meal_type_fresh,
                'meal_type_dry': feeding_log.meal_type_dry,
                'meal_name': feeding_log.meal_name or "",
                'prep_method': feeding_log.prep_method.value if feeding_log.prep_method else "",
                'grams': feeding_log.grams or 0,
                'water_ml': feeding_log.water_ml or 0,
                'supplements': feeding_log.supplements or [],
                'body_condition': feeding_log.body_condition.value if feeding_log.body_condition else "",
                'notes': feeding_log.notes or ""
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in feeding_log_create: {e}")
        return jsonify({'error': 'خطأ في إنشاء سجل التغذية'}), 500

@api_bp.route('/breeding/feeding/log/<log_id>', methods=['PUT'])
@login_required
def feeding_log_update(log_id):
    """Update feeding log entry"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "EDIT"):
        return jsonify({'error': 'غير مصرح لك بتعديل سجلات التغذية'}), 403
    
    try:
        feeding_log = FeedingLog.query.get_or_404(log_id)
        
        # Check PROJECT_MANAGER scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if feeding_log.project_id not in project_ids:
                return jsonify({'error': 'غير مصرح لك بتعديل هذا السجل'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'بيانات JSON مطلوبة'}), 400
        
        # Update fields (similar validation as create)
        # ... (implementation similar to create but updating existing record)
        
        feeding_log.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث سجل التغذية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in feeding_log_update: {e}")
        return jsonify({'error': 'خطأ في تحديث سجل التغذية'}), 500

@api_bp.route('/breeding/feeding/log/<log_id>', methods=['DELETE'])
@login_required
def feeding_log_delete(log_id):
    """Delete feeding log entry"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "DELETE"):
        return jsonify({'error': 'غير مصرح لك بحذف سجلات التغذية'}), 403
    
    try:
        feeding_log = FeedingLog.query.get_or_404(log_id)
        
        # Check PROJECT_MANAGER scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if feeding_log.project_id not in project_ids:
                return jsonify({'error': 'غير مصرح لك بحذف هذا السجل'}), 403
        
        db.session.delete(feeding_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف سجل التغذية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in feeding_log_delete: {e}")
        return jsonify({'error': 'خطأ في حذف سجل التغذية'}), 500


# Daily Checkup API Routes
@api_bp.route('/breeding/checkup/list')
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.VIEW)
def api_checkup_list():
    """API endpoint to list daily checkup records with filters and pagination"""
    try:
        # Get query parameters
        project_id = request.args.get('project_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dog_id = request.args.get('dog_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        # Base query
        query = DailyCheckupLog.query

        # Apply project manager scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            query = query.filter(DailyCheckupLog.project_id.in_(assigned_project_ids))

        # Apply filters
        if project_id:
            query = query.filter(DailyCheckupLog.project_id == project_id)
        if date_from:
            query = query.filter(DailyCheckupLog.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(DailyCheckupLog.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if dog_id:
            query = query.filter(DailyCheckupLog.dog_id == dog_id)

        # Load related data
        query = query.options(
            db.joinedload(DailyCheckupLog.dog),
            db.joinedload(DailyCheckupLog.project),
            db.joinedload(DailyCheckupLog.examiner_employee)
        ).order_by(DailyCheckupLog.date.desc(), DailyCheckupLog.time.desc())

        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        checkups = paginated.items

        # Calculate KPIs
        total_query = query
        all_checkups = total_query.all()
        
        # Count body part flags (not 'سليم')
        body_parts = ['eyes', 'ears', 'nose', 'front_legs', 'hind_legs', 'coat', 'tail']
        flags = {}
        for part in body_parts:
            flags[part] = len([c for c in all_checkups if getattr(c, part) and getattr(c, part) != 'سليم'])
        
        # Count severity levels
        severity_counts = {"خفيف": 0, "متوسط": 0, "شديد": 0}
        for checkup in all_checkups:
            if checkup.severity:
                severity_counts[checkup.severity] = severity_counts.get(checkup.severity, 0) + 1

        # Format response
        items = []
        for checkup in checkups:
            items.append({
                'id': checkup.id,
                'date': checkup.date.isoformat(),
                'time': checkup.time.strftime('%H:%M'),
                'dog_name': checkup.dog.name if checkup.dog else '',
                'project_name': checkup.project.name if checkup.project else '',
                'examiner_name': checkup.examiner_employee.name if checkup.examiner_employee else '',
                'eyes': checkup.eyes,
                'ears': checkup.ears,
                'nose': checkup.nose,
                'front_legs': checkup.front_legs,
                'hind_legs': checkup.hind_legs,
                'coat': checkup.coat,
                'tail': checkup.tail,
                'severity': checkup.severity,
                'symptoms': checkup.symptoms,
                'initial_diagnosis': checkup.initial_diagnosis,
                'suggested_treatment': checkup.suggested_treatment
            })

        return jsonify({
            'items': items,
            'pagination': {
                'page': page,
                'pages': paginated.pages,
                'per_page': per_page,
                'total': paginated.total,
                'has_prev': paginated.has_prev,
                'has_next': paginated.has_next
            },
            'kpis': {
                'total': len(all_checkups),
                'flags': {
                    'العين': flags['eyes'],
                    'الأذن': flags['ears'],
                    'الأنف': flags['nose'],
                    'الأطراف_الأمامية': flags['front_legs'],
                    'الأطراف_الخلفية': flags['hind_legs'],
                    'الشعر': flags['coat'],
                    'الذيل': flags['tail']
                },
                'severity': severity_counts
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/breeding/checkup', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.CREATE)
def api_checkup_create():
    """API endpoint to create a new daily checkup record"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['project_id', 'date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'مطلوب: {field}'}), 400

        # Check project access for project managers
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            if int(data['project_id']) not in assigned_project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403

        # Validate enum values
        valid_part_statuses = ["سليم", "احمرار", "التهاب", "إفرازات", "تورم", "جرح", "ألم", "أخرى"]
        valid_severities = ["خفيف", "متوسط", "شديد"]

        body_parts = ['eyes', 'ears', 'nose', 'front_legs', 'hind_legs', 'coat', 'tail']
        for part in body_parts:
            if data.get(part) and data[part] not in valid_part_statuses:
                return jsonify({'error': f'قيمة غير صحيحة لـ {part}'}), 400

        if data.get('severity') and data['severity'] not in valid_severities:
            return jsonify({'error': 'قيمة شدة الحالة غير صحيحة'}), 400

        # Parse and normalize time
        time_str = data['time']
        if len(time_str) == 5:  # HH:MM
            time_str += ':00'  # Add seconds
        parsed_time = datetime.strptime(time_str, '%H:%M:%S').time()

        # Create checkup record
        checkup = DailyCheckupLog()
        checkup.project_id = int(data['project_id'])
        checkup.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        checkup.time = parsed_time
        checkup.dog_id = int(data['dog_id'])
        checkup.examiner_employee_id = int(data['examiner_employee_id']) if data.get('examiner_employee_id') else None

        # Set body part statuses
        for part in body_parts:
            if data.get(part):
                setattr(checkup, part, data[part])

        checkup.severity = data.get('severity')
        checkup.symptoms = data.get('symptoms')
        checkup.initial_diagnosis = data.get('initial_diagnosis')
        checkup.suggested_treatment = data.get('suggested_treatment')
        checkup.notes = data.get('notes')
        checkup.created_by_user_id = current_user.id
        checkup.created_at = datetime.utcnow()
        checkup.updated_at = datetime.utcnow()

        db.session.add(checkup)
        db.session.commit()

        # Return created record
        return jsonify({
            'success': True,
            'id': checkup.id,
            'message': 'تم إنشاء الفحص بنجاح'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/breeding/checkup/<id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.EDIT)
def api_checkup_update(id):
    """API endpoint to update a daily checkup record"""
    try:
        checkup = DailyCheckupLog.query.get_or_404(id)

        # Check project access for project managers
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            if checkup.project_id not in assigned_project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403

        data = request.get_json()

        # Validate enum values
        valid_part_statuses = ["سليم", "احمرار", "التهاب", "إفرازات", "تورم", "جرح", "ألم", "أخرى"]
        valid_severities = ["خفيف", "متوسط", "شديد"]

        body_parts = ['eyes', 'ears', 'nose', 'front_legs', 'hind_legs', 'coat', 'tail']
        for part in body_parts:
            if data.get(part) and data[part] not in valid_part_statuses:
                return jsonify({'error': f'قيمة غير صحيحة لـ {part}'}), 400

        if data.get('severity') and data['severity'] not in valid_severities:
            return jsonify({'error': 'قيمة شدة الحالة غير صحيحة'}), 400

        # Update fields
        if data.get('examiner_employee_id'):
            checkup.examiner_employee_id = int(data['examiner_employee_id'])

        # Update body part statuses
        for part in body_parts:
            if part in data:
                setattr(checkup, part, data[part])

        if 'severity' in data:
            checkup.severity = data['severity']
        if 'symptoms' in data:
            checkup.symptoms = data['symptoms']
        if 'initial_diagnosis' in data:
            checkup.initial_diagnosis = data['initial_diagnosis']
        if 'suggested_treatment' in data:
            checkup.suggested_treatment = data['suggested_treatment']
        if 'notes' in data:
            checkup.notes = data['notes']

        checkup.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم تحديث الفحص بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/breeding/checkup/<id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.DELETE)
def api_checkup_delete(id):
    """API endpoint to delete a daily checkup record"""
    try:
        checkup = DailyCheckupLog.query.get_or_404(id)

        # Check project access for project managers
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            if checkup.project_id not in assigned_project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403

        db.session.delete(checkup)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف الفحص بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500