"""
Project Manager Routes
Workflow-oriented interface for PMs managing their assigned project
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_
from app import db
from k9.models.models import (
    User, UserRole, Project, Dog, Employee, 
    TrainingSession, VeterinaryVisit, ProductionCycle,
    ProjectAssignment, ProjectDog, DogStatus, EmployeeRole,
    WorkflowStatus, BreedingTrainingActivity, CaretakerDailyLog
)
from k9.models.models_handler_daily import HandlerReport, ReportStatus, DailySchedule

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

def get_project_dog_ids(project_id):
    """Helper to get dog IDs for a project"""
    project_dogs = ProjectDog.query.filter_by(
        project_id=project_id,
        is_active=True
    ).all()
    return [pd.dog_id for pd in project_dogs]

def get_project_employees(project_id):
    """Helper to get employees assigned to a project - optimized query"""
    try:
        from sqlalchemy import Table
        project_emp_table = Table('project_employee_assignment', db.metadata, autoload_with=db.engine)
        
        employees = db.session.query(Employee).join(
            project_emp_table,
            Employee.id == project_emp_table.c.employee_id
        ).filter(
            project_emp_table.c.project_id == project_id
        ).all()
        
        return employees
    except Exception as e:
        print(f"Error getting project employees: {e}")
        return []

@pm_bp.route('/dashboard')
@login_required
@require_pm_project
def dashboard():
    """PM Dashboard - Overview of their project"""
    project = get_pm_project()
    if not project:
        return redirect(url_for('main.index'))
    
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
    dog_ids = get_project_dog_ids(project.id)
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    stats['total_dogs'] = len(dogs)
    stats['active_dogs'] = len([d for d in dogs if d.current_status == DogStatus.ACTIVE])
    
    # Get employees assigned to this project
    project_employees = get_project_employees(project.id)
    
    stats['total_employees'] = len(project_employees)
    stats['active_employees'] = len([e for e in project_employees if e.is_active])
    
    # Pending reports from handlers (filtered by project)
    stats['pending_reports'] = HandlerReport.query.filter_by(
        project_id=project.id,
        status=ReportStatus.SUBMITTED
    ).count()
    
    # Recent activities for this project's dogs - optimized with limit
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
    pending_vet_count = 0
    if dog_ids:
        pending_vet_count = VeterinaryVisit.query.filter(
            VeterinaryVisit.dog_id.in_(dog_ids),
            VeterinaryVisit.status == WorkflowStatus.PENDING_PM_REVIEW.value
        ).count()
    
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
    if not project:
        return redirect(url_for('main.index'))
    
    # Get all assigned dogs
    dog_ids = get_project_dog_ids(project.id)
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    # Get all assigned employees
    project_employees = get_project_employees(project.id)
    
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
    if not project:
        return redirect(url_for('main.index'))
    
    # Get employees assigned to this project
    project_employees = get_project_employees(project.id)
    
    # Get handlers with their user accounts - FIX: properly match employee to user
    handlers = []
    for emp in project_employees:
        if emp.role == EmployeeRole.HANDLER:
            # FIX: Match user account by employee_id, not just any handler in project
            user_account = User.query.filter_by(
                employee_id=emp.id,
                role=UserRole.HANDLER
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
    if not project:
        return redirect(url_for('main.index'))
    
    # Get dogs assigned to this project
    dog_ids = get_project_dog_ids(project.id)
    dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all() if dog_ids else []
    
    # Get recent activity for each dog - optimized to use single query per type
    dog_activity = {}
    
    if dogs:
        dog_id_list = [d.id for d in dogs]
        
        # Get last training for all dogs in one query
        last_trainings = db.session.query(
            TrainingSession.dog_id,
            func.max(TrainingSession.created_at).label('max_date')
        ).filter(
            TrainingSession.dog_id.in_(dog_id_list)
        ).group_by(TrainingSession.dog_id).all()
        
        training_dates = {dog_id: max_date for dog_id, max_date in last_trainings}
        
        # Get actual training sessions
        training_sessions = {}
        for dog_id, max_date in training_dates.items():
            session = TrainingSession.query.filter_by(
                dog_id=dog_id
            ).order_by(TrainingSession.created_at.desc()).first()
            if session:
                training_sessions[dog_id] = session
        
        # Get last vet visit for all dogs in one query
        last_vets = db.session.query(
            VeterinaryVisit.dog_id,
            func.max(VeterinaryVisit.created_at).label('max_date')
        ).filter(
            VeterinaryVisit.dog_id.in_(dog_id_list)
        ).group_by(VeterinaryVisit.dog_id).all()
        
        vet_dates = {dog_id: max_date for dog_id, max_date in last_vets}
        
        # Get actual vet visits
        vet_visits = {}
        for dog_id, max_date in vet_dates.items():
            visit = VeterinaryVisit.query.filter_by(
                dog_id=dog_id
            ).order_by(VeterinaryVisit.created_at.desc()).first()
            if visit:
                vet_visits[dog_id] = visit
        
        # Build activity dict
        for dog in dogs:
            dog_activity[dog.id] = {
                'last_training': training_sessions.get(dog.id),
                'last_vet': vet_visits.get(dog.id)
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
    if not project:
        return redirect(url_for('main.index'))
    
    # Get project's dog IDs
    dog_ids = get_project_dog_ids(project.id)
    
    # Get pending handler reports (filtered by project)
    pending_reports = HandlerReport.query.filter_by(
        project_id=project.id,
        status=ReportStatus.SUBMITTED
    ).order_by(HandlerReport.created_at.desc()).all()
    
    # Get pending vet visits
    pending_vet_visits = []
    if dog_ids:
        pending_vet_visits = VeterinaryVisit.query.filter(
            VeterinaryVisit.dog_id.in_(dog_ids),
            VeterinaryVisit.status == WorkflowStatus.PENDING_PM_REVIEW.value
        ).order_by(VeterinaryVisit.created_at.desc()).all()
    
    # Get pending breeding activities
    pending_breeding = []
    if dog_ids:
        pending_breeding = BreedingTrainingActivity.query.filter(
            BreedingTrainingActivity.dog_id.in_(dog_ids),
            BreedingTrainingActivity.status == WorkflowStatus.PENDING_PM_REVIEW.value
        ).order_by(BreedingTrainingActivity.created_at.desc()).all()
    
    # Get pending caretaker logs
    pending_caretaker = []
    if dog_ids:
        pending_caretaker = CaretakerDailyLog.query.filter(
            CaretakerDailyLog.dog_id.in_(dog_ids),
            CaretakerDailyLog.status == WorkflowStatus.PENDING_PM_REVIEW.value
        ).order_by(CaretakerDailyLog.created_at.desc()).all()
    
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
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        report = HandlerReport.query.get_or_404(report_id)
        
        # Security check: Ensure report belongs to PM's project
        if report.project_id != project.id:
            flash('ليس لديك صلاحية لمراجعة هذا التقرير', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if report.status != ReportStatus.SUBMITTED:
            flash('هذا التقرير تمت مراجعته بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        report.status = ReportStatus.APPROVED
        report.reviewed_at = datetime.utcnow()
        report.reviewed_by_user_id = current_user.id
        
        db.session.commit()
        
        flash('تمت الموافقة على التقرير بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الموافقة على التقرير: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/reject-report/<report_id>', methods=['POST'])
@login_required
@require_pm_project
def reject_report(report_id):
    """Reject a handler report"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        report = HandlerReport.query.get_or_404(report_id)
        
        # Security check: Ensure report belongs to PM's project
        if report.project_id != project.id:
            flash('ليس لديك صلاحية لمراجعة هذا التقرير', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
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
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء رفض التقرير: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/approve-vet-visit/<visit_id>', methods=['POST'])
@login_required
@require_pm_project
def approve_vet_visit(visit_id):
    """Approve a veterinary visit"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        visit = VeterinaryVisit.query.get_or_404(visit_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure visit belongs to PM's project
        if visit.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذه الزيارة', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if visit.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذه الزيارة تمت مراجعتها بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        visit.status = WorkflowStatus.PM_APPROVED.value
        visit.reviewed_at = datetime.utcnow()
        visit.reviewed_by_user_id = current_user.id
        
        db.session.commit()
        
        flash('تمت الموافقة على الزيارة البيطرية بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الموافقة على الزيارة: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/reject-vet-visit/<visit_id>', methods=['POST'])
@login_required
@require_pm_project
def reject_vet_visit(visit_id):
    """Reject a veterinary visit"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        visit = VeterinaryVisit.query.get_or_404(visit_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure visit belongs to PM's project
        if visit.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذه الزيارة', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if visit.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذه الزيارة تمت مراجعتها بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        feedback = request.form.get('feedback', '')
        
        visit.status = WorkflowStatus.PM_REJECTED.value
        visit.reviewed_at = datetime.utcnow()
        visit.reviewed_by_user_id = current_user.id
        visit.review_notes = feedback
        
        db.session.commit()
        
        flash('تم رفض الزيارة البيطرية', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء رفض الزيارة: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/approve-breeding/<activity_id>', methods=['POST'])
@login_required
@require_pm_project
def approve_breeding(activity_id):
    """Approve a breeding training activity"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        activity = BreedingTrainingActivity.query.get_or_404(activity_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure activity belongs to PM's project
        if activity.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذا النشاط', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if activity.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذا النشاط تمت مراجعته بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        activity.status = WorkflowStatus.PM_APPROVED.value
        activity.reviewed_at = datetime.utcnow()
        activity.reviewed_by_user_id = current_user.id
        
        db.session.commit()
        
        flash('تمت الموافقة على نشاط التكاثر بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الموافقة على النشاط: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/reject-breeding/<activity_id>', methods=['POST'])
@login_required
@require_pm_project
def reject_breeding(activity_id):
    """Reject a breeding training activity"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        activity = BreedingTrainingActivity.query.get_or_404(activity_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure activity belongs to PM's project
        if activity.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذا النشاط', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if activity.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذا النشاط تمت مراجعته بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        feedback = request.form.get('feedback', '')
        
        activity.status = WorkflowStatus.PM_REJECTED.value
        activity.reviewed_at = datetime.utcnow()
        activity.reviewed_by_user_id = current_user.id
        activity.review_notes = feedback
        
        db.session.commit()
        
        flash('تم رفض نشاط التكاثر', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء رفض النشاط: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/approve-caretaker/<log_id>', methods=['POST'])
@login_required
@require_pm_project
def approve_caretaker(log_id):
    """Approve a caretaker daily log"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        log = CaretakerDailyLog.query.get_or_404(log_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure log belongs to PM's project
        if log.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذا السجل', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if log.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذا السجل تمت مراجعته بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        log.status = WorkflowStatus.PM_APPROVED.value
        log.reviewed_at = datetime.utcnow()
        log.reviewed_by_user_id = current_user.id
        
        db.session.commit()
        
        flash('تمت الموافقة على سجل الرعاية بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الموافقة على السجل: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))

@pm_bp.route('/reject-caretaker/<log_id>', methods=['POST'])
@login_required
@require_pm_project
def reject_caretaker(log_id):
    """Reject a caretaker daily log"""
    project = get_pm_project()
    if not project:
        flash('لم يتم العثور على المشروع', 'error')
        return redirect(url_for('main.index'))
        
    try:
        log = CaretakerDailyLog.query.get_or_404(log_id)
        dog_ids = get_project_dog_ids(project.id)
        
        # Security check: Ensure log belongs to PM's project
        if log.dog_id not in dog_ids:
            flash('ليس لديك صلاحية لمراجعة هذا السجل', 'error')
            return redirect(url_for('pm.pending_approvals'))
        
        if log.status != WorkflowStatus.PENDING_PM_REVIEW.value:
            flash('هذا السجل تمت مراجعته بالفعل', 'info')
            return redirect(url_for('pm.pending_approvals'))
        
        feedback = request.form.get('feedback', '')
        
        log.status = WorkflowStatus.PM_REJECTED.value
        log.reviewed_at = datetime.utcnow()
        log.reviewed_by_user_id = current_user.id
        log.review_notes = feedback
        
        db.session.commit()
        
        flash('تم رفض سجل الرعاية', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء رفض السجل: {str(e)}', 'error')
        
    return redirect(url_for('pm.pending_approvals'))
