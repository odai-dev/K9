"""
Breeding Feeding Reports API
Handles data endpoints for Arabic/RTL feeding reports
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
    FeedingLog, Dog, Project, PermissionType, BodyConditionScale, PrepMethod
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
    
    # Performance optimization: Add pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 records to match existing patterns
    
    if not date_str:
        return jsonify({'error': 'التاريخ مطلوب'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (UUID) when provided
    no_project_filter = False
    if project_id and project_id.strip():
        if project_id.strip() == "no_project":
            # Special case: filter for records with NULL project_id
            no_project_filter = True
            project_id = None
        else:
            # project_id is a UUID string - keep as string for database queries
            project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        # dog_id is a UUID string, not an integer
        dog_id = dog_id.strip()
    else:
        dog_id = None
    
    # Security fix: Get user's authorized projects when project_id is omitted
    if project_id is not None and not no_project_filter:
        # Verify project access for specific project
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    elif not no_project_filter:
        # Get all authorized projects for the user
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    else:
        # no_project_filter case: no project authorization needed
        authorized_project_ids = []
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Security fix: Scope queries to authorized projects only
    base_query = db.session.query(FeedingLog).options(
        selectinload(FeedingLog.dog),  # type: ignore
        selectinload(FeedingLog.project)  # type: ignore
    ).filter(
        FeedingLog.date == target_date
    )
    
    # Apply project filtering based on the filter type
    if no_project_filter:
        # Special case: only records with NULL project_id
        base_query = base_query.filter(FeedingLog.project_id.is_(None))
    elif project_id is not None:
        # Specific project filter
        base_query = base_query.filter(FeedingLog.project_id == project_id)
    else:
        # All authorized projects (default behavior)
        base_query = base_query.filter(FeedingLog.project_id.in_(authorized_project_ids))
    
    if dog_id:
        base_query = base_query.filter(FeedingLog.dog_id == dog_id)
    
    # Get total count for pagination
    total_count = base_query.count()
    
    # Apply pagination and ordering
    feeding_logs = base_query.order_by(FeedingLog.time.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Security fix: KPI query must match base query filters
    kpi_query = db.session.query(
        func.count(FeedingLog.id).label('total_meals'),
        func.sum(FeedingLog.grams).label('total_grams'),
        func.sum(FeedingLog.water_ml).label('total_water_ml'),
        func.count(func.distinct(FeedingLog.dog_id)).label('unique_dogs'),
        func.sum(case((FeedingLog.meal_type_fresh == True, 1), else_=0)).label('fresh_meals'),
        func.sum(case((FeedingLog.meal_type_dry == True, 1), else_=0)).label('dry_meals')
    ).filter(
        FeedingLog.date == target_date,
        FeedingLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        kpi_query = kpi_query.filter(FeedingLog.dog_id == dog_id)
    
    kpi_result = kpi_query.first()
    
    # Extract KPI values with null checking
    if kpi_result:
        total_meals_all = kpi_result.total_meals or 0
        total_grams = kpi_result.total_grams or 0
        total_water_ml = kpi_result.total_water_ml or 0
        unique_dogs = kpi_result.unique_dogs or 0
        fresh_meals = kpi_result.fresh_meals or 0
        dry_meals = kpi_result.dry_meals or 0
    else:
        total_meals_all = 0
        total_grams = 0
        total_water_ml = 0
        unique_dogs = 0
        fresh_meals = 0
        dry_meals = 0
    
    # Calculate additional metrics (backward compatible)
    avg_quantity = (total_grams / total_meals_all) if total_meals_all > 0 else 0
    
    # Count by meal type and BCS distribution for backward compatibility
    by_meal_type = {"طازج": fresh_meals, "مجفف": dry_meals, "مختلط": 0}
    bcs_dist = defaultdict(int)
    poor_conditions = 0
    
    # Get BCS distribution separately to maintain compatibility
    for log in feeding_logs:
        meal_type = get_meal_type_display(log.meal_type_fresh, log.meal_type_dry)
        if meal_type == "مختلط":
            by_meal_type["مختلط"] += 1
        
        if log.body_condition:
            bcs_num = get_bcs_numeric(log.body_condition)
            if bcs_num:
                bcs_dist[str(bcs_num)] += 1
                if bcs_num <= 3:  # Consider 1-3 as poor conditions
                    poor_conditions += 1
    
    # Get project name for response
    project = db.session.query(Project).filter(Project.id == project_id).first()
    project_name = project.name if project else ""
    
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
            "total_meals": total_meals_all,
            "total_dogs": unique_dogs,
            "total_grams": total_grams,
            "total_water_ml": total_water_ml,
            "fresh_meals": fresh_meals,
            "dry_meals": dry_meals,
            "poor_conditions": poor_conditions,
            "avg_quantity": round(avg_quantity, 2),
            "by_meal_type": by_meal_type,
            "bcs_dist": dict(bcs_dist)
        },
        "rows": rows,
        "date": date_str,
        "project_name": project_name
    })


@bp.route('/weekly')
@login_required
@require_sub_permission("Reports", "Feeding Weekly", PermissionType.VIEW) 
def feeding_weekly_data():
    """Get weekly feeding report data aggregated by dog"""
    project_id = request.args.get('project_id')
    week_start_str = request.args.get('week_start')
    dog_id = request.args.get('dog_id')  # optional filter
    
    # Performance optimization: Add pagination for weekly reports  
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 dogs per page
    
    if not week_start_str:
        return jsonify({'error': 'بداية الأسبوع مطلوبة'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (integer) when provided
    if project_id and project_id.strip():
        # project_id is a UUID string - keep as string for database queries
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        try:
            dog_id = int(dog_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'معرف الكلب يجب أن يكون رقماً'}), 400
    else:
        dog_id = None
    
    # Security fix: Get user's authorized projects when project_id is omitted
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
    
    # Security fix: Scope query to authorized projects only
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),  # type: ignore
        joinedload(FeedingLog.project)  # type: ignore
    ).filter(
        FeedingLog.project_id.in_(authorized_project_ids),
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
        "rows": table
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
    
    if not date_str:
        return jsonify({'error': 'التاريخ مطلوب'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (integer) when provided
    if project_id and project_id.strip():
        # project_id is a UUID string - keep as string for database queries
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        try:
            dog_id = int(dog_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'معرف الكلب يجب أن يكون رقماً'}), 400
    else:
        dog_id = None
    
    # Security fix: Get user's authorized projects when project_id is omitted
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
    
    # Get data by directly calling the same logic
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Security fix: Scope query to authorized projects only
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),  # type: ignore
        joinedload(FeedingLog.project)  # type: ignore
    ).filter(
        FeedingLog.date == target_date,
        FeedingLog.project_id.in_(authorized_project_ids)
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
        # Security fix: Use 'all' instead of None for filename when project_id is omitted
        project_suffix = str(project_id) if project_id else "all"
        filename = f"feeding_daily_{date_str}_{project_suffix}.pdf"
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
    
    if not week_start_str:
        return jsonify({'error': 'بداية الأسبوع مطلوبة'}), 400
    
    # Input validation: Handle project_id (UUID) and dog_id (integer) when provided
    if project_id and project_id.strip():
        # project_id is a UUID string - keep as string for database queries
        project_id = project_id.strip()
    else:
        project_id = None
    
    if dog_id and dog_id.strip():
        try:
            dog_id = int(dog_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'معرف الكلب يجب أن يكون رقماً'}), 400
    else:
        dog_id = None
    
    # Security fix: Get user's authorized projects when project_id is omitted
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
    
    # Get data by directly calling the same logic
    try:
        week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
    except ValueError:
        return jsonify({'error': 'تنسيق التاريخ غير صالح'}), 400
    
    # Security fix: Scope query to authorized projects only
    query = db.session.query(FeedingLog).options(
        joinedload(FeedingLog.dog),  # type: ignore
        joinedload(FeedingLog.project)  # type: ignore
    ).filter(
        FeedingLog.project_id.in_(authorized_project_ids),
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
        # Security fix: Use 'all' instead of None for filename when project_id is omitted
        project_suffix = str(project_id) if project_id else "all"
        filename = f"feeding_weekly_{week_start_str}_{project_suffix}.pdf"
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
    from k9.utils.report_header import create_pdf_report_header
    
    # Register Arabic fonts
    register_arabic_fonts()
    font_name = get_arabic_font_name()
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=40, leftMargin=40,
                          topMargin=40, bottomMargin=40)
    
    # Build content
    story = []
    
    # Add standardized header
    header_elements = create_pdf_report_header(
        report_title_ar=title
    )
    story.extend(header_elements)
    
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
        # REVERSED order of KPIs and REVERSED columns (value first, then label)
        if 'meals_count' in kpis:
            kpi_data.append([str(kpis['meals_count']), rtl('عدد الوجبات')])
        if 'dogs_count' in kpis:
            kpi_data.append([str(kpis['dogs_count']), rtl('عدد الكلاب')])
        if 'total_water_ml' in kpis:
            kpi_data.append([str(kpis['total_water_ml']), rtl('إجمالي الماء (مل)')])
        if 'total_grams' in kpis:
            kpi_data.append([str(kpis['total_grams']), rtl('إجمالي الغرامات')])
        if 'total_meals' in kpis:
            kpi_data.append([str(kpis['total_meals']), rtl('إجمالي الوجبات')])
            
        if kpi_data:
            kpi_table = Table(kpi_data, colWidths=[2*72, 3*72])
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
        # Daily report table (REVERSED column order)
        table_data = []
        headers = [rtl('الماء (مل)'), rtl('الكمية (غرام)'), rtl('نوع الوجبة'), rtl('الكلب'), rtl('التاريخ')]
        table_data.append(headers)
        
        for row in data['rows'][:20]:  # Limit to first 20 rows for PDF
            table_data.append([
                str(row.get('ماء_الشرب_مل', 0)),
                str(row.get('كمية_الوجبة_غرام', 0)),
                rtl(row.get('نوع_الوجبة', '')),
                rtl(row.get('dog_name', '')),
                row.get('date', '')
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
        # Weekly report table (REVERSED column order)
        table_data = []
        headers = [rtl('متوسط BCS'), rtl('الماء (مل)'), rtl('الغرامات'), rtl('عدد الوجبات'), rtl('الكلب')]
        table_data.append(headers)
        
        for row in data['table']:
            table_data.append([
                str(row.get('bcs_avg', '')) if row.get('bcs_avg') else '',
                str(row.get('water_sum_ml', 0)),
                str(row.get('grams_sum', 0)),
                str(row.get('meals', 0)),
                rtl(row.get('dog_name', ''))
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


# ==============================================================================
# UNIFIED ENDPOINTS (New Range-Based API)
# ==============================================================================

@bp.route('/unified')
@login_required
def feeding_unified_data():
    """Unified feeding report data with range selector and smart aggregation"""
    
    # Check unified permission
    if not has_permission(current_user, "reports.breeding.feeding.view"):
        return jsonify({'error': 'ليس لديك صلاحية لعرض تقارير التغذية'}), 403
    
    # Get parameters
    range_type = request.args.get('range_type', 'daily')
    project_id = request.args.get('project_id', '').strip() or None
    dog_id = request.args.get('dog_id', '').strip() or None
    
    # Handle "no_project" special case
    no_project_filter = False
    if project_id and project_id.strip():
        if project_id.strip() == "no_project":
            # Special case: filter for records with NULL project_id
            no_project_filter = True
            project_id = None
        else:
            # project_id is a UUID string - keep as string for database queries
            project_id = project_id.strip()
    else:
        project_id = None
    
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
    if project_id is not None and not no_project_filter:
        # Verify project access for specific project
        if not check_project_access(current_user, project_id):
            return jsonify({'error': 'ليس لديك صلاحية للوصول لهذا المشروع'}), 403
        authorized_project_ids = [project_id]
    elif not no_project_filter:
        # Get all authorized projects for the user
        authorized_projects = get_user_projects(current_user)
        authorized_project_ids = [p.id for p in authorized_projects]
        if not authorized_project_ids:
            return jsonify({'error': 'ليس لديك صلاحية للوصول لأي مشروع'}), 403
    else:
        # no_project_filter case: no project authorization needed
        authorized_project_ids = []
    
    # Build base query with date range
    base_query = db.session.query(FeedingLog).options(
        selectinload(FeedingLog.dog),
        selectinload(FeedingLog.project),
        selectinload(FeedingLog.recorder_employee)
    ).filter(
        FeedingLog.date >= date_from,
        FeedingLog.date <= date_to
    )
    
    # Apply project filtering based on the filter type
    if no_project_filter:
        # Special case: only records with NULL project_id
        base_query = base_query.filter(FeedingLog.project_id.is_(None))
    elif project_id is not None:
        # Specific project filter
        base_query = base_query.filter(FeedingLog.project_id == project_id)
    else:
        # All authorized projects (default behavior)
        base_query = base_query.filter(FeedingLog.project_id.in_(authorized_project_ids))
    
    if dog_id:
        base_query = base_query.filter(FeedingLog.dog_id == dog_id)
    
    # Apply aggregation strategy
    if aggregation == "daily":
        # Daily: Show individual feeding records with pagination
        total_count = base_query.count()
        feeding_logs = base_query.order_by(
            FeedingLog.date.desc(),
            FeedingLog.time.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # Build daily response format
        rows = []
        for log in feeding_logs:
            meal_type = get_meal_type_display(log.meal_type_fresh, log.meal_type_dry)
            bcs_numeric = get_bcs_numeric(log.body_condition)
            
            # Handle supplements properly - return empty list if None
            supplements = log.supplements if log.supplements else []
            
            rows.append({
                'id': str(log.id),
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M'),
                'dog_name': log.dog.name if log.dog else 'غير معروف',
                'dog_microchip': log.dog.microchip_id if log.dog else '',
                'feeder': log.recorder_employee.name if log.recorder_employee else 'غير محدد',
                'project': log.project.name if log.project else 'غير محدد',
                'meal_type': meal_type,
                'grams': log.grams or 0,
                'water_ml': log.water_ml or 0,
                'prep_method': log.prep_method.value if log.prep_method else 'غير محدد',
                'body_condition_scale': bcs_numeric,
                'supplements': supplements,
                'notes': log.notes or ''
            })
        
    elif aggregation == "weekly":
        # Weekly: Aggregate by dog and week
        feeding_logs = base_query.all()
        
        # Group by dog and week
        dogs_data = {}
        total_count = 0
        
        for log in feeding_logs:
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
                    'meals': 0,
                    'total_grams': 0,
                    'total_water_ml': 0,
                    'bcs_values': [],
                    'logs': []
                }
            
            # Aggregate data for this week
            week_data = dogs_data[dog_key]['weeks'][week_key]
            week_data['meals'] += 1
            week_data['total_grams'] += log.grams or 0
            week_data['total_water_ml'] += log.water_ml or 0
            
            bcs_numeric = get_bcs_numeric(log.body_condition)
            if bcs_numeric:
                week_data['bcs_values'].append(bcs_numeric)
            
            week_data['logs'].append({
                'date': log.date.strftime('%Y-%m-%d'),
                'meal_type': get_meal_type_display(log.meal_type_fresh, log.meal_type_dry),
                'grams': log.grams or 0,
                'water_ml': log.water_ml or 0
            })
        
        # Convert to paginated rows format
        rows = []
        for dog_key, dog_data in list(dogs_data.items())[(page-1)*per_page:page*per_page]:
            for week_key, week_data in dog_data['weeks'].items():
                avg_bcs = sum(week_data['bcs_values']) / len(week_data['bcs_values']) if week_data['bcs_values'] else None
                rows.append({
                    'dog_name': dog_data['dog_name'],
                    'dog_microchip': dog_data['dog_microchip'],
                    'week': week_key,
                    'meals': week_data['meals'],
                    'total_grams': week_data['total_grams'],
                    'total_water_ml': week_data['total_water_ml'],
                    'avg_bcs': round(avg_bcs, 1) if avg_bcs else None,
                    'logs': week_data['logs']
                })
        
        total_count = len(dogs_data)
        
    elif aggregation == "monthly":
        # Monthly: Aggregate by dog and month
        feeding_logs = base_query.all()
        
        # Group by dog and month
        dogs_data = {}
        total_count = 0
        
        for log in feeding_logs:
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
                    'meals': 0,
                    'total_grams': 0,
                    'total_water_ml': 0,
                    'bcs_values': [],
                    'logs': []
                }
            
            # Aggregate data for this month
            month_data = dogs_data[dog_key]['months'][month_key]
            month_data['meals'] += 1
            month_data['total_grams'] += log.grams or 0
            month_data['total_water_ml'] += log.water_ml or 0
            
            bcs_numeric = get_bcs_numeric(log.body_condition)
            if bcs_numeric:
                month_data['bcs_values'].append(bcs_numeric)
            
            month_data['logs'].append({
                'date': log.date.strftime('%Y-%m-%d'),
                'meal_type': get_meal_type_display(log.meal_type_fresh, log.meal_type_dry),
                'grams': log.grams or 0,
                'water_ml': log.water_ml or 0
            })
        
        # Convert to paginated rows format
        rows = []
        for dog_key, dog_data in list(dogs_data.items())[(page-1)*per_page:page*per_page]:
            for month_key, month_data in dog_data['months'].items():
                avg_bcs = sum(month_data['bcs_values']) / len(month_data['bcs_values']) if month_data['bcs_values'] else None
                rows.append({
                    'dog_name': dog_data['dog_name'],
                    'dog_microchip': dog_data['dog_microchip'],
                    'month': month_key,
                    'meals': month_data['meals'],
                    'total_grams': month_data['total_grams'],
                    'total_water_ml': month_data['total_water_ml'],
                    'avg_bcs': round(avg_bcs, 1) if avg_bcs else None,
                    'logs': month_data['logs']
                })
        
        total_count = len(dogs_data)
        
    else:
        return jsonify({'error': 'إستراتيجية التجميع غير مدعومة'}), 400
    
    # Calculate KPIs from full dataset
    kpi_query = db.session.query(
        func.count(FeedingLog.id).label('total_feedings'),
        func.count(func.distinct(FeedingLog.dog_id)).label('unique_dogs'),
        func.sum(FeedingLog.grams).label('total_grams'),
        func.sum(FeedingLog.water_ml).label('total_water_ml')
    ).filter(
        FeedingLog.date >= date_from,
        FeedingLog.date <= date_to,
        FeedingLog.project_id.in_(authorized_project_ids)
    )
    
    if dog_id:
        kpi_query = kpi_query.filter(FeedingLog.dog_id == dog_id)
    
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
            'total_feedings': kpi_result.total_feedings if kpi_result else 0,
            'unique_dogs': kpi_result.unique_dogs if kpi_result else 0,
            'total_grams': float(kpi_result.total_grams or 0) if kpi_result else 0,
            'total_water_ml': float(kpi_result.total_water_ml or 0) if kpi_result else 0,
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
def feeding_unified_export_pdf():
    """Export unified feeding report as PDF with proper naming"""
    
    # Check export permission
    if not has_permission(current_user, "reports.breeding.feeding.export"):
        return jsonify({'error': 'ليس لديك صلاحية لتصدير تقارير التغذية'}), 403
    
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
        filename = generate_export_filename("feeding", project_code, date_from, date_to, "pdf")
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
        base_query = db.session.query(FeedingLog).options(
            selectinload(FeedingLog.dog),
            selectinload(FeedingLog.project),
            selectinload(FeedingLog.recorder_employee)
        ).filter(
            FeedingLog.date >= date_from,
            FeedingLog.date <= date_to,
            FeedingLog.project_id.in_(authorized_project_ids)
        )
        
        if dog_id:
            base_query = base_query.filter(FeedingLog.dog_id == dog_id)
        
        feeding_logs = base_query.order_by(FeedingLog.date.desc(), FeedingLog.time.desc()).all()
        
        # Calculate KPIs
        total_feedings = len(feeding_logs)
        unique_dogs = len(set(str(log.dog_id) for log in feeding_logs))
        total_grams = sum(log.grams or 0 for log in feeding_logs)
        total_water_ml = sum(log.water_ml or 0 for log in feeding_logs)
        
        # Group by meal type
        meal_type_counts = defaultdict(int)
        for log in feeding_logs:
            meal_type = get_meal_type_display(log.meal_type_fresh, log.meal_type_dry)
            meal_type_counts[meal_type] += 1
        
        # Prepare data for existing PDF generation
        pdf_data = {
            'kpis': {
                'total_meals': total_feedings,
                'total_grams': total_grams,
                'total_water_ml': total_water_ml,
                'dogs_count': unique_dogs,
                'meals_count': total_feedings
            }
        }
        
        # Prepare rows data for PDF - limit to first 50 for readability
        if aggregation == "daily":
            pdf_data['rows'] = []
            for log in feeding_logs[:50]:
                pdf_data['rows'].append({
                    'date': log.date.strftime('%Y-%m-%d'),
                    'dog_name': log.dog.name if log.dog else 'غير معروف',
                    'نوع_الوجبة': get_meal_type_display(log.meal_type_fresh, log.meal_type_dry),
                    'كمية_الوجبة_غرام': log.grams or 0,
                    'ماء_الشرب_مل': log.water_ml or 0
                })
        else:
            # For weekly/monthly aggregation, create summary table
            dogs_summary = {}
            for log in feeding_logs:
                dog_key = str(log.dog_id)
                if dog_key not in dogs_summary:
                    dogs_summary[dog_key] = {
                        'dog_name': log.dog.name if log.dog else 'غير معروف',
                        'meals': 0,
                        'grams_sum': 0,
                        'water_sum_ml': 0,
                        'bcs_values': []
                    }
                
                dogs_summary[dog_key]['meals'] += 1
                dogs_summary[dog_key]['grams_sum'] += log.grams or 0
                dogs_summary[dog_key]['water_sum_ml'] += log.water_ml or 0
                
                bcs_numeric = get_bcs_numeric(log.body_condition)
                if bcs_numeric:
                    dogs_summary[dog_key]['bcs_values'].append(bcs_numeric)
            
            pdf_data['table'] = []
            for dog_data in dogs_summary.values():
                avg_bcs = sum(dog_data['bcs_values']) / len(dog_data['bcs_values']) if dog_data['bcs_values'] else None
                pdf_data['table'].append({
                    'dog_name': dog_data['dog_name'],
                    'meals': dog_data['meals'],
                    'grams_sum': dog_data['grams_sum'],
                    'water_sum_ml': dog_data['water_sum_ml'],
                    'bcs_avg': round(avg_bcs, 1) if avg_bcs else None
                })
        
        # Generate title based on range type
        range_display = format_date_range_for_display(date_from, date_to, range_type, "ar")
        title = f"تقرير التغذية الموحد - {range_display}"
        
        # Use existing PDF generation function
        _generate_feeding_pdf(title, pdf_data, filepath)
        
        # Serve the PDF file directly for download
        response = send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # Add caching headers
        response.cache_control.max_age = 60
        response.cache_control.private = True
        response.headers['Vary'] = 'Cookie, Authorization'
        return response
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating unified feeding PDF: {str(e)}")
        return jsonify({'error': f'خطأ في إنشاء ملف PDF: {str(e)}'}), 500