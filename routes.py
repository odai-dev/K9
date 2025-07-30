from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import Dog, Employee, TrainingSession, VeterinaryVisit, BreedingCycle, Project, AttendanceRecord, AuditLog, UserRole, DogStatus, EmployeeRole, TrainingCategory, VisitType
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
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.order_by(Dog.name).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).order_by(Dog.name).all()
    
    return render_template('dogs/list.html', dogs=dogs)

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
                family_line=request.form.get('family_line'),
                gender=request.form['gender'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date(),
                microchip_id=request.form.get('microchip_id'),
                location=request.form.get('location'),
                specialization=request.form.get('specialization'),
                color=request.form.get('color'),
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
                         vet_visits=vet_visits, breeding_cycles=breeding_cycles)

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
            dog.family_line = request.form.get('family_line')
            dog.gender = request.form['gender']
            dog.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            dog.microchip_id = request.form.get('microchip_id')
            dog.current_status = request.form['current_status']
            dog.location = request.form.get('location')
            dog.specialization = request.form.get('specialization')
            dog.color = request.form.get('color')
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
                id_number=request.form['id_number'],
                role=request.form['role'],
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date(),
                department=request.form.get('department'),
                rank=request.form.get('rank'),
                assigned_to_user_id=current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            )
            
            db.session.add(employee)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Employee', str(employee.id), {'name': employee.name, 'employee_id': employee.employee_id})
            
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
    
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
            employee.id_number = request.form['id_number']
            employee.role = request.form['role']
            employee.phone = request.form.get('phone')
            employee.email = request.form.get('email')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
            employee.department = request.form.get('department')
            employee.rank = request.form.get('rank')
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
@main_bp.route('/breeding')
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
            project = Project(
                name=request.form['name'],
                code=request.form['code'],
                description=request.form.get('description'),
                location=request.form.get('location'),
                mission_type=request.form.get('mission_type'),
                priority=request.form.get('priority', 'MEDIUM'),
                manager_id=current_user.id
            )
            
            if request.form.get('start_date'):
                project.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('expected_completion_date'):
                project.expected_completion_date = datetime.strptime(request.form['expected_completion_date'], '%Y-%m-%d').date()
            
            db.session.add(project)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Project', str(project.id), {'name': project.name, 'code': project.code})
            
            flash('تم إضافة المشروع بنجاح', 'success')
            return redirect(url_for('main.projects_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المشروع: {str(e)}', 'error')
    
    return render_template('projects/add.html')

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
    return render_template('reports/index.html')

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
