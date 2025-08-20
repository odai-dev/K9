#!/usr/bin/env python3
"""
Sample data creator for breeding system delivery records
Creates test data for pregnancy records and delivery records to test puppy creation
"""

from app import app, db
from models import *
from datetime import datetime, date, timedelta
import uuid

def create_delivery_sample_data():
    """Create sample delivery records for testing puppy creation"""
    
    with app.app_context():
        print("Creating sample breeding and delivery data...")
        
        # Check if we have any dogs
        dogs = Dog.query.filter(Dog.gender == DogGender.FEMALE).all()
        if not dogs:
            print("No female dogs found. Creating sample dogs first...")
            # Create sample female dogs
            female1 = Dog()
            female1.name = "بيلا"
            female1.code = "F001"
            female1.breed = "جيرمن شيبرد"
            female1.gender = DogGender.FEMALE
            female1.birth_date = date(2020, 5, 15)
            female1.current_status = DogStatus.ACTIVE
            
            female2 = Dog()
            female2.name = "لونا"
            female2.code = "F002"
            female2.breed = "لابرادور"
            female2.gender = DogGender.FEMALE
            female2.birth_date = date(2019, 8, 22)
            female2.current_status = DogStatus.ACTIVE
            
            male1 = Dog()
            male1.name = "ماكس"
            male1.code = "M001"
            male1.breed = "جيرمن شيبرد"
            male1.gender = DogGender.MALE
            male1.birth_date = date(2019, 3, 10)
            male1.current_status = DogStatus.ACTIVE
            
            db.session.add_all([female1, female2, male1])
            db.session.commit()
            print("✓ Created sample dogs")
            
            dogs = [female1, female2]
            males = [male1]
        else:
            print(f"✓ Found {len(dogs)} female dogs")
            males = Dog.query.filter(Dog.gender == DogGender.MALE).all()
            if not males:
                male1 = Dog()
                male1.name = "ماكس"
                male1.code = "M001"
                male1.breed = "جيرمن شيبرد"
                male1.gender = DogGender.MALE
                male1.birth_date = date(2019, 3, 10)
                male1.current_status = DogStatus.ACTIVE
                db.session.add(male1)
                db.session.commit()
                males = [male1]
        
        # Create maturity records for females
        for female in dogs[:2]:  # Take first 2 females
            maturity = MaturityRecord.query.filter_by(dog_id=female.id).first()
            if not maturity:
                maturity = MaturityRecord()
                maturity.dog_id = female.id
                maturity.maturity_date = female.birth_date + timedelta(days=365)  # 1 year old
                maturity.maturity_weight = 25.5
                maturity.status = MaturityStatus.MATURE
                maturity.notes = "وصلت للنضج الجنسي"
                db.session.add(maturity)
                print(f"✓ Created maturity record for {female.name}")
        
        # Create heat cycle records
        for female in dogs[:2]:
            heat_cycle = HeatCycleRecord.query.filter_by(dog_id=female.id).first()
            if not heat_cycle:
                heat_cycle = HeatCycleRecord()
                heat_cycle.dog_id = female.id
                heat_cycle.start_date = date.today() - timedelta(days=90)
                heat_cycle.end_date = date.today() - timedelta(days=75)
                heat_cycle.duration_days = 15
                heat_cycle.intensity = "متوسط"
                heat_cycle.behavioral_changes = "زيادة النشاط"
                heat_cycle.status = HeatStatus.COMPLETED
                db.session.add(heat_cycle)
                print(f"✓ Created heat cycle record for {female.name}")
        
        db.session.commit()
        
        # Create mating records
        for i, female in enumerate(dogs[:2]):
            male = males[0] if males else None
            if not male:
                continue
                
            mating = MatingRecord.query.filter_by(female_id=female.id, male_id=male.id).first()
            if not mating:
                mating = MatingRecord()
                mating.female_id = female.id
                mating.male_id = male.id
                mating.mating_date = date.today() - timedelta(days=65)
                mating.mating_time = datetime.now().time()
                mating.location = "منطقة التزاوج المخصصة"
                mating.duration_minutes = 30
                mating.success_rate = 90
                mating.result = MatingResult.SUCCESSFUL
                mating.behavior_observed = "تزاوج طبيعي وناجح"
                mating.notes = "تمت العملية تحت إشراف طبيب بيطري"
                db.session.add(mating)
                print(f"✓ Created mating record for {female.name} × {male.name}")
        
        db.session.commit()
        
        # Create pregnancy records
        mating_records = MatingRecord.query.all()
        for mating in mating_records:
            pregnancy = PregnancyRecord.query.filter_by(mating_record_id=mating.id).first()
            if not pregnancy:
                pregnancy = PregnancyRecord()
                pregnancy.mating_record_id = mating.id
                pregnancy.dog_id = mating.female_id
                pregnancy.confirmed_date = mating.mating_date + timedelta(days=21)
                pregnancy.expected_delivery_date = mating.mating_date + timedelta(days=63)
                pregnancy.status = PregnancyStatus.DELIVERED
                pregnancy.special_diet = "غذاء عالي البروتين للحوامل"
                pregnancy.exercise_restrictions = "تمارين خفيفة فقط"
                pregnancy.notes = "حمل طبيعي بدون مضاعفات"
                db.session.add(pregnancy)
                print(f"✓ Created pregnancy record for {mating.female.name}")
        
        db.session.commit()
        
        # Create delivery records
        pregnancy_records = PregnancyRecord.query.all()
        for pregnancy in pregnancy_records:
            delivery = DeliveryRecord.query.filter_by(pregnancy_record_id=pregnancy.id).first()
            if not delivery:
                delivery = DeliveryRecord()
                delivery.pregnancy_record_id = pregnancy.id
                delivery.delivery_date = pregnancy.expected_delivery_date
                delivery.delivery_start_time = datetime.strptime("08:30", "%H:%M").time()
                delivery.delivery_end_time = datetime.strptime("12:45", "%H:%M").time()
                delivery.location = "غرفة الولادة المجهزة"
                delivery.total_puppies = 5
                delivery.live_births = 5
                delivery.stillbirths = 0
                delivery.assistance_required = False
                delivery.delivery_complications = None
                delivery.mother_condition = "ممتازة"
                delivery.notes = "ولادة طبيعية وناجحة، جميع الجراء بصحة جيدة"
                db.session.add(delivery)
                print(f"✓ Created delivery record for {pregnancy.dog.name} - {delivery.live_births} puppies")
        
        db.session.commit()
        
        # Verify created data
        delivery_count = DeliveryRecord.query.count()
        pregnancy_count = PregnancyRecord.query.count()
        mating_count = MatingRecord.query.count()
        
        print(f"\n📊 Sample data created successfully:")
        print(f"   • {mating_count} mating records")
        print(f"   • {pregnancy_count} pregnancy records") 
        print(f"   • {delivery_count} delivery records")
        print(f"\n✅ Puppy creation form should now show delivery records in dropdown!")

if __name__ == "__main__":
    create_delivery_sample_data()