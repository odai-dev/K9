# Setup Instructions for K9 Operations Management System

## Replit Import & Setup (Recommended)

When importing this project to a new Replit account, follow these steps to ensure proper setup:

### Step 1: Import the Project
1. Fork or import the repository into your Replit account
2. Wait for Replit to automatically detect the Python environment

### Step 2: Verify Dependencies
The project uses `pyproject.toml` for dependency management. Dependencies should install automatically, but if needed:
```bash
# Check if dependencies are installed
python -c "import flask, sqlalchemy; print('Dependencies OK')"

# If missing, install manually
python -m pip install flask flask-sqlalchemy flask-login flask-migrate gunicorn psycopg2-binary reportlab werkzeug email-validator
```

### Step 3: Database Setup
**IMPORTANT**: The system automatically uses PostgreSQL for production compatibility.

1. **Clean Start** (recommended for imports):
```bash
# Database is automatically configured via Replit environment variables
# No manual setup required - PostgreSQL database created automatically
```

2. **Environment Variables** (automatic):
   - `DATABASE_URL`: Automatically configured by Replit
   - `SESSION_SECRET`: Automatically generated if not set
   - All environment variables managed by Replit infrastructure

### Step 4: Start the Application
Click the "Run" button in Replit or use:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Step 5: Verify Setup
1. **Check Application Startup**:
   - Look for: `✓ Default admin user created successfully`
   - Application should be accessible on port 5000

2. **Test Login**:
   - Username: `admin`
   - Password: `admin123`

### Step 6: Add Sample Data
For testing and demonstration:
```bash
python simple_seed.py
```

This creates:
- 5 sample dogs with various specializations
- 4 employees (handlers, vet, trainer, project manager)
- 3 sample projects
- Additional user accounts

## Troubleshooting Import Issues

### Database Connection Errors
If you see database connection errors:

1. **Check Environment Variables**:
```bash
# Verify DATABASE_URL is set (should be automatic in Replit)
echo $DATABASE_URL
```

2. **Restart Application**:
   - Stop the current run
   - Click "Run" again
   - Database connection will be recreated automatically

3. **Verify PostgreSQL Compatibility**:
   The codebase handles PostgreSQL natively with UUID support:
   - Models use native UUID columns for PostgreSQL
   - Automatic fallback to string UUIDs for SQLite (local development)
   - Connection pooling configured for production use

### Missing Dependencies
```bash
# Check what's installed
pip list | grep -E "(flask|sqlalchemy|werkzeug)"

# Install missing packages
pip install <missing-package-name>
```

### Database Permission Issues
```bash
# Check file permissions
ls -la k9_operations.db

# Fix permissions if needed
chmod 664 k9_operations.db
```

## Manual Database Reset

If you encounter persistent database issues:

```bash
# 1. Stop the application
# 2. Remove database files
rm -f k9_operations.db instance/k9_operations.db

# 3. Start fresh
python main.py

# 4. Add sample data
python simple_seed.py
```

## Environment-Specific Notes

### Replit Environment
- PostgreSQL database automatically configured
- File uploads stored in `uploads/` directory with security scanning
- Port 5000 automatically configured with proper proxy handling
- Environment variables managed by Replit infrastructure
- No additional server setup needed

### Local Development
```bash
# Optional: Use PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/k9_ops"

# Optional: Custom session secret
export SESSION_SECRET="your-secret-key"

# Run locally
python main.py
```

## Post-Setup Verification

### 1. Check Application Health
- [ ] Application starts without errors
- [ ] Admin user created successfully
- [ ] Database file exists (`k9_operations.db`)
- [ ] Web interface accessible

### 2. Test Core Functionality
- [ ] Login with admin/admin123
- [ ] Navigate to Dogs section
- [ ] Navigate to Employees section
- [ ] Navigate to Projects section
- [ ] File upload works (try adding a dog photo)

### 3. Test Sample Data (if added)
- [ ] 5 dogs visible in Dogs section
- [ ] 4 employees visible in Employees section
- [ ] 3 projects visible in Projects section
- [ ] Additional login accounts work

## Common Patterns for Issues

### Pattern 1: "Module not found" errors
**Solution**: Dependencies not installed
```bash
pip install -r requirements.txt
```

### Pattern 2: "UUID not supported" errors
**Solution**: Database needs reset for SQLite compatibility
```bash
rm k9_operations.db && python main.py
```

### Pattern 3: "Permission denied" errors
**Solution**: File permissions issue
```bash
chmod 755 uploads/ && chmod 664 k9_operations.db
```

### Pattern 4: "Template not found" errors
**Solution**: Working directory issue
```bash
# Ensure you're in the project root
pwd
# Should show the directory containing main.py
```

## Getting Support

1. **Check Logs**: Look at the Replit console for error messages
2. **Database Issues**: Try database reset steps above
3. **Permission Issues**: Check file permissions in the file tree
4. **Dependency Issues**: Verify all packages in `pyproject.toml` are installed

---

**Quick Summary for Replit Import**:
1. Import repository to Replit
2. Click "Run" button
3. Wait for "Default admin user created successfully"
4. Optional: Run `python simple_seed.py`
5. Login with admin/admin123

That's it! The system should work out of the box in Replit.