#!/usr/bin/env python3
"""
Script to populate the K9 system with test data for daily schedule testing
"""
import os
import sys
from datetime import date, time, timedelta
from werkzeug.security import generate_password_hash

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import User, UserRole, Employee, EmployeeRole, Project, Dog, DogGender, DogStatus, Shift
from k9.models.models_handler_daily import DailySchedule, DailyScheduleItem, ScheduleStatus, ScheduleItemStatus


def create_test_data():
    """Create comprehensive test data for the system"""
    
    with app.app_context():
        print("🚀 Starting test data creation...")
        
        # Clear existing data (in reverse order of dependencies)
        print("🗑️  Clearing existing test data...")
        DailyScheduleItem.query.delete()
        DailySchedule.query.delete()
        
        # Only delete test users/data if they exist
        User.query.filter(User.username.in_(['admin', 'pm1', 'supervisor1', 'handler1', 'handler2', 'handler3'])).delete(synchronize_session=False)
        Employee.query.filter(Employee.employee_id.in_(['EMP-ADMIN', 'EMP-PM1', 'EMP-SUP1', 'EMP-H1', 'EMP-H2', 'EMP-H3'])).delete(synchronize_session=False)
        Dog.query.filter(Dog.code.in_(['DOG-001', 'DOG-002', 'DOG-003', 'DOG-004', 'DOG-005'])).delete(synchronize_session=False)
        Shift.query.filter(Shift.name.in_(['الوردية الصباحية', 'الوردية المسائية', 'الوردية الليلية'])).delete(synchronize_session=False)
        Project.query.filter(Project.code == 'SEC-001').delete(synchronize_session=False)
        
        db.session.commit()
        
        # 1. Create Projects (optional)
        print("📁 Creating projects...")
        project1 = Project(
            name="مشروع تدريب الكلاب الأمنية",
            code="SEC-001",
            main_task="تدريب وإعداد الكلاب للمهام الأمنية",
            description="مشروع تدريب الكلاب على الكشف عن المتفجرات والمخدرات",
            status='ACTIVE',
            start_date=date.today() - timedelta(days=30),
            location="الرياض"
        )
        db.session.add(project1)
        db.session.flush()
        print(f"   ✓ Created project: {project1.name}")
        
        # 2. Create Employees FIRST (required before users)
        print("👷 Creating employees...")
        employees = [
            Employee(
                name="مدير النظام",
                employee_id="EMP-ADMIN",
                role=EmployeeRole.PROJECT_MANAGER,
                phone="+966500000001",
                email="admin@k9system.com",
                hire_date=date.today() - timedelta(days=365),
                is_active=True,
                full_name="مدير النظام العام"
            ),
            Employee(
                name="أحمد المدير",
                employee_id="EMP-PM1",
                role=EmployeeRole.PROJECT_MANAGER,
                phone="+966500000002",
                email="pm@k9system.com",
                hire_date=date.today() - timedelta(days=180),
                is_active=True,
                full_name="أحمد بن محمد المدير"
            ),
            Employee(
                name="محمد المشرف",
                employee_id="EMP-SUP1",
                role=EmployeeRole.PROJECT_MANAGER,
                phone="+966500000003",
                email="supervisor@k9system.com",
                hire_date=date.today() - timedelta(days=150),
                is_active=True,
                full_name="محمد بن عبدالله المشرف"
            ),
            Employee(
                name="خالد السائس",
                employee_id="EMP-H1",
                role=EmployeeRole.HANDLER,
                phone="+966500000004",
                email="handler1@k9system.com",
                hire_date=date.today() - timedelta(days=90),
                is_active=True,
                full_name="خالد بن سعد السائس"
            ),
            Employee(
                name="سعيد السائس",
                employee_id="EMP-H2",
                role=EmployeeRole.HANDLER,
                phone="+966500000005",
                email="handler2@k9system.com",
                hire_date=date.today() - timedelta(days=60),
                is_active=True,
                full_name="سعيد بن ناصر السائس"
            ),
            Employee(
                name="فهد السائس",
                employee_id="EMP-H3",
                role=EmployeeRole.HANDLER,
                phone="+966500000006",
                email="handler3@k9system.com",
                hire_date=date.today() - timedelta(days=30),
                is_active=True,
                full_name="فهد بن راشد السائس"
            )
        ]
        
        for emp in employees:
            db.session.add(emp)
        db.session.flush()
        
        for emp in employees:
            print(f"   ✓ Created employee: {emp.name} ({emp.employee_id})")
        
        # 3. Create Users linked to Employees
        print("👥 Creating user accounts...")
        password = "test123"
        
        # General Admin user
        admin = User(
            username="admin",
            email="admin@k9system.com",
            full_name="مدير النظام",
            role=UserRole.GENERAL_ADMIN,
            active=True,
            employee_id=employees[0].id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(admin)
        
        # Project Manager
        pm = User(
            username="pm1",
            email="pm@k9system.com",
            full_name="أحمد المدير",
            role=UserRole.PROJECT_MANAGER,
            active=True,
            employee_id=employees[1].id,
            project_id=project1.id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(pm)
        
        # Supervisor
        supervisor = User(
            username="supervisor1",
            email="supervisor@k9system.com",
            full_name="محمد المشرف",
            role=UserRole.PROJECT_MANAGER,
            active=True,
            employee_id=employees[2].id,
            project_id=project1.id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(supervisor)
        
        # Handlers
        handler1 = User(
            username="handler1",
            email="handler1@k9system.com",
            full_name="خالد السائس",
            role=UserRole.HANDLER,
            active=True,
            employee_id=employees[3].id,
            project_id=project1.id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(handler1)
        
        handler2 = User(
            username="handler2",
            email="handler2@k9system.com",
            full_name="سعيد السائس",
            role=UserRole.HANDLER,
            active=True,
            employee_id=employees[4].id,
            project_id=project1.id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(handler2)
        
        handler3 = User(
            username="handler3",
            email="handler3@k9system.com",
            full_name="فهد السائس",
            role=UserRole.HANDLER,
            active=True,
            employee_id=employees[5].id,
            project_id=project1.id,
            password_hash=generate_password_hash(password)
        )
        db.session.add(handler3)
        
        db.session.flush()
        print(f"   ✓ Created user account: {admin.username}")
        print(f"   ✓ Created user account: {pm.username}")
        print(f"   ✓ Created user account: {supervisor.username}")
        print(f"   ✓ Created user account: {handler1.username}")
        print(f"   ✓ Created user account: {handler2.username}")
        print(f"   ✓ Created user account: {handler3.username}")
        
        # 4. Create Dogs
        print("🐕 Creating dogs...")
        dogs = [
            Dog(
                name="رعد",
                code="DOG-001",
                breed="جيرمن شيبرد",
                gender=DogGender.MALE,
                birth_date=date(2020, 5, 15),
                current_status=DogStatus.ACTIVE,
                specialization="كشف المتفجرات",
                color="أسود وبني"
            ),
            Dog(
                name="صقر",
                code="DOG-002",
                breed="بلجيكي ماليونيز",
                gender=DogGender.MALE,
                birth_date=date(2019, 8, 20),
                current_status=DogStatus.ACTIVE,
                specialization="كشف المخدرات",
                color="بني غامق"
            ),
            Dog(
                name="غزال",
                code="DOG-003",
                breed="جيرمن شيبرد",
                gender=DogGender.FEMALE,
                birth_date=date(2021, 3, 10),
                current_status=DogStatus.ACTIVE,
                specialization="الحراسة",
                color="أسود"
            ),
            Dog(
                name="نمر",
                code="DOG-004",
                breed="روت فايلر",
                gender=DogGender.MALE,
                birth_date=date(2020, 11, 5),
                current_status=DogStatus.ACTIVE,
                specialization="الأمن",
                color="أسود وبني"
            ),
            Dog(
                name="ليث",
                code="DOG-005",
                breed="دوبرمان",
                gender=DogGender.MALE,
                birth_date=date(2019, 12, 25),
                current_status=DogStatus.ACTIVE,
                specialization="الحراسة",
                color="أسود"
            )
        ]
        
        for dog in dogs:
            db.session.add(dog)
            print(f"   ✓ Created dog: {dog.name} ({dog.code})")
        
        db.session.flush()
        
        # 5. Create Shifts
        print("⏰ Creating shifts...")
        shifts = [
            Shift(
                name="الوردية الصباحية",
                start_time=time(6, 0),
                end_time=time(14, 0),
                is_active=True
            ),
            Shift(
                name="الوردية المسائية",
                start_time=time(14, 0),
                end_time=time(22, 0),
                is_active=True
            ),
            Shift(
                name="الوردية الليلية",
                start_time=time(22, 0),
                end_time=time(6, 0),
                is_active=True
            )
        ]
        
        for shift in shifts:
            db.session.add(shift)
            print(f"   ✓ Created shift: {shift.name}")
        
        db.session.flush()
        
        # 6. Create Daily Schedule for Today
        print("📅 Creating daily schedule for today...")
        today = date.today()
        
        daily_schedule = DailySchedule(
            date=today,
            project_id=project1.id,
            created_by_user_id=supervisor.id,
            status=ScheduleStatus.OPEN,
            notes="جدول يومي للتدريب والرعاية"
        )
        db.session.add(daily_schedule)
        db.session.flush()
        print(f"   ✓ Created schedule for {today}")
        
        # 7. Create Schedule Items
        print("📋 Creating schedule items...")
        schedule_items = [
            # Handler 1 - Morning shift with رعد
            DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler1.id,
                dog_id=dogs[0].id,
                shift_id=shifts[0].id,
                status=ScheduleItemStatus.PLANNED
            ),
            # Handler 1 - Morning shift with صقر
            DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler1.id,
                dog_id=dogs[1].id,
                shift_id=shifts[0].id,
                status=ScheduleItemStatus.PLANNED
            ),
            # Handler 2 - Afternoon shift with غزال
            DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler2.id,
                dog_id=dogs[2].id,
                shift_id=shifts[1].id,
                status=ScheduleItemStatus.PLANNED
            ),
            # Handler 2 - Afternoon shift with نمر
            DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler2.id,
                dog_id=dogs[3].id,
                shift_id=shifts[1].id,
                status=ScheduleItemStatus.PLANNED
            ),
            # Handler 3 - Night shift with ليث
            DailyScheduleItem(
                daily_schedule_id=daily_schedule.id,
                handler_user_id=handler3.id,
                dog_id=dogs[4].id,
                shift_id=shifts[2].id,
                status=ScheduleItemStatus.PLANNED
            )
        ]
        
        for item in schedule_items:
            db.session.add(item)
        print(f"   ✓ Created {len(schedule_items)} schedule items")
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Test data creation completed successfully!")
        print("\n" + "="*60)
        print("LOGIN CREDENTIALS (All passwords: test123)")
        print("="*60)
        print(f"Admin:      username: admin       password: test123")
        print(f"PM:         username: pm1         password: test123")
        print(f"Supervisor: username: supervisor1 password: test123")
        print(f"Handler 1:  username: handler1    password: test123")
        print(f"Handler 2:  username: handler2    password: test123")
        print(f"Handler 3:  username: handler3    password: test123")
        print("="*60)
        
        print("\n📊 Summary:")
        print(f"   • Projects: 1")
        print(f"   • Employees: 6 (1 admin, 2 managers, 3 handlers)")
        print(f"   • User Accounts: 6 (linked to employees above)")
        print(f"   • Dogs: 5")
        print(f"   • Shifts: 3")
        print(f"   • Daily Schedules: 1 (for {today})")
        print(f"   • Schedule Items: {len(schedule_items)}")
        print("\n🎯 You can now login as handler1, handler2, or handler3 to see their daily schedules!")
        print("Note: All user accounts are properly linked to employee records (employee_id constraint enforced)")


if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
