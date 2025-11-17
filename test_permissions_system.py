#!/usr/bin/env python3
"""
Test script to verify permissions system is working correctly
Tests:
1. Save permissions to database
2. Read permissions from database  
3. has_permission function works correctly
"""

import sys
sys.path.insert(0, '/home/runner/workspace')

from app import app, db
from k9.models.models import SubPermission, User, PermissionType, Project
from k9.utils.permission_utils import update_permission, has_permission

def test_permissions_system():
    with app.app_context():
        print("="*60)
        print("TESTING PERMISSIONS SYSTEM")
        print("="*60)
        
        # Find a non-admin user to test
        test_user = User.query.filter(User.role != 'GENERAL_ADMIN').first()
        if not test_user:
            print("❌ No non-admin user found for testing")
            return
        
        print(f"\n✓ Test user: {test_user.username} (ID: {test_user.id})")
        print(f"  Role: {test_user.role}")
        
        # Get first project
        project = Project.query.first()
        project_id = project.id if project else None
        print(f"  Test project: {project.name if project else 'No project'}")
        
        # Test 1: Save a new permission
        print("\n" + "="*60)
        print("TEST 1: Saving new permission to database")
        print("="*60)
        
        test_section = "dogs"
        test_subsection = ""
        test_permission_type = PermissionType.VIEW
        
        print(f"Saving permission: {test_section}.{test_subsection or '(main)'}.{test_permission_type.value}")
        print(f"Project ID: {project_id}")
        
        # First, check if permission already exists
        existing = SubPermission.query.filter_by(
            user_id=test_user.id,
            section=test_section,
            subsection=test_subsection,
            permission_type=test_permission_type,
            project_id=project_id
        ).first()
        
        print(f"Existing permission: {existing.is_granted if existing else 'Not found'}")
        
        # Update permission to granted=True
        success = update_permission(
            user_id=test_user.id,
            section=test_section,
            subsection=test_subsection,
            permission_type=test_permission_type,
            granted=True,
            updated_by=test_user.id,  # self-update for testing
            project_id=project_id
        )
        
        if success:
            print("✓ Permission saved successfully")
        else:
            print("❌ Failed to save permission")
            return
        
        # Test 2: Read permission from database
        print("\n" + "="*60)
        print("TEST 2: Reading permission from database")
        print("="*60)
        
        saved_perm = SubPermission.query.filter_by(
            user_id=test_user.id,
            section=test_section,
            subsection=test_subsection,
            permission_type=test_permission_type,
            project_id=project_id
        ).first()
        
        if saved_perm:
            print(f"✓ Permission found in database")
            print(f"  Section: {saved_perm.section}")
            print(f"  Subsection: {saved_perm.subsection or '(empty)'}")
            print(f"  Type: {saved_perm.permission_type.value}")
            print(f"  Is Granted: {saved_perm.is_granted}")
            print(f"  Project ID: {saved_perm.project_id}")
        else:
            print("❌ Permission NOT found in database")
            return
        
        # Test 3: has_permission function
        print("\n" + "="*60)
        print("TEST 3: Testing has_permission function")
        print("="*60)
        
        # Test with correct format
        perm_key = f"{test_section}.{test_permission_type.value.lower()}"
        print(f"Checking permission: {perm_key}")
        print(f"Project ID: {project_id}")
        
        has_perm = has_permission(test_user, perm_key, project_id=project_id)
        
        if has_perm:
            print(f"✓ has_permission returned True")
        else:
            print(f"❌ has_permission returned False (expected True)")
        
        # Test 4: Grant another permission and verify
        print("\n" + "="*60)
        print("TEST 4: Grant EDIT permission and verify")
        print("="*60)
        
        test_permission_type_2 = PermissionType.EDIT
        print(f"Saving permission: {test_section}.{test_subsection or '(main)'}.{test_permission_type_2.value}")
        
        success2 = update_permission(
            user_id=test_user.id,
            section=test_section,
            subsection=test_subsection,
            permission_type=test_permission_type_2,
            granted=True,
            updated_by=test_user.id,
            project_id=project_id
        )
        
        if success2:
            print("✓ EDIT permission saved successfully")
            
            # Verify it was saved
            perm_key_2 = f"{test_section}.{test_permission_type_2.value.lower()}"
            has_perm_2 = has_permission(test_user, perm_key_2, project_id=project_id)
            
            if has_perm_2:
                print(f"✓ has_permission for EDIT returned True")
            else:
                print(f"❌ has_permission for EDIT returned False")
        else:
            print("❌ Failed to save EDIT permission")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY - All user permissions")
        print("="*60)
        
        all_perms = SubPermission.query.filter_by(
            user_id=test_user.id,
            is_granted=True
        ).all()
        
        print(f"Total granted permissions: {len(all_perms)}")
        for perm in all_perms[:10]:  # Show first 10
            project_str = f" (Project: {perm.project_id})" if perm.project_id else " (Global)"
            print(f"  • {perm.section}.{perm.subsection or '(main)'}.{perm.permission_type.value}{project_str}")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)

if __name__ == "__main__":
    test_permissions_system()
