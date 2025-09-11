"""
Breeding Checkup Reports API
Handles data endpoints for Arabic/RTL daily checkup reports
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import and_, func, case
from sqlalchemy.orm import selectinload, joinedload

from k9.utils.permission_decorators import require_sub_permission
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