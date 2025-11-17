#!/usr/bin/env python3
"""Create test users for testing permissions system"""

from app import app, db
from k9.models.models import User, UserRole, Employee, EmployeeRole
from k9.utils.default_permissions import create_base_permissions_for_user
from werkzeug.security import generate_password_hash
from datetime import date
import sys

def create_test_users():
    with app.app_context():
        print("Creating Test Users...")
        print("=" * 60)
        
        # Delete old test users
        for username in ['test_pm', 'test_handler', 'test_trainer']:
            user = User.query.filter_by(username=username).first()
            if user:
                if user.employee:
                    db.session.delete(user.employee)
                db.session.delete(user)
        db.session.commit()
        
        # Test users data
        test_users = [
            ('PROJECT_MANAGER', 'مدير مشروع تجريبي', 'PM-TEST-001', EmployeeRole.PROJECT_MANAGER),
            ('HANDLER', 'سائس تجريبي', 'HANDLER-TEST-001', EmployeeRole.HANDLER),
            ('TRAINER', 'مدرب تجريبي', 'TRAINER-TEST-001', EmployeeRole.TRAINER),
        ]
        
        for idx, (role_name, ar_name, emp_id, emp_role) in enumerate(test_users):
            # Create employee
            employee = Employee(
                name=ar_name,
                employee_id=emp_id,
                role=emp_role,
                email=f"test_{role_name.lower()}@test.com",
                phone=f"0500000{idx:03d}",
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(employee)
            db.session.flush()
            
            # Create user
            user = User(
                username=f'test_{role_name.lower()}',
                email=f'test_{role_name.lower()}@test.com',
                full_name=ar_name,
                password_hash=generate_password_hash('Test123!'),
                role=UserRole[role_name],
                employee_id=employee.id,
                active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Create base permissions
            perms_created = create_base_permissions_for_user(user, db.session)
            print(f"✓ {user.username:20} - {perms_created} permissions")
        
        db.session.commit()
        print()
        print("✓ Test users created successfully!")
        print("  Password for all: Test123!")

if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
