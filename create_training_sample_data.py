#!/usr/bin/env python3
"""
Create sample training session data for testing trainer daily reports
"""

import os
from datetime import datetime, date, timedelta
from app import app, db
from models import TrainingSession, Employee, Dog, Project, TrainingCategory
import random

def create_training_sample_data():
    """Create sample training sessions for testing"""
    
    with app.app_context():
        print("Creating sample training session data...")
        
        # Get existing employees (trainers)
        trainers = db.session.query(Employee).limit(3).all()
        if not trainers:
            print("No employees found. Please create employees first.")
            return
            
        # Get existing dogs
        dogs = db.session.query(Dog).limit(5).all()
        if not dogs:
            print("No dogs found. Please create dogs first.")
            return
            
        # Get existing projects
        projects = db.session.query(Project).limit(2).all()
        
        # Training categories
        categories = [
            TrainingCategory.OBEDIENCE,
            TrainingCategory.DETECTION, 
            TrainingCategory.AGILITY,
            TrainingCategory.ATTACK,
            TrainingCategory.FITNESS
        ]
        
        # Training subjects by category
        subjects = {
            TrainingCategory.OBEDIENCE: ["أوامر الطاعة الأساسية", "التحكم في السلوك", "الاستجابة للنداء"],
            TrainingCategory.DETECTION: ["كشف المواد المخدرة", "كشف المتفجرات", "تتبع الروائح"],
            TrainingCategory.AGILITY: ["تسلق الحواجز", "المرور عبر الأنفاق", "التوازن"],
            TrainingCategory.ATTACK: ["الهجوم المحكم", "الدفاع عن المدرب", "التحكم في القوة"],
            TrainingCategory.FITNESS: ["الجري والتحمل", "تمارين القوة", "المرونة"]
        }
        
        # Equipment lists
        equipment_options = [
            ["مقود", "كرة"],
            ["حاجز", "مخروط"],
            ["دمية", "واقي"],
            ["كرة", "حبل"],
            []
        ]
        
        # Create training sessions for the last 7 days
        sessions_created = 0
        for days_ago in range(7):
            session_date = date.today() - timedelta(days=days_ago)
            
            # Create 2-5 sessions per day
            sessions_per_day = random.randint(2, 5)
            
            for i in range(sessions_per_day):
                # Random time during the day
                hour = random.randint(8, 17)
                minute = random.randint(0, 59)
                session_datetime = datetime.combine(session_date, datetime.min.time().replace(hour=hour, minute=minute))
                
                # Random selections
                trainer = random.choice(trainers)
                dog = random.choice(dogs)
                category = random.choice(categories)
                project = random.choice(projects) if projects and random.choice([True, False]) else None
                
                # Create training session
                session = TrainingSession(
                    dog_id=dog.id,
                    trainer_id=trainer.id,
                    project_id=project.id if project else None,
                    category=category,
                    subject=random.choice(subjects[category]),
                    session_date=session_datetime,
                    duration=random.randint(30, 120),  # 30-120 minutes
                    success_rating=random.randint(5, 10),  # 5-10 rating
                    location=random.choice(["الملعب الرئيسي", "منطقة التدريب", "الحديقة الخلفية"]),
                    weather_conditions=random.choice(["مشمس", "غائم", "معتدل", "حار"]),
                    equipment_used=random.choice(equipment_options),
                    notes=f"ملاحظات تدريب {category.value}"
                )
                
                db.session.add(session)
                sessions_created += 1
        
        # Commit all sessions
        db.session.commit()
        print(f"✅ Created {sessions_created} training sessions successfully!")
        
        # Show summary
        print("\n📊 Data Summary:")
        print(f"Trainers: {len(trainers)}")
        print(f"Dogs: {len(dogs)}")
        print(f"Projects: {len(projects)}")
        print(f"Training sessions: {sessions_created}")

if __name__ == "__main__":
    create_training_sample_data()