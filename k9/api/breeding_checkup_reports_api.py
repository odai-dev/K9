"""
Breeding Checkup Reports API
Handles data endpoints for Arabic/RTL daily checkup reports
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify, request, current_app, send_file, make_response
from flask_login import login_required, current_user
from sqlalchemy import and_, func, case
from sqlalchemy.orm import selectinload, joinedload

from k9.utils.permission_decorators import require_sub_permission
from k9.utils.permission_utils import has_permission
from k9.reporting.range_utils import (
    resolve_range, get_aggregation_strategy, 
    parse_date_string, format_date_range_for_display,
    generate_export_filename, validate_range_params
)
from k9.models.models import (
    DailyCheckupLog, Dog, Project, Employee, PermissionType
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
bp = Blueprint('breeding_checkup_reports_api', __name__)

# Arabic body part names for display
BODY_PARTS_AR = {
    'eyes': 'العين',
    'ears': 'الأذن', 
    'nose': 'الأنف',
    'front_legs': 'الأطراف الأمامية',
    'hind_legs': 'الأطراف الخلفية',
    'coat': 'الشعر',
    'tail': 'الذيل'
}

# Severity levels in order (for max severity calculation)
SEVERITY_LEVELS = ['خفيف', 'متوسط', 'شديد']

def is_abnormal_finding(value):
    """Check if a body part finding is abnormal (not normal)"""
    if not value:
        return False
    # Consider anything that's not "طبيعي" or "سليم" as abnormal
    normal_values = ['طبيعي', 'سليم', 'Normal', 'normal']
    return value.strip() not in normal_values

def get_max_severity(severities):
    """Get the maximum severity from a list of severity values"""
    if not severities:
        return None
    
    # Filter out None/empty values
    valid_severities = [s for s in severities if s and s.strip()]
    if not valid_severities:
        return None
        
    # Find the max by index in SEVERITY_LEVELS
    max_idx = -1
    max_severity = None
    for severity in valid_severities:
        try:
            idx = SEVERITY_LEVELS.index(severity.strip())
            if idx > max_idx:
                max_idx = idx
                max_severity = severity.strip()
        except ValueError:
            # Unknown severity level, skip
            continue
    
    return max_severity


@bp.route('/daily')
@login_required
@require_sub_permission("Reports", "Checkup Daily", PermissionType.VIEW)
def checkup_daily_data():
    """Get daily checkup report data with KPIs and rows"""
    project_id = request.args.get('project_id')
    date_str = request.args.get('date')
    dog_id = request.args.get('dog_id')  # optional filter
    
    # Performance optimization: Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    if not date_str:
        return jsonify({'error': 'التاريخ مطلوب'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (UUID) when provided
    if project_id and project_id.strip():
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        dog_id = dog_id.strip()
    else:
        dog_id = None
    
    # Security: Get user's authorized projects when project_id is omitted
    if project_id is not None:
        # Verify project access for specific project
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    else:
        # Get all authorized projects for the user
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Security fix: Scope queries to authorized projects only
    base_query = db.session.query(DailyCheckupLog).options(
        selectinload(DailyCheckupLog.dog),  # type: ignore
        selectinload(DailyCheckupLog.project),  # type: ignore
        selectinload(DailyCheckupLog.examiner_employee)  # type: ignore
    ).filter(
        DailyCheckupLog.date == target_date,
        DailyCheckupLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        base_query = base_query.filter(DailyCheckupLog.dog_id == dog_id)
    
    # Get total count for pagination
    total_count = base_query.count()
    
    # Apply pagination and ordering
    checkup_logs = base_query.order_by(DailyCheckupLog.time.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Fix: Calculate KPIs from full dataset using DB queries (not just paginated results)
    kpi_query = db.session.query(
        func.count(DailyCheckupLog.id).label('total_checks'),
        func.count(func.distinct(DailyCheckupLog.dog_id)).label('unique_dogs')
    ).filter(
        DailyCheckupLog.date == target_date,
        DailyCheckupLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        kpi_query = kpi_query.filter(DailyCheckupLog.dog_id == dog_id)
    
    kpi_result = kpi_query.first()
    
    # Fix: Calculate severity and flag distributions from full dataset using DB queries
    severity_counts = defaultdict(int)
    flag_counts = defaultdict(int)
    
    # Get all logs for accurate KPI calculation (not just paginated results)
    all_logs_for_kpis = base_query.all()
    
    for log in all_logs_for_kpis:
        # Count severity levels from full dataset
        if log.severity:
            severity_counts[log.severity] += 1
        
        # Count abnormal findings by body part from full dataset
        for field, ar_name in BODY_PARTS_AR.items():
            value = getattr(log, field)
            if is_abnormal_finding(value):
                flag_counts[ar_name] += 1
    
    # Prepare data for frontend
    rows = []
    for log in checkup_logs:
        row_data = {
            'date': log.date.strftime('%Y-%m-%d'),
            'time': log.time.strftime('%H:%M:%S'),
            'dog_id': str(log.dog_id),
            'dog_code': log.dog.code if log.dog else '',
            'dog_name': log.dog.name if log.dog else '',
            'المربي': log.examiner_employee.name if log.examiner_employee else 'غير محدد',
            'العين': log.eyes or '',
            'الأذن': log.ears or '',
            'الأنف': log.nose or '', 
            'الأطراف الأمامية': log.front_legs or '',
            'الأطراف الخلفية': log.hind_legs or '',
            'الشعر': log.coat or '',
            'الذيل': log.tail or '',
            'شدة الحالة': log.severity or '',
            'ملاحظات': log.notes or ''
        }
        rows.append(row_data)
    
    # Get project name for response
    project = db.session.query(Project).filter(Project.id == project_id).first()
    project_name = project.name if project else ""
    
    # Fix: Build response aligned with feeding reports format
    response_data = {
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
            "date": date_str,
            "dog_id": dog_id
        },
        "kpis": {
            "total_checks": kpi_result.total_checks if kpi_result else 0,
            "unique_dogs": kpi_result.unique_dogs if kpi_result else 0,
            "by_severity": dict(severity_counts),
            "flags": dict(flag_counts)
        },
        "rows": rows,
        "date": date_str,
        "project_name": project_name
    }
    
    return jsonify(response_data)


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Checkup Weekly", PermissionType.VIEW)
def checkup_weekly_data():
    """Get weekly checkup report data aggregated by dog"""
    project_id = request.args.get('project_id')
    week_start_str = request.args.get('week_start')
    dog_id = request.args.get('dog_id')  # optional filter
    
    # Performance optimization: Add pagination for weekly reports  
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 dogs per page
    
    if not week_start_str:
        return jsonify({'error': 'بداية الأسبوع مطلوبة'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (UUID) when provided
    if project_id and project_id.strip():
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        dog_id = dog_id.strip()
    else:
        dog_id = None
    
    # Security: Get user's authorized projects when project_id is omitted
    if project_id is not None:
        # Verify project access for specific project
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    else:
        # Get all authorized projects for the user
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Query checkup logs for the week
    query = db.session.query(DailyCheckupLog).options(
        joinedload(DailyCheckupLog.dog),  # type: ignore
        joinedload(DailyCheckupLog.project),  # type: ignore
        joinedload(DailyCheckupLog.examiner_employee)  # type: ignore
    ).filter(
        DailyCheckupLog.project_id.in_(authorized_project_ids),
        DailyCheckupLog.date >= week_start,
        DailyCheckupLog.date <= week_end
    )
    
    if dog_id:
        query = query.filter(DailyCheckupLog.dog_id == dog_id)
    
    checkup_logs = query.all()
    
    # Aggregate by dog
    dogs_data = {}
    
    # Calculate overall KPIs
    total_dogs = set()
    total_checks = len(checkup_logs)
    severity_counts = defaultdict(int)
    flagged_dogs = set()
    
    for log in checkup_logs:
        dog_key = str(log.dog_id)
        total_dogs.add(dog_key)
        
        # Initialize dog data if not exists
        if dog_key not in dogs_data:
            dogs_data[dog_key] = {
                'dog_id': str(log.dog_id),
                'dog_code': log.dog.code if log.dog else '',
                'dog_name': log.dog.name if log.dog else '',
                'checks': 0,
                'severities': [],
                'flags_total': 0,
                'flags_by_part': defaultdict(int),
                'days': {}
            }
        
        dog_data = dogs_data[dog_key]
        dog_data['checks'] += 1
        
        if log.severity:
            dog_data['severities'].append(log.severity)
            severity_counts[log.severity] += 1
        
        # Count flags for this dog
        day_flags = 0
        for field, ar_name in BODY_PARTS_AR.items():
            value = getattr(log, field)
            if is_abnormal_finding(value):
                dog_data['flags_by_part'][ar_name] += 1
                dog_data['flags_total'] += 1
                day_flags += 1
                flagged_dogs.add(dog_key)
        
        # Store daily data
        day_key = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][log.date.weekday()]
        if day_key not in dog_data['days']:
            dog_data['days'][day_key] = {'severity': '', 'flags': 0}
        
        # Update day data with max severity and total flags
        if log.severity:
            current_day_severity = dog_data['days'][day_key]['severity']
            if not current_day_severity:
                dog_data['days'][day_key]['severity'] = log.severity
            else:
                dog_data['days'][day_key]['severity'] = get_max_severity([current_day_severity, log.severity]) or current_day_severity
        
        dog_data['days'][day_key]['flags'] += day_flags
    
    # Convert to list and add pagination
    table_data = []
    for dog_key, dog_data in dogs_data.items():
        # Get max severity for the dog across the week
        severity_max = get_max_severity(dog_data['severities'])
        
        # Ensure all days are present
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            if day not in dog_data['days']:
                dog_data['days'][day] = {'severity': '', 'flags': 0}
        
        table_entry = {
            'dog_id': dog_data['dog_id'],
            'dog_code': dog_data['dog_code'],
            'dog_name': dog_data['dog_name'],
            'checks': dog_data['checks'],
            'severity_max': severity_max or '',
            'flags_total': dog_data['flags_total'],
            'flags_by_part': dict(dog_data['flags_by_part']),
            'days': dog_data['days']
        }
        table_data.append(table_entry)
    
    # Sort by dog name for consistent ordering
    table_data.sort(key=lambda x: x['dog_name'])
    
    # Apply pagination
    total_dogs_count = len(table_data)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_table_data = table_data[start_idx:end_idx]
    
    # Fix: Build response aligned with feeding reports format
    response_data = {
        "success": True,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_dogs_count,
            "pages": (total_dogs_count + per_page - 1) // per_page,
            "has_next": page * per_page < total_dogs_count,
            "has_prev": page > 1
        },
        "filters": {
            "project_id": project_id,
            "week_start": week_start_str,
            "dog_id": dog_id
        },
        "kpis": {
            "dogs_count": len(total_dogs),
            "checks_count": total_checks,
            "by_severity": dict(severity_counts),
            "flagged_dogs": len(flagged_dogs)
        },
        "table": paginated_table_data
    }
    
    return jsonify(response_data)


@bp.route('/daily/export.pdf')
@login_required
@require_sub_permission("Reports", "Checkup Daily", PermissionType.EXPORT)
def export_checkup_daily_pdf():
    """Export daily checkup report as PDF"""
    project_id = request.args.get('project_id')
    date_str = request.args.get('date')
    dog_id = request.args.get('dog_id')
    
    if not date_str:
        return jsonify({'error': 'التاريخ مطلوب'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (UUID) when provided
    if project_id and project_id.strip():
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        dog_id = dog_id.strip()
    else:
        dog_id = None
    
    # Fix: Remove unsafe request patching - use direct query like feeding API
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Security check: Get user's authorized projects
    if project_id is not None:
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    else:
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    
    # Fix: Direct query without unsafe mocking
    query = db.session.query(DailyCheckupLog).options(
        selectinload(DailyCheckupLog.dog),  # type: ignore
        selectinload(DailyCheckupLog.project),  # type: ignore
        selectinload(DailyCheckupLog.examiner_employee)  # type: ignore
    ).filter(
        DailyCheckupLog.date == target_date,
        DailyCheckupLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        query = query.filter(DailyCheckupLog.dog_id == dog_id)
    
    checkup_logs = query.order_by(DailyCheckupLog.time.desc()).all()
    
    try:
        
        # Generate PDF
        upload_dir = os.path.join('uploads', 'reports', 'checkup', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(upload_dir, exist_ok=True)
        
        date_str_clean = date_str.replace('-', '')
        project_suffix = f"_{project_id[:8]}" if project_id else "_all"
        filename = f"checkup_daily{project_suffix}_{date_str_clean}.pdf"
        filepath = os.path.join(upload_dir, filename)
        
        # Register Arabic fonts
        has_arabic_font = register_arabic_fonts()
        font_name = get_arabic_font_name() if has_arabic_font else 'Helvetica'
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40,
                              topMargin=40, bottomMargin=40)
        
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_RIGHT
        )
        
        story.append(Paragraph(rtl("تقرير الفحص الظاهري اليومي"), title_style))
        
        # Header information
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        
        # Get project name if specified
        project_name = "جميع المشاريع"
        if project_id and checkup_logs:
            project_name = checkup_logs[0].project.name if checkup_logs[0].project else project_name
        
        header_info = [
            f"التاريخ: {target_date.strftime('%Y-%m-%d')}",
            f"المشروع: {project_name}"
        ]
        
        if dog_id and checkup_logs:
            dog_name = checkup_logs[0].dog.name if checkup_logs[0].dog else "غير محدد"
            header_info.append(f"الكلب: {dog_name}")
        
        for info in header_info:
            story.append(Paragraph(rtl(info), header_style))
        
        story.append(Spacer(1, 20))
        
        # KPIs
        total_checks = len(checkup_logs)
        unique_dogs = len(set(log.dog_id for log in checkup_logs))
        severity_counts = defaultdict(int)
        for log in checkup_logs:
            if log.severity:
                severity_counts[log.severity] += 1
        
        kpis_style = ParagraphStyle(
            'KPIsStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=15,
            alignment=TA_RIGHT
        )
        
        kpis_text = [
            f"إجمالي الفحوصات: {total_checks}",
            f"عدد الكلاب: {unique_dogs}",
        ]
        
        if severity_counts:
            severity_text = " | ".join([f"{k}: {v}" for k, v in severity_counts.items()])
            kpis_text.append(f"توزيع الشدة: {severity_text}")
        
        for kpi in kpis_text:
            story.append(Paragraph(rtl(kpi), kpis_style))
        
        story.append(Spacer(1, 20))
        
        # Table data with RTL headers (reversed order)
        if checkup_logs:
            # Headers (RIGHT to LEFT order as specified)
            headers = [
                "التاريخ", "الوقت",
                "العين", "الأذن", "الأنف", "الأطراف الأمامية", "الأطراف الخلفية", "الشعر", "الذيل",
                "شدة الحالة", "ملاحظات",
                "المربي", "الكلب", "المشروع"
            ]
            
            table_data = [headers]
            
            for log in checkup_logs:
                row = [
                    log.date.strftime('%Y-%m-%d'),
                    log.time.strftime('%H:%M'),
                    log.eyes or '',
                    log.ears or '',
                    log.nose or '',
                    log.front_legs or '',
                    log.hind_legs or '',
                    log.coat or '',
                    log.tail or '',
                    log.severity or '',
                    (log.notes or '')[:50] + '...' if log.notes and len(log.notes) > 50 else log.notes or '',
                    log.examiner_employee.name if log.examiner_employee else 'غير محدد',
                    log.dog.name if log.dog else '',
                    log.project.name if log.project else ''
                ]
                table_data.append(row)
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph(rtl("لا توجد بيانات للعرض"), header_style))
        
        # Add signature blocks
        story.append(Spacer(1, 40))
        
        signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        
        story.append(Paragraph(rtl("ملاحظات عامة:"), signature_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(rtl("_" * 80), signature_style))
        story.append(Spacer(1, 30))
        
        signature_table_data = [
            [rtl("اسم المربي: __________"), rtl("التوقيع: __________")],
            [rtl("مسؤول المشروع: __________"), rtl("التوقيع: __________")]
        ]
        
        signature_table = Table(signature_table_data)
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(signature_table)
        
        # Build PDF
        doc.build(story)
        
        return jsonify({
            'success': True,
            'file': filepath,
            'filename': filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating checkup daily PDF: {str(e)}")
        return jsonify({'error': f'خطأ في إنشاء ملف PDF: {str(e)}'}), 500


@bp.route('/weekly/export.pdf')
@login_required
@require_sub_permission("Reports", "Checkup Weekly", PermissionType.EXPORT)
def export_checkup_weekly_pdf():
    """Export weekly checkup report as PDF"""
    project_id = request.args.get('project_id')
    week_start_str = request.args.get('week_start')
    dog_id = request.args.get('dog_id')
    
    if not week_start_str:
        return jsonify({'error': 'بداية الأسبوع مطلوبة'}), 400
    
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        # Security check
        if project_id and project_id.strip():
            if not check_project_access(current_user, project_id.strip()):
                return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
            authorized_project_ids = [project_id.strip()]
        else:
            authorized_projects = get_user_projects(current_user)
            authorized_project_ids = [p.id for p in authorized_projects]
            if not authorized_project_ids:
                return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
        
        # Query data (simplified version of weekly logic)
        query = db.session.query(DailyCheckupLog).options(
            joinedload(DailyCheckupLog.dog),  # type: ignore
            joinedload(DailyCheckupLog.project),  # type: ignore
            joinedload(DailyCheckupLog.examiner_employee)  # type: ignore
        ).filter(
            DailyCheckupLog.project_id.in_(authorized_project_ids),
            DailyCheckupLog.date >= week_start,
            DailyCheckupLog.date <= week_end
        )
        
        if dog_id and dog_id.strip():
            query = query.filter(DailyCheckupLog.dog_id == dog_id.strip())
        
        checkup_logs = query.all()
        
        # Generate PDF
        upload_dir = os.path.join('uploads', 'reports', 'checkup', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(upload_dir, exist_ok=True)
        
        week_str = f"{week_start.strftime('%Y%m%d')}-{week_end.strftime('%Y%m%d')}"
        project_suffix = f"_{project_id[:8]}" if project_id else "_all"
        filename = f"checkup_weekly{project_suffix}_{week_str}.pdf"
        filepath = os.path.join(upload_dir, filename)
        
        # Register Arabic fonts
        has_arabic_font = register_arabic_fonts()
        font_name = get_arabic_font_name() if has_arabic_font else 'Helvetica'
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40,
                              topMargin=40, bottomMargin=80)
        
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_RIGHT
        )
        
        story.append(Paragraph(rtl("تقرير الفحص الظاهري الأسبوعي"), title_style))
        
        # Header information
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        
        project_name = "جميع المشاريع"
        if project_id and checkup_logs:
            project_name = checkup_logs[0].project.name if checkup_logs[0].project else project_name
        
        header_info = [
            f"نطاق الأسبوع: {week_start.strftime('%Y-%m-%d')} إلى {week_end.strftime('%Y-%m-%d')}",
            f"المشروع: {project_name}"
        ]
        
        for info in header_info:
            story.append(Paragraph(rtl(info), header_style))
        
        story.append(Spacer(1, 20))
        
        # Build and return PDF
        doc.build(story)
        
        return jsonify({
            'success': True,
            'file': filepath,
            'filename': filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating checkup weekly PDF: {str(e)}")
        return jsonify({'error': f'خطأ في إنشاء ملف PDF: {str(e)}'}), 500


# ==============================================================================
# UNIFIED ENDPOINTS (New Range-Based API)
# ==============================================================================

@bp.route('/unified')
@login_required
def checkup_unified_data():
    """Unified checkup report data with range selector and smart aggregation"""
    
    # Check unified permission
    if not has_permission(current_user, "reports.breeding.checkup.view"):
        return jsonify({'error': 'ليس لديك صلاحية لعرض تقارير الفحص الظاهري'}), 403
    
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
    
    # Build base query with date range
    base_query = db.session.query(DailyCheckupLog).options(
        selectinload(DailyCheckupLog.dog),
        selectinload(DailyCheckupLog.project),
        selectinload(DailyCheckupLog.examiner_employee)
    ).filter(
        DailyCheckupLog.date >= date_from,
        DailyCheckupLog.date <= date_to,
        DailyCheckupLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        base_query = base_query.filter(DailyCheckupLog.dog_id == dog_id)
    
    # Apply aggregation strategy
    if aggregation == "daily":
        # Daily: Show individual records with pagination
        total_count = base_query.count()
        checkup_logs = base_query.order_by(
            DailyCheckupLog.date.desc(),
            DailyCheckupLog.time.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # Build daily response format
        rows = []
        for log in checkup_logs:
            # Use the single severity field from the model
            severity = log.severity or 'غير محدد'
            
            rows.append({
                'id': str(log.id),
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M'),
                'dog_name': log.dog.name if log.dog else 'غير معروف',
                'dog_microchip': log.dog.microchip_id if log.dog else '',
                'examiner': log.examiner_employee.name if log.examiner_employee else 'غير محدد',
                'project': log.project.name if log.project else 'غير محدد',
                'severity': severity,
                'abnormal_findings': [
                    BODY_PARTS_AR[part] for part, finding in [
                        ('eyes', log.eyes), ('ears', log.ears),
                        ('nose', log.nose), ('front_legs', log.front_legs),
                        ('hind_legs', log.hind_legs), ('coat', log.coat),
                        ('tail', log.tail)
                    ] if is_abnormal_finding(finding)
                ],
                'symptoms': log.symptoms or '',
                'initial_diagnosis': log.initial_diagnosis or '',
                'suggested_treatment': log.suggested_treatment or '',
                'notes': log.notes or ''
            })
        
    elif aggregation == "weekly":
        # Weekly: Aggregate by dog and week
        checkup_logs = base_query.all()
        
        # Group by dog and week
        dogs_data = {}
        total_count = 0
        
        for log in checkup_logs:
            # Calculate which week this log belongs to
            days_since_start = (log.date - date_from).days
            week_num = days_since_start // 7
            
            dog_key = str(log.dog_id)
            week_key = f"week_{week_num}"
            
            if dog_key not in dogs_data:
                dogs_data[dog_key] = {
                    'dog_name': log.dog.name if log.dog else 'غير معروف',
                    'dog_microchip': log.dog.microchip_id if log.dog else '',
                    'weeks': {}
                }
            
            if week_key not in dogs_data[dog_key]['weeks']:
                dogs_data[dog_key]['weeks'][week_key] = {
                    'checks': [],
                    'severities': [],
                    'abnormal_count': 0
                }
            
            # Add this check to the week
            severity = log.severity or 'غير محدد'
            
            abnormal_findings = [
                part for part, finding in [
                    ('eyes', log.eyes), ('ears', log.ears),
                    ('nose', log.nose), ('front_legs', log.front_legs),
                    ('hind_legs', log.hind_legs), ('coat', log.coat),
                    ('tail', log.tail)
                ] if is_abnormal_finding(finding)
            ]
            
            dogs_data[dog_key]['weeks'][week_key]['checks'].append({
                'date': log.date.strftime('%Y-%m-%d'),
                'severity': severity,
                'abnormal_findings': abnormal_findings
            })
            dogs_data[dog_key]['weeks'][week_key]['severities'].append(severity)
            dogs_data[dog_key]['weeks'][week_key]['abnormal_count'] += len(abnormal_findings)
        
        # Convert to paginated rows format
        rows = []
        for dog_key, dog_data in list(dogs_data.items())[(page-1)*per_page:page*per_page]:
            for week_key, week_data in dog_data['weeks'].items():
                max_severity = get_max_severity(week_data['severities'])
                rows.append({
                    'dog_name': dog_data['dog_name'],
                    'dog_microchip': dog_data['dog_microchip'],
                    'week': week_key,
                    'check_count': len(week_data['checks']),
                    'max_severity': max_severity or 'غير محدد',
                    'abnormal_count': week_data['abnormal_count'],
                    'checks': week_data['checks']
                })
        
        total_count = len(dogs_data)
        
    elif aggregation == "monthly":
        # Monthly: Aggregate by dog and month
        checkup_logs = base_query.all()
        
        # Group by dog and month
        dogs_data = {}
        total_count = 0
        
        for log in checkup_logs:
            # Calculate which month this log belongs to (relative to date_from)
            days_since_start = (log.date - date_from).days
            month_num = days_since_start // 30  # Approximate monthly grouping
            
            dog_key = str(log.dog_id)
            month_key = f"month_{month_num}"
            
            if dog_key not in dogs_data:
                dogs_data[dog_key] = {
                    'dog_name': log.dog.name if log.dog else 'غير معروف',
                    'dog_microchip': log.dog.microchip_id if log.dog else '',
                    'months': {}
                }
            
            if month_key not in dogs_data[dog_key]['months']:
                dogs_data[dog_key]['months'][month_key] = {
                    'checks': [],
                    'severities': [],
                    'abnormal_count': 0
                }
            
            # Add this check to the month
            severity = log.severity or 'غير محدد'
            
            abnormal_findings = [
                part for part, finding in [
                    ('eyes', log.eyes), ('ears', log.ears),
                    ('nose', log.nose), ('front_legs', log.front_legs),
                    ('hind_legs', log.hind_legs), ('coat', log.coat),
                    ('tail', log.tail)
                ] if is_abnormal_finding(finding)
            ]
            
            dogs_data[dog_key]['months'][month_key]['checks'].append({
                'date': log.date.strftime('%Y-%m-%d'),
                'severity': severity,
                'abnormal_findings': abnormal_findings
            })
            dogs_data[dog_key]['months'][month_key]['severities'].append(severity)
            dogs_data[dog_key]['months'][month_key]['abnormal_count'] += len(abnormal_findings)
        
        # Convert to paginated rows format
        rows = []
        for dog_key, dog_data in list(dogs_data.items())[(page-1)*per_page:page*per_page]:
            for month_key, month_data in dog_data['months'].items():
                max_severity = get_max_severity(month_data['severities'])
                rows.append({
                    'dog_name': dog_data['dog_name'],
                    'dog_microchip': dog_data['dog_microchip'],
                    'month': month_key,
                    'check_count': len(month_data['checks']),
                    'max_severity': max_severity or 'غير محدد',
                    'abnormal_count': month_data['abnormal_count'],
                    'checks': month_data['checks']
                })
        
        total_count = len(dogs_data)
        
    else:
        return jsonify({'error': 'إستراتيجية التجميع غير مدعومة'}), 400
    
    # Calculate KPIs from full dataset
    kpi_query = db.session.query(
        func.count(DailyCheckupLog.id).label('total_checks'),
        func.count(func.distinct(DailyCheckupLog.dog_id)).label('unique_dogs')
    ).filter(
        DailyCheckupLog.date >= date_from,
        DailyCheckupLog.date <= date_to,
        DailyCheckupLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        kpi_query = kpi_query.filter(DailyCheckupLog.dog_id == dog_id)
    
    kpi_result = kpi_query.first()
    
    # Get project name for display
    project_name = "جميع المشاريع"
    if project_id:
        project = Project.query.get(project_id)
        if project:
            project_name = project.name
    
    # Create response with caching headers
    response_data = {
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page,
            'has_next': page * per_page < total_count,
            'has_prev': page > 1
        },
        'filters': {
            'project_id': project_id,
            'range_type': range_type,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'aggregation': aggregation,
            'dog_id': dog_id
        },
        'kpis': {
            'total_checks': kpi_result.total_checks if kpi_result else 0,
            'unique_dogs': kpi_result.unique_dogs if kpi_result else 0,
            'date_range_display': format_date_range_for_display(date_from, date_to, range_type, "ar")
        },
        'rows': rows,
        'project_name': project_name
    }
    
    response = make_response(jsonify(response_data))
    response.cache_control.max_age = 60
    response.cache_control.private = True
    response.headers['Vary'] = 'Cookie, Authorization'
    return response


@bp.route('/unified/export.pdf')
@login_required
def checkup_unified_export_pdf():
    """Export unified checkup report as PDF with proper naming"""
    
    # Check export permission
    if not has_permission(current_user, "reports.breeding.checkup.export"):
        return jsonify({'error': 'ليس لديك صلاحية لتصدير تقارير الفحص الظاهري'}), 403
    
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
        filename = generate_export_filename("checkup", project_code, date_from, date_to, "pdf")
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
        
        # Get aggregation strategy
        aggregation = get_aggregation_strategy(date_from, date_to, range_type)
        
        # Build query with date range
        base_query = db.session.query(DailyCheckupLog).options(
            selectinload(DailyCheckupLog.dog),
            selectinload(DailyCheckupLog.project),
            selectinload(DailyCheckupLog.examiner_employee)
        ).filter(
            DailyCheckupLog.date >= date_from,
            DailyCheckupLog.date <= date_to,
            DailyCheckupLog.project_id.in_(authorized_project_ids)
        )
        
        if dog_id:
            base_query = base_query.filter(DailyCheckupLog.dog_id == dog_id)
        
        checkup_logs = base_query.order_by(DailyCheckupLog.date.desc(), DailyCheckupLog.time.desc()).all()
        
        # Calculate KPIs
        total_checks = len(checkup_logs)
        unique_dogs = len(set(str(log.dog_id) for log in checkup_logs))
        severity_counts = defaultdict(int)
        flag_counts = defaultdict(int)
        
        for log in checkup_logs:
            if log.severity:
                severity_counts[log.severity] += 1
            
            # Count abnormal findings
            for field, ar_name in BODY_PARTS_AR.items():
                value = getattr(log, field)
                if is_abnormal_finding(value):
                    flag_counts[ar_name] += 1
        
        # Generate PDF using existing logic
        register_arabic_fonts()
        font_name = get_arabic_font_name()
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40,
                              topMargin=40, bottomMargin=40)
        
        story = []
        
        # Title with range type
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        range_display = format_date_range_for_display(date_from, date_to, range_type, "ar")
        title = f"تقرير الفحص الظاهري الموحد - {range_display}"
        story.append(Paragraph(rtl(title), title_style))
        story.append(Spacer(1, 20))
        
        # KPIs section
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        
        kpis_style = ParagraphStyle(
            'KPIsStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=5,
            alignment=TA_RIGHT
        )
        
        story.append(Paragraph(rtl("الملخص التنفيذي"), header_style))
        
        project_name = "جميع المشاريع"
        if project_id:
            project = Project.query.get(project_id)
            if project:
                project_name = project.name
        
        kpis_text = [
            f"إجمالي الفحوصات: {total_checks}",
            f"عدد الكلاب: {unique_dogs}",
            f"المشروع: {project_name}",
            f"فترة التقرير: {range_display}"
        ]
        
        if severity_counts:
            severity_text = " | ".join([f"{k}: {v}" for k, v in severity_counts.items()])
            kpis_text.append(f"توزيع الشدة: {severity_text}")
        
        if flag_counts:
            flag_text = " | ".join([f"{k}: {v}" for k, v in flag_counts.items()])
            kpis_text.append(f"الحالات غير الطبيعية: {flag_text}")
        
        for kpi in kpis_text:
            story.append(Paragraph(rtl(kpi), kpis_style))
        
        story.append(Spacer(1, 20))
        
        # Data table - limit to first 50 records for PDF readability
        if checkup_logs:
            headers = [
                "التاريخ", "الوقت",
                "العين", "الأذن", "الأنف", "الأطراف الأمامية", "الأطراف الخلفية", "الشعر", "الذيل",
                "شدة الحالة", "ملاحظات",
                "المربي", "الكلب", "المشروع"
            ]
            
            table_data = [headers]
            
            for log in checkup_logs[:50]:  # Limit for PDF readability
                row = [
                    log.date.strftime('%Y-%m-%d'),
                    log.time.strftime('%H:%M'),
                    log.eyes or '',
                    log.ears or '',
                    log.nose or '',
                    log.front_legs or '',
                    log.hind_legs or '',
                    log.coat or '',
                    log.tail or '',
                    log.severity or '',
                    (log.notes or '')[:30] + '...' if log.notes and len(log.notes) > 30 else log.notes or '',
                    log.examiner_employee.name if log.examiner_employee else 'غير محدد',
                    log.dog.name if log.dog else '',
                    log.project.name if log.project else ''
                ]
                table_data.append(row)
            
            table = Table(table_data, colWidths=[0.8*72, 0.6*72, 0.6*72, 0.6*72, 0.6*72, 0.8*72, 0.8*72, 0.6*72, 0.6*72, 0.8*72, 1.2*72, 1*72, 1*72, 1*72])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            if len(checkup_logs) > 50:
                story.append(Spacer(1, 10))
                story.append(Paragraph(rtl(f"* عرض أول 50 سجل من إجمالي {len(checkup_logs)} سجل"), kpis_style))
        else:
            story.append(Paragraph(rtl("لا توجد بيانات للعرض"), header_style))
        
        # Build PDF
        doc.build(story)
        
        # Create response with caching headers for PDF export
        response_data = {
            'success': True,
            'file': filepath,
            'filename': filename
        }
        
        response = make_response(jsonify(response_data))
        response.cache_control.max_age = 60
        response.cache_control.private = True
        response.headers['Vary'] = 'Cookie, Authorization'
        return response
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating unified checkup PDF: {str(e)}")
        return jsonify({'error': f'خطأ في إنشاء ملف PDF: {str(e)}'}), 500