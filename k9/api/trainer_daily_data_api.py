"""
Data API endpoints for trainer daily report dropdowns
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from k9.models.models import Project, Employee, Dog, EmployeeRole
from app import db
from k9.utils.permissions_new import has_permission, require_permission

bp = Blueprint('trainer_daily_data_api', __name__)


@bp.route('/api/projects')
@login_required
def get_projects():
    """Get list of projects for dropdown"""
    if not has_permission("projects.view"):
        return jsonify({'error': 'Unauthorized'}), 403
    
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
@require_permission('employees.view')
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
    if not has_permission("dogs.view"):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from k9.models.models import project_dog_assignment, ProjectAssignment, DogStatus, User, UserRole
        
        # Get optional project_id parameter
        project_id = request.args.get('project_id')
        
        if project_id:
            # Filter dogs by specific project using multiple methods
            all_dogs_set = {}
            
            # Method 1: Dogs assigned via ProjectAssignment model (recommended)
            project_assignments = ProjectAssignment.query.filter_by(
                project_id=project_id,
                is_active=True
            ).filter(
                ProjectAssignment.dog_id.isnot(None)
            ).all()
            assignment_dog_ids = [pa.dog_id for pa in project_assignments]
            if assignment_dog_ids:
                for dog in Dog.query.filter(Dog.id.in_(assignment_dog_ids)).all():
                    if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                        all_dogs_set[str(dog.id)] = dog
            
            # Method 2: Dogs assigned via legacy many-to-many relationship
            legacy_dogs = db.session.query(Dog).join(
                project_dog_assignment
            ).filter(
                project_dog_assignment.c.project_id == project_id
            ).all()
            for dog in legacy_dogs:
                if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                    all_dogs_set[str(dog.id)] = dog
            
            # Method 3: Dogs assigned to handlers who are in this project
            handlers_in_project = User.query.filter_by(
                role=UserRole.HANDLER,
                project_id=project_id
            ).all()
            handler_ids = [h.id for h in handlers_in_project]
            if handler_ids:
                handler_dogs = Dog.query.filter(
                    Dog.assigned_to_user_id.in_(handler_ids)
                ).all()
                for dog in handler_dogs:
                    if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                        all_dogs_set[str(dog.id)] = dog
            
            # Method 4: Include unassigned dogs as available options
            unassigned_dogs = Dog.query.filter(
                Dog.assigned_to_user_id.is_(None)
            ).all()
            for dog in unassigned_dogs:
                if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                    all_dogs_set[str(dog.id)] = dog
            
            dogs = list(all_dogs_set.values())
        else:
            # No project filter - apply role-based filtering
            if current_user.role.value == "GENERAL_ADMIN":
                dogs = db.session.query(Dog).filter(
                    Dog.current_status.in_([DogStatus.ACTIVE, DogStatus.TRAINING])
                ).all()
            else:
                # PROJECT_MANAGER - get dogs assigned to their projects via multiple methods
                all_dogs_set = {}
                
                # Get PM's project IDs
                pm_projects = Project.query.filter_by(manager_id=current_user.id).all()
                pm_project_ids = [p.id for p in pm_projects]
                
                if pm_project_ids:
                    # Method 1: Via ProjectAssignment
                    for proj_id in pm_project_ids:
                        project_assignments = ProjectAssignment.query.filter_by(
                            project_id=proj_id,
                            is_active=True
                        ).filter(
                            ProjectAssignment.dog_id.isnot(None)
                        ).all()
                        for pa in project_assignments:
                            dog = Dog.query.get(pa.dog_id)
                            if dog and dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                                all_dogs_set[str(dog.id)] = dog
                    
                    # Method 2: Via legacy many-to-many
                    legacy_dogs = db.session.query(Dog).join(
                        project_dog_assignment
                    ).filter(
                        project_dog_assignment.c.project_id.in_(pm_project_ids)
                    ).all()
                    for dog in legacy_dogs:
                        if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                            all_dogs_set[str(dog.id)] = dog
                
                dogs = list(all_dogs_set.values())
        
        # Return array directly for backwards compatibility with JS files
        return jsonify([{
            'id': str(dog.id),
            'name': dog.name,
            'code': dog.code
        } for dog in dogs])
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/dogs/accessible')
@login_required
@require_permission('breeding.excretion')
def get_accessible_dogs():
    """Get list of accessible dogs and projects for breeding forms"""
    try:
        from k9.models.models import project_dog_assignment, ProjectAssignment, DogStatus, User, UserRole
        
        # GENERAL_ADMIN sees all dogs, PROJECT_MANAGER sees assigned dogs
        if current_user.role.value == "GENERAL_ADMIN":
            dogs = db.session.query(Dog).filter(
                Dog.current_status.in_([DogStatus.ACTIVE, DogStatus.TRAINING])
            ).all()
            projects = db.session.query(Project).filter(
                Project.status.in_(['PLANNED', 'ACTIVE'])
            ).all()
        else:
            # PROJECT_MANAGER - get dogs assigned to their projects via multiple methods
            all_dogs_set = {}
            
            # Get PM's project IDs
            pm_projects = Project.query.filter_by(manager_id=current_user.id).all()
            pm_project_ids = [p.id for p in pm_projects]
            
            if pm_project_ids:
                # Method 1: Via ProjectAssignment
                for proj_id in pm_project_ids:
                    project_assignments = ProjectAssignment.query.filter_by(
                        project_id=proj_id,
                        is_active=True
                    ).filter(
                        ProjectAssignment.dog_id.isnot(None)
                    ).all()
                    for pa in project_assignments:
                        dog = Dog.query.get(pa.dog_id)
                        if dog and dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                            all_dogs_set[str(dog.id)] = dog
                
                # Method 2: Via legacy many-to-many
                legacy_dogs = db.session.query(Dog).join(
                    project_dog_assignment
                ).filter(
                    project_dog_assignment.c.project_id.in_(pm_project_ids)
                ).all()
                for dog in legacy_dogs:
                    if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                        all_dogs_set[str(dog.id)] = dog
                
                # Method 3: Dogs assigned to handlers who are in these projects
                for proj_id in pm_project_ids:
                    handlers_in_project = User.query.filter_by(
                        role=UserRole.HANDLER,
                        project_id=proj_id
                    ).all()
                    handler_ids = [h.id for h in handlers_in_project]
                    if handler_ids:
                        handler_dogs = Dog.query.filter(
                            Dog.assigned_to_user_id.in_(handler_ids)
                        ).all()
                        for dog in handler_dogs:
                            if dog.current_status in [DogStatus.ACTIVE, DogStatus.TRAINING]:
                                all_dogs_set[str(dog.id)] = dog
            
            dogs = list(all_dogs_set.values())
            projects = pm_projects
        
        # Get project assignments for dogs using both methods
        dog_projects = {}
        if dogs:
            # From ProjectAssignment
            for dog in dogs:
                assignments = ProjectAssignment.query.filter_by(
                    dog_id=dog.id,
                    is_active=True
                ).all()
                if assignments:
                    dog_projects[dog.id] = [a.project_id for a in assignments]
            
            # From legacy many-to-many
            legacy_assignments = db.session.query(project_dog_assignment).all()
            for assignment in legacy_assignments:
                if assignment.dog_id not in dog_projects:
                    dog_projects[assignment.dog_id] = []
                if assignment.project_id not in dog_projects.get(assignment.dog_id, []):
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