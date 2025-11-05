#!/usr/bin/env python3
"""
Migration Script: Link All Users to Employee Records

IMPORTANT: This migration is now handled by Alembic migrations.
Please use the following command instead:

    flask db upgrade

If you need to manually verify the migration, you can use:

    flask db current    # Check current migration version
    flask db upgrade    # Apply pending migrations
    
The Alembic migration will:
1. Add employee_id column to user table (initially nullable)
2. Link existing users to their employee records
3. Create employee records for users without them
4. Make employee_id required (NOT NULL)

Usage:
    python scripts/migrate_users_to_employees.py  # For verification only
"""

import os
import sys
from datetime import date

def migrate_users_to_employees():
    """Migrate existing users to have required employee linkage"""
    
    # Import Flask app and models
    try:
        from app import app, db
        from k9.models.models import User, Employee, EmployeeRole, UserRole
    except ImportError as e:
        print(f"Error importing application modules: {e}")
        print("Make sure you're running this script from the application directory.")
        sys.exit(1)
    
    with app.app_context():
        print("=" * 70)
        print("User to Employee Migration Script")
        print("=" * 70)
        print("\nThis script will ensure all users are linked to employee records.")
        print("All users must be employees to comply with the new security policy.\n")
        
        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users in the database.\n")
        
        if len(users) == 0:
            print("No users found. Migration not needed.")
            return
        
        users_migrated = 0
        users_already_linked = 0
        users_with_errors = 0
        
        for user in users:
            try:
                # Check if user already has employee_id set
                if user.employee_id:
                    users_already_linked += 1
                    print(f"✓ User '{user.username}' already linked to employee")
                    continue
                
                # Try to find employee linked via user_account_id (old relationship)
                employee = Employee.query.filter_by(user_account_id=user.id).first()
                
                if employee:
                    # Link existing employee to user
                    user.employee_id = employee.id
                    db.session.add(user)
                    users_migrated += 1
                    print(f"✓ Linked user '{user.username}' to existing employee '{employee.name}' (ID: {employee.employee_id})")
                else:
                    # Create new employee record for this user
                    # Generate unique employee ID
                    base_emp_id = f"EMP{str(user.id)[:8]}"
                    emp_id = base_emp_id
                    counter = 1
                    while Employee.query.filter_by(employee_id=emp_id).first():
                        emp_id = f"{base_emp_id}_{counter}"
                        counter += 1
                    
                    # Map user role to employee role
                    role_mapping = {
                        UserRole.HANDLER: EmployeeRole.HANDLER,
                        UserRole.TRAINER: EmployeeRole.TRAINER,
                        UserRole.BREEDER: EmployeeRole.BREEDER,
                        UserRole.VET: EmployeeRole.VET,
                        UserRole.PROJECT_MANAGER: EmployeeRole.PROJECT_MANAGER,
                        UserRole.GENERAL_ADMIN: EmployeeRole.PROJECT_MANAGER,
                    }
                    employee_role = role_mapping.get(user.role, EmployeeRole.PROJECT_MANAGER)
                    
                    # Generate phone number if not set
                    phone = user.phone if hasattr(user, 'phone') and user.phone else f"+967{str(user.id)[:9]}"
                    
                    # Create new employee
                    new_employee = Employee(
                        name=user.full_name,
                        employee_id=emp_id,
                        role=employee_role,
                        phone=phone,
                        email=user.email,
                        hire_date=user.created_at.date() if user.created_at else date.today(),
                        is_active=user.active,
                        user_account_id=user.id
                    )
                    
                    db.session.add(new_employee)
                    db.session.flush()  # Get employee ID
                    
                    # Link user to new employee
                    user.employee_id = new_employee.id
                    db.session.add(user)
                    
                    users_migrated += 1
                    print(f"✓ Created new employee record for user '{user.username}' (Employee ID: {emp_id})")
                
            except Exception as e:
                users_with_errors += 1
                print(f"✗ Error migrating user '{user.username}': {e}")
                db.session.rollback()
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 70)
            print("Migration Summary:")
            print("=" * 70)
            print(f"Total users: {len(users)}")
            print(f"Already linked: {users_already_linked}")
            print(f"Migrated: {users_migrated}")
            print(f"Errors: {users_with_errors}")
            print("\n✓ Migration completed successfully!")
            print("\nAll users are now linked to employee records.")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error committing migration: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_users_to_employees()
