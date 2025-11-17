#!/usr/bin/env python3
"""إنشاء مستخدم PM للاختبار"""
import sys
import os
from datetime import date
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.models import Employee, User, Project, EmployeeRole, UserRole
from k9.utils.default_permissions import create_base_permissions_for_user

with app.app_context():
    try:
        print("\n🚀 إنشاء مستخدم PM...\n")
        
        # Get project
        project = Project.query.filter_by(code='PROJ-001').first()
        if not project:
            print("❌ المشروع غير موجود")
            sys.exit(1)
        print(f"✅ المشروع: {project.name}")
        
        # Create employee
        emp = Employee.query.filter_by(employee_id='EMP-PM-001').first()
        if not emp:
            emp = Employee(
                employee_id='EMP-PM-001',
                name='محمد PM',
                role=EmployeeRole.PROJECT_MANAGER,
                phone='0500000002',
                email='pm@test.com',
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(emp)
            db.session.flush()
            print(f"✅ الموظف: {emp.name}")
        else:
            print(f"⚠️ الموظف موجود: {emp.name}")
        
        # Create user
        user = User.query.filter_by(username='pm_test').first()
        if not user:
            user = User(
                username='pm_test',
                email='pm@test.com',
                full_name='محمد PM',
                password_hash=generate_password_hash('Test123!'),
                role=UserRole.PROJECT_MANAGER,
                project_id=str(project.id),
                employee_id=str(emp.id),
                active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Create base permissions
            count = create_base_permissions_for_user(user, db.session, str(project.id))
            print(f"✅ المستخدم: pm_test ({count} صلاحية)")
        else:
            print(f"⚠️ المستخدم موجود: {user.username}")
        
        db.session.commit()
        
        print("\n✅ تم بنجاح!")
        print(f"   اسم المستخدم: pm_test")
        print(f"   كلمة المرور: Test123!")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)
