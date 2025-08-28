import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "k9-operations-development-secret-key-2025"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Use SQLite as fallback for Replit environment
    database_url = 'sqlite:///k9_operations.db'
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
else:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "client_encoding": "utf8"
        }
    }

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

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
    import models  # noqa: F401
    import models_attendance_reporting  # noqa: F401
    import models_notifications  # noqa: F401

    db.create_all()
    
    # Ensure default admin user exists
    from models import User, UserRole
    from werkzeug.security import generate_password_hash
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User()
        admin_user.username = 'admin'
        admin_user.email = 'admin@k9ops.com'
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.role = UserRole.GENERAL_ADMIN
        admin_user.full_name = 'System Administrator'
        admin_user.active = True
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Default admin user created successfully (username: admin, password: admin123)")

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register template functions
    from utils import get_user_permissions
    from datetime import date, datetime
    app.jinja_env.globals.update(
        get_user_permissions=get_user_permissions,
        date=date,
        datetime=datetime
    )
    
    # Register blueprints
    from routes import main_bp
    from auth import auth_bp
    from api_routes import api_bp
    from admin_routes import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    # Register attendance reporting blueprints
    from attendance_reporting_routes import bp as reports_attendance_ui_bp
    from attendance_reporting_api import bp as reports_attendance_api_bp
    app.register_blueprint(reports_attendance_ui_bp, url_prefix='/reports/attendance')
    app.register_blueprint(reports_attendance_api_bp, url_prefix='/api/reports/attendance')
    
    # Register PM Daily Report blueprints
    from pm_daily_routes import bp as pm_daily_ui_bp
    from pm_daily_api import bp as pm_daily_api_bp
    app.register_blueprint(pm_daily_ui_bp, url_prefix='/reports/attendance')
    app.register_blueprint(pm_daily_api_bp, url_prefix='/api/reports/attendance')
    
    # Register Training Report blueprints
    try:
        from trainer_daily_routes import bp as training_trainer_daily_ui_bp
        from trainer_daily_api import bp as training_trainer_daily_api_bp
        from trainer_daily_data_api import bp as training_data_api_bp
        
        app.register_blueprint(training_trainer_daily_ui_bp, url_prefix='/reports/training')
        app.register_blueprint(training_trainer_daily_api_bp, url_prefix='/api/reports/training')
        app.register_blueprint(training_data_api_bp)  # Root level for /api/projects etc
        print("✓ Training reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register training reports: {e}")
        # Continue without training reports for now
    
    # Register Veterinary Report blueprints
    try:
        from veterinary_daily_routes import bp as vet_daily_ui_bp
        from veterinary_daily_api import bp as vet_daily_api_bp
        
        app.register_blueprint(vet_daily_ui_bp, url_prefix='/reports/veterinary')
        app.register_blueprint(vet_daily_api_bp, url_prefix='/api/reports/veterinary')
        print("✓ Veterinary reports registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register veterinary reports: {e}")
        # Continue without veterinary reports for now
        
    # Register Cleaning API blueprint
    try:
        from api_cleaning import bp as cleaning_api_bp
        app.register_blueprint(cleaning_api_bp)
        print("✓ Cleaning API registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register cleaning API: {e}")
        # Continue without cleaning API for now
    
    # Register Notifications API and WebSocket
    try:
        from notifications_api import bp as notifications_api_bp
        from routes_notifications import bp as notifications_routes_bp
        app.register_blueprint(notifications_api_bp)
        app.register_blueprint(notifications_routes_bp)
        
        # Import notification models to create tables
        import models_notifications
        
        # Initialize SocketIO with notifications
        from flask_socketio import SocketIO
        from websocket_handlers import init_socketio_handlers
        from notifications_api import notification_service
        from notification_scheduler import init_notification_scheduler
        
        # Create SocketIO instance
        socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
        
        # Set socketio in notification service
        notification_service.socketio = socketio
        
        # Initialize WebSocket handlers
        init_socketio_handlers(socketio, notification_service)
        
        # Initialize notification scheduler
        init_notification_scheduler(notification_service)
        
        print("✓ Notifications system registered successfully")
        
    except Exception as e:
        print(f"⚠ Warning: Could not register notifications system: {e}")
        # Continue without notifications for now
    
    
    # Add route to serve uploaded files
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory('uploads', filename)
