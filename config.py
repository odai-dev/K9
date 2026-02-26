import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET')

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "PostgreSQL is required to run this application."
        )
    # Normalize legacy postgres:// scheme
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "client_encoding": "utf8"
        }
    }
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Pagination
    POSTS_PER_PAGE = 25
    
    # Languages
    LANGUAGES = ['ar', 'en']
    
    # Handler Report Settings
    HANDLER_REPORT_GRACE_MINUTES = int(os.environ.get('HANDLER_REPORT_GRACE_MINUTES', 240))  # 4 hours default
    
    # Schedule Auto-Lock Settings
    SCHEDULE_AUTO_LOCK_HOUR = int(os.environ.get('SCHEDULE_AUTO_LOCK_HOUR', 23))  # 11 PM default
    SCHEDULE_AUTO_LOCK_MINUTE = int(os.environ.get('SCHEDULE_AUTO_LOCK_MINUTE', 59))  # 11:59 PM default
    
    # Notification Settings
    NOTIFICATION_POLL_INTERVAL = int(os.environ.get('NOTIFICATION_POLL_INTERVAL', 30))  # seconds
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
