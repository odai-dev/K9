"""
سكريبت لإنشاء بيانات اختبار لنظام Handler Daily System
"""
from app import app, db
from k9.models.models import Project, Dog, Employee, User, UserRole, EmployeeRole, DogStatus, DogGender, ProjectStatus, Shift, ProjectLocation
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem, ScheduleStatus, ScheduleItemStatus
from k9.services.handler_service import DailyScheduleService
from werkzeug.security import generate_password_hash
from datetime import date, time, datetime, timedelta
import sys

def create_test_data():
    """إنشاء بيانات اختبار كاملة"""
    
    with app.app_context():
        print("🚀 بدء إنشاء بيانات اختبار Handler Daily System...")
        
        # 1. إنشاء مشروع تجريبي
        print("\n1️⃣ إنشاء مشروع تجريبي...")
        project = Project.query.filter_by(code='PROJ-001').first()
        if not project:
            project = Project(
                name='مشروع الأمن الحدودي',
                code='PROJ-001',
                status=ProjectStatus.ACTIVE,
                start_date=date.today()
            )
            db.session.add(project)
            db.session.flush()
            print(f"   ✅ تم إنشاء المشروع: {project.name} ({project.code})")
        else:
            print(f"   ⚠️ المشروع موجود مسبقاً: {project.name}")
        
        # 2. إنشاء موقع للمشروع
        print("\n2️⃣ إنشاء موقع للمشروع...")
        location = ProjectLocation.query.filter_by(project_id=project.id).first()
        if not location:
            location = ProjectLocation(
                project_id=project.id,
                name='البوابة الشمالية',
                description='موقع البوابة الرئيسية الشمالية'
            )
            db.session.add(location)
            db.session.flush()
            print(f"   ✅ تم إنشاء الموقع: {location.name}")
        else:
            print(f"   ⚠️ الموقع موجود مسبقاً: {location.name}")
        
        # 3. إنشاء كلب تجريبي
        print("\n3️⃣ إنشاء كلب تجريبي...")
        dog = Dog.query.filter_by(code='DOG-001').first()
        if not dog:
            dog = Dog(
                name='ريكس',
                code='DOG-001',
                breed='جيرمن شيبرد',
                gender=DogGender.MALE,
                birth_date=date(2020, 1, 15),
                current_status=DogStatus.ACTIVE
            )
            db.session.add(dog)
            db.session.flush()
            print(f"   ✅ تم إنشاء الكلب: {dog.name} ({dog.code})")
        else:
            print(f"   ⚠️ الكلب موجود مسبقاً: {dog.name}")
        
        # 4. إنشاء وردية تجريبية
        print("\n4️⃣ إنشاء وردية تجريبية...")
        shift = Shift.query.filter_by(name='الصباحية').first()
        if not shift:
            shift = Shift(
                name='الصباحية',
                start_time=time(8, 0),
                end_time=time(16, 0)
            )
            db.session.add(shift)
            db.session.flush()
            print(f"   ✅ تم إنشاء الوردية: {shift.name} ({shift.start_time} - {shift.end_time})")
        else:
            print(f"   ⚠️ الوردية موجودة مسبقاً: {shift.name}")
        
        # 5. إنشاء موظف سائس
        print("\n5️⃣ إنشاء موظف سائس...")
        employee = Employee.query.filter_by(employee_id='EMP-HANDLER-001').first()
        if not employee:
            employee = Employee(
                employee_id='EMP-HANDLER-001',
                name='أحمد السائس',
                role=EmployeeRole.HANDLER,
                phone='0500000001',
                email='handler@test.com',
                hire_date=date.today(),
                is_active=True
            )
            db.session.add(employee)
            db.session.flush()
            print(f"   ✅ تم إنشاء الموظف: {employee.name} ({employee.employee_id})")
        else:
            print(f"   ⚠️ الموظف موجود مسبقاً: {employee.name}")
        
        # 6. إنشاء مستخدم سائس (مرتبط بالموظف)
        print("\n6️⃣ إنشاء مستخدم سائس...")
        handler_user = User.query.filter_by(username='handler_test').first()
        if not handler_user:
            handler_user = User(
                username='handler_test',
                email='handler@test.com',
                password_hash=generate_password_hash('Test123!'),
                full_name='أحمد السائس',
                role=UserRole.HANDLER,
                active=True,
                employee_id=employee.id,
                project_id=project.id,
                dog_id=dog.id
            )
            db.session.add(handler_user)
            db.session.flush()
            print(f"   ✅ تم إنشاء المستخدم: {handler_user.username}")
            print(f"      - اسم المستخدم: handler_test")
            print(f"      - كلمة المرور: Test123!")
            print(f"      - الدور: HANDLER")
            print(f"      - المشروع: {project.name}")
            print(f"      - الكلب: {dog.name}")
        else:
            print(f"   ⚠️ المستخدم موجود مسبقاً: {handler_user.username}")
        
        # 7. إنشاء جدول يومي لليوم التالي
        print("\n7️⃣ إنشاء جدول يومي لليوم التالي...")
        tomorrow = date.today() + timedelta(days=1)
        daily_schedule = DailySchedule.query.filter_by(
            date=tomorrow,
            project_id=project.id
        ).first()
        
        if not daily_schedule:
            daily_schedule = DailySchedule(
                date=tomorrow,
                project_id=project.id,
                status=ScheduleStatus.OPEN,
                notes='جدول تجريبي للاختبار',
                created_by_user_id=handler_user.id  # استخدام handler كمنشئ مؤقتاً
            )
            db.session.add(daily_schedule)
            db.session.flush()
            print(f"   ✅ تم إنشاء الجدول اليومي: {tomorrow}")
            
            # إنشاء عنصر في الجدول
            schedule_item = DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler_user.id,
                dog_id=dog.id,
                shift_id=shift.id,
                location_id=location.id,
                status=ScheduleItemStatus.PLANNED
            )
            db.session.add(schedule_item)
            print(f"   ✅ تم إضافة عنصر للجدول:")
            print(f"      - السائس: {handler_user.full_name}")
            print(f"      - الكلب: {dog.name}")
            print(f"      - الوردية: {shift.name}")
            print(f"      - الموقع: {location.name}")
        else:
            print(f"   ⚠️ الجدول اليومي موجود مسبقاً لتاريخ: {tomorrow}")
        
        # حفظ كل التغييرات
        db.session.commit()
        
        print("\n" + "="*70)
        print("✅ تم إنشاء بيانات الاختبار بنجاح!")
        print("="*70)
        
        print("\n📋 ملخص البيانات:")
        print(f"   - المشروع: {project.name} ({project.code})")
        print(f"   - الموقع: {location.name}")
        print(f"   - الكلب: {dog.name} ({dog.code})")
        print(f"   - الوردية: {shift.name} ({shift.start_time} - {shift.end_time})")
        print(f"   - الموظف: {employee.name} ({employee.employee_id})")
        print(f"   - المستخدم: {handler_user.username} (كلمة المرور: Test123!)")
        print(f"   - الجدول اليومي: {tomorrow}")
        
        print("\n🧪 خطوات الاختبار:")
        print("   1. سجل خروج من حساب GENERAL_ADMIN")
        print("   2. سجل دخول باستخدام:")
        print("      - اسم المستخدم: handler_test")
        print("      - كلمة المرور: Test123!")
        print("   3. انتقل إلى /handler/dashboard")
        print("   4. سترى جدول يوم غد في قسم 'جدول اليوم'")
        print("   5. اضغط 'تقرير وردية' أو 'تقرير يومي' لرفع تقرير")
        
        print("\n✅ جاهز للاختبار!")

if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
