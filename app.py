import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
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

# Create the app
app = Flask(__name__, template_folder='k9/templates', static_folder='k9/static')
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("SESSION_SECRET environment variable is required but not set")
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
# Login manager configuration
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import k9.models.models  # noqa: F401
    import k9.models.models_attendance_reporting  # noqa: F401

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
    app.jinja_env.globals.update(
        get_user_permissions=get_user_permissions,
        date=date,
        datetime=datetime
    )
    
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
    
    # Register Breeding Feeding Reports blueprints
    try:
        from k9.routes.breeding_feeding_reports_routes import bp as breeding_feeding_reports_ui_bp
        from k9.api.breeding_feeding_reports_api import bp as breeding_feeding_reports_api_bp
        app.register_blueprint(breeding_feeding_reports_ui_bp, url_prefix='/reports/breeding/feeding')
        app.register_blueprint(breeding_feeding_reports_api_bp, url_prefix='/api/reports/breeding/feeding')
        print("✓ Breeding feeding reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register breeding feeding reports: {e}")
        # Continue without breeding feeding reports for now
    
    # Register Breeding Checkup Reports blueprints
    try:
        from k9.routes.breeding_checkup_reports_routes import bp as breeding_checkup_reports_ui_bp
        from k9.api.breeding_checkup_reports_api import bp as breeding_checkup_reports_api_bp
        app.register_blueprint(breeding_checkup_reports_ui_bp, url_prefix='/reports/breeding/checkup')
        app.register_blueprint(breeding_checkup_reports_api_bp, url_prefix='/api/reports/breeding/checkup')
        print("✓ Breeding checkup reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register breeding checkup reports: {e}")
        # Continue without breeding checkup reports for now
    
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
