"""
مسارات إدارة الورديات
Shift Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, time
from app import db
from k9.models.models import Shift
from k9.utils.permission_decorators import require_permission

shift_bp = Blueprint('shift', __name__, url_prefix='/supervisor/shifts')


@shift_bp.route('/')
@login_required
@require_permission('attendance.view')
def index():
    """عرض جميع الورديات"""
    shifts = Shift.query.filter_by(is_active=True).order_by(Shift.start_time).all()
    return render_template('shifts/index.html',
                         page_title='إدارة الورديات',
                         shifts=shifts)


@shift_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('attendance.create')
def create():
    """إنشاء وردية جديدة"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            
            # التحقق من البيانات
            if not name or not start_time_str or not end_time_str:
                flash('جميع الحقول مطلوبة', 'danger')
                return redirect(url_for('shift.create'))
            
            # تحويل الوقت
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # التحقق من صحة الأوقات
            if start_time == end_time:
                flash('وقت النهاية يجب أن يكون مختلفاً عن وقت البداية', 'danger')
                return redirect(url_for('shift.create'))
            
            # للورديات التي تبدأ بعد وقت النهاية (overnight shifts)
            # نتحقق من أنها منطقية: يجب أن تبدأ في المساء/الليل وتنتهي في الصباح/الظهر
            if start_time > end_time:
                # التحقق من أن البداية بعد الساعة 12 ظهراً والنهاية قبل الساعة 3 عصراً
                # هذا يسمح بورديات overnight معقولة ويمنع الأخطاء العرضية
                if start_time.hour < 12 or end_time.hour >= 15:
                    flash('وردية عبر منتصف الليل يجب أن تبدأ بعد 12 ظهراً وتنتهي قبل 3 عصراً. للورديات النهارية، تأكد من أن وقت النهاية بعد وقت البداية.', 'danger')
                    return redirect(url_for('shift.create'))
            
            # التحقق من عدم وجود وردية بنفس الاسم
            existing_shift = Shift.query.filter_by(name=name, is_active=True).first()
            if existing_shift:
                flash('يوجد وردية بنفس الاسم', 'danger')
                return redirect(url_for('shift.create'))
            
            # إنشاء الوردية
            shift = Shift(
                name=name,
                start_time=start_time,
                end_time=end_time,
                is_active=True
            )
            
            db.session.add(shift)
            db.session.commit()
            
            flash('تم إنشاء الوردية بنجاح', 'success')
            return redirect(url_for('shift.index'))
            
        except ValueError as e:
            flash('تنسيق الوقت غير صحيح. استخدم صيغة HH:MM', 'danger')
            return redirect(url_for('shift.create'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            return redirect(url_for('shift.create'))
    
    # GET request
    return render_template('shifts/create.html',
                         page_title='إضافة وردية جديدة')


@shift_bp.route('/<shift_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('attendance.edit')
def edit(shift_id):
    """تعديل وردية"""
    shift = Shift.query.get_or_404(shift_id)
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            
            # التحقق من البيانات
            if not name or not start_time_str or not end_time_str:
                flash('جميع الحقول مطلوبة', 'danger')
                return redirect(url_for('shift.edit', shift_id=shift_id))
            
            # تحويل الوقت
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # التحقق من صحة الأوقات
            if start_time == end_time:
                flash('وقت النهاية يجب أن يكون مختلفاً عن وقت البداية', 'danger')
                return redirect(url_for('shift.edit', shift_id=shift_id))
            
            # للورديات التي تبدأ بعد وقت النهاية (overnight shifts)
            # نتحقق من أنها منطقية: يجب أن تبدأ في المساء/الليل وتنتهي في الصباح/الظهر
            if start_time > end_time:
                # التحقق من أن البداية بعد الساعة 12 ظهراً والنهاية قبل الساعة 3 عصراً
                # هذا يسمح بورديات overnight معقولة ويمنع الأخطاء العرضية
                if start_time.hour < 12 or end_time.hour >= 15:
                    flash('وردية عبر منتصف الليل يجب أن تبدأ بعد 12 ظهراً وتنتهي قبل 3 عصراً. للورديات النهارية، تأكد من أن وقت النهاية بعد وقت البداية.', 'danger')
                    return redirect(url_for('shift.edit', shift_id=shift_id))
            
            # التحقق من عدم وجود وردية أخرى بنفس الاسم
            existing_shift = Shift.query.filter(
                Shift.name == name,
                Shift.id != shift_id,
                Shift.is_active == True
            ).first()
            if existing_shift:
                flash('يوجد وردية أخرى بنفس الاسم', 'danger')
                return redirect(url_for('shift.edit', shift_id=shift_id))
            
            # تحديث البيانات
            shift.name = name
            shift.start_time = start_time
            shift.end_time = end_time
            
            db.session.commit()
            
            flash('تم تحديث الوردية بنجاح', 'success')
            return redirect(url_for('shift.index'))
            
        except ValueError as e:
            flash('تنسيق الوقت غير صحيح. استخدم صيغة HH:MM', 'danger')
            return redirect(url_for('shift.edit', shift_id=shift_id))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            return redirect(url_for('shift.edit', shift_id=shift_id))
    
    # GET request
    return render_template('shifts/edit.html',
                         page_title='تعديل الوردية',
                         shift=shift)


@shift_bp.route('/<shift_id>/delete', methods=['POST'])
@login_required
@require_permission('attendance.edit')
def delete(shift_id):
    """تعطيل وردية (soft delete)"""
    try:
        shift = Shift.query.get_or_404(shift_id)
        
        # التحقق من عدم استخدام الوردية في أي جداول (بغض النظر عن الحالة أو التاريخ)
        from k9.models.models_handler_daily import DailyScheduleItem, ShiftReport
        
        # البحث عن أي عناصر جدول تستخدم هذه الوردية
        schedule_items_count = DailyScheduleItem.query.filter_by(shift_id=shift_id).count()
        
        if schedule_items_count > 0:
            flash(f'لا يمكن تعطيل الوردية لأنها مستخدمة في {schedule_items_count} جدول. يجب حذف هذه الجداول أولاً.', 'danger')
            return redirect(url_for('shift.index'))
        
        # البحث عن أي تقارير وردية تستخدم هذه الوردية
        # تقارير الوردية مرتبطة بـ schedule_item الذي يحتوي على shift_id
        shift_reports_count = ShiftReport.query.join(DailyScheduleItem).filter(
            DailyScheduleItem.shift_id == shift_id
        ).count()
        
        if shift_reports_count > 0:
            flash(f'لا يمكن تعطيل الوردية لأنها مرتبطة بـ {shift_reports_count} تقرير. يجب حذف هذه التقارير أولاً.', 'danger')
            return redirect(url_for('shift.index'))
        
        # تعطيل الوردية بدلاً من حذفها
        shift.is_active = False
        db.session.commit()
        
        flash('تم تعطيل الوردية بنجاح', 'success')
        return redirect(url_for('shift.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('shift.index'))


@shift_bp.route('/api/active')
@login_required
@require_permission('attendance.view')
def api_active_shifts():
    """API لجلب الورديات النشطة (للاستخدام في النماذج)"""
    shifts = Shift.query.filter_by(is_active=True).order_by(Shift.start_time).all()
    
    shifts_data = []
    for shift in shifts:
        shifts_data.append({
            'id': str(shift.id),
            'name': shift.name,
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M')
        })
    
    return jsonify(shifts_data)
