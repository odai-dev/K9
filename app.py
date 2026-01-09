import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging based on environment
flask_env = os.environ.get("FLASK_ENV", "development")
if flask_env == "production":
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# Create the app
app = Flask(__name__, template_folder='k9/templates', static_folder='k9/static')
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    if flask_env == "production":
        raise RuntimeError(
            "SESSION_SECRET environment variable is required in production. "
            "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    else:
        # For local development only, provide a fallback
        import secrets
        app.secret_key = secrets.token_urlsafe(32)
        print("WARNING: SESSION_SECRET not set. Using temporary session key.")
        print("Set SESSION_SECRET environment variable for production!")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# CSRF configuration - configured later after environment check
# Enhanced security configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
app.config['WTF_CSRF_SSL_STRICT'] = True if flask_env == "production" else False  # Enable SSL strict in production
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Configure database - enforce PostgreSQL in production
database_url = os.environ.get("DATABASE_URL")
flask_env = os.environ.get("FLASK_ENV", "development")

if flask_env == "production":
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required in production. "
            "Please set it to a PostgreSQL connection string."
        )
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError(
            "Production environment requires PostgreSQL database. "
            f"Got: {database_url[:20]}..."
        )
    # Ensure postgresql:// prefix for compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
else:
    # Development/Replit environment: use PostgreSQL if available, SQLite as fallback
    if not database_url:
        database_url = 'sqlite:///k9_operations.db'

# Configure engine options based on database type
if database_url.startswith(("postgresql://", "postgres://")):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "client_encoding": "utf8"
        }
    }
else:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Security settings for session cookies
# Replit uses HTTPS and iframes, so we need SameSite=None for cookies to work
if flask_env == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "None"
else:
    # For Replit development, use HTTPS-compatible settings for iframe
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "None"

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)

# CSRF error handler for JSON API endpoints
from flask_wtf.csrf import CSRFError
from flask import request, jsonify, abort

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors with JSON response for API calls"""
    # Check if this is an API/JSON request
    if request.path.startswith('/admin/permissions/') or request.is_json or request.accept_mimetypes.accept_json:
        return jsonify({
            'success': False,
            'error': 'رمز الحماية (CSRF) غير صالح. يرجى إعادة تحميل الصفحة والمحاولة مرة أخرى.',
            'csrf_error': str(e.description)
        }), 400
    
    # For regular form submissions, use default behavior
    abort(400, description=e.description)

# Login manager configuration
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import k9.models.models  # noqa: F401
    import k9.models.models_handler_daily  # noqa: F401
    import k9.models.permissions_new  # noqa: F401
    import k9.models.permissions_v2  # noqa: F401 - New permission system

    # Bootstrap database on fresh import - creates all tables
    # For production, use migrations instead (flask db upgrade)
    if flask_env != "production":
        try:
            db.create_all()
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
    else:
        print("✓ Production mode: Using migrations for database schema (flask db upgrade)")
    
    # CRITICAL: Auto-seed permissions on every startup
    # Permissions are the foundation of the system and must NEVER be empty
    try:
        from k9.utils.permission_seeder import ensure_permissions_exist
        from k9.models.permissions_new import Permission
        ensure_permissions_exist(db, Permission)
    except Exception as e:
        print(f"⚠ Warning: Could not auto-seed permissions: {e}")
    
    # Initialize V2 Permission System (new role-based system)
    try:
        from k9.services.permission_service import init_permission_context_processor, seed_default_roles
        from k9.utils.permissions_v2_migration import run_migration_if_needed
        
        # Seed default roles
        seed_default_roles()
        print("✓ V2 Permission roles seeded successfully")
        
        # Run migration for existing users if needed
        run_migration_if_needed()
        print("✓ V2 Permission migration check completed")
        
        # Register context processor for templates
        init_permission_context_processor(app)
        print("✓ V2 Permission context processor registered")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize V2 permissions: {e}")
    
    # User creation is handled via migrations and manual setup
    # No automatic user creation during app initialization

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from k9.models.models import User
        import uuid
        
        # Validate that user_id is a valid UUID
        try:
            uuid.UUID(str(user_id))
            return User.query.get(user_id)
        except (ValueError, TypeError):
            # Invalid UUID format, return None
            return None
    
    # Register template functions
    from k9.utils.utils import get_user_permissions
    from k9.utils.pm_scoping import is_admin
    from k9.utils.permissions_new import has_permission as _has_permission_new, has_any_permission, has_all_permissions, _is_admin_mode
    from k9.utils.permissions_new import get_sections_for_user
    from datetime import date, datetime
    
    # Permission key mapping: old format -> new format
    PERMISSION_KEY_MAP = {
        # Dogs
        'dogs.management.view': 'dogs.view',
        'dogs.management.create': 'dogs.create',
        'dogs.management.edit': 'dogs.edit',
        'dogs.management.delete': 'dogs.delete',
        'dogs.assignment.manage': 'dogs.assign',
        # Employees
        'employees.management.view': 'employees.view',
        'employees.management.create': 'employees.create',
        'employees.management.edit': 'employees.edit',
        'employees.management.delete': 'employees.delete',
        'employees.assignment.manage': 'employees.assign',
        # Projects
        'projects.management.view': 'projects.view',
        'projects.management.create': 'projects.create',
        'projects.management.edit': 'projects.edit',
        'projects.management.delete': 'projects.delete',
        # Training
        'training.view_sessions.view': 'training.view',
        'training.manage_sessions.create': 'training.create',
        'training.manage_sessions.edit': 'training.edit',
        'training.manage_sessions.delete': 'training.delete',
        'training.reports.view': 'training.reports',
        # Veterinary
        'veterinary.visits.view': 'veterinary.view',
        'veterinary.visits.create': 'veterinary.create',
        'veterinary.visits.edit': 'veterinary.edit',
        'veterinary.visits.delete': 'veterinary.delete',
        'veterinary.history.view': 'veterinary.history',
        # Breeding
        'breeding.feeding.view': 'breeding.feeding',
        'breeding.checkup.view': 'breeding.checkup',
        'breeding.excretion.view': 'breeding.excretion',
        'breeding.grooming.view': 'breeding.grooming',
        'breeding.deworming.view': 'breeding.deworming',
        'breeding.cleaning.view': 'breeding.cleaning',
        # Production
        'production.breeding.view': 'production.view',
        'production.breeding.manage': 'production.manage',
        'production.puppies.view': 'production.puppies',
        'production.puppies.manage': 'production.manage_puppies',
        'production.statistics.view': 'production.statistics',
        # Shifts
        'shifts.management.view': 'shifts.view',
        'shifts.management.create': 'shifts.create',
        'shifts.management.edit': 'shifts.edit',
        'shifts.management.delete': 'shifts.delete',
        # Schedule
        'schedule.management.view': 'schedule.view',
        'schedule.management.create': 'schedule.create',
        'schedule.management.edit': 'schedule.edit',
        'schedule.management.delete': 'schedule.delete',
        'schedule.management.export': 'schedule.export',
        # Tasks
        'tasks.management.view': 'tasks.view',
        'tasks.management.create': 'tasks.create',
        'tasks.management.edit': 'tasks.edit',
        'tasks.management.delete': 'tasks.delete',
        'tasks.assignment.manage': 'tasks.assign',
        'tasks.completion.manage': 'tasks.complete',
        # Incidents
        'incidents.management.view': 'incidents.view',
        'incidents.management.create': 'incidents.create',
        'incidents.management.edit': 'incidents.edit',
        'incidents.management.delete': 'incidents.delete',
        # Reports
        'reports.attendance.view': 'reports.attendance.view',
        'reports.attendance.export': 'reports.attendance.export',
        'reports.training.view': 'reports.training.view',
        'reports.training.export': 'reports.training.export',
        'reports.veterinary.unified.view': 'reports.veterinary.view',
        'reports.veterinary.unified.export': 'reports.veterinary.export',
        'reports.breeding.feeding.unified.view': 'reports.breeding.feeding.view',
        'reports.breeding.feeding.unified.export': 'reports.breeding.feeding.export',
        'reports.breeding.checkup.unified.view': 'reports.breeding.checkup.view',
        'reports.breeding.checkup.unified.export': 'reports.breeding.checkup.export',
        'reports.caretaker_daily.view': 'reports.caretaker.view',
        'reports.caretaker_daily.export': 'reports.caretaker.export',
        'reports.general.view': 'reports.general.view',
        # Admin
        'admin.panel.access': 'admin.access',
        'admin.users.view': 'admin.users.view',
        'admin.users.manage': 'admin.users.manage',
        'admin.permissions.view': 'admin.permissions.view',
        'admin.permissions.manage': 'admin.permissions.manage',
        'admin.backup.manage': 'admin.backup',
        # Handler reports
        'handler.daily_report.view': 'handler_reports.view',
        'handler.daily_report.create': 'handler_reports.create',
        'handler.daily_report.edit': 'handler_reports.edit',
        'handler.daily_report.review': 'handler_reports.review',
        # Supervisor
        'supervisor.dashboard.view': 'supervisor.dashboard',
        'supervisor.reports.review': 'supervisor.review',
        'supervisor.team.manage': 'supervisor.team',
        # PM
        'pm.dashboard.view': 'pm.dashboard',
        'pm.reports.review': 'pm.review',
        'pm.team.manage': 'pm.team',
        'pm.project.manage': 'pm.project',
        'pm.approval.final': 'pm.approve',
        # Accounts
        'accounts.view': 'accounts.view',
        'accounts.create': 'accounts.create',
        'accounts.edit': 'accounts.edit',
        'accounts.delete': 'accounts.delete',
        # Notifications
        'notifications.view': 'notifications.view',
        'notifications.manage': 'notifications.manage',
    }
    
    def has_permission(first_arg, second_arg=None):
        """
        Template-compatible permission check wrapper.
        Uses V2 PermissionService for role-based access control.
        
        Handles both old format: has_permission(user, 'old.key')
        And new format: has_permission('new.key')
        """
        from flask_login import current_user
        from k9.services.permission_service import PermissionService
        
        # Determine which format is being used
        if second_arg is not None:
            # Old format: has_permission(user, key)
            user = first_arg
            permission_key = second_arg
        else:
            # New format: has_permission(key)
            user = current_user
            permission_key = first_arg
        
        # Check if user is authenticated
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return False
        
        # Map old key to new V2 key format if needed
        mapped_key = PERMISSION_KEY_MAP.get(permission_key, permission_key)
        
        # Use V2 PermissionService for role-based check
        return PermissionService.has_permission(user.id, mapped_key)
    
    def get_notification_link(notification):
        """Generate direct link for notification based on related_type and related_id"""
        from flask import url_for
        from k9.models.models_handler_daily import NotificationType
        
        if not notification.related_type or not notification.related_id:
            return '#'
        
        if notification.related_type == 'HandlerReport':
            # Direct link to specific report
            return url_for('supervisor.report_view', report_id=notification.related_id)
        elif notification.related_type == 'DailySchedule':
            # Direct link to specific schedule  
            return url_for('supervisor.schedule_view', schedule_id=notification.related_id)
        elif notification.related_type == 'DailyScheduleItem':
            # Link to handler's schedule
            return url_for('handler.dashboard')
        
        return '#'
    
    def get_pending_reports_count():
        """Get count of pending handler reports for users with any permissions"""
        from flask_login import current_user
        from k9.models.models_handler_daily import HandlerReport, ReportStatus
        
        if not current_user.is_authenticated:
            return 0
        
        # Check if user has any operational permissions
        user_sections = get_sections_for_user(current_user)
        if not user_sections:
            return 0
        
        try:
            # Count submitted reports (pending review)
            count = HandlerReport.query.filter_by(status=ReportStatus.SUBMITTED).count()
            return count
        except Exception:
            return 0
    
    def get_pm_pending_count():
        """Get total count of all pending approvals for users with operational permissions"""
        from flask_login import current_user
        from k9.models.models import Project, VeterinaryVisit, BreedingTrainingActivity, CaretakerDailyLog, WorkflowStatus, ProjectDog
        from k9.models.models_handler_daily import HandlerReport, ReportStatus
        
        if not current_user.is_authenticated:
            return 0
        
        # Check if user has any operational permissions
        user_sections = get_sections_for_user(current_user)
        if not user_sections:
            return 0
        
        try:
            # Find PM's project
            project = Project.query.filter_by(manager_id=current_user.id).first()
            if not project:
                return 0
            
            # Get project's dog IDs
            project_dogs = ProjectDog.query.filter_by(project_id=project.id, is_active=True).all()
            dog_ids = [pd.dog_id for pd in project_dogs]
            
            total = 0
            
            # Handler reports
            total += HandlerReport.query.filter_by(
                project_id=project.id,
                status=ReportStatus.SUBMITTED
            ).count()
            
            if dog_ids:
                # Vet visits
                total += VeterinaryVisit.query.filter(
                    VeterinaryVisit.dog_id.in_(dog_ids),
                    VeterinaryVisit.status == WorkflowStatus.PENDING_PM_REVIEW.value
                ).count()
                
                # Breeding activities
                total += BreedingTrainingActivity.query.filter(
                    BreedingTrainingActivity.dog_id.in_(dog_ids),
                    BreedingTrainingActivity.status == WorkflowStatus.PENDING_PM_REVIEW.value
                ).count()
                
                # Caretaker logs
                total += CaretakerDailyLog.query.filter(
                    CaretakerDailyLog.dog_id.in_(dog_ids),
                    CaretakerDailyLog.status == WorkflowStatus.PENDING_PM_REVIEW.value
                ).count()
            
            return total
        except Exception:
            return 0
    
    # V2 Permission helper wrappers for templates
    def has_any_permission_v2(*permission_keys):
        """Check if current user has any of the specified permissions"""
        from flask_login import current_user
        from k9.services.permission_service import PermissionService
        if not current_user.is_authenticated:
            return False
        return PermissionService.has_any_permission(current_user.id, list(permission_keys))
    
    def has_all_permissions_v2(*permission_keys):
        """Check if current user has all specified permissions"""
        from flask_login import current_user
        from k9.services.permission_service import PermissionService
        if not current_user.is_authenticated:
            return False
        return PermissionService.has_all_permissions(current_user.id, list(permission_keys))
    
    def is_admin_v2():
        """Check if current user is an admin using V2 system"""
        from flask_login import current_user
        from k9.services.permission_service import PermissionService
        if not current_user.is_authenticated:
            return False
        return PermissionService.is_admin(current_user.id)
    
    def has_role_v2(role_name, project_id=None):
        """Check if current user has a specific role"""
        from flask_login import current_user
        from k9.services.permission_service import PermissionService
        if not current_user.is_authenticated:
            return False
        return PermissionService.has_role(current_user.id, role_name, project_id)
    
    # Import V2 permission types for templates
    from k9.models.permissions_v2 import RoleType, PermissionKey
    
    app.jinja_env.globals.update(
        get_user_permissions=get_user_permissions,
        get_notification_link=get_notification_link,
        get_pending_reports_count=get_pending_reports_count,
        get_pm_pending_count=get_pm_pending_count,
        is_admin=is_admin_v2,
        is_admin_mode=_is_admin_mode,
        has_permission=has_permission,
        has_any_permission=has_any_permission_v2,
        has_all_permissions=has_all_permissions_v2,
        has_role=has_role_v2,
        get_sections_for_user=get_sections_for_user,
        date=date,
        datetime=datetime,
        RoleType=RoleType,
        PermissionKey=PermissionKey
    )
    
    # Context processor for notifications (all users)
    @app.context_processor
    def inject_notifications_data():
        """Inject notification data into all templates for all users"""
        from flask_login import current_user
        
        data = {
            'handler_unread_count': 0,
            'admin_unread_count': 0
        }
        
        if current_user.is_authenticated:
            try:
                from k9.services.handler_service import NotificationService
                unread_count = NotificationService.get_unread_count(str(current_user.id))
                
                # Check if user has any operational permissions
                user_sections = get_sections_for_user(current_user)
                
                if user_sections:
                    # User has permissions - treat as admin
                    data['admin_unread_count'] = unread_count
                else:
                    # User has no permissions - treat as handler
                    data['handler_unread_count'] = unread_count
            except Exception:
                pass
        
        return data
    
    # Register blueprints
    from k9.routes.main import main_bp
    from k9.routes.auth import auth_bp
    from k9.api.api_routes import api_bp
    from k9.routes.admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    # Attendance reporting blueprints removed - now using DailySchedule system only
    
    # Register PM Daily Report blueprints
    from k9.routes.pm_daily_routes import bp as pm_daily_ui_bp
    from k9.api.pm_daily_api import bp as pm_daily_api_bp
    app.register_blueprint(pm_daily_ui_bp, url_prefix='/reports/attendance')
    app.register_blueprint(pm_daily_api_bp, url_prefix='/api/reports/attendance')
    
    # Register Training Report blueprints
    try:
        from k9.routes.trainer_daily_routes import bp as training_trainer_daily_ui_bp
        from k9.api.trainer_daily_api import bp as training_trainer_daily_api_bp
        from k9.api.trainer_daily_data_api import bp as training_data_api_bp
        
        app.register_blueprint(training_trainer_daily_ui_bp, url_prefix='/reports/training')
        app.register_blueprint(training_trainer_daily_api_bp, url_prefix='/api/reports/training')
        app.register_blueprint(training_data_api_bp)  # Root level for /api/projects etc
        print("✓ Training reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register training reports: {e}")
        # Continue without training reports for now
    
    # Note: Veterinary daily reports have been removed from the system
        
    # Register Cleaning API blueprint
    try:
        from k9.api.api_cleaning import bp as cleaning_api_bp
        app.register_blueprint(cleaning_api_bp)
        print("✓ Cleaning API registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register cleaning API: {e}")
        # Continue without cleaning API for now
    
    # Register Excretion API blueprint
    try:
        from k9.api.api_excretion import bp as excretion_api_bp
        app.register_blueprint(excretion_api_bp)
        print("✓ Excretion API registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register excretion API: {e}")
        # Continue without excretion API for now
    
    # Register Deworming API blueprint
    try:
        from k9.api.api_deworming import bp as deworming_api_bp
        app.register_blueprint(deworming_api_bp)
        print("✓ Deworming API registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register deworming API: {e}")
        # Continue without deworming API for now
    
    # Register Breeding Training Activity API blueprint
    try:
        from k9.api.api_breeding_training_activity import bp as breeding_training_api_bp
        app.register_blueprint(breeding_training_api_bp)
        print("✓ Breeding Training Activity API registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register breeding training activity API: {e}")
        # Continue without breeding training activity API for now
    
    # Register MFA routes blueprint
    try:
        from k9.routes.mfa_routes import mfa_bp
        app.register_blueprint(mfa_bp)
        print("✓ MFA routes registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register MFA routes: {e}")
        # Continue without MFA routes for now
    
    # Register Password Reset routes blueprint
    try:
        from k9.routes.password_reset_routes import password_reset_bp
        app.register_blueprint(password_reset_bp)
        print("✓ Password reset routes registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register password reset routes: {e}")
        # Continue without password reset routes for now
    
    # Register Unified Breeding Reports blueprints
    try:
        from k9.routes.unified_feeding_reports_routes import bp as unified_feeding_reports_ui_bp
        app.register_blueprint(unified_feeding_reports_ui_bp, url_prefix='/reports/breeding/feeding')
        print("✓ Unified breeding feeding reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register unified feeding reports: {e}")
    
    try:
        from k9.routes.unified_checkup_reports_routes import bp as unified_checkup_reports_ui_bp
        app.register_blueprint(unified_checkup_reports_ui_bp, url_prefix='/reports/breeding/checkup')
        print("✓ Unified breeding checkup reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register unified checkup reports: {e}")
    
    # Register Unified Veterinary Reports blueprints
    try:
        from k9.routes.veterinary_reports_routes import bp as veterinary_reports_ui_bp
        from k9.api.veterinary_reports_api import bp as veterinary_reports_api_bp
        from k9.routes.veterinary_legacy_routes import bp as veterinary_legacy_bp
        app.register_blueprint(veterinary_reports_ui_bp, url_prefix='/reports/breeding/veterinary')
        app.register_blueprint(veterinary_reports_api_bp, url_prefix='/api/reports/breeding/veterinary')
        app.register_blueprint(veterinary_legacy_bp, url_prefix='/reports/veterinary')
        print("✓ Unified veterinary reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register unified veterinary reports: {e}")
    
    # Register Caretaker Daily Report blueprints
    try:
        from k9.routes.caretaker_daily_report_routes import bp as caretaker_daily_reports_ui_bp
        from k9.api.caretaker_daily_report_api import bp as caretaker_daily_reports_api_bp
        app.register_blueprint(caretaker_daily_reports_ui_bp, url_prefix='/reports/breeding/caretaker-daily')
        app.register_blueprint(caretaker_daily_reports_api_bp, url_prefix='/api/reports/breeding/caretaker-daily')
        print("✓ Caretaker daily reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register caretaker daily reports: {e}")
    
    # Keep legacy UI blueprints for backward compatibility during transition
    try:
        from k9.routes.breeding_feeding_reports_routes import bp as breeding_feeding_reports_ui_bp
        from k9.routes.breeding_checkup_reports_routes import bp as breeding_checkup_reports_ui_bp
        app.register_blueprint(breeding_feeding_reports_ui_bp, url_prefix='/reports/breeding/feeding')
        app.register_blueprint(breeding_checkup_reports_ui_bp, url_prefix='/reports/breeding/checkup')
        print("✓ Legacy breeding reports UI registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register legacy breeding reports UI: {e}")
    
    # Keep legacy API blueprints for backward compatibility during transition
    try:
        from k9.api.breeding_feeding_reports_api import bp as breeding_feeding_reports_api_bp
        from k9.api.breeding_checkup_reports_api import bp as breeding_checkup_reports_api_bp
        app.register_blueprint(breeding_feeding_reports_api_bp, url_prefix='/api/reports/breeding/feeding')
        app.register_blueprint(breeding_checkup_reports_api_bp, url_prefix='/api/reports/breeding/checkup')
        print("✓ Legacy breeding reports APIs registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register legacy breeding reports APIs: {e}")
    
    # Register Handler Daily System blueprints
    try:
        from k9.routes.handler_routes import handler_bp
        from k9.routes.schedule_routes import schedule_bp
        from k9.routes.shift_routes import shift_bp
        from k9.routes.account_management_routes import account_mgmt_bp
        from k9.routes.supervisor_routes import supervisor_bp
        from k9.routes.task_routes import task_bp
        app.register_blueprint(handler_bp)
        app.register_blueprint(schedule_bp)
        app.register_blueprint(shift_bp)
        app.register_blueprint(account_mgmt_bp)
        app.register_blueprint(supervisor_bp)
        app.register_blueprint(task_bp)
        print("✓ Handler daily system registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register handler daily system: {e}")
    
    # Register Project Manager Routes
    try:
        from k9.routes.pm_routes import pm_bp
        app.register_blueprint(pm_bp)
        print("✓ Project Manager routes registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register PM routes: {e}")
    
    # Register Dashboard API Routes
    try:
        from k9.routes.dashboard_api_routes import dashboard_api_bp
        app.register_blueprint(dashboard_api_bp)
        print("✓ Dashboard API routes registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register Dashboard API routes: {e}")
    
    # Initialize Security Middleware
    try:
        from k9.utils.security_middleware import SecurityMiddleware
        SecurityMiddleware(app)
        print("✓ Security middleware initialized successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not initialize security middleware: {e}")
        # Continue without enhanced security middleware for now
    
    
    
    # Add route to serve uploaded files
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory('uploads', filename)
    
    # Initialize Automated Backup Scheduler
    # Skip scheduler when running seed/migration scripts (set SKIP_SCHEDULER=1)
    skip_scheduler = os.environ.get('SKIP_SCHEDULER', '').lower() in ('1', 'true', 'yes')
    
    if skip_scheduler:
        print("⚠ Scheduler initialization skipped (SKIP_SCHEDULER=1)")
        backup_scheduler = None
        app.reschedule_backup_jobs = lambda: False  # type: ignore
    else:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from k9.models.models import BackupSettings, BackupFrequency
            from k9.utils.backup_utils import LocalBackupManager
            from datetime import datetime
            
            backup_scheduler = BackgroundScheduler()
            
            def run_scheduled_backup():
                """Run scheduled backup job"""
                with app.app_context():
                    try:
                        settings = BackupSettings.get_settings()
                        
                        if not settings.auto_backup_enabled or settings.backup_frequency == BackupFrequency.DISABLED:
                            print("⚠ Automated backup skipped: disabled in settings")
                            return
                        
                        backup_manager = LocalBackupManager()
                        description = f'Automated {settings.backup_frequency.value.lower()} backup'
                        success, filename, error = backup_manager.create_backup(description)
                        
                        settings.last_backup_at = datetime.utcnow()
                        if success:
                            if error:
                                settings.last_backup_status = 'partial'
                                settings.last_backup_message = f'Backup created locally but Google Drive upload failed: {error}'
                                print(f"⚠ Automated backup created locally: {filename}, but Google Drive upload failed: {error}")
                            else:
                                settings.last_backup_status = 'success'
                                settings.last_backup_message = f'Automated backup created: {filename}'
                                print(f"✓ Automated backup created successfully: {filename}")
                            
                            if settings.retention_days > 0:
                                cleanup_count = backup_manager.cleanup_old_backups(settings.retention_days)
                                if cleanup_count > 0:
                                    print(f"✓ Cleaned up {cleanup_count} old backups")
                        else:
                            settings.last_backup_status = 'failed'
                            settings.last_backup_message = error
                            print(f"✗ Automated backup failed: {error}")
                        
                        db.session.commit()
                        
                    except Exception as e:
                        print(f"✗ Scheduled backup error: {str(e)}")
            
            def reschedule_backup_jobs():
                """Reschedule backup jobs based on current settings"""
                if backup_scheduler is None:
                    return False
                    
                with app.app_context():
                    try:
                        backup_scheduler.remove_job('backup_job')
                        print("✓ Removed existing backup job")
                    except:
                        pass
                    
                    try:
                        settings = BackupSettings.get_settings()
                    except Exception:
                        # Tables don't exist yet (during migration), skip backup scheduling
                        return False
                    
                    if settings.auto_backup_enabled and settings.backup_frequency != BackupFrequency.DISABLED:
                        if settings.backup_frequency == BackupFrequency.DAILY:
                            trigger = CronTrigger(hour=settings.backup_hour, minute=0)
                            backup_scheduler.add_job(
                                run_scheduled_backup,
                                trigger=trigger,
                                id='backup_job',
                                name='Daily Backup',
                                replace_existing=True
                            )
                            print(f"✓ Daily backup scheduled at {settings.backup_hour}:00")
                        
                        elif settings.backup_frequency == BackupFrequency.WEEKLY:
                            trigger = CronTrigger(day_of_week='sun', hour=settings.backup_hour, minute=0)
                            backup_scheduler.add_job(
                                run_scheduled_backup,
                                trigger=trigger,
                                id='backup_job',
                                name='Weekly Backup',
                                replace_existing=True
                            )
                            print(f"✓ Weekly backup scheduled on Sundays at {settings.backup_hour}:00")
                        
                        elif settings.backup_frequency == BackupFrequency.MONTHLY:
                            trigger = CronTrigger(day=1, hour=settings.backup_hour, minute=0)
                            backup_scheduler.add_job(
                                run_scheduled_backup,
                                trigger=trigger,
                                id='backup_job',
                                name='Monthly Backup',
                                replace_existing=True
                            )
                            print(f"✓ Monthly backup scheduled on 1st of month at {settings.backup_hour}:00")
                        
                        return True
                    else:
                        print("⚠ Automated backup not scheduled: disabled in settings")
                        return False
            
            backup_scheduler.start()
            print("✓ Backup scheduler started")
            
            reschedule_backup_jobs()
            
            # Add daily schedule auto-lock job
            try:
                from k9.utils.schedule_utils import auto_lock_yesterday_schedules, cleanup_old_notifications
                from config import Config
                
                # Auto-lock schedules at the end of each day
                backup_scheduler.add_job(
                    auto_lock_yesterday_schedules,
                    trigger=CronTrigger(hour=Config.SCHEDULE_AUTO_LOCK_HOUR, minute=Config.SCHEDULE_AUTO_LOCK_MINUTE),
                    id='auto_lock_schedules',
                    name='Auto Lock Yesterday Schedules',
                    replace_existing=True
                )
                print(f"✓ Auto-lock schedules job scheduled at {Config.SCHEDULE_AUTO_LOCK_HOUR}:{Config.SCHEDULE_AUTO_LOCK_MINUTE:02d}")
                
                # Cleanup old notifications weekly
                backup_scheduler.add_job(
                    cleanup_old_notifications,
                    trigger=CronTrigger(day_of_week='mon', hour=2, minute=0),
                    id='cleanup_notifications',
                    name='Cleanup Old Notifications',
                    replace_existing=True
                )
                print("✓ Notification cleanup job scheduled (weekly on Monday 2:00 AM)")
                
            except Exception as e:
                print(f"⚠ Warning: Could not schedule auto-lock job: {e}")
            
            app.reschedule_backup_jobs = reschedule_backup_jobs  # type: ignore
            
        except Exception as e:
            print(f"⚠ Warning: Could not initialize backup scheduler: {e}")
            backup_scheduler = None
            app.reschedule_backup_jobs = lambda: False  # type: ignore
