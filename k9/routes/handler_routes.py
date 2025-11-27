"""
مسارات واجهة السائس
Handler Interface Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from k9.services.handler_service import (
    DailyScheduleService, HandlerReportService, ShiftReportService, NotificationService, AttachmentService
)
from k9.models.models_handler_daily import (
    HandlerReport, HandlerReportHealth, HandlerReportTraining,
    HandlerReportCare, HandlerReportBehavior, HandlerReportIncident,
    ShiftReport, ShiftReportHealth, ShiftReportBehavior, ShiftReportIncident, ShiftReportAttachment,
    TrainingType, BehaviorType, IncidentType, StoolColor, StoolShape,
    HealthCheckStatus
)
from k9.models.models import UserRole, Dog, User
from k9.utils.permissions_new import has_permission
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


# Helper functions for form parsing
HEALTH_FIELDS = ['eyes', 'nose', 'ears', 'mouth', 'teeth', 'gums', 
                 'front_limbs', 'back_limbs', 'hair', 'tail', 'rear']


def parse_health_data(form_data, health_object):
    """Parse health section data from form and update health object"""
    for field in HEALTH_FIELDS:
        status_val = form_data.get(f'{field}_status')
        # Always set status - either to the selected value or None if cleared
        if status_val:
            setattr(health_object, f'{field}_status', HealthCheckStatus(status_val))
        else:
            setattr(health_object, f'{field}_status', None)
        # Always update notes (can be empty string to clear)
        setattr(health_object, f'{field}_notes', form_data.get(f'{field}_notes'))


def parse_training_data(form_data, report):
    """Parse training section data from form and create training sessions"""
    training_types_map = {
        'fitness': TrainingType.FITNESS,
        'agility': TrainingType.AGILITY,
        'obedience': TrainingType.OBEDIENCE,
        'ball': TrainingType.BALL,
        'explosives': TrainingType.EXPLOSIVES,
        'other': TrainingType.OTHER
    }
    
    for key, training_type in training_types_map.items():
        description = form_data.get(f'training_{key}_description')
        time_from_str = form_data.get(f'training_{key}_from')
        time_to_str = form_data.get(f'training_{key}_to')
        notes = form_data.get(f'training_{key}_notes')
        
        # Only create if at least one field is filled
        if description or time_from_str or time_to_str or notes:
            try:
                time_from = datetime.strptime(time_from_str, '%H:%M').time() if time_from_str else None
                time_to = datetime.strptime(time_to_str, '%H:%M').time() if time_to_str else None
            except ValueError:
                continue  # Skip invalid time formats
            
            training_session = HandlerReportTraining(  # type: ignore
                report_id=report.id,
                training_type=training_type,
                description=description,
                time_from=time_from,
                time_to=time_to,
                notes=notes
            )
            db.session.add(training_session)


def parse_care_data(form_data, care_object):
    """Parse care section data from form and update care object"""
    care_object.food_amount = form_data.get('food_amount')
    care_object.food_type = form_data.get('food_type')
    care_object.supplements = form_data.get('supplements')
    care_object.water_amount = form_data.get('water_amount')
    care_object.grooming_done = bool(form_data.get('grooming_done'))
    care_object.washing_done = bool(form_data.get('washing_done'))
    care_object.excretion_location = form_data.get('excretion_location')
    
    # Stool color
    stool_color_val = form_data.get('stool_color')
    if stool_color_val:
        care_object.stool_color = StoolColor(stool_color_val)
    
    # Stool shape
    stool_shape_val = form_data.get('stool_shape')
    if stool_shape_val:
        care_object.stool_shape = StoolShape(stool_shape_val)


def parse_behavior_data(form_data, behavior_object):
    """Parse behavior section data from form and update behavior object"""
    behavior_object.good_behavior_notes = form_data.get('good_behavior_notes')
    behavior_object.bad_behavior_notes = form_data.get('bad_behavior_notes')


def parse_incidents_data(form_data, report):
    """Parse incidents section data from form and create incident records"""
    suspicion_cases = form_data.get('suspicion_cases')
    detection_cases = form_data.get('detection_cases')
    
    if suspicion_cases:
        suspicion_incident = HandlerReportIncident(  # type: ignore
            report_id=report.id,
            incident_type=IncidentType.SUSPICION,
            description=suspicion_cases
        )
        db.session.add(suspicion_incident)
    
    if detection_cases:
        detection_incident = HandlerReportIncident(  # type: ignore
            report_id=report.id,
            incident_type=IncidentType.DETECTION,
            description=detection_cases
        )
        db.session.add(detection_incident)


def parse_shift_incidents_data(form_data, shift_report, request_obj):
    """Parse shift report incidents and handle file uploads"""
    suspicion_cases = form_data.get('suspicion_cases')
    detection_cases = form_data.get('detection_cases')
    
    # Handle suspicion incident
    if suspicion_cases:
        suspicion_incident = ShiftReportIncident(  # type: ignore
            shift_report_id=shift_report.id,
            incident_type=IncidentType.SUSPICION,
            description=suspicion_cases
        )
        db.session.add(suspicion_incident)
        db.session.flush()  # Get the incident ID
        
        # Handle file uploads for suspicion
        suspicion_files = request_obj.files.getlist('suspicion_attachments')
        if suspicion_files:
            for file in suspicion_files:
                if file and file.filename:
                    attachment, error = AttachmentService.save_attachment(
                        file=file,
                        incident_id=str(suspicion_incident.id),
                        upload_folder='uploads/shift_reports'
                    )
                    if error:
                        flash(f'خطأ في رفع المرفق: {error}', 'warning')
    
    # Handle detection incident
    if detection_cases:
        detection_incident = ShiftReportIncident(  # type: ignore
            shift_report_id=shift_report.id,
            incident_type=IncidentType.DETECTION,
            description=detection_cases
        )
        db.session.add(detection_incident)
        db.session.flush()  # Get the incident ID
        
        # Handle file uploads for detection
        detection_files = request_obj.files.getlist('detection_attachments')
        if detection_files:
            for file in detection_files:
                if file and file.filename:
                    attachment, error = AttachmentService.save_attachment(
                        file=file,
                        incident_id=str(detection_incident.id),
                        upload_folder='uploads/shift_reports'
                    )
                    if error:
                        flash(f'خطأ في رفع المرفق: {error}', 'warning')


@handler_bp.route('/dashboard')
@login_required
@handler_required
def dashboard():
    """لوحة تحكم السائس"""
    from k9.models.models import Project
    from k9.models.models_handler_daily import ReportStatus, ShiftReport
    from dateutil.relativedelta import relativedelta
    
    today = date.today()
    
    # Get project and assigned dog
    project = None
    assigned_dog = None
    if current_user.project_id:
        project = Project.query.get(current_user.project_id)
    if current_user.dog_id:
        assigned_dog = Dog.query.get(current_user.dog_id)
    
    # Get active schedule (today or tomorrow) with actual date
    today_schedule, schedule_date = DailyScheduleService.get_active_handler_schedule(
        str(current_user.id)
    )
    
    # Use schedule_date if available, otherwise use today
    effective_date = schedule_date if schedule_date else today
    
    # Determine if showing today's or tomorrow's schedule
    schedule_is_for_tomorrow = False
    if schedule_date and schedule_date > today:
        schedule_is_for_tomorrow = True
    
    # Add shift report status to each schedule item
    for item in today_schedule:
        shift_report = ShiftReport.query.filter_by(schedule_item_id=item.id).first()
        item.shift_report = shift_report
    
    # Get dogs worked with on the effective date and their report status
    dogs_worked_today = HandlerReportService.get_dogs_worked_today(str(current_user.id), effective_date)
    
    # Get notifications - optimized to avoid duplicate query
    all_unread_notifications = NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True
    )
    unread_count = len(all_unread_notifications)
    recent_notifications = all_unread_notifications[:5]
    
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
                         schedule_date=schedule_date.strftime('%Y-%m-%d') if schedule_date else None,
                         schedule_is_for_tomorrow=schedule_is_for_tomorrow,
                         project=project,
                         assigned_dog=assigned_dog,
                         today_schedule=today_schedule,
                         dogs_worked_today=dogs_worked_today,
                         recent_notifications=recent_notifications,
                         unread_count=unread_count,
                         recent_reports=recent_reports,
                         stats=stats)


@handler_bp.route('/daily-reports/select', methods=['GET'])
@login_required
@handler_required
def select_daily_report():
    """عرض الكلاب المتاحة لإنشاء تقرير يومي"""
    if not has_permission("handlers.reports.view"):
        return redirect("/unauthorized")
    
    today = date.today()
    target_date_str = request.args.get('date')
    
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('تاريخ غير صحيح', 'danger')
            return redirect(url_for('handler.dashboard'))
    else:
        target_date = today
    
    # Get all dogs worked with on target date and their report status
    dogs_info = HandlerReportService.get_dogs_worked_today(str(current_user.id), target_date)
    
    return render_template('handler/select_daily_report.html',
                         page_title='اختر كلب لإنشاء تقرير يومي',
                         dogs_info=dogs_info,
                         target_date=target_date,
                         today=today)


@handler_bp.route('/report/new', methods=['GET', 'POST'])
@login_required
@handler_required
def new_report():
    """إنشاء تقرير يومي جديد"""
    if not has_permission("handlers.reports.create"):
        return redirect("/unauthorized")
    
    from k9.models.models import Shift
    from k9.models.models_handler_daily import DailyScheduleItem, ReportType
    
    if request.method == 'POST':
        action = request.form.get('action', 'save_draft')
        dog_id = request.form.get('dog_id')
        schedule_item_id = request.form.get('schedule_item_id')
        location = request.form.get('location')
        report_date = request.form.get('date')
        
        # Parse date with error handling
        if report_date:
            try:
                report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
            except ValueError:
                flash('تاريخ غير صحيح', 'danger')
                return redirect(url_for('handler.new_report'))
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
        
        # Update health section using helper function
        if report.health:
            parse_health_data(request.form, report.health)
        
        # Training section using helper function
        parse_training_data(request.form, report)
        
        # Care section using helper function
        if report.care:
            parse_care_data(request.form, report.care)
        
        # Behavior section using helper function
        if report.behavior:
            parse_behavior_data(request.form, report.behavior)
        
        # Incidents section using helper function
        parse_incidents_data(request.form, report)
        
        # Handle file attachments
        files = request.files.getlist('attachments')
        descriptions = request.form.getlist('attachment_descriptions')
        
        attachment_errors = []
        for i, file in enumerate(files):
            if file and file.filename:
                description = descriptions[i] if i < len(descriptions) else None
                attachment, error = AttachmentService.save_report_attachment(
                    file=file,
                    report_id=str(report.id),
                    description=description
                )
                if error:
                    attachment_errors.append(f"{file.filename}: {error}")
        
        # Show attachment errors as warnings (not fatal)
        if attachment_errors:
            for err in attachment_errors:
                flash(f'خطأ في المرفق - {err}', 'warning')
        
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
    dog_id = request.args.get('dog_id')
    report_date_str = request.args.get('date')
    
    # Parse report date with error handling
    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('تاريخ غير صحيح', 'danger')
            return redirect(url_for('handler.dashboard'))
    else:
        report_date = today
    
    # Get schedule item if provided
    schedule_item = None
    if schedule_item_id:
        schedule_item = DailyScheduleItem.query.get(schedule_item_id)
    
    # Get assigned dog
    assigned_dog = None
    if current_user.dog_id:
        assigned_dog = Dog.query.get(current_user.dog_id)
    
    # Get pre-population data from shift reports if dog_id provided
    shift_reports = []
    prepopulated_data = {}
    if dog_id:
        shift_reports = HandlerReportService.get_shift_reports_for_prepopulation(dog_id, report_date)
        
        # Compile data from shift reports for pre-population
        if shift_reports:
            # Aggregate health data from all shift reports
            health_notes = {}
            for sr in shift_reports:
                if sr.health:
                    for field in ['eyes', 'nose', 'ears', 'mouth', 'teeth', 'gums', 
                                 'front_limbs', 'back_limbs', 'hair', 'tail', 'rear']:
                        status = getattr(sr.health, f'{field}_status', None)
                        notes = getattr(sr.health, f'{field}_notes', None)
                        if status or notes:
                            if field not in health_notes:
                                health_notes[field] = {'status': status, 'notes': []}
                            if notes:
                                health_notes[field]['notes'].append(notes)
            
            prepopulated_data['health'] = health_notes
            
            # Aggregate behavior notes
            good_behaviors = []
            bad_behaviors = []
            for sr in shift_reports:
                if sr.behavior:
                    if sr.behavior.good_behavior_notes:
                        good_behaviors.append(sr.behavior.good_behavior_notes)
                    if sr.behavior.bad_behavior_notes:
                        bad_behaviors.append(sr.behavior.bad_behavior_notes)
            
            prepopulated_data['good_behavior'] = '\n'.join(good_behaviors) if good_behaviors else ''
            prepopulated_data['bad_behavior'] = '\n'.join(bad_behaviors) if bad_behaviors else ''
            
            # List incidents
            incidents = {'suspicion': [], 'detection': []}
            for sr in shift_reports:
                for incident in sr.incidents:  # type: ignore
                    if incident.incident_type == IncidentType.SUSPICION:
                        incidents['suspicion'].append(incident)
                    elif incident.incident_type == IncidentType.DETECTION:
                        incidents['detection'].append(incident)
            
            prepopulated_data['incidents'] = incidents
    
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
                         shifts=shifts,
                         shift_reports=shift_reports,
                         prepopulated_data=prepopulated_data,
                         report_date=report_date.strftime('%Y-%m-%d'),
                         selected_dog_id=dog_id)


@handler_bp.route('/report/<report_id>/edit', methods=['GET', 'POST'])
@login_required
@handler_required
def edit_report(report_id):
    """تعديل التقرير اليومي"""
    if not has_permission("handlers.reports.edit"):
        return redirect("/unauthorized")
    
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
        # Update general info
        report.location = request.form.get('location')
        
        # Update health section using helper function
        if report.health:
            parse_health_data(request.form, report.health)
        
        # Update training - delete old and create new
        for training in report.training_sessions:
            db.session.delete(training)
        parse_training_data(request.form, report)
        
        # Update care section using helper function
        if report.care:
            parse_care_data(request.form, report.care)
        
        # Update behavior section using helper function
        if report.behavior:
            parse_behavior_data(request.form, report.behavior)
        
        # Update incidents - delete old and create new
        for incident in report.incidents:
            db.session.delete(incident)
        parse_incidents_data(request.form, report)
        
        # Handle new file attachments
        files = request.files.getlist('attachments')
        descriptions = request.form.getlist('attachment_descriptions')
        
        attachment_errors = []
        for i, file in enumerate(files):
            if file and file.filename:
                description = descriptions[i] if i < len(descriptions) else None
                attachment, error = AttachmentService.save_report_attachment(
                    file=file,
                    report_id=str(report.id),
                    description=description
                )
                if error:
                    attachment_errors.append(f"{file.filename}: {error}")
        
        # Show attachment errors as warnings
        if attachment_errors:
            for err in attachment_errors:
                flash(f'خطأ في المرفق - {err}', 'warning')
        
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


@handler_bp.route('/shift-report/<report_id>')
@login_required
@handler_required
def view_shift_report(report_id):
    """عرض تقرير الوردية"""
    from k9.models.models_handler_daily import ShiftReport
    
    shift_report = ShiftReport.query.get_or_404(report_id)
    
    # Verify ownership
    if str(shift_report.handler_user_id) != str(current_user.id):
        flash('غير مصرح لك بعرض هذا التقرير', 'danger')
        return redirect(url_for('handler.dashboard'))
    
    return render_template('handler/view_shift_report.html',
                         page_title='عرض تقرير الوردية',
                         shift_report=shift_report)


@handler_bp.route('/notifications')
@login_required
@handler_required
def notifications():
    """عرض الإشعارات"""
    if not has_permission("handlers.notifications.view"):
        return redirect("/unauthorized")
    
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
    if not has_permission("handlers.general.access"):
        return redirect("/unauthorized")
    
    count = len(NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True
    ))
    return jsonify({'count': count})


@handler_bp.route('/reports/<report_id>/delete', methods=['POST'])
@login_required
@handler_required
def delete_report(report_id):
    """حذف تقرير (مسودة فقط)"""
    if not has_permission("handlers.reports.delete"):
        return redirect("/unauthorized")
    
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


@handler_bp.route('/shift-report/new/<schedule_item_id>', methods=['GET', 'POST'])
@login_required
@handler_required
def new_shift_report(schedule_item_id):
    """إنشاء تقرير وردية جديد"""
    from k9.models.models_handler_daily import DailyScheduleItem, ReportStatus
    
    # Get schedule item
    schedule_item = DailyScheduleItem.query.get_or_404(schedule_item_id)
    
    # Verify ownership - check if this schedule item belongs to current handler
    if str(schedule_item.handler_user_id) != str(current_user.id):
        flash('غير مصرح لك بإنشاء تقرير لهذه الوردية', 'danger')
        return redirect(url_for('handler.dashboard'))
    
    # Check if shift report already exists for this schedule item
    existing_report = ShiftReport.query.filter_by(schedule_item_id=schedule_item_id).first()
    if existing_report:
        flash('يوجد تقرير وردية لهذا العنصر بالفعل', 'warning')
        return redirect(url_for('handler.dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action', 'save_draft')
        location = request.form.get('location')
        
        # Get dog_id from schedule item or form
        dog_id = schedule_item.dog_id if schedule_item.dog_id else request.form.get('dog_id')
        
        if not dog_id:
            flash('يجب تحديد الكلب', 'danger')
            return redirect(url_for('handler.new_shift_report', schedule_item_id=schedule_item_id))
        
        # Create shift report
        shift_report, error = ShiftReportService.create_shift_report(
            schedule_item_id=schedule_item_id,
            handler_user_id=str(current_user.id),
            dog_id=str(dog_id),
            project_id=str(current_user.project_id) if current_user.project_id else str(schedule_item.schedule.project_id),
            report_date=schedule_item.schedule.date,
            location=location
        )
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('handler.dashboard'))
        
        # Update Health section using helper function
        if shift_report.health:
            parse_health_data(request.form, shift_report.health)
        
        # Behavior section using helper function
        if shift_report.behavior:
            parse_behavior_data(request.form, shift_report.behavior)
        
        # Incidents section with file uploads using helper function
        parse_shift_incidents_data(request.form, shift_report, request)
        
        db.session.commit()
        
        # Submit if requested
        if action == 'submit':
            success, error = ShiftReportService.submit_shift_report(str(shift_report.id))
            if success:
                flash('تم إرسال تقرير الوردية للمراجعة بنجاح', 'success')
                return redirect(url_for('handler.dashboard'))
            else:
                flash(f'تم حفظ التقرير لكن فشل الإرسال: {error}', 'warning')
        else:
            flash('تم حفظ تقرير الوردية كمسودة', 'success')
        
        return redirect(url_for('handler.dashboard'))
    
    # GET request
    # Get dog from schedule item
    dog = None
    if schedule_item.dog_id:
        dog = Dog.query.get(schedule_item.dog_id)
    
    return render_template('handler/new_shift_report.html',
                         page_title='تقرير وردية جديد',
                         schedule_item=schedule_item,
                         dog=dog,
                         today=schedule_item.schedule.date.strftime('%Y-%m-%d'))


@handler_bp.route('/shift-report/submit/<shift_report_id>', methods=['POST'])
@login_required
@handler_required
def submit_shift_report(shift_report_id):
    """إرسال تقرير الوردية للمراجعة"""
    shift_report = ShiftReport.query.get_or_404(shift_report_id)
    
    # Verify ownership
    if str(shift_report.handler_user_id) != str(current_user.id):
        flash('غير مصرح لك بإرسال هذا التقرير', 'danger')
        return redirect(url_for('handler.dashboard'))
    
    # Submit the report
    success, error = ShiftReportService.submit_shift_report(shift_report_id)
    
    if success:
        flash('تم إرسال تقرير الوردية للمراجعة بنجاح', 'success')
    else:
        flash(f'فشل إرسال التقرير: {error}', 'danger')
    
    return redirect(url_for('handler.dashboard'))


@handler_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """صفحة البروفايل للسائس ومسؤول المشروع"""
    if not has_permission("handlers.profile.view"):
        return redirect("/unauthorized")
    
    from werkzeug.security import check_password_hash, generate_password_hash
    from k9.utils.security_utils import PasswordValidator, SecurityHelper
    from k9.models.models import Employee, AuditAction
    from k9.utils.utils import log_audit
    from werkzeug.utils import secure_filename
    import os
    
    # التحقق من أن المستخدم سائس أو مسؤول مشروع
    if current_user.role not in [UserRole.HANDLER, UserRole.PROJECT_MANAGER]:
        flash('هذه الصفحة غير متاحة لك', 'error')
        return redirect(url_for('main.index'))
    
    # الحصول على بيانات الموظف المرتبط
    employee = current_user.employee if current_user.employee else None
    
    if not employee:
        flash('لا يوجد موظف مرتبط بهذا الحساب', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # تغيير كلمة المرور
        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_password:
                flash('يرجى إدخال كلمة المرور الحالية', 'error')
            elif not check_password_hash(current_user.password_hash, current_password):
                flash('كلمة المرور الحالية غير صحيحة', 'error')
            elif not new_password or not confirm_password:
                flash('يرجى إدخال كلمة المرور الجديدة وتأكيدها', 'error')
            elif new_password != confirm_password:
                flash('كلمة المرور الجديدة وتأكيدها غير متطابقتين', 'error')
            else:
                is_valid, error_message = PasswordValidator.validate_password(new_password)
                if not is_valid:
                    flash(f'كلمة المرور غير صالحة: {error_message}', 'error')
                elif check_password_hash(current_user.password_hash, new_password):
                    flash('كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية', 'error')
                else:
                    try:
                        current_user.password_hash = generate_password_hash(new_password)
                        current_user.password_changed_at = datetime.utcnow()
                        current_user.failed_login_attempts = 0
                        current_user.account_locked_until = None
                        db.session.commit()
                        
                        log_audit(current_user.id, AuditAction.UPDATE, 'User', current_user.id, 
                                 f'المستخدم {current_user.username} غيّر كلمة المرور')
                        flash('تم تغيير كلمة المرور بنجاح', 'success')
                        return redirect(url_for('handler.profile'))
                    except Exception as e:
                        db.session.rollback()
                        flash(f'حدث خطأ أثناء تغيير كلمة المرور: {str(e)}', 'error')
        
        # تحديث البيانات الشخصية
        elif action == 'update_info':
            try:
                phone = request.form.get('phone', '').strip()
                current_residence = request.form.get('current_residence', '').strip()
                
                # تحديث رقم الجوال في Employee
                if phone:
                    employee.phone = phone
                
                # تحديث عنوان السكن
                if current_residence:
                    employee.current_residence = current_residence
                
                db.session.commit()
                log_audit(current_user.id, AuditAction.UPDATE, 'Employee', employee.id, 
                         f'تحديث البيانات الشخصية للموظف {employee.name}')
                flash('تم تحديث البيانات بنجاح', 'success')
                return redirect(url_for('handler.profile'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'حدث خطأ أثناء تحديث البيانات: {str(e)}', 'error')
        
        # تحديث الصورة
        elif action == 'update_photo':
            if 'photo' in request.files:
                photo_file = request.files['photo']
                if photo_file and photo_file.filename:
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    filename = photo_file.filename
                    if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        try:
                            # إنشاء مجلد للصور إذا لم يكن موجوداً
                            upload_folder = os.path.join('uploads', 'employee_photos')
                            os.makedirs(upload_folder, exist_ok=True)
                            
                            # حفظ الملف باسم آمن
                            filename = secure_filename(f"{employee.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{filename.rsplit('.', 1)[1].lower()}")
                            file_path = os.path.join(upload_folder, filename)
                            photo_file.save(file_path)
                            
                            # حذف الصورة القديمة إذا كانت موجودة
                            if employee.employee_photo and os.path.exists(employee.employee_photo):
                                try:
                                    os.remove(employee.employee_photo)
                                except:
                                    pass
                            
                            # تحديث مسار الصورة في قاعدة البيانات
                            employee.employee_photo = file_path
                            db.session.commit()
                            
                            log_audit(current_user.id, AuditAction.UPDATE, 'Employee', employee.id, 
                                     f'تحديث صورة الموظف {employee.name}')
                            flash('تم تحديث الصورة بنجاح', 'success')
                            return redirect(url_for('handler.profile'))
                            
                        except Exception as e:
                            db.session.rollback()
                            flash(f'حدث خطأ أثناء رفع الصورة: {str(e)}', 'error')
                    else:
                        flash('نوع الملف غير مسموح. يُسمح فقط بـ PNG, JPG, JPEG, GIF', 'error')
                else:
                    flash('يرجى اختيار صورة', 'error')
    
    return render_template('handler/profile.html', employee=employee)


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
        elif notification.related_type == 'Task':
            # Direct link to task details for handler
            return url_for('tasks.handler_view', task_id=notification.related_id)
        
        return '#'
    
    return dict(get_notification_link=get_notification_link)
