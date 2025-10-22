#!/usr/bin/env python3
"""
Populate test data for K9 Operations Management System
"""

import os
import sys
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def populate():
    """Populate test data using SQL to avoid enum issues"""
    print("Populating K9 system with test data...")
    
    with app.app_context():
        try:
            # Get what was already created
            existing_users = db.session.execute(db.text("SELECT COUNT(*) FROM \"user\"")).scalar()
            existing_employees = db.session.execute(db.text("SELECT COUNT(*) FROM employee")).scalar()
            existing_dogs = db.session.execute(db.text("SELECT COUNT(*) FROM dog")).scalar()
            existing_projects = db.session.execute(db.text("SELECT COUNT(*) FROM project")).scalar()
            
            print(f"Found existing data: {existing_users} users, {existing_employees} employees, {existing_dogs} dogs, {existing_projects} projects")
            
            # Get IDs for relationships
            dog_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM dog")).fetchall()]
            employee_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM employee")).fetchall()]
            project_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM project WHERE status = 'ACTIVE'")).fetchall()]
            trainer_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM employee WHERE role = 'TRAINER'")).fetchall()]
            vet_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM employee WHERE role = 'VET'")).fetchall()]
            breeder_ids = [row[0] for row in db.session.execute(db.text("SELECT id FROM employee WHERE role = 'BREEDER'")).fetchall()]
            
            print(f"IDs available: {len(dog_ids)} dogs, {len(trainer_ids)} trainers, {len(vet_ids)} vets, {len(breeder_ids)} breeders")
            
            # 1. Create Training Sessions with valid enum values
            if trainer_ids and dog_ids:
                print("Creating training sessions...")
                categories = ['OBEDIENCE', 'DETECTION', 'AGILITY', 'ATTACK', 'FITNESS', 'BEHAVIOR_IMPROVEMENT']
                
                for i in range(25):
                    session_date = datetime.now() - timedelta(days=random.randint(1, 45))
                    dog_id = random.choice(dog_ids)
                    trainer_id = random.choice(trainer_ids)
                    project_id = random.choice(project_ids) if project_ids and random.random() < 0.8 else None
                    category = random.choice(categories)
                    
                    sql = """
                    INSERT INTO training_session 
                    (id, dog_id, trainer_id, project_id, category, subject, session_date, duration, success_rating, notes)
                    VALUES (gen_random_uuid(), :dog_id, :trainer_id, :project_id, :category, :subject, :session_date, :duration, :success_rating, :notes)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'dog_id': dog_id,
                        'trainer_id': trainer_id,
                        'project_id': project_id,
                        'category': category,
                        'subject': f'Training: {category}',
                        'session_date': session_date,
                        'duration': random.randint(60, 120),
                        'success_rating': random.randint(6, 10),
                        'notes': 'Training session completed successfully'
                    })
                
                db.session.commit()
                print("✓ Created 25 training sessions")
            
            # 2. Create Veterinary Visits
            if vet_ids and dog_ids:
                print("Creating veterinary visits...")
                visit_types = ['ROUTINE', 'EMERGENCY', 'VACCINATION']
                
                for i in range(20):
                    visit_date = datetime.now() - timedelta(days=random.randint(1, 60))
                    dog_id = random.choice(dog_ids)
                    vet_id = random.choice(vet_ids)
                    project_id = random.choice(project_ids) if project_ids and random.random() < 0.7 else None
                    visit_type = random.choice(visit_types)
                    
                    sql = """
                    INSERT INTO veterinary_visit 
                    (id, dog_id, vet_id, project_id, visit_type, visit_date, symptoms, diagnosis, treatment, cost, weight, notes)
                    VALUES (gen_random_uuid(), :dog_id, :vet_id, :project_id, :visit_type, :visit_date, :symptoms, :diagnosis, :treatment, :cost, :weight, :notes)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'dog_id': dog_id,
                        'vet_id': vet_id,
                        'project_id': project_id,
                        'visit_type': visit_type,
                        'visit_date': visit_date,
                        'symptoms': 'Routine checkup',
                        'diagnosis': 'Healthy',
                        'treatment': 'No treatment needed',
                        'cost': round(random.uniform(100.0, 500.0), 2),
                        'weight': round(random.uniform(25.0, 40.0), 1),
                        'notes': f'{visit_type} visit completed'
                    })
                
                db.session.commit()
                print("✓ Created 20 veterinary visits")
            
            # 3. Create Project Shifts
            if project_ids:
                print("Creating project shifts...")
                for project_id in project_ids:
                    # Check if shift already exists
                    existing = db.session.execute(
                        db.text("SELECT COUNT(*) FROM project_shift WHERE project_id = :pid"),
                        {'pid': project_id}
                    ).scalar()
                    
                    if existing == 0:
                        sql = """
                        INSERT INTO project_shift (id, project_id, name, start_time, end_time, is_active)
                        VALUES (gen_random_uuid(), :project_id, :name, :start_time, :end_time, :is_active)
                        """
                        
                        db.session.execute(db.text(sql), {
                            'project_id': project_id,
                            'name': 'Day Shift',
                            'start_time': time(8, 0),
                            'end_time': time(16, 0),
                            'is_active': True
                        })
                
                db.session.commit()
                print("✓ Created project shifts")
            
            # 4. Create Attendance Records
            if project_ids and employee_ids:
                print("Creating attendance records...")
                statuses = ['PRESENT', 'LATE', 'ABSENT']
                
                for days_ago in range(10):
                    attendance_date = date.today() - timedelta(days=days_ago)
                    
                    for project_id in project_ids:
                        # Select 6 employees per project per day
                        selected = random.sample(employee_ids, min(len(employee_ids), 6))
                        
                        for i, employee_id in enumerate(selected):
                            sql = """
                            INSERT INTO project_attendance_reporting 
                            (id, date, project_id, employee_id, group_no, seq_no, check_in_time, check_out_time, status, is_project_controlled)
                            VALUES (gen_random_uuid(), :date, :project_id, :employee_id, :group_no, :seq_no, :check_in, :check_out, :status, :is_project_controlled)
                            """
                            
                            status = random.choice(statuses) if random.random() < 0.1 else 'PRESENT'
                            
                            db.session.execute(db.text(sql), {
                                'date': attendance_date,
                                'project_id': project_id,
                                'employee_id': employee_id,
                                'group_no': 1,
                                'seq_no': i + 1,
                                'check_in': time(8, random.randint(0, 30)),
                                'check_out': time(16, random.randint(0, 30)),
                                'status': status,
                                'is_project_controlled': True
                            })
                
                db.session.commit()
                print("✓ Created attendance records for 10 days")
            
            # 5. Create Feeding Logs
            caretaker_ids = breeder_ids if breeder_ids else employee_ids[:3]
            if caretaker_ids and dog_ids:
                print("Creating feeding logs...")
                
                for i in range(40):
                    feeding_date = date.today() - timedelta(days=random.randint(1, 20))
                    feeding_time = time(random.randint(7, 18), 0)
                    project_id = random.choice(project_ids) if project_ids and random.random() < 0.8 else None
                    
                    sql = """
                    INSERT INTO feeding_log 
                    (id, project_id, date, time, dog_id, recorder_employee_id, meal_type_fresh, meal_type_dry, meal_name, grams, water_ml, notes, created_at)
                    VALUES (gen_random_uuid(), :project_id, :date, :time, :dog_id, :recorder_id, :fresh, :dry, :meal_name, :grams, :water, :notes, CURRENT_TIMESTAMP)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'project_id': project_id,
                        'date': feeding_date,
                        'time': feeding_time,
                        'dog_id': random.choice(dog_ids),
                        'recorder_id': random.choice(caretaker_ids),
                        'fresh': True,
                        'dry': random.random() < 0.5,
                        'meal_name': random.choice(['Morning Feed', 'Evening Feed']),
                        'grams': random.randint(300, 700),
                        'water': random.randint(250, 500),
                        'notes': 'Regular feeding'
                    })
                
                db.session.commit()
                print("✓ Created 40 feeding logs")
            
            # 6. Create Caretaker Daily Logs
            if caretaker_ids and dog_ids and project_ids:
                print("Creating caretaker daily logs...")
                
                for i in range(30):
                    log_date = date.today() - timedelta(days=random.randint(1, 15))
                    
                    sql = """
                    INSERT INTO caretaker_daily_log 
                    (id, project_id, date, dog_id, caretaker_employee_id, feeding_morning_given, feeding_evening_given, 
                     water_refilled, kennel_cleaned, exercise_given, health_check_done, notes, created_at)
                    VALUES (gen_random_uuid(), :project_id, :date, :dog_id, :caretaker_id, :morning, :evening, :water, :cleaned, :exercise, :health, :notes, CURRENT_TIMESTAMP)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'project_id': random.choice(project_ids),
                        'date': log_date,
                        'dog_id': random.choice(dog_ids),
                        'caretaker_id': random.choice(caretaker_ids),
                        'morning': True,
                        'evening': random.random() < 0.9,
                        'water': random.random() < 0.95,
                        'cleaned': random.random() < 0.85,
                        'exercise': random.random() < 0.8,
                        'health': random.random() < 0.75,
                        'notes': 'Daily care completed'
                    })
                
                db.session.commit()
                print("✓ Created 30 caretaker daily logs")
            
            # Summary
            print("\n" + "="*60)
            print("✅ Test data population completed successfully!")
            print("\n📊 Data Summary:")
            
            tables = {
                'Users': '\"user\"',
                'Employees': 'employee',
                'Dogs': 'dog',
                'Projects': 'project',
                'Training Sessions': 'training_session',
                'Veterinary Visits': 'veterinary_visit',
                'Attendance Records': 'project_attendance_reporting',
                'Feeding Logs': 'feeding_log',
                'Caretaker Logs': 'caretaker_daily_log',
                'Shifts': 'project_shift'
            }
            
            for name, table in tables.items():
                count = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"   - {name}: {count}")
            
            print("="*60)
            print("\n✨ Ready to test all features!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    populate()
