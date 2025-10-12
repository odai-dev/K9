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
import csv
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

@admin_bp.route('/permissions/export-csv')
@login_required
@admin_required
def export_all_permissions_csv():
    """Export all permissions to CSV for compliance tracking"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'User ID', 'Username', 'Full Name', 'Project ID', 'Section', 'Subsection', 
        'Permission Type', 'Is Granted', 'Updated At'
    ])
    
    # Get all permissions
    permissions = SubPermission.query.join(User).all()
    
    for perm in permissions:
        writer.writerow([
            perm.user_id,
            perm.user.username,
            perm.user.full_name,
            perm.project_id or 'Global',
            perm.section,
            perm.subsection,
            perm.permission_type.value,
            'Yes' if perm.is_granted else 'No',
            perm.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Log audit
    log_audit(
        user_id=current_user.id,
        action='EXPORT',
        target_type='SubPermission',
        target_id='all-permissions-csv',
        description="Exported all permissions to CSV for compliance"
    )
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        as_attachment=True,
        download_name=f"all_permissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mimetype='text/csv'
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