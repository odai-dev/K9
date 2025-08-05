from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import (Dog, Employee, TrainingSession, VeterinaryVisit, BreedingCycle, 
                   Project, AuditLog, UserRole, DogStatus, 
                   EmployeeRole, TrainingCategory, VisitType, BreedingCycleType, 
                   BreedingResult, ProjectStatus, AuditAction, DogGender, User,
                   MaturityStatus, HeatStatus, PregnancyStatus, ProjectDog, ProjectAssignment,
                   Incident, Suspicion, PerformanceEvaluation, 
                   ElementType, PerformanceRating, TargetType,
                   project_employee_assignment, project_dog_assignment,
                   # New attendance models
                   ProjectShift, ProjectShiftAssignment, ProjectAttendance,
                   EntityType, AttendanceStatus, AbsenceReason)
from utils import log_audit, allowed_file, generate_pdf_report
import os
from datetime import datetime, date
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    stats = {}
    
    if current_user.role == UserRole.GENERAL_ADMIN:
        stats['total_dogs'] = Dog.query.count()
        stats['active_dogs'] = Dog.query.filter_by(current_status=DogStatus.ACTIVE).count()
        stats['total_employees'] = Employee.query.count()
        stats['active_employees'] = Employee.query.filter_by(is_active=True).count()
        stats['total_projects'] = Project.query.count()
        
        # Recent activities
        recent_training = TrainingSession.query.order_by(TrainingSession.created_at.desc()).limit(5).all()
        recent_vet_visits = VeterinaryVisit.query.order_by(VeterinaryVisit.created_at.desc()).limit(5).all()
        
    else:  # PROJECT_MANAGER
        # Only show data assigned to this manager
        assigned_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).all()
        assigned_employees = Employee.query.filter_by(assigned_to_user_id=current_user.id).all()
        assigned_projects = Project.query.filter_by(manager_id=current_user.id).all()
        
        stats['total_dogs'] = len(assigned_dogs)
        stats['active_dogs'] = len([d for d in assigned_dogs if d.current_status == DogStatus.ACTIVE])
        stats['total_employees'] = len(assigned_employees)
        stats['active_employees'] = len([e for e in assigned_employees if e.is_active])
        stats['total_projects'] = len(assigned_projects)
        
        # Recent activities for assigned dogs only
        dog_ids = [d.id for d in assigned_dogs]
        recent_training = TrainingSession.query.filter(TrainingSession.dog_id.in_(dog_ids)).order_by(TrainingSession.created_at.desc()).limit(5).all()
        recent_vet_visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(dog_ids)).order_by(VeterinaryVisit.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', stats=stats, recent_training=recent_training, recent_vet_visits=recent_vet_visits)

# Dog management routes
@main_bp.route('/dogs')
@login_required
def dogs_list():
    from datetime import date
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.order_by(Dog.name).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).order_by(Dog.name).all()
    
    return render_template('dogs/list.html', dogs=dogs, today=date.today())

@main_bp.route('/dogs/add', methods=['GET', 'POST'])
@login_required
def dogs_add():
    if request.method == 'POST':
        try:
            # Handle photo upload
            photo_filename = None
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if allowed_file(photo.filename):
                    # Create unique filename
                    photo_filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
                    photo.save(photo_path)
            
            # Determine who the dog should be assigned to
            assigned_to_user_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            
            dog = Dog(
                name=request.form['name'],
                breed=request.form['breed'],
                gender=DogGender(request.form['gender']),
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form['date_of_birth'] else None,
                color=request.form.get('color'),
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                height=float(request.form['height']) if request.form.get('height') else None,
                microchip_id=request.form.get('microchip_id'),
                current_status=DogStatus.ACTIVE,
                health_notes=request.form.get('health_notes'),
                training_notes=request.form.get('training_notes'),
                photo_path=photo_filename,
                assigned_to_user_id=assigned_to_user_id
            )
            
            db.session.add(dog)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Dog', dog.id, f'أضيف كلب جديد: {dog.name}', None, {'name': dog.name, 'breed': dog.breed})
            flash('تم إضافة الكلب بنجاح', 'success')
            return redirect(url_for('main.dogs_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الكلب: {str(e)}', 'error')
    
    return render_template('dogs/add.html', genders=DogGender)

@main_bp.route('/dogs/<dog_id>')
@login_required
def dogs_view(dog_id):
    try:
        dog_uuid = uuid.UUID(dog_id)
        dog = Dog.query.get_or_404(dog_uuid)
    except ValueError:
        flash('معرف الكلب غير صحيح', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and dog.assigned_to_user_id != current_user.id:
        flash('غير مسموح لك بعرض بيانات هذا الكلب', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Get related data
    training_sessions = TrainingSession.query.filter_by(dog_id=dog_uuid).order_by(TrainingSession.created_at.desc()).all()
    vet_visits = VeterinaryVisit.query.filter_by(dog_id=dog_uuid).order_by(VeterinaryVisit.created_at.desc()).all()
    breeding_cycles = BreedingCycle.query.filter_by(dog_id=dog_uuid).order_by(BreedingCycle.created_at.desc()).all()
    
    return render_template('dogs/view.html', dog=dog, training_sessions=training_sessions, 
                         vet_visits=vet_visits, breeding_cycles=breeding_cycles)

@main_bp.route('/dogs/<dog_id>/edit', methods=['GET', 'POST'])
@login_required
def dogs_edit(dog_id):
    try:
        dog_uuid = uuid.UUID(dog_id)
        dog = Dog.query.get_or_404(dog_uuid)
    except ValueError:
        flash('معرف الكلب غير صحيح', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and dog.assigned_to_user_id != current_user.id:
        flash('غير مسموح لك بتعديل بيانات هذا الكلب', 'error')
        return redirect(url_for('main.dogs_list'))
    
    if request.method == 'POST':
        try:
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if allowed_file(photo.filename):
                    # Delete old photo if exists
                    if dog.photo_path:
                        old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dog.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Save new photo
                    photo_filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
                    photo.save(photo_path)
                    dog.photo_path = photo_filename
            
            # Update dog data
            dog.name = request.form['name']
            dog.breed = request.form['breed']
            dog.gender = DogGender(request.form['gender'])
            dog.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form['date_of_birth'] else None
            dog.color = request.form.get('color')
            dog.weight = float(request.form['weight']) if request.form.get('weight') else None
            dog.height = float(request.form['height']) if request.form.get('height') else None
            dog.microchip_id = request.form.get('microchip_id')
            dog.current_status = DogStatus(request.form['current_status'])
            dog.health_notes = request.form.get('health_notes')
            dog.training_notes = request.form.get('training_notes')
            
            db.session.commit()
            
            log_audit(current_user.id, 'UPDATE', 'Dog', str(dog.id), {'name': dog.name})
            flash('تم تحديث بيانات الكلب بنجاح', 'success')
            return redirect(url_for('main.dogs_view', dog_id=dog_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الكلب: {str(e)}', 'error')
    
    return render_template('dogs/edit.html', dog=dog, genders=DogGender, statuses=DogStatus)

# Employee management routes
@main_bp.route('/employees')
@login_required
def employees_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.order_by(Employee.name).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id).order_by(Employee.name).all()
    
    return render_template('employees/list.html', employees=employees)

@main_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
def employees_add():
    if request.method == 'POST':
        try:
            # Determine who the employee should be assigned to
            assigned_to_user_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            
            employee = Employee(
                name=request.form['name'],
                employee_id=request.form['employee_id'],
                role=EmployeeRole(request.form['role']),
                contact_info=request.form.get('contact_info'),
                hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None,
                is_active=True,
                assigned_to_user_id=assigned_to_user_id
            )
            
            db.session.add(employee)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Employee', str(employee.id), {'name': employee.name, 'role': employee.role.value})
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
    
    return render_template('employees/add.html', roles=EmployeeRole)

@main_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
def employees_edit(employee_id):
    try:
        employee_uuid = uuid.UUID(employee_id)
        employee = Employee.query.get_or_404(employee_uuid)
    except ValueError:
        flash('معرف الموظف غير صحيح', 'error')
        return redirect(url_for('main.employees_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and employee.assigned_to_user_id != current_user.id:
        flash('غير مسموح لك بتعديل بيانات هذا الموظف', 'error')
        return redirect(url_for('main.employees_list'))
    
    if request.method == 'POST':
        try:
            employee.name = request.form['name']
            employee.employee_id = request.form['employee_id']
            employee.role = EmployeeRole(request.form['role'])
            employee.contact_info = request.form.get('contact_info')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None
            employee.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            log_audit(current_user.id, 'UPDATE', 'Employee', str(employee.id), {'name': employee.name})
            flash('تم تحديث بيانات الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الموظف: {str(e)}', 'error')
    
    return render_template('employees/edit.html', employee=employee, roles=EmployeeRole)

# Training routes
@main_bp.route('/training')
@login_required
def training_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        sessions = TrainingSession.query.order_by(TrainingSession.created_at.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        sessions = TrainingSession.query.filter(TrainingSession.dog_id.in_(assigned_dog_ids)).order_by(TrainingSession.created_at.desc()).all()
    
    return render_template('training/list.html', sessions=sessions)

@main_bp.route('/training/add', methods=['GET', 'POST'])
@login_required
def training_add():
    if request.method == 'POST':
        try:
            session = TrainingSession(
                dog_id=request.form['dog_id'],
                trainer_id=request.form['trainer_id'],
                category=TrainingCategory(request.form['category']),
                duration_minutes=int(request.form['duration_minutes']),
                description=request.form['description'],
                progress_notes=request.form.get('progress_notes'),
                rating=int(request.form['rating']) if request.form.get('rating') else None
            )
            
            db.session.add(session)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'TrainingSession', session.id, f'جلسة تدريب جديدة للكلب {session.dog.name}', None, {'category': session.category.value})
            flash('تم تسجيل جلسة التدريب بنجاح', 'success')
            return redirect(url_for('main.training_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل جلسة التدريب: {str(e)}', 'error')
    
    # Get available dogs and employees for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        trainers = Employee.query.filter_by(is_active=True).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        trainers = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    return render_template('training/add.html', dogs=dogs, trainers=trainers, categories=TrainingCategory)

# Veterinary routes
@main_bp.route('/veterinary')
@login_required
def veterinary_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        visits = VeterinaryVisit.query.order_by(VeterinaryVisit.created_at.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(assigned_dog_ids)).order_by(VeterinaryVisit.created_at.desc()).all()
    
    return render_template('veterinary/list.html', visits=visits)

@main_bp.route('/veterinary/add', methods=['GET', 'POST'])
@login_required
def veterinary_add():
    if request.method == 'POST':
        try:
            visit = VeterinaryVisit(
                dog_id=request.form['dog_id'],
                veterinarian_id=request.form['veterinarian_id'],
                visit_type=VisitType(request.form['visit_type']),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                medications=request.form.get('medications'),
                cost=float(request.form['cost']) if request.form.get('cost') else None,
                notes=request.form.get('notes'),
                follow_up_required='follow_up_required' in request.form,
                follow_up_date=datetime.strptime(request.form['follow_up_date'], '%Y-%m-%d').date() if request.form.get('follow_up_date') else None
            )
            
            db.session.add(visit)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'VeterinaryVisit', visit.id, f'زيارة بيطرية جديدة للكلب {visit.dog.name}', None, {'visit_type': visit.visit_type.value})
            flash('تم تسجيل الزيارة البيطرية بنجاح', 'success')
            return redirect(url_for('main.veterinary_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الزيارة البيطرية: {str(e)}', 'error')
    
    # Get available dogs and vets for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        vets = Employee.query.filter_by(role=EmployeeRole.VET, is_active=True).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        vets = Employee.query.filter_by(assigned_to_user_id=current_user.id, role=EmployeeRole.VET, is_active=True).all()
    
    return render_template('veterinary/add.html', dogs=dogs, vets=vets, visit_types=VisitType)

# Breeding routes
@main_bp.route('/breeding')
@login_required
def breeding_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        cycles = BreedingCycle.query.order_by(BreedingCycle.created_at.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        cycles = BreedingCycle.query.filter(BreedingCycle.dog_id.in_(assigned_dog_ids)).order_by(BreedingCycle.created_at.desc()).all()
    
    return render_template('breeding/index.html', cycles=cycles)

@main_bp.route('/breeding/add', methods=['GET', 'POST'])
@login_required
def breeding_add():
    if request.method == 'POST':
        try:
            cycle = BreedingCycle(
                dog_id=request.form['dog_id'],
                cycle_type=BreedingCycleType(request.form['cycle_type']),
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
                partner_dog_id=request.form.get('partner_dog_id') if request.form.get('partner_dog_id') else None,
                result=BreedingResult(request.form['result']) if request.form.get('result') else None,
                notes=request.form.get('notes')
            )
            
            db.session.add(cycle)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'BreedingCycle', cycle.id, f'دورة تربية جديدة للكلب {cycle.dog.name}', None, {'cycle_type': cycle.cycle_type.value})
            flash('تم تسجيل دورة التربية بنجاح', 'success')
            return redirect(url_for('main.breeding_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل دورة التربية: {str(e)}', 'error')
    
    # Get available dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('breeding/add.html', dogs=dogs, cycle_types=BreedingCycleType, results=BreedingResult)

# Individual breeding component routes
@main_bp.route('/breeding/maturity')
@login_required
def maturity_list():
    return render_template('breeding/maturity_list.html')

@main_bp.route('/breeding/heat-cycles')
@login_required  
def heat_cycles_list():
    return render_template('breeding/heat_cycles_list.html')

@main_bp.route('/breeding/mating')
@login_required
def mating_list():
    return render_template('breeding/mating_list.html')

@main_bp.route('/breeding/pregnancy')
@login_required
def pregnancy_list():
    return render_template('breeding/pregnancy_list.html')

@main_bp.route('/breeding/delivery')
@login_required
def delivery_list():
    return render_template('breeding/delivery_list.html')

@main_bp.route('/breeding/puppies')
@login_required
def puppies_list():
    return render_template('breeding/puppies_list.html')

@main_bp.route('/breeding/puppy-training')
@login_required
def puppy_training_list():
    return render_template('breeding/puppy_training_list.html')

# Project routes (without attendance/assignment functionality)
@main_bp.route('/projects')
@login_required
def projects():
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.filter_by(manager_id=current_user.id).order_by(Project.created_at.desc()).all()
    
    # Calculate stats for the modern view
    active_count = sum(1 for p in projects if p.status == ProjectStatus.ACTIVE)
    planned_count = sum(1 for p in projects if p.status == ProjectStatus.PLANNED)
    completed_count = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)
    cancelled_count = sum(1 for p in projects if p.status == ProjectStatus.CANCELLED)
    total_count = len(projects)
    
    # Priority counts
    high_priority_count = sum(1 for p in projects if p.priority == 'HIGH')
    medium_priority_count = sum(1 for p in projects if p.priority == 'MEDIUM')
    low_priority_count = sum(1 for p in projects if p.priority == 'LOW')
    
    return render_template('projects/modern_list.html', 
                         projects=projects,
                         active_count=active_count,
                         planned_count=planned_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count,
                         total_count=total_count,
                         high_priority_count=high_priority_count,
                         medium_priority_count=medium_priority_count,
                         low_priority_count=low_priority_count)

@main_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def project_add():
    if request.method == 'POST':
        try:
            # Determine the manager ID
            manager_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else request.form.get('manager_id')
            
            # Generate unique project code
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            project = Project(
                name=request.form['name'],
                code=code,
                description=request.form.get('description'),
                main_task=request.form.get('main_task'),
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                expected_completion_date=datetime.strptime(request.form['expected_completion_date'], '%Y-%m-%d').date() if request.form.get('expected_completion_date') else None,
                status=ProjectStatus.PLANNED,
                project_manager_id=manager_id,
                location=request.form.get('location'),
                mission_type=request.form.get('mission_type'),
                priority=request.form.get('priority', 'MEDIUM')
            )
            
            db.session.add(project)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Project', project.id, f'مشروع جديد: {project.name}', None, {'name': project.name})
            flash('تم إنشاء المشروع بنجاح', 'success')
            return redirect(url_for('main.projects'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء المشروع: {str(e)}', 'error')
    
    # Get available data for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()
    else:
        managers = []  # PROJECT_MANAGER users can only assign to themselves
    
    return render_template('projects/add.html', managers=managers)

# Project Dashboard Route (without attendance statistics)
@main_bp.route('/projects/<project_id>/dashboard')
@login_required
def project_dashboard(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    # Get dashboard statistics with new assignment system
    dog_assignments = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).count()
    active_dog_assignments = dog_assignments  # All are active since we filter by is_active=True
    
    employee_assignments = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).count()
    active_employee_assignments = employee_assignments  # All are active since we filter by is_active=True
    
    # Incident statistics
    total_incidents = Incident.query.filter_by(project_id=project_uuid).count()
    resolved_incidents = Incident.query.filter_by(project_id=project_uuid, resolved=True).count()
    pending_incidents = total_incidents - resolved_incidents
    
    # Suspicion statistics
    total_suspicions = Suspicion.query.filter_by(project_id=project_uuid).count()
    confirmed_suspicions = Suspicion.query.filter_by(project_id=project_uuid, evidence_collected=True).count()
    
    # Evaluation statistics
    total_evaluations = PerformanceEvaluation.query.filter_by(project_id=project_uuid).count()
    
    stats = {
        'dog_assignments': dog_assignments,
        'active_dog_assignments': active_dog_assignments,
        'employee_assignments': employee_assignments,
        'active_employee_assignments': active_employee_assignments,
        'total_incidents': total_incidents,
        'resolved_incidents': resolved_incidents,
        'pending_incidents': pending_incidents,
        'total_suspicions': total_suspicions,
        'confirmed_suspicions': confirmed_suspicions,
        'total_evaluations': total_evaluations
    }
    
    # Get assignment objects for display in resources section
    assigned_dogs = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).options(db.joinedload(ProjectAssignment.dog)).all()
    assigned_employees = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).options(db.joinedload(ProjectAssignment.employee)).all()
    
    # Get project managers for the quick update modal
    project_managers = Employee.query.filter_by(role=EmployeeRole.PROJECT_MANAGER, is_active=True).all()
    
    # Recent activities
    recent_incidents = Incident.query.filter_by(project_id=project_uuid).order_by(Incident.incident_date.desc()).limit(5).all()
    recent_suspicions = Suspicion.query.filter_by(project_id=project_uuid).order_by(Suspicion.discovery_date.desc()).limit(5).all()
    recent_evaluations = PerformanceEvaluation.query.filter_by(project_id=project_uuid).order_by(PerformanceEvaluation.evaluation_date.desc()).limit(5).all()
    
    return render_template('projects/modern_dashboard.html', 
                         project=project, 
                         stats=stats,
                         assigned_dogs=assigned_dogs,
                         assigned_employees=assigned_employees,
                         project_managers=project_managers,
                         recent_incidents=recent_incidents,
                         recent_suspicions=recent_suspicions,
                         recent_evaluations=recent_evaluations)

# Project Status Management
@main_bp.route('/projects/<project_id>/status', methods=['POST'])
@login_required
def project_status_change(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بتعديل حالة هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    new_status = request.form.get('status')
    if new_status:
        old_status = project.status.value
        project.status = ProjectStatus(new_status)
        
        # Set finish date if completed
        if project.status == ProjectStatus.COMPLETED and not project.actual_end_date:
            project.actual_end_date = date.today()
        
        db.session.commit()
        
        log_audit(current_user.id, 'UPDATE', 'Project', str(project.id), 
                 {'status_changed': f'من {old_status} إلى {project.status.value}'})
        flash('تم تحديث حالة المشروع بنجاح', 'success')
    
    return redirect(url_for('main.projects'))

# Project Dog Management
@main_bp.route('/projects/<project_id>/dogs/add', methods=['POST'])
@login_required
def project_dog_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بإضافة كلاب لهذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    dog_id = request.form.get('dog_id')
    if dog_id:
        # Check if already assigned
        existing = ProjectDog.query.filter_by(project_id=project_uuid, dog_id=dog_id).first()
        if existing:
            flash('هذا الكلب مُعيَّن بالفعل للمشروع', 'error')
        else:
            project_dog = ProjectDog(
                project_id=project_uuid,
                dog_id=dog_id,
                is_active=True
            )
            db.session.add(project_dog)
            db.session.commit()
            
            dog = Dog.query.get(dog_id)
            log_audit(current_user.id, AuditAction.CREATE, 'ProjectDog', project_dog.id, f'تعيين كلب {dog.name} للمشروع {project.name}', None, {'project': project.name, 'dog': dog.name})
            flash('تم تعيين الكلب للمشروع بنجاح', 'success')
    
    return redirect(url_for('main.project_dashboard', project_id=project_id))

# Project Manager Update Route
@main_bp.route('/projects/<project_id>/manager/update', methods=['POST'])
@login_required
def project_manager_update(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('غير مسموح لك بتعديل مدير المشروع', 'error')
        return redirect(url_for('main.project_dashboard', project_id=project_id))
    
    project_manager_id = request.form.get('project_manager_id')
    
    try:
        if project_manager_id:
            # Verify it's actually a project manager
            manager = Employee.query.get(project_manager_id)
            if manager and manager.role == EmployeeRole.PROJECT_MANAGER:
                old_manager = project.project_manager.name if project.project_manager else 'غير معين'
                project.project_manager_id = project_manager_id
                
                # Log the change
                log_audit(current_user.id, AuditAction.UPDATE, 'Project', str(project.id), 
                         f'تغيير مدير المشروع من {old_manager} إلى {manager.name}', 
                         None, {'old_manager': old_manager, 'new_manager': manager.name})
                
                flash('تم تحديث مدير المشروع بنجاح', 'success')
            else:
                flash('الموظف المحدد ليس مدير مشروع', 'error')
        else:
            # Remove project manager
            old_manager = project.project_manager.name if project.project_manager else 'غير معين'
            project.project_manager_id = None
            
            # Log the change
            log_audit(current_user.id, AuditAction.UPDATE, 'Project', str(project.id), 
                     f'إزالة مدير المشروع {old_manager}', 
                     None, {'old_manager': old_manager, 'new_manager': 'غير معين'})
            
            flash('تم إزالة مدير المشروع', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث مدير المشروع: {str(e)}', 'error')
    
    return redirect(url_for('main.project_dashboard', project_id=project_id))

# Project Assignments Management
@main_bp.route('/projects/<project_id>/assignments')
@login_required
def project_assignments(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    # Get current assignments
    dog_assignments = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).all()
    employee_assignments = ProjectAssignment.query.filter_by(project_id=project_uuid, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).all()
    
    # Get available dogs (not assigned to other active projects) and employees for assignment
    # Get dogs that are either not assigned or not assigned to active projects
    assigned_dog_ids = db.session.query(ProjectAssignment.dog_id).join(Project).filter(
        ProjectAssignment.is_active == True,
        ProjectAssignment.dog_id.isnot(None),
        Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED]),
        Project.id != project_uuid  # Exclude current project
    ).subquery()
    
    available_dogs = Dog.query.filter(
        Dog.current_status == DogStatus.ACTIVE,
        ~Dog.id.in_(assigned_dog_ids)
    ).all()
    
    # Exclude project managers from regular employee assignments
    available_employees = Employee.query.filter(
        Employee.is_active == True,
        Employee.role != EmployeeRole.PROJECT_MANAGER
    ).all()
    
    # Get project managers (employees with PROJECT_MANAGER role)
    project_managers = Employee.query.filter_by(role=EmployeeRole.PROJECT_MANAGER, is_active=True).all()
    
    return render_template('projects/assignments.html', 
                         project=project,
                         dog_assignments=dog_assignments,
                         employee_assignments=employee_assignments,
                         available_dogs=available_dogs,
                         available_employees=available_employees,
                         project_managers=project_managers)

@main_bp.route('/projects/<project_id>/assignments/add', methods=['POST'])
@login_required
def project_assignment_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بإضافة تعيينات لهذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    assignment_type = request.form.get('assignment_type')
    notes = request.form.get('notes', '')
    
    try:
        if assignment_type == 'dog':
            dog_ids = request.form.getlist('dog_ids')
            for dog_id in dog_ids:
                if dog_id:
                    # Check if already assigned to this project
                    existing = ProjectAssignment.query.filter_by(
                        project_id=project_uuid, 
                        dog_id=dog_id,
                        is_active=True
                    ).first()
                    
                    if existing:
                        flash(f'الكلب معيّن بالفعل لهذا المشروع', 'warning')
                        continue
                    
                    # Check if dog is assigned to another active project
                    active_assignment = ProjectAssignment.query.join(Project).filter(
                        ProjectAssignment.dog_id == dog_id,
                        ProjectAssignment.is_active == True,
                        Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])
                    ).first()
                    
                    if active_assignment:
                        dog = Dog.query.get(dog_id)
                        flash(f'الكلب {dog.name} معيّن بالفعل لمشروع نشط آخر: {active_assignment.project.name}', 'error')
                        continue
                    
                    assignment = ProjectAssignment(
                        project_id=project_uuid,
                        dog_id=dog_id,
                        notes=notes,
                        is_active=True
                    )
                    db.session.add(assignment)
                        
        elif assignment_type == 'employee':
            employee_ids = request.form.getlist('employee_ids')
            for employee_id in employee_ids:
                if employee_id:
                    # Verify employee is not a project manager
                    employee = Employee.query.get(employee_id)
                    if employee and employee.role == EmployeeRole.PROJECT_MANAGER:
                        flash('لا يمكن تعيين مدراء المشاريع كموظفين عاديين. استخدم قسم مدير المشروع.', 'error')
                        continue
                        
                    # Check if already assigned
                    existing = ProjectAssignment.query.filter_by(
                        project_id=project_uuid, 
                        employee_id=employee_id,
                        is_active=True
                    ).first()
                    
                    if not existing:
                        assignment = ProjectAssignment(
                            project_id=project_uuid,
                            employee_id=employee_id,
                            notes=notes,
                            is_active=True
                        )
                        db.session.add(assignment)
        
        # Handle project manager assignment separately 
        elif assignment_type == 'project_manager':
            project_manager_id = request.form.get('project_manager_id')
            if project_manager_id:
                # Verify it's actually a project manager
                manager = Employee.query.get(project_manager_id)
                if manager and manager.role == EmployeeRole.PROJECT_MANAGER:
                    project.project_manager_id = project_manager_id
                    flash('تم تحديث مسؤول المشروع بنجاح', 'success')
                else:
                    flash('الموظف المحدد ليس مسؤول مشروع', 'error')
            else:
                # Remove project manager
                project.project_manager_id = None
                flash('تم إزالة مسؤول المشروع', 'success')
        
        db.session.commit()
        log_audit(current_user.id, AuditAction.CREATE, 'ProjectAssignment', project.id, f'تعيين جديد للمشروع {project.name}', None, {'assignment_type': assignment_type})
        flash('تم تعيين المهام بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التعيين: {str(e)}', 'error')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

@main_bp.route('/projects/<project_id>/assignments/<assignment_id>/remove', methods=['POST'])
@login_required
def project_assignment_remove(project_id, assignment_id):
    try:
        project_uuid = uuid.UUID(project_id)
        assignment_uuid = uuid.UUID(assignment_id)
        project = Project.query.get_or_404(project_uuid)
        assignment = ProjectAssignment.query.get_or_404(assignment_uuid)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بإزالة التعيينات من هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    try:
        assignment.is_active = False
        assignment.unassigned_date = date.today()
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.DELETE, 'ProjectAssignment', assignment.id, f'حذف تعيين من المشروع {project.name}', None, {'project': project.name})
        flash('تم إزالة التعيين بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إزالة التعيين: {str(e)}', 'error')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

@main_bp.route('/projects/<project_id>/assignments/<assignment_id>/edit', methods=['POST'])
@login_required
def project_assignment_edit(project_id, assignment_id):
    try:
        project_uuid = uuid.UUID(project_id)
        assignment_uuid = uuid.UUID(assignment_id)
        project = Project.query.get_or_404(project_uuid)
        assignment = ProjectAssignment.query.get_or_404(assignment_uuid)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بتعديل التعيينات في هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    try:
        assignment.notes = request.form.get('notes', assignment.notes)
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.UPDATE, 'ProjectAssignment', assignment.id, f'تحديث ملاحظات التعيين', None, {'notes_updated': True})
        flash('تم تحديث التعيين بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث التعيين: {str(e)}', 'error')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

# Enhanced Projects Section - Incidents
@main_bp.route('/projects/<project_id>/incidents')
@login_required
def project_incidents(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    incidents = Incident.query.filter_by(project_id=project_uuid).order_by(Incident.incident_date.desc()).all()
    
    return render_template('projects/incidents.html', project=project, incidents=incidents)

@main_bp.route('/projects/<project_id>/incidents/add', methods=['GET', 'POST'])
@login_required
def project_incident_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            incident = Incident(
                project_id=project_uuid,
                incident_date=datetime.strptime(request.form['incident_date'], '%Y-%m-%d').date(),
                incident_time=datetime.strptime(request.form['incident_time'], '%H:%M').time() if request.form.get('incident_time') else None,
                incident_type=request.form['incident_type'],
                description=request.form['description'],
                location=request.form.get('location'),
                severity=request.form['severity'],
                reported_by=request.form.get('reported_by'),
                witnesses=request.form.get('witnesses'),
                immediate_action_taken=request.form.get('immediate_action_taken'),
                resolved=False
            )
            
            db.session.add(incident)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Incident', incident.id, f'حادث جديد في المشروع {project.name}', None, {'type': incident.incident_type, 'severity': incident.severity})
            flash('تم تسجيل الحادث بنجاح', 'success')
            return redirect(url_for('main.project_incidents', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الحادث: {str(e)}', 'error')
    
    return render_template('projects/incident_add.html', project=project)

# Enhanced Projects Section - Suspicions
@main_bp.route('/projects/<project_id>/suspicions')
@login_required
def project_suspicions(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    suspicions = Suspicion.query.filter_by(project_id=project_uuid).order_by(Suspicion.discovery_date.desc()).all()
    
    return render_template('projects/suspicions.html', project=project, suspicions=suspicions)

@main_bp.route('/projects/<project_id>/suspicions/add', methods=['GET', 'POST'])
@login_required
def project_suspicion_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            suspicion = Suspicion(
                project_id=project_uuid,
                discovery_date=datetime.strptime(request.form['discovery_date'], '%Y-%m-%d').date(),
                discovery_time=datetime.strptime(request.form['discovery_time'], '%H:%M').time() if request.form.get('discovery_time') else None,
                suspicion_type=request.form['suspicion_type'],
                description=request.form['description'],
                location=request.form.get('location'),
                risk_level=request.form['risk_level'],
                discovered_by=request.form.get('discovered_by'),
                initial_assessment=request.form.get('initial_assessment'),
                recommended_action=request.form.get('recommended_action'),
                evidence_collected=False
            )
            
            db.session.add(suspicion)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Suspicion', str(suspicion.id), 
                     {'project': project.name, 'type': suspicion.suspicion_type, 'risk_level': suspicion.risk_level})
            flash('تم تسجيل حالة الاشتباه بنجاح', 'success')
            return redirect(url_for('main.project_suspicions', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل حالة الاشتباه: {str(e)}', 'error')
    
    return render_template('projects/suspicion_add.html', project=project)

# Enhanced Projects Section - Evaluations
@main_bp.route('/projects/<project_id>/evaluations')
@login_required
def project_evaluations(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    evaluations = PerformanceEvaluation.query.filter_by(project_id=project_uuid).order_by(PerformanceEvaluation.evaluation_date.desc()).all()
    
    return render_template('projects/evaluations.html', project=project, evaluations=evaluations)

@main_bp.route('/projects/<project_id>/evaluations/add', methods=['GET', 'POST'])
@login_required
def project_evaluation_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.project_manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            # Determine target based on form selection
            target_employee_id = request.form.get('target_employee_id') if request.form.get('target_type') == 'EMPLOYEE' else None
            target_dog_id = request.form.get('target_dog_id') if request.form.get('target_type') == 'DOG' else None
            
            evaluation = PerformanceEvaluation(
                project_id=project_uuid,
                evaluation_date=datetime.strptime(request.form['evaluation_date'], '%Y-%m-%d').date(),
                evaluator_id=current_user.id,
                target_type=TargetType(request.form['target_type']),
                target_employee_id=target_employee_id,
                target_dog_id=target_dog_id,
                rating=PerformanceRating(request.form['rating']),
                performance_criteria=request.form.get('performance_criteria'),
                strengths=request.form.get('strengths'),
                areas_for_improvement=request.form.get('areas_for_improvement'),
                comments=request.form.get('comments'),
                recommendations=request.form.get('recommendations')
            )
            
            db.session.add(evaluation)
            db.session.commit()
            
            target_name = evaluation.target_employee.name if evaluation.target_employee else evaluation.target_dog.name
            log_audit(current_user.id, 'CREATE', 'PerformanceEvaluation', str(evaluation.id), 
                     {'project': project.name, 'target': target_name, 'rating': evaluation.rating.value})
            flash('تم تسجيل التقييم بنجاح', 'success')
            return redirect(url_for('main.project_evaluations', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل التقييم: {str(e)}', 'error')
    
    # Get employees and dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.filter_by(is_active=True).all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('projects/evaluation_add.html', project=project, employees=employees, dogs=dogs, 
                         target_types=TargetType, ratings=PerformanceRating)

# Reports route
@main_bp.route('/reports')
@login_required
def reports_index():
    # Calculate statistics for the reports dashboard
    stats = {
        'total_dogs': Dog.query.count(),
        'active_dogs': Dog.query.filter_by(current_status=DogStatus.ACTIVE).count(),
        'total_employees': Employee.query.filter_by(is_active=True).count(),
        'total_projects': Project.query.count(),
        'active_projects': Project.query.filter_by(status=ProjectStatus.ACTIVE).count(),
        'completed_projects': Project.query.filter_by(status=ProjectStatus.COMPLETED).count(),
        'total_training_sessions': TrainingSession.query.count(),
        'total_vet_visits': VeterinaryVisit.query.count()
    }
    
    return render_template('reports/index.html', stats=stats)


# ============================================================================
# ATTENDANCE SYSTEM ROUTES
# ============================================================================

@main_bp.route('/projects/<project_id>/attendance')
@login_required
def project_attendance(project_id):
    """Main attendance page for a project"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            flash('ليس لديك صلاحية للوصول إلى هذا المشروع', 'error')
            return redirect(url_for('main.projects'))
    
    # Get project shifts
    shifts = ProjectShift.query.filter_by(project_id=project_id, is_active=True).all()
    
    # Get current date for default selection
    today = date.today()
    
    return render_template('projects/attendance.html', 
                         project=project, 
                         shifts=shifts, 
                         today=today,
                         EntityType=EntityType,
                         AttendanceStatus=AttendanceStatus,
                         AbsenceReason=AbsenceReason)

@main_bp.route('/projects/<project_id>/shifts', methods=['GET', 'POST'])
@login_required
def project_shifts(project_id):
    """Manage project shifts"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            flash('ليس لديك صلاحية للوصول إلى هذا المشروع', 'error')
            return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            shift = ProjectShift(
                project_id=project_id,
                name=request.form['name'],
                start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(request.form['end_time'], '%H:%M').time()
            )
            db.session.add(shift)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'ProjectShift', shift.id, 
                     description=f'Created shift {shift.name} for project {project.name}')
            
            flash('تم إنشاء الوردية بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء الوردية: {str(e)}', 'error')
    
    shifts = ProjectShift.query.filter_by(project_id=project_id).all()
    return render_template('projects/shifts.html', project=project, shifts=shifts)

@main_bp.route('/projects/<project_id>/attendance/record', methods=['POST'])
@login_required
def record_attendance(project_id):
    """Record attendance for a specific date and shift"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذا المشروع'}), 403
    
    try:
        shift_id = request.json['shift_id']
        attendance_date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
        entity_type = request.json['entity_type']
        entity_id = request.json['entity_id']
        status = request.json['status']
        absence_reason = request.json.get('absence_reason')
        late_reason = request.json.get('late_reason')
        notes = request.json.get('notes', '')
        
        # Validate that entity is assigned to this shift
        assignment = ProjectShiftAssignment.query.filter_by(
            shift_id=shift_id,
            entity_type=EntityType(entity_type),
            entity_id=entity_id,
            is_active=True
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'هذا العضو غير مُعيَّن لهذه الوردية'}), 400
        
        # Validate absence reason for absent status
        if status == 'ABSENT' and not absence_reason:
            return jsonify({'success': False, 'error': 'يجب تحديد سبب الغياب'}), 400
        
        # Check if attendance record already exists
        existing_record = ProjectAttendance.query.filter_by(
            project_id=project_id,
            shift_id=shift_id,
            date=attendance_date,
            entity_type=EntityType(entity_type),
            entity_id=entity_id
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.status = AttendanceStatus(status)
            existing_record.absence_reason = AbsenceReason(absence_reason) if absence_reason else None
            existing_record.late_reason = late_reason if status == 'LATE' else None
            existing_record.notes = notes
            existing_record.updated_at = datetime.utcnow()
            attendance_record = existing_record
        else:
            # Create new record
            attendance_record = ProjectAttendance(
                project_id=project_id,
                shift_id=shift_id,
                date=attendance_date,
                entity_type=EntityType(entity_type),
                entity_id=entity_id,
                status=AttendanceStatus(status),
                absence_reason=AbsenceReason(absence_reason) if absence_reason else None,
                late_reason=late_reason if status == 'LATE' else None,
                notes=notes,
                recorded_by_user_id=current_user.id
            )
            db.session.add(attendance_record)
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.CREATE, 'ProjectAttendance', attendance_record.id,
                 description=f'Recorded attendance for {attendance_record.get_entity_name()}: {status}')
        
        return jsonify({'success': True, 'message': 'تم تسجيل الحضور بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/projects/<project_id>/shifts/<shift_id>/assignments', methods=['GET', 'POST'])
@login_required
def shift_assignments(project_id, shift_id):
    """Manage shift assignments"""
    project = Project.query.get_or_404(project_id)
    shift = ProjectShift.query.get_or_404(shift_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            flash('ليس لديك صلاحية للوصول إلى هذا المشروع', 'error')
            return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        entity_type = request.form['entity_type']
        entity_id = request.form['entity_id']
        
        try:
            # Check if entity is assigned to project using ProjectAssignment model
            if entity_type == 'EMPLOYEE':
                employee_assignment = ProjectAssignment.query.filter_by(
                    project_id=project_id,
                    employee_id=entity_id,
                    is_active=True
                ).first()
                if not employee_assignment:
                    flash('هذا الموظف غير مُعيَّن لهذا المشروع', 'error')
                    return redirect(request.url)
            elif entity_type == 'DOG':
                dog_assignment = ProjectAssignment.query.filter_by(
                    project_id=project_id,
                    dog_id=entity_id,
                    is_active=True
                ).first()
                if not dog_assignment:
                    flash('هذا الكلب غير مُعيَّن لهذا المشروع', 'error')
                    return redirect(request.url)
            
            # Create assignment
            assignment = ProjectShiftAssignment(
                shift_id=shift_id,
                entity_type=EntityType(entity_type),
                entity_id=entity_id,
                notes=request.form.get('notes', '')
            )
            db.session.add(assignment)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'ProjectShiftAssignment', assignment.id,
                     description=f'Assigned {assignment.get_entity_name()} to shift {shift.name}')
            
            flash('تم تعيين العضو للوردية بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في التعيين: {str(e)}', 'error')
    
    # Get current assignments
    assignments = ProjectShiftAssignment.query.filter_by(shift_id=shift_id, is_active=True).all()
    
    # Get available employees and dogs for assignment from ProjectAssignment model
    project_employee_assignments = ProjectAssignment.query.filter_by(
        project_id=project_id, 
        is_active=True
    ).filter(ProjectAssignment.employee_id.isnot(None)).all()
    
    project_dog_assignments = ProjectAssignment.query.filter_by(
        project_id=project_id, 
        is_active=True
    ).filter(ProjectAssignment.dog_id.isnot(None)).all()
    
    available_employees = [assignment.employee for assignment in project_employee_assignments if assignment.employee.is_active]
    available_dogs = [assignment.dog for assignment in project_dog_assignments if assignment.dog.current_status == DogStatus.ACTIVE]
    
    return render_template('projects/shift_assignments.html', 
                         project=project, 
                         shift=shift, 
                         assignments=assignments,
                         available_employees=available_employees,
                         available_dogs=available_dogs,
                         EntityType=EntityType)

@main_bp.route('/projects/<project_id>/attendance/data')
@login_required
def get_attendance_data(project_id):
    """Get attendance data for a specific date and shift"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا المشروع'}), 403
    
    shift_id = request.args.get('shift_id')
    attendance_date = request.args.get('date')
    search_query = request.args.get('search', '').lower()
    
    if not shift_id or not attendance_date:
        return jsonify({'error': 'معاملات مطلوبة مفقودة'}), 400
    
    try:
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        # Get all assignments for this shift
        assignments = ProjectShiftAssignment.query.filter_by(
            shift_id=shift_id, 
            is_active=True
        ).all()
        
        attendance_data = []
        
        for assignment in assignments:
            # Get existing attendance record
            attendance_record = ProjectAttendance.query.filter_by(
                project_id=project_id,
                shift_id=shift_id,
                date=attendance_date,
                entity_type=assignment.entity_type,
                entity_id=assignment.entity_id
            ).first()
            
            entity_name = assignment.get_entity_name()
            entity_code = assignment.get_entity_code()
            
            # Apply search filter
            if search_query and search_query not in entity_name.lower() and search_query not in entity_code.lower():
                continue
            
            data = {
                'assignment_id': str(assignment.id),
                'entity_type': assignment.entity_type.value,
                'entity_id': str(assignment.entity_id),
                'entity_name': entity_name,
                'entity_code': entity_code,
                'status': attendance_record.status.value if attendance_record else 'PRESENT',
                'absence_reason': attendance_record.absence_reason.value if attendance_record and attendance_record.absence_reason else '',
                'late_reason': attendance_record.late_reason if attendance_record else '',
                'notes': attendance_record.notes if attendance_record else ''
            }
            attendance_data.append(data)
        
        return jsonify({'data': attendance_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/projects/<project_id>/attendance/bulk', methods=['POST'])
@login_required
def bulk_attendance(project_id):
    """Bulk attendance operations"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            return jsonify({'success': False, 'error': 'ليس لديك صلاحية للوصول إلى هذا المشروع'}), 403
    
    try:
        action = request.json['action']
        shift_id = request.json['shift_id']
        attendance_date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
        
        # Get all assignments for this shift
        assignments = ProjectShiftAssignment.query.filter_by(
            shift_id=shift_id, 
            is_active=True
        ).all()
        
        updated_count = 0
        
        for assignment in assignments:
            # Determine status based on action
            if action == 'mark_all_present':
                status = AttendanceStatus.PRESENT
                absence_reason = None
                late_reason = None
            elif action == 'mark_all_absent':
                status = AttendanceStatus.ABSENT
                absence_reason = AbsenceReason(request.json.get('absence_reason', 'OTHER'))
                late_reason = None
            elif action == 'mark_all_late':
                status = AttendanceStatus.LATE
                absence_reason = None
                late_reason = request.json.get('late_reason', '')
            else:
                continue
            
            # Check if record exists
            existing_record = ProjectAttendance.query.filter_by(
                project_id=project_id,
                shift_id=shift_id,
                date=attendance_date,
                entity_type=assignment.entity_type,
                entity_id=assignment.entity_id
            ).first()
            
            if existing_record:
                existing_record.status = status
                existing_record.absence_reason = absence_reason
                existing_record.late_reason = late_reason
                existing_record.updated_at = datetime.utcnow()
            else:
                attendance_record = ProjectAttendance(
                    project_id=project_id,
                    shift_id=shift_id,
                    date=attendance_date,
                    entity_type=assignment.entity_type,
                    entity_id=assignment.entity_id,
                    status=status,
                    absence_reason=absence_reason,
                    late_reason=late_reason,
                    recorded_by_user_id=current_user.id
                )
                db.session.add(attendance_record)
            
            updated_count += 1
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.EDIT, 'ProjectAttendance', None,
                 description=f'Bulk attendance action: {action} for {updated_count} entities')
        
        return jsonify({'success': True, 'message': f'تم تحديث حضور {updated_count} عضو'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/projects/<project_id>/attendance/report')
@login_required  
def attendance_report(project_id):
    """Generate attendance report for a date range"""
    project = Project.query.get_or_404(project_id)
    
    # Check permissions
    if current_user.role == UserRole.PROJECT_MANAGER:
        if project.manager_id != current_user.id:
            flash('ليس لديك صلاحية للوصول إلى هذا المشروع', 'error')
            return redirect(url_for('main.projects'))
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        flash('يرجى تحديد تاريخ البداية والنهاية', 'error')
        return redirect(url_for('main.project_attendance', project_id=project_id))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get attendance records for the date range
        attendance_records = ProjectAttendance.query.filter(
            ProjectAttendance.project_id == project_id,
            ProjectAttendance.date >= start_date,
            ProjectAttendance.date <= end_date
        ).order_by(ProjectAttendance.date, ProjectAttendance.shift_id).all()
        
        # Generate basic CSV report since reportlab might not be available
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['التاريخ', 'الوردية', 'النوع', 'الاسم', 'الكود', 'الحالة', 'سبب الغياب', 'سبب التأخير', 'ملاحظات'])
        
        # Write data
        for record in attendance_records:
            writer.writerow([
                record.date.strftime('%Y-%m-%d'),
                record.shift.name if record.shift else '',
                'موظف' if record.entity_type == EntityType.EMPLOYEE else 'كلب',
                record.get_entity_name(),
                record.get_entity_code(),
                record.get_status_display(),
                record.get_absence_reason_display(),
                record.late_reason or '',
                record.notes or ''
            ])
        
        # Create response
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_report_{project.code}_{start_date}_{end_date}.csv'
        
        log_audit(current_user.id, AuditAction.EXPORT, 'AttendanceReport', project_id,
                 description=f'Generated attendance report for {start_date} to {end_date}')
        
        return response
        
    except Exception as e:
        flash(f'خطأ في توليد التقرير: {str(e)}', 'error')
    
    return redirect(url_for('main.project_attendance', project_id=project_id))

@main_bp.route('/projects/<project_id>/shifts/<shift_id>/assignments/<assignment_id>/remove', methods=['POST'])
@login_required
def remove_shift_assignment(project_id, shift_id, assignment_id):
    """Remove a shift assignment"""
    assignment = ProjectShiftAssignment.query.get_or_404(assignment_id)
    
    try:
        assignment.is_active = False
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.DELETE, 'ProjectShiftAssignment', assignment_id,
                 description=f'Removed {assignment.get_entity_name()} from shift')
        
        flash('تم إزالة التعيين بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إزالة التعيين: {str(e)}', 'error')
    
    return redirect(url_for('main.shift_assignments', project_id=project_id, shift_id=shift_id))

@main_bp.route('/projects/<project_id>/shifts/<shift_id>/assignments/<assignment_id>/edit', methods=['POST'])
@login_required
def edit_shift_assignment(project_id, shift_id, assignment_id):
    """Edit a shift assignment"""
    assignment = ProjectShiftAssignment.query.get_or_404(assignment_id)
    
    try:
        assignment.notes = request.form.get('notes', '')
        assignment.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.EDIT, 'ProjectShiftAssignment', assignment_id,
                 description=f'Updated notes for {assignment.get_entity_name()}')
        
        flash('تم تحديث التعيين بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث التعيين: {str(e)}', 'error')
    
    return redirect(url_for('main.shift_assignments', project_id=project_id, shift_id=shift_id))