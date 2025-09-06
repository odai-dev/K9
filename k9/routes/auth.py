from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from k9.models.models import User, UserRole, AuditLog
from k9.utils.utils import log_audit
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = bool(request.form.get('remember', False))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_active and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log successful login
            log_audit(user.id, 'LOGIN', 'User', str(user.id), {'username': username})
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'LOGOUT', 'User', str(current_user.id), {'username': current_user.username})
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # Check if any admin users exist
    admin_exists = User.query.filter_by(role=UserRole.GENERAL_ADMIN).first()
    if admin_exists:
        flash('تم إعداد النظام بالفعل', 'info')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            # Create the first admin user
            admin_user = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(request.form['password']),
                role=UserRole.GENERAL_ADMIN,
                full_name=request.form['full_name'],
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            flash('تم إنشاء حساب المدير الأول بنجاح', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'error')
    
    return render_template('auth/setup.html')

@auth_bp.route('/create_manager', methods=['GET', 'POST'])
@login_required
def create_manager():
    # Only general admins can create project managers
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            # Create new project manager
            manager = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(request.form['password']),
                role=UserRole.PROJECT_MANAGER,
                full_name=request.form['full_name'],
                active=True,
                allowed_sections=request.form.getlist('allowed_sections')
            )
            
            db.session.add(manager)
            db.session.flush()  # Get the manager ID
            
            # Link the employee to the user account if employee was selected
            if request.form.get('employee_id'):
                from k9.models.models import Employee
                employee = Employee.query.get(request.form['employee_id'])
                if employee:
                    employee.user_account_id = manager.id
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'User', str(manager.id), 
                     {'username': manager.username, 'role': manager.role.value})
            
            flash('تم إنشاء حساب مدير المشروع بنجاح', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'error')
    
    # Available sections that can be assigned to project managers
    available_sections = [
        {'key': 'dogs', 'name': 'إدارة الكلاب'},
        {'key': 'employees', 'name': 'إدارة الموظفين'},
        {'key': 'training', 'name': 'التدريب'},
        {'key': 'veterinary', 'name': 'الطبابة'},
        {'key': 'breeding', 'name': 'التكاثر'},
        {'key': 'projects', 'name': 'المشاريع'},
        {'key': 'attendance', 'name': 'الحضور والغياب'},
        {'key': 'reports', 'name': 'التقارير'},
    ]
    
    # Get employees who are project managers and don't have user accounts yet
    from k9.models.models import Employee, EmployeeRole
    employees_without_accounts = Employee.query.filter_by(
        role=EmployeeRole.PROJECT_MANAGER,
        user_account_id=None, 
        is_active=True
    ).all()
    
    return render_template('auth/create_manager.html', 
                         available_sections=available_sections,
                         employees=employees_without_accounts)
