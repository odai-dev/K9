#!/usr/bin/env python3
"""
Populate activity data for K9 system using existing base data
"""

import os
import sys
from datetime import datetime, date, time, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from k9.models.models import *
from k9.models.models_attendance_reporting import *

def main():
    print("=" * 60)
    print("Populating K9 Activity Data")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Get existing data
            dogs = Dog.query.all()
            employees = Employee.query.all()
            projects = Project.query.filter_by(status=ProjectStatus.ACTIVE).all()
            trainers = Employee.query.filter_by(role=EmployeeRole.TRAINER).all()
            vets = Employee.query.filter_by(role=EmployeeRole.VET).all()
            breeders = Employee.query.filter_by(role=EmployeeRole.BREEDER).all()
            
            print(f"\nFound: {len(dogs)} dogs, {len(employees)} employees, {len(projects)} projects")
            print(f"       {len(trainers)} trainers, {len(vets)} vets, {len(breeders)} breeders")
            
            if not (dogs and employees and projects):
                print("\n❌ Missing base data. Please ensure dogs, employees, and projects exist.")
                return
            
            # 1. Training Sessions
            print("\n1. Creating training sessions...")
            create_training_sessions(dogs, trainers, projects)
            
            # 2. Veterinary Visits
            print("2. Creating veterinary visits...")
            create_veterinary_visits(dogs, vets, projects)
            
            # 3. Attendance Records
            print("3. Creating attendance records...")
            create_attendance(employees, projects)
            
            # 4. Feeding Records
            print("4. Creating feeding records...")
            create_feeding(dogs, breeders)
            
            # 5. Checkup Records
            print("5. Creating checkup records...")
            create_checkups(dogs, breeders)
            
            # 6. Caretaker Logs
            print("6. Creating caretaker logs...")
            create_caretaker_logs(dogs, breeders)
            
            # 7. Breeding Training Activities
            print("7. Creating breeding training activities...")
            create_breeding_training(dogs, employees)
            
            print("\n" + "=" * 60)
            print("✅ Activity data population completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

def create_training_sessions(dogs, trainers, projects):
    if not trainers:
        print("   ⚠ No trainers available")
        return
    
    categories = ['OBEDIENCE', 'DETECTION', 'AGILITY', 'ATTACK', 'FITNESS']
    count = 0
    
    for i in range(80):
        session = TrainingSession()
        session.dog_id = random.choice(dogs).id
        session.trainer_id = random.choice(trainers).id
        session.project_id = random.choice(projects).id if random.random() < 0.7 else None
        session.category = random.choice(categories)
        session.subject = f"تدريب {session.category}"
        session.session_date = datetime.now() - timedelta(days=random.randint(1, 90))
        session.duration = random.randint(45, 120)
        session.success_rating = random.randint(6, 10)
        session.location = f"ميدان تدريب {random.randint(1, 5)}"
        session.notes = "جلسة تدريبية ناجحة"
        db.session.add(session)
        count += 1
        
        if count % 20 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} training sessions")

def create_veterinary_visits(dogs, vets, projects):
    if not vets:
        print("   ⚠ No vets available")
        return
    
    visit_types = ['ROUTINE', 'EMERGENCY', 'VACCINATION']
    count = 0
    
    for i in range(60):
        visit = VeterinaryVisit()
        visit.dog_id = random.choice(dogs).id
        visit.vet_id = random.choice(vets).id
        visit.project_id = random.choice(projects).id if random.random() < 0.6 else None
        visit.visit_type = random.choice(visit_types)
        visit.visit_date = datetime.now() - timedelta(days=random.randint(1, 120))
        visit.symptoms = random.choice(["فحص روتيني", "تطعيم", "فحص طارئ"])
        visit.diagnosis = random.choice(["بصحة جيدة", "يحتاج مراقبة", "ممتاز"])
        visit.treatment = random.choice(["لا يوجد", "أدوية", "تطعيمات"])
        visit.cost = round(random.uniform(150.0, 1200.0), 2)
        visit.weight = round(random.uniform(28.0, 42.0), 1)
        visit.notes = f"زيارة {visit.visit_type}"
        db.session.add(visit)
        count += 1
        
        if count % 20 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} veterinary visits")

def create_attendance(employees, projects):
    count = 0
    
    for i in range(120):
        record = AttendanceRecord()
        record.employee_id = random.choice(employees).id
        record.project_id = random.choice(projects).id
        record.date = date.today() - timedelta(days=random.randint(1, 60))
        record.check_in = datetime.combine(record.date, time(8, random.randint(0, 45)))
        record.check_out = datetime.combine(record.date, time(16, random.randint(0, 45)))
        record.status = random.choice(['PRESENT', 'PRESENT', 'PRESENT', 'ABSENT', 'LATE'])
        record.notes = "سجل حضور"
        db.session.add(record)
        count += 1
        
        if count % 30 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} attendance records")

def create_feeding(dogs, breeders):
    if not breeders:
        print("   ⚠ No breeders available")
        return
    
    count = 0
    
    for i in range(100):
        record = BreedingFeedingLog()
        record.dog_id = random.choice(dogs).id
        record.log_date = date.today() - timedelta(days=random.randint(1, 50))
        record.log_time = time(random.randint(6, 18), random.randint(0, 59))
        record.food_type = random.choice(["طعام جاف", "طعام رطب", "طعام مخلوط", "طعام خاص"])
        record.quantity_kg = round(random.uniform(0.5, 3.0), 2)
        record.notes = "تم إطعام الكلب بنجاح"
        record.recorded_by_id = random.choice(breeders).id
        db.session.add(record)
        count += 1
        
        if count % 25 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} feeding records")

def create_checkups(dogs, breeders):
    if not breeders:
        print("   ⚠ No breeders available")
        return
    
    count = 0
    
    for i in range(90):
        record = BreedingCheckupLog()
        record.dog_id = random.choice(dogs).id
        record.log_date = date.today() - timedelta(days=random.randint(1, 55))
        record.log_time = time(random.randint(8, 17), random.randint(0, 59))
        record.health_status = random.choice(["ممتاز", "جيد جداً", "جيد", "مقبول"])
        record.weight_kg = round(random.uniform(28.0, 43.0), 1)
        record.temperature = round(random.uniform(37.5, 39.2), 1)
        record.notes = "فحص روتيني يومي"
        record.recorded_by_id = random.choice(breeders).id
        db.session.add(record)
        count += 1
        
        if count % 25 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} checkup records")

def create_caretaker_logs(dogs, breeders):
    if not breeders:
        print("   ⚠ No breeders available")
        return
    
    count = 0
    activities = ['feeding', 'cleaning', 'exercise', 'grooming', 'health_check']
    
    for i in range(80):
        log = CaretakerDailyLog()
        log.dog_id = random.choice(dogs).id
        log.log_date = date.today() - timedelta(days=random.randint(1, 45))
        log.activity_type = random.choice(activities)
        log.activity_details = f"نشاط {log.activity_type} مكتمل"
        log.recorded_by_id = random.choice(breeders).id
        log.notes = "تم بنجاح"
        db.session.add(log)
        count += 1
        
        if count % 20 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} caretaker daily logs")

def create_breeding_training(dogs, employees):
    count = 0
    subtypes = ['basic_obedience', 'advanced_detection', 'agility_training']
    
    for i in range(50):
        activity = BreedingTrainingActivity()
        activity.dog_id = random.choice(dogs).id
        activity.activity_date = date.today() - timedelta(days=random.randint(1, 60))
        activity.subtype = random.choice(subtypes)
        activity.duration_minutes = random.randint(30, 120)
        activity.performance_rating = random.randint(6, 10)
        activity.notes = "نشاط تدريبي في التكاثر"
        activity.recorded_by_id = random.choice(employees).id
        db.session.add(activity)
        count += 1
        
        if count % 15 == 0:
            db.session.commit()
    
    db.session.commit()
    print(f"   ✓ Created {count} breeding training activities")

if __name__ == "__main__":
    main()
