import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'k9-operations-secret-key'
    
    # Smart database URL detection for Replit/SQLite compatibility
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///k9_operations.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Conditional engine options based on database type
    if database_url and not database_url.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "connect_args": {
                "charset": "utf8mb4",
                "client_encoding": "utf8"
            }
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                "check_same_thread": False
            }
        }
    
    @staticmethod
    def is_sqlite():
        """Check if we're using SQLite (for UUID compatibility)"""
        database_url = os.environ.get('DATABASE_URL', '')
        return not database_url or database_url.startswith('sqlite')
    
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
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
