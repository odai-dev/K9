#!/usr/bin/env python3
"""
K9 Operations Management System - Test Data Population Script

This script populates the database with comprehensive test data for testing
all reports, functionality, and system integration.
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
import random
import json

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *

def populate_users():
    """Create test users including project managers"""
    print("Creating test users...")
    
    users_data = [
        {"username": "pm1", "email": "pm1@k9system.local", "full_name": "Ahmed Hassan", "role": UserRole.PROJECT_MANAGER},
        {"username": "pm2", "email": "pm2@k9system.local", "full_name": "Omar Salem", "role": UserRole.PROJECT_MANAGER},
        {"username": "pm3", "email": "pm3@k9system.local", "full_name": "Mahmoud Ali", "role": UserRole.PROJECT_MANAGER},
    ]
    
    created_users = []
    for user_data in users_data:
        if not User.query.filter_by(username=user_data["username"]).first():
            user = User()
            user.username = user_data["username"]
            user.email = user_data["email"]
            user.full_name = user_data["full_name"]
            user.role = user_data["role"]
            user.password_hash = generate_password_hash('password123')
            user.active = True
            db.session.add(user)
            created_users.append(user)
    
    db.session.commit()
    print(f"Created {len(created_users)} users")
    return created_users

def populate_employees():
    """Create test employees with different roles"""
    print("Creating test employees...")
    
    employees_data = [
        # Handlers
        {"name": "سعد محمد", "employee_id": "H001", "role": EmployeeRole.HANDLER, "phone": "+966501234567"},
        {"name": "خالد أحمد", "employee_id": "H002", "role": EmployeeRole.HANDLER, "phone": "+966501234568"},
        {"name": "محمد علي", "employee_id": "H003", "role": EmployeeRole.HANDLER, "phone": "+966501234569"},
        {"name": "أحمد حسن", "employee_id": "H004", "role": EmployeeRole.HANDLER, "phone": "+966501234570"},
        
        # Trainers
        {"name": "عبد الله سالم", "employee_id": "T001", "role": EmployeeRole.TRAINER, "phone": "+966501234571"},
        {"name": "يوسف إبراهيم", "employee_id": "T002", "role": EmployeeRole.TRAINER, "phone": "+966501234572"},
        {"name": "فهد محمد", "employee_id": "T003", "role": EmployeeRole.TRAINER, "phone": "+966501234573"},
        
        # Breeders
        {"name": "ناصر العتيبي", "employee_id": "B001", "role": EmployeeRole.BREEDER, "phone": "+966501234574"},
        {"name": "سلطان الرشيد", "employee_id": "B002", "role": EmployeeRole.BREEDER, "phone": "+966501234575"},
        
        # Veterinarians
        {"name": "د. علي الحسن", "employee_id": "V001", "role": EmployeeRole.VET, "phone": "+966501234576"},
        {"name": "د. محمد الخالد", "employee_id": "V002", "role": EmployeeRole.VET, "phone": "+966501234577"},
        
        # Project Managers
        {"name": "عمر السعيد", "employee_id": "PM001", "role": EmployeeRole.PROJECT_MANAGER, "phone": "+966501234578"},
        {"name": "أحمد الملك", "employee_id": "PM002", "role": EmployeeRole.PROJECT_MANAGER, "phone": "+966501234579"},
    ]
    
    created_employees = []
    for emp_data in employees_data:
        if not Employee.query.filter_by(employee_id=emp_data["employee_id"]).first():
            employee = Employee()
            employee.name = emp_data["name"]
            employee.employee_id = emp_data["employee_id"]
            employee.role = emp_data["role"]
            employee.phone = emp_data["phone"]
            employee.email = f"{emp_data['employee_id'].lower()}@k9unit.local"
            employee.hire_date = date.today() - timedelta(days=random.randint(30, 1000))
            employee.is_active = True
            db.session.add(employee)
            created_employees.append(employee)
    
    db.session.commit()
    print(f"Created {len(created_employees)} employees")
    return created_employees

def populate_dogs():
    """Create test dogs with various breeds and characteristics"""
    print("Creating test dogs...")
    
    breeds = ["German Shepherd", "Belgian Malinois", "Dutch Shepherd", "Rottweiler", "Labrador"]
    colors = ["Black", "Brown", "Golden", "Black/Tan", "Sable"]
    specializations = ["Detection", "Patrol", "Tracking", "Search & Rescue", "Protection"]
    
    created_dogs = []
    for i in range(25):
        dog_code = f"K9{i+1:03d}"
        if not Dog.query.filter_by(code=dog_code).first():
            dog = Dog()
            dog.name = random.choice([
                "Rex", "Max", "Duke", "Zeus", "Thor", "Ace", "Bruno", "Rocky", 
                "Hunter", "Scout", "Bandit", "Chief", "Storm", "Shadow", "Titan",
                "Ranger", "Axel", "Diesel", "Rebel", "Blade", "Ghost", "Hawk",
                "Striker", "Phoenix", "Viper"
            ]) + f" {i+1}"
            dog.code = dog_code
            dog.breed = random.choice(breeds)
            dog.family_line = f"Line {random.randint(1, 5)}"
            dog.gender = random.choice(list(DogGender))
            dog.birth_date = date.today() - timedelta(days=random.randint(365, 2000))
            dog.microchip_id = f"MC{random.randint(100000, 999999)}"
            dog.current_status = random.choice(list(DogStatus))
            dog.location = f"Kennel {random.randint(1, 20)}"
            dog.specialization = random.choice(specializations)
            dog.color = random.choice(colors)
            dog.weight = round(random.uniform(20.0, 45.0), 1)
            dog.height = round(random.uniform(55.0, 70.0), 1)
            db.session.add(dog)
            created_dogs.append(dog)
    
    db.session.commit()
    
    # Create some parent relationships
    for i in range(5):
        if len(created_dogs) >= 3:
            father = random.choice([d for d in created_dogs if d.gender == DogGender.MALE])
            mother = random.choice([d for d in created_dogs if d.gender == DogGender.FEMALE])
            child = random.choice([d for d in created_dogs if not d.father_id and not d.mother_id])
            child.father_id = father.id
            child.mother_id = mother.id
    
    db.session.commit()
    print(f"Created {len(created_dogs)} dogs")
    return created_dogs

def populate_projects():
    """Create test projects with different statuses"""
    print("Creating test projects...")
    
    projects_data = [
        {"name": "Border Security Alpha", "code": "BSA001", "status": ProjectStatus.ACTIVE},
        {"name": "Airport Security Beta", "code": "ASB002", "status": ProjectStatus.ACTIVE},
        {"name": "Training Program Delta", "code": "TPD003", "status": ProjectStatus.PLANNED},
        {"name": "Detection Unit Gamma", "code": "DUG004", "status": ProjectStatus.ACTIVE},
        {"name": "Emergency Response", "code": "ER005", "status": ProjectStatus.COMPLETED},
    ]
    
    created_projects = []
    for proj_data in projects_data:
        if not Project.query.filter_by(code=proj_data["code"]).first():
            project = Project()
            project.name = proj_data["name"]
            project.code = proj_data["code"]
            project.description = f"Test project for {proj_data['name']}"
            project.status = proj_data["status"]
            project.start_date = date.today() - timedelta(days=random.randint(1, 180))
            if proj_data["status"] == ProjectStatus.COMPLETED:
                project.end_date = date.today() - timedelta(days=random.randint(1, 30))
            project.location = f"Site {random.randint(1, 10)}"
            db.session.add(project)
            created_projects.append(project)
    
    db.session.commit()
    print(f"Created {len(created_projects)} projects")
    return created_projects

def create_assignments(dogs, employees, projects):
    """Create assignments between dogs, employees, and projects"""
    print("Creating assignments...")
    
    # Assign dogs to projects
    for project in projects:
        if project.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]:
            # Assign 3-8 dogs per project
            num_dogs = random.randint(3, min(8, len(dogs)))
            assigned_dogs = random.sample(dogs, num_dogs)
            project.assigned_dogs = assigned_dogs
    
    # Assign employees to projects
    for project in projects:
        if project.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]:
            # Assign 5-12 employees per project
            num_employees = random.randint(5, min(12, len(employees)))
            assigned_employees = random.sample(employees, num_employees)
            project.assigned_employees = assigned_employees
    
    # Assign dogs to handlers
    handlers = [e for e in employees if e.role == EmployeeRole.HANDLER]
    for handler in handlers:
        # Each handler gets 2-4 dogs
        num_dogs = random.randint(2, min(4, len(dogs)))
        assigned_dogs = random.sample(dogs, num_dogs)
        handler.assigned_dogs = assigned_dogs
    
    db.session.commit()
    print("Created assignments between dogs, employees, and projects")

def populate_training_sessions(dogs, employees):
    """Create training session records"""
    print("Creating training sessions...")
    
    trainers = [e for e in employees if e.role == EmployeeRole.TRAINER]
    if not trainers:
        print("No trainers found, skipping training sessions")
        return []
    
    created_sessions = []
    # Create 50 training sessions over the last 90 days
    for _ in range(50):
        session = TrainingSession()
        session.dog = random.choice(dogs)
        session.trainer = random.choice(trainers)
        session.session_date = datetime.now() - timedelta(days=random.randint(1, 90))
        session.duration = random.randint(30, 180)  # 30-180 minutes
        session.category = random.choice(list(TrainingCategory))
        session.subject = f"Training session for {session.category.value}"
        session.notes = random.choice([
            "Excellent progress", "Good performance", "Needs improvement", 
            "Outstanding results", "Satisfactory work"
        ])
        session.success_rating = random.randint(1, 10)
        session.location = f"Training Ground {random.randint(1, 5)}"
        db.session.add(session)
        created_sessions.append(session)
    
    db.session.commit()
    print(f"Created {len(created_sessions)} training sessions")
    return created_sessions

def populate_veterinary_visits(dogs, employees):
    """Create veterinary visit records"""
    print("Creating veterinary visits...")
    
    vets = [e for e in employees if e.role == EmployeeRole.VET]
    if not vets:
        print("No veterinarians found, skipping veterinary visits")
        return []
    
    created_visits = []
    # Create 40 vet visits over the last 120 days
    for _ in range(40):
        visit = VeterinaryVisit()
        visit.dog = random.choice(dogs)
        visit.vet = random.choice(vets)
        visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 120))
        visit.visit_type = random.choice(list(VisitType))
        visit.symptoms = random.choice([
            "Routine checkup", "Vaccination due", "Minor injury", "Digestive issues",
            "Skin condition", "Joint pain", "Behavioral assessment"
        ])
        visit.diagnosis = random.choice([
            "Healthy", "Minor infection", "Nutritional deficiency", "Allergic reaction",
            "Muscle strain", "Vaccination completed", "Requires monitoring"
        ])
        visit.treatment = random.choice([
            "No treatment needed", "Prescribed medication", "Rest recommended",
            "Diet adjustment", "Follow-up visit scheduled", "Vaccination administered"
        ])
        visit.cost = round(random.uniform(50.0, 500.0), 2)
        visit.notes = f"Visit for {visit.visit_type.value}"
        visit.weight = round(random.uniform(20.0, 45.0), 1)
        visit.temperature = round(random.uniform(38.0, 39.5), 1)
        visit.heart_rate = random.randint(60, 120)
        db.session.add(visit)
        created_visits.append(visit)
    
    db.session.commit()
    print(f"Created {len(created_visits)} veterinary visits")
    return created_visits

def populate_breeding_data(dogs):
    """Create comprehensive breeding data using ProductionCycle model"""
    print("Creating breeding data...")
    
    # Create production cycles (breeding records)
    male_dogs = [d for d in dogs if d.gender == DogGender.MALE]
    female_dogs = [d for d in dogs if d.gender == DogGender.FEMALE]
    
    for _ in range(8):
        if female_dogs and male_dogs:
            cycle = ProductionCycle()
            cycle.female = random.choice(female_dogs)
            cycle.male = random.choice(male_dogs)
            cycle.cycle_type = random.choice(list(ProductionCycleType))
            cycle.mating_date = date.today() - timedelta(days=random.randint(30, 200))
            cycle.heat_start_date = cycle.mating_date - timedelta(days=random.randint(1, 7))
            cycle.expected_delivery_date = cycle.mating_date + timedelta(days=63)
            if random.random() < 0.6:  # 60% have delivered
                cycle.actual_delivery_date = cycle.expected_delivery_date + timedelta(days=random.randint(-3, 7))
                cycle.result = ProductionResult.SUCCESSFUL if random.random() < 0.8 else ProductionResult.FAILED
                if cycle.result == ProductionResult.SUCCESSFUL:
                    cycle.number_of_puppies = random.randint(3, 8)
                    cycle.puppies_survived = random.randint(max(1, cycle.number_of_puppies - 2), cycle.number_of_puppies)
                    puppy_info = []
                    for i in range(cycle.number_of_puppies):
                        puppy_info.append({
                            "name": f"Puppy {i+1}",
                            "gender": random.choice(["MALE", "FEMALE"]),
                            "birth_weight": round(random.uniform(0.3, 0.8), 2)
                        })
                    cycle.puppies_info = puppy_info
            else:
                cycle.result = ProductionResult.UNKNOWN
            
            cycle.prenatal_care = "Regular checkups and proper nutrition"
            cycle.delivery_notes = f"Delivery for {cycle.female.name}"
            db.session.add(cycle)
    
    db.session.commit()
    print("Created breeding data records")

def populate_attendance_data(projects, employees):
    """Create attendance and shift data"""
    print("Creating attendance data...")
    
    # Create shifts for active projects
    created_shifts = []
    for project in projects:
        if project.status == ProjectStatus.ACTIVE:
            # Morning shift
            shift1 = ProjectShift()
            shift1.project = project
            shift1.name = "Morning Shift"
            shift1.start_time = time(6, 0)
            shift1.end_time = time(14, 0)
            shift1.is_active = True
            db.session.add(shift1)
            created_shifts.append(shift1)
            
            # Evening shift
            shift2 = ProjectShift()
            shift2.project = project
            shift2.name = "Evening Shift"
            shift2.start_time = time(14, 0)
            shift2.end_time = time(22, 0)
            shift2.is_active = True
            db.session.add(shift2)
            created_shifts.append(shift2)
    
    db.session.commit()
    
    # Create attendance records for the last 30 days
    for days_ago in range(30):
        attendance_date = date.today() - timedelta(days=days_ago)
        
        for project in projects:
            if project.status == ProjectStatus.ACTIVE and project.assigned_employees:
                # Create attendance reporting entries
                seq = 1
                for employee in project.assigned_employees[:15]:  # Limit to 15 per day
                    attendance = ProjectAttendanceReporting()
                    attendance.date = attendance_date
                    attendance.project_id = project.id
                    attendance.employee_id = employee.id
                    attendance.group_no = 1 if seq <= 8 else 2
                    attendance.seq_no = seq if seq <= 8 else seq - 8
                    attendance.check_in_time = time(random.randint(6, 8), random.randint(0, 59))
                    attendance.check_out_time = time(random.randint(14, 16), random.randint(0, 59))
                    attendance.status = random.choice(list(AttendanceStatus))
                    db.session.add(attendance)
                    seq += 1
    
    # Create some leave records
    for _ in range(20):
        leave = AttendanceDayLeave()
        leave.project_id = random.choice(projects).id
        leave.date = date.today() - timedelta(days=random.randint(1, 30))
        leave.employee_id = random.choice(employees).id
        leave.leave_type = random.choice(list(LeaveType))
        leave.note = "Personal leave"
        leave.seq_no = random.randint(1, 10)
        db.session.add(leave)
    
    db.session.commit()
    print("Created attendance and shift data")

def populate_daily_logs(dogs, employees, projects):
    """Create various daily activity logs"""
    print("Creating daily activity logs...")
    
    breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
    if not breeders:
        print("No breeders found, using handlers for daily logs")
        breeders = [e for e in employees if e.role == EmployeeRole.HANDLER][:3]
    
    # Create feeding logs
    for _ in range(100):
        feeding = FeedingLog()
        feeding.project_id = random.choice(projects).id if random.random() < 0.8 else None
        feeding.date = date.today() - timedelta(days=random.randint(1, 60))
        feeding.time = time(random.randint(6, 18), random.randint(0, 59))
        feeding.dog_id = random.choice(dogs).id
        feeding.recorder_employee_id = random.choice(breeders).id if breeders else None
        feeding.meal_type_fresh = random.random() < 0.6
        feeding.meal_type_dry = random.random() < 0.4
        feeding.meal_name = random.choice(["Morning Meal", "Evening Meal", "Lunch", "Snack"])
        feeding.grams = random.randint(200, 800)
        feeding.water_ml = random.randint(200, 500)
        feeding.notes = "Regular feeding"
        db.session.add(feeding)
    
    # Create cleaning logs
    for _ in range(80):
        cleaning = CleaningLog()
        cleaning.project_id = random.choice(projects).id if random.random() < 0.8 else None
        cleaning.date = date.today() - timedelta(days=random.randint(1, 60))
        cleaning.time = time(random.randint(8, 16), random.randint(0, 59))
        cleaning.dog_id = random.choice(dogs).id
        cleaning.cleaner_employee_id = random.choice(breeders).id if breeders else None
        cleaning.kennel_cleaned = random.random() < 0.9
        cleaning.food_water_area_cleaned = random.random() < 0.8
        cleaning.toys_cleaned = random.random() < 0.6
        cleaning.notes = "Daily cleaning"
        db.session.add(cleaning)
    
    # Create excretion logs  
    for _ in range(120):
        excretion = ExcretionLog()
        excretion.project_id = random.choice(projects).id if random.random() < 0.8 else None
        excretion.date = date.today() - timedelta(days=random.randint(1, 60))
        excretion.time = time(random.randint(6, 20), random.randint(0, 59))
        excretion.dog_id = random.choice(dogs).id
        excretion.observer_employee_id = random.choice(breeders).id if breeders else None
        excretion.stool_observed = random.random() < 0.7
        excretion.urine_observed = random.random() < 0.8
        excretion.notes = "Normal excretion"
        db.session.add(excretion)
    
    # Create caretaker daily logs
    for _ in range(40):
        caretaker_log = CaretakerDailyLog()
        caretaker_log.project_id = random.choice(projects).id
        caretaker_log.date = date.today() - timedelta(days=random.randint(1, 30))
        caretaker_log.dog_id = random.choice(dogs).id
        caretaker_log.caretaker_employee_id = random.choice(breeders).id if breeders else None
        caretaker_log.feeding_morning_given = random.random() < 0.9
        caretaker_log.feeding_evening_given = random.random() < 0.9
        caretaker_log.water_refilled = random.random() < 0.95
        caretaker_log.kennel_cleaned = random.random() < 0.85
        caretaker_log.exercise_given = random.random() < 0.7
        caretaker_log.health_check_done = random.random() < 0.8
        caretaker_log.notes = "Daily care completed"
        db.session.add(caretaker_log)
    
    db.session.commit()
    print("Created daily activity logs")

def main():
    """Main function to populate all test data"""
    print("Starting K9 system test data population...")
    print("="*60)
    
    with app.app_context():
        try:
            # Create all data in order
            users = populate_users()
            employees = populate_employees()
            dogs = populate_dogs()
            projects = populate_projects()
            
            # Create relationships
            create_assignments(dogs, employees, projects)
            
            # Create activity records
            populate_training_sessions(dogs, employees)
            populate_veterinary_visits(dogs, employees)
            populate_breeding_data(dogs)
            populate_attendance_data(projects, employees)
            populate_daily_logs(dogs, employees, projects)
            
            print("="*60)
            print("✅ Test data population completed successfully!")
            print(f"📊 Created:")
            print(f"   - {len(users)} additional users")
            print(f"   - {len(employees)} employees")
            print(f"   - {len(dogs)} dogs")
            print(f"   - {len(projects)} projects")
            print(f"   - Training sessions, vet visits, breeding records")
            print(f"   - Attendance data and daily activity logs")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during data population: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == "__main__":
    main()