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
    # For local development, provide a fallback but warn user
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
app.config['WTF_CSRF_SSL_STRICT'] = False  # Required for Replit iframe/proxy environment
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

    # Bootstrap database on fresh import - creates all tables
    # For production, use migrations instead
    try:
        db.create_all()
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")
    
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
    from k9.utils.permission_utils import has_permission, has_any_permission, has_all_permissions, get_sections_for_user
    from datetime import date, datetime
    
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
    
    app.jinja_env.globals.update(
        get_user_permissions=get_user_permissions,
        get_notification_link=get_notification_link,
        get_pending_reports_count=get_pending_reports_count,
        get_pm_pending_count=get_pm_pending_count,
        is_admin=is_admin,
        has_permission=has_permission,
        has_any_permission=has_any_permission,
        has_all_permissions=has_all_permissions,
        get_sections_for_user=get_sections_for_user,
        date=date,
        datetime=datetime
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
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from k9.models.models import BackupSettings, BackupFrequency
        from k9.utils.backup_utils import BackupManager
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
                    
                    backup_manager = BackupManager()
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
