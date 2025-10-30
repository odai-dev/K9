"""
Project Manager Scoping Utilities
Provides intelligent data filtering that works for both PM (project-scoped) and GENERAL_ADMIN (full access)
"""

from flask_login import current_user
from k9.models.models import (
    UserRole, Project, Dog, Employee, ProjectDog, ProjectAssignment,
    VeterinaryVisit, TrainingSession, ProductionCycle,
    HeatCycle, MatingRecord, PregnancyRecord, DeliveryRecord, PuppyRecord,
    FeedingLog, DailyCheckupLog, ExcretionLog, GroomingLog, CleaningLog,
    BreedingTrainingActivity, CaretakerDailyLog, DewormingLog
)
from sqlalchemy import and_


def get_pm_project(user=None):
    """Get the PM's assigned project or None if not a PM or not assigned"""
    if user is None:
        user = current_user
    
    if not hasattr(user, 'is_authenticated') or not user.is_authenticated or user.role != UserRole.PROJECT_MANAGER:
        return None
    
    # Find project where user is the manager (direct User FK)
    project = Project.query.filter_by(manager_id=user.id).first()
    
    # If not found, check via Employee link (project_manager_id)
    if not project:
        employee = Employee.query.filter_by(user_account_id=user.id).first()
        if employee:
            project = Project.query.filter_by(project_manager_id=employee.id).first()
    
    return project


def is_pm(user=None):
    """Check if user is a Project Manager"""
    if user is None:
        user = current_user
    return hasattr(user, 'is_authenticated') and user.is_authenticated and user.role == UserRole.PROJECT_MANAGER


def is_admin(user=None):
    """Check if user is a General Admin"""
    if user is None:
        user = current_user
    return hasattr(user, 'is_authenticated') and user.is_authenticated and user.role == UserRole.GENERAL_ADMIN


def get_scoped_dogs(user=None):
    """
    Get dogs accessible to user
    - GENERAL_ADMIN: All dogs
    - PROJECT_MANAGER: Only dogs assigned to their project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return Dog.query.all()
    
    if is_pm(user):
        project = get_pm_project(user)
        if not project:
            return []
        
        # Get dog IDs from ProjectDog table
        project_dogs = ProjectDog.query.filter_by(
            project_id=project.id,
            is_active=True
        ).all()
        dog_ids = [pd.dog_id for pd in project_dogs]
        
        if not dog_ids:
            return []
        
        return Dog.query.filter(Dog.id.in_(dog_ids)).all()
    
    return []


def get_scoped_dog_ids(user=None):
    """
    Get dog IDs accessible to user
    - GENERAL_ADMIN: All dog IDs
    - PROJECT_MANAGER: Only dog IDs assigned to their project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return [dog.id for dog in Dog.query.all()]
    
    if is_pm(user):
        project = get_pm_project(user)
        if not project:
            return []
        
        # Get dog IDs from ProjectDog table
        project_dogs = ProjectDog.query.filter_by(
            project_id=project.id,
            is_active=True
        ).all()
        return [pd.dog_id for pd in project_dogs]
    
    return []


def get_scoped_projects(user=None):
    """
    Get projects accessible to user
    - GENERAL_ADMIN: All projects
    - PROJECT_MANAGER: Only their assigned project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return Project.query.all()
    
    if is_pm(user):
        project = get_pm_project(user)
        return [project] if project else []
    
    return []


def get_scoped_employees(user=None):
    """
    Get employees accessible to user
    - GENERAL_ADMIN: All employees
    - PROJECT_MANAGER: Only employees assigned to their project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return Employee.query.all()
    
    if is_pm(user):
        project = get_pm_project(user)
        if not project:
            return []
        
        # Get employees assigned to this project via ProjectAssignment model
        from app import db
        
        # Query active employee assignments for this project
        employee_assignments = ProjectAssignment.query.filter_by(
            project_id=project.id,
            is_active=True
        ).filter(
            ProjectAssignment.employee_id.isnot(None)
        ).all()
        
        employee_ids = [assignment.employee_id for assignment in employee_assignments]
        
        if not employee_ids:
            return []
        
        # Return the actual Employee objects
        employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        return employees
    
    return []


def apply_project_scope(query, model, user=None):
    """
    Apply project scoping to a query
    - GENERAL_ADMIN: Return query unchanged (all records)
    - PROJECT_MANAGER: Filter by project_id or dog_id based on model
    
    Args:
        query: SQLAlchemy query object
        model: The model class being queried
        user: User object (defaults to current_user)
        
    Returns:
        Filtered query
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return query
    
    if is_pm(user):
        project = get_pm_project(user)
        if not project:
            # Return empty query
            return query.filter(False)
        
        # Models with direct project_id field
        if hasattr(model, 'project_id'):
            return query.filter(model.project_id == project.id)
        
        # Models linked via dog_id
        if hasattr(model, 'dog_id'):
            dog_ids = get_scoped_dog_ids(user)
            if not dog_ids:
                return query.filter(False)
            return query.filter(model.dog_id.in_(dog_ids))
        
        # Default: return empty
        return query.filter(False)
    
    return query.filter(False)


def get_auto_project_id(user=None):
    """
    Get project_id to auto-inject for PM create operations
    - GENERAL_ADMIN: None (they choose manually)
    - PROJECT_MANAGER: Their assigned project ID
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return None
    
    if is_pm(user):
        project = get_pm_project(user)
        return project.id if project else None
    
    return None


def can_access_project(project_id, user=None):
    """
    Check if current user can access a specific project
    - GENERAL_ADMIN: Can access any project
    - PROJECT_MANAGER: Can only access their assigned project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return True
    
    if is_pm(user):
        project = get_pm_project(user)
        return project and str(project.id) == str(project_id)
    
    return False


def can_access_dog(dog_id, user=None):
    """
    Check if current user can access a specific dog
    - GENERAL_ADMIN: Can access any dog
    - PROJECT_MANAGER: Can only access dogs in their project
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return True
    
    if is_pm(user):
        accessible_dog_ids = get_scoped_dog_ids(user)
        return str(dog_id) in [str(d_id) for d_id in accessible_dog_ids]
    
    return False


def validate_access_or_403(dog_id=None, project_id=None, user=None):
    """
    Validate access to dog or project, abort with 403 if unauthorized
    Use this in routes to enforce access control
    """
    from flask import abort
    
    if dog_id and not can_access_dog(dog_id, user):
        abort(403)
    
    if project_id and not can_access_project(project_id, user):
        abort(403)


def inject_pm_context(record, user=None):
    """
    Auto-inject project_id and created_by_user_id for PM-created records
    - GENERAL_ADMIN: No auto-injection (they set manually)
    - PROJECT_MANAGER: Auto-inject their project_id and user_id
    
    Args:
        record: Database model instance (must have project_id and/or created_by_user_id fields)
    
    Returns:
        Modified record
    """
    if user is None:
        user = current_user
        
    if is_pm(user):
        project = get_pm_project(user)
        
        # Auto-inject project_id if field exists and not already set
        if hasattr(record, 'project_id') and not record.project_id:
            if project:
                record.project_id = project.id
        
        # Auto-inject created_by_user_id if field exists and not already set
        if hasattr(record, 'created_by_user_id') and not record.created_by_user_id:
            record.created_by_user_id = user.id
    
    return record


def get_form_project_id(form_data=None, user=None):
    """
    Get project_id from form data or auto-inject for PMs
    - GENERAL_ADMIN: Use form data (they choose from dropdown)
    - PROJECT_MANAGER: Auto-return their project_id (ignore form)
    
    Args:
        form_data: Flask request.form or dict with 'project_id' key
    
    Returns:
        project_id (UUID string or None)
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        # Admin chooses from dropdown
        if form_data and 'project_id' in form_data:
            project_id = form_data.get('project_id')
            # Handle empty strings or "no_project"
            if project_id and project_id not in ['', 'null', 'no_project']:
                return project_id
        return None
    
    if is_pm(user):
        # PM gets their project automatically
        project = get_pm_project(user)
        return project.id if project else None
    
    return None


def filter_form_choices(choices, field_type='project', user=None):
    """
    Filter dropdown choices based on user role
    - GENERAL_ADMIN: See all choices
    - PROJECT_MANAGER: See only their project/dogs/employees
    
    Args:
        choices: List of (value, label) tuples or model objects
        field_type: 'project', 'dog', or 'employee'
    
    Returns:
        Filtered choices
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return choices
    
    if is_pm(user):
        if field_type == 'project':
            project = get_pm_project(user)
            if not project:
                return []
            # Filter to only PM's project
            if isinstance(choices[0] if choices else None, tuple):
                return [(v, l) for v, l in choices if str(v) == str(project.id)]
            else:
                return [c for c in choices if str(c.id) == str(project.id)]
        
        elif field_type == 'dog':
            dog_ids = get_scoped_dog_ids(user)
            dog_id_strs = [str(d_id) for d_id in dog_ids]
            if isinstance(choices[0] if choices else None, tuple):
                return [(v, l) for v, l in choices if str(v) in dog_id_strs]
            else:
                return [c for c in choices if str(c.id) in dog_id_strs]
        
        elif field_type == 'employee':
            employees = get_scoped_employees(user)
            emp_id_strs = [str(e.id) for e in employees]
            if isinstance(choices[0] if choices else None, tuple):
                return [(v, l) for v, l in choices if str(v) in emp_id_strs]
            else:
                return [c for c in choices if str(c.id) in emp_id_strs]
    
    return []
