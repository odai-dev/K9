#!/usr/bin/env python3
"""
K9 Operations Management System - Local Setup Automation Script

This script automates the complete setup process for local development.
It handles environment setup, database configuration, and dependency installation.
"""

import os
import sys
import subprocess
import secrets
import platform
import shutil
import time
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

class SetupHelper:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system() == 'Windows'
        self.is_linux = platform.system() == 'Linux'
        self.is_mac = platform.system() == 'Darwin'
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE} {text} {Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        
    def print_success(self, text):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")
        
    def print_error(self, text):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.ENDC}")
        
    def print_warning(self, text):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")
        
    def print_info(self, text):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")
        
    def run_command(self, command, shell=False, capture_output=False):
        """Run a system command with error handling"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=shell, capture_output=True, text=True)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=shell)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
            
    def check_python_version(self):
        """Check if Python version is 3.11 or higher"""
        self.print_header("Checking Python Version")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro} is supported")
            return True
        else:
            self.print_error(f"Python {version.major}.{version.minor}.{version.micro} is not supported")
            self.print_info("This project requires Python 3.11 or higher")
            if self.is_linux:
                self.print_info("Install with: sudo apt install python3.11 python3.11-venv")
            elif self.is_mac:
                self.print_info("Install with: brew install python@3.11")
            elif self.is_windows:
                self.print_info("Download from: https://www.python.org/downloads/")
            return False
            
    def check_git(self):
        """Check if Git is installed"""
        success, _, _ = self.run_command(['git', '--version'], capture_output=True)
        if success:
            self.print_success("Git is available")
            return True
        else:
            self.print_error("Git is not installed")
            if self.is_linux:
                self.print_info("Install with: sudo apt install git")
            elif self.is_mac:
                self.print_info("Install with: brew install git")
            elif self.is_windows:
                self.print_info("Download from: https://git-scm.com/download/win")
            return False
            
    def setup_virtual_environment(self):
        """Create and activate virtual environment"""
        self.print_header("Setting Up Python Virtual Environment")
        
        venv_path = self.project_root / 'venv'
        
        # Remove existing venv if it exists
        if venv_path.exists():
            self.print_info("Removing existing virtual environment...")
            shutil.rmtree(venv_path)
            
        # Create new virtual environment
        self.print_info("Creating virtual environment...")
        success, _, error = self.run_command([sys.executable, '-m', 'venv', str(venv_path)])
        
        if not success:
            self.print_error(f"Failed to create virtual environment: {error}")
            return False
            
        self.print_success("Virtual environment created successfully")
        
        # Provide activation instructions
        if self.is_windows:
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
            
        self.print_info(f"To activate: {activate_cmd}")
        return True
        
    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_header("Installing Python Dependencies")
        
        venv_path = self.project_root / 'venv'
        if self.is_windows:
            python_exe = venv_path / 'Scripts' / 'python.exe'
            pip_exe = venv_path / 'Scripts' / 'pip.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
            pip_exe = venv_path / 'bin' / 'pip'
            
        if not python_exe.exists():
            self.print_error("Virtual environment not found. Please run setup_virtual_environment first.")
            return False
            
        # Upgrade pip
        self.print_info("Upgrading pip...")
        success, _, _ = self.run_command([str(pip_exe), 'install', '--upgrade', 'pip'])
        if not success:
            self.print_warning("Failed to upgrade pip, continuing...")
            
        # Install uv for faster package management
        self.print_info("Installing uv package manager...")
        success, _, _ = self.run_command([str(pip_exe), 'install', 'uv'])
        error = ""
        
        if success:
            uv_exe = venv_path / ('Scripts' if self.is_windows else 'bin') / 'uv'
            if uv_exe.exists():
                self.print_info("Installing project dependencies with uv...")
                success, _, error = self.run_command([str(uv_exe), 'pip', 'install', '-e', '.'])
            else:
                success = False
                error = "uv executable not found after installation"
        
        if not success:
            self.print_warning("uv installation failed, falling back to pip...")
            success, _, error = self.run_command([str(pip_exe), 'install', '-e', '.'])
            
        if success:
            self.print_success("Dependencies installed successfully")
            return True
        else:
            self.print_error(f"Failed to install dependencies: {error}")
            return False
            
    def setup_environment_file(self):
        """Create .env file with required environment variables"""
        self.print_header("Setting Up Environment Variables")
        
        env_file = self.project_root / '.env'
        
        # Generate secure session secret
        session_secret = secrets.token_urlsafe(32)
        
        env_content = f"""# K9 Operations Management System - Local Development Environment
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SESSION_SECRET={session_secret}

# Database Configuration (choose one)
# Option 1: SQLite for simple development
DATABASE_URL=sqlite:///k9_operations.db

# Option 2: PostgreSQL for production-like development
# DATABASE_URL=postgresql://k9user:yourpassword@localhost/k9operations

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Security Settings
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600

# Pagination
POSTS_PER_PAGE=25

# Supported Languages
LANGUAGES=ar,en
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            self.print_success(f"Environment file created: {env_file}")
            self.print_info("You can modify database settings in .env file")
            return True
        except Exception as e:
            self.print_error(f"Failed to create .env file: {e}")
            return False
            
    def check_postgresql(self):
        """Check if PostgreSQL is available"""
        self.print_header("Checking PostgreSQL Availability")
        
        # Check if psql is available
        success, output, _ = self.run_command(['psql', '--version'], capture_output=True)
        if success:
            self.print_success(f"PostgreSQL client available: {output.strip()}")
            
            # Check if PostgreSQL server is running
            success, _, _ = self.run_command(['pg_isready'], capture_output=True)
            if success:
                self.print_success("PostgreSQL server is running")
                return True
            else:
                self.print_warning("PostgreSQL server is not running")
                if self.is_linux:
                    self.print_info("Start with: sudo systemctl start postgresql")
                elif self.is_mac:
                    self.print_info("Start with: brew services start postgresql")
                elif self.is_windows:
                    self.print_info("Start PostgreSQL service from Services app")
                return False
        else:
            self.print_warning("PostgreSQL is not installed")
            if self.is_linux:
                self.print_info("Install with: sudo apt install postgresql postgresql-contrib")
            elif self.is_mac:
                self.print_info("Install with: brew install postgresql")
            elif self.is_windows:
                self.print_info("Download from: https://www.postgresql.org/download/windows/")
            return False
            
    def setup_postgresql_database(self):
        """Set up PostgreSQL database for the project"""
        self.print_header("Setting Up PostgreSQL Database")
        
        if not self.check_postgresql():
            self.print_info("Skipping PostgreSQL setup. Using SQLite instead.")
            return True
            
        db_name = "k9operations"
        db_user = "k9user"
        
        # Prompt for password
        db_password = input(f"Enter password for PostgreSQL user '{db_user}' (or press Enter for 'k9password'): ").strip()
        if not db_password:
            db_password = "k9password"
            
        # Create user and database
        commands = [
            f"CREATE USER {db_user} WITH PASSWORD '{db_password}';",
            f"CREATE DATABASE {db_name} OWNER {db_user};",
            f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"
        ]
        
        for cmd in commands:
            success, _, error = self.run_command(['sudo', '-u', 'postgres', 'psql', '-c', cmd], capture_output=True)
            if not success and "already exists" not in error:
                self.print_warning(f"Command might have failed: {cmd}")
                
        # Update .env file with PostgreSQL URL
        database_url = f"postgresql://{db_user}:{db_password}@localhost/{db_name}"
        env_file = self.project_root / '.env'
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Replace SQLite URL with PostgreSQL URL
            updated_content = content.replace(
                "DATABASE_URL=sqlite:///k9_operations.db",
                f"DATABASE_URL={database_url}"
            )
            
            with open(env_file, 'w') as f:
                f.write(updated_content)
                
            self.print_success("PostgreSQL database configured")
            self.print_info(f"Database: {db_name}")
            self.print_info(f"User: {db_user}")
            return True
        else:
            self.print_error(".env file not found")
            return False
            
    def create_directories(self):
        """Create necessary directories"""
        self.print_header("Creating Required Directories")
        
        directories = [
            'uploads',
            'uploads/reports',
            'uploads/reports/feeding',
            'uploads/reports/veterinary',
            'logs'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.print_success(f"Directory created: {directory}")
            
        return True
        
    def run_database_migrations(self):
        """Run Flask database migrations"""
        self.print_header("Running Database Migrations")
        
        venv_path = self.project_root / 'venv'
        if self.is_windows:
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
            
        if not python_exe.exists():
            self.print_error("Virtual environment not found")
            return False
            
        # Load environment variables from .env file
        env = os.environ.copy()
        env_file = self.project_root / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
                        
        # Run migrations
        self.print_info("Running database migrations...")
        success, output, error = self.run_command(
            [str(python_exe), '-m', 'flask', 'db', 'upgrade'],
            capture_output=True
        )
        
        if success:
            self.print_success("Database migrations completed successfully")
            return True
        else:
            self.print_error(f"Database migrations failed: {error}")
            return False
            
    def create_admin_user(self):
        """Create admin user"""
        self.print_header("Creating Admin User")
        
        venv_path = self.project_root / 'venv'
        if self.is_windows:
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
            
        # Load environment variables
        env = os.environ.copy()
        env_file = self.project_root / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
                        
        # Create admin user script
        admin_script = '''
from app import app, db
from k9.models.models import User, UserRole
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    email = "admin@k9ops.local"
    password = "password123"
    full_name = "System Administrator"
    
    existing_user = User.query.filter_by(username=username).first()
    
    if existing_user:
        print("Admin user already exists, updating...")
        user = existing_user
        user.email = email
        user.full_name = full_name
        user.password_hash = generate_password_hash(password)
        user.role = UserRole.GENERAL_ADMIN
        user.active = True
    else:
        print("Creating new admin user...")
        user = User()
        user.username = username
        user.email = email
        user.full_name = full_name
        user.password_hash = generate_password_hash(password)
        user.role = UserRole.GENERAL_ADMIN
        user.active = True
        db.session.add(user)
    
    db.session.commit()
    print(f"✓ Admin user ready!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Email: {email}")
'''
        
        success, output, error = self.run_command(
            [str(python_exe), '-c', admin_script],
            capture_output=True
        )
        
        if success:
            self.print_success("Admin user created successfully")
            self.print_info("Username: admin")
            self.print_info("Password: password123")
            self.print_warning("Remember to change the password after first login!")
            return True
        else:
            self.print_error(f"Failed to create admin user: {error}")
            return False
            
    def verify_installation(self):
        """Verify the installation is working"""
        self.print_header("Verifying Installation")
        
        venv_path = self.project_root / 'venv'
        if self.is_windows:
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
            
        # Load environment variables
        env = os.environ.copy()
        env_file = self.project_root / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key] = value
                        
        # Test import
        test_script = '''
try:
    from app import app, db
    from k9.models.models import User
    print("✓ All imports successful")
    
    with app.app_context():
        user_count = User.query.count()
        print(f"✓ Database connection working - {user_count} users found")
        
    print("✓ Installation verification complete")
except Exception as e:
    print(f"✗ Verification failed: {e}")
    exit(1)
'''
        
        success, output, error = self.run_command(
            [str(python_exe), '-c', test_script],
            capture_output=True
        )
        
        if success:
            self.print_success("Installation verification passed")
            print(output)
            return True
        else:
            self.print_error(f"Installation verification failed: {error}")
            return False
            
    def print_completion_instructions(self):
        """Print final instructions"""
        self.print_header("Setup Complete!")
        
        venv_path = self.project_root / 'venv'
        if self.is_windows:
            activate_cmd = f"{venv_path}\\Scripts\\activate"
            python_cmd = f"{venv_path}\\Scripts\\python.exe"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
            python_cmd = f"{venv_path}/bin/python"
            
        print(f"""
{Colors.GREEN}🎉 K9 Operations Management System is ready!{Colors.ENDC}

{Colors.BOLD}To start the application:{Colors.ENDC}

1. Activate the virtual environment:
   {Colors.BLUE}{activate_cmd}{Colors.ENDC}

2. Start the development server:
   {Colors.BLUE}flask run --host=0.0.0.0 --port=5000{Colors.ENDC}
   
   Or with Python directly:
   {Colors.BLUE}{python_cmd} -m flask run --host=0.0.0.0 --port=5000{Colors.ENDC}

3. Open your browser to:
   {Colors.BLUE}http://localhost:5000{Colors.ENDC}

4. Login with:
   {Colors.BLUE}Username: admin{Colors.ENDC}
   {Colors.BLUE}Password: password123{Colors.ENDC}

{Colors.BOLD}Important Notes:{Colors.ENDC}
• Environment variables are in .env file
• Change admin password after first login
• Upload directory: {self.project_root}/uploads
• Database migrations are in migrations/ folder

{Colors.BOLD}For VS Code development:{Colors.ENDC}
• Select Python interpreter: {python_cmd}
• Install Python extension
• Consider installing PostgreSQL extension if using PostgreSQL

{Colors.YELLOW}⚠ Remember to change the default admin password!{Colors.ENDC}
""")
        
    def run_setup(self):
        """Run the complete setup process"""
        print(f"{Colors.BOLD}{Colors.GREEN}")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                K9 Operations Management System               ║")
        print("║                    Local Setup Assistant                     ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Checking Git availability", self.check_git),
            ("Setting up virtual environment", self.setup_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up environment variables", self.setup_environment_file),
            ("Creating required directories", self.create_directories),
            ("Running database migrations", self.run_database_migrations),
            ("Creating admin user", self.create_admin_user),
            ("Verifying installation", self.verify_installation),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    failed_steps.append(step_name)
                    self.print_error(f"Step failed: {step_name}")
                    
                    # Ask user if they want to continue
                    response = input(f"\n{Colors.YELLOW}Continue with remaining steps? (y/N): {Colors.ENDC}").strip().lower()
                    if response != 'y':
                        break
            except KeyboardInterrupt:
                self.print_error("Setup interrupted by user")
                sys.exit(1)
            except Exception as e:
                self.print_error(f"Unexpected error in {step_name}: {e}")
                failed_steps.append(step_name)
                
        if failed_steps:
            self.print_warning(f"Setup completed with {len(failed_steps)} issues:")
            for step in failed_steps:
                print(f"  - {step}")
        else:
            self.print_completion_instructions()

if __name__ == "__main__":
    setup = SetupHelper()
    setup.run_setup()