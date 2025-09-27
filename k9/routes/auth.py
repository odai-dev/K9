from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, csrf
from k9.models.models import User, UserRole, AuditLog
from k9.utils.utils import log_audit
from k9.utils.security_utils import PasswordValidator, AccountLockoutManager, MFAManager, SecurityHelper
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
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
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
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
