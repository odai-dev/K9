"""
Unified Reports Routes
======================
Routes for the unified report preview, export, and approval workflow.
Provides HTML preview of reports and handles PDF/Excel export requests.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import login_required, current_user
from functools import wraps
import logging

from k9.services.unified_report_service import UnifiedReportService
from k9.services.permission_service import PermissionService
from k9.models.report_models import (
    ReportContext, UnifiedReportStatus, UnifiedReportType,
    REPORT_TYPE_NAMES_AR, REPORT_STATUS_NAMES_AR
)

logger = logging.getLogger(__name__)

unified_reports_bp = Blueprint('unified_reports', __name__)


def require_report_access(f):
    """Decorator to ensure user has access to the report context"""
    @wraps(f)
    def decorated_function(context_id, *args, **kwargs):
        context = UnifiedReportService.get_report_context(context_id, str(current_user.id))
        if not context:
            flash('التقرير غير موجود أو ليس لديك صلاحية للوصول', 'error')
            return redirect(url_for('main.dashboard'))
        return f(context_id, *args, **kwargs)
    return decorated_function


@unified_reports_bp.route('/reports/preview/<context_id>')
@login_required
@require_report_access
def preview(context_id):
    """Render HTML preview of a report"""
    preview_data, message = UnifiedReportService.preview_report(context_id, str(current_user.id))
    
    if not preview_data:
        flash(message, 'error')
        return redirect(url_for('main.dashboard'))
    
    context = UnifiedReportService.get_report_context(context_id, str(current_user.id))
    
    can_approve = False
    can_reject = False
    can_submit = False
    can_export = preview_data.get('can_export', False)
    
    if context:
        project_id = str(context.project_id) if context.project_id else None
        
        if context.status == UnifiedReportStatus.DRAFT:
            if str(context.created_by_user_id) == str(current_user.id):
                can_submit = True
        
        elif context.status == UnifiedReportStatus.SUBMITTED:
            if PermissionService.has_permission(str(current_user.id), 'pm.reports.approve', project_id):
                if str(context.created_by_user_id) != str(current_user.id):
                    can_approve = True
                    can_reject = True
        
        elif context.status in [UnifiedReportStatus.PM_APPROVED, UnifiedReportStatus.FORWARDED_TO_ADMIN]:
            if PermissionService.has_any_permission(str(current_user.id), ['admin.*', 'admin.reports.approve']):
                can_approve = True
                can_reject = True
    
    return render_template(
        'reports/unified_preview.html',
        preview_data=preview_data,
        context=context,
        can_approve=can_approve,
        can_reject=can_reject,
        can_submit=can_submit,
        can_export=can_export,
        REPORT_TYPE_NAMES_AR=REPORT_TYPE_NAMES_AR,
        REPORT_STATUS_NAMES_AR=REPORT_STATUS_NAMES_AR
    )


@unified_reports_bp.route('/reports/export/<context_id>/pdf')
@login_required
@require_report_access
def export_pdf(context_id):
    """Export report to PDF format"""
    pdf_buffer, message = UnifiedReportService.export_pdf(context_id, str(current_user.id))
    
    if not pdf_buffer:
        flash(message, 'error')
        return redirect(url_for('unified_reports.preview', context_id=context_id))
    
    context = UnifiedReportService.get_report_context(context_id)
    filename = f"report_{context.report_type.value}_{context_id[:8]}.pdf" if context else f"report_{context_id[:8]}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@unified_reports_bp.route('/reports/export/<context_id>/excel')
@login_required
@require_report_access
def export_excel(context_id):
    """Export report to Excel format"""
    excel_buffer, message = UnifiedReportService.export_excel(context_id, str(current_user.id))
    
    if not excel_buffer:
        flash(message, 'error')
        return redirect(url_for('unified_reports.preview', context_id=context_id))
    
    context = UnifiedReportService.get_report_context(context_id)
    filename = f"report_{context.report_type.value}_{context_id[:8]}.xlsx" if context else f"report_{context_id[:8]}.xlsx"
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@unified_reports_bp.route('/reports/<context_id>/submit', methods=['POST'])
@login_required
@require_report_access
def submit_report(context_id):
    """Submit report for PM review"""
    success, message = UnifiedReportService.submit_for_review(context_id, str(current_user.id))
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('unified_reports.preview', context_id=context_id))


@unified_reports_bp.route('/reports/<context_id>/approve', methods=['POST'])
@login_required
@require_report_access
def approve_report(context_id):
    """PM or Admin approve a report"""
    notes = request.form.get('notes', '').strip()
    
    context = UnifiedReportService.get_report_context(context_id)
    if not context:
        flash('التقرير غير موجود', 'error')
        return redirect(url_for('main.dashboard'))
    
    if context.status == UnifiedReportStatus.SUBMITTED:
        success, message = UnifiedReportService.pm_approve(context_id, str(current_user.id), notes)
    elif context.status in [UnifiedReportStatus.PM_APPROVED, UnifiedReportStatus.FORWARDED_TO_ADMIN]:
        success, message = UnifiedReportService.admin_approve(context_id, str(current_user.id), notes)
    else:
        success = False
        message = f"التقرير في حالة {REPORT_STATUS_NAMES_AR.get(context.status, 'غير معروفة')} ولا يمكن اعتماده"
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('unified_reports.preview', context_id=context_id))


@unified_reports_bp.route('/reports/<context_id>/reject', methods=['POST'])
@login_required
@require_report_access
def reject_report(context_id):
    """PM reject a report with reason"""
    reason = request.form.get('reason', '').strip()
    
    if not reason:
        flash('يجب إدخال سبب الرفض', 'error')
        return redirect(url_for('unified_reports.preview', context_id=context_id))
    
    success, message = UnifiedReportService.pm_reject(context_id, str(current_user.id), reason)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('unified_reports.preview', context_id=context_id))


@unified_reports_bp.route('/api/reports/<context_id>/status')
@login_required
def get_report_status(context_id):
    """API endpoint to get report status"""
    context = UnifiedReportService.get_report_context(context_id, str(current_user.id))
    
    if not context:
        return jsonify({'error': 'التقرير غير موجود أو ليس لديك صلاحية للوصول'}), 404
    
    return jsonify({
        'id': str(context.id),
        'status': context.status.value,
        'status_name': REPORT_STATUS_NAMES_AR.get(context.status, 'غير معروف'),
        'report_type': context.report_type.value,
        'report_type_name': REPORT_TYPE_NAMES_AR.get(context.report_type, 'تقرير'),
        'can_export': UnifiedReportService.can_export(context_id, str(current_user.id))[0]
    })
