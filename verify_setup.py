#!/usr/bin/env python3
"""
K9 Operations Management System - Setup Verification Script

This script verifies that the local setup is working correctly.
Run this after setup_local.py to ensure everything is configured properly.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

class SetupVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.issues_found = []
        self.warnings_found = []
        
    def print_success(self, text):
        print(f"✓ {text}")
        
    def print_error(self, text):
        print(f"✗ {text}")
        self.issues_found.append(text)
        
    def print_warning(self, text):
        print(f"⚠ {text}")
        self.warnings_found.append(text)
        
    def print_info(self, text):
        print(f"ℹ {text}")
        
    def check_python_environment(self):
        """Check Python environment and virtual environment"""
        print("\n=== Python Environment ===")
        
        # Check Python version
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        else:
            self.print_error(f"Python {version.major}.{version.minor}.{version.micro} - requires 3.11+")
            
        # Check if we're in virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_success("Virtual environment active")
        else:
            self.print_warning("Not in virtual environment")
            
        # Check virtual environment directory
        venv_path = self.project_root / 'venv'
        if venv_path.exists():
            self.print_success("Virtual environment directory exists")
        else:
            self.print_error("Virtual environment directory not found")
            
    def check_environment_variables(self):
        """Check required environment variables"""
        print("\n=== Environment Variables ===")
        
        # Load from .env file if it exists
        env_file = self.project_root / '.env'
        env_vars = {}
        
        if env_file.exists():
            self.print_success(".env file exists")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                        os.environ[key] = value
        else:
            self.print_error(".env file not found")
            
        # Check required variables
        required_vars = {
            'SESSION_SECRET': "Session security key",
            'DATABASE_URL': "Database connection string",
            'FLASK_ENV': "Flask environment (should be 'development')"
        }
        
        for var, description in required_vars.items():
            if var in os.environ:
                value = os.environ[var]
                if var == 'SESSION_SECRET':
                    if len(value) >= 32:
                        self.print_success(f"{var}: {description} (secure length)")
                    else:
                        self.print_warning(f"{var}: {description} (short length)")
                elif var == 'FLASK_ENV':
                    if value == 'development':
                        self.print_success(f"{var}: {value}")
                    else:
                        self.print_warning(f"{var}: {value} (expected 'development')")
                else:
                    self.print_success(f"{var}: {description}")
            else:
                self.print_error(f"{var}: Missing - {description}")
                
    def check_dependencies(self):
        """Check if required Python packages are installed"""
        print("\n=== Python Dependencies ===")
        
        required_packages = [
            'flask',
            'flask_sqlalchemy',
            'flask_login',
            'flask_migrate',
            'sqlalchemy',
            'werkzeug',
            'psycopg2',
            'reportlab',
            'gunicorn'
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                self.print_success(f"{package}")
            except ImportError:
                try:
                    # Try alternative names
                    alt_names = {
                        'psycopg2': 'psycopg2_binary'
                    }
                    if package in alt_names:
                        importlib.import_module(alt_names[package])
                        self.print_success(f"{package} (as {alt_names[package]})")
                    else:
                        raise ImportError
                except ImportError:
                    self.print_error(f"{package} - not installed")
                    
    def check_database_connection(self):
        """Check database connection"""
        print("\n=== Database Connection ===")
        
        try:
            # Import Flask app modules
            from app import app, db
            
            with app.app_context():
                # Test database connection
                try:
                    with db.engine.connect() as conn:
                        result = conn.execute(db.text('SELECT 1'))
                        result.fetchone()
                    self.print_success("Database connection successful")
                    
                    # Check if tables exist
                    from k9.models.models import User
                    user_count = User.query.count()
                    self.print_success(f"User table accessible ({user_count} users)")
                    
                    # Check for admin user
                    admin_user = User.query.filter_by(username='admin').first()
                    if admin_user:
                        self.print_success("Admin user exists")
                    else:
                        self.print_warning("Admin user not found")
                        
                except Exception as e:
                    self.print_error(f"Database query failed: {e}")
                    
        except ImportError as e:
            self.print_error(f"Cannot import app modules: {e}")
        except Exception as e:
            self.print_error(f"Database connection failed: {e}")
            
    def check_file_structure(self):
        """Check required files and directories"""
        print("\n=== File Structure ===")
        
        required_files = [
            'app.py',
            'main.py',
            'config.py',
            'pyproject.toml',
            'k9/__init__.py',
            'k9/models/models.py',
            'k9/routes/main.py',
            'k9/templates/base.html',
            'migrations/env.py'
        ]
        
        required_dirs = [
            'k9',
            'k9/models',
            'k9/routes',
            'k9/templates',
            'k9/static',
            'migrations',
            'uploads'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.print_success(f"File: {file_path}")
            else:
                self.print_error(f"File missing: {file_path}")
                
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                self.print_success(f"Directory: {dir_path}")
            else:
                self.print_error(f"Directory missing: {dir_path}")
                
    def check_static_files(self):
        """Check static files and assets"""
        print("\n=== Static Files ===")
        
        static_files = [
            'k9/static/css/style.css',
            'k9/static/js/main.js',
            'k9/static/fonts/NotoSansArabic-Regular.ttf'
        ]
        
        for file_path in static_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.print_success(f"Static file: {file_path}")
            else:
                self.print_warning(f"Static file missing: {file_path}")
                
    def test_flask_app(self):
        """Test Flask application startup"""
        print("\n=== Flask Application ===")
        
        try:
            from app import app
            
            # Test app configuration
            with app.app_context():
                if app.config.get('SECRET_KEY'):
                    self.print_success("Flask app has secret key")
                else:
                    self.print_error("Flask app missing secret key")
                    
                if app.config.get('SQLALCHEMY_DATABASE_URI'):
                    self.print_success("Database URI configured")
                else:
                    self.print_error("Database URI not configured")
                    
                # Test route registration
                routes = [rule.rule for rule in app.url_map.iter_rules()]
                if '/' in routes:
                    self.print_success("Main route registered")
                else:
                    self.print_error("Main route not found")
                    
                if '/auth/login' in routes:
                    self.print_success("Auth routes registered")
                else:
                    self.print_error("Auth routes not found")
                    
        except Exception as e:
            self.print_error(f"Flask app test failed: {e}")
            
    def check_migrations(self):
        """Check database migrations"""
        print("\n=== Database Migrations ===")
        
        migrations_dir = self.project_root / 'migrations' / 'versions'
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob('*.py'))
            if migration_files:
                self.print_success(f"Found {len(migration_files)} migration files")
            else:
                self.print_warning("No migration files found")
        else:
            self.print_error("Migrations directory not found")
            
        # Check if migrations have been applied
        try:
            from app import app, db
            from flask_migrate import current
            
            with app.app_context():
                try:
                    current_revision = current()
                    if current_revision:
                        self.print_success(f"Database at revision: {current_revision}")
                    else:
                        self.print_warning("No migration revision applied")
                except Exception as e:
                    self.print_warning(f"Cannot check migration status: {e}")
                    
        except Exception as e:
            self.print_error(f"Migration check failed: {e}")
            
    def run_verification(self):
        """Run all verification checks"""
        print("K9 Operations Management System - Setup Verification")
        print("=" * 60)
        
        checks = [
            self.check_python_environment,
            self.check_environment_variables,
            self.check_dependencies,
            self.check_file_structure,
            self.check_static_files,
            self.check_database_connection,
            self.check_flask_app,
            self.check_migrations
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.print_error(f"Check failed with error: {e}")
                
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        if not self.issues_found and not self.warnings_found:
            print("🎉 All checks passed! Your setup is ready.")
            print("\nTo start the application:")
            print("1. Activate virtual environment: source venv/bin/activate")
            print("2. Start Flask: flask run --host=0.0.0.0 --port=5000")
            print("3. Open browser: http://localhost:5000")
            print("4. Login: admin / password123")
            return True
        else:
            if self.issues_found:
                print(f"❌ {len(self.issues_found)} critical issues found:")
                for issue in self.issues_found:
                    print(f"   • {issue}")
                    
            if self.warnings_found:
                print(f"⚠️  {len(self.warnings_found)} warnings:")
                for warning in self.warnings_found:
                    print(f"   • {warning}")
                    
            print("\nPlease fix the issues above before running the application.")
            return False

if __name__ == "__main__":
    verifier = SetupVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)