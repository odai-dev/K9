#!/usr/bin/env python3
"""
Setup script for the enhanced permission system
Creates database tables and initializes sample data for testing
"""

from app import app, db
from models import User, UserRole, Project, ProjectStatus, SubPermission, PermissionType
from permission_utils import initialize_default_permissions, PERMISSION_STRUCTURE
from werkzeug.security import generate_password_hash
import sys

def create_sample_users():
    """Create sample users for testing"""
    print("Creating sample users...")
    
    # Create a sample PROJECT_MANAGER user if it doesn't exist
    pm_user = User.query.filter_by(username='pm_test').first()
    if not pm_user:
        pm_user = User()
        pm_user.username = 'pm_test'
        pm_user.email = 'pm@k9ops.com'
        pm_user.password_hash = generate_password_hash('pm123')
        pm_user.role = UserRole.PROJECT_MANAGER
        pm_user.full_name = 'مدير مشروع تجريبي'
        pm_user.active = True
        db.session.add(pm_user)
    
    # Create another PROJECT_MANAGER
    pm_user2 = User.query.filter_by(username='pm_test2').first()
    if not pm_user2:
        pm_user2 = User()
        pm_user2.username = 'pm_test2'
        pm_user2.email = 'pm2@k9ops.com'
        pm_user2.password_hash = generate_password_hash('pm123')
        pm_user2.role = UserRole.PROJECT_MANAGER
        pm_user2.full_name = 'مدير مشروع تجريبي ثاني'
        pm_user2.active = True
        db.session.add(pm_user2)
    
    try:
        db.session.commit()
        print(f"✓ Created sample PROJECT_MANAGER users")
        return pm_user, pm_user2
    except Exception as e:
        db.session.rollback()
        print(f"Error creating users: {str(e)}")
        return None, None

def create_sample_project():
    """Create a sample project for testing"""
    print("Creating sample project...")
    
    project = Project.query.filter_by(name='مشروع تجريبي للصلاحيات').first()
    if not project:
        project = Project()
        project.name = 'مشروع تجريبي للصلاحيات'
        project.code = 'PERM-TEST-001'
        project.main_task = 'اختبار نظام الصلاحيات المتقدم'
        project.description = 'مشروع تجريبي لاختبار نظام الصلاحيات المتقدم'
        project.status = ProjectStatus.ACTIVE
        project.start_date = db.func.current_date()
        project.location = 'مقر التدريب الرئيسي'
        project.mission_type = 'تدريب'
        project.priority = 'MEDIUM'
        db.session.add(project)
        
        try:
            db.session.commit()
            print(f"✓ Created sample project: {project.name}")
            return project
        except Exception as e:
            db.session.rollback()
            print(f"Error creating project: {str(e)}")
            return None
    else:
        print(f"✓ Sample project already exists: {project.name}")
        return project

def setup_sample_permissions(pm_user, project):
    """Set up some sample permissions for demonstration"""
    print("Setting up sample permissions...")
    
    if not pm_user or not project:
        print("Cannot set up permissions - missing user or project")
        return
    
    # Initialize default permissions for the user
    initialize_default_permissions(pm_user)
    
    # Grant some specific permissions for demonstration
    sample_permissions = [
        ("Dogs", "تعديل معلومات الكلب", PermissionType.EDIT, True),
        ("Dogs", "تعيين إلى مشروع", PermissionType.ASSIGN, True),
        ("Employees", "عرض تفاصيل الموظف", PermissionType.VIEW, True),
        ("Projects", "تعديل المشروع", PermissionType.EDIT, True),
        ("Projects", "تسجيل الحوادث", PermissionType.CREATE, True),
        ("Training", "إنشاء جلسة تدريب", PermissionType.CREATE, True),
        ("Attendance", "تسجيل الحضور", PermissionType.CREATE, True),
        ("Reports", "إنشاء تقارير PDF", PermissionType.CREATE, True),
    ]
    
    for section, subsection, perm_type, is_granted in sample_permissions:
        # Check if permission already exists
        existing = SubPermission.query.filter_by(
            user_id=pm_user.id,
            section=section,
            subsection=subsection,
            permission_type=perm_type,
            project_id=project.id
        ).first()
        
        if not existing:
            permission = SubPermission()
            permission.user_id = pm_user.id
            permission.section = section
            permission.subsection = subsection
            permission.permission_type = perm_type
            permission.project_id = project.id
            permission.is_granted = is_granted
            db.session.add(permission)
    
    try:
        db.session.commit()
        print(f"✓ Set up sample permissions for {pm_user.full_name}")
    except Exception as e:
        db.session.rollback()
        print(f"Error setting up permissions: {str(e)}")

def validate_permission_structure():
    """Validate that the permission structure is properly defined"""
    print("Validating permission structure...")
    
    total_permissions = 0
    for section, subsections in PERMISSION_STRUCTURE.items():
        section_count = 0
        for subsection, permission_types in subsections.items():
            section_count += len(permission_types)
        
        total_permissions += section_count
        print(f"  {section}: {len(subsections)} subsections, {section_count} permissions")
    
    print(f"✓ Total permission structure: {len(PERMISSION_STRUCTURE)} sections, {total_permissions} total permission combinations")

def main():
    """Main setup function"""
    print("🚀 Setting up Enhanced Permission System for K9 Operations...")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Create all database tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Validate permission structure
            validate_permission_structure()
            
            # Create sample data
            pm_user, pm_user2 = create_sample_users()
            project = create_sample_project()
            
            # Setup sample permissions
            if pm_user and project:
                setup_sample_permissions(pm_user, project)
            
            print("\n" + "=" * 60)
            print("✅ Enhanced Permission System Setup Complete!")
            print("\nTest Accounts:")
            print("  Admin: admin / admin123 (GENERAL_ADMIN)")
            print("  Project Manager 1: pm_test / pm123 (PROJECT_MANAGER)")
            print("  Project Manager 2: pm_test2 / pm123 (PROJECT_MANAGER)")
            print("\nAccess the Admin Dashboard:")
            print("  URL: /admin/permissions")
            print("  Login as 'admin' to manage granular permissions")
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()