#!/usr/bin/env python3
"""
Comprehensive Sample Data Seeder for K9 Operations System
Adds employees, projects, dogs, and attendance data for testing
"""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, UserRole, Employee, EmployeeRole, Project, ProjectStatus,
    Dog, DogStatus, DogGender, ProjectAttendance, AttendanceStatus
)
from werkzeug.security import generate_password_hash

def create_comprehensive_data():
    """Create comprehensive sample data for testing"""
    with app.app_context():
        print("Creating comprehensive sample data...")
        
        # Clear existing data (except admin user)
        print("Clearing existing data...")
        ProjectAttendance.query.delete()
        Dog.query.delete()
        Project.query.delete()
        Employee.query.delete()
        
        # Keep admin user, remove others
        User.query.filter(User.username != 'admin').delete()
        
        db.session.commit()
        
        # Create sample employees
        print("Creating employees...")
        employees = []
        
        # Employee 1: Handler
        emp1 = Employee()
        emp1.id = str(uuid4())
        emp1.employee_id = "EMP001"
        emp1.name = "أحمد محمد علي"
        emp1.role = EmployeeRole.HANDLER
        emp1.phone = "+966501234567"
        emp1.email = "ahmed.ali@k9ops.com"
        emp1.hire_date = datetime(2023, 1, 15).date()
        emp1.is_active = True
        employees.append(emp1)
        
        # Employee 2: Handler  
        emp2 = Employee()
        emp2.id = str(uuid4())
        emp2.employee_id = "EMP002"
        emp2.name = "فاطمة سعد الأحمد"
        emp2.role = EmployeeRole.HANDLER
        emp2.phone = "+966502345678"
        emp2.email = "fatima.saad@k9ops.com"
        emp2.hire_date = datetime(2023, 3, 20).date()
        emp2.is_active = True
        employees.append(emp2)
        
        # Employee 3: Trainer
        emp3 = Employee()
        emp3.id = str(uuid4())
        emp3.employee_id = "EMP003"
        emp3.name = "خالد عبدالله المطيري"
        emp3.role = EmployeeRole.TRAINER
        emp3.phone = "+966503456789"
        emp3.email = "khalid.mutairi@k9ops.com"
        emp3.hire_date = datetime(2022, 11, 10).date()
        emp3.is_active = True
        employees.append(emp3)
        
        # Employee 4: Veterinarian
        emp4 = Employee()
        emp4.id = str(uuid4())
        emp4.employee_id = "EMP004"
        emp4.name = "د. سارة أحمد الزهراني"
        emp4.role = EmployeeRole.VET
        emp4.phone = "+966504567890"
        emp4.email = "sara.zahrani@k9ops.com"
        emp4.hire_date = datetime(2022, 8, 5).date()
        emp4.is_active = True
        employees.append(emp4)
        
        # Employee 5: Project Manager
        emp5 = Employee()
        emp5.id = str(uuid4())
        emp5.employee_id = "EMP005"
        emp5.name = "محمد سالم القحطاني"
        emp5.role = EmployeeRole.PROJECT_MANAGER
        emp5.phone = "+966505678901"
        emp5.email = "mohammed.qahtani@k9ops.com"
        emp5.hire_date = datetime(2022, 6, 1).date()
        emp5.is_active = True
        employees.append(emp5)
        
        # Employee 6: Breeder
        emp6 = Employee()
        emp6.id = str(uuid4())
        emp6.employee_id = "EMP006"
        emp6.name = "عبدالرحمن ناصر العتيبي"
        emp6.role = EmployeeRole.BREEDER
        emp6.phone = "+966506789012"
        emp6.email = "abdulrahman.otaibi@k9ops.com"
        emp6.hire_date = datetime(2023, 2, 12).date()
        emp6.is_active = True
        employees.append(emp6)
        
        # Save employees
        for emp in employees:
            db.session.add(emp)
        
        # Create Project Manager user
        pm_user = User()
        pm_user.username = 'pm_mohammed'
        pm_user.email = 'mohammed.qahtani@k9ops.com'
        pm_user.password_hash = generate_password_hash('pm123')
        pm_user.role = UserRole.PROJECT_MANAGER
        pm_user.full_name = 'محمد سالم القحطاني'
        pm_user.active = True
        # Link user to employee (will set after commit)
        db.session.add(pm_user)
        
        db.session.commit()
        print(f"Created {len(employees)} employees")
        
        # Create sample projects
        print("Creating projects...")
        projects = []
        
        # Project 1: Border Security
        proj1 = Project()
        proj1.id = str(uuid4())
        proj1.name = "أمن الحدود الجنوبية"
        proj1.description = "مشروع تأمين الحدود الجنوبية باستخدام الكلاب البوليسية المدربة"
        proj1.status = ProjectStatus.ACTIVE
        proj1.code = "PROJ001"
        proj1.start_date = datetime(2024, 1, 15).date()
        proj1.location = "منطقة الحدود الجنوبية"
        proj1.project_manager_id = emp5.id
        proj1.created_at = datetime.now()
        projects.append(proj1)
        
        # Project 2: Airport Security
        proj2 = Project()
        proj2.id = str(uuid4())
        proj2.name = "أمن المطارات"
        proj2.description = "مشروع كشف المتفجرات والمواد المخدرة في المطارات الدولية"
        proj2.status = ProjectStatus.ACTIVE
        proj2.code = "PROJ002"
        proj2.start_date = datetime(2024, 3, 1).date()
        proj2.location = "مطار الملك عبدالعزيز الدولي"
        proj2.project_manager_id = emp5.id
        proj2.created_at = datetime.now()
        projects.append(proj2)
        
        # Save projects
        for proj in projects:
            db.session.add(proj)
        
        db.session.commit()
        print(f"Created {len(projects)} projects")
        
        # Create sample dogs
        print("Creating dogs...")
        dogs = []
        
        # Dog 1: German Shepherd
        dog1 = Dog()
        dog1.id = str(uuid4())
        dog1.name = "ريكس"
        dog1.code = "DOG001"
        dog1.breed = "German Shepherd"
        dog1.gender = DogGender.MALE
        dog1.birth_date = datetime(2020, 5, 15).date()
        dog1.current_status = DogStatus.ACTIVE
        dog1.microchip_id = "123456789012345"
        dog1.weight = 35.0
        dog1.height = 65.0
        dog1.color = "بني وأسود"
        dogs.append(dog1)
        
        # Dog 2: Belgian Malinois
        dog2 = Dog()
        dog2.id = str(uuid4())
        dog2.name = "لونا"
        dog2.code = "DOG002"
        dog2.breed = "Belgian Malinois"
        dog2.gender = DogGender.FEMALE
        dog2.birth_date = datetime(2021, 3, 20).date()
        dog2.current_status = DogStatus.ACTIVE
        dog2.microchip_id = "234567890123456"
        dog2.weight = 28.0
        dog2.height = 58.0
        dog2.color = "بني فاتح"
        dogs.append(dog2)
        
        # Dog 3: German Shepherd
        dog3 = Dog()
        dog3.id = str(uuid4())
        dog3.name = "ماكس"
        dog3.code = "DOG003"
        dog3.breed = "German Shepherd"
        dog3.gender = DogGender.MALE
        dog3.birth_date = datetime(2019, 8, 10).date()
        dog3.current_status = DogStatus.ACTIVE
        dog3.microchip_id = "345678901234567"
        dog3.weight = 38.0
        dog3.height = 67.0
        dog3.color = "أسود"
        dogs.append(dog3)
        
        # Dog 4: Labrador
        dog4 = Dog()
        dog4.id = str(uuid4())
        dog4.name = "بيلا"
        dog4.code = "DOG004"
        dog4.breed = "Labrador"
        dog4.gender = DogGender.FEMALE
        dog4.birth_date = datetime(2022, 1, 5).date()
        dog4.current_status = DogStatus.TRAINING
        dog4.microchip_id = "456789012345678"
        dog4.weight = 30.0
        dog4.height = 60.0
        dog4.color = "أصفر"
        dogs.append(dog4)
        
        # Save dogs
        for dog in dogs:
            db.session.add(dog)
        
        db.session.commit()
        print(f"Created {len(dogs)} dogs")
        
        # Create attendance records for the last 14 days
        print("Creating attendance records...")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=13)  # 14 days total
        
        attendance_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Create attendance for each employee
            for emp in employees:
                # Skip weekends (Friday and Saturday in Saudi Arabia)
                if current_date.weekday() in [4, 5]:  # Friday=4, Saturday=5
                    continue
                
                # Random attendance status (mostly present)
                import random
                status_weights = [
                    (AttendanceStatus.PRESENT, 0.8),
                    (AttendanceStatus.LATE, 0.1),
                    (AttendanceStatus.ABSENT, 0.05),
                    (AttendanceStatus.SICK, 0.03),
                    (AttendanceStatus.LEAVE, 0.02)
                ]
                
                status = random.choices(
                    [s[0] for s in status_weights],
                    weights=[s[1] for s in status_weights]
                )[0]
                
                # Create attendance record for Project 1
                att1 = ProjectAttendance()
                att1.id = str(uuid4())
                att1.employee_id = emp.id
                att1.project_id = proj1.id
                att1.date = current_date
                att1.status = status
                att1.check_in_time = datetime.combine(current_date, datetime.strptime("08:00", "%H:%M").time()) if status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE] else None
                att1.check_out_time = datetime.combine(current_date, datetime.strptime("16:00", "%H:%M").time()) if status == AttendanceStatus.PRESENT else None
                att1.notes = f"تسجيل حضور تلقائي - {status.value}"
                att1.created_at = datetime.now()
                
                db.session.add(att1)
                attendance_count += 1
                
                # Some employees also work on Project 2
                if emp.role in [EmployeeRole.HANDLER, EmployeeRole.TRAINER] and random.random() > 0.5:
                    att2 = ProjectAttendance()
                    att2.id = str(uuid4())
                    att2.employee_id = emp.id
                    att2.project_id = proj2.id
                    att2.date = current_date
                    att2.status = status
                    att2.check_in_time = datetime.combine(current_date, datetime.strptime("08:00", "%H:%M").time()) if status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE] else None
                    att2.check_out_time = datetime.combine(current_date, datetime.strptime("16:00", "%H:%M").time()) if status == AttendanceStatus.PRESENT else None
                    att2.notes = f"تسجيل حضور تلقائي - مشروع ثانوي"
                    att2.created_at = datetime.now()
                    
                    db.session.add(att2)
                    attendance_count += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        print(f"Created {attendance_count} attendance records")
        
        print("\n✅ Sample data creation completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Employees: {len(employees)}")
        print(f"   - Projects: {len(projects)}")
        print(f"   - Dogs: {len(dogs)}")
        print(f"   - Attendance Records: {attendance_count}")
        print(f"   - Date Range: {start_date} to {end_date}")
        
        print(f"\n🔐 Login Credentials:")
        print(f"   Admin: admin / admin123")
        print(f"   Project Manager: pm_mohammed / pm123")

if __name__ == "__main__":
    create_comprehensive_data()