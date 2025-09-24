#!/usr/bin/env python3
"""
K9 Operations Management System - Common Issues Fixer

This script automatically fixes common issues that users encounter
when setting up the application locally.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class IssueFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.fixed_issues = []
        self.failed_fixes = []
        
    def print_success(self, text):
        print(f"✓ {text}")
        
    def print_error(self, text):
        print(f"✗ {text}")
        
    def print_info(self, text):
        print(f"ℹ {text}")
        
    def run_command(self, command, capture_output=False):
        """Run command with error handling"""
        try:
            if capture_output:
                result = subprocess.run(command, capture_output=True, text=True, shell=True)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=True)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
            
    def fix_missing_env_file(self):
        """Fix missing .env file"""
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            self.print_info("Creating missing .env file...")
            
            # Generate secure session secret
            import secrets
            session_secret = secrets.token_urlsafe(32)
            
            env_content = f"""# K9 Operations Management System - Environment Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SESSION_SECRET={session_secret}
DATABASE_URL=sqlite:///k9_operations.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
POSTS_PER_PAGE=25
LANGUAGES=ar,en
"""
            
            try:
                with open(env_file, 'w') as f:
                    f.write(env_content)
                self.print_success("Created .env file with default configuration")
                self.fixed_issues.append("Missing .env file")
                return True
            except Exception as e:
                self.print_error(f"Failed to create .env file: {e}")
                return False
        else:
            return True
            
    def fix_missing_directories(self):
        """Fix missing upload directories"""
        directories = [
            'uploads',
            'uploads/reports',
            'uploads/reports/feeding',
            'uploads/reports/veterinary',
            'logs'
        ]
        
        created_dirs = []
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(directory)
                except Exception as e:
                    self.print_error(f"Failed to create directory {directory}: {e}")
                    return False
                    
        if created_dirs:
            self.print_success(f"Created missing directories: {', '.join(created_dirs)}")
            self.fixed_issues.append("Missing directories")
            
        return True
        
    def fix_file_permissions(self):
        """Fix file permissions"""
        if os.name != 'posix':  # Skip on Windows
            return True
            
        try:
            # Fix upload directory permissions
            uploads_dir = self.project_root / 'uploads'
            if uploads_dir.exists():
                os.chmod(uploads_dir, 0o755)
                for root, dirs, files in os.walk(uploads_dir):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
                        
            # Fix static file permissions
            static_dir = self.project_root / 'k9' / 'static'
            if static_dir.exists():
                for root, dirs, files in os.walk(static_dir):
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
                        
            self.print_success("Fixed file permissions")
            self.fixed_issues.append("File permissions")
            return True
        except Exception as e:
            self.print_error(f"Failed to fix permissions: {e}")
            return False
            
    def fix_database_url_format(self):
        """Fix PostgreSQL database URL format"""
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            return True
            
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Fix postgres:// to postgresql://
            if 'postgres://' in content and 'postgresql://' not in content:
                updated_content = content.replace('postgres://', 'postgresql://')
                
                with open(env_file, 'w') as f:
                    f.write(updated_content)
                    
                self.print_success("Fixed PostgreSQL URL format")
                self.fixed_issues.append("Database URL format")
                
            return True
        except Exception as e:
            self.print_error(f"Failed to fix database URL: {e}")
            return False
            
    def fix_missing_session_secret(self):
        """Fix missing session secret"""
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            return self.fix_missing_env_file()
            
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            if 'SESSION_SECRET=' not in content or 'SESSION_SECRET=\n' in content:
                import secrets
                session_secret = secrets.token_urlsafe(32)
                
                if 'SESSION_SECRET=' in content:
                    # Replace existing empty secret
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('SESSION_SECRET='):
                            lines[i] = f'SESSION_SECRET={session_secret}'
                            break
                    updated_content = '\n'.join(lines)
                else:
                    # Add session secret
                    updated_content = content + f'\nSESSION_SECRET={session_secret}\n'
                    
                with open(env_file, 'w') as f:
                    f.write(updated_content)
                    
                self.print_success("Fixed missing session secret")
                self.fixed_issues.append("Session secret")
                
            return True
        except Exception as e:
            self.print_error(f"Failed to fix session secret: {e}")
            return False
            
    def fix_python_path_issues(self):
        """Fix Python path issues"""
        try:
            # Add current directory to Python path
            current_dir = str(self.project_root)
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                
            # Try to import the app to test
            try:
                import app
                self.print_success("Python import paths working")
                return True
            except ImportError as e:
                self.print_error(f"Import still failing: {e}")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to fix Python paths: {e}")
            return False
            
    def fix_virtual_environment_issues(self):
        """Fix virtual environment issues"""
        venv_path = self.project_root / 'venv'
        
        # Check if virtual environment exists
        if not venv_path.exists():
            self.print_info("Virtual environment not found - this is expected if not yet created")
            return True
            
        # Check if virtual environment is activated
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_success("Virtual environment is active")
            return True
        else:
            self.print_info("Virtual environment exists but not activated")
            
            # Provide activation instructions
            if os.name == 'nt':  # Windows
                activate_cmd = str(venv_path / 'Scripts' / 'activate.bat')
            else:
                activate_cmd = f"source {venv_path}/bin/activate"
                
            self.print_info(f"To activate: {activate_cmd}")
            return True
            
    def fix_database_migration_issues(self):
        """Fix database migration issues"""
        migrations_dir = self.project_root / 'migrations'
        
        if not migrations_dir.exists():
            self.print_info("Migrations directory not found - run 'flask db init' first")
            return True
            
        # Check for migration files
        versions_dir = migrations_dir / 'versions'
        if versions_dir.exists():
            migration_files = list(versions_dir.glob('*.py'))
            if migration_files:
                self.print_success(f"Found {len(migration_files)} migration files")
            else:
                self.print_info("No migration files found - run 'flask db migrate' first")
        
        return True
        
    def fix_static_file_issues(self):
        """Fix static file issues"""
        static_dir = self.project_root / 'k9' / 'static'
        
        if not static_dir.exists():
            self.print_error("Static directory not found")
            return False
            
        # Check for required static files
        required_files = [
            'css/style.css',
            'js/main.js'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = static_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            self.print_info(f"Missing static files: {', '.join(missing_files)}")
        else:
            self.print_success("Essential static files present")
            
        # Check Arabic font
        font_path = static_dir / 'fonts' / 'NotoSansArabic-Regular.ttf'
        if not font_path.exists():
            self.print_info("Arabic font missing - some text may not display correctly")
            
        return True
        
    def fix_gitignore_issues(self):
        """Fix .gitignore issues"""
        gitignore_path = self.project_root / '.gitignore'
        
        required_entries = [
            '.env',
            '__pycache__/',
            '*.pyc',
            'instance/',
            'venv/',
            'k9_operations.db',
            'logs/',
            'uploads/'
        ]
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
        else:
            existing_content = ""
            
        missing_entries = []
        for entry in required_entries:
            if entry not in existing_content:
                missing_entries.append(entry)
                
        if missing_entries:
            try:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Added by fix script\n')
                    for entry in missing_entries:
                        f.write(f'{entry}\n')
                        
                self.print_success(f"Added {len(missing_entries)} entries to .gitignore")
                self.fixed_issues.append("Git ignore entries")
                
            except Exception as e:
                self.print_error(f"Failed to update .gitignore: {e}")
                return False
                
        return True
        
    def run_fixes(self):
        """Run all fixes"""
        print("K9 Operations Management System - Issue Fixer")
        print("=" * 50)
        
        fixes = [
            ("Environment file", self.fix_missing_env_file),
            ("Required directories", self.fix_missing_directories),
            ("File permissions", self.fix_file_permissions),
            ("Database URL format", self.fix_database_url_format),
            ("Session secret", self.fix_missing_session_secret),
            ("Python paths", self.fix_python_path_issues),
            ("Virtual environment", self.fix_virtual_environment_issues),
            ("Database migrations", self.fix_database_migration_issues),
            ("Static files", self.fix_static_file_issues),
            ("Git ignore", self.fix_gitignore_issues)
        ]
        
        print("Running automatic fixes...")
        print()
        
        for fix_name, fix_func in fixes:
            try:
                print(f"Checking {fix_name}...")
                success = fix_func()
                if not success:
                    self.failed_fixes.append(fix_name)
            except Exception as e:
                print(f"Error in {fix_name}: {e}")
                self.failed_fixes.append(fix_name)
                
        # Summary
        print("\n" + "=" * 50)
        print("FIX SUMMARY")
        print("=" * 50)
        
        if self.fixed_issues:
            print(f"✓ Fixed {len(self.fixed_issues)} issues:")
            for issue in self.fixed_issues:
                print(f"  • {issue}")
                
        if self.failed_fixes:
            print(f"✗ Failed to fix {len(self.failed_fixes)} items:")
            for fix in self.failed_fixes:
                print(f"  • {fix}")
                
        if not self.fixed_issues and not self.failed_fixes:
            print("✓ No issues found that needed fixing")
            
        print(f"\nNext steps:")
        print("1. Run setup_local.py for full setup")
        print("2. Run verify_setup.py to verify installation")
        print("3. Check TROUBLESHOOTING.md for manual fixes")

if __name__ == "__main__":
    fixer = IssueFixer()
    fixer.run_fixes()