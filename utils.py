import os
from flask import request, current_app
from models import AuditLog
from app import db
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import uuid

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_audit(user_id, action, target_type, target_id, description=None, old_values=None, new_values=None):
    """Log an audit trail entry"""
    import json
    try:
        audit_log = AuditLog()
        audit_log.user_id = user_id
        audit_log.action = action
        audit_log.target_type = target_type
        # Handle target_id properly for UUID compatibility
        # Don't convert User IDs (integers) to UUIDs, leave them as None for User targets
        if target_type == 'User' and isinstance(target_id, (int, str)) and str(target_id).isdigit():
            audit_log.target_id = None  # Don't try to store integer user IDs as UUIDs
        else:
            audit_log.target_id = str(target_id) if target_id is not None else None
        
        # Ensure description is a string, not dict (for SQLite compatibility)
        if isinstance(description, dict):
            audit_log.description = json.dumps(description, ensure_ascii=False)
        else:
            audit_log.description = description
            
        # Ensure old_values and new_values are properly handled for SQLite
        audit_log.old_values = json.dumps(old_values, ensure_ascii=False) if old_values and isinstance(old_values, dict) else old_values
        audit_log.new_values = json.dumps(new_values, ensure_ascii=False) if new_values and isinstance(new_values, dict) else new_values
        
        audit_log.ip_address = request.remote_addr if request else None
        audit_log.user_agent = request.headers.get('User-Agent') if request else None
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {str(e)}")

def generate_pdf_report(report_type, start_date, end_date, user):
    """Generate PDF reports based on type and date range"""
    from models import Dog, Employee, TrainingSession, VeterinaryVisit, BreedingCycle
    
    # Create filename
    filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        alignment=2,  # Right alignment for Arabic
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=2,  # Right alignment for Arabic
    )
    
    # Add title
    if report_type == 'dogs':
        title = "تقرير الكلاب"
        # Get dogs data
        if user.role.value == 'GENERAL_ADMIN':
            dogs = Dog.query.all()
        else:
            dogs = Dog.query.filter_by(assigned_to_user_id=user.id).all()
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Create table data
        data = [['اسم الكلب', 'الكود', 'السلالة', 'الجنس', 'الحالة', 'الموقع']]
        for dog in dogs:
            gender_ar = 'ذكر' if dog.gender.value == 'MALE' else 'أنثى'
            status_ar = {'ACTIVE': 'نشط', 'RETIRED': 'متقاعد', 'DECEASED': 'متوفى', 'TRAINING': 'تدريب'}.get(dog.current_status.value, dog.current_status.value)
            data.append([
                dog.name or '',
                dog.code or '',
                dog.breed or '',
                gender_ar,
                status_ar,
                dog.location or ''
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    elif report_type == 'training':
        title = "تقرير التدريب"
        # Get training sessions
        if user.role.value == 'GENERAL_ADMIN':
            sessions = TrainingSession.query.filter(
                TrainingSession.session_date >= start_date,
                TrainingSession.session_date <= end_date
            ).all() if start_date and end_date else TrainingSession.query.all()
        else:
            assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=user.id).all()]
            sessions = TrainingSession.query.filter(
                TrainingSession.dog_id.in_(assigned_dog_ids)
            ).all()
            if start_date and end_date:
                sessions = [s for s in sessions if start_date <= s.session_date.date() <= end_date]
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Create table data
        data = [['الكلب', 'المدرب', 'النوع', 'الموضوع', 'التاريخ', 'المدة (دقيقة)', 'التقييم']]
        for session in sessions:
            category_ar = {
                'OBEDIENCE': 'طاعة',
                'DETECTION': 'كشف',
                'AGILITY': 'رشاقة',
                'ATTACK': 'هجوم',
                'FITNESS': 'لياقة'
            }.get(session.category.value, session.category.value)
            
            data.append([
                session.dog.name,
                session.trainer.name,
                category_ar,
                session.subject,
                session.session_date.strftime('%Y-%m-%d'),
                str(session.duration),
                f"{session.success_rating}/10"
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    elif report_type == 'veterinary':
        title = "تقرير الطبابة"
        # Get veterinary visits
        if user.role.value == 'GENERAL_ADMIN':
            visits = VeterinaryVisit.query.filter(
                VeterinaryVisit.visit_date >= start_date,
                VeterinaryVisit.visit_date <= end_date
            ).all() if start_date and end_date else VeterinaryVisit.query.all()
        else:
            assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=user.id).all()]
            visits = VeterinaryVisit.query.filter(
                VeterinaryVisit.dog_id.in_(assigned_dog_ids)
            ).all()
            if start_date and end_date:
                visits = [v for v in visits if start_date <= v.visit_date.date() <= end_date]
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Create table data
        data = [['الكلب', 'الطبيب', 'نوع الزيارة', 'التاريخ', 'التشخيص', 'العلاج']]
        for visit in visits:
            visit_type_ar = {
                'ROUTINE': 'روتينية',
                'EMERGENCY': 'طارئة',
                'VACCINATION': 'تطعيم'
            }.get(visit.visit_type.value, visit.visit_type.value)
            
            data.append([
                visit.dog.name,
                visit.vet.name,
                visit_type_ar,
                visit.visit_date.strftime('%Y-%m-%d'),
                visit.diagnosis or '',
                visit.treatment or ''
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    # Add generation info
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"تم إنشاء التقرير في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Paragraph(f"بواسطة: {user.full_name}", normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Log the report generation
    log_audit(user.id, 'EXPORT', 'Report', filename, {
        'report_type': report_type,
        'start_date': start_date.isoformat() if start_date else None,
        'end_date': end_date.isoformat() if end_date else None
    })
    
    return filename

def get_user_permissions(user):
    """Get user permissions based on role and SubPermission grants"""
    if user.role.value == 'GENERAL_ADMIN':
        return {
            'dogs': True,
            'employees': True,
            'training': True,
            'veterinary': True,
            'breeding': True,
            'projects': True,
            'attendance': True,
            'reports': True,
            'admin': True
        }
    else:  # PROJECT_MANAGER
        # Load permissions from SubPermission table for PROJECT_MANAGER
        from models import SubPermission, Project
        permissions = {section: False for section in ['dogs', 'employees', 'training', 'veterinary', 'breeding', 'projects', 'attendance', 'reports', 'admin']}
        
        # Check if user has any granted permissions in SubPermission table
        user_permissions = SubPermission.query.filter_by(user_id=user.id, is_granted=True).all()
        
        # Map SubPermission sections to the main sections
        section_mapping = {
            'Dogs': 'dogs',
            'Employees': 'employees', 
            'Training': 'training',
            'Veterinary': 'veterinary',
            'Breeding': 'breeding',
            'Projects': 'projects',
            'Attendance': 'attendance',
            'Reports': 'reports',
            'Analytics': 'reports'
        }
        
        # If user has any granted permissions, enable those sections
        for perm in user_permissions:
            mapped_section = section_mapping.get(perm.section)
            if mapped_section and mapped_section in permissions:
                permissions[mapped_section] = True
                
        # Also check assigned projects - if user has projects assigned, they should see projects section
        user_projects = Project.query.filter_by(manager_id=user.id).all()
        if user_projects:
            permissions['projects'] = True
        
        return permissions

def get_project_manager_permissions(user, project_id):
    """Get granular permissions for a PROJECT_MANAGER user on a specific project"""
    from models import ProjectManagerPermission, UserRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        # GENERAL_ADMIN has all permissions
        return {
            'can_manage_assignments': True,
            'can_manage_shifts': True,
            'can_manage_attendance': True,
            'can_manage_training': True,
            'can_manage_incidents': True,
            'can_manage_performance': True,
            'can_view_veterinary': True,
            'can_view_breeding': True
        }
    
    if user.role == UserRole.PROJECT_MANAGER:
        # Check if permission record exists
        permission = ProjectManagerPermission.query.filter_by(
            user_id=user.id,
            project_id=project_id
        ).first()
        
        if permission:
            return {
                'can_manage_assignments': permission.can_manage_assignments,
                'can_manage_shifts': permission.can_manage_shifts,
                'can_manage_attendance': permission.can_manage_attendance,
                'can_manage_training': permission.can_manage_training,
                'can_manage_incidents': permission.can_manage_incidents,
                'can_manage_performance': permission.can_manage_performance,
                'can_view_veterinary': permission.can_view_veterinary,
                'can_view_breeding': permission.can_view_breeding
            }
        else:
            # Create default permissions for new PROJECT_MANAGER with all permissions enabled
            permission = ProjectManagerPermission()
            permission.user_id = user.id
            permission.project_id = project_id
            # Explicitly set all permissions to True (override any defaults)
            permission.can_manage_assignments = True
            permission.can_manage_shifts = True
            permission.can_manage_attendance = True
            permission.can_manage_training = True
            permission.can_manage_incidents = True
            permission.can_manage_performance = True
            permission.can_view_veterinary = True
            permission.can_view_breeding = True
            db.session.add(permission)
            db.session.commit()
            
            return {
                'can_manage_assignments': True,
                'can_manage_shifts': True,
                'can_manage_attendance': True,
                'can_manage_training': True,
                'can_manage_incidents': True,
                'can_manage_performance': True,
                'can_view_veterinary': True,
                'can_view_breeding': True
            }
    
    # Default: no permissions for other roles
    return {
        'can_manage_assignments': False,
        'can_manage_shifts': False,
        'can_manage_attendance': False,
        'can_manage_training': False,
        'can_manage_incidents': False,
        'can_manage_performance': False,
        'can_view_veterinary': False,
        'can_view_breeding': False
    }

def get_user_assigned_projects(user):
    """Get projects with data that PROJECT_MANAGER can access based on SubPermission"""
    from models import Project, UserRole, SubPermission
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Project.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Get projects where this user is assigned as manager
        assigned_projects = Project.query.filter_by(manager_id=user.id).all()
        
        # Also get projects from SubPermission grants
        project_permissions = SubPermission.query.filter_by(
            user_id=user.id, 
            section="Projects",
            is_granted=True
        ).filter(SubPermission.project_id.isnot(None)).all()
        
        # Add projects from permission grants
        permission_project_ids = [p.project_id for p in project_permissions]
        permission_projects = Project.query.filter(Project.id.in_(permission_project_ids)).all() if permission_project_ids else []
        
        # Combine and deduplicate
        all_projects = list(set(assigned_projects + permission_projects))
        return all_projects
    
    return []

def get_user_accessible_dogs(user):
    """Get dogs that PROJECT_MANAGER can access based on SubPermission and project assignments"""
    from models import Dog, UserRole, SubPermission, ProjectAssignment, Project, PermissionType
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Dog.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Check if user has VIEW permission for Dogs
        dogs_permission = SubPermission.query.filter_by(
            user_id=user.id,
            section="Dogs",
            subsection="عرض قائمة الكلاب",
            permission_type=PermissionType.VIEW,
            is_granted=True
        ).first()
        
        if not dogs_permission:
            return []
            
        # Get projects this user has access to
        user_projects = get_user_assigned_projects(user)
        if not user_projects:
            return []
            
        # Get dogs through project assignments
        dogs = []
        for project in user_projects:
            project_dogs = db.session.query(Dog).join(ProjectAssignment).filter(
                ProjectAssignment.project_id == project.id,
                ProjectAssignment.dog_id.isnot(None)
            ).all()
            dogs.extend(project_dogs)
        
        return list(set(dogs))  # Remove duplicates
    
    return []

def get_user_accessible_employees(user):
    """Get employees that PROJECT_MANAGER can access based on SubPermission and project assignments"""
    from models import Employee, UserRole, SubPermission, ProjectAssignment, Project, PermissionType
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Employee.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Check if user has VIEW permission for Employees
        employees_permission = SubPermission.query.filter_by(
            user_id=user.id,
            section="Employees",
            subsection="عرض قائمة الموظفين",
            permission_type=PermissionType.VIEW,
            is_granted=True
        ).first()
        
        if not employees_permission:
            return []
            
        # Get projects this user has access to
        user_projects = get_user_assigned_projects(user)
        if not user_projects:
            return []
            
        # Get employees through project assignments
        employees = []
        for project in user_projects:
            project_employees = db.session.query(Employee).join(ProjectAssignment).filter(
                ProjectAssignment.project_id == project.id,
                ProjectAssignment.employee_id.isnot(None)
            ).all()
            employees.extend(project_employees)
        
        return list(set(employees))  # Remove duplicates
    
    return []

def get_user_projects(user):
    """Get projects assigned to a PROJECT_MANAGER user"""
    from models import Project, UserRole, Employee, EmployeeRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Project.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Get projects where this user is the manager
        # First try by direct user assignment
        direct_projects = Project.query.filter_by(project_manager_id=user.id).all()
        
        # Also check through employee profile assignment
        employee = Employee.query.filter_by(user_account_id=user.id, role=EmployeeRole.PROJECT_MANAGER).first()
        if employee:
            employee_projects = employee.projects
            # Combine and deduplicate
            all_projects = list(set(direct_projects + employee_projects))
            return all_projects
        
        return direct_projects
    
    return []

def check_project_access(user, project_id):
    """Check if user has access to a specific project"""
    from models import Project, UserRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        return True
    elif user.role == UserRole.PROJECT_MANAGER:
        project = Project.query.get(project_id)
        return project and project.project_manager_id == user.id
    
    return False

def filter_data_by_project_access(user, query, model_class):
    """Filter query results based on user's project access"""
    from models import UserRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        return query
    elif user.role == UserRole.PROJECT_MANAGER:
        user_projects = get_user_projects(user)
        project_ids = [p.id for p in user_projects]
        
        # Apply filtering based on model type
        if hasattr(model_class, 'project_id'):
            return query.filter(model_class.project_id.in_(project_ids))
        elif hasattr(model_class, 'projects'):
            # For models with many-to-many relationship with projects
            return query.join(model_class.projects).filter(model_class.id.in_(project_ids))
    
    return query.filter(False)  # No access by default

def ensure_employee_user_linkage():
    """Ensure all PROJECT_MANAGER employees have linked user accounts"""
    from models import Employee, User, EmployeeRole, UserRole
    from werkzeug.security import generate_password_hash
    import secrets
    
    # Find PROJECT_MANAGER employees without user accounts
    pm_employees = Employee.query.filter_by(role=EmployeeRole.PROJECT_MANAGER, user_account_id=None).all()
    
    created_users = []
    for employee in pm_employees:
        # Create user account for this employee
        username = f"pm_{employee.employee_id.lower()}"
        temp_password = secrets.token_urlsafe(12)
        
        new_user = User()
        new_user.username = username
        new_user.email = employee.email or f"{username}@k9ops.local"
        new_user.password_hash = generate_password_hash(temp_password)
        new_user.full_name = employee.name
        new_user.role = UserRole.PROJECT_MANAGER
        new_user.active = True
        
        db.session.add(new_user)
        db.session.flush()
        
        # Link employee to user
        employee.user_account_id = new_user.id
        
        created_users.append({
            'user': new_user,
            'employee': employee,
            'temp_password': temp_password
        })
    
    if created_users:
        db.session.commit()
    
    return created_users

def get_employee_profile_for_user(user):
    """Get the employee profile for a PROJECT_MANAGER user"""
    from models import Employee, EmployeeRole
    
    return Employee.query.filter_by(user_account_id=user.id, role=EmployeeRole.PROJECT_MANAGER).first()

def get_user_active_projects(user):
    """Get active projects for a PROJECT_MANAGER user"""
    from models import Project, UserRole, Employee, EmployeeRole, ProjectStatus
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Project.query.filter_by(status=ProjectStatus.ACTIVE).all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Get active projects where this user is the manager
        active_projects = Project.query.filter_by(
            project_manager_id=user.id, 
            status=ProjectStatus.ACTIVE
        ).all()
        
        # Also check through employee profile assignment for active projects
        employee = Employee.query.filter_by(user_account_id=user.id, role=EmployeeRole.PROJECT_MANAGER).first()
        if employee:
            employee_active_projects = [p for p in employee.projects if p.status == ProjectStatus.ACTIVE]
            # Combine and deduplicate
            all_active_projects = list(set(active_projects + employee_active_projects))
            return all_active_projects
        
        return active_projects
    
    return []

def get_user_all_projects(user):
    """Get ALL projects (regardless of status) for a PROJECT_MANAGER user"""
    from models import Project, UserRole, Employee, EmployeeRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Project.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Get all projects where this user is the manager
        manager_projects = Project.query.filter_by(project_manager_id=user.id).all()
        
        # Also check through employee profile assignment
        employee = Employee.query.filter_by(user_account_id=user.id, role=EmployeeRole.PROJECT_MANAGER).first()
        if employee:
            employee_projects = employee.projects
            # Combine and deduplicate
            all_projects = list(set(manager_projects + employee_projects))
            return all_projects
        
        return manager_projects
    
    return []

def validate_project_manager_assignment(user, project):
    """
    Validate if a project manager can be assigned to a project.
    
    Enhanced Rules:
    - GENERAL_ADMIN can be assigned to any project
    - PROJECT_MANAGER can only manage ONE project at a time regardless of status
    - PROJECT_MANAGER cannot be assigned to any project if they manage another ongoing project
    - PROJECT_MANAGER can be reassigned to the same project they're already managing
    """
    from models import ProjectStatus, UserRole
    
    # Skip validation for GENERAL_ADMIN
    if user.role == UserRole.GENERAL_ADMIN:
        return True, None
    
    # For PROJECT_MANAGER role, enforce strict one-project rule
    if user.role == UserRole.PROJECT_MANAGER:
        # Get ALL projects (not just active) for this manager
        all_projects = get_user_all_projects(user)
        
        # Only consider ongoing projects (ACTIVE or PLANNED)
        ongoing_projects = [p for p in all_projects if p.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]]
        
        # Check if they already manage any other ongoing projects
        other_ongoing_projects = [p for p in ongoing_projects if p.id != project.id]
        
        if other_ongoing_projects:
            project_names = []
            for p in other_ongoing_projects:
                status_text = "نشط" if p.status == ProjectStatus.ACTIVE else "مخطط"
                project_names.append(f"{p.name} ({status_text})")
            
            return False, f"المدير {user.username} يدير بالفعل المشروع: {', '.join(project_names)}. يجب إنهاء أو إلغاء المشروع الحالي قبل تعيين مشروع جديد."
    
    return True, None

def validate_project_status_change(project, new_status, current_user=None):
    """
    Validate if a project status change is allowed, especially for project manager constraints.
    
    Rules:
    - If changing to ACTIVE or PLANNED, ensure the project manager doesn't have other ongoing projects
    - If project manager is being changed while project is ACTIVE/PLANNED, validate the new manager
    """
    from models import ProjectStatus, UserRole
    
    # If changing to ACTIVE or PLANNED status, validate project manager
    if new_status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED] and project.project_manager_id:
        # Get the project manager user
        from models import User
        manager = User.query.get(project.project_manager_id)
        
        if manager and manager.role == UserRole.PROJECT_MANAGER:
            # Temporarily set the new status for validation
            original_status = project.status
            project.status = new_status
            
            can_assign, error_msg = validate_project_manager_assignment(manager, project)
            
            # Restore original status
            project.status = original_status
            
            if not can_assign:
                return False, error_msg
    
    return True, None

def get_dog_active_project(dog_id, activity_date=None):
    """Get the active project for a dog at a specific date"""
    from models import ProjectAssignment
    from datetime import datetime
    
    if activity_date is None:
        activity_date = datetime.utcnow()
    
    # Convert date to datetime if needed
    if hasattr(activity_date, 'date'):
        activity_datetime = activity_date
    else:
        activity_datetime = datetime.combine(activity_date, datetime.min.time())
    
    # Find active assignment for the dog at the given date
    active_assignment = ProjectAssignment.query.filter(
        ProjectAssignment.dog_id == str(dog_id),
        ProjectAssignment.assigned_from <= activity_datetime,
        db.or_(
            ProjectAssignment.assigned_to.is_(None),  # Still active
            ProjectAssignment.assigned_to >= activity_datetime  # Not yet ended
        )
    ).first()
    
    return active_assignment.project_id if active_assignment else None

def auto_link_dog_activity_to_project(dog_id, activity_date=None):
    """Automatically determine and return the project_id for a dog activity"""
    return get_dog_active_project(dog_id, activity_date)

def get_project_linked_activities(project_id, start_date=None, end_date=None):
    """Get all activities linked to a project within a date range"""
    from models import TrainingSession, VeterinaryVisit, Incident, Suspicion, ProjectAssignment
    from datetime import datetime
    
    activities = {
        'training_sessions': [],
        'veterinary_visits': [],
        'incidents': [],
        'suspicions': []
    }
    
    # Get project assignments to filter activities by assignment period
    assignments = ProjectAssignment.query.filter_by(project_id=str(project_id)).all()
    dog_assignments = {a.dog_id: a for a in assignments if a.dog_id}
    
    # Training sessions
    training_query = TrainingSession.query.filter_by(project_id=str(project_id))
    if start_date:
        training_query = training_query.filter(TrainingSession.session_date >= start_date)
    if end_date:
        training_query = training_query.filter(TrainingSession.session_date <= end_date)
    
    for session in training_query.all():
        # Check if session is within dog's assignment period
        assignment = dog_assignments.get(session.dog_id)
        if assignment:
            session_date = session.session_date
            if assignment.assigned_from <= session_date:
                if not assignment.assigned_to or assignment.assigned_to >= session_date:
                    activities['training_sessions'].append(session)
    
    # Veterinary visits
    vet_query = VeterinaryVisit.query.filter_by(project_id=str(project_id))
    if start_date:
        vet_query = vet_query.filter(VeterinaryVisit.visit_date >= start_date)
    if end_date:
        vet_query = vet_query.filter(VeterinaryVisit.visit_date <= end_date)
    
    for visit in vet_query.all():
        # Check if visit is within dog's assignment period
        assignment = dog_assignments.get(visit.dog_id)
        if assignment:
            visit_date = visit.visit_date
            if assignment.assigned_from <= visit_date:
                if not assignment.assigned_to or assignment.assigned_to >= visit_date:
                    activities['veterinary_visits'].append(visit)
    
    # Incidents (already have project_id)
    incident_query = Incident.query.filter_by(project_id=str(project_id))
    if start_date:
        incident_query = incident_query.filter(Incident.incident_date >= start_date)
    if end_date:
        incident_query = incident_query.filter(Incident.incident_date <= end_date)
    activities['incidents'] = incident_query.all()
    
    # Suspicions (already have project_id)
    suspicion_query = Suspicion.query.filter_by(project_id=str(project_id))
    if start_date:
        suspicion_query = suspicion_query.filter(Suspicion.discovery_date >= start_date)
    if end_date:
        suspicion_query = suspicion_query.filter(Suspicion.discovery_date <= end_date)
    activities['suspicions'] = suspicion_query.all()
    
    return activities
