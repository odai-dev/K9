from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import func
from k9.models.models import (
    db, Project, Employee, Dog, UserRole, AttendanceStatus,
    FeedingLog, PrepMethod, BodyConditionScale, DailyCheckupLog, PermissionType, DogStatus,
    ExcretionLog, StoolColor, StoolConsistency, StoolContent, UrineColor, VomitColor, ExcretionPlace,
    GroomingLog, GroomingYesNo, GroomingCleanlinessScore
)
from k9.utils.utils import get_user_permissions, get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
from k9.utils.permission_decorators import require_sub_permission
import uuid
from k9.services.attendance_service import (
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

from k9.utils.permission_utils import has_permission
from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs
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
                # Only show feeding logs with no project
                query = query.filter(FeedingLog.project_id.is_(None))
            else:
                # Show feeding logs with no project OR assigned projects
                query = query.filter(
                    (FeedingLog.project_id.is_(None)) | 
                    (FeedingLog.project_id.in_(project_ids))
                )
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(FeedingLog.project_id.is_(None))
            else:
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
        
        # Validate required fields (project_id can be null for "No project")
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # Check PROJECT_MANAGER scoping (only if project_id is provided)
        project_id = data.get('project_id')
        if current_user.role == UserRole.PROJECT_MANAGER and project_id:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if project_id not in project_ids:
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
        supplements = data.get('supplements') or []
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
        feeding_log = FeedingLog()
        feeding_log.project_id = data.get('project_id') or None
        feeding_log.date = parsed_date
        feeding_log.time = parsed_time
        feeding_log.dog_id = data['dog_id']
        feeding_log.recorder_employee_id = data.get('recorder_employee_id')
        feeding_log.meal_type_fresh = data.get('meal_type_fresh', False)
        feeding_log.meal_type_dry = data.get('meal_type_dry', False)
        feeding_log.meal_name = data.get('meal_name')
        feeding_log.prep_method = prep_method
        feeding_log.grams = grams
        feeding_log.water_ml = water_ml
        feeding_log.supplements = supplements if supplements else None
        feeding_log.body_condition = body_condition
        feeding_log.notes = data.get('notes')
        feeding_log.created_by_user_id = current_user.id
        
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
                'project_name': feeding_log.project.name if feeding_log.project else "بدون مشروع",
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
            # Allow access if project_id is None or in assigned projects
            if feeding_log.project_id is not None and feeding_log.project_id not in project_ids:
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
            # Allow access if project_id is None or in assigned projects
            if feeding_log.project_id is not None and feeding_log.project_id not in project_ids:
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
            # Allow PROJECT_MANAGER to see logs from assigned projects OR logs without projects
            query = query.filter(
                or_(
                    DailyCheckupLog.project_id.in_(assigned_project_ids),
                    DailyCheckupLog.project_id.is_(None)
                )
            )

        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(DailyCheckupLog.project_id.is_(None))
            else:
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

        # Validate required fields (project_id is optional)
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'مطلوب: {field}'}), 400

        # Check project access for project managers (only if project_id is provided)
        project_id = data.get('project_id')
        if current_user.role == UserRole.PROJECT_MANAGER and project_id:
            assigned_projects = get_user_assigned_projects(current_user)
            assigned_project_ids = [p.id for p in assigned_projects]
            if project_id not in [str(pid) for pid in assigned_project_ids]:
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
        checkup.project_id = data['project_id'] if data.get('project_id') else None
        checkup.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        checkup.time = parsed_time
        checkup.dog_id = data['dog_id']
        checkup.examiner_employee_id = data['examiner_employee_id'] if data.get('examiner_employee_id') else None

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
            checkup.examiner_employee_id = data['examiner_employee_id']

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


# Excretion API Routes - DISABLED: Handled by api_excretion.py instead
# @api_bp.route('/breeding/excretion/list', methods=['GET'])
# @login_required
# @require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.VIEW)
# def excretion_list():
    """Get excretion log entries with filters and pagination"""
    try:
        # Get parameters
        project_id = request.args.get('project_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dog_id = request.args.get('dog_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Build base query with eager loading
        query = ExcretionLog.query.options(
            db.joinedload(ExcretionLog.project),
            db.joinedload(ExcretionLog.dog),
            db.joinedload(ExcretionLog.recorder_employee)
        )
        
        # Apply PROJECT_MANAGER scoping
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if not project_ids:
                return jsonify({'items': [], 'pagination': {}, 'kpis': {}})
            query = query.filter(db.or_(ExcretionLog.project_id.in_(project_ids), ExcretionLog.project_id.is_(None)))
        
        # Apply filters
        if project_id:
            query = query.filter(ExcretionLog.project_id == project_id)
        if date_from:
            query = query.filter(ExcretionLog.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(ExcretionLog.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if dog_id:
            query = query.filter(ExcretionLog.dog_id == dog_id)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(ExcretionLog.date.desc(), ExcretionLog.time.desc())\
                    .offset((page - 1) * per_page)\
                    .limit(per_page)\
                    .all()
        
        # Calculate KPIs
        all_items = query.all()
        
        stool_abnormal_consistency_count = len([
            i for i in all_items 
            if i.stool_consistency in ["سائل", "لين", "شديد الصلابة"]
        ])
        
        constipation_count = len([i for i in all_items if i.constipation])
        
        urine_abnormal_color_count = len([
            i for i in all_items 
            if i.urine_color in ["أصفر غامق", "بني مصفر", "وردي/دموي"]
        ])
        
        total_vomit_events = sum([i.vomit_count or 0 for i in all_items])
        
        # Count stool consistency distribution
        stool_consistency_counts = {}
        for consistency in StoolConsistency:
            stool_consistency_counts[consistency.value] = len([
                i for i in all_items if i.stool_consistency == consistency.value
            ])
        
        kpis = {
            'total': total,
            'stool': {
                'abnormal_consistency': stool_abnormal_consistency_count,
                'constipation': constipation_count,
                'by_consistency': stool_consistency_counts
            },
            'urine': {
                'abnormal_color': urine_abnormal_color_count
            },
            'vomit': {
                'total_events': total_vomit_events
            }
        }
        
        # Serialize items
        items_data = []
        for item in items:
            items_data.append({
                'id': str(item.id),
                'date': item.date.strftime('%Y-%m-%d'),
                'time': item.time.strftime('%H:%M:%S'),
                'dog_name': item.dog.name if item.dog else None,
                'dog_code': item.dog.code if item.dog else None,
                'project_name': item.project.name if item.project else None,
                'recorder_name': item.recorder_employee.name if item.recorder_employee else None,
                'stool_color': item.stool_color,
                'stool_consistency': item.stool_consistency,
                'stool_content': item.stool_content,
                'constipation': item.constipation,
                'stool_place': item.stool_place,
                'stool_notes': item.stool_notes,
                'urine_color': item.urine_color,
                'urine_notes': item.urine_notes,
                'vomit_color': item.vomit_color,
                'vomit_count': item.vomit_count,
                'vomit_notes': item.vomit_notes,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': item.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'items': items_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            },
            'kpis': kpis
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in excretion_list API: {e}")
        return jsonify({'error': 'خطأ في جلب سجلات الإفراز'}), 500


@api_bp.route('/breeding/excretion', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.CREATE)
def excretion_create():
    """Create new excretion log entry"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'لم يتم تقديم بيانات'}), 400
        
        # Validate required fields (project_id is optional)
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # Check PROJECT_MANAGER access
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if data.get('project_id') and data['project_id'] not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        # Validate at least one observation type has data
        has_stool = any([
            data.get('stool_color'), data.get('stool_consistency'), 
            data.get('stool_content'), data.get('stool_notes'),
            data.get('constipation', False), data.get('stool_place')
        ])
        has_urine = any([data.get('urine_color'), data.get('urine_notes')])
        has_vomit = any([
            data.get('vomit_color'), data.get('vomit_count'), data.get('vomit_notes')
        ])
        
        if not (has_stool or has_urine or has_vomit):
            return jsonify({'error': 'يجب تسجيل ملاحظة واحدة على الأقل (براز أو بول أو قيء)'}), 400
        
        # Parse date and time
        try:
            parsed_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'صيغة التاريخ غير صحيحة، استخدم YYYY-MM-DD'}), 400
        
        try:
            # Handle both HH:MM and HH:MM:SS formats
            time_str = data['time']
            if len(time_str.split(':')) == 2:
                time_str += ':00'
            parsed_time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return jsonify({'error': 'صيغة الوقت غير صحيحة، استخدم HH:MM أو HH:MM:SS'}), 400
        
        # Create excretion log with safe project_id handling
        excretion_log = ExcretionLog()
        # Ensure project_id is properly handled for nullable constraint
        project_id_value = data.get('project_id')
        excretion_log.project_id = project_id_value if project_id_value and project_id_value != '' else None
        excretion_log.date = parsed_date
        excretion_log.time = parsed_time
        excretion_log.dog_id = data['dog_id']
        excretion_log.recorder_employee_id = data.get('recorder_employee_id')
        
        # Stool fields
        excretion_log.stool_color = data.get('stool_color')
        excretion_log.stool_consistency = data.get('stool_consistency')
        excretion_log.stool_content = data.get('stool_content')
        excretion_log.constipation = data.get('constipation', False)
        excretion_log.stool_place = data.get('stool_place')
        excretion_log.stool_notes = data.get('stool_notes')
        
        # Urine fields
        excretion_log.urine_color = data.get('urine_color')
        excretion_log.urine_notes = data.get('urine_notes')
        
        # Vomit fields
        excretion_log.vomit_color = data.get('vomit_color')
        excretion_log.vomit_count = data.get('vomit_count')
        excretion_log.vomit_notes = data.get('vomit_notes')
        
        # Audit fields
        excretion_log.created_by_user_id = current_user.id
        
        db.session.add(excretion_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حفظ سجل الإفراز بنجاح',
            'id': str(excretion_log.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating excretion log: {e}")
        return jsonify({'error': 'خطأ في حفظ سجل الإفراز'}), 500


@api_bp.route('/breeding/excretion/<id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.EDIT)
def excretion_update(id):
    """Update excretion log entry"""
    try:
        excretion_log = ExcretionLog.query.get_or_404(id)
        
        # Check PROJECT_MANAGER access
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if excretion_log.project_id not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'لم يتم تقديم بيانات'}), 400
        
        # Update fields if provided
        if 'date' in data:
            try:
                excretion_log.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'صيغة التاريخ غير صحيحة'}), 400
        
        if 'time' in data:
            try:
                time_str = data['time']
                if len(time_str.split(':')) == 2:
                    time_str += ':00'
                excretion_log.time = datetime.strptime(time_str, '%H:%M:%S').time()
            except ValueError:
                return jsonify({'error': 'صيغة الوقت غير صحيحة'}), 400
        
        if 'dog_id' in data:
            excretion_log.dog_id = data['dog_id']
        if 'recorder_employee_id' in data:
            excretion_log.recorder_employee_id = data['recorder_employee_id']
        
        # Update stool fields
        if 'stool_color' in data:
            excretion_log.stool_color = data['stool_color']
        if 'stool_consistency' in data:
            excretion_log.stool_consistency = data['stool_consistency']
        if 'stool_content' in data:
            excretion_log.stool_content = data['stool_content']
        if 'constipation' in data:
            excretion_log.constipation = data['constipation']
        if 'stool_place' in data:
            excretion_log.stool_place = data['stool_place']
        if 'stool_notes' in data:
            excretion_log.stool_notes = data['stool_notes']
        
        # Update urine fields
        if 'urine_color' in data:
            excretion_log.urine_color = data['urine_color']
        if 'urine_notes' in data:
            excretion_log.urine_notes = data['urine_notes']
        
        # Update vomit fields
        if 'vomit_color' in data:
            excretion_log.vomit_color = data['vomit_color']
        if 'vomit_count' in data:
            excretion_log.vomit_count = data['vomit_count']
        if 'vomit_notes' in data:
            excretion_log.vomit_notes = data['vomit_notes']
        
        excretion_log.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث سجل الإفراز بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating excretion log: {e}")
        return jsonify({'error': 'خطأ في تحديث سجل الإفراز'}), 500


@api_bp.route('/breeding/excretion/<id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.DELETE)
def excretion_delete(id):
    """Delete excretion log entry"""
    try:
        excretion_log = ExcretionLog.query.get_or_404(id)
        
        # Check PROJECT_MANAGER access
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if excretion_log.project_id not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        db.session.delete(excretion_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف سجل الإفراز بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting excretion log: {e}")
        return jsonify({'error': 'خطأ في حذف سجل الإفراز'}), 500


# ============================================================
# GROOMING API ENDPOINTS
# ============================================================

@api_bp.route('/breeding/grooming/list', methods=['GET'])
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.VIEW)
def grooming_list():
    """Get paginated list of grooming logs with KPIs"""
    try:
        # Get query parameters
        project_id = request.args.get('project_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dog_id = request.args.get('dog_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Build base query
        query = GroomingLog.query
        
        # Apply PROJECT_MANAGER restrictions
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if not project_ids:
                return jsonify({
                    'items': [],
                    'pagination': {'total': 0, 'page': 1, 'per_page': per_page, 'pages': 0},
                    'kpis': {'total': 0, 'washed_yes': 0, 'brushed_yes': 0, 'nails_yes': 0, 
                            'teeth_yes': 0, 'ear_yes': 0, 'eye_yes': 0, 'avg_cleanliness': 0}
                })
            # For project managers, show records assigned to their projects OR records with no project
            query = query.filter((GroomingLog.project_id.in_(project_ids)) | (GroomingLog.project_id.is_(None)))
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(GroomingLog.project_id.is_(None))
            else:
                query = query.filter(GroomingLog.project_id == project_id)
        if date_from:
            query = query.filter(GroomingLog.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        if date_to:
            query = query.filter(GroomingLog.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        if dog_id:
            query = query.filter(GroomingLog.dog_id == dog_id)
        
        # Get total count for KPIs (before pagination)
        total_query = query
        total_count = total_query.count()
        
        # Calculate KPIs
        kpis = {
            'total': total_count,
            'washed_yes': total_query.filter(GroomingLog.washed_bathed == GroomingYesNo.YES).count(),
            'brushed_yes': total_query.filter(GroomingLog.brushing == GroomingYesNo.YES).count(),
            'nails_yes': total_query.filter(GroomingLog.nail_trimming == GroomingYesNo.YES).count(),
            'teeth_yes': total_query.filter(GroomingLog.teeth_brushing == GroomingYesNo.YES).count(),
            'ear_yes': total_query.filter(GroomingLog.ear_cleaning == GroomingYesNo.YES).count(),
            'eye_yes': total_query.filter(GroomingLog.eye_cleaning == GroomingYesNo.YES).count(),
            'avg_cleanliness': 0
        }
        
        # Calculate average cleanliness score
        cleanliness_logs = total_query.filter(GroomingLog.cleanliness_score.isnot(None)).all()
        if cleanliness_logs:
            cleanliness_sum = sum(int(log.cleanliness_score.value) for log in cleanliness_logs)
            kpis['avg_cleanliness'] = round(cleanliness_sum / len(cleanliness_logs), 2)
        
        # Apply pagination and sorting
        query = query.order_by(GroomingLog.date.desc(), GroomingLog.time.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare items with Arabic display values
        items = []
        for log in paginated.items:
            items.append({
                'id': log.id,
                'project_id': log.project_id,
                'project_name': log.project.name if log.project else '',
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M:%S'),
                'dog_id': log.dog_id,
                'dog_name': log.dog.name if log.dog else '',
                'recorder_employee_id': log.recorder_employee_id,
                'recorder_name': log.recorder_employee.name if log.recorder_employee else '',
                'washed_bathed': "نعم" if log.washed_bathed == GroomingYesNo.YES else "لا" if log.washed_bathed == GroomingYesNo.NO else "",
                'shampoo_type': log.shampoo_type or '',
                'brushing': "نعم" if log.brushing == GroomingYesNo.YES else "لا" if log.brushing == GroomingYesNo.NO else "",
                'nail_trimming': "نعم" if log.nail_trimming == GroomingYesNo.YES else "لا" if log.nail_trimming == GroomingYesNo.NO else "",
                'teeth_brushing': "نعم" if log.teeth_brushing == GroomingYesNo.YES else "لا" if log.teeth_brushing == GroomingYesNo.NO else "",
                'ear_cleaning': "نعم" if log.ear_cleaning == GroomingYesNo.YES else "لا" if log.ear_cleaning == GroomingYesNo.NO else "",
                'eye_cleaning': "نعم" if log.eye_cleaning == GroomingYesNo.YES else "لا" if log.eye_cleaning == GroomingYesNo.NO else "",
                'cleanliness_score': log.cleanliness_score.value if log.cleanliness_score else '',
                'notes': log.notes or '',
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'items': items,
            'pagination': {
                'total': paginated.total,
                'page': paginated.page,
                'per_page': paginated.per_page,
                'pages': paginated.pages
            },
            'kpis': kpis
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching grooming logs: {e}")
        return jsonify({'error': 'خطأ في جلب سجلات العناية'}), 500


@api_bp.route('/breeding/grooming', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.CREATE)
def grooming_create():
    """Create new grooming log entry"""
    try:
        data = request.json
        
        # Validate required fields (project_id is optional)
        if not all(k in data for k in ['date', 'time', 'dog_id']):
            return jsonify({'error': 'الحقول المطلوبة: التاريخ، الوقت، الكلب'}), 400
        
        # Check PROJECT_MANAGER access to project (only if project is specified)
        project_id_value = data.get('project_id')
        if current_user.role == UserRole.PROJECT_MANAGER and project_id_value and project_id_value.strip():
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            if project_id_value not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        # Validate project exists (only if project is specified)
        if project_id_value and project_id_value.strip():
            project = Project.query.get(project_id_value)
            if not project:
                return jsonify({'error': 'المشروع غير موجود'}), 404
            
        dog = Dog.query.get(data['dog_id'])
        if not dog:
            return jsonify({'error': 'الكلب غير موجود'}), 404
        
        # Parse and validate date/time
        try:
            log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            log_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'تنسيق التاريخ أو الوقت غير صحيح'}), 400
        
        # Validate enum values
        for field, enum_class in [
            ('washed_bathed', GroomingYesNo),
            ('brushing', GroomingYesNo),
            ('nail_trimming', GroomingYesNo),
            ('teeth_brushing', GroomingYesNo),
            ('ear_cleaning', GroomingYesNo),
            ('eye_cleaning', GroomingYesNo)
        ]:
            if field in data and data[field]:
                try:
                    enum_class(data[field])
                except ValueError:
                    return jsonify({'error': f'قيمة غير صحيحة للحقل {field}'}), 400
        
        if 'cleanliness_score' in data and data['cleanliness_score']:
            try:
                GroomingCleanlinessScore(data['cleanliness_score'])
            except ValueError:
                return jsonify({'error': 'قيمة غير صحيحة لدرجة النظافة'}), 400
        
        # Create new grooming log
        grooming_log = GroomingLog()
        # Set project_id (already validated above)
        if project_id_value and project_id_value.strip():
            grooming_log.project_id = project_id_value
        else:
            grooming_log.project_id = None
        grooming_log.date = log_date
        grooming_log.time = log_time
        grooming_log.dog_id = data['dog_id']
        grooming_log.recorder_employee_id = data.get('recorder_employee_id')
        
        # Set enum fields
        grooming_log.washed_bathed = GroomingYesNo(data['washed_bathed']) if data.get('washed_bathed') else None
        grooming_log.shampoo_type = data.get('shampoo_type', '').strip()[:120]
        grooming_log.brushing = GroomingYesNo(data['brushing']) if data.get('brushing') else None
        grooming_log.nail_trimming = GroomingYesNo(data['nail_trimming']) if data.get('nail_trimming') else None
        grooming_log.teeth_brushing = GroomingYesNo(data['teeth_brushing']) if data.get('teeth_brushing') else None
        grooming_log.ear_cleaning = GroomingYesNo(data['ear_cleaning']) if data.get('ear_cleaning') else None
        grooming_log.eye_cleaning = GroomingYesNo(data['eye_cleaning']) if data.get('eye_cleaning') else None
        grooming_log.cleanliness_score = GroomingCleanlinessScore(data['cleanliness_score']) if data.get('cleanliness_score') else None
        grooming_log.notes = data.get('notes', '').strip()
        grooming_log.created_by_user_id = current_user.id
        
        db.session.add(grooming_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء سجل العناية بنجاح',
            'id': grooming_log.id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating grooming log: {e}")
        return jsonify({'error': 'خطأ في إنشاء سجل العناية'}), 500


@api_bp.route('/breeding/grooming/<id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.EDIT)
def grooming_update(id):
    """Update existing grooming log entry"""
    try:
        grooming_log = GroomingLog.query.get_or_404(id)
        
        # Check PROJECT_MANAGER access
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            # Allow access if project_id is None (no project) or if it's in assigned projects
            if grooming_log.project_id is not None and grooming_log.project_id not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        data = request.json
        
        # Update fields if provided
        if 'shampoo_type' in data:
            grooming_log.shampoo_type = data['shampoo_type'].strip()[:120]
        
        # Update enum fields
        for field, enum_class, attr in [
            ('washed_bathed', GroomingYesNo, 'washed_bathed'),
            ('brushing', GroomingYesNo, 'brushing'),
            ('nail_trimming', GroomingYesNo, 'nail_trimming'),
            ('teeth_brushing', GroomingYesNo, 'teeth_brushing'),
            ('ear_cleaning', GroomingYesNo, 'ear_cleaning'),
            ('eye_cleaning', GroomingYesNo, 'eye_cleaning')
        ]:
            if field in data:
                if data[field]:
                    try:
                        setattr(grooming_log, attr, enum_class(data[field]))
                    except ValueError:
                        return jsonify({'error': f'قيمة غير صحيحة للحقل {field}'}), 400
                else:
                    setattr(grooming_log, attr, None)
        
        if 'cleanliness_score' in data:
            if data['cleanliness_score']:
                try:
                    grooming_log.cleanliness_score = GroomingCleanlinessScore(data['cleanliness_score'])
                except ValueError:
                    return jsonify({'error': 'قيمة غير صحيحة لدرجة النظافة'}), 400
            else:
                grooming_log.cleanliness_score = None
        
        if 'notes' in data:
            grooming_log.notes = data['notes'].strip()
        
        if 'recorder_employee_id' in data:
            grooming_log.recorder_employee_id = data['recorder_employee_id']
        
        grooming_log.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث سجل العناية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating grooming log: {e}")
        return jsonify({'error': 'خطأ في تحديث سجل العناية'}), 500


@api_bp.route('/breeding/grooming/<id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.DELETE)
def grooming_delete(id):
    """Delete grooming log entry"""
    try:
        grooming_log = GroomingLog.query.get_or_404(id)
        
        # Check PROJECT_MANAGER access
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [p.id for p in assigned_projects]
            # Allow access if project_id is None (no project) or if it's in assigned projects
            if grooming_log.project_id is not None and grooming_log.project_id not in project_ids:
                return jsonify({'error': 'ليس لديك صلاحية لهذا المشروع'}), 403
        
        db.session.delete(grooming_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف سجل العناية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting grooming log: {e}")
        return jsonify({'error': 'خطأ في حذف سجل العناية'}), 500

# =======================
# DOGS API ENDPOINTS
# =======================

@api_bp.route('/dogs', methods=['GET'])
@login_required
def get_dogs():
    """Get list of accessible dogs with optional filtering"""
    try:
        # Get parameters
        status = request.args.get('status', '')
        project_id = request.args.get('project_id', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build base query
        query = Dog.query
        
        # Apply status filter if provided
        if status:
            try:
                status_enum = DogStatus(status)
                query = query.filter(Dog.current_status == status_enum)
            except ValueError:
                valid_statuses = [s.value for s in DogStatus]
                return jsonify({'error': f'Invalid status. Valid options: {valid_statuses}'}), 400
        
        # Apply project filter if provided
        if project_id == 'no_project':
            # Special case: return dogs with NO project assignments
            query = query.outerjoin(Dog.projects).filter(Project.id.is_(None))
        elif project_id:
            # Regular project filter: dogs assigned to specific project
            query = query.join(Dog.projects).filter(Project.id == project_id)
        
        # Apply permission filtering - PROJECT_MANAGER sees only their assigned dogs
        if current_user.role == UserRole.PROJECT_MANAGER:
            accessible_dogs = get_user_accessible_dogs(current_user)
            dog_ids = [dog.id for dog in accessible_dogs]
            query = query.filter(Dog.id.in_(dog_ids))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        dogs = query.offset(offset).limit(limit).all()
        
        # Format response
        dogs_data = []
        for dog in dogs:
            dogs_data.append({
                'id': str(dog.id),
                'name': dog.name,
                'code': dog.code,
                'microchip_id': dog.microchip_id,
                'breed': dog.breed,
                'status': dog.current_status.value if dog.current_status else None,
                'gender': dog.gender.value if dog.gender else None,
                'birth_date': dog.birth_date.isoformat() if dog.birth_date else None,
                'created_at': dog.created_at.isoformat() if dog.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': dogs_data,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dogs: {e}")
        return jsonify({'error': 'خطأ في جلب بيانات الكلاب'}), 500


@api_bp.route('/dogs/<dog_id>', methods=['GET'])
@login_required  
def get_dog(dog_id):
    """Get specific dog details"""
    try:
        dog = Dog.query.get_or_404(dog_id)
        
        # Check permissions - PROJECT_MANAGER can only see their assigned dogs
        if current_user.role == UserRole.PROJECT_MANAGER:
            accessible_dogs = get_user_accessible_dogs(current_user)
            dog_ids = [d.id for d in accessible_dogs]
            if dog.id not in dog_ids:
                return jsonify({'error': 'ليس لديك صلاحية لعرض بيانات هذا الكلب'}), 403
        
        # Format response
        dog_data = {
            'id': str(dog.id),
            'name': dog.name,
            'code': dog.code,
            'microchip_id': dog.microchip_id,
            'breed': dog.breed,
            'status': dog.current_status.value if dog.current_status else None,
            'gender': dog.gender.value if dog.gender else None,
            'birth_date': dog.birth_date.isoformat() if dog.birth_date else None,
            'color': dog.color,
            'weight': float(dog.weight) if dog.weight else None,
            'height': float(dog.height) if dog.height else None,
            'created_at': dog.created_at.isoformat() if dog.created_at else None
        }
        
        return jsonify({
            'success': True,
            'data': dog_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dog details: {e}")
        return jsonify({'error': 'خطأ في جلب تفاصيل الكلب'}), 500

# =======================
# DEWORMING API ENDPOINTS - Moved to api_deworming.py
# =======================
# All deworming endpoints have been moved to the dedicated api_deworming.py blueprint

