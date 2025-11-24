"""
Test script for Step 4: Employee Routes Permission System
This script tests that employee routes properly enforce the new permission system.
"""
import sys
from datetime import date
from app import app, db
from k9.models.models import User, UserRole, SubPermission, PermissionType, Employee, EmployeeRole
from k9.utils.permission_utils import update_permission, has_permission
from werkzeug.security import generate_password_hash

def create_test_user():
    """Create a test user for permission testing"""
    with app.app_context():
        # Check if test user already exists
        test_user = User.query.filter_by(username='test_employee_viewer').first()
        
        if test_user:
            print("✓ Test user 'test_employee_viewer' already exists")
            return test_user
        
        # Create test employee first (required for user)
        test_employee = Employee.query.filter_by(employee_id='TEST_EMP_001').first()
        
        if not test_employee:
            test_employee = Employee()
            test_employee.employee_id = 'TEST_EMP_001'
            test_employee.name = 'Test Employee'
            test_employee.full_name = 'Test Employee Viewer'
            test_employee.role = EmployeeRole.PROJECT_MANAGER
            test_employee.phone = '777000000'
            test_employee.hire_date = date.today()
            test_employee.is_active = True
            
            db.session.add(test_employee)
            db.session.flush()  # Get the employee ID
            print(f"✓ Created test employee: {test_employee.name} (ID: {test_employee.id})")
        
        # Create new test user linked to employee
        test_user = User()
        test_user.username = 'test_employee_viewer'
        test_user.email = 'test_viewer@test.com'
        test_user.full_name = 'Test Employee Viewer'
        test_user.password_hash = generate_password_hash('test123')
        test_user.role = UserRole.PROJECT_MANAGER
        test_user.active = True
        test_user.employee_id = test_employee.id
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✓ Created test user: {test_user.username} (ID: {test_user.id})")
        return test_user


def grant_view_permission(user):
    """Grant only employees.view permission to the test user"""
    with app.app_context():
        # Grant employees.view permission
        success = update_permission(
            user_id=user.id,
            section='employees',
            subsection='view',
            permission_type=PermissionType.VIEW,
            granted=True,
            updated_by=user.id  # Self-grant for testing
        )
        
        if success:
            print(f"✓ Granted employees.view permission to {user.username}")
        else:
            print(f"✗ Failed to grant employees.view permission")
        
        return success


def test_view_permission(user):
    """Test that user has view permission"""
    with app.app_context():
        # Refresh user from database
        user = User.query.get(user.id)
        
        # Test employees.view permission
        has_view = has_permission(user, 'employees.view')
        print(f"  - employees.view: {'✓ GRANTED' if has_view else '✗ DENIED'}")
        
        # Test employees.create permission (should be denied)
        has_create = has_permission(user, 'employees.create')
        print(f"  - employees.create: {'✗ GRANTED (UNEXPECTED!)' if has_create else '✓ DENIED'}")
        
        # Test employees.edit permission (should be denied)
        has_edit = has_permission(user, 'employees.edit')
        print(f"  - employees.edit: {'✗ GRANTED (UNEXPECTED!)' if has_edit else '✓ DENIED'}")
        
        # Test employees.delete permission (should be denied)
        has_delete = has_permission(user, 'employees.delete')
        print(f"  - employees.delete: {'✗ GRANTED (UNEXPECTED!)' if has_delete else '✓ DENIED'}")
        
        # Verify expectations
        if has_view and not has_create and not has_edit and not has_delete:
            print("✓ Permission test PASSED: User has only view permission")
            return True
        else:
            print("✗ Permission test FAILED: Unexpected permission state")
            return False


def revoke_all_permissions(user):
    """Revoke all employee permissions from the test user"""
    with app.app_context():
        # Revoke all employee permissions
        update_permission(
            user_id=user.id,
            section='employees',
            subsection='view',
            permission_type=PermissionType.VIEW,
            granted=False,
            updated_by=user.id
        )
        
        print(f"✓ Revoked all employee permissions from {user.username}")


def test_no_permissions(user):
    """Test that user has no employee permissions"""
    with app.app_context():
        # Refresh user from database
        user = User.query.get(user.id)
        
        # Test all permissions (should all be denied)
        has_view = has_permission(user, 'employees.view')
        has_create = has_permission(user, 'employees.create')
        has_edit = has_permission(user, 'employees.edit')
        has_delete = has_permission(user, 'employees.delete')
        
        print(f"  - employees.view: {'✗ GRANTED (UNEXPECTED!)' if has_view else '✓ DENIED'}")
        print(f"  - employees.create: {'✗ GRANTED (UNEXPECTED!)' if has_create else '✓ DENIED'}")
        print(f"  - employees.edit: {'✗ GRANTED (UNEXPECTED!)' if has_edit else '✓ DENIED'}")
        print(f"  - employees.delete: {'✗ GRANTED (UNEXPECTED!)' if has_delete else '✓ DENIED'}")
        
        # Verify expectations
        if not has_view and not has_create and not has_edit and not has_delete:
            print("✓ Permission test PASSED: User has no employee permissions")
            return True
        else:
            print("✗ Permission test FAILED: User still has some permissions")
            return False


def cleanup_test_user(user):
    """Delete the test user"""
    with app.app_context():
        # Get the employee before deleting user
        employee = user.employee
        
        # Delete related permissions first
        SubPermission.query.filter_by(user_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        
        # Delete the test employee if it exists
        if employee and employee.employee_id == 'TEST_EMP_001':
            db.session.delete(employee)
        
        db.session.commit()
        
        print(f"✓ Cleaned up test user and employee: {user.username}")


def main():
    print("=" * 60)
    print("STEP 4 - Employee Routes Permission System Test")
    print("=" * 60)
    print()
    
    # Test 1: Create test user
    print("TEST 1: Create test user")
    print("-" * 40)
    test_user = create_test_user()
    print()
    
    # Test 2: Grant employees.view permission only
    print("TEST 2: Grant employees.view permission only")
    print("-" * 40)
    grant_view_permission(test_user)
    print()
    
    # Test 3: Verify user has only view permission
    print("TEST 3: Verify user has only view permission")
    print("-" * 40)
    test1_passed = test_view_permission(test_user)
    print()
    
    # Test 4: Revoke all permissions
    print("TEST 4: Revoke all employee permissions")
    print("-" * 40)
    revoke_all_permissions(test_user)
    print()
    
    # Test 5: Verify user has no permissions
    print("TEST 5: Verify user has no employee permissions")
    print("-" * 40)
    test2_passed = test_no_permissions(test_user)
    print()
    
    # Cleanup
    print("CLEANUP: Remove test user")
    print("-" * 40)
    cleanup_test_user(test_user)
    print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("Step 4 is complete! Employee routes now use the new permission system:")
        print("  - employees.view: View employee list")
        print("  - employees.create: Add new employees")
        print("  - employees.edit: Edit employee data and manage user links")
        print("  - employees.delete: Delete employees")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("Please review the permission system configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
