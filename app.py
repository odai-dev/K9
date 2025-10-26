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

# Enhanced security configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['SESSION_COOKIE_SECURE'] = flask_env == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
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
if flask_env == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
else:
    # For development, allow non-secure cookies
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
# Login manager configuration
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import k9.models.models  # noqa: F401
    import k9.models.models_attendance_reporting  # noqa: F401
    import k9.models.models_handler_daily  # noqa: F401

    # Always skip automatic table creation, use migrations instead
    # db.create_all() - disabled for proper migration handling
    
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
        """Get count of pending handler reports for PROJECT_MANAGER and GENERAL_ADMIN"""
        from flask_login import current_user
        from k9.models.models import UserRole
        from k9.models.models_handler_daily import HandlerReport, ReportStatus
        
        if not current_user.is_authenticated:
            return 0
        
        if current_user.role not in [UserRole.GENERAL_ADMIN, UserRole.PROJECT_MANAGER]:
            return 0
        
        try:
            # Count submitted reports (pending review)
            count = HandlerReport.query.filter_by(status=ReportStatus.SUBMITTED).count()
            return count
        except Exception:
            return 0
    
    app.jinja_env.globals.update(
        get_user_permissions=get_user_permissions,
        get_notification_link=get_notification_link,
        get_pending_reports_count=get_pending_reports_count,
        date=date,
        datetime=datetime
    )
    
    # Context processor for notifications (all users)
    @app.context_processor
    def inject_notifications_data():
        """Inject notification data into all templates for all users"""
        from flask_login import current_user
        from k9.models.models import UserRole
        
        data = {
            'handler_unread_count': 0,
            'admin_unread_count': 0
        }
        
        if current_user.is_authenticated:
            try:
                from k9.services.handler_service import NotificationService
                unread_count = NotificationService.get_unread_count(str(current_user.id))
                
                if current_user.role == UserRole.HANDLER:
                    data['handler_unread_count'] = unread_count
                elif current_user.role in [UserRole.GENERAL_ADMIN, UserRole.PROJECT_MANAGER]:
                    data['admin_unread_count'] = unread_count
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
    
    # Register attendance reporting blueprints
    from k9.routes.attendance_reporting_routes import bp as reports_attendance_ui_bp
    from k9.api.attendance_reporting_api import bp as reports_attendance_api_bp
    app.register_blueprint(reports_attendance_ui_bp, url_prefix='/reports/attendance')
    app.register_blueprint(reports_attendance_api_bp, url_prefix='/api/reports/attendance')
    
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
        from k9.routes.user_management_routes import user_mgmt_bp
        from k9.routes.supervisor_routes import supervisor_bp
        from k9.routes.task_routes import task_bp
        app.register_blueprint(handler_bp)
        app.register_blueprint(schedule_bp)
        app.register_blueprint(user_mgmt_bp)
        app.register_blueprint(supervisor_bp)
        app.register_blueprint(task_bp)
        print("✓ Handler daily system registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register handler daily system: {e}")
    
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
                
                settings = BackupSettings.get_settings()
                
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
