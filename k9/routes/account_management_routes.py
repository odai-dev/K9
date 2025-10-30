"""
مسارات إدارة الحسابات
Account Management Routes - For granting system access to employees
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from k9.models.models import User, UserRole, Employee, EmployeeRole, ProjectAssignment, Project
from k9.decorators import admin_required
from werkzeug.security import generate_password_hash
from app import db
from k9.utils.pm_scoping import get_pm_project, is_pm
import secrets
import string


account_mgmt_bp = Blueprint('account_management', __name__, url_prefix='/admin/accounts')


def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def map_employee_role_to_user_role(employee_role):
    """Map EmployeeRole to UserRole"""
    role_mapping = {
        EmployeeRole.HANDLER: UserRole.HANDLER,
        EmployeeRole.TRAINER: UserRole.TRAINER,
        EmployeeRole.BREEDER: UserRole.BREEDER,
        EmployeeRole.VET: UserRole.VET,
        EmployeeRole.PROJECT_MANAGER: UserRole.PROJECT_MANAGER,
    }
    return role_mapping.get(employee_role)


@account_mgmt_bp.route('/')
@login_required
@admin_required
def index():
    """عرض جميع الحسابات"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    user_accounts = []
    for user in users:
        employee = None
        if hasattr(user, 'employee_profile') and user.employee_profile:
            employee = user.employee_profile
        
        user_accounts.append({
            'user': user,
            'employee': employee
        })
    
    return render_template('admin/account_management/index.html',
                         page_title='إدارة الحسابات',
                         user_accounts=user_accounts,
                         user_roles=UserRole)


@account_mgmt_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """منح صلاحية دخول لموظف"""
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not employee_id or not username:
            flash('يجب اختيار موظف وإدخال اسم مستخدم', 'danger')
            return redirect(url_for('account_management.create'))
        
        employee = Employee.query.get(employee_id)
        if not employee:
            flash('الموظف غير موجود', 'danger')
            return redirect(url_for('account_management.create'))
        
        if employee.user_account_id:
            flash('هذا الموظف لديه حساب بالفعل', 'danger')
            return redirect(url_for('account_management.create'))
        
        # Check if username exists
        existing_user_by_username = User.query.filter_by(username=username).first()
        if existing_user_by_username:
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('account_management.create'))
        
        # Check email availability
        email = employee.email or f"{username}@k9system.local"
        existing_user_by_email = User.query.filter_by(email=email).first()
        
        # If email exists, check if it's linked to another employee
        if existing_user_by_email:
            # Check if this user is linked to a different employee
            linked_employee = Employee.query.filter_by(user_account_id=existing_user_by_email.id).first()
            if linked_employee:
                flash('البريد الإلكتروني موجود بالفعل ومرتبط بموظف آخر', 'danger')
                return redirect(url_for('account_management.create'))
            # If user exists but not linked to any employee, use a system-generated email instead
            email = f"{username}@k9system.local"
            flash('تم استخدام بريد إلكتروني بديل لأن البريد الأصلي مستخدم من قبل', 'info')
        
        if not password:
            password = generate_secure_password()
        
        user_role = map_employee_role_to_user_role(employee.role)
        if not user_role:
            flash('نوع دور الموظف غير معروف', 'danger')
            return redirect(url_for('account_management.create'))
        
        try:
            user = User()
            user.username = username
            user.email = email
            user.password_hash = generate_password_hash(password)
            user.role = user_role
            user.full_name = employee.name
            user.phone = employee.phone
            user.active = True
            user.mfa_enabled = False
            
            db.session.add(user)
            db.session.flush()
            
            employee.user_account_id = user.id
            
            # Auto-assign employee to project if creator is a PM and employee has no active assignments
            if is_pm(current_user):
                pm_project = get_pm_project(current_user)
                if pm_project:
                    # Check if employee already has an active assignment to this project
                    existing_assignment = ProjectAssignment.query.filter_by(
                        project_id=pm_project.id,
                        employee_id=employee.id,
                        is_active=True
                    ).first()
                    
                    if not existing_assignment:
                        # Create new project assignment
                        new_assignment = ProjectAssignment()
                        new_assignment.project_id = pm_project.id
                        new_assignment.employee_id = employee.id
                        new_assignment.is_active = True
                        db.session.add(new_assignment)
                        flash('تم تعيين الموظف للمشروع تلقائياً', 'success')
            
            db.session.commit()
            
            return render_template('admin/account_management/create_success.html',
                                 page_title='تم إنشاء الحساب بنجاح',
                                 username=username,
                                 password=password,
                                 employee=employee,
                                 user_role=user_role.value)
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'danger')
            return redirect(url_for('account_management.create'))
    
    employees_without_accounts = Employee.query.filter(
        Employee.user_account_id.is_(None),
        Employee.is_active == True
    ).order_by(Employee.name).all()
    
    return render_template('admin/account_management/create.html',
                         page_title='منح صلاحية دخول لموظف',
                         employees=employees_without_accounts)


@account_mgmt_bp.route('/api/generate-password', methods=['GET'])
@login_required
@admin_required
def api_generate_password():
    """Generate a secure password via API"""
    password = generate_secure_password()
    return jsonify({'password': password})


@account_mgmt_bp.route('/api/search-employees', methods=['GET'])
@login_required
@admin_required
def api_search_employees():
    """Search employees without accounts"""
    search_term = request.args.get('q', '')
    
    query = Employee.query.filter(
        Employee.user_account_id.is_(None),
        Employee.is_active == True
    )
    
    if search_term:
        query = query.filter(
            db.or_(
                Employee.name.ilike(f'%{search_term}%'),
                Employee.employee_id.ilike(f'%{search_term}%')
            )
        )
    
    employees = query.order_by(Employee.name).limit(20).all()
    
    results = []
    for emp in employees:
        results.append({
            'id': str(emp.id),
            'name': emp.name,
            'employee_id': emp.employee_id,
            'role': emp.role.value,
            'email': emp.email or '',
            'phone': emp.phone or ''
        })
    
    return jsonify(results)


@account_mgmt_bp.route('/<user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(user_id):
    """تفعيل/تعطيل حساب"""
    user = User.query.get_or_404(user_id)
    
    if user.role == UserRole.GENERAL_ADMIN and User.query.filter_by(role=UserRole.GENERAL_ADMIN, active=True).count() == 1 and user.active:
        flash('لا يمكن تعطيل آخر حساب مدير عام نشط', 'danger')
        return redirect(url_for('account_management.index'))
    
    user.active = not user.active
    db.session.commit()
    
    status_text = 'تم تفعيل' if user.active else 'تم تعطيل'
    flash(f'{status_text} حساب {user.username}', 'success')
    
    return redirect(url_for('account_management.index'))


@account_mgmt_bp.route('/<user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """إعادة تعيين كلمة المرور"""
    user = User.query.get_or_404(user_id)
    
    new_password = generate_secure_password()
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return render_template('admin/account_management/reset_success.html',
                         page_title='تم إعادة تعيين كلمة المرور',
                         username=user.username,
                         password=new_password,
                         full_name=user.full_name,
                         user_role=user.role.value)
