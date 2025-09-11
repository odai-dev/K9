"""
Breeding Feeding Reports API
Handles data endpoints for Arabic/RTL feeding reports
"""

import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import and_, func
from sqlalchemy.orm import selectinload, joinedload

from k9.utils.permission_decorators import require_sub_permission
from k9.models.models import (
    FeedingLog, Dog, Project, PermissionType, BodyConditionScale, PrepMethod
)
from k9.utils.utils import get_user_projects, check_project_access
from k9.utils.pdf_rtl import register_arabic_fonts, rtl, get_arabic_font
from k9.utils.utils_pdf_rtl import get_arabic_font_name
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from app import db

# Create blueprint
bp = Blueprint('breeding_feeding_reports_api', __name__)


def get_meal_type_display(meal_type_fresh, meal_type_dry):
    """Convert boolean meal types to Arabic display format"""
    if meal_type_fresh and meal_type_dry:
        return "مختلط"
    elif meal_type_fresh:
        return "طازج"
    elif meal_type_dry:
        return "مجفف"
    else:
        return "غير محدد"


def get_bcs_numeric(bcs_enum):
    """Extract numeric value from BCS enum (1-9)"""
    if not bcs_enum:
        return None
    
    # Map enum values to numeric BCS
    bcs_mapping = {
        BodyConditionScale.VERY_THIN: 1,
        BodyConditionScale.THIN: 2,
        BodyConditionScale.BELOW_IDEAL: 3,
        BodyConditionScale.NEAR_IDEAL: 4,
        BodyConditionScale.IDEAL: 5,
        BodyConditionScale.ABOVE_IDEAL: 6,
        BodyConditionScale.FULL: 7,
        BodyConditionScale.OBESE: 8,
        BodyConditionScale.VERY_OBESE: 9,
    }
    return bcs_mapping.get(bcs_enum)


@bp.route('/daily')
@login_required
@require_sub_permission("Reports", "Feeding Daily", PermissionType.VIEW)
def feeding_daily_data():
    """Get daily feeding report data with KPIs and rows"""
    project_id = request.args.get('project_id')
    date_str = request.args.get('date')
    dog_id = request.args.get('dog_id')  # optional filter
    
    if not project_id or not date_str:
        return jsonify({'error': 'مشروع وتاريخ مطلوبان'}), 400
    
    # Verify project access
    if not check_project_access(current_user, project_id):
        return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Build query with joins
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),
        joinedload(FeedingLog.project)
    ).filter(
        FeedingLog.project_id == project_id,
        FeedingLog.date == target_date
    )
    
    if dog_id:
        query = query.filter(FeedingLog.dog_id == dog_id)
    
    feeding_logs = query.order_by(FeedingLog.time.desc()).all()
    
    # Calculate KPIs
    total_meals = len(feeding_logs)
    total_grams = sum(log.grams or 0 for log in feeding_logs)
    total_water_ml = sum(log.water_ml or 0 for log in feeding_logs)
    
    # Count by meal type
    by_meal_type = {"طازج": 0, "مجفف": 0, "مختلط": 0}
    bcs_dist = defaultdict(int)
    
    for log in feeding_logs:
        meal_type = get_meal_type_display(log.meal_type_fresh, log.meal_type_dry)
        if meal_type in by_meal_type:
            by_meal_type[meal_type] += 1
        
        if log.body_condition:
            bcs_num = get_bcs_numeric(log.body_condition)
            if bcs_num:
                bcs_dist[str(bcs_num)] += 1
    
    # Format rows for frontend
    rows = []
    for log in feeding_logs:
        rows.append({
            "date": log.date.strftime('%Y-%m-%d'),
            "time": log.time.strftime('%H:%M:%S'),
            "dog_id": str(log.dog_id),
            "dog_code": log.dog.code if log.dog else "",
            "dog_name": log.dog.name if log.dog else "",
            "نوع_الوجبة": get_meal_type_display(log.meal_type_fresh, log.meal_type_dry),
            "اسم_الوجبة": log.meal_name or "",
            "كمية_الوجبة_غرام": log.grams or 0,
            "ماء_الشرب_مل": log.water_ml or 0,
            "طريقة_التحضير": log.prep_method.value if log.prep_method else "",
            "مكملات": log.supplements or [],
            "كتلة_الجسد_BCS": str(get_bcs_numeric(log.body_condition)) if log.body_condition else "",
            "ملاحظات": log.notes or ""
        })
    
    return jsonify({
        "filters": {
            "project_id": project_id,
            "date": date_str,
            "dog_id": dog_id
        },
        "kpis": {
            "total_meals": total_meals,
            "total_grams": total_grams,
            "total_water_ml": total_water_ml,
            "by_meal_type": by_meal_type,
            "bcs_dist": dict(bcs_dist)
        },
        "rows": rows
    })


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Feeding Weekly", PermissionType.VIEW) 
def feeding_weekly_data():
    """Get weekly feeding report data aggregated by dog"""
    project_id = request.args.get('project_id')
    week_start_str = request.args.get('week_start')
    dog_id = request.args.get('dog_id')  # optional filter
    
    if not project_id or not week_start_str:
        return jsonify({'error': 'مشروع وبداية الأسبوع مطلوبان'}), 400
    
    # Verify project access
    if not check_project_access(current_user, project_id):
        return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
    
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Build query
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),
        joinedload(FeedingLog.project)
    ).filter(
        FeedingLog.project_id == project_id,
        FeedingLog.date >= week_start,
        FeedingLog.date <= week_end
    )
    
    if dog_id:
        query = query.filter(FeedingLog.dog_id == dog_id)
    
    feeding_logs = query.all()
    
    # Group by dog and aggregate
    dog_data = {}
    
    def get_dog_data():
        return {
            'dog_id': '',
            'dog_code': '',
            'dog_name': '',
            'meals': 0,
            'grams_sum': 0,
            'water_sum_ml': 0,
            'bcs_values': [],
            'by_type': {"طازج": 0, "مجفف": 0, "مختلط": 0},
            'days': {
                'Mon': {'meals': 0, 'grams': 0, 'water': 0},
                'Tue': {'meals': 0, 'grams': 0, 'water': 0},
                'Wed': {'meals': 0, 'grams': 0, 'water': 0},
                'Thu': {'meals': 0, 'grams': 0, 'water': 0},
                'Fri': {'meals': 0, 'grams': 0, 'water': 0},
                'Sat': {'meals': 0, 'grams': 0, 'water': 0},
                'Sun': {'meals': 0, 'grams': 0, 'water': 0}
            }
        }
    
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    for log in feeding_logs:
        dog_key = str(log.dog_id)
        
        # Initialize dog data if not exists
        if dog_key not in dog_data:
            dog_data[dog_key] = get_dog_data()
            
        data = dog_data[dog_key]
        
        # Add dog info
        data['dog_id'] = dog_key
        data['dog_code'] = log.dog.code if log.dog else ""
        data['dog_name'] = log.dog.name if log.dog else ""
        
        # Aggregate totals
        data['meals'] += 1
        data['grams_sum'] += log.grams or 0
        data['water_sum_ml'] += log.water_ml or 0
        
        # Track BCS values
        if log.body_condition:
            bcs_num = get_bcs_numeric(log.body_condition)
            if bcs_num:
                data['bcs_values'].append(bcs_num)
        
        # Count by meal type
        meal_type = get_meal_type_display(log.meal_type_fresh, log.meal_type_dry)
        if meal_type in data['by_type']:
            data['by_type'][meal_type] += 1
        
        # Aggregate by day
        weekday = weekdays[log.date.weekday()]
        data['days'][weekday]['meals'] += 1
        data['days'][weekday]['grams'] += log.grams or 0
        data['days'][weekday]['water'] += log.water_ml or 0
    
    # Calculate final averages and format table
    table = []
    dogs_count = len(dog_data)
    meals_count = sum(data['meals'] for data in dog_data.values())
    grams_sum = sum(data['grams_sum'] for data in dog_data.values())
    water_sum_ml = sum(data['water_sum_ml'] for data in dog_data.values())
    
    all_bcs_values = []
    for data in dog_data.values():
        all_bcs_values.extend(data['bcs_values'])
    
    avg_bcs = sum(all_bcs_values) / len(all_bcs_values) if all_bcs_values else None
    
    for data in dog_data.values():
        bcs_avg = sum(data['bcs_values']) / len(data['bcs_values']) if data['bcs_values'] else None
        
        table.append({
            "dog_id": data['dog_id'],
            "dog_code": data['dog_code'],
            "dog_name": data['dog_name'],
            "meals": data['meals'],
            "grams_sum": data['grams_sum'],
            "water_sum_ml": data['water_sum_ml'],
            "bcs_avg": round(bcs_avg, 1) if bcs_avg else None,
            "by_type": data['by_type'],
            "days": data['days']
        })
    
    return jsonify({
        "filters": {
            "project_id": project_id,
            "week_start": week_start_str,
            "dog_id": dog_id
        },
        "kpis": {
            "dogs_count": dogs_count,
            "meals_count": meals_count,
            "grams_sum": grams_sum,
            "water_sum_ml": water_sum_ml,
            "avg_bcs": round(avg_bcs, 1) if avg_bcs else None
        },
        "table": table
    })


@bp.route('/daily/export.pdf')
@login_required
@require_sub_permission("Reports", "Feeding Daily", PermissionType.EXPORT)
def export_daily_pdf():
    """Export daily feeding report as PDF"""
    # Get the same data as daily endpoint
    project_id = request.args.get('project_id')
    date_str = request.args.get('date')
    dog_id = request.args.get('dog_id')
    
    if not project_id or not date_str:
        return jsonify({'error': 'مشروع وتاريخ مطلوبان'}), 400
    
    # Verify project access
    if not check_project_access(current_user, project_id):
        return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
    
    # Get data by directly calling the same logic
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Build query with joins - reuse same logic as daily endpoint
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),
        joinedload(FeedingLog.project)
    ).filter(
        FeedingLog.project_id == project_id,
        FeedingLog.date == target_date
    )
    
    if dog_id:
        query = query.filter(FeedingLog.dog_id == dog_id)
    
    feeding_logs = query.order_by(FeedingLog.time.desc()).all()
    
    # Calculate data - simplified version for PDF
    total_meals = len(feeding_logs)
    total_grams = sum(log.grams or 0 for log in feeding_logs)
    total_water_ml = sum(log.water_ml or 0 for log in feeding_logs)
    
    rows = []
    for log in feeding_logs:
        rows.append({
            "date": log.date.strftime('%Y-%m-%d'),
            "dog_name": log.dog.name if log.dog else "",
            "نوع_الوجبة": get_meal_type_display(log.meal_type_fresh, log.meal_type_dry),
            "كمية_الوجبة_غرام": log.grams or 0,
            "ماء_الشرب_مل": log.water_ml or 0
        })
    
    data = {
        "kpis": {
            "total_meals": total_meals,
            "total_grams": total_grams,
            "total_water_ml": total_water_ml
        },
        "rows": rows
    }
    
    # Generate PDF
    try:
        filename = f"feeding_daily_{date_str}_{project_id}.pdf"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', 'feeding', date_str)
        os.makedirs(file_path, exist_ok=True)
        full_path = os.path.join(file_path, filename)
        
        # Generate RTL PDF using available utilities
        _generate_feeding_pdf(
            title="تقرير التغذية اليومي",
            data=data,
            output_path=full_path
        )
        
        return jsonify({
            "success": True,
            "file": f"/uploads/reports/feeding/{date_str}/{filename}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating feeding daily PDF: {str(e)}")
        return jsonify({'error': 'خطأ في إنشاء ملف PDF'}), 500


@bp.route('/weekly/export.pdf')
@login_required
@require_sub_permission("Reports", "Feeding Weekly", PermissionType.EXPORT)
def export_weekly_pdf():
    """Export weekly feeding report as PDF"""
    # Get the same data as weekly endpoint
    project_id = request.args.get('project_id')
    week_start_str = request.args.get('week_start')
    dog_id = request.args.get('dog_id')
    
    if not project_id or not week_start_str:
        return jsonify({'error': 'مشروع وبداية الأسبوع مطلوبان'}), 400
    
    # Verify project access
    if not check_project_access(current_user, project_id):
        return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
    
    # Get data by directly calling the same logic
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Build query - reuse same logic as weekly endpoint
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),
        joinedload(FeedingLog.project)
    ).filter(
        FeedingLog.project_id == project_id,
        FeedingLog.date >= week_start,
        FeedingLog.date <= week_end
    )
    
    if dog_id:
        query = query.filter(FeedingLog.dog_id == dog_id)
    
    feeding_logs = query.all()
    
    # Simplified aggregation for PDF
    dog_data = {}
    for log in feeding_logs:
        dog_key = str(log.dog_id)
        if dog_key not in dog_data:
            dog_data[dog_key] = {
                'dog_name': log.dog.name if log.dog else "",
                'meals': 0,
                'grams_sum': 0,
                'water_sum_ml': 0
            }
        
        dog_data[dog_key]['meals'] += 1
        dog_data[dog_key]['grams_sum'] += log.grams or 0
        dog_data[dog_key]['water_sum_ml'] += log.water_ml or 0
    
    table = list(dog_data.values())
    dogs_count = len(dog_data)
    meals_count = sum(d['meals'] for d in dog_data.values())
    
    data = {
        "kpis": {
            "dogs_count": dogs_count,
            "meals_count": meals_count
        },
        "table": table
    }
    
    # Generate PDF
    try:
        filename = f"feeding_weekly_{week_start_str}_{project_id}.pdf"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', 'feeding', week_start_str)
        os.makedirs(file_path, exist_ok=True)
        full_path = os.path.join(file_path, filename)
        
        # Generate RTL PDF using available utilities  
        _generate_feeding_pdf(
            title="تقرير التغذية الأسبوعي",
            data=data,
            output_path=full_path
        )
        
        return jsonify({
            "success": True,
            "file": f"/uploads/reports/feeding/{week_start_str}/{filename}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating feeding weekly PDF: {str(e)}")
        return jsonify({'error': 'خطأ في إنشاء ملف PDF'}), 500


def _generate_feeding_pdf(title: str, data: dict, output_path: str):
    """Generate feeding report PDF with Arabic RTL support"""
    # Register Arabic fonts
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40,
                          topMargin=40, bottomMargin=40)
    
    # Build content
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=getSampleStyleSheet()['Heading1'],
        fontName=font_name,
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(rtl(title), title_style))
    story.append(Spacer(1, 20))
    
    # Add KPIs section
    if 'kpis' in data:
        kpis = data['kpis']
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=getSampleStyleSheet()['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        
        story.append(Paragraph(rtl("الملخص التنفيذي"), header_style))
        
        kpi_data = []
        if 'total_meals' in kpis:
            kpi_data.append([rtl('إجمالي الوجبات'), str(kpis['total_meals'])])
        if 'total_grams' in kpis:
            kpi_data.append([rtl('إجمالي الغرامات'), str(kpis['total_grams'])])
        if 'total_water_ml' in kpis:
            kpi_data.append([rtl('إجمالي الماء (مل)'), str(kpis['total_water_ml'])])
        if 'dogs_count' in kpis:
            kpi_data.append([rtl('عدد الكلاب'), str(kpis['dogs_count'])])
        if 'meals_count' in kpis:
            kpi_data.append([rtl('عدد الوجبات'), str(kpis['meals_count'])])
            
        if kpi_data:
            kpi_table = Table(kpi_data, colWidths=[3*72, 2*72])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 20))
    
    # Add detailed data table if available
    if 'rows' in data and data['rows']:
        # Daily report table
        table_data = []
        headers = [rtl('التاريخ'), rtl('الكلب'), rtl('نوع الوجبة'), rtl('الكمية (غرام)'), rtl('الماء (مل)')]
        table_data.append(headers)
        
        for row in data['rows'][:20]:  # Limit to first 20 rows for PDF
            table_data.append([
                row.get('date', ''),
                row.get('dog_name', ''),
                rtl(row.get('نوع_الوجبة', '')),
                str(row.get('كمية_الوجبة_غرام', 0)),
                str(row.get('ماء_الشرب_مل', 0))
            ])
            
        detail_table = Table(table_data, colWidths=[1.5*72, 1.5*72, 1.5*72, 1*72, 1*72])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(detail_table)
    
    elif 'table' in data and data['table']:
        # Weekly report table
        table_data = []
        headers = [rtl('الكلب'), rtl('عدد الوجبات'), rtl('الغرامات'), rtl('الماء (مل)'), rtl('متوسط BCS')]
        table_data.append(headers)
        
        for row in data['table']:
            table_data.append([
                rtl(row.get('dog_name', '')),
                str(row.get('meals', 0)),
                str(row.get('grams_sum', 0)),
                str(row.get('water_sum_ml', 0)),
                str(row.get('bcs_avg', '')) if row.get('bcs_avg') else ''
            ])
            
        detail_table = Table(table_data, colWidths=[2*72, 1*72, 1*72, 1*72, 1*72])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(detail_table)
    
    # Build PDF
    doc.build(story)