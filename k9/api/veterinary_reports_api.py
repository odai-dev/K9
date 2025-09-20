"""
Veterinary Reports API - unified veterinary reports with range selector
Handles data endpoints and PDF exports for Arabic/RTL veterinary reports
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify, request, current_app, send_file, make_response
from flask_login import login_required, current_user
from sqlalchemy import and_, func, case, or_
from sqlalchemy.orm import selectinload, joinedload

from k9.utils.permission_utils import has_permission
from k9.reporting.range_utils import (
    resolve_range, get_aggregation_strategy, 
    parse_date_string, format_date_range_for_display,
    generate_export_filename, validate_range_params
)
from k9.models.models import (
    VeterinaryVisit, Dog, Project, Employee, VisitType
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
bp = Blueprint('veterinary_reports_api', __name__)

# Visit type display mapping
VISIT_TYPE_LABELS = {
    VisitType.ROUTINE: "روتيني",
    VisitType.EMERGENCY: "طارئ", 
    VisitType.VACCINATION: "تطعيم"
}


def get_visit_type_display(visit_type):
    """Convert VisitType enum to Arabic display format"""
    return VISIT_TYPE_LABELS.get(visit_type, "غير محدد")


def format_medications_display(medications):
    """Format medications list for display"""
    if not medications:
        return ""
    
    if isinstance(medications, list):
        med_strs = []
        for med in medications:
            if isinstance(med, dict):
                name = med.get('name', '')
                dose = med.get('dose', '')
                if name and dose:
                    med_strs.append(f"{name} ({dose})")
                elif name:
                    med_strs.append(name)
        return ", ".join(med_strs)
    
    return str(medications)


def get_project_scope_filter(user, project_id):
    """Get project scope filter for PROJECT_MANAGER users"""
    if user.role.value == "GENERAL_ADMIN":
        if project_id:
            return VeterinaryVisit.project_id == project_id
        else:
            return None  # No filter - see all
    
    # PROJECT_MANAGER scope
    if project_id:
        # Verify PM has access to this project
        if not check_project_access(user, project_id):
            raise ValueError("ليس لديك صلاحية للوصول لهذا المشروع")
        return VeterinaryVisit.project_id == project_id
    else:
        # Show visits for PM's projects + off-project visits
        authorized_projects = get_user_projects(user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if authorized_project_ids:
            return or_(
                VeterinaryVisit.project_id.in_(authorized_project_ids),
                VeterinaryVisit.project_id.is_(None)
            )
        else:
            # Only off-project visits
            return VeterinaryVisit.project_id.is_(None)


@bp.route('/')
@login_required
def veterinary_data():
    """Get unified veterinary report data with range selector"""
    
    # Check permission
    if not has_permission(current_user, "reports.veterinary.view"):
        return jsonify({'error': 'ليس لديك صلاحية لعرض التقارير البيطرية'}), 403
    
    # Get and validate parameters
    range_type = request.args.get('range_type', 'daily')
    project_id = request.args.get('project_id', '').strip() or None
    dog_id = request.args.get('dog_id', '').strip() or None
    show_kpis = request.args.get('show_kpis', '1') == '1'
    
    # Validate range parameters
    errors = validate_range_params(range_type, request.args.to_dict())
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Resolve date range
        date_from, date_to, granularity = resolve_range(range_type, request.args.to_dict())
        
        # Build base query with optimized joins
        query = VeterinaryVisit.query.options(
            selectinload(VeterinaryVisit.dog),
            selectinload(VeterinaryVisit.vet),
            selectinload(VeterinaryVisit.project)
        ).filter(
            and_(
                VeterinaryVisit.visit_date >= datetime.combine(date_from, datetime.min.time()),
                VeterinaryVisit.visit_date <= datetime.combine(date_to, datetime.max.time())
            )
        )
        
        # Apply project scope filter
        try:
            project_filter = get_project_scope_filter(current_user, project_id)
            if project_filter is not None:
                query = query.filter(project_filter)
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
        
        # Apply dog filter if specified
        if dog_id:
            query = query.filter(VeterinaryVisit.dog_id == dog_id)
        
        # Execute query
        visits = query.order_by(VeterinaryVisit.visit_date.desc()).all()
        
        # Calculate KPIs if requested
        kpis = None
        if show_kpis:
            total_visits = len(visits)
            by_visit_type = defaultdict(int)
            total_medications = 0
            total_cost = 0
            total_dogs = len(set(visit.dog_id for visit in visits))
            total_vets = len(set(visit.vet_id for visit in visits))
            
            for visit in visits:
                visit_type_label = get_visit_type_display(visit.visit_type)
                by_visit_type[visit_type_label] += 1
                
                if visit.medications:
                    total_medications += len(visit.medications)
                
                if visit.cost:
                    total_cost += visit.cost
            
            kpis = {
                'total_visits': total_visits,
                'total_dogs': total_dogs,
                'total_vets': total_vets,
                'by_visit_type': dict(by_visit_type),
                'total_medications': total_medications,
                'total_cost': round(total_cost, 2)
            }
        
        # Build response based on granularity
        response_data = {
            'filters': {
                'project_id': project_id,
                'dog_id': dog_id,
                'range_type': range_type,
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'show_kpis': show_kpis
            },
            'granularity': granularity
        }
        
        if show_kpis:
            response_data['kpis'] = kpis
        
        if granularity == "day":
            # Daily view: return detailed rows
            rows = []
            for visit in visits:
                project_name = "(خارج مشروع)" if not visit.project else visit.project.name
                
                rows.append({
                    'date': visit.visit_date.strftime('%Y-%m-%d'),
                    'time': visit.visit_date.strftime('%H:%M:%S'),
                    'dog_id': visit.dog_id,
                    'dog_code': visit.dog.code if visit.dog else '',
                    'dog_name': visit.dog.name if visit.dog else '',
                    'vet_id': visit.vet_id,
                    'vet_name': visit.vet.name if visit.vet else '',
                    'visit_type': get_visit_type_display(visit.visit_type),
                    'diagnosis': visit.diagnosis or '',
                    'treatment': visit.treatment or '',
                    'medications': visit.medications or [],
                    'cost': visit.cost,
                    'notes': visit.notes or '',
                    'project_id': visit.project_id,
                    'project_name': project_name
                })
            
            response_data['rows'] = rows
        else:
            # Aggregate view: return per-dog aggregates
            dog_aggregates = {}
            
            for visit in visits:
                dog_key = visit.dog_id
                if dog_key not in dog_aggregates:
                    dog_aggregates[dog_key] = {
                        'dog_id': visit.dog_id,
                        'dog_code': visit.dog.code if visit.dog else '',
                        'dog_name': visit.dog.name if visit.dog else '',
                        'visits': 0,
                        'by_visit_type': {},
                        'medications_count': 0,
                        'cost_sum': 0
                    }
                
                agg = dog_aggregates[dog_key]
                agg['visits'] += 1
                
                visit_type_label = get_visit_type_display(visit.visit_type)
                if visit_type_label not in agg['by_visit_type']:
                    agg['by_visit_type'][visit_type_label] = 0
                agg['by_visit_type'][visit_type_label] += 1
                
                if visit.medications:
                    agg['medications_count'] += len(visit.medications)
                
                if visit.cost:
                    agg['cost_sum'] += visit.cost
                
                # VeterinaryVisit doesn't track duration
            
            # Convert to table format
            table = []
            for dog_id, agg in dog_aggregates.items():
                table.append({
                    'dog_id': agg['dog_id'],
                    'dog_code': agg['dog_code'],
                    'dog_name': agg['dog_name'],
                    'visits': agg['visits'],
                    'by_visit_type': dict(agg['by_visit_type']),
                    'medications_count': agg['medications_count'],
                    'cost_sum': round(agg['cost_sum'], 2)
                })
            
            response_data['table'] = table
        
        return jsonify(response_data)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in veterinary_data: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500


@bp.route('/export.pdf')
@login_required
def export_pdf():
    """Export veterinary report as Arabic RTL PDF"""
    
    # Check permission
    if not has_permission(current_user, "reports.veterinary.export"):
        return jsonify({'error': 'ليس لديك صلاحية لتصدير التقارير البيطرية'}), 403
    
    # Get the same data as the main endpoint
    try:
        # Reuse the same logic from veterinary_data but get raw data
        range_type = request.args.get('range_type', 'daily')
        project_id = request.args.get('project_id', '').strip() or None
        dog_id = request.args.get('dog_id', '').strip() or None
        show_kpis = request.args.get('show_kpis', '1') == '1'
        
        # Get data using the same logic
        errors = validate_range_params(range_type, request.args.to_dict())
        if errors:
            return jsonify({'errors': errors}), 400
        
        date_from, date_to, granularity = resolve_range(range_type, request.args.to_dict())
        
        # Build query (simplified version)
        query = VeterinaryVisit.query.options(
            selectinload(VeterinaryVisit.dog),
            selectinload(VeterinaryVisit.vet),
            selectinload(VeterinaryVisit.project)
        ).filter(
            and_(
                VeterinaryVisit.visit_date >= datetime.combine(date_from, datetime.min.time()),
                VeterinaryVisit.visit_date <= datetime.combine(date_to, datetime.max.time())
            )
        )
        
        # Apply filters as needed
        project_filter = get_project_scope_filter(current_user, project_id)
        if project_filter is not None:
            query = query.filter(project_filter)
        
        if dog_id:
            query = query.filter(VeterinaryVisit.dog_id == dog_id)
        
        visits = query.order_by(VeterinaryVisit.visit_date.desc()).all()
        
        # Build simplified data structure for PDF
        data = {
            'filters': {
                'project_id': project_id,
                'dog_id': dog_id,
                'range_type': range_type,
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'show_kpis': show_kpis
            },
            'granularity': granularity
        }
        
        # Add KPIs if requested
        if show_kpis:
            total_visits = len(visits)
            by_visit_type = {}
            total_medications = 0
            total_cost = 0
            # VeterinaryVisit doesn't track duration like TrainingSession
            total_dogs = len(set(visit.dog_id for visit in visits))
            total_vets = len(set(visit.vet_id for visit in visits))
            
            for visit in visits:
                visit_type_label = get_visit_type_display(visit.visit_type)
                by_visit_type[visit_type_label] = by_visit_type.get(visit_type_label, 0) + 1
                
                if visit.medications:
                    total_medications += len(visit.medications)
                
                if visit.cost:
                    total_cost += visit.cost
            
            data['kpis'] = {
                'total_visits': total_visits,
                'total_dogs': total_dogs,
                'total_vets': total_vets,
                'by_visit_type': by_visit_type,
                'total_medications': total_medications,
                'total_cost': round(total_cost, 2)
            }
        
        # Add rows/table data
        if granularity == "day":
            rows = []
            for visit in visits:
                project_name = "(خارج مشروع)" if not visit.project else visit.project.name
                
                rows.append({
                    'date': visit.visit_date.strftime('%Y-%m-%d'),
                    'time': visit.visit_date.strftime('%H:%M:%S'),
                    'dog_name': visit.dog.name if visit.dog else '',
                    'vet_name': visit.vet.name if visit.vet else '',
                    'visit_type': get_visit_type_display(visit.visit_type),
                    'diagnosis': visit.diagnosis or '',
                    'treatment': visit.treatment or '',
                    'medications': visit.medications or [],
                    'cost': visit.cost,
                    'notes': visit.notes or '',
                    'project_name': project_name
                })
            
            data['rows'] = rows
        else:
            # Create aggregate table
            dog_aggregates = {}
            for visit in visits:
                dog_key = visit.dog_id
                if dog_key not in dog_aggregates:
                    dog_aggregates[dog_key] = {
                        'dog_code': visit.dog.code if visit.dog else '',
                        'dog_name': visit.dog.name if visit.dog else '',
                        'visits': 0,
                        'by_visit_type': {},
                        'medications_count': 0,
                        'cost_sum': 0
                    }
                
                agg = dog_aggregates[dog_key]
                agg['visits'] += 1
                
                visit_type_label = get_visit_type_display(visit.visit_type)
                agg['by_visit_type'][visit_type_label] = agg['by_visit_type'].get(visit_type_label, 0) + 1
                
                if visit.medications:
                    agg['medications_count'] += len(visit.medications)
                
                if visit.cost:
                    agg['cost_sum'] += visit.cost
                
                # VeterinaryVisit doesn't track duration
            
            table = []
            for agg in dog_aggregates.values():
                avg_duration = None
                # VeterinaryVisit doesn't track duration
                
                table.append({
                    'dog_code': agg['dog_code'],
                    'dog_name': agg['dog_name'],
                    'visits': agg['visits'],
                    'by_visit_type': agg['by_visit_type'],
                    'medications_count': agg['medications_count'],
                    'cost_sum': round(agg['cost_sum'], 2),
                    # No duration tracking for veterinary visits
                })
            
            data['table'] = table
        
        # Generate PDF
        register_arabic_fonts()
        
        # Create directory structure
        today_str = datetime.now().strftime('%Y-%m-%d')
        export_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', 'veterinary', today_str)
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename
        project_code = "all"
        if data['filters']['project_id']:
            project = Project.query.get(data['filters']['project_id'])
            if project and project.code:
                project_code = project.code
        
        date_from = data['filters']['date_from']
        date_to = data['filters']['date_to']
        filename = f"breeding_veterinary_{project_code}_{date_from}_to_{date_to}.pdf"
        file_path = os.path.join(export_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        # Import and create standardized header
        from k9.utils.report_header import create_pdf_report_header
        
        # Header information
        project_name = "الكل" if not data['filters']['project_id'] else "مشروع محدد"
        date_range = format_date_range_for_display(
            parse_date_string(date_from), 
            parse_date_string(date_to), 
            data['filters']['range_type']
        )
        
        additional_info = f"المشروع: {project_name}   الفترة: {date_range}"
        
        # Add standardized header
        header_elements = create_pdf_report_header(
            report_title_ar="التقرير البيطري",
            additional_info=additional_info
        )
        story.extend(header_elements)
        
        # KPIs section
        if data.get('kpis') and data['filters']['show_kpis']:
            kpis = data['kpis']
            kpis_data = [
                [rtl("إجمالي الزيارات"), str(kpis['total_visits'])],
                [rtl("إجمالي الأدوية"), str(kpis['total_medications'])],
                [rtl("إجمالي التكلفة"), f"{kpis['total_cost']} ر.س"],
            ]
            
            # No duration data for veterinary visits
            
            # Visit type breakdown
            for visit_type, count in kpis['by_visit_type'].items():
                kpis_data.append([rtl(f"زيارات {visit_type}"), str(count)])
            
            kpis_table = Table(kpis_data, colWidths=[200, 100])
            kpis_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), get_arabic_font_name()),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            story.append(kpis_table)
            story.append(Spacer(1, 20))
        
        # Data table
        table_data = None
        if data['granularity'] == "day" and 'rows' in data:
            # Daily detailed table - REORGANIZED column order for better readability
            headers = [
                rtl("التاريخ"), rtl("الوقت"), rtl("الكلب"), rtl("اسم الطبيب"), 
                rtl("نوع الزيارة"), rtl("التشخيص"), rtl("العلاج"), rtl("الأدوية"), 
                rtl("التكلفة"), rtl("المشروع"), rtl("ملاحظات")
            ]
            
            table_data = [headers]
            for row in data['rows']:
                medications_str = format_medications_display(row['medications'])
                cost_str = f"{row['cost']} ر.س" if row['cost'] else ""
                # No duration data for veterinary visits
                duration_str = ""
                
                # REORGANIZED: Better column order matching headers
                table_data.append([
                    row['date'],
                    row['time'],
                    rtl(row['dog_name']),
                    rtl(row['vet_name']),
                    rtl(row['visit_type']),
                    rtl(row['diagnosis']),
                    rtl(row['treatment']),
                    rtl(medications_str),
                    rtl(cost_str),
                    rtl(row['project_name']),
                    rtl(row['notes'])
                ])
        
        elif 'table' in data:
            # Aggregate table (RTL column order) - FIXED: Apply RTL to headers, removed duration
            headers = [
                rtl("الكود"), rtl("الكلب"), rtl("عدد الزيارات"), 
                rtl("حسب النوع"), rtl("عدد الأدوية"), rtl("مجموع التكلفة")
            ]
            
            table_data = [headers]
            for row in data['table']:
                visit_types_str = ", ".join([f"{t}: {c}" for t, c in row['by_visit_type'].items()])
                cost_str = f"{row['cost_sum']} ر.س" if row['cost_sum'] else ""
                # No duration data for veterinary visits  
                duration_str = ""
                
                # FIXED: Removed duration column for better width management
                table_data.append([
                    rtl(row['dog_code']),
                    rtl(row['dog_name']),
                    str(row['visits']),
                    rtl(visit_types_str),
                    str(row['medications_count']),
                    rtl(cost_str)
                ])
        
        # Create and style table with proper width management
        if table_data is not None:
            # FIXED: Calculate optimal column widths based on content and page width
            page_width = A4[0] - 120  # Smaller table with more margins
            num_columns = len(table_data[0]) if table_data else 0
            
            if num_columns > 0:
                # Define column widths based on content type and importance
                if data['granularity'] == "day":
                    # SMARTER column widths based on content type and typical length
                    col_widths = [
                        page_width * 0.07,  # التاريخ - dates are predictable width
                        page_width * 0.05,  # الوقت - times are short
                        page_width * 0.10,  # الكلب - dog names are usually short
                        page_width * 0.11,  # اسم الطبيب - vet names vary
                        page_width * 0.09,  # نوع الزيارة - visit types are fixed options
                        page_width * 0.20,  # التشخيص - diagnoses need most space (medical details)
                        page_width * 0.20,  # العلاج - treatments need most space (medical details)  
                        page_width * 0.08,  # الأدوية - medication names are usually short
                        page_width * 0.06,  # التكلفة - costs are just numbers
                        page_width * 0.08,  # المشروع - project names are usually short
                        page_width * 0.16   # ملاحظات - notes need reasonable space but not too much
                    ]
                else:
                    # SMARTER aggregate table widths
                    col_widths = [
                        page_width * 0.10,  # الكود - codes are short
                        page_width * 0.16,  # الكلب - dog names need reasonable space
                        page_width * 0.12,  # عدد الزيارات - visit counts are numbers
                        page_width * 0.38,  # حسب النوع - visit type breakdown needs most space
                        page_width * 0.10,  # عدد الأدوية - medication counts are numbers
                        page_width * 0.14   # مجموع التكلفة - total costs need moderate space
                    ]
                
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), get_arabic_font_name()),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),  # Smaller font for better fit
                    ('FONTSIZE', (0, 0), (-1, 0), 8),   # Slightly larger for headers
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue]),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(table)
            else:
                # Fallback for empty data
                story.append(Paragraph(rtl("لا توجد بيانات لعرضها"), title_style))
        
        # Footer for daily reports
        if data['granularity'] == "day":
            story.append(Spacer(1, 40))
            footer_style = ParagraphStyle(
                'Footer',
                fontName=get_arabic_font_name(),
                fontSize=12,
                alignment=TA_RIGHT,
                spaceAfter=10
            )
            
            story.append(Paragraph(rtl("ملاحظات عامة:"), footer_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph(rtl("اسم الطبيب البيطري: ________________    التوقيع: ________________"), footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(rtl("مسؤول المشروع: ________________    التوقيع: ________________"), footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Return file info
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        download_url = f"/uploads/{relative_path.replace(os.sep, '/')}"
        
        return jsonify({
            'success': True,
            'file': download_url,
            'filename': filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in veterinary PDF export: {e}")
        return jsonify({'error': 'حدث خطأ في تصدير التقرير'}), 500