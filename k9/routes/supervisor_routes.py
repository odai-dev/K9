"""
مسارات واجهة المشرف
Supervisor Interface Routes - Daily Schedule Management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from sqlalchemy.orm import joinedload
from k9.services.handler_service import DailyScheduleService
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem
from k9.models.models import UserRole, User, Dog, Project, Shift
from k9.decorators import supervisor_required
from app import db


supervisor_bp = Blueprint('supervisor', __name__, url_prefix='/supervisor')


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
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
        if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
            created_by_user_id=current_user.id
        )
        # status defaults to ScheduleStatus.OPEN automatically
        db.session.add(schedule)
        db.session.flush()
        
        # Add schedule items
        handler_ids = request.form.getlist('handler_ids[]')
        dog_ids = request.form.getlist('dog_ids[]')
        shift_ids = request.form.getlist('shift_ids[]')
        
        for i in range(len(handler_ids)):
            if handler_ids[i] and dog_ids[i] and shift_ids[i]:
                item = DailyScheduleItem(
                    daily_schedule_id=schedule.id,
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
    elif current_user.role == UserRole.PROJECT_MANAGER:
        if current_user.project_id:
            # Supervisor with assigned project sees only their project
            projects = [Project.query.get(current_user.project_id)]
        else:
            # Supervisor without assigned project can see all projects
            projects = Project.query.all()
    
    # Handlers and dogs will be loaded dynamically via API when project is selected
    handlers = []
    dogs = []
    
    # Get shifts and convert to dictionaries for JSON serialization
    shifts = Shift.query.all()
    shifts_data = [{
        'id': str(shift.id),
        'name': shift.name,
        'start_time': shift.start_time.strftime('%H:%M') if shift.start_time else None,
        'end_time': shift.end_time.strftime('%H:%M') if shift.end_time else None
    } for shift in shifts]
    
    return render_template('supervisor/schedule_create.html',
                         page_title='إنشاء جدول يومي جديد',
                         today=today.strftime('%Y-%m-%d'),
                         projects=projects,
                         handlers=handlers,
                         dogs=dogs,
                         shifts=shifts_data)


@supervisor_bp.route('/schedules/<schedule_id>')
@login_required
@supervisor_required
def schedule_view(schedule_id):
    """عرض الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Verify access
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
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
    # Get handlers assigned to this project
    assigned_handlers = User.query.filter_by(
        role=UserRole.HANDLER,
        project_id=project_id,
        active=True
    ).all()
    
    # Also include handlers not assigned to any project (available for assignment)
    unassigned_handlers = User.query.filter_by(
        role=UserRole.HANDLER,
        active=True
    ).filter(
        User.project_id.is_(None)
    ).all()
    
    all_handlers = assigned_handlers + unassigned_handlers
    
    return jsonify({
        'handlers': [
            {
                'id': str(h.id),
                'name': h.full_name,
                'dog_id': str(h.dog_id) if h.dog_id else None
            }
            for h in all_handlers
        ]
    })


@supervisor_bp.route('/api/dogs-by-project/<project_id>')
@login_required
@supervisor_required
def get_dogs_by_project(project_id):
    """API: الحصول على الكلاب حسب المشروع"""
    # Dogs are assigned to handlers, and handlers are assigned to projects
    # Get all handlers in this project
    handlers_in_project = User.query.filter_by(
        role=UserRole.HANDLER,
        project_id=project_id
    ).all()
    
    # Get dogs assigned to these handlers
    handler_ids = [h.id for h in handlers_in_project]
    dogs = Dog.query.filter(
        Dog.assigned_to_user_id.in_(handler_ids),
        Dog.current_status == 'ACTIVE'
    ).all() if handler_ids else []
    
    # Also include dogs not assigned to anyone (available for assignment)
    unassigned_dogs = Dog.query.filter(
        Dog.assigned_to_user_id.is_(None),
        Dog.current_status == 'ACTIVE'
    ).all()
    
    all_dogs = dogs + unassigned_dogs
    
    return jsonify({
        'dogs': [
            {
                'id': str(d.id),
                'name': d.name,
                'code': d.code
            }
            for d in all_dogs
        ]
    })


# ============================================================================
# Handler Reports Management
# ============================================================================

@supervisor_bp.route('/reports')
@login_required
@supervisor_required
def reports_index():
    """قائمة تقارير السائسين للمراجعة"""
    from k9.models.models_handler_daily import HandlerReport, ReportStatus
    from k9.services.handler_service import HandlerReportService
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    handler_id = request.args.get('handler_id')
    project_id = request.args.get('project_id')
    status_filter = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = HandlerReport.query
    
    # Filter by project if supervisor has project
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
        query = query.filter_by(project_id=current_user.project_id)
    elif project_id:
        query = query.filter_by(project_id=project_id)
    
    if handler_id:
        query = query.filter_by(handler_user_id=handler_id)
    if status_filter:
        query = query.filter_by(status=ReportStatus[status_filter])
    if date_from:
        query = query.filter(HandlerReport.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(HandlerReport.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    # Pagination
    pagination = query.order_by(HandlerReport.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get statistics
    stats = {}
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
        base_query = HandlerReport.query.filter_by(project_id=current_user.project_id)
    else:
        base_query = HandlerReport.query
    
    stats['total'] = base_query.count()
    stats['pending'] = base_query.filter_by(status=ReportStatus.SUBMITTED).count()
    stats['approved'] = base_query.filter_by(status=ReportStatus.APPROVED).count()
    stats['rejected'] = base_query.filter_by(status=ReportStatus.REJECTED).count()
    
    # Get handlers for filter
    handlers = []
    if current_user.role == UserRole.GENERAL_ADMIN:
        handlers = User.query.filter_by(role=UserRole.HANDLER).all()
    elif current_user.project_id:
        handlers = User.query.filter_by(role=UserRole.HANDLER, project_id=current_user.project_id).all()
    
    # Get projects for filter
    projects = []
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
    elif current_user.project_id:
        projects = [Project.query.get(current_user.project_id)]
    
    return render_template('supervisor/reports_index.html',
                         page_title='تقارير السائسين',
                         reports=pagination.items,
                         pagination=pagination,
                         stats=stats,
                         handlers=handlers,
                         projects=projects,
                         ReportStatus=ReportStatus)


@supervisor_bp.route('/reports/<report_id>')
@login_required
@supervisor_required
def report_view(report_id):
    """عرض تفاصيل التقرير"""
    from k9.models.models_handler_daily import HandlerReport, ReportStatus
    
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify access
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
        if str(report.project_id) != str(current_user.project_id):
            flash('غير مصرح لك بعرض هذا التقرير', 'danger')
            return redirect(url_for('supervisor.reports_index'))
    
    return render_template('supervisor/report_view.html',
                         page_title=f'التقرير اليومي - {report.date.strftime("%Y-%m-%d")}',
                         report=report,
                         ReportStatus=ReportStatus)


@supervisor_bp.route('/reports/<report_id>/approve', methods=['POST'])
@login_required
@supervisor_required
def report_approve(report_id):
    """اعتماد التقرير"""
    from k9.models.models_handler_daily import HandlerReport, ReportStatus
    from k9.services.handler_service import HandlerReportService, NotificationService
    from k9.models.models_handler_daily import NotificationType
    
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify access
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
        if str(report.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    review_notes = request.json.get('review_notes', '')
    
    # Update report status
    report.status = ReportStatus.APPROVED
    report.reviewed_by_user_id = current_user.id
    report.reviewed_at = datetime.utcnow()
    report.review_notes = review_notes
    
    db.session.commit()
    
    # Send notification to handler
    NotificationService.create_notification(
        user_id=str(report.handler_user_id),
        notification_type=NotificationType.REPORT_APPROVED,
        title="تم اعتماد التقرير",
        message=f"تم اعتماد تقريرك اليومي بتاريخ {report.date.strftime('%Y-%m-%d')} من قبل {current_user.full_name}",
        related_id=str(report.id),
        related_type='HandlerReport'
    )
    
    flash('تم اعتماد التقرير بنجاح', 'success')
    return jsonify({'success': True, 'message': 'تم اعتماد التقرير بنجاح'})


@supervisor_bp.route('/reports/<report_id>/reject', methods=['POST'])
@login_required
@supervisor_required
def report_reject(report_id):
    """رفض التقرير"""
    from k9.models.models_handler_daily import HandlerReport, ReportStatus
    from k9.services.handler_service import HandlerReportService, NotificationService
    from k9.models.models_handler_daily import NotificationType
    
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify access
    if current_user.role == UserRole.PROJECT_MANAGER and current_user.project_id:
        if str(report.project_id) != str(current_user.project_id):
            return jsonify({'success': False, 'error': 'غير مصرح لك'})
    
    review_notes = request.json.get('review_notes', '')
    
    if not review_notes:
        return jsonify({'success': False, 'error': 'يجب إدخال سبب الرفض'})
    
    # Update report status
    report.status = ReportStatus.REJECTED
    report.reviewed_by_user_id = current_user.id
    report.reviewed_at = datetime.utcnow()
    report.review_notes = review_notes
    
    db.session.commit()
    
    # Send notification to handler
    NotificationService.create_notification(
        user_id=str(report.handler_user_id),
        notification_type=NotificationType.REPORT_REJECTED,
        title="تم رفض التقرير",
        message=f"تم رفض تقريرك اليومي بتاريخ {report.date.strftime('%Y-%m-%d')}. السبب: {review_notes}",
        related_id=str(report.id),
        related_type='HandlerReport'
    )
    
    flash('تم رفض التقرير', 'warning')
    return jsonify({'success': True, 'message': 'تم رفض التقرير'})
