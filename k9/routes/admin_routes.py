"""
Admin Routes for Enhanced Permission Management System
Provides comprehensive permission control interface for GENERAL_ADMIN users
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, session
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash
from k9.utils.permission_decorators import admin_required
from k9.utils.permission_utils import (
    PERMISSION_STRUCTURE, get_user_permissions_matrix, update_permission, 
    bulk_update_permissions, get_project_managers, get_all_projects,
    initialize_default_permissions, export_permissions_matrix
)
from k9.utils.security_utils import PasswordValidator, SecurityHelper
from k9.models.models import User, Project, SubPermission, PermissionAuditLog, PermissionType, UserRole
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

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main admin dashboard with system overview and navigation"""
    from k9.models.models import User, Project, SubPermission, PermissionAuditLog, Dog, Employee, TrainingSession, VeterinaryVisit
    from sqlalchemy import func
    
    # System statistics
    stats = {
        'total_users': User.query.count(),
        'total_project_managers': User.query.filter_by(role=UserRole.PROJECT_MANAGER).count(),
        'total_projects': Project.query.count(),
        'total_dogs': Dog.query.count(),
        'total_employees': Employee.query.count(),
        'total_permissions': SubPermission.query.count(),
        'granted_permissions': SubPermission.query.filter_by(is_granted=True).count(),
    }
    
    # Recent activities
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

@admin_bp.route('/permissions')
@login_required
@admin_required
def permissions_dashboard():
    """Main permissions management dashboard"""
    project_managers = get_project_managers()
    projects = get_all_projects()
    
    return render_template('admin/permissions_dashboard.html',
                         project_managers=project_managers,
                         projects=projects,
                         permission_structure=PERMISSION_STRUCTURE)

@admin_bp.route('/permissions/user/<int:user_id>')
@login_required
@admin_required
def get_user_permissions(user_id):
    """Get permissions matrix for a specific user"""
    user = User.query.get_or_404(user_id)
    project_id = request.args.get('project_id')
    
    if user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'يمكن إدارة صلاحيات مديري المشاريع فقط'}), 400
    
    matrix = get_user_permissions_matrix(user.id, project_id=project_id)
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name
        },
        'project_id': project_id,
        'permissions': matrix
    })

@admin_bp.route('/permissions/update', methods=['POST'])
@login_required
@admin_required
def update_user_permission():
    """Update a specific permission for a user"""
    data = request.get_json()
    
    required_fields = ['user_id', 'section', 'subsection', 'permission_type', 'is_granted']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'بيانات ناقصة'}), 400
    
    user = User.query.get(data['user_id'])
    if not user or user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'مستخدم غير صحيح'}), 400
    
    try:
        permission_type = PermissionType(data['permission_type'])
    except ValueError:
        return jsonify({'error': 'نوع صلاحية غير صحيح'}), 400
    
    project_id = data.get('project_id')
    
    # Get old permission value for audit
    existing_perm = SubPermission.query.filter_by(
        user_id=user.id,
        section=data['section'],
        subsection=data['subsection'],
        permission_type=permission_type,
        project_id=project_id
    ).first()
    old_value = existing_perm.is_granted if existing_perm else False
    new_value = data['is_granted']
    
    # Create permission key for the simple function signature
    permission_key = f"{data['section']}.{data['subsection']}.{permission_type.value}"
    
    success = update_permission(
        user_id=user.id,
        permission_key=permission_key,
        granted=new_value,
        updated_by=current_user.id,
        project_id=project_id
    )
    
    if success:
        # Create audit log entry
        audit_log = PermissionAuditLog()
        audit_log.changed_by_user_id = current_user.id
        audit_log.target_user_id = user.id
        audit_log.section = data['section']
        audit_log.subsection = data['subsection']
        audit_log.permission_type = permission_type
        audit_log.project_id = project_id
        audit_log.old_value = old_value
        audit_log.new_value = new_value
        audit_log.ip_address = request.remote_addr
        audit_log.user_agent = request.headers.get('User-Agent', '')
        db.session.add(audit_log)
        db.session.commit()
        # Log audit
        log_audit(
            user_id=current_user.id,
            action='EDIT',
            target_type='SubPermission',
            target_id=f"{user.id}-{data['section']}-{data['subsection']}",
            description=f"Updated permission for {user.username}: {data['section']} -> {data['subsection']} ({data['permission_type']}) = {data['is_granted']}"
        )
        
        return jsonify({'success': True, 'message': 'تم تحديث الصلاحية بنجاح'})
    else:
        return jsonify({'error': 'فشل في تحديث الصلاحية'}), 500

@admin_bp.route('/permissions/bulk-update', methods=['POST'])
@login_required
@admin_required
def bulk_update_user_permissions():
    """Bulk update permissions for a section"""
    data = request.get_json()
    
    required_fields = ['user_id', 'section', 'is_granted']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'بيانات ناقصة'}), 400
    
    user = User.query.get(data['user_id'])
    if not user or user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'مستخدم غير صحيح'}), 400
    
    project_id = data.get('project_id')
    
    # Build permissions dict for bulk update
    permissions_dict = {
        'section': data['section'],
        'is_granted': data['is_granted'],
        'project_id': project_id
    }
    
    count = bulk_update_permissions(
        user_id=user.id,
        permissions_dict=permissions_dict,
        updated_by=current_user.id,
        project_id=project_id
    )
    
    if count > 0:
        # Create audit log entry for bulk update
        audit_log = PermissionAuditLog()
        audit_log.changed_by_user_id = current_user.id
        audit_log.target_user_id = user.id
        audit_log.section = data['section']
        audit_log.subsection = 'bulk_update'
        audit_log.permission_type = PermissionType.VIEW  # Generic for bulk operation
        audit_log.project_id = project_id
        audit_log.old_value = False
        audit_log.new_value = data['is_granted']
        audit_log.ip_address = request.remote_addr
        audit_log.user_agent = request.headers.get('User-Agent', '')
        db.session.add(audit_log)
        db.session.commit()
        # Log audit
        log_audit(
            user_id=current_user.id,
            action='EDIT',
            target_type='SubPermission',
            target_id=f"{user.id}-{data['section']}-bulk",
            description=f"Bulk updated {count} permissions for {user.username} in section {data['section']} = {data['is_granted']}"
        )
        
        return jsonify({'success': True, 'message': f'تم تحديث {count} صلاحية بنجاح', 'count': count})
    else:
        return jsonify({'error': 'فشل في التحديث المجمع'}), 500

@admin_bp.route('/permissions/initialize/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def initialize_user_permissions(user_id):
    """Initialize default permissions for a new PROJECT_MANAGER"""
    user = User.query.get_or_404(user_id)
    
    if user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'يمكن تهيئة صلاحيات مديري المشاريع فقط'}), 400
    
    initialize_default_permissions(user)
    
    # Log audit
    log_audit(
        user_id=current_user.id,
        action='CREATE',
        target_type='SubPermission',
        target_id=f"{user.id}-default-init",
        description=f"Initialized default permissions for {user.username}"
    )
    
    return jsonify({'success': True, 'message': 'تم تهيئة الصلاحيات الافتراضية بنجاح'})

@admin_bp.route('/permissions/audit')
@login_required
@admin_required
def permissions_audit_log():
    """View permission change audit log"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filter parameters
    target_user_id = request.args.get('target_user_id', type=int)
    section = request.args.get('section')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = PermissionAuditLog.query.order_by(PermissionAuditLog.created_at.desc())
    
    if target_user_id:
        query = query.filter(PermissionAuditLog.target_user_id == target_user_id)
    
    if section:
        query = query.filter(PermissionAuditLog.section == section)
    
    if start_date:
        query = query.filter(PermissionAuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(PermissionAuditLog.created_at <= end_date)
    
    audit_logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    project_managers = get_project_managers()
    
    return render_template('admin/permissions_audit.html',
                         audit_logs=audit_logs,
                         project_managers=project_managers,
                         permission_structure=PERMISSION_STRUCTURE,
                         filters={
                             'target_user_id': target_user_id,
                             'section': section,
                             'start_date': start_date,
                             'end_date': end_date
                         })

@admin_bp.route('/permissions/export/<int:user_id>')
@login_required
@admin_required
def export_user_permissions_json(user_id):
    """Export user permissions as JSON"""
    user = User.query.get_or_404(user_id)
    project_id = request.args.get('project_id')
    
    if user.role != UserRole.PROJECT_MANAGER:
        return jsonify({'error': 'يمكن تصدير صلاحيات مديري المشاريع فقط'}), 400
    
    permissions_data = export_permissions_matrix([user], project_id=project_id)
    
    # Log audit
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='SubPermission',
        target_id=f"{user.id}-export-json",
        description=f"Exported permissions matrix for {user.username}"
    )
    
    return jsonify(permissions_data)

@admin_bp.route('/permissions/export-pdf/<int:user_id>')
@login_required
@admin_required
def export_user_permissions_pdf(user_id):
    """Export user permissions as PDF"""
    user = User.query.get_or_404(user_id)
    project_id = request.args.get('project_id')
    
    if user.role != UserRole.PROJECT_MANAGER:
        flash('يمكن تصدير صلاحيات مديري المشاريع فقط', 'error')
        return redirect(url_for('admin.permissions_dashboard'))
    
    # Get permissions matrix
    matrix = get_user_permissions_matrix(user.id, project_id=project_id)
    
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
    project_info = f" - مشروع {project_id}" if project_id else " - جميع المشاريع"
    title = Paragraph(f"مصفوفة الصلاحيات - {user.full_name}{project_info}", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Create table data
    data = [['القسم', 'القسم الفرعي', 'عرض', 'إنشاء', 'تعديل', 'حذف', 'تصدير', 'تعيين', 'اعتماد']]
    
    for section, subsections in matrix.items():
        for subsection, permissions in subsections.items():
            row = [section, subsection]
            for perm_type in ['VIEW', 'CREATE', 'EDIT', 'DELETE', 'EXPORT', 'ASSIGN', 'APPROVE']:
                status = '✓' if permissions.get(perm_type, False) else '✗'
                row.append(status)
            data.append(row)
    
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
        target_type='SubPermission',
        target_id=f"{user.id}-export-pdf",
        description=f"Exported permissions PDF for {user.username}"
    )
    
    return send_file(temp_path, as_attachment=True, download_name=filename, mimetype='application/pdf')

@admin_bp.route('/permissions/export-excel')
@login_required
@admin_required
def export_all_permissions_excel():
    """Export all permissions to Excel for compliance tracking"""
    from k9.utils.excel_exporter import create_permissions_report_excel, save_excel_to_bytes
    
    # Get all permissions
    permissions = SubPermission.query.join(User).all()
    
    # Create Excel workbook
    wb = create_permissions_report_excel(permissions)
    
    # Convert to bytes
    excel_bytes = save_excel_to_bytes(wb)
    
    # Log audit
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='SubPermission',
        target_id='all-permissions-excel',
        description="Exported all permissions to Excel for compliance"
    )
    
    return send_file(
        io.BytesIO(excel_bytes),
        as_attachment=True,
        download_name=f"all_permissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@admin_bp.route('/permissions/preview/<int:user_id>')
@login_required
@admin_required
def preview_pm_view(user_id):
    """Preview what a PROJECT_MANAGER user can see (for testing)"""
    user = User.query.get_or_404(user_id)
    project_id = request.args.get('project_id')
    
    if user.role != UserRole.PROJECT_MANAGER:
        flash('يمكن معاينة عرض مديري المشاريع فقط', 'error')
        return redirect(url_for('admin.permissions_dashboard'))
    
    # Get user's permissions
    matrix = get_user_permissions_matrix(user.id, project_id=project_id)
    
    # Calculate summary statistics
    total_permissions = 0
    granted_permissions = 0
    
    for section, subsections in matrix.items():
        for subsection, permissions in subsections.items():
            for perm_type, is_granted in permissions.items():
                total_permissions += 1
                if is_granted:
                    granted_permissions += 1
    
    coverage_percentage = (granted_permissions / total_permissions * 100) if total_permissions > 0 else 0
    
    return render_template('admin/permissions_preview.html',
                         target_user=user,
                         project_id=project_id,
                         permissions_matrix=matrix,
                         coverage_percentage=round(coverage_percentage, 1),
                         granted_permissions=granted_permissions,
                         total_permissions=total_permissions)

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_profile():
    """Admin profile management with password change functionality"""
    
    # Get system stats for display (needed for all renders)
    from k9.models.models import User, Project, SubPermission, Dog, Employee
    stats = {
        'total_users': User.query.count(),
        'total_project_managers': User.query.filter_by(role=UserRole.PROJECT_MANAGER).count(),
        'total_projects': Project.query.count(),
        'total_dogs': Dog.query.count(),
        'total_employees': Employee.query.count(),
        'granted_permissions': SubPermission.query.filter_by(is_granted=True).count(),
    }
    
    # Get recent admin activities (recent permission changes)
    recent_activities = PermissionAuditLog.query.filter_by(changed_by_user_id=current_user.id).order_by(PermissionAuditLog.created_at.desc()).limit(5).all()
    
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
    from k9.models.models import BackupSettings
    from k9.utils.backup_utils import BackupManager
    
    settings = BackupSettings.get_settings()
    backup_manager = BackupManager()
    backups = backup_manager.list_backups()
    
    return render_template('admin/backup_management.html',
                         settings=settings,
                         backups=backups)


@admin_bp.route('/backup/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Create a new database backup"""
    from k9.utils.backup_utils import BackupManager
    from k9.models.models import BackupSettings
    
    data = request.get_json() or {}
    description = data.get('description', '')
    
    backup_manager = BackupManager()
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
def list_backups():
    """List all available backups"""
    from k9.utils.backup_utils import BackupManager
    
    backup_manager = BackupManager()
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
    from k9.utils.backup_utils import BackupManager
    
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    
    if not confirm:
        return jsonify({
            'success': False,
            'message': 'يرجى التأكيد على الاستعادة'
        }), 400
    
    backup_manager = BackupManager()
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
    from k9.utils.backup_utils import BackupManager
    import os
    
    backup_manager = BackupManager()
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
    from k9.utils.backup_utils import BackupManager
    
    backup_manager = BackupManager()
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
    from k9.utils.backup_utils import BackupManager
    from k9.models.models import BackupSettings
    
    settings = BackupSettings.get_settings()
    backup_manager = BackupManager()
    
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
