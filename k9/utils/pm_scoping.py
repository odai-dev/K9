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
    """Get the PM's assigned project or None if not a PM or not assigned
    
    Now supports GENERAL_ADMIN in PM mode - they should be assigned to a project
    just like regular PROJECT_MANAGERs.
    """
    if user is None:
        user = current_user
    
    # Check if user should be treated as PM (regular PM or GENERAL_ADMIN in PM mode)
    if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return None
    
    # GENERAL_ADMIN in PM mode should be treated like PROJECT_MANAGER
    from flask import session
    if user.role == UserRole.GENERAL_ADMIN:
        admin_mode = session.get('admin_mode', 'general_admin')
        if admin_mode != 'project_manager':
            return None  # Not in PM mode, so no project scoping
    elif user.role != UserRole.PROJECT_MANAGER:
        return None  # Not a PM and not an admin in PM mode
    
    # Find project where user is the manager (direct User FK)
    project = Project.query.filter_by(manager_id=user.id).first()
    
    # If not found, check via Employee link (project_manager_id)
    if not project:
        employee = user.employee
        if employee:
            project = Project.query.filter_by(project_manager_id=employee.id).first()
    
    return project


def is_pm(user=None):
    """Check if user should be treated as a Project Manager
    
    Returns True for:
    - Regular PROJECT_MANAGER users
    - GENERAL_ADMIN users in PM mode (session['admin_mode'] == 'project_manager')
    """
    if user is None:
        user = current_user
    
    if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Regular PROJECT_MANAGER
    if user.role == UserRole.PROJECT_MANAGER:
        return True
    
    # GENERAL_ADMIN in PM mode
    if user.role == UserRole.GENERAL_ADMIN:
        from flask import session
        admin_mode = session.get('admin_mode', 'general_admin')
        return admin_mode == 'project_manager'
    
    return False


def is_admin(user=None):
    """Check if user should be treated as having full administrative access
    
    Returns True ONLY for:
    - GENERAL_ADMIN users in general admin mode (NOT in PM mode)
    
    PROJECT_MANAGER users should NOT have full admin access and must use granular permissions.
    When GENERAL_ADMIN is in PM mode, they should be treated as PROJECT_MANAGER.
    """
    if user is None:
        user = current_user
    
    if not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    # Only GENERAL_ADMIN can have full admin access
    if user.role != UserRole.GENERAL_ADMIN:
        return False
    
    # Check if in PM mode - if so, not acting as admin
    from flask import session
    admin_mode = session.get('admin_mode', 'general_admin')
    return admin_mode == 'general_admin'


def get_scoped_dogs(user=None):
    """
    Get dogs accessible to user
    - GENERAL_ADMIN: All dogs
    - PROJECT_MANAGER: Dogs assigned to their project OR directly assigned to user
    
    Checks THREE assignment methods:
    1. ProjectDog table (old project-dog assignment)
    2. ProjectAssignment table (NEW unified assignment)
    3. assigned_to_user_id field (direct user assignment)
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return Dog.query.all()
    
    if is_pm(user):
        project = get_pm_project(user)
        if not project:
            # Fallback to direct assignments only
            directly_assigned = Dog.query.filter_by(assigned_to_user_id=user.id).all()
            return list(set(directly_assigned))
        
        # Method 1: ProjectDog table (old project-dog assignment)
        project_dogs_old = ProjectDog.query.filter_by(
            project_id=project.id,
            is_active=True
        ).all()
        dog_ids_old = [pd.dog_id for pd in project_dogs_old]
        
        # Method 2: ProjectAssignment table (NEW unified assignment - CRITICAL!)
        project_dogs_new = ProjectAssignment.query.filter_by(
            project_id=project.id,
            is_active=True
        ).filter(
            ProjectAssignment.dog_id.isnot(None)
        ).all()
        dog_ids_new = [pa.dog_id for pa in project_dogs_new]
        
        # Method 3: Direct user assignment
        directly_assigned = Dog.query.filter_by(assigned_to_user_id=user.id).all()
        
        # Merge all dog IDs from project assignments and query
        all_dog_ids = list(set(dog_ids_old + dog_ids_new))
        project_dogs = Dog.query.filter(Dog.id.in_(all_dog_ids)).all() if all_dog_ids else []
        
        # Combine with direct assignments and deduplicate
        return list(set(project_dogs + directly_assigned))
    
    return []


def get_scoped_dog_ids(user=None):
    """
    Get dog IDs accessible to user
    - GENERAL_ADMIN: All dog IDs
    - PROJECT_MANAGER: Dog IDs assigned to their project OR directly assigned to user
    
    Checks THREE assignment methods:
    1. ProjectDog table (old project-dog assignment)
    2. ProjectAssignment table (NEW unified assignment)
    3. assigned_to_user_id field (direct user assignment)
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return [dog.id for dog in Dog.query.all()]
    
    if is_pm(user):
        dog_ids_set = set()
        
        project = get_pm_project(user)
        if project:
            # Method 1: ProjectDog table (old project-dog assignment)
            project_dogs_old = ProjectDog.query.filter_by(
                project_id=project.id,
                is_active=True
            ).all()
            for pd in project_dogs_old:
                dog_ids_set.add(pd.dog_id)
            
            # Method 2: ProjectAssignment table (NEW unified assignment - CRITICAL!)
            project_dogs_new = ProjectAssignment.query.filter_by(
                project_id=project.id,
                is_active=True
            ).filter(
                ProjectAssignment.dog_id.isnot(None)
            ).all()
            for pa in project_dogs_new:
                dog_ids_set.add(pa.dog_id)
        
        # Method 3: Direct user assignment
        directly_assigned_dogs = Dog.query.filter_by(assigned_to_user_id=user.id).all()
        for dog in directly_assigned_dogs:
            dog_ids_set.add(dog.id)
        
        return list(dog_ids_set)
    
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
    - PROJECT_MANAGER: Employees assigned to their project OR directly assigned to user
    """
    if user is None:
        user = current_user
        
    if is_admin(user):
        return Employee.query.all()
    
    if is_pm(user):
        employee_ids_set = set()
        
        # Method 1: Get employees assigned to project via ProjectAssignment model
        project = get_pm_project(user)
        if project:
            from app import db
            
            # Query active employee assignments for this project
            employee_assignments = ProjectAssignment.query.filter_by(
                project_id=project.id,
                is_active=True
            ).filter(
                ProjectAssignment.employee_id.isnot(None)
            ).all()
            
            for assignment in employee_assignments:
                employee_ids_set.add(assignment.employee_id)
        
        # Method 2: Get employees directly assigned to user (legacy direct assignments)
        directly_assigned_employees = Employee.query.filter_by(assigned_to_user_id=user.id).all()
        for employee in directly_assigned_employees:
            employee_ids_set.add(employee.id)
        
        # Fetch all unique employees
        if employee_ids_set:
            return Employee.query.filter(Employee.id.in_(employee_ids_set)).all()
        
        return []
    
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
