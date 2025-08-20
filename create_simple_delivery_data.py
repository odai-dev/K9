#!/usr/bin/env python3
"""
Simple delivery sample data creator - creates minimal test data for puppy creation
"""

from app import app, db
from models import Dog, DogGender, DogStatus, PregnancyRecord, DeliveryRecord, PregnancyStatus, MatingRecord, MatingResult
from datetime import datetime, date, timedelta
import uuid

def create_simple_delivery_data():
    """Create simple delivery records for testing puppy creation"""
    
    with app.app_context():
        print("Creating simple delivery test data...")
        
        # Check if we already have delivery records
        existing_deliveries = DeliveryRecord.query.count()
        if existing_deliveries > 0:
            print(f"✓ Already have {existing_deliveries} delivery records")
            return
        
        # Get existing dogs or create simple ones
        female_dogs = Dog.query.filter(Dog.gender == DogGender.FEMALE).all()
        if not female_dogs:
            print("Creating sample female dogs...")
            female1 = Dog()
            female1.name = "بيلا"
            female1.code = "F001"
            female1.breed = "جيرمن شيبرد"
            female1.gender = DogGender.FEMALE
            female1.birth_date = date(2020, 5, 15)
            female1.current_status = DogStatus.ACTIVE
            
            db.session.add(female1)
            db.session.commit()
            female_dogs = [female1]
            print(f"✓ Created female dog: {female1.name}")
        
        male_dogs = Dog.query.filter(Dog.gender == DogGender.MALE).all()
        if not male_dogs:
            print("Creating sample male dog...")
            male1 = Dog()
            male1.name = "ماكس"
            male1.code = "M001"
            male1.breed = "جيرمن شيبرد"
            male1.gender = DogGender.MALE
            male1.birth_date = date(2019, 3, 10)
            male1.current_status = DogStatus.ACTIVE
            
            db.session.add(male1)
            db.session.commit()
            male_dogs = [male1]
            print(f"✓ Created male dog: {male1.name}")
        
        # Create a simple mating record
        female = female_dogs[0]
        male = male_dogs[0]
        
        mating = MatingRecord()
        mating.female_id = female.id
        mating.male_id = male.id
        mating.mating_date = date.today() - timedelta(days=65)
        mating.result = MatingResult.SUCCESSFUL
        mating.notes = "تزاوج ناجح - بيانات تجريبية"
        
        db.session.add(mating)
        db.session.commit()
        print(f"✓ Created mating record: {female.name} × {male.name}")
        
        # Create pregnancy record
        pregnancy = PregnancyRecord()
        pregnancy.mating_record_id = mating.id
        pregnancy.dog_id = female.id
        pregnancy.confirmed_date = mating.mating_date + timedelta(days=21)
        pregnancy.expected_delivery_date = mating.mating_date + timedelta(days=63)
        pregnancy.status = PregnancyStatus.DELIVERED
        pregnancy.notes = "حمل ناجح - بيانات تجريبية"
        
        db.session.add(pregnancy)
        db.session.commit()
        print(f"✓ Created pregnancy record for {female.name}")
        
        # Create delivery record
        delivery = DeliveryRecord()
        delivery.pregnancy_record_id = pregnancy.id
        delivery.delivery_date = pregnancy.expected_delivery_date
        delivery.total_puppies = 4
        delivery.live_births = 4
        delivery.stillbirths = 0
        delivery.mother_condition = "ممتازة"
        delivery.notes = "ولادة ناجحة - 4 جراء بصحة جيدة - بيانات تجريبية"
        
        db.session.add(delivery)
        db.session.commit()
        print(f"✓ Created delivery record: {delivery.live_births} live puppies")
        
        # Create a second delivery for more test data
        delivery2 = DeliveryRecord()
        delivery2.pregnancy_record_id = pregnancy.id
        delivery2.delivery_date = date.today() - timedelta(days=30)
        delivery2.total_puppies = 3
        delivery2.live_births = 3
        delivery2.stillbirths = 0
        delivery2.mother_condition = "جيدة"
        delivery2.notes = "ولادة ثانية - 3 جراء - بيانات تجريبية"
        
        db.session.add(delivery2)
        db.session.commit()
        print(f"✓ Created second delivery record: {delivery2.live_births} live puppies")
        
        # Verify
        total_deliveries = DeliveryRecord.query.count()
        print(f"\n✅ Success! Created {total_deliveries} delivery records")
        print("🐕 Puppy creation form should now show delivery records in dropdown!")

if __name__ == "__main__":
    create_simple_delivery_data()