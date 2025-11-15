from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, csrf
from k9.models.models import User, UserRole, AuditLog
from k9.utils.utils import log_audit
from k9.utils.security_utils import PasswordValidator, AccountLockoutManager, MFAManager, SecurityHelper
from k9.utils.validators import validate_yemen_phone
from k9.utils.permission_utils import has_permission
from sqlalchemy.exc import IntegrityError
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if not has_permission(current_user, "auth.login.access"):
        return redirect("/unauthorized")
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = bool(request.form.get('remember', False))
        mfa_token = request.form.get('mfa_token', '').strip()
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
            return render_template('login.html')
        
        # Check if account is locked
        if AccountLockoutManager.is_account_locked(user):
            remaining_time = AccountLockoutManager.get_lockout_time_remaining(user)
            flash(f'الحساب مؤقت لمدة {remaining_time} دقيقة بسبب محاولات دخول فاشلة متكررة', 'error')
            SecurityHelper.log_security_event(user.id, 'LOCKED_ACCOUNT_ACCESS_ATTEMPT', {
                'username': username,
                'ip': request.remote_addr
            })
            return render_template('login.html')
        
        # Verify password
        if not (user.is_active and check_password_hash(user.password_hash, password)):
            AccountLockoutManager.increment_failed_attempts(user)
            SecurityHelper.log_security_event(user.id, 'FAILED_LOGIN_ATTEMPT', {
                'username': username,
                'ip': request.remote_addr,
                'attempts': user.failed_login_attempts
            })
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
            return render_template('login.html')
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                # Show MFA form
                session['pending_user_id'] = user.id
                return render_template('auth/mfa_verify.html', user=user)
            
            # Verify MFA token
            mfa_valid = False
            if mfa_token.startswith('backup-'):
                # Backup code verification
                backup_code = mfa_token[7:]
                mfa_valid, new_codes = MFAManager.verify_backup_code(user.backup_codes or [], backup_code)
                if mfa_valid:
                    user.backup_codes = new_codes
                    db.session.commit()
                    SecurityHelper.log_security_event(user.id, 'BACKUP_CODE_USED', {'username': username})
            else:
                # TOTP verification
                mfa_valid = MFAManager.verify_totp(user.mfa_secret, mfa_token)
            
            if not mfa_valid:
                AccountLockoutManager.increment_failed_attempts(user)
                SecurityHelper.log_security_event(user.id, 'FAILED_MFA_ATTEMPT', {
                    'username': username,
                    'ip': request.remote_addr
                })
                flash('رمز المصادقة الثنائية غير صحيح', 'error')
                return render_template('auth/mfa_verify.html', user=user)
        
        # Security check: Ensure user has employee record (all users must be employees)
        from k9.models.models import Employee
        if not user.employee_id:
            SecurityHelper.log_security_event(user.id, 'LOGIN_DENIED_NO_EMPLOYEE', {
                'username': username,
                'reason': 'User account not linked to employee record'
            })
            flash('خطأ في النظام: حساب المستخدم غير مرتبط بسجل موظف. يرجى الاتصال بالإدارة.', 'error')
            return render_template('login.html')
        
        employee = Employee.query.get(user.employee_id)
        if not employee or not employee.is_active:
            SecurityHelper.log_security_event(user.id, 'LOGIN_DENIED_INACTIVE_EMPLOYEE', {
                'username': username,
                'reason': 'Employee record not found or inactive'
            })
            flash('حساب الموظف غير نشط. يرجى الاتصال بالإدارة.', 'error')
            return render_template('login.html')
        
        # Successful login
        AccountLockoutManager.reset_failed_attempts(user)
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Clear pending session
        session.pop('pending_user_id', None)
        
        # Log successful login
        log_audit(user.id, 'LOGIN', 'User', str(user.id), {'username': username})
        SecurityHelper.log_security_event(user.id, 'SUCCESSFUL_LOGIN', {
            'username': username,
            'ip': request.remote_addr,
            'mfa_used': user.mfa_enabled
        })
        
        # Check if user is GENERAL_ADMIN with linked Employee - show mode selection
        # ROLE CHECK DISABLED: if user.role == UserRole.GENERAL_ADMIN:
        if True:  # Role check bypassed
            from k9.models.models import Employee
            employee = user.employee
            if employee:
                # Store pending mode selection in session
                session['pending_mode_selection'] = True
                session['pending_user_id'] = str(user.id)
                return redirect(url_for('auth.select_mode'))
        
        # For other users or admins without employee records, go to dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    if not has_permission(current_user, "auth.logout.access"):
        return redirect("/unauthorized")
    
    log_audit(current_user.id, 'LOGOUT', 'User', str(current_user.id), {'username': current_user.username})
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if not has_permission(current_user, "auth.setup.access"):
        return redirect("/unauthorized")
    
    # Check if any admin users exist
    admin_exists = User.query.filter_by(role=UserRole.GENERAL_ADMIN).first()
    if admin_exists:
        flash('تم إعداد النظام بالفعل', 'info')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            from k9.models.models import Employee, EmployeeRole
            from datetime import datetime
            
            # Validate password
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            if password != confirm_password:
                flash('كلمات المرور غير متطابقة', 'error')
                return render_template('auth/setup.html')
            
            # Validate phone number format
            phone = request.form.get('phone', '').strip()
            is_valid, error_message = validate_yemen_phone(phone)
            if not is_valid:
                flash(error_message or 'رقم الهاتف غير صحيح', 'error')
                return render_template('auth/setup.html')
            
            # Check if phone number already exists
            existing_phone = Employee.query.filter_by(phone=phone).first()
            if existing_phone:
                flash('رقم الهاتف مستخدم بالفعل من قبل موظف آخر', 'error')
                return render_template('auth/setup.html')
            
            # Parse hire date
            hire_date_str = request.form.get('hire_date')
            try:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else datetime.utcnow().date()
            except ValueError:
                hire_date = datetime.utcnow().date()
            
            # Create Employee record first (required for User.employee_id foreign key)
            admin_employee = Employee(
                name=request.form['full_name'],
                employee_id=request.form['employee_id'],
                role=EmployeeRole.PROJECT_MANAGER,  # Admin can work as PM when in project-scoped mode
                phone=phone,
                email=request.form['email'],
                hire_date=hire_date,
                is_active=True
            )
            
            db.session.add(admin_employee)
            db.session.flush()  # Get the employee ID
            
            # Create the first admin user linked to the employee
            admin_user = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(password),
                role=UserRole.GENERAL_ADMIN,
                full_name=request.form['full_name'],
                phone=phone,
                active=True,
                employee_id=admin_employee.id  # Link user to employee (required)
            )
            
            db.session.add(admin_user)
            
            db.session.commit()
            
            log_audit(admin_user.id, 'SETUP', 'User', str(admin_user.id), {
                'username': admin_user.username,
                'employee_id': admin_employee.employee_id,
                'note': 'Initial system setup with linked User and Employee records'
            })
            
            flash('تم إنشاء حساب المدير الأول بنجاح. يمكنك الآن تسجيل الدخول.', 'success')
            return redirect(url_for('auth.login'))
            
        except IntegrityError as e:
            db.session.rollback()
            if 'employee_id' in str(e):
                flash('رقم الموظف مستخدم بالفعل', 'error')
            elif 'phone' in str(e):
                flash('رقم الهاتف مستخدم بالفعل', 'error')
            elif 'username' in str(e):
                flash('اسم المستخدم مستخدم بالفعل', 'error')
            elif 'email' in str(e):
                flash('البريد الإلكتروني مستخدم بالفعل', 'error')
            else:
                flash('حدث خطأ: البيانات المدخلة مكررة', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'error')
    
    from datetime import date
    return render_template('auth/setup.html', current_date=date.today().isoformat())

@auth_bp.route('/select-mode', methods=['GET', 'POST'])
@login_required
def select_mode():
    if not has_permission(current_user, "auth.mode.switch"):
        return redirect("/unauthorized")
    
    """Allow GENERAL_ADMIN users to select their working mode"""
    from k9.models.models import Employee
    from k9.utils.pm_scoping import get_pm_project
    
    # Only for GENERAL_ADMIN users
    # ROLE CHECK DISABLED: if current_user.role != UserRole.GENERAL_ADMIN:
    if True:  # Role check bypassed
        return redirect(url_for('main.dashboard'))
    
    # Get linked employee record
    employee = current_user.employee
    if not employee:
        # No employee record - default to general admin mode
        session['admin_mode'] = 'general_admin'
        session.pop('pending_mode_selection', None)
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode in ['general_admin', 'project_manager']:
            session['admin_mode'] = mode
            session.pop('pending_mode_selection', None)
            
            log_audit(current_user.id, 'MODE_SELECTION', 'User', str(current_user.id), {
                'mode': mode,
                'username': current_user.username
            })
            
            flash(f'تم تبديل الوضع بنجاح إلى: {"المدير العام" if mode == "general_admin" else "مدير المشروع"}', 'success')
            
            # Redirect directly to appropriate dashboard
            if mode == 'project_manager':
                return redirect(url_for('pm.dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('وضع غير صالح', 'error')
    
    # Check if user has an assigned project using proper scoping function
    # Temporarily set admin_mode to check project assignment
    old_mode = session.get('admin_mode')
    session['admin_mode'] = 'project_manager'
    assigned_project = get_pm_project(current_user)
    if old_mode:
        session['admin_mode'] = old_mode
    else:
        session.pop('admin_mode', None)
    
    return render_template('auth/mode_selection.html', 
                         employee=employee,
                         assigned_project=assigned_project)

@auth_bp.route('/switch-mode', methods=['POST'])
@login_required
def switch_mode():
    """Allow GENERAL_ADMIN to switch between modes without re-logging"""
    from k9.models.models import Employee, AccessOutcome
    from k9.services.access_audit_service import log_mode_switch
    
    # ROLE CHECK DISABLED: if current_user.role != UserRole.GENERAL_ADMIN:
    if True:  # Role check bypassed
        log_mode_switch('N/A', 'N/A', outcome=AccessOutcome.BLOCKED)
        flash('ليس لديك صلاحية لتبديل الأوضاع', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Verify employee record exists
    employee = current_user.employee
    if not employee:
        log_mode_switch('general_admin', 'project_manager', outcome=AccessOutcome.FAILURE)
        flash('لا يمكن التبديل: لا يوجد سجل موظف مرتبط', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Toggle mode
    current_mode = session.get('admin_mode', 'general_admin')
    new_mode = 'project_manager' if current_mode == 'general_admin' else 'general_admin'
    session['admin_mode'] = new_mode
    
    # Log the mode switch using new access audit service
    log_mode_switch(current_mode, new_mode, outcome=AccessOutcome.SUCCESS)
    
    flash(f'تم التبديل إلى وضع: {"المدير العام" if new_mode == "general_admin" else "مدير المشروع"}', 'success')
    
    # Redirect directly to appropriate dashboard
    if new_mode == 'project_manager':
        return redirect(url_for('pm.dashboard'))
    else:
        return redirect(url_for('main.dashboard'))

@auth_bp.route('/create_manager', methods=['GET', 'POST'])
@login_required
def create_manager():
    if not has_permission(current_user, "auth.create_manager.access"):
        return redirect("/unauthorized")
    
    # Only general admins can create project managers
    # ROLE CHECK DISABLED: if current_user.role != UserRole.GENERAL_ADMIN:
    if True:  # Role check bypassed
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Define variables needed by both GET and POST
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
    
    from k9.models.models import Employee, EmployeeRole
    employees_without_accounts = Employee.query.filter(
        Employee.role == EmployeeRole.PROJECT_MANAGER,
        ~Employee.id.in_(db.session.query(User.employee_id).filter(User.employee_id.isnot(None))),
        Employee.is_active == True
    ).all()
    
    if request.method == 'POST':
        try:
            # Validate password complexity
            password = request.form['password']
            is_valid, error_msg = PasswordValidator.validate_password(password)
            if not is_valid:
                flash(f'كلمة المرور لا تتوافق مع متطلبات الأمان: {error_msg}', 'error')
                return render_template('auth/create_manager.html', 
                                     available_sections=available_sections,
                                     employees=employees_without_accounts)
            
            # Create new project manager
            manager = User(
                username=request.form['username'],
                email=request.form['email'],
                password_hash=generate_password_hash(password),
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
                    manager.employee_id = employee.id
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'User', str(manager.id), 
                     {'username': manager.username, 'role': manager.role.value})
            
            flash('تم إنشاء حساب مدير المشروع بنجاح', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'error')
    
    return render_template('auth/create_manager.html', 
                         available_sections=available_sections,
                         employees=employees_without_accounts)
