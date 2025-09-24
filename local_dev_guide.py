#!/usr/bin/env python3
"""
K9 Operations Management System - Local Development Guide Generator

This script generates a comprehensive setup guide for local development.
"""

import os
import platform
from pathlib import Path

def generate_guide():
    """Generate comprehensive setup guide"""
    
    system = platform.system()
    is_windows = system == 'Windows'
    is_linux = system == 'Linux'
    is_mac = system == 'Darwin'
    
    # Detect system-specific commands
    if is_windows:
        python_cmd = "python"
        venv_activate = "venv\\Scripts\\activate"
        pip_cmd = "pip"
    else:
        python_cmd = "python3.11"
        venv_activate = "source venv/bin/activate"
        pip_cmd = "pip3"
    
    guide = f"""
# K9 Operations Management System - Local Development Setup Guide

## System Requirements

### Operating System Support
- ✅ Ubuntu 20.04+ / Debian 11+
- ✅ macOS 11+ (Big Sur)
- ✅ Windows 10/11
- ✅ Other Linux distributions

### Required Software
- **Python**: 3.11 or higher
- **Git**: Any recent version
- **Database**: PostgreSQL 12+ (recommended) or SQLite (development only)
- **Text Editor**: VS Code (recommended) with Python extension

## Quick Setup (Automated)

### Option 1: Fully Automated Setup
```bash
# Clone the repository
git clone https://github.com/odai-dev/K9.git
cd K9

# Run automated setup
{python_cmd} setup_local.py

# Verify installation
{python_cmd} verify_setup.py
```

The automated setup will:
- ✅ Check system requirements
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up environment variables
- ✅ Configure database
- ✅ Run migrations
- ✅ Create admin user
- ✅ Verify installation

## Manual Setup (Step-by-Step)

### Step 1: System Dependencies

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL (optional but recommended)
sudo apt install postgresql postgresql-contrib

# Install Git
sudo apt install git

# Install build tools for Python packages
sudo apt install build-essential libpq-dev
```

#### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install PostgreSQL (optional but recommended)
brew install postgresql

# Install Git
brew install git
```

#### Windows
1. **Python 3.11**: Download from https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH"
   - ✅ Check "pip" during installation

2. **Git**: Download from https://git-scm.com/download/win
   - ✅ Use default settings

3. **PostgreSQL** (optional): Download from https://www.postgresql.org/download/windows/

### Step 2: Clone Repository
```bash
git clone https://github.com/odai-dev/K9.git
cd K9
```

### Step 3: Python Environment Setup
```bash
# Create virtual environment
{python_cmd} -m venv venv

# Activate virtual environment
{venv_activate}

# Upgrade pip
{pip_cmd} install --upgrade pip

# Install uv for faster dependency management
{pip_cmd} install uv

# Install project dependencies
uv pip install -e .
```

### Step 4: Environment Configuration

Create `.env` file in project root:
```bash
# Copy and modify this template
cat > .env << 'EOF'
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SESSION_SECRET=your-secret-key-here

# Database Configuration
# Option 1: SQLite (simple, for development)
DATABASE_URL=sqlite:///k9_operations.db

# Option 2: PostgreSQL (recommended)
# DATABASE_URL=postgresql://k9user:password@localhost/k9operations

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Security Settings
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
EOF
```

### Step 5: Generate Secure Session Secret
```bash
# Generate secure session secret
{python_cmd} -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))" >> .env
```

### Step 6: Database Setup

#### Option A: SQLite (Simpler)
```bash
# SQLite database will be created automatically
# No additional setup required
```

#### Option B: PostgreSQL (Recommended)

**Ubuntu/Debian:**
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user and database
sudo -u postgres psql -c "CREATE USER k9user WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE k9operations OWNER k9user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE k9operations TO k9user;"

# Update .env file
sed -i 's|DATABASE_URL=sqlite:///k9_operations.db|DATABASE_URL=postgresql://k9user:yourpassword@localhost/k9operations|' .env
```

**macOS:**
```bash
# Start PostgreSQL service
brew services start postgresql

# Create database user and database
psql postgres -c "CREATE USER k9user WITH PASSWORD 'yourpassword';"
psql postgres -c "CREATE DATABASE k9operations OWNER k9user;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE k9operations TO k9user;"

# Update .env file
sed -i '' 's|DATABASE_URL=sqlite:///k9_operations.db|DATABASE_URL=postgresql://k9user:yourpassword@localhost/k9operations|' .env
```

**Windows:**
```cmd
# Start PostgreSQL service from Services app or:
net start postgresql-x64-14

# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL shell:
CREATE USER k9user WITH PASSWORD 'yourpassword';
CREATE DATABASE k9operations OWNER k9user;
GRANT ALL PRIVILEGES ON DATABASE k9operations TO k9user;
\\q

# Manually edit .env file to update DATABASE_URL
```

### Step 7: Database Migrations
```bash
# Activate virtual environment
{venv_activate}

# Run database migrations
flask db upgrade
```

### Step 8: Create Admin User
```bash
# Option 1: Use the creation script
{python_cmd} scripts/create_admin_user.py

# Option 2: Create programmatically
{python_cmd} -c "
from app import app, db
from k9.models.models import User, UserRole
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User()
    admin.username = 'admin'
    admin.email = 'admin@k9ops.local'
    admin.full_name = 'System Administrator'
    admin.password_hash = generate_password_hash('password123')
    admin.role = UserRole.GENERAL_ADMIN
    admin.active = True
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin / password123')
"
```

### Step 9: Create Required Directories
```bash
# Create upload directories
mkdir -p uploads/reports/feeding uploads/reports/veterinary

# Create logs directory
mkdir -p logs
```

### Step 10: Start the Application
```bash
# Activate virtual environment
{venv_activate}

# Start Flask development server
flask run --host=0.0.0.0 --port=5000

# Alternative: Start with Python directly
{python_cmd} -m flask run --host=0.0.0.0 --port=5000
```

### Step 11: Access the Application
1. Open your web browser
2. Navigate to: http://localhost:5000
3. Login with:
   - **Username**: admin
   - **Password**: password123

## VS Code Setup

### Recommended Extensions
```bash
# Install VS Code extensions
code --install-extension ms-python.python
code --install-extension ms-python.pylance
code --install-extension ms-vscode.vscode-json
code --install-extension bradlc.vscode-tailwindcss
code --install-extension formulahendry.auto-rename-tag
```

### Python Interpreter Setup
1. Open VS Code in project directory: `code .`
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
3. Type "Python: Select Interpreter"
4. Choose: `./venv/bin/python` (Linux/macOS) or `.\\venv\\Scripts\\python.exe` (Windows)

### Launch Configuration
Create `.vscode/launch.json`:
```json
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Flask App",
            "type": "python",
            "request": "launch",
            "program": "-m",
            "args": ["flask", "run", "--host=0.0.0.0", "--port=5000"],
            "console": "integratedTerminal",
            "envFile": "${{workspaceFolder}}/.env",
            "cwd": "${{workspaceFolder}}"
        }}
    ]
}}
```

## Common Issues and Solutions

### Issue 1: Python Version Error
```
Error: This project requires Python 3.11 or higher
```
**Solution:**
- Install Python 3.11+ from official website
- On Ubuntu: `sudo apt install python3.11`
- On macOS: `brew install python@3.11`

### Issue 2: Virtual Environment Creation Failed
```
Error: Failed to create virtual environment
```
**Solution:**
```bash
# Install venv module
{pip_cmd} install virtualenv

# Or use virtualenv directly
virtualenv -p {python_cmd} venv
```

### Issue 3: Database Connection Error
```
Error: relation "user" does not exist
```
**Solution:**
```bash
# Run database migrations
{venv_activate}
flask db upgrade
```

### Issue 4: Session Secret Error
```
Error: SESSION_SECRET environment variable is required
```
**Solution:**
```bash
# Generate and add session secret to .env
echo "SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

### Issue 5: Permission Denied on Uploads
```
Error: Permission denied writing to uploads directory
```
**Solution:**
```bash
# Fix permissions
chmod 755 uploads
mkdir -p uploads/reports
chmod -R 755 uploads/
```

### Issue 6: PostgreSQL Connection Failed
```
Error: FATAL: role "k9user" does not exist
```
**Solution:**
```bash
# Create PostgreSQL user
sudo -u postgres createuser -P k9user
sudo -u postgres createdb -O k9user k9operations
```

### Issue 7: Missing Dependencies
```
Error: No module named 'flask'
```
**Solution:**
```bash
# Ensure virtual environment is activated
{venv_activate}

# Reinstall dependencies
{pip_cmd} install -e .
```

### Issue 8: Static Files Not Loading
```
Error: 404 for static files
```
**Solution:**
- Ensure static files exist in `k9/static/`
- Check Flask app configuration for static folder
- Verify file permissions

## Performance Optimization

### Development Settings
```bash
# Add to .env for better development experience
export FLASK_DEBUG=True
export FLASK_ENV=development
export PYTHONPATH=${{PWD}}
```

### Database Optimization
```sql
-- PostgreSQL performance settings (add to postgresql.conf)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

## Security Considerations

### Environment Variables
- ✅ Never commit `.env` file to version control
- ✅ Use strong SESSION_SECRET (32+ characters)
- ✅ Change default admin password immediately
- ✅ Use PostgreSQL for production-like testing

### File Permissions
```bash
# Secure file permissions
chmod 600 .env
chmod 755 uploads/
```

## Testing Setup

### Run Tests
```bash
# Activate virtual environment
{venv_activate}

# Run all tests
pytest

# Run with coverage
pytest --cov=k9 --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Test Database
```bash
# Create test database (PostgreSQL)
createdb k9operations_test

# Set test environment
export DATABASE_URL=postgresql://k9user:password@localhost/k9operations_test
```

## Deployment Preparation

### Environment Variables for Production
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=production-secret-key
WTF_CSRF_ENABLED=True
```

### Database Backup
```bash
# Backup PostgreSQL database
pg_dump k9operations > backup.sql

# Restore from backup
psql k9operations < backup.sql
```

## Support and Troubleshooting

### Getting Help
1. Check this guide for common issues
2. Run verification script: `{python_cmd} verify_setup.py`
3. Check application logs in `logs/` directory
4. Review Flask debug output in terminal

### Log Files
- Application logs: `logs/app.log`
- Database queries: Enable `SQLALCHEMY_ECHO=True`
- Flask debug: Set `FLASK_DEBUG=True`

### Health Check
```bash
# Quick health check
curl http://localhost:5000/
```

---

**🎉 Congratulations! Your K9 Operations Management System is ready for development.**

**Default Login:**
- Username: `admin`
- Password: `password123`

**⚠️ Important:** Change the default admin password after first login!
"""

    return guide

if __name__ == "__main__":
    guide_content = generate_guide()
    
    # Write to file
    output_file = Path(__file__).parent / "LOCAL_SETUP_GUIDE.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✓ Setup guide generated: {output_file}")
    print("✓ Open LOCAL_SETUP_GUIDE.md for complete instructions")