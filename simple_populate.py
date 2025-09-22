#!/usr/bin/env python3
"""
K9 Operations Management System - Simple Test Data Population
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
import random

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *

def create_test_data():
    """Create test data in smaller, safer batches"""
    print("Creating test data for K9 system...")
    
    with app.app_context():
        try:
            # 1. Create Project Manager Users
            pm_users = []
            for i in range(3):
                username = f"pm{i+1}"
                if not User.query.filter_by(username=username).first():
                    user = User()
                    user.username = username
                    user.email = f"{username}@k9system.local"
                    user.full_name = f"Project Manager {i+1}"
                    user.role = UserRole.PROJECT_MANAGER
                    user.password_hash = generate_password_hash('password123')
                    user.active = True
                    db.session.add(user)
                    pm_users.append(user)
            
            db.session.commit()
            print(f"✓ Created {len(pm_users)} project manager users")
            
            # 2. Create Employees
            employees_data = [
                ("Handler 1", "H001", EmployeeRole.HANDLER),
                ("Handler 2", "H002", EmployeeRole.HANDLER),
                ("Handler 3", "H003", EmployeeRole.HANDLER),
                ("Trainer 1", "T001", EmployeeRole.TRAINER),
                ("Trainer 2", "T002", EmployeeRole.TRAINER),
                ("Breeder 1", "B001", EmployeeRole.BREEDER),
                ("Breeder 2", "B002", EmployeeRole.BREEDER),
                ("Vet 1", "V001", EmployeeRole.VET),
                ("Vet 2", "V002", EmployeeRole.VET),
            ]
            
            employees = []
            for name, emp_id, role in employees_data:
                if not Employee.query.filter_by(employee_id=emp_id).first():
                    employee = Employee()
                    employee.name = name
                    employee.employee_id = emp_id
                    employee.role = role
                    employee.email = f"{emp_id.lower()}@k9unit.local"
                    employee.hire_date = date.today() - timedelta(days=random.randint(30, 500))
                    employee.is_active = True
                    db.session.add(employee)
                    employees.append(employee)
            
            db.session.commit()
            print(f"✓ Created {len(employees)} employees")
            
            # 3. Create Dogs
            dogs = []
            breeds = ["German Shepherd", "Belgian Malinois", "Dutch Shepherd"]
            for i in range(20):
                code = f"K9{i+1:03d}"
                if not Dog.query.filter_by(code=code).first():
                    dog = Dog()
                    dog.name = f"Dog {i+1}"
                    dog.code = code
                    dog.breed = random.choice(breeds)
                    dog.gender = random.choice(list(DogGender))
                    dog.birth_date = date.today() - timedelta(days=random.randint(365, 1500))
                    dog.microchip_id = f"MC{random.randint(100000, 999999)}"
                    dog.current_status = random.choice(list(DogStatus))
                    dog.color = random.choice(["Black", "Brown", "Golden"])
                    dog.weight = round(random.uniform(25.0, 40.0), 1)
                    db.session.add(dog)
                    dogs.append(dog)
            
            db.session.commit()
            print(f"✓ Created {len(dogs)} dogs")
            
            # 4. Create Projects
            projects_data = [
                ("Border Security", "BSA001", ProjectStatus.ACTIVE),
                ("Airport Security", "ASB002", ProjectStatus.ACTIVE),
                ("Training Program", "TPD003", ProjectStatus.PLANNED),
            ]
            
            projects = []
            for name, code, status in projects_data:
                if not Project.query.filter_by(code=code).first():
                    project = Project()
                    project.name = name
                    project.code = code
                    project.description = f"Test project: {name}"
                    project.status = status
                    project.start_date = date.today() - timedelta(days=30)
                    project.location = f"Location {len(projects) + 1}"
                    db.session.add(project)
                    projects.append(project)
            
            db.session.commit()
            print(f"✓ Created {len(projects)} projects")
            
            # 5. Create Training Sessions
            trainers = [e for e in employees if e.role == EmployeeRole.TRAINER]
            if trainers and dogs:
                for _ in range(30):
                    session = TrainingSession()
                    session.dog_id = random.choice(dogs).id
                    session.trainer_id = random.choice(trainers).id
                    session.session_date = datetime.now() - timedelta(days=random.randint(1, 60))
                    session.duration = random.randint(60, 120)
                    session.category = random.choice(list(TrainingCategory))
                    session.subject = f"Training: {session.category.value}"
                    session.success_rating = random.randint(6, 10)
                    session.notes = "Training completed successfully"
                    db.session.add(session)
                
                db.session.commit()
                print("✓ Created 30 training sessions")
            
            # 6. Create Veterinary Visits
            vets = [e for e in employees if e.role == EmployeeRole.VET]
            if vets and dogs:
                for _ in range(25):
                    visit = VeterinaryVisit()
                    visit.dog_id = random.choice(dogs).id
                    visit.vet_id = random.choice(vets).id
                    visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 90))
                    visit.visit_type = random.choice(list(VisitType))
                    visit.symptoms = "Routine checkup"
                    visit.diagnosis = "Healthy"
                    visit.treatment = "No treatment needed"
                    visit.cost = round(random.uniform(100.0, 400.0), 2)
                    visit.weight = round(random.uniform(25.0, 40.0), 1)
                    visit.notes = f"Routine {visit.visit_type.value} visit"
                    db.session.add(visit)
                
                db.session.commit()
                print("✓ Created 25 veterinary visits")
            
            # 7. Create Feeding Logs
            breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
            if breeders and dogs and projects:
                for _ in range(50):
                    feeding = FeedingLog()
                    feeding.project_id = random.choice(projects).id if random.random() < 0.8 else None
                    feeding.date = date.today() - timedelta(days=random.randint(1, 30))
                    feeding.time = time(random.randint(7, 18), 0)
                    feeding.dog_id = random.choice(dogs).id
                    feeding.recorder_employee_id = random.choice(breeders).id
                    feeding.meal_type_fresh = True
                    feeding.meal_name = random.choice(["Morning", "Evening"])
                    feeding.grams = random.randint(300, 600)
                    feeding.water_ml = random.randint(250, 400)
                    feeding.notes = "Daily feeding"
                    db.session.add(feeding)
                
                db.session.commit()
                print("✓ Created 50 feeding logs")
            
            # 8. Create Caretaker Daily Logs
            if breeders and dogs and projects:
                for _ in range(30):
                    log = CaretakerDailyLog()
                    log.project_id = random.choice(projects).id
                    log.date = date.today() - timedelta(days=random.randint(1, 20))
                    log.dog_id = random.choice(dogs).id
                    log.caretaker_employee_id = random.choice(breeders).id
                    log.feeding_morning_given = True
                    log.feeding_evening_given = True
                    log.water_refilled = True
                    log.kennel_cleaned = random.random() < 0.9
                    log.exercise_given = random.random() < 0.8
                    log.health_check_done = random.random() < 0.7
                    log.notes = "Daily care completed"
                    db.session.add(log)
                
                db.session.commit()
                print("✓ Created 30 caretaker daily logs")
            
            # 9. Create Attendance Data
            if projects and employees:
                # Create shifts first
                for project in projects:
                    if project.status == ProjectStatus.ACTIVE:
                        shift = ProjectShift()
                        shift.project_id = project.id
                        shift.name = "Day Shift"
                        shift.start_time = time(8, 0)
                        shift.end_time = time(16, 0)
                        shift.is_active = True
                        db.session.add(shift)
                
                db.session.commit()
                
                # Create attendance records
                for i in range(20):
                    attendance = ProjectAttendanceReporting()
                    attendance.date = date.today() - timedelta(days=random.randint(1, 10))
                    attendance.project_id = random.choice(projects).id
                    attendance.employee_id = random.choice(employees).id
                    attendance.group_no = 1
                    attendance.seq_no = i % 8 + 1
                    attendance.check_in_time = time(8, random.randint(0, 30))
                    attendance.check_out_time = time(16, random.randint(0, 30))
                    attendance.status = AttendanceStatus.PRESENT
                    db.session.add(attendance)
                
                db.session.commit()
                print("✓ Created attendance data")
            
            print("\n" + "="*60)
            print("✅ Test data population completed successfully!")
            print("📊 Summary:")
            print(f"   - {len(pm_users)} project manager users")
            print(f"   - {len(employees)} employees")
            print(f"   - {len(dogs)} dogs")
            print(f"   - {len(projects)} projects")
            print("   - Training sessions, vet visits, daily logs")
            print("   - Attendance records and shifts")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    create_test_data()