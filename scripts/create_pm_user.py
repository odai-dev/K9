#!/usr/bin/env python3
"""
سكريبت لإنشاء مستخدم Project Manager لاختبار نظام الجدولة
"""
import sys
import os
from datetime import date
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from k9.models.models import Employee, User, Project, EmployeeRole, UserRole
from k9.services.user_service import UserService

def create_pm_user():
    """إنشاء مستخدم PM للاختبار"""
    with app.app_context():
        try:
            print("\n🚀 بدء إنشاء مستخدم Project Manager...\n")
            
            # الحصول على المشروع
            project = Project.query.filter_by(code='PROJ-001').first()
            if not project:
                print("❌ المشروع غير موجود")
                return False
            print(f"✅ المشروع: {project.name}")
            
            # 1. إنشاء موظف PM
            print("\n1️⃣ إنشاء موظف PM...")
            employee = Employee.query.filter_by(employee_id='EMP-PM-001').first()
            if not employee:
                employee = Employee(
                    employee_id='EMP-PM-001',
                    name='محمد مدير المشروع',
                    role=EmployeeRole.PROJECT_MANAGER,
                    phone='0500000002',
                    email='pm@test.com',
                    hire_date=date.today(),
                    is_active=True
                )
                db.session.add(employee)
                db.session.flush()
                print(f"   ✅ تم إنشاء الموظف: {employee.name} ({employee.employee_id})")
            else:
                print(f"   ⚠️ الموظف موجود مسبقاً: {employee.name}")
            
            # 2. إنشاء مستخدم PM
            print("\n2️⃣ إنشاء مستخدم PM...")
            pm_user = User.query.filter_by(username='pm_test').first()
            if not pm_user:
                pm_user = User(
                    username='pm_test',
                    full_name='محمد مدير المشروع',
                    password_hash=generate_password_hash('Test123!'),
                    role=UserRole.PROJECT_MANAGER,
                    project_id=str(project.id),
                    employee_id=str(employee.id),
                    active=True
                )
                db.session.add(pm_user)
                db.session.flush()
                print(f"   ✅ تم إنشاء المستخدم: pm_test")
                print(f"      - اسم المستخدم: pm_test")
                print(f"      - كلمة المرور: Test123!")
                print(f"      - الدور: PROJECT_MANAGER")
                print(f"      - المشروع: {project.name}")
            else:
                print(f"   ⚠️ المستخدم موجود مسبقاً: {pm_user.username}")
            
            # 3. إعطاء الصلاحيات
            print("\n3️⃣ إعطاء الصلاحيات...")
            from k9.services.user_service import UserService
            
            # Give base permissions (auto-assigned)
            UserService.initialize_user_permissions(pm_user)
            
            # إعطاء صلاحيات إضافية مطلوبة للجدولة
            permissions_needed = [
                'schedule.daily.view',
                'schedule.daily.create',
                'schedule.daily.edit',
                'handler.shift_reports.view',
                'handler.shift_reports.review'
            ]
            
            for perm in permissions_needed:
                if not UserService.has_permission(pm_user, perm):
                    success, msg = UserService.grant_permission(pm_user.id, perm)
                    if success:
                        print(f"   ✅ تم إعطاء صلاحية: {perm}")
                    else:
                        print(f"   ⚠️ {msg}")
                else:
                    print(f"   ⚠️ الصلاحية موجودة: {perm}")
            
            db.session.commit()
            
            print("\n" + "="*70)
            print("✅ تم إنشاء مستخدم PM بنجاح!")
            print("="*70)
            print("\n📋 بيانات المستخدم:")
            print(f"   - الموظف: محمد مدير المشروع (EMP-PM-001)")
            print(f"   - المستخدم: pm_test (كلمة المرور: Test123!)")
            print(f"   - المشروع: {project.name}")
            print(f"   - الدور: PROJECT_MANAGER")
            
            print("\n🧪 خطوات الاختبار:")
            print("   1. سجل دخول باستخدام: pm_test / Test123!")
            print("   2. انتقل إلى /schedule/create")
            print("   3. أنشئ جدول يومي جديد")
            
            print("\n✅ جاهز للاختبار!")
            return True
            
        except Exception as e:
            print(f"\n❌ خطأ: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    create_pm_user()
