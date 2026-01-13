"""
Admin Routes for Enhanced Permission Management System
Provides comprehensive permission control interface for GENERAL_ADMIN users
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, session, current_app
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import csrf
from k9.utils.permissions_new import (
    admin_required, has_permission, require_admin_permission,
    get_project_managers, get_all_projects,
    get_users_by_project, get_user_permissions_by_project,
    grant_permission, revoke_permission, get_user_permission_keys,
    get_all_permissions_grouped, batch_grant_permissions, batch_revoke_permissions
)
from k9.utils.security_utils import PasswordValidator, SecurityHelper
from k9.models.models import User, Project, UserRole, ProjectAssignment
from k9.models.permissions_v2 import Role, UserRoleAssignment, PermissionAuditLog
from k9.models.models_handler_daily import HandlerReport, ShiftReport
from app import db
from k9.utils.utils import log_audit
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import json
import io
import os
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard with system overview and navigation"""
    from k9.models.models import User, Project, Dog, Employee, TrainingSession, VeterinaryVisit
    from k9.models.permissions_v2 import Role, UserRoleAssignment, PermissionOverride, PermissionAuditLog
    from sqlalchemy import func
    
    # System statistics - using V2 permission system
    # Calculate permission statistics - count all permission key attributes in PermissionKey class
    from k9.models.permissions_v2 import PermissionKey, PermissionOverride
    total_permissions = len([attr for attr in dir(PermissionKey) if not attr.startswith('_') and isinstance(getattr(PermissionKey, attr), str)])
    granted_permissions = PermissionOverride.query.filter_by(is_granted=True).count()
    
    stats = {
        'total_users': User.query.count(),
        'total_project_managers': User.query.filter_by(role=UserRole.PROJECT_MANAGER).count(),
        'total_projects': Project.query.count(),
        'total_dogs': Dog.query.count(),
        'total_employees': Employee.query.count(),
        'total_roles': Role.query.count(),
        'total_role_assignments': UserRoleAssignment.query.count(),
        'total_permissions': total_permissions,
        'granted_permissions': granted_permissions,
    }
    
    # Recent activities - use V2 PermissionAuditLog
    recent_permission_changes = PermissionAuditLog.query.order_by(PermissionAuditLog.created_at.desc()).limit(5).all()
    recent_training = TrainingSession.query.order_by(TrainingSession.created_at.desc()).limit(5).all()
    recent_vet_visits = VeterinaryVisit.query.order_by(VeterinaryVisit.created_at.desc()).limit(5).all()
    
    # Get project managers for quick access
    project_managers = get_project_managers()
    projects = get_all_projects()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_permission_changes=recent_permission_changes,
                         recent_training=recent_training,
                         recent_vet_visits=recent_vet_visits,
                         project_managers=project_managers,
                         projects=projects)

# Old permissions_dashboard route removed - now using /permissions/comprehensive

@admin_bp.route('/permissions/user/<user_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def get_user_permissions(user_id):
    """Get permissions for a specific user"""
    user = User.query.get_or_404(user_id)
    
    permissions = list(get_user_permission_keys(str(user.id)))
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name
        },
        'permissions': permissions
    })

@admin_bp.route('/permissions/update', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def update_user_permission():
    """Update a specific permission for a user - supports both old and new permission formats"""
    from k9.utils.permissions_new import grant_permission, revoke_permission
    
    try:
        data = request.get_json()
        
        if not data:
            current_app.logger.error("Permission update failed: No data received")
            return jsonify({'success': False, 'error': 'لا توجد بيانات'}), 400
        
        # Log incoming data for debugging
        current_app.logger.info(f"Permission update request: user_id={data.get('user_id')}, section={data.get('section')}, subsection={data.get('subsection')}, type={data.get('permission_type')}, granted={data.get('is_granted')}, project_id={data.get('project_id')}")
        
        required_fields = ['user_id', 'section', 'permission_type', 'is_granted']
        if not all(field in data for field in required_fields):
            missing = [f for f in required_fields if f not in data]
            current_app.logger.error(f"Permission update failed: Missing fields: {missing}")
            return jsonify({'success': False, 'error': 'بيانات ناقصة'}), 400
    except Exception as e:
        current_app.logger.error(f"Error parsing JSON: {e}")
        return jsonify({'success': False, 'error': 'خطأ في تنسيق البيانات'}), 400
    
    try:
        user = User.query.get(data['user_id'])
        if not user:
            current_app.logger.error(f"Permission update failed: User not found: {data['user_id']}")
            return jsonify({'success': False, 'error': 'مستخدم غير موجود'}), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching user: {e}")
        return jsonify({'success': False, 'error': 'خطأ في جلب بيانات المستخدم'}), 500
    
    section = data['section']
    subsection = data.get('subsection', '')
    perm_type = data['permission_type']
    is_granted = data['is_granted']
    
    # Build the new permission key
    # Converts old format (section=reports, subsection=breeding_reports, type=VIEW)
    # to new format (reports.breeding.view)
    perm_type_lower = perm_type.lower() if perm_type else ''
    
    if subsection:
        permission_key = f"{section}.{subsection}.{perm_type_lower}"
    else:
        permission_key = f"{section}.{perm_type_lower}"
    
    # Clean up the permission key (remove double dots, normalize)
    permission_key = permission_key.replace('..', '.').strip('.')
    
    current_app.logger.info(f"Built permission key: {permission_key} for user {user.username}, granted={is_granted}")
    
    # Use the new permission system
    if is_granted:
        success = grant_permission(str(user.id), permission_key, str(current_user.id))
    else:
        success = revoke_permission(str(user.id), permission_key, str(current_user.id))
    
    if success:
        current_app.logger.info(f"Permission update successful for user {user.username}: {permission_key} = {is_granted}")
        log_audit(
            user_id=current_user.id,
            action='EDIT',
            target_type='Permission',
            target_id=None,
            description=f"Updated permission for {user.username}: {permission_key} = {is_granted}"
        )
        return jsonify({'success': True, 'message': 'تم تحديث الصلاحية بنجاح'})
    else:
        # Permission key might not exist in new system - try to provide helpful message
        current_app.logger.warning(f"Permission key not found in new system: {permission_key}")
        return jsonify({
            'success': False, 
            'error': f'صلاحية غير موجودة: {permission_key}. يرجى استخدام واجهة الصلاحيات الجديدة.'
        }), 400

@admin_bp.route('/permissions/bulk-update', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def bulk_update_user_permissions():
    """Bulk update permissions for a category - OPTIMIZED with batch operations"""
    data = request.get_json()
    
    required_fields = ['user_id', 'category', 'is_granted']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'بيانات ناقصة'}), 400
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'مستخدم غير صحيح'}), 400
    
    category = data['category']
    is_granted = data['is_granted']
    
    # Get all permissions in this category using V2 ROLE_PERMISSIONS patterns
    from k9.models.permissions_v2 import ROLE_PERMISSIONS, PermissionKey
    
    # Collect all permission keys matching this category from ROLE_PERMISSIONS
    all_permission_keys = set()
    for role_perms in ROLE_PERMISSIONS.values():
        for perm in role_perms:
            if perm.startswith(f"{category}."):
                all_permission_keys.add(perm)
    
    # Also add known permissions from PermissionKey enum
    for key in PermissionKey:
        if key.value.startswith(f"{category}."):
            all_permission_keys.add(key.value)
    
    permission_keys = list(all_permission_keys)
    
    # Use batch operations (ONE commit for all changes)
    if is_granted:
        count = batch_grant_permissions(str(user.id), permission_keys, str(current_user.id))
    else:
        count = batch_revoke_permissions(str(user.id), permission_keys, str(current_user.id))
    
    log_audit(
        user_id=current_user.id,
        action='EDIT',
        target_type='Permission',
        target_id=None,
        description=f"Bulk updated {count} permissions for {user.username} in category {category} = {is_granted}"
    )
    
    return jsonify({'success': True, 'message': f'تم تحديث {count} صلاحية بنجاح', 'count': count})

@admin_bp.route('/permissions/initialize/<user_id>', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def initialize_user_permissions(user_id):
    """Initialize default permissions for a new PROJECT_MANAGER - OPTIMIZED with batch"""
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'يمكن تهيئة صلاحيات مديري المشاريع فقط'}), 400
    
    # Grant default PM permissions - use correct keys from database
    default_pm_permissions = [
        'projects.view', 'dogs.view', 'employees.view', 'schedule.view',
        'shifts.view', 'reports.attendance.view', 'pm.dashboard',
        'pm.project.view', 'pm.team.view', 'pm.approvals.view'
    ]
    
    # Use batch operation (ONE commit for all 10 permissions)
    count = batch_grant_permissions(str(user.id), default_pm_permissions, str(current_user.id))
    
    log_audit(
        user_id=current_user.id,
        action='CREATE',
        target_type='Permission',
        target_id=None,
        description=f"Initialized {count} default permissions for {user.username}"
    )
    
    return jsonify({'success': True, 'message': 'تم تهيئة الصلاحيات الافتراضية بنجاح'})

@admin_bp.route('/permissions/comprehensive')
@login_required
@require_admin_permission('admin.permissions.view')
def comprehensive_permissions():
    """Redirect to the new Access Control Hub"""
    return redirect(url_for('admin.access_control_hub'))

@admin_bp.route('/permissions/projects')
@login_required
@require_admin_permission('admin.permissions.view')
def get_projects_list():
    """Get list of all projects for permissions management"""
    projects = Project.query.all()
    
    projects_data = []
    for project in projects:
        # Count employees from ProjectAssignment table (the current way of assigning)
        employee_count = ProjectAssignment.query.filter(
            ProjectAssignment.project_id == project.id,
            ProjectAssignment.is_active == True,
            ProjectAssignment.employee_id.isnot(None)
        ).count()
        
        # Also include employees from legacy assigned_employees relationship
        legacy_count = len(project.assigned_employees) if project.assigned_employees else 0
        
        # Total unique employees (in case some are in both)
        total_employees = employee_count + legacy_count
        
        projects_data.append({
            'id': str(project.id),
            'name': project.name,
            'code': project.code,
            'status': project.status.value if hasattr(project.status, 'value') else str(project.status),
            'employees_count': total_employees
        })
    
    return jsonify({'projects': projects_data})

@admin_bp.route('/permissions/users/<project_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def get_project_users(project_id):
    """Get list of ALL users (for comprehensive permissions management)"""
    try:
        # Get ALL active users with employee accounts
        # This allows assigning permissions to anyone, not just currently assigned users
        users = User.query.filter(
            User.active == True,
            User.employee_id.isnot(None)
        ).order_by(User.full_name).all()
        
        # Prioritize users already assigned to this project
        project_user_ids = set()
        assigned_users = get_users_by_project(project_id)
        for user in assigned_users:
            project_user_ids.add(user.id)
        
        users_data = [{
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'role': user.role.value if hasattr(user.role, 'value') else str(user.role),
            'employee_name': user.employee.name if user.employee else '',
            'employee_id': user.employee.employee_id if user.employee else '',
            'is_assigned': user.id in project_user_ids  # Flag for UI to show assigned users first
        } for user in users]
        
        # Sort: assigned users first, then alphabetically
        users_data.sort(key=lambda x: (not x['is_assigned'], x['full_name']))
        
        return jsonify({'users': users_data})
    except Exception as e:
        logger.error(f"Error getting users for project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/permissions/matrix/<user_id>/<project_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def get_permissions_matrix(user_id, project_id):
    """Get complete permissions matrix for a user in a project - SHOWS ALL PERMISSIONS"""
    try:
        user = User.query.get_or_404(user_id)
        project = Project.query.get_or_404(project_id)
        
        # Get ALL permissions grouped by category - NO role-based filtering
        # General Admin needs to see and control ALL permissions for any user
        grouped_perms = get_all_permissions_grouped()
        
        # Get user's granted permissions
        user_perms = get_user_permission_keys(str(user.id))
        
        # Category metadata for display
        CATEGORY_NAMES = {
            'dogs': {'ar': 'الكلاب', 'en': 'Dogs', 'icon': 'fa-dog'},
            'employees': {'ar': 'الموظفين', 'en': 'Employees', 'icon': 'fa-users'},
            'projects': {'ar': 'المشاريع', 'en': 'Projects', 'icon': 'fa-project-diagram'},
            'schedule': {'ar': 'الجداول', 'en': 'Schedule', 'icon': 'fa-calendar'},
            'training': {'ar': 'التدريب', 'en': 'Training', 'icon': 'fa-running'},
            'veterinary': {'ar': 'البيطرة', 'en': 'Veterinary', 'icon': 'fa-stethoscope'},
            'breeding': {'ar': 'التربية', 'en': 'Breeding', 'icon': 'fa-paw'},
            'cleaning': {'ar': 'التنظيف', 'en': 'Cleaning', 'icon': 'fa-broom'},
            'handler_reports': {'ar': 'تقارير السائسين', 'en': 'Handler Reports', 'icon': 'fa-file-alt'},
            'tasks': {'ar': 'المهام', 'en': 'Tasks', 'icon': 'fa-tasks'},
            'accounts': {'ar': 'الحسابات', 'en': 'Accounts', 'icon': 'fa-user-cog'},
            'account': {'ar': 'إدارة الحسابات', 'en': 'Account', 'icon': 'fa-user-circle'},
            'shifts': {'ar': 'الورديات', 'en': 'Shifts', 'icon': 'fa-clock'},
            'incidents': {'ar': 'الحوادث', 'en': 'Incidents', 'icon': 'fa-exclamation-triangle'},
            'suspicions': {'ar': 'الشبهات', 'en': 'Suspicions', 'icon': 'fa-search-plus'},
            'evaluations': {'ar': 'التقييمات', 'en': 'Evaluations', 'icon': 'fa-star'},
            'supervisor': {'ar': 'المشرف', 'en': 'Supervisor', 'icon': 'fa-user-tie'},
            'pm': {'ar': 'مدير المشروع', 'en': 'Project Manager', 'icon': 'fa-user-shield'},
            'handlers': {'ar': 'السائسين', 'en': 'Handlers', 'icon': 'fa-user'},
            'admin': {'ar': 'الإدارة', 'en': 'Admin', 'icon': 'fa-cogs'},
            'notifications': {'ar': 'الإشعارات', 'en': 'Notifications', 'icon': 'fa-bell'},
            'production': {'ar': 'الإنتاج', 'en': 'Production', 'icon': 'fa-industry'},
            'account_management': {'ar': 'إدارة الحسابات', 'en': 'Account Management', 'icon': 'fa-users-cog'},
            'mfa': {'ar': 'المصادقة الثنائية', 'en': 'MFA', 'icon': 'fa-shield-alt'},
            'general': {'ar': 'عام', 'en': 'General', 'icon': 'fa-globe'},
            'reports': {'ar': 'التقارير', 'en': 'Reports', 'icon': 'fa-chart-bar'},
            'reports.attendance': {'ar': 'تقارير الحضور', 'en': 'Attendance Reports', 'icon': 'fa-clipboard-check'},
            'reports.training': {'ar': 'تقارير التدريب', 'en': 'Training Reports', 'icon': 'fa-chart-line'},
            'reports.veterinary': {'ar': 'التقارير البيطرية', 'en': 'Veterinary Reports', 'icon': 'fa-file-medical'},
            'reports.breeding.feeding': {'ar': 'تقارير تغذية التربية', 'en': 'Breeding Feeding Reports', 'icon': 'fa-utensils'},
            'reports.breeding.checkup': {'ar': 'تقارير فحص التربية', 'en': 'Breeding Checkup Reports', 'icon': 'fa-heartbeat'},
            'reports.caretaker': {'ar': 'تقارير العناية', 'en': 'Caretaker Reports', 'icon': 'fa-hand-holding-heart'},
            'reports.breeding': {'ar': 'تقارير التربية', 'en': 'Breeding Reports', 'icon': 'fa-paw'},
            'reports.general': {'ar': 'التقارير العامة', 'en': 'General Reports', 'icon': 'fa-file'},
            'locations': {'ar': 'المواقع', 'en': 'Locations', 'icon': 'fa-map-marker-alt'},
            'assignments': {'ar': 'التعيينات', 'en': 'Assignments', 'icon': 'fa-user-check'},
            'backup': {'ar': 'النسخ الاحتياطي', 'en': 'Backup', 'icon': 'fa-database'},
            'settings': {'ar': 'الإعدادات', 'en': 'Settings', 'icon': 'fa-cog'},
            'dictionaries': {'ar': 'القوائم المرجعية', 'en': 'Dictionaries', 'icon': 'fa-book'},
            'audit': {'ar': 'سجل التدقيق', 'en': 'Audit Log', 'icon': 'fa-history'},
            'users': {'ar': 'إدارة المستخدمين', 'en': 'User Management', 'icon': 'fa-users-cog'},
            'grooming': {'ar': 'العناية', 'en': 'Grooming', 'icon': 'fa-cut'},
            'excretion': {'ar': 'الإخراج', 'en': 'Excretion', 'icon': 'fa-toilet'},
            'deworming': {'ar': 'مكافحة الديدان', 'en': 'Deworming', 'icon': 'fa-bug'},
            'api': {'ar': 'واجهة البرمجة', 'en': 'API', 'icon': 'fa-code'},
            'auth': {'ar': 'المصادقة', 'en': 'Authentication', 'icon': 'fa-key'},
            'dashboard': {'ar': 'لوحة التحكم', 'en': 'Dashboard', 'icon': 'fa-tachometer-alt'},
            'home': {'ar': 'الصفحة الرئيسية', 'en': 'Home', 'icon': 'fa-home'},
            'password_reset': {'ar': 'إعادة تعيين كلمة المرور', 'en': 'Password Reset', 'icon': 'fa-lock'},
            'search': {'ar': 'البحث', 'en': 'Search', 'icon': 'fa-search'},
        }
        
        permissions_data = []
        for category, perms in grouped_perms.items():
            cat_meta = CATEGORY_NAMES.get(category, {'ar': category, 'en': category, 'icon': 'fa-folder'})
            
            for perm in perms:
                key_parts = perm.key.split('.')
                permission_type = key_parts[-1].upper() if key_parts else 'VIEW'
                
                if len(key_parts) >= 3:
                    section = key_parts[0]
                    subsection = '.'.join(key_parts[1:-1])
                elif len(key_parts) == 2:
                    section = key_parts[0]
                    subsection = ''
                else:
                    section = perm.key
                    subsection = ''
                
                permissions_data.append({
                    'category': category,
                    'category_ar': cat_meta['ar'],
                    'category_en': cat_meta['en'],
                    'category_icon': cat_meta['icon'],
                    'key': perm.key,
                    'section': section,
                    'subsection': subsection,
                    'permission_type': permission_type,
                    'name': perm.name or perm.key,
                    'name_ar': perm.name_ar or perm.name or perm.key,
                    'name_en': perm.name_en or perm.name or perm.key,
                    'description': perm.description or '',
                    'is_granted': perm.key in user_perms
                })
        
        # Get total counts
        total_permissions = len(permissions_data)
        granted_count = sum(1 for p in permissions_data if p['is_granted'])
        
        return jsonify({
            'user': {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
            },
            'project': {
                'id': str(project.id),
                'name': project.name,
                'code': project.code
            },
            'permissions': permissions_data,
            'stats': {
                'total': total_permissions,
                'granted': granted_count,
                'categories_count': len(grouped_perms)
            }
        })
    except Exception as e:
        logger.error(f"Error getting permissions matrix: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/permissions/audit')
@login_required
@require_admin_permission('admin.permissions.view')
def permissions_audit_log():
    """View permission change audit log"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filter parameters
    target_user_id = request.args.get('target_user_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = PermissionAuditLog.query.order_by(PermissionAuditLog.created_at.desc())
    
    if target_user_id:
        query = query.filter(PermissionAuditLog.target_user_id == target_user_id)
    
    if start_date:
        query = query.filter(PermissionAuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(PermissionAuditLog.created_at <= end_date)
    
    audit_logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    project_managers = get_project_managers()
    permission_structure = get_all_permissions_grouped()
    
    return render_template('admin/permissions_audit.html',
                         audit_logs=audit_logs,
                         project_managers=project_managers,
                         permission_structure=permission_structure,
                         filters={
                             'target_user_id': target_user_id,
                             'start_date': start_date,
                             'end_date': end_date
                         })

@admin_bp.route('/permissions/export/<user_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def export_user_permissions_json(user_id):
    """Export user permissions as JSON"""
    user = User.query.get_or_404(user_id)
    
    permissions = list(get_user_permission_keys(str(user.id)))
    permissions_data = {
        'user': {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name
        },
        'permissions': permissions
    }
    
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='Permission',
        target_id=None,
        description=f"Exported permissions for {user.username}"
    )
    
    return jsonify(permissions_data)

@admin_bp.route('/permissions/export-pdf/<user_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def export_user_permissions_pdf(user_id):
    """Export user permissions as PDF"""
    user = User.query.get_or_404(user_id)
    
    # Get user's permissions
    permissions = list(get_user_permission_keys(str(user.id)))
    
    # Create PDF
    filename = f"permissions_{user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    temp_path = os.path.join('/tmp', filename)
    
    doc = SimpleDocTemplate(temp_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )
    
    # Title
    title = Paragraph(f"صلاحيات المستخدم - {user.full_name}", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Create table data - simple list of permissions
    data = [['الفئة', 'الصلاحية']]
    
    # Group permissions by category
    grouped = {}
    for perm_key in permissions:
        parts = perm_key.split('.')
        category = parts[0] if parts else 'other'
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(perm_key)
    
    for category, perm_keys in grouped.items():
        for perm_key in perm_keys:
            data.append([category, perm_key])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    
    # Log audit
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='Permission',
        target_id=None,
        description=f"Exported permissions PDF for {user.username}"
    )
    
    return send_file(temp_path, as_attachment=True, download_name=filename, mimetype='application/pdf')

@admin_bp.route('/permissions/export-excel')
@login_required
@require_admin_permission('admin.permissions.view')
def export_all_permissions_excel():
    """Export all permissions to Excel for compliance tracking"""
    from openpyxl import Workbook
    
    # Get all user permissions
    users = User.query.filter_by(active=True).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Permissions"
    
    # Headers
    ws.append(['User', 'Username', 'Role', 'Permissions'])
    
    for user in users:
        perms = list(get_user_permission_keys(str(user.id)))
        ws.append([user.full_name, user.username, user.role.value, ', '.join(perms)])
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='Permission',
        target_id=None,
        description="Exported all permissions to Excel"
    )
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"all_permissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@admin_bp.route('/permissions/preview/<user_id>')
@login_required
@require_admin_permission('admin.permissions.view')
def preview_pm_view(user_id):
    """Preview what a user can see based on their permissions"""
    user = User.query.get_or_404(user_id)
    
    # Get user's permissions
    permissions = list(get_user_permission_keys(str(user.id)))
    
    # Get all possible permissions count from V2 ROLE_PERMISSIONS
    from k9.models.permissions_v2 import ROLE_PERMISSIONS, PermissionKey
    all_permission_keys = set()
    for role_perms in ROLE_PERMISSIONS.values():
        for perm in role_perms:
            if not perm.endswith('.*'):  # Don't count wildcards
                all_permission_keys.add(perm)
    for key in PermissionKey:
        all_permission_keys.add(key.value)
    
    total_permissions = len(all_permission_keys)
    granted_permissions = len(permissions)
    
    coverage_percentage = (granted_permissions / total_permissions * 100) if total_permissions > 0 else 0
    
    # Group by category
    grouped = {}
    for perm_key in permissions:
        parts = perm_key.split('.')
        category = parts[0] if parts else 'other'
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(perm_key)
    
    return render_template('admin/permissions_preview.html',
                         target_user=user,
                         permissions=permissions,
                         permissions_grouped=grouped,
                         coverage_percentage=round(coverage_percentage, 1),
                         granted_permissions=granted_permissions,
                         total_permissions=total_permissions)

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_profile():
    """Admin profile management with password change functionality"""
    
    # Get system stats for display (needed for all renders)
    from k9.models.models import User, Project, Dog, Employee
    stats = {
        'total_users': User.query.count(),
        'total_project_managers': User.query.filter_by(role=UserRole.PROJECT_MANAGER).count(),
        'total_projects': Project.query.count(),
        'total_dogs': Dog.query.count(),
        'total_employees': Employee.query.count(),
        'total_role_assignments': UserRoleAssignment.query.count(),
    }
    
    # Get recent admin activities (recent permission changes from V2)
    recent_activities = PermissionAuditLog.query.filter_by(changed_by_id=current_user.id).order_by(PermissionAuditLog.created_at.desc()).limit(5).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Basic validation
            if not current_password:
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'empty_current_password',
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                flash('يرجى إدخال كلمة المرور الحالية', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            # Verify current password
            if not check_password_hash(current_user.password_hash, current_password):
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'invalid_current_password',
                    'username': current_user.username,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                })
                flash('كلمة المرور الحالية غير صحيحة', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            # Validate new password inputs
            if not new_password or not confirm_password:
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'empty_new_password',
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                flash('يرجى إدخال كلمة المرور الجديدة وتأكيدها', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            if new_password != confirm_password:
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'password_confirmation_mismatch',
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                flash('كلمة المرور الجديدة وتأكيدها غير متطابقتين', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            # Check password complexity
            is_valid, error_message = PasswordValidator.validate_password(new_password)
            if not is_valid:
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'password_complexity_failed',
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                flash(f'كلمة المرور غير صالحة: {error_message}', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            # Check if new password is different from current
            if check_password_hash(current_user.password_hash, new_password):
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ATTEMPT_FAILED', {
                    'reason': 'same_as_current_password',
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                flash('كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
            
            try:
                # Update password and timestamp
                current_user.password_hash = generate_password_hash(new_password)
                current_user.password_changed_at = datetime.utcnow()
                
                # Reset failed login attempts if any
                current_user.failed_login_attempts = 0
                current_user.account_locked_until = None
                
                db.session.commit()
                
                # Log successful password change
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGED', {
                    'username': current_user.username,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'changed_at': current_user.password_changed_at.isoformat()
                })
                
                # Log audit trail
                log_audit(
                    user_id=current_user.id,
                    action='EDIT',
                    target_type='User',
                    target_id=str(current_user.id),
                    description=f'Admin {current_user.username} successfully changed their password'
                )
                
                # Invalidate current session and create new one for security
                # This forces re-authentication and invalidates any other active sessions
                user_to_relogin = current_user
                logout_user()
                
                # Clear session data
                session.clear()
                
                # Log the user back in with fresh session
                login_user(user_to_relogin, remember=False, force=True, fresh=True)
                
                flash('تم تغيير كلمة المرور بنجاح! تم تسجيل دخولك بجلسة جديدة لأمان إضافي.', 'success')
                
                # Redirect to avoid POST resubmission
                return redirect(url_for('admin.admin_profile'))
                
            except Exception as e:
                db.session.rollback()
                
                # Log the error
                SecurityHelper.log_security_event(current_user.id, 'PASSWORD_CHANGE_ERROR', {
                    'reason': 'database_error',
                    'error': str(e),
                    'username': current_user.username,
                    'ip_address': request.remote_addr
                })
                
                flash(f'حدث خطأ أثناء تغيير كلمة المرور. يرجى المحاولة مرة أخرى.', 'error')
                return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)
    
    return render_template('admin/profile.html', stats=stats, recent_activities=recent_activities)


@admin_bp.route('/backup')
@login_required
@admin_required
def backup_management():
    """Backup management page"""
    if not has_permission("admin.backup"):
        return redirect("/unauthorized")
    
    from k9.models.models import BackupSettings
    from k9.utils.backup_utils import LocalBackupManager
    
    settings = BackupSettings.get_settings()
    backup_manager = LocalBackupManager()
    backups = backup_manager.list_backups()
    
    return render_template('admin/backup_management.html',
                         settings=settings,
                         backups=backups)


@admin_bp.route('/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Create a new database backup"""
    from k9.utils.backup_utils import LocalBackupManager
    from k9.models.models import BackupSettings
    
    data = request.get_json() or {}
    description = data.get('description', '')
    
    backup_manager = LocalBackupManager()
    success, filename, error = backup_manager.create_backup(description)
    
    if success:
        settings = BackupSettings.get_settings()
        settings.last_backup_at = datetime.utcnow()
        
        if error:
            settings.last_backup_status = 'partial'
            settings.last_backup_message = error
            message = f'تم إنشاء النسخة الاحتياطية محلياً، لكن فشل الرفع إلى Google Drive: {error}'
        else:
            settings.last_backup_status = 'success'
            settings.last_backup_message = f'Backup created: {filename}'
            message = 'تم إنشاء النسخة الاحتياطية بنجاح'
        
        db.session.commit()
        
        log_audit(
            user_id=current_user.id,
            action='CREATE',
            target_type='Backup',
            target_id=filename,
            description=f'Created database backup: {filename}' + (f' (Drive upload failed: {error})' if error else '')
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'filename': filename,
            'warning': error if error else None
        })
    else:
        settings = BackupSettings.get_settings()
        settings.last_backup_at = datetime.utcnow()
        settings.last_backup_status = 'failed'
        settings.last_backup_message = error
        db.session.commit()
        
        return jsonify({
            'success': False,
            'message': f'فشل إنشاء النسخة الاحتياطية: {error}'
        }), 500


@admin_bp.route('/backup/list')
@login_required
@admin_required
@csrf.exempt
def list_backups():
    """List all available backups"""
    from k9.utils.backup_utils import LocalBackupManager
    
    backup_manager = LocalBackupManager()
    backups = backup_manager.list_backups()
    
    backups_data = []
    for backup in backups:
        backups_data.append({
            'filename': backup['filename'],
            'timestamp': backup['timestamp'],
            'description': backup.get('description', ''),
            'size': backup['size'],
            'size_mb': round(backup['size'] / (1024 * 1024), 2),
            'created_at': backup['created_at'].isoformat(),
            'database': backup.get('database', 'unknown')
        })
    
    return jsonify({'backups': backups_data})


@admin_bp.route('/backup/restore/<path:filename>', methods=['POST'])
@login_required
@admin_required
def restore_backup(filename):
    """Restore database from backup"""
    from k9.utils.backup_utils import LocalBackupManager
    
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    
    if not confirm:
        return jsonify({
            'success': False,
            'message': 'يرجى التأكيد على الاستعادة'
        }), 400
    
    backup_manager = LocalBackupManager()
    success, error = backup_manager.restore_backup(filename)
    
    if success:
        log_audit(
            user_id=current_user.id,
            action='RESTORE',
            target_type='Backup',
            target_id=filename,
            description=f'Restored database from backup: {filename}'
        )
        
        return jsonify({
            'success': True,
            'message': 'تمت استعادة قاعدة البيانات بنجاح'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'فشلت الاستعادة: {error}'
        }), 500


@admin_bp.route('/backup/download/<path:filename>')
@login_required
@admin_required
def download_backup(filename):
    """Download a backup file"""
    from k9.utils.backup_utils import LocalBackupManager
    import os
    
    backup_manager = LocalBackupManager()
    backup_path = os.path.join(backup_manager.backup_dir, filename)
    
    if not os.path.exists(backup_path):
        flash('الملف غير موجود', 'error')
        return redirect(url_for('admin.backup_management'))
    
    log_audit(
        user_id=current_user.id,
        action='DOWNLOAD',
        target_type='Backup',
        target_id=filename,
        description=f'Downloaded backup: {filename}'
    )
    
    return send_file(backup_path, as_attachment=True, download_name=filename)


@admin_bp.route('/backup/delete/<path:filename>', methods=['POST'])
@login_required
@admin_required
def delete_backup(filename):
    """Delete a backup file"""
    from k9.utils.backup_utils import LocalBackupManager
    
    backup_manager = LocalBackupManager()
    success, error = backup_manager.delete_backup(filename)
    
    if success:
        log_audit(
            user_id=current_user.id,
            action='DELETE',
            target_type='Backup',
            target_id=filename,
            description=f'Deleted backup: {filename}'
        )
        
        return jsonify({
            'success': True,
            'message': 'تم حذف النسخة الاحتياطية بنجاح'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'فشل الحذف: {error}'
        }), 500


@admin_bp.route('/backup/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def backup_settings():
    """Manage backup settings"""
    from k9.models.models import BackupSettings, BackupFrequency
    
    settings = BackupSettings.get_settings()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        
        try:
            settings.auto_backup_enabled = data.get('auto_backup_enabled', settings.auto_backup_enabled)
            
            if 'backup_frequency' in data:
                settings.backup_frequency = BackupFrequency(data['backup_frequency'])
            
            if 'backup_hour' in data:
                backup_hour = int(data['backup_hour'])
                if 0 <= backup_hour <= 23:
                    settings.backup_hour = backup_hour
            
            if 'retention_days' in data:
                retention_days = int(data['retention_days'])
                if retention_days > 0:
                    settings.retention_days = retention_days
            
            settings.google_drive_enabled = data.get('google_drive_enabled', settings.google_drive_enabled)
            
            if 'google_drive_folder_id' in data:
                settings.google_drive_folder_id = data['google_drive_folder_id']
            
            settings.updated_by_user_id = current_user.id
            settings.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            from flask import current_app
            if hasattr(current_app, 'reschedule_backup_jobs'):
                current_app.reschedule_backup_jobs()
            
            log_audit(
                user_id=current_user.id,
                action='EDIT',
                target_type='BackupSettings',
                target_id=str(settings.id),
                description=f'Updated backup settings'
            )
            
            return jsonify({
                'success': True,
                'message': 'تم تحديث إعدادات النسخ الاحتياطي بنجاح'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'فشل التحديث: {str(e)}'
            }), 500
    
    return jsonify({
        'settings': {
            'auto_backup_enabled': settings.auto_backup_enabled,
            'backup_frequency': settings.backup_frequency.value,
            'backup_hour': settings.backup_hour,
            'retention_days': settings.retention_days,
            'google_drive_enabled': settings.google_drive_enabled,
            'google_drive_folder_id': settings.google_drive_folder_id,
            'last_backup_at': settings.last_backup_at.isoformat() if settings.last_backup_at else None,
            'last_backup_status': settings.last_backup_status,
            'last_backup_message': settings.last_backup_message
        }
    })


@admin_bp.route('/backup/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_old_backups():
    """Clean up old backups based on retention policy"""
    from k9.utils.backup_utils import LocalBackupManager
    from k9.models.models import BackupSettings
    
    settings = BackupSettings.get_settings()
    backup_manager = LocalBackupManager()
    
    count = backup_manager.cleanup_old_backups(settings.retention_days)
    
    log_audit(
        user_id=current_user.id,
        action='CLEANUP',
        target_type='Backup',
        target_id='cleanup',
        description=f'Cleaned up {count} old backups (retention: {settings.retention_days} days)'
    )
    
    return jsonify({
        'success': True,
        'message': f'تم حذف {count} نسخة احتياطية قديمة',
        'count': count
    })


@admin_bp.route('/google-drive/connect')
@login_required
@admin_required
def google_drive_connect():
    """Initiate Google Drive OAuth flow"""
    from k9.utils.google_drive_manager import GoogleDriveManager
    import secrets
    
    try:
        drive_manager = GoogleDriveManager()
        redirect_uri = url_for('admin.google_drive_callback', _external=True)
        
        authorization_url, state = drive_manager.get_authorization_url(redirect_uri)
        
        session['google_oauth_state'] = state
        session['google_oauth_user_id'] = str(current_user.id)
        
        return redirect(authorization_url)
        
    except ValueError as e:
        flash(f'خطأ في الإعداد: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))
    except Exception as e:
        flash(f'فشل الاتصال بـ Google Drive: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/google-drive/callback')
@login_required
@admin_required
def google_drive_callback():
    """Handle Google Drive OAuth callback"""
    if not has_permission("admin.google_drive.manage"):
        return redirect("/unauthorized")
    
    from k9.utils.google_drive_manager import GoogleDriveManager
    from k9.models.models import BackupSettings
    import json
    
    state = session.get('google_oauth_state')
    stored_user_id = session.get('google_oauth_user_id')
    
    if not state or stored_user_id != str(current_user.id):
        session.pop('google_oauth_state', None)
        session.pop('google_oauth_user_id', None)
        flash('جلسة OAuth غير صالحة', 'error')
        return redirect(url_for('admin.backup_management'))
    
    try:
        drive_manager = GoogleDriveManager()
        redirect_uri = url_for('admin.google_drive_callback', _external=True)
        
        credentials_dict = drive_manager.exchange_code_for_credentials(
            authorization_response=request.url,
            redirect_uri=redirect_uri,
            state=state
        )
        
        user_info = drive_manager.get_user_info(credentials_dict)
        
        success, folder_id, error = drive_manager.find_or_create_backup_folder(credentials_dict)
        
        if not success:
            session.pop('google_oauth_state', None)
            session.pop('google_oauth_user_id', None)
            flash(f'فشل إنشاء مجلد النسخ الاحتياطي: {error}', 'error')
            return redirect(url_for('admin.backup_management'))
        
        settings = BackupSettings.get_settings()
        settings.google_drive_credentials = json.dumps(credentials_dict)
        settings.google_drive_folder_id = folder_id
        settings.google_drive_enabled = True
        settings.updated_by_user_id = current_user.id
        settings.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        session.pop('google_oauth_state', None)
        session.pop('google_oauth_user_id', None)
        
        log_audit(
            user_id=current_user.id,
            action='CONNECT',
            target_type='GoogleDrive',
            target_id=folder_id,
            description=f'Connected Google Drive account: {user_info.get("email") if user_info else "unknown"}'
        )
        
        flash(f'تم الاتصال بـ Google Drive بنجاح ({user_info.get("email") if user_info else ""})', 'success')
        return redirect(url_for('admin.backup_management'))
        
    except Exception as e:
        db.session.rollback()
        session.pop('google_oauth_state', None)
        session.pop('google_oauth_user_id', None)
        flash(f'فشل الاتصال بـ Google Drive: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/google-drive/disconnect', methods=['POST'])
@login_required
@admin_required
def google_drive_disconnect():
    """Disconnect Google Drive and revoke tokens"""
    from k9.utils.google_drive_manager import GoogleDriveManager
    from k9.models.models import BackupSettings
    import json
    
    try:
        settings = BackupSettings.get_settings()
        
        if settings.google_drive_credentials:
            try:
                credentials_dict = json.loads(settings.google_drive_credentials)
                drive_manager = GoogleDriveManager()
                drive_manager.revoke_credentials(credentials_dict)
            except Exception as e:
                logger.warning(f"Failed to revoke Google Drive credentials: {e}")
        
        settings.google_drive_credentials = None
        settings.google_drive_folder_id = None
        settings.google_drive_enabled = False
        settings.updated_by_user_id = current_user.id
        settings.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_audit(
            user_id=current_user.id,
            action='DISCONNECT',
            target_type='GoogleDrive',
            target_id='disconnect',
            description='Disconnected Google Drive account'
        )
        
        return jsonify({
            'success': True,
            'message': 'تم قطع الاتصال بـ Google Drive بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'فشل قطع الاتصال: {str(e)}'
        }), 500


@admin_bp.route('/google-drive/status')
@login_required
@admin_required
def google_drive_status():
    """Get Google Drive connection status"""
    from k9.utils.google_drive_manager import GoogleDriveManager
    from k9.models.models import BackupSettings
    import json
    
    settings = BackupSettings.get_settings()
    
    if not settings.google_drive_credentials:
        return jsonify({
            'connected': False,
            'enabled': settings.google_drive_enabled
        })
    
    try:
        credentials_dict = json.loads(settings.google_drive_credentials)
        drive_manager = GoogleDriveManager()
        
        credentials_dict = drive_manager.refresh_credentials(credentials_dict)
        
        if json.dumps(credentials_dict) != settings.google_drive_credentials:
            settings.google_drive_credentials = json.dumps(credentials_dict)
            db.session.commit()
        
        user_info = drive_manager.get_user_info(credentials_dict)
        
        return jsonify({
            'connected': True,
            'enabled': settings.google_drive_enabled,
            'user_email': user_info.get('email') if user_info else None,
            'user_name': user_info.get('name') if user_info else None,
            'folder_id': settings.google_drive_folder_id
        })
        
    except Exception as e:
        logger.error(f"Failed to get Google Drive status: {e}")
        return jsonify({
            'connected': False,
            'enabled': settings.google_drive_enabled,
            'error': str(e)
        })
# ============================================================================
# Notifications Routes (For Admins and Project Managers)
# ============================================================================

@admin_bp.route('/notifications')
@login_required
def notifications():
    """صفحة الإشعارات للأدمن ومسؤولي المشاريع"""
    if not has_permission("admin.notifications.view"):
        return redirect("/unauthorized")
    
    from k9.models.models_handler_daily import Notification
    from k9.services.handler_service import NotificationService
    
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
    
    return render_template('admin/notifications.html',
                         page_title='الإشعارات',
                         notifications=pagination.items,
                         pagination=pagination,
                         unread_count=unread_count,
                         total_count=total_count)


@admin_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """تعليم الإشعار كمقروء"""
    from k9.services.handler_service import NotificationService
    NotificationService.mark_as_read(notification_id)
    return jsonify({'success': True})


@admin_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """تعليم جميع الإشعارات كمقروءة"""
    from k9.services.handler_service import NotificationService
    count = NotificationService.mark_all_as_read(str(current_user.id))
    return jsonify({'success': True, 'count': count})


@admin_bp.route('/api/unread-count')
@csrf.exempt
@login_required
@admin_required
def get_unread_count():
    """API: الحصول على عدد الإشعارات غير المقروءة"""
    if not has_permission("admin.general.access"):
        return redirect("/unauthorized")
    
    from k9.services.handler_service import NotificationService
    count = len(NotificationService.get_user_notifications(
        str(current_user.id), unread_only=True
    ))
    return jsonify({'count': count})


@admin_bp.route('/reports/pending')
@login_required
@admin_required
def admin_pending_reports():
    """صفحة التقارير بانتظار مراجعة الإدارة العامة"""
    from k9.services.report_review_service import ReportReviewService
    
    reports = ReportReviewService.get_forwarded_reports(str(current_user.id))
    
    total_count = sum(len(reports_list) for reports_list in reports.values())
    
    return render_template('admin/pending_reports.html',
                         page_title='التقارير بانتظار المراجعة',
                         reports=reports,
                         total_count=total_count)


@admin_bp.route('/reports/<report_type>/<report_id>/approve', methods=['POST'])
@login_required
@admin_required
def admin_approve_report(report_type, report_id):
    """اعتماد تقرير من الإدارة العامة"""
    from k9.services.report_review_service import ReportReviewService
    
    data = request.get_json() or {}
    notes = data.get('notes', '').strip()
    
    success, message = ReportReviewService.admin_approve(
        report_type=report_type.upper(),
        report_id=report_id,
        admin_user_id=str(current_user.id),
        notes=notes if notes else None
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 400


@admin_bp.route('/reports/<report_type>/<report_id>/reject', methods=['POST'])
@login_required
@admin_required
def admin_reject_report(report_type, report_id):
    """رفض تقرير من الإدارة العامة"""
    from k9.services.report_review_service import ReportReviewService
    
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    
    if not reason:
        return jsonify({'success': False, 'error': 'يجب إدخال سبب الرفض'}), 400
    
    success, message = ReportReviewService.admin_reject(
        report_type=report_type.upper(),
        report_id=report_id,
        admin_user_id=str(current_user.id),
        reason=reason
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 400


@admin_bp.route('/api/reports/pending/count')
@login_required
@admin_required
def get_pending_reports_count():
    """API: الحصول على عدد التقارير بانتظار المراجعة"""
    if not has_permission("admin.reports.view_pending"):
        return redirect("/unauthorized")
    
    from k9.services.report_review_service import ReportReviewService
    
    reports = ReportReviewService.get_forwarded_reports(str(current_user.id))
    total_count = sum(len(reports_list) for reports_list in reports.values())
    
    return jsonify({
        'total': total_count,
        'handler': len(reports.get('HANDLER', [])),
        'trainer': len(reports.get('TRAINER', [])),
        'vet': len(reports.get('VET', [])),
        'caretaker': len(reports.get('CARETAKER', []))
    })


@admin_bp.route('/reports/handler/<report_id>/export/pdf')
@login_required
@admin_required
def export_handler_report_pdf(report_id):
    """تصدير تقرير السائس اليومي إلى PDF - الإدارة العامة"""
    from k9.services.report_export_service import ReportExportService
    from flask import send_file
    
    report = HandlerReport.query.get_or_404(report_id)
    
    pdf_buffer = ReportExportService.export_handler_report_to_pdf(report_id)
    if not pdf_buffer:
        flash('فشل في تصدير التقرير', 'error')
        return redirect(url_for('admin.dashboard'))
    
    filename = f"handler_report_{report.date.strftime('%Y%m%d')}_{report.dog.code if report.dog else 'unknown'}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/reports/handler/<report_id>/export/excel')
@login_required
@admin_required
def export_handler_report_excel(report_id):
    """تصدير تقرير السائس اليومي إلى Excel - الإدارة العامة"""
    from k9.services.report_export_service import ReportExportService
    from flask import send_file
    
    report = HandlerReport.query.get_or_404(report_id)
    
    excel_buffer = ReportExportService.export_handler_report_to_excel(report_id)
    if not excel_buffer:
        flash('فشل في تصدير التقرير', 'error')
        return redirect(url_for('admin.dashboard'))
    
    filename = f"handler_report_{report.date.strftime('%Y%m%d')}_{report.dog.code if report.dog else 'unknown'}.xlsx"
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/reports/shift/<report_id>/export/pdf')
@login_required
@admin_required
def export_shift_report_pdf(report_id):
    """تصدير تقرير الوردية إلى PDF - الإدارة العامة"""
    from k9.services.report_export_service import ReportExportService
    from flask import send_file
    
    report = ShiftReport.query.get_or_404(report_id)
    
    pdf_buffer = ReportExportService.export_shift_report_to_pdf(report_id)
    if not pdf_buffer:
        flash('فشل في تصدير التقرير', 'error')
        return redirect(url_for('admin.dashboard'))
    
    filename = f"shift_report_{report.date.strftime('%Y%m%d')}_{report.dog.code if report.dog else 'unknown'}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/reports/shift/<report_id>/export/excel')
@login_required
@admin_required
def export_shift_report_excel(report_id):
    """تصدير تقرير الوردية إلى Excel - الإدارة العامة"""
    from k9.services.report_export_service import ReportExportService
    from flask import send_file
    
    report = ShiftReport.query.get_or_404(report_id)
    
    excel_buffer = ReportExportService.export_shift_report_to_excel(report_id)
    if not excel_buffer:
        flash('فشل في تصدير التقرير', 'error')
        return redirect(url_for('admin.dashboard'))
    
    filename = f"shift_report_{report.date.strftime('%Y%m%d')}_{report.dog.code if report.dog else 'unknown'}.xlsx"
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# ============================================================================
# Multi-Cloud Backup Integration Routes
# ============================================================================

@admin_bp.route('/backup/cloud/status')
@login_required
@admin_required
@csrf.exempt
def cloud_backup_status():
    """Get cloud backup connection and storage status"""
    from k9.services.backup_manager import BackupManager
    
    try:
        backup_manager = BackupManager(str(current_user.id))
        connections = backup_manager.get_connection_status()
        storage = backup_manager.get_storage_status()
        
        return jsonify({
            'success': True,
            'connections': connections,
            'storage': storage
        })
    except Exception as e:
        current_app.logger.error(f"Error getting cloud backup status: {e}")
        return jsonify({
            'success': False,
            'message': 'فشل تحميل حالة النسخ السحابي',
            'errors': [str(e)]
        }), 500


@admin_bp.route('/backup/cloud/create-distributed', methods=['POST'])
@login_required
@admin_required
def create_distributed_backup():
    """Create backup and distribute to selected cloud providers"""
    from k9.services.backup_manager import BackupManager
    
    try:
        data = request.get_json() or {}
        
        backup_manager = BackupManager(str(current_user.id))
        results = backup_manager.create_and_distribute_backup(
            include_local=data.get('include_local', True),
            include_google_drive=data.get('include_google_drive', True),
            include_dropbox=data.get('include_dropbox', True)
        )
        
        if results['success']:
            log_audit(
                user_id=current_user.id,
                action='CREATE',
                target_type='MultiCloudBackup',
                target_id=results.get('backup_file', 'unknown'),
                description=f'Created distributed backup: Local={results["local"]["success"]}, Drive={results["google_drive"]["success"]}, Dropbox={results["dropbox"]["success"]}'
            )
            
            return jsonify({
                'success': True,
                'message': 'تم إنشاء النسخة الاحتياطية وتوزيعها بنجاح',
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل إنشاء النسخة الاحتياطية',
                'errors': results.get('errors', [])
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating distributed backup: {e}")
        return jsonify({
            'success': False,
            'message': 'فشل إنشاء النسخة الاحتياطية',
            'errors': [str(e)]
        }), 500


@admin_bp.route('/backup/cloud/google-drive/connect')
@login_required
@admin_required
def connect_google_drive_v2():
    """Initiate Google Drive OAuth connection"""
    from k9.services.google_drive_service import GoogleDriveService
    
    try:
        service = GoogleDriveService(str(current_user.id))
        redirect_uri = url_for('admin.google_drive_callback_v2', _external=True)
        auth_url, state = service.get_authorization_url(redirect_uri)
        
        session['cloud_oauth_provider'] = 'google_drive'
        session['cloud_oauth_user_id'] = str(current_user.id)
        session['cloud_oauth_state'] = state
        
        return redirect(auth_url)
        
    except ValueError as e:
        flash(f'خطأ في الإعداد: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))
    except Exception as e:
        current_app.logger.error(f"Error initiating Google Drive OAuth: {e}")
        flash(f'فشل الاتصال بـ Google Drive: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/backup/cloud/google-drive/callback')
@csrf.exempt
def google_drive_callback_v2():
    """Handle Google Drive OAuth callback"""
    from k9.services.google_drive_service import GoogleDriveService
    
    stored_provider = session.get('cloud_oauth_provider')
    stored_user_id = session.get('cloud_oauth_user_id')
    stored_state = session.get('cloud_oauth_state')
    
    if not stored_provider or stored_provider != 'google_drive' or not stored_state or not stored_user_id:
        session.pop('cloud_oauth_provider', None)
        session.pop('cloud_oauth_user_id', None)
        session.pop('cloud_oauth_state', None)
        flash('جلسة OAuth غير صالحة', 'error')
        return redirect(url_for('admin.backup_management'))
    
    try:
        code = request.args.get('code')
        state_from_callback = request.args.get('state')
        
        if not code or not state_from_callback or state_from_callback != stored_state:
            session.pop('cloud_oauth_provider', None)
            session.pop('cloud_oauth_user_id', None)
            session.pop('cloud_oauth_state', None)
            flash('رمز التفويض أو الحالة غير صالحة', 'error')
            return redirect(url_for('admin.backup_management'))
        
        service = GoogleDriveService(str(stored_user_id))
        redirect_uri = url_for('admin.google_drive_callback_v2', _external=True)
        
        success = service.handle_oauth_callback(code, redirect_uri, stored_state)
        
        session.pop('cloud_oauth_provider', None)
        session.pop('cloud_oauth_user_id', None)
        
        if success:
            flash('تم ربط Google Drive بنجاح!', 'success')
        else:
            flash('فشل ربط Google Drive', 'error')
        
        return redirect(url_for('admin.backup_management'))
        
    except Exception as e:
        current_app.logger.error(f"Error handling Google Drive callback: {e}")
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/backup/cloud/dropbox/connect')
@login_required
@admin_required
def connect_dropbox():
    """Initiate Dropbox OAuth connection"""
    from k9.services.dropbox_service import DropboxService
    
    try:
        service = DropboxService(str(current_user.id))
        redirect_uri = url_for('admin.dropbox_callback', _external=True)
        auth_url, state = service.get_authorization_url(redirect_uri)
        
        session['cloud_oauth_provider'] = 'dropbox'
        session['cloud_oauth_user_id'] = str(current_user.id)
        session['cloud_oauth_state'] = state
        
        return redirect(auth_url)
        
    except ValueError as e:
        flash(f'خطأ في الإعداد: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))
    except Exception as e:
        current_app.logger.error(f"Error initiating Dropbox OAuth: {e}")
        flash(f'فشل الاتصال بـ Dropbox: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/backup/cloud/dropbox/callback')
@csrf.exempt
def dropbox_callback():
    """Handle Dropbox OAuth callback"""
    from k9.services.dropbox_service import DropboxService
    
    stored_provider = session.get('cloud_oauth_provider')
    stored_user_id = session.get('cloud_oauth_user_id')
    stored_state = session.get('cloud_oauth_state')
    
    if not stored_provider or stored_provider != 'dropbox' or not stored_state or not stored_user_id:
        session.pop('cloud_oauth_provider', None)
        session.pop('cloud_oauth_user_id', None)
        session.pop('cloud_oauth_state', None)
        flash('جلسة OAuth غير صالحة', 'error')
        return redirect(url_for('admin.backup_management'))
    
    try:
        code = request.args.get('code')
        state_from_callback = request.args.get('state')
        
        if not code or not state_from_callback or state_from_callback != stored_state:
            session.pop('cloud_oauth_provider', None)
            session.pop('cloud_oauth_user_id', None)
            session.pop('cloud_oauth_state', None)
            flash('رمز التفويض أو الحالة غير صالحة', 'error')
            return redirect(url_for('admin.backup_management'))
        
        service = DropboxService(str(stored_user_id))
        redirect_uri = url_for('admin.dropbox_callback', _external=True)
        
        success = service.handle_oauth_callback(code, redirect_uri, stored_state)
        
        session.pop('cloud_oauth_provider', None)
        session.pop('cloud_oauth_user_id', None)
        session.pop('cloud_oauth_state', None)
        
        if success:
            flash('تم ربط Dropbox بنجاح!', 'success')
        else:
            flash('فشل ربط Dropbox', 'error')
        
        return redirect(url_for('admin.backup_management'))
        
    except Exception as e:
        current_app.logger.error(f"Error handling Dropbox callback: {e}")
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('admin.backup_management'))


@admin_bp.route('/backup/cloud/disconnect/<provider>', methods=['POST'])
@login_required
@admin_required
def disconnect_cloud_provider(provider):
    """Disconnect a cloud provider"""
    from k9.services.backup_manager import BackupManager
    
    try:
        backup_manager = BackupManager(str(current_user.id))
        success = backup_manager.disconnect_provider(provider)
        
        if success:
            log_audit(
                user_id=current_user.id,
                action='DISCONNECT',
                target_type='CloudProvider',
                target_id=provider,
                description=f'Disconnected {provider}'
            )
            
            return jsonify({
                'success': True,
                'message': f'تم فصل {provider} بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'فشل الفصل'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error disconnecting {provider}: {e}")
        return jsonify({
            'success': False,
            'message': f'فشل قطع الاتصال بـ {provider}',
            'errors': [str(e)]
        }), 500


# ============================================================================
# NEW PERMISSION SYSTEM ROUTES (Step 3)
# ============================================================================

@admin_bp.route('/permissions-new')
@login_required
@require_admin_permission('admin.permissions.view')
def permissions_management_new():
    """New permission management interface"""
    from k9.models.permissions_new import Permission
    from k9.models.models import User
    
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    return render_template('admin/permissions_new.html', users=users)

@admin_bp.route('/permissions-new/api/users')
@login_required
@require_admin_permission('admin.permissions.view')
def get_users_for_permissions():
    """Get all active users"""
    from k9.models.models import User
    
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    return jsonify({
        'users': [
            {
                'id': str(u.id),
                'username': u.username,
                'full_name': u.full_name,
                'role': u.role.value
            }
            for u in users
        ]
    })

@admin_bp.route('/permissions-new/api/user/<user_id>/permissions')
@login_required
@require_admin_permission('admin.permissions.view')
def get_user_permissions_new(user_id):
    """Get all permissions for a user"""
    from k9.utils.permissions_new import get_user_permission_keys
    
    perm_keys = get_user_permission_keys(user_id)
    return jsonify({
        'user_id': user_id,
        'permissions': list(perm_keys)
    })

@admin_bp.route('/permissions-new/api/grant', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def grant_permission_api():
    """Grant a permission to a user"""
    from k9.utils.permissions_new import grant_permission
    
    data = request.get_json()
    user_id = data.get('user_id')
    permission_key = data.get('permission_key')
    
    success = grant_permission(user_id, permission_key, current_user.id)
    
    if success:
        return jsonify({'success': True, 'message': 'تم منح الصلاحية بنجاح'})
    else:
        return jsonify({'success': False, 'error': 'فشل في منح الصلاحية'}), 400

@admin_bp.route('/permissions-new/api/revoke', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def revoke_permission_api():
    """Revoke a permission from a user"""
    from k9.utils.permissions_new import revoke_permission
    
    data = request.get_json()
    user_id = data.get('user_id')
    permission_key = data.get('permission_key')
    
    success = revoke_permission(user_id, permission_key, current_user.id)
    
    if success:
        return jsonify({'success': True, 'message': 'تم إلغاء الصلاحية بنجاح'})
    else:
        return jsonify({'success': False, 'error': 'فشل في إلغاء الصلاحية'}), 400

@admin_bp.route('/permissions-new/api/permissions-catalog')
@login_required
@require_admin_permission('admin.permissions.view')
def get_permissions_catalog():
    """Get all permissions grouped by category"""
    from k9.utils.permissions_new import get_all_permissions_grouped
    
    grouped = get_all_permissions_grouped()
    
    result = {}
    for category, perms in grouped.items():
        result[category] = [
            {
                'id': str(p.id),
                'key': p.key,
                'name': p.name,
                'name_ar': p.name_ar,
                'name_en': p.name_en,
                'description': p.description
            }
            for p in perms
        ]
    
    return jsonify({'catalog': result})


@admin_bp.route('/permissions-advanced')
@login_required
@require_admin_permission('admin.permissions.view')
def permissions_management_advanced():
    """Advanced permission management interface with project-user-permissions workflow"""
    return render_template('admin/permissions_advanced.html')


@admin_bp.route('/permissions-new/api/toggle-permission', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def toggle_permission_api():
    """Toggle a permission for a user (grant or revoke)"""
    from k9.utils.permissions_new import grant_permission, revoke_permission
    
    data = request.get_json()
    user_id = data.get('user_id')
    permission_key = data.get('permission_key')
    granted = data.get('granted', False)
    
    if granted:
        success = grant_permission(user_id, permission_key, current_user.id)
    else:
        success = revoke_permission(user_id, permission_key, current_user.id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update permission'}), 400


@admin_bp.route('/permissions-new/api/apply-template', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def apply_permission_template():
    """Apply a permission template to a user using V2 role system"""
    from k9.services.permission_service import PermissionService
    from k9.models.permissions_v2 import Role
    from app import db
    
    data = request.get_json()
    user_id = data.get('user_id')
    template = data.get('template')
    
    if not user_id or not template:
        return jsonify({'error': 'Missing user_id or template'}), 400
    
    try:
        # Map templates to V2 roles - comprehensive mapping
        template_to_role = {
            'full_access': 'super_admin',
            'pm_access': 'project_manager',
            'view_only': 'viewer',
            'handler_access': 'handler',
            'security_access': 'general_admin',
            'vet_access': 'veterinarian',
            'breeding_manager': 'breeder',
            'trainer_access': 'trainer',
        }
        
        if template == 'custom':
            return jsonify({'success': True, 'granted_count': 0, 'message': 'Custom template - no changes made'})
        
        role_name = template_to_role.get(template)
        if not role_name:
            return jsonify({'error': 'Unknown template'}), 400
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'error': f'Role {role_name} not found'}), 400
        
        # Clear existing roles and assign the template role
        PermissionService.clear_user_roles(user_id, cleared_by_id=current_user.id)
        PermissionService.grant_role(user_id, role_name, granted_by_id=current_user.id)
        
        # Get permissions count from the ROLE_PERMISSIONS constant
        from k9.models.permissions_v2 import ROLE_PERMISSIONS
        role_permissions = ROLE_PERMISSIONS.get(role_name, [])
        permissions_count = len(role_permissions)
        
        return jsonify({
            'success': True,
            'granted_count': permissions_count,
            'role_assigned': role.name_ar or role.name
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying template: {e}")
        return jsonify({'error': f'Failed to apply template: {str(e)}'}), 500


@admin_bp.route('/permissions-new/api/revoke-all', methods=['POST'])
@login_required
@require_admin_permission('admin.permissions.edit')
def revoke_all_permissions():
    """Revoke all permissions from a user using V2 system"""
    from k9.services.permission_service import PermissionService
    from k9.models.permissions_v2 import UserRoleAssignment, PermissionOverride
    from app import db
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    try:
        # Count existing assignments and overrides
        role_count = UserRoleAssignment.query.filter_by(user_id=user_id).count()
        override_count = PermissionOverride.query.filter_by(user_id=user_id).count()
        
        # Clear all roles and overrides
        PermissionService.clear_user_roles(user_id, cleared_by_id=current_user.id)
        PermissionService.clear_user_overrides(user_id, cleared_by_id=current_user.id)
        
        return jsonify({
            'success': True,
            'revoked_count': role_count + override_count
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error revoking all permissions: {e}")
        return jsonify({'error': f'Failed to revoke permissions: {str(e)}'}), 500


@admin_bp.route('/permissions-new/api/user/<user_id>/audit')
@login_required
@require_admin_permission('admin.permissions.view')
def get_user_permission_audit(user_id):
    """Get permission change audit log for a user with pagination (V2)"""
    from k9.models.permissions_v2 import PermissionAuditLog
    from k9.models.models import User
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    
    query = PermissionAuditLog.query.filter_by(
        target_user_id=user_id
    ).order_by(PermissionAuditLog.created_at.desc())
    
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    
    actor_ids = {log.changed_by_id for log in logs if log.changed_by_id}
    actors = {u.id: u for u in User.query.filter(User.id.in_(actor_ids)).all()} if actor_ids else {}
    
    result = []
    for log in logs:
        actor = actors.get(log.changed_by_id) if log.changed_by_id else None
        result.append({
            'timestamp': log.created_at.isoformat() if log.created_at else None,
            'permission_key': log.details,
            'action': log.action,
            'actor_name': actor.full_name if actor else 'النظام',
            'ip_address': log.ip_address
        })
    
    return jsonify({
        'logs': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


# =============================================================================
# V2 Role Management Routes
# =============================================================================

@admin_bp.route('/roles')
@login_required
@admin_required
def roles_list():
    """List all V2 roles"""
    from k9.models.permissions_v2 import Role, ROLE_PERMISSIONS
    
    roles = Role.query.filter_by(is_active=True).order_by(Role.name).all()
    
    roles_data = []
    for role in roles:
        role_permissions = ROLE_PERMISSIONS.get(role.name, [])
        roles_data.append({
            'id': str(role.id),
            'name': role.name,
            'name_ar': role.name_ar,
            'description': role.description,
            'is_system': role.is_system,
            'permissions': role_permissions,
            'permission_count': len(role_permissions)
        })
    
    return render_template('admin/roles_list.html', roles=roles_data)


@admin_bp.route('/roles/api/list')
@login_required
@admin_required
def api_roles_list():
    """API: Get all roles"""
    from k9.models.permissions_v2 import Role, ROLE_PERMISSIONS
    
    roles = Role.query.filter_by(is_active=True).order_by(Role.name).all()
    
    return jsonify({
        'roles': [{
            'id': str(r.id),
            'name': r.name,
            'name_ar': r.name_ar,
            'description': r.description,
            'is_system': r.is_system,
            'permissions': ROLE_PERMISSIONS.get(r.name, [])
        } for r in roles]
    })


@admin_bp.route('/roles/user/<user_id>')
@login_required
@admin_required
def get_user_roles(user_id):
    """Get V2 roles for a specific user"""
    from k9.models.permissions_v2 import UserRoleAssignment
    from k9.services.permission_service import PermissionService
    
    user = User.query.get_or_404(user_id)
    
    assignments = UserRoleAssignment.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()
    
    roles = []
    for a in assignments:
        if a.role:
            role_perms = PermissionService.get_role_permissions(a.role.name)
            roles.append({
                'assignment_id': str(a.id),
                'role_id': str(a.role_id),
                'role_name': a.role.name,
                'role_name_ar': a.role.name_ar,
                'project_id': str(a.project_id) if a.project_id else None,
                'granted_at': a.granted_at.isoformat() if a.granted_at else None,
                'expires_at': a.expires_at.isoformat() if a.expires_at else None,
                'permissions': role_perms
            })
    
    effective_permissions = list(PermissionService.get_user_permissions(user_id))
    
    return jsonify({
        'user': {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role.value if user.role else None
        },
        'roles': roles,
        'effective_permissions': effective_permissions
    })


@admin_bp.route('/roles/assign', methods=['POST'])
@login_required
@admin_required
def assign_role():
    """Assign a V2 role to a user"""
    from k9.services.permission_service import PermissionService
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        role_name = data.get('role_name')
        project_id = data.get('project_id')
        
        if not user_id or not role_name:
            return jsonify({'error': 'user_id and role_name are required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        PermissionService.grant_role(
            user_id=user_id,
            role_name=role_name,
            project_id=project_id,
            granted_by_id=str(current_user.id)
        )
        db.session.commit()
        
        log_audit(
            action='role_assigned',
            target_type='User',
            target_id=str(user_id),
            description=f"Assigned role '{role_name}' to user {user.username}"
        )
        
        PermissionService.clear_cache(user_id)
        
        return jsonify({
            'success': True,
            'message': f"تم تعيين الدور '{role_name}' للمستخدم {user.username}"
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning role: {e}")
        return jsonify({'error': f'Failed to assign role: {str(e)}'}), 500


@admin_bp.route('/roles/revoke', methods=['POST'])
@login_required
@admin_required
def revoke_role():
    """Revoke a V2 role from a user"""
    from k9.services.permission_service import PermissionService
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        role_name = data.get('role_name')
        project_id = data.get('project_id')
        
        if not user_id or not role_name:
            return jsonify({'error': 'user_id and role_name are required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        success = PermissionService.revoke_role(
            user_id=user_id,
            role_name=role_name,
            project_id=project_id
        )
        db.session.commit()
        
        if success:
            log_audit(
                action='role_revoked',
                target_type='User',
                target_id=str(user_id),
                description=f"Revoked role '{role_name}' from user {user.username}"
            )
            
            PermissionService.clear_cache(user_id)
            
            return jsonify({
                'success': True,
                'message': f"تم إلغاء الدور '{role_name}' من المستخدم {user.username}"
            })
        else:
            return jsonify({'error': 'Role assignment not found'}), 404
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error revoking role: {e}")
        return jsonify({'error': f'Failed to revoke role: {str(e)}'}), 500


@admin_bp.route('/roles/users')
@login_required
@admin_required
def roles_users_management():
    """V2 Role management interface - list users with their roles"""
    from k9.models.permissions_v2 import Role, UserRoleAssignment
    from k9.services.permission_service import PermissionService
    
    users = User.query.order_by(User.username).all()
    roles = Role.query.filter_by(is_active=True).order_by(Role.name).all()
    
    users_data = []
    for user in users:
        assignments = UserRoleAssignment.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        
        user_roles = []
        for a in assignments:
            if a.role:
                user_roles.append({
                    'name': a.role.name,
                    'name_ar': a.role.name_ar
                })
        
        users_data.append({
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name,
            'user_role': user.role.value if user.role else None,
            'v2_roles': user_roles
        })
    
    return render_template('admin/roles_users.html', 
                          users=users_data, 
                          roles=[{'id': str(r.id), 'name': r.name, 'name_ar': r.name_ar} for r in roles])


# =============================================================================
# Access Control Hub - Modern Permission Management
# =============================================================================

@admin_bp.route('/access-control')
@login_required
@admin_required
def access_control_hub():
    """Modern Access Control Hub - role-first permission management"""
    return render_template('admin/access_control_hub.html')


@admin_bp.route('/access-control/api/users')
@login_required
@admin_required
def access_control_users():
    """API: Get all users with their current V2 roles"""
    from k9.models.permissions_v2 import Role, UserRoleAssignment, RoleType
    
    users = User.query.order_by(User.full_name).all()
    
    users_data = []
    for user in users:
        assignment = UserRoleAssignment.query.filter_by(
            user_id=user.id,
            is_active=True,
            project_id=None
        ).first()
        
        v2_role = None
        if assignment and assignment.role:
            v2_role = assignment.role.name
        
        users_data.append({
            'id': str(user.id),
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'v2_role': v2_role,
            'legacy_role': user.role.value if user.role else None
        })
    
    return jsonify({'users': users_data})


@admin_bp.route('/access-control/api/user/<user_id>/permissions')
@login_required
@admin_required
def access_control_user_permissions(user_id):
    """API: Get a user's current role and permission overrides"""
    from k9.models.permissions_v2 import Role, UserRoleAssignment, PermissionOverride
    
    user = User.query.get_or_404(user_id)
    
    assignment = UserRoleAssignment.query.filter_by(
        user_id=user_id,
        is_active=True,
        project_id=None
    ).first()
    
    current_role = None
    if assignment and assignment.role:
        current_role = assignment.role.name
    
    overrides = {}
    override_records = PermissionOverride.query.filter_by(user_id=user_id, project_id=None).all()
    for o in override_records:
        overrides[o.permission_key] = o.is_granted
    
    return jsonify({
        'user_id': str(user.id),
        'username': user.username,
        'full_name': user.full_name,
        'current_role': current_role,
        'overrides': overrides
    })


@admin_bp.route('/access-control/api/save', methods=['POST'])
@login_required
@admin_required
def access_control_save():
    """API: Save user role and permission overrides"""
    from k9.models.permissions_v2 import Role, UserRoleAssignment, PermissionOverride, PermissionAuditLog
    from k9.services.permission_service import PermissionService
    
    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('role')
    overrides = data.get('overrides', {})
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        current_assignment = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            is_active=True,
            project_id=None
        ).first()
        
        old_role = current_assignment.role.name if current_assignment and current_assignment.role else None
        
        if new_role and new_role != old_role:
            role = Role.query.filter_by(name=new_role, is_active=True).first()
            
            if not role:
                role = Role(
                    name=new_role,
                    name_ar=get_role_arabic_name(new_role),
                    description=f'Role: {new_role}',
                    is_system=True,
                    is_active=True
                )
                db.session.add(role)
                db.session.flush()
            
            if current_assignment:
                current_assignment.is_active = False
            
            new_assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role.id,
                is_active=True,
                granted_by_id=current_user.id
            )
            db.session.add(new_assignment)
            
            audit = PermissionAuditLog(
                target_user_id=user_id,
                changed_by_id=current_user.id,
                action='role_change',
                entity_type='role',
                details=f'Changed role from {old_role or "none"} to {new_role}',
                ip_address=request.remote_addr
            )
            db.session.add(audit)
        
        existing_overrides_list = PermissionOverride.query.filter_by(user_id=user_id, project_id=None).all()
        existing_overrides = {o.permission_key: o for o in existing_overrides_list}
        processed_keys = set()
        
        for perm_key, is_granted in overrides.items():
            processed_keys.add(perm_key)
            
            if perm_key in existing_overrides:
                existing = existing_overrides[perm_key]
                if existing.is_granted != is_granted:
                    existing.is_granted = is_granted
                    existing.granted_by_id = current_user.id
                    
                    audit = PermissionAuditLog(
                        target_user_id=user_id,
                        changed_by_id=current_user.id,
                        action='grant' if is_granted else 'revoke',
                        entity_type='permission_override',
                        details=f'Updated override: {perm_key}',
                        ip_address=request.remote_addr
                    )
                    db.session.add(audit)
            else:
                new_override = PermissionOverride(
                    user_id=user_id,
                    permission_key=perm_key,
                    is_granted=is_granted,
                    project_id=None,
                    granted_by_id=current_user.id
                )
                db.session.add(new_override)
                
                audit = PermissionAuditLog(
                    target_user_id=user_id,
                    changed_by_id=current_user.id,
                    action='grant' if is_granted else 'revoke',
                    entity_type='permission_override',
                    details=f'New override: {perm_key}',
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
        
        for perm_key, override_to_remove in existing_overrides.items():
            if perm_key not in processed_keys:
                db.session.delete(override_to_remove)
                audit = PermissionAuditLog(
                    target_user_id=user_id,
                    changed_by_id=current_user.id,
                    action='revoke',
                    entity_type='permission_override',
                    details=f'Removed override: {perm_key}',
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
        
        db.session.commit()
        
        logger.info(f"Access control updated for user {user.username} by {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Permissions saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving access control: {e}")
        return jsonify({'error': str(e)}), 500


def get_role_arabic_name(role_name):
    """Get Arabic name for a role"""
    names = {
        'super_admin': 'مسؤول أعلى',
        'general_admin': 'مسؤول عام',
        'project_manager': 'مدير مشروع',
        'handler': 'سائس',
        'trainer': 'مدرب',
        'veterinarian': 'طبيب بيطري',
        'breeder': 'مربي',
        'viewer': 'مشاهد'
    }
    return names.get(role_name, role_name)
