"""
مسارات إدارة المستخدمين
User Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from k9.services.user_management_service import UserManagementService
from k9.models.models import User, UserRole, Project, Dog
from k9.decorators import admin_required
from werkzeug.utils import secure_filename
from app import app, db
import os
import tempfile


user_mgmt_bp = Blueprint('user_management', __name__, url_prefix='/admin/users')


@user_mgmt_bp.route('/')
@login_required
@admin_required
def index():
    """عرض جميع المستخدمين"""
    role_filter = request.args.get('role')
    project_filter = request.args.get('project_id')
    status_filter = request.args.get('status')
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=UserRole[role_filter])
    if project_filter:
        query = query.filter_by(project_id=project_filter)
    if status_filter:
        active = status_filter == 'active'
        query = query.filter_by(active=active)
    
    users = query.order_by(User.created_at.desc()).all()
    
    # Get projects for filter
    projects = Project.query.all()
    
    return render_template('admin/user_management/index.html',
                         page_title='إدارة المستخدمين',
                         users=users,
                         projects=projects,
                         user_roles=UserRole)


@user_mgmt_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """إنشاء حساب مستخدم جديد"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        role = request.form.get('role')
        project_id = request.form.get('project_id') or None
        dog_id = request.form.get('dog_id') or None
        
        if role == 'HANDLER':
            user, password, error = UserManagementService.create_handler_user(
                username=username,
                email=email,
                full_name=full_name,
                phone=phone,
                project_id=project_id,
                dog_id=dog_id
            )
        else:
            # For non-handlers, use standard user creation
            from werkzeug.security import generate_password_hash
            password = UserManagementService.generate_password()
            
            user = User(  # type: ignore
                username=username,
                email=email,
                full_name=full_name,
                password_hash=generate_password_hash(password),
                role=UserRole[role],
                phone=phone,
                project_id=project_id if role == 'PROJECT_MANAGER' else None,
                active=True
            )
            db.session.add(user)
            db.session.commit()
            error = None
        
        if error:
            flash(error, 'danger')
        else:
            # Show password on success page instead of flash message
            return render_template('admin/user_management/create_success.html',
                                 page_title='تم إنشاء المستخدم بنجاح',
                                 username=username,
                                 password=password,
                                 full_name=full_name,
                                 user_role=role)
    
    # GET request
    projects = Project.query.all()
    dogs = Dog.query.filter_by(current_status='ACTIVE').all()
    
    return render_template('admin/user_management/create.html',
                         page_title='إنشاء مستخدم جديد',
                         projects=projects,
                         dogs=dogs,
                         user_roles=UserRole)


@user_mgmt_bp.route('/bulk-import', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_import():
    """استيراد جماعي للمستخدمين"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)
        
        # Validate file extension
        allowed_extensions = {'xlsx', 'xls', 'csv'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash('نوع الملف غير مسموح. يجب أن يكون Excel أو CSV', 'danger')
            return redirect(request.url)
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp:
            file.save(tmp.name)
            temp_path = tmp.name
        
        try:
            # Import based on file type
            if file_ext == 'csv':
                results, error = UserManagementService.bulk_import_from_csv(temp_path)
            else:
                results, error = UserManagementService.bulk_import_from_excel(temp_path)
            
            if error:
                flash(error, 'danger')
            else:
                success_count = len(results['success'])
                error_count = len(results['errors'])
                
                flash(f'تم الاستيراد بنجاح! نجح: {success_count}, فشل: {error_count}', 'success')
                
                # Store results in session for display
                return render_template('admin/user_management/bulk_import_results.html',
                                     page_title='نتائج الاستيراد الجماعي',
                                     results=results)
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return redirect(url_for('user_management.index'))
    
    # GET request
    return render_template('admin/user_management/bulk_import.html',
                         page_title='استيراد جماعي للمستخدمين')


@user_mgmt_bp.route('/download-template')
@login_required
@admin_required
def download_template():
    """تحميل قالب Excel للاستيراد الجماعي"""
    import openpyxl
    from openpyxl.styles import Font, Alignment
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Users Template"
    
    # Headers
    headers = ['name', 'username', 'phone', 'email', 'project_id', 'dog_id', 'password']
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Add sample row
    ws.append([
        'محمد أحمد',
        'handler001',
        '0501234567',
        'handler001@k9.local',
        '',  # optional
        '',  # optional
        ''   # optional - will be generated if empty
    ])
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        wb.save(tmp.name)
        temp_path = tmp.name
    
    try:
        return send_file(
            temp_path,
            as_attachment=True,
            download_name='users_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    finally:
        # Schedule cleanup after send
        pass


@user_mgmt_bp.route('/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(user_id):
    """تفعيل/تعطيل حساب مستخدم"""
    user = User.query.get_or_404(user_id)
    
    if user.active:
        UserManagementService.deactivate_user(user_id)
        flash(f'تم تعطيل حساب {user.username}', 'success')
    else:
        UserManagementService.activate_user(user_id)
        flash(f'تم تفعيل حساب {user.username}', 'success')
    
    return redirect(url_for('user_management.index'))


@user_mgmt_bp.route('/<user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """إعادة تعيين كلمة المرور"""
    user = User.query.get_or_404(user_id)
    
    new_password, error = UserManagementService.reset_password(user_id)
    
    if error:
        flash(error, 'danger')
        return redirect(url_for('user_management.index'))
    else:
        # Show password on success page instead of flash message
        return render_template('admin/user_management/reset_success.html',
                             page_title='تم إعادة تعيين كلمة المرور',
                             username=user.username,
                             password=new_password,
                             full_name=user.full_name,
                             user_role=user.role.value)


@user_mgmt_bp.route('/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """تعديل بيانات المستخدم"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone') or None
        
        role = request.form.get('role')
        user.role = UserRole[role]
        
        project_id = request.form.get('project_id') or None
        dog_id = request.form.get('dog_id') or None
        
        user.project_id = project_id
        user.dog_id = dog_id
        
        db.session.commit()
        
        flash(f'تم تحديث بيانات المستخدم {user.username} بنجاح', 'success')
        return redirect(url_for('user_management.index'))
    
    # GET request
    projects = Project.query.all()
    dogs = Dog.query.filter_by(current_status='ACTIVE').all()
    
    return render_template('admin/user_management/edit.html',
                         page_title=f'تعديل مستخدم - {user.username}',
                         user=user,
                         projects=projects,
                         dogs=dogs)


@user_mgmt_bp.route('/<user_id>')
@login_required
@admin_required
def view(user_id):
    """عرض تفاصيل المستخدم - Redirect to edit page"""
    # Redirect to edit page since we don't have a separate view template
    return redirect(url_for('user_management.edit', user_id=user_id))
