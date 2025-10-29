"""
Project Manager Routes
Workflow-oriented interface for PMs managing their assigned project
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from k9.models.models import (
    User, UserRole, Project, Dog, Employee, 
    TrainingSession, VeterinaryVisit, ProductionCycle,
    ProjectAssignment, ProjectDog, DogStatus, EmployeeRole
)
from k9.models.models_handler_daily import HandlerReport, ReportStatus, DailySchedule
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_

pm_bp = Blueprint('pm', __name__, url_prefix='/pm')

def get_pm_project():
    """Get the PM's assigned project or None if not assigned"""
    if current_user.role != UserRole.PROJECT_MANAGER:
        return None
    
    # Find project where current user is the manager
    project = Project.query.filter_by(manager_id=current_user.id).first()
    return project

def require_pm_project(f):
    """Decorator to ensure PM has an assigned project"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.PROJECT_MANAGER:
            flash('الوصول مرفوض', 'error')
            return redirect(url_for('main.index'))
        
        project = get_pm_project()
        if not project:
            flash('لم يتم تعيين مشروع لك بعد. يرجى الاتصال بالمسؤول.', 'warning')
            return render_template('pm/no_project.html')
        
        return f(*args, **kwargs)
    return decorated_function

@pm_bp.route('/dashboard')
@login_required
@require_pm_project
def dashboard():
    """PM Dashboard - Overview of their project"""
    project = get_pm_project()
    
    # Get project statistics
    stats = {
        'project': project,
        'total_dogs': 0,
        'active_dogs': 0,
        'total_employees': 0,
        'active_employees': 0,
        'pending_reports': 0,
        'pending_vet_visits': 0,
    }
    
    # Get dogs assigned to this project
    project_dogs = ProjectDog.query.filter_by(
        project_id=project.id,
        is_active=True
    ).all()
    dog_ids = [pd.dog_id for pd in project_dogs]
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    stats['total_dogs'] = len(dogs)
    stats['active_dogs'] = len([d for d in dogs if d.current_status == DogStatus.ACTIVE])
    
    # Get employees assigned to this project
    project_employees = db.session.query(Employee).join(
        db.Table('project_employee_assignment', db.metadata,
                 autoload_with=db.engine),
        Employee.id == db.Table('project_employee_assignment', db.metadata,
                                autoload_with=db.engine).c.employee_id
    ).filter(
        db.Table('project_employee_assignment', db.metadata,
                autoload_with=db.engine).c.project_id == project.id
    ).all()
    
    stats['total_employees'] = len(project_employees)
    stats['active_employees'] = len([e for e in project_employees if e.is_active])
    
    # Pending reports from handlers
    stats['pending_reports'] = HandlerReport.query.filter_by(
        status=ReportStatus.SUBMITTED
    ).count()
    
    # Recent activities for this project's dogs
    recent_training = []
    recent_vet_visits = []
    if dog_ids:
        recent_training = TrainingSession.query.filter(
            TrainingSession.dog_id.in_(dog_ids)
        ).order_by(TrainingSession.created_at.desc()).limit(5).all()
        
        recent_vet_visits = VeterinaryVisit.query.filter(
            VeterinaryVisit.dog_id.in_(dog_ids)
        ).order_by(VeterinaryVisit.created_at.desc()).limit(5).all()
    
    # Pending approvals count (vet visits needing review)
    from k9.models.models import WorkflowStatus
    pending_vet_count = VeterinaryVisit.query.filter(
        VeterinaryVisit.dog_id.in_(dog_ids) if dog_ids else False,
        VeterinaryVisit.pm_workflow_status == WorkflowStatus.PENDING_PM_REVIEW
    ).count() if dog_ids else 0
    
    stats['pending_vet_visits'] = pending_vet_count
    
    return render_template('pm/dashboard.html', 
                         stats=stats,
                         recent_training=recent_training,
                         recent_vet_visits=recent_vet_visits)

@pm_bp.route('/project')
@login_required
@require_pm_project
def project_view():
    """View PM's project details"""
    project = get_pm_project()
    
    # Get all assigned dogs
    project_dogs = ProjectDog.query.filter_by(
        project_id=project.id,
        is_active=True
    ).all()
    dog_ids = [pd.dog_id for pd in project_dogs]
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    # Get all assigned employees
    project_employees = db.session.query(Employee).join(
        db.Table('project_employee_assignment', db.metadata,
                 autoload_with=db.engine),
        Employee.id == db.Table('project_employee_assignment', db.metadata,
                                autoload_with=db.engine).c.employee_id
    ).filter(
        db.Table('project_employee_assignment', db.metadata,
                autoload_with=db.engine).c.project_id == project.id
    ).all()
    
    return render_template('pm/project_view.html',
                         project=project,
                         dogs=dogs,
                         employees=project_employees)

@pm_bp.route('/my-team')
@login_required
@require_pm_project
def my_team():
    """View team members assigned to PM's project"""
    project = get_pm_project()
    
    # Get employees assigned to this project
    project_employees = db.session.query(Employee).join(
        db.Table('project_employee_assignment', db.metadata,
                 autoload_with=db.engine),
        Employee.id == db.Table('project_employee_assignment', db.metadata,
                                autoload_with=db.engine).c.employee_id
    ).filter(
        db.Table('project_employee_assignment', db.metadata,
                autoload_with=db.engine).c.project_id == project.id
    ).all()
    
    # Get handlers with their user accounts
    handlers = []
    for emp in project_employees:
        if emp.role == EmployeeRole.HANDLER:
            user_account = User.query.filter_by(
                role=UserRole.HANDLER,
                project_id=project.id
            ).first()
            handlers.append({
                'employee': emp,
                'user_account': user_account,
                'has_account': user_account is not None
            })
    
    return render_template('pm/my_team.html',
                         project=project,
                         employees=project_employees,
                         handlers=handlers)

@pm_bp.route('/my-dogs')
@login_required
@require_pm_project
def my_dogs():
    """View dogs assigned to PM's project"""
    project = get_pm_project()
    
    # Get dogs assigned to this project
    project_dogs = ProjectDog.query.filter_by(
        project_id=project.id,
        is_active=True
    ).all()
    dog_ids = [pd.dog_id for pd in project_dogs]
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    # Get recent activity for each dog
    dog_activity = {}
    for dog in dogs:
        last_training = TrainingSession.query.filter_by(
            dog_id=dog.id
        ).order_by(TrainingSession.created_at.desc()).first()
        
        last_vet = VeterinaryVisit.query.filter_by(
            dog_id=dog.id
        ).order_by(VeterinaryVisit.created_at.desc()).first()
        
        dog_activity[dog.id] = {
            'last_training': last_training,
            'last_vet': last_vet
        }
    
    return render_template('pm/my_dogs.html',
                         project=project,
                         dogs=dogs,
                         dog_activity=dog_activity,
                         today=date.today())

@pm_bp.route('/pending-approvals')
@login_required
@require_pm_project
def pending_approvals():
    """View all items pending PM approval"""
    project = get_pm_project()
    
    # Get project's dog IDs
    project_dogs = ProjectDog.query.filter_by(
        project_id=project.id,
        is_active=True
    ).all()
    dog_ids = [pd.dog_id for pd in project_dogs]
    
    # Get pending handler reports
    pending_reports = HandlerReport.query.filter_by(
        status=ReportStatus.SUBMITTED
    ).order_by(HandlerReport.created_at.desc()).all()
    
    # Get pending vet visits
    from k9.models.models import WorkflowStatus
    pending_vet_visits = VeterinaryVisit.query.filter(
        VeterinaryVisit.dog_id.in_(dog_ids) if dog_ids else False,
        VeterinaryVisit.pm_workflow_status == WorkflowStatus.PENDING_PM_REVIEW
    ).order_by(VeterinaryVisit.created_at.desc()).all() if dog_ids else []
    
    # Get pending breeding activities
    from k9.models.models import BreedingTrainingActivity
    pending_breeding = BreedingTrainingActivity.query.filter(
        BreedingTrainingActivity.dog_id.in_(dog_ids) if dog_ids else False,
        BreedingTrainingActivity.pm_workflow_status == WorkflowStatus.PENDING_PM_REVIEW
    ).order_by(BreedingTrainingActivity.created_at.desc()).all() if dog_ids else []
    
    # Get pending caretaker logs
    from k9.models.models import CaretakerDailyLog
    pending_caretaker = CaretakerDailyLog.query.filter(
        CaretakerDailyLog.dog_id.in_(dog_ids) if dog_ids else False,
        CaretakerDailyLog.pm_workflow_status == WorkflowStatus.PENDING_PM_REVIEW
    ).order_by(CaretakerDailyLog.created_at.desc()).all() if dog_ids else []
    
    return render_template('pm/pending_approvals.html',
                         project=project,
                         pending_reports=pending_reports,
                         pending_vet_visits=pending_vet_visits,
                         pending_breeding=pending_breeding,
                         pending_caretaker=pending_caretaker)

@pm_bp.route('/approve-report/<report_id>', methods=['POST'])
@login_required
@require_pm_project
def approve_report(report_id):
    """Approve a handler report"""
    report = HandlerReport.query.get_or_404(report_id)
    
    if report.status != ReportStatus.SUBMITTED:
        flash('هذا التقرير تمت مراجعته بالفعل', 'info')
        return redirect(url_for('pm.pending_approvals'))
    
    report.status = ReportStatus.APPROVED
    report.reviewed_at = datetime.utcnow()
    report.reviewed_by_user_id = current_user.id
    
    db.session.commit()
    
    flash('تمت الموافقة على التقرير بنجاح', 'success')
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/reject-report/<report_id>', methods=['POST'])
@login_required
@require_pm_project
def reject_report(report_id):
    """Reject a handler report"""
    report = HandlerReport.query.get_or_404(report_id)
    
    if report.status != ReportStatus.SUBMITTED:
        flash('هذا التقرير تمت مراجعته بالفعل', 'info')
        return redirect(url_for('pm.pending_approvals'))
    
    feedback = request.form.get('feedback', '')
    
    report.status = ReportStatus.REJECTED
    report.reviewed_at = datetime.utcnow()
    report.reviewed_by_user_id = current_user.id
    report.supervisor_feedback = feedback
    
    db.session.commit()
    
    flash('تم رفض التقرير', 'info')
    return redirect(url_for('pm.pending_approvals'))
