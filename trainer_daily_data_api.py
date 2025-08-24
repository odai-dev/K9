"""
Data API endpoints for trainer daily report dropdowns
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Project, Employee, Dog, EmployeeRole
from app import db

bp = Blueprint('trainer_daily_data_api', __name__)


@bp.route('/api/projects')
@login_required
def get_projects():
    """Get list of projects for dropdown"""
    try:
        # GENERAL_ADMIN sees all projects, PROJECT_MANAGER sees assigned projects
        if current_user.role.value == "GENERAL_ADMIN":
            projects = db.session.query(Project).filter(
                Project.status.in_(['PLANNED', 'ACTIVE'])
            ).all()
        else:
            # PROJECT_MANAGER - get assigned projects only
            projects = db.session.query(Project).filter(
                Project.status.in_(['PLANNED', 'ACTIVE']),
                Project.manager_id == current_user.id
            ).all()
        
        return jsonify([{
            'id': str(project.id),
            'name': project.name,
            'code': project.code
        } for project in projects])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/employees')
@login_required  
def get_employees():
    """Get list of employees (trainers) for dropdown"""
    try:
        # Filter by role if provided
        role_filter = None
        if 'role' in request.args:
            role_value = request.args.get('role')
            if role_value == 'TRAINER':
                role_filter = EmployeeRole.TRAINER
        
        query = db.session.query(Employee)
        if role_filter:
            query = query.filter(Employee.role == role_filter)
            
        employees = query.all()
        
        return jsonify([{
            'id': str(employee.id),
            'name': employee.name,
            'full_name': employee.name,
            'role': employee.role.value
        } for employee in employees])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/dogs')
@login_required
def get_dogs():
    """Get list of dogs for dropdown"""
    try:
        # GENERAL_ADMIN sees all dogs, PROJECT_MANAGER sees assigned dogs
        if current_user.role.value == "GENERAL_ADMIN":
            dogs = db.session.query(Dog).filter(
                Dog.current_status.in_(['ACTIVE', 'TRAINING'])
            ).all()
        else:
            # PROJECT_MANAGER - get dogs assigned to their projects
            from models import project_dog_assignment
            dogs = db.session.query(Dog).join(
                project_dog_assignment
            ).join(Project).filter(
                Dog.current_status.in_(['ACTIVE', 'TRAINING']),
                Project.manager_id == current_user.id
            ).all()
        
        return jsonify([{
            'id': str(dog.id),
            'name': dog.name,
            'code': dog.code
        } for dog in dogs])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500