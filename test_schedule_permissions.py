"""
Test script for Step 6: Schedule permissions implementation
Tests that schedule routes use the new permission system correctly
"""
import sys
from app import app, db
from k9.models.models import User, UserRole, Project
from k9.models.permissions_new import UserPermission
from datetime import datetime
from werkzeug.security import generate_password_hash


def create_test_user():
    """Create a test user with PROJECT_MANAGER role"""
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(username='test_schedule_pm').first()
        if test_user:
            print(f"✓ Test user already exists: {test_user.username}")
            return test_user
        
        # Get first active project
        project = Project.query.filter_by(status='ACTIVE').first()
        if not project:
            print("✗ No active project found. Please create a project first.")
            return None
        
        # Create test user
        test_user = User(
            username='test_schedule_pm',
            email='test_schedule_pm@example.com',
            full_name='Test Schedule PM',
            role=UserRole.PROJECT_MANAGER,
            project_id=str(project.id),
            is_active=True,
            password_hash=generate_password_hash('test123')
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✓ Created test user: {test_user.username}")
        print(f"  - Email: {test_user.email}")
        print(f"  - Password: test123")
        print(f"  - Role: {test_user.role.value}")
        print(f"  - Project: {project.name}")
        
        return test_user


def grant_view_permission(user):
    """Grant only attendance.view permission to user"""
    with app.app_context():
        # Remove all existing permissions
        UserPermission.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # Grant attendance.view permission
        view_perm = UserPermission(
            user_id=user.id,
            permission_key='attendance.view',
            is_granted=True,
            project_id=user.project_id
        )
        
        db.session.add(view_perm)
        db.session.commit()
        
        print(f"\n✓ Granted 'attendance.view' permission to {user.username}")
        print(f"  User should be able to:")
        print(f"    - View schedule list (/schedule, /supervisor/schedules)")
        print(f"    - View specific schedule (/schedule/<id>)")
        print(f"  User should NOT be able to:")
        print(f"    - Create schedules (/schedule/create)")
        print(f"    - Edit schedules (/schedule/<id>/edit)")
        print(f"    - Delete schedule items")


def grant_edit_permission(user):
    """Add attendance.edit permission to user"""
    with app.app_context():
        # Check if edit permission exists
        edit_perm = UserPermission.query.filter_by(
            user_id=user.id,
            permission_key='attendance.edit'
        ).first()
        
        if not edit_perm:
            edit_perm = UserPermission(
                user_id=user.id,
                permission_key='attendance.edit',
                is_granted=True,
                project_id=user.project_id
            )
            db.session.add(edit_perm)
            db.session.commit()
        
        print(f"\n✓ Granted 'attendance.edit' permission to {user.username}")
        print(f"  User should now ALSO be able to:")
        print(f"    - Edit schedules (/schedule/<id>/edit)")
        print(f"    - Lock/unlock schedules")
        print(f"    - Delete schedule items")
        print(f"    - Replace handlers")


def grant_create_permission(user):
    """Add attendance.create permission to user"""
    with app.app_context():
        # Check if create permission exists
        create_perm = UserPermission.query.filter_by(
            user_id=user.id,
            permission_key='attendance.create'
        ).first()
        
        if not create_perm:
            create_perm = UserPermission(
                user_id=user.id,
                permission_key='attendance.create',
                is_granted=True,
                project_id=user.project_id
            )
            db.session.add(create_perm)
            db.session.commit()
        
        print(f"\n✓ Granted 'attendance.create' permission to {user.username}")
        print(f"  User should now ALSO be able to:")
        print(f"    - Create new schedules (/schedule/create, /supervisor/schedules/create)")


def remove_all_permissions(user):
    """Remove all permissions from user"""
    with app.app_context():
        count = UserPermission.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        print(f"\n✓ Removed all {count} permissions from {user.username}")
        print(f"  User should NOT be able to access ANY schedule routes")
        print(f"  All schedule routes should redirect to dashboard with error message")


def list_user_permissions(user):
    """List all permissions for a user"""
    with app.app_context():
        user = User.query.get(user.id)
        perms = UserPermission.query.filter_by(user_id=user.id, is_granted=True).all()
        
        print(f"\nCurrent permissions for {user.username}:")
        if perms:
            for perm in perms:
                print(f"  - {perm.permission_key}")
        else:
            print(f"  (No permissions granted)")


def main():
    print("=" * 70)
    print("STEP 6: Schedule Permissions Test")
    print("=" * 70)
    
    # Create test user
    print("\n1. Creating test user...")
    user = create_test_user()
    if not user:
        return
    
    # Test 1: View only permission
    print("\n" + "=" * 70)
    print("TEST 1: User with attendance.view only")
    print("=" * 70)
    grant_view_permission(user)
    list_user_permissions(user)
    print("\n📝 Manual Test Required:")
    print(f"   1. Login as: {user.username} / test123")
    print(f"   2. Navigate to /schedule or /supervisor/schedules")
    print(f"   3. Verify you CAN view schedules")
    print(f"   4. Try to access /schedule/create")
    print(f"   5. Verify you get 'ليس لديك صلاحية لتنفيذ هذا الإجراء' message")
    
    input("\nPress Enter when done testing VIEW permission...")
    
    # Test 2: Add edit permission
    print("\n" + "=" * 70)
    print("TEST 2: User with attendance.view + attendance.edit")
    print("=" * 70)
    grant_edit_permission(user)
    list_user_permissions(user)
    print("\n📝 Manual Test Required:")
    print(f"   1. Still logged in as: {user.username}")
    print(f"   2. Navigate to a schedule detail page")
    print(f"   3. Click 'Edit' - verify you CAN now access edit page")
    print(f"   4. Try locking/unlocking a schedule - should work")
    print(f"   5. Try /schedule/create - should still be blocked")
    
    input("\nPress Enter when done testing EDIT permission...")
    
    # Test 3: Add create permission
    print("\n" + "=" * 70)
    print("TEST 3: User with all schedule permissions")
    print("=" * 70)
    grant_create_permission(user)
    list_user_permissions(user)
    print("\n📝 Manual Test Required:")
    print(f"   1. Still logged in as: {user.username}")
    print(f"   2. Navigate to /schedule/create")
    print(f"   3. Verify you CAN now create schedules")
    
    input("\nPress Enter when done testing CREATE permission...")
    
    # Test 4: Remove all permissions
    print("\n" + "=" * 70)
    print("TEST 4: User with NO permissions")
    print("=" * 70)
    remove_all_permissions(user)
    list_user_permissions(user)
    print("\n📝 Manual Test Required:")
    print(f"   1. Still logged in as: {user.username}")
    print(f"   2. Try to access ANY schedule route")
    print(f"   3. Verify all routes are blocked with error message")
    print(f"   4. You should be redirected to dashboard")
    
    input("\nPress Enter when done testing NO PERMISSIONS...")
    
    # Cleanup option
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print("\nTo cleanup test user, run:")
    print(f"  python -c 'from app import app, db; from k9.models.models import User; \\")
    print(f"    u = User.query.filter_by(username=\"test_schedule_pm\").first(); \\")
    print(f"    db.session.delete(u) if u else None; db.session.commit()'")


if __name__ == '__main__':
    main()
