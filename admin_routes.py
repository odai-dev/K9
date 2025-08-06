"""
Admin Routes for Enhanced Permission Management System
Provides comprehensive permission control interface for GENERAL_ADMIN users
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from permission_decorators import admin_required
from permission_utils import (
    PERMISSION_STRUCTURE, get_user_permissions_matrix, update_permission, 
    bulk_update_permissions, get_project_managers, get_all_projects,
    initialize_default_permissions, export_permissions_matrix
)
from models import User, Project, SubPermission, PermissionAuditLog, PermissionType, UserRole
from app import db
from utils import log_audit
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
    
    matrix = get_user_permissions_matrix(user, project_id)
    
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
    
    success = update_permission(
        admin_user=current_user,
        target_user=user,
        section=data['section'],
        subsection=data['subsection'],
        permission_type=permission_type,
        project_id=project_id,
        is_granted=data['is_granted']
    )
    
    if success:
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
    
    count = bulk_update_permissions(
        admin_user=current_user,
        target_user=user,
        section=data['section'],
        is_granted=data['is_granted'],
        project_id=project_id
    )
    
    if count > 0:
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
    
    permissions_data = export_permissions_matrix(user, project_id)
    
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
    matrix = get_user_permissions_matrix(user, project_id)
    
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
    matrix = get_user_permissions_matrix(user, project_id)
    
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