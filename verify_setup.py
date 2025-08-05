#!/usr/bin/env python3
"""
K9 Operations Management System - Setup Verification Script

Run this script after importing the project to ensure everything is configured correctly.
"""

import os
import sys
import sqlite3
from pathlib import Path

def print_status(message, status="INFO"):
    symbols = {"OK": "✅", "ERROR": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Compatible", "OK")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - May have compatibility issues", "WARN")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'sqlalchemy', 'flask_sqlalchemy', 'flask_login', 
        'flask_migrate', 'werkzeug', 'reportlab'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"Package '{package}' - Installed", "OK")
        except ImportError:
            missing.append(package)
            print_status(f"Package '{package}' - Missing", "ERROR")
    
    if missing:
        print_status("Install missing packages with: pip install " + " ".join(missing), "ERROR")
        return False
    return True

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        'main.py', 'app.py', 'models.py', 'routes.py', 'api_routes.py',
        'auth.py', 'config.py', 'simple_seed.py', 'pyproject.toml'
    ]
    
    required_dirs = ['templates', 'static', 'uploads']
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print_status(f"File '{file}' - Found", "OK")
        else:
            missing_files.append(file)
            print_status(f"File '{file}' - Missing", "ERROR")
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print_status(f"Directory '{dir_name}' - Found", "OK")
        else:
            print_status(f"Directory '{dir_name}' - Missing", "ERROR")
            missing_files.append(dir_name)
    
    return len(missing_files) == 0

def check_database_setup():
    """Check database configuration and connectivity"""
    database_url = os.environ.get('DATABASE_URL', '')
    
    if not database_url or database_url.startswith('sqlite'):
        print_status("Database: SQLite mode (Replit compatible)", "OK")
        
        # Check if database file exists
        db_files = ['k9_operations.db', 'instance/k9_operations.db']
        db_found = False
        for db_file in db_files:
            if Path(db_file).exists():
                print_status(f"Database file '{db_file}' - Found", "OK")
                db_found = True
                
                # Try to connect and check tables
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    if tables:
                        print_status(f"Database tables - Found {len(tables)} tables", "OK")
                    else:
                        print_status("Database tables - No tables found, run the app once", "WARN")
                    conn.close()
                except Exception as e:
                    print_status(f"Database connection error: {e}", "ERROR")
                break
        
        if not db_found:
            print_status("Database file - Not found, will be created on first run", "INFO")
        
    else:
        print_status(f"Database: PostgreSQL mode - {database_url}", "INFO")
        print_status("PostgreSQL connection not tested in this script", "INFO")
    
    return True

def check_uuid_compatibility():
    """Check UUID handling in models"""
    try:
        with open('models.py', 'r') as f:
            content = f.read()
            
        if 'get_uuid_column()' in content:
            print_status("UUID compatibility function - Found", "OK")
        else:
            print_status("UUID compatibility function - Missing", "ERROR")
            return False
            
        if 'default_uuid' in content:
            print_status("UUID default function - Found", "OK")
        else:
            print_status("UUID default function - Missing", "ERROR")
            return False
            
        return True
    except Exception as e:
        print_status(f"Error checking UUID compatibility: {e}", "ERROR")
        return False

def check_routes_compatibility():
    """Check routes for UUID object usage"""
    try:
        with open('routes.py', 'r') as f:
            content = f.read()
            
        if 'uuid.UUID(' in content:
            print_status("Routes contain UUID object conversions - PROBLEMATIC", "ERROR")
            print_status("This may cause SQLite compatibility issues", "ERROR")
            return False
        else:
            print_status("Routes UUID compatibility - OK", "OK")
            return True
    except Exception as e:
        print_status(f"Error checking routes: {e}", "ERROR")
        return False

def check_environment():
    """Check environment variables"""
    session_secret = os.environ.get('SESSION_SECRET')
    if session_secret:
        print_status("SESSION_SECRET environment variable - Set", "OK")
    else:
        print_status("SESSION_SECRET environment variable - Using default", "INFO")
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print_status(f"DATABASE_URL environment variable - Set", "OK")
    else:
        print_status("DATABASE_URL environment variable - Using SQLite default", "OK")
    
    return True

def main():
    """Main verification function"""
    print("🔍 K9 Operations Management System - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Database Setup", check_database_setup),
        ("UUID Compatibility", check_uuid_compatibility),
        ("Routes Compatibility", check_routes_compatibility),
        ("Environment Variables", check_environment),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"Check failed with error: {e}", "ERROR")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {check_name}: {status}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("System appears ready for use!", "OK")
        print("\n🚀 Next steps:")
        print("1. Start the application: Click 'Run' in Replit")
        print("2. Wait for: '✓ Default admin user created successfully'")
        print("3. Login with: admin / admin123")
        print("4. Optional: Run 'python simple_seed.py' for sample data")
    else:
        print_status(f"Found {total - passed} issues that need attention", "WARN")
        print("\n🔧 Recommended actions:")
        print("1. Address the failed checks above")
        print("2. Refer to README.md or SETUP.md for detailed instructions")
        print("3. Try deleting database file and restarting if UUID issues persist")

if __name__ == "__main__":
    main()