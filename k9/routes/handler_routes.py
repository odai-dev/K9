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
from k9.models.models import UserRole, Dog
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
    today = date.today()
    
    # Get today's schedule
    schedule_items = DailyScheduleService.get_handler_schedule_for_date(
        str(current_user.id), today
    )
    
    # Get notifications
    notifications = NotificationService.get_user_notifications(
        str(current_user.id), unread_only=False, limit=10
    )
    unread_count = NotificationService.get_unread_count(str(current_user.id))
    
    # Get recent reports
    recent_reports = HandlerReport.query.filter_by(
        handler_user_id=current_user.id
    ).order_by(HandlerReport.date.desc()).limit(5).all()
    
    return render_template('handler/dashboard.html',
                         page_title='لوحة تحكم السائس',
                         schedule_items=schedule_items,
                         notifications=notifications,
                         unread_count=unread_count,
                         recent_reports=recent_reports,
                         today=today)


@handler_bp.route('/report/new', methods=['GET', 'POST'])
@login_required
@handler_required
def new_report():
    """إنشاء تقرير يومي جديد"""
    if request.method == 'POST':
        dog_id = request.form.get('dog_id')
        schedule_item_id = request.form.get('schedule_item_id')
        location = request.form.get('location')
        
        # Check if can submit
        if schedule_item_id:
            can_submit, error_msg = HandlerReportService.can_submit_report(
                str(current_user.id), schedule_item_id
            )
            if not can_submit:
                flash(error_msg, 'danger')
                return redirect(url_for('handler.dashboard'))
        
        report, error = HandlerReportService.create_report(
            handler_user_id=str(current_user.id),
            dog_id=dog_id,
            schedule_item_id=schedule_item_id,
            project_id=str(current_user.project_id) if current_user.project_id else None,
            location=location
        )
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('handler.dashboard'))
        
        flash('تم إنشاء التقرير بنجاح', 'success')
        return redirect(url_for('handler.edit_report', report_id=str(report.id)))
    
    # GET request
    # Get assigned dog
    dog = None
    if current_user.dog_id:
        dog = Dog.query.get(current_user.dog_id)
    
    # Get today's schedule item
    today = date.today()
    schedule_items = DailyScheduleService.get_handler_schedule_for_date(
        str(current_user.id), today
    )
    
    return render_template('handler/new_report.html',
                         page_title='تقرير يومي جديد',
                         dog=dog,
                         schedule_items=schedule_items)


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
    all_notifications = NotificationService.get_user_notifications(
        str(current_user.id), limit=100
    )
    
    return render_template('handler/notifications.html',
                         page_title='الإشعارات',
                         notifications=all_notifications)


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
