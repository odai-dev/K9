"""
مسارات واجهة السائس
Handler Interface Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from k9.services.handler_service import (
    DailyScheduleService, HandlerReportService, NotificationService, AttachmentService
)
from k9.models.models_handler_daily import (
    HandlerReport, HandlerReportHealth, HandlerReportTraining,
    HandlerReportCare, HandlerReportBehavior, HandlerReportIncident,
    TrainingType, BehaviorType, IncidentType, StoolColor, StoolShape,
    HealthCheckStatus
)
from k9.models.models import UserRole, Dog, User
from app import db
from functools import wraps


handler_bp = Blueprint('handler', __name__, url_prefix='/handler')


def handler_required(f):
    """Decorator to require HANDLER role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.HANDLER:
            flash('هذه الصفحة متاحة للسائسين فقط', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@handler_bp.route('/dashboard')
@login_required
@handler_required
def dashboard():
    """لوحة تحكم السائس"""
    from k9.models.models import Project
    from k9.models.models_handler_daily import ReportStatus
    from dateutil.relativedelta import relativedelta
    
    today = date.today()
    
    # Get project and assigned dog
    project = None
    assigned_dog = None
    if current_user.project_id:
        project = Project.query.get(current_user.project_id)
    if current_user.dog_id:
        assigned_dog = Dog.query.get(current_user.dog_id)
    
    # Get today's schedule
    today_schedule = DailyScheduleService.get_handler_schedule_for_date(
        str(current_user.id), today
    )
    
    # Get notifications
    recent_notifications = NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True, limit=5
    )
    unread_count = len(NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True
    ))
    
    # Get recent reports
    recent_reports = HandlerReport.query.filter_by(
        handler_user_id=current_user.id
    ).order_by(HandlerReport.date.desc()).limit(5).all()
    
    # Calculate stats
    this_month_start = today.replace(day=1)
    stats = {
        'total_reports': HandlerReport.query.filter_by(handler_user_id=current_user.id).count(),
        'approved_reports': HandlerReport.query.filter_by(
            handler_user_id=current_user.id,
            status=ReportStatus.APPROVED
        ).count(),
        'pending_reports': HandlerReport.query.filter_by(
            handler_user_id=current_user.id,
            status=ReportStatus.SUBMITTED
        ).count(),
        'this_month_reports': HandlerReport.query.filter(
            db.and_(
                HandlerReport.handler_user_id == current_user.id,
                HandlerReport.date >= this_month_start
            )
        ).count()
    }
    
    return render_template('handler/dashboard.html',
                         page_title='لوحة تحكم السائس',
                         today_date=today.strftime('%Y-%m-%d'),
                         project=project,
                         assigned_dog=assigned_dog,
                         today_schedule=today_schedule,
                         recent_notifications=recent_notifications,
                         unread_count=unread_count,
                         recent_reports=recent_reports,
                         stats=stats)


@handler_bp.route('/report/new', methods=['GET', 'POST'])
@login_required
@handler_required
def new_report():
    """إنشاء تقرير يومي جديد"""
    from k9.models.models import Shift
    from k9.models.models_handler_daily import DailyScheduleItem
    
    if request.method == 'POST':
        action = request.form.get('action', 'save_draft')
        dog_id = request.form.get('dog_id')
        schedule_item_id = request.form.get('schedule_item_id')
        location = request.form.get('location')
        report_date = request.form.get('date')
        
        # Parse date
        if report_date:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            report_date = date.today()
        
        # Validate required fields
        if not dog_id:
            flash('يجب اختيار الكلب', 'danger')
            return redirect(url_for('handler.new_report'))
        
        # Create report with parsed date
        report, error = HandlerReportService.create_report(
            handler_user_id=str(current_user.id),
            dog_id=dog_id,
            schedule_item_id=schedule_item_id if schedule_item_id else None,
            project_id=str(current_user.project_id) if current_user.project_id else None,
            location=location,
            report_date=report_date
        )
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('handler.new_report'))
        
        # Update health section - 11 body parts
        if report.health:
            # Eyes
            eyes_status_val = request.form.get('eyes_status')
            report.health.eyes_status = HealthCheckStatus(eyes_status_val) if eyes_status_val else None
            report.health.eyes_notes = request.form.get('eyes_notes')
            
            # Nose
            nose_status_val = request.form.get('nose_status')
            report.health.nose_status = HealthCheckStatus(nose_status_val) if nose_status_val else None
            report.health.nose_notes = request.form.get('nose_notes')
            
            # Ears
            ears_status_val = request.form.get('ears_status')
            report.health.ears_status = HealthCheckStatus(ears_status_val) if ears_status_val else None
            report.health.ears_notes = request.form.get('ears_notes')
            
            # Mouth
            mouth_status_val = request.form.get('mouth_status')
            report.health.mouth_status = HealthCheckStatus(mouth_status_val) if mouth_status_val else None
            report.health.mouth_notes = request.form.get('mouth_notes')
            
            # Teeth
            teeth_status_val = request.form.get('teeth_status')
            report.health.teeth_status = HealthCheckStatus(teeth_status_val) if teeth_status_val else None
            report.health.teeth_notes = request.form.get('teeth_notes')
            
            # Gums
            gums_status_val = request.form.get('gums_status')
            report.health.gums_status = HealthCheckStatus(gums_status_val) if gums_status_val else None
            report.health.gums_notes = request.form.get('gums_notes')
            
            # Front limbs
            front_limbs_status_val = request.form.get('front_limbs_status')
            report.health.front_limbs_status = HealthCheckStatus(front_limbs_status_val) if front_limbs_status_val else None
            report.health.front_limbs_notes = request.form.get('front_limbs_notes')
            
            # Back limbs
            back_limbs_status_val = request.form.get('back_limbs_status')
            report.health.back_limbs_status = HealthCheckStatus(back_limbs_status_val) if back_limbs_status_val else None
            report.health.back_limbs_notes = request.form.get('back_limbs_notes')
            
            # Hair
            hair_status_val = request.form.get('hair_status')
            report.health.hair_status = HealthCheckStatus(hair_status_val) if hair_status_val else None
            report.health.hair_notes = request.form.get('hair_notes')
            
            # Tail
            tail_status_val = request.form.get('tail_status')
            report.health.tail_status = HealthCheckStatus(tail_status_val) if tail_status_val else None
            report.health.tail_notes = request.form.get('tail_notes')
            
            # Rear
            rear_status_val = request.form.get('rear_status')
            report.health.rear_status = HealthCheckStatus(rear_status_val) if rear_status_val else None
            report.health.rear_notes = request.form.get('rear_notes')
        
        # Training section - 6 types
        training_types_map = {
            'fitness': TrainingType.FITNESS,
            'agility': TrainingType.AGILITY,
            'obedience': TrainingType.OBEDIENCE,
            'ball': TrainingType.BALL,
            'explosives': TrainingType.EXPLOSIVES,
            'other': TrainingType.OTHER
        }
        
        for key, training_type in training_types_map.items():
            description = request.form.get(f'training_{key}_description')
            time_from_str = request.form.get(f'training_{key}_from')
            time_to_str = request.form.get(f'training_{key}_to')
            notes = request.form.get(f'training_{key}_notes')
            
            # Only create if at least one field is filled
            if description or time_from_str or time_to_str or notes:
                from datetime import time as dt_time
                time_from = datetime.strptime(time_from_str, '%H:%M').time() if time_from_str else None
                time_to = datetime.strptime(time_to_str, '%H:%M').time() if time_to_str else None
                
                training_session = HandlerReportTraining(
                    report_id=report.id,
                    training_type=training_type,
                    description=description,
                    time_from=time_from,
                    time_to=time_to,
                    notes=notes
                )
                db.session.add(training_session)
        
        # Care section - matching Word document
        if report.care:
            report.care.food_amount = request.form.get('food_amount')
            report.care.food_type = request.form.get('food_type')
            report.care.supplements = request.form.get('supplements')
            report.care.water_amount = request.form.get('water_amount')
            report.care.grooming_done = bool(request.form.get('grooming_done'))
            report.care.washing_done = bool(request.form.get('washing_done'))
            report.care.excretion_location = request.form.get('excretion_location')
            
            # Stool color
            stool_color_val = request.form.get('stool_color')
            report.care.stool_color = StoolColor(stool_color_val) if stool_color_val else None
            
            # Stool shape
            stool_shape_val = request.form.get('stool_shape')
            report.care.stool_shape = StoolShape(stool_shape_val) if stool_shape_val else None
        
        # Behavior section
        if report.behavior:
            report.behavior.good_behavior_notes = request.form.get('good_behavior_notes')
            report.behavior.bad_behavior_notes = request.form.get('bad_behavior_notes')
        
        # Incidents section - suspicion and detection
        suspicion_cases = request.form.get('suspicion_cases')
        detection_cases = request.form.get('detection_cases')
        
        if suspicion_cases:
            suspicion_incident = HandlerReportIncident(
                report_id=report.id,
                incident_type=IncidentType.SUSPICION,
                description=suspicion_cases
            )
            db.session.add(suspicion_incident)
        
        if detection_cases:
            detection_incident = HandlerReportIncident(
                report_id=report.id,
                incident_type=IncidentType.DETECTION,
                description=detection_cases
            )
            db.session.add(detection_incident)
        
        db.session.commit()
        
        # Submit if requested
        if action == 'submit':
            success, error = HandlerReportService.submit_report(str(report.id))
            if success:
                flash('تم إرسال التقرير للمراجعة بنجاح', 'success')
                return redirect(url_for('handler.dashboard'))
            else:
                flash(f'تم حفظ التقرير لكن فشل الإرسال: {error}', 'warning')
        else:
            flash('تم حفظ التقرير كمسودة', 'success')
        
        return redirect(url_for('handler.view_report', report_id=str(report.id)))
    
    # GET request
    today = date.today()
    schedule_item_id = request.args.get('schedule_item_id')
    
    # Get schedule item if provided
    schedule_item = None
    if schedule_item_id:
        schedule_item = DailyScheduleItem.query.get(schedule_item_id)
    
    # Get assigned dog
    assigned_dog = None
    if current_user.dog_id:
        assigned_dog = Dog.query.get(current_user.dog_id)
    
    # Get available dogs (project dogs or all if no project)
    available_dogs = []
    if current_user.project_id:
        # Dogs are assigned to handlers, not directly to projects
        # Get all handlers in this project
        handlers_in_project = User.query.filter_by(
            role=UserRole.HANDLER,
            project_id=current_user.project_id
        ).all()
        
        # Get dogs assigned to these handlers
        handler_ids = [h.id for h in handlers_in_project]
        if handler_ids:
            available_dogs = Dog.query.filter(
                Dog.assigned_to_user_id.in_(handler_ids),
                Dog.current_status == 'ACTIVE'
            ).all()
        
        # Also include unassigned dogs
        unassigned_dogs = Dog.query.filter(
            Dog.assigned_to_user_id.is_(None),
            Dog.current_status == 'ACTIVE'
        ).all()
        available_dogs = available_dogs + unassigned_dogs
    else:
        available_dogs = Dog.query.filter_by(current_status='ACTIVE').all()
    
    # Get shifts
    shifts = Shift.query.all()
    
    return render_template('handler/new_report.html',
                         page_title='تقرير يومي جديد',
                         today=today.strftime('%Y-%m-%d'),
                         schedule_item=schedule_item,
                         assigned_dog=assigned_dog,
                         available_dogs=available_dogs,
                         shifts=shifts)


@handler_bp.route('/report/<report_id>/edit', methods=['GET', 'POST'])
@login_required
@handler_required
def edit_report(report_id):
    """تعديل التقرير اليومي"""
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify ownership
    if str(report.handler_user_id) != str(current_user.id):
        flash('غير مصرح لك بتعديل هذا التقرير', 'danger')
        return redirect(url_for('handler.dashboard'))
    
    # Can only edit drafts
    if report.status.value != 'DRAFT':
        flash('لا يمكن تعديل التقرير بعد إرساله', 'warning')
        return redirect(url_for('handler.view_report', report_id=report_id))
    
    if request.method == 'POST':
        # Save report data from form
        # This is simplified - you'd parse all the form fields
        
        # Update general info
        report.location = request.form.get('location')
        
        # Update health section
        if not report.health:
            report.health = HandlerReportHealth(report_id=report.id)  # type: ignore
        
        report.health.eyes_status = request.form.get('eyes_status')  # type: ignore
        report.health.eyes_notes = request.form.get('eyes_notes')  # type: ignore
        
        # ... (continue for all fields)
        
        db.session.commit()
        flash('تم حفظ التقرير', 'success')
        
        # Check if submitting
        if request.form.get('action') == 'submit':
            success, error = HandlerReportService.submit_report(report_id)
            if success:
                flash('تم إرسال التقرير للمراجعة', 'success')
                return redirect(url_for('handler.dashboard'))
            else:
                flash(error, 'danger')
        
        return redirect(url_for('handler.edit_report', report_id=report_id))
    
    # GET request
    return render_template('handler/edit_report.html',
                         page_title='تعديل التقرير',
                         report=report,
                         training_types=TrainingType,
                         behavior_types=BehaviorType,
                         incident_types=IncidentType,
                         stool_colors=StoolColor,
                         stool_shapes=StoolShape,
                         health_statuses=HealthCheckStatus)


@handler_bp.route('/report/<report_id>')
@login_required
@handler_required
def view_report(report_id):
    """عرض التقرير"""
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify ownership
    if str(report.handler_user_id) != str(current_user.id):
        flash('غير مصرح لك بعرض هذا التقرير', 'danger')
        return redirect(url_for('handler.dashboard'))
    
    return render_template('handler/view_report.html',
                         page_title='عرض التقرير',
                         report=report)


@handler_bp.route('/notifications')
@login_required
@handler_required
def notifications():
    """عرض الإشعارات"""
    from k9.models.models_handler_daily import Notification
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filter_type = request.args.get('filter', 'all')
    
    # Build query
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filter
    if filter_type == 'unread':
        query = query.filter_by(read=False)
    elif filter_type == 'read':
        query = query.filter_by(read=True)
    
    # Get pagination object
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get counts
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, read=False
    ).count()
    total_count = Notification.query.filter_by(user_id=current_user.id).count()
    
    return render_template('handler/notifications.html',
                         page_title='الإشعارات',
                         notifications=pagination.items,
                         pagination=pagination,
                         unread_count=unread_count,
                         total_count=total_count)


@handler_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
@handler_required
def mark_notification_read(notification_id):
    """تعليم الإشعار كمقروء"""
    NotificationService.mark_as_read(notification_id)
    return jsonify({'success': True})


@handler_bp.route('/notifications/read-all', methods=['POST'])
@login_required
@handler_required
def mark_all_notifications_read():
    """تعليم جميع الإشعارات كمقروءة"""
    count = NotificationService.mark_all_as_read(str(current_user.id))
    return jsonify({'success': True, 'count': count})


@handler_bp.route('/my-reports')
@login_required
@handler_required
def my_reports():
    """قائمة تقارير السائس"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status_filter = request.args.get('status')
    
    # Build query
    query = HandlerReport.query.filter_by(handler_user_id=current_user.id)
    
    if date_from:
        query = query.filter(HandlerReport.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        query = query.filter(HandlerReport.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if status_filter:
        from k9.models.models_handler_daily import ReportStatus
        query = query.filter_by(status=ReportStatus[status_filter])
    
    # Pagination
    pagination = query.order_by(HandlerReport.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Summary stats
    from k9.models.models_handler_daily import ReportStatus
    summary = {
        'total': HandlerReport.query.filter_by(handler_user_id=current_user.id).count(),
        'draft': HandlerReport.query.filter_by(handler_user_id=current_user.id, status=ReportStatus.DRAFT).count(),
        'pending': HandlerReport.query.filter_by(handler_user_id=current_user.id, status=ReportStatus.SUBMITTED).count(),
        'approved': HandlerReport.query.filter_by(handler_user_id=current_user.id, status=ReportStatus.APPROVED).count(),
    }
    
    return render_template('handler/my_reports.html',
                         page_title='تقاريري',
                         reports=pagination.items,
                         pagination=pagination,
                         summary=summary)


@handler_bp.route('/api/unread-count')
@login_required
@handler_required
def get_unread_count():
    """API: الحصول على عدد الإشعارات غير المقروءة"""
    count = len(NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True
    ))
    return jsonify({'count': count})


@handler_bp.route('/reports/<report_id>/delete', methods=['POST'])
@login_required
@handler_required
def delete_report(report_id):
    """حذف تقرير (مسودة فقط)"""
    report = HandlerReport.query.get_or_404(report_id)
    
    # Verify ownership
    if str(report.handler_user_id) != str(current_user.id):
        return jsonify({'success': False, 'error': 'غير مصرح لك بحذف هذا التقرير'})
    
    # Can only delete drafts
    from k9.models.models_handler_daily import ReportStatus
    if report.status != ReportStatus.DRAFT:
        return jsonify({'success': False, 'error': 'لا يمكن حذف التقرير بعد إرساله'})
    
    db.session.delete(report)
    db.session.commit()
    
    return jsonify({'success': True})


# Context processor for notification links
@handler_bp.app_context_processor
def utility_processor():
    """إضافة دوال مساعدة لجميع templates"""
    def get_notification_link(notification):
        """الحصول على رابط الإشعار"""
        if not notification.related_type or not notification.related_id:
            return '#'
        
        if notification.related_type == 'HandlerReport':
            return url_for('handler.view_report', report_id=notification.related_id)
        elif notification.related_type == 'DailyScheduleItem':
            return url_for('handler.dashboard')
        
        return '#'
    
    return dict(get_notification_link=get_notification_link)
