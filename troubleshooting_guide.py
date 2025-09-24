#!/usr/bin/env python3
"""
K9 Operations Management System - Troubleshooting Guide Generator

This script generates a comprehensive troubleshooting guide for common issues.
"""

def generate_troubleshooting_guide():
    """Generate comprehensive troubleshooting guide"""
    
    guide = """
# K9 Operations Management System - Troubleshooting Guide

## Common Setup Issues

### 1. Python Version Issues

#### Problem: "Python version not supported"
```
Error: Python 3.8.10 is not supported. Requires Python 3.11+
```

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS with Homebrew
brew install python@3.11

# Verify installation
python3.11 --version
```

#### Problem: "python: command not found"
**Solutions:**
```bash
# Ubuntu/Debian
sudo apt install python3.11
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# macOS - add to ~/.zshrc or ~/.bash_profile
export PATH="/opt/homebrew/bin:$PATH"
alias python=python3.11
```

### 2. Virtual Environment Issues

#### Problem: "Failed to create virtual environment"
```
Error: The virtual environment was not created successfully
```

**Solutions:**
```bash
# Ensure venv module is available
python3.11 -m pip install virtualenv

# Alternative: use virtualenv directly
virtualenv -p python3.11 venv

# Windows: use py launcher
py -3.11 -m venv venv

# Clean up and retry
rm -rf venv
python3.11 -m venv venv
```

#### Problem: "Virtual environment not activating"
**Solutions:**
```bash
# Linux/macOS
source venv/bin/activate

# Windows Command Prompt
venv\\Scripts\\activate.bat

# Windows PowerShell
venv\\Scripts\\Activate.ps1

# Verify activation (should show venv path)
which python
```

### 3. Dependency Installation Issues

#### Problem: "No module named 'uv'"
```
ModuleNotFoundError: No module named 'uv'
```

**Solutions:**
```bash
# Install uv package manager
pip install uv

# Or use pip directly for dependencies
pip install -e .

# Clear cache and retry
pip cache purge
pip install --no-cache-dir -e .
```

#### Problem: "psycopg2 installation failed"
```
Error: Microsoft Visual C++ 14.0 is required
```

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt install build-essential libpq-dev python3-dev

# macOS
brew install postgresql

# Windows - install Visual Studio Build Tools
# Or use binary wheel:
pip install psycopg2-binary

# Alternative for all platforms
pip install psycopg2-binary
```

#### Problem: "ReportLab installation failed"
```
Error: Failed building wheel for reportlab
```

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev libjpeg-dev zlib1g-dev

# macOS
brew install jpeg zlib

# Windows
pip install --only-binary=all reportlab

# Or install from wheel
pip install reportlab --only-binary=reportlab
```

### 4. Environment Variable Issues

#### Problem: "SESSION_SECRET not set"
```
RuntimeError: SESSION_SECRET environment variable is required
```

**Solutions:**
```bash
# Generate secure session secret
python -c "import secrets; print('SESSION_SECRET=' + secrets.token_urlsafe(32))" >> .env

# Or manually add to .env file
echo "SESSION_SECRET=your-very-long-secret-key-here" >> .env

# Verify .env file exists and has correct format
cat .env
```

#### Problem: "Environment variables not loading"
**Solutions:**
```bash
# Check .env file format (no spaces around =)
# CORRECT:
SESSION_SECRET=abc123
DATABASE_URL=sqlite:///k9.db

# INCORRECT:
SESSION_SECRET = abc123
DATABASE_URL = sqlite:///k9.db

# Load environment manually
export $(cat .env | xargs)

# Or use python-dotenv
pip install python-dotenv
```

### 5. Database Issues

#### Problem: "relation 'user' does not exist"
```
psycopg2.errors.UndefinedTable: relation "user" does not exist
```

**Solutions:**
```bash
# Run database migrations
flask db upgrade

# If migrations don't exist, create them
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Check database tables
# SQLite:
sqlite3 k9_operations.db ".tables"

# PostgreSQL:
psql k9operations -c "\\dt"
```

#### Problem: "PostgreSQL connection refused"
```
psycopg2.OperationalError: connection to server on socket failed
```

**Solutions:**
```bash
# Start PostgreSQL service
# Ubuntu/Debian:
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS:
brew services start postgresql

# Windows:
net start postgresql-x64-14

# Check if PostgreSQL is running
pg_isready
```

#### Problem: "role 'k9user' does not exist"
```
psycopg2.OperationalError: FATAL: role "k9user" does not exist
```

**Solutions:**
```bash
# Create PostgreSQL user and database
sudo -u postgres psql -c "CREATE USER k9user WITH PASSWORD 'yourpassword';"
sudo -u postgres psql -c "CREATE DATABASE k9operations OWNER k9user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE k9operations TO k9user;"

# Verify user exists
sudo -u postgres psql -c "\\du"
```

#### Problem: "permission denied for database"
**Solutions:**
```bash
# Grant proper permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE k9operations TO k9user;"
sudo -u postgres psql -c "ALTER USER k9user CREATEDB;"

# Or use superuser for development
sudo -u postgres psql -c "ALTER USER k9user WITH SUPERUSER;"
```

### 6. Flask Application Issues

#### Problem: "ModuleNotFoundError: No module named 'app'"
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**
```bash
# Ensure you're in the correct directory
ls -la  # Should see app.py, main.py, etc.

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/K9
python -m flask run
```

#### Problem: "Flask app won't start"
```
Error: Could not locate a Flask application
```

**Solutions:**
```bash
# Set Flask app environment variable
export FLASK_APP=main.py

# Or run directly
python main.py

# Check if main.py exists and has correct content
cat main.py
```

#### Problem: "Template not found"
```
jinja2.exceptions.TemplateNotFound: base.html
```

**Solutions:**
```bash
# Check template directory structure
ls -la k9/templates/

# Ensure Flask app points to correct template folder
# In app.py:
app = Flask(__name__, template_folder='k9/templates')

# Check file permissions
chmod -R 644 k9/templates/
```

### 7. Static Files Issues

#### Problem: "Static files not loading (404)"
**Solutions:**
```bash
# Check static directory structure
ls -la k9/static/

# Verify static folder configuration in app.py
app = Flask(__name__, static_folder='k9/static')

# Check file permissions
chmod -R 644 k9/static/

# Clear browser cache
# Ctrl+Shift+R (hard refresh)
```

#### Problem: "Arabic fonts not displaying"
**Solutions:**
```bash
# Check if Arabic font exists
ls -la k9/static/fonts/NotoSansArabic-Regular.ttf

# Download missing font
mkdir -p k9/static/fonts
curl -o k9/static/fonts/NotoSansArabic-Regular.ttf "https://fonts.gstatic.com/s/notosansarabic/v18/nwpxtLGrOAZMl5nJ_wfgRg3DrWFZWsnVBJ_sS6tlqHHFlhQ5l3sQWIHPqzCfyGyvu3CBFQLaig.ttf"
```

### 8. File Permission Issues

#### Problem: "Permission denied writing to uploads"
```
PermissionError: [Errno 13] Permission denied: 'uploads'
```

**Solutions:**
```bash
# Create uploads directory with correct permissions
mkdir -p uploads/reports/feeding uploads/reports/veterinary
chmod -R 755 uploads/

# Fix ownership if needed
sudo chown -R $USER:$USER uploads/

# Windows: Run as administrator or check folder properties
```

### 9. Network and Port Issues

#### Problem: "Address already in use"
```
OSError: [Errno 98] Address already in use
```

**Solutions:**
```bash
# Find process using port 5000
lsof -i :5000
netstat -tulpn | grep :5000

# Kill process using port
kill -9 <PID>

# Use different port
flask run --port=5001

# Or stop other Flask applications
```

#### Problem: "Cannot access localhost:5000"
**Solutions:**
```bash
# Check if Flask is running
ps aux | grep flask

# Check firewall
sudo ufw status
sudo ufw allow 5000

# Try different host binding
flask run --host=127.0.0.1 --port=5000

# Check browser console for errors (F12)
```

### 10. Migration Issues

#### Problem: "Migration files not found"
```
alembic.util.exc.CommandError: Can't locate revision identified by
```

**Solutions:**
```bash
# Initialize migrations
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade

# Check migration history
flask db history
```

#### Problem: "Database is ahead of migrations"
**Solutions:**
```bash
# Mark current state as head
flask db stamp head

# Or downgrade and reapply
flask db downgrade
flask db upgrade
```

### 11. VS Code Integration Issues

#### Problem: "Python interpreter not found"
**Solutions:**
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose: `./venv/bin/python` or `./venv/Scripts/python.exe`

#### Problem: "Imports not resolving"
**Solutions:**
```json
// Add to .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.pythonPath": "./venv/bin/python"
}
```

### 12. Performance Issues

#### Problem: "Application is slow"
**Solutions:**
```bash
# Enable Flask debug mode
export FLASK_DEBUG=True

# Use development database settings
# In .env:
SQLALCHEMY_ECHO=False  # Disable SQL logging
FLASK_ENV=development

# Check for N+1 queries in logs
tail -f logs/app.log
```

## Diagnostic Commands

### System Information
```bash
# Check Python version
python --version
python3 --version
python3.11 --version

# Check pip version
pip --version

# Check virtual environment
which python
echo $VIRTUAL_ENV

# Check environment variables
env | grep FLASK
env | grep DATABASE
cat .env
```

### Database Diagnostics
```bash
# Test database connection
# SQLite:
sqlite3 k9_operations.db "SELECT 1;"

# PostgreSQL:
psql k9operations -c "SELECT 1;"

# Check database tables
# SQLite:
sqlite3 k9_operations.db ".schema"

# PostgreSQL:
psql k9operations -c "\\dt"
```

### Flask Diagnostics
```bash
# Test Flask app import
python -c "from app import app; print('Flask app imported successfully')"

# Check Flask routes
python -c "from app import app; print([str(r) for r in app.url_map.iter_rules()])"

# Test basic functionality
python -c "
from app import app, db
with app.app_context():
    print('Database URI:', app.config['SQLALCHEMY_DATABASE_URI'])
    print('Secret key set:', bool(app.secret_key))
"
```

### Network Diagnostics
```bash
# Check if port is open
netstat -tulpn | grep :5000
lsof -i :5000

# Test local connection
curl http://localhost:5000/
curl -I http://127.0.0.1:5000/

# Check firewall
sudo ufw status
```

## Getting Additional Help

### Log Files to Check
1. **Application logs**: `logs/app.log`
2. **Flask debug output**: Terminal where you ran `flask run`
3. **Database logs**: PostgreSQL logs in `/var/log/postgresql/`
4. **System logs**: `journalctl -u postgresql`

### Useful Debug Environment Variables
```bash
# Add to .env for debugging
FLASK_DEBUG=True
SQLALCHEMY_ECHO=True
WERKZEUG_DEBUG_PIN=off
```

### Creating Bug Reports
When reporting issues, include:
1. **Error message**: Full error text
2. **System info**: OS, Python version
3. **Steps to reproduce**: What you did before the error
4. **Environment**: Contents of .env (without sensitive data)
5. **Log files**: Recent error logs

### Emergency Recovery
If everything fails, start fresh:
```bash
# Backup your data
cp -r uploads uploads_backup
pg_dump k9operations > database_backup.sql

# Clean installation
rm -rf venv .env
python3.11 setup_local.py

# Restore data
cp -r uploads_backup uploads
psql k9operations < database_backup.sql
```

---

**Need more help?** Run the verification script to diagnose issues:
```bash
python verify_setup.py
```
"""
    
    return guide

if __name__ == "__main__":
    guide_content = generate_troubleshooting_guide()
    
    # Write to file
    from pathlib import Path
    output_file = Path(__file__).parent / "TROUBLESHOOTING.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✓ Troubleshooting guide generated: {output_file}")
    print("✓ Open TROUBLESHOOTING.md for comprehensive issue resolution")