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
            # Handle file uploads
            birth_certificate = None
            photo = None
            
            if 'birth_certificate' in request.files and request.files['birth_certificate'].filename:
                file = request.files['birth_certificate']
                if allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    birth_certificate = filename
            
            if 'photo' in request.files and request.files['photo'].filename:
                file = request.files['photo']
                if allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    photo = filename
            
            # Create new dog
            dog = Dog(
                name=request.form['name'],
                code=request.form['code'],
                breed=request.form['breed'],
                family_line=request.form.get('family_line') or None,
                gender=request.form['gender'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date(),
                microchip_id=request.form.get('microchip_id') or None,
                location=request.form.get('location') or None,
                specialization=request.form.get('specialization') or None,
                color=request.form.get('color') or None,
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                height=float(request.form['height']) if request.form.get('height') else None,
                birth_certificate=birth_certificate,
                photo=photo,
                assigned_to_user_id=current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            )
            
            # Set father and mother if provided
            if request.form.get('father_id'):
                dog.father_id = request.form['father_id']
            if request.form.get('mother_id'):
                dog.mother_id = request.form['mother_id']
            
            db.session.add(dog)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Dog', str(dog.id), {'name': dog.name, 'code': dog.code})
            
            flash('تم إضافة الكلب بنجاح', 'success')
            return redirect(url_for('main.dogs_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الكلب: {str(e)}', 'error')
    
    # Get potential parents (existing dogs)
    if current_user.role == UserRole.GENERAL_ADMIN:
        potential_parents = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        potential_parents = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('dogs/add.html', potential_parents=potential_parents)

@main_bp.route('/dogs/<dog_id>')
@login_required
def dogs_view(dog_id):
    from datetime import date
    dog = Dog.query.get_or_404(dog_id)
    
    # Check access permissions
    if current_user.role == UserRole.PROJECT_MANAGER and dog.assigned_to_user_id != current_user.id:
        flash('ليس لديك صلاحية للوصول إلى هذا الكلب', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Get related records
    training_sessions = TrainingSession.query.filter_by(dog_id=dog.id).order_by(TrainingSession.session_date.desc()).limit(10).all()
    vet_visits = VeterinaryVisit.query.filter_by(dog_id=dog.id).order_by(VeterinaryVisit.visit_date.desc()).limit(10).all()
    breeding_cycles = BreedingCycle.query.filter((BreedingCycle.female_id == dog.id) | (BreedingCycle.male_id == dog.id)).all()
    
    return render_template('dogs/view.html', dog=dog, training_sessions=training_sessions, 
                         vet_visits=vet_visits, breeding_cycles=breeding_cycles, today=date.today())

@main_bp.route('/dogs/<dog_id>/edit', methods=['GET', 'POST'])
@login_required
def dogs_edit(dog_id):
    dog = Dog.query.get_or_404(dog_id)
    
    # Check access permissions
    if current_user.role == UserRole.PROJECT_MANAGER and dog.assigned_to_user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الكلب', 'error')
        return redirect(url_for('main.dogs_list'))
    
    if request.method == 'POST':
        try:
            old_data = {'name': dog.name, 'code': dog.code, 'status': dog.current_status.value}
            
            # Update basic information
            dog.name = request.form['name']
            dog.code = request.form['code']
            dog.breed = request.form['breed']
            dog.family_line = request.form.get('family_line') or None
            dog.gender = request.form['gender']
            dog.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            dog.microchip_id = request.form.get('microchip_id') or None
            dog.current_status = request.form['current_status']
            dog.location = request.form.get('location') or None
            dog.specialization = request.form.get('specialization') or None
            dog.color = request.form.get('color') or None
            dog.weight = float(request.form['weight']) if request.form.get('weight') else None
            dog.height = float(request.form['height']) if request.form.get('height') else None
            dog.updated_at = datetime.utcnow()
            
            # Handle file uploads
            if 'birth_certificate' in request.files and request.files['birth_certificate'].filename:
                file = request.files['birth_certificate']
                if allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    dog.birth_certificate = filename
            
            if 'photo' in request.files and request.files['photo'].filename:
                file = request.files['photo']
                if allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    dog.photo = filename
            
            db.session.commit()
            
            new_data = {'name': dog.name, 'code': dog.code, 'status': dog.current_status.value if hasattr(dog.current_status, 'value') else dog.current_status}
            log_audit(current_user.id, 'EDIT', 'Dog', str(dog.id), {'old': old_data, 'new': new_data})
            
            flash('تم تحديث بيانات الكلب بنجاح', 'success')
            return redirect(url_for('main.dogs_view', dog_id=dog.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الكلب: {str(e)}', 'error')
    
    # Get potential parents
    if current_user.role == UserRole.GENERAL_ADMIN:
        potential_parents = Dog.query.filter(Dog.id != dog.id, Dog.current_status == DogStatus.ACTIVE).all()
    else:
        potential_parents = Dog.query.filter(Dog.id != dog.id, Dog.assigned_to_user_id == current_user.id, Dog.current_status == DogStatus.ACTIVE).all()
    
    return render_template('dogs/edit.html', dog=dog, potential_parents=potential_parents)

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
            employee = Employee(
                name=request.form['name'],
                employee_id=request.form['employee_id'],
                role=request.form['role'],
                phone=request.form.get('phone') or None,
                email=request.form.get('email') or None,
                hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date(),
                assigned_to_user_id=current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            )
            
            db.session.add(employee)
            db.session.flush()  # Get the employee ID
            
            # If this is a project manager, create a user account
            if request.form['role'] == EmployeeRole.PROJECT_MANAGER.value and current_user.role == UserRole.GENERAL_ADMIN:
                if request.form.get('create_user_account') == 'on':
                    from werkzeug.security import generate_password_hash
                    
                    # Get the selected sections
                    allowed_sections = []
                    section_checkboxes = ['dogs', 'employees', 'training', 'veterinary', 'breeding', 'projects', 'attendance', 'reports']
                    for section in section_checkboxes:
                        if request.form.get(f'section_{section}') == 'on':
                            allowed_sections.append(section)
                    
                    # Create user account
                    user_account = User(
                        username=request.form['username'],
                        email=request.form.get('email', f"{request.form['username']}@k9operations.mil"),
                        password_hash=generate_password_hash(request.form['password']),
                        role=UserRole.PROJECT_MANAGER,
                        full_name=request.form['name'],
                        active=True,
                        allowed_sections=allowed_sections
                    )
                    
                    db.session.add(user_account)
                    db.session.flush()  # Get the user ID
                    
                    # Link the employee to the user account
                    employee.user_account_id = user_account.id
                    
                    log_audit(current_user.id, 'CREATE', 'User', str(user_account.id), {
                        'username': user_account.username, 
                        'role': 'PROJECT_MANAGER',
                        'allowed_sections': allowed_sections
                    })
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Employee', str(employee.id), {'name': employee.name, 'employee_id': employee.employee_id})
            
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            if 'duplicate key value violates unique constraint "employee_id_number_key"' in error_msg:
                flash('رقم الهوية المدني موجود بالفعل. يرجى استخدام رقم مختلف.', 'error')
            elif 'duplicate key value violates unique constraint "employee_employee_id_key"' in error_msg:
                flash('رقم الموظف موجود بالفعل. يرجى استخدام رقم مختلف.', 'error')
            else:
                flash(f'حدث خطأ أثناء إضافة الموظف: {error_msg}', 'error')
    
    return render_template('employees/add.html', employee_roles=EmployeeRole)

@main_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
def employees_edit(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    # Check access permissions
    if current_user.role == UserRole.PROJECT_MANAGER and employee.assigned_to_user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الموظف', 'error')
        return redirect(url_for('main.employees_list'))
    
    if request.method == 'POST':
        try:
            old_data = {'name': employee.name, 'role': employee.role.value if hasattr(employee.role, 'value') else employee.role, 'active': employee.is_active}
            
            employee.name = request.form['name']
            employee.employee_id = request.form['employee_id']
            employee.role = request.form['role']
            employee.phone = request.form.get('phone')
            employee.email = request.form.get('email')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
            employee.is_active = request.form.get('is_active') == 'on'
            employee.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            new_data = {'name': employee.name, 'role': employee.role.value if hasattr(employee.role, 'value') else employee.role, 'active': employee.is_active}
            log_audit(current_user.id, 'EDIT', 'Employee', str(employee.id), {'old': old_data, 'new': new_data})
            
            flash('تم تحديث بيانات الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الموظف: {str(e)}', 'error')
    
    return render_template('employees/edit.html', employee=employee, employee_roles=EmployeeRole)

# Training routes
@main_bp.route('/training')
@login_required
def training_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        sessions = TrainingSession.query.order_by(TrainingSession.session_date.desc()).all()
    else:
        # Get sessions for assigned dogs
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        sessions = TrainingSession.query.filter(TrainingSession.dog_id.in_(assigned_dog_ids)).order_by(TrainingSession.session_date.desc()).all()
    
    return render_template('training/list.html', sessions=sessions)

@main_bp.route('/training/add', methods=['GET', 'POST'])
@login_required
def training_add():
    if request.method == 'POST':
        try:
            session = TrainingSession(
                dog_id=request.form['dog_id'],
                trainer_id=request.form['trainer_id'],
                category=request.form['category'],
                subject=request.form['subject'],
                session_date=datetime.strptime(request.form['session_date'], '%Y-%m-%dT%H:%M'),
                duration=int(request.form['duration']),
                success_rating=int(request.form['success_rating']),
                location=request.form.get('location'),
                notes=request.form.get('notes'),
                weather_conditions=request.form.get('weather_conditions')
            )
            
            db.session.add(session)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'TrainingSession', str(session.id), 
                     {'dog': session.dog.name, 'subject': session.subject})
            
            flash('تم إضافة جلسة التدريب بنجاح', 'success')
            return redirect(url_for('main.training_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة جلسة التدريب: {str(e)}', 'error')
    
    # Get available dogs and trainers
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        trainers = Employee.query.filter_by(role=EmployeeRole.TRAINER, is_active=True).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        trainers = Employee.query.filter_by(assigned_to_user_id=current_user.id, role=EmployeeRole.TRAINER, is_active=True).all()
    
    return render_template('training/add.html', dogs=dogs, trainers=trainers, categories=TrainingCategory)

# Veterinary routes
@main_bp.route('/veterinary')
@login_required
def veterinary_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        visits = VeterinaryVisit.query.order_by(VeterinaryVisit.visit_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(assigned_dog_ids)).order_by(VeterinaryVisit.visit_date.desc()).all()
    
    return render_template('veterinary/list.html', visits=visits)

@main_bp.route('/veterinary/add', methods=['GET', 'POST'])
@login_required
def veterinary_add():
    if request.method == 'POST':
        try:
            visit = VeterinaryVisit(
                dog_id=request.form['dog_id'],
                vet_id=request.form['vet_id'],
                visit_type=request.form['visit_type'],
                visit_date=datetime.strptime(request.form['visit_date'], '%Y-%m-%dT%H:%M'),
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                temperature=float(request.form['temperature']) if request.form.get('temperature') else None,
                heart_rate=int(request.form['heart_rate']) if request.form.get('heart_rate') else None,
                blood_pressure=request.form.get('blood_pressure'),
                symptoms=request.form.get('symptoms'),
                diagnosis=request.form.get('diagnosis'),
                treatment=request.form.get('treatment'),
                stool_color=request.form.get('stool_color'),
                stool_consistency=request.form.get('stool_consistency'),
                urine_color=request.form.get('urine_color'),
                notes=request.form.get('notes'),
                cost=float(request.form['cost']) if request.form.get('cost') else None
            )
            
            # Handle next visit date
            if request.form.get('next_visit_date'):
                visit.next_visit_date = datetime.strptime(request.form['next_visit_date'], '%Y-%m-%d').date()
            
            db.session.add(visit)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'VeterinaryVisit', str(visit.id), 
                     {'dog': visit.dog.name, 'type': visit.visit_type.value})
            
            flash('تم إضافة الزيارة البيطرية بنجاح', 'success')
            return redirect(url_for('main.veterinary_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الزيارة البيطرية: {str(e)}', 'error')
    
    # Get available dogs and vets
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        vets = Employee.query.filter_by(role=EmployeeRole.VET, is_active=True).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        vets = Employee.query.filter_by(assigned_to_user_id=current_user.id, role=EmployeeRole.VET, is_active=True).all()
    
    return render_template('veterinary/add.html', dogs=dogs, vets=vets, visit_types=VisitType)

# Breeding routes
@main_bp.route('/breeding/list')
@login_required
def breeding_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        cycles = BreedingCycle.query.order_by(BreedingCycle.mating_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        cycles = BreedingCycle.query.filter(
            (BreedingCycle.female_id.in_(assigned_dog_ids)) | 
            (BreedingCycle.male_id.in_(assigned_dog_ids))
        ).order_by(BreedingCycle.mating_date.desc()).all()
    
    return render_template('breeding/list.html', cycles=cycles)

@main_bp.route('/breeding/add', methods=['GET', 'POST'])
@login_required
def breeding_add():
    if request.method == 'POST':
        try:
            cycle = BreedingCycle(
                female_id=request.form['female_id'],
                male_id=request.form['male_id'],
                cycle_type=request.form['cycle_type'],
                mating_date=datetime.strptime(request.form['mating_date'], '%Y-%m-%d').date(),
                prenatal_care=request.form.get('prenatal_care')
            )
            
            # Calculate expected delivery date (approximately 63 days)
            from datetime import timedelta
            cycle.expected_delivery_date = cycle.mating_date + timedelta(days=63)
            
            if request.form.get('heat_start_date'):
                cycle.heat_start_date = datetime.strptime(request.form['heat_start_date'], '%Y-%m-%d').date()
            
            db.session.add(cycle)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'BreedingCycle', str(cycle.id), 
                     {'female': cycle.female.name, 'male': cycle.male.name})
            
            flash('تم إضافة دورة التكاثر بنجاح', 'success')
            return redirect(url_for('main.breeding_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة دورة التكاثر: {str(e)}', 'error')
    
    # Get available dogs for breeding
    if current_user.role == UserRole.GENERAL_ADMIN:
        females = Dog.query.filter_by(gender='FEMALE', current_status=DogStatus.ACTIVE).all()
        males = Dog.query.filter_by(gender='MALE', current_status=DogStatus.ACTIVE).all()
    else:
        females = Dog.query.filter_by(assigned_to_user_id=current_user.id, gender='FEMALE', current_status=DogStatus.ACTIVE).all()
        males = Dog.query.filter_by(assigned_to_user_id=current_user.id, gender='MALE', current_status=DogStatus.ACTIVE).all()
    
    return render_template('breeding/add.html', females=females, males=males)

# Projects routes
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
            # Allow GENERAL_ADMIN to assign any manager, PROJECT_MANAGER assigns to themselves
            manager_id = request.form.get('manager_id') if current_user.role == UserRole.GENERAL_ADMIN else current_user.id
            
            project = Project(
                name=request.form['name'],
                code=request.form['code'],
                main_task=request.form.get('main_task'),  # المهمة الأساسية
                description=request.form.get('description'),
                location=request.form.get('location'),
                mission_type=request.form.get('mission_type'),
                priority=request.form.get('priority', 'MEDIUM'),
                manager_id=manager_id
            )
            
            if request.form.get('start_date'):
                project.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('expected_completion_date'):
                project.expected_completion_date = datetime.strptime(request.form['expected_completion_date'], '%Y-%m-%d').date()
            
            db.session.add(project)
            db.session.flush()  # Get the project ID
            
            # Assign employees to project
            employee_ids = request.form.getlist('employee_ids')
            if employee_ids:
                employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
                project.assigned_employees.extend(employees)
            
            # Assign dogs to project
            dog_ids = request.form.getlist('dog_ids')
            if dog_ids:
                dogs = Dog.query.filter(Dog.id.in_(dog_ids)).all()
                project.assigned_dogs.extend(dogs)
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Project', str(project.id), {'name': project.name, 'code': project.code})
            
            flash('تم إضافة المشروع بنجاح', 'success')
            return redirect(url_for('main.projects_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المشروع: {str(e)}', 'error')
    
    # Get employees, dogs and managers for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.filter_by(is_active=True).all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        managers = []  # PROJECT_MANAGER users can only assign to themselves
    
    return render_template('projects/add.html', employees=employees, dogs=dogs, managers=managers)

# Project Dashboard Route
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
    
    # Get dashboard statistics
    stats = {}
    
    # Assignment statistics - simplified without attendance
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

# Enhanced Projects Section - Project Assignments


@main_bp.route('/projects/<project_id>/assignments')
@login_required
def project_assignments(project_id):
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
    
    assignments = ProjectAssignment.query.filter_by(project_id=project_uuid).all()
    dog_assignments = ProjectDog.query.filter_by(project_id=project_uuid).all()
    
    # Get available employees and dogs for assignments
    if current_user.role == UserRole.GENERAL_ADMIN:
        available_employees = Employee.query.filter_by(is_active=True).all()
        available_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        available_managers = User.query.filter_by(role=UserRole.PROJECT_MANAGER, active=True).all()
    else:
        available_employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
        available_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        available_managers = []  # PROJECT_MANAGER users can't change managers
    
    return render_template('projects/assignments.html', 
                         project=project, 
                         assignments=assignments, 
                         dog_assignments=dog_assignments,
                         available_employees=available_employees,
                         available_dogs=available_dogs,
                         today=date.today(),
                         available_managers=available_managers)

@main_bp.route('/projects/<project_id>/assignments/add', methods=['GET', 'POST'])
@login_required
def project_assignment_add(project_id):
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
            # Get the employee to determine their role
            employee = Employee.query.get(request.form['employee_id'])
            if not employee:
                flash('الموظف المحدد غير موجود', 'error')
                return redirect(url_for('main.project_assignment_add', project_id=project_id))
            
            # Check if trying to assign a project manager when one already exists
            if employee.role == EmployeeRole.PROJECT_MANAGER:
                existing_pm = ProjectAssignment.query.filter_by(
                    project_id=project_uuid, 
                    role=ProjectRole.PROJECT_MANAGER
                ).first()
                
                if existing_pm:
                    # Replace existing project manager
                    db.session.delete(existing_pm)
                    flash(f'تم استبدال مسؤول المشروع السابق: {existing_pm.employee.name}', 'info')
            
            # Map employee role to project role
            role_mapping = {
                EmployeeRole.HANDLER: ProjectRole.HANDLER,
                EmployeeRole.VET: ProjectRole.VET,
                EmployeeRole.PROJECT_MANAGER: ProjectRole.PROJECT_MANAGER
            }
            
            project_role = role_mapping.get(employee.role)
            if not project_role:
                flash('دور الموظف غير مدعوم في المشاريع', 'error')
                return redirect(url_for('main.project_assignment_add', project_id=project_id))
            
            assignment = ProjectAssignment(
                project_id=project_uuid,
                employee_id=request.form['employee_id'],
                role=project_role,
                period=PeriodType.MORNING,  # Default period
                is_present=True,  # Default to present
                leave_type=None
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'ProjectAssignment', str(assignment.id), 
                     {'project': project.name, 'employee': assignment.employee.name})
            flash('تم تعيين الموظف للمشروع بنجاح', 'success')
            return redirect(url_for('main.project_assignments', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء التعيين: {str(e)}', 'error')
    
    # Get available employees
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    return render_template('projects/assignment_add.html', project=project, employees=employees)

@main_bp.route('/projects/<project_id>/assignments/bulk-add', methods=['POST'])
@login_required
def project_bulk_assignment_add(project_id):
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
    
    employee_ids = request.form.getlist('employee_ids')
    if not employee_ids:
        flash('يرجى تحديد موظف واحد على الأقل', 'error')
        return redirect(url_for('main.project_assignments', project_id=project_id))
    
    try:
        assigned_count = 0
        already_assigned = []
        errors = []
        
        # Check if there's already a project manager assigned
        existing_pm = ProjectAssignment.query.filter_by(
            project_id=project_uuid, 
            role=ProjectRole.PROJECT_MANAGER
        ).first()
        
        # Get selected employees and check for project managers
        selected_employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        project_managers = [emp for emp in selected_employees if emp.role == EmployeeRole.PROJECT_MANAGER]
        
        # Handle project manager logic
        if project_managers:
            if existing_pm:
                # Replace existing project manager
                db.session.delete(existing_pm)
                flash(f'تم استبدال مسؤول المشروع السابق: {existing_pm.employee.name}', 'info')
            
            if len(project_managers) > 1:
                # Only assign the first project manager
                project_managers = project_managers[:1]
                flash(f'يمكن تعيين مسؤول مشروع واحد فقط. تم تعيين: {project_managers[0].name}', 'warning')
        
        for employee_id in employee_ids:
            try:
                # Check if employee is already assigned
                existing_assignment = ProjectAssignment.query.filter_by(
                    project_id=project_uuid, 
                    employee_id=employee_id
                ).first()
                
                if existing_assignment and existing_assignment.role != ProjectRole.PROJECT_MANAGER:
                    employee = Employee.query.get(employee_id)
                    if employee:
                        already_assigned.append(employee.name)
                    continue
                
                # Get the employee to determine their role
                employee = Employee.query.get(employee_id)
                if not employee:
                    errors.append(f'موظف غير موجود: {employee_id}')
                    continue
                
                # Skip if this is not the first project manager in the list
                if employee.role == EmployeeRole.PROJECT_MANAGER and employee not in project_managers:
                    continue
                
                # Map employee role to project role
                role_mapping = {
                    EmployeeRole.HANDLER: ProjectRole.HANDLER,
                    EmployeeRole.VET: ProjectRole.VET,
                    EmployeeRole.PROJECT_MANAGER: ProjectRole.PROJECT_MANAGER
                }
                
                project_role = role_mapping.get(employee.role)
                if not project_role:
                    errors.append(f'دور غير مدعوم للموظف: {employee.name}')
                    continue
                
                # Create assignment
                assignment = ProjectAssignment(
                    project_id=project_uuid,
                    employee_id=employee_id,
                    role=project_role,
                    period=PeriodType.MORNING,  # Default period
                    is_present=True,  # Default to present
                    leave_type=None
                )
                
                db.session.add(assignment)
                assigned_count += 1
                
                # Log the assignment
                log_audit(current_user.id, 'CREATE', 'ProjectAssignment', str(assignment.id), 
                         {'project': project.name, 'employee': employee.name, 'bulk': True})
                
            except Exception as e:
                errors.append(f'خطأ في تعيين الموظف {employee_id}: {str(e)}')
                continue
        
        db.session.commit()
        
        # Create success message
        messages = []
        if assigned_count > 0:
            messages.append(f'تم تعيين {assigned_count} موظف بنجاح')
        
        if already_assigned:
            messages.append(f'الموظفون التالون مُعينون مسبقاً: {", ".join(already_assigned[:3])}{"..." if len(already_assigned) > 3 else ""}')
        
        if errors:
            messages.append(f'حدثت أخطاء في {len(errors)} تعيين')
        
        if messages:
            flash(' | '.join(messages), 'success' if assigned_count > 0 else 'warning')
        
        return redirect(url_for('main.project_assignments', project_id=project_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء التعيين المجمع: {str(e)}', 'error')
        return redirect(url_for('main.project_assignments', project_id=project_id))

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
        flash('غير مسموح لك بتغيير حالة هذا المشروع', 'error')
        return redirect(url_for('main.project_dashboard', project_id=project_id))
    
    new_status = request.form.get('status')
    if not new_status or new_status not in ['PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED']:
        flash('حالة المشروع غير صحيحة', 'error')
        return redirect(url_for('main.project_dashboard', project_id=project_id))
    
    try:
        old_status = project.status
        project.status = ProjectStatus(new_status)
        
        # If completing the project, automatically set end_date and calculate duration
        if new_status == 'COMPLETED' and not project.end_date:
            project.end_date = datetime.now().date()
            if project.start_date:
                project.duration_days = (project.end_date - project.start_date).days
        
        db.session.commit()
        
        # Log the status change
        log_audit(current_user.id, 'UPDATE', 'Project', str(project.id), 
                 {'status_change': f'{old_status} -> {new_status}', 'end_date': str(project.end_date) if project.end_date else None})
        
        status_names = {
            'PLANNED': 'مخطط',
            'ACTIVE': 'نشط', 
            'COMPLETED': 'مكتمل',
            'CANCELLED': 'ملغي'
        }
        
        flash(f'تم تغيير حالة المشروع إلى: {status_names.get(new_status, new_status)}', 'success')
        if new_status == 'COMPLETED':
            flash(f'تم إنهاء المشروع بتاريخ: {project.end_date.strftime("%Y-%m-%d")}', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تغيير حالة المشروع: {str(e)}', 'error')
    
    return redirect(url_for('main.project_dashboard', project_id=project_id))

@main_bp.route('/projects/<project_id>/dogs/add', methods=['GET', 'POST'])
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
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
    if request.method == 'POST':
        try:
            dog_assignment = ProjectDog(
                project_id=project_uuid,
                dog_id=request.form['dog_id'],
                is_active=True,
                assigned_date=date.today()
            )
            
            db.session.add(dog_assignment)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'ProjectDog', str(dog_assignment.id), 
                     {'project': project.name, 'dog': dog_assignment.dog.name})
            flash('تم تعيين الكلب للمشروع بنجاح', 'success')
            return redirect(url_for('main.project_assignments', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء التعيين: {str(e)}', 'error')
    
    # Get available dogs
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('projects/dog_add.html', project=project, dogs=dogs)

# Project Manager Change Route
@main_bp.route('/projects/<project_id>/change-manager', methods=['POST'])
@login_required
def project_change_manager(project_id):
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('غير مسموح لك بتغيير مدير المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects_list'))
    
    new_manager_id = request.form.get('manager_id')
    
    if new_manager_id:
        old_manager = project.manager.username if project.manager else 'غير محدد'
        project.manager_id = new_manager_id
        db.session.commit()
        
        new_manager = User.query.get(new_manager_id)
        log_audit(current_user.id, 'UPDATE', 'Project', str(project.id), 
                 {'manager_changed': f'من {old_manager} إلى {new_manager.username}'})
        flash('تم تغيير مدير المشروع بنجاح', 'success')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

@main_bp.route('/projects/<project_id>/assignments/toggle-attendance')
@login_required
def project_assignment_toggle_attendance(project_id):
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
    
    assignment_id = request.args.get('assignment_id')
    status = request.args.get('status')
    
    if assignment_id and status:
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
        assignment.is_present = status.lower() == 'true'
        
        # If marking as absent and no leave type is set, clear it
        # If marking as present, clear leave type
        if assignment.is_present:
            assignment.leave_type = None
        
        db.session.commit()
        
        status_text = 'حاضر' if assignment.is_present else 'غائب'
        log_audit(current_user.id, 'UPDATE', 'ProjectAssignment', str(assignment.id), 
                 {'employee': assignment.employee.name, 'attendance': status_text})
        flash(f'تم تحديث حالة حضور {assignment.employee.name} إلى {status_text}', 'success')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

# Assignment Management Routes
@main_bp.route('/projects/<project_id>/assignments/remove')
@login_required
def project_assignment_remove(project_id):
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
    
    assignment_id = request.args.get('assignment_id')
    if assignment_id:
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
        employee_name = assignment.employee.name
        db.session.delete(assignment)
        db.session.commit()
        
        log_audit(current_user.id, 'DELETE', 'ProjectAssignment', str(assignment.id), 
                 {'project': project.name, 'employee': employee_name})
        flash('تم حذف تعيين الموظف', 'success')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

@main_bp.route('/projects/<project_id>/dogs/toggle')
@login_required
def project_dog_toggle(project_id):
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
    
    assignment_id = request.args.get('assignment_id')
    if assignment_id:
        assignment = ProjectDog.query.get_or_404(assignment_id)
        assignment.is_active = not assignment.is_active
        db.session.commit()
        
        status = 'نشط' if assignment.is_active else 'غير نشط'
        log_audit(current_user.id, 'UPDATE', 'ProjectDog', str(assignment.id), 
                 {'dog': assignment.dog.name, 'status': status})
        flash(f'تم تغيير حالة الكلب إلى {status}', 'success')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

@main_bp.route('/projects/<project_id>/dogs/remove')
@login_required
def project_dog_remove(project_id):
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
    
    assignment_id = request.args.get('assignment_id')
    if assignment_id:
        assignment = ProjectDog.query.get_or_404(assignment_id)
        dog_name = assignment.dog.name
        db.session.delete(assignment)
        db.session.commit()
        
        log_audit(current_user.id, 'DELETE', 'ProjectDog', str(assignment.id), 
                 {'project': project.name, 'dog': dog_name})
        flash('تم حذف تعيين الكلب', 'success')
    
    return redirect(url_for('main.project_assignments', project_id=project_id))

# Modern Attendance Management APIs
@main_bp.route('/projects/<project_id>/assignments/toggle-attendance', methods=['POST'])
@login_required
def project_assignment_toggle_attendance_api(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        return jsonify({'success': False, 'message': 'معرف المشروع غير صحيح'})
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        return jsonify({'success': False, 'message': 'غير مسموح لك بالوصول إلى هذا المشروع'})
    
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    is_present = data.get('is_present')
    
    if assignment_id and is_present is not None:
        try:
            assignment_uuid = uuid.UUID(assignment_id)
            assignment = ProjectAssignment.query.get_or_404(assignment_uuid)
            assignment.is_present = is_present
            
            # Clear leave type when marking present
            if assignment.is_present:
                assignment.leave_type = None
            
            db.session.commit()
            
            status_text = 'حاضر' if assignment.is_present else 'غائب'
            log_audit(current_user.id, 'UPDATE', 'ProjectAssignment', str(assignment.id), 
                     {'employee': assignment.employee.name, 'attendance': status_text})
            
            return jsonify({
                'success': True, 
                'message': f'تم تحديث حالة حضور {assignment.employee.name} إلى {status_text}'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'بيانات غير صحيحة'})

@main_bp.route('/projects/<project_id>/assignments/set-leave', methods=['POST'])
@login_required
def project_assignment_set_leave_api(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        return jsonify({'success': False, 'message': 'معرف المشروع غير صحيح'})
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        return jsonify({'success': False, 'message': 'غير مسموح لك بالوصول إلى هذا المشروع'})
    
    data = request.get_json()
    assignment_id = data.get('assignment_id')
    leave_type = data.get('leave_type')
    
    if assignment_id and leave_type:
        try:
            assignment_uuid = uuid.UUID(assignment_id)
            assignment = ProjectAssignment.query.get_or_404(assignment_uuid)
            assignment.leave_type = LeaveType(leave_type)
            assignment.is_present = False  # Set as absent when on leave
            
            db.session.commit()
            
            leave_text = {'SICK': 'مرضية', 'PERSONAL': 'شخصية', 'VACATION': 'اعتيادية'}.get(leave_type, leave_type)
            log_audit(current_user.id, 'UPDATE', 'ProjectAssignment', str(assignment.id), 
                     {'employee': assignment.employee.name, 'leave_type': leave_text})
            
            return jsonify({
                'success': True, 
                'message': f'تم تسجيل إجازة {leave_text} للموظف {assignment.employee.name}'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'بيانات غير صحيحة'})

@main_bp.route('/projects/<project_id>/assignments/bulk-attendance', methods=['POST'])
@login_required
def project_assignment_bulk_attendance_api(project_id):
    try:
        project_uuid = uuid.UUID(project_id)
        project = Project.query.get_or_404(project_uuid)
    except ValueError:
        return jsonify({'success': False, 'message': 'معرف المشروع غير صحيح'})
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        return jsonify({'success': False, 'message': 'غير مسموح لك بالوصول إلى هذا المشروع'})
    
    data = request.get_json()
    is_present = data.get('is_present')
    period = data.get('period', 'MORNING')
    
    if is_present is not None:
        try:
            assignments = ProjectAssignment.query.filter_by(
                project_id=project_uuid,
                period=PeriodType(period)
            ).all()
            
            updated_count = 0
            for assignment in assignments:
                assignment.is_present = is_present
                if is_present:
                    assignment.leave_type = None
                updated_count += 1
            
            db.session.commit()
            
            status_text = 'حاضرين' if is_present else 'غائبين'
            log_audit(current_user.id, 'BULK_UPDATE', 'ProjectAssignment', f'bulk_{period}', 
                     {'project': project.name, 'count': updated_count, 'status': status_text})
            
            return jsonify({
                'success': True, 
                'message': f'تم تحديث حضور {updated_count} موظف إلى {status_text}'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'بيانات غير صحيحة'})





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

@main_bp.route('/projects/<project_id>/incidents/resolve')
@login_required
def project_resolve_incident(project_id):
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
    
    incident_id = request.args.get('incident_id')
    if incident_id:
        incident = Incident.query.get_or_404(incident_id)
        incident.resolved = True
        incident.resolution_date = datetime.now().date()
        db.session.commit()
        
        log_audit(current_user.id, 'UPDATE', 'Incident', str(incident.id), {'resolved': True})
        flash('تم تمييز الحادث كمحلول', 'success')
    
    return redirect(url_for('main.project_incidents', project_id=project_id))

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
                name=request.form['name'],
                incident_date=datetime.strptime(request.form['incident_date'], '%Y-%m-%d').date(),
                incident_time=datetime.strptime(request.form['incident_time'], '%H:%M').time(),
                incident_type=request.form['incident_type'],
                description=request.form.get('description'),
                location=request.form.get('location'),
                severity=request.form.get('severity', 'MEDIUM'),
                reported_by=request.form.get('reported_by') if request.form.get('reported_by') else None,
                people_involved=request.form.getlist('people_involved'),
                dogs_involved=request.form.getlist('dogs_involved'),
                witness_statements=request.form.get('witness_statements'),
                resolved=bool(request.form.get('resolved')),
                resolution_notes=request.form.get('resolution_notes'),
                resolution_date=datetime.strptime(request.form['resolution_date'], '%Y-%m-%d').date() if request.form.get('resolution_date') else None
            )
            
            db.session.add(incident)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Incident', str(incident.id), 
                     {'project': project.name, 'incident': incident.name})
            flash('تم تسجيل الحادث بنجاح', 'success')
            return redirect(url_for('main.project_incidents', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الحادث: {str(e)}', 'error')
    
    # Get employees and dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.filter_by(is_active=True).all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('projects/incident_add.html', project=project, employees=employees, dogs=dogs)

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
                element_type=ElementType(request.form['element_type']),
                subtype=request.form.get('subtype'),
                discovery_date=datetime.strptime(request.form['discovery_date'], '%Y-%m-%d').date(),
                discovery_time=datetime.strptime(request.form['discovery_time'], '%H:%M').time(),
                location=request.form['location'],
                detected_by_dog=request.form.get('detected_by_dog') if request.form.get('detected_by_dog') else None,
                handler=request.form.get('handler') if request.form.get('handler') else None,
                detection_method=request.form.get('detection_method'),
                description=request.form.get('description'),
                quantity_estimate=request.form.get('quantity_estimate'),
                authorities_notified=bool(request.form.get('authorities_notified')),
                evidence_collected=bool(request.form.get('evidence_collected')),
                follow_up_required=bool(request.form.get('follow_up_required')),
                follow_up_notes=request.form.get('follow_up_notes')
            )
            
            db.session.add(suspicion)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Suspicion', str(suspicion.id), 
                     {'project': project.name, 'element': suspicion.element_type.value})
            flash('تم تسجيل الاشتباه بنجاح', 'success')
            return redirect(url_for('main.project_suspicions', project_id=project_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الاشتباه: {str(e)}', 'error')
    
    # Get employees and dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        employees = Employee.query.filter_by(is_active=True).all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('projects/suspicion_add.html', project=project, employees=employees, dogs=dogs, element_types=ElementType)

# Enhanced Projects Section - Performance Evaluations
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
            evaluation = PerformanceEvaluation(
                project_id=project_uuid,
                evaluator_id=current_user.id,
                target_type=TargetType(request.form['target_type']),
                target_employee_id=request.form.get('target_employee_id') if request.form.get('target_employee_id') else None,
                target_dog_id=request.form.get('target_dog_id') if request.form.get('target_dog_id') else None,
                evaluation_date=datetime.strptime(request.form['evaluation_date'], '%Y-%m-%d').date(),
                rating=PerformanceRating(request.form['rating']),
                uniform_ok=bool(request.form.get('uniform_ok')),
                id_card_ok=bool(request.form.get('id_card_ok')),
                appearance_ok=bool(request.form.get('appearance_ok')),
                cleanliness_ok=bool(request.form.get('cleanliness_ok')),
                punctuality=int(request.form['punctuality']) if request.form.get('punctuality') else None,
                job_knowledge=int(request.form['job_knowledge']) if request.form.get('job_knowledge') else None,
                teamwork=int(request.form['teamwork']) if request.form.get('teamwork') else None,
                communication=int(request.form['communication']) if request.form.get('communication') else None,
                obedience_level=int(request.form['obedience_level']) if request.form.get('obedience_level') else None,
                detection_accuracy=int(request.form['detection_accuracy']) if request.form.get('detection_accuracy') else None,
                physical_condition=int(request.form['physical_condition']) if request.form.get('physical_condition') else None,
                handler_relationship=int(request.form['handler_relationship']) if request.form.get('handler_relationship') else None,
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



@main_bp.route('/projects/<project_id>/attendance/add', methods=['GET', 'POST'])
@login_required  
def project_attendance_add(project_id):
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
            # Check if attendance record already exists for this date/period
            existing_record = ProjectAttendance.query.filter_by(
                project_id=project_uuid,
                attendance_date=datetime.strptime(request.form['attendance_date'], '%Y-%m-%d').date(),
                period=PeriodType(request.form['period'])
            ).first()
            
            if existing_record:
                flash('يوجد بالفعل سجل حضور لهذا التاريخ والمجموعة', 'error')
                return redirect(url_for('main.project_attendance_list', project_id=project_id))
            
            # Create simplified attendance record
            attendance_record = ProjectAttendance(
                project_id=project_uuid,
                attendance_date=datetime.strptime(request.form['attendance_date'], '%Y-%m-%d').date(),
                period=PeriodType(request.form['period']),
                shift_manager_id=request.form.get('shift_manager_id') if request.form.get('shift_manager_id') else None,
                notes=request.form.get('notes'),
                weather_conditions=request.form.get('weather_conditions')
            )
            
            db.session.add(attendance_record)
            db.session.commit()
            
            # Determine group number based on period (unified concept)
            group_number = 1 if attendance_record.period == PeriodType.MORNING else (2 if attendance_record.period == PeriodType.EVENING else 3)
            group_name = 'الأولى (صباحي)' if group_number == 1 else ('الثانية (مسائي)' if group_number == 2 else 'الثالثة (ليلي)')
            
            log_audit(current_user.id, 'CREATE', 'ProjectAttendance', str(attendance_record.id), 
                     {'project': project.name, 'date': attendance_record.attendance_date.strftime('%Y-%m-%d'), 'group': f'المجموعة {group_name}'})
            
            flash(f'تم إنشاء سجل حضور للمجموعة {group_name} بنجاح', 'success')
            return redirect(url_for('main.project_attendance_view', project_id=project_id, attendance_id=attendance_record.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الحضور: {str(e)}', 'error')
    
    return redirect(url_for('main.project_attendance_list', project_id=project_id))

@main_bp.route('/projects/<project_id>/attendance/<attendance_id>')
@login_required
def project_attendance_view(project_id, attendance_id):
    try:
        project_uuid = uuid.UUID(project_id)
        attendance_uuid = uuid.UUID(attendance_id)
        project = Project.query.get_or_404(project_uuid)
        attendance_record = ProjectAttendance.query.get_or_404(attendance_uuid)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and project.manager_id != current_user.id:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects_list'))
    
    if attendance_record.project_id != project_uuid:
        flash('سجل الحضور غير متطابق مع المشروع', 'error')
        return redirect(url_for('main.project_attendance_list', project_id=project_id))
    
    # Get assigned employees and dogs for this project (for attendance form)
    employee_assignments = ProjectAssignment.query.filter_by(project_id=project_uuid).all()
    dog_assignments = ProjectDog.query.filter_by(project_id=project_uuid, is_active=True).all()
    
    assigned_employees = [a.employee for a in employee_assignments if a.employee and a.employee.is_active]
    assigned_dogs = [a.dog for a in dog_assignments if a.dog and a.dog.current_status == DogStatus.ACTIVE]
    
    # Get existing attendance entries for this record
    attendance_entries = AttendanceEntry.query.filter_by(attendance_record_id=attendance_uuid).all()
    
    # Get leave requests for this date
    leave_requests = LeaveRequest.query.filter_by(
        project_id=project_uuid,
        leave_date=attendance_record.attendance_date
    ).all()
    
    # Determine group info based on period (unified concept)
    group_number = 1 if attendance_record.period == PeriodType.MORNING else (2 if attendance_record.period == PeriodType.EVENING else 3)
    group_name = 'الأولى (صباحي)' if group_number == 1 else ('الثانية (مسائي)' if group_number == 2 else 'الثالثة (ليلي)')
    
    return render_template('projects/attendance_view.html', 
                         project=project, 
                         attendance_record=attendance_record,
                         attendance_entries=attendance_entries,
                         assigned_employees=assigned_employees,
                         assigned_dogs=assigned_dogs,
                         leave_requests=leave_requests,
                         group_number=group_number,
                         group_name=group_name,
                         today=date.today())

# Attendance routes
@main_bp.route('/attendance')
@login_required
def attendance_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).limit(100).all()
    else:
        assigned_employee_ids = [e.id for e in Employee.query.filter_by(assigned_to_user_id=current_user.id).all()]
        records = AttendanceRecord.query.filter(AttendanceRecord.employee_id.in_(assigned_employee_ids)).order_by(AttendanceRecord.date.desc()).limit(100).all()
    
    return render_template('attendance/list.html', records=records)

# Reports routes
@main_bp.route('/reports')
@login_required
def reports_index():
    # Calculate stats for the reports page
    if current_user.role == UserRole.GENERAL_ADMIN:
        total_dogs = Dog.query.count()
        total_employees = Employee.query.count()
        total_sessions = TrainingSession.query.count()
        total_vet_visits = VeterinaryVisit.query.count()
    else:
        assigned_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).all()
        assigned_employees = Employee.query.filter_by(assigned_to_user_id=current_user.id).all()
        dog_ids = [d.id for d in assigned_dogs]
        employee_ids = [e.id for e in assigned_employees]
        
        total_dogs = len(assigned_dogs)
        total_employees = len(assigned_employees)
        total_sessions = TrainingSession.query.filter(TrainingSession.dog_id.in_(dog_ids)).count() if dog_ids else 0
        total_vet_visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(dog_ids)).count() if dog_ids else 0
    
    stats = {
        'total_dogs': total_dogs,
        'total_employees': total_employees,
        'total_sessions': total_sessions,
        'total_vet_visits': total_vet_visits
    }
    
    return render_template('reports/index.html', stats=stats)

@main_bp.route('/reports/generate', methods=['POST'])
@login_required
def reports_generate():
    report_type = request.form['report_type']
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None
    
    try:
        filename = generate_pdf_report(report_type, start_date, end_date, current_user)
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء التقرير: {str(e)}', 'error')
        return redirect(url_for('main.reports_index'))

# File upload route
@main_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Search route
@main_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'dogs': [], 'employees': []})
    
    # Search dogs
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter(
            (Dog.name.ilike(f'%{query}%')) | 
            (Dog.code.ilike(f'%{query}%'))
        ).limit(10).all()
        employees = Employee.query.filter(
            (Employee.name.ilike(f'%{query}%')) | 
            (Employee.employee_id.ilike(f'%{query}%'))
        ).limit(10).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).filter(
            (Dog.name.ilike(f'%{query}%')) | 
            (Dog.code.ilike(f'%{query}%'))
        ).limit(10).all()
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id).filter(
            (Employee.name.ilike(f'%{query}%')) | 
            (Employee.employee_id.ilike(f'%{query}%'))
        ).limit(10).all()
    
    return jsonify({
        'dogs': [{'id': str(d.id), 'name': d.name, 'code': d.code} for d in dogs],
        'employees': [{'id': str(e.id), 'name': e.name, 'employee_id': e.employee_id} for e in employees]
    })

# ================ BREEDING/PRODUCTION SYSTEM ROUTES (8 Sections) ================

@main_bp.route('/breeding')
@login_required  
def breeding_index():
    """Main breeding dashboard with all 8 sections"""
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    # Get breeding-ready females (mature females who have had 3+ heat cycles)
    breeding_ready_females = []
    for dog in dogs:
        if dog.gender == DogGender.FEMALE:
            heat_cycles = HeatCycle.query.filter_by(dog_id=dog.id).count()
            if heat_cycles >= 3 and dog.maturity_record:
                latest_maturity = dog.maturity_record[-1] if isinstance(dog.maturity_record, list) else dog.maturity_record
                if latest_maturity and latest_maturity.maturity_status == MaturityStatus.MATURE:
                    breeding_ready_females.append(dog)
    
    # Get available males for breeding
    breeding_males = []
    for dog in dogs:
        if dog.gender == DogGender.MALE and dog.maturity_record:
            latest_maturity = dog.maturity_record[-1] if isinstance(dog.maturity_record, list) else dog.maturity_record
            if latest_maturity and latest_maturity.maturity_status == MaturityStatus.MATURE:
                breeding_males.append(dog)
    
    # Count mature dogs safely
    mature_count = 0
    for dog in dogs:
        if dog.maturity_record:
            latest_maturity = dog.maturity_record[-1] if isinstance(dog.maturity_record, list) else dog.maturity_record
            if latest_maturity and latest_maturity.maturity_status == MaturityStatus.MATURE:
                mature_count += 1
    
    stats = {
        'total_dogs': len(dogs),
        'mature_dogs': mature_count,
        'breeding_ready_females': len(breeding_ready_females),
        'breeding_males': len(breeding_males),
        'active_pregnancies': PregnancyRecord.query.filter_by(status=PregnancyStatus.PREGNANT).count(),
        'recent_births': DeliveryRecord.query.filter(DeliveryRecord.delivery_date >= (datetime.now().date().replace(day=1))).count()
    }
    
    return render_template('breeding/index.html', stats=stats, dogs=dogs, breeding_ready_females=breeding_ready_females)

# Section 1 & 2: General Information + Maturity (البلوغ)
@main_bp.route('/breeding/maturity')
@login_required
def maturity_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        maturity_records = DogMaturity.query.join(Dog).order_by(DogMaturity.created_at.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        maturity_records = DogMaturity.query.filter(DogMaturity.dog_id.in_(assigned_dog_ids)).order_by(DogMaturity.created_at.desc()).all()
    
    return render_template('breeding/maturity_list.html', records=maturity_records)

@main_bp.route('/breeding/maturity/add', methods=['GET', 'POST'])
@login_required
def maturity_add():
    if request.method == 'POST':
        try:
            maturity = DogMaturity(
                dog_id=request.form['dog_id'],
                maturity_date=datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date(),
                maturity_status=MaturityStatus.MATURE,
                weight_at_maturity=float(request.form['weight_at_maturity']) if request.form.get('weight_at_maturity') else None,
                height_at_maturity=float(request.form['height_at_maturity']) if request.form.get('height_at_maturity') else None,
                notes=request.form.get('notes')
            )
            
            db.session.add(maturity)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'DogMaturity', str(maturity.id), {'dog': maturity.dog.name})
            flash('تم تسجيل بلوغ الكلب بنجاح', 'success')
            return redirect(url_for('main.maturity_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل البلوغ: {str(e)}', 'error')
    
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('breeding/maturity_add.html', dogs=dogs)

# Section 3: Heat Cycles (الدورة)
@main_bp.route('/breeding/heat-cycles')
@login_required
def heat_cycles_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        cycles = HeatCycle.query.join(Dog).order_by(HeatCycle.start_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        cycles = HeatCycle.query.filter(HeatCycle.dog_id.in_(assigned_dog_ids)).order_by(HeatCycle.start_date.desc()).all()
    
    return render_template('breeding/heat_cycles_list.html', cycles=cycles)

@main_bp.route('/breeding/heat-cycles/add', methods=['GET', 'POST'])
@login_required
def heat_cycles_add():
    if request.method == 'POST':
        try:
            # Get the cycle number (count existing cycles + 1)
            existing_cycles = HeatCycle.query.filter_by(dog_id=request.form['dog_id']).count()
            
            cycle = HeatCycle(
                dog_id=request.form['dog_id'],
                cycle_number=existing_cycles + 1,
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
                behavioral_changes=request.form.get('behavioral_changes'),
                physical_signs=request.form.get('physical_signs'),
                appetite_changes=request.form.get('appetite_changes'),
                notes=request.form.get('notes')
            )
            
            # Calculate duration if end date is provided
            if cycle.end_date:
                cycle.duration_days = (cycle.end_date - cycle.start_date).days
                cycle.status = HeatStatus.POST_HEAT
            
            db.session.add(cycle)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'HeatCycle', str(cycle.id), {'dog': cycle.dog.name, 'cycle_number': cycle.cycle_number})
            flash(f'تم تسجيل الدورة رقم {cycle.cycle_number} بنجاح', 'success')
            return redirect(url_for('main.heat_cycles_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الدورة: {str(e)}', 'error')
    
    # Only show mature females
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE, gender=DogGender.FEMALE).join(DogMaturity).filter_by(maturity_status=MaturityStatus.MATURE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE, gender=DogGender.FEMALE).join(DogMaturity).filter_by(maturity_status=MaturityStatus.MATURE).all()
    
    return render_template('breeding/heat_cycles_add.html', dogs=dogs)

# Section 4: Mating Records (التزاوج)
@main_bp.route('/breeding/mating')
@login_required
def mating_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        matings = MatingRecord.query.order_by(MatingRecord.mating_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        matings = MatingRecord.query.filter((MatingRecord.female_id.in_(assigned_dog_ids)) | (MatingRecord.male_id.in_(assigned_dog_ids))).order_by(MatingRecord.mating_date.desc()).all()
    
    return render_template('breeding/mating_list.html', matings=matings)

@main_bp.route('/breeding/mating/add', methods=['GET', 'POST'])
@login_required
def mating_add():
    if request.method == 'POST':
        try:
            mating = MatingRecord(
                female_id=request.form['female_id'],
                male_id=request.form['male_id'],
                heat_cycle_id=request.form['heat_cycle_id'],
                mating_date=datetime.strptime(request.form['mating_date'], '%Y-%m-%d').date(),
                mating_time=datetime.strptime(request.form['mating_time'], '%H:%M').time() if request.form.get('mating_time') else None,
                location=request.form.get('location'),
                supervised_by=request.form.get('supervised_by') if request.form.get('supervised_by') else None,
                success_rate=int(request.form['success_rate']) if request.form.get('success_rate') else None,
                duration_minutes=int(request.form['duration_minutes']) if request.form.get('duration_minutes') else None,
                behavior_observed=request.form.get('behavior_observed'),
                complications=request.form.get('complications'),
                notes=request.form.get('notes')
            )
            
            db.session.add(mating)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'MatingRecord', str(mating.id), {'female': mating.female.name, 'male': mating.male.name})
            flash('تم تسجيل التزاوج بنجاح', 'success')
            return redirect(url_for('main.mating_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل التزاوج: {str(e)}', 'error')
    
    # Get breeding-ready females (those with 3+ heat cycles)
    if current_user.role == UserRole.GENERAL_ADMIN:
        all_females = Dog.query.filter_by(current_status=DogStatus.ACTIVE, gender=DogGender.FEMALE).all()
        males = Dog.query.filter_by(current_status=DogStatus.ACTIVE, gender=DogGender.MALE).join(DogMaturity).filter_by(maturity_status=MaturityStatus.MATURE).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        all_females = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE, gender=DogGender.FEMALE).all()
        males = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE, gender=DogGender.MALE).join(DogMaturity).filter_by(maturity_status=MaturityStatus.MATURE).all()
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    # Filter females that have 3+ heat cycles
    breeding_females = []
    for female in all_females:
        heat_count = HeatCycle.query.filter_by(dog_id=female.id).count()
        if heat_count >= 3:
            breeding_females.append(female)
    
    return render_template('breeding/mating_add.html', females=breeding_females, males=males, employees=employees)

# Section 5: Pregnancy Records (الحمل)
@main_bp.route('/breeding/pregnancy')
@login_required
def pregnancy_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        pregnancies = PregnancyRecord.query.order_by(PregnancyRecord.confirmed_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        pregnancies = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(PregnancyRecord.confirmed_date.desc()).all()
    
    return render_template('breeding/pregnancy_list.html', pregnancies=pregnancies)

@main_bp.route('/breeding/pregnancy/add', methods=['GET', 'POST'])
@login_required
def pregnancy_add():
    if request.method == 'POST':
        try:
            pregnancy = PregnancyRecord(
                mating_record_id=request.form['mating_record_id'],
                dog_id=request.form['dog_id'],
                confirmed_date=datetime.strptime(request.form['confirmed_date'], '%Y-%m-%d').date(),
                expected_delivery_date=datetime.strptime(request.form['expected_delivery_date'], '%Y-%m-%d').date(),
                status=PregnancyStatus.PREGNANT,
                special_diet=request.form.get('special_diet'),
                exercise_restrictions=request.form.get('exercise_restrictions'),
                notes=request.form.get('notes')
            )
            
            db.session.add(pregnancy)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'PregnancyRecord', str(pregnancy.id), {'dog': pregnancy.dog.name})
            flash('تم تسجيل الحمل بنجاح', 'success')
            return redirect(url_for('main.pregnancy_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الحمل: {str(e)}', 'error')
    
    # Get mating records that don't have pregnancy records yet
    if current_user.role == UserRole.GENERAL_ADMIN:
        available_matings = MatingRecord.query.outerjoin(PregnancyRecord).filter(PregnancyRecord.id == None).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        available_matings = MatingRecord.query.filter(MatingRecord.female_id.in_(assigned_dog_ids)).outerjoin(PregnancyRecord).filter(PregnancyRecord.id == None).all()
    
    return render_template('breeding/pregnancy_add.html', matings=available_matings)

# Section 6: Delivery Records (الولادة)
@main_bp.route('/breeding/delivery')
@login_required
def delivery_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        deliveries = DeliveryRecord.query.order_by(DeliveryRecord.delivery_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        deliveries = DeliveryRecord.query.join(PregnancyRecord).filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(DeliveryRecord.delivery_date.desc()).all()
    
    return render_template('breeding/delivery_list.html', deliveries=deliveries)

@main_bp.route('/breeding/delivery/add', methods=['GET', 'POST'])
@login_required
def delivery_add():
    if request.method == 'POST':
        try:
            delivery = DeliveryRecord(
                pregnancy_record_id=request.form['pregnancy_record_id'],
                delivery_date=datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date(),
                delivery_start_time=datetime.strptime(request.form['delivery_start_time'], '%H:%M').time() if request.form.get('delivery_start_time') else None,
                delivery_end_time=datetime.strptime(request.form['delivery_end_time'], '%H:%M').time() if request.form.get('delivery_end_time') else None,
                location=request.form.get('location'),
                vet_present=request.form.get('vet_present') if request.form.get('vet_present') else None,
                handler_present=request.form.get('handler_present') if request.form.get('handler_present') else None,
                assistance_required=bool(request.form.get('assistance_required')),
                assistance_type=request.form.get('assistance_type'),
                total_puppies=int(request.form['total_puppies']),
                live_births=int(request.form['live_births']),
                stillbirths=int(request.form['stillbirths']),
                delivery_complications=request.form.get('delivery_complications'),
                mother_condition=request.form.get('mother_condition'),
                notes=request.form.get('notes')
            )
            
            db.session.add(delivery)
            
            # Update pregnancy status
            pregnancy = PregnancyRecord.query.get(request.form['pregnancy_record_id'])
            pregnancy.status = PregnancyStatus.DELIVERED
            
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'DeliveryRecord', str(delivery.id), {'puppies': delivery.total_puppies})
            flash('تم تسجيل الولادة بنجاح', 'success')
            return redirect(url_for('main.delivery_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الولادة: {str(e)}', 'error')
    
    # Get pregnant dogs without delivery records
    if current_user.role == UserRole.GENERAL_ADMIN:
        available_pregnancies = PregnancyRecord.query.filter_by(status=PregnancyStatus.PREGNANT).outerjoin(DeliveryRecord).filter(DeliveryRecord.id == None).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        available_pregnancies = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(assigned_dog_ids), PregnancyRecord.status == PregnancyStatus.PREGNANT).outerjoin(DeliveryRecord).filter(DeliveryRecord.id == None).all()
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    return render_template('breeding/delivery_add.html', pregnancies=available_pregnancies, employees=employees)

# Section 7: Puppy Records (الجراء)
@main_bp.route('/breeding/puppies')
@login_required
def puppies_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        puppies = PuppyRecord.query.order_by(PuppyRecord.created_at.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(PuppyRecord.created_at.desc()).all()
    
    return render_template('breeding/puppies_list.html', puppies=puppies)

@main_bp.route('/breeding/puppies/add', methods=['GET', 'POST'])
@login_required
def puppies_add():
    if request.method == 'POST':
        try:
            puppy = PuppyRecord(
                delivery_record_id=request.form['delivery_record_id'],
                puppy_number=int(request.form['puppy_number']),
                name=request.form.get('name'),
                temporary_id=request.form.get('temporary_id'),
                gender=DogGender(request.form['gender']),
                birth_weight=float(request.form['birth_weight']) if request.form.get('birth_weight') else None,
                birth_time=datetime.strptime(request.form['birth_time'], '%H:%M').time() if request.form.get('birth_time') else None,
                birth_order=int(request.form['birth_order']) if request.form.get('birth_order') else None,
                alive_at_birth=bool(request.form.get('alive_at_birth', True)),
                current_status=request.form.get('current_status', 'جيد'),
                color=request.form.get('color'),
                markings=request.form.get('markings'),
                birth_defects=request.form.get('birth_defects'),
                notes=request.form.get('notes')
            )
            
            db.session.add(puppy)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'PuppyRecord', str(puppy.id), {'name': puppy.name or f'Puppy #{puppy.puppy_number}'})
            flash('تم تسجيل الجرو بنجاح', 'success')
            return redirect(url_for('main.puppies_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الجرو: {str(e)}', 'error')
    
    # Get deliveries
    if current_user.role == UserRole.GENERAL_ADMIN:
        deliveries = DeliveryRecord.query.order_by(DeliveryRecord.delivery_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        deliveries = DeliveryRecord.query.join(PregnancyRecord).filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(DeliveryRecord.delivery_date.desc()).all()
    
    return render_template('breeding/puppies_add.html', deliveries=deliveries)

# Section 8: Puppy Training (تدريب الجراء)
@main_bp.route('/breeding/puppy-training')
@login_required
def puppy_training_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        training_sessions = PuppyTraining.query.order_by(PuppyTraining.session_date.desc()).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        training_sessions = PuppyTraining.query.join(PuppyRecord).join(DeliveryRecord).join(PregnancyRecord).filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(PuppyTraining.session_date.desc()).all()
    
    return render_template('breeding/puppy_training_list.html', sessions=training_sessions)

@main_bp.route('/breeding/puppy-training/add', methods=['GET', 'POST'])
@login_required
def puppy_training_add():
    if request.method == 'POST':
        try:
            training = PuppyTraining(
                puppy_id=request.form['puppy_id'],
                trainer_id=request.form['trainer_id'],
                training_name=request.form['training_name'],
                training_type=TrainingCategory(request.form['training_type']),
                session_date=datetime.strptime(request.form['session_date'], '%Y-%m-%dT%H:%M'),
                duration=int(request.form['duration']),
                puppy_age_weeks=int(request.form['puppy_age_weeks']) if request.form.get('puppy_age_weeks') else None,
                developmental_stage=request.form.get('developmental_stage'),
                success_rating=int(request.form['success_rating']),
                behavior_observations=request.form.get('behavior_observations'),
                location=request.form.get('location'),
                weather_conditions=request.form.get('weather_conditions'),
                areas_for_improvement=request.form.get('areas_for_improvement'),
                notes=request.form.get('notes')
            )
            
            db.session.add(training)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'PuppyTraining', str(training.id), {'puppy': training.puppy.name, 'training': training.training_name})
            flash('تم تسجيل تدريب الجرو بنجاح', 'success')
            return redirect(url_for('main.puppy_training_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل تدريب الجرو: {str(e)}', 'error')
    
    # Get available puppies and trainers
    if current_user.role == UserRole.GENERAL_ADMIN:
        puppies = PuppyRecord.query.filter(PuppyRecord.alive_at_birth == True, PuppyRecord.current_status != 'متوفي').all()
        trainers = Employee.query.filter_by(role=EmployeeRole.TRAINER, is_active=True).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(PregnancyRecord.dog_id.in_(assigned_dog_ids), PuppyRecord.alive_at_birth == True, PuppyRecord.current_status != 'متوفي').all()
        trainers = Employee.query.filter_by(assigned_to_user_id=current_user.id, role=EmployeeRole.TRAINER, is_active=True).all()
    
    return render_template('breeding/puppy_training_add.html', puppies=puppies, trainers=trainers, categories=TrainingCategory)
