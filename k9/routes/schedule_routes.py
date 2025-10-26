"""
مسارات إدارة الجداول اليومية
Daily Schedule Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from k9.services.handler_service import DailyScheduleService, NotificationService
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem
from k9.models.models import Employee, Dog, Shift, Project
from k9.decorators import admin_or_pm_required
from app import db


schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


@schedule_bp.route('/')
@login_required
@admin_or_pm_required
def index():
    """عرض جميع الجداول"""
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    project_id = request.args.get('project_id')
    
    query = DailySchedule.query
    
    if start_date:
        query = query.filter(DailySchedule.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(DailySchedule.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    schedules = query.order_by(DailySchedule.date.desc()).limit(50).all()
    
    # Get projects for filter
    projects = Project.query.filter_by(status='ACTIVE').all()
    
    return render_template('schedule/index.html',
                         page_title='الجداول اليومية',
                         schedules=schedules,
                         projects=projects)


@schedule_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def create():
    """إنشاء جدول يومي جديد"""
    if request.method == 'POST':
        schedule_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        project_id = request.form.get('project_id') or None
        notes = request.form.get('notes')
        
        schedule, error = DailyScheduleService.create_schedule(
            date=schedule_date,
            project_id=project_id,
            created_by_user_id=str(current_user.id),
            notes=notes
        )
        
        if error:
            flash(error, 'danger')
            return redirect(url_for('schedule.create'))
        
        flash('تم إنشاء الجدول اليومي بنجاح', 'success')
        return redirect(url_for('schedule.edit', schedule_id=str(schedule.id)))
    
    # GET request
    projects = Project.query.filter_by(status='ACTIVE').all()
    tomorrow = date.today() + timedelta(days=1)
    
    return render_template('schedule/create.html',
                         page_title='إنشاء جدول يومي',
                         projects=projects,
                         default_date=tomorrow)


@schedule_bp.route('/<schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def edit(schedule_id):
    """تعديل الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    # Check if locked
    if schedule.status.value == 'LOCKED':
        flash('الجدول مقفل ولا يمكن تعديله', 'warning')
        return redirect(url_for('schedule.view', schedule_id=schedule_id))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_item':
            employee_id = request.form.get('employee_id')
            dog_id = request.form.get('dog_id') or None
            shift_id = request.form.get('shift_id') or None
            
            item, error = DailyScheduleService.add_schedule_item(
                schedule_id=schedule_id,
                employee_id=employee_id,
                dog_id=dog_id,
                shift_id=shift_id
            )
            
            if error:
                flash(error, 'danger')
            else:
                flash('تمت إضافة العنصر بنجاح', 'success')
        
        elif action == 'update_status':
            item_id = request.form.get('item_id')
            new_status = request.form.get('status')
            
            if new_status == 'PRESENT':
                DailyScheduleService.mark_present(item_id)
                flash('تم تسجيل الحضور', 'success')
            elif new_status == 'ABSENT':
                reason = request.form.get('absence_reason', 'غير محدد')
                DailyScheduleService.mark_absent(item_id, reason)
                flash('تم تسجيل الغياب', 'success')
        
        elif action == 'replace':
            item_id = request.form.get('item_id')
            replacement_id = request.form.get('replacement_employee_id')
            reason = request.form.get('replacement_reason')
            notes = request.form.get('replacement_notes')
            
            DailyScheduleService.replace_employee(item_id, replacement_id, reason, notes)
            flash('تم تسجيل الاستبدال', 'success')
        
        elif action == 'lock':
            DailyScheduleService.lock_schedule(schedule_id)
            flash('تم إقفال الجدول', 'success')
            return redirect(url_for('schedule.view', schedule_id=schedule_id))
        
        return redirect(url_for('schedule.edit', schedule_id=schedule_id))
    
    # GET request
    employees = Employee.query.filter_by(is_active=True).all()
    dogs = Dog.query.filter_by(current_status='ACTIVE').all()
    shifts = Shift.query.filter_by(is_active=True).all()
    
    return render_template('schedule/edit.html',
                         page_title='تعديل الجدول اليومي',
                         schedule=schedule,
                         employees=employees,
                         dogs=dogs,
                         shifts=shifts)


@schedule_bp.route('/<schedule_id>')
@login_required
@admin_or_pm_required
def view(schedule_id):
    """عرض الجدول اليومي"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    return render_template('schedule/view.html',
                         page_title=f'الجدول اليومي - {schedule.date}',
                         schedule=schedule)


@schedule_bp.route('/<schedule_id>/item/<item_id>/delete', methods=['POST'])
@login_required
@admin_or_pm_required
def delete_item(schedule_id, item_id):
    """حذف عنصر من الجدول"""
    schedule = DailySchedule.query.get_or_404(schedule_id)
    
    if schedule.status.value == 'LOCKED':
        return jsonify({'success': False, 'error': 'الجدول مقفل'})
    
    item = DailyScheduleItem.query.get(item_id)
    if item and str(item.daily_schedule_id) == schedule_id:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'العنصر غير موجود'})
