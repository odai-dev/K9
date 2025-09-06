"""
Data API endpoints for trainer daily report dropdowns
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from k9.models.models import Project, Employee, Dog, EmployeeRole
from app import db
from k9.utils.permission_decorators import require_sub_permission

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
    """Get list of dogs for dropdown, optionally filtered by project"""
    try:
        # Get optional project_id parameter
        project_id = request.args.get('project_id')
        
        if project_id:
            # Filter dogs by specific project
            from k9.models.models import project_dog_assignment
            dogs = db.session.query(Dog).join(
                project_dog_assignment
            ).filter(
                Dog.current_status.in_(['ACTIVE', 'TRAINING']),
                project_dog_assignment.c.project_id == project_id
            ).all()
        else:
            # No project filter - apply role-based filtering
            if current_user.role.value == "GENERAL_ADMIN":
                dogs = db.session.query(Dog).filter(
                    Dog.current_status.in_(['ACTIVE', 'TRAINING'])
                ).all()
            else:
                # PROJECT_MANAGER - get dogs assigned to their projects
                from k9.models.models import project_dog_assignment
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

@bp.route('/api/dogs/accessible')
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', 'VIEW')
def get_accessible_dogs():
    """Get list of accessible dogs and projects for breeding forms"""
    try:
        # GENERAL_ADMIN sees all dogs, PROJECT_MANAGER sees assigned dogs
        if current_user.role.value == "GENERAL_ADMIN":
            dogs = db.session.query(Dog).filter(
                Dog.current_status.in_(['ACTIVE', 'TRAINING'])
            ).all()
            projects = db.session.query(Project).filter(
                Project.status.in_(['PLANNED', 'ACTIVE'])
            ).all()
        else:
            # PROJECT_MANAGER - get dogs assigned to their projects
            from k9.models.models import project_dog_assignment
            dogs = db.session.query(Dog).join(
                project_dog_assignment
            ).join(Project).filter(
                Dog.current_status.in_(['ACTIVE', 'TRAINING']),
                Project.manager_id == current_user.id
            ).all()
            
            # Get assigned projects
            projects = db.session.query(Project).filter(
                Project.status.in_(['PLANNED', 'ACTIVE']),
                Project.manager_id == current_user.id
            ).all()
        
        # Get project assignments for dogs
        dog_projects = {}
        if dogs:
            from k9.models.models import project_dog_assignment
            assignments = db.session.query(project_dog_assignment).all()
            for assignment in assignments:
                if assignment.dog_id not in dog_projects:
                    dog_projects[assignment.dog_id] = []
                dog_projects[assignment.dog_id].append(assignment.project_id)

        return jsonify({
            'dogs': [{
                'id': str(dog.id),
                'name': dog.name,
                'code': dog.code,
                'project_id': str(dog_projects.get(dog.id, [None])[0]) if dog_projects.get(dog.id) else None,
                'project_name': next((p.name for p in projects if str(p.id) == str(dog_projects.get(dog.id, [None])[0])), None) if dog_projects.get(dog.id) else None
            } for dog in dogs],
            'projects': [{
                'id': str(project.id),
                'name': project.name,
                'code': project.code
            } for project in projects]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500