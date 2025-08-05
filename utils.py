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
    try:
        audit_log = AuditLog()
        audit_log.user_id = user_id
        audit_log.action = action
        audit_log.target_type = target_type
        audit_log.target_id = target_id
        audit_log.description = description
        audit_log.old_values = old_values
        audit_log.new_values = new_values
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
    """Get user permissions based on role and allowed sections"""
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
        permissions = {section: False for section in ['dogs', 'employees', 'training', 'veterinary', 'breeding', 'projects', 'attendance', 'reports', 'admin']}
        for section in user.allowed_sections or []:
            if section in permissions:
                permissions[section] = True
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
            # Create default permissions for new PROJECT_MANAGER
            permission = ProjectManagerPermission()
            permission.user_id = user.id
            permission.project_id = project_id
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

def get_user_projects(user):
    """Get projects assigned to a PROJECT_MANAGER user"""
    from models import Project, UserRole
    
    if user.role == UserRole.GENERAL_ADMIN:
        return Project.query.all()
    elif user.role == UserRole.PROJECT_MANAGER:
        # Get projects where this user is the manager
        return Project.query.filter_by(project_manager_id=user.id).all()
    
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
