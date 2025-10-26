"""
مسارات واجهة المشرف
Supervisor Interface Routes - Daily Schedule Management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from k9.services.handler_service import DailyScheduleService
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem
from k9.models.models import UserRole, User, Dog, Project, Shift
from app import db
from functools import wraps


supervisor_bp = Blueprint('supervisor', __name__, url_prefix='/supervisor')


def supervisor_required(f):
    """Decorator to require SUPERVISOR or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_roles = [UserRole.SUPERVISOR, UserRole.GENERAL_ADMIN, UserRole.PROJECT_ADMIN]
        if not current_user.is_authenticated or current_user.role not in allowed_roles:
            flash('هذه الصفحة متاحة للمشرفين فقط', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@supervisor_bp.route('/schedules')
@login_required
@supervisor_required
def schedules_index():
    """قائمة الجداول اليومية"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    project_id = request.args.get('project_id')
    status_filter = request.args.get('status')
    
    # Build query
    query = DailySchedule.query
    
    # Filter by project if supervisor has project
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        query = query.filter_by(project_id=current_user.project_id)
    elif project_id:
        query = query.filter_by(project_id=project_id)
    
    if date_from:
        query = query.filter(DailySchedule.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(DailySchedule.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if status_filter:
        query = query.filter_by(is_locked=(status_filter == 'locked'))
    
    # Pagination
    pagination = query.order_by(DailySchedule.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get projects for filter
    projects = []
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
    elif current_user.project_id:
        projects = [Project.query.get(current_user.project_id)]
    
    return render_template('supervisor/schedules_index.html',
                         page_title='إدارة الجداول اليومية',
                         schedules=pagination.items,
                         pagination=pagination,
                         projects=projects)


@supervisor_bp.route('/schedules/create', methods=['GET', 'POST'])
@login_required
@supervisor_required
def schedule_create():
    """إنشاء جدول يومي جديد"""
    if request.method == 'POST':
        schedule_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        project_id = request.form.get('project_id')
        notes = request.form.get('notes')
        
        # Validate project access
        if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
            project_id = str(current_user.project_id)
        
        # Check if schedule already exists
        existing = DailySchedule.query.filter_by(
            date=schedule_date, project_id=project_id
        ).first()
        
        if existing:
            flash(f'جدول يومي موجود بالفعل لهذا التاريخ ({schedule_date})', 'warning')
            return redirect(url_for('supervisor.schedule_view', schedule_id=str(existing.id)))
        
        # Create schedule
        schedule = DailySchedule(
            date=schedule_date,
            project_id=project_id,
            notes=notes,
            is_locked=False,
            created_by_user_id=current_user.id
        )
        db.session.add(schedule)
        db.session.flush()
        
        # Add schedule items
        handler_ids = request.form.getlist('handler_ids[]')
        dog_ids = request.form.getlist('dog_ids[]')
        shift_ids = request.form.getlist('shift_ids[]')
        
        for i in range(len(handler_ids)):
            if handler_ids[i] and dog_ids[i] and shift_ids[i]:
                item = DailyScheduleItem(
                    schedule_id=schedule.id,
                    handler_user_id=handler_ids[i],
                    dog_id=dog_ids[i],
                    shift_id=shift_ids[i]
                )
                db.session.add(item)
        
        db.session.commit()
        
        # Send notifications
        DailyScheduleService.notify_handlers_of_new_schedule(str(schedule.id))
        
        flash(f'تم إنشاء الجدول اليومي لتاريخ {schedule_date} بنجاح', 'success')
        return redirect(url_for('supervisor.schedule_view', schedule_id=str(schedule.id)))
    
    # GET request
    today = date.today()
    
    # Get projects list
    projects = []
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Admin can see all projects
        projects = Project.query.all()
    elif current_user.role == UserRole.SUPERVISOR:
        if current_user.project_id:
            # Supervisor with assigned project sees only their project
            projects = [Project.query.get(current_user.project_id)]
        else:
            # Supervisor without assigned project can see all projects
            projects = Project.query.all()
    
    # Handlers and dogs will be loaded dynamically via API when project is selected
    handlers = []
    dogs = []
    
    # Get shifts
    shifts = Shift.query.all()
    
    return render_template('supervisor/schedule_create.html',
                         page_title='إنشاء جدول يومي جديد',
                         today=today.strftime('%Y-%m-%d'),
                         projects=projects,
                         handlers=handlers,
                         dogs=dogs,
                         shifts=shifts)


@supervisor_bp.route('/schedules/<schedule_id>')
@login_required
@supervisor_required
def schedule_view(schedule_id):
    """عرض الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Verify access
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        if str(schedule.project_id) != str(current_user.project_id):
            flash('غير مصرح لك بعرض هذا الجدول', 'danger')
            return redirect(url_for('supervisor.schedules_index'))
    
    return render_template('supervisor/schedule_view.html',
                         page_title=f'الجدول اليومي - {schedule.date.strftime("%Y-%m-%d")}',
                         schedule=schedule)


@supervisor_bp.route('/schedules/<schedule_id>/lock', methods=['POST'])
@login_required
@supervisor_required
def schedule_lock(schedule_id):
    """قفل الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Verify access
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        if str(schedule.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    if schedule.is_locked:
        return jsonify({'success': False, 'error': 'الجدول مقفل بالفعل'})
    
    success, message = DailyScheduleService.lock_schedule(schedule_id)
    return jsonify({'success': success, 'message': message})


@supervisor_bp.route('/schedules/<schedule_id>/unlock', methods=['POST'])
@login_required
@supervisor_required
def schedule_unlock(schedule_id):
    """إلغاء قفل الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Verify access
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        if str(schedule.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    if not schedule.is_locked:
        return jsonify({'success': False, 'error': 'الجدول غير مقفل'})
    
    schedule.is_locked = False
    schedule.locked_at = None
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم إلغاء قفل الجدول بنجاح'})


@supervisor_bp.route('/schedules/<schedule_id>/delete', methods=['POST'])
@login_required
@supervisor_required
def schedule_delete(schedule_id):
    """حذف الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Verify access
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        if str(schedule.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    if schedule.is_locked:
        return jsonify({'success': False, 'error': 'لا يمكن حذف جدول مقفل'})
    
    # Check if any reports exist
    from k9.models.models_handler_daily import HandlerReport
    reports_count = HandlerReport.query.join(DailyScheduleItem).filter(
        DailyScheduleItem.schedule_id == schedule_id
    ).count()
    
    if reports_count > 0:
        return jsonify({
            'success': False, 
            'error': f'لا يمكن حذف الجدول. يوجد {reports_count} تقرير مرتبط به'
        })
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم حذف الجدول بنجاح'})


@supervisor_bp.route('/schedules/item/<item_id>/replace-handler', methods=['POST'])
@login_required
@supervisor_required
def replace_handler(item_id):
    """استبدال سائس في عنصر من الجدول"""
    item = DailyScheduleItem.query.get_or_404(item_id)
    schedule = item.schedule
    
    # Verify access
    if current_user.role == UserRole.SUPERVISOR and current_user.project_id:
        if str(schedule.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    new_handler_id = request.json.get('new_handler_id')
    reason = request.json.get('reason', '')
    
    if not new_handler_id:
        return jsonify({'success': False, 'error': 'يجب اختيار سائس بديل'})
    
    success, message = DailyScheduleService.replace_handler(
        str(item.id), new_handler_id, reason
    )
    
    return jsonify({'success': success, 'message': message})


@supervisor_bp.route('/api/handlers-by-project/<project_id>')
@login_required
@supervisor_required
def get_handlers_by_project(project_id):
    """API: الحصول على السائسين حسب المشروع"""
    handlers = User.query.filter_by(
        role=UserRole.HANDLER,
        project_id=project_id
    ).all()
    
    return jsonify({
        'handlers': [
            {
                'id': str(h.id),
                'name': h.full_name,
                'dog_id': str(h.dog_id) if h.dog_id else None
            }
            for h in handlers
        ]
    })


@supervisor_bp.route('/api/dogs-by-project/<project_id>')
@login_required
@supervisor_required
def get_dogs_by_project(project_id):
    """API: الحصول على الكلاب حسب المشروع"""
    dogs = Dog.query.filter_by(
        project_id=project_id,
        current_status='ACTIVE'
    ).all()
    
    return jsonify({
        'dogs': [
            {
                'id': str(d.id),
                'name': d.name,
                'code': d.code
            }
            for d in dogs
        ]
    })
