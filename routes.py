from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import (Dog, Employee, TrainingSession, VeterinaryVisit, BreedingCycle, 
                   Project, AuditLog, UserRole, DogStatus, 
                   EmployeeRole, TrainingCategory, VisitType, BreedingCycleType, 
                   BreedingResult, ProjectStatus, AuditAction, DogGender, User,
                   MaturityStatus, HeatStatus, PregnancyStatus, ProjectDog, 
                   Incident, Suspicion, PerformanceEvaluation, 
                   ElementType, PerformanceRating, TargetType,
                   project_employee_assignment, project_dog_assignment)
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
            
            log_audit(current_user.id, 'CREATE', 'Dog', str(dog.id), {'name': dog.name, 'breed': dog.breed})
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
            
            log_audit(current_user.id, 'CREATE', 'TrainingSession', str(session.id), 
                     {'dog_id': str(session.dog_id), 'category': session.category.value})
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
            
            log_audit(current_user.id, 'CREATE', 'VeterinaryVisit', str(visit.id), 
                     {'dog_id': str(visit.dog_id), 'visit_type': visit.visit_type.value})
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
            
            log_audit(current_user.id, 'CREATE', 'BreedingCycle', str(cycle.id), 
                     {'dog_id': str(cycle.dog_id), 'cycle_type': cycle.cycle_type.value})
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
def projects_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        projects = Project.query.filter_by(manager_id=current_user.id).order_by(Project.created_at.desc()).all()
    
    return render_template('projects/list.html', projects=projects)

@main_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def projects_add():
    if request.method == 'POST':
        try:
            # Determine the manager ID
            manager_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else request.form.get('manager_id')
            
            project = Project(
                name=request.form['name'],
                description=request.form.get('description'),
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                expected_end_date=datetime.strptime(request.form['expected_end_date'], '%Y-%m-%d').date() if request.form.get('expected_end_date') else None,
                status=ProjectStatus.PLANNED,
                manager_id=manager_id,
                budget=float(request.form['budget']) if request.form.get('budget') else None,
                location=request.form.get('location'),
                objectives=request.form.get('objectives')
            )
            
            db.session.add(project)
            db.session.commit()
            
            # Add project dogs if any selected
            if request.form.getlist('dog_ids'):
                for dog_id in request.form.getlist('dog_ids'):
                    if dog_id:  # Make sure it's not empty
                        project_dog = ProjectDog(
                            project_id=project.id,
                            dog_id=dog_id,
                            is_active=True
                        )
                        db.session.add(project_dog)
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Project', str(project.id), {'name': project.name})
            flash('تم إنشاء المشروع بنجاح', 'success')
            return redirect(url_for('main.projects_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إنشاء المشروع: {str(e)}', 'error')
    
    # Get available data for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        managers = []  # PROJECT_MANAGER users can only assign to themselves
    
    return render_template('projects/add.html', dogs=dogs, managers=managers)

# Project Dashboard Route (without attendance statistics)
@main_bp.route('/projects/<project_id>/dashboard')
@login_required
def project_dashboard(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
    # Get dashboard statistics (without assignment/attendance stats)
    dog_assignments = ProjectDog.query.filter_by(project_id=project_uuid).count()
    
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
        'total_incidents': total_incidents,
        'resolved_incidents': resolved_incidents,
        'pending_incidents': pending_incidents,
        'total_suspicions': total_suspicions,
        'confirmed_suspicions': confirmed_suspicions,
        'total_evaluations': total_evaluations
    }
    
    # Recent activities
    recent_incidents = Incident.query.filter_by(project_id=project_uuid).order_by(Incident.incident_date.desc()).limit(5).all()
    recent_suspicions = Suspicion.query.filter_by(project_id=project_uuid).order_by(Suspicion.discovery_date.desc()).limit(5).all()
    recent_evaluations = PerformanceEvaluation.query.filter_by(project_id=project_uuid).order_by(PerformanceEvaluation.evaluation_date.desc()).limit(5).all()
    
    return render_template('projects/dashboard.html', 
                         project=project, 
                         stats=stats,
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بتعديل حالة هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
    
    return redirect(url_for('main.projects_list'))

# Project Dog Management
@main_bp.route('/projects/<project_id>/dogs/add', methods=['POST'])
@login_required
def project_dog_add(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بإضافة كلاب لهذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
            log_audit(current_user.id, 'CREATE', 'ProjectDog', str(project_dog.id), 
                     {'project': project.name, 'dog': dog.name})
            flash('تم تعيين الكلب للمشروع بنجاح', 'success')
    
    return redirect(url_for('main.project_dashboard', project_id=project_id))

# Enhanced Projects Section - Incidents
@main_bp.route('/projects/<project_id>/incidents')
@login_required
def project_incidents(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
            
            log_audit(current_user.id, 'CREATE', 'Incident', str(incident.id), 
                     {'project': project.name, 'type': incident.incident_type, 'severity': incident.severity})
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
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
    return render_template('reports/index.html')