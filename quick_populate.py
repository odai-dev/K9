#!/usr/bin/env python3
"""
Quick data population for testing K9 system reports
"""

import os
import sys
from datetime import datetime, date, time, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def populate_test_data():
    """Populate test data using direct SQL to avoid enum issues"""
    print("Populating test data using direct SQL...")
    
    with app.app_context():
        try:
            # Get existing IDs for foreign keys
            dogs_result = db.session.execute(db.text("SELECT id FROM dog LIMIT 10")).fetchall()
            employees_result = db.session.execute(db.text("SELECT id FROM employee")).fetchall()
            projects_result = db.session.execute(db.text("SELECT id FROM project WHERE status = 'ACTIVE'")).fetchall()
            
            dog_ids = [str(row[0]) for row in dogs_result]
            employee_ids = [str(row[0]) for row in employees_result]
            project_ids = [str(row[0]) for row in projects_result]
            
            print(f"Found {len(dog_ids)} dogs, {len(employee_ids)} employees, {len(project_ids)} active projects")
            
            if not dog_ids or not employee_ids or not project_ids:
                print("Missing basic data")
                return
            
            # Get trainer and vet IDs
            trainers_result = db.session.execute(db.text("SELECT id FROM employee WHERE role = 'TRAINER'")).fetchall()
            vets_result = db.session.execute(db.text("SELECT id FROM employee WHERE role = 'VET'")).fetchall()
            breeders_result = db.session.execute(db.text("SELECT id FROM employee WHERE role = 'BREEDER'")).fetchall()
            
            trainer_ids = [str(row[0]) for row in trainers_result]
            vet_ids = [str(row[0]) for row in vets_result]
            breeder_ids = [str(row[0]) for row in breeders_result]
            
            # 1. Create Training Sessions
            print("Creating training sessions...")
            training_categories = ['OBEDIENCE', 'DETECTION', 'AGILITY', 'ATTACK', 'FITNESS', 'BEHAVIOR_IMPROVEMENT']
            
            for i in range(30):
                if trainer_ids:
                    session_date = datetime.now() - timedelta(days=random.randint(1, 60))
                    dog_id = random.choice(dog_ids)
                    trainer_id = random.choice(trainer_ids)
                    project_id = random.choice(project_ids) if random.random() < 0.8 else None
                    category = random.choice(training_categories)
                    
                    sql = """
                    INSERT INTO training_session 
                    (id, dog_id, trainer_id, project_id, category, subject, session_date, duration, success_rating, location, notes)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        'location': f'Training Ground {random.randint(1, 5)}',
                        'notes': 'Training session completed successfully'
                    })
            
            db.session.commit()
            print("✓ Created training sessions")
            
            # 2. Create Veterinary Visits
            print("Creating veterinary visits...")
            visit_types = ['ROUTINE', 'EMERGENCY', 'VACCINATION']
            
            for i in range(25):
                if vet_ids:
                    visit_date = datetime.now() - timedelta(days=random.randint(1, 90))
                    dog_id = random.choice(dog_ids)
                    vet_id = random.choice(vet_ids)
                    visit_type = random.choice(visit_types)
                    
                    sql = """
                    INSERT INTO veterinary_visit 
                    (id, dog_id, vet_id, project_id, visit_type, visit_date, symptoms, diagnosis, treatment, cost, weight, notes)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'dog_id': dog_id,
                        'vet_id': vet_id,
                        'project_id': random.choice(project_ids) if random.random() < 0.7 else None,
                        'visit_type': visit_type,
                        'visit_date': visit_date,
                        'symptoms': 'Routine checkup',
                        'diagnosis': 'Healthy',
                        'treatment': 'No treatment needed',
                        'cost': round(random.uniform(100.0, 500.0), 2),
                        'weight': round(random.uniform(25.0, 40.0), 1),
                        'notes': f'Routine {visit_type} visit completed'
                    })
            
            db.session.commit()
            print("✓ Created veterinary visits")
            
            # 3. Create Project Shifts
            print("Creating project shifts...")
            for project_id in project_ids:
                # Morning shift
                sql = """
                INSERT INTO project_shift (id, project_id, name, start_time, end_time, is_active)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
                """
                
                db.session.execute(db.text(sql), {
                    'project_id': project_id,
                    'name': 'Morning Shift',
                    'start_time': time(8, 0),
                    'end_time': time(16, 0),
                    'is_active': True
                })
                
                # Evening shift
                db.session.execute(db.text(sql), {
                    'project_id': project_id,
                    'name': 'Evening Shift', 
                    'start_time': time(16, 0),
                    'end_time': time(24, 0),
                    'is_active': True
                })
            
            db.session.commit()
            print("✓ Created project shifts")
            
            # 4. Create Attendance Records
            print("Creating attendance records...")
            attendance_statuses = ['PRESENT', 'LATE', 'ABSENT']
            
            for days_ago in range(15):
                attendance_date = date.today() - timedelta(days=days_ago)
                
                for project_id in project_ids:
                    # Select 8 employees per project per day
                    selected_employees = random.sample(employee_ids, min(len(employee_ids), 8))
                    
                    for i, employee_id in enumerate(selected_employees):
                        sql = """
                        INSERT INTO project_attendance_reporting 
                        (id, date, project_id, employee_id, group_no, seq_no, check_in_time, check_out_time, status)
                        VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        status = random.choice(attendance_statuses) if random.random() < 0.1 else 'PRESENT'
                        
                        db.session.execute(db.text(sql), {
                            'date': attendance_date,
                            'project_id': project_id,
                            'employee_id': employee_id,
                            'group_no': 1,
                            'seq_no': i + 1,
                            'check_in_time': time(8 + random.randint(0, 1), random.randint(0, 30)),
                            'check_out_time': time(16 + random.randint(0, 1), random.randint(0, 30)),
                            'status': status
                        })
            
            db.session.commit()
            print("✓ Created attendance records")
            
            # 5. Create Feeding Logs
            print("Creating feeding logs...")
            caretaker_ids = breeder_ids + [eid for eid in employee_ids if eid not in breeder_ids][:5]
            
            for i in range(60):
                if caretaker_ids:
                    feeding_date = date.today() - timedelta(days=random.randint(1, 30))
                    feeding_time = time(random.randint(7, 18), 0)
                    
                    sql = """
                    INSERT INTO feeding_log 
                    (id, project_id, date, time, dog_id, recorder_employee_id, meal_type_fresh, meal_type_dry, meal_name, grams, water_ml, notes)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'project_id': random.choice(project_ids) if random.random() < 0.8 else None,
                        'date': feeding_date,
                        'time': feeding_time,
                        'dog_id': random.choice(dog_ids),
                        'recorder_employee_id': random.choice(caretaker_ids),
                        'meal_type_fresh': True,
                        'meal_type_dry': random.random() < 0.5,
                        'meal_name': random.choice(['Morning Feed', 'Evening Feed', 'Afternoon Snack']),
                        'grams': random.randint(300, 700),
                        'water_ml': random.randint(250, 500),
                        'notes': 'Regular feeding completed'
                    })
            
            db.session.commit()
            print("✓ Created feeding logs")
            
            # 6. Create Caretaker Daily Logs
            print("Creating caretaker daily logs...")
            for i in range(45):
                if caretaker_ids:
                    log_date = date.today() - timedelta(days=random.randint(1, 20))
                    
                    sql = """
                    INSERT INTO caretaker_daily_log 
                    (id, project_id, date, dog_id, caretaker_employee_id, feeding_morning_given, feeding_evening_given, 
                     water_refilled, kennel_cleaned, exercise_given, health_check_done, notes)
                    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    db.session.execute(db.text(sql), {
                        'project_id': random.choice(project_ids),
                        'date': log_date,
                        'dog_id': random.choice(dog_ids),
                        'caretaker_employee_id': random.choice(caretaker_ids),
                        'feeding_morning_given': True,
                        'feeding_evening_given': random.random() < 0.9,
                        'water_refilled': random.random() < 0.95,
                        'kennel_cleaned': random.random() < 0.85,
                        'exercise_given': random.random() < 0.8,
                        'health_check_done': random.random() < 0.75,
                        'notes': 'Daily care routine completed'
                    })
            
            db.session.commit()
            print("✓ Created caretaker daily logs")
            
            print("\n" + "="*60)
            print("✅ Test data population completed successfully!")
            
            # Verify data counts
            counts = {}
            tables = ['training_session', 'veterinary_visit', 'project_attendance_reporting', 
                     'project_shift', 'feeding_log', 'caretaker_daily_log']
            
            for table in tables:
                result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                counts[table] = result[0]
            
            print("📊 Final data counts:")
            for table, count in counts.items():
                print(f"   - {table}: {count}")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    populate_test_data()