#!/usr/bin/env python3
"""
Test script to verify the permission system integration
This tests whether PROJECT_MANAGER users see data based on their SubPermission grants
"""

from app import app, db
from models import User, SubPermission, PermissionType, UserRole, Project, Dog, Employee
from utils import get_user_permissions, get_user_accessible_dogs, get_user_accessible_employees

def test_permissions():
    with app.app_context():
        # Get the admin user
        admin = User.query.filter_by(username='admin').first()
        print(f"✓ Admin user found: {admin.username if admin else 'None'}")
        
        # Get all users
        all_users = User.query.all()
        print(f"✓ Total users in system: {len(all_users)}")
        
        for user in all_users:
            print(f"  - {user.username} ({user.role.value})")
        
        # Check SubPermission table
        sub_permissions = SubPermission.query.all()
        print(f"✓ Total SubPermissions in system: {len(sub_permissions)}")
        
        if sub_permissions:
            print("  SubPermission details:")
            for perm in sub_permissions[:5]:  # Show first 5
                print(f"    - User {perm.user_id}: {perm.section} -> {perm.subsection} ({perm.permission_type.value}) = {perm.is_granted}")
        
        # Check if any PROJECT_MANAGER users exist
        pm_users = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
        print(f"✓ PROJECT_MANAGER users: {len(pm_users)}")
        
        for pm in pm_users:
            print(f"  Testing permissions for: {pm.username}")
            permissions = get_user_permissions(pm)
            print(f"    Main permissions: {permissions}")
            
            accessible_dogs = get_user_accessible_dogs(pm)
            print(f"    Accessible dogs: {len(accessible_dogs)}")
            
            accessible_employees = get_user_accessible_employees(pm)
            print(f"    Accessible employees: {len(accessible_employees)}")
        
        # Check projects
        projects = Project.query.all()
        print(f"✓ Total projects: {len(projects)}")
        
        # Check total dogs and employees
        total_dogs = Dog.query.count()
        total_employees = Employee.query.count()
        print(f"✓ Total dogs: {total_dogs}")
        print(f"✓ Total employees: {total_employees}")

if __name__ == '__main__':
    test_permissions()