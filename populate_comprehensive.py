#!/usr/bin/env python3
"""
Comprehensive data population for K9 Operations Management System
Populates all sections with realistic test data
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *

def main():
    """Main function to populate all data"""
    print("=" * 60)
    print("K9 Operations - Comprehensive Data Population")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 1. Create additional users
            print("\n1. Creating users...")
            users_created = create_users()
            
            # 2. Create employees
            print("\n2. Creating employees...")
            employees = create_employees()
            
            # 3. Create dogs
            print("\n3. Creating dogs...")
            dogs = create_dogs()
            
            # 4. Create projects
            print("\n4. Creating projects...")
            projects = create_projects()
            
            # 5. Assign permissions
            print("\n5. Creating permissions...")
            create_permissions(projects)
            
            # 6. Create project shifts
            print("\n6. Creating project shifts...")
            create_shifts(projects)
            
            # 7. Create training sessions
            print("\n7. Creating training sessions...")
            create_training_sessions(dogs, employees, projects)
            
            # 8. Create veterinary visits
            print("\n8. Creating veterinary visits...")
            create_veterinary_visits(dogs, employees, projects)
            
            # 9. Create attendance records
            print("\n9. Creating attendance records...")
            create_attendance_records(employees, projects)
            
            # 10. Create feeding records
            print("\n10. Creating feeding records...")
            create_feeding_records(dogs, employees)
            
            # 11. Create checkup records
            print("\n11. Creating checkup records...")
            create_checkup_records(dogs, employees)
            
            # 12. Create caretaker daily logs
            print("\n12. Creating caretaker daily logs...")
            create_caretaker_logs(dogs, employees)
            
            print("\n" + "=" * 60)
            print("✅ Data population completed successfully!")
            print("=" * 60)
            print("\nYou can now login with:")
            print("  Username: admin")
            print("  Password: password123")
            print("\nOr use any project manager:")
            print("  Username: pm1, pm2, or pm3")
            print("  Password: password123")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)

def create_users():
    """Create project manager users"""
    pm_users = []
    for i in range(3):
        username = f"pm{i+1}"
        if not User.query.filter_by(username=username).first():
            user = User()
            user.username = username
            user.email = f"{username}@k9system.local"
            user.full_name = f"مدير المشروع {i+1}"
            user.role = UserRole.PROJECT_MANAGER
            user.password_hash = generate_password_hash('password123')
            user.active = True
            db.session.add(user)
            pm_users.append(user)
    
    db.session.commit()
    print(f"   ✓ Created {len(pm_users)} project manager users")
    return pm_users

def create_employees():
    """Create employees of various roles"""
    employees_data = [
        ("سعد محمد", "H001", EmployeeRole.HANDLER),
        ("خالد أحمد", "H002", EmployeeRole.HANDLER),
        ("محمد علي", "H003", EmployeeRole.HANDLER),
        ("أحمد حسن", "H004", EmployeeRole.HANDLER),
        ("عبد الله سالم", "T001", EmployeeRole.TRAINER),
        ("يوسف إبراهيم", "T002", EmployeeRole.TRAINER),
        ("فهد محمد", "T003", EmployeeRole.TRAINER),
        ("ناصر العتيبي", "B001", EmployeeRole.BREEDER),
        ("سلطان الرشيد", "B002", EmployeeRole.BREEDER),
        ("د. علي الحسن", "V001", EmployeeRole.VET),
        ("د. محمد الخالد", "V002", EmployeeRole.VET),
    ]
    
    employees = []
    for name, emp_id, role in employees_data:
        if not Employee.query.filter_by(employee_id=emp_id).first():
            employee = Employee()
            employee.name = name
            employee.employee_id = emp_id
            employee.role = role
            employee.email = f"{emp_id.lower()}@k9unit.local"
            employee.phone = f"+96650{random.randint(1000000, 9999999)}"
            employee.hire_date = date.today() - timedelta(days=random.randint(30, 800))
            employee.is_active = True
            db.session.add(employee)
            employees.append(employee)
    
    db.session.commit()
    print(f"   ✓ Created {len(employees)} employees")
    return employees

def create_dogs():
    """Create dogs with various characteristics"""
    breeds = ["German Shepherd", "Belgian Malinois", "Dutch Shepherd", "Rottweiler"]
    colors = ["أسود", "بني", "ذهبي", "أسود/بني"]
    
    dogs = []
    for i in range(25):
        code = f"K9{i+1:03d}"
        if not Dog.query.filter_by(code=code).first():
            dog = Dog()
            dog.name = f"كلب {i+1}"
            dog.code = code
            dog.breed = random.choice(breeds)
            dog.gender = random.choice(list(DogGender))
            dog.birth_date = date.today() - timedelta(days=random.randint(365, 2500))
            dog.microchip_id = f"MC{random.randint(100000, 999999)}"
            dog.current_status = random.choice([DogStatus.ACTIVE, DogStatus.TRAINING])
            dog.color = random.choice(colors)
            dog.weight = round(random.uniform(25.0, 42.0), 1)
            dog.location = f"Kennel {random.randint(1, 15)}"
            db.session.add(dog)
            dogs.append(dog)
    
    db.session.commit()
    print(f"   ✓ Created {len(dogs)} dogs")
    return dogs

def create_projects():
    """Create active projects"""
    projects_data = [
        ("أمن الحدود الشمالية", "BSN001", "الحدود الشمالية", ProjectStatus.ACTIVE),
        ("أمن المطار الدولي", "AIA002", "المطار الدولي", ProjectStatus.ACTIVE),
        ("برنامج التدريب المتقدم", "ATP003", "مركز التدريب", ProjectStatus.ACTIVE),
    ]
    
    projects = []
    for name, code, location, status in projects_data:
        if not Project.query.filter_by(code=code).first():
            project = Project()
            project.name = name
            project.code = code
            project.description = f"مشروع: {name}"
            project.status = status
            project.start_date = date.today() - timedelta(days=random.randint(60, 300))
            project.location = location
            project.required_dogs = random.randint(5, 12)
            db.session.add(project)
            projects.append(project)
    
    db.session.commit()
    print(f"   ✓ Created {len(projects)} projects")
    return projects

def create_permissions(projects):
    """Create permissions for project managers"""
    pms = User.query.filter_by(role=UserRole.PROJECT_MANAGER).all()
    sections = ['dogs', 'employees', 'training', 'veterinary', 'reports']
    permission_types = list(PermissionType)
    
    count = 0
    for pm in pms:
        for project in projects:
            for section in sections:
                for perm_type in permission_types:
                    if not SubPermission.query.filter_by(
                        user_id=pm.id,
                        project_id=project.id,
                        section=section,
                        permission_type=perm_type
                    ).first():
                        perm = SubPermission()
                        perm.user_id = pm.id
                        perm.project_id = project.id
                        perm.section = section
                        perm.subsection = 'all'
                        perm.permission_type = perm_type
                        perm.is_granted = random.choice([True, True, True, False])  # 75% granted
                        db.session.add(perm)
                        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} permissions")

def create_shifts(projects):
    """Create shifts for projects"""
    shifts_data = [
        ("Morning Shift", time(8, 0), time(16, 0)),
        ("Evening Shift", time(16, 0), time(0, 0)),
        ("Night Shift", time(0, 0), time(8, 0)),
    ]
    
    count = 0
    for project in projects:
        for shift_name, start, end in shifts_data:
            if not ProjectShift.query.filter_by(project_id=project.id, name=shift_name).first():
                shift = ProjectShift()
                shift.project_id = project.id
                shift.name = shift_name
                shift.start_time = start
                shift.end_time = end
                shift.is_active = True
                db.session.add(shift)
                count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} shifts")

def create_training_sessions(dogs, employees, projects):
    """Create training sessions"""
    trainers = [e for e in employees if e.role == EmployeeRole.TRAINER]
    if not trainers:
        print("   ⚠ No trainers found, skipping training sessions")
        return
    
    categories = ['OBEDIENCE', 'DETECTION', 'AGILITY', 'ATTACK', 'FITNESS', 'BEHAVIOR_IMPROVEMENT']
    
    count = 0
    for _ in range(60):
        session = TrainingSession()
        session.dog_id = random.choice(dogs).id if dogs else None
        session.trainer_id = random.choice(trainers).id
        session.project_id = random.choice(projects).id if random.random() < 0.7 else None
        session.category = random.choice(categories)
        session.subject = f"Training: {session.category}"
        session.session_date = datetime.now() - timedelta(days=random.randint(1, 90))
        session.duration = random.randint(45, 120)
        session.success_rating = random.randint(6, 10)
        session.location = f"Training Area {random.randint(1, 5)}"
        session.notes = "Training session completed successfully"
        db.session.add(session)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} training sessions")

def create_veterinary_visits(dogs, employees, projects):
    """Create veterinary visits"""
    vets = [e for e in employees if e.role == EmployeeRole.VET]
    if not vets:
        print("   ⚠ No vets found, skipping veterinary visits")
        return
    
    visit_types = ['ROUTINE', 'EMERGENCY', 'VACCINATION']
    
    count = 0
    for _ in range(40):
        visit = VeterinaryVisit()
        visit.dog_id = random.choice(dogs).id if dogs else None
        visit.vet_id = random.choice(vets).id
        visit.project_id = random.choice(projects).id if random.random() < 0.6 else None
        visit.visit_type = random.choice(visit_types)
        visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 120))
        visit.symptoms = "روتين"
        visit.diagnosis = "بصحة جيدة"
        visit.treatment = "لا يوجد"
        visit.cost = round(random.uniform(150.0, 800.0), 2)
        visit.weight = round(random.uniform(28.0, 42.0), 1)
        visit.notes = "Routine checkup completed"
        db.session.add(visit)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} veterinary visits")

def create_attendance_records(employees, projects):
    """Create attendance records"""
    count = 0
    for _ in range(100):
        record = AttendanceRecord()
        record.employee_id = random.choice(employees).id
        record.project_id = random.choice(projects).id
        record.date = date.today() - timedelta(days=random.randint(1, 60))
        record.check_in = datetime.combine(record.date, time(8, random.randint(0, 30)))
        record.check_out = datetime.combine(record.date, time(16, random.randint(0, 30)))
        record.status = random.choice(['PRESENT', 'PRESENT', 'PRESENT', 'ABSENT', 'LATE'])
        record.notes = "Attendance recorded"
        db.session.add(record)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} attendance records")

def create_feeding_records(dogs, employees):
    """Create feeding records"""
    breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
    if not breeders or not dogs:
        print("   ⚠ Missing breeders or dogs, skipping feeding records")
        return
    
    count = 0
    for _ in range(80):
        record = BreedingFeedingLog()
        record.dog_id = random.choice(dogs).id
        record.log_date = date.today() - timedelta(days=random.randint(1, 45))
        record.log_time = time(random.randint(6, 18), random.randint(0, 59))
        record.food_type = random.choice(["طعام جاف", "طعام رطب", "طعام مخلوط"])
        record.quantity_kg = round(random.uniform(0.5, 2.5), 2)
        record.notes = "تم إطعام الكلب"
        record.recorded_by_id = random.choice(breeders).id
        db.session.add(record)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} feeding records")

def create_checkup_records(dogs, employees):
    """Create checkup records"""
    breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
    if not breeders or not dogs:
        print("   ⚠ Missing breeders or dogs, skipping checkup records")
        return
    
    count = 0
    for _ in range(70):
        record = BreedingCheckupLog()
        record.dog_id = random.choice(dogs).id
        record.log_date = date.today() - timedelta(days=random.randint(1, 50))
        record.log_time = time(random.randint(8, 17), random.randint(0, 59))
        record.health_status = random.choice(["ممتاز", "جيد", "مقبول"])
        record.weight_kg = round(random.uniform(28.0, 42.0), 1)
        record.temperature = round(random.uniform(37.5, 39.0), 1)
        record.notes = "فحص روتيني"
        record.recorded_by_id = random.choice(breeders).id
        db.session.add(record)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} checkup records")

def create_caretaker_logs(dogs, employees):
    """Create caretaker daily logs"""
    breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
    if not breeders or not dogs:
        print("   ⚠ Missing breeders or dogs, skipping caretaker logs")
        return
    
    count = 0
    for _ in range(50):
        log = CaretakerDailyLog()
        log.dog_id = random.choice(dogs).id
        log.log_date = date.today() - timedelta(days=random.randint(1, 40))
        log.activity_type = random.choice(['feeding', 'cleaning', 'exercise', 'grooming'])
        log.activity_details = "نشاط روتيني مكتمل"
        log.recorded_by_id = random.choice(breeders).id
        log.notes = "تم بنجاح"
        db.session.add(log)
        count += 1
    
    db.session.commit()
    print(f"   ✓ Created {count} caretaker daily logs")

if __name__ == "__main__":
    main()
