from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, abort, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from k9.models.models import (Dog, Employee, TrainingSession, VeterinaryVisit, ProductionCycle, 
                   Project, AuditLog, UserRole, DogStatus, 
                   EmployeeRole, TrainingCategory, VisitType, ProductionCycleType, 
                   ProductionResult, ProjectStatus, AuditAction, DogGender, User,
                   MaturityStatus, HeatStatus, PregnancyStatus, ProjectDog, ProjectAssignment,
                   Incident, Suspicion, PerformanceEvaluation, 
                   ElementType, PerformanceRating, TargetType,
                   project_employee_assignment, project_dog_assignment,
                   # Production models
                   HeatCycle, MatingRecord, MatingResult, PregnancyRecord, DeliveryRecord, PuppyRecord, PuppyTraining,
                   # New attendance models
                   ProjectShift, ProjectShiftAssignment, ProjectAttendance,
                   EntityType, AttendanceStatus, AbsenceReason, AttendanceDay,
                   # Standalone attendance models
                   Shift, ShiftAssignment, Attendance,
                   # Breeding models
                   FeedingLog, PrepMethod, BodyConditionScale, DailyCheckupLog, PermissionType,
                   # Excretion models
                   ExcretionLog, StoolColor, StoolConsistency, StoolContent, UrineColor, VomitColor, ExcretionPlace,
                   # Grooming models
                   GroomingLog, GroomingCleanlinessScore, GroomingYesNo,
                   # Cleaning models
                   CleaningLog)
from k9.utils.utils import log_audit, allowed_file, generate_pdf_report, get_project_manager_permissions, get_employee_profile_for_user, get_user_active_projects, validate_project_manager_assignment, get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
from k9.utils.permission_decorators import require_sub_permission
import os
from datetime import datetime, date, timedelta
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
        # Optimize with single queries combining multiple counts
        from sqlalchemy import func
        stats['total_dogs'] = Dog.query.count()
        stats['active_dogs'] = Dog.query.filter_by(current_status=DogStatus.ACTIVE).count()
        stats['total_employees'] = Employee.query.count()
        stats['active_employees'] = Employee.query.filter_by(is_active=True).count()
        stats['total_projects'] = Project.query.count()
        
        # Recent activities - limit to reduce load
        recent_training = TrainingSession.query.order_by(TrainingSession.created_at.desc()).limit(3).all()
        recent_vet_visits = VeterinaryVisit.query.order_by(VeterinaryVisit.created_at.desc()).limit(3).all()
        
    else:  # PROJECT_MANAGER - Use permission-based access
        # Get data through SubPermission system
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_employees = get_user_accessible_employees(current_user)
        
        stats['total_dogs'] = len(assigned_dogs)
        stats['active_dogs'] = len([d for d in assigned_dogs if d.current_status == DogStatus.ACTIVE])
        stats['total_employees'] = len(assigned_employees)
        stats['active_employees'] = len([e for e in assigned_employees if e.is_active])
        stats['total_projects'] = len(assigned_projects)
        
        # Recent activities for assigned dogs only
        dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if dog_ids:
            recent_training = TrainingSession.query.filter(TrainingSession.dog_id.in_(dog_ids)).order_by(TrainingSession.created_at.desc()).limit(5).all()
            recent_vet_visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(dog_ids)).order_by(VeterinaryVisit.created_at.desc()).limit(5).all()
        else:
            recent_training = []
            recent_vet_visits = []
    
    return render_template('dashboard.html', stats=stats, recent_training=recent_training, recent_vet_visits=recent_vet_visits)

# Dog management routes
@main_bp.route('/dogs')
@login_required
def dogs_list():
    from datetime import date
    # Use permission-based access for both roles
    dogs = get_user_accessible_dogs(current_user)
    dogs.sort(key=lambda x: x.name or '')  # Sort by name
    
    return render_template('dogs/list.html', dogs=dogs, today=date.today())

@main_bp.route('/dogs/add', methods=['GET', 'POST'])
@login_required  
def dogs_add():
    # Get potential parents for dropdowns
    potential_parents = get_user_accessible_dogs(current_user)
    
    if request.method == 'POST':
        try:
            # Handle photo upload
            photo_filename = None
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                if photo.filename and allowed_file(photo.filename):
                    # Create unique filename
                    safe_filename = secure_filename(photo.filename or 'image')
                    photo_filename = f"{uuid.uuid4()}_{safe_filename}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
                    photo.save(photo_path)
            
            # Handle birth certificate upload
            birth_cert_filename = None
            if 'birth_certificate' in request.files and request.files['birth_certificate'].filename:
                cert = request.files['birth_certificate']
                if cert.filename and allowed_file(cert.filename):
                    # Create unique filename
                    safe_cert_filename = secure_filename(cert.filename or 'certificate')
                    birth_cert_filename = f"{uuid.uuid4()}_{safe_cert_filename}"
                    cert_path = os.path.join(current_app.config['UPLOAD_FOLDER'], birth_cert_filename)
                    cert.save(cert_path)
            
            # Determine who the dog should be assigned to
            assigned_to_user_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            
            # Create Dog instance using proper constructor
            dog = Dog()
            dog.name = request.form['name']
            dog.code = request.form['code']
            dog.breed = request.form['breed']
            dog.family_line = request.form.get('family_line')
            dog.gender = DogGender(request.form['gender'])
            dog.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form['birth_date'] else None
            dog.color = request.form.get('color')
            dog.weight = float(request.form['weight']) if request.form.get('weight') and request.form.get('weight').strip() else None
            dog.height = float(request.form['height']) if request.form.get('height') and request.form.get('height').strip() else None
            dog.microchip_id = request.form.get('microchip_id').strip() if request.form.get('microchip_id') and request.form.get('microchip_id').strip() else None
            dog.location = request.form.get('location')
            dog.specialization = request.form.get('specialization')
            dog.current_status = DogStatus.ACTIVE
            dog.photo = photo_filename
            dog.birth_certificate = birth_cert_filename
            dog.assigned_to_user_id = assigned_to_user_id
            dog.father_id = request.form.get('father_id') if request.form.get('father_id') else None
            dog.mother_id = request.form.get('mother_id') if request.form.get('mother_id') else None
            
            db.session.add(dog)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Dog', dog.id, f'أضيف كلب جديد: {dog.name}', None, {'name': dog.name, 'breed': dog.breed, 'code': dog.code})
            flash('تم إضافة الكلب بنجاح', 'success')
            return redirect(url_for('main.dogs_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding dog: {e}")
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ أثناء إضافة الكلب: {str(e)}', 'error')
    
    return render_template('dogs/add.html', genders=DogGender, potential_parents=potential_parents)

@main_bp.route('/dogs/<dog_id>')
@login_required
def dogs_view(dog_id):
    try:
        dog_id = dog_id
        dog = Dog.query.get_or_404(dog_id)
    except ValueError:
        flash('معرف الكلب غير صحيح', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and dog.assigned_to_user_id != current_user.id:
        flash('غير مسموح لك بعرض بيانات هذا الكلب', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Get related data
    training_sessions = TrainingSession.query.filter_by(dog_id=dog.id).order_by(TrainingSession.created_at.desc()).all()
    vet_visits = VeterinaryVisit.query.filter_by(dog_id=dog.id).order_by(VeterinaryVisit.created_at.desc()).all()
    production_cycles = ProductionCycle.query.filter(
        (ProductionCycle.female_id == dog.id) | (ProductionCycle.male_id == dog.id)
    ).order_by(ProductionCycle.created_at.desc()).all()
    
    return render_template('dogs/view.html', dog=dog, training_sessions=training_sessions, 
                         vet_visits=vet_visits, production_cycles=production_cycles, 
                         today=datetime.now().date())

@main_bp.route('/dogs/<dog_id>/edit', methods=['GET', 'POST'])
@login_required
def dogs_edit(dog_id):
    try:
        dog_id = dog_id
        dog = Dog.query.get_or_404(dog_id)
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
                    photo_filename = f"{uuid.uuid4()}_{secure_filename(photo.filename or 'image')}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
                    photo.save(photo_path)
                    dog.photo_path = photo_filename
            
            # Handle birth certificate upload
            if 'birth_certificate' in request.files and request.files['birth_certificate'].filename != '':
                birth_cert = request.files['birth_certificate']
                if allowed_file(birth_cert.filename):
                    # Delete old certificate if exists
                    if dog.birth_certificate:
                        old_cert_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dog.birth_certificate)
                        if os.path.exists(old_cert_path):
                            os.remove(old_cert_path)
                    
                    # Save new certificate
                    cert_filename = f"{uuid.uuid4()}_{secure_filename(birth_cert.filename or 'certificate')}"
                    cert_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cert_filename)
                    birth_cert.save(cert_path)
                    dog.birth_certificate = cert_filename

            # Update dog data - fix field name mismatches
            dog.name = request.form['name']
            dog.code = request.form['code']
            dog.breed = request.form['breed']
            dog.family_line = request.form.get('family_line') if request.form.get('family_line', '').strip() else None
            dog.gender = DogGender(request.form['gender'])
            dog.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form['birth_date'] else None
            dog.microchip_id = request.form.get('microchip_id') if request.form.get('microchip_id', '').strip() else None
            dog.current_status = DogStatus(request.form['current_status'])
            dog.color = request.form.get('color') if request.form.get('color', '').strip() else None
            dog.weight = float(request.form['weight']) if request.form.get('weight', '').strip() else None
            dog.height = float(request.form['height']) if request.form.get('height', '').strip() else None
            dog.location = request.form.get('location') if request.form.get('location', '').strip() else None
            dog.specialization = request.form.get('specialization') if request.form.get('specialization', '').strip() else None
            
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
    print(f"Employee add route called with method: {request.method}")
    if request.method == 'POST':
        print(f"Form data: {dict(request.form)}")
        try:
            # Determine who the employee should be assigned to
            assigned_to_user_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else None
            
            employee = Employee()
            employee.name = request.form['name']
            employee.employee_id = request.form['employee_id']
            # Map form values to enum values
            role_mapping = {
                'HANDLER': EmployeeRole.HANDLER,
                'TRAINER': EmployeeRole.TRAINER,
                'BREEDER': EmployeeRole.BREEDER,
                'VET': EmployeeRole.VET,
                'PROJECT_MANAGER': EmployeeRole.PROJECT_MANAGER
            }
            employee.role = role_mapping[request.form['role']]
            employee.phone = request.form.get('phone')
            employee.email = request.form.get('email')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None
            employee.is_active = True
            employee.assigned_to_user_id = assigned_to_user_id
            
            db.session.add(employee)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Employee', employee.id, f'أضيف موظف جديد: {employee.name}', None, {'name': employee.name, 'role': employee.role.value})
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding employee: {e}")
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
    
    return render_template('employees/add.html', roles=EmployeeRole)

@main_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
def employees_edit(employee_id):
    try:
        employee_id = employee_id
        employee = Employee.query.get_or_404(employee_id)
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
            # Map form values to enum values
            role_mapping = {
                'HANDLER': EmployeeRole.HANDLER,
                'TRAINER': EmployeeRole.TRAINER,
                'BREEDER': EmployeeRole.BREEDER,
                'VET': EmployeeRole.VET,
                'PROJECT_MANAGER': EmployeeRole.PROJECT_MANAGER
            }
            employee.role = role_mapping[request.form['role']]
            employee.contact_info = request.form.get('contact_info')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None
            employee.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.UPDATE, 'Employee', employee.id, f'تم تحديث بيانات الموظف: {employee.name}', None, {'name': employee.name})
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
    """Redirect legacy training list to new breeding training activity"""
    return redirect(url_for('main.breeding_training_activity'), code=301)

@main_bp.route('/training/add', methods=['GET', 'POST'])
@login_required
def training_add():
    """Redirect legacy training add to new breeding training activity"""
    return redirect(url_for('main.breeding_training_activity_new'), code=301)

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
            from k9.utils.utils import auto_link_dog_activity_to_project
            from datetime import datetime
            
            # Create veterinary visit with proper model construction
            visit = VeterinaryVisit()
            visit.dog_id = request.form['dog_id']
            visit.vet_id = request.form['vet_id']
            visit.visit_type = VisitType(request.form['visit_type'])
            visit.visit_date = datetime.strptime(request.form['visit_date'], '%Y-%m-%dT%H:%M') if request.form.get('visit_date') else datetime.utcnow()
            visit.weight = float(request.form['weight']) if request.form.get('weight') else None
            visit.temperature = float(request.form['temperature']) if request.form.get('temperature') else None
            visit.heart_rate = int(request.form['heart_rate']) if request.form.get('heart_rate') else None
            visit.blood_pressure = request.form.get('blood_pressure')
            visit.symptoms = request.form.get('symptoms')
            visit.diagnosis = request.form.get('diagnosis')
            visit.treatment = request.form.get('treatment')
            visit.stool_color = request.form.get('stool_color')
            visit.stool_consistency = request.form.get('stool_consistency')
            visit.urine_color = request.form.get('urine_color')
            visit.next_visit_date = datetime.strptime(request.form['next_visit_date'], '%Y-%m-%d').date() if request.form.get('next_visit_date') else None
            visit.notes = request.form.get('notes')
            visit.cost = float(request.form['cost']) if request.form.get('cost') else None
            
            # Automatically link to project based on dog assignment
            visit.project_id = auto_link_dog_activity_to_project(visit.dog_id, visit.visit_date)
            
            db.session.add(visit)
            db.session.commit()
            
            project_info = f" (مرتبط بالمشروع: {visit.project.name})" if visit.project else " (غير مرتبط بمشروع)"
            log_audit(current_user.id, AuditAction.CREATE, 'VeterinaryVisit', visit.id, f'زيارة بيطرية جديدة للكلب {visit.dog.name}{project_info}', None, {'visit_type': visit.visit_type.value})
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

# Production routes
@main_bp.route('/production')
@login_required
def production_list():
    if current_user.role == UserRole.GENERAL_ADMIN:
        cycles = ProductionCycle.query.order_by(ProductionCycle.created_at.desc()).all()
        all_dogs = Dog.query.all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        cycles = ProductionCycle.query.filter(
            db.or_(ProductionCycle.female_id.in_(assigned_dog_ids), ProductionCycle.male_id.in_(assigned_dog_ids))
        ).order_by(ProductionCycle.created_at.desc()).all()
        all_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id).all()
    
    # Calculate production statistics
    stats = {
        'total_dogs': len(all_dogs),
        'mature_dogs': len([d for d in all_dogs if d.gender == DogGender.FEMALE]),
        'production_ready_females': len([d for d in all_dogs if d.gender == DogGender.FEMALE and d.current_status == DogStatus.ACTIVE]),
        'production_males': len([d for d in all_dogs if d.gender == DogGender.MALE and d.current_status == DogStatus.ACTIVE]),
        'active_pregnancies': 0,  # This would need pregnancy tracking
        'recent_births': 0  # This would need birth tracking
    }
    
    return render_template('production/index.html', cycles=cycles, stats=stats)

@main_bp.route('/production/add', methods=['GET', 'POST'])
@login_required
def production_add():
    if request.method == 'POST':
        try:
            cycle = ProductionCycle()
            cycle.female_id = request.form['female_id']
            cycle.male_id = request.form['male_id']
            cycle.cycle_type = ProductionCycleType(request.form['cycle_type'])
            cycle.mating_date = datetime.strptime(request.form['mating_date'], '%Y-%m-%d').date()
            if request.form.get('heat_start_date'):
                cycle.heat_start_date = datetime.strptime(request.form['heat_start_date'], '%Y-%m-%d').date()
            if request.form.get('expected_delivery_date'):
                cycle.expected_delivery_date = datetime.strptime(request.form['expected_delivery_date'], '%Y-%m-%d').date()
            if request.form.get('actual_delivery_date'):
                cycle.actual_delivery_date = datetime.strptime(request.form['actual_delivery_date'], '%Y-%m-%d').date()
            if request.form.get('result'):
                cycle.result = ProductionResult(request.form['result'])
            else:
                cycle.result = ProductionResult.UNKNOWN
            cycle.prenatal_care = request.form.get('prenatal_care')
            cycle.delivery_notes = request.form.get('delivery_notes')
            cycle.complications = request.form.get('complications')
            
            db.session.add(cycle)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'ProductionCycle', cycle.id, f'دورة إنتاج جديدة: {cycle.female.name} × {cycle.male.name}', None, {'cycle_type': cycle.cycle_type.value})
            flash('تم تسجيل دورة التربية بنجاح', 'success')
            return redirect(url_for('main.production_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل دورة التربية: {str(e)}', 'error')
    
    # Get available dogs for the form - separate males and females
    if current_user.role == UserRole.GENERAL_ADMIN:
        all_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        all_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    males = [dog for dog in all_dogs if dog.gender == DogGender.MALE]
    
    return render_template('production/add.html', females=females, males=males, cycle_types=ProductionCycleType, results=ProductionResult)

# Individual production component routes
@main_bp.route('/production/maturity')
@login_required
def maturity_list():
    from k9.models.models import DogMaturity
    if current_user.role == UserRole.GENERAL_ADMIN:
        maturity_records = DogMaturity.query.order_by(DogMaturity.created_at.desc()).all()
    else:
        # Get assigned dogs and their maturity records
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        maturity_records = DogMaturity.query.filter(DogMaturity.dog_id.in_(assigned_dog_ids)).order_by(DogMaturity.created_at.desc()).all()
    
    return render_template('production/maturity_list.html', records=maturity_records, maturities=maturity_records)

@main_bp.route('/production/maturity/add', methods=['GET', 'POST'])
@login_required
def maturity_add():
    if request.method == 'POST':
        try:
            from k9.models.models import DogMaturity, MaturityStatus
            maturity = DogMaturity()
            maturity.dog_id = request.form['dog_id']
            maturity.maturity_date = datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date()
            maturity.maturity_status = MaturityStatus.MATURE  # Set default status
            if request.form.get('weight_at_maturity'):
                maturity.weight_at_maturity = float(request.form['weight_at_maturity'])
            if request.form.get('height_at_maturity'):
                maturity.height_at_maturity = float(request.form['height_at_maturity'])
            maturity.notes = request.form.get('notes')
            
            db.session.add(maturity)
            db.session.commit()
            
            # Log audit
            from k9.utils.utils import log_audit
            from k9.models.models import AuditAction
            log_audit(current_user.id, AuditAction.CREATE, 'DogMaturity', maturity.id, 
                     f'تسجيل بلوغ جديد للكلب {maturity.dog.name}', None, {'maturity_date': str(maturity.maturity_date)})
            
            flash('تم تسجيل البلوغ بنجاح', 'success')
            return redirect(url_for('main.maturity_list'))
        except Exception as e:
            db.session.rollback()
            print(f'Maturity add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get available dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    return render_template('production/maturity_add.html', dogs=dogs)

@main_bp.route('/production/heat-cycles')
@login_required  
def heat_cycles_list():
    from k9.models.models import HeatCycle
    if current_user.role == UserRole.GENERAL_ADMIN:
        heat_cycles = HeatCycle.query.order_by(HeatCycle.created_at.desc()).all()
    else:
        # Get assigned dogs and their heat cycles
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        heat_cycles = HeatCycle.query.filter(HeatCycle.dog_id.in_(assigned_dog_ids)).order_by(HeatCycle.created_at.desc()).all()
    
    return render_template('production/heat_cycles_list.html', records=heat_cycles, heat_cycles=heat_cycles)

@main_bp.route('/production/heat-cycles/add', methods=['GET', 'POST'])
@login_required
def heat_cycles_add():
    if request.method == 'POST':
        try:
            from k9.models.models import HeatCycle, HeatStatus
            heat_cycle = HeatCycle()
            heat_cycle.dog_id = request.form['dog_id']
            # Use user-entered cycle number (allows recording of historical cycles)
            heat_cycle.cycle_number = int(request.form['cycle_number'])
            heat_cycle.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            if request.form.get('end_date'):
                heat_cycle.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
                heat_cycle.status = HeatStatus.COMPLETED
            else:
                heat_cycle.status = HeatStatus.IN_HEAT
            heat_cycle.behavioral_changes = request.form.get('behavioral_changes')
            heat_cycle.physical_signs = request.form.get('physical_signs')
            heat_cycle.appetite_changes = request.form.get('appetite_changes')
            heat_cycle.notes = request.form.get('notes')
            
            db.session.add(heat_cycle)
            db.session.commit()
            
            # Log audit
            from k9.utils.utils import log_audit
            from k9.models.models import AuditAction
            log_audit(current_user.id, AuditAction.CREATE, 'HeatCycle', heat_cycle.id, 
                     f'تسجيل دورة حرارية جديدة للكلب {heat_cycle.dog.name}', None, {'cycle_number': heat_cycle.cycle_number})
            
            flash('تم تسجيل الدورة الحرارية بنجاح', 'success')
            return redirect(url_for('main.heat_cycles_list'))
        except Exception as e:
            db.session.rollback()
            print(f'Heat cycle add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get available female dogs for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        all_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
    else:
        all_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
    
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    
    return render_template('production/heat_cycles_add.html', females=females)

@main_bp.route('/production/mating')
@login_required
def mating_list():
    from k9.models.models import MatingRecord
    if current_user.role == UserRole.GENERAL_ADMIN:
        mating_records = MatingRecord.query.order_by(MatingRecord.created_at.desc()).all()
    else:
        # Get assigned dogs and their mating records
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        mating_records = MatingRecord.query.filter(
            db.or_(MatingRecord.female_id.in_(assigned_dog_ids), MatingRecord.male_id.in_(assigned_dog_ids))
        ).order_by(MatingRecord.created_at.desc()).all()
    
    return render_template('production/mating_list.html', records=mating_records, matings=mating_records)

@main_bp.route('/production/mating/add', methods=['GET', 'POST'])
@login_required
def mating_add():
    if request.method == 'POST':
        try:
            from k9.models.models import MatingRecord, MatingResult
            mating = MatingRecord()
            mating.female_id = request.form['female_id']
            mating.male_id = request.form['male_id']
            # Set heat_cycle_id if provided, otherwise None (nullable field)
            heat_cycle_id = request.form.get('heat_cycle_id')
            if heat_cycle_id and heat_cycle_id.strip():
                mating.heat_cycle_id = heat_cycle_id
            else:
                mating.heat_cycle_id = None
            mating.mating_date = datetime.strptime(request.form['mating_date'], '%Y-%m-%d').date()
            if request.form.get('mating_time'):
                mating.mating_time = datetime.strptime(request.form['mating_time'], '%H:%M').time()
            mating.location = request.form.get('location')
            if request.form.get('supervised_by'):
                mating.supervised_by = request.form['supervised_by']
            if request.form.get('duration_minutes'):
                mating.duration_minutes = int(request.form['duration_minutes'])
            if request.form.get('success_rate'):
                mating.success_rate = int(request.form['success_rate'])
            mating.result = MatingResult.UNKNOWN  # Set default result
            mating.behavior_observed = request.form.get('behavior_observed')
            mating.complications = request.form.get('complications')
            mating.notes = request.form.get('notes')
            
            db.session.add(mating)
            db.session.commit()
            
            # Log audit
            from k9.utils.utils import log_audit
            from k9.models.models import AuditAction
            log_audit(current_user.id, AuditAction.CREATE, 'MatingRecord', mating.id, 
                     f'تسجيل تزاوج جديد: {mating.female.name} × {mating.male.name}', None, {'mating_date': str(mating.mating_date)})
            
            flash('تم تسجيل التزاوج بنجاح', 'success')
            return redirect(url_for('main.mating_list'))
        except Exception as e:
            db.session.rollback()
            print(f'Mating add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get available dogs and employees for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        all_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        all_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    males = [dog for dog in all_dogs if dog.gender == DogGender.MALE]
    
    return render_template('production/mating_add.html', females=females, males=males, employees=employees)

@main_bp.route('/production/pregnancy')
@login_required
def pregnancy_list():
    from k9.models.models import PregnancyRecord
    if current_user.role == UserRole.GENERAL_ADMIN:
        pregnancy_records = PregnancyRecord.query.order_by(PregnancyRecord.created_at.desc()).all()
    else:
        # Get assigned dogs and their pregnancy records
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        pregnancy_records = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(assigned_dog_ids)).order_by(PregnancyRecord.created_at.desc()).all()
    
    return render_template('production/pregnancy_list.html', pregnancies=pregnancy_records, records=pregnancy_records)

@main_bp.route('/production/pregnancy/add', methods=['GET', 'POST'])
@login_required
def pregnancy_add():
    if request.method == 'POST':
        try:
            from k9.models.models import PregnancyRecord, PregnancyStatus
            pregnancy = PregnancyRecord()
            pregnancy.dog_id = request.form['dog_id']  # This comes from the hidden field updated by JavaScript
            pregnancy.mating_record_id = request.form['mating_record_id']
                
            pregnancy.confirmed_date = datetime.strptime(request.form['confirmed_date'], '%Y-%m-%d').date()
            pregnancy.expected_delivery_date = datetime.strptime(request.form['expected_delivery_date'], '%Y-%m-%d').date()
            pregnancy.status = PregnancyStatus.PREGNANT
            
            pregnancy.special_diet = request.form.get('special_diet')
            pregnancy.exercise_restrictions = request.form.get('exercise_restrictions')
            pregnancy.notes = request.form.get('notes')
            
            db.session.add(pregnancy)
            db.session.commit()
            
            # Log audit
            from k9.utils.utils import log_audit
            from k9.models.models import AuditAction
            log_audit(current_user.id, AuditAction.CREATE, 'PregnancyRecord', pregnancy.id, 
                     f'تسجيل حمل جديد للكلبة {pregnancy.dog.name}', None, {'confirmed_date': str(pregnancy.confirmed_date)})
            
            flash('تم تسجيل الحمل بنجاح', 'success')
            return redirect(url_for('main.pregnancy_list'))
        except Exception as e:
            db.session.rollback()
            print(f'Pregnancy add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get available females and mating records for pregnancy
    from k9.models.models import MatingRecord
    if current_user.role == UserRole.GENERAL_ADMIN:
        all_dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        mating_records = MatingRecord.query.order_by(MatingRecord.created_at.desc()).all()
    else:
        all_dogs = Dog.query.filter_by(assigned_to_user_id=current_user.id, current_status=DogStatus.ACTIVE).all()
        assigned_dog_ids = [d.id for d in all_dogs]
        mating_records = MatingRecord.query.filter(
            db.or_(MatingRecord.female_id.in_(assigned_dog_ids), MatingRecord.male_id.in_(assigned_dog_ids))
        ).order_by(MatingRecord.created_at.desc()).all()
    
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    
    return render_template('production/pregnancy_add.html', females=females, matings=mating_records)

@main_bp.route('/production/delivery')
@login_required
def delivery_list():
    from k9.models.models import DeliveryRecord
    try:
        if current_user.role == UserRole.GENERAL_ADMIN:
            delivery_records = DeliveryRecord.query.order_by(DeliveryRecord.created_at.desc()).all()
        else:
            # Get accessible dogs for this user
            assigned_dogs = get_user_accessible_dogs(current_user)
            assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
            if assigned_dog_ids:
                delivery_records = DeliveryRecord.query.join(PregnancyRecord).filter(
                    PregnancyRecord.dog_id.in_(assigned_dog_ids)
                ).order_by(DeliveryRecord.created_at.desc()).all()
            else:
                delivery_records = []
    except Exception as e:
        print(f"Error fetching delivery records: {e}")
        delivery_records = []
    
    return render_template('production/delivery_list.html', deliveries=delivery_records, records=delivery_records)

@main_bp.route('/production/delivery/add', methods=['GET', 'POST'])
@login_required
def delivery_add():
    if request.method == 'POST':
        try:
            from k9.models.models import DeliveryRecord, PregnancyRecord, PregnancyStatus
            delivery = DeliveryRecord()
            delivery.pregnancy_record_id = request.form.get('pregnancy_record_id') or request.form.get('pregnancy_id')
            delivery.delivery_date = datetime.strptime(request.form['delivery_date'], '%Y-%m-%d').date()
            
            if request.form.get('delivery_start_time'):
                delivery.delivery_start_time = datetime.strptime(request.form['delivery_start_time'], '%H:%M').time()
            if request.form.get('delivery_end_time'):
                delivery.delivery_end_time = datetime.strptime(request.form['delivery_end_time'], '%H:%M').time()
                
            if request.form.get('vet_present'):
                delivery.vet_present = request.form['vet_present']
            if request.form.get('handler_present'):
                delivery.handler_present = request.form['handler_present']
                
            if request.form.get('total_puppies'):
                delivery.total_puppies = int(request.form['total_puppies'])
            if request.form.get('live_births'):
                delivery.live_births = int(request.form['live_births'])
            if request.form.get('stillbirths'):
                delivery.stillbirths = int(request.form['stillbirths'])
                
            delivery.delivery_complications = request.form.get('delivery_complications')
            delivery.mother_condition = request.form.get('mother_condition')
            delivery.notes = request.form.get('notes')
            
            db.session.add(delivery)
            
            # Update pregnancy status to delivered
            pregnancy_id = request.form.get('pregnancy_record_id') or request.form.get('pregnancy_id')
            pregnancy = PregnancyRecord.query.get(pregnancy_id)
            if pregnancy:
                pregnancy.status = PregnancyStatus.DELIVERED
                
            db.session.commit()
            
            # Log audit
            from k9.utils.utils import log_audit
            from k9.models.models import AuditAction
            log_audit(current_user.id, AuditAction.CREATE, 'DeliveryRecord', delivery.id, 
                     f'تسجيل ولادة جديدة للكلبة {delivery.pregnancy_record.dog.name}', None, {'delivery_date': str(delivery.delivery_date)})
            
            flash('تم تسجيل الولادة بنجاح', 'success')
            return redirect(url_for('main.delivery_list'))
        except Exception as e:
            db.session.rollback()
            print(f'Delivery add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get available pregnancies and employees for delivery
    from k9.models.models import PregnancyRecord, PregnancyStatus
    if current_user.role == UserRole.GENERAL_ADMIN:
        pregnancies = PregnancyRecord.query.filter_by(status=PregnancyStatus.PREGNANT).order_by(PregnancyRecord.expected_delivery_date.asc()).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_dog_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
        pregnancies = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(assigned_dog_ids), PregnancyRecord.status == PregnancyStatus.PREGNANT).order_by(PregnancyRecord.expected_delivery_date.asc()).all()
        employees = Employee.query.filter_by(assigned_to_user_id=current_user.id, is_active=True).all()
    
    return render_template('production/delivery_add.html', pregnancies=pregnancies, employees=employees)

@main_bp.route('/production/puppies')
@login_required
def puppies_list():
    from k9.models.models import PuppyRecord, DeliveryRecord
    try:
        if current_user.role == UserRole.GENERAL_ADMIN:
            puppies = PuppyRecord.query.order_by(PuppyRecord.created_at.desc()).all()
        else:
            # Get accessible dogs for this user
            assigned_dogs = get_user_accessible_dogs(current_user)
            assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
            if assigned_dog_ids:
                puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(
                    PregnancyRecord.dog_id.in_(assigned_dog_ids)
                ).order_by(PuppyRecord.created_at.desc()).all()
            else:
                puppies = []
    except Exception as e:
        print(f"Error fetching puppy records: {e}")
        puppies = []
    
    return render_template('production/puppies_list.html', puppies=puppies)

@main_bp.route('/production/puppies/add', methods=['GET', 'POST'])
@login_required
def puppies_add():
    if request.method == 'POST':
        try:
            from k9.models.models import PuppyRecord, DeliveryRecord
            puppy = PuppyRecord()
            puppy.delivery_record_id = request.form['delivery_record_id']
            puppy.puppy_number = int(request.form['puppy_number'])
            puppy.name = request.form.get('name')
            puppy.temporary_id = request.form.get('temporary_id')
            puppy.gender = DogGender(request.form['gender'])
            
            if request.form.get('birth_weight'):
                puppy.birth_weight = float(request.form['birth_weight'])
            if request.form.get('birth_time'):
                puppy.birth_time = datetime.strptime(request.form['birth_time'], '%H:%M').time()
            if request.form.get('birth_order'):
                puppy.birth_order = int(request.form['birth_order'])
                
            puppy.alive_at_birth = 'alive_at_birth' in request.form
            puppy.current_status = request.form.get('current_status', 'صحي ونشط')
            puppy.color = request.form.get('color')
            puppy.markings = request.form.get('markings')
            puppy.birth_defects = request.form.get('birth_defects')
            puppy.notes = request.form.get('notes')
            
            db.session.add(puppy)
            db.session.commit()
            
            # Log audit
            log_audit(current_user.id, AuditAction.CREATE, 'PuppyRecord', puppy.id, 
                     f'تسجيل جرو جديد: {puppy.name or "جرو رقم " + str(puppy.puppy_number)}', None, 
                     {'delivery_record_id': str(puppy.delivery_record_id), 'puppy_number': puppy.puppy_number})
            
            flash('تم تسجيل الجرو بنجاح', 'success')
            return redirect(url_for('main.puppies_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تسجيل الجرو: {str(e)}', 'error')
    
    # Get delivery records for puppies dropdown
    from k9.models.models import DeliveryRecord, PregnancyRecord
    try:
        if current_user.role == UserRole.GENERAL_ADMIN:
            deliveries = DeliveryRecord.query.order_by(DeliveryRecord.delivery_date.desc()).all()
        else:
            # Get assigned dogs and their delivery records
            assigned_dogs = get_user_accessible_dogs(current_user)
            assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
            if assigned_dog_ids:
                deliveries = DeliveryRecord.query.join(PregnancyRecord).filter(
                    PregnancyRecord.dog_id.in_(assigned_dog_ids)
                ).order_by(DeliveryRecord.delivery_date.desc()).all()
            else:
                deliveries = []
    except Exception as e:
        print(f"Error fetching delivery records: {e}")
        deliveries = []
    
    # Add helpful message if no delivery records exist
    if not deliveries:
        flash('لا توجد سجلات ولادة متاحة. يجب إنشاء سجلات الحمل والولادة أولاً من قسم التربية.', 'info')
    
    return render_template('production/puppies_add.html', deliveries=deliveries)

# View routes for all breeding sections
@main_bp.route('/production/maturity/view/<id>')
@login_required
def maturity_view(id):
    from k9.models.models import DogMaturity
    maturity = DogMaturity.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if maturity.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/maturity_view.html', maturity=maturity)

@main_bp.route('/production/heat-cycles/view/<id>')
@login_required
def heat_cycles_view(id):
    from k9.models.models import HeatCycle
    heat_cycle = HeatCycle.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if heat_cycle.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/heat_cycles_view.html', heat_cycle=heat_cycle)

@main_bp.route('/production/mating/view/<id>')
@login_required
def mating_view(id):
    from k9.models.models import MatingRecord
    mating = MatingRecord.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if mating.female_id not in assigned_dog_ids and mating.male_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/mating_view.html', mating=mating)

@main_bp.route('/production/pregnancy/view/<id>')
@login_required
def pregnancy_view(id):
    from k9.models.models import PregnancyRecord
    pregnancy = PregnancyRecord.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if pregnancy.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/pregnancy_view.html', pregnancy=pregnancy)

@main_bp.route('/production/delivery/view/<id>')
@login_required
def delivery_view(id):
    from k9.models.models import DeliveryRecord
    delivery = DeliveryRecord.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if delivery.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/delivery_view.html', delivery=delivery)

@main_bp.route('/production/puppies/view/<id>')
@login_required
def puppies_view(id):
    from k9.models.models import PuppyRecord
    puppy = PuppyRecord.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if puppy.delivery_record.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/puppies_view.html', puppy=puppy)

@main_bp.route('/production/puppy-training')
@login_required
def puppy_training_list():
    # Get puppy training sessions
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Get all training sessions
        sessions = PuppyTraining.query.order_by(PuppyTraining.session_date.desc()).all()
    else:
        # Get sessions for accessible dogs only
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        
        sessions = PuppyTraining.query.join(PuppyRecord).join(DeliveryRecord).join(PregnancyRecord).filter(
            PregnancyRecord.dog_id.in_(assigned_dog_ids)
        ).order_by(PuppyTraining.session_date.desc()).all()
    
    return render_template('production/puppy_training_list.html', sessions=sessions)

@main_bp.route('/production/puppy-training/view/<id>')
@login_required
def puppy_training_view(id):
    session = PuppyTraining.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN:
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if session.puppy.delivery_record.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/puppy_training_view.html', session=session)

@main_bp.route('/production/puppy-training/add', methods=['GET', 'POST'])
@login_required
def puppy_training_add():
    if request.method == 'POST':
        # Create new puppy training record
        puppy_training = PuppyTraining()
        puppy_training.puppy_id = request.form['puppy_id']
        puppy_training.trainer_id = request.form['trainer_id']
        puppy_training.training_name = request.form['training_name']
        puppy_training.training_type = request.form['training_type']
        puppy_training.session_date = datetime.strptime(request.form['session_date'], '%Y-%m-%dT%H:%M')
        puppy_training.duration = int(request.form['duration'])
        puppy_training.puppy_age_weeks = int(request.form['puppy_age_weeks']) if request.form.get('puppy_age_weeks') else None
        puppy_training.developmental_stage = request.form.get('developmental_stage')
        puppy_training.success_rating = int(request.form['success_rating'])
        puppy_training.location = request.form.get('location')
        puppy_training.weather_conditions = request.form.get('weather_conditions')
        puppy_training.behavior_observations = request.form.get('behavior_observations')
        puppy_training.areas_for_improvement = request.form.get('areas_for_improvement')
        puppy_training.notes = request.form.get('notes')
        
        db.session.add(puppy_training)
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.CREATE, 'PuppyTraining', puppy_training.id, 
                 f'إضافة جلسة تدريب جرو: {request.form["training_name"]}')
        
        flash('تم تسجيل تدريب الجرو بنجاح', 'success')
        return redirect(url_for('main.puppy_training_list'))
    
    # Get puppies and trainers for puppy training
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Get all available puppies (alive and healthy)
        puppies = PuppyRecord.query.filter(
            PuppyRecord.alive_at_birth == True,
            PuppyRecord.current_status.notin_(['متوفي', 'مريض', 'غير صالح'])
        ).order_by(PuppyRecord.created_at.desc()).all()
        trainers = Employee.query.filter_by(role=EmployeeRole.TRAINER, is_active=True).all()
    else:
        # Get puppies from accessible dogs only
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        
        puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(
            PregnancyRecord.dog_id.in_(assigned_dog_ids),
            PuppyRecord.alive_at_birth == True,
            PuppyRecord.current_status.notin_(['متوفي', 'مريض', 'غير صالح'])
        ).order_by(PuppyRecord.created_at.desc()).all()
        
        trainers = Employee.query.filter_by(assigned_to_user_id=current_user.id, role=EmployeeRole.TRAINER, is_active=True).all()
    
    # Training categories for dropdown
    categories = [
        {'name': 'OBEDIENCE', 'value': 'تدريب الطاعة'},
        {'name': 'DETECTION', 'value': 'تدريب الكشف'},
        {'name': 'AGILITY', 'value': 'تدريب الرشاقة'},
        {'name': 'ATTACK', 'value': 'تدريب الهجوم'},
        {'name': 'FITNESS', 'value': 'تدريب اللياقة'}
    ]
    
    return render_template('production/puppy_training_add.html', puppies=puppies, trainers=trainers, categories=categories)

# Project routes (without attendance/assignment functionality)
@main_bp.route('/projects')
@login_required
def projects():
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        # PROJECT_MANAGER users - get projects where they are assigned as project manager via Employee relationship
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        if employee:
            projects = Project.query.filter_by(project_manager_id=employee.id).order_by(Project.created_at.desc()).all()
        else:
            projects = []
    
    # Add assignment counts to each project
    for project in projects:
        # Count active dog assignments
        project.assigned_dogs_count = ProjectAssignment.query.filter_by(
            project_id=project.id, 
            is_active=True
        ).filter(ProjectAssignment.dog_id.isnot(None)).count()
        
        # Count active employee assignments  
        project.assigned_employees_count = ProjectAssignment.query.filter_by(
            project_id=project.id, 
            is_active=True
        ).filter(ProjectAssignment.employee_id.isnot(None)).count()
    
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
            print("=== تشخيص إضافة المشروع ===")
            print(f"Form data: {dict(request.form)}")
            
            # التحقق من وجود البيانات المطلوبة
            if not request.form.get('name'):
                flash('اسم المشروع مطلوب', 'error')
                raise Exception("Project name is required")
            
            if not request.form.get('start_date'):
                flash('تاريخ البداية مطلوب', 'error')
                raise Exception("Start date is required")
            
            # Determine the manager ID
            manager_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else request.form.get('manager_id')
            print(f"Manager ID: {manager_id}")
            
            # Generate unique project code
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            print(f"Generated code: {code}")
            
            project = Project()
            project.name = request.form['name']
            project.code = code
            project.description = request.form.get('description')
            project.main_task = request.form.get('main_task')
            project.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            project.expected_completion_date = datetime.strptime(request.form['expected_completion_date'], '%Y-%m-%d').date() if request.form.get('expected_completion_date') else None
            project.status = ProjectStatus.PLANNED
            project.location = request.form.get('location')
            project.mission_type = request.form.get('mission_type')
            project.priority = request.form.get('priority', 'MEDIUM')
            
            print(f"Project object created: {project.name}, {project.code}")
            
            # Validate project manager assignment if provided
            if manager_id:
                # Find the employee profile for project manager
                employee = Employee.query.get(manager_id)
                print(f"Employee found: {employee}")
                if employee and employee.role == EmployeeRole.PROJECT_MANAGER:
                    # Validate one-project-per-manager constraint
                    can_assign, error_msg = validate_project_manager_assignment(employee.id, project)
                    if not can_assign:
                        flash(error_msg, 'error')
                        raise Exception("Project manager assignment validation failed")
                    
                    project.project_manager_id = employee.id
                    print(f"Project manager assigned: {employee.name}")
                else:
                    flash('الموظف المحدد ليس مدير مشروع صالح', 'error')
                    raise Exception("Invalid project manager")
            
            print("Adding project to database...")
            db.session.add(project)
            db.session.commit()
            print("Project committed successfully!")
            
            log_audit(current_user.id, AuditAction.CREATE, 'Project', project.id, f'مشروع جديد: {project.name}', None, {'name': project.name})
            flash('تم إنشاء المشروع بنجاح', 'success')
            return redirect(url_for('main.projects'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating project: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ أثناء إنشاء المشروع: {str(e)}', 'error')
    
    # Get available data for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Get only project managers who are NOT assigned to any active/planned projects
        subquery = db.session.query(Project.project_manager_id).filter(
            Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])
        ).subquery()
        
        managers = Employee.query.filter(
            Employee.role == EmployeeRole.PROJECT_MANAGER,
            Employee.is_active == True,
            ~Employee.id.in_(db.session.query(subquery.c.project_manager_id))
        ).all()
    else:
        managers = []  # PROJECT_MANAGER users can only assign to themselves
    
    return render_template('projects/add.html', managers=managers)

# Project Dashboard Route (without attendance statistics)
@main_bp.route('/projects/<project_id>/dashboard')
@login_required
def project_dashboard(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    # Get dashboard statistics with new assignment system
    dog_assignments = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).count()
    active_dog_assignments = dog_assignments  # All are active since we filter by is_active=True
    
    employee_assignments = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).count()
    active_employee_assignments = employee_assignments  # All are active since we filter by is_active=True
    
    # Incident statistics
    total_incidents = Incident.query.filter_by(project_id=project.id).count()
    resolved_incidents = Incident.query.filter_by(project_id=project.id, resolved=True).count()
    pending_incidents = total_incidents - resolved_incidents
    
    # Suspicion statistics
    total_suspicions = Suspicion.query.filter_by(project_id=project.id).count()
    confirmed_suspicions = Suspicion.query.filter_by(project_id=project.id, evidence_collected=True).count()
    
    # Evaluation statistics
    total_evaluations = PerformanceEvaluation.query.filter_by(project_id=project.id).count()
    
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
    assigned_dogs = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).options(db.joinedload(ProjectAssignment.dog)).all()
    assigned_employees = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).options(db.joinedload(ProjectAssignment.employee)).all()
    
    # Get project managers for the quick update modal
    project_managers = Employee.query.filter_by(role=EmployeeRole.PROJECT_MANAGER, is_active=True).all()
    
    # Recent activities - include linked training and veterinary visits
    recent_incidents = Incident.query.filter_by(project_id=project.id).order_by(Incident.incident_date.desc()).limit(5).all()
    recent_suspicions = Suspicion.query.filter_by(project_id=project.id).order_by(Suspicion.discovery_date.desc()).limit(5).all()
    recent_evaluations = PerformanceEvaluation.query.filter_by(project_id=project.id).order_by(PerformanceEvaluation.evaluation_date.desc()).limit(5).all()
    recent_training = TrainingSession.query.filter_by(project_id=project.id).order_by(TrainingSession.session_date.desc()).limit(5).all()
    recent_veterinary = VeterinaryVisit.query.filter_by(project_id=project.id).order_by(VeterinaryVisit.visit_date.desc()).limit(5).all()
    
    # Get statistics for linked activities
    total_training = TrainingSession.query.filter_by(project_id=project.id).count()
    total_veterinary = VeterinaryVisit.query.filter_by(project_id=project.id).count()
    
    stats.update({
        'total_training': total_training,
        'total_veterinary': total_veterinary
    })
    
    return render_template('projects/modern_dashboard.html', 
                         project=project, 
                         stats=stats,
                         assigned_dogs=assigned_dogs,
                         assigned_employees=assigned_employees,
                         project_managers=project_managers,
                         recent_incidents=recent_incidents,
                         recent_suspicions=recent_suspicions,
                         recent_evaluations=recent_evaluations,
                         recent_training=recent_training,
                         recent_veterinary=recent_veterinary)

# Project Status Management
@main_bp.route('/projects/<project_id>/status', methods=['POST'])
@login_required
def project_status_change(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بتعديل حالة هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    new_status = request.form.get('status')
    if new_status:
        old_status = project.status.value
        new_project_status = ProjectStatus(new_status)
        
        # If changing to ACTIVE or PLANNED, validate project manager constraints
        if new_project_status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED] and project.project_manager_id:
            employee = Employee.query.get(project.project_manager_id)
            if employee and employee.role == EmployeeRole.PROJECT_MANAGER:
                # Temporarily set the new status for validation
                original_status = project.status
                project.status = new_project_status
                
                can_assign, error_msg = validate_project_manager_assignment(employee.id, project)
                
                # Restore original status
                project.status = original_status
                
                if not can_assign:
                    flash(f"لا يمكن تغيير حالة المشروع: {error_msg}", 'error')
                    return redirect(url_for('main.projects'))
        
        # Apply the status change
        project.status = new_project_status
        
        # Set finish date if completed
        if project.status == ProjectStatus.COMPLETED and not project.actual_end_date:
            project.actual_end_date = date.today()
        
        db.session.commit()
        
        log_audit(current_user.id, 'UPDATE', 'Project', str(project.id), 
                 {'status_changed': f'من {old_status} إلى {project.status.value}'})
        flash('تم تحديث حالة المشروع بنجاح', 'success')
    
    return redirect(url_for('main.projects'))

# Project Delete Route
@main_bp.route('/projects/<project_id>/delete', methods=['POST'])
@login_required
def project_delete(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions - Only GENERAL_ADMIN can delete projects
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('غير مسموح لك بحذف المشاريع', 'error')
        return redirect(url_for('main.projects'))
    
    # Check if project is in PLANNED status only
    if project.status != ProjectStatus.PLANNED:
        flash('يمكن حذف المشاريع المخططة فقط التي لم تبدأ بعد', 'error')
        return redirect(url_for('main.projects'))
    
    try:
        project_name = project.name
        
        # Check for any related data that would prevent deletion
        # Count related records
        dogs_count = ProjectDog.query.filter_by(project_id=project.id).count()
        assignments_count = ProjectAssignment.query.filter_by(project_id=project.id).count()
        shifts_count = ProjectShift.query.filter_by(project_id=project.id).count()
        incidents_count = Incident.query.filter_by(project_id=project.id).count()
        suspicions_count = Suspicion.query.filter_by(project_id=project.id).count()
        evaluations_count = PerformanceEvaluation.query.filter_by(project_id=project.id).count()
        attendance_count = ProjectAttendance.query.filter_by(project_id=project.id).count()
        
        total_related = dogs_count + assignments_count + shifts_count + incidents_count + suspicions_count + evaluations_count + attendance_count
        
        if total_related > 0:
            flash(f'لا يمكن حذف المشروع لأنه يحتوي على بيانات مرتبطة ({total_related} سجل). قم بإلغاء المشروع بدلاً من حذفه.', 'error')
            return redirect(url_for('main.projects'))
        
        # Safe to delete - no related data
        db.session.delete(project)
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.DELETE, 'Project', str(project.id), 
                 f'حذف المشروع المخطط: {project_name}', None, {'project_name': project_name})
        flash(f'تم حذف المشروع "{project_name}" بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المشروع: {str(e)}', 'error')
    
    return redirect(url_for('main.projects'))

# Project Dog Management
@main_bp.route('/projects/<project_id>/dogs/add', methods=['POST'])
@login_required
def project_dog_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بإضافة كلاب لهذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    dog_id = request.form.get('dog_id')
    if dog_id:
        # Check if already assigned
        existing = ProjectDog.query.filter_by(project_id=project.id, dog_id=dog_id).first()
        if existing:
            flash('هذا الكلب مُعيَّن بالفعل للمشروع', 'error')
        else:
            project_dog = ProjectDog()
            project_dog.project_id = project.id
            project_dog.dog_id = dog_id
            project_dog.is_active = True
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
        project_id = project_id
        project = Project.query.get_or_404(project_id)
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
                # Validate project manager assignment constraints
                can_assign, error_msg = validate_project_manager_assignment(manager.id, project)
                if not can_assign:
                    flash(error_msg, 'error')
                    return redirect(url_for('main.project_dashboard', project_id=project_id))
                
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
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    # Get current assignments
    dog_assignments = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.dog_id.isnot(None)).all()
    employee_assignments = ProjectAssignment.query.filter_by(project_id=project.id, is_active=True).filter(ProjectAssignment.employee_id.isnot(None)).all()
    
    # Get available dogs (not assigned to other active projects) and employees for assignment
    # Get dogs that are either not assigned or not assigned to active projects
    assigned_dog_ids = db.session.query(ProjectAssignment.dog_id).join(Project).filter(
        ProjectAssignment.is_active == True,
        ProjectAssignment.dog_id.isnot(None),
        Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED]),
        Project.id != project.id  # Exclude current project
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
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
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
                        project_id=project.id, 
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
                    
                    assignment = ProjectAssignment()
                    assignment.project_id = project.id
                    assignment.dog_id = dog_id
                    assignment.notes = notes
                    assignment.is_active = True
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
                        project_id=project.id, 
                        employee_id=employee_id,
                        is_active=True
                    ).first()
                    
                    if not existing:
                        assignment = ProjectAssignment()
                        assignment.project_id = project.id
                        assignment.employee_id = employee_id
                        assignment.notes = notes
                        assignment.is_active = True
                        db.session.add(assignment)
        
        # Handle project manager assignment separately 
        elif assignment_type == 'project_manager':
            project_manager_id = request.form.get('project_manager_id')
            if project_manager_id:
                # Verify it's actually a project manager
                manager = Employee.query.get(project_manager_id)
                if manager and manager.role == EmployeeRole.PROJECT_MANAGER:
                    # Validate project manager assignment constraints
                    can_assign, error_msg = validate_project_manager_assignment(manager.id, project)
                    if not can_assign:
                        flash(error_msg, 'error')
                        return redirect(url_for('main.project_assignments', project_id=project_id))
                    
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
        project_id = project_id
        assignment_id = assignment_id
        project = Project.query.get_or_404(project_id)
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
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
        project_id = project_id
        assignment_id = assignment_id
        project = Project.query.get_or_404(project_id)
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
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
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    incidents = Incident.query.filter_by(project_id=project.id).order_by(Incident.incident_date.desc()).all()
    
    return render_template('projects/incidents.html', project=project, incidents=incidents)

@main_bp.route('/projects/<project_id>/incidents/add', methods=['GET', 'POST'])
@login_required
def project_incident_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            incident = Incident(
                project_id=project.id,
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

@main_bp.route('/projects/<project_id>/incidents/resolve')
@login_required
def project_resolve_incident(project_id):
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    incident_id = request.args.get('incident_id')
    if not incident_id:
        flash('معرف الحادث مفقود', 'error')
        return redirect(url_for('main.project_incidents', project_id=project_id))
    
    try:
        incident = Incident.query.get_or_404(incident_id)
        if incident.project_id != project.id:
            flash('الحادث غير مرتبط بهذا المشروع', 'error')
            return redirect(url_for('main.project_incidents', project_id=project_id))
        
        incident.resolved = True
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by_id = current_user.id
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.UPDATE, 'Incident', incident.id, f'تم حل الحادث', None, {'resolved': True})
        flash('تم تمييز الحادث كمحلول بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الحادث: {str(e)}', 'error')
    
    return redirect(url_for('main.project_incidents', project_id=project_id))

# Enhanced Projects Section - Suspicions
@main_bp.route('/projects/<project_id>/suspicions')
@login_required
def project_suspicions(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    suspicions = Suspicion.query.filter_by(project_id=project.id).order_by(Suspicion.discovery_date.desc()).all()
    
    return render_template('projects/suspicions.html', project=project, suspicions=suspicions)

@main_bp.route('/projects/<project_id>/suspicions/add', methods=['GET', 'POST'])
@login_required
def project_suspicion_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            suspicion = Suspicion(
                project_id=project.id,
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
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    evaluations = PerformanceEvaluation.query.filter_by(project_id=project.id).order_by(PerformanceEvaluation.evaluation_date.desc()).all()
    
    return render_template('projects/evaluations.html', project=project, evaluations=evaluations)

@main_bp.route('/projects/<project_id>/evaluations/add', methods=['GET', 'POST'])
@login_required
def project_evaluation_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Check permissions
    # Check project access - for project managers, check if they have an employee profile linked to this project
    has_access = current_user.role == UserRole.GENERAL_ADMIN
    if not has_access and current_user.role == UserRole.PROJECT_MANAGER:
        employee = Employee.query.filter_by(user_account_id=current_user.id).first()
        has_access = employee and project.project_manager_id == employee.id
    
    if not has_access:
        flash('غير مسموح لك بالوصول إلى هذا المشروع', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            # Determine target based on form selection
            target_employee_id = request.form.get('target_employee_id') if request.form.get('target_type') == 'EMPLOYEE' else None
            target_dog_id = request.form.get('target_dog_id') if request.form.get('target_type') == 'DOG' else None
            
            evaluation = PerformanceEvaluation(
                project_id=project.id,
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
    """Redirect to Reports Hub"""
    return redirect(url_for('main.reports_hub'))

@main_bp.route('/reports/hub')
@login_required
def reports_hub():
    """Centralized Reports Hub with all reporting sections"""
    # Calculate real statistics
    stats = {
        'total_dogs': Dog.query.count(),
        'total_employees': Employee.query.filter_by(is_active=True).count(),
        'total_projects': Project.query.count(),
        'total_training_sessions': TrainingSession.query.count(),
        'total_vet_visits': VeterinaryVisit.query.count()
    }
    return render_template('reports/hub.html', stats=stats)

@main_bp.route('/reports/simple')
@login_required
def reports_simple():
    """Simple reports dashboard (original)"""
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

@main_bp.route('/reports/advanced')
@login_required
def reports_advanced():
    """Advanced reports interface with live preview and filtering"""
    employees = Employee.query.filter_by(is_active=True).all()
    # Get optional type parameter for pre-filtering
    report_type = request.args.get('type')
    return render_template('reports/advanced.html', employees=employees, pre_selected_type=report_type)

@main_bp.route('/reports/generate', methods=['POST'])
@login_required
def reports_generate():
    """
    Generate a report based on type, optional date range and optional filters.
    Supported report types: 'dogs', 'employees', 'training', 'veterinary',
                            'breeding', 'projects', 'attendance_daily', 'attendance_pm_daily',
                            'training_trainer_daily', plus production sub-types.
    Additional filters (passed via POST form) vary by type:
      - dogs: status, gender
      - employees: role, status
      - training: category
      - veterinary: visit_type
      - breeding: cycle_type
      - projects: project_status
    """
    report_type = request.form.get('report_type')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    # Parse ISO date strings into date objects (may be None)
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    # Extract filter values from the POST data into a dict
    filters = {}
    for field in ['status', 'gender', 'role', 'category', 'visit_type', 'cycle_type', 'project_status']:
        value = request.form.get(field)
        if value:
            filters[field] = value

    # Check export format
    export_format = request.form.get('export_format', 'pdf')
    
    try:
        if export_format == 'excel':
            from k9.utils.utils import generate_excel_report
            filename = generate_excel_report(report_type, start_date, end_date, current_user, filters)
        else:
            # Map new report types to existing system for PDF generation
            if report_type.startswith('production_'):
                pdf_report_type = 'breeding'  # Use breeding for all production reports
            elif report_type in ['attendance_daily', 'attendance_pm_daily', 'training_trainer_daily']:
                # For daily reports, redirect to training or veterinary as appropriate
                if 'training' in report_type:
                    pdf_report_type = 'training'
                elif 'veterinary' in report_type:
                    pdf_report_type = 'veterinary'
                else:
                    pdf_report_type = 'employees'  # Attendance reports use employee-like format
            else:
                pdf_report_type = report_type
            
            filename = generate_pdf_report(pdf_report_type, start_date, end_date, current_user, filters)
        
        upload_dir = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_dir, filename, as_attachment=True)
    except Exception as e:
        flash(f'تعذّر إنشاء التقرير: {str(e)}', 'error')
        return redirect(url_for('main.reports_advanced'))

@main_bp.route('/reports/preview', methods=['POST'])
@login_required
def reports_preview():
    """Get filtered data for live preview in advanced reports"""
    from k9.models.models import Dog, Employee, TrainingSession, VeterinaryVisit, ProductionCycle, Project
    
    report_type = request.form.get('report_type')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    
    # Build comprehensive filters dict from form data
    filters = {}
    
    # Basic filters
    basic_fields = ['status', 'gender', 'role', 'category', 'visit_type', 'cycle_type', 'project_status']
    for field in basic_fields:
        value = request.form.get(field)
        if value:
            filters[field] = value
    
    # Multi-select filters (handle arrays)
    multi_select_fields = ['gender[]', 'training_status[]', 'role[]', 'shift[]', 'employment_status[]', 
                          'project_status[]', 'priority_level[]', 'project_type[]', 'training_category[]',
                          'visit_type[]', 'cycle_type[]', 'cycle_outcome[]', 'manager[]']
    
    for field in multi_select_fields:
        values = request.form.getlist(field)
        if values:
            base_field = field.replace('[]', '')
            filters[base_field] = values
    
    # Range filters
    range_fields = {
        'age': ('age_min', 'age_max'),
        'hire_date': ('hire_date_min', 'hire_date_max'),
        'rating': ('rating_min', 'rating_max'),
        'duration': ('duration_min', 'duration_max'),
        'puppies': ('puppies_min', 'puppies_max')
    }
    
    for range_name, (min_field, max_field) in range_fields.items():
        min_val = request.form.get(min_field)
        max_val = request.form.get(max_field)
        if min_val or max_val:
            filters[range_name] = {'min': min_val, 'max': max_val}
    
    # Text and keyword filters
    text_fields = ['breed', 'location_cluster', 'diagnosis_keyword', 'treatment_type', 'custom_tags']
    for field in text_fields:
        value = request.form.get(field)
        if value:
            filters[field] = value.strip()
    
    # Special filters
    keyword = request.form.get('keyword', '').strip()
    if keyword:
        filters['keyword'] = keyword
        
    has_attachments = request.form.get('has_attachments')
    if has_attachments:
        filters['has_attachments'] = has_attachments == 'true'
        
    activity_filter = request.form.get('activity_filter')
    if activity_filter:
        filters['activity_filter'] = activity_filter
        
    filter_logic = request.form.get('filter_logic', 'AND')
    filters['logic'] = filter_logic
    
    # Get data based on report type
    records = []
    if report_type == 'dogs':
        dogs = Dog.query.all() if current_user.role.value == 'GENERAL_ADMIN' \
            else Dog.query.filter_by(assigned_to_user_id=current_user.id).all()
        
        # Apply advanced filters
        filtered_dogs = []
        for dog in dogs:
            include = True
            
            # Gender filter (multi-select)
            if filters.get('gender') and isinstance(filters['gender'], list):
                if dog.gender.value not in filters['gender']:
                    include = False
            elif filters.get('gender') and dog.gender.value != filters['gender']:
                include = False
            
            # Training status filter (multi-select) 
            if filters.get('training_status') and isinstance(filters['training_status'], list):
                if dog.current_status.value not in filters['training_status']:
                    include = False
            elif filters.get('status') and dog.current_status.value != filters['status']:
                include = False
                
            # Breed filter (text search)
            if filters.get('breed') and filters['breed'].lower() not in (dog.breed or '').lower():
                include = False
                
            # Age range filter 
            if filters.get('age'):
                age_min = filters['age'].get('min')
                age_max = filters['age'].get('max')
                dog_age = (datetime.now().date() - dog.birth_date).days / 365 if dog.birth_date else 0
                if age_min and dog_age < float(age_min):
                    include = False
                if age_max and dog_age > float(age_max):
                    include = False
            
            # Keyword search in all text fields
            if filters.get('keyword'):
                keyword = filters['keyword'].lower()
                searchable_text = ' '.join([
                    dog.name or '', dog.code or '', dog.breed or '', 
                    dog.location or '', dog.microchip_id or '', dog.notes or ''
                ]).lower()
                if keyword not in searchable_text:
                    include = False
            
            # Activity filters
            if filters.get('activity_filter') == 'no_activity_30':
                # Check if dog has no training sessions in last 30 days
                from k9.models.models import TrainingSession
                thirty_days_ago = datetime.now().date() - timedelta(days=30)
                recent_sessions = TrainingSession.query.filter(
                    TrainingSession.dog_id == dog.id,
                    TrainingSession.session_date >= thirty_days_ago
                ).count()
                if recent_sessions > 0:
                    include = False
            
            if include:
                filtered_dogs.append(dog)
            
        for dog in filtered_dogs:
            records.append({
                'اسم الكلب': dog.name or '',
                'الكود': dog.code or '',
                'السلالة': dog.breed or '',
                'الجنس': 'ذكر' if dog.gender.value == 'MALE' else 'أنثى',
                'الحالة': {'ACTIVE': 'نشط', 'RETIRED': 'متقاعد', 'DECEASED': 'متوفى', 'TRAINING': 'تدريب'}.get(dog.current_status.value, ''),
                'الموقع': dog.location or '',
                'العمر': str(int((datetime.now().date() - dog.birth_date).days / 365)) + ' سنة' if dog.birth_date else 'غير محدد'
            })
    
    elif report_type == 'employees':
        employees = Employee.query.all()
        
        # Apply advanced filters
        filtered_employees = []
        for emp in employees:
            include = True
            
            # Role filter (multi-select)
            if filters.get('role') and isinstance(filters['role'], list):
                if emp.role.value not in filters['role']:
                    include = False
            elif filters.get('role') and emp.role.value != filters['role']:
                include = False
            
            # Employment status filter
            if filters.get('employment_status') and isinstance(filters['employment_status'], list):
                emp_status = 'ACTIVE' if emp.is_active else 'INACTIVE'
                if emp_status not in filters['employment_status']:
                    include = False
            elif filters.get('status'):
                is_active = (filters['status'] == 'ACTIVE')
                if emp.is_active != is_active:
                    include = False
            
            # Hire date range filter
            if filters.get('hire_date') and emp.hire_date:
                hire_min = filters['hire_date'].get('min')
                hire_max = filters['hire_date'].get('max')
                if hire_min and emp.hire_date < datetime.strptime(hire_min, '%Y-%m-%d').date():
                    include = False
                if hire_max and emp.hire_date > datetime.strptime(hire_max, '%Y-%m-%d').date():
                    include = False
            
            # Shift filter (multi-select)
            if filters.get('shift') and isinstance(filters['shift'], list):
                emp_shift = 'MORNING'  # Default shift for existing employees
                if emp_shift not in filters['shift']:
                    include = False
            
            # Keyword search
            if filters.get('keyword'):
                keyword = filters['keyword'].lower()
                searchable_text = ' '.join([
                    emp.name or '', emp.employee_id or '', emp.phone or '', 
                    emp.email or '', emp.address or ''
                ]).lower()
                if keyword not in searchable_text:
                    include = False
            
            if include:
                filtered_employees.append(emp)
            
        for emp in filtered_employees:
            records.append({
                'الاسم': emp.name,
                'الرقم الوظيفي': emp.employee_id or '',
                'الوظيفة': {'HANDLER': 'معالج', 'TRAINER': 'مدرب', 'VET': 'طبيب بيطري', 'PROJECT_MANAGER': 'مدير مشروع', 'BREEDER': 'مربي'}.get(emp.role.value, emp.role.value),
                'تاريخ التعيين': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                'الحالة': 'نشط' if emp.is_active else 'غير نشط',
                'الهاتف': emp.phone or '',
                'البريد': emp.email or ''
            })
    
    elif report_type == 'training':
        sessions = TrainingSession.query
        if start_date and end_date:
            sessions = sessions.filter(TrainingSession.session_date >= start_date,
                                     TrainingSession.session_date <= end_date)
        if current_user.role.value != 'GENERAL_ADMIN':
            assigned_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
            sessions = sessions.filter(TrainingSession.dog_id.in_(assigned_ids))
        if filters.get('category'):
            if isinstance(filters['category'], list):
                sessions = sessions.filter(TrainingSession.category.in_(filters['category']))
            else:
                sessions = sessions.filter(TrainingSession.category == filters['category'])
        sessions = sessions.all()
        
        category_map = {'OBEDIENCE': 'طاعة', 'DETECTION': 'كشف', 'AGILITY': 'رشاقة', 'ATTACK': 'هجوم', 'FITNESS': 'لياقة'}
        for s in sessions:
            records.append({
                'اسم الكلب': s.dog.name,
                'المدرب': s.trainer.name,
                'الفئة': category_map.get(s.category.value, s.category.value),
                'الموضوع': s.subject or '',
                'التاريخ': s.session_date.strftime('%Y-%m-%d'),
                'المدة (دقيقة)': str(s.duration),
                'التقييم': f"{s.success_rating}/10"
            })
    
    elif report_type == 'veterinary':
        visits = VeterinaryVisit.query
        if start_date and end_date:
            visits = visits.filter(VeterinaryVisit.visit_date >= start_date,
                                 VeterinaryVisit.visit_date <= end_date)
        if current_user.role.value != 'GENERAL_ADMIN':
            assigned_ids = [d.id for d in Dog.query.filter_by(assigned_to_user_id=current_user.id).all()]
            visits = visits.filter(VeterinaryVisit.dog_id.in_(assigned_ids))
        if filters.get('visit_type'):
            if isinstance(filters['visit_type'], list):
                visits = visits.filter(VeterinaryVisit.visit_type.in_(filters['visit_type']))
            else:
                visits = visits.filter(VeterinaryVisit.visit_type == filters['visit_type'])
        visits = visits.all()
        
        visit_type_map = {'ROUTINE': 'روتينية', 'EMERGENCY': 'طارئة', 'VACCINATION': 'تطعيم'}
        for v in visits:
            records.append({
                'الكلب': v.dog.name,
                'الطبيب': v.vet.name,
                'نوع الزيارة': visit_type_map.get(v.visit_type.value, v.visit_type.value),
                'التاريخ': v.visit_date.strftime('%Y-%m-%d'),
                'التشخيص': v.diagnosis or '',
                'العلاج': v.treatment or ''
            })
    
    elif report_type == 'breeding' or report_type.startswith('production_'):
        # Handle production/breeding reports
        cycles = ProductionCycle.query
        if start_date and end_date:
            cycles = cycles.filter(ProductionCycle.mating_date >= start_date,
                                 ProductionCycle.mating_date <= end_date)
        if filters.get('cycle_type'):
            if isinstance(filters['cycle_type'], list):
                cycles = cycles.filter(ProductionCycle.cycle_type.in_(filters['cycle_type']))
            else:
                cycles = cycles.filter(ProductionCycle.cycle_type == filters['cycle_type'])
        cycles = cycles.all()
        
        cycle_map = {'NATURAL': 'طبيعي', 'ARTIFICIAL': 'صناعي'}
        result_map = {'SUCCESSFUL': 'ناجحة', 'FAILED': 'فاشلة', 'UNKNOWN': 'غير معروف'}
        for c in cycles:
            records.append({
                'الأم': c.female.name if c.female else '',
                'الأب': c.male.name if c.male else '',
                'نوع الدورة': cycle_map.get(c.cycle_type.value, c.cycle_type.value),
                'تاريخ التزاوج': c.mating_date.strftime('%Y-%m-%d') if c.mating_date else '',
                'تاريخ الولادة المتوقع': c.expected_delivery_date.strftime('%Y-%m-%d') if c.expected_delivery_date else '',
                'تاريخ الولادة': c.actual_delivery_date.strftime('%Y-%m-%d') if c.actual_delivery_date else '',
                'النتيجة': result_map.get(c.result.value, '') if c.result else '',
                'عدد الجراء': c.number_of_puppies or '',
                'الناجون': c.puppies_survived or ''
            })
    
    # New report types for attendance and daily reports
    elif report_type == 'attendance_daily':
        # Get attendance daily sheet data
        try:
            from k9.services.attendance_reporting_services import get_daily_sheet_summary
            summary_data = get_daily_sheet_summary(start_date, end_date, current_user)
            for item in summary_data:
                records.append({
                    'المشروع': item.get('project_name', ''),
                    'التاريخ': item.get('date', ''),
                    'الحضور': item.get('attendance_count', 0),
                    'الغياب': item.get('absence_count', 0),
                    'المجموع': item.get('total_employees', 0)
                })
        except Exception:
            records = []
    
    elif report_type == 'attendance_pm_daily':
        # Get PM daily data
        try:
            from k9.services.pm_daily_services import get_pm_daily_summary
            summary_data = get_pm_daily_summary(start_date, end_date, current_user)
            for item in summary_data:
                records.append({
                    'المشروع': item.get('project_name', ''),
                    'التاريخ': item.get('date', ''),
                    'المسؤول': item.get('responsible_name', ''),
                    'الحالة': item.get('status', ''),
                    'الملاحظات': item.get('notes', '')
                })
        except Exception:
            records = []
    
    elif report_type == 'training_trainer_daily':
        # Get trainer daily data
        try:
            from k9.services.trainer_daily_services import get_trainer_daily_summary
            summary_data = get_trainer_daily_summary(start_date, end_date, current_user)
            for item in summary_data:
                records.append({
                    'المدرب': item.get('trainer_name', ''),
                    'التاريخ': item.get('date', ''),
                    'الكلب': item.get('dog_name', ''),
                    'التمرين': item.get('exercise_type', ''),
                    'التقييم': item.get('rating', ''),
                    'الملاحظات': item.get('notes', '')
                })
        except Exception:
            records = []
    
    elif report_type == 'projects':
        projects = Project.query
        if start_date and end_date:
            projects = projects.filter(Project.start_date >= start_date,
                                     Project.start_date <= end_date)
        if filters.get('project_status'):
            if isinstance(filters['project_status'], list):
                projects = projects.filter(Project.status.in_(filters['project_status']))
            else:
                projects = projects.filter(Project.status == filters['project_status'])
        projects = projects.all()
        
        status_map = {'ACTIVE': 'نشط', 'COMPLETED': 'منجز', 'CANCELLED': 'ملغى', 'PLANNED': 'مخطط'}
        for p in projects:
            records.append({
                'اسم المشروع': p.name,
                'الكود': p.code or '',
                'الحالة': status_map.get(p.status.value, p.status.value),
                'تاريخ البداية': p.start_date.strftime('%Y-%m-%d') if p.start_date else '',
                'تاريخ النهاية': p.end_date.strftime('%Y-%m-%d') if p.end_date else '',
                'المدير': p.manager.full_name if p.manager else '',
                'الموقع': p.location or ''
            })
    
    try:
        return jsonify({
            'records': records,
            'total': len(records),
            'filtered': len(records),
            'report_type': report_type
        })
    except Exception as e:
        current_app.logger.error(f"Error in reports_preview: {str(e)}")
        return jsonify({
            'error': f'حدث خطأ في معالجة التقرير: {str(e)}',
            'records': [],
            'total': 0,
            'filtered': 0,
            'report_type': report_type
        }), 500

@main_bp.route('/reports/preview-pdf', methods=['POST'])
@login_required
def reports_preview_pdf():
    """Generate HTML preview that mimics PDF layout"""
    report_type = request.form.get('report_type')
    
    # Get the same data as preview
    preview_response = reports_preview()
    if hasattr(preview_response, 'get_json'):
        data = preview_response.get_json()
    else:
        # Handle error case
        return f"<div class='alert alert-danger'>حدث خطأ في تحميل البيانات</div>"
    
    # Generate HTML that looks like the PDF
    report_titles = {
        'dogs': 'تقرير الكلاب', 
        'employees': 'تقرير الموظفين', 
        'training': 'تقرير التدريب', 
        'veterinary': 'تقرير الطبابة', 
        'breeding': 'تقرير التكاثر', 
        'projects': 'تقرير المشاريع',
        'attendance_daily': 'تقرير الحضور اليومي',
        'attendance_pm_daily': 'تقرير المسؤول اليومي',
        'training_trainer_daily': 'تقرير المدرب اليومي',
        'production_maturity': 'تقرير البلوغ',
        'production_heat_cycles': 'تقرير الدورة',
        'production_mating': 'تقرير التزاوج',
        'production_pregnancy': 'تقرير الحمل',
        'production_delivery': 'تقرير الولادة',
        'production_puppies': 'تقرير الجراء',
        'production_puppy_training': 'تقرير تدريب الجراء'
    }
    report_title = report_titles.get(report_type, 'تقرير')
    
    # Render the header template
    header_html = render_template('reports/_header.html')
    
    html_content = f"""
    <div class="report-preview" style="font-family: 'Cairo', 'Amiri', sans-serif; direction: rtl;">
        {header_html}
        
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="color: #C00000; font-family: 'Cairo', 'Amiri', sans-serif;">
                {report_title}
            </h3>
            <p style="font-size: 12px; color: #666;">
                تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-family: 'Cairo', 'Amiri', sans-serif; font-size: 10px;">
    """
    
    if data['records']:
        # Table headers
        headers = list(data['records'][0].keys())
        html_content += "<thead><tr style='background-color: #603913; color: white;'>"
        html_content += "<th style='border: 1px solid #603913; padding: 8px; text-align: center;'>م</th>"
        for header in headers:
            html_content += f"<th style='border: 1px solid #603913; padding: 8px; text-align: center;'>{header}</th>"
        html_content += "</tr></thead><tbody>"
        
        # Table rows
        for idx, record in enumerate(data['records'][:20], 1):  # Show first 20 records in preview
            bg_color = '#f8f9fa' if idx % 2 == 0 else 'white'
            html_content += f"<tr style='background-color: {bg_color};'>"
            html_content += f"<td style='border: 1px solid #ddd; padding: 6px; text-align: center;'>{idx}</td>"
            for header in headers:
                html_content += f"<td style='border: 1px solid #ddd; padding: 6px; text-align: center;'>{record.get(header, '')}</td>"
            html_content += "</tr>"
        
        if len(data['records']) > 20:
            html_content += f"<tr><td colspan='{len(headers)+1}' style='text-align: center; padding: 10px; font-style: italic;'>... و {len(data['records'])-20} سجل آخر</td></tr>"
        
        html_content += "</tbody>"
    else:
        html_content += "<tr><td style='text-align: center; padding: 20px;'>لا توجد بيانات</td></tr>"
    
    html_content += """
            </table>
        </div>
        
        <div style="margin-top: 40px; font-size: 12px;">
            <p><strong>ملاحظات:</strong></p>
            <div style="margin-top: 60px;">
                <p>اسم المسؤول: ..............................     التوقيع: ..............................</p>
                <p>اسم المدير: ..............................     التوقيع: ..............................</p>
            </div>
        </div>
    </div>
    """
    
    return html_content


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
            action = request.form.get('action')
            shift_id = request.form.get('shift_id')
            
            if action == 'toggle_status' and shift_id:  # Toggle shift status
                shift = ProjectShift.query.get_or_404(shift_id)
                is_active = request.form.get('is_active') == 'true'
                shift.is_active = is_active
                
                status_text = 'تفعيل' if is_active else 'إيقاف'
                log_audit(current_user.id, AuditAction.EDIT, 'ProjectShift', shift.id, 
                         description=f'{status_text} shift {shift.name} for project {project.name}')
                
                flash(f'تم {status_text} الوردية بنجاح', 'success')
                
            elif shift_id and not action:  # Editing existing shift
                shift = ProjectShift.query.get_or_404(shift_id)
                shift.name = request.form['name']
                shift.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
                shift.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
                
                log_audit(current_user.id, AuditAction.EDIT, 'ProjectShift', shift.id, 
                         description=f'Updated shift {shift.name} for project {project.name}')
                
                flash('تم تحديث الوردية بنجاح', 'success')
            else:  # Creating new shift
                shift = ProjectShift(
                    project_id=project_id,
                    name=request.form['name'],
                    start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
                    end_time=datetime.strptime(request.form['end_time'], '%H:%M').time()
                )
                db.session.add(shift)
                
                log_audit(current_user.id, AuditAction.CREATE, 'ProjectShift', shift.id, 
                         description=f'Created shift {shift.name} for project {project.name}')
                
                flash('تم إنشاء الوردية بنجاح', 'success')
                
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في معالجة الوردية: {str(e)}', 'error')
    
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
        # Ensure request contains JSON data
        if not request.json:
            return jsonify({'success': False, 'error': 'البيانات المرسلة غير صحيحة'}), 400
            
        # Extract data with error handling
        shift_id = request.json.get('shift_id')
        date_str = request.json.get('date')
        entity_type = request.json.get('entity_type')
        entity_id = request.json.get('entity_id')
        status = request.json.get('status')
        absence_reason = request.json.get('absence_reason')
        late_reason = request.json.get('late_reason')
        notes = request.json.get('notes', '')
        
        # Validate required fields
        if not all([shift_id, date_str, entity_type, entity_id, status]):
            return jsonify({'success': False, 'error': 'البيانات المطلوبة مفقودة'}), 400
            
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Validate that entity is assigned to this shift
        assignment = ProjectShiftAssignment.query.filter_by(
            shift_id=shift_id,
            entity_type=EntityType(entity_type),
            entity_id=entity_id,
            is_active=True
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'هذا العضو غير مُعيَّن لهذه الوردية'}), 400
        
        # Validate absence reason for absent status - set default if not provided  
        if status == 'ABSENT' and (not absence_reason or absence_reason.strip() == ''):
            absence_reason = AbsenceReason.NO_REASON.name  # Default to no reason if not specified
        
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
            existing_record.absence_reason = AbsenceReason[absence_reason] if absence_reason and absence_reason.strip() else None
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
                absence_reason=AbsenceReason[absence_reason] if absence_reason and absence_reason.strip() else None,
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
        # Log the error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Attendance recording error: {error_details}")
        return jsonify({'success': False, 'error': f'خطأ في تسجيل الحضور: {str(e)}'}), 500

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
                absence_reason = AbsenceReason(request.json.get('absence_reason', 'NO_REASON'))
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

# Admin Management Routes (GENERAL_ADMIN only)
@main_bp.route('/admin')
@login_required
def admin_panel():
    """Redirect to the new admin dashboard"""
    # Redirect to the new admin dashboard with trailing slash
    return redirect(url_for('admin.dashboard'))

# Enhanced Permission API Endpoints
@main_bp.route('/api/admin/permissions/<user_id>')
@login_required
def get_user_permissions_api(user_id):
    """API endpoint to get user permissions for AJAX requests"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        project_id = request.args.get('project_id')
        project_id = project_id if project_id and project_id.strip() else None
        
        from k9.utils.permission_utils import get_user_permissions_for_project
        permissions = get_user_permissions_for_project(user_id, project_id)
        
        return jsonify({
            'success': True,
            'permissions': permissions,
            'user_id': user_id,
            'project_id': project_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/admin/permissions/update', methods=['POST'])
@login_required  
def update_user_permissions_api():
    """API endpoint to update user permissions via AJAX"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        project_id = data.get('project_id')
        permissions = data.get('permissions', {})
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Get target user
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        from k9.utils.permission_utils import update_permission
        from k9.models.models import PermissionType
        
        update_count = 0
        
        # Update each permission
        for section, subsections in permissions.items():
            for subsection, perm_types in subsections.items():
                for perm_type_str, is_granted in perm_types.items():
                    try:
                        perm_type = PermissionType(perm_type_str)
                        success = update_permission(
                            current_user, target_user, section, subsection, 
                            perm_type, project_id, is_granted
                        )
                        if success:
                            update_count += 1
                    except ValueError:
                        # Invalid permission type, skip
                        continue
        
        return jsonify({
            'success': True,
            'message': f'Updated {update_count} permissions',
            'updated_count': update_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/admin/sync_managers', methods=['POST'])
@login_required
def sync_project_managers():
    """Automatically create user accounts for all PROJECT_MANAGER employees"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لهذا الإجراء', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        from k9.utils.utils import ensure_employee_user_linkage
        
        created_users = ensure_employee_user_linkage()
        
        if created_users:
            count = len(created_users)
            flash(f'تم إنشاء {count} حساب مستخدم لمديري المشاريع', 'success')
            
            # Log each creation
            for user_info in created_users:
                log_audit(current_user.id, AuditAction.CREATE, 'User', user_info['user'].id,
                         description=f'Auto-created user account for employee {user_info["employee"].employee_id}')
        else:
            flash('جميع موظفي إدارة المشاريع لديهم حسابات مستخدمين بالفعل', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في مزامنة المديرين: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/update_user', methods=['POST'])
@login_required
def update_user_credentials():
    """Update user credentials (username, email, password)"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لتعديل بيانات المستخدمين', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        from werkzeug.security import generate_password_hash
        
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        
        if not all([user_id, username, email, full_name]):
            flash('جميع الحقول مطلوبة', 'error')
            return redirect(url_for('main.admin_panel'))
        
        user = User.query.get_or_404(user_id)
        
        # Check if username or email already exists for other users
        existing_username = User.query.filter_by(username=username).filter(User.id != user_id).first()
        if existing_username:
            flash('اسم المستخدم موجود مسبقاً', 'error')
            return redirect(url_for('main.admin_panel'))
        
        existing_email = User.query.filter_by(email=email).filter(User.id != user_id).first()
        if existing_email:
            flash('البريد الإلكتروني موجود مسبقاً', 'error')
            return redirect(url_for('main.admin_panel'))
        
        # Update user data
        old_values = {
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        }
        
        user.username = username
        user.email = email
        user.full_name = full_name
        
        # Update password if provided
        if password:
            user.password_hash = generate_password_hash(password)
            old_values['password_changed'] = True
        
        # Update corresponding employee record
        if user.employee_profile:
            user.employee_profile.name = full_name
            user.employee_profile.email = email
        
        db.session.commit()
        
        # Log the update
        log_audit(current_user.id, AuditAction.EDIT, 'User', user_id,
                 description=f'Updated user credentials for {username}',
                 old_values=old_values)
        
        flash(f'تم تحديث بيانات المستخدم {full_name} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث بيانات المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/permissions/update', methods=['POST'])
@login_required
def update_permissions():
    """Update PROJECT_MANAGER permissions"""
    from k9.models.models import ProjectManagerPermission
    
    # Check admin access
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لتعديل الصلاحيات', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user_id = request.form.get('user_id')
        project_id = request.form.get('project_id')
        
        if not user_id or not project_id:
            flash('يجب تحديد المستخدم والمشروع', 'error')
            return redirect(url_for('main.admin_panel'))
        
        # Get or create permission record
        permission = ProjectManagerPermission.query.filter_by(
            user_id=user_id,
            project_id=project_id
        ).first()
        
        if not permission:
            permission = ProjectManagerPermission()
            permission.user_id = user_id
            permission.project_id = project_id
            db.session.add(permission)
        
        # Update permissions based on form data
        permission.can_manage_assignments = 'can_manage_assignments' in request.form
        permission.can_manage_shifts = 'can_manage_shifts' in request.form
        permission.can_manage_attendance = 'can_manage_attendance' in request.form
        permission.can_manage_training = 'can_manage_training' in request.form
        permission.can_manage_incidents = 'can_manage_incidents' in request.form
        permission.can_manage_performance = 'can_manage_performance' in request.form
        permission.can_view_veterinary = 'can_view_veterinary' in request.form
        permission.can_view_breeding = 'can_view_breeding' in request.form
        
        db.session.commit()
        
        # Log the permission change
        user = User.query.get(user_id)
        project = Project.query.get(project_id)
        log_audit(current_user.id, AuditAction.EDIT, 'ProjectManagerPermission', 
                 f"{user_id}_{project_id}",
                 description=f'Updated permissions for {user.username} on project {project.name}')
        
        flash('تم تحديث الصلاحيات بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تحديث الصلاحيات: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لتعديل حالة المستخدمين', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        user = User.query.get_or_404(user_id)
        user.active = not user.active
        db.session.commit()
        
        status = 'تم تفعيل' if user.active else 'تم إلغاء تفعيل'
        log_audit(current_user.id, AuditAction.EDIT, 'User', user_id,
                 description=f'{status} المستخدم {user.username}')
        
        flash(f'{status} المستخدم {user.full_name} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في تعديل حالة المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_panel'))

# EMPLOYEE-USER ACCOUNT LINKING SYSTEM
@main_bp.route('/admin/employee-user-links')
@login_required
def employee_user_links():
    """Manage links between employees and user accounts"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية للوصول إلى إدارة الربط', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all employees with their linked user accounts
    employees = Employee.query.order_by(Employee.name).all()
    
    # Get all handler users (for linking)
    handler_users = User.query.filter_by(role=UserRole.HANDLER).order_by(User.full_name).all()
    
    # Get unlinked employees
    unlinked_employees = Employee.query.filter(Employee.user_account_id.is_(None)).all()
    
    # Get unlinked users
    unlinked_users = User.query.filter(
        User.role == UserRole.HANDLER,
        ~User.id.in_(db.session.query(Employee.user_account_id).filter(Employee.user_account_id.isnot(None)))
    ).all()
    
    return render_template('admin/employee_user_links.html',
                         employees=employees,
                         handler_users=handler_users,
                         unlinked_employees=unlinked_employees,
                         unlinked_users=unlinked_users)

@main_bp.route('/admin/employee-user-links/link', methods=['POST'])
@login_required
def link_employee_to_user():
    """Link an employee to a user account"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية لربط الحسابات'}), 403
    
    try:
        employee_id = request.form.get('employee_id')
        user_id = request.form.get('user_id')
        
        if not employee_id or not user_id:
            return jsonify({'success': False, 'error': 'يجب تحديد الموظف والمستخدم'})
        
        employee = Employee.query.get(employee_id)
        user = User.query.get(user_id)
        
        if not employee or not user:
            return jsonify({'success': False, 'error': 'الموظف أو المستخدم غير موجود'})
        
        # Check if user is already linked to another employee
        existing_link = Employee.query.filter_by(user_account_id=user_id).first()
        if existing_link and str(existing_link.id) != str(employee_id):
            return jsonify({'success': False, 'error': f'المستخدم مرتبط بالفعل بالموظف: {existing_link.name}'})
        
        # Create the link
        employee.user_account_id = user_id
        
        # Sync basic information
        employee.email = user.email
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.EDIT, 'Employee', employee_id,
                 description=f'Linked employee {employee.name} to user {user.username}')
        
        return jsonify({
            'success': True, 
            'message': f'تم ربط الموظف {employee.name} بالحساب {user.username} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'خطأ في الربط: {str(e)}'})

@main_bp.route('/admin/employee-user-links/unlink', methods=['POST'])
@login_required
def unlink_employee_from_user():
    """Unlink an employee from a user account"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية لفك الربط'}), 403
    
    try:
        employee_id = request.form.get('employee_id')
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'يجب تحديد الموظف'})
        
        employee = Employee.query.get(employee_id)
        
        if not employee:
            return jsonify({'success': False, 'error': 'الموظف غير موجود'})
        
        if not employee.user_account_id:
            return jsonify({'success': False, 'error': 'الموظف غير مرتبط بأي حساب'})
        
        old_user = User.query.get(employee.user_account_id)
        old_username = old_user.username if old_user else 'Unknown'
        
        # Remove the link
        employee.user_account_id = None
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.EDIT, 'Employee', employee_id,
                 description=f'Unlinked employee {employee.name} from user {old_username}')
        
        return jsonify({
            'success': True, 
            'message': f'تم فك ربط الموظف {employee.name} بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'خطأ في فك الربط: {str(e)}'})

# UNIFIED GLOBAL ATTENDANCE SYSTEM
# Only accessible to GENERAL_ADMIN users

@main_bp.route('/attendance')
@login_required
def unified_attendance():
    """Main attendance dashboard - standalone attendance system"""
    # Only GENERAL_ADMIN can access unified attendance
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية للوصول إلى نظام الحضور الموحد', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get current date and basic statistics
    today = date.today()
    
    # Get all active shifts
    shifts = Shift.query.filter_by(is_active=True).all()
    
    # Statistics for today
    stats = {}
    if shifts:
        total_assignments = 0
        present_count = 0
        absent_count = 0
        late_count = 0
        
        for shift in shifts:
            shift_assignments = ShiftAssignment.query.filter_by(shift_id=shift.id, is_active=True).count()
            total_assignments += shift_assignments
            
            shift_present = Attendance.query.filter_by(
                shift_id=shift.id,
                date=today,
                status=AttendanceStatus.PRESENT
            ).count()
            
            shift_absent = Attendance.query.filter_by(
                shift_id=shift.id,
                date=today,
                status=AttendanceStatus.ABSENT
            ).count()
            
            shift_late = Attendance.query.filter_by(
                shift_id=shift.id,
                date=today,
                status=AttendanceStatus.LATE
            ).count()
            
            present_count += shift_present
            absent_count += shift_absent
            late_count += shift_late
        
        stats = {
            'total_assignments': total_assignments,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'recorded': present_count + absent_count + late_count
        }
    else:
        stats = {
            'total_assignments': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'recorded': 0
        }
    
    return render_template('attendance/dashboard.html', 
                         today=today,
                         shifts=shifts,
                         stats=stats,
                         AttendanceStatus=AttendanceStatus)

@main_bp.route('/attendance/shifts')
@login_required
def attendance_shifts():
    """Manage standalone shifts"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية للوصول إلى إدارة الورديات', 'error')
        return redirect(url_for('main.dashboard'))
    
    shifts = Shift.query.order_by(Shift.start_time).all()
    response = make_response(render_template('attendance/shifts.html', shifts=shifts))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@main_bp.route('/attendance/shifts/add', methods=['GET', 'POST'])
@login_required
def attendance_shifts_add():
    """Add new shift"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لإضافة ورديات', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            shift = Shift(
                name=request.form['name'],
                start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
                is_active=True
            )
            
            db.session.add(shift)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Shift', shift.id,
                     description=f'Created shift {shift.name}')
            
            flash('تم إنشاء الوردية بنجاح', 'success')
            return redirect(url_for('main.attendance_shifts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء الوردية: {str(e)}', 'error')
    
    return render_template('attendance/shift_add.html')

@main_bp.route('/attendance/shifts/<shift_id>/edit', methods=['GET', 'POST'])
@login_required
def attendance_shifts_edit(shift_id):
    """Edit shift"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لتعديل الورديات', 'error')
        return redirect(url_for('main.dashboard'))
    
    shift = Shift.query.get_or_404(shift_id)
    
    if request.method == 'POST':
        try:
            shift.name = request.form['name']
            shift.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            shift.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            shift.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.EDIT, 'Shift', shift.id,
                     description=f'Updated shift {shift.name}')
            
            flash('تم تحديث الوردية بنجاح', 'success')
            return redirect(url_for('main.attendance_shifts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تحديث الوردية: {str(e)}', 'error')
    
    return render_template('attendance/shift_edit.html', shift=shift)

@main_bp.route('/attendance/assignments')
@login_required
def attendance_assignments():
    """Manage shift assignments"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية للوصول إلى تعيينات الورديات', 'error')
        return redirect(url_for('main.dashboard'))
    
    assignments = ShiftAssignment.query.filter_by(is_active=True).all()
    shifts = Shift.query.filter_by(is_active=True).all()
    
    # Get all active employees for assignment
    available_employees = Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
    
    # Create dictionary for efficient lookups in template
    employees_dict = {str(emp.id): emp for emp in available_employees}
    
    return render_template('attendance/assignments.html', 
                         assignments=assignments,
                         shifts=shifts,
                         available_employees=available_employees,
                         employees_dict=employees_dict,
                         EntityType=EntityType)

@main_bp.route('/attendance/assignments/add', methods=['POST'])
@login_required
def attendance_assignments_add():
    """Add shift assignment"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية لإضافة تعيينات'}), 403
    
    try:
        shift_id = request.form['shift_id']
        entity_type = request.form['entity_type']
        entity_id = request.form['entity_id']
        notes = request.form.get('notes', '')
        
        # Check if assignment already exists
        existing = ShiftAssignment.query.filter_by(
            shift_id=shift_id,
            entity_type=EntityType(entity_type),
            entity_id=entity_id,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'هذا العضو مُعيَّن بالفعل لهذه الوردية'})
        
        # Only allow EMPLOYEE entity type
        if entity_type != 'EMPLOYEE':
            return jsonify({'success': False, 'error': 'يُسمح فقط بتعيين الموظفين في هذا النظام'})
        
        # Create new assignment
        assignment = ShiftAssignment(
            shift_id=shift_id,
            entity_type=EntityType(entity_type),
            entity_id=entity_id,
            notes=notes,
            is_active=True
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.CREATE, 'ShiftAssignment', assignment.id,
                 description=f'Assigned {assignment.get_entity_name()} to shift')
        
        return jsonify({'success': True, 'message': 'تم التعيين بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'خطأ في التعيين: {str(e)}'})

@main_bp.route('/attendance/record')
@login_required
def attendance_record():
    """Daily attendance recording"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لتسجيل الحضور', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get selected date (default to today)
    selected_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    
    # Get selected shift (default to first active shift)
    shift_id = request.args.get('shift_id')
    shifts = Shift.query.filter_by(is_active=True).order_by(Shift.start_time).all()
    
    if not shifts:
        flash('لا توجد ورديات نشطة. يرجى إنشاء وردية أولاً', 'warning')
        return redirect(url_for('main.attendance_shifts'))
    
    if shift_id:
        selected_shift = Shift.query.get_or_404(shift_id)
    else:
        selected_shift = shifts[0]
        shift_id = selected_shift.id
    
    # Get employee assignments for selected shift only
    assignments = ShiftAssignment.query.filter_by(
        shift_id=shift_id,
        is_active=True,
        entity_type=EntityType.EMPLOYEE
    ).all()
    
    # Get existing attendance records for the date and shift
    attendance_records = {}
    existing_records = Attendance.query.filter_by(
        shift_id=shift_id,
        date=selected_date
    ).all()
    
    for record in existing_records:
        key = f"{record.entity_type.value}_{record.entity_id}"
        attendance_records[key] = record
    
    return render_template('attendance/record.html',
                         shifts=shifts,
                         selected_shift=selected_shift,
                         selected_date=selected_date,
                         assignments=assignments,
                         attendance_records=attendance_records,
                         AttendanceStatus=AttendanceStatus,
                         AbsenceReason=AbsenceReason,
                         EntityType=EntityType)

@main_bp.route('/attendance/record/save', methods=['POST'])
@login_required
def attendance_record_save():
    """Save individual attendance record"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية لتسجيل الحضور'}), 403
    
    try:
        data = request.json
        shift_id = data['shift_id']
        entity_type = data['entity_type']
        entity_id = data['entity_id']
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        status = data['status']
        absence_reason = data.get('absence_reason')
        late_reason = data.get('late_reason')
        notes = data.get('notes', '')
        check_in_time = data.get('check_in_time')
        check_out_time = data.get('check_out_time')
        
        # Validate that entity is assigned to this shift
        assignment = ShiftAssignment.query.filter_by(
            shift_id=shift_id,
            entity_type=EntityType(entity_type),
            entity_id=entity_id,
            is_active=True
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'هذا العضو غير مُعيَّن لهذه الوردية'})
        
        # Set default absence reason if absent and no reason provided
        if status == 'ABSENT' and (not absence_reason or absence_reason.strip() == ''):
            absence_reason = 'NO_REASON'
        
        # Check if record already exists
        existing_record = Attendance.query.filter_by(
            shift_id=shift_id,
            date=attendance_date,
            entity_type=EntityType(entity_type),
            entity_id=entity_id
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.status = AttendanceStatus(status)
            existing_record.absence_reason = AbsenceReason[absence_reason] if absence_reason and absence_reason.strip() else None
            existing_record.late_reason = late_reason if status == 'LATE' else None
            existing_record.notes = notes
            existing_record.check_in_time = datetime.strptime(check_in_time, '%H:%M').time() if check_in_time else None
            existing_record.check_out_time = datetime.strptime(check_out_time, '%H:%M').time() if check_out_time else None
            existing_record.updated_at = datetime.utcnow()
            
            record = existing_record
        else:
            # Create new record
            record = Attendance(
                shift_id=shift_id,
                date=attendance_date,
                entity_type=EntityType(entity_type),
                entity_id=entity_id,
                status=AttendanceStatus(status),
                absence_reason=AbsenceReason[absence_reason] if absence_reason and absence_reason.strip() else None,
                late_reason=late_reason if status == 'LATE' else None,
                notes=notes,
                check_in_time=datetime.strptime(check_in_time, '%H:%M').time() if check_in_time else None,
                check_out_time=datetime.strptime(check_out_time, '%H:%M').time() if check_out_time else None,
                recorded_by_user_id=current_user.id
            )
            db.session.add(record)
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.CREATE, 'Attendance', record.id,
                 description=f'Recorded attendance for {record.get_entity_name()}: {status}')
        
        return jsonify({'success': True, 'message': 'تم تسجيل الحضور بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'خطأ في تسجيل الحضور: {str(e)}'})

@main_bp.route('/attendance/bulk', methods=['POST'])
@login_required
def attendance_bulk():
    """Bulk attendance operations"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية للعمليات المجمعة'}), 403
    
    try:
        data = request.json
        action = data['action']  # 'mark_all_present' or 'mark_all_absent'
        shift_id = data['shift_id']
        attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        absence_reason = data.get('absence_reason', 'NO_REASON') if action == 'mark_all_absent' else None
        
        # Get all assignments for this shift
        assignments = ShiftAssignment.query.filter_by(
            shift_id=shift_id,
            is_active=True
        ).all()
        
        updated_count = 0
        
        for assignment in assignments:
            # Check if record already exists
            existing_record = Attendance.query.filter_by(
                shift_id=shift_id,
                date=attendance_date,
                entity_type=assignment.entity_type,
                entity_id=assignment.entity_id
            ).first()
            
            if action == 'mark_all_present':
                status = AttendanceStatus.PRESENT
                reason = None
            else:  # mark_all_absent
                status = AttendanceStatus.ABSENT
                reason = AbsenceReason[absence_reason] if absence_reason else AbsenceReason.NO_REASON
            
            if existing_record:
                existing_record.status = status
                existing_record.absence_reason = reason
                existing_record.late_reason = None
                existing_record.updated_at = datetime.utcnow()
            else:
                record = Attendance(
                    shift_id=shift_id,
                    date=attendance_date,
                    entity_type=assignment.entity_type,
                    entity_id=assignment.entity_id,
                    status=status,
                    absence_reason=reason,
                    recorded_by_user_id=current_user.id
                )
                db.session.add(record)
            
            updated_count += 1
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.CREATE, 'Attendance', None,
                 description=f'Bulk attendance action: {action} for {updated_count} entities')
        
        return jsonify({'success': True, 'message': f'تم تحديث حضور {updated_count} عضو بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'خطأ في العملية المجمعة: {str(e)}'})

@main_bp.route('/attendance/reports')
@login_required
def attendance_reports():
    """Generate attendance reports"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        flash('ليس لديك صلاحية لإنشاء التقارير', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Show report form
    shifts = Shift.query.filter_by(is_active=True).all()
    return render_template('attendance/report.html', shifts=shifts)

@main_bp.route('/attendance/report/generate', methods=['POST'])
@login_required
def attendance_report_generate():
    """Generate and download attendance report"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return redirect(url_for('main.dashboard'))
    
    try:
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        shift_id = request.form.get('shift_id')
        
        if start_date > end_date:
            flash('تاريخ البداية يجب أن يكون قبل تاريخ النهاية', 'error')
            return redirect(url_for('main.attendance_reports'))
        
        # Build query
        query = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
        
        if shift_id:
            query = query.filter_by(shift_id=shift_id)
            shift = Shift.query.get(shift_id)
            report_title = f"تقرير حضور - {shift.name} - من {start_date} إلى {end_date}"
        else:
            report_title = f"تقرير حضور شامل - من {start_date} إلى {end_date}"
        
        records = query.order_by(Attendance.date.desc(), Attendance.shift_id).all()
        
        # Generate Excel
        from flask import Response
        from k9.utils.excel_exporter import create_attendance_report_excel, save_excel_to_bytes
        
        # Create Excel workbook
        if shift_id:
            shift = Shift.query.get(shift_id)
            wb = create_attendance_report_excel(records, start_date, end_date, shift.name)
        else:
            wb = create_attendance_report_excel(records, start_date, end_date)
        
        # Convert to bytes
        excel_bytes = save_excel_to_bytes(wb)
        
        # Create response
        response = Response(
            excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'attendance_report_{start_date}_{end_date}.xlsx'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        log_audit(current_user.id, AuditAction.EXPORT, 'Attendance', None,
                 description=f'Generated attendance report for {start_date} to {end_date}')
        
        return response
        
    except Exception as e:
        flash(f'خطأ في إنشاء التقرير: {str(e)}', 'error')
        return redirect(url_for('main.attendance_reports'))

@main_bp.route('/attendance/assignments/<assignment_id>/remove', methods=['POST'])
@login_required
def attendance_assignments_remove(assignment_id):
    """Remove shift assignment"""
    if current_user.role != UserRole.GENERAL_ADMIN:
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية لإزالة التعيينات'}), 403
    
    try:
        assignment = ShiftAssignment.query.get_or_404(assignment_id)
        assignment.is_active = False
        
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.DELETE, 'ShiftAssignment', assignment.id,
                 description=f'Removed assignment for {assignment.get_entity_name()}')
        
        return jsonify({'success': True, 'message': 'تم إزالة التعيين بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'خطأ في إزالة التعيين: {str(e)}'})


# =============================================
# BREEDING SECTION ROUTES (Arabic RTL)
# =============================================

from k9.utils.permission_utils import has_permission
from sqlalchemy.orm import joinedload

@main_bp.route('/breeding/feeding/log')
@login_required
def breeding_feeding_log():
    """Feeding Log main page (Arabic RTL)"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "VIEW"):
        abort(403)
    
    return render_template('breeding/feeding_log.html')

@main_bp.route('/breeding/feeding/log/new')
@login_required
def breeding_feeding_log_new():
    """Create new feeding log entry"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "CREATE"):
        abort(403)
    
    # Get available projects and dogs for dropdowns
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    return render_template('breeding/feeding_log_form.html', 
                         projects=assigned_projects, 
                         dogs=assigned_dogs)

@main_bp.route('/breeding/feeding/log/<log_id>/edit')
@login_required
def breeding_feeding_log_edit(log_id):
    """Edit existing feeding log entry"""
    # Check permissions
    if not has_permission(current_user, "Breeding", "التغذية - السجل اليومي", "EDIT"):
        abort(403)
    
    # Get the log entry with eager loading
    log_entry = FeedingLog.query.options(
        joinedload(FeedingLog.project),
        joinedload(FeedingLog.dog),
        joinedload(FeedingLog.recorder_employee)
    ).get_or_404(log_id)
    
    # Check if user has access to this project
    if current_user.role == UserRole.PROJECT_MANAGER:
        assigned_projects = get_user_assigned_projects(current_user)
        project_ids = [p.id for p in assigned_projects]
        if log_entry.project_id not in project_ids:
            abort(403)
    
    # Get available projects and dogs for dropdowns
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    return render_template('breeding/feeding_log_form.html',
                         projects=assigned_projects,
                         dogs=assigned_dogs,
                         log_entry=log_entry)

# Daily Checkup Routes (Breeding Module)
@main_bp.route('/breeding/checkup')
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.VIEW)
def breeding_checkup():
    """List daily checkup records"""
    return render_template('breeding/checkup_list.html')

@main_bp.route('/breeding/checkup/new')
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.CREATE)
def breeding_checkup_new():
    """Create new daily checkup record"""
    # Get user's accessible projects and dogs
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_employees = get_user_accessible_employees(current_user)
        projects = assigned_projects
        dogs = assigned_dogs
        employees = assigned_employees

    # Arabic choices for form
    part_status_choices = [
        ("سليم", "سليم"),
        ("احمرار", "احمرار"), 
        ("التهاب", "التهاب"),
        ("إفرازات", "إفرازات"),
        ("تورم", "تورم"),
        ("جرح", "جرح"),
        ("جفاف", "جفاف"),
        ("ألم", "ألم"),
        ("أخرى", "أخرى"),
    ]
    
    severity_choices = [
        ("خفيف", "خفيف"),
        ("متوسط", "متوسط"),
        ("شديد", "شديد"),
    ]
    
    return render_template('breeding/checkup_form.html', 
                         projects=projects, 
                         dogs=dogs, 
                         employees=employees,
                         part_status_choices=part_status_choices,
                         severity_choices=severity_choices)

@main_bp.route('/breeding/checkup/<id>/edit')
@login_required
@require_sub_permission('Breeding', 'الفحص الظاهري اليومي', PermissionType.EDIT)
def breeding_checkup_edit(id):
    """Edit daily checkup record"""
    checkup = DailyCheckupLog.query.get_or_404(id)
    
    # Check project access for project managers
    if current_user.role == UserRole.PROJECT_MANAGER:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_project_ids = [p.id for p in assigned_projects]
        if checkup.project_id not in assigned_project_ids:
            abort(403)
    
    # Get data for form
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
        dogs = Dog.query.filter_by(current_status=DogStatus.ACTIVE).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_employees = get_user_accessible_employees(current_user)
        projects = assigned_projects
        dogs = assigned_dogs
        employees = assigned_employees

    # Arabic choices for form  
    part_status_choices = [
        ("سليم", "سليم"),
        ("احمرار", "احمرار"),
        ("التهاب", "التهاب"),
        ("إفرازات", "إفرازات"),
        ("تورم", "تورم"),
        ("جرح", "جرح"),
        ("جفاف", "جفاف"),
        ("ألم", "ألم"),
        ("أخرى", "أخرى"),
    ]
    
    severity_choices = [
        ("خفيف", "خفيف"),
        ("متوسط", "متوسط"),
        ("شديد", "شديد"),
    ]
    
    return render_template('breeding/checkup_form.html', 
                         checkup=checkup,
                         projects=projects, 
                         dogs=dogs, 
                         employees=employees,
                         part_status_choices=part_status_choices,
                         severity_choices=severity_choices)

# Excretion Routes (Breeding Module)
@main_bp.route('/breeding/excretion')
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.VIEW)
def breeding_excretion():
    """List excretion logs"""
    return render_template('breeding/excretion_list.html')

@main_bp.route('/breeding/excretion/new')
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.CREATE)
def breeding_excretion_new():
    """Create new excretion log entry"""
    # Get user's accessible projects and dogs
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
        # Include ACTIVE and TRAINING dogs for health monitoring
        dogs = Dog.query.filter(Dog.current_status.in_([DogStatus.ACTIVE, DogStatus.TRAINING])).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_employees = get_user_accessible_employees(current_user)
        projects = assigned_projects
        dogs = assigned_dogs
        employees = assigned_employees

    # Arabic choices for form enums
    stool_color_choices = [(e.value, e.value) for e in StoolColor]
    stool_consistency_choices = [(e.value, e.value) for e in StoolConsistency]
    stool_content_choices = [(e.value, e.value) for e in StoolContent]
    urine_color_choices = [(e.value, e.value) for e in UrineColor]
    vomit_color_choices = [(e.value, e.value) for e in VomitColor]
    excretion_place_choices = [(e.value, e.value) for e in ExcretionPlace]
    
    return render_template('breeding/excretion_form.html', 
                         projects=projects, 
                         dogs=dogs, 
                         employees=employees,
                         stool_color_choices=stool_color_choices,
                         stool_consistency_choices=stool_consistency_choices,
                         stool_content_choices=stool_content_choices,
                         urine_color_choices=urine_color_choices,
                         vomit_color_choices=vomit_color_choices,
                         excretion_place_choices=excretion_place_choices)

@main_bp.route('/breeding/excretion/<id>/edit')
@login_required
@require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.EDIT)
def breeding_excretion_edit(id):
    """Edit excretion log record"""
    excretion_log = ExcretionLog.query.get_or_404(id)
    
    # Check project access for project managers
    if current_user.role == UserRole.PROJECT_MANAGER:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_project_ids = [p.id for p in assigned_projects]
        if excretion_log.project_id not in assigned_project_ids:
            abort(403)
    
    # Get data for form
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.all()
        # Include ACTIVE and TRAINING dogs for health monitoring in edit form too
        dogs = Dog.query.filter(Dog.current_status.in_([DogStatus.ACTIVE, DogStatus.TRAINING])).all()
        employees = Employee.query.filter_by(is_active=True).all()
    else:
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_employees = get_user_accessible_employees(current_user)
        projects = assigned_projects
        dogs = assigned_dogs
        employees = assigned_employees

    # Arabic choices for form enums
    stool_color_choices = [(e.value, e.value) for e in StoolColor]
    stool_consistency_choices = [(e.value, e.value) for e in StoolConsistency]
    stool_content_choices = [(e.value, e.value) for e in StoolContent]
    urine_color_choices = [(e.value, e.value) for e in UrineColor]
    vomit_color_choices = [(e.value, e.value) for e in VomitColor]
    excretion_place_choices = [(e.value, e.value) for e in ExcretionPlace]
    
    return render_template('breeding/excretion_form.html', 
                         excretion_log=excretion_log,
                         projects=projects, 
                         dogs=dogs, 
                         employees=employees,
                         stool_color_choices=stool_color_choices,
                         stool_consistency_choices=stool_consistency_choices,
                         stool_content_choices=stool_content_choices,
                         urine_color_choices=urine_color_choices,
                         vomit_color_choices=vomit_color_choices,
                         excretion_place_choices=excretion_place_choices)

# API Routes for Excretion - DEPRECATED: Use api_excretion.py instead
# @main_bp.route('/api/breeding/excretion/list')
# @login_required
# @require_sub_permission('Breeding', 'البراز / البول / القيء', PermissionType.VIEW)
def api_list_excretion_deprecated():
    """API endpoint for excretion logs list"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        project_id = request.args.get('project_id')
        dog_id = request.args.get('dog_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Base query with joins
        query = ExcretionLog.query.join(Dog, ExcretionLog.dog_id == Dog.id)
        query = query.outerjoin(Project, ExcretionLog.project_id == Project.id)
        
        # Apply user access restrictions
        if current_user.role == UserRole.GENERAL_ADMIN:
            # Admin can see all logs
            pass
        else:
            # PROJECT_MANAGER can only see logs from assigned projects
            assigned_projects = get_user_assigned_projects(current_user)
            if not assigned_projects:
                return jsonify({
                    'items': [],
                    'pagination': {'page': 1, 'pages': 1, 'per_page': per_page, 'total': 0, 'has_prev': False, 'has_next': False},
                    'kpis': {'total': 0, 'stool': {'constipation': 0, 'abnormal_consistency': 0}, 'urine': {'abnormal_color': 0}, 'vomit': {'total_events': 0}}
                })
            
            project_ids = [p.id for p in assigned_projects]
            query = query.filter(db.or_(ExcretionLog.project_id.in_(project_ids), ExcretionLog.project_id.is_(None)))
        
        # Apply filters
        if project_id:
            query = query.filter(ExcretionLog.project_id == project_id)
        
        if dog_id:
            query = query.filter(ExcretionLog.dog_id == dog_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(ExcretionLog.date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(ExcretionLog.date <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        
        # Calculate KPIs on filtered data
        kpis_query = query.with_entities(ExcretionLog)
        total_count = kpis_query.count()
        constipation_count = kpis_query.filter(ExcretionLog.constipation == True).count()
        abnormal_stool_count = kpis_query.filter(ExcretionLog.stool_consistency.in_(['سائل', 'شديد الصلابة'])).count()
        abnormal_urine_count = kpis_query.filter(ExcretionLog.urine_color.in_(['بني مصفر', 'وردي/دموي'])).count()
        vomit_events = kpis_query.filter(ExcretionLog.vomit_count > 0).count()
        
        kpis = {
            'total': total_count,
            'stool': {
                'constipation': constipation_count,
                'abnormal_consistency': abnormal_stool_count
            },
            'urine': {
                'abnormal_color': abnormal_urine_count
            },
            'vomit': {
                'total_events': vomit_events
            }
        }
        
        # Order by date and time descending
        query = query.order_by(ExcretionLog.date.desc(), ExcretionLog.time.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format results
        items = []
        for log in pagination.items:
            items.append({
                'id': str(log.id),
                'date': log.date.strftime('%Y-%m-%d'),
                'time': log.time.strftime('%H:%M'),
                'project_name': log.project.name if log.project else '',
                'dog_name': log.dog.name if log.dog else '',
                'stool_color': log.stool_color,
                'stool_consistency': log.stool_consistency,
                'stool_content': log.stool_content,
                'constipation': log.constipation,
                'stool_place': log.stool_place,
                'stool_notes': log.stool_notes,
                'urine_color': log.urine_color,
                'urine_notes': log.urine_notes,
                'vomit_color': log.vomit_color,
                'vomit_count': log.vomit_count,
                'vomit_notes': log.vomit_notes,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'items': items,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            },
            'kpis': kpis
        })
        
    except Exception as e:
        app.logger.error(f"Error listing excretion logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/breeding/grooming')
@login_required 
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.VIEW)
def breeding_grooming():
    """Grooming care main page"""
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Arabic display mappings for enums
    yesno_display = {
        GroomingYesNo.YES.value: "نعم",
        GroomingYesNo.NO.value: "لا"
    }
    
    cleanliness_display = {
        GroomingCleanlinessScore.SCORE_1.value: "1",
        GroomingCleanlinessScore.SCORE_2.value: "2", 
        GroomingCleanlinessScore.SCORE_3.value: "3",
        GroomingCleanlinessScore.SCORE_4.value: "4",
        GroomingCleanlinessScore.SCORE_5.value: "5"
    }
    
    return render_template('breeding/grooming_list.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         yesno_display=yesno_display,
                         cleanliness_display=cleanliness_display)

@main_bp.route('/breeding/grooming/new')
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.CREATE)
def breeding_grooming_new():
    """Create new grooming log entry"""
    # Get projects accessible by user  
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Get accessible employees for recorder field
    accessible_employees = get_user_accessible_employees(current_user)
    
    # Arabic choices for enums
    yesno_choices = [
        (GroomingYesNo.YES.value, "نعم"),
        (GroomingYesNo.NO.value, "لا")
    ]
    
    cleanliness_choices = [
        (GroomingCleanlinessScore.SCORE_1.value, "1"),
        (GroomingCleanlinessScore.SCORE_2.value, "2"),
        (GroomingCleanlinessScore.SCORE_3.value, "3"),
        (GroomingCleanlinessScore.SCORE_4.value, "4"),
        (GroomingCleanlinessScore.SCORE_5.value, "5")
    ]
    
    return render_template('breeding/grooming_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         employees=accessible_employees,
                         yesno_choices=yesno_choices,
                         cleanliness_choices=cleanliness_choices,
                         grooming_log=None)

@main_bp.route('/breeding/grooming/<id>/edit')
@login_required
@require_sub_permission('Breeding', 'العناية (الاستحمام)', PermissionType.EDIT)
def breeding_grooming_edit(id):
    """Edit existing grooming log entry"""
    grooming_log = GroomingLog.query.get_or_404(id)
    
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
        # Verify user has access to this log's project (allow if no project assigned)
        if grooming_log.project is not None and grooming_log.project not in projects:
            abort(403)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Get accessible employees 
    accessible_employees = get_user_accessible_employees(current_user)
    
    # Arabic choices for enums
    yesno_choices = [
        (GroomingYesNo.YES.value, "نعم"),
        (GroomingYesNo.NO.value, "لا")
    ]
    
    cleanliness_choices = [
        (GroomingCleanlinessScore.SCORE_1.value, "1"),
        (GroomingCleanlinessScore.SCORE_2.value, "2"),
        (GroomingCleanlinessScore.SCORE_3.value, "3"),
        (GroomingCleanlinessScore.SCORE_4.value, "4"),
        (GroomingCleanlinessScore.SCORE_5.value, "5")
    ]
    
    return render_template('breeding/grooming_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         employees=accessible_employees,
                         yesno_choices=yesno_choices,
                         cleanliness_choices=cleanliness_choices,
                         grooming_log=grooming_log)

# Cleaning Routes (Breeding Module)
@main_bp.route('/breeding/cleaning')
@login_required 
@require_sub_permission('Breeding', 'النظافة (البيئة/القفص)', PermissionType.VIEW)
def cleaning_list():
    """Cleaning logs main page"""
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    return render_template('breeding/cleaning_list.html',
                         projects=projects,
                         dogs=accessible_dogs)

@main_bp.route('/breeding/cleaning/new')
@login_required
@require_sub_permission('Breeding', 'النظافة (البيئة/القفص)', PermissionType.CREATE)
def cleaning_new():
    """Create new cleaning log entry"""
    # Get projects accessible by user  
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    return render_template('breeding/cleaning_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         cleaning_log=None,
                         today=date.today())

@main_bp.route('/breeding/cleaning/<id>/edit')
@login_required
@require_sub_permission('Breeding', 'النظافة (البيئة/القفص)', PermissionType.EDIT)
def cleaning_edit(id):
    """Edit existing cleaning log entry"""
    cleaning_log = CleaningLog.query.get_or_404(id)
    
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
        # Verify user has access to this log's project
        if cleaning_log.project not in projects:
            abort(403)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    return render_template('breeding/cleaning_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         cleaning_log=cleaning_log,
                         today=date.today())

# Feeding Routes (Breeding Module)
@main_bp.route('/breeding/feeding')
@login_required 
@require_sub_permission('Breeding', 'التغذية', PermissionType.VIEW)
def breeding_feeding():
    """Feeding logs main page"""
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Get accessible employees for recorder field
    accessible_employees = get_user_accessible_employees(current_user)
    
    # Arabic display mappings for enums
    prep_method_display = {
        PrepMethod.BOILED.value: "مسلوق",
        PrepMethod.STEAMED.value: "مطبوخ بالبخار", 
        PrepMethod.SOAKED.value: "منقوع",
        PrepMethod.OTHER.value: "أخرى"
    }
    
    body_condition_display = {
        BodyConditionScale.VERY_THIN.value: "نحيف جداً",
        BodyConditionScale.THIN.value: "نحيف",
        BodyConditionScale.BELOW_IDEAL.value: "أقل من المثالي",
        BodyConditionScale.NEAR_IDEAL.value: "قريب من المثالي",
        BodyConditionScale.IDEAL.value: "مثالي",
        BodyConditionScale.ABOVE_IDEAL.value: "أعلى من المثالي",
        BodyConditionScale.FULL.value: "ممتلئ",
        BodyConditionScale.OBESE.value: "بدين",
        BodyConditionScale.VERY_OBESE.value: "بدين جداً"
    }
    
    return render_template('breeding/feeding_list.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         employees=accessible_employees,
                         prep_method_display=prep_method_display,
                         body_condition_display=body_condition_display)

@main_bp.route('/breeding/feeding/new')
@login_required
@require_sub_permission('Breeding', 'التغذية', PermissionType.CREATE)
def breeding_feeding_new():
    """Create new feeding log entry"""
    # Get projects accessible by user  
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Get accessible employees for recorder field
    accessible_employees = get_user_accessible_employees(current_user)
    
    # Arabic choices for enums
    prep_method_choices = [
        (PrepMethod.BOILED.value, "مسلوق"),
        (PrepMethod.STEAMED.value, "مطبوخ بالبخار"),
        (PrepMethod.SOAKED.value, "منقوع"),
        (PrepMethod.OTHER.value, "أخرى")
    ]
    
    body_condition_choices = [
        (BodyConditionScale.VERY_THIN.value, "نحيف جداً"),
        (BodyConditionScale.THIN.value, "نحيف"),
        (BodyConditionScale.BELOW_IDEAL.value, "أقل من المثالي"),
        (BodyConditionScale.NEAR_IDEAL.value, "قريب من المثالي"),
        (BodyConditionScale.IDEAL.value, "مثالي"),
        (BodyConditionScale.ABOVE_IDEAL.value, "أعلى من المثالي"),
        (BodyConditionScale.FULL.value, "ممتلئ"),
        (BodyConditionScale.OBESE.value, "بدين"),
        (BodyConditionScale.VERY_OBESE.value, "بدين جداً")
    ]
    
    return render_template('breeding/feeding_log_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         employees=accessible_employees,
                         prep_method_choices=prep_method_choices,
                         body_condition_choices=body_condition_choices,
                         feeding_log=None,
                         today=date.today())

@main_bp.route('/breeding/feeding/<id>/edit')
@login_required
@require_sub_permission('Breeding', 'التغذية', PermissionType.EDIT)
def breeding_feeding_edit(id):
    """Edit existing feeding log entry"""
    feeding_log = FeedingLog.query.get_or_404(id)
    
    # Get projects accessible by user
    if current_user.role == UserRole.GENERAL_ADMIN:
        projects = Project.query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED])).all()
    else:
        projects = get_user_assigned_projects(current_user)
        # Verify user has access to this log's project (allow if no project assigned)
        if feeding_log.project is not None and feeding_log.project not in projects:
            abort(403)
    
    # Get accessible dogs
    accessible_dogs = get_user_accessible_dogs(current_user)
    
    # Get accessible employees 
    accessible_employees = get_user_accessible_employees(current_user)
    
    # Arabic choices for enums
    prep_method_choices = [
        (PrepMethod.BOILED.value, "مسلوق"),
        (PrepMethod.STEAMED.value, "مطبوخ بالبخار"),
        (PrepMethod.SOAKED.value, "منقوع"),
        (PrepMethod.OTHER.value, "أخرى")
    ]
    
    body_condition_choices = [
        (BodyConditionScale.VERY_THIN.value, "نحيف جداً"),
        (BodyConditionScale.THIN.value, "نحيف"),
        (BodyConditionScale.BELOW_IDEAL.value, "أقل من المثالي"),
        (BodyConditionScale.NEAR_IDEAL.value, "قريب من المثالي"),
        (BodyConditionScale.IDEAL.value, "مثالي"),
        (BodyConditionScale.ABOVE_IDEAL.value, "أعلى من المثالي"),
        (BodyConditionScale.FULL.value, "ممتلئ"),
        (BodyConditionScale.OBESE.value, "بدين"),
        (BodyConditionScale.VERY_OBESE.value, "بدين جداً")
    ]
    
    return render_template('breeding/feeding_log_form.html',
                         projects=projects,
                         dogs=accessible_dogs,
                         employees=accessible_employees,
                         prep_method_choices=prep_method_choices,
                         body_condition_choices=body_condition_choices,
                         feeding_log=feeding_log,
                         today=date.today())


@main_bp.route('/breeding/deworming')
@login_required
def breeding_deworming():
    """List deworming logs"""
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'جرعة الديدان', PermissionType.VIEW):
        abort(403)
    
    from k9.utils.utils import get_user_assigned_projects
    assigned_projects = get_user_assigned_projects(current_user)
    
    from k9.models.models import Route, Unit, Reaction
    # Convert enums to list of dictionaries for JavaScript
    route_choices = [{"value": choice.value, "text": choice.value} for choice in Route]
    unit_choices = [{"value": choice.value, "text": choice.value} for choice in Unit]
    reaction_choices = [{"value": choice.value, "text": choice.value} for choice in Reaction]
    
    return render_template('breeding/deworming_list.html',
                          route_choices=route_choices,
                          unit_choices=unit_choices,
                          reaction_choices=reaction_choices,
                          assigned_projects=assigned_projects)

@main_bp.route('/breeding/deworming/new')
@login_required
def breeding_deworming_new():
    """Add new deworming log"""
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'جرعة الديدان', PermissionType.CREATE):
        abort(403)
        
    from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    from k9.models.models import Employee, Route, Unit, Reaction, EmployeeRole
    # Get all accessible employees, then filter for VETs and other relevant roles
    accessible_employees = get_user_accessible_employees(current_user)
    # Also include all active employees for compatibility - can be refined later
    employees = Employee.query.filter_by(is_active=True).all()
    
    # Convert enums to list of dictionaries for JavaScript
    route_choices = [{"value": choice.value, "text": choice.value} for choice in Route]
    unit_choices = [{"value": choice.value, "text": choice.value} for choice in Unit]
    reaction_choices = [{"value": choice.value, "text": choice.value} for choice in Reaction]
    
    return render_template('breeding/deworming_form.html',
                          assigned_projects=assigned_projects,
                          assigned_dogs=assigned_dogs,
                          employees=employees,
                          route_choices=route_choices,
                          unit_choices=unit_choices,
                          reaction_choices=reaction_choices,
                          mode='create')

@main_bp.route('/breeding/deworming/<id>/edit')
@login_required
def breeding_deworming_edit(id):
    """Edit deworming log"""
    from k9.models.models import DewormingLog, Employee, Dog, Route, Unit, Reaction
    
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'جرعة الديدان', PermissionType.EDIT):
        abort(403)
    
    log = DewormingLog.query.get_or_404(id)
    
    # Check project access for project managers
    if current_user.role.value == "PROJECT_MANAGER":
        from k9.utils.utils import get_user_assigned_projects
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_project_ids = [p.id for p in assigned_projects]
        if log.project_id not in assigned_project_ids:
            abort(403)
    
    from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    # Get all accessible employees
    accessible_employees = get_user_accessible_employees(current_user)
    # Also include all active employees for compatibility - can be refined later  
    employees = Employee.query.filter_by(is_active=True).all()
    
    # Convert enums to list of dictionaries for JavaScript
    route_choices = [{"value": choice.value, "text": choice.value} for choice in Route]
    unit_choices = [{"value": choice.value, "text": choice.value} for choice in Unit]
    reaction_choices = [{"value": choice.value, "text": choice.value} for choice in Reaction]
    
    return render_template('breeding/deworming_form.html',
                          log=log,
                          assigned_projects=assigned_projects,
                          assigned_dogs=assigned_dogs,
                          employees=employees,
                          route_choices=route_choices,
                          unit_choices=unit_choices,
                          reaction_choices=reaction_choices,
                          mode='edit')

@main_bp.route('/breeding/training-activity')
@login_required
def breeding_training_activity():
    """List training activities"""
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'تدريب — أنشطة يومية', PermissionType.VIEW):
        abort(403)
    
    from k9.utils.utils import get_user_assigned_projects
    assigned_projects = get_user_assigned_projects(current_user)
    
    return render_template('breeding/training_activity_list.html',
                          assigned_projects=assigned_projects)

@main_bp.route('/breeding/training-activity/new')
@login_required
def breeding_training_activity_new():
    """Add new training activity"""
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'تدريب — أنشطة يومية', PermissionType.CREATE):
        abort(403)
        
    from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    from k9.models.models import Employee, EmployeeRole
    # Get trainers and other relevant employees
    accessible_employees = get_user_accessible_employees(current_user)
    # Also include all active trainers for compatibility
    trainers = Employee.query.filter_by(is_active=True, role=EmployeeRole.TRAINER).all()
    
    return render_template('breeding/training_activity_form.html',
                          assigned_projects=assigned_projects,
                          assigned_dogs=assigned_dogs,
                          trainers=trainers,
                          activity=None)

@main_bp.route('/breeding/training-activity/<id>/edit')
@login_required
def breeding_training_activity_edit(id):
    """Edit training activity"""
    from k9.models.models import BreedingTrainingActivity, Employee, EmployeeRole
    
    # Check permissions
    from k9.utils.permission_utils import has_permission
    from k9.models.models import PermissionType
    if not has_permission(current_user, 'Breeding', 'تدريب — أنشطة يومية', PermissionType.EDIT):
        abort(403)
    
    activity = BreedingTrainingActivity.query.get_or_404(id)
    
    # Check project access for project managers
    if current_user.role.value == "PROJECT_MANAGER":
        from k9.utils.utils import get_user_assigned_projects
        assigned_projects = get_user_assigned_projects(current_user)
        assigned_project_ids = [p.id for p in assigned_projects]
        if activity.project_id and activity.project_id not in assigned_project_ids:
            abort(403)
    
    from k9.utils.utils import get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
    assigned_projects = get_user_assigned_projects(current_user)
    assigned_dogs = get_user_accessible_dogs(current_user)
    
    # Get trainers
    accessible_employees = get_user_accessible_employees(current_user)
    trainers = Employee.query.filter_by(is_active=True, role=EmployeeRole.TRAINER).all()
    
    return render_template('breeding/training_activity_form.html',
                          assigned_projects=assigned_projects,
                          assigned_dogs=assigned_dogs,
                          trainers=trainers,
                          activity=activity)

@main_bp.route('/breeding/cleaning')
@login_required
def breeding_cleaning():
    """Environment/cage cleaning placeholder page"""
    return render_template('breeding/_placeholder.html',
                         title="النظافة (البيئة/القفص)",
                         fields=["نوع التنظيف", "المواد المستخدمة", "وقت التنظيف", "حالة القفص", "تغيير الفراش", "تطهير الأواني", "حالة المنطقة", "ملاحظات"])

@main_bp.route('/search')
@login_required
def search():
    """Global search functionality - works independently of projects"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({
            'dogs': [],
            'employees': [],
            'projects': []
        })
    
    try:
        # Search ALL dogs globally (no project restriction)
        dogs_results = []
        if current_user.role == UserRole.GENERAL_ADMIN:
            # Admin can search all dogs regardless of project assignment
            dogs = Dog.query.filter(
                Dog.name.ilike(f'%{query}%') | 
                Dog.code.ilike(f'%{query}%')
            ).limit(15).all()
        else:
            # PROJECT_MANAGER - search accessible dogs but also include unassigned dogs
            accessible_dogs = get_user_accessible_dogs(current_user)
            # Also include dogs not assigned to any project
            unassigned_dogs = Dog.query.outerjoin(ProjectDog).filter(
                ProjectDog.dog_id.is_(None),
                Dog.name.ilike(f'%{query}%') | Dog.code.ilike(f'%{query}%')
            ).all()
            
            # Combine accessible and unassigned dogs
            all_searchable_dogs = list(accessible_dogs) + unassigned_dogs
            dogs = [dog for dog in all_searchable_dogs 
                   if query.lower() in dog.name.lower() or 
                      query.lower() in dog.code.lower()][:15]
        
        dogs_results = [{
            'id': str(dog.id),
            'name': dog.name,
            'code': dog.code,
            'status': dog.current_status.value if dog.current_status else 'غير محدد',
            'assigned_project': 'غير مُعين' if not hasattr(dog, 'project_assignments') or not dog.project_assignments else 'مُعين لمشروع'
        } for dog in dogs]
        
        # Search ALL employees globally 
        employees_results = []
        if current_user.role == UserRole.GENERAL_ADMIN:
            employees = Employee.query.filter(
                Employee.name.ilike(f'%{query}%') | 
                Employee.employee_id.ilike(f'%{query}%')
            ).filter_by(is_active=True).limit(15).all()
        else:
            # PROJECT_MANAGER - search accessible employees + unassigned ones
            accessible_employees = get_user_accessible_employees(current_user)
            # Also include employees not assigned to any specific project
            all_employees = Employee.query.filter(
                Employee.name.ilike(f'%{query}%') | 
                Employee.employee_id.ilike(f'%{query}%'),
                Employee.is_active == True
            ).all()
            
            employees = [emp for emp in all_employees 
                        if query.lower() in emp.name.lower() or 
                           query.lower() in emp.employee_id.lower()][:15]
        
        employees_results = [{
            'id': str(employee.id),
            'name': employee.name,
            'employee_id': employee.employee_id,
            'role': employee.role.value if employee.role else 'غير محدد'
        } for employee in employees]
        
        # Search projects (for completeness)
        projects_results = []
        if current_user.role == UserRole.GENERAL_ADMIN:
            projects = Project.query.filter(
                Project.name.ilike(f'%{query}%') | 
                Project.code.ilike(f'%{query}%')
            ).limit(10).all()
        else:
            assigned_projects = get_user_assigned_projects(current_user)
            projects = [proj for proj in assigned_projects 
                       if query.lower() in proj.name.lower() or 
                          query.lower() in proj.code.lower()][:10]
        
        projects_results = [{
            'id': str(project.id),
            'name': project.name,
            'code': project.code,
            'status': project.status.value if project.status else 'غير محدد'
        } for project in projects]
        
        return jsonify({
            'dogs': dogs_results,
            'employees': employees_results,
            'projects': projects_results
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Search failed',
            'dogs': [],
            'employees': [],
            'projects': []
        }), 500

