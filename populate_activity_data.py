#!/usr/bin/env python3
"""
Populate activity data for K9 system testing
"""

import os
import sys
from datetime import datetime, date, time, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *

def populate_activity_data():
    """Populate missing activity data for testing"""
    print("Populating activity data for testing...")
    
    with app.app_context():
        try:
            # Get existing data
            dogs = Dog.query.all()
            employees = Employee.query.all()
            projects = Project.query.filter_by(status=ProjectStatus.ACTIVE).all()
            trainers = [e for e in employees if e.role == EmployeeRole.TRAINER]
            vets = [e for e in employees if e.role == EmployeeRole.VET]
            breeders = [e for e in employees if e.role == EmployeeRole.BREEDER]
            handlers = [e for e in employees if e.role == EmployeeRole.HANDLER]
            
            print(f"Found {len(dogs)} dogs, {len(employees)} employees, {len(projects)} active projects")
            
            if not dogs or not employees or not projects:
                print("Missing basic data - cannot populate activity data")
                return
            
            # 1. Create Training Sessions
            print("Creating training sessions...")
            for _ in range(40):
                if trainers and dogs:
                    session = TrainingSession()
                    session.dog_id = random.choice(dogs).id
                    session.trainer_id = random.choice(trainers).id
                    session.project_id = random.choice(projects).id if random.random() < 0.8 else None
                    session.session_date = datetime.now() - timedelta(days=random.randint(1, 60))
                    session.duration = random.randint(60, 120)
                    session.category = random.choice(list(TrainingCategory))
                    session.subject = f"Training: {session.category.value}"
                    session.success_rating = random.randint(6, 10)
                    session.location = f"Training Ground {random.randint(1, 5)}"
                    session.notes = "Training session completed successfully"
                    db.session.add(session)
            
            db.session.commit()
            print("✓ Created training sessions")
            
            # 2. Create Veterinary Visits
            print("Creating veterinary visits...")
            for _ in range(30):
                if vets and dogs:
                    visit = VeterinaryVisit()
                    visit.dog_id = random.choice(dogs).id
                    visit.vet_id = random.choice(vets).id
                    visit.project_id = random.choice(projects).id if random.random() < 0.7 else None
                    visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 90))
                    visit.visit_type = random.choice(list(VisitType))
                    visit.symptoms = random.choice(["Routine checkup", "Vaccination", "Health screening"])
                    visit.diagnosis = random.choice(["Healthy", "Minor condition", "Requires monitoring"])
                    visit.treatment = random.choice(["No treatment needed", "Medication prescribed", "Follow-up required"])
                    visit.cost = round(random.uniform(100.0, 500.0), 2)
                    visit.weight = round(random.uniform(25.0, 40.0), 1)
                    visit.temperature = round(random.uniform(38.0, 39.5), 1)
                    visit.heart_rate = random.randint(70, 120)
                    visit.notes = f"Routine {visit.visit_type.value} visit completed"
                    db.session.add(visit)
            
            db.session.commit()
            print("✓ Created veterinary visits")
            
            # 3. Create Attendance Records
            print("Creating attendance records...")
            
            # First create shifts for active projects
            for project in projects:
                # Morning shift
                shift1 = ProjectShift()
                shift1.project_id = project.id
                shift1.name = "Morning Shift"
                shift1.start_time = time(8, 0)
                shift1.end_time = time(16, 0)
                shift1.is_active = True
                db.session.add(shift1)
                
                # Evening shift
                shift2 = ProjectShift()
                shift2.project_id = project.id
                shift2.name = "Evening Shift"
                shift2.start_time = time(16, 0)
                shift2.end_time = time(24, 0)
                shift2.is_active = True
                db.session.add(shift2)
            
            db.session.commit()
            
            # Create attendance records for the last 15 days
            for days_ago in range(15):
                attendance_date = date.today() - timedelta(days=days_ago)
                
                for project in projects:
                    # Select 8-12 employees per project per day
                    daily_employees = random.sample(employees, min(len(employees), random.randint(8, 12)))
                    
                    for i, employee in enumerate(daily_employees):
                        attendance = ProjectAttendanceReporting()
                        attendance.date = attendance_date
                        attendance.project_id = project.id
                        attendance.employee_id = employee.id
                        attendance.group_no = 1 if i < 8 else 2
                        attendance.seq_no = (i % 8) + 1
                        
                        # Random check-in/out times
                        base_checkin = 8 if i < 8 else 16
                        attendance.check_in_time = time(base_checkin + random.randint(0, 1), random.randint(0, 30))
                        attendance.check_out_time = time(base_checkin + 8 + random.randint(0, 1), random.randint(0, 30))
                        
                        attendance.status = random.choice([AttendanceStatus.PRESENT] * 8 + [AttendanceStatus.LATE, AttendanceStatus.ABSENT])
                        db.session.add(attendance)
            
            db.session.commit()
            print("✓ Created attendance records")
            
            # 4. Create Feeding Logs
            print("Creating feeding logs...")
            for _ in range(80):
                if breeders and dogs:
                    feeding = FeedingLog()
                    feeding.project_id = random.choice(projects).id if random.random() < 0.8 else None
                    feeding.date = date.today() - timedelta(days=random.randint(1, 30))
                    feeding.time = time(random.randint(7, 18), 0)
                    feeding.dog_id = random.choice(dogs).id
                    feeding.recorder_employee_id = random.choice(breeders + handlers).id
                    feeding.meal_type_fresh = random.random() < 0.7
                    feeding.meal_type_dry = random.random() < 0.5
                    feeding.meal_name = random.choice(["Morning Feed", "Evening Feed", "Afternoon Snack"])
                    feeding.grams = random.randint(300, 700)
                    feeding.water_ml = random.randint(250, 500)
                    feeding.notes = "Regular feeding completed"
                    db.session.add(feeding)
            
            db.session.commit()
            print("✓ Created feeding logs")
            
            # 5. Create Caretaker Daily Logs
            print("Creating caretaker daily logs...")
            for _ in range(60):
                if (breeders or handlers) and dogs:
                    log = CaretakerDailyLog()
                    log.project_id = random.choice(projects).id
                    log.date = date.today() - timedelta(days=random.randint(1, 20))
                    log.dog_id = random.choice(dogs).id
                    log.caretaker_employee_id = random.choice(breeders + handlers).id if (breeders or handlers) else None
                    log.feeding_morning_given = random.random() < 0.95
                    log.feeding_evening_given = random.random() < 0.90
                    log.water_refilled = random.random() < 0.98
                    log.kennel_cleaned = random.random() < 0.85
                    log.exercise_given = random.random() < 0.80
                    log.health_check_done = random.random() < 0.75
                    log.notes = "Daily care routine completed"
                    db.session.add(log)
            
            db.session.commit()
            print("✓ Created caretaker daily logs")
            
            # 6. Create some production cycles for breeding data
            print("Creating breeding data...")
            male_dogs = [d for d in dogs if d.gender == DogGender.MALE]
            female_dogs = [d for d in dogs if d.gender == DogGender.FEMALE]
            
            for _ in range(5):
                if male_dogs and female_dogs:
                    cycle = ProductionCycle()
                    cycle.female_id = random.choice(female_dogs).id
                    cycle.male_id = random.choice(male_dogs).id
                    cycle.cycle_type = random.choice(list(ProductionCycleType))
                    cycle.mating_date = date.today() - timedelta(days=random.randint(30, 180))
                    cycle.heat_start_date = cycle.mating_date - timedelta(days=random.randint(1, 7))
                    cycle.expected_delivery_date = cycle.mating_date + timedelta(days=63)
                    
                    if random.random() < 0.6:  # 60% have delivered
                        cycle.actual_delivery_date = cycle.expected_delivery_date + timedelta(days=random.randint(-3, 7))
                        cycle.result = ProductionResult.SUCCESSFUL if random.random() < 0.8 else ProductionResult.FAILED
                        if cycle.result == ProductionResult.SUCCESSFUL:
                            cycle.number_of_puppies = random.randint(3, 8)
                            cycle.puppies_survived = random.randint(max(1, cycle.number_of_puppies - 2), cycle.number_of_puppies)
                    else:
                        cycle.result = ProductionResult.UNKNOWN
                    
                    cycle.prenatal_care = "Regular checkups and proper nutrition provided"
                    cycle.delivery_notes = "Standard delivery procedure followed"
                    db.session.add(cycle)
            
            db.session.commit()
            print("✓ Created breeding data")
            
            print("\n" + "="*60)
            print("✅ Activity data population completed successfully!")
            
            # Verify data counts
            print("📊 Final data counts:")
            print(f"   - Training Sessions: {TrainingSession.query.count()}")
            print(f"   - Veterinary Visits: {VeterinaryVisit.query.count()}")
            print(f"   - Attendance Records: {ProjectAttendanceReporting.query.count()}")
            print(f"   - Project Shifts: {ProjectShift.query.count()}")
            print(f"   - Feeding Logs: {FeedingLog.query.count()}")
            print(f"   - Caretaker Logs: {CaretakerDailyLog.query.count()}")
            print(f"   - Production Cycles: {ProductionCycle.query.count()}")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    populate_activity_data()