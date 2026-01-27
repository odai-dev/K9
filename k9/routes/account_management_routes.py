"""
مسارات إدارة الحسابات
Account Management Routes - For granting system access to employees
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from k9.models.models import User, UserRole, Employee, EmployeeRole, ProjectAssignment, Project
from k9.utils.permissions_new import admin_required, require_permission, has_permission, grant_permission
from k9.models.permissions_v2 import PermissionKey, PermissionOverride, ROLE_PERMISSIONS, RoleType
from k9.services.permission_service import PermissionService
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import db


def create_base_permissions_for_user(user_id, granted_by_id=None):
    """Create base permissions for a new user account.
    
    This function grants basic viewing permissions to a new user.
    More specific permissions can be granted later through the admin interface.
    """
    base_permissions = [
        'dashboard.view',
        'handler.profile.view'
    ]
    
    for perm_key in base_permissions:
        grant_permission(str(user_id), perm_key, str(granted_by_id) if granted_by_id else None)


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
    if not has_permission("account_management.index.view"):
        return redirect("/unauthorized")
    
    users = User.query.order_by(User.created_at.desc()).all()
    
    user_accounts = []
    for user in users:
        employee = user.employee if user.employee else None
        
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
    if not has_permission("account_management.create.access"):
        return redirect("/unauthorized")
    
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
        
        if employee.user_account is not None:
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
            linked_employee = existing_user_by_email.employee
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
            user.employee_id = employee.id
            
            db.session.add(user)
            db.session.flush()
            
            # Create base permissions for the user based on their role
            create_base_permissions_for_user(user.id, current_user.id)
            
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
            
            # Verify the user was actually saved
            saved_user = User.query.filter_by(username=username).first()
            if not saved_user:
                flash('حدث خطأ: لم يتم حفظ الحساب بشكل صحيح', 'danger')
                return redirect(url_for('account_management.create'))
            
            import logging
            logging.info(f"Account created successfully: username={username}, user_id={saved_user.id}")
            
            return render_template('admin/account_management/create_success.html',
                                 page_title='تم إنشاء الحساب بنجاح',
                                 username=username,
                                 password=password,
                                 employee=employee,
                                 user_role=user_role.value)
        
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Error creating account: {str(e)}")
            flash(f'حدث خطأ أثناء إنشاء الحساب: {str(e)}', 'danger')
            return redirect(url_for('account_management.create'))
    
    employees_without_accounts = Employee.query.filter(
        ~Employee.id.in_(db.session.query(User.employee_id).filter(User.employee_id.isnot(None))),
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
    if not has_permission("account_management.api.access"):
        return jsonify({'error': 'Unauthorized'}), 403
    
    password = generate_secure_password()
    return jsonify({'password': password})


@account_mgmt_bp.route('/api/search-employees', methods=['GET'])
@login_required
@require_permission('employees.view')
def api_search_employees():
    """Search employees without accounts"""
    search_term = request.args.get('q', '')
    
    query = Employee.query.filter(
        ~Employee.id.in_(db.session.query(User.employee_id).filter(User.employee_id.isnot(None))),
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
    if not has_permission("account_management.toggle_status.access"):
        return redirect("/unauthorized")
    
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
    if not has_permission("account_management.reset_password.access"):
        return redirect("/unauthorized")
    
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


def get_role_baseline_permissions(user_role):
    """Get baseline permissions for a user's role from ROLE_PERMISSIONS mapping.
    
    Maps UserRole enum to RoleType and expands wildcard patterns to get all 
    permission keys that are included in the role baseline.
    """
    role_mapping = {
        UserRole.GENERAL_ADMIN: RoleType.GENERAL_ADMIN,
        UserRole.PROJECT_MANAGER: RoleType.PROJECT_MANAGER,
        UserRole.HANDLER: RoleType.HANDLER,
        UserRole.TRAINER: RoleType.TRAINER,
        UserRole.BREEDER: RoleType.BREEDER,
        UserRole.VET: RoleType.VETERINARIAN,
    }
    
    role_type = role_mapping.get(user_role)
    if not role_type:
        return set()
    
    role_permissions = ROLE_PERMISSIONS.get(role_type, [])
    
    all_permission_keys = set()
    for attr_name in dir(PermissionKey):
        if not attr_name.startswith('_'):
            perm_key = getattr(PermissionKey, attr_name)
            if isinstance(perm_key, str) and '.' in perm_key:
                all_permission_keys.add(perm_key)
    
    baseline_permissions = set()
    
    for pattern in role_permissions:
        if pattern == "*":
            baseline_permissions = all_permission_keys.copy()
            break
        elif pattern.endswith(".*"):
            module = pattern[:-2]
            for perm_key in all_permission_keys:
                if perm_key.startswith(module + "."):
                    baseline_permissions.add(perm_key)
        else:
            if pattern in all_permission_keys:
                baseline_permissions.add(pattern)
    
    return baseline_permissions


def get_permission_categories():
    """Get all permission keys organized by module/category"""
    categories = {
        'dogs': {
            'name_ar': 'الكلاب',
            'icon': 'fa-dog',
            'permissions': []
        },
        'employees': {
            'name_ar': 'الموظفين',
            'icon': 'fa-users',
            'permissions': []
        },
        'projects': {
            'name_ar': 'المشاريع',
            'icon': 'fa-project-diagram',
            'permissions': []
        },
        'training': {
            'name_ar': 'التدريب',
            'icon': 'fa-dumbbell',
            'permissions': []
        },
        'veterinary': {
            'name_ar': 'البيطري',
            'icon': 'fa-stethoscope',
            'permissions': []
        },
        'breeding': {
            'name_ar': 'التربية',
            'icon': 'fa-leaf',
            'permissions': []
        },
        'reports': {
            'name_ar': 'التقارير',
            'icon': 'fa-file-alt',
            'permissions': []
        },
        'schedule': {
            'name_ar': 'الجداول',
            'icon': 'fa-calendar-alt',
            'permissions': []
        },
        'users': {
            'name_ar': 'المستخدمين',
            'icon': 'fa-user-cog',
            'permissions': []
        },
        'admin': {
            'name_ar': 'الإدارة',
            'icon': 'fa-cogs',
            'permissions': []
        },
        'handler_daily': {
            'name_ar': 'العمليات اليومية',
            'icon': 'fa-clipboard-list',
            'permissions': []
        },
        'pm': {
            'name_ar': 'مسؤول المشروع',
            'icon': 'fa-user-tie',
            'permissions': []
        }
    }
    
    permission_labels = {
        'view': 'عرض',
        'create': 'إنشاء',
        'edit': 'تعديل',
        'delete': 'حذف',
        'export': 'تصدير',
        'approve': 'اعتماد',
        'manage_team': 'إدارة الفريق',
        'final_approve': 'الاعتماد النهائي',
        'dashboard': 'لوحة التحكم',
        'settings': 'الإعدادات',
        'backup': 'النسخ الاحتياطي',
        'audit': 'سجل التدقيق',
        'review_reports': 'مراجعة التقارير',
        'manage_project': 'إدارة المشروع',
        'manage_permissions': 'إدارة الصلاحيات'
    }
    
    for attr_name in dir(PermissionKey):
        if not attr_name.startswith('_'):
            perm_key = getattr(PermissionKey, attr_name)
            if isinstance(perm_key, str) and '.' in perm_key:
                parts = perm_key.split('.')
                module = parts[0]
                action = parts[1] if len(parts) > 1 else ''
                
                if module in categories:
                    action_label = permission_labels.get(action, action)
                    categories[module]['permissions'].append({
                        'key': perm_key,
                        'action': action,
                        'action_ar': action_label
                    })
    
    return {k: v for k, v in categories.items() if v['permissions']}


@account_mgmt_bp.route('/<user_id>/edit')
@login_required
@admin_required
def edit(user_id):
    """تعديل حساب المستخدم وصلاحياته"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('هذه الصفحة متاحة فقط للمدير العام', 'danger')
        return redirect(url_for('account_management.index'))
    
    user = User.query.get_or_404(user_id)
    employee = user.employee if user.employee else None
    
    permission_categories = get_permission_categories()
    
    role_baseline_permissions = get_role_baseline_permissions(user.role)
    
    current_overrides = {}
    overrides = PermissionOverride.query.filter_by(
        user_id=user.id,
        project_id=None
    ).all()
    for override in overrides:
        current_overrides[override.permission_key] = override.is_granted
    
    return render_template('admin/account_management/edit.html',
                         page_title=f'تعديل حساب {user.username}',
                         user=user,
                         employee=employee,
                         permission_categories=permission_categories,
                         role_baseline_permissions=role_baseline_permissions,
                         current_overrides=current_overrides,
                         user_roles=UserRole)


@account_mgmt_bp.route('/<user_id>/permissions', methods=['POST'])
@login_required
@admin_required
def save_permissions(user_id):
    """حفظ صلاحيات المستخدم الإضافية (منح وحجب)"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 403
    
    user = User.query.get_or_404(user_id)
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'لا توجد بيانات'}), 400
        
        grants = data.get('grants', [])
        revokes = data.get('revokes', [])
        
        PermissionOverride.query.filter_by(
            user_id=user.id,
            project_id=None
        ).delete()
        db.session.flush()
        
        for perm_key in grants:
            override = PermissionOverride(
                user_id=user.id,
                permission_key=perm_key,
                is_granted=True,
                granted_by_id=current_user.id,
                reason='منح إضافي من إدارة الحسابات'
            )
            db.session.add(override)
        
        for perm_key in revokes:
            override = PermissionOverride(
                user_id=user.id,
                permission_key=perm_key,
                is_granted=False,
                granted_by_id=current_user.id,
                reason='حجب من إدارة الحسابات'
            )
            db.session.add(override)
        
        user.permissions_updated_at = datetime.utcnow()
        PermissionService.clear_cache(user.id)
        
        db.session.commit()
        
        total_changes = len(grants) + len(revokes)
        message_parts = []
        if grants:
            message_parts.append(f'{len(grants)} صلاحية ممنوحة')
        if revokes:
            message_parts.append(f'{len(revokes)} صلاحية محجوبة')
        
        if message_parts:
            message = 'تم حفظ: ' + ' و '.join(message_parts)
        else:
            message = 'تم إعادة تعيين جميع الصلاحيات للقيم الافتراضية'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
