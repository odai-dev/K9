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

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "k9-operations-secret-key")
    
    # Database configuration - use SQLite for development in Replit
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Default to SQLite for development
        database_url = "sqlite:///k9_operations.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
    login_manager.login_message_category = 'info'
    
    # Import models
    from models import (User, Dog, Employee, TrainingSession, VeterinaryVisit, BreedingCycle, Project, 
                        AttendanceRecord, AuditLog, UserRole, ProjectAssignment, ProjectDog, Incident, 
                        Suspicion, PerformanceEvaluation)
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register template functions
    from utils import get_user_permissions
    app.jinja_env.globals.update(get_user_permissions=get_user_permissions)
    
    # Register blueprints
    from routes import main_bp
    from auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@k9operations.mil'
            admin_user.password_hash = generate_password_hash('admin123')
            admin_user.role = UserRole.GENERAL_ADMIN
            admin_user.full_name = 'مدير النظام العام'
            admin_user.active = True
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created: admin/admin123")
    
    return app

# Create the app instance
app = create_app()
