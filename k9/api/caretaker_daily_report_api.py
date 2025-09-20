"""
Caretaker Daily Report API
Handles data endpoints for Arabic/RTL caretaker daily reports
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify, request, current_app, send_file, make_response
from flask_login import login_required, current_user
from sqlalchemy import and_, func, case
from sqlalchemy.orm import selectinload, joinedload

from k9.utils.permission_utils import has_permission
from k9.reporting.range_utils import (
    resolve_range, get_aggregation_strategy, 
    parse_date_string, format_date_range_for_display,
    generate_export_filename, validate_range_params
)
from k9.models.models import (
    CaretakerDailyLog, Dog, Project, Employee
)
from k9.utils.utils import get_user_projects, check_project_access
from k9.utils.utils_pdf_rtl import register_arabic_fonts, rtl, get_arabic_font_name
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from app import db

# Create blueprint
bp = Blueprint('caretaker_daily_reports_api', __name__)


def get_cleaning_status_display(status):
    """Convert boolean cleaning status to Arabic display format"""
    return "نعم" if status else "لا"


# ==============================================================================
# UNIFIED ENDPOINTS (Range-Based API)
# ==============================================================================

@bp.route('/unified')
@login_required
def caretaker_daily_unified_data():
    """Unified caretaker daily report data with range selector and smart aggregation"""
    
    # Check unified permission
    if not has_permission(current_user, "reports.breeding.caretaker_daily.view"):
        return jsonify({'error': 'ليس لديك صلاحية لعرض تقارير الرعاية اليومية'}), 403
    
    # Get parameters
    range_type = request.args.get('range_type', 'daily')
    project_id = request.args.get('project_id', '').strip() or None
    dog_id = request.args.get('dog_id', '').strip() or None
    
    # Input validation: Handle dog_id (UUID) when provided
    if dog_id:
        try:
            # Validate UUID format - dog_id should be a valid UUID string
            import uuid
            uuid.UUID(dog_id)  # This will raise ValueError if invalid UUID format
        except (ValueError, TypeError):
            return jsonify({'error': 'معرف الكلب يجب أن يكون UUID صحيح'}), 400
    else:
        dog_id = None
    
    # Performance optimization: Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    # Collect range parameters
    range_params = {
        'date': request.args.get('date'),
        'week_start': request.args.get('week_start'), 
        'year_month': request.args.get('year_month'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }
    
    try:
        # Validate parameters
        validation_errors = validate_range_params(range_type, range_params)
        if validation_errors:
            return jsonify({'error': 'معاملات غير صالحة', 'details': validation_errors}), 400
        
        # Resolve date range and aggregation strategy
        date_from, date_to, granularity = resolve_range(range_type, range_params)
        aggregation = get_aggregation_strategy(date_from, date_to, range_type)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Security: Get user's authorized projects
    if project_id is not None:
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    else:
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    
    # Build base query
    base_query = db.session.query(CaretakerDailyLog).options(
        selectinload(CaretakerDailyLog.dog),  # type: ignore
        selectinload(CaretakerDailyLog.project),  # type: ignore
        selectinload(CaretakerDailyLog.caretaker_employee),  # type: ignore
        selectinload(CaretakerDailyLog.created_by_user)  # type: ignore
    ).filter(
        CaretakerDailyLog.date >= date_from,
        CaretakerDailyLog.date <= date_to,
        CaretakerDailyLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        base_query = base_query.filter(CaretakerDailyLog.dog_id == dog_id)
    
    # Get total count for pagination
    total_count = base_query.count()
    
    # Apply pagination and ordering
    caretaker_logs = base_query.order_by(
        CaretakerDailyLog.date.desc(),
        CaretakerDailyLog.created_at.desc()
    ).offset((page - 1) * per_page).limit(per_page).all()
    
    # Calculate KPIs
    kpi_query = base_query
    all_logs = kpi_query.all()
    
    # Basic KPIs
    total_entries = len(all_logs)
    unique_dogs = len(set(log.dog_id for log in all_logs))
    unique_dates = len(set(log.date for log in all_logs))
    
    # Cleaning status KPIs
    house_clean_count = sum(1 for log in all_logs if log.house_clean)
    house_vacuum_count = sum(1 for log in all_logs if log.house_vacuum)
    house_tap_clean_count = sum(1 for log in all_logs if log.house_tap_clean)
    house_drain_clean_count = sum(1 for log in all_logs if log.house_drain_clean)
    
    dog_clean_count = sum(1 for log in all_logs if log.dog_clean)
    dog_washed_count = sum(1 for log in all_logs if log.dog_washed)
    dog_brushed_count = sum(1 for log in all_logs if log.dog_brushed)
    bowls_bucket_clean_count = sum(1 for log in all_logs if log.bowls_bucket_clean)
    
    # Calculate percentages (avoid division by zero)
    house_clean_pct = round((house_clean_count / total_entries * 100), 1) if total_entries > 0 else 0
    dog_clean_pct = round((dog_clean_count / total_entries * 100), 1) if total_entries > 0 else 0
    
    # Full house cleaning (all house tasks completed)
    full_house_clean = sum(1 for log in all_logs if all([
        log.house_clean, log.house_vacuum, log.house_tap_clean, log.house_drain_clean
    ]))
    full_house_clean_pct = round((full_house_clean / total_entries * 100), 1) if total_entries > 0 else 0
    
    # Full dog grooming (all dog tasks completed)
    full_dog_grooming = sum(1 for log in all_logs if all([
        log.dog_clean, log.dog_washed, log.dog_brushed
    ]))
    full_dog_grooming_pct = round((full_dog_grooming / total_entries * 100), 1) if total_entries > 0 else 0
    
    # Build rows for display
    rows = []
    for log in caretaker_logs:
        rows.append({
            "id": str(log.id),
            "التاريخ": log.date.strftime('%Y-%m-%d'),
            "اسم_الكلب": log.dog.name if log.dog else "",
            "رمز_الكلب": log.dog.code if log.dog else "",
            "رقم_البيت": log.kennel_code or "",
            "القائم_بالرعاية": log.caretaker_employee.name if log.caretaker_employee else "",
            "تنظيف_البيت": get_cleaning_status_display(log.house_clean),
            "شفط_البيت": get_cleaning_status_display(log.house_vacuum),
            "تنظيف_الصنبور": get_cleaning_status_display(log.house_tap_clean),
            "تنظيف_البالوعة": get_cleaning_status_display(log.house_drain_clean),
            "تنظيف_الكلب": get_cleaning_status_display(log.dog_clean),
            "استحمام_الكلب": get_cleaning_status_display(log.dog_washed),
            "تمشيط_الكلب": get_cleaning_status_display(log.dog_brushed),
            "تنظيف_الأواني": get_cleaning_status_display(log.bowls_bucket_clean),
            "ملاحظات": log.notes or "",
            "المسجل_بواسطة": log.created_by_user.username if log.created_by_user else "",
            "وقت_التسجيل": log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else ""
        })
    
    # Get project name for display
    project_name = "جميع المشاريع"
    if project_id:
        project = Project.query.get(project_id)
        if project:
            project_name = project.name
    
    return jsonify({
        "success": True,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "pages": (total_count + per_page - 1) // per_page,
            "has_next": page * per_page < total_count,
            "has_prev": page > 1
        },
        "filters": {
            "project_id": project_id,
            "range_type": range_type,
            "date_from": date_from.strftime('%Y-%m-%d'),
            "date_to": date_to.strftime('%Y-%m-%d'),
            "dog_id": dog_id
        },
        "kpis": {
            "total_entries": total_entries,
            "unique_dogs": unique_dogs,
            "unique_dates": unique_dates,
            "house_tasks": {
                "house_clean": house_clean_count,
                "house_vacuum": house_vacuum_count,
                "house_tap_clean": house_tap_clean_count,
                "house_drain_clean": house_drain_clean_count,
                "full_house_clean": full_house_clean,
                "house_clean_pct": house_clean_pct,
                "full_house_clean_pct": full_house_clean_pct
            },
            "dog_tasks": {
                "dog_clean": dog_clean_count,
                "dog_washed": dog_washed_count,
                "dog_brushed": dog_brushed_count,
                "bowls_bucket_clean": bowls_bucket_clean_count,
                "full_dog_grooming": full_dog_grooming,
                "dog_clean_pct": dog_clean_pct,
                "full_dog_grooming_pct": full_dog_grooming_pct
            }
        },
        "rows": rows,
        "range_display": format_date_range_for_display(date_from, date_to, range_type),
        "project_name": project_name
    })


@bp.route('/unified/export.pdf')
@login_required
def caretaker_daily_unified_export_pdf():
    """Export unified caretaker daily report as PDF with proper naming"""
    
    # Check export permission
    if not has_permission(current_user, "reports.breeding.caretaker_daily.export"):
        return jsonify({'error': 'ليس لديك صلاحية لتصدير تقارير الرعاية اليومية'}), 403
    
    # Get parameters (same as data endpoint)
    range_type = request.args.get('range_type', 'daily')
    project_id = request.args.get('project_id', '').strip() or None
    dog_id = request.args.get('dog_id', '').strip() or None
    
    range_params = {
        'date': request.args.get('date'),
        'week_start': request.args.get('week_start'),
        'year_month': request.args.get('year_month'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }
    
    try:
        # Validate parameters
        validation_errors = validate_range_params(range_type, range_params)
        if validation_errors:
            return jsonify({'error': 'معاملات غير صالحة', 'details': validation_errors}), 400
        
        # Resolve date range
        date_from, date_to, granularity = resolve_range(range_type, range_params)
        
        # Get project code for filename
        project_code = "all"
        if project_id:
            if not check_project_access(current_user, project_id):
                return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
            project = Project.query.get(project_id)
            if project and project.code:
                project_code = project.code
        
        # Generate filename using unified format
        filename = generate_export_filename("caretaker_daily", project_code, date_from, date_to, "pdf")
        filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Get unified data using same logic as data endpoint
        import uuid
        
        # Validate dog_id if provided
        if dog_id:
            try:
                uuid.UUID(dog_id)  # Validate UUID format
            except (ValueError, TypeError):
                return jsonify({'error': 'معرف الكلب يجب أن يكون UUID صحيح'}), 400
        else:
            dog_id = None
        
        # Get user's authorized projects
        if project_id is not None:
            if not check_project_access(current_user, project_id):
                return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
            authorized_project_ids = [project_id]
        else:
            authorized_projects = get_user_projects(current_user)
            authorized_project_ids = [p.id for p in authorized_projects]
            if not authorized_project_ids:
                return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
        
        # Get data for PDF
        query = db.session.query(CaretakerDailyLog).options(
            joinedload(CaretakerDailyLog.dog),  # type: ignore
            joinedload(CaretakerDailyLog.project),  # type: ignore
            joinedload(CaretakerDailyLog.caretaker_employee)  # type: ignore
        ).filter(
            CaretakerDailyLog.date >= date_from,
            CaretakerDailyLog.date <= date_to,
            CaretakerDailyLog.project_id.in_(authorized_project_ids)
        )
        
        if dog_id:
            query = query.filter(CaretakerDailyLog.dog_id == dog_id)
        
        caretaker_logs = query.order_by(
            CaretakerDailyLog.date.desc(),
            CaretakerDailyLog.created_at.desc()
        ).all()
        
        # Calculate data for PDF - simplified version
        total_entries = len(caretaker_logs)
        house_clean_count = sum(1 for log in caretaker_logs if log.house_clean)
        dog_clean_count = sum(1 for log in caretaker_logs if log.dog_clean)
        
        rows = []
        for log in caretaker_logs:
            rows.append({
                "التاريخ": log.date.strftime('%Y-%m-%d'),
                "اسم_الكلب": log.dog.name if log.dog else "",
                "تنظيف_البيت": get_cleaning_status_display(log.house_clean),
                "تنظيف_الكلب": get_cleaning_status_display(log.dog_clean),
                "القائم_بالرعاية": log.caretaker_employee.name if log.caretaker_employee else ""
            })
        
        data = {
            "kpis": {
                "total_entries": total_entries,
                "house_clean_count": house_clean_count,
                "dog_clean_count": dog_clean_count
            },
            "rows": rows
        }
        
        # Generate RTL PDF using available utilities
        _generate_caretaker_daily_pdf(
            title="تقرير الرعاية اليومية",
            data=data,
            output_path=filepath,
            date_range=format_date_range_for_display(date_from, date_to, range_type)
        )
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')
    
    except Exception as e:
        current_app.logger.error(f"Error exporting caretaker daily PDF: {str(e)}")
        return jsonify({'error': 'حدث خطأ في تصدير التقرير'}), 500


def _generate_caretaker_daily_pdf(title, data, output_path, date_range):
    """Generate RTL PDF for caretaker daily report"""
    from k9.utils.report_header import create_pdf_report_header
    
    register_arabic_fonts()
    
    # Create document
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=20, leftMargin=20)
    story = []
    
    # Get styles for section headers
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('RTLHeader', 
                                 parent=styles['Normal'],
                                 fontName=get_arabic_font_name(),
                                 fontSize=12,
                                 alignment=TA_RIGHT,
                                 spaceAfter=10)
    
    # Add standardized header
    header_elements = create_pdf_report_header(
        report_title_ar=title,
        additional_info=f"الفترة: {date_range}"
    )
    story.extend(header_elements)
    
    # KPIs summary
    kpis = data.get('kpis', {})
    summary_data = [
        [rtl('إجمالي الإدخالات'), str(kpis.get('total_entries', 0))],
        [rtl('تنظيف البيت'), str(kpis.get('house_clean_count', 0))],
        [rtl('تنظيف الكلب'), str(kpis.get('dog_clean_count', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), get_arabic_font_name()),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Data table
    if data.get('rows'):
        # Table headers
        headers = [rtl('التاريخ'), rtl('اسم الكلب'), rtl('تنظيف البيت'), 
                  rtl('تنظيف الكلب'), rtl('القائم بالرعاية')]
        
        # Prepare table data
        table_data = [headers]
        for row in data['rows']:
            table_data.append([
                row.get('التاريخ', ''),
                rtl(row.get('اسم_الكلب', '')),
                rtl(row.get('تنظيف_البيت', '')),
                rtl(row.get('تنظيف_الكلب', '')),
                rtl(row.get('القائم_بالرعاية', ''))
            ])
        
        # Create table
        data_table = Table(table_data, colWidths=[80, 100, 80, 80, 100])
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), get_arabic_font_name()),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(data_table)
    
    # Build PDF
    doc.build(story)