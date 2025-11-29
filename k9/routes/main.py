from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, abort, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from k9.models.models import (Dog, Employee, TrainingSession, VeterinaryVisit, ProductionCycle, 
                   Project, ProjectLocation, AuditLog, UserRole, DogStatus, 
                   EmployeeRole, TrainingCategory, VisitType, ProductionCycleType, 
                   ProductionResult, ProjectStatus, AuditAction, DogGender, User,
                   MaturityStatus, HeatStatus, PregnancyStatus, ProjectDog, ProjectAssignment,
                   Incident, Suspicion, PerformanceEvaluation, 
                   ElementType, PerformanceRating, TargetType,
                   project_employee_assignment, project_dog_assignment,
                   # Production models
                   HeatCycle, MatingRecord, MatingResult, PregnancyRecord, DeliveryRecord, PuppyRecord, PuppyTraining,
                   # Breeding models
                   FeedingLog, PrepMethod, BodyConditionScale, DailyCheckupLog,
                   # Excretion models
                   ExcretionLog, StoolColor, StoolConsistency, StoolContent, UrineColor, VomitColor, ExcretionPlace,
                   # Grooming models
                   GroomingLog, GroomingCleanlinessScore, GroomingYesNo,
                   # Cleaning models
                   CleaningLog,
                   # Shift models
                   Shift)
from k9.utils.utils import log_audit, allowed_file, generate_pdf_report, get_project_manager_permissions, get_employee_profile_for_user, get_user_active_projects, validate_project_manager_assignment, get_user_assigned_projects, get_user_accessible_dogs, get_user_accessible_employees
from k9.utils.permissions_new import (
    admin_or_pm_required, has_permission, _is_admin_mode, require_permission, 
    get_sections_for_user
)
from k9.utils.validators import validate_yemen_phone
from k9.utils.template_utils import get_base_template, is_pm_view
from k9.utils.pm_scoping import get_scoped_dogs, get_scoped_employees, get_scoped_projects, is_pm, is_admin
from sqlalchemy.exc import IntegrityError
import os
from datetime import datetime, date, timedelta
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/unauthorized')
@login_required
def unauthorized():
    """صفحة عدم التصريح"""
    return render_template('unauthorized.html'), 403

@main_bp.route('/my-permissions')
@login_required
def user_permissions_dashboard():
    """لوحة تحكم صلاحيات المستخدم - تعرض جميع الصلاحيات الممنوحة"""
    from k9.models.permissions_new import Permission, UserPermission
    from collections import defaultdict
    
    user_perms = db.session.query(Permission).join(
        UserPermission, Permission.id == UserPermission.permission_id
    ).filter(UserPermission.user_id == current_user.id).all()
    
    permissions_by_category = defaultdict(list)
    for perm in user_perms:
        perm_url = get_permission_url(perm.key)
        perm_data = {
            'key': perm.key,
            'name_ar': perm.name_ar,
            'description': perm.description,
            'url': perm_url
        }
        permissions_by_category[perm.category].append(perm_data)
    
    category_names = {
        'dogs': 'الكلاب',
        'employees': 'الموظفين',
        'training': 'التدريب',
        'veterinary': 'الطب البيطري',
        'breeding': 'التربية',
        'production': 'الإنتاج',
        'projects': 'المشاريع',
        'admin': 'الإدارة',
        'pm': 'مدير المشروع',
        'schedule': 'الجداول',
        'shifts': 'الورديات',
        'incidents': 'الحوادث',
        'tasks': 'المهام',
        'notifications': 'الإشعارات',
        'accounts': 'الحسابات',
        'handler_reports': 'تقارير السائسين',
        'supervisor': 'المشرف',
        'reports.attendance': 'تقارير الحضور',
        'reports.breeding.feeding': 'تقارير التغذية',
        'reports.breeding.checkup': 'تقارير الفحص',
        'reports.caretaker': 'تقارير العناية',
        'reports.training': 'تقارير التدريب',
        'reports.veterinary': 'التقارير البيطرية'
    }
    
    view_count = sum(1 for p in user_perms if 'view' in p.key)
    edit_count = sum(1 for p in user_perms if 'edit' in p.key or 'create' in p.key)
    
    quick_access = build_quick_access_items(user_perms)
    
    return render_template('user/dashboard.html',
        user_permissions=user_perms,
        permissions_by_category=dict(permissions_by_category),
        categories=list(permissions_by_category.keys()),
        category_names=category_names,
        view_count=view_count,
        edit_count=edit_count,
        quick_access=quick_access
    )

def get_permission_url(permission_key):
    """تحويل مفتاح الصلاحية إلى رابط مباشر"""
    url_mapping = {
        'dogs.view': 'main.dogs_list',
        'dogs.create': 'main.dogs_add',
        'employees.view': 'main.employees_list',
        'employees.create': 'main.employees_add',
        'training.view': 'main.training_list',
        'veterinary.view': 'main.veterinary_list',
        'breeding.view': 'main.breeding_training_activity',
        'production.view': 'main.maturity_list',
        'projects.view': 'main.projects_list',
        'pm.dashboard': 'pm.dashboard',
        'pm.dogs': 'pm.my_dogs',
        'pm.team': 'pm.my_team',
        'pm.approvals': 'pm.pending_approvals',
        'admin.dashboard': 'admin.dashboard',
        'admin.permissions.view': 'admin.comprehensive_permissions',
        'schedule.view': 'handler_daily.schedules',
        'reports.breeding.feeding.view': 'unified_feeding_reports_ui.feeding',
        'reports.breeding.checkup.view': 'unified_checkup_reports_ui.checkup',
        'reports.veterinary.view': 'veterinary_reports_ui.veterinary',
        'reports.caretaker.view': 'caretaker_daily_reports_ui.caretaker_daily',
        'reports.training.view': 'reports_training_trainer_daily_ui.trainer_daily',
        'handler_reports.view': 'handler_daily.my_reports',
    }
    
    endpoint = url_mapping.get(permission_key)
    if endpoint:
        try:
            return url_for(endpoint)
        except Exception:
            return None
    return None

def build_quick_access_items(permissions):
    """بناء قائمة الوصول السريع بناء على الصلاحيات"""
    quick_items = []
    perm_keys = [p.key for p in permissions]
    
    try:
        if any(k in perm_keys for k in ['dogs.view', 'dogs.edit', 'pm.dogs']):
            if 'dogs.view' in perm_keys:
                quick_items.append({
                    'title': 'الكلاب',
                    'icon': 'fas fa-dog',
                    'url': url_for('main.dogs_list'),
                    'color': 'text-primary'
                })
            elif 'pm.dogs' in perm_keys:
                quick_items.append({
                    'title': 'كلاب المشروع',
                    'icon': 'fas fa-dog',
                    'url': url_for('pm.my_dogs'),
                    'color': 'text-primary'
                })
    except Exception:
        pass
    
    try:
        if any(k in perm_keys for k in ['employees.view', 'employees.edit', 'pm.team']):
            if 'employees.view' in perm_keys:
                quick_items.append({
                    'title': 'الموظفين',
                    'icon': 'fas fa-users',
                    'url': url_for('main.employees_list'),
                    'color': 'text-success'
                })
            elif 'pm.team' in perm_keys:
                quick_items.append({
                    'title': 'فريق المشروع',
                    'icon': 'fas fa-users',
                    'url': url_for('pm.my_team'),
                    'color': 'text-success'
                })
    except Exception:
        pass
    
    try:
        if any(k in perm_keys for k in ['pm.dashboard', 'pm.project']):
            quick_items.append({
                'title': 'لوحة مدير المشروع',
                'icon': 'fas fa-project-diagram',
                'url': url_for('pm.dashboard'),
                'color': 'text-warning'
            })
    except Exception:
        pass
    
    try:
        if 'training.view' in perm_keys:
            quick_items.append({
                'title': 'التدريب',
                'icon': 'fas fa-graduation-cap',
                'url': url_for('main.training_list'),
                'color': 'text-info'
            })
        elif 'reports.training.view' in perm_keys:
            quick_items.append({
                'title': 'تقارير التدريب',
                'icon': 'fas fa-graduation-cap',
                'url': url_for('reports_training_trainer_daily_ui.trainer_daily'),
                'color': 'text-info'
            })
    except Exception:
        pass
    
    try:
        if 'veterinary.view' in perm_keys:
            quick_items.append({
                'title': 'الطب البيطري',
                'icon': 'fas fa-stethoscope',
                'url': url_for('main.veterinary_list'),
                'color': 'text-danger'
            })
        elif 'reports.veterinary.view' in perm_keys:
            quick_items.append({
                'title': 'التقارير البيطرية',
                'icon': 'fas fa-stethoscope',
                'url': url_for('veterinary_reports_ui.veterinary'),
                'color': 'text-danger'
            })
    except Exception:
        pass
    
    try:
        if 'reports.breeding.feeding.view' in perm_keys:
            quick_items.append({
                'title': 'تقارير التغذية',
                'icon': 'fas fa-bone',
                'url': url_for('unified_feeding_reports_ui.feeding'),
                'color': 'text-pink'
            })
    except Exception:
        pass
    
    try:
        if 'reports.breeding.checkup.view' in perm_keys:
            quick_items.append({
                'title': 'تقارير الفحص',
                'icon': 'fas fa-heartbeat',
                'url': url_for('unified_checkup_reports_ui.checkup'),
                'color': 'text-pink'
            })
    except Exception:
        pass
    
    try:
        if 'reports.caretaker.view' in perm_keys:
            quick_items.append({
                'title': 'تقارير المربي',
                'icon': 'fas fa-hand-holding-heart',
                'url': url_for('caretaker_daily_reports_ui.caretaker_daily'),
                'color': 'text-success'
            })
    except Exception:
        pass
    
    try:
        if 'admin.dashboard' in perm_keys:
            quick_items.append({
                'title': 'لوحة المدير العام',
                'icon': 'fas fa-user-shield',
                'url': url_for('admin.dashboard'),
                'color': 'text-dark'
            })
    except Exception:
        pass
    
    return quick_items

@main_bp.route('/dashboard')
@login_required
def dashboard():
    from flask import session, current_app
    # get_sections_for_user and _is_admin_mode imported at module level from permissions_new
    
    # DEBUG: Log dashboard access
    current_app.logger.info(f"Dashboard accessed by user: {current_user.username}, role: {current_user.role}")
    current_app.logger.info(f"Session data: pending_mode_selection={session.get('pending_mode_selection')}, admin_mode={session.get('admin_mode')}")
    
    # CRITICAL: Handle pending mode selection for GENERAL_ADMIN users ONLY
    # This replaces the middleware enforcement to prevent redirect loops
    if current_user.role == UserRole.GENERAL_ADMIN and session.get('pending_mode_selection'):
        current_app.logger.info("Redirecting GENERAL_ADMIN to select_mode (pending_mode_selection=True)")
        return redirect(url_for('auth.select_mode'))
    
    # For non-admin users, ensure any stale pending_mode_selection is cleared
    if current_user.role != UserRole.GENERAL_ADMIN:
        if session.get('pending_mode_selection') or session.get('pending_user_id'):
            current_app.logger.info(f"Clearing stale session flags for non-admin user: {current_user.username}")
        session.pop('pending_mode_selection', None)
        session.pop('pending_user_id', None)
    
    # GENERAL_ADMIN in admin mode gets admin dashboard
    if _is_admin_mode(current_user):
        current_app.logger.info("Redirecting to admin dashboard (_is_admin_mode=True)")
        return redirect(url_for('admin.dashboard'))
    
    # GENERAL_ADMIN in PM mode gets PM dashboard
    if current_user.role == UserRole.GENERAL_ADMIN:
        admin_mode = session.get('admin_mode', 'general_admin')
        if admin_mode == 'project_manager':
            current_app.logger.info("Redirecting GENERAL_ADMIN in PM mode to pm.dashboard")
            return redirect(url_for('pm.dashboard'))
    
    # PROJECT_MANAGER users ALWAYS go to PM dashboard (prevents redirect loop with handler)
    if current_user.role == UserRole.PROJECT_MANAGER:
        current_app.logger.info("Redirecting PROJECT_MANAGER to pm.dashboard")
        return redirect(url_for('pm.dashboard'))
    
    # Check if user has any operational permissions (for other roles like HANDLER)
    user_sections = get_sections_for_user(current_user)
    
    # Users WITH permissions get PM dashboard
    if user_sections:
        current_app.logger.info(f"Redirecting user with sections to pm.dashboard: {user_sections}")
        return redirect(url_for('pm.dashboard'))
    
    # HANDLER users (and only HANDLER users) go to handler dashboard
    if current_user.role == UserRole.HANDLER:
        current_app.logger.info("Redirecting HANDLER to handler.dashboard")
        return redirect(url_for('handler.dashboard'))
    
    # Fallback for any other role - go to PM dashboard to avoid redirect loops
    current_app.logger.info(f"Fallback redirect to pm.dashboard for role: {current_user.role}")
    return redirect(url_for('pm.dashboard'))
    
    # Fallback statistics (this code is now unreachable but kept for safety)
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
@require_permission('dogs.view')
def dogs_list():
    from datetime import date
    # Use permission-based access for both roles
    dogs = get_user_accessible_dogs(current_user)
    dogs.sort(key=lambda x: x.name or '')  # Sort by name
    
    return render_template('dogs/list.html', dogs=dogs, today=date.today())

@main_bp.route('/dogs/add', methods=['GET', 'POST'])
@login_required
@require_permission('dogs.add')
def dogs_add():
    # Get potential parents for dropdowns
    potential_parents = get_user_accessible_dogs(current_user)
    
    if request.method == 'POST':
        try:
            # File size limits
            MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
            
            # Handle photo upload
            photo_filename = None
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                if photo.filename and allowed_file(photo.filename):
                    # Check file size
                    photo.seek(0, os.SEEK_END)
                    file_size = photo.tell()
                    photo.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'الصورة كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('dogs/add.html', potential_parents=potential_parents)
                    
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
                    # Check file size
                    cert.seek(0, os.SEEK_END)
                    file_size = cert.tell()
                    cert.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'شهادة الميلاد كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('dogs/add.html', potential_parents=potential_parents)
                    
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
            current_app.logger.error(f"Error adding dog: {e}")
            flash(f'حدث خطأ أثناء إضافة الكلب: {str(e)}', 'error')
    
    return render_template('dogs/add.html', genders=DogGender, potential_parents=potential_parents)

@main_bp.route('/dogs/<dog_id>')
@login_required
@require_permission('dogs.view')
def dogs_view(dog_id):
    try:
        dog_id = dog_id
        dog = Dog.query.get_or_404(dog_id)
    except ValueError:
        flash('معرف الكلب غير صحيح', 'error')
        return redirect(url_for('main.dogs_list'))
    
    # Check permissions - use permission-aware helper
    if not _is_admin_mode(current_user):
        accessible_dogs = get_user_accessible_dogs(current_user)
        accessible_dog_ids = [d.id for d in accessible_dogs] if accessible_dogs else []
        if dog.id not in accessible_dog_ids:
            flash('غير مسموح لك بعرض بيانات هذا الكلب', 'error')
            return redirect(url_for('pm.my_dogs') if is_pm(current_user) else url_for('main.index'))
    
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
@require_permission('dogs.edit')
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
            # File size limits
            MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
            
            # Get potential parents for error rendering
            potential_parents = get_user_accessible_dogs(current_user)
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if allowed_file(photo.filename):
                    # Check file size
                    photo.seek(0, os.SEEK_END)
                    file_size = photo.tell()
                    photo.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'الصورة كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('dogs/edit.html', dog=dog, potential_parents=potential_parents)
                    
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
                    # Check file size
                    birth_cert.seek(0, os.SEEK_END)
                    file_size = birth_cert.tell()
                    birth_cert.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'شهادة الميلاد كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('dogs/edit.html', dog=dog, potential_parents=potential_parents)
                    
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
@require_permission('employees.view')
def employees_list():
    # Use permission-aware helper instead of role check
    employees = get_user_accessible_employees(current_user)
    employees.sort(key=lambda x: x.name or '')
    
    return render_template('employees/list.html', employees=employees)

@main_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
@require_permission('employees.create')
def employees_add():
    if request.method == 'POST':
        try:
            # Validate phone number format
            phone = request.form.get('phone', '').strip()
            is_valid, error_message = validate_yemen_phone(phone)
            if not is_valid:
                flash(error_message or 'رقم الهاتف غير صحيح', 'error')
                return render_template('employees/add.html', roles=EmployeeRole)
            
            # Check if phone number already exists
            existing_phone = Employee.query.filter_by(phone=phone).first()
            if existing_phone:
                flash('رقم الهاتف مستخدم بالفعل من قبل موظف آخر', 'error')
                return render_template('employees/add.html', roles=EmployeeRole)
            
            # Prepare employee data first (before any I/O)
            # Use permission-aware helper - assign to user if NOT in admin mode
            assigned_to_user_id = current_user.id if not _is_admin_mode(current_user) else None
            role_mapping = {
                'HANDLER': EmployeeRole.HANDLER,
                'TRAINER': EmployeeRole.TRAINER,
                'BREEDER': EmployeeRole.BREEDER,
                'VET': EmployeeRole.VET,
                'PROJECT_MANAGER': EmployeeRole.PROJECT_MANAGER
            }
            
            employee = Employee()
            employee.name = request.form['name']
            employee.employee_id = request.form['employee_id']
            employee.role = role_mapping[request.form['role']]
            employee.phone = phone
            employee.email = request.form.get('email')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None
            employee.is_active = True
            employee.assigned_to_user_id = assigned_to_user_id
            employee.national_id = request.form.get('national_id')
            employee.full_name = request.form.get('full_name')
            employee.birth_place = request.form.get('birth_place')
            employee.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date() if request.form.get('birth_date') else None
            employee.current_residence = request.form.get('current_residence')
            employee.residence_google_map_link = request.form.get('residence_google_map_link')
            
            # Add geolocation coordinates
            latitude_str = request.form.get('residence_latitude')
            if latitude_str:
                try:
                    employee.residence_latitude = float(latitude_str)
                except (ValueError, TypeError):
                    employee.residence_latitude = None
            
            longitude_str = request.form.get('residence_longitude')
            if longitude_str:
                try:
                    employee.residence_longitude = float(longitude_str)
                except (ValueError, TypeError):
                    employee.residence_longitude = None
            
            # Add employee to session but don't commit yet (flush to get ID)
            db.session.add(employee)
            db.session.flush()
            
            # Create employee upload folder once
            employee_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'employees', str(employee.id))
            os.makedirs(employee_folder, exist_ok=True)
            
            # Handle employee photo upload (with size limit: 2MB)
            MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
            employee_photo_filename = None
            if 'employee_photo' in request.files and request.files['employee_photo'].filename:
                photo = request.files['employee_photo']
                if photo.filename and allowed_file(photo.filename):
                    # Check file size
                    photo.seek(0, os.SEEK_END)
                    file_size = photo.tell()
                    photo.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'صورة الموظف كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('employees/add.html', roles=EmployeeRole)
                    
                    safe_filename = secure_filename(photo.filename or 'image')
                    employee_photo_filename = f"{uuid.uuid4()}_{safe_filename}"
                    photo_path = os.path.join(employee_folder, employee_photo_filename)
                    photo.save(photo_path)
                    employee.employee_photo = os.path.join('employees', str(employee.id), employee_photo_filename)
            
            # Handle ID card photo upload (with size limit: 2MB)
            id_card_photo_filename = None
            if 'id_card_photo' in request.files and request.files['id_card_photo'].filename:
                id_card = request.files['id_card_photo']
                if id_card.filename and allowed_file(id_card.filename):
                    # Check file size
                    id_card.seek(0, os.SEEK_END)
                    file_size = id_card.tell()
                    id_card.seek(0)
                    
                    if file_size > MAX_IMAGE_SIZE:
                        flash(f'صورة البطاقة كبيرة جداً ({file_size / 1024 / 1024:.1f} ميجابايت). الحد الأقصى 2 ميجابايت', 'error')
                        return render_template('employees/add.html', roles=EmployeeRole)
                    
                    safe_id_filename = secure_filename(id_card.filename or 'id_card')
                    id_card_photo_filename = f"{uuid.uuid4()}_{safe_id_filename}"
                    id_card_path = os.path.join(employee_folder, id_card_photo_filename)
                    id_card.save(id_card_path)
                    employee.id_card_photo = os.path.join('employees', str(employee.id), id_card_photo_filename)
            
            # Handle employee documents (batch process)
            document_types = request.form.getlist('document_types[]')
            document_files = request.files.getlist('document_files[]')
            document_notes = request.form.getlist('document_notes[]')
            
            rejected_files = []
            employee_documents = []
            
            if document_types and document_files:
                from k9.models.models import EmployeeDocument
                MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB
                
                for i, (doc_type, doc_file) in enumerate(zip(document_types, document_files)):
                    if doc_file and doc_file.filename:
                        if allowed_file(doc_file.filename):
                            # Check document file size
                            doc_file.seek(0, os.SEEK_END)
                            file_size = doc_file.tell()
                            doc_file.seek(0)
                            
                            if file_size > MAX_DOCUMENT_SIZE:
                                rejected_files.append(f"{doc_file.filename} (حجم كبير: {file_size / 1024 / 1024:.1f} ميجابايت)")
                                continue
                            
                            safe_doc_filename = secure_filename(doc_file.filename or 'document')
                            unique_doc_filename = f"employee_{employee.id}_{uuid.uuid4()}_{safe_doc_filename}"
                            doc_path = os.path.join(employee_folder, unique_doc_filename)
                            doc_file.save(doc_path)
                            
                            employee_doc = EmployeeDocument()
                            employee_doc.employee_id = employee.id
                            employee_doc.document_type = doc_type
                            employee_doc.file_path = os.path.join('employees', str(employee.id), unique_doc_filename)
                            employee_doc.original_filename = doc_file.filename
                            employee_doc.uploaded_by_id = current_user.id
                            if i < len(document_notes):
                                employee_doc.notes = document_notes[i] if document_notes[i].strip() else None
                            
                            employee_documents.append(employee_doc)
                        else:
                            rejected_files.append(doc_file.filename)
            
            # Bulk add all documents
            if employee_documents:
                db.session.bulk_save_objects(employee_documents)
            
            # Single commit for everything
            db.session.commit()
            
            if rejected_files:
                flash(f'تنبيه: تم رفض بعض الملفات بسبب صيغة غير مسموحة: {", ".join(rejected_files)}', 'warning')
            
            log_audit(current_user.id, AuditAction.CREATE, 'Employee', employee.id, f'أضيف موظف جديد: {employee.name}', None, {'name': employee.name, 'role': employee.role.value})
            flash('تم إضافة الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error adding employee: {e}")
            if 'employee_id' in str(e):
                flash('رقم الموظف مستخدم بالفعل', 'error')
            elif 'phone' in str(e):
                flash('رقم الهاتف مستخدم بالفعل', 'error')
            else:
                flash('حدث خطأ: البيانات المدخلة مكررة', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding employee: {e}")
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
    
    return render_template('employees/add.html', roles=EmployeeRole)

@main_bp.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('employees.edit')
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
            employee.phone = request.form.get('phone')
            employee.email = request.form.get('email')
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form['hire_date'] else None
            employee.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.UPDATE, 'Employee', employee.id, f'تم تحديث بيانات الموظف: {employee.name}', None, {'name': employee.name})
            flash('تم تحديث بيانات الموظف بنجاح', 'success')
            return redirect(url_for('main.employees_list'))
            
        except IntegrityError as e:
            db.session.rollback()
            if 'phone' in str(e):
                flash('رقم الهاتف مستخدم بالفعل', 'error')
            elif 'employee_id' in str(e):
                flash('رقم الموظف مستخدم بالفعل', 'error')
            else:
                flash('حدث خطأ: البيانات المدخلة مكررة', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الموظف: {str(e)}', 'error')
    
    return render_template('employees/edit.html', employee=employee, roles=EmployeeRole)

@main_bp.route('/employees/<employee_id>/delete', methods=['POST'])
@login_required
@require_permission('employees.delete')
def employees_delete(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
    except ValueError:
        flash('معرف الموظف غير صحيح', 'error')
        return redirect(url_for('main.employees_list'))
    
    # Check permissions
    if current_user.role != UserRole.GENERAL_ADMIN and employee.assigned_to_user_id != current_user.id:
        flash('غير مسموح لك بحذف هذا الموظف', 'error')
        return redirect(url_for('main.employees_list'))
    
    try:
        employee_name = employee.name
        
        # Delete employee documents first (cascade should handle this, but just in case)
        EmployeeDocument.query.filter_by(employee_id=employee.id).delete()
        
        db.session.delete(employee)
        db.session.commit()
        
        log_audit(current_user.id, AuditAction.DELETE, 'Employee', employee.id, f'تم حذف الموظف: {employee_name}', None, {'name': employee_name})
        flash('تم حذف الموظف بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الموظف: {str(e)}', 'error')
    
    return redirect(url_for('main.employees_list'))

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
@require_permission('veterinary.view')
def veterinary_list():
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        visits = VeterinaryVisit.query.filter(VeterinaryVisit.dog_id.in_(dog_ids)).order_by(VeterinaryVisit.created_at.desc()).all()
    else:
        visits = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('veterinary/list.html', visits=visits, base_template=base_template)

@main_bp.route('/veterinary/add', methods=['GET', 'POST'])
@login_required
@require_permission('veterinary.create')
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
    
    # Get scoped dogs and vets using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dogs = [d for d in scoped_dogs if d.current_status == DogStatus.ACTIVE] if scoped_dogs else []
    
    scoped_employees = get_scoped_employees()
    vets = [e for e in scoped_employees if e.role == EmployeeRole.VET and e.is_active] if scoped_employees else []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('veterinary/add.html', dogs=dogs, vets=vets, visit_types=VisitType, base_template=base_template)

# Production routes
@main_bp.route('/production')
@login_required
@admin_or_pm_required
def production_list():
    if not has_permission("production.general.view"):
        return redirect("/unauthorized")
    # Use permission-aware helper instead of role check
    all_dogs = get_user_accessible_dogs(current_user)
    assigned_dog_ids = [d.id for d in all_dogs] if all_dogs else []
    
    if assigned_dog_ids:
        cycles = ProductionCycle.query.filter(
            db.or_(ProductionCycle.female_id.in_(assigned_dog_ids), ProductionCycle.male_id.in_(assigned_dog_ids))
        ).order_by(ProductionCycle.created_at.desc()).all()
    else:
        cycles = []
    
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
    if not has_permission("production.general.create"):
        return redirect("/unauthorized")
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
    # Use permission-aware helper instead of role check
    accessible_dogs = get_user_accessible_dogs(current_user)
    all_dogs = [d for d in accessible_dogs if d.current_status == DogStatus.ACTIVE]
    
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    males = [dog for dog in all_dogs if dog.gender == DogGender.MALE]
    
    return render_template('production/add.html', females=females, males=males, cycle_types=ProductionCycleType, results=ProductionResult)

# Individual production component routes
@main_bp.route('/production/maturity')
@login_required
@admin_or_pm_required
def maturity_list():
    if not has_permission("production.maturity.list"):
        return redirect("/unauthorized")
    from k9.models.models import DogMaturity
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        maturity_records = DogMaturity.query.filter(DogMaturity.dog_id.in_(dog_ids)).order_by(DogMaturity.created_at.desc()).all()
    else:
        maturity_records = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/maturity_list.html', records=maturity_records, maturities=maturity_records, base_template=base_template)

@main_bp.route('/production/maturity/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def maturity_add():
    if not has_permission("production.maturity.create"):
        return redirect("/unauthorized")
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
            current_app.logger.error(f'Maturity add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dogs = [d for d in scoped_dogs if d.current_status == DogStatus.ACTIVE] if scoped_dogs else []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/maturity_add.html', dogs=dogs, base_template=base_template)

@main_bp.route('/production/heat-cycles')
@login_required
@admin_or_pm_required
def heat_cycles_list():
    if not has_permission("production.heat_cycles.list"):
        return redirect("/unauthorized")
    from k9.models.models import HeatCycle
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        heat_cycles = HeatCycle.query.filter(HeatCycle.dog_id.in_(dog_ids)).order_by(HeatCycle.created_at.desc()).all()
    else:
        heat_cycles = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/heat_cycles_list.html', records=heat_cycles, heat_cycles=heat_cycles, base_template=base_template)

@main_bp.route('/production/heat-cycles/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def heat_cycles_add():
    if not has_permission("production.heat_cycles.create"):
        return redirect("/unauthorized")
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
            current_app.logger.error(f'Heat cycle add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    all_dogs = [d for d in scoped_dogs if d.current_status == DogStatus.ACTIVE] if scoped_dogs else []
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/heat_cycles_add.html', females=females, base_template=base_template)

@main_bp.route('/production/mating')
@login_required
@admin_or_pm_required
def mating_list():
    if not has_permission("production.mating.list"):
        return redirect("/unauthorized")
    from k9.models.models import MatingRecord
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        mating_records = MatingRecord.query.filter(
            db.or_(MatingRecord.female_id.in_(dog_ids), MatingRecord.male_id.in_(dog_ids))
        ).order_by(MatingRecord.created_at.desc()).all()
    else:
        mating_records = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/mating_list.html', records=mating_records, matings=mating_records, base_template=base_template)

@main_bp.route('/production/mating/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def mating_add():
    if not has_permission("production.mating.create"):
        return redirect("/unauthorized")
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
            current_app.logger.error(f'Mating add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get scoped dogs and employees using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    all_dogs = [d for d in scoped_dogs if d.current_status == DogStatus.ACTIVE] if scoped_dogs else []
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    males = [dog for dog in all_dogs if dog.gender == DogGender.MALE]
    
    scoped_employees = get_scoped_employees()
    employees = [e for e in scoped_employees if e.is_active] if scoped_employees else []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/mating_add.html', females=females, males=males, employees=employees, base_template=base_template)

@main_bp.route('/production/pregnancy')
@login_required
@admin_or_pm_required
def pregnancy_list():
    if not has_permission("production.pregnancy.list"):
        return redirect("/unauthorized")
    from k9.models.models import PregnancyRecord
    
    # Get scoped dogs using PM scoping utility
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        pregnancy_records = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(dog_ids)).order_by(PregnancyRecord.created_at.desc()).all()
    else:
        pregnancy_records = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/pregnancy_list.html', pregnancies=pregnancy_records, records=pregnancy_records, base_template=base_template)

@main_bp.route('/production/pregnancy/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def pregnancy_add():
    if not has_permission("production.pregnancy.create"):
        return redirect("/unauthorized")
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
            current_app.logger.error(f'Pregnancy add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get scoped dogs and mating records using PM scoping utility
    from k9.models.models import MatingRecord
    scoped_dogs = get_scoped_dogs()
    all_dogs = [d for d in scoped_dogs if d.current_status == DogStatus.ACTIVE] if scoped_dogs else []
    females = [dog for dog in all_dogs if dog.gender == DogGender.FEMALE]
    
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    if dog_ids:
        mating_records = MatingRecord.query.filter(
            db.or_(MatingRecord.female_id.in_(dog_ids), MatingRecord.male_id.in_(dog_ids))
        ).order_by(MatingRecord.created_at.desc()).all()
    else:
        mating_records = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/pregnancy_add.html', females=females, matings=mating_records, base_template=base_template)

@main_bp.route('/production/delivery')
@login_required
@admin_or_pm_required
def delivery_list():
    if not has_permission("production.delivery.list"):
        return redirect("/unauthorized")
    from k9.models.models import DeliveryRecord
    try:
        # Get scoped dogs using PM scoping utility
        scoped_dogs = get_scoped_dogs()
        dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
        
        if dog_ids:
            delivery_records = DeliveryRecord.query.join(PregnancyRecord).filter(
                PregnancyRecord.dog_id.in_(dog_ids)
            ).order_by(DeliveryRecord.created_at.desc()).all()
        else:
            delivery_records = []
    except Exception as e:
        current_app.logger.error(f"Error fetching delivery records: {e}")
        delivery_records = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/delivery_list.html', deliveries=delivery_records, records=delivery_records, base_template=base_template)

@main_bp.route('/production/delivery/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def delivery_add():
    if not has_permission("production.delivery.create"):
        return redirect("/unauthorized")
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
            current_app.logger.error(f'Delivery add error: {e}')
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    # Get scoped dogs and employees using PM scoping utility
    from k9.models.models import PregnancyRecord, PregnancyStatus
    scoped_dogs = get_scoped_dogs()
    dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
    
    if dog_ids:
        pregnancies = PregnancyRecord.query.filter(PregnancyRecord.dog_id.in_(dog_ids), PregnancyRecord.status == PregnancyStatus.PREGNANT).order_by(PregnancyRecord.expected_delivery_date.asc()).all()
    else:
        pregnancies = []
    
    scoped_employees = get_scoped_employees()
    employees = [e for e in scoped_employees if e.is_active] if scoped_employees else []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/delivery_add.html', pregnancies=pregnancies, employees=employees, base_template=base_template)

@main_bp.route('/production/puppies')
@login_required
@admin_or_pm_required
def puppies_list():
    if not has_permission("production.puppies.list"):
        return redirect("/unauthorized")
    from k9.models.models import PuppyRecord, DeliveryRecord
    try:
        # Get scoped dogs using PM scoping utility
        scoped_dogs = get_scoped_dogs()
        dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
        
        if dog_ids:
            puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(
                PregnancyRecord.dog_id.in_(dog_ids)
            ).order_by(PuppyRecord.created_at.desc()).all()
        else:
            puppies = []
    except Exception as e:
        current_app.logger.error(f"Error fetching puppy records: {e}")
        puppies = []
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/puppies_list.html', puppies=puppies, base_template=base_template)

@main_bp.route('/production/puppies/add', methods=['GET', 'POST'])
@login_required
@admin_or_pm_required
def puppies_add():
    if not has_permission("production.puppies.create"):
        return redirect("/unauthorized")
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
    
    # Get delivery records for puppies dropdown using PM scoping utility
    from k9.models.models import DeliveryRecord, PregnancyRecord
    try:
        scoped_dogs = get_scoped_dogs()
        dog_ids = [d.id for d in scoped_dogs] if scoped_dogs else []
        
        if dog_ids:
            deliveries = DeliveryRecord.query.join(PregnancyRecord).filter(
                PregnancyRecord.dog_id.in_(dog_ids)
            ).order_by(DeliveryRecord.delivery_date.desc()).all()
        else:
            deliveries = []
    except Exception as e:
        current_app.logger.error(f"Error fetching delivery records: {e}")
        deliveries = []
    
    # Add helpful message if no delivery records exist
    if not deliveries:
        flash('لا توجد سجلات ولادة متاحة. يجب إنشاء سجلات الحمل والولادة أولاً من قسم التربية.', 'info')
    
    # Get correct base template for PM vs Admin
    base_template = get_base_template()
    
    return render_template('production/puppies_add.html', deliveries=deliveries, base_template=base_template)

# View routes for all breeding sections
@main_bp.route('/production/maturity/view/<id>')
@login_required
def maturity_view(id):
    if not has_permission("production.maturity.view"):
        return redirect("/unauthorized")
    from k9.models.models import DogMaturity
    maturity = DogMaturity.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if maturity.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/maturity_view.html', maturity=maturity)

@main_bp.route('/production/heat-cycles/view/<id>')
@login_required
def heat_cycles_view(id):
    if not has_permission("production.heat_cycles.view"):
        return redirect("/unauthorized")
    from k9.models.models import HeatCycle
    heat_cycle = HeatCycle.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if heat_cycle.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/heat_cycles_view.html', heat_cycle=heat_cycle)

@main_bp.route('/production/mating/view/<id>')
@login_required
def mating_view(id):
    if not has_permission("production.mating.view"):
        return redirect("/unauthorized")
    from k9.models.models import MatingRecord
    mating = MatingRecord.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if mating.female_id not in assigned_dog_ids and mating.male_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/mating_view.html', mating=mating)

@main_bp.route('/production/pregnancy/view/<id>')
@login_required
def pregnancy_view(id):
    if not has_permission("production.pregnancy.view"):
        return redirect("/unauthorized")
    from k9.models.models import PregnancyRecord
    pregnancy = PregnancyRecord.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if pregnancy.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/pregnancy_view.html', pregnancy=pregnancy)

@main_bp.route('/production/delivery/view/<id>')
@login_required
def delivery_view(id):
    if not has_permission("production.delivery.view"):
        return redirect("/unauthorized")
    from k9.models.models import DeliveryRecord
    delivery = DeliveryRecord.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if delivery.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/delivery_view.html', delivery=delivery)

@main_bp.route('/production/puppies/view/<id>')
@login_required
def puppies_view(id):
    if not has_permission("production.puppies.view"):
        return redirect("/unauthorized")
    from k9.models.models import PuppyRecord
    puppy = PuppyRecord.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if puppy.delivery_record.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/puppies_view.html', puppy=puppy)

@main_bp.route('/production/puppy-training')
@login_required
def puppy_training_list():
    # Get puppy training sessions - use permission-aware helper
    assigned_dogs = get_user_accessible_dogs(current_user)
    assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
    
    if assigned_dog_ids:
        sessions = PuppyTraining.query.join(PuppyRecord).join(DeliveryRecord).join(PregnancyRecord).filter(
            PregnancyRecord.dog_id.in_(assigned_dog_ids)
        ).order_by(PuppyTraining.session_date.desc()).all()
    else:
        sessions = []
    
    return render_template('production/puppy_training_list.html', sessions=sessions)

@main_bp.route('/production/puppy-training/view/<id>')
@login_required
def puppy_training_view(id):
    session = PuppyTraining.query.get_or_404(id)
    
    # Check permissions
    if not is_admin(current_user):
        assigned_dogs = get_user_accessible_dogs(current_user)
        assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
        if session.puppy.delivery_record.pregnancy_record.dog_id not in assigned_dog_ids:
            abort(403)
    
    return render_template('production/puppy_training_view.html', session=session)

@main_bp.route('/production/puppy-training/add', methods=['GET', 'POST'])
@login_required
def puppy_training_add():
    if not has_permission("training.sessions.create"):
        return redirect("/unauthorized")
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
    
    # Get puppies and trainers for puppy training - use permission-aware helpers
    assigned_dogs = get_user_accessible_dogs(current_user)
    assigned_dog_ids = [d.id for d in assigned_dogs] if assigned_dogs else []
    
    if assigned_dog_ids:
        puppies = PuppyRecord.query.join(DeliveryRecord).join(PregnancyRecord).filter(
            PregnancyRecord.dog_id.in_(assigned_dog_ids),
            PuppyRecord.alive_at_birth == True,
            PuppyRecord.current_status.notin_(['متوفي', 'مريض', 'غير صالح'])
        ).order_by(PuppyRecord.created_at.desc()).all()
    else:
        puppies = []
    
    # Get accessible trainers
    accessible_employees = get_user_accessible_employees(current_user)
    trainers = [e for e in accessible_employees if e.role == EmployeeRole.TRAINER and e.is_active]
    
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
@require_permission('projects.view')
def projects():
    # Use permission-aware helper instead of role check
    projects = get_user_assigned_projects(current_user)
    projects.sort(key=lambda x: x.created_at, reverse=True)
    
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
@require_permission('projects.create')
def project_add():
    if request.method == 'POST':
        try:
            current_app.logger.error(f"Form data: {dict(request.form)}")
            
            # التحقق من وجود البيانات المطلوبة
            if not request.form.get('name'):
                flash('اسم المشروع مطلوب', 'error')
                raise Exception("Project name is required")
            
            if not request.form.get('start_date'):
                flash('تاريخ البداية مطلوب', 'error')
                raise Exception("Start date is required")
            
            # Determine the manager ID
            manager_id = current_user.id if current_user.role == UserRole.PROJECT_MANAGER else request.form.get('manager_id')
            current_app.logger.error(f"Manager ID: {manager_id}")
            
            # Generate unique project code
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            current_app.logger.error(f"Generated code: {code}")
            
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
            project.sector = request.form.get('sector')
            
            current_app.logger.error(f"Project object created: {project.name}, {project.code}")
            
            # Validate project manager assignment if provided
            if manager_id:
                # Find the employee profile for project manager
                employee = Employee.query.get(manager_id)
                current_app.logger.error(f"Employee found: {employee}")
                
                # Check if employee is a valid project manager:
                # Either has EmployeeRole.PROJECT_MANAGER OR is linked to a User with UserRole.PROJECT_MANAGER
                is_valid_pm = False
                if employee:
                    if employee.role == EmployeeRole.PROJECT_MANAGER:
                        is_valid_pm = True
                    else:
                        # Check if linked to a User with PROJECT_MANAGER role
                        pm_user = User.query.filter_by(employee_id=employee.id, role=UserRole.PROJECT_MANAGER).first()
                        if pm_user:
                            is_valid_pm = True
                
                if is_valid_pm:
                    # Validate one-project-per-manager constraint
                    can_assign, error_msg = validate_project_manager_assignment(employee.id, project)
                    if not can_assign:
                        flash(error_msg, 'error')
                        raise Exception("Project manager assignment validation failed")
                    
                    project.project_manager_id = employee.id
                    current_app.logger.error(f"Project manager assigned: {employee.name}")
                else:
                    flash('الموظف المحدد ليس مدير مشروع صالح', 'error')
                    raise Exception("Invalid project manager")
            
            db.session.add(project)
            db.session.commit()
            
            log_audit(current_user.id, AuditAction.CREATE, 'Project', project.id, f'مشروع جديد: {project.name}', None, {'name': project.name})
            flash('تم إنشاء المشروع بنجاح', 'success')
            return redirect(url_for('main.projects'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating project: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'حدث خطأ أثناء إنشاء المشروع: {str(e)}', 'error')
    
    # Get available data for the form
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Get employees who are linked to Users with PROJECT_MANAGER role
        # OR employees with EmployeeRole.PROJECT_MANAGER
        # AND are NOT already assigned to any active/planned projects
        subquery = db.session.query(Project.project_manager_id).filter(
            Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED]),
            Project.project_manager_id.isnot(None)
        ).subquery()
        
        # Find employees linked to users with PROJECT_MANAGER role
        pm_user_employees = db.session.query(User.employee_id).filter(
            User.role == UserRole.PROJECT_MANAGER,
            User.employee_id.isnot(None)
        ).subquery()
        
        # Get employees that are either:
        # 1. Linked to a User with PROJECT_MANAGER role, OR
        # 2. Have EmployeeRole.PROJECT_MANAGER
        # AND are active AND not already assigned to active/planned projects
        managers = Employee.query.filter(
            Employee.is_active == True,
            db.or_(
                Employee.id.in_(db.session.query(pm_user_employees.c.employee_id)),
                Employee.role == EmployeeRole.PROJECT_MANAGER
            ),
            ~Employee.id.in_(db.session.query(subquery.c.project_manager_id))
        ).all()
    else:
        managers = []  # PROJECT_MANAGER users can only assign to themselves
    
    return render_template('projects/add.html', managers=managers)

@main_bp.route('/projects/<project_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_edit(project_id):
    """Edit project details"""
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            # Update project details
            project.name = request.form['name']
            project.description = request.form.get('description')
            project.main_task = request.form.get('main_task')
            project.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            project.expected_completion_date = datetime.strptime(request.form['expected_completion_date'], '%Y-%m-%d').date() if request.form.get('expected_completion_date') else None
            project.location = request.form.get('location')
            project.mission_type = request.form.get('mission_type')
            project.priority = request.form.get('priority', 'MEDIUM')
            project.sector = request.form.get('sector')
            
            # Update project manager if admin is editing
            if current_user.role == UserRole.GENERAL_ADMIN:
                manager_id = request.form.get('manager_id')
                if manager_id:
                    employee = Employee.query.get(manager_id)
                    # Check if employee is a valid project manager
                    is_valid_pm = False
                    if employee:
                        if employee.role == EmployeeRole.PROJECT_MANAGER:
                            is_valid_pm = True
                        else:
                            # Check if linked to a User with PROJECT_MANAGER role
                            pm_user = User.query.filter_by(employee_id=employee.id, role=UserRole.PROJECT_MANAGER).first()
                            if pm_user:
                                is_valid_pm = True
                    
                    if is_valid_pm:
                        # Validate one-project-per-manager constraint
                        can_assign, error_msg = validate_project_manager_assignment(employee.id, project)
                        if not can_assign:
                            flash(error_msg, 'error')
                            raise Exception("Project manager assignment validation failed")
                        project.project_manager_id = employee.id
                    else:
                        flash('الموظف المحدد ليس مدير مشروع صالح', 'error')
                        raise Exception("Invalid project manager")
                elif request.form.get('remove_manager') == 'yes':
                    project.project_manager_id = None
            
            db.session.commit()
            log_audit(current_user.id, AuditAction.UPDATE, 'Project', project.id, f'تحديث المشروع: {project.name}', None, {'name': project.name})
            flash('تم تحديث المشروع بنجاح', 'success')
            return redirect(url_for('main.project_edit', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث المشروع: {str(e)}', 'error')
    
    # Get project locations
    locations = ProjectLocation.query.filter_by(project_id=project.id).all()
    
    # Get available managers for admin
    if current_user.role == UserRole.GENERAL_ADMIN:
        # Get only project managers who are NOT assigned to any active/planned projects
        # OR the current project manager
        subquery = db.session.query(Project.project_manager_id).filter(
            Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNED]),
            Project.id != project.id,  # Exclude current project
            Project.project_manager_id.isnot(None)
        ).subquery()
        
        # Find employees linked to users with PROJECT_MANAGER role
        pm_user_employees = db.session.query(User.employee_id).filter(
            User.role == UserRole.PROJECT_MANAGER,
            User.employee_id.isnot(None)
        ).subquery()
        
        # Get employees that are either:
        # 1. Linked to a User with PROJECT_MANAGER role, OR
        # 2. Have EmployeeRole.PROJECT_MANAGER
        # AND are active AND not already assigned to active/planned projects
        managers = Employee.query.filter(
            Employee.is_active == True,
            db.or_(
                Employee.id.in_(db.session.query(pm_user_employees.c.employee_id)),
                Employee.role == EmployeeRole.PROJECT_MANAGER
            ),
            ~Employee.id.in_(db.session.query(subquery.c.project_manager_id))
        ).all()
        
        # Add current project manager if exists and not in list
        if project.project_manager and project.project_manager not in managers:
            managers.insert(0, project.project_manager)
    else:
        managers = []
    
    return render_template('projects/edit.html', project=project, locations=locations, managers=managers)

# Project Dashboard Route (without attendance statistics)
@main_bp.route('/projects/<project_id>/dashboard')
@login_required
@require_permission('projects.view')
def project_dashboard(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_status_change(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.delete')
def project_delete(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
        incidents_count = Incident.query.filter_by(project_id=project.id).count()
        suspicions_count = Suspicion.query.filter_by(project_id=project.id).count()
        evaluations_count = PerformanceEvaluation.query.filter_by(project_id=project.id).count()
        
        total_related = dogs_count + assignments_count + incidents_count + suspicions_count + evaluations_count
        
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
@require_permission('projects.edit')
def project_dog_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_manager_update(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
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
@require_permission('projects.view')
def project_assignments(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_assignment_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_assignment_remove(project_id, assignment_id):
    try:
        project_id = project_id
        assignment_id = assignment_id
        project = Project.query.get_or_404(project_id)
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_assignment_edit(project_id, assignment_id):
    try:
        project_id = project_id
        assignment_id = assignment_id
        project = Project.query.get_or_404(project_id)
        assignment = ProjectAssignment.query.get_or_404(assignment_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
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
@require_permission('projects.view')
def project_incidents(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    incidents = Incident.query.filter_by(project_id=project.id).order_by(Incident.incident_date.desc()).all()
    
    return render_template('projects/incidents.html', project=project, incidents=incidents)

@main_bp.route('/projects/<project_id>/incidents/add', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_incident_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.edit')
def project_resolve_incident(project_id):
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.view')
def project_suspicions(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    suspicions = Suspicion.query.filter_by(project_id=project.id).order_by(Suspicion.discovery_date.desc()).all()
    
    return render_template('projects/suspicions.html', project=project, suspicions=suspicions)

@main_bp.route('/projects/<project_id>/suspicions/add', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_suspicion_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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
@require_permission('projects.view')
def project_evaluations(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    evaluations = PerformanceEvaluation.query.filter_by(project_id=project.id).order_by(PerformanceEvaluation.evaluation_date.desc()).all()
    
    return render_template('projects/evaluations.html', project=project, evaluations=evaluations)

@main_bp.route('/projects/<project_id>/evaluations/add', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_evaluation_add(project_id):
    try:
        project_id = project_id
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
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

@main_bp.route('/reports/generate', methods=['POST'])
@login_required
def reports_generate():
    """
    Generate a report based on type, optional date range and optional filters.
    Supported report types: 'dogs', 'employees', 'training', 'veterinary',
                            'breeding', 'projects',
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
            elif report_type in ['training_trainer_daily']:
                # For daily reports, redirect to training
                pdf_report_type = 'training'
            else:
                pdf_report_type = report_type
            
            filename = generate_pdf_report(pdf_report_type, start_date, end_date, current_user, filters)
        
        upload_dir = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_dir, filename, as_attachment=True)
    except Exception as e:
        flash(f'تعذّر إنشاء التقرير: {str(e)}', 'error')
        return redirect(url_for('main.reports_hub'))

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
    
    # New report types for daily reports
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
    if not is_admin(current_user):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        project_id = request.args.get('project_id')
        project_id = project_id if project_id and project_id.strip() else None
        
        from k9.utils.permissions_new import get_user_permission_keys
        permissions = list(get_user_permission_keys(user_id))
        
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
    if not is_admin(current_user):
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
        
        from k9.utils.permissions_new import grant_permission, revoke_permission
        
        update_count = 0
        
        # Update each permission using the new system
        for permission_key, is_granted in permissions.items():
            try:
                if is_granted:
                    success = grant_permission(str(target_user.id), permission_key, str(current_user.id))
                else:
                    success = revoke_permission(str(target_user.id), permission_key, str(current_user.id))
                if success:
                    update_count += 1
            except Exception:
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
    if not is_admin(current_user):
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
    if not is_admin(current_user):
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
        if user.employee:
            user.employee.name = full_name
            user.employee.email = email
        
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

@main_bp.route('/admin/permissions/update-legacy', methods=['POST'])
@login_required
def update_permissions_legacy():
    """Update PROJECT_MANAGER permissions (Legacy route - use comprehensive permissions instead)"""
    from k9.models.models import ProjectManagerPermission
    
    # Check admin access
    if not is_admin(current_user):
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
    if not is_admin(current_user):
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
@require_permission('employees.edit')
def employee_user_links():
    """Manage links between employees and user accounts"""
    # Get all employees with their linked user accounts
    employees = Employee.query.order_by(Employee.name).all()
    
    # Get all handler users (for linking)
    handler_users = User.query.filter_by(role=UserRole.HANDLER).order_by(User.full_name).all()
    
    # Get unlinked employees
    unlinked_employees = Employee.query.filter(
        ~Employee.id.in_(db.session.query(User.employee_id).filter(User.employee_id.isnot(None)))
    ).all()
    
    # Get unlinked users
    unlinked_users = User.query.filter(
        User.role == UserRole.HANDLER,
        User.employee_id.is_(None)
    ).all()
    
    return render_template('admin/employee_user_links.html',
                         employees=employees,
                         handler_users=handler_users,
                         unlinked_employees=unlinked_employees,
                         unlinked_users=unlinked_users)

@main_bp.route('/admin/employee-user-links/link', methods=['POST'])
@login_required
@require_permission('employees.edit')
def link_employee_to_user():
    """Link an employee to a user account"""
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
        existing_link = user.employee
        if existing_link and str(existing_link.id) != str(employee_id):
            return jsonify({'success': False, 'error': f'المستخدم مرتبط بالفعل بالموظف: {existing_link.name}'})
        
        # Create the link
        user.employee_id = employee.id
        
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
@require_permission('employees.edit')
def unlink_employee_from_user():
    """Unlink an employee from a user account"""
    try:
        employee_id = request.form.get('employee_id')
        
        if not employee_id:
            return jsonify({'success': False, 'error': 'يجب تحديد الموظف'})
        
        employee = Employee.query.get(employee_id)
        
        if not employee:
            return jsonify({'success': False, 'error': 'الموظف غير موجود'})
        
        if employee.user_account is None:
            return jsonify({'success': False, 'error': 'الموظف غير مرتبط بأي حساب'})
        
        old_user = employee.user_account
        old_username = old_user.username if old_user else 'Unknown'
        
        # Remove the link
        if old_user:
            old_user.employee_id = None
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

# =============================================
# BREEDING SECTION ROUTES (Arabic RTL)
# =============================================

from sqlalchemy.orm import joinedload

@main_bp.route('/breeding/feeding/log')
@login_required
def breeding_feeding_log():
    """Feeding Log main page (Arabic RTL)"""
    if not has_permission("breeding.feeding_log.view"):
        return redirect("/unauthorized")
    
    return render_template('breeding/feeding_log.html')

@main_bp.route('/breeding/feeding/log/new')
@login_required
def breeding_feeding_log_new():
    """Create new feeding log entry"""
    if not has_permission("breeding.feeding_log.create"):
        return redirect("/unauthorized")
    
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
    if not has_permission("breeding.feeding_log.edit"):
        return redirect("/unauthorized")
    
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
@require_permission('breeding.checkup')
def breeding_checkup():
    """List daily checkup records"""
    if not has_permission("breeding.checkup.view"):
        return redirect("/unauthorized")
    return render_template('breeding/checkup_list.html')

@main_bp.route('/breeding/checkup/new')
@login_required
@require_permission('breeding.checkup')
def breeding_checkup_new():
    """Create new daily checkup record"""
    if not has_permission("breeding.checkup.create"):
        return redirect("/unauthorized")
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
@require_permission('breeding.checkup')
def breeding_checkup_edit(id):
    """Edit daily checkup record"""
    if not has_permission("breeding.checkup.edit"):
        return redirect("/unauthorized")
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
@require_permission('breeding.excretion')
def breeding_excretion():
    """List excretion logs"""
    if not has_permission("breeding.excretion.view"):
        return redirect("/unauthorized")
    return render_template('breeding/excretion_list.html')

@main_bp.route('/breeding/excretion/new')
@login_required
@require_permission('breeding.excretion')
def breeding_excretion_new():
    """Create new excretion log entry"""
    if not has_permission("breeding.excretion.create"):
        return redirect("/unauthorized")
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
@require_permission('breeding.excretion')
def breeding_excretion_edit(id):
    """Edit excretion log record"""
    if not has_permission("breeding.excretion.edit"):
        return redirect("/unauthorized")
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
# @require_permission('breeding.excretion')
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
@require_permission('breeding.grooming')
def breeding_grooming():
    """Grooming care main page"""
    if not has_permission("breeding.grooming.view"):
        return redirect("/unauthorized")
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
@require_permission('breeding.grooming')
def breeding_grooming_new():
    """Create new grooming log entry"""
    if not has_permission("breeding.grooming.create"):
        return redirect("/unauthorized")
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
@require_permission('breeding.grooming')
def breeding_grooming_edit(id):
    """Edit existing grooming log entry"""
    if not has_permission("breeding.grooming.edit"):
        return redirect("/unauthorized")
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
@require_permission('breeding.cleaning')
def cleaning_list():
    """Cleaning logs main page"""
    if not has_permission("breeding.cleaning.view"):
        return redirect("/unauthorized")
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
@require_permission('breeding.cleaning')
def cleaning_new():
    """Create new cleaning log entry"""
    if not has_permission("breeding.cleaning.create"):
        return redirect("/unauthorized")
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
@require_permission('breeding.cleaning')
def cleaning_edit(id):
    """Edit existing cleaning log entry"""
    if not has_permission("breeding.cleaning.edit"):
        return redirect("/unauthorized")
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
@require_permission('breeding.feeding')
def breeding_feeding():
    """Feeding logs main page"""
    if not has_permission("breeding.feeding.view"):
        return redirect("/unauthorized")
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
@require_permission('breeding.feeding')
def breeding_feeding_new():
    """Create new feeding log entry"""
    if not has_permission("breeding.feeding.create"):
        return redirect("/unauthorized")
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
@require_permission('breeding.feeding')
def breeding_feeding_edit(id):
    """Edit existing feeding log entry"""
    if not has_permission("breeding.feeding.edit"):
        return redirect("/unauthorized")
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
    if not has_permission("breeding.deworming.view"):
        return redirect("/unauthorized")
    
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
    if not has_permission("breeding.deworming.create"):
        return redirect("/unauthorized")
        
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
    if not has_permission("breeding.deworming.edit"):
        return redirect("/unauthorized")
    from k9.models.models import DewormingLog, Employee, Dog, Route, Unit, Reaction
    
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
    if not has_permission("training.sessions.view"):
        return redirect("/unauthorized")
    
    from k9.utils.utils import get_user_assigned_projects
    assigned_projects = get_user_assigned_projects(current_user)
    
    return render_template('breeding/training_activity_list.html',
                          assigned_projects=assigned_projects)

@main_bp.route('/breeding/training-activity/new')
@login_required
def breeding_training_activity_new():
    """Add new training activity"""
    if not has_permission('training.create'):
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
    
    if not has_permission('training.edit'):
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
    if not has_permission("search.global.access"):
        return redirect("/unauthorized")
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


# ============================================================================
# Project Locations Management Routes
# ============================================================================

@main_bp.route('/projects/<project_id>/locations')
@login_required
@require_permission('projects.view')
def project_locations(project_id):
    """View all locations for a project"""
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Get all locations for this project
    locations = ProjectLocation.query.filter_by(project_id=project.id).order_by(ProjectLocation.created_at.desc()).all()
    
    return render_template('projects/locations.html',
                         project=project,
                         locations=locations)


@main_bp.route('/projects/<project_id>/locations/add', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_location_add(project_id):
    """Add a new location to a project"""
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف المشروع غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            if not name:
                flash('اسم الموقع مطلوب', 'error')
                return render_template('projects/location_add.html', project=project)
            
            location = ProjectLocation()
            location.project_id = project.id
            location.name = name
            location.description = description
            
            db.session.add(location)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'ProjectLocation', str(location.id), 
                     {'project_id': str(project.id), 'name': name})
            
            flash('تم إضافة الموقع بنجاح', 'success')
            return redirect(url_for('main.project_locations', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الموقع: {str(e)}', 'error')
    
    return render_template('projects/location_add.html', project=project)


@main_bp.route('/projects/<project_id>/locations/<location_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('projects.edit')
def project_location_edit(project_id, location_id):
    """Edit a project location"""
    try:
        project = Project.query.get_or_404(project_id)
        location = ProjectLocation.query.get_or_404(location_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Verify location belongs to project
    if location.project_id != project.id:
        flash('الموقع غير تابع لهذا المشروع', 'error')
        return redirect(url_for('main.project_locations', project_id=project.id))
    
    if request.method == 'POST':
        try:
            old_name = location.name
            name = request.form.get('name')
            description = request.form.get('description')
            
            if not name:
                flash('اسم الموقع مطلوب', 'error')
                return render_template('projects/location_edit.html', project=project, location=location)
            
            location.name = name
            location.description = description
            
            db.session.commit()
            
            log_audit(current_user.id, 'UPDATE', 'ProjectLocation', str(location.id), 
                     {'old_name': old_name, 'new_name': name})
            
            flash('تم تحديث الموقع بنجاح', 'success')
            return redirect(url_for('main.project_locations', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث الموقع: {str(e)}', 'error')
    
    return render_template('projects/location_edit.html', project=project, location=location)


@main_bp.route('/projects/<project_id>/locations/<location_id>/delete', methods=['POST'])
@login_required
@require_permission('projects.edit')
def project_location_delete(project_id, location_id):
    """Delete a project location"""
    try:
        project = Project.query.get_or_404(project_id)
        location = ProjectLocation.query.get_or_404(location_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    # Verify location belongs to project
    if location.project_id != project.id:
        flash('الموقع غير تابع لهذا المشروع', 'error')
        return redirect(url_for('main.project_locations', project_id=project.id))
    
    try:
        location_name = location.name
        db.session.delete(location)
        db.session.commit()
        
        log_audit(current_user.id, 'DELETE', 'ProjectLocation', str(location_id), 
                 {'name': location_name, 'project_id': str(project.id)})
        
        flash('تم حذف الموقع بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الموقع: {str(e)}', 'error')
    
    return redirect(url_for('main.project_locations', project_id=project.id))


@main_bp.route('/projects/<project_id>/shifts', methods=['GET', 'POST'])
@login_required
@require_permission('projects.view')
def project_shifts(project_id):
    """View and manage system-wide shifts (shifts are shared across all projects)"""
    try:
        project = Project.query.get_or_404(project_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    if request.method == 'POST':
        if current_user.role != UserRole.GENERAL_ADMIN:
            flash('فقط المسؤول العام يمكنه إضافة ورديات جديدة', 'error')
            return redirect(url_for('main.project_shifts', project_id=project.id))
        
        try:
            name = request.form.get('name')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            
            if not all([name, start_time, end_time]):
                flash('جميع الحقول مطلوبة', 'error')
                return redirect(url_for('main.project_shifts', project_id=project.id))
            
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            if start_time_obj >= end_time_obj:
                flash('وقت البداية يجب أن يكون قبل وقت النهاية', 'error')
                return redirect(url_for('main.project_shifts', project_id=project.id))
            
            shift = Shift(
                name=name,
                start_time=start_time_obj,
                end_time=end_time_obj,
                is_active=True
            )
            
            db.session.add(shift)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE', 'Shift', str(shift.id), 
                     {'name': name, 'start_time': start_time, 'end_time': end_time})
            
            flash('تم إضافة الوردية بنجاح', 'success')
            return redirect(url_for('main.project_shifts', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الوردية: {str(e)}', 'error')
    
    if current_user.role == UserRole.GENERAL_ADMIN:
        shifts = Shift.query.order_by(Shift.start_time).all()
    else:
        shifts = Shift.query.filter_by(is_active=True).order_by(Shift.start_time).all()
    
    return render_template('projects/shifts.html', project=project, shifts=shifts)


@main_bp.route('/projects/<project_id>/shifts/<shift_id>', methods=['GET'])
@login_required
@require_permission('projects.view')
def shift_assignments(project_id, shift_id):
    """View shift details and redirect to daily scheduling"""
    try:
        project = Project.query.get_or_404(project_id)
        shift = Shift.query.get_or_404(shift_id)
    except ValueError:
        flash('معرف غير صحيح', 'error')
        return redirect(url_for('main.projects'))
    
    from k9.models.models_handler_daily import DailyScheduleItem, DailySchedule
    
    recent_assignments = db.session.query(DailyScheduleItem).join(
        DailySchedule
    ).filter(
        DailySchedule.project_id == project.id,
        DailyScheduleItem.shift_id == shift.id
    ).order_by(DailySchedule.date.desc()).limit(20).all()
    
    project_users = User.query.join(Employee).join(project_employee_assignment).filter(
        project_employee_assignment.c.project_id == project.id,
        Employee.is_active == True,
        User.role == UserRole.HANDLER
    ).all()
    
    project_dogs = Dog.query.join(ProjectDog).filter(
        ProjectDog.project_id == project.id,
        ProjectDog.is_active == True
    ).all()
    
    return render_template('projects/shift_assignments.html', 
                         project=project, 
                         shift=shift,
                         employees=project_users,
                         dogs=project_dogs,
                         assignments=recent_assignments)


@main_bp.route('/projects/<project_id>/shifts/<shift_id>/toggle', methods=['POST'])
@login_required
@require_permission('projects.edit')
def toggle_shift(project_id, shift_id):
    """Toggle shift active status (admin only)"""
    
    try:
        project = Project.query.get_or_404(project_id)
        shift = Shift.query.get_or_404(shift_id)
        
        shift.is_active = not shift.is_active
        db.session.commit()
        
        log_audit(current_user.id, 'UPDATE', 'Shift', str(shift.id), 
                 {'action': 'toggle_active', 'new_status': shift.is_active})
        
        status = 'تم تفعيل' if shift.is_active else 'تم تعطيل'
        flash(f'{status} الوردية بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('main.project_shifts', project_id=project_id))

