"""
Comprehensive Permissions System Diagnostic and Test Script

This script performs a full end-to-end test of the permissions system:
1. Creates test users (GENERAL_ADMIN and PROJECT_MANAGER)
2. Creates a test project
3. Grants specific permissions to PROJECT_MANAGER
4. Validates permissions are stored correctly in database
5. Simulates login and checks if permissions are loaded correctly
6. Tests UI permission checking logic
7. Tests backend permission checking logic

Run this to diagnose and validate the permissions system.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from k9.models.models import User, UserRole, Employee, EmployeeRole, Project, SubPermission, PermissionType
from k9.utils.default_permissions import create_base_permissions_for_user
from k9.utils.permission_utils import has_permission, get_user_permissions_matrix, get_sections_for_user
from k9.utils.utils import get_user_permissions
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import uuid


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")


def print_error(message):
    """Print an error message"""
    print(f"✗ {message}")


def print_info(message):
    """Print an info message"""
    print(f"ℹ {message}")


def cleanup_test_data():
    """Clean up any existing test data"""
    print_section("Cleaning up existing test data")
    
    try:
        # Delete test users and related data
        test_users = User.query.filter(User.username.in_(['test_admin', 'test_pm'])).all()
        for user in test_users:
            # Delete SubPermissions
            SubPermission.query.filter_by(user_id=user.id).delete()
            # Delete User
            db.session.delete(user)
        
        # Delete test employees
        test_employees = Employee.query.filter(Employee.employee_id.in_(['TEST_ADMIN_001', 'TEST_PM_001'])).all()
        for emp in test_employees:
            db.session.delete(emp)
        
        # Delete test project
        test_project = Project.query.filter_by(name='Test Project for Permissions').first()
        if test_project:
            db.session.delete(test_project)
        
        db.session.commit()
        print_success("Test data cleaned up successfully")
    except Exception as e:
        db.session.rollback()
        print_error(f"Error during cleanup: {e}")


def create_test_users():
    """Create test users for the diagnostic"""
    print_section("Creating Test Users")
    
    try:
        # Create GENERAL_ADMIN employee (using PROJECT_MANAGER employee role)
        admin_employee = Employee()
        admin_employee.employee_id = 'TEST_ADMIN_001'
        admin_employee.name = 'Test Admin User'
        admin_employee.role = EmployeeRole.PROJECT_MANAGER  # No ADMIN role in EmployeeRole
        admin_employee.phone = '1234567890'
        admin_employee.email = 'admin@test.local'
        admin_employee.hire_date = date.today()
        admin_employee.is_active = True
        db.session.add(admin_employee)
        db.session.flush()
        
        # Create GENERAL_ADMIN user
        admin_user = User()
        admin_user.username = 'test_admin'
        admin_user.email = 'admin@test.local'
        admin_user.password_hash = generate_password_hash('admin123')
        admin_user.role = UserRole.GENERAL_ADMIN
        admin_user.full_name = 'Test Admin User'
        admin_user.active = True
        admin_user.employee_id = admin_employee.id
        db.session.add(admin_user)
        db.session.flush()
        print_success(f"Created GENERAL_ADMIN user: {admin_user.username} (ID: {admin_user.id})")
        
        # Create PROJECT_MANAGER employee
        pm_employee = Employee()
        pm_employee.employee_id = 'TEST_PM_001'
        pm_employee.name = 'Test Project Manager'
        pm_employee.role = EmployeeRole.PROJECT_MANAGER
        pm_employee.phone = '0987654321'
        pm_employee.email = 'pm@test.local'
        pm_employee.hire_date = date.today()
        pm_employee.is_active = True
        db.session.add(pm_employee)
        db.session.flush()
        
        # Create PROJECT_MANAGER user
        pm_user = User()
        pm_user.username = 'test_pm'
        pm_user.email = 'pm@test.local'
        pm_user.password_hash = generate_password_hash('pm123')
        pm_user.role = UserRole.PROJECT_MANAGER
        pm_user.full_name = 'Test Project Manager'
        pm_user.active = True
        pm_user.employee_id = pm_employee.id
        db.session.add(pm_user)
        db.session.flush()
        print_success(f"Created PROJECT_MANAGER user: {pm_user.username} (ID: {pm_user.id})")
        
        # Create base permissions for PM
        permissions_created = create_base_permissions_for_user(pm_user, db.session)
        print_success(f"Created {permissions_created} base permissions for PROJECT_MANAGER")
        
        # Create test project
        project = Project()
        project.name = 'Test Project for Permissions'
        project.code = 'TEST-PERM-001'
        project.main_task = 'Testing Permissions System'
        project.description = 'Test project for permissions diagnostic'
        project.manager_id = pm_user.id
        project.start_date = date.today()
        project.is_active = True
        db.session.add(project)
        db.session.flush()
        print_success(f"Created test project: {project.name} (ID: {project.id})")
        
        db.session.commit()
        
        return admin_user, pm_user, project
        
    except Exception as e:
        db.session.rollback()
        print_error(f"Error creating test users: {e}")
        raise


def test_permission_storage(pm_user, project):
    """Test that permissions are stored correctly in the database"""
    print_section("Testing Permission Storage")
    
    try:
        # Check base permissions were created
        base_perms = SubPermission.query.filter_by(
            user_id=pm_user.id,
            is_granted=True
        ).all()
        
        print_info(f"Found {len(base_perms)} base permissions for PROJECT_MANAGER")
        
        if len(base_perms) == 0:
            print_error("NO BASE PERMISSIONS CREATED! This is a critical issue.")
            return False
        
        # Print some of the base permissions
        print_info("Sample base permissions:")
        for perm in base_perms[:5]:
            print(f"   - {perm.section}.{perm.subsection or '(none)'} [{perm.permission_type.value}]")
        
        print_success("Base permissions stored correctly in database")
        
        # Now grant some additional permissions via the API logic
        from k9.utils.permission_utils import update_permission
        
        # Grant some additional permissions
        additional_perms = [
            ('dogs', None, PermissionType.CREATE, "Create Dogs"),
            ('dogs', None, PermissionType.DELETE, "Delete Dogs"),
            ('training', None, PermissionType.CREATE, "Create Training"),
            ('training', None, PermissionType.EDIT, "Edit Training"),
        ]
        
        print_info("Granting additional permissions...")
        for section, subsection, perm_type, desc in additional_perms:
            success = update_permission(
                user_id=pm_user.id,
                section=section,
                subsection=subsection or "",
                permission_type=perm_type,
                granted=True,
                updated_by=pm_user.id,  # Self-granted for test
                project_id=None
            )
            if success:
                print_success(f"Granted: {desc}")
            else:
                print_error(f"Failed to grant: {desc}")
        
        db.session.commit()
        
        # Verify the permissions were stored
        new_perms = SubPermission.query.filter_by(
            user_id=pm_user.id,
            is_granted=True
        ).all()
        
        print_success(f"Total permissions after granting: {len(new_perms)}")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print_error(f"Error testing permission storage: {e}")
        return False


def test_permission_loading(pm_user):
    """Test that permissions are loaded correctly for the user"""
    print_section("Testing Permission Loading")
    
    try:
        # Test has_permission function
        test_permissions = [
            ('dogs.view', True, "Dogs View (base permission)"),
            ('dogs.create', True, "Dogs Create (granted)"),
            ('dogs.delete', True, "Dogs Delete (granted)"),
            ('training.view', True, "Training View (base permission)"),
            ('training.create', True, "Training Create (granted)"),
            ('employees.delete', False, "Employees Delete (not granted)"),
            ('admin.permissions.edit', False, "Admin Permissions Edit (not granted)"),
        ]
        
        print_info("Testing has_permission() function:")
        all_passed = True
        for perm_key, expected, desc in test_permissions:
            result = has_permission(pm_user, perm_key)
            if result == expected:
                print_success(f"{desc}: {'GRANTED' if result else 'DENIED'} (as expected)")
            else:
                print_error(f"{desc}: {'GRANTED' if result else 'DENIED'} (expected {'GRANTED' if expected else 'DENIED'})")
                all_passed = False
        
        if not all_passed:
            print_error("Some permission checks failed!")
            return False
        
        # Test get_user_permissions function
        print_info("\nTesting get_user_permissions() function:")
        user_perms = get_user_permissions(pm_user)
        print_info(f"User permissions: {user_perms}")
        
        # Check that sections with any granted permission show as True
        expected_sections = ['dogs', 'projects', 'training', 'employees']
        for section in expected_sections:
            if user_perms.get(section):
                print_success(f"Section '{section}' is accessible")
            else:
                print_error(f"Section '{section}' should be accessible but shows as False")
                all_passed = False
        
        # Test get_sections_for_user function
        print_info("\nTesting get_sections_for_user() function:")
        sections = get_sections_for_user(pm_user)
        print_info(f"Accessible sections: {sections}")
        
        if len(sections) == 0:
            print_error("NO SECTIONS ACCESSIBLE! This is a critical issue.")
            return False
        
        print_success(f"User has access to {len(sections)} sections")
        
        # Test get_user_permissions_matrix function
        print_info("\nTesting get_user_permissions_matrix() function:")
        matrix = get_user_permissions_matrix(pm_user.id)
        if matrix:
            print_success(f"Permissions matrix generated with {len(matrix)} sections")
        else:
            print_error("Permissions matrix is empty!")
            return False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Error testing permission loading: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_rendering(pm_user):
    """Test UI template functions for permission-based rendering"""
    print_section("Testing UI Rendering Logic")
    
    try:
        # Simulate template context
        print_info("Testing template helper functions:")
        
        # Test get_user_permissions (used in templates)
        user_perms = get_user_permissions(pm_user)
        
        # Simulate navigation rendering
        nav_items = {
            'dogs': user_perms.get('dogs', False),
            'employees': user_perms.get('employees', False),
            'training': user_perms.get('training', False),
            'veterinary': user_perms.get('veterinary', False),
            'projects': user_perms.get('projects', False),
            'reports': user_perms.get('reports', False),
            'admin': user_perms.get('admin', False),
        }
        
        print_info("Navigation visibility simulation:")
        for nav, visible in nav_items.items():
            status = "VISIBLE" if visible else "HIDDEN"
            symbol = "✓" if visible else "✗"
            print(f"   {symbol} {nav.title()}: {status}")
        
        # Check if expected items are visible
        expected_visible = ['dogs', 'employees', 'training', 'projects']
        expected_hidden = ['admin']
        
        all_correct = True
        for item in expected_visible:
            if not nav_items.get(item):
                print_error(f"'{item}' should be VISIBLE but is HIDDEN")
                all_correct = False
        
        for item in expected_hidden:
            if nav_items.get(item):
                print_error(f"'{item}' should be HIDDEN but is VISIBLE")
                all_correct = False
        
        if all_correct:
            print_success("UI rendering logic works correctly")
        else:
            print_error("UI rendering logic has issues")
        
        return all_correct
        
    except Exception as e:
        print_error(f"Error testing UI rendering: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_protection(pm_user):
    """Test backend route protection logic"""
    print_section("Testing Backend Route Protection")
    
    try:
        print_info("Testing permission decorator logic:")
        
        # Test has_permission function (used by decorators)
        test_routes = [
            ('dogs.view', True, "GET /dogs (should allow)"),
            ('dogs.create', True, "POST /dogs/create (should allow)"),
            ('dogs.delete', True, "DELETE /dogs/<id> (should allow)"),
            ('employees.create', False, "POST /employees/create (should deny)"),
            ('admin.permissions.edit', False, "POST /admin/permissions/update (should deny)"),
        ]
        
        all_passed = True
        for perm_key, expected_allow, route_desc in test_routes:
            has_perm = has_permission(pm_user, perm_key)
            if has_perm == expected_allow:
                status = "ALLOWED" if has_perm else "DENIED"
                print_success(f"{route_desc}: {status}")
            else:
                status = "ALLOWED" if has_perm else "DENIED"
                expected = "ALLOWED" if expected_allow else "DENIED"
                print_error(f"{route_desc}: {status} (expected {expected})")
                all_passed = False
        
        if all_passed:
            print_success("Backend route protection logic works correctly")
        else:
            print_error("Backend route protection has issues")
        
        return all_passed
        
    except Exception as e:
        print_error(f"Error testing backend protection: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_final_report(results):
    """Print final diagnostic report"""
    print_section("FINAL DIAGNOSTIC REPORT")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print()
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    if failed_tests == 0:
        print_success("ALL TESTS PASSED! Permissions system is working correctly.")
        print_info("\nThe permissions system is fully functional:")
        print_info("  1. Permissions are stored correctly in database")
        print_info("  2. Permissions are loaded correctly for users")
        print_info("  3. UI renders correctly based on permissions")
        print_info("  4. Backend routes are protected correctly")
        print()
        print_info("NEXT STEPS:")
        print_info("  1. Create your actual employees and users")
        print_info("  2. Grant permissions through the admin interface")
        print_info("  3. Test with real user accounts")
    else:
        print_error("SOME TESTS FAILED! There are issues with the permissions system.")
        print()
        print_info("Please review the failed tests above for details.")
        print_info("Common issues:")
        print_info("  - Base permissions not created when user is created")
        print_info("  - Permission loading functions not querying database correctly")
        print_info("  - Template functions not registered in Flask app context")
        print_info("  - Permission decorators not checking permissions correctly")
    
    print("\n" + "=" * 80)


def main():
    """Run the full diagnostic"""
    print_section("K9 PERMISSIONS SYSTEM COMPREHENSIVE DIAGNOSTIC")
    print_info("This script will test the entire permissions system end-to-end")
    print_info("Started at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    with app.app_context():
        results = {}
        
        # Cleanup first
        cleanup_test_data()
        
        # Create test users
        try:
            admin_user, pm_user, project = create_test_users()
        except Exception as e:
            print_error(f"Failed to create test users: {e}")
            return
        
        # Run tests
        results['Permission Storage'] = test_permission_storage(pm_user, project)
        results['Permission Loading'] = test_permission_loading(pm_user)
        results['UI Rendering'] = test_ui_rendering(pm_user)
        results['Backend Protection'] = test_backend_protection(pm_user)
        
        # Print final report
        print_final_report(results)
        
        # Cleanup
        print_section("Cleanup")
        print_info("Cleaning up test data...")
        cleanup_test_data()
        print_success("Test data cleaned up")
        
        print()
        print_info("Diagnostic complete at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == '__main__':
    main()
