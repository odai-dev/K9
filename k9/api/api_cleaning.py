"""
API endpoints for Cleaning Log management
Provides CRUD operations and listing functionality
"""
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from k9.models.models import (CleaningLog, Project, Dog, Employee, User, UserRole, ProjectStatus)
from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs, log_audit
from datetime import datetime, date, time, timedelta
from sqlalchemy import func, and_, or_
from k9.utils.permission_decorators import require_permission
import json
import re

# Create blueprint
bp = Blueprint('api_cleaning', __name__)

# Text sanitization function
def sanitize_text(text):
    """Sanitize text to prevent encoding issues with PostgreSQL"""
    if not text:
        return text
    
    try:
        # Convert to string if not already
        text_str = str(text)
        
        # Remove or replace problematic characters
        # Remove null bytes
        text_str = text_str.replace('\x00', '')
        
        # Ensure valid UTF-8 encoding
        text_str = text_str.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Remove any remaining control characters except newlines and tabs
        text_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text_str)
        
        return text_str
    except Exception as e:
        print(f"Error sanitizing text: {e}")
        return str(text) if text else ''

@bp.route('/api/breeding/cleaning/list')
@login_required
@require_permission('cleaning:view')
def list_cleaning_logs():
    """List cleaning logs with filters and KPIs"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        project_id = request.args.get('project_id')
        dog_id = request.args.get('dog_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Base query with joins (LEFT JOIN for project to handle NULL project_id)
        query = CleaningLog.query.outerjoin(Project).join(Dog, CleaningLog.dog_id == Dog.id)
        
        # Apply user access restrictions
        if current_user.role == UserRole.GENERAL_ADMIN:
            # Admin can see all logs
            pass
        else:
            # PROJECT_MANAGER can only see logs from assigned projects
            assigned_projects = get_user_assigned_projects(current_user)
            if not assigned_projects:
                return jsonify({
                    'items': [],
                    'pagination': {'page': 1, 'pages': 1, 'per_page': per_page, 'total': 0, 'has_prev': False, 'has_next': False},
                    'kpis': {'total': 0, 'cleaned_yes': 0, 'washed_yes': 0, 'disinfected_yes': 0, 'group_disinfections': 0, 
                            'due_wash_count': 0, 'overdue_wash_count': 0, 'due_disinfect_count': 0, 'overdue_disinfect_count': 0}
                })
            
            project_ids = [p.id for p in assigned_projects]
            # PROJECT_MANAGER only sees logs from assigned projects (not logs without projects)
            query = query.filter(CleaningLog.project_id.in_(project_ids))
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                # Filter for records without project assignment
                query = query.filter(CleaningLog.project_id.is_(None))
            else:
                query = query.filter(CleaningLog.project_id == project_id)
        
        if dog_id:
            query = query.filter(CleaningLog.dog_id == dog_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(CleaningLog.date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(CleaningLog.date <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        
        # Calculate KPIs on filtered data
        kpis = calculate_cleaning_kpis(query, date_to)
        
        # Order by date and time descending
        query = query.order_by(CleaningLog.date.desc(), CleaningLog.time.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format results
        items = []
        for log in pagination.items:
            items.append({
                'id': str(log.id),
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M'),
                'project_name': log.project.name if log.project else '',
                'dog_name': log.dog.name if log.dog else '',
                'area_type': log.area_type,
                'cage_house_number': log.cage_house_number,
                'alternate_place': log.alternate_place,
                'cleaned_house': log.cleaned_house,
                'washed_house': log.washed_house,
                'disinfected_house': log.disinfected_house,
                'group_disinfection': log.group_disinfection,
                'group_description': log.group_description,
                'materials_used': log.materials_used,
                'notes': log.notes,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'items': items,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            },
            'kpis': kpis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/breeding/cleaning', methods=['POST'])
@login_required
@require_permission('cleaning:create')
def create_cleaning_log():
    """Create new cleaning log"""
    try:
        data = request.get_json()
        
        # Validate required fields (project_id is optional)
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if not data.get('project_id'):
                return jsonify({'error': 'Project ID is required for project managers'}), 400
            
            assigned_projects = get_user_assigned_projects(current_user)
            project_ids = [str(p.id) for p in assigned_projects]
            if str(data['project_id']) not in project_ids:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        # Verify project exists (if provided)
        project = None
        if data.get('project_id'):
            project = Project.query.get(data['project_id'])
            if not project:
                return jsonify({'error': 'Project not found'}), 404
        
        dog = Dog.query.get(data['dog_id'])
        if not dog:
            return jsonify({'error': 'Dog not found'}), 404
        
        # Parse date and time
        try:
            log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            log_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
        
        # Validate group disinfection
        if data.get('group_disinfection') == u'نعم' and not data.get('group_description'):
            return jsonify({'error': 'Group description is required when group disinfection is Yes'}), 400
        
        # Validate at least one action
        actions = [data.get('cleaned_house'), data.get('washed_house'), data.get('disinfected_house'), data.get('group_disinfection')]
        has_materials = data.get('materials_used') and len(data.get('materials_used', [])) > 0
        has_notes = data.get('notes') and data.get('notes').strip()
        
        if not any(action == 'نعم' for action in actions) and not has_materials and not has_notes:
            return jsonify({'error': 'At least one action, materials, or notes must be provided'}), 400
        
        # Check for duplicate entry
        project_id_value = data['project_id'] if data.get('project_id') else None
        existing = CleaningLog.query.filter(
            CleaningLog.project_id == project_id_value,
            CleaningLog.dog_id == data['dog_id'],
            CleaningLog.date == log_date,
            CleaningLog.time == log_time
        ).first()
        
        if existing:
            return jsonify({'error': 'A cleaning log already exists for this dog, project, date, and time'}), 400
        
        # Create new log with sanitized text fields
        cleaning_log = CleaningLog()
        cleaning_log.project_id = data['project_id'] if data.get('project_id') else None
        cleaning_log.dog_id = data['dog_id']
        cleaning_log.date = log_date
        cleaning_log.time = log_time
        cleaning_log.area_type = sanitize_text(data.get('area_type'))
        cleaning_log.cage_house_number = sanitize_text(data.get('cage_house_number'))
        cleaning_log.alternate_place = sanitize_text(data.get('alternate_place'))
        cleaning_log.cleaned_house = sanitize_text(data.get('cleaned_house'))
        cleaning_log.washed_house = sanitize_text(data.get('washed_house'))
        cleaning_log.disinfected_house = sanitize_text(data.get('disinfected_house'))
        cleaning_log.group_disinfection = sanitize_text(data.get('group_disinfection'))
        cleaning_log.group_description = sanitize_text(data.get('group_description'))
        
        # Sanitize materials_used if it's a list
        materials = data.get('materials_used')
        if materials and isinstance(materials, list):
            sanitized_materials = []
            for material in materials:
                if isinstance(material, dict):
                    sanitized_material = {
                        'name': sanitize_text(material.get('name')),
                        'qty': sanitize_text(material.get('qty'))
                    }
                    sanitized_materials.append(sanitized_material)
            cleaning_log.materials_used = sanitized_materials
        else:
            cleaning_log.materials_used = materials
            
        cleaning_log.notes = sanitize_text(data.get('notes'))
        cleaning_log.created_by_user_id = current_user.id
        
        db.session.add(cleaning_log)
        db.session.commit()
        
        # Log audit
        log_audit(current_user.id, 'CREATE', 'CleaningLog', str(cleaning_log.id), f'Created cleaning log for dog {dog.name}')
        
        return jsonify({
            'message': 'Cleaning log created successfully',
            'id': str(cleaning_log.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/breeding/cleaning/<log_id>', methods=['PUT'])
@login_required
@require_permission('cleaning:edit')
def update_cleaning_log(log_id):
    """Update existing cleaning log"""
    try:
        cleaning_log = CleaningLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if cleaning_log.project not in assigned_projects:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        data = request.get_json()
        
        # Validate required fields (project_id is optional)
        required_fields = ['date', 'time', 'dog_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse date and time
        try:
            log_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            log_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError as e:
            return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
        
        # Validate group disinfection
        if data.get('group_disinfection') == u'نعم' and not data.get('group_description'):
            return jsonify({'error': 'Group description is required when group disinfection is Yes'}), 400
        
        # Check for duplicate entry (excluding current record)
        project_id_value = data['project_id'] if data.get('project_id') else None
        existing = CleaningLog.query.filter(
            and_(
                CleaningLog.project_id == project_id_value,
                CleaningLog.dog_id == data['dog_id'],
                CleaningLog.date == log_date,
                CleaningLog.time == log_time,
                CleaningLog.id != log_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'A cleaning log already exists for this dog, project, date, and time'}), 400
        
        # Update log
        cleaning_log.project_id = data['project_id'] if data.get('project_id') else None
        cleaning_log.dog_id = data['dog_id']
        cleaning_log.date = log_date
        cleaning_log.time = log_time
        cleaning_log.area_type = data.get('area_type')
        cleaning_log.cage_house_number = data.get('cage_house_number')
        cleaning_log.alternate_place = data.get('alternate_place')
        cleaning_log.cleaned_house = data.get('cleaned_house')
        cleaning_log.washed_house = data.get('washed_house')
        cleaning_log.disinfected_house = data.get('disinfected_house')
        cleaning_log.group_disinfection = data.get('group_disinfection')
        cleaning_log.group_description = data.get('group_description')
        cleaning_log.materials_used = data.get('materials_used')
        cleaning_log.notes = data.get('notes')
        cleaning_log.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log audit
        log_audit('EDIT', 'CleaningLog', str(cleaning_log.id), f'Updated cleaning log for dog {cleaning_log.dog.name}')
        
        return jsonify({'message': 'Cleaning log updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/breeding/cleaning/<log_id>', methods=['DELETE'])
@login_required
@require_permission('cleaning:delete')
def delete_cleaning_log(log_id):
    """Delete cleaning log"""
    try:
        cleaning_log = CleaningLog.query.get_or_404(log_id)
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            assigned_projects = get_user_assigned_projects(current_user)
            if cleaning_log.project not in assigned_projects:
                return jsonify({'error': 'Access denied to this project'}), 403
        
        dog_name = cleaning_log.dog.name if cleaning_log.dog else 'Unknown'
        
        db.session.delete(cleaning_log)
        db.session.commit()
        
        # Log audit
        log_audit('DELETE', 'CleaningLog', str(log_id), f'Deleted cleaning log for dog {dog_name}')
        
        return jsonify({'message': 'Cleaning log deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def calculate_cleaning_kpis(query, date_to_str=None):
    """Calculate KPIs for cleaning logs"""
    try:
        # Basic counts
        total = query.count()
        
        # Use Unicode strings explicitly for Arabic text
        yes_value = 'نعم'
        
        cleaned_yes = query.filter(CleaningLog.cleaned_house == yes_value).count()
        washed_yes = query.filter(CleaningLog.washed_house == yes_value).count()
        disinfected_yes = query.filter(CleaningLog.disinfected_house == yes_value).count()
        group_disinfections = query.filter(CleaningLog.group_disinfection == yes_value).count()
        
        # Cadence calculations
        reference_date = date.today()
        if date_to_str:
            try:
                reference_date = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except:
                pass
        
        # Get unique dogs from the query scope
        dog_ids = [row[0] for row in query.with_entities(CleaningLog.dog_id).distinct().all()]
        
        due_wash_count = 0
        overdue_wash_count = 0
        due_disinfect_count = 0
        overdue_disinfect_count = 0
        
        for dog_id in dog_ids:
            # Find last wash for this dog
            last_wash = CleaningLog.query.filter(
                and_(
                    CleaningLog.dog_id == dog_id,
                    CleaningLog.washed_house == yes_value
                )
            ).order_by(CleaningLog.date.desc(), CleaningLog.time.desc()).first()
            
            if last_wash:
                days_since_wash = (reference_date - last_wash.date).days
                if days_since_wash >= 3:
                    due_wash_count += 1
                if days_since_wash > 3:
                    overdue_wash_count += 1
            else:
                # Never washed - count as overdue
                overdue_wash_count += 1
            
            # Find last disinfection for this dog
            last_disinfect = CleaningLog.query.filter(
                and_(
                    CleaningLog.dog_id == dog_id,
                    CleaningLog.disinfected_house == yes_value
                )
            ).order_by(CleaningLog.date.desc(), CleaningLog.time.desc()).first()
            
            if last_disinfect:
                days_since_disinfect = (reference_date - last_disinfect.date).days
                if days_since_disinfect >= 7:
                    due_disinfect_count += 1
                if days_since_disinfect > 7:
                    overdue_disinfect_count += 1
            else:
                # Never disinfected - count as overdue
                overdue_disinfect_count += 1
        
        return {
            'total': total,
            'cleaned_yes': cleaned_yes,
            'washed_yes': washed_yes,
            'disinfected_yes': disinfected_yes,
            'group_disinfections': group_disinfections,
            'due_wash_count': due_wash_count,
            'overdue_wash_count': overdue_wash_count,
            'due_disinfect_count': due_disinfect_count,
            'overdue_disinfect_count': overdue_disinfect_count
        }
        
    except Exception as e:
        import traceback
        print(f"Error calculating KPIs: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'total': 0,
            'cleaned_yes': 0,
            'washed_yes': 0,
            'disinfected_yes': 0,
            'group_disinfections': 0,
            'due_wash_count': 0,
            'overdue_wash_count': 0,
            'due_disinfect_count': 0,
            'overdue_disinfect_count': 0
        }