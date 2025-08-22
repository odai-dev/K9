"""
Project validation utilities for enforcing business rules
"""
from models import Project, Employee, ProjectStatus


def validate_project_manager_assignment(employee_id, project=None):
    """
    Validate that a project manager can be assigned to a project.
    Enforces the rule: One project manager can only have one active/planned project at a time.
    
    Args:
        employee_id: Employee ID to validate
        project: Optional Project object (for updates)
    
    Returns:
        tuple: (can_assign: bool, error_message: str)
    """
    # Check if this employee has any existing active/planned projects
    existing_projects_query = Project.query.filter(
        Project.project_manager_id == employee_id,
        Project.status.in_([ProjectStatus.PLANNED, ProjectStatus.ACTIVE])
    )
    
    # Exclude current project if we're updating
    if project:
        existing_projects_query = existing_projects_query.filter(Project.id != project.id)
    
    existing_project = existing_projects_query.first()
    
    if existing_project:
        employee = Employee.query.get(employee_id)
        employee_name = employee.name if employee else "غير معروف"
        return False, f'مسؤول المشروع {employee_name} لديه مشروع نشط بالفعل: {existing_project.name}. لا يمكن تعيين أكثر من مشروع واحد في نفس الوقت.'
    
    return True, ""


def clean_multiple_project_assignments():
    """
    Clean up any existing multiple project assignments by keeping only the first active project per manager.
    This function should be run once to fix existing data.
    """
    from app import db
    
    # Find all project managers with multiple active projects
    employees = Employee.query.filter_by(role='PROJECT_MANAGER').all()
    
    cleaned_count = 0
    for employee in employees:
        active_projects = Project.query.filter_by(project_manager_id=employee.id).filter(
            Project.status.in_([ProjectStatus.PLANNED, ProjectStatus.ACTIVE])
        ).all()
        
        if len(active_projects) > 1:
            # Keep only the first project, remove others
            for project in active_projects[1:]:
                project.project_manager_id = None
                cleaned_count += 1
    
    # Also check user-based assignments
    from models import User, UserRole
    users = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
    
    for user in users:
        active_projects = Project.query.filter_by(manager_id=user.id).filter(
            Project.status.in_([ProjectStatus.PLANNED, ProjectStatus.ACTIVE])
        ).all()
        
        if len(active_projects) > 1:
            # Keep only the first project, remove others
            for project in active_projects[1:]:
                project.manager_id = None
                cleaned_count += 1
    
    db.session.commit()
    return cleaned_count